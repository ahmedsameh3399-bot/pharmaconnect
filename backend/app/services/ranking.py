"""Best-offer ranking algorithm (Upgrade #1).

The book's "discount comparison" is vague. We turn it into something concrete
and defendable: for each offer carrying the requested medication we compute a
weighted score from three normalized signals, then return offers sorted by
that score.

Signals (each normalized to [0, 1], higher = better):

  1. price_score      = (max_final_price - this_final_price) / (max_final_price - min_final_price)
                        i.e. the cheapest offer scores 1.0, the most expensive scores 0.0.
  2. stock_score      = min(this_stock / requested_quantity, 1.0)
                        i.e. enough stock = 1.0; less than enough degrades linearly.
  3. reliability_score = distributor.accepted_orders / total_orders, neutral 0.5 if new.

Total score:
  total = W_PRICE * price_score + W_STOCK * stock_score + W_RELIABILITY * reliability_score

Weights are constants at the top of this file. They sum to 1.0 so the total is
also in [0, 1]. Choosing 0.6 / 0.25 / 0.15 reflects that pharmacies care most
about price, then having enough stock to fulfill the request, and finally
about whether the distributor is likely to actually accept the order.

The student can defend this on a whiteboard by walking through one row of the
formula with real numbers.
"""

from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.medication import Medication
from app.models.offer import Offer

W_PRICE = 0.60
W_STOCK = 0.25
W_RELIABILITY = 0.15


@dataclass
class RankedOffer:
    offer: Offer
    price_score: float
    stock_score: float
    reliability_score: float
    total_score: float


def rank_offers_for_medication(
    db: Session,
    medication_id: int,
    requested_quantity: int = 1,
) -> list[RankedOffer]:
    """Return every distributor's offer for a medication, sorted best-first.

    Offers with zero stock are kept in the result (with stock_score=0) so the
    pharmacy sees them, but they sink to the bottom of the list because of
    the lower total score.
    """
    if requested_quantity < 1:
        raise ValueError("requested_quantity must be >= 1")

    stmt = (
        select(Offer)
        .where(Offer.medication_id == medication_id)
        .options(joinedload(Offer.distributor), joinedload(Offer.medication))
    )
    offers: list[Offer] = list(db.scalars(stmt).all())
    if not offers:
        return []

    final_prices = [o.final_unit_price for o in offers]
    min_price, max_price = min(final_prices), max(final_prices)
    price_range = max_price - min_price  # may be 0 when there's only one offer

    ranked: list[RankedOffer] = []
    for offer in offers:
        # When all offers cost the same, every offer ties on price.
        if price_range == 0:
            price_score = 1.0
        else:
            price_score = (max_price - offer.final_unit_price) / price_range

        stock_score = min(offer.stock / requested_quantity, 1.0) if requested_quantity else 0.0
        reliability_score = offer.distributor.reliability_score

        total = (
            W_PRICE * price_score
            + W_STOCK * stock_score
            + W_RELIABILITY * reliability_score
        )

        ranked.append(
            RankedOffer(
                offer=offer,
                price_score=round(price_score, 4),
                stock_score=round(stock_score, 4),
                reliability_score=round(reliability_score, 4),
                total_score=round(total, 4),
            )
        )

    ranked.sort(key=lambda r: r.total_score, reverse=True)
    return ranked
