from decimal import Decimal

import pytest

from shopping_copilot.domain.entities import Product
from shopping_copilot.domain.value_objects import Money, Sku


def _product(sku: str = "LAP-001", price: str = "1200") -> Product:
    return Product(
        sku=Sku(sku),
        name="ThinkPad X1",
        category="laptop",
        brand="Lenovo",
        description='Lightweight 14" ultrabook',
        price=Money(Decimal(price), "USD"),
        stock=5,
        rating_avg=4.5,
    )


class TestProduct:
    def test_product_can_be_constructed(self) -> None:
        p = _product()
        assert p.sku == Sku("LAP-001")
        assert p.price.amount == Decimal("1200")
        assert p.category == "laptop"

    def test_equality_by_sku(self) -> None:
        p1 = _product("LAP-001", "1200")
        p2 = _product("LAP-001", "1300")  # different price
        assert p1 == p2  # same sku → same entity

    def test_inequality_by_sku(self) -> None:
        assert _product("LAP-001") != _product("LAP-002")

    def test_hash_by_sku(self) -> None:
        p1, p2 = _product("LAP-001", "1200"), _product("LAP-001", "1300")
        assert {p1, p2} == {p1}

    def test_negative_stock_raises(self) -> None:
        with pytest.raises(ValueError, match="stock"):
            Product(
                sku=Sku("LAP-001"),
                name="x",
                category="laptop",
                brand="b",
                description="d",
                price=Money(Decimal("1"), "USD"),
                stock=-1,
                rating_avg=0,
            )

    def test_rating_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="rating"):
            Product(
                sku=Sku("LAP-001"),
                name="x",
                category="laptop",
                brand="b",
                description="d",
                price=Money(Decimal("1"), "USD"),
                stock=0,
                rating_avg=6,
            )
