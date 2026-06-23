"""Distributor-facing stock-depletion forecast (Upgrade #4)."""

from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db, require_distributor
from app.models.user import User
from app.services.stock_forecast import forecast_for_distributor

router = APIRouter(prefix="/stock-forecast", tags=["stock-forecast"])


@router.get("/mine")
def my_forecast(
    user: User = Depends(require_distributor),
    db: Session = Depends(get_db),
) -> list[dict]:
    assert user.distributor is not None
    return [asdict(f) for f in forecast_for_distributor(db, user.distributor.id)]
