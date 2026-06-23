"""Distributor catalog management: create/update/delete own offers."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.deps import get_db, require_distributor
from app.models.medication import Medication
from app.models.offer import Offer
from app.models.user import User
from app.schemas.offer import OfferOut, OfferUpsert

router = APIRouter(prefix="/offers", tags=["offers"])


@router.get("/mine", response_model=list[OfferOut])
def list_my_offers(
    user: User = Depends(require_distributor),
    db: Session = Depends(get_db),
) -> list[Offer]:
    assert user.distributor is not None
    stmt = (
        select(Offer)
        .where(Offer.distributor_id == user.distributor.id)
        .options(joinedload(Offer.medication))
        .order_by(Offer.id.desc())
    )
    return list(db.scalars(stmt).all())


@router.put("/mine", response_model=OfferOut)
def upsert_my_offer(
    payload: OfferUpsert,
    user: User = Depends(require_distributor),
    db: Session = Depends(get_db),
) -> Offer:
    """Create or update this distributor's offer for a given medication.

    Using PUT-as-upsert keyed on (distributor, medication) keeps the API tiny
    and matches the DB's unique constraint - clients don't need to know
    whether they're creating or editing.
    """
    assert user.distributor is not None
    if not db.get(Medication, payload.medication_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medication not found")

    offer = db.scalar(
        select(Offer).where(
            Offer.distributor_id == user.distributor.id,
            Offer.medication_id == payload.medication_id,
        )
    )
    if offer is None:
        offer = Offer(
            distributor_id=user.distributor.id,
            medication_id=payload.medication_id,
        )
        db.add(offer)
    offer.unit_price = payload.unit_price
    offer.discount_percent = payload.discount_percent
    offer.stock = payload.stock
    db.commit()
    db.refresh(offer)
    # Force-load the medication relationship for the response.
    _ = offer.medication
    return offer


@router.delete("/mine/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_offer(
    offer_id: int,
    user: User = Depends(require_distributor),
    db: Session = Depends(get_db),
) -> None:
    assert user.distributor is not None
    offer = db.get(Offer, offer_id)
    if not offer or offer.distributor_id != user.distributor.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Offer not found")
    db.delete(offer)
    db.commit()
