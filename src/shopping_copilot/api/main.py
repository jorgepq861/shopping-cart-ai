"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from shopping_copilot.api.routers import chat, health
from shopping_copilot.infrastructure.observability.langsmith_setup import configure_langsmith


def create_app() -> FastAPI:
    configure_langsmith()
    app = FastAPI(
        title="Shopping Copilot",
        version="0.1.0",
        description="Retail agentic shopping assistant",
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    return app


app = create_app()
