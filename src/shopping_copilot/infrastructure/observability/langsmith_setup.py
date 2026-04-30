"""LangSmith configuration — env-var driven, zero-code."""

from __future__ import annotations

import os

from shopping_copilot.config import get_settings


def configure_langsmith() -> None:
    """Populate os.environ so langchain/langsmith pick up tracing settings.

    Call this ONCE at app startup, before any Anthropic/OpenAI client is created.
    """
    s = get_settings()
    os.environ["LANGSMITH_TRACING"] = "true" if s.langsmith_tracing else "false"
    os.environ["LANGSMITH_ENDPOINT"] = s.langsmith_endpoint
    if s.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = s.langsmith_api_key.get_secret_value()
    os.environ["LANGSMITH_PROJECT"] = s.langsmith_project
