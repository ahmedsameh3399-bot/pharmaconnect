"""Pharmacy profile: the buyer side of the marketplace."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    license_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)

    user: Mapped["User"] = relationship(back_populates="pharmacy")  # noqa: F821
    orders: Mapped[list["Order"]] = relationship(back_populates="pharmacy")  # noqa: F821
