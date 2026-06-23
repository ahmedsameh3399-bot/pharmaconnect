"""Medication: the global, shared catalog row.

Multiple distributors can carry the same medication (each as an Offer). This
separation is what enables the comparison feature: search a medication once,
get every distributor's offer back.
"""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Commercial / brand name (e.g. "Panadol Extra"). Indexed for trigram search.
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # Active substance / INN (e.g. "Paracetamol"). The chatbot uses this to
    # find alternatives — "what else contains paracetamol?".
    active_ingredient: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # WHO ATC classification code (e.g. "N02BE01" for paracetamol). Optional,
    # used by the chatbot for higher-quality grouping when present.
    atc_code: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)

    # Pharmaceutical form (tablet, syrup, ointment...). Useful UI filter.
    form: Mapped[str] = mapped_column(String(60), nullable=False)

    strength: Mapped[str] = mapped_column(String(60), nullable=False)  # e.g. "500 mg"
    manufacturer: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    offers: Mapped[list["Offer"]] = relationship(back_populates="medication")  # noqa: F821
