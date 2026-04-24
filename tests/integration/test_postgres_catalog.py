from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shopping_copilot.domain.value_objects import Sku
from shopping_copilot.infrastructure.catalog.models import ProductRow
from shopping_copilot.infrastructure.catalog.postgres_catalog import PostgresCatalogAdapter


@pytest.fixture
async def _seed(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[None, None]:
    async with session_factory() as s:
        await s.execute(ProductRow.__table__.delete())
        s.add_all(
            [
                ProductRow(
                    sku="LAP-001",
                    name="ThinkPad X1",
                    category="laptop",
                    brand="Lenovo",
                    description='14" ultrabook',
                    price_amount=Decimal("1200"),
                    price_currency="USD",
                    stock=3,
                    rating_avg=4.5,
                    specs={"ram": "16GB"},
                ),
                ProductRow(
                    sku="LAP-002",
                    name="MacBook Air",
                    category="laptop",
                    brand="Apple",
                    description='13" M3',
                    price_amount=Decimal("1100"),
                    price_currency="USD",
                    stock=5,
                    rating_avg=4.8,
                    specs={"ram": "16GB"},
                ),
                ProductRow(
                    sku="PHN-001",
                    name="Pixel 8",
                    category="phone",
                    brand="Google",
                    description='6.2" phone',
                    price_amount=Decimal("699"),
                    price_currency="USD",
                    stock=10,
                    rating_avg=4.3,
                    specs={"storage": "128GB"},
                ),
            ]
        )
        await s.commit()
    yield
    async with session_factory() as s:
        await s.execute(ProductRow.__table__.delete())
        await s.commit()


@pytest.mark.asyncio
async def test_get_product_returns_entity(
    session_factory: async_sessionmaker[AsyncSession], _seed: None
) -> None:
    adapter = PostgresCatalogAdapter(session_factory)
    p = await adapter.get_product(Sku("LAP-001"))
    assert p is not None
    assert p.name == "ThinkPad X1"
    assert p.price.amount == Decimal("1200")


@pytest.mark.asyncio
async def test_get_product_missing_returns_none(
    session_factory: async_sessionmaker[AsyncSession], _seed: None
) -> None:
    adapter = PostgresCatalogAdapter(session_factory)
    p = await adapter.get_product(Sku("ZZZ-999"))
    assert p is None


@pytest.mark.asyncio
async def test_find_by_category_and_max_price(
    session_factory: async_sessionmaker[AsyncSession], _seed: None
) -> None:
    adapter = PostgresCatalogAdapter(session_factory)
    products = await adapter.find_products(category="laptop", max_price_usd=1150)
    assert {p.sku.value for p in products} == {"LAP-002"}


@pytest.mark.asyncio
async def test_skus_exist(session_factory: async_sessionmaker[AsyncSession], _seed: None) -> None:
    adapter = PostgresCatalogAdapter(session_factory)
    existing = await adapter.skus_exist([Sku("LAP-001"), Sku("ZZZ-000")])
    assert existing == {Sku("LAP-001")}
