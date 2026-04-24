"""Postgres adapter for CatalogPort."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shopping_copilot.domain.entities import Product
from shopping_copilot.domain.value_objects import Money, Sku
from shopping_copilot.infrastructure.catalog.models import ProductRow


def _row_to_product(row: ProductRow) -> Product:
    return Product(
        sku=Sku(row.sku),
        name=row.name,
        category=row.category,
        brand=row.brand,
        description=row.description,
        price=Money(Decimal(row.price_amount), row.price_currency),
        stock=row.stock,
        rating_avg=row.rating_avg,
        specs=dict(row.specs or {}),
    )


class PostgresCatalogAdapter:
    """Implements CatalogPort against Postgres via SQLAlchemy 2 async."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_product(self, sku: Sku) -> Product | None:
        async with self._sf() as session:
            row = await session.get(ProductRow, sku.value)
            return _row_to_product(row) if row else None

    async def find_products(
        self,
        *,
        skus: Sequence[Sku] | None = None,
        category: str | None = None,
        max_price_usd: float | None = None,
    ) -> list[Product]:
        async with self._sf() as session:
            stmt = select(ProductRow)
            if skus:
                stmt = stmt.where(ProductRow.sku.in_([s.value for s in skus]))
            if category:
                stmt = stmt.where(ProductRow.category == category)
            if max_price_usd is not None:
                stmt = stmt.where(ProductRow.price_amount <= Decimal(str(max_price_usd)))
            result = await session.scalars(stmt)
            return [_row_to_product(r) for r in result]

    async def skus_exist(self, skus: Sequence[Sku]) -> set[Sku]:
        if not skus:
            return set()
        async with self._sf() as session:
            stmt = select(ProductRow.sku).where(ProductRow.sku.in_([s.value for s in skus]))
            result = await session.scalars(stmt)
            return {Sku(s) for s in result.all()}
