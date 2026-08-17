from datetime import datetime, UTC
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    DateTime,
    Numeric,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.price_history import PriceHistory


class TrackedProduct(Base):
    __tablename__ = "tracked_products"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    target_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    current_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    created_at = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    last_checked = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    user: Mapped["User"] = relationship(
        back_populates="products"
    )

    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan"
    )

    last_alerted_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    last_alerted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    is_in_stock: Mapped[bool | None] = mapped_column(
        nullable=True
    )

    last_stock_alert_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )