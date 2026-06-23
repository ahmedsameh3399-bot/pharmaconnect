"""Best-offer ranking endpoint: the heart of the comparison feature."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.deps import get_db, require_pharmacy
from app.models.user import User
from app.schemas.offer import DistributorBrief, RankedOfferOut
from app.services.ranking import rank_offers_for_medication

router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.get("/medication/{medication_id}", response_model=list[RankedOfferOut])
def rank_for_medication(
    medication_id: int,
    quantity: int = Query(default=1, ge=1, le=10000),
    db: Session = Depends(get_db),
    _: User = Depends(require_pharmacy),
) -> list[RankedOfferOut]:
    ranked = rank_offers_for_medication(db, medication_id, requested_quantity=quantity)
    return [
        RankedOfferOut(
            offer_id=r.offer.id,
            distributor=DistributorBrief(
                id=r.offer.distributor.id,
                company_name=r.offer.distributor.company_name,
                reliability_score=r.offer.distributor.reliability_score,
            ),
            unit_price=r.offer.unit_price,
            discount_percent=r.offer.discount_percent,
            final_unit_price=r.offer.final_unit_price,
            stock=r.offer.stock,
            price_score=r.price_score,
            stock_score=r.stock_score,
            reliability_score=r.reliability_score,
            total_score=r.total_score,
        )
        for r in ranked
    ]
