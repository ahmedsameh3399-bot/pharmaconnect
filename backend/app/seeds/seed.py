"""Idempotent seed script.

Run with `python -m app.seeds.seed`. Safe to run repeatedly: it only inserts
rows that don't already exist. The Docker entrypoint runs this on every
backend startup so the demo always has data.
"""

import json
import random
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal
from app.models.distributor import Distributor
from app.models.medication import Medication
from app.models.offer import Offer
from app.models.pharmacy import Pharmacy
from app.models.user import User, UserRole
from app.security import hash_password

SEED_MEDICATIONS_PATH = Path(__file__).parent / "medications.json"

# Deterministic randomness so the demo looks the same every time it's built.
RNG = random.Random(42)

DEMO_PHARMACIES = [
    {"email": "alpha@pharma.local", "name": "Alpha Pharmacy", "license": "PH-1001"},
    {"email": "beta@pharma.local", "name": "Beta Pharmacy", "license": "PH-1002"},
]

DEMO_DISTRIBUTORS = [
    {"email": "ibnsina@dist.local", "company": "Ibn Sina Pharma", "license": "DS-2001"},
    {"email": "uniphar@dist.local", "company": "UniPhar", "license": "DS-2002"},
    {"email": "ediphar@dist.local", "company": "EgyPharma Dist.", "license": "DS-2003"},
    {"email": "midpharm@dist.local", "company": "Middle East Pharma", "license": "DS-2004"},
]

DEMO_ADMIN = {"email": "admin@pharma.local", "name": "System Admin", "password": "AdminPass123!"}
DEMO_USER_PASSWORD = "Pass1234!"


def _ensure_admin(db) -> None:
    if db.scalar(select(User).where(User.email == DEMO_ADMIN["email"])):
        return
    db.add(
        User(
            email=DEMO_ADMIN["email"],
            hashed_password=hash_password(DEMO_ADMIN["password"]),
            role=UserRole.ADMIN,
            full_name=DEMO_ADMIN["name"],
        )
    )


def _ensure_medications(db) -> list[Medication]:
    with SEED_MEDICATIONS_PATH.open() as f:
        records = json.load(f)
    existing = {m.name for m in db.scalars(select(Medication)).all()}
    for rec in records:
        if rec["name"] not in existing:
            db.add(Medication(**rec))
    db.flush()
    return list(db.scalars(select(Medication).order_by(Medication.id)).all())


def _ensure_pharmacies(db) -> list[Pharmacy]:
    pharmacies: list[Pharmacy] = []
    for spec in DEMO_PHARMACIES:
        user = db.scalar(select(User).where(User.email == spec["email"]))
        if not user:
            user = User(
                email=spec["email"],
                hashed_password=hash_password(DEMO_USER_PASSWORD),
                role=UserRole.PHARMACY,
                full_name=spec["name"] + " Owner",
            )
            db.add(user)
            db.flush()
            ph = Pharmacy(
                user_id=user.id,
                name=spec["name"],
                license_number=spec["license"],
                address="Cairo, Egypt",
                phone="+20-100-000-0000",
            )
            db.add(ph)
            db.flush()
            pharmacies.append(ph)
        else:
            pharmacies.append(user.pharmacy)  # type: ignore[arg-type]
    return pharmacies


def _ensure_distributors(db) -> list[Distributor]:
    distributors: list[Distributor] = []
    for spec in DEMO_DISTRIBUTORS:
        user = db.scalar(select(User).where(User.email == spec["email"]))
        if not user:
            user = User(
                email=spec["email"],
                hashed_password=hash_password(DEMO_USER_PASSWORD),
                role=UserRole.DISTRIBUTOR,
                full_name=spec["company"] + " Manager",
            )
            db.add(user)
            db.flush()
            dist = Distributor(
                user_id=user.id,
                company_name=spec["company"],
                license_number=spec["license"],
                address="Cairo, Egypt",
                phone="+20-200-000-0000",
            )
            db.add(dist)
            db.flush()
            distributors.append(dist)
        else:
            distributors.append(user.distributor)  # type: ignore[arg-type]
    return distributors


def _ensure_offers(db, distributors: list[Distributor], medications: list[Medication]) -> None:
    """Generate offers so each distributor carries most medications with
    randomized-but-deterministic prices, discounts, and stock."""
    for dist in distributors:
        for med in medications:
            # Each distributor randomly skips ~15% of medications, so the
            # comparison view actually has variance to show.
            if RNG.random() < 0.15:
                continue
            exists = db.scalar(
                select(Offer).where(
                    Offer.distributor_id == dist.id, Offer.medication_id == med.id
                )
            )
            if exists:
                continue
            base = RNG.uniform(15, 120)
            db.add(
                Offer(
                    distributor_id=dist.id,
                    medication_id=med.id,
                    unit_price=round(base, 2),
                    discount_percent=round(RNG.uniform(0, 25), 1),
                    stock=RNG.randint(0, 400),
                )
            )


def main() -> None:
    db = SessionLocal()
    try:
        _ensure_admin(db)
        meds = _ensure_medications(db)
        _ensure_pharmacies(db)
        distributors = _ensure_distributors(db)
        _ensure_offers(db, distributors, meds)
        db.commit()
        print(
            f"Seed complete: {len(meds)} medications, "
            f"{len(DEMO_PHARMACIES)} pharmacies, "
            f"{len(distributors)} distributors. "
            f"Default password for demo accounts: {DEMO_USER_PASSWORD} "
            f"(admin: {DEMO_ADMIN['password']})"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
