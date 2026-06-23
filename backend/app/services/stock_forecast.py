"""Stock-depletion forecast (Upgrade #4).

We deliberately do NOT use an ML model here. With only weeks of operational
data, a moving-average of recent demand is the right tool: it's interpretable,
fast, and the student can derive it on a whiteboard.

Method:
  1. For a given distributor's offer, look at the past N days of OrderItems
     for that medication that belong to ACCEPTED+ orders (i.e. demand the
     distributor has actually committed to, not noisy PENDING-then-rejected
     orders).
  2. Compute average daily units sold = total_units / N.
  3. Predicted days-until-stockout = current_stock / avg_daily_units.
  4. If average daily units is 0 we return None (no signal yet).

Anything with predicted_days < `risk_threshold_days` is flagged on the
distributor's dashboard.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.medication import Medication
from app.models.offer import Offer
from app.models.order import Order, OrderItem, OrderStatus

WINDOW_DAYS = 30  # how much recent history to average over
RISK_THRESHOLD_DAYS = 7  # below this, flag the offer as at-risk

# Statuses we treat as "real" demand. Anything before ACCEPTED is unreliable
# (the distributor may have rejected it), so we exclude PENDING/REJECTED.
DEMAND_STATUSES = (
    OrderStatus.ACCEPTED,
    OrderStatus.PREPARING,
    OrderStatus.SHIPPED,
    OrderStatus.COMPLETED,
)


@dataclass
class StockForecast:
    offer_id: int
    medication_id: int
    medication_name: str
    current_stock: int
    avg_daily_units: float
    predicted_days_until_stockout: float | None
    at_risk: bool


def forecast_for_distributor(db: Session, distributor_id: int) -> list[StockForecast]:
    """Compute forecasts for every offer of one distributor."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)

    # Aggregate demand per medication for this distributor in the window.
    demand_stmt = (
        select(OrderItem.medication_id, func.coalesce(func.sum(OrderItem.quantity), 0))
        .join(Order, Order.id == OrderItem.order_id)
        .where(
            Order.distributor_id == distributor_id,
            Order.created_at >= cutoff,
            Order.status.in_([s.value for s in DEMAND_STATUSES]),
        )
        .group_by(OrderItem.medication_id)
    )
    demand_by_med: dict[int, int] = dict(db.execute(demand_stmt).all())

    offers_stmt = (
        select(Offer, Medication)
        .join(Medication, Medication.id == Offer.medication_id)
        .where(Offer.distributor_id == distributor_id)
    )
    results: list[StockForecast] = []
    for offer, med in db.execute(offers_stmt).all():
        units_sold = demand_by_med.get(offer.medication_id, 0)
        avg_daily = units_sold / WINDOW_DAYS

        if avg_daily <= 0:
            predicted_days = None
            at_risk = False
        else:
            predicted_days = offer.stock / avg_daily
            at_risk = predicted_days < RISK_THRESHOLD_DAYS

        results.append(
            StockForecast(
                offer_id=offer.id,
                medication_id=offer.medication_id,
                medication_name=med.name,
                current_stock=offer.stock,
                avg_daily_units=round(avg_daily, 3),
                predicted_days_until_stockout=(
                    round(predicted_days, 2) if predicted_days is not None else None
                ),
                at_risk=at_risk,
            )
        )

    # Sort at-risk first (ascending by predicted days) so the dashboard widget
    # shows the most urgent items at the top.
    def sort_key(f: StockForecast) -> tuple[int, float]:
        return (0 if f.at_risk else 1, f.predicted_days_until_stockout or 1e9)

    results.sort(key=sort_key)
    return results
