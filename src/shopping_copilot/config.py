"""Central configuration. All env vars flow through this module."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project-wide settings loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM providers
    anthropic_api_key: SecretStr
    openai_api_key: SecretStr | None = None
    voyage_api_key: SecretStr

    # Models
    llm_model_sonnet: str = "claude-sonnet-4-6"
    llm_model_haiku: str = "claude-haiku-4-5-20251001"
    embeddings_model: str = "voyage-3-lite"

    # LangSmith
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "shopping-copilot-dev"

    # Infra
    postgres_dsn: str
    postgres_test_dsn: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    # App
    app_env: Literal["dev", "ci", "prod"] = "dev"
    app_log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings accessor."""
    return Settings()
