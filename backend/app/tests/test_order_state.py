"""FSM tests: every legal transition succeeds, every illegal one raises."""

import pytest

from app.models.distributor import Distributor
from app.models.order import Order, OrderStatus
from app.models.pharmacy import Pharmacy
from app.models.user import User, UserRole
from app.security import hash_password
from app.services.order_state import (
    ALLOWED_TRANSITIONS,
    InvalidTransition,
    can_transition,
    transition,
)


def _make_order(db) -> Order:
    pharma_user = User(email="p@x", hashed_password=hash_password("x"),
                       role=UserRole.PHARMACY, full_name="p")
    dist_user = User(email="d@x", hashed_password=hash_password("x"),
                     role=UserRole.DISTRIBUTOR, full_name="d")
    db.add_all([pharma_user, dist_user]); db.flush()
    ph = Pharmacy(user_id=pharma_user.id, name="p", license_number="L1",
                  address="a", phone="p")
    di = Distributor(user_id=dist_user.id, company_name="d", license_number="L2",
                     address="a", phone="p")
    db.add_all([ph, di]); db.flush()
    order = Order(pharmacy_id=ph.id, distributor_id=di.id,
                  status=OrderStatus.PENDING, total_amount=0)
    db.add(order); db.flush()
    return order


def test_terminal_states_have_no_transitions():
    for terminal in (OrderStatus.REJECTED, OrderStatus.COMPLETED, OrderStatus.CANCELLED):
        assert ALLOWED_TRANSITIONS[terminal] == set()


def test_happy_path_pending_to_completed(db):
    order = _make_order(db)
    for nxt in (OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.SHIPPED, OrderStatus.COMPLETED):
        transition(db, order, nxt, actor_user_id=1)
        assert order.status == nxt
    assert len(order.events) == 4


def test_illegal_transition_raises(db):
    order = _make_order(db)
    with pytest.raises(InvalidTransition):
        transition(db, order, OrderStatus.SHIPPED, actor_user_id=1)


def test_cancel_allowed_until_shipped(db):
    order = _make_order(db)
    transition(db, order, OrderStatus.ACCEPTED, actor_user_id=1)
    transition(db, order, OrderStatus.PREPARING, actor_user_id=1)
    transition(db, order, OrderStatus.CANCELLED, actor_user_id=1)
    assert order.status == OrderStatus.CANCELLED


def test_can_transition_helper():
    assert can_transition(OrderStatus.PENDING, OrderStatus.ACCEPTED)
    assert not can_transition(OrderStatus.PENDING, OrderStatus.SHIPPED)
    assert not can_transition(OrderStatus.COMPLETED, OrderStatus.PENDING)
