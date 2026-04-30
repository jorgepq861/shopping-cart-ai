"""Dependency injection for FastAPI routes.

Routes depend on Ports (Protocols), not concrete adapters.
Swapping an adapter means changing only this file.
"""

from __future__ import annotations

from functools import lru_cache

from shopping_copilot.config import Settings, get_settings
from shopping_copilot.domain.ports import EmbeddingsPort, LLMPort
from shopping_copilot.infrastructure.embeddings.voyage_adapter import VoyageAdapter
from shopping_copilot.infrastructure.llm.anthropic_adapter import AnthropicAdapter


@lru_cache(maxsize=1)
def _build_llm(settings: Settings) -> LLMPort:
    return AnthropicAdapter(
        api_key=settings.anthropic_api_key.get_secret_value(),
        model_sonnet=settings.llm_model_sonnet,
        model_haiku=settings.llm_model_haiku,
    )


@lru_cache(maxsize=1)
def _build_embeddings(settings: Settings) -> EmbeddingsPort:
    return VoyageAdapter(
        api_key=settings.voyage_api_key.get_secret_value(),
        model=settings.embeddings_model,
        dimensions=512,
    )


def get_llm() -> LLMPort:
    return _build_llm(get_settings())


def get_embeddings() -> EmbeddingsPort:
    return _build_embeddings(get_settings())
