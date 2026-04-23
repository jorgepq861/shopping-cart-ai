# Retail Shopping Copilot — Design Spec

- **Fecha:** 2026-04-23
- **Autor:** Jorge (Bayteq) + Claude (guía pedagógica)
- **Estado:** Diseño aprobado (pendiente de review del usuario)
- **Fase cubierta:** Fase 1 (MVP Python puro, 3–4 semanas)
- **Alcance futuro referido:** Fases 2, 3, 4 (hoja de ruta)

---

## 1. Contexto y objetivo

Este proyecto es el vehículo de aprendizaje de Jorge para dominar el ecosistema **agentic-AI** (LangGraph, LangFlow, LangSmith, RAG, búsqueda semántica, governance, tracing, monitoring) aplicándolo a un caso de uso realista y vistoso: un **copiloto conversacional de compras retail**.

El usuario final del copiloto chatea en lenguaje natural ("quiero una laptop para diseño bajo $1500") y un agente basado en LangGraph lo guía desde la búsqueda hasta el checkout, con RAG sobre fichas técnicas y reseñas, comparaciones inteligentes entre productos, gestión de carrito, y confirmación humana para compras sobre un umbral.

El proyecto tiene **dos objetivos paralelos**:

1. **Producto demostrable** — un asistente de compras creíble, con arquitectura limpia y governance real.
2. **Experiencia pedagógica** — cada decisión del diseño toca un concepto distinto de agentic-AI, de forma que al terminar Fase 1 Jorge haya practicado *todo* el temario: multi-agente, RAG híbrido, reranking, guardrails, evals, tracing, HITL, policy-as-code.

### 1.1 Principios del proyecto

- **Aprender haciendo:** Jorge escribe todo el código. Claude solo crea documentos en `docs/` (specs, guías, tracker) y guía la implementación conceptualmente.
- **Clean Architecture + puertos y adaptadores:** cambiar de proveedor (Voyage → OpenAI, Anthropic → Bedrock, Qdrant → pgvector) debe ser una línea de configuración.
- **Observability-first:** si no está trazado, no existe.
- **Cero telemetría custom:** solo auto-instrumentación (OTel, LangSmith env vars, Prometheus middleware). No custom spans, no wrappers de logging.
- **Policy-as-code:** precios, descuentos y stock nunca dependen del prompt. El LLM sugiere, el dominio decide.
- **Fail-safe defaults:** duda → handoff a humano, nunca inventar.
- **YAGNI:** lo que no esté en este spec se posterga a Fase 2 o posterior.

---

## 2. Alcance

### 2.1 Dentro de alcance (Fase 1)

- Agente conversacional multi-turno con historial persistente (checkpointer Postgres).
- Búsqueda semántica + léxica (híbrida) sobre catálogo sintético (200 productos, 3 categorías: laptops, smartphones, auriculares).
- Comparación inteligente de productos con contexto RAG (reseñas + fichas técnicas).
- Gestión de carrito (add / remove / update / clear).
- Checkout con **Human-in-the-Loop** cuando `total > $500` o `descuento > 30 %`.
- Guardrails: prompt injection, jailbreak, PII (Presidio), topic restriction, no-hallucination de SKU/precios, moderación de output.
- Policy-as-code: pricing, stock, budget.
- Evals reproducibles en CI con bloqueos de merge por regresión.
- Trazado completo en LangSmith + OTel auto-instrument + structlog JSON.
- UI Streamlit en semanas 1–3; opcional migración a Next.js + Vercel AI SDK en semana 4.

### 2.2 Fuera de alcance (explícito)

Se difiere conscientemente a Fases 2+ para no inflar el scope:

| Ítem | Fase |
|---|---|
| Autenticación real (OAuth2/SSO) | 2 |
| Multi-tenant / multi-usuario concurrente | 2 |
| Pagos reales (Stripe, pasarelas) | 2 |
| LiteLLM como dev gateway | 2 |
| Spring Boot gateway empresarial | 2 |
| Kong AI Gateway (edge prod-grade) | 3 |
| Langfuse self-host (alternativa OSS a LangSmith) | 2 |
| Stack LGTM (Grafana/Prometheus/Loki/Tempo) | 2 |
| Alertas y on-call | 3 |
| Memoria de largo plazo / personalización profunda | 4 |
| Fine-tuning / LoRA | 4 |
| Multimodalidad (imágenes de producto) | 4 |
| Multi-vector retrieval / ColBERT | 3 |
| Query decomposition avanzada | 3 |

---

## 3. Arquitectura

### 3.1 Vista en capas (Clean Architecture)

```
┌─────────────────────────────────────────────────────────┐
│  UI          Streamlit (Fase 1a) → Next.js (Fase 1b)   │
├─────────────────────────────────────────────────────────┤
│  API         FastAPI (/chat, /stream, /feedback)       │
│              Guardrails IN/OUT como middleware         │
├─────────────────────────────────────────────────────────┤
│  Orchestr.   LangGraph (router + sub-agents)           │
│              StateGraph + checkpointer Postgres        │
├─────────────────────────────────────────────────────────┤
│  Applicat.   Use cases: SearchProducts, Compare,       │
│              AddToCart, Checkout, EscalateToHuman      │
├─────────────────────────────────────────────────────────┤
│  Domain      Entities, Value Objects, Domain Services, │
│              Ports (LLMPort, EmbeddingsPort, ...)      │
├─────────────────────────────────────────────────────────┤
│  Infra       Adapters: Anthropic, Voyage, Qdrant,      │
│              Postgres, Redis, Mock Payment             │
│              + Observability (LangSmith, OTel)         │
└─────────────────────────────────────────────────────────┘
```

