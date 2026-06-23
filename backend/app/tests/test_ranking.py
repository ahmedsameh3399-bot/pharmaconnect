"""Worked-example tests for the best-offer ranking algorithm.

These tests double as the "show me your formula on the whiteboard" answer:
they encode concrete numerical scenarios and assert the expected ordering.
"""

import pytest

from app.models.distributor import Distributor
from app.models.medication import Medication
from app.models.offer import Offer
from app.models.user import User, UserRole
from app.security import hash_password
from app.services.ranking import W_PRICE, rank_offers_for_medication


def _make_distributor(db, name: str, accepted: int = 0, rejected: int = 0) -> Distributor:
    user = User(
        email=f"{name}@x.local", hashed_password=hash_password("x"),
        role=UserRole.DISTRIBUTOR, full_name=name,
    )
    db.add(user)
    db.flush()
    dist = Distributor(
        user_id=user.id, company_name=name, license_number=f"L-{name}",
        address="a", phone="p",
        accepted_orders_count=accepted, rejected_orders_count=rejected,
    )
    db.add(dist)
    db.flush()
    return dist


def test_cheapest_offer_ranks_first_when_stock_is_equal(db):
    med = Medication(name="Panadol", active_ingredient="Paracetamol",
                     form="Tablet", strength="500 mg", manufacturer="GSK")
    db.add(med); db.flush()

    cheap = _make_distributor(db, "cheap")
    expensive = _make_distributor(db, "expensive")
    db.add_all([
        Offer(distributor_id=cheap.id, medication_id=med.id, unit_price=10, stock=100),
        Offer(distributor_id=expensive.id, medication_id=med.id, unit_price=20, stock=100),
    ])
    db.flush()

    ranked = rank_offers_for_medication(db, med.id, requested_quantity=10)
    assert ranked[0].offer.distributor_id == cheap.id
    # Cheapest must score a perfect 1.0 on price.
    assert ranked[0].price_score == 1.0


def test_stock_score_degrades_when_request_exceeds_stock(db):
    """Stock score is linear in (stock / requested_quantity), capped at 1.0.
    This is what gives the algorithm awareness of order size."""
    med = Medication(name="X", active_ingredient="X", form="Tablet",
                     strength="1", manufacturer="m")
    db.add(med); db.flush()

    low_stock = _make_distributor(db, "low_stock")
    well_stocked = _make_distributor(db, "well_stocked")
    db.add_all([
        Offer(distributor_id=low_stock.id, medication_id=med.id, unit_price=10, stock=10),
        Offer(distributor_id=well_stocked.id, medication_id=med.id, unit_price=10, stock=500),
    ])
    db.flush()

    # Equal prices => the only differentiator is stock. Well-stocked must win.
    ranked = rank_offers_for_medication(db, med.id, requested_quantity=100)
    assert ranked[0].offer.distributor_id == well_stocked.id
    low_row = next(r for r in ranked if r.offer.distributor_id == low_stock.id)
    assert low_row.stock_score == 0.1  # 10/100


def test_reliability_breaks_a_tie_on_price_and_stock(db):
    med = Medication(name="Y", active_ingredient="Y", form="Tablet",
                     strength="1", manufacturer="m")
    db.add(med); db.flush()

    reliable = _make_distributor(db, "reliable", accepted=90, rejected=10)
    flaky = _make_distributor(db, "flaky", accepted=20, rejected=80)
    db.add_all([
        Offer(distributor_id=reliable.id, medication_id=med.id, unit_price=10, stock=100),
        Offer(distributor_id=flaky.id, medication_id=med.id, unit_price=10, stock=100),
    ])
    db.flush()

    ranked = rank_offers_for_medication(db, med.id, requested_quantity=10)
    assert ranked[0].offer.distributor_id == reliable.id


def test_no_offers_returns_empty(db):
    med = Medication(name="Z", active_ingredient="Z", form="Tablet",
                     strength="1", manufacturer="m")
    db.add(med); db.flush()
    assert rank_offers_for_medication(db, med.id) == []
