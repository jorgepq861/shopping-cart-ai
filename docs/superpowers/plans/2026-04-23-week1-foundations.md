# Semana 1 — Fundaciones y primer flujo E2E trivial

> **Guía de implementación para Jorge.** Los steps usan checkboxes (`- [ ]`) para que marques progreso. Jorge escribe todo el código; Claude acompaña con explicaciones inline y revisión. Cross-ref: [`docs/progress/plan.html`](../../progress/plan.html) (tracker visual) y [spec](../specs/2026-04-23-retail-shopping-copilot-design.md).

**Goal:** Tener un agente conversacional *trivial* funcionando end-to-end — Streamlit → FastAPI → Claude → respuesta — con arquitectura Clean + puertos, infra local en Docker, y tracing verificado en LangSmith.

**Architecture:** Python 3.12 + uv + FastAPI async + Pydantic v2 + Clean Architecture con puertos (`Protocol`). Adaptadores `AnthropicAdapter`, `VoyageAdapter`, `PostgresCatalogAdapter`. Dominio puro sin dependencias externas. Streamlit como UI mínima.

**Tech Stack:** Python 3.12, uv, FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic, Ruff, mypy --strict, Docker Compose (Postgres 16 + Qdrant + Redis), Anthropic SDK, Voyage SDK, LangSmith (env-var tracing), Streamlit.

---

## Convenciones del plan

- **Cada Task** agrupa cambios que terminan en un commit coherente.
- **Cada Step** es atómico (2–5 min).
- Todos los comandos se ejecutan desde la raíz del proyecto `~/Documents/Jorge/Bayteq/source-code/agentic-ai` salvo indicación.
- **TDD estricto** en dominio y adaptadores (test rojo → implementación → test verde → commit).
- **Infra y setup** no van por TDD (no aplica) — se valida con comandos de verificación.
- **Claude explica el "por qué"** antes de cada bloque temático nuevo. Si no entiendes un concepto, **pausa y pregunta** antes de continuar.

---

## Tabla de contenido

| Task | Título | Concepto principal |
|---|---|---|
| 1 | Scaffold con uv + `.gitignore` + estructura | uv, pyproject.toml, Clean Arch dirs |
| 2 | Ruff + mypy --strict + pre-commit | linting unificado, type checking |
| 3 | Docker Compose (Postgres + Qdrant + Redis) + Makefile | infra local |
| 4 | Pydantic Settings + `.env.example` | 12-factor config |
| 5 | Value Objects (Sku, Money) con TDD | dominio puro, inmutabilidad |
| 6 | Entity Product + tests | DDD entities vs VOs |
| 7 | Puertos (LLMPort, EmbeddingsPort, VectorStorePort, CatalogPort) | Port/Adapter, `Protocol` |
| 8 | AnthropicAdapter con tests (respx mocked) | implementar puerto, tool calling |
| 9 | VoyageAdapter con tests | embeddings, input_type doc/query |
| 10 | SQLAlchemy 2 async + Alembic init | ORM async, migrations |
| 11 | Migración inicial: tabla `products` | Alembic versioning |
| 12 | PostgresCatalogAdapter implementando CatalogPort | adapter DB |
| 13 | Seed script: 20 laptops generadas por Haiku | structured output + Pydantic |
| 14 | FastAPI skeleton + `/health` | FastAPI async, OpenAPI |
| 15 | DI container (`deps.py`) + schemas Pydantic | Depends, DTOs |
| 16 | Endpoint `/chat` — echo con Claude | primer flujo E2E |
| 17 | UI Streamlit consumiendo `/chat` | chat_input, chat_message |
| 18 | LangSmith tracing verificado | env vars, zero-code tracing |
| 19 | GitHub Actions CI básica | lint + mypy + tests en PR |
| 20 | Review final Semana 1 | checklist de cierre |

---

## Task 1 — Scaffold con uv + `.gitignore` + estructura

**Concepto (explicar antes de arrancar):**

- **`uv`** es un package manager + virtualenv manager Rust-based. Reemplaza `pip`, `pip-tools`, `poetry`, `virtualenv`. Más rápido (10-100×), lockfile reproducible (`uv.lock`), simplifica todo.
- **Clean Architecture folders** — capas con dependencias hacia adentro: `domain` (núcleo), `application` (casos de uso), `agents` (orquestación), `infrastructure` (adaptadores), `api` (HTTP). Ningún módulo "arriba" importa de uno "más arriba".

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md` (mínimo)
- Create: estructura de carpetas bajo `src/shopping_copilot/` y `tests/`

- [x] **Step 1.1: Inicializar repo git**

```bash
cd ~/Documents/Jorge/Bayteq/source-code/agentic-ai
git init
git branch -m main
```

Verificar: `git status` dice "On branch main".

- [x] **Step 1.2: Crear `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
.eggs/
dist/
build/

# Virtualenv & uv
.venv/
.python-version

# IDEs
.vscode/
.idea/
*.swp
.DS_Store

# Env files
.env
.env.local
.env.*.local

# Docker
docker/.data/
docker/data/

# Test & coverage
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Logs
*.log

# Local notes
NOTES.md
scratch/
```

- [x] **Step 1.3: Instalar `uv` si no lo tienes**

```bash
which uv || curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verificar: `uv --version` imprime versión ≥ 0.4.

- [x] **Step 1.4: Crear `pyproject.toml` inicial**

```toml
[project]
name = "shopping-copilot"
version = "0.1.0"
description = "Retail shopping copilot — agentic AI learning project"
authors = [{ name = "Jorge Pareja", email = "claude1@bayteq.com" }]
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/shopping_copilot"]

[dependency-groups]
dev = [
  "pytest>=8.0",
  "pytest-asyncio>=0.23",
  "pytest-cov>=5.0",
  "ruff>=0.6",
  "mypy>=1.11",
  "pre-commit>=3.8",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-ra --strict-markers"
```

- [x] **Step 1.5: Crear estructura de carpetas**

```bash
mkdir -p src/shopping_copilot/{domain,application,agents,infrastructure/{llm,embeddings,catalog,observability},api/routers,observability,guardrails} \
         tests/{unit/domain,unit/application,integration,contracts} \
         scripts ui docker migrations/versions docs/{progress,superpowers/plans,superpowers/specs,learning-journal}

# archivos __init__.py vacíos para que Python reconozca los paquetes
find src tests -type d -exec touch {}/__init__.py \;
```

Verificar: `ls src/shopping_copilot/domain/` devuelve `__init__.py`.

- [x] **Step 1.6: Crear README.md mínimo**

```markdown
# Shopping Copilot

Retail agentic-AI learning project. See [spec](docs/superpowers/specs/2026-04-23-retail-shopping-copilot-design.md).

## Quickstart

```bash
uv sync
cp .env.example .env
make up
uv run streamlit run ui/app.py
```
```

- [x] **Step 1.7: Sincronizar dependencias de dev**

```bash
uv sync
```

Verificar:
- Se crea `.venv/` (ignorado por git).
- Se crea `uv.lock`.
- `uv run pytest --version` responde `pytest 8.x`.

- [x] **Step 1.8: Commit**

```bash
git add pyproject.toml .gitignore README.md src tests scripts ui docker migrations docs uv.lock
git commit -m "chore: bootstrap project with uv + Clean Arch scaffolding"
```

---

## Task 2 — Ruff + mypy --strict + pre-commit

**Concepto:**

- **Ruff** = formatter + linter + import sorter en un solo binario. Drop-in replacement de Black. Configuración en `pyproject.toml`.
- **mypy --strict** — type checker. `--strict` activa todos los flags (`disallow_untyped_defs`, `no_implicit_optional`, etc.). Obliga a tipar **todo**. Es clave en proyectos con LLM porque los outputs estructurados dependen de tipos.
- **pre-commit** — corre checks antes de cada commit. Evita commits con lint/type/test rotos.

**Files:**
- Modify: `pyproject.toml` (añadir secciones `[tool.ruff]` y `[tool.mypy]`)
- Create: `.pre-commit-config.yaml`

- [x] **Step 2.1: Añadir configuración Ruff a `pyproject.toml`**

