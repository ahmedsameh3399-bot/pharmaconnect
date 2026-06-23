"""Order finite state machine (Upgrade #2).

Centralizing the allowed transitions in one place means the API layer never
has to think about state correctness - it just calls `transition()` and trusts
the guard to either succeed or raise. Every transition also writes an
OrderEvent row, giving us a complete audit log for free.

State diagram:

    PENDING ──accept──> ACCEPTED ──start_prep──> PREPARING ──ship──> SHIPPED ──complete──> COMPLETED
       │                   │                        │
       │                   │                        │
       ├──reject──> REJECTED  (terminal)
       │
       └──cancel──> CANCELLED (terminal; also reachable from ACCEPTED/PREPARING)

Who can trigger what is enforced at the router layer (require_distributor for
accept/reject/prepare/ship/complete; require_pharmacy for cancel from
PENDING). The state machine itself just owns the *what's valid* question.
"""

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.models.order_event import OrderEvent


class InvalidTransition(Exception):
    """Raised when the requested transition isn't allowed from the current state."""


# Adjacency list. Edit here to evolve the FSM - nothing else changes.
ALLOWED_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.ACCEPTED, OrderStatus.REJECTED, OrderStatus.CANCELLED},
    OrderStatus.ACCEPTED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.COMPLETED},
    OrderStatus.REJECTED: set(),
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def transition(
    db: Session,
    order: Order,
    new_status: OrderStatus,
    actor_user_id: int,
    note: str | None = None,
) -> Order:
    """Apply a state transition and record an audit event.

    Caller is responsible for committing the session.
    """
    # SQLAlchemy loads the column as a plain string; coerce so the FSM can
    # work in enum-space regardless of how the order was constructed.
    current = order.status if isinstance(order.status, OrderStatus) else OrderStatus(order.status)
    if not can_transition(current, new_status):
        raise InvalidTransition(
            f"Cannot move order {order.id} from {current.value} to {new_status.value}"
        )

    event = OrderEvent(
        order_id=order.id,
        actor_user_id=actor_user_id,
        from_status=current.value,
        to_status=new_status.value,
        note=note,
    )
    order.status = new_status
    db.add(event)
    db.flush()
    return order
