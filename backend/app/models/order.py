"""Order and OrderItem models.

An Order is a single pharmacy buying from a single distributor. Multi-distributor
orders would force the pharmacy to manage N sub-orders manually, so we keep one
distributor per order — clean, defendable, matches every B2B catalog pattern.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class OrderStatus(str, Enum):
    """States of the order finite state machine.

    Valid transitions (enforced in services/order_state.py):
      PENDING   -> ACCEPTED, REJECTED, CANCELLED
      ACCEPTED  -> PREPARING, CANCELLED
      PREPARING -> SHIPPED, CANCELLED
      SHIPPED   -> COMPLETED
      REJECTED, COMPLETED, CANCELLED are terminal.
    """

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PREPARING = "PREPARING"
    SHIPPED = "SHIPPED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    pharmacy_id: Mapped[int] = mapped_column(
        ForeignKey("pharmacies.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    distributor_id: Mapped[int] = mapped_column(
        ForeignKey("distributors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        String(20), default=OrderStatus.PENDING, nullable=False, index=True
    )
    # Snapshot of the total at creation time so historical orders stay accurate
    # even if a distributor later changes their prices/discounts.
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)

    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    pharmacy: Mapped["Pharmacy"] = relationship(back_populates="orders")  # noqa: F821
    distributor: Mapped["Distributor"] = relationship(back_populates="orders")  # noqa: F821
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    events: Mapped[list["OrderEvent"]] = relationship(  # noqa: F821
        back_populates="order", cascade="all, delete-orphan", order_by="OrderEvent.created_at"
    )


class OrderItem(Base):
    """One medication line within an order, with snapshotted pricing."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    medication_id: Mapped[int] = mapped_column(
        ForeignKey("medications.id", ondelete="RESTRICT"), nullable=False
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Snapshotted at order-creation time. We do NOT recompute from the live
    # offer because the distributor might change discounts mid-order.
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    medication: Mapped["Medication"] = relationship()  # noqa: F821

    @property
    def line_total(self) -> float:
        return round(self.unit_price * (1 - self.discount_percent / 100.0) * self.quantity, 2)
