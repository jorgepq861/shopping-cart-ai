"""Anthropic implementation of LLMPort."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from anthropic import AsyncAnthropic
from langsmith.wrappers import wrap_anthropic

from shopping_copilot.domain.ports import LLMMessage, LLMResponse


class AnthropicAdapter:
    """Anthropic Claude — implements LLMPort."""

    def __init__(
        self,
        *,
        api_key: str,
        model_sonnet: str,
        model_haiku: str,
    ) -> None:
        self._client = wrap_anthropic(AsyncAnthropic(api_key=api_key))
        self._model_sonnet = model_sonnet
        self._model_haiku = model_haiku

    async def send_messages(
        self,
        messages: Sequence[LLMMessage],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        tools: Sequence[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        sys_prompt = next((m.content for m in messages if m.role == "system"), None)
        api_messages = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]
        kwargs: dict[str, Any] = {
            "model": model or self._model_sonnet,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": api_messages,
        }
        if sys_prompt is not None:
            kwargs["system"] = sys_prompt
        if tools:
            kwargs["tools"] = list(tools)

        resp = await self._client.messages.create(**kwargs)
        text_blocks = [block.text for block in resp.content if block.type == "text"]
        return LLMResponse(
            content="".join(text_blocks),
            model=resp.model,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            stop_reason=resp.stop_reason,
        )
