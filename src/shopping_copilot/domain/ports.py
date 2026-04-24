"""Domain ports (Protocols). Framework-agnostic interfaces."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from shopping_copilot.domain.entities import Product
from shopping_copilot.domain.value_objects import Sku

# =====================================================================
# LLMPort
# =====================================================================


@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None


@runtime_checkable
class LLMPort(Protocol):
    """Generic LLM chat completion."""

    async def send_messages(
        self,
        messages: Sequence[LLMMessage],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        tools: Sequence[dict[str, Any]] | None = None,
    ) -> LLMResponse: ...


# =====================================================================
# EmbeddingsPort
# =====================================================================

Vector = list[float]
EmbeddingInputType = Literal["document", "query"]


@runtime_checkable
class EmbeddingsPort(Protocol):
    """Text → vector embedding."""

    @property
    def dimensions(self) -> int:
        """Dimensionality of produced vectors."""
        ...

    async def embed(
        self,
        texts: Sequence[str],
        *,
        input_type: EmbeddingInputType,
    ) -> list[Vector]: ...


# =====================================================================
# VectorStorePort
# =====================================================================


@dataclass(frozen=True, slots=True)
class VectorPoint:
    id: str
    vector: Vector
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SearchHit:
    id: str
    score: float
    payload: dict[str, Any]


@runtime_checkable
class VectorStorePort(Protocol):
    """Approximate nearest-neighbor store with metadata filters."""

    async def upsert(self, collection: str, points: Sequence[VectorPoint]) -> None: ...

    async def search(
        self,
        collection: str,
        query_vector: Vector,
        *,
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]: ...


# =====================================================================
# CatalogPort
# =====================================================================


@runtime_checkable
class CatalogPort(Protocol):
    """Transactional source of truth for the catalog."""

    async def get_product(self, sku: Sku) -> Product | None: ...

    async def find_products(
        self,
        *,
        skus: Sequence[Sku] | None = None,
        category: str | None = None,
        max_price_usd: float | None = None,
    ) -> list[Product]: ...

    async def skus_exist(self, skus: Sequence[Sku]) -> set[Sku]:
        """Return subset of `skus` that exist in the catalog."""
        ...
