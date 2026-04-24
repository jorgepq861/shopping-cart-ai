"""SQLAlchemy declarative models for the catalog."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import JSON, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class ProductRow(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(5000), nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    rating_avg: Mapped[float] = mapped_column(nullable=False, default=0.0)
    specs: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
