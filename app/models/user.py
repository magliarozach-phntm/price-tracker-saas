from datetime import datetime, UTC
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import TrackedProduct


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    created_at = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    products: Mapped[list["TrackedProduct"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="America/New_York"
    )