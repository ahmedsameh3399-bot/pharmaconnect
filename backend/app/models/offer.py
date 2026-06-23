"""Offer: a specific distributor's price/discount/stock for a specific medication.

This is the table the ranking algorithm operates on.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (
        # A distributor only has one offer per medication; updating an offer
        # mutates this row rather than inserting a new one.
        UniqueConstraint("distributor_id", "medication_id", name="uq_offer_distributor_med"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    distributor_id: Mapped[int] = mapped_column(
        ForeignKey("distributors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medication_id: Mapped[int] = mapped_column(
        ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Price per unit before discount (EGP). Float is fine for a demo; in
    # production money should be stored as Numeric(12,2) to avoid rounding.
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)

    # Discount percentage off the unit price. 0..100.
    discount_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Current available stock with this distributor.
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    distributor: Mapped["Distributor"] = relationship(back_populates="offers")  # noqa: F821
    medication: Mapped["Medication"] = relationship(back_populates="offers")  # noqa: F821

    @property
    def final_unit_price(self) -> float:
        """Unit price after the distributor's discount is applied."""
        return round(self.unit_price * (1 - self.discount_percent / 100.0), 2)
