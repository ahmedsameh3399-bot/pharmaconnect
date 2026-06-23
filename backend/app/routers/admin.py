"""Admin endpoints: moderation and system-wide views."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_db, require_admin
from app.models.distributor import Distributor
from app.models.order import Order, OrderStatus
from app.models.pharmacy import Pharmacy
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


class UserAdminView(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_suspended: bool


class SuspendRequest(BaseModel):
    suspended: bool


@router.get("/users", response_model=list[UserAdminView])
def list_users(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[UserAdminView]:
    users = db.scalars(select(User).order_by(User.id)).all()
    return [
        UserAdminView(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value,
            is_suspended=u.is_suspended,
        )
        for u in users
    ]


@router.post("/users/{user_id}/suspension")
def set_suspension(
    user_id: int,
    payload: SuspendRequest,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserAdminView:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.role.value == "ADMIN":
        # Defensive: don't allow admins to suspend each other through the API.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot suspend an admin")
    user.is_suspended = payload.suspended
    db.commit()
    return UserAdminView(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_suspended=user.is_suspended,
    )


@router.get("/metrics")
def metrics(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """One-shot dashboard numbers for the admin home page."""
    pharmacy_count = db.scalar(select(func.count(Pharmacy.id))) or 0
    distributor_count = db.scalar(select(func.count(Distributor.id))) or 0
    order_count = db.scalar(select(func.count(Order.id))) or 0
    pending_orders = db.scalar(
        select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING)
    ) or 0
    suspended_users = db.scalar(select(func.count(User.id)).where(User.is_suspended.is_(True))) or 0
    return {
        "pharmacies": pharmacy_count,
        "distributors": distributor_count,
        "orders_total": order_count,
        "orders_pending": pending_orders,
        "users_suspended": suspended_users,
    }
