from __future__ import annotations

import json

import pytest
import respx
from httpx import Response

from shopping_copilot.domain.ports import LLMMessage
from shopping_copilot.infrastructure.llm.anthropic_adapter import AnthropicAdapter


@pytest.fixture
def adapter() -> AnthropicAdapter:
    return AnthropicAdapter(
        api_key="test-key",
        model_sonnet="claude-sonnet-4-6",
        model_haiku="claude-haiku-4-5-20251001",
    )


@pytest.mark.asyncio
async def test_send_messages_returns_response(adapter: AnthropicAdapter) -> None:
    payload = {
        "id": "msg_01",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-4-6",
        "content": [{"type": "text", "text": "Hola, Jorge."}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 15, "output_tokens": 5},
    }
    with respx.mock(base_url="https://api.anthropic.com") as mock:
        mock.post("/v1/messages").mock(return_value=Response(200, json=payload))
        result = await adapter.send_messages([LLMMessage("user", "Hola")])

    assert result.content == "Hola, Jorge."
    assert result.model == "claude-sonnet-4-6"
    assert result.input_tokens == 15
    assert result.output_tokens == 5
    assert result.stop_reason == "end_turn"


@pytest.mark.asyncio
async def test_send_messages_default_is_sonnet(adapter: AnthropicAdapter) -> None:
    captured: dict = {}
    with respx.mock(base_url="https://api.anthropic.com") as mock:

        def _handler(request):
            captured.update(json.loads(request.content))
            return Response(
                200,
                json={
                    "id": "m",
                    "type": "message",
                    "role": "assistant",
                    "model": "claude-sonnet-4-6",
                    "content": [{"type": "text", "text": "ok"}],
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                },
            )

        mock.post("/v1/messages").mock(side_effect=_handler)
        await adapter.send_messages([LLMMessage("user", "x")])

    assert captured["model"] == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_send_messages_can_select_haiku(adapter: AnthropicAdapter) -> None:
    captured: dict = {}
    with respx.mock(base_url="https://api.anthropic.com") as mock:

        def _handler(request):
            captured.update(json.loads(request.content))
            return Response(
                200,
                json={
                    "id": "m",
                    "type": "message",
                    "role": "assistant",
                    "model": "claude-haiku-4-5-20251001",
                    "content": [{"type": "text", "text": "ok"}],
                    "stop_reason": "end_turn",
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                },
            )

        mock.post("/v1/messages").mock(side_effect=_handler)
        await adapter.send_messages(
            [LLMMessage("user", "x")],
            model="claude-haiku-4-5-20251001",
        )

    assert captured["model"] == "claude-haiku-4-5-20251001"