**Regla de dependencias:** hacia adentro. `domain` no conoce ningún framework externo. `application` solo conoce `domain`. `infrastructure` implementa puertos de `domain`. `agents`, `api`, `ui` son capas externas. Validado en CI vía **import-linter**.

### 3.2 Stack técnico

| Capa | Tecnología | Justificación |
|---|---|---|
| Lenguaje | Python 3.12 | Ecosistema agentic maduro |
| Package manager | **uv** | Rápido, lockfile reproducible |
| Web framework | FastAPI + Uvicorn | Async, OTel auto-instrument |
| Validación | Pydantic v2 | Output estructurado, settings |
| Orquestación agentes | **LangGraph** | State machines, checkpointing, HITL nativo |
| LLM SDK | LangChain + `langchain-anthropic` | Interfaces estables, tool calling unificado |
| LLM generación | Claude Sonnet 4.6 + Haiku 4.5 | Model cascading: Sonnet razona, Haiku clasifica |
| Embeddings | Voyage `voyage-3-lite` (512 d) | Top benchmarks, free tier 50M tok/mes |
| Vector store | Qdrant (self-host Docker) | Payload indexing, BM25, UI web, portable |
| Full-text / BM25 | Qdrant text index | Híbrido en una sola DB vectorial |
| Reranker | Voyage `rerank-2-lite` | Cross-encoder, +10–20 % recall |
| DB transaccional | Postgres 16 | Catálogo, órdenes, checkpointer LangGraph |
| Cache/sesión | Redis | Carrito efímero, rate limiting |
| Guardrails | NeMo Guardrails + Presidio + Guardrails AI | Runtime rails + PII + structured output |
| Prototipado | LangFlow (Docker) | Variantes del grafo visuales antes de código |
| Tracing/evals LLM | **LangSmith** (SaaS free tier) | Primario Fase 1 |
| Tracing infra | OpenTelemetry (auto-instrument) | Console exporter en Fase 1 |
| Métricas | `prometheus-fastapi-instrumentator` | `/metrics` expuesto |
| Logs | structlog JSON | trace_id auto-inyectado |
| UI | Streamlit (1a) / Next.js + Vercel AI SDK (1b) | Contraste pedagógico |
| Infra local | Docker Compose | `make up` levanta todo |
| Tests | pytest + pytest-asyncio + httpx + respx | Unit + integración + contract |
| Lint/format | **Ruff** (format + lint + isort) + mypy --strict | Único formatter (drop-in Black) |
| Precommit | pre-commit hooks | Ruff + mypy + tests rápidos |
| CI | GitHub Actions | Tests + evals en PR |
| Arquitectura tests | import-linter | Valida dependencias entre capas |

### 3.3 Principios no-funcionales

1. **Swappable providers** — todo LLM/embeddings/vector store tras un puerto.
2. **Determinismo donde importa** — temperatura 0 en router, guardrails y juez de evals; temperatura baja (<0.5) en generación al usuario.
3. **Observability-first** — cada nodo del grafo emite trace + métricas automáticamente.
4. **Fail-safe defaults** — duda → handoff humano.
5. **Policy-as-code** — reglas de negocio en código tipado con tests, no en prompts.
6. **Reproducibilidad** — `uv.lock` + modelos pinneados por versión + seeds en evals.
7. **12-factor** — config por env vars, stateless API, logs a stdout.
8. **Free-tier friendly** — uso responsable de LangSmith (≤ 4k traces/mes en dev) y Voyage.

### 3.4 Estructura de carpetas

```
agentic-ai/
├── docs/
│   ├── superpowers/specs/
│   │   └── 2026-04-23-retail-shopping-copilot-design.md   ← este spec
│   └── progress/
│       └── plan.html                                       ← tracker interactivo
├── src/shopping_copilot/
│   ├── domain/                 # entities, value objects, ports
│   ├── application/            # use cases
│   ├── agents/                 # LangGraph graphs, nodes, edges, prompts
│   ├── infrastructure/         # adapters (anthropic, voyage, qdrant, postgres, redis…)
│   ├── api/                    # FastAPI routers, deps, middleware, schemas
│   ├── guardrails/             # NeMo config, input/output rails, policies
│   ├── observability/          # OTel setup, LangSmith wiring, structlog config
│   └── config.py
├── ui/                         # Streamlit app (Fase 1a)
├── ui-next/                    # Next.js app (Fase 1b, opcional)
├── data/
│   ├── catalog_seed.py         # generador sintético
│   └── faqs.json
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contracts/              # tests de puertos vs adaptadores
│   └── evals/
│       ├── datasets/
│       ├── evaluators/
│       ├── redteam/
│       └── run.py
├── notebooks/                  # exploración, exports LangFlow
├── docker/
│   ├── docker-compose.yml
│   └── Dockerfile
├── pyproject.toml              # uv-managed
├── Makefile
└── .env.example
```

---

## 4. Componentes y módulos

### 4.1 `domain/` — núcleo de negocio

**Entidades:** `Product`, `Cart`, `CartItem`, `Order`, `User`.

**Value Objects (inmutables y validados):** `Sku`, `Money`, `Discount`, `StockLevel`, `Rating`.

**Domain services:** `PricingService` (aplica descuentos según policy), `StockService`.

