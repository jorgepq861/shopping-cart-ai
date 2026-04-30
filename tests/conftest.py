"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shopping_copilot.config import get_settings


@pytest.fixture(scope="session")
def postgres_dsn() -> str:
    """Use the dedicated test DB to avoid touching dev/app data."""
    s = get_settings()
    if s.postgres_test_dsn:
        return s.postgres_test_dsn
    # Fallback: derive test DSN by replacing ONLY the path component
    # (str.replace would also clobber the username "shopping" -> "shopping_test").
    parsed = urlparse(s.postgres_dsn)
    return urlunparse(parsed._replace(path="/shopping_test"))


@pytest.fixture
async def engine(postgres_dsn: str) -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine(postgres_dsn, echo=False)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
