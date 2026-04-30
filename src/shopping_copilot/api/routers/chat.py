"""Minimal chat endpoint — single-turn echo via Claude (no agent yet)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from shopping_copilot.api.deps import get_llm
from shopping_copilot.api.schemas import ChatRequest, ChatResponse
from shopping_copilot.domain.ports import LLMMessage, LLMPort

router = APIRouter(prefix="/chat", tags=["chat"])

_SYSTEM_PROMPT = (
    "You are a friendly retail shopping assistant. "
    "Keep answers short and clear. "
    "You don't have access to the catalog yet; if asked about products, "
    "politely say the feature is coming in the next iteration."
)


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    llm: Annotated[LLMPort, Depends(get_llm)],
) -> ChatResponse:
    messages = [LLMMessage("system", _SYSTEM_PROMPT)] + [
        LLMMessage(role=m.role, content=m.content)  # type: ignore[arg-type]
        for m in body.messages
    ]
    result = await llm.send_messages(messages, max_tokens=512, temperature=0.3)
    return ChatResponse(
        content=result.content,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