**Puertos (Protocol / ABC):**
- `LLMPort` — `send_messages(messages, tools) -> LLMResponse`
- `EmbeddingsPort` — `embed(texts, input_type) -> list[Vector]`, `dimensions: int`
- `RerankerPort` — `rerank(query, docs) -> list[ScoredDoc]`
- `VectorStorePort` — `upsert`, `search(query_vec, filters, k)`
- `CatalogPort` — `get_product(sku)`, `find_products(filters)`
- `CartPort` — `get(user_id)`, `add`, `remove`, `update`, `clear`
- `PaymentPort` — `charge(amount, method)`, `refund(tx_id)`
- `NotificationPort` — `notify_human(context, reason)`

**Regla:** dominio **no importa** nada externo. Test de import-linter lo valida.

### 4.2 `application/` — casos de uso

Clases con un único método `execute`. Reciben puertos por constructor (DI).

- `SearchProductsUseCase`
- `CompareProductsUseCase`
- `AddToCartUseCase`, `RemoveFromCartUseCase`, `UpdateCartUseCase`
- `CheckoutUseCase` (evalúa si `requires_human_approval`)
- `EscalateToHumanUseCase`

### 4.3 `agents/` — grafo LangGraph

```
agents/
├── graph.py                    # construye y compila StateGraph
├── state.py                    # TypedDict del estado compartido
├── nodes/
│   ├── input_guardrails.py
│   ├── router.py               # Haiku
│   ├── search.py               # Sonnet
│   ├── comparator.py           # Sonnet
│   ├── cart.py                 # Haiku
│   ├── checkout.py             # Sonnet
│   ├── human_approval.py       # interrupt + resume
│   ├── smalltalk.py            # Haiku
│   ├── out_of_scope.py         # template fijo
│   └── output_guardrails.py
├── edges/conditional.py
└── prompts/                    # archivos Jinja versionados
```

### 4.4 `infrastructure/` — adaptadores

- `llm/anthropic_adapter.py`
- `embeddings/voyage_adapter.py`, `embeddings/openai_adapter.py`
- `reranker/voyage_reranker.py`
- `vectorstore/qdrant_adapter.py`
- `catalog/postgres_catalog.py` (SQLAlchemy 2 async)
- `cart/redis_cart.py`
- `payment/mock_payment.py`
- `notification/console_notif.py`
- `observability/otel_setup.py`, `observability/langsmith_setup.py`

Cada adaptador tiene **tests de contrato** en `tests/contracts/` validando mismo input/output/errores entre variantes del mismo puerto.

### 4.5 `api/` — FastAPI

- `routers/chat.py` — `POST /chat` (turno síncrono), `POST /stream` (SSE)
- `routers/feedback.py` — `POST /feedback` → LangSmith
- `routers/health.py` — `/health`, `/ready`
- `deps.py` — container DI (puertos → adaptadores)
- `middleware/guardrails.py`
- `schemas/` — Pydantic request/response DTOs

### 4.6 `guardrails/` — políticas

- `config.yml` — NeMo Guardrails (flows Colang)
- `input_rails.py` — jailbreak, PII (Presidio), injection heuristics, topic restriction
- `output_rails.py` — no-hallucination SKU, price match, moderation, structured output
- `policies/pricing.py` — max 30 % descuento, no stackable, min total $20
- `policies/stock.py` — no vender sin stock actual
- `policies/budget.py` — HITL si `total > $500` o `discount > 30 %`

### 4.7 `observability/`

Solo **configuración**, cero código custom:

