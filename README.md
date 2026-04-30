# Shopping Copilot

Retail agentic-AI learning project — a conversational shopping assistant built with LangGraph, RAG, and Clean Architecture.

**Status:** Phase 1a (Week 1) complete. End-to-end echo agent with FastAPI, Streamlit, LangSmith tracing, and CI.

## Architecture

Clean Architecture with ports and adapters. Domain is pure Python; LLM/embeddings/vector-store/persistence are swappable via `Protocol` interfaces.

```
ui (Streamlit)
   v
api (FastAPI)
   v
agents (LangGraph)            <- coming in Week 2
   v
application (use cases)
   v
domain (entities + ports) <- infrastructure (adapters)
```

Full design in [docs/superpowers/specs/2026-04-23-retail-shopping-copilot-design.md](docs/superpowers/specs/2026-04-23-retail-shopping-copilot-design.md).

## Tech stack

| Layer | Tech |
|---|---|
| Language | Python 3.12 |
| Package manager | uv |
| Web framework | FastAPI + Uvicorn |
| Validation | Pydantic v2 |
| LLM | Anthropic Claude (Sonnet 4.6 + Haiku 4.5) |
| Embeddings | Voyage AI (`voyage-3-lite`, 512 dims) |
| Vector store | Qdrant (Docker) — used from Week 2 |
| RDBMS | Postgres 16 + SQLAlchemy 2 async + Alembic |
| Cache / sessions | Redis — used from Week 3 |
| UI | Streamlit (Phase 1a) -> Next.js (Phase 1b) |
| Tracing / evals | LangSmith |
| Lint / format / types | Ruff, mypy --strict |
| Tests | pytest + pytest-asyncio + respx |
| CI | GitHub Actions |

## Prerequisites

- Python 3.12 (recommended via [pyenv](https://github.com/pyenv/pyenv))
- [uv](https://github.com/astral-sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker Desktop (running)
- API keys:
  - [Anthropic](https://console.anthropic.com/)
  - [Voyage AI](https://dash.voyageai.com/) (free tier 50M tok/mo)
  - [LangSmith](https://smith.langchain.com/) (free tier 5k traces/mo)

## Quickstart

```bash
# 1. Install dependencies
uv sync

# 2. Copy and fill in API keys
cp .env.example .env
$EDITOR .env   # set ANTHROPIC_API_KEY, VOYAGE_API_KEY, LANGSMITH_API_KEY (and the regional endpoint if needed)

# 3. Start infra (Postgres, Qdrant, Redis)
make up

# 4. Apply DB migrations
uv run alembic upgrade head

# 5. Set up the dedicated test DB (one-time)
make test-db-setup

# 6. Seed the catalog with 20 synthetic laptops (uses Anthropic Haiku, ~$0.01)
uv run python -m scripts.seed
```

Then run the app in two terminals:

```bash
# Terminal A — API
uv run uvicorn shopping_copilot.api.main:app --reload --port 8000

# Terminal B — UI
uv run streamlit run ui/app.py
```

Open http://localhost:8501 and chat. Traces appear in LangSmith within ~30s.

## Project structure

```
agentic-ai/
├── docs/
│   ├── superpowers/specs/      # design specs
│   ├── superpowers/plans/      # implementation plans (per week)
│   ├── progress/plan.html      # interactive progress tracker
│   └── learning-journal/       # brainstorming narrative
├── src/shopping_copilot/
│   ├── domain/                 # entities, value objects, ports (Protocol)
│   ├── application/            # use cases (Week 2+)
│   ├── agents/                 # LangGraph state, nodes, edges (Week 2+)
│   ├── infrastructure/         # adapters: anthropic, voyage, postgres, ...
│   ├── api/                    # FastAPI routers, deps, schemas
│   ├── guardrails/             # NeMo, policies (Week 3+)
│   └── observability/          # OTel + structlog (Week 4)
├── ui/                         # Streamlit app
├── scripts/                    # seed and ingest scripts
├── migrations/                 # Alembic versions
├── tests/
│   ├── unit/                   # domain + adapter logic (mocked)
│   ├── integration/            # against real Postgres
│   └── contracts/              # port-vs-adapter equivalence
├── docker/docker-compose.yml
├── .github/workflows/ci.yml
├── pyproject.toml              # uv-managed
└── Makefile
```

## Useful Make commands

| Command | Purpose |
|---|---|
| `make up` / `make down` / `make restart` | Manage Docker Compose stack |
| `make reset` | Wipe volumes (destroys data) and restart |
| `make logs` | Follow container logs |
| `make psql` | Open psql against the dev DB |
| `make qdrant-ui` | Print the Qdrant dashboard URL |
| `make test-db-setup` | Create `shopping_test` and apply migrations (one-time) |
| `make fmt` | Auto-format and auto-fix lint with Ruff |
| `make lint` | Verify lint and format are clean |
| `make typecheck` | Run mypy --strict over `src/` |
| `make test` | Run pytest (unit + integration) |
| `make ci` | Run the full local quality gate (lint + typecheck + test) |

## Testing

Tests run against a dedicated DB (`shopping_test`) — your dev catalog is never touched.

```bash
uv run pytest -v
```

In CI, GitHub Actions provisions a fresh Postgres service container per run, creates `shopping_test`, applies migrations, then runs the suite. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Observability

LangSmith is enabled by default in dev (`LANGSMITH_TRACING=true` in `.env`). Each `/chat` turn appears as a trace with full prompt, response, tokens, latency, and cost. Project: `shopping-copilot-dev`.

If your account is on the regional AWS endpoint, set `LANGSMITH_ENDPOINT=https://aws.api.smith.langchain.com` in `.env`.

No custom telemetry code — auto-instrumentation only.

## Roadmap

- **Phase 1a (Week 1)** — DONE: scaffolding, domain, adapters, API, Streamlit, LangSmith, CI.
- **Phase 1b (Weeks 2-4)** — RAG (hybrid retrieval + reranker), LangGraph multi-agent, guardrails (NeMo + Presidio), HITL, evals + CI gates.
- **Phase 2** — LiteLLM dev gateway, Spring Boot enterprise gateway, Langfuse self-host, Grafana/Prometheus/Loki/Tempo stack.
- **Phase 3** — Kong AI Gateway at the edge, Phoenix evals, multi-vector retrieval.
- **Phase 4** — long-term memory, multi-tenant, fine-tuning, multimodal.

Detailed weekly plans live under [docs/superpowers/plans/](docs/superpowers/plans/).

## Documentation

- [Design spec](docs/superpowers/specs/2026-04-23-retail-shopping-copilot-design.md) — formal architecture and decisions
- [Week 1 implementation plan](docs/superpowers/plans/2026-04-23-week1-foundations.md) — task-by-task with code
- [Week 2-4 skeletons](docs/superpowers/plans/) — to be expanded as each week starts
- [Learning journal](docs/learning-journal/2026-04-23-brainstorming-agentic-ai.md) — pedagogical narrative of decisions
- [Progress tracker](docs/progress/plan.html) — open in a browser, persists in localStorage

## License

Internal learning project (Bayteq). No public distribution.
