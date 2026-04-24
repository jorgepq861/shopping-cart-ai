from decimal import Decimal

import pytest

from shopping_copilot.domain.value_objects import Money, Sku


class TestSku:
    def test_valid_sku_is_accepted(self) -> None:
        s = Sku("LAP-001")
        assert s.value == "LAP-001"

    def test_sku_is_uppercased(self) -> None:
        s = Sku("lap-002")
        assert s.value == "LAP-002"

    def test_empty_sku_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            Sku("")

    def test_sku_with_invalid_chars_raises(self) -> None:
        with pytest.raises(ValueError, match="format"):
            Sku("LAP 001")  # spaces not allowed

    def test_sku_is_hashable(self) -> None:
        s1, s2 = Sku("LAP-001"), Sku("LAP-001")
        assert s1 == s2
        assert hash(s1) == hash(s2)
        assert {s1, s2} == {s1}


class TestMoney:
    def test_money_stores_decimal(self) -> None:
        m = Money(Decimal("19.99"), "USD")
        assert m.amount == Decimal("19.99")
        assert m.currency == "USD"

    def test_money_rejects_negative(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            Money(Decimal("-1"), "USD")

    def test_money_rejects_unknown_currency(self) -> None:
        with pytest.raises(ValueError, match="currency"):
            Money(Decimal("1"), "XYZ")

    def test_money_addition(self) -> None:
        a, b = Money(Decimal("10"), "USD"), Money(Decimal("5"), "USD")
        assert (a + b) == Money(Decimal("15"), "USD")

    def test_money_addition_different_currencies_raises(self) -> None:
        a, b = Money(Decimal("10"), "USD"), Money(Decimal("5"), "EUR")
        with pytest.raises(ValueError, match="currency"):
            _ = a + b

    def test_money_is_immutable(self) -> None:
        m = Money(Decimal("1"), "USD")
        with pytest.raises(AttributeError):
            m.amount = Decimal("2")  # type: ignore[misc]