- `otel.py` — `FastAPIInstrumentor`, `HTTPXClientInstrumentor`, `SQLAlchemyInstrumentor`, `RedisInstrumentor`, console exporter
- `langsmith.py` — lee env vars (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_PROJECT`, `LANGCHAIN_API_KEY`)
- `logging.py` — structlog JSON con `trace_id` auto-inyectado
- `metrics.py` — `prometheus_fastapi_instrumentator.Instrumentator().instrument(app).expose(app)`

### 4.8 `ui/`

**Fase 1a — Streamlit:** `app.py` con `st.chat_input` + `st.chat_message` + sidebar con viewer de trace del último turno.

**Fase 1b — Next.js + Vercel AI SDK (opcional):** `ui-next/` con `useChat` hook, SSE streaming, tool-call rendering, `useInterrupt` para HITL.

### 4.9 Dependencias entre módulos

```
ui → api → agents → application → domain ← infrastructure
                └→ guardrails
```

Enforced por **import-linter**.

---

## 5. Flujo conversacional (LangGraph)

### 5.1 State compartido

```python
class ShoppingState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    thread_id: str
    intent: Literal["search", "compare", "cart", "checkout", "smalltalk", "out_of_scope"]
    intent_confidence: float
    search_results: list[Product] | None
    compared_products: list[ComparisonResult] | None
    cart_snapshot: Cart | None
    guardrail_violations: list[GuardrailViolation]
    requires_human_approval: bool
    human_decision: Literal["approve", "reject"] | None
    cost_accumulated_usd: float
    tool_calls_log: list[ToolCall]
```

### 5.2 Diagrama del grafo

```
START
  → input_guardrails    (NeMo: jailbreak, PII, injection, topic)
  → router              (Haiku: intent + confidence)
      → search | comparator | cart | checkout | smalltalk | out_of_scope
  → (si checkout y requires_human_approval)
      → human_approval  (interrupt + resume)
  → output_guardrails   (no-SKU-inventado, price match, moderation, pydantic)
  → END
```

### 5.3 Responsabilidad de cada nodo

| Nodo | Modelo | Rol |
|---|---|---|
| `input_guardrails` | — | NeMo rails (T=0). Si viola → END con mensaje seguro. |
| `router` | Haiku 4.5 | Clasifica intent + confidence (structured output). |
| `search` | Sonnet 4.6 | Llama `SearchProductsUseCase`. Tool calling para filtros. |
| `comparator` | Sonnet 4.6 | RAG sobre reseñas y specs. Tabla comparativa en markdown. |
| `cart` | Haiku 4.5 | Operaciones de carrito vía tools. |
| `checkout` | Sonnet 4.6 | Valida stock y pricing; setea `requires_human_approval`. |
| `human_approval` | — | `interrupt()`. Pausa hasta recibir `Command(resume=...)`. |
| `smalltalk` | Haiku 4.5 | Model cascading barato para mensajes triviales. |
| `out_of_scope` | — | Respuesta fija "solo ayudo con compras, no con X". |
| `output_guardrails` | — | Valida SKU existen en DB, precios coinciden, moderación. |

**Patrón:** Haiku para clasificar/decidir, Sonnet para razonar/generar. *Model cascading.*

### 5.4 Límites runtime (runtime rails)

- Max tool calls / turno: **8**
- Max tokens input / output: **4 000 / 2 000**
- Max latency / turno: **30 s**
- Max cost acumulado / thread: **$0.50**

Violación → nodo `budget_guard` corta con mensaje y cierra el turno.

### 5.5 Manejo de errores

1. **Error de negocio** (SKU no existe) → nodo captura, mensaje amigable, END.
2. **Error técnico** (Qdrant caído) → `tenacity` retry 3× exponential, si persiste → `error_fallback` node → mensaje "problema técnico, reintenta".
3. **Guardrail violado** → no es error, es flujo esperado. END limpio.

### 5.6 Checkpointing — persistencia de conversaciones

`PostgresSaver` (LangGraph) con `thread_id = conversation_id`. Beneficios:

- Conversaciones multi-día con estado exacto restaurado.
- HITL sobrevive reinicios del proceso.
- Time-travel debugging: cargar estado en turno N y re-ejecutar desde ahí.
- Auditoría: cada checkpoint queda en tabla `checkpoints` (JSONB) con `parent_checkpoint_id`.

---

## 6. RAG pipeline y datos

### 6.1 Documentos indexados

| Fuente | Rol | Cantidad |
|---|---|---|
| Fichas técnicas | Factual (specs, descripción) | ~200 |
| Reseñas | Cualitativo (experiencia de uso) | ~1 000 |
| FAQs y políticas | No-catálogo (devoluciones, envíos, garantías) | ~30 |

### 6.2 Chunking específico por tipo

- **Fichas técnicas:** 1 chunk por ficha (300–600 tokens). Si largas, split por sección.
- **Reseñas:** 1 reseña = 1 chunk. Metadata: `rating`, `date`, `helpful_count`.
- **FAQs:** 1 pregunta+respuesta = 1 chunk.
- **Parent-document retrieval** (LangChain) para fichas largas.

### 6.3 Embeddings

- Modelo: Voyage `voyage-3-lite` (512 d).
- Distancia: `cosine`.
- `input_type="document"` al indexar; `input_type="query"` al consultar.
- Batch size: 128.
- `EmbeddingsPort.dimensions` detecta incompatibilidad al cambiar modelo (forzaría re-index).

### 6.4 Contextual Retrieval (técnica Anthropic 2024)

Antes de embedder un chunk, Haiku genera un header contextual que lo sitúa en su documento padre. Mejora recall 35–50 %. Costo estimado para todo el catálogo: < $1.

### 6.5 Qdrant — diseño de colección

- **Collection:** `products_rag`, `size: 512`, `distance: Cosine`.
- **Payload schema:**
  - `sku: keyword` (indexado)
  - `doc_type: keyword` (indexado) — `spec | review | faq`
  - `category: keyword` (indexado)
  - `brand: keyword` (indexado)
  - `price: float` (indexado, range queries)
  - `rating: float` (indexado)
  - `created_at: integer`
  - `text: text` (indexado full-text para BM25)
  - `parent_id: keyword`
  - `source_url: keyword`

**Payload indexes no son automáticos** — se crean explícitamente vía `create_payload_index()` por cada campo filtrable. Sin índice → filtros O(n).

### 6.6 Retrieval híbrido

```
query
  ├── rama semántica:  Voyage embed → Qdrant vector search (k=30) con filters
  ├── rama léxica:     Qdrant full-text search BM25 (k=30)
  └── fusion:          Reciprocal Rank Fusion (RRF, k=60)
                        → top 20
  → Voyage rerank-2-lite (cross-encoder) → top 5
  → Parent-document expansion si aplica
  → contexto final al LLM
```

### 6.7 Datos sintéticos — generación

Script `python -m shopping_copilot.seed`:

1. **Catálogo:** 200 productos (laptops, smartphones, auriculares) generados por Haiku con Pydantic schema estricto; validación de SKU único.
2. **Reseñas:** 3–8 por producto (mezcla 70/20/10 positivas/neutrales/negativas).
3. **FAQs:** 30 comunes sobre devoluciones, envíos, garantías.
4. **Persist:** productos/reseñas → Postgres (tabla fuente de verdad) + Qdrant (índice). Costo < $2, tiempo ~5 min.

### 6.8 Pipeline de ingesta

Script idempotente e incremental:

1. Lee docs de Postgres.
2. Chunking por tipo.
3. Contextual retrieval header (Haiku).
4. Batch embed (Voyage, lotes 128).
5. Upsert Qdrant con payload.
6. Registra en `rag_ingestion_log` para incremental.

ID de punto Qdrant = `hash(doc_id + chunk_idx + embedding_model)` → sin duplicados al re-correr.

### 6.9 Evals de RAG

- **Golden dataset** (~40 queries etiquetadas) — relevant SKUs + must-not-appear.
- **Métricas deterministas:** Recall@10 ≥ 0.85, MRR ≥ 0.6, NDCG@10 ≥ 0.7.
- **Métricas LLM-as-judge (RAGAS):** Faithfulness ≥ 0.95, Answer Relevance ≥ 0.9, Context Relevance ≥ 0.8.
- Corren en `make evals-rag` local (subset) y `make evals-full` en CI.

### 6.10 Diferido a Fase 2+

- Multi-vector / ColBERT
- HyDE
- Query decomposition
- Graph-RAG sobre KG de productos

---

## 7. Governance, guardrails, policies, evals

### 7.1 Taxonomía de amenazas cubiertas (Fase 1)

1. Prompt injection
2. Jailbreak
3. PII leak (CC, DNI, email, teléfono) → Presidio
4. Topic restriction (off-topic blocking)
5. Hallucination de SKU / precio
6. Unsafe tool call (checkout sin confirmación)
7. Output toxicidad / moderación
8. Data exfiltration (cross-user)
9. Cost runaway (loop infinito de tool calls)

*Rate limiting por usuario queda en Fase 2.*

### 7.2 Herramientas

- **NeMo Guardrails** (OSS, NVIDIA) — runtime rails, DSL Colang, integración LangGraph.
- **Presidio** (OSS, Microsoft) — detección PII con 30+ entidades, soporte español.
- **Guardrails AI** (OSS) — validación estructurada de outputs (complementa Pydantic).
- **Pydantic v2** — structured output tipado en tool calls y responses.

### 7.3 Input rails (`rails/input.yml`)

- `check_jailbreak` (LLM-judge con Haiku)
- `self_check_input` (NeMo built-in)
- `detect_pii` (Presidio: bloquea CC/DNI; redacta email/teléfono)
- `topic_restriction` (solo compras/productos/envíos/devoluciones)
- `injection_heuristics` (regex + firmas conocidas)

### 7.4 Output rails (`rails/output.yml`)

- `self_check_output` (NeMo built-in)
- `no_invented_skus` (regex + DB check)
- `price_matches_catalog` (DB)
- `structured_output_ok` (Pydantic)
- `moderation` (modelo de moderación; Llama Guard en Fase 1 si entra local, si no, modelo Anthropic)

### 7.5 Policies-as-code

Reglas de negocio tipadas con tests unitarios exhaustivos:

- `PricingService` — max 30 % descuento, no stackable, min order total $20.
- `StockService` — no permite checkout si `stock < qty`.
- `BudgetService` — HITL si `total > $500` o `discount > 30 %`.

**El LLM nunca calcula precio final.** Sugiere, el dominio calcula.

### 7.6 Red-team dataset

~70 ataques en `tests/evals/redteam/`:

- `prompt_injection.jsonl` (30)
- `pii_leak.jsonl` (20)
- `jailbreak.jsonl` (15)
- `hallucination.jsonl` (20)
- `off_topic.jsonl` (15)
- `cost_attacks.jsonl` (5)

Cada entrada: `{"input": "...", "expected_behavior": "block|safe_refusal|clarify", "tag": "..."}`. Meta: **block rate ≥ 95 %** (sin tolerancia en CI gate).

### 7.7 Evals — estructura

```
tests/evals/
├── datasets/
│   ├── golden_conversations.jsonl   (30 flows completos)
│   ├── rag_golden.jsonl             (40 queries + relevant SKUs)
│   ├── router_golden.jsonl          (50 mensajes + intent)
│   └── redteam/                     (ver 7.6)
├── evaluators/
│   ├── llm_judge_faithfulness.py
│   ├── llm_judge_relevance.py
│   ├── llm_judge_safety.py
│   ├── deterministic/
│   │   ├── sku_valid.py
│   │   ├── price_valid.py
│   │   └── intent_accuracy.py
│   └── end_to_end_task_success.py
└── run.py                           (CLI → LangSmith)
```

### 7.8 LLM-as-judge discipline

- Juez **distinto** del modelo generador.
- Prompt canónico versionado, **temperatura 0**.
- Rubric binario + explicación.
- **Calibración formal:** 30 juicios manuales vs juez, se mide **Cohen's kappa**. Si κ < 0.6, re-prompt del juez antes de confiar.
- Verdict caching por `hash(input + prompt)`.

### 7.9 CI gates

Un PR se bloquea si, comparado con `main`, alguna métrica empeora más del delta permitido:

| Métrica | Umbral | Delta |
|---|---|---|
| Router accuracy | ≥ 0.90 | −0.02 |
| RAG Recall@10 | ≥ 0.85 | −0.02 |
| Faithfulness | ≥ 0.95 | −0.01 |
| Red-team block rate | ≥ 0.95 | 0 |
| End-to-end task success | ≥ 0.80 | −0.03 |
| Cost / conversación | ≤ $0.08 | +10 % |
| Latencia p95 | ≤ 6 s | +15 % |

Override posible vía commit message `eval-override: <razón>` (visible en PR, auditable).

### 7.10 Flujo de desarrollo con evals

1. Cambio de prompt / nodo.
2. Local: `make evals-quick` (15 casos, ~1 min, <$0.05).
3. PR: CI corre `make evals-full` (130 casos, ~10 min, ~$0.30).
4. LangSmith comenta tabla delta en PR.
5. Revisar casos regresivos.
6. Merge o iterar.

### 7.11 Consumo LangSmith free tier (5 k traces / mes)

- Dev local: tracing on siempre (~3 k traces presupuesto personal).
- CI: `evals-full` solo en `main` / `release/*`. PRs usan runs offline a JSONL para no agotar cuota.
- Monitoreo mensual del consumo para ajustar.

---

## 8. Observabilidad

### 8.1 Dos mundos — LLM vs App/Infra

| Aspecto | LangSmith | OTel + Prometheus |
|---|---|---|
| Qué captura | Prompts, respuestas, tool calls, tokens, costo, evals | Latencia endpoints, SQL, HTTP externo, CPU, RAM |
| Granularidad | Por turno conversacional | Por request HTTP, por query SQL |
| Auto-instrumentación | env var `LANGCHAIN_TRACING_V2=true` | `opentelemetry-instrument <cmd>` |
| Dónde brilla | "¿Por qué el agente respondió X?" | "¿Por qué el endpoint está lento?" |

### 8.2 LangSmith — jerarquía y setup

- Organization → Projects → Runs.
- Projects separados: `shopping-copilot-dev`, `-ci`, `-prod`.
- Setup: 4 env vars (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_ENDPOINT`, `LANGCHAIN_API_KEY`, `LANGCHAIN_PROJECT`). Cero código.

### 8.3 Metadata y tags (una línea al invocar grafo)

```python
config = {
    "configurable": {"thread_id": conversation_id},
    "metadata": {"user_id": u.id, "env": s.env, "agent_version": s.git_sha},
    "tags": ["shopping", f"v:{s.git_sha[:7]}"],
}
```

Habilita filtros brutales en LangSmith UI.

### 8.4 Feedback del usuario

Botones 👍 👎 en UI → `POST /feedback` → `langsmith.create_feedback(run_id, key="user_rating", score=0|1, comment)`.

### 8.5 Prompt Hub (Fase 2)

Fase 1: prompts como archivos Jinja en `agents/prompts/`.
Fase 2: migración a LangSmith Prompt Hub (versionado central, A/B en prod, rollback en un click).

### 8.6 OTel auto-instrumentation (Fase 1)

Dependencias:

```
opentelemetry-distro
opentelemetry-exporter-otlp
opentelemetry-instrumentation-fastapi
opentelemetry-instrumentation-httpx
opentelemetry-instrumentation-sqlalchemy
opentelemetry-instrumentation-redis
opentelemetry-instrumentation-asyncpg
```

Setup único ~30 líneas en `observability/otel.py`.
**Export Fase 1: console** — spans impresos en terminal, pedagógico.
**Export Fase 2: Tempo** — cambio de env var.

### 8.7 Métricas y logs

- `prometheus-fastapi-instrumentator` → `/metrics` (latencia, rps, errores por endpoint).
- `structlog` JSON a stdout, con `trace_id` inyectado por hook OTel.

### 8.8 Dónde mirar según síntoma

| Síntoma | Dónde primero |
|---|---|
| "Respondió cualquier cosa" | LangSmith — trace del turno |
| "Está lento" | OTel console + LangSmith latency por span |
| "Está caro" | LangSmith cost report |
| "RAG no trae lo correcto" | LangSmith `search_node` input/output |
| "Fallan checkouts" | structlog filter `event=checkout_failed` |
| "Loop infinito" | OTel trace del request — tool calls count |

### 8.9 Diferido a Fase 2+

- Langfuse self-host (alternativa OSS)
- Stack LGTM: Grafana, Prometheus, Loki, Tempo
- Alertas (Slack/PagerDuty)
- Prompt Hub

---

## 9. Roadmap de Fase 1 (3–4 semanas)

### Prerrequisitos antes de arrancar

**Cuentas y API keys:**

- [ ] Anthropic (pagado, budget cap $30)
- [ ] OpenAI (pagado, budget cap $10)
- [ ] Voyage AI (free tier 50M tok/mes)
- [ ] LangSmith (free tier 5k traces/mes)
- [ ] GitHub (repo + Actions)

**Software local:**

- [ ] Python 3.12 (pyenv)
- [ ] `uv` instalado
- [ ] Docker Desktop corriendo
- [ ] Cursor + PyCharm Community
- [ ] Git con email Bayteq
- [ ] `make`

### Semana 1 — Fundaciones + primer flujo E2E trivial

**Objetivo:** repo scaffoldeado, arquitectura sólida, agente trivial respondiendo y trazado.

**Bloques:**

- Setup proyecto (uv, ruff, mypy, pre-commit, estructura Clean Arch)
- Docker Compose (Postgres + Qdrant + Redis), `make up/down/reset`
- `pydantic-settings` + `.env.example`
- Domain mínimo (`Sku`, `Money`, `Product`) + puertos `LLMPort`, `EmbeddingsPort`, `VectorStorePort`, `CatalogPort`
- Adapters: `AnthropicAdapter`, `VoyageAdapter`
- Seed inicial (20 laptops sintéticas → Postgres + Alembic)
- FastAPI `/health` + `/chat` (nodo único tipo echo-con-Claude)
- Streamlit `app.py` consumiendo `/chat`
- LangSmith tracing verificado en UI
- CI básica (lint + mypy + unit tests)

**Entregable:** Streamlit → "hola" → Claude responde → trace en LangSmith con tokens y costo.

**Conceptos nuevos (explicar inline al implementar):** Port/Adapter en Python (`Protocol`), uv, ruff, mypy --strict, pydantic-settings, SQLAlchemy 2 async, Alembic, Pydantic DTOs, LangSmith tracing básico, token, costo, prompt caching.

### Semana 2 — RAG completo + primer grafo LangGraph

**Objetivo:** búsqueda semántica funcional sobre catálogo real, cero alucinación de SKU.

**Bloques:**

- Seed completo (200 productos + 1 000 reseñas + 30 FAQs)
- Pipeline ingesta: chunking, contextual retrieval, embeddings Voyage, upsert Qdrant
- Qdrant: colección + **payload indexes** + text index
- Retrieval híbrido: semántico + BM25 + RRF + Voyage rerank
- `SearchProductsUseCase`
- Primer grafo LangGraph: `START → router → search → output_guardrails → END` con checkpointer Postgres
- Router node (Haiku + structured output)
- Prompts en Jinja versionados
- RAG evals v1: 20 queries, Recall@10 ≥ 0.85

**Entregable:** "quiero una laptop para diseño bajo $1500" → respuesta con 3–5 productos reales, trace completo, RAG Recall@10 ≥ 0.85.

**Conceptos:** chunking por tipo, embeddings (dense vectors, dims, normalización, input types), cosine vs dot product, HNSW, payload index (por qué sin ellos los filtros son O(n)), BM25, retrieval híbrido, RRF, cross-encoder vs bi-encoder, contextual retrieval, parent-document, LangGraph (`StateGraph`, nodes, edges, `TypedDict`, `add_messages`), checkpointer, `thread_id`, structured output Pydantic, LLM-as-judge faithfulness, Recall@K / MRR / NDCG.

### Semana 3 — Multi-agente completo + guardrails + HITL

**Objetivo:** copiloto end-to-end con carrito, comparaciones, checkout + HITL, guardrails activos.

**Bloques:**

- Dominio ampliado (`Cart`, `CartItem`, `Order`, `Discount`, `StockLevel`)
- Puertos: `CartPort`, `PaymentPort`, `NotificationPort`
- Adapters: `RedisCartAdapter`, `MockPaymentAdapter`, `ConsoleNotificationAdapter`
- Use cases: `CompareProductsUseCase`, `AddToCart`, `Checkout`, `EscalateToHuman`
- Grafo completo (router + search + comparator + cart + checkout + smalltalk + out_of_scope + guardrails)
- HITL: `interrupt()` + botones Streamlit Aprobar/Rechazar + `/resume`
- NeMo Guardrails `config.yml` (jailbreak, PII Presidio, injection, topic)
- `no_invented_skus` rail custom
- Policies-as-code (pricing, stock, budget) + tests
- Red-team v1 (30–50 ataques)

**Entregable:** conversación de 8–10 turnos (buscar → comparar → carrito → cupón → checkout → aprobar → orden). Red-team > 90 % bloqueado.

**Conceptos:** LangGraph avanzado (conditional edges, `Command`, interrupts, resume), model cascading, NeMo Guardrails + Colang, Presidio (entities, recognizers, anonymization), prompt injection defense-in-depth, Guardrails AI structured output, policy-as-code vs prompt-driven, combinación guardrails + policies + tool calling.

### Semana 4 — Evals completos + CI gates + observabilidad + pulido

**Objetivo:** calidad "defendible"; cualquier cambio futuro protegido por evals; listo para Fase 2.

**Bloques:**

- Suite evals (faithfulness, relevance, safety, task_success) + deterministic (sku_valid, price_valid, intent_accuracy)
- Datasets LangSmith: `golden_conversations`, `rag_golden`, `router_golden`, `redteam`
- Calibración del juez (30 juicios manuales → Cohen's kappa)
- GitHub Actions: `make evals-full` en PR, comentario con tabla delta, gates activos
- OTel auto-instrumentation + console exporter
- structlog JSON con `trace_id`
- `prometheus-fastapi-instrumentator` expuesto
- Iteración de prompts hasta alcanzar umbrales
- README, arquitectura, runbook setup
- **Opcional:** migración inicial a Next.js + Vercel AI SDK

**Entregable:** PR con cambio de prompt → CI corre 130 evals en 10 min → tabla delta en PR → mergeable o bloqueado con razón. README completo (setup en <30 min).

**Conceptos:** LLM-as-judge discipline (calibración, Cohen's kappa, agreement), rubrics, regression testing, CI gates declarativos, OTel spans/attributes/context propagation, auto vs manual instrumentation, correlación logs/traces/metrics vía `trace_id`, SLOs/SLIs para agentes, (opcional) SSE streaming tool calls, Vercel AI SDK, interrupts en cliente.

---

## 10. Definition of Done — Fase 1

**Funcional:**

- [ ] Conversación multi-turno: buscar → comparar → carrito → checkout → orden
- [ ] HITL operativo (compra > $500 requiere aprobación)
- [ ] Guardrails bloquean injection, PII, jailbreak, off-topic
- [ ] Cero hallucination de SKU/precio (validado por rail)
- [ ] HITL resume funciona tras reinicio del proceso (checkpointer)

**Calidad:**

- [ ] Router accuracy ≥ 0.90
- [ ] RAG Recall@10 ≥ 0.85, Faithfulness ≥ 0.95
- [ ] Red-team block rate ≥ 0.95
- [ ] E2E task success ≥ 0.80 sobre golden

**Operacional:**

- [ ] CI con evals en PR + gates activos
- [ ] LangSmith tracing + feedback 👍👎 operativo
- [ ] OTel + structlog en console
- [ ] `make up` levanta todo
- [ ] Docs: README, arquitectura, runbook

**Económico:**

- [ ] Costo estimado < $0.08 / conversación
- [ ] Latencia p95 < 6 s / turno
- [ ] LangSmith consumo ≤ 4 k traces / mes

---

## 11. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| LangSmith free tier se agota | Alta | `evals-full` solo en `main`/`release`; PRs offline |
| Evals inestables (juez no determinístico) | Media | T=0 en juez + cache verdicts + calibración formal κ ≥ 0.6 |
| NeMo Guardrails curva de aprendizaje | Media | Empezar con rails built-in; custom después |
| Postgres / Qdrant out-of-sync en seed | Media | Seed idempotente + test `catalog == qdrant payload` |
| Costo Anthropic dispara en dev | Baja-Media | Budget cap $30; Haiku default; cost guard en grafo |
| Scope creep | **Alta** | Lo no listado en este spec → Fase 2 por principio |

---

## 12. Hoja de ruta a largo plazo

### Fase 2 — Realismo empresarial

- **LiteLLM** como dev gateway (virtual keys, budget per-team, cost tracking, caching, fallback OpenAI↔Anthropic)
- **Spring Boot gateway** delante del agente Python (auth, auditoría, integración legacy simulada)
- **Langfuse self-host** como alternativa OSS a LangSmith (aprender self-host)
- **Stack LGTM** (Grafana + Prometheus + Loki + Tempo) por Docker Compose
- **OAuth2 / JWT** para auth real
- **Alertas básicas** en Slack
- **Prompt Hub** (LangSmith) para versionado y A/B

### Fase 3 — Platform gateway prod-grade

- **Kong AI Gateway** al edge con unified LLM API, semantic cache, guardrails empresariales, audit trail a SIEM simulado, RBAC por consumidor, rate limiting por tokens
- **Arize Phoenix** para evals offline avanzadas
- **Multi-vector / ColBERT retrieval**
- **Query decomposition** avanzada
- **PagerDuty + runbooks**

### Fase 4 — Evolución producto

- Memoria de largo plazo y personalización
- Multi-tenant real
- Fine-tuning / LoRA con datos de carrito
- Multimodalidad (imágenes de producto)
- A/B testing de prompts en producción

---

## 13. Tracker interactivo de progreso

Se entrega también una página HTML autónoma en [`docs/progress/plan.html`](../../progress/plan.html) que:

- Lista todas las semanas con bloques marcables
- Persiste progreso en `localStorage` del navegador
- Muestra % de avance por semana y global
- Incluye prerequisitos, Definition of Done y conceptos por semana
- Botón de export/import JSON (backup)
- Botón de reset total

No requiere backend — se abre directamente en navegador (`open docs/progress/plan.html` en macOS).

---

## 14. Anexos

### 14.1 Glosario abreviado de conceptos

*La lista completa está en la feedback memory [`teach_concepts_inline`](../../../../../.claude/projects/...). Se explican todos inline al aparecer por primera vez.*

| Término | En 1 línea |
|---|---|
| Chunking | Partir documentos en trozos más chicos para indexar |
| Embedding | Vector de floats que representa semántica de un texto |
| BM25 | Algoritmo clásico de ranking léxico (TF-IDF evolucionado) |
| RRF | Reciprocal Rank Fusion — combina rankings distintos |
| Reranker | Modelo que re-puntúa candidatos con query+doc juntos |
| Cross-encoder | Arquitectura del reranker (más preciso, más caro) |
| Bi-encoder | Arquitectura de embeddings (rápido, menos preciso solo) |
| HNSW | Algoritmo del índice vectorial de Qdrant (grafo jerárquico) |
| Payload index | Índice de Qdrant sobre campos de metadata para filtros rápidos |
| Contextual Retrieval | Técnica Anthropic: prepend de contexto antes de embedder |
| Parent-document | Indexar chunks chicos, devolver doc padre al LLM |
| LLM-as-judge | Usar otro LLM para puntuar respuestas (faithfulness, relevance) |
| Cohen's kappa | Métrica de agreement entre juez LLM y juez humano |
| Checkpointer | Persistencia del estado del grafo LangGraph |
| Interrupt | Pausa del grafo para HITL; resume con `Command(resume=...)` |
| Model cascading | Usar modelo barato para clasificar, caro para razonar |
| Guardrail | Validación runtime de input / output del agente |
| Policy-as-code | Reglas de negocio en código tipado, no en prompts |
| Structured output | Respuesta del LLM validada con Pydantic / JSON schema |
| RAGAS | Librería Python para evaluar pipelines RAG |

### 14.2 Referencias

- LangGraph docs: https://langchain-ai.github.io/langgraph/
- LangSmith docs: https://docs.smith.langchain.com/
- Qdrant docs: https://qdrant.tech/documentation/
- Voyage AI: https://docs.voyageai.com/
- Anthropic Contextual Retrieval: https://www.anthropic.com/news/contextual-retrieval
- NeMo Guardrails: https://docs.nvidia.com/nemo/guardrails/
- Presidio: https://microsoft.github.io/presidio/
- RAGAS: https://docs.ragas.io/
- Vercel AI SDK: https://sdk.vercel.ai/

---

**Fin del spec.** El siguiente paso es que Jorge lo revise; tras aprobación se invoca la skill `writing-plans` para producir el plan de implementación paso a paso de la Semana 1.
