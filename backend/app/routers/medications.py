"""Public medication catalog: list/search and (admin-only) create."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db, require_admin
from app.models.medication import Medication
from app.models.user import User
from app.schemas.medication import MedicationCreate, MedicationOut

router = APIRouter(prefix="/medications", tags=["medications"])


@router.get("", response_model=list[MedicationOut])
def list_medications(
    q: str | None = Query(default=None, description="Search by name or active ingredient"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[Medication]:
    stmt = select(Medication)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Medication.name.ilike(pattern),
                Medication.active_ingredient.ilike(pattern),
                Medication.manufacturer.ilike(pattern),
            )
        )
    return list(db.scalars(stmt.order_by(Medication.name).limit(limit)).all())


@router.get("/{medication_id}", response_model=MedicationOut)
def get_medication(
    medication_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Medication:
    med = db.get(Medication, medication_id)
    if not med:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Medication not found")
    return med


@router.post("", response_model=MedicationOut, status_code=status.HTTP_201_CREATED)
def create_medication(
    payload: MedicationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Medication:
    med = Medication(**payload.model_dump())
    db.add(med)
    db.commit()
    db.refresh(med)
    return med
