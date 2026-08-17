from datetime import datetime, UTC
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Numeric,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import TrackedProduct


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("tracked_products.id"),
        nullable=False
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    checked_at = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    product: Mapped["TrackedProduct"] = relationship(
        back_populates="price_history"
    )