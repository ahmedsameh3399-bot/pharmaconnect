"""Distributor (pharmaceutical company) profile: the seller side."""

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Distributor(Base):
    __tablename__ = "distributors"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(160), nullable=False)
    license_number: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)

    # Reliability score is the running fraction of orders this distributor accepted
    # (vs rejected). It feeds into the ranking algorithm. Stored denormalized so
    # the ranking endpoint stays a simple SELECT and not a heavy aggregation per request.
    accepted_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_orders_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="distributor")  # noqa: F821
    offers: Mapped[list["Offer"]] = relationship(  # noqa: F821
        back_populates="distributor", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="distributor")  # noqa: F821

    @property
    def reliability_score(self) -> float:
        """Acceptance rate in [0, 1]. New distributors start neutral at 0.5 so
        they aren't penalised before having any history."""
        total = self.accepted_orders_count + self.rejected_orders_count
        if total == 0:
            return 0.5
        return self.accepted_orders_count / total
