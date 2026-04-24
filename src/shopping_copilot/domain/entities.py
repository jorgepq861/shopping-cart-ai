"""Domain entities. Identity-based equality."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from shopping_copilot.domain.value_objects import Money, Sku

_MAX_RATING: Final = 5.0


@dataclass(eq=False, slots=True)
class Product:
    """Catalog product. Identity = sku."""

    sku: Sku
    name: str
    category: str
    brand: str
    description: str
    price: Money
    stock: int
    rating_avg: float
    specs: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.stock < 0:
            raise ValueError(f"Product stock cannot be negative, got {self.stock}")
        if not (0.0 <= self.rating_avg <= _MAX_RATING):
            raise ValueError(f"Product rating must be in [0, 5], got {self.rating_avg}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return self.sku == other.sku

    def __hash__(self) -> int:
        return hash(self.sku)
