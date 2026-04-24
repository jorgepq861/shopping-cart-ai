from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from shopping_copilot.infrastructure.embeddings.voyage_adapter import VoyageAdapter


@pytest.fixture
def fake_client() -> MagicMock:
    c = MagicMock()
    c.embed = AsyncMock(return_value=MagicMock(embeddings=[[0.1] * 512, [0.2] * 512]))
    return c


@pytest.mark.asyncio
async def test_embed_documents_returns_vectors(fake_client: MagicMock) -> None:
    adapter = VoyageAdapter(
        api_key="test",
        model="voyage-3-lite",
        dimensions=512,
        _client=fake_client,
    )
    result = await adapter.embed(["laptop x1", "phone y2"], input_type="document")
    assert len(result) == 2
    assert len(result[0]) == 512
    fake_client.embed.assert_awaited_once_with(
        texts=["laptop x1", "phone y2"],
        model="voyage-3-lite",
        input_type="document",
    )


@pytest.mark.asyncio
async def test_embed_query_passes_input_type(fake_client: MagicMock) -> None:
    adapter = VoyageAdapter(
        api_key="test", model="voyage-3-lite", dimensions=512, _client=fake_client
    )
    await adapter.embed(["query text"], input_type="query")
    call = fake_client.embed.await_args.kwargs
    assert call["input_type"] == "query"


def test_dimensions_property() -> None:
    adapter = VoyageAdapter(
        api_key="test", model="voyage-3-lite", dimensions=512, _client=MagicMock()
    )
    assert adapter.dimensions == 512
