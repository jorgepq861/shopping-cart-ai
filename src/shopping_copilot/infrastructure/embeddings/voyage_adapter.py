"""Voyage implementation of EmbeddingsPort."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import voyageai

from shopping_copilot.domain.ports import EmbeddingInputType, Vector


class VoyageAdapter:
    """Voyage AI embeddings — implements EmbeddingsPort."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimensions: int,
        _client: Any | None = None,
    ) -> None:
        self._model = model
        self._dimensions = dimensions
        # allow injection for tests
        self._client = _client or voyageai.AsyncClient(api_key=api_key)

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(
        self,
        texts: Sequence[str],
        *,
        input_type: EmbeddingInputType,
    ) -> list[Vector]:
        result = await self._client.embed(
            texts=list(texts),
            model=self._model,
            input_type=input_type,
        )
        return list(result.embeddings)
