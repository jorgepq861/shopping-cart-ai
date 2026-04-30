"""Seed the catalog with synthetic laptops using Haiku.

Usage:
    uv run python -m scripts.seed

Idempotent: re-running upserts by sku.
"""

from __future__ import annotations

import asyncio
import json
import re
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shopping_copilot.config import get_settings
from shopping_copilot.domain.ports import LLMMessage
from shopping_copilot.infrastructure.catalog.models import ProductRow
from shopping_copilot.infrastructure.llm.anthropic_adapter import AnthropicAdapter


class LaptopSpec(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    sku: str = Field(pattern=r"^LAP-\d{3}$")
    name: str
    brand: str
    description: str
    price_usd: float
    stock: int = Field(ge=0, le=50)
    rating_avg: float = Field(ge=0, le=5)
    specs: dict[str, str]


class LaptopList(BaseModel):
    items: list[LaptopSpec]


SYSTEM_PROMPT = """You are a data generator for a retail shopping assistant test catalog.
Produce realistic but fictional laptops with plausible specs.
Return ONLY valid JSON in this exact shape, with no preamble, no explanation, no markdown fences:
{"items": [ { ... }, ... ] }
"""

USER_PROMPT = """Generate exactly 20 laptops with:
- sku: "LAP-001" through "LAP-020" (unique)
- name, brand (mix: Lenovo, Apple, Dell, HP, Asus, Framework, Acer, Microsoft, Razer, LG)
- description: 1-2 sentences with key selling points
- price_usd: realistic range 500-2500
- stock: integer 0-30
- rating_avg: float 3.5-5.0
- specs: dict with keys like cpu, ram, storage, display, weight_kg

Return JSON: {"items": [ { ... }, ... ] }
"""


async def main() -> None:
    settings = get_settings()
    llm = AnthropicAdapter(
        api_key=settings.anthropic_api_key.get_secret_value(),
        model_sonnet=settings.llm_model_sonnet,
        model_haiku=settings.llm_model_haiku,
    )
    print("Requesting laptop catalog from Haiku...")
    resp = await llm.send_messages(
        [
            LLMMessage("system", SYSTEM_PROMPT),
            LLMMessage("user", USER_PROMPT),
        ],
        model=settings.llm_model_haiku,
        max_tokens=4096,
        temperature=0.7,
    )
    print(f"Tokens in={resp.input_tokens} out={resp.output_tokens}")

    data = json.loads(_extract_json(resp.content))
    parsed = LaptopList(**data)
    print(f"Parsed {len(parsed.items)} laptops.")

    engine = create_async_engine(settings.postgres_dsn)
    sf = async_sessionmaker(engine, expire_on_commit=False)
    async with sf() as s:
        for item in parsed.items:
            stmt = (
                insert(ProductRow)
                .values(
                    sku=item.sku,
                    name=item.name,
                    category="laptop",
                    brand=item.brand,
                    description=item.description,
                    price_amount=Decimal(str(round(item.price_usd, 2))),
                    price_currency="USD",
                    stock=item.stock,
                    rating_avg=item.rating_avg,
                    specs=item.specs,
                )
                .on_conflict_do_update(
                    index_elements=["sku"],
                    set_={
                        "name": item.name,
                        "description": item.description,
                        "price_amount": Decimal(str(round(item.price_usd, 2))),
                        "stock": item.stock,
                        "rating_avg": item.rating_avg,
                        "specs": item.specs,
                    },
                )
            )
            await s.execute(stmt)
        await s.commit()
    await engine.dispose()
    print("Seed done.")


def _extract_json(text: str) -> str:
    """Robustly extract a JSON object from an LLM response.
    Handles three failure modes:
      1. Wrapped in ```json ... ``` markdown fences.
      2. Wrapped in plain ``` ... ``` fences.
      3. Prose prefix ("Here is the JSON: { ... }").
    """
    text = text.strip()
    # Try fenced code block first
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    # Fall back to first {...} block
    obj = re.search(r"\{.*\}", text, re.DOTALL)
    if obj:
        return obj.group(0)
    # Last resort — return as-is, let json.loads explode with detail
    return text


if __name__ == "__main__":
    asyncio.run(main())
