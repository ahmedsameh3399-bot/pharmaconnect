"""Order lifecycle: place / list / update status / cancel."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.deps import get_current_user, get_db, require_distributor, require_pharmacy
from app.models.distributor import Distributor
from app.models.offer import Offer
from app.models.order import Order, OrderItem, OrderStatus
from app.models.order_event import OrderEvent
from app.models.user import User, UserRole
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from app.services.notifications import Notification, hub
from app.services.order_state import InvalidTransition, transition

router = APIRouter(prefix="/orders", tags=["orders"])


def _serialize(order: Order) -> Order:
    """Touch lazy relationships so Pydantic can serialize without N+1 issues."""
    _ = [item.medication.name for item in order.items]
    _ = order.events
    return order


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def place_order(
    payload: OrderCreate,
    user: User = Depends(require_pharmacy),
    db: Session = Depends(get_db),
) -> Order:
    assert user.pharmacy is not None
    distributor = db.get(Distributor, payload.distributor_id)
    if not distributor:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Distributor not found")

    # Snapshot pricing from current offers and validate stock in one pass.
    items: list[OrderItem] = []
    total = 0.0
    for line in payload.items:
        offer = db.scalar(
            select(Offer).where(
                Offer.distributor_id == payload.distributor_id,
                Offer.medication_id == line.medication_id,
            )
        )
        if not offer:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Distributor doesn't carry medication {line.medication_id}",
            )
        if offer.stock < line.quantity:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Insufficient stock for medication {line.medication_id} "
                f"(requested {line.quantity}, available {offer.stock})",
            )
        item = OrderItem(
            medication_id=line.medication_id,
            quantity=line.quantity,
            unit_price=offer.unit_price,
            discount_percent=offer.discount_percent,
        )
        items.append(item)
        total += item.line_total

    order = Order(
        pharmacy_id=user.pharmacy.id,
        distributor_id=payload.distributor_id,
        status=OrderStatus.PENDING,
        total_amount=round(total, 2),
        notes=payload.notes,
        items=items,
    )
    db.add(order)
    db.flush()
    # Audit-log the creation as a "transition" from None to PENDING.
    db.add(
        OrderEvent(
            order_id=order.id,
            actor_user_id=user.id,
            from_status=None,
            to_status=OrderStatus.PENDING.value,
            note="Order placed",
        )
    )
    db.commit()
    db.refresh(order)

    # Notify the distributor in real time.
    hub.publish(
        distributor.user_id,
        Notification(
            type="order.created",
            payload={"order_id": order.id, "pharmacy_id": user.pharmacy.id, "total": order.total_amount},
        ),
    )
    return _serialize(order)


@router.get("/mine", response_model=list[OrderOut])
def list_my_orders(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Order]:
    """Pharmacies see their placed orders; distributors see their inbox."""
    stmt = select(Order).options(
        joinedload(Order.items).joinedload(OrderItem.medication),
        joinedload(Order.events),
    )
    if user.role == UserRole.PHARMACY:
        assert user.pharmacy is not None
        stmt = stmt.where(Order.pharmacy_id == user.pharmacy.id)
    elif user.role == UserRole.DISTRIBUTOR:
        assert user.distributor is not None
        stmt = stmt.where(Order.distributor_id == user.distributor.id)
    else:
        # Admins use /admin/orders; this endpoint is per-actor.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Use /admin/orders for admin views")
    stmt = stmt.order_by(Order.created_at.desc())
    return list(db.scalars(stmt).unique().all())


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    # Only the two parties (or admin) can see an order.
    if user.role == UserRole.PHARMACY and (
        not user.pharmacy or order.pharmacy_id != user.pharmacy.id
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your order")
    if user.role == UserRole.DISTRIBUTOR and (
        not user.distributor or order.distributor_id != user.distributor.id
    ):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your order")
    return _serialize(order)


@router.post("/{order_id}/status", response_model=OrderOut)
def change_status(
    order_id: int,
    payload: OrderStatusUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Order:
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")

    # Who can drive which transition is enforced here.
    target = payload.new_status
    if user.role == UserRole.PHARMACY:
        if not user.pharmacy or order.pharmacy_id != user.pharmacy.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your order")
        # Pharmacies can only cancel (and only from PENDING, enforced by FSM).
        if target != OrderStatus.CANCELLED:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Pharmacies can only cancel orders"
            )
    elif user.role == UserRole.DISTRIBUTOR:
        if not user.distributor or order.distributor_id != user.distributor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your order")
        # Distributors can accept/reject, then drive through prepare/ship/complete.
        if target not in {
            OrderStatus.ACCEPTED,
            OrderStatus.REJECTED,
            OrderStatus.PREPARING,
            OrderStatus.SHIPPED,
            OrderStatus.COMPLETED,
        }:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"Distributors can't set status to {target.value}"
            )
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admins use /admin endpoints")

    try:
        transition(db, order, target, actor_user_id=user.id, note=payload.note)
    except InvalidTransition as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))

    # Side effects of certain transitions:
    #   - On ACCEPTED: decrement stock (now committed demand).
    #   - On ACCEPTED/REJECTED: bump distributor reliability counters.
    if target == OrderStatus.ACCEPTED:
        for item in order.items:
            offer = db.scalar(
                select(Offer).where(
                    Offer.distributor_id == order.distributor_id,
                    Offer.medication_id == item.medication_id,
                )
            )
            if offer:
                offer.stock = max(0, offer.stock - item.quantity)
        order.distributor.accepted_orders_count += 1
    elif target == OrderStatus.REJECTED:
        order.distributor.rejected_orders_count += 1

    db.commit()
    db.refresh(order)

    # Notify the other party.
    other_user_id = (
        order.pharmacy.user_id
        if user.role == UserRole.DISTRIBUTOR
        else order.distributor.user_id
    )
    hub.publish(
        other_user_id,
        Notification(
            type="order.status_changed",
            payload={"order_id": order.id, "new_status": target.value},
        ),
    )
    return _serialize(order)
