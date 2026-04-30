"""Pydantic DTOs for API I/O."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessageDto(BaseModel):
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessageDto] = Field(min_length=1)


class ChatResponse(BaseModel):
    content: str
    model: str
    input_tokens: int
    output_tokens: int
