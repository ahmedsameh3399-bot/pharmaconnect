"""Tests for the moving-average stock forecast service."""

from datetime import datetime, timedelta, timezone

from app.models.distributor import Distributor
from app.models.medication import Medication
from app.models.offer import Offer
from app.models.order import Order, OrderItem, OrderStatus
from app.models.pharmacy import Pharmacy
from app.models.user import User, UserRole
from app.security import hash_password
from app.services.stock_forecast import RISK_THRESHOLD_DAYS, WINDOW_DAYS, forecast_for_distributor


def _bootstrap(db):
    pu = User(email="p@x", hashed_password=hash_password("x"), role=UserRole.PHARMACY, full_name="p")
    du = User(email="d@x", hashed_password=hash_password("x"), role=UserRole.DISTRIBUTOR, full_name="d")
    db.add_all([pu, du]); db.flush()
    ph = Pharmacy(user_id=pu.id, name="p", license_number="L1", address="a", phone="p")
    di = Distributor(user_id=du.id, company_name="d", license_number="L2", address="a", phone="p")
    db.add_all([ph, di]); db.flush()
    med = Medication(name="M", active_ingredient="m", form="Tab", strength="1", manufacturer="x")
    db.add(med); db.flush()
    return ph, di, med


def test_no_demand_returns_none(db):
    _, di, med = _bootstrap(db)
    db.add(Offer(distributor_id=di.id, medication_id=med.id, unit_price=10, stock=100))
    db.commit()
    forecasts = forecast_for_distributor(db, di.id)
    assert len(forecasts) == 1
    assert forecasts[0].avg_daily_units == 0.0
    assert forecasts[0].predicted_days_until_stockout is None
    assert forecasts[0].at_risk is False


def test_high_demand_flags_at_risk(db):
    ph, di, med = _bootstrap(db)
    db.add(Offer(distributor_id=di.id, medication_id=med.id, unit_price=10, stock=10))

    # Simulate 30 days * 5 units/day = 150 units sold in the window via two
    # ACCEPTED orders. 30-day avg = 5/day; stock=10; predicted days = 2 < 7 => at risk.
    for _ in range(2):
        order = Order(
            pharmacy_id=ph.id, distributor_id=di.id,
            status=OrderStatus.ACCEPTED, total_amount=0,
        )
        order.items.append(OrderItem(medication_id=med.id, quantity=75, unit_price=10, discount_percent=0))
        db.add(order)
    db.commit()

    forecasts = forecast_for_distributor(db, di.id)
    [f] = forecasts
    assert f.avg_daily_units == round(150 / WINDOW_DAYS, 3)
    assert f.predicted_days_until_stockout is not None
    assert f.predicted_days_until_stockout < RISK_THRESHOLD_DAYS
    assert f.at_risk is True