Al final de `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]

[tool.ruff.lint]
select = [
  "E",    # pycodestyle errors
  "W",    # pycodestyle warnings
  "F",    # pyflakes
  "I",    # isort
  "B",    # flake8-bugbear
  "C4",   # flake8-comprehensions
  "UP",   # pyupgrade
  "SIM",  # flake8-simplify
  "RUF",  # ruff-specific
  "N",    # pep8-naming
  "PL",   # pylint
  # "TCH" intencionalmente excluido: choca con Pydantic/SQLAlchemy/FastAPI
  # (sus anotaciones se resuelven en runtime, no solo para el type checker)
]
ignore = ["PLR0913"]  # too many arguments — a veces inevitable en handlers

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["PLR2004"]   # magic values in tests están bien

[tool.ruff.format]
quote-style = "double"
```

- [x] **Step 2.2: Añadir configuración mypy a `pyproject.toml`**

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
warn_unused_ignores = true
plugins = ["pydantic.mypy"]
exclude = ["migrations/"]

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false  # tests pueden tener fixtures sin tipar
```

- [x] **Step 2.3: Crear `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff-check
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=500]

  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy src
        language: system
        types: [python]
        pass_filenames: false
```

- [x] **Step 2.4: Instalar los hooks**

```bash
uv run pre-commit install
```

Verificar: `.git/hooks/pre-commit` existe.

- [x] **Step 2.5: Correr Ruff sobre el repo vacío (debe pasar)**

```bash
uv run ruff check .
uv run ruff format --check .
```

Expected: ambos salen sin errores (no hay código aún).

- [x] **Step 2.6: Commit**

```bash
git add pyproject.toml .pre-commit-config.yaml
git commit -m "chore: configure ruff, mypy --strict, and pre-commit"
```

---

## Task 3 — Docker Compose (Postgres + Qdrant + Redis) + Makefile

**Concepto:**

- **Docker Compose** levanta los servicios de infra locales con un comando. Evita instalar Postgres/Qdrant en tu máquina.
- **Postgres 16** — catálogo, órdenes, checkpointer LangGraph.
- **Qdrant** — vector store (aunque en Semana 1 aún no lo usamos, lo dejamos listo).
- **Redis** — carrito efímero, cache.
- **Makefile** — atajos para comandos comunes (`make up`, `make down`, `make logs`).

**Files:**
- Create: `docker/docker-compose.yml`
- Create: `Makefile`

- [x] **Step 3.1: Crear `docker/docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: sc-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: shopping
      POSTGRES_PASSWORD: shopping
      POSTGRES_DB: shopping
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U shopping"]
      interval: 5s
      timeout: 5s
      retries: 10

  qdrant:
    image: qdrant/qdrant:v1.12.0
    container_name: sc-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"  # REST
      - "6334:6334"  # gRPC
    volumes:
      - qdrant-data:/qdrant/storage
    healthcheck:
      test: ["CMD-SHELL", "bash -c ':> /dev/tcp/127.0.0.1/6333' || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: sc-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres-data:
  qdrant-data:
  redis-data:
```

- [x] **Step 3.2: Crear `Makefile`**

```make
.PHONY: up down restart logs reset psql redis-cli qdrant-ui install fmt lint typecheck test ci

up:
	docker compose -f docker/docker-compose.yml up -d

down:
	docker compose -f docker/docker-compose.yml down

restart: down up

logs:
	docker compose -f docker/docker-compose.yml logs -f

reset:
	docker compose -f docker/docker-compose.yml down -v
	docker compose -f docker/docker-compose.yml up -d

psql:
	docker exec -it sc-postgres psql -U shopping -d shopping

redis-cli:
	docker exec -it sc-redis redis-cli

qdrant-ui:
	@echo "Open http://localhost:6333/dashboard"

install:
	uv sync

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy src

test:
	uv run pytest -v

ci: lint typecheck test
```

- [x] **Step 3.3: Levantar la infra**

```bash
make up
```

Verificar (paciencia 10–20 seg al primer arranque):

```bash
docker compose -f docker/docker-compose.yml ps
```

Debe mostrar `postgres`, `qdrant`, `redis` todos `healthy`.

- [x] **Step 3.4: Verificar Qdrant**

Abrir http://localhost:6333/dashboard — debe cargar la UI web de Qdrant. Esta UI la vas a usar en Semana 2 para inspeccionar colecciones.

- [x] **Step 3.5: Verificar Postgres**

```bash
make psql
# dentro: \l  (listar DBs) → debe aparecer "shopping". \q para salir.
```

- [x] **Step 3.6: Commit**

```bash
git add docker/docker-compose.yml Makefile
git commit -m "infra: add docker compose (postgres + qdrant + redis) and Makefile"
```

---

## Task 4 — Pydantic Settings + `.env.example`

**Concepto:**

- **pydantic-settings** — lee variables de entorno o `.env` y las **valida con tipos**. Es el estándar Python para 12-factor config. Alternativa a `os.environ["..."]` pero tipado y con defaults.
- Regla: **todas** las configuraciones del proyecto (API keys, URLs, modelos, flags) pasan por aquí. Nunca hardcodes en código.

**Files:**
- Create: `.env.example`
- Create: `src/shopping_copilot/config.py`
- Modify: `pyproject.toml` (añadir dependencia)

- [x] **Step 4.1: Añadir `pydantic-settings` como dependencia principal**

```bash
uv add "pydantic>=2.9" "pydantic-settings>=2.5"
```

Esto actualiza `pyproject.toml` y `uv.lock`.

- [x] **Step 4.2: Crear `.env.example`**

```bash
# === LLM providers ===
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
VOYAGE_API_KEY=pa-xxx

# === Modelos ===
LLM_MODEL_SONNET=claude-sonnet-4-6
LLM_MODEL_HAIKU=claude-haiku-4-5-20251001
EMBEDDINGS_MODEL=voyage-3-lite

# === LangSmith (tracing) ===
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=lsv2_xxx
LANGCHAIN_PROJECT=shopping-copilot-dev

# === Infra local ===
POSTGRES_DSN=postgresql+asyncpg://shopping:shopping@localhost:5432/shopping
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# === App ===
APP_ENV=dev
APP_LOG_LEVEL=INFO
```

- [x] **Step 4.3: Crear `src/shopping_copilot/config.py`**

```python
"""Central configuration. All env vars flow through this module."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
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
    langchain_tracing_v2: bool = False
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: SecretStr | None = None
    langchain_project: str = "shopping-copilot-dev"

    # Infra
    postgres_dsn: str
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"

    # App
    app_env: Literal["dev", "ci", "prod"] = "dev"
    app_log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings accessor."""
    return Settings()  # type: ignore[call-arg]
```

- [x] **Step 4.4: Crear tu `.env` real (sin commit)**

```bash
cp .env.example .env
```

Editar `.env` y completar **solo** lo que ya tienes (Anthropic/OpenAI/Voyage/LangSmith si ya creaste las cuentas). Si aún no tienes las keys, déjalas como `xxx` — las llenarás en la Task 8.

- [x] **Step 4.5: Test rápido de config**

```bash
uv run python -c "from shopping_copilot.config import get_settings; s = get_settings(); print('env:', s.app_env); print('project:', s.langchain_project)"
```

Expected: imprime `env: dev` y el nombre del proyecto.

- [x] **Step 4.6: Commit**

```bash
git add pyproject.toml uv.lock .env.example src/shopping_copilot/config.py
git commit -m "feat(config): pydantic-settings with .env.example"
```

---

## Task 5 — Value Objects (Sku, Money) con TDD

**Concepto:**

- **Value Object (VO)** — objeto inmutable definido por sus atributos (no por identidad). Dos `Sku("LAP-001")` son el mismo VO. Se usan para encapsular reglas de validación y evitar "primitive obsession" (pasar strings crudos por todos lados).
- **TDD (Test-Driven Development):** escribes el test *primero*, verificas que falla, escribes la implementación mínima, verificas que pasa, refactorizas. Aplica perfecto a VOs porque son puros.

**Files:**
- Create: `src/shopping_copilot/domain/value_objects.py`
- Create: `tests/unit/domain/test_value_objects.py`

- [x] **Step 5.1: Escribir tests (rojo)**

`tests/unit/domain/test_value_objects.py`:

```python
from decimal import Decimal

import pytest

from shopping_copilot.domain.value_objects import Money, Sku


class TestSku:
    def test_valid_sku_is_accepted(self) -> None:
        s = Sku("LAP-001")
        assert s.value == "LAP-001"

    def test_sku_is_uppercased(self) -> None:
        s = Sku("lap-002")
        assert s.value == "LAP-002"

    def test_empty_sku_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            Sku("")

    def test_sku_with_invalid_chars_raises(self) -> None:
        with pytest.raises(ValueError, match="format"):
            Sku("LAP 001")  # spaces not allowed

    def test_sku_is_hashable(self) -> None:
        s1, s2 = Sku("LAP-001"), Sku("LAP-001")
        assert s1 == s2
        assert hash(s1) == hash(s2)
        assert {s1, s2} == {s1}


class TestMoney:
    def test_money_stores_decimal(self) -> None:
        m = Money(Decimal("19.99"), "USD")
        assert m.amount == Decimal("19.99")
        assert m.currency == "USD"

    def test_money_rejects_negative(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            Money(Decimal("-1"), "USD")

    def test_money_rejects_unknown_currency(self) -> None:
        with pytest.raises(ValueError, match="currency"):
            Money(Decimal("1"), "XYZ")

    def test_money_addition(self) -> None:
        a, b = Money(Decimal("10"), "USD"), Money(Decimal("5"), "USD")
        assert (a + b) == Money(Decimal("15"), "USD")

    def test_money_addition_different_currencies_raises(self) -> None:
        a, b = Money(Decimal("10"), "USD"), Money(Decimal("5"), "EUR")
        with pytest.raises(ValueError, match="currency"):
            _ = a + b

    def test_money_is_immutable(self) -> None:
        m = Money(Decimal("1"), "USD")
        with pytest.raises(AttributeError):
            m.amount = Decimal("2")  # type: ignore[misc]
```

- [x] **Step 5.2: Correr los tests (deben fallar)**

```bash
uv run pytest tests/unit/domain/test_value_objects.py -v
```

Expected: `ModuleNotFoundError: No module named 'shopping_copilot.domain.value_objects'`.

- [x] **Step 5.3: Implementar `value_objects.py`**

```python
"""Pure domain value objects. No framework dependencies."""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

_SKU_RE: Final = re.compile(r"^[A-Z0-9]+(-[A-Z0-9]+)*$")
_ALLOWED_CURRENCIES: Final = frozenset({"USD", "EUR", "MXN", "PEN", "COP"})


@dataclass(frozen=True, slots=True)
class Sku:
    """Stock Keeping Unit. Case-insensitive on construction, stored uppercase."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Sku cannot be empty")
        upper = self.value.upper()
        if not _SKU_RE.fullmatch(upper):
            raise ValueError(f"Invalid sku format: {self.value!r}")
        object.__setattr__(self, "value", upper)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Money:
    """Money with currency. Immutable. Decimal under the hood (no floats)."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.amount, Decimal):
            raise TypeError("Money.amount must be Decimal")
        if self.amount < 0:
            raise ValueError("Money cannot be negative")
        if self.currency not in _ALLOWED_CURRENCIES:
            raise ValueError(f"Unsupported currency: {self.currency}")

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add different currencies: {self.currency} vs {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
```

- [x] **Step 5.4: Correr tests (deben pasar)**

```bash
uv run pytest tests/unit/domain/test_value_objects.py -v
```

Expected: **11 passed**.

- [x] **Step 5.5: Typecheck**

```bash
uv run mypy src/shopping_copilot/domain
```

Expected: `Success: no issues found`.

- [x] **Step 5.6: Commit**

```bash
git add src/shopping_copilot/domain/value_objects.py tests/unit/domain/test_value_objects.py
git commit -m "feat(domain): Sku and Money value objects with TDD"
```

---

## Task 6 — Entity Product + tests

**Concepto:**

- **Entity** — tiene identidad (SKU). Dos productos con el mismo SKU son el mismo, aunque sus specs difieran. A diferencia del VO (definido por valor), la entity se define por su ID.
- Dataclass con `eq=False` + `__eq__` por identidad.

**Files:**
- Create: `src/shopping_copilot/domain/entities.py`
- Create: `tests/unit/domain/test_entities.py`

- [ ] **Step 6.1: Escribir tests (rojo)**

`tests/unit/domain/test_entities.py`:

```python
from decimal import Decimal

from shopping_copilot.domain.entities import Product
from shopping_copilot.domain.value_objects import Money, Sku


def _product(sku: str = "LAP-001", price: str = "1200") -> Product:
    return Product(
        sku=Sku(sku),
        name="ThinkPad X1",
        category="laptop",
        brand="Lenovo",
        description="Lightweight 14\" ultrabook",
        price=Money(Decimal(price), "USD"),
        stock=5,
        rating_avg=4.5,
    )


class TestProduct:
    def test_product_can_be_constructed(self) -> None:
        p = _product()
        assert p.sku == Sku("LAP-001")
        assert p.price.amount == Decimal("1200")
        assert p.category == "laptop"

    def test_equality_by_sku(self) -> None:
        p1 = _product("LAP-001", "1200")
        p2 = _product("LAP-001", "1300")  # different price
        assert p1 == p2  # same sku → same entity

    def test_inequality_by_sku(self) -> None:
        assert _product("LAP-001") != _product("LAP-002")

    def test_hash_by_sku(self) -> None:
        p1, p2 = _product("LAP-001", "1200"), _product("LAP-001", "1300")
        assert {p1, p2} == {p1}

    def test_negative_stock_raises(self) -> None:
        import pytest
        with pytest.raises(ValueError, match="stock"):
            Product(
                sku=Sku("LAP-001"),
                name="x",
                category="laptop",
                brand="b",
                description="d",
                price=Money(Decimal("1"), "USD"),
                stock=-1,
                rating_avg=0,
            )

    def test_rating_out_of_range_raises(self) -> None:
        import pytest
        with pytest.raises(ValueError, match="rating"):
            Product(
                sku=Sku("LAP-001"),
                name="x",
                category="laptop",
                brand="b",
                description="d",
                price=Money(Decimal("1"), "USD"),
                stock=0,
                rating_avg=6,
            )
```

- [ ] **Step 6.2: Correr tests (deben fallar)**

```bash
uv run pytest tests/unit/domain/test_entities.py -v
```

Expected: import error.

- [ ] **Step 6.3: Implementar `entities.py`**

```python
"""Domain entities. Identity-based equality."""
from __future__ import annotations

from dataclasses import dataclass, field

from shopping_copilot.domain.value_objects import Money, Sku


@dataclass(eq=False, slots=True)
class Product:
    """Catalog product. Identity = sku."""

    sku: Sku
    name: str
    category: str
    brand: str
    description: str
    price: Money
    stock: int
    rating_avg: float
    specs: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.stock < 0:
            raise ValueError(f"Product stock cannot be negative, got {self.stock}")
        if not (0.0 <= self.rating_avg <= 5.0):
            raise ValueError(
                f"Product rating must be in [0, 5], got {self.rating_avg}"
            )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Product):
            return NotImplemented
        return self.sku == other.sku

    def __hash__(self) -> int:
        return hash(self.sku)
```

- [ ] **Step 6.4: Correr tests (deben pasar)**

```bash
uv run pytest tests/unit/domain/ -v
```

Expected: **17 passed** (11 del Task 5 + 6 nuevos).

- [ ] **Step 6.5: Commit**

```bash
git add src/shopping_copilot/domain/entities.py tests/unit/domain/test_entities.py
git commit -m "feat(domain): Product entity with identity-based equality"
```

---

## Task 7 — Puertos (LLMPort, EmbeddingsPort, VectorStorePort, CatalogPort)

**Concepto:**

- **Port** = **interface** (en Python, usualmente `Protocol` structural). Define **qué** hace algo, no **cómo**.
- `Protocol` structural (PEP 544) no requiere herencia explícita — cualquier clase con los métodos correctos "implementa" el protocolo. Más Pythonic que ABC.
- Los puertos viven en `domain/` y no importan nada de frameworks. Esto es lo que hace "swappable" al proveedor.

**Files:**
- Create: `src/shopping_copilot/domain/ports.py`

- [ ] **Step 7.1: Crear `ports.py`**

```python
"""Domain ports (Protocols). Framework-agnostic interfaces."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from shopping_copilot.domain.entities import Product
from shopping_copilot.domain.value_objects import Sku

# =====================================================================
# LLMPort
# =====================================================================

@dataclass(frozen=True, slots=True)
class LLMMessage:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None


@runtime_checkable
class LLMPort(Protocol):
    """Generic LLM chat completion."""

    async def send_messages(
        self,
        messages: Sequence[LLMMessage],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        tools: Sequence[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        ...


# =====================================================================
# EmbeddingsPort
# =====================================================================

Vector = list[float]
EmbeddingInputType = Literal["document", "query"]


@runtime_checkable
class EmbeddingsPort(Protocol):
    """Text → vector embedding."""

    @property
    def dimensions(self) -> int:
        """Dimensionality of produced vectors."""
        ...

    async def embed(
        self,
        texts: Sequence[str],
        *,
        input_type: EmbeddingInputType,
    ) -> list[Vector]:
        ...


# =====================================================================
# VectorStorePort
# =====================================================================

@dataclass(frozen=True, slots=True)
class VectorPoint:
    id: str
    vector: Vector
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SearchHit:
    id: str
    score: float
    payload: dict[str, Any]


@runtime_checkable
class VectorStorePort(Protocol):
    """Approximate nearest-neighbor store with metadata filters."""

    async def upsert(self, collection: str, points: Sequence[VectorPoint]) -> None:
        ...

    async def search(
        self,
        collection: str,
        query_vector: Vector,
        *,
        k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        ...


# =====================================================================
# CatalogPort
# =====================================================================

@runtime_checkable
class CatalogPort(Protocol):
    """Transactional source of truth for the catalog."""

    async def get_product(self, sku: Sku) -> Product | None:
        ...

    async def find_products(
        self,
        *,
        skus: Sequence[Sku] | None = None,
        category: str | None = None,
        max_price_usd: float | None = None,
    ) -> list[Product]:
        ...

    async def skus_exist(self, skus: Sequence[Sku]) -> set[Sku]:
        """Return subset of `skus` that exist in the catalog."""
        ...
```

- [ ] **Step 7.2: Typecheck**

```bash
uv run mypy src/shopping_copilot/domain
```

Expected: `Success`.

- [ ] **Step 7.3: Smoke test — el módulo se importa**

```bash
uv run python -c "from shopping_copilot.domain.ports import LLMPort, EmbeddingsPort, VectorStorePort, CatalogPort; print('ports ok')"
```

Expected: `ports ok`.

- [ ] **Step 7.4: Commit**

```bash
git add src/shopping_copilot/domain/ports.py
git commit -m "feat(domain): ports (LLM, Embeddings, VectorStore, Catalog)"
```

---

## Task 8 — AnthropicAdapter con tests (respx mocked)

**Concepto:**

- **Adapter** = implementación concreta de un puerto. Vive en `infrastructure/`.
- **respx** — mockea HTTP de `httpx` (lo que usa el SDK de Anthropic). Nos permite testear el adaptador sin llamar al API real (ni gastar tokens).
- **Tool calling** aún no — en Semana 1 solo mandamos mensajes y recibimos texto.

**Files:**
- Create: `src/shopping_copilot/infrastructure/llm/anthropic_adapter.py`
- Create: `tests/unit/infrastructure/test_anthropic_adapter.py`
- Modify: `pyproject.toml` (agregar `anthropic` + `respx`)

- [ ] **Step 8.1: Añadir dependencias**

```bash
uv add anthropic
uv add --dev respx
```

- [ ] **Step 8.2: Crear carpeta de test y `__init__.py`**

```bash
mkdir -p tests/unit/infrastructure
touch tests/unit/infrastructure/__init__.py
```

- [ ] **Step 8.3: Escribir tests (rojo)**

`tests/unit/infrastructure/test_anthropic_adapter.py`:

```python
from __future__ import annotations

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
            import json
            captured.update(json.loads(request.content))
            return Response(200, json={
                "id": "m", "type": "message", "role": "assistant",
                "model": "claude-sonnet-4-6",
                "content": [{"type": "text", "text": "ok"}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            })
        mock.post("/v1/messages").mock(side_effect=_handler)
        await adapter.send_messages([LLMMessage("user", "x")])

    assert captured["model"] == "claude-sonnet-4-6"


@pytest.mark.asyncio
async def test_send_messages_can_select_haiku(adapter: AnthropicAdapter) -> None:
    captured: dict = {}
    with respx.mock(base_url="https://api.anthropic.com") as mock:
        def _handler(request):
            import json
            captured.update(json.loads(request.content))
            return Response(200, json={
                "id": "m", "type": "message", "role": "assistant",
                "model": "claude-haiku-4-5-20251001",
                "content": [{"type": "text", "text": "ok"}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            })
        mock.post("/v1/messages").mock(side_effect=_handler)
        await adapter.send_messages(
            [LLMMessage("user", "x")],
            model="claude-haiku-4-5-20251001",
        )

    assert captured["model"] == "claude-haiku-4-5-20251001"
```

- [ ] **Step 8.4: Correr tests (rojo)**

```bash
uv run pytest tests/unit/infrastructure/test_anthropic_adapter.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 8.5: Implementar `anthropic_adapter.py`**

`src/shopping_copilot/infrastructure/llm/anthropic_adapter.py`:

```python
"""Anthropic implementation of LLMPort."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from anthropic import AsyncAnthropic

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
        self._client = AsyncAnthropic(api_key=api_key)
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
        sys_prompt = next(
            (m.content for m in messages if m.role == "system"), None
        )
        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
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

        text_blocks = [
            block.text for block in resp.content if block.type == "text"
        ]
        return LLMResponse(
            content="".join(text_blocks),
            model=resp.model,
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
            stop_reason=resp.stop_reason,
        )
```

- [ ] **Step 8.6: Correr tests (deben pasar)**

```bash
uv run pytest tests/unit/infrastructure/test_anthropic_adapter.py -v
```

Expected: **3 passed**.

- [ ] **Step 8.7: Typecheck**

```bash
uv run mypy src/shopping_copilot/infrastructure
```

Expected: `Success`.

- [ ] **Step 8.8: Commit**

```bash
git add src/shopping_copilot/infrastructure/llm/anthropic_adapter.py tests/unit/infrastructure/test_anthropic_adapter.py pyproject.toml uv.lock
git commit -m "feat(infra): AnthropicAdapter implementing LLMPort + respx tests"
```

---

## Task 9 — VoyageAdapter con tests

**Concepto:**

- **Embeddings** = convertir texto a un vector denso (lista de floats). Voyage `voyage-3-lite` produce vectores de 512 dimensiones. No los usamos todavía para RAG en Semana 1, pero el adapter queda listo.
- **`input_type`** — Voyage distingue al embbedar entre `document` (al indexar) y `query` (al consultar). Mejora el recall notablemente. Parámetro crítico.

**Files:**
- Create: `src/shopping_copilot/infrastructure/embeddings/voyage_adapter.py`
- Create: `tests/unit/infrastructure/test_voyage_adapter.py`
- Modify: `pyproject.toml` (agregar `voyageai`)

- [ ] **Step 9.1: Añadir dependencia**

```bash
uv add voyageai
```

- [ ] **Step 9.2: Escribir tests (rojo)**

`tests/unit/infrastructure/test_voyage_adapter.py`:

```python
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from shopping_copilot.infrastructure.embeddings.voyage_adapter import VoyageAdapter


@pytest.fixture
def fake_client() -> MagicMock:
    c = MagicMock()
    c.embed = AsyncMock(
        return_value=MagicMock(embeddings=[[0.1] * 512, [0.2] * 512])
    )
    return c


@pytest.mark.asyncio
async def test_embed_documents_returns_vectors(fake_client: MagicMock) -> None:
    adapter = VoyageAdapter(
        api_key="test",
        model="voyage-3-lite",
        dimensions=512,
        _client=fake_client,
    )
    result = await adapter.embed(["laptop x1", "phone y2"], input_type="document")

    assert len(result) == 2
    assert len(result[0]) == 512
    fake_client.embed.assert_awaited_once_with(
        texts=["laptop x1", "phone y2"],
        model="voyage-3-lite",
        input_type="document",
    )


@pytest.mark.asyncio
async def test_embed_query_passes_input_type(fake_client: MagicMock) -> None:
    adapter = VoyageAdapter(
        api_key="test", model="voyage-3-lite", dimensions=512, _client=fake_client
    )
    await adapter.embed(["query text"], input_type="query")

    call = fake_client.embed.await_args.kwargs
    assert call["input_type"] == "query"


def test_dimensions_property() -> None:
    adapter = VoyageAdapter(
        api_key="test", model="voyage-3-lite", dimensions=512, _client=MagicMock()
    )
    assert adapter.dimensions == 512
```

- [ ] **Step 9.3: Correr tests (rojo)**

```bash
uv run pytest tests/unit/infrastructure/test_voyage_adapter.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 9.4: Implementar `voyage_adapter.py`**

```python
"""Voyage implementation of EmbeddingsPort."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import voyageai

from shopping_copilot.domain.ports import EmbeddingInputType, Vector


class VoyageAdapter:
    """Voyage AI embeddings — implements EmbeddingsPort."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        dimensions: int,
        _client: Any | None = None,
    ) -> None:
        self._model = model
        self._dimensions = dimensions
        # allow injection for tests
        self._client = _client or voyageai.AsyncClient(api_key=api_key)

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(
        self,
        texts: Sequence[str],
        *,
        input_type: EmbeddingInputType,
    ) -> list[Vector]:
        result = await self._client.embed(
            texts=list(texts),
            model=self._model,
            input_type=input_type,
        )
        return list(result.embeddings)
```

- [ ] **Step 9.5: Correr tests (verde)**

```bash
uv run pytest tests/unit/infrastructure/ -v
```

Expected: **6 passed** (3 Anthropic + 3 Voyage).

- [ ] **Step 9.6: Commit**

```bash
git add src/shopping_copilot/infrastructure/embeddings/voyage_adapter.py tests/unit/infrastructure/test_voyage_adapter.py pyproject.toml uv.lock
git commit -m "feat(infra): VoyageAdapter implementing EmbeddingsPort"
```

---

## Task 10 — SQLAlchemy 2 async + Alembic init

**Concepto:**

- **SQLAlchemy 2** — ORM. API async con `AsyncSession`. Más ergonómico que el modelo 1.x.
- **Alembic** — sistema de migraciones (equivalente Python de Flyway). Cada cambio de schema es un archivo versionado en `migrations/versions/`.

**Files:**
- Modify: `pyproject.toml`
- Create: `alembic.ini`
- Create: `migrations/env.py`
- Create: `migrations/script.py.mako`
- Create: `src/shopping_copilot/infrastructure/catalog/models.py` (SQLAlchemy models)

- [ ] **Step 10.1: Añadir dependencias**

```bash
uv add "sqlalchemy[asyncio]>=2.0" asyncpg alembic
```

- [ ] **Step 10.2: Inicializar Alembic**

```bash
uv run alembic init -t async migrations
```

Esto crea `alembic.ini` y `migrations/` con `env.py`, `script.py.mako`, `versions/`.

- [ ] **Step 10.3: Editar `alembic.ini` — dejar vacía la URL (la inyectaremos desde env)**

Buscar la línea `sqlalchemy.url = ...` y dejarla en blanco:

```ini
sqlalchemy.url =
```

- [ ] **Step 10.4: Crear `src/shopping_copilot/infrastructure/catalog/models.py`**

```python
"""SQLAlchemy declarative models for the catalog."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import JSON, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class ProductRow(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(5000), nullable=False)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    rating_avg: Mapped[float] = mapped_column(nullable=False, default=0.0)
    specs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
```

- [ ] **Step 10.5: Editar `migrations/env.py` para leer el DSN desde settings y conocer los modelos**

Reemplazar el contenido de `migrations/env.py` con:

```python
from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from shopping_copilot.config import get_settings
from shopping_copilot.infrastructure.catalog.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_url() -> str:
    return get_settings().postgres_dsn


def run_migrations_offline() -> None:
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = _get_url()
    connectable = async_engine_from_config(
        cfg, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 10.6: Verificar que Alembic se conecta**

(Asegúrate de que Postgres está corriendo vía `make up` y que `.env` tiene `POSTGRES_DSN` correcto.)

```bash
uv run alembic current
```

Expected: imprime `(no output)` pero sin error → conectó y no hay migraciones aplicadas.

- [ ] **Step 10.7: Commit**

```bash
git add pyproject.toml uv.lock alembic.ini migrations/ src/shopping_copilot/infrastructure/catalog/models.py
git commit -m "feat(infra): SQLAlchemy 2 async + Alembic init + Product model"
```

---

## Task 11 — Migración inicial: tabla `products`

**Concepto:**

- **Migration autogenerate** — Alembic compara el modelo declarado (`ProductRow`) con el schema actual de la DB y genera una migración automáticamente.

**Files:**
- Create: `migrations/versions/0001_create_products.py` (autogenerado + revisado)

- [ ] **Step 11.1: Generar la migración**

```bash
uv run alembic revision --autogenerate -m "create products table"
```

Esto crea un archivo nuevo en `migrations/versions/` con prefijo tipo `<hash>_create_products_table.py`.

- [ ] **Step 11.2: Renombrar para consistencia (opcional pero recomendado)**

Renombrar el archivo a `0001_create_products.py`. Abrirlo y verificar que contiene `op.create_table("products", ...)` con las columnas correctas.

- [ ] **Step 11.3: Aplicar la migración**

```bash
uv run alembic upgrade head
```

Expected: `Running upgrade  -> 0001, create products table`.

- [ ] **Step 11.4: Verificar en Postgres**

```bash
make psql
# dentro de psql:
\dt
# debe mostrar la tabla "products"
\d products
# debe mostrar columnas sku, name, category, brand, ...
\q
```

- [ ] **Step 11.5: Commit**

```bash
git add migrations/versions/0001_create_products.py
git commit -m "feat(infra): initial migration creating products table"
```

---

## Task 12 — PostgresCatalogAdapter implementando CatalogPort

**Concepto:**

- **Adapter de persistencia** — traduce entre entities de dominio y filas SQL. Mantiene el dominio puro.
- Funciones pequeñas para mapear `ProductRow ↔ Product`.

**Files:**
- Create: `src/shopping_copilot/infrastructure/catalog/postgres_catalog.py`
- Create: `tests/integration/test_postgres_catalog.py`
- Create: `tests/conftest.py` (fixture de engine)

- [ ] **Step 12.1: Crear `tests/conftest.py`**

```python
"""Shared pytest fixtures."""
from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from shopping_copilot.config import get_settings


@pytest.fixture(scope="session")
def postgres_dsn() -> str:
    return get_settings().postgres_dsn


@pytest.fixture
async def engine(postgres_dsn: str) -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine(postgres_dsn, echo=False)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
```

- [ ] **Step 12.2: Crear `src/shopping_copilot/infrastructure/catalog/postgres_catalog.py`**

```python
"""Postgres adapter for CatalogPort."""
from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shopping_copilot.domain.entities import Product
from shopping_copilot.domain.value_objects import Money, Sku
from shopping_copilot.infrastructure.catalog.models import ProductRow


def _row_to_product(row: ProductRow) -> Product:
    return Product(
        sku=Sku(row.sku),
        name=row.name,
        category=row.category,
        brand=row.brand,
        description=row.description,
        price=Money(Decimal(row.price_amount), row.price_currency),
        stock=row.stock,
        rating_avg=row.rating_avg,
        specs=dict(row.specs or {}),
    )


class PostgresCatalogAdapter:
    """Implements CatalogPort against Postgres via SQLAlchemy 2 async."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._sf = session_factory

    async def get_product(self, sku: Sku) -> Product | None:
        async with self._sf() as session:
            row = await session.get(ProductRow, sku.value)
            return _row_to_product(row) if row else None

    async def find_products(
        self,
        *,
        skus: Sequence[Sku] | None = None,
        category: str | None = None,
        max_price_usd: float | None = None,
    ) -> list[Product]:
        async with self._sf() as session:
            stmt = select(ProductRow)
            if skus:
                stmt = stmt.where(ProductRow.sku.in_([s.value for s in skus]))
            if category:
                stmt = stmt.where(ProductRow.category == category)
            if max_price_usd is not None:
                stmt = stmt.where(ProductRow.price_amount <= Decimal(str(max_price_usd)))
            result = await session.scalars(stmt)
            return [_row_to_product(r) for r in result]

    async def skus_exist(self, skus: Sequence[Sku]) -> set[Sku]:
        if not skus:
            return set()
        async with self._sf() as session:
            stmt = select(ProductRow.sku).where(
                ProductRow.sku.in_([s.value for s in skus])
            )
            result = await session.scalars(stmt)
            return {Sku(s) for s in result.all()}
```

- [ ] **Step 12.3: Crear tests de integración**

`tests/integration/test_postgres_catalog.py`:

```python
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shopping_copilot.domain.value_objects import Sku
from shopping_copilot.infrastructure.catalog.models import ProductRow
from shopping_copilot.infrastructure.catalog.postgres_catalog import PostgresCatalogAdapter


@pytest.fixture
async def _seed(session_factory: async_sessionmaker[AsyncSession]) -> None:
    async with session_factory() as s:
        # Clean
        await s.execute(ProductRow.__table__.delete())
        s.add_all([
            ProductRow(
                sku="LAP-001", name="ThinkPad X1", category="laptop",
                brand="Lenovo", description="14\" ultrabook",
                price_amount=Decimal("1200"), price_currency="USD",
                stock=3, rating_avg=4.5, specs={"ram": "16GB"},
            ),
            ProductRow(
                sku="LAP-002", name="MacBook Air", category="laptop",
                brand="Apple", description="13\" M3",
                price_amount=Decimal("1100"), price_currency="USD",
                stock=5, rating_avg=4.8, specs={"ram": "16GB"},
            ),
            ProductRow(
                sku="PHN-001", name="Pixel 8", category="phone",
                brand="Google", description="6.2\" phone",
                price_amount=Decimal("699"), price_currency="USD",
                stock=10, rating_avg=4.3, specs={"storage": "128GB"},
            ),
        ])
        await s.commit()


@pytest.mark.asyncio
async def test_get_product_returns_entity(
    session_factory: async_sessionmaker[AsyncSession], _seed: None
) -> None:
    adapter = PostgresCatalogAdapter(session_factory)
    p = await adapter.get_product(Sku("LAP-001"))
    assert p is not None
    assert p.name == "ThinkPad X1"
    assert p.price.amount == Decimal("1200")


@pytest.mark.asyncio
async def test_get_product_missing_returns_none(
    session_factory: async_sessionmaker[AsyncSession], _seed: None
) -> None:
    adapter = PostgresCatalogAdapter(session_factory)
    p = await adapter.get_product(Sku("ZZZ-999"))
    assert p is None


@pytest.mark.asyncio
async def test_find_by_category_and_max_price(
    session_factory: async_sessionmaker[AsyncSession], _seed: None
) -> None:
    adapter = PostgresCatalogAdapter(session_factory)
    products = await adapter.find_products(category="laptop", max_price_usd=1150)
    assert {p.sku.value for p in products} == {"LAP-002"}


@pytest.mark.asyncio
async def test_skus_exist(
    session_factory: async_sessionmaker[AsyncSession], _seed: None
) -> None:
    adapter = PostgresCatalogAdapter(session_factory)
    existing = await adapter.skus_exist([Sku("LAP-001"), Sku("ZZZ-000")])
    assert existing == {Sku("LAP-001")}
```

- [ ] **Step 12.4: Correr tests (debe conectar a Postgres real vía `.env`)**

```bash
uv run pytest tests/integration/test_postgres_catalog.py -v
```

Expected: **4 passed**.

- [ ] **Step 12.5: Commit**

```bash
git add src/shopping_copilot/infrastructure/catalog/postgres_catalog.py tests/conftest.py tests/integration/
git commit -m "feat(infra): PostgresCatalogAdapter + integration tests"
```

---

## Task 13 — Seed script: 20 laptops generadas por Haiku

**Concepto:**

- **Structured output** con Pydantic — le pedimos a Haiku que produzca JSON que cumpla un schema. Si no cumple → retry. Esto garantiza datos limpios.
- **Idempotencia** — el seed se puede correr N veces sin duplicar (upsert por SKU).

**Files:**
- Create: `scripts/seed.py`

- [ ] **Step 13.1: Crear `scripts/seed.py`**

```python
"""Seed the catalog with synthetic laptops using Haiku.

Usage:
    uv run python -m scripts.seed

Idempotent: re-running upserts by sku.
"""
from __future__ import annotations

import asyncio
import json
from decimal import Decimal

from pydantic import BaseModel, Field
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from shopping_copilot.config import get_settings
from shopping_copilot.domain.ports import LLMMessage
from shopping_copilot.infrastructure.catalog.models import ProductRow
from shopping_copilot.infrastructure.llm.anthropic_adapter import AnthropicAdapter


class LaptopSpec(BaseModel):
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
Output STRICT JSON matching the schema — no prose, no markdown fences.
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

    data = json.loads(resp.content)
    parsed = LaptopList(**data)
    print(f"Parsed {len(parsed.items)} laptops.")

    engine = create_async_engine(settings.postgres_dsn)
    sf = async_sessionmaker(engine, expire_on_commit=False)
    async with sf() as s:
        for item in parsed.items:
            stmt = insert(ProductRow).values(
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
            ).on_conflict_do_update(
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
            await s.execute(stmt)
        await s.commit()
    await engine.dispose()
    print("Seed done.")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 13.2: Correr el seed** (necesitas key válida de Anthropic en `.env`)

```bash
uv run python -m scripts.seed
```

Expected output:
```
Requesting laptop catalog from Haiku...
Tokens in=~200 out=~2500
Parsed 20 laptops.
Seed done.
```

Costo estimado: < $0.02.

- [ ] **Step 13.3: Verificar en Postgres**

```bash
make psql
# dentro:
SELECT sku, name, brand, price_amount FROM products ORDER BY sku;
\q
```

Debe mostrar 20 filas `LAP-001` ... `LAP-020`.

- [ ] **Step 13.4: Re-correr para verificar idempotencia**

```bash
uv run python -m scripts.seed
# luego, en psql:
SELECT COUNT(*) FROM products;
# debe seguir siendo 20
```

- [ ] **Step 13.5: Commit**

```bash
git add scripts/seed.py
git commit -m "feat(seed): generate 20 synthetic laptops via Haiku (idempotent)"
```

---

## Task 14 — FastAPI skeleton + `/health`

**Concepto:**

- **FastAPI** — web framework async, genera OpenAPI automáticamente.
- `/health` — endpoint liveness estándar para orquestadores.

**Files:**
- Create: `src/shopping_copilot/api/main.py`
- Create: `src/shopping_copilot/api/routers/health.py`
- Modify: `pyproject.toml` (agregar `fastapi`, `uvicorn`)

- [ ] **Step 14.1: Añadir dependencias**

```bash
uv add "fastapi>=0.115" "uvicorn[standard]>=0.31"
```

- [ ] **Step 14.2: Crear `health.py`**

```python
"""Liveness and readiness probes."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}
```

- [ ] **Step 14.3: Crear `main.py`**

```python
"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI

from shopping_copilot.api.routers import health


def create_app() -> FastAPI:
    app = FastAPI(
        title="Shopping Copilot",
        version="0.1.0",
        description="Retail agentic shopping assistant",
    )
    app.include_router(health.router)
    return app


app = create_app()
```

- [ ] **Step 14.4: Levantar el servidor**

```bash
uv run uvicorn shopping_copilot.api.main:app --reload --port 8000
```

Dejarlo corriendo en una terminal.

- [ ] **Step 14.5: Probar en otra terminal**

```bash
curl http://localhost:8000/health
# {"status":"ok"}
curl http://localhost:8000/ready
# {"status":"ready"}
```

Abrir http://localhost:8000/docs — debe mostrar Swagger UI con los dos endpoints.

- [ ] **Step 14.6: Commit**

```bash
git add src/shopping_copilot/api/main.py src/shopping_copilot/api/routers/health.py pyproject.toml uv.lock
git commit -m "feat(api): FastAPI skeleton + /health and /ready probes"
```

---

## Task 15 — DI container (`deps.py`) + schemas Pydantic

**Concepto:**

- **Dependency Injection en FastAPI** — `Depends(fn)` inyecta lo que la función devuelva. Usamos esto para que los endpoints reciban *puertos*, no adapters concretos. Swap de proveedor sin tocar routers.
- **Schemas** — Pydantic DTOs separados del dominio. El dominio es interno; los schemas son el contrato público del API.

**Files:**
- Create: `src/shopping_copilot/api/schemas.py`
- Create: `src/shopping_copilot/api/deps.py`

- [ ] **Step 15.1: Crear `schemas.py`**

```python
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
```

- [ ] **Step 15.2: Crear `deps.py`**

```python
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
```

- [ ] **Step 15.3: Typecheck**

```bash
uv run mypy src/shopping_copilot
```

Expected: `Success`.

- [ ] **Step 15.4: Commit**

```bash
git add src/shopping_copilot/api/schemas.py src/shopping_copilot/api/deps.py
git commit -m "feat(api): DI container and chat schemas"
```

---

## Task 16 — Endpoint `/chat` — echo con Claude

**Concepto:**

- Un solo endpoint, sin streaming, sin grafo LangGraph aún. Objetivo: **cerrar el lazo** UI → FastAPI → Anthropic → respuesta.
- Todo el pipeline de LangGraph llega en Semana 2.

**Files:**
- Create: `src/shopping_copilot/api/routers/chat.py`
- Modify: `src/shopping_copilot/api/main.py` (registrar el router)

- [ ] **Step 16.1: Crear `chat.py`**

```python
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
        LLMMessage(role=m.role, content=m.content) for m in body.messages  # type: ignore[arg-type]
    ]
    result = await llm.send_messages(messages, max_tokens=512, temperature=0.3)
    return ChatResponse(
        content=result.content,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
```

- [ ] **Step 16.2: Registrar el router en `main.py`**

Editar `src/shopping_copilot/api/main.py` — añadir el import y el `include_router`:

```python
from shopping_copilot.api.routers import chat, health


def create_app() -> FastAPI:
    app = FastAPI(
        title="Shopping Copilot",
        version="0.1.0",
        description="Retail agentic shopping assistant",
    )
    app.include_router(health.router)
    app.include_router(chat.router)
    return app
```

- [ ] **Step 16.3: Reiniciar uvicorn y probar**

(Si dejaste uvicorn corriendo con `--reload`, ya tomó el cambio.)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hola, ¿qué haces?"}]}'
```

Expected: JSON con `content`, `model`, `input_tokens`, `output_tokens`. El `content` debe ser una respuesta coherente de Claude.

- [ ] **Step 16.4: Commit**

```bash
git add src/shopping_copilot/api/routers/chat.py src/shopping_copilot/api/main.py
git commit -m "feat(api): minimal /chat endpoint wired to Anthropic"
```

---

## Task 17 — UI Streamlit consumiendo `/chat`

**Concepto:**

- **Streamlit** — la forma más rápida de darle cara a un backend Python. `st.chat_input` y `st.chat_message` son widgets built-in.
- Sin streaming aún (el endpoint `/chat` es síncrono). En Semana 3-4 migramos a streaming y Next.js.

**Files:**
- Create: `ui/app.py`
- Modify: `pyproject.toml` (añadir `streamlit`, `httpx`)

- [ ] **Step 17.1: Añadir dependencias**

```bash
uv add streamlit httpx
```

- [ ] **Step 17.2: Crear `ui/app.py`**

```python
"""Streamlit UI for the shopping copilot — Fase 1a."""
from __future__ import annotations

import httpx
import streamlit as st

API_URL = "http://localhost:8000/chat"

st.set_page_config(page_title="Shopping Copilot", page_icon="🛒", layout="wide")
st.title("🛒 Shopping Copilot")
st.caption("Fase 1a — echo con Claude. El agente completo llega en Semana 2.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("¿Qué buscas hoy?")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resp = httpx.post(
                API_URL,
                json={"messages": st.session_state.messages},
                timeout=60.0,
            )
        if resp.status_code != 200:
            st.error(f"Error {resp.status_code}: {resp.text}")
        else:
            data = resp.json()
            st.markdown(data["content"])
            st.caption(
                f"`{data['model']}` · in={data['input_tokens']} out={data['output_tokens']}"
            )
            st.session_state.messages.append(
                {"role": "assistant", "content": data["content"]}
            )

with st.sidebar:
    st.subheader("Sesión")
    st.write(f"Mensajes: **{len(st.session_state.messages)}**")
    if st.button("🧹 Reset"):
        st.session_state.messages = []
        st.rerun()
```

- [ ] **Step 17.3: Correr Streamlit**

```bash
uv run streamlit run ui/app.py
```

Se abre el navegador en http://localhost:8501. Escribir "hola" y probar que Claude responde.

- [ ] **Step 17.4: Commit**

```bash
git add ui/app.py pyproject.toml uv.lock
git commit -m "feat(ui): streamlit chat consuming /chat endpoint"
```

---

## Task 18 — LangSmith tracing verificado

**Concepto:**

- **Tracing con cero código** — basta con instalar `langsmith` como dep, tener las env vars correctas, y usar el cliente de Anthropic *vía* el SDK oficial (que LangSmith auto-wrappea) O vía LangChain. Para la Fase 1 lo más fácil es usar el wrapper de LangSmith para el SDK de Anthropic.

**Files:**
- Modify: `pyproject.toml` (agregar `langsmith`)
- Modify: `src/shopping_copilot/infrastructure/llm/anthropic_adapter.py` (envolver cliente con `wrap_anthropic`)
- Create: `src/shopping_copilot/infrastructure/observability/langsmith_setup.py`

- [ ] **Step 18.1: Añadir dependencia**

```bash
uv add langsmith
```

- [ ] **Step 18.2: Crear `langsmith_setup.py`**

```python
"""LangSmith configuration — env-var driven, zero-code."""
from __future__ import annotations

import os

from shopping_copilot.config import get_settings


def configure_langsmith() -> None:
    """Populate os.environ so langchain/langsmith pick up tracing settings.

    Call this ONCE at app startup, before any Anthropic/OpenAI client is created.
    """
    s = get_settings()
    os.environ["LANGCHAIN_TRACING_V2"] = "true" if s.langchain_tracing_v2 else "false"
    os.environ["LANGCHAIN_ENDPOINT"] = s.langchain_endpoint
    if s.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = s.langchain_api_key.get_secret_value()
    os.environ["LANGCHAIN_PROJECT"] = s.langchain_project
```

- [ ] **Step 18.3: Envolver el cliente Anthropic en el adapter**

Editar `src/shopping_copilot/infrastructure/llm/anthropic_adapter.py` — modificar el `__init__`:

```python
from anthropic import AsyncAnthropic
from langsmith.wrappers import wrap_anthropic

# ... resto del módulo

class AnthropicAdapter:
    def __init__(
        self,
        *,
        api_key: str,
        model_sonnet: str,
        model_haiku: str,
    ) -> None:
        raw_client = AsyncAnthropic(api_key=api_key)
        # wrap_anthropic es no-op si LANGCHAIN_TRACING_V2 != "true"
        self._client = wrap_anthropic(raw_client)
        self._model_sonnet = model_sonnet
        self._model_haiku = model_haiku
```

- [ ] **Step 18.4: Llamar a `configure_langsmith()` al arrancar la app**

Editar `src/shopping_copilot/api/main.py`:

```python
from shopping_copilot.infrastructure.observability.langsmith_setup import configure_langsmith


def create_app() -> FastAPI:
    configure_langsmith()  # ← primer cosa, antes de cualquier cliente
    app = FastAPI(...)
    ...
```

- [ ] **Step 18.5: Asegurar `.env` con LangSmith**

Editar tu `.env` real (ya no el ejemplo) y poner:

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_<tu_key_real>
LANGCHAIN_PROJECT=shopping-copilot-dev
```

- [ ] **Step 18.6: Reiniciar uvicorn y disparar una llamada**

```bash
# Detener el uvicorn con Ctrl+C y arrancar de nuevo para que lea la nueva env
uv run uvicorn shopping_copilot.api.main:app --reload --port 8000
```

En otra terminal:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"dime un chiste de programadores"}]}'
```

- [ ] **Step 18.7: Verificar en LangSmith UI**

1. Abrir https://smith.langchain.com/
2. Ir al workspace, seleccionar proyecto `shopping-copilot-dev`.
3. En **Traces** debe aparecer una llamada reciente a `Anthropic.messages.create` con input/output, tokens y latencia.

Si no aparece, debug rápido:
- `echo $LANGCHAIN_TRACING_V2` dentro del shell donde corres uvicorn → debe ser `true`.
- `echo $LANGCHAIN_API_KEY` → debe empezar con `lsv2_`.
- Revisar los logs de uvicorn por errores de autenticación LangSmith.

- [ ] **Step 18.8: Commit**

```bash
git add src/shopping_copilot/infrastructure/observability/langsmith_setup.py src/shopping_copilot/infrastructure/llm/anthropic_adapter.py src/shopping_copilot/api/main.py pyproject.toml uv.lock
git commit -m "feat(obs): wire LangSmith tracing via wrap_anthropic (zero custom code)"
```

---

## Task 19 — GitHub Actions CI básica

**Concepto:**

- **CI (Continuous Integration)** — correr lint + typecheck + tests en cada PR.
- En Semana 4 agregaremos corrida de evals; en Semana 1, solo lo básico.

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 19.1: Crear workflow**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  quality:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: shopping
          POSTGRES_PASSWORD: shopping
          POSTGRES_DB: shopping
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U shopping"
          --health-interval 5s
          --health-timeout 5s
          --health-retries 10

    env:
      POSTGRES_DSN: postgresql+asyncpg://shopping:shopping@localhost:5432/shopping
      ANTHROPIC_API_KEY: dummy-ci-key
      VOYAGE_API_KEY: dummy-ci-key

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          version: "latest"

      - name: Install Python
        run: uv python install 3.12

      - name: Sync deps
        run: uv sync

      - name: Alembic upgrade
        run: uv run alembic upgrade head

      - name: Lint
        run: |
          uv run ruff check .
          uv run ruff format --check .

      - name: Typecheck
        run: uv run mypy src

      - name: Unit + integration tests
        run: uv run pytest -v
```

- [ ] **Step 19.2: Crear un repo vacío en GitHub y pushear**

(Sólo si aún no existe el repo remoto — en la UI de GitHub, crear uno, luego:)

```bash
git remote add origin git@github.com:<tu-usuario>/agentic-ai.git
git push -u origin main
```

- [ ] **Step 19.3: Verificar CI en GitHub**

Ir a la pestaña **Actions** del repo — el workflow debe estar corriendo. Si falla, revisar logs y ajustar.

- [ ] **Step 19.4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: basic github actions (lint + mypy + tests)"
git push
```

---

## Task 20 — Review final Semana 1

Comprueba cada ítem antes de cerrar la semana. Cualquier no cumplido → crear micro-task y resolverlo.

- [ ] **20.1 Funcional end-to-end**
  - [ ] `make up` levanta Postgres + Qdrant + Redis en verde
  - [ ] `uv run uvicorn shopping_copilot.api.main:app` levanta `/health` y `/chat`
  - [ ] `uv run streamlit run ui/app.py` abre UI en 8501
  - [ ] Una pregunta a Streamlit llega a Claude y vuelve

- [ ] **20.2 Tests**
  - [ ] `uv run pytest -v` pasa todo (~ 20 tests)
  - [ ] Dominio: VOs + Product entity
  - [ ] Infra: Anthropic adapter mocked + Voyage adapter mocked
  - [ ] Integración: Postgres catalog

- [ ] **20.3 Calidad**
  - [ ] `uv run ruff check .` limpio
  - [ ] `uv run ruff format --check .` limpio
  - [ ] `uv run mypy src` limpio

- [ ] **20.4 Datos**
  - [ ] 20 laptops en Postgres (`SELECT COUNT(*) FROM products;` → 20)
  - [ ] Seed es idempotente (re-ejecución no duplica)

- [ ] **20.5 Observabilidad**
  - [ ] Una llamada real a `/chat` aparece como trace en LangSmith UI (proyecto `shopping-copilot-dev`)
  - [ ] Se ven tokens y costo por run

- [ ] **20.6 CI**
  - [ ] El último push a `main` muestra check verde en GitHub Actions

- [ ] **20.7 Documentación mínima**
  - [ ] README explica cómo arrancar
  - [ ] `.env.example` refleja todas las env vars reales
  - [ ] Tracker `docs/progress/plan.html` con todas las casillas de Semana 1 marcadas ✓

- [ ] **20.8 Commit de cierre**

```bash
git tag -a week1-done -m "Fase 1 — Semana 1 completa"
git push --tags
```

---

## Conceptos aprendidos en Semana 1

Marca en el tracker HTML cada uno cuando te sientas cómodo explicándoselo a alguien más:

- Port/Adapter en Python (`Protocol`, `@runtime_checkable`)
- `uv` — sync, add, lock, run
- Ruff (formatter + linter + isort en uno)
- `mypy --strict`
- `pydantic-settings` (`.env`, SecretStr, 12-factor)
- SQLAlchemy 2 async (`AsyncSession`, `async_sessionmaker`)
- Alembic (`revision --autogenerate`, `upgrade head`)
- Pydantic DTOs en FastAPI (`response_model`, `Field(pattern=...)`)
- FastAPI dependency injection (`Depends`, `Annotated`)
- LangSmith tracing zero-code (`wrap_anthropic` + env vars)
- Token counting y costo en responses
- Structured output con Pydantic (seed con Haiku)
- GitHub Actions (service containers, matrix)
- Idempotencia en seeds (`ON CONFLICT DO UPDATE`)

---

## Self-review del plan (post-escritura)

**Cobertura del spec:**
- ✅ Task 1–2 cubre w1-b1, w1-b2
- ✅ Task 3 cubre w1-b3
- ✅ Task 4 cubre w1-b4
- ✅ Task 5–7 cubre w1-b5
- ✅ Task 8 cubre w1-b6
- ✅ Task 9 cubre w1-b7
- ✅ Task 8 + 9 + 12 cubre w1-b8 (tests mocked + integration)
- ✅ Task 10–13 cubre w1-b9
- ✅ Task 14–16 cubre w1-b10
- ✅ Task 17 cubre w1-b11
- ✅ Task 18 cubre w1-b12
- ✅ Task 19 cubre w1-b13

**Placeholders:** ninguno — todos los steps tienen código/comando concreto.

**Consistencia de tipos:** verificada: `LLMMessage` y `LLMResponse` se usan igual en Task 7, 8, 13, 15, 16. `Sku`/`Money` consistentes entre Task 5, 6, 12.

**Scope:** solo Fase 1 Semana 1 — alineado con el spec y el roadmap.

---

## Handoff — cómo ejecutar este plan

Este plan es para que **tú** (Jorge) lo ejecutes. Diferencia con el patrón por defecto de `writing-plans`:

- **No voy a despachar subagentes** ni correr tasks automáticamente — tú escribes el código.
- **Mi rol:** a medida que avances, pégame (o compárteme) bloques de código mientras los escribes, y yo reviso, corrijo y explico en detalle cada concepto que aparezca por primera vez.
- **Cadencia sugerida:** una sesión de trabajo = 1–2 tasks completos. Antes de empezar cada task, pídeme la "mini-clase" del concepto principal si quieres profundizar.
- **Cuando termines un task:** marca los checkboxes aquí y en `docs/progress/plan.html`, luego commit.
- **Si te atoras:** para, copia el error + último comando que corriste, y pregúntame.

### Próximo paso sugerido

Empieza por el **Prerrequisitos** del tracker HTML — abrí las cuentas pendientes (Anthropic/Voyage/LangSmith), instalá Python 3.12 / uv / Docker / Cursor. Cuando estés listo, arrancamos con **Task 1**.
