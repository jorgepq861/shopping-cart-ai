"""Pure domain value objects. No framework dependencies."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

_SKU_RE: Final = re.compile(r"^[A-Z0-9]+(-[A-Z0-9]+)*$")
_ALLOWED_CURRENCICIES: Final = frozenset({"USD", "EUR", "MXN", "PEN", "COP"})


@dataclass(frozen=True, slots=True)
class Sku:
    """Stock Keeping Unit. Case-insensitive on construction, stored uppercase."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Sku cannot be empty")
        upper = self.value.upper()
        if not _SKU_RE.fullmatch(upper):
            raise ValueError(f"Invalid sku format: {self.value!r}")
        object.__setattr__(self, "value", upper)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Money:
    """Money with currency. Immutable. Decimal under the hood (no floats)."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Money.amount must be Decimal")
        if self.amount < 0:
            raise ValueError("Money cannot be negative")
        if self.currency not in _ALLOWED_CURRENCICIES:
            raise ValueError(f"Unsupported currency: {self.currency}")

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add different currencies: {self.currency} vs {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
