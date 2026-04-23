# Diario de aprendizaje — Brainstorming agentic-AI

- **Fecha:** 2026-04-23
- **Participantes:** Jorge (Bayteq) — aprendiz · Claude Opus 4.7 — guía
- **Propósito:** documentar el proceso de brainstorming que derivó en el spec
  [`2026-04-23-retail-shopping-copilot-design.md`](../superpowers/specs/2026-04-23-retail-shopping-copilot-design.md).
  Aquí viven las **preguntas, comparaciones y razonamientos** — el *porqué* detrás de cada decisión del spec.

---

## Índice

1. [Cómo elegir un caso de uso para aprender agentic-AI](#1-cómo-elegir-un-caso-de-uso-para-aprender-agentic-ai)
2. [LangSmith — qué es y para qué sirve](#2-langsmith--qué-es-y-para-qué-sirve)
3. [Python puro vs híbrido — la realidad empresarial](#3-python-puro-vs-híbrido--la-realidad-empresarial)
4. [Kong AI Gateway vs LiteLLM — gobernanza en el borde](#4-kong-ai-gateway-vs-litellm--gobernanza-en-el-borde)
5. [Decisión de proveedores LLM y embeddings](#5-decisión-de-proveedores-llm-y-embeddings)
6. [Arquitectura swappable + IDE + stack de observabilidad](#6-arquitectura-swappable--ide--stack-de-observabilidad)
7. [Qdrant vs pgvector — y el resto del mercado](#7-qdrant-vs-pgvector--y-el-resto-del-mercado)
8. [Streamlit vs Next.js — elecciones de UI por fases](#8-streamlit-vs-nextjs--elecciones-de-ui-por-fases)
9. [Ruff-only + telemetría sin código custom](#9-ruff-only--telemetría-sin-código-custom)
10. [Arquitectura general y capas (Clean Architecture aplicada a agentes)](#10-arquitectura-general-y-capas-clean-architecture-aplicada-a-agentes)
11. [Componentes y módulos del proyecto](#11-componentes-y-módulos-del-proyecto)
12. [Flujo conversacional y grafo LangGraph](#12-flujo-conversacional-y-grafo-langgraph)
13. [RAG pipeline moderno paso a paso](#13-rag-pipeline-moderno-paso-a-paso)
14. [Governance: guardrails + policies + evals](#14-governance-guardrails--policies--evals)
15. [Observabilidad completa (LLM + app + infra)](#15-observabilidad-completa-llm--app--infra)
16. [Roadmap por fases (1–4)](#16-roadmap-por-fases-1-4)

---

## 1. Cómo elegir un caso de uso para aprender agentic-AI

**Pregunta de Jorge:** quiero entrar al mundo agentic-AI y tocar LangGraph, LangFlow, LangSmith,
governance, tracing, monitoring, RAG, búsqueda semántica, etc. ¿Qué caso de uso real me propones?

### Criterio de selección

Para ejercitar *todos* los conceptos, el caso ideal combina **documentos + datos estructurados + acciones**.
Un caso demasiado simple no toca gobernanza ni evals en serio; uno demasiado regulado (salud real) te atasca en compliance.

### Cuatro opciones evaluadas

| Opción | Rol pedagógico |
|---|---|
| **A)** Asistente legal/compliance interno | Buen terreno para governance y citación de fuentes |
| **B)** Copiloto de soporte técnico / DevOps | Multi-agente natural (triage → diagnóstico → acción) |
| **C)** Analista conversacional (text-to-SQL + RAG) | Ideal para text-to-SQL seguro y evals |
| **D)** Procurement/supply-chain agent | Cercano al contexto Pronaca/Bayteq, HITL rico |

### Giro hacia retail vs salud

Jorge propuso salud o retail (ej: carrito de compras). Conclusión:

- Un **carrito** a secas es CRUD fino, pero subido a **copiloto de compras conversacional** se vuelve rico.
- **Salud** fuerza gobernanza en serio (PII, disclaimers, red-teaming, handoff a humano) → mejor ingeniero de agentes, pero más fricción.
- **Retail + nivel de gobernanza empresarial** = sweet spot pedagógico: demos vistosas + guardrails serios.

### Decisión

**Retail Shopping Copilot** con governance "grado salud":
- Guardrails de entrada (prompt injection, PII)
- Guardrails de salida (no inventar productos/precios, no recomendar out-of-stock)
- Confidence scoring + fallback humano
- Red-teaming sistemático con dataset de ataques
- Políticas de precio/descuento como tool separado (no en el LLM)
- Auditoría completa en LangSmith + métricas de negocio

---

## 2. LangSmith — qué es y para qué sirve

**Pregunta de Jorge:** ¿dónde entra LangSmith exactamente?

### Respuesta sintetizada

LangSmith es la **plataforma de observabilidad + evaluación** de LangChain. Cuatro usos concretos:

1. **Tracing** — cada conversación queda grabada como un árbol: prompt → retrieval → tool call → respuesta,
   con tokens, latencia y costo por nodo. Reemplaza los `print()` de un backend tradicional.

2. **Datasets + Evals** — guardas conversaciones reales/sintéticas como dataset de prueba, y defines evaluators
   (LLM-as-judge, regex, human feedback) que corren sobre cada cambio del agente. Es tu *suite de tests* para agentes.

3. **Prompt Hub + versionado** — prompts versionados fuera del código, con A/B testing entre versiones.

4. **Monitoring en producción** — dashboards de latencia, costo, error rate, feedback de usuario;
   alertas cuando el agente se degrada (p. ej. sube la tasa de "no sé responder").

### Regla mental

**LangGraph** es el runtime del agente. **LangSmith** es la torre de control (dev + prod). Son complementarios.

---

## 3. Python puro vs híbrido — la realidad empresarial

**Observación de Jorge:** Python puro no es el común de los escenarios empresariales; muchos clientes tienen soluciones en Java/.NET/Node.

### Tres opciones de stack

- **A) Python puro** — FastAPI + LangGraph + LangSmith. Camino canónico, máximo material, más rápido para aprender.
- **B) Híbrido** — Python para el agente + Spring Boot como API gateway/backoffice. **Realidad empresarial real**, dobla complejidad al inicio.
- **C) Java con LangChain4j** — aprovechas el stack de Jorge, pero LangFlow no existe para Java y LangGraph-Java está verde.

### Decisión — "A por fases"

- **Fase 1 (MVP learning):** Python puro. Aprendes LangGraph/Smith/Flow/RAG/evals sin ruido de cruzar lenguajes.
- **Fase 2 (enterprise realism):** metemos un gateway Spring Boot por delante (auth, rate limit, auditoría, integración con catálogo corporativo "legacy") y el agente Python queda como servicio interno. Aquí se aprende el *patrón real* de clientes.

No se sacrifica ni aprendizaje ni realidad.

### Qué construiríamos en Fase 1 — inventario concreto

1. **Agent core (LangGraph):** grafo multi-agente (router, search, comparator, cart, checkout guardian), estado compartido, HITL node.
2. **RAG pipeline:** ingesta, chunking, embeddings, vector store (Qdrant), retriever híbrido + re-ranking.
3. **Tools del agente:** `search_catalog`, `get_product_details`, `compare_products`, `add_to_cart / remove / update`, `apply_coupon`, `checkout`.
4. **Datos simulados:** catálogo ~200 productos, Postgres + Redis, reseñas para RAG.
5. **API + UI:** FastAPI (`/chat`, `/stream`, `/feedback`), UI Streamlit (rápida) o Next.js + chat SDK (realista).
6. **Governance & guardrails:** detección de prompt injection + PII, validación estructurada (Pydantic), bloqueo de out-of-stock, policy-as-code para precio/descuento, red-team en CI.
7. **Observabilidad (LangSmith):** tracing, 50 conversaciones "golden", evaluators (LLM-as-judge, regex, custom), dashboard.
8. **LangFlow:** para diseñar visualmente variantes del grafo antes de llevarlas a código. No en producción.
9. **Infra local:** Docker Compose (Postgres + Qdrant + Redis + FastAPI + Streamlit), `.env`, Makefile.
10. **CI/CD mínimo:** tests unitarios de tools + corrida de evals al hacer push a `main`.

---

## 4. Kong AI Gateway vs LiteLLM — gobernanza en el borde

**Pregunta de Jorge:** ¿qué gana Kong Enterprise para governance/trazabilidad? ¿Y LiteLLM?

### Kong AI Gateway

- **Unified LLM API** — un solo endpoint abstrae OpenAI/Anthropic/Bedrock/Azure; cambiás proveedor sin tocar código.
- **Rate limiting por tokens** (no solo requests) y **budget caps** por consumidor/equipo.
- **Semantic caching** en el edge — cachea respuestas similares (ahorro 30–70 % en costo/latencia).
- **Guardrails en el borde** — PII redaction, moderation, prompt injection *antes* de tocar al LLM → la política la define seguridad, no el dev.
- **Audit trail centralizado** — quién llamó qué modelo con qué prompt, con hash para cumplimiento.
- **Circuit breaker + fallback** — si OpenAI se cae, ruta a Anthropic automáticamente.
- **RBAC + API keys por consumidor** — integrable con SSO corporativo.
- **Observability nativa** → OTel/Prometheus/Datadog.

**Valor central:** desacopla políticas del código del agente — clave en empresas reguladas.

### LiteLLM (el "hermano liviano")

- Proxy/SDK open source que unifica 100+ LLMs bajo formato OpenAI.
- Virtual keys con budget per-team, cost tracking en Postgres/S3, caching en Redis, fallbacks, UI admin.
- Python-first, perfecto para equipos de datos/ML, se monta en una tarde.

### Cómo conviven

No son excluyentes. Patrón empresarial típico:
- **Kong al edge** (políticas corporativas, edge security)
- **LiteLLM interno** (devex para el equipo de IA, cost per-project)

LiteLLM es el "dev gateway", Kong el "platform gateway".

### Hoja de ruta anclada

- **Fase 1 — MVP Python puro:** llamadas directas a OpenAI/Anthropic, sin gateway.
- **Fase 2 — Dev gateway:** **LiteLLM** como proxy + Spring Boot gateway por delante del agente.
- **Fase 3 — Platform gateway prod-grade:** **Kong AI Gateway** al edge con guardrails empresariales, semantic cache, audit trail.
- **Fase 4 (opcional):** memoria largo-plazo, multi-tenant, fine-tuning, A/B de prompts en prod.

---

## 5. Decisión de proveedores LLM y embeddings

**Pregunta de Jorge:** ¿voy con mix multi-proveedor (C) para probar routing, o solo Anthropic (B) para aprender primero?

### Razonamiento

Routing entre proveedores es *exactamente* lo que LiteLLM resuelve en Fase 2. Implementarlo a mano ahora reinventa la rueda.

Claude Sonnet 4.6 + Haiku 4.5 ya permiten **routing interno por complejidad de tarea**:
- **Sonnet** para razonamiento complejo (router, comparador)
- **Haiku** para tareas simples (extracción, clasificación)

### Decisión

- **Generación:** Anthropic (Sonnet 4.6 + Haiku 4.5)
- **Embeddings:** Voyage AI (`voyage-3-lite`, partner de Anthropic, top retrieval benchmarks, free tier 50M tok/mes)

Fase 1 ya tiene **dos proveedores por necesidad**, pero no "routing cruzado" — cada uno hace lo que mejor sabe.
En Fase 2, con LiteLLM, sumamos fallback OpenAI↔Anthropic, semantic cache, cost routing, A/B de modelos.

---

## 6. Arquitectura swappable + IDE + stack de observabilidad

**Pregunta de Jorge:** voy con Voyage y luego cambio a OpenAI — ¿no debería ser crítico con buena arquitectura, no? ¿Qué IDE recomendás? ¿Qué herramientas para trazabilidad/monitoring además de LangSmith?

### Swappable providers (port/adapter pattern)

Diseñado con:
- `EmbeddingsPort` (interface) + `VoyageAdapter` / `OpenAIAdapter` / `CohereAdapter`
- `LLMPort` + `AnthropicAdapter` / `OpenAIAdapter`
- Inyección vía factory + `settings.yaml` (o `pydantic-settings`)
- Tests de contrato por adaptador (mismo input → misma forma de output)

LangChain ya expone `Embeddings` y `BaseChatModel` — les añadimos nuestra capa cuando aporta (métricas, cache, fallback).

### IDE — recomendación

- **Primario:** **Cursor** — VS Code + AI nativo, extensiones Python, Jupyter integrado. Mejor DevEx para iterar grafos LangGraph rápido.
- **Secundario:** **PyCharm Community** (gratis) — debugger superior para estado complejo de LangGraph, pytest parametrizado, profiling.
- **VS Code:** lo saltamos. Cursor ya es "VS Code + AI".

### Stack de observabilidad completo

Distinción crítica: **observabilidad de LLM/agente** vs **observabilidad de app/infra**. Se necesitan las dos.

**Capa LLM/agente (trazas semánticas):**
- **LangSmith** — primario Fase 1. Trazas del grafo, evals, datasets, playground. SaaS, free tier generoso.
- **Langfuse** — alternativa **OSS self-hostable** (Docker). Fase 2 para aprender self-host.
- **Arize Phoenix** — OSS, OTel-nativo, excelente para evals offline. Opcional Fase 3.

**Capa app/infra (métricas + logs clásicos):**
- **OpenTelemetry** — estándar. Instrumentamos FastAPI + LangGraph con OTel. Las trazas se exportan a LangSmith **y** a un collector.
- **Grafana + Prometheus + Loki + Tempo** (stack "LGTM") — Fase 2. Prometheus para métricas, Loki para logs, Tempo para trazas OTel. Docker Compose, sin coste.
- **Sentry** (opcional) — errores de aplicación y alertas.

### Stack final por fases

| Fase | LLM/agente | App/infra |
|---|---|---|
| 1 | LangSmith | Logs simples + OTel básico |
| 2 | LangSmith + Langfuse self-host | Stack LGTM (Grafana+Prom+Loki+Tempo) |
| 3 | + Phoenix (evals offline) | + Sentry + alertas |

Así Jorge aprende **el espectro completo**: SaaS vs self-host, LLM-native vs OTel-native, real-time vs batch.

---

## 7. Qdrant vs pgvector — y el resto del mercado

**Pregunta de Jorge:** ¿qué me recomendás y por qué? ¿En prod qué es mejor? ¿Costo?

### pgvector (extensión Postgres)

- ✅ Una sola pieza de infra — menor overhead operativo, backups unificados, transacciones que cruzan catálogo + embeddings
- ✅ Gratis (la pagás ya con Postgres)
- ✅ Equipos con DBAs ya saben operarlo
- ❌ HNSW más joven, menor throughput en alta concurrencia
- ❌ Filtros complejos (`WHERE brand=X AND price<Y`) combinados con búsqueda vectorial más lentos
- ❌ Features avanzadas limitadas (sin named vectors, sin quantization nativa)
- **Sweet spot prod:** hasta ~5-10M vectores, cargas moderadas.

### Qdrant (DB vectorial dedicada, Rust)

- ✅ Performance sobresaliente — p95 bajo con millones de vectores
- ✅ **Payload indexing** — filtros con índices invertidos (brutalmente rápido)
- ✅ **Named vectors** (varios embeddings por documento)
- ✅ **Quantization** (scalar/binary/product) → 4-32× menos RAM
- ✅ UI web decente para inspeccionar colecciones
- ✅ Multi-tenancy built-in
- ❌ Una pieza más de infra que operar
- ❌ Sin transacciones con Postgres
- **Sweet spot prod:** >10M vectores, alta concurrencia, filtros complejos, multi-tenant, SLAs estrictos.

### Mapa del mercado

| Tool | Tipo | Cuándo |
|---|---|---|
| **Pinecone** | SaaS managed | No querés operar nada, presupuesto disponible ($70+/mes inicio) |
| **Weaviate** | OSS, similar Qdrant | Módulos de generación built-in |
| **Milvus** | OSS, empresarial | Big-tech scale, tolerancia a complejidad |
| **Chroma** | OSS, developer-first | Prototipos muy simples, embedded |
| **LanceDB** | Embedded (SQLite-style) | Apps locales, edge |
| **Elasticsearch/OpenSearch kNN** | Híbrido | Ya tenés ES operando |
| **Redis + RediSearch** | In-memory | Datasets pequeños, baja latencia extrema |

### Costos reales

- pgvector self-host: solo pagás el Postgres que ya pagarías
- Qdrant self-host: solo la VM
- Qdrant Cloud: free 1GB, después ~$25/mes por nodo
- Pinecone Starter: $70/mes, escala rápido
- Weaviate Cloud: $25/mes starter

### Decisión — Qdrant

Razones pedagógicas:
1. Aprendés el patrón productivo real (capa vectorial separada es lo común en empresas serias).
2. Su UI web te deja **ver qué está pasando** (embeddings, filtros).
3. Los filtros avanzados te obligan a **pensar en schema de metadatos** (50 % de hacer RAG bien).
4. Portable: los conceptos (collections, payload, HNSW params) son los mismos en Pinecone/Weaviate.
5. Gracias al port/adapter haremos un adapter **pgvector en Fase 2** como ejercicio.

### Nota aprendida después

**Payload indexes no se crean solos.** Hay que llamar `create_payload_index()` explícitamente por cada campo filtrable.
Sin índice, un filtro `price < 1500 AND category = "laptop"` escanea O(n).

---

## 8. Streamlit vs Next.js — elecciones de UI por fases

**Pregunta de Jorge:** el tiempo no me importa, quiero aprender bien.

### Streamlit

- Todo en Python, mismo ecosistema
- Chat widgets built-in (`st.chat_input`, `st.chat_message`)
- Un archivo, una corrida
- ✅ Cero context switching, ves el estado del agente fácilmente
- ❌ No aprendés cómo se consume un agente desde un frontend real
- ❌ No patrones streaming profesionales, state management raro

### Next.js + Vercel AI SDK

- Frontend moderno, SSE/streaming real, UI componible
- Vercel AI SDK abstrae `useChat`, streaming, tool calls renderizados
- Aprendés el patrón real cliente-servidor
- Requiere TypeScript básico, saber React
- ❌ Más código, más contexto

### Decisión — las dos en fases

- **Fase 1a (Sem 1–2):** **Streamlit.** Todo Python, ves el estado del agente al lado, cero context switching. Te concentrás en LangGraph, RAG, guardrails, evals sin que el frontend robe atención.
- **Fase 1b (Sem 3–4):** **Next.js + Vercel AI SDK.** Migrás el frontend. Aquí aprendés lo que Streamlit *no* enseña:
  - **SSE streaming** con tool calls renderizados en vivo
  - **Contrato API del agente** (qué eventos emite: `tool_start`, `tool_end`, `interrupt`, `final`)
  - **Human-in-the-loop real** con interrupts + resume
  - **Optimistic UI** para tool calls
  - **Patrón cliente-servidor productivo**

Se ven los dos paradigmas por contraste — pedagógicamente vale oro.

---

## 9. Ruff-only + telemetría sin código custom

### Formatter — Ruff-only

`ruff format` es **drop-in replacement de Black**, 100 % compatible, 30× más rápido.
Usar **ambos** es redundante y puede crear conflictos en pre-commit.

**Decisión:** solo `ruff` (format + lint + import sort en una herramienta).

### Regla de oro de telemetría

**NO custom spans, NO custom metrics, NO wrappers de logging.** Solo auto-instrumentación:

- `opentelemetry-instrumentation-fastapi` — traces automáticos de cada endpoint
- `opentelemetry-instrumentation-httpx` / `requests` — llamadas salientes trazadas
- `opentelemetry-instrumentation-sqlalchemy` / `redis` / `asyncpg`
- **LangSmith** se auto-instrumenta solo con `LANGCHAIN_TRACING_V2=true` + API key. Cero código.
- `prometheus-fastapi-instrumentator` — métricas estándar (latencia, rps, errores)
- `structlog` en JSON para logs

**Frase que resume:** "si el SDK no lo emite solo, no lo necesitamos".

### Metodología de aprendizaje acordada

- Jorge escribe **todo el código**. Claude solo crea documentos en `docs/` (specs, guías, tracker).
- Claude guía comando-por-comando, explica el *por qué* de cada pieza, revisa lo que Jorge escribe, propone ejercicios.
- Claude explica **cada término NLP/IR/RAG la primera vez que aparece** (chunking, embeddings, BM25, RRF, reranker, HITL, etc.).
- Jorge pregunta mucho por naturaleza — valora explicaciones profundas con alternativas, costos y trade-offs productivos.

---

## 10. Arquitectura general y capas (Clean Architecture aplicada a agentes)

### Visión de alto nivel

El sistema es un **copiloto conversacional de compras** donde el usuario chatea en lenguaje natural y un grafo de agentes LangGraph lo guía desde "estoy buscando X" hasta "listo, compré".

- **Router-agent** clasifica intención en cada turno (buscar / comparar / gestionar carrito / checkout / fuera de scope).
- **Agentes especializados** (search, comparator, cart, checkout guardian) ejecutan sub-flujos con sus tools.
- **RAG** le da al comparador contexto rico de reseñas y fichas técnicas.
- **Guardrails** envuelven entrada y salida. **LangSmith** lo graba todo.
- **Human-in-the-loop** frena compras > umbral.

### Capas

```
UI       → Streamlit / Next.js
API      → FastAPI (/chat, /stream, /feedback) + middleware guardrails
Orchestr → LangGraph (router + sub-agents) + checkpointer
Applic.  → Use cases: SearchProducts, Compare, AddToCart, Checkout, Escalate
Domain   → Entities, Value Objects, Domain Services, Ports
Infra    → Adapters (Anthropic, Voyage, Qdrant, Postgres, Redis, Payment-mock)
           + Observability (LangSmith, OTel)
```

**Regla de dependencias (férrea):** hacia adentro. Domain no conoce LangChain ni Anthropic ni nada.
Application conoce Domain. Infrastructure implementa puertos de Domain.
Esto hace que swap `Voyage→OpenAI` o `Anthropic→Bedrock` sea un cambio de una línea.

### Stack técnico decidido

| Capa | Tecnología | Por qué |
|---|---|---|
| Lenguaje | Python 3.12 | Ecosistema agentic maduro |
| Package manager | **uv** | 10-100× más rápido que pip |
| Web framework | FastAPI + Uvicorn | Async nativo, OTel auto-instrumentación |
| Validación | Pydantic v2 | Outputs estructurados del LLM |
| Orquestación agentes | **LangGraph** | State machines, checkpointing, HITL built-in |
| LLM SDK | LangChain + `langchain-anthropic` | Interfaces estables |
| LLM generación | Claude Sonnet 4.6 + Haiku 4.5 | Sonnet razona, Haiku clasifica |
| Embeddings | Voyage `voyage-3-lite` | Top benchmarks retrieval, free tier |
| Vector store | **Qdrant** (Docker) | Filtros potentes, UI web |
| Full-text search | Qdrant BM25 | Retriever híbrido |
| Re-ranker | Voyage `rerank-2-lite` | Sube precisión de RAG |
| DB transaccional | PostgreSQL 16 | Catálogo, órdenes, checkpointer |
| Cache/sesión | Redis | Carrito efímero, rate limiting |
| Guardrails | **NeMo Guardrails** + Pydantic | PII, prompt injection, structured output |
| Prototipado visual | **LangFlow** (Docker) | Diseñar variantes del grafo |
| Tracing/evals | **LangSmith** | Primario Fase 1 |
| UI | Streamlit (1a) / Next.js (1b) | Contraste pedagógico |
| Infra local | Docker Compose | `make up` |
| Tests | pytest + pytest-asyncio + httpx + respx | Unit + integración + contratos |
| Linter/formatter | **Ruff** + mypy --strict | Único formatter |
| Precommit | pre-commit hooks | Ruff + mypy + tests rápidos |
| CI | GitHub Actions | Tests + evals LangSmith en PR |

### Principios no-funcionales

1. **Swappable providers** — todo LLM/embeddings/vector store detrás de un puerto.
2. **Determinismo donde importa** — temperatura 0 en router y guardrails, alta solo en generación al usuario.
3. **Observability-first** — cada nodo del grafo emite trace + métricas. Si no está trazado, no existe.
4. **Fail-safe defaults** — cualquier duda → handoff a humano, nunca inventar.
5. **Policy-as-code** — reglas de precio, descuento y stock viven en código tipado, no en prompts.
6. **Reproducibilidad** — `uv.lock` + versiones fijas de modelo + semilla en evals.
7. **12-factor** — config por env vars, logs a stdout, stateless API.

---

## 11. Componentes y módulos del proyecto

El sistema tiene **8 módulos** con responsabilidades claras, presentados en orden de dependencia (de dentro hacia afuera).

### 11.1 `domain/` — núcleo de negocio (cero dependencias externas)

**Entidades:** `Product`, `Cart`, `CartItem`, `Order`, `User` (minimal)

**Value Objects (inmutables, validados):**
- `Sku` — valida formato, case-normalizado
- `Money` — con currency, evita bugs de float
- `Discount` — porcentaje o absoluto
- `StockLevel` — con método `is_available(qty)`
- `Rating` — 0-5

**Domain services:**
- `PricingService` — aplica descuentos según reglas (policy-as-code)
- `StockService` — consulta y reserva

**Puertos (interfaces — `Protocol` de Python o `ABC`):**

```
LLMPort            → send_messages(messages, tools) -> LLMResponse
EmbeddingsPort     → embed(texts) -> list[Vector]
RerankerPort       → rerank(query, docs) -> list[ScoredDoc]
VectorStorePort    → upsert(points), search(query_vec, filters, k)
CatalogPort        → get_product(sku), find_products(filters)
CartPort           → get(user_id), add, remove, clear
PaymentPort        → charge(amount, method), refund(tx_id)
NotificationPort   → notify_human(context, reason)  # para HITL
```

**Por qué esto importa:** cambiar `Voyage→OpenAI` es crear un `OpenAIEmbeddingsAdapter` que implemente `EmbeddingsPort`.
Cero cambio en `application/`, `agents/`, `api/`. Es lo que preguntan en una entrevista técnica seria.

### 11.2 `application/` — casos de uso

Cada caso de uso es una clase con un único método `execute` (patrón command handler de CQRS).

- `SearchProductsUseCase`
- `CompareProductsUseCase`
- `AddToCartUseCase` / `RemoveFromCartUseCase` / `UpdateCartUseCase`
- `CheckoutUseCase`
- `EscalateToHumanUseCase`

**Analogía con tu mundo:** es *exactamente* como un `CommandHandler` en Quarkus/Spring + Clean Arch.

### 11.3 `agents/` — el grafo LangGraph

```
agents/
├── graph.py          # construye el StateGraph y lo compila
├── state.py          # TypedDict del estado compartido
├── nodes/
│   ├── router.py
│   ├── search.py
│   ├── comparator.py
│   ├── cart.py
│   ├── checkout.py
│   ├── human_approval.py
│   └── guardrails.py
├── edges/conditional.py
└── prompts/*.jinja    # prompts versionados, externos al código
```

**LangGraph es una máquina de estados finita** donde cada nodo es una función Python async. Tiene **checkpointer** (Postgres/Redis) que persiste el estado → un turno puede pausarse (HITL), reanudarse después, retomarse tras un crash. Equivalente a un workflow engine (Temporal/Camunda) orientado a conversaciones LLM.

### 11.4 `infrastructure/` — adaptadores técnicos

```
infrastructure/
├── llm/anthropic_adapter.py
├── embeddings/voyage_adapter.py, openai_adapter.py
├── reranker/voyage_reranker.py
├── vectorstore/qdrant_adapter.py
├── catalog/postgres_catalog.py
├── cart/redis_cart.py
├── payment/mock_payment.py
├── notification/console_notif.py
└── observability/{otel_setup.py, langsmith_setup.py}
```

Cada adapter tiene **tests de contrato** en `tests/contracts/` que validan que todos los adapters de un mismo puerto se comportan igual.

### 11.5 `api/` — capa HTTP (FastAPI)

```
api/
├── main.py
├── deps.py           # DI container (puertos → adaptadores)
├── routers/
│   ├── chat.py       # POST /chat + /stream (SSE)
│   ├── feedback.py   # POST /feedback → LangSmith
│   └── health.py
├── middleware/guardrails.py
└── schemas/          # Pydantic DTOs
```

### 11.6 `guardrails/` — políticas de seguridad

```
guardrails/
├── config.yml          # NeMo Guardrails rails
├── input_rails.py      # PII, prompt injection, topic-restriction
├── output_rails.py     # no inventar SKU, formato, moderation
└── policies/
    ├── pricing.py
    ├── stock.py
    └── budget.py
```

**Regla:** las policies son **Python puro tipado con tests**, no prompts. Precio y stock nunca dependen del LLM.

### 11.7 `observability/` — todo auto-instrumentado

Solo **configuración**, cero código custom:
- `otel.py` — lee `OTEL_EXPORTER_OTLP_ENDPOINT`, registra instruments
- `logging.py` — structlog en JSON
- `metrics.py` — `prometheus-fastapi-instrumentator`

### 11.8 `ui/` — frontend

- Fase 1a: Streamlit en un solo archivo + sidebar con viewer de trace
- Fase 1b: Next.js + Vercel AI SDK (carpeta separada `ui-next/`)

### 11.9 Diagrama de dependencias

```
ui → api → agents → application → domain ← infrastructure
                └→ guardrails
```

**Validación:** import-linter en CI (equivalente Python de ArchUnit).

---

## 12. Flujo conversacional y grafo LangGraph

### 12.1 Mental model de LangGraph

Tres piezas:
1. **State** — un `TypedDict` que fluye entre nodos. Memoria de trabajo del turno + conversación.
2. **Nodes** — funciones `async def node(state) -> state_delta`. Cada nodo lee el estado y devuelve *el delta*. LangGraph hace merge — estilo reducer de Redux.
3. **Edges** — cómo se pasa de un nodo a otro. Fijas o **condicionales** (función que mira el estado y decide el próximo nodo).

**Features críticas:**
- **Checkpointer** — persiste estado después de cada nodo. `thread_id` identifica una conversación. Si el proceso muere, reanuda desde el último checkpoint.
- **Interrupts** — un nodo puede gritar `interrupt("necesito aprobación")` y el grafo **pausa**. Luego `graph.invoke(Command(resume=user_decision), thread_id)` y sigue. HITL de primera clase.

**Comparación:** es como **Temporal/Camunda workflows** pero diseñado para flujos LLM. O un **state machine de Spring Integration** con superpoderes de LLM.

### 12.2 Estado compartido

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

- `add_messages` reducer acumula mensajes turno a turno automáticamente.
- `guardrail_violations` viaja en el estado — cualquier nodo puede verlo y decidir.
- `cost_accumulated_usd` / `tool_calls_log` se usan para evals y análisis.

### 12.3 El grafo completo

```
START
  → input_guardrails (NeMo: PII, prompt injection, topic restriction)
  → router (Haiku 4.5: intent + confidence, structured output)
  → [search | comparator | cart | checkout | smalltalk | out_of_scope]
  → si checkout y requires_human_approval → human_approval (interrupt)
  → output_guardrails (no-invented-SKU, price match, moderation, pydantic)
  → END
```

### 12.4 Responsabilidad de cada nodo

| Nodo | Modelo | Rol |
|---|---|---|
| `input_guardrails` | — (NeMo rules) | Si viola → END con mensaje seguro. T=0. |
| `router` | **Haiku 4.5** | Clasifica intent + confidence (structured output). Costo <$0.001/turno. |
| `search` | **Sonnet 4.6** | Llama `SearchProductsUseCase`. Tool calling. |
| `comparator` | **Sonnet 4.6** | RAG sobre reseñas/specs. Tabla de comparación. |
| `cart` | **Haiku 4.5** | Tools `add/remove/update`. Rápido. |
| `checkout` | **Sonnet 4.6** | Si total > $500 o descuento > 30 % → HITL. |
| `human_approval` | — (interrupt) | Pausa. La UI muestra aprobar/rechazar. |
| `smalltalk` | **Haiku 4.5** | "Hola", "gracias" → no desperdiciar Sonnet. |
| `out_of_scope` | — (template) | "Solo te ayudo con compras, no con X". |
| `output_guardrails` | — | Valida SKU existen, precios coinciden. |

**Patrón clave: model cascading** — Haiku para clasificar/decidir, Sonnet para razonar/generar.

### 12.5 Ejemplo de turno completo

```
Turno 1: "quiero una laptop para diseño bajo $1500"

START
  → input_guardrails (ok)
  → router (Haiku: intent="search", conf=0.92, 150ms, $0.0008)
  → search
     • SearchProductsUseCase.execute(query, {max_price:1500, category:laptop})
     • EmbeddingsPort.embed(...) → vec
     • VectorStorePort.search(vec, filters, k=20)
     • RerankerPort.rerank(query, candidates) → top 5
     • CatalogPort.get_products([skus]) → detalles
     • Sonnet genera respuesta
  → output_guardrails
     • Valida SKU existen ✓
     • Valida precios coinciden ✓
  → END  (total 1.8s, $0.012, 3 spans en LangSmith)

Turno 2: "compara las 3 más ligeras"
  • add_messages acumula historia
  → router → intent="compare"
  → comparator (usa search_results del turno anterior desde checkpointer)
    • Filtra por peso
    • RAG sobre reseñas
    • Sonnet genera tabla markdown
  → END
```

### 12.6 Human-in-the-Loop

Cuando `checkout` detecta `cart.total > $500`:

```python
# human_approval_node
async def human_approval(state):
    decision = interrupt({
        "type": "approval_required",
        "cart_total": cart.total,
        "items": [...],
        "reason": "Monto supera umbral"
    })
    # Se pausa hasta graph.invoke(Command(resume=decision), thread_id)
    return {"human_decision": decision}
```

- **Streamlit:** `st.button("Aprobar")` llama `/resume`.
- **Next.js (Fase 1b):** patrón `useInterrupt` del Vercel AI SDK.

El checkpointer Postgres mantiene el estado mientras el humano decide — aunque el proceso se reinicie.

### 12.7 Manejo de errores — 3 niveles

1. **Error de negocio** (SKU no existe) → nodo captura, mensaje amigable, END.
2. **Error técnico** (Qdrant caído) → `tenacity` retry 3× exponential → `error_fallback` → "tengo un problema técnico, reintenta".
3. **Guardrail violado** → no es error, camino esperado. END limpio.

**Cero custom error-tracking.** LangSmith + OTel + Sentry (Fase 2) cubren todo.

### 12.8 Checkpointing

`PostgresSaver` con `thread_id = conversation_id`. Beneficios:
- Una conversación puede tener 50 turnos, volver en 3 días, retomarse exacta.
- HITL sobrevive reinicios.
- **Time-travel debugging** — cargar estado en turno 7, cambiar algo, re-ejecutar.
- Auditoría completa por `thread_id`.

---

## 13. RAG pipeline moderno paso a paso

### 13.1 Qué indexamos (3 tipos de documentos)

| Fuente | Rol | Cantidad |
|---|---|---|
| **Fichas técnicas** (specs + descripción) | Factual: specs exactas citables | ~200 |
| **Reseñas de usuarios** | Cualitativo: "se calienta", "batería dura" | ~1000 |
| **FAQs y políticas** | No-catálogo: devoluciones, envíos, garantías | ~30 |

### 13.2 Chunking específico por tipo (el 80/20 del RAG)

**Anti-patrón:** `RecursiveCharacterTextSplitter(chunk_size=500)` sobre todo.

**Lo que hacemos:**
- **Fichas técnicas** → 1 chunk por ficha (300–600 tokens). Si largas, split por secciones.
- **Reseñas** → 1 reseña = 1 chunk. Conservar rating y fecha en metadata.
- **FAQs** → 1 pregunta+respuesta = 1 chunk. Nunca mezclar preguntas.

**Parent-Document retrieval** (LangChain): indexar chunks pequeños (buena precisión), devolver el **documento padre completo** al LLM (buen contexto).

### 13.3 Embeddings — decisiones

- **Modelo:** Voyage `voyage-3-lite` (512 dims, free tier 50M tok/mes)
- **Distancia:** `cosine` (o `dot` si vectores ya normalizados)
- **Input types:** `input_type="document"` al indexar; `input_type="query"` al consultar → mejora notable en retrieval
- **Batch size:** 128 al indexar

**Punto sutil:** embeddings distintos **no son intercambiables sin re-indexar**.
Si cambiás a `voyage-3` (1024 dims) o `text-embedding-3-small`, hay que re-embeddar todo.
El `EmbeddingsPort` tiene `dimensions` para detectar incompatibilidad.

### 13.4 Diseño de la colección Qdrant

```
Collection: products_rag
  vectors: { size: 512, distance: Cosine }
  payload_schema:
    sku: keyword          (indexado — filtro exacto)
    doc_type: keyword     (indexado — "spec" | "review" | "faq")
    category: keyword     (indexado — "laptop" | "phone" | ...)
    brand: keyword        (indexado)
    price: float          (indexado — range queries)
    rating: float         (indexado — para reviews)
    created_at: integer
    text: text            (indexado full-text para BM25)
    parent_id: keyword    (para parent-document retrieval)
    source_url: keyword
```

**Los `payload_index` no se crean solos.** Código de setup:

```python
qdrant.create_collection(
    "products_rag",
    vectors_config=VectorParams(size=512, distance=Distance.COSINE),
)
qdrant.create_payload_index("products_rag", "sku",      PayloadSchemaType.KEYWORD)
qdrant.create_payload_index("products_rag", "category", PayloadSchemaType.KEYWORD)
qdrant.create_payload_index("products_rag", "price",    PayloadSchemaType.FLOAT)
# ...
qdrant.create_payload_index("products_rag", "text",
    TextIndexParams(type="text", tokenizer="prefix"))  # BM25
```

Sin estos índices, un filtro `price < 1500 AND category = "laptop"` escanea O(n).

### 13.5 Retrieval híbrido (semántico + léxico)

Solo con embeddings falla en queries como `"MacBook M3 Pro 14"` (nombres propios, modelos).

```
query "MacBook M3 Pro 14 barato"
  ├── rama semántica:
  │     • Voyage embed (input_type=query)
  │     • Qdrant search con filters, k=30
  ├── rama léxica (BM25):
  │     • Qdrant full-text search sobre payload.text, k=30
  └── fusion:
        • Reciprocal Rank Fusion (RRF, k=60)
        • top 20 deduplicados
          ↓
  Voyage rerank-2-lite(query, top 20) → top 5
          ↓
  Parent-document expansion → contexto final para LLM
```

**Conceptos:**
- **BM25** — algoritmo clásico de IR (TF-IDF evolucionado).
- **RRF** — combina rankings diversos sin preocuparte por escalas. Fórmula: `score(d) = Σ 1/(k + rank_i(d))` con `k=60`.
- **Re-ranking** — modelo cross-encoder pasa query+doc juntos (no solo embeddings). 10–20 % mejor recall.

### 13.6 Contextual Retrieval (técnica Anthropic 2024)

Antes de embbedar un chunk, Haiku genera un resumen que pone el chunk en contexto de su documento padre.
Mejora recall 35–50 %. Costo: <$1 para todo el catálogo.

```python
for chunk in doc_chunks:
    ctx = await llm.invoke(
        f"Summarize how this chunk fits in the full doc:\n\n{full_doc}\n\nChunk: {chunk}"
    )
    enriched = f"{ctx}\n\n{chunk}"
    vec = await embeddings.embed(enriched, input_type="document")
    qdrant.upsert(id, vec, payload={...})
```

### 13.7 Datos sintéticos

No scrapeamos Amazon. Script `scripts/seed.py`:

1. **Catálogo (200 productos):** Haiku genera 10 categorías × 20 productos con schema Pydantic estricto.
   Valida SKU único.
2. **Reseñas (~1000):** Haiku genera 3–8 por producto, mezcla 70/20/10 positivas/neutrales/negativas.
3. **FAQs (~30):** devoluciones, envíos, garantías, métodos de pago.
4. **Persist:** Postgres (fuente de verdad) → Qdrant (índice). Patrón productivo real.

Costo total del seed: <$2. Tiempo: ~5 min.

### 13.8 Pipeline de ingesta

Script `python -m shopping_copilot.ingest`, idempotente e incremental:

1. Lee productos/reseñas/FAQs de Postgres.
2. Chunking específico por tipo.
3. Contextual retrieval header (Haiku).
4. Batch embed (Voyage, lotes de 128).
5. Upsert a Qdrant con payload.
6. Registra en `rag_ingestion_log`.

**ID Qdrant = hash(doc_id + chunk_idx + embedding_model).** Re-correr no duplica.

### 13.9 Evaluación de RAG

**Golden dataset** (~40 queries a mano):

```json
{
  "query": "laptop liviana para programar bajo $1200",
  "relevant_skus": ["LAP-007", "LAP-012", "LAP-023"],
  "must_not_appear": ["LAP-099"]
}
```

**Métricas en CI:**

| Métrica | Qué mide | Objetivo |
|---|---|---|
| `Recall@10` | % relevantes en top-10 | >0.85 |
| `MRR@10` | qué tan arriba aparece el primer relevante | >0.6 |
| `NDCG@10` | calidad del ranking completo | >0.7 |
| **Faithfulness** (LLM-judge) | respuesta usa solo info del contexto | >0.95 |
| **Answer relevance** (LLM-judge) | respuesta contesta la pregunta | >0.9 |
| **Context relevance** (LLM-judge) | chunks recuperados pertinentes | >0.8 |

Herramienta: **RAGAS** (librería OSS) para métricas LLM-as-judge. Integra con LangSmith.

### 13.10 Diferido a Fase 2+

- **Multi-vector retrieval** (dense + colbert/late-interaction) — Fase 3
- **HyDE** — Fase 3 opcional
- **Query decomposition** — Fase 2 si las evals lo piden
- **Graph RAG** sobre KG de productos — Fase 4

---

## 14. Governance: guardrails + policies + evals

Tres capas, cada una contesta una pregunta distinta:

- **Guardrails** — ¿es seguro procesar esta entrada / devolver esta salida *ahora*?
- **Policies** — ¿la decisión de negocio respeta las reglas (precio, stock, descuento, budget)?
- **Evals** — ¿la calidad global del agente subió, bajó o se mantuvo tras mi cambio?

### 14.1 Taxonomía de amenazas

| # | Amenaza | Dónde vive | Fase |
|---|---|---|---|
| 1 | Prompt injection | input rail | 1 |
| 2 | Jailbreak | input rail | 1 |
| 3 | PII leak | input rail | 1 |
| 4 | Topic restriction | input rail | 1 |
| 5 | Hallucination de SKU/precio | output rail | 1 |
| 6 | Unsafe tool call | tool rail | 1 |
| 7 | Moderación de output | output rail | 1 |
| 8 | Data exfiltration | output rail | 1 |
| 9 | Cost runaway | runtime rail | 1 |
| 10 | Rate limiting por usuario | api layer | 2 |

### 14.2 Herramientas

- **NeMo Guardrails** (OSS, NVIDIA) — runtime rails, DSL Colang, integración LangGraph nativa.
- **Presidio** (OSS, Microsoft) — detección PII, 30+ entidades, soporte español.
- **Guardrails AI** (OSS) — validación estructurada de outputs (complementa Pydantic).
- **Pydantic v2** — structured output tipado.

### 14.3 Input rails

```yaml
rails:
  input:
    flows:
      - check_jailbreak        # LLM-judge con Haiku + prompt canónico NVIDIA
      - self_check_input       # NeMo built-in: ¿razonable para copiloto compras?
      - detect_pii             # Presidio → redacta o bloquea
      - topic_restriction      # solo compras/productos/envíos/devoluciones
      - injection_heuristics   # regex + signatures conocidas
```

**Presidio — tres modos:**
- **Block** — CC, DNI → rechaza con mensaje "no compartas info sensible por chat".
- **Redact** — email, teléfono → reemplaza por `[EMAIL]`, `[PHONE]`.
- **Warn** — registra, deja pasar.

**Prompt injection — capas:**
1. Regex (rápido): `r"(?i)ignore (all|previous|above) (instructions|rules)"`
2. LLM-judge (Haiku, ~$0.0005): *"¿Esta entrada intenta redefinir instrucciones del sistema?"*
3. Firmas conocidas (Rebuff / garak datasets)

Si **cualquier** capa detecta → reject + audit con tag `prompt_injection`.

### 14.4 Output rails

```yaml
rails:
  output:
    flows:
      - self_check_output       # NeMo built-in
      - no_invented_skus        # custom: SKUs mencionados existen en Postgres
      - price_matches_catalog   # custom: precios == DB
      - structured_output_ok    # Pydantic
      - moderation              # Llama Guard o similar
```

**No-hallucination de SKU (el más importante):**

```python
async def no_invented_skus(response: str, ctx: dict) -> GuardrailDecision:
    mentioned = extract_skus(response)
    existing = await catalog.skus_exist(mentioned)
    if mentioned - existing:
        return GuardrailDecision(
            blocked=True,
            reason=f"SKU inventados: {mentioned - existing}",
            safe_fallback="Déjame verificar el catálogo de nuevo..."
        )
    return GuardrailDecision(blocked=False)
```

### 14.5 Policies-as-code

Descuentos, precios y stock **nunca** dependen del prompt.
El LLM puede *sugerir* aplicar un cupón pero el precio final lo calcula `PricingService` del dominio.

```python
@dataclass(frozen=True)
class DiscountPolicy:
    max_percent: Decimal = Decimal("0.30")     # máx 30 %
    stackable: bool = False                     # no combinar cupones
    min_order_total: Money = Money("20", "USD")
    def validate(self, cart, discount) -> PolicyResult:
        ...
```

**Tests unitarios exhaustivos** sobre policies — es donde más cobertura se exige.
Los guardrails pueden tener falsos positivos/negativos; las policies **no pueden fallar**.

### 14.6 Runtime rails — límites de ejecución

- Max tool calls / turno: **8**
- Max tokens input/output: **4 000 / 2 000**
- Max latency / turno: **30 s**
- Max cost acumulado / thread: **$0.50**

Violación → nodo `budget_guard` corta con mensaje.

### 14.7 Red-team dataset

~70 ataques en `tests/evals/redteam/`:

```
├── prompt_injection.jsonl    (30)
├── pii_leak.jsonl            (20)
├── jailbreak.jsonl           (15)
├── hallucination.jsonl       (20)
├── off_topic.jsonl           (15)
└── cost_attacks.jsonl        (5)
```

Meta: **block rate ≥ 95 %** antes de merge.

### 14.8 Evals — estructura

```
tests/evals/
├── datasets/
│   ├── golden_conversations.jsonl     (30 flows completos)
│   ├── rag_golden.jsonl               (40 queries + relevant SKUs)
│   ├── router_golden.jsonl            (50 mensajes + intent)
│   └── redteam/                       (ver 14.7)
├── evaluators/
│   ├── llm_judge_faithfulness.py
│   ├── llm_judge_relevance.py
│   ├── llm_judge_safety.py
│   ├── deterministic/
│   │   ├── sku_valid.py
│   │   ├── price_valid.py
│   │   └── intent_accuracy.py
│   └── end_to_end_task_success.py
└── run.py                             (CLI → LangSmith)
```

### 14.9 LLM-as-judge — disciplina

- **Modelo juez** diferente al generador (evita sesgo).
- **Prompt canónico** versionado, temperatura 0.
- **Rubric binario** con explicación.
- **Calibración:** 30 juicios manuales vs LLM-judge → mide Cohen's kappa. Si κ < 0.6, re-prompt del juez.
- **Caching:** mismo input+prompt = mismo verdict.

### 14.10 CI gates

Un PR se bloquea si, comparado con `main`, **empeora** alguna métrica umbral:

| Métrica | Umbral | Delta permitido |
|---|---|---|
| Router accuracy | ≥ 0.90 | −0.02 |
| RAG Recall@10 | ≥ 0.85 | −0.02 |
| Faithfulness | ≥ 0.95 | −0.01 |
| Red-team block rate | ≥ 0.95 | 0 (sin tolerancia) |
| E2E task success | ≥ 0.80 | −0.03 |
| Cost / conversación | ≤ $0.08 | +10 % |
| Latencia p95 | ≤ 6 s | +15 % |

Override vía commit message `eval-override: <razón>`.

### 14.11 Flujo de desarrollo con evals

1. Cambiás prompt o nodo.
2. Local: `make evals-quick` (15 casos, 1 min, <$0.05).
3. PR → CI `make evals-full` (130 casos, ~10 min, ~$0.30).
4. LangSmith comenta tabla delta en el PR.
5. Revisás casos regresivos.
6. Merge o iteración.

### 14.12 Consumo LangSmith free tier (5k traces/mes)

- 1 turno ≈ 5–8 spans = 1 trace. Con 5k traces → ~5k turnos/mes.
- `evals-full` con 130 casos = 130 traces. Con 10 PRs/día = 1 300 traces/día solo CI. **Explosivo.**
- **Mitigación:** `LANGCHAIN_TRACING_V2=true` solo para `evals-full` en `main`/`release/*`. PRs ordinarios exportan a JSONL.
- Local dev: 3 k traces/mes suele bastar.

---

## 15. Observabilidad completa (LLM + app + infra)

### 15.1 Dos mundos

| Aspecto | LangSmith | OTel + Prometheus |
|---|---|---|
| Qué captura | Prompts, respuestas, tool calls, tokens, costo, evals | Latencia endpoints, SQL, HTTP externos, CPU, RAM |
| Granularidad | Semántica (por turno) | Técnica (por request HTTP) |
| Auto-instrumentación | `LANGCHAIN_TRACING_V2=true` | `opentelemetry-instrument <cmd>` |
| Dónde brilla | "¿Por qué respondió X?" | "¿Por qué está lento?" |

### 15.2 LangSmith — jerarquía

1. **Organization** — una por equipo.
2. **Project** — uno por entorno: `shopping-copilot-dev`, `-ci`, `-prod`.
3. **Run** — una "llamada trazada". Run padre (turno) + runs hijos (nodos, tool calls, retrievals).

Setup completo (env vars — cero código):

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=shopping-copilot-dev
```

### 15.3 Anatomía de un trace

```
📦 graph_invoke                                1.8s   $0.012
├── 🛡️ input_guardrails_node                    120ms  $0.0003
├── 🧭 router_node                               150ms  $0.0008
│   └── anthropic.chat(model=haiku-4.5)        150ms
├── 🔍 search_node                               1.3s   $0.010
│   ├── voyage.embed(input_type=query)         180ms
│   ├── qdrant.hybrid_search(k=30)              90ms
│   ├── voyage.rerank(k=20→5)                  220ms
│   ├── postgres.catalog.get_products([5])      40ms
│   └── anthropic.chat(model=sonnet-4.6)       720ms
└── 🛡️ output_guardrails_node                    80ms
```

En LangSmith UI por cada span ves: timeline, input/output completo, tokens, costo, metadata, tags, errores, feedback, botón "Open in Playground".

### 15.4 Metadata y tags (no es "código custom")

Una sola línea al invocar el grafo:

```python
config = {
    "configurable": {"thread_id": conversation_id},
    "metadata": {
        "user_id": user.id,
        "env": settings.env,
        "agent_version": settings.git_sha,
        "model_profile": "cost_optimized",
    },
    "tags": ["shopping", f"v:{settings.git_sha[:7]}"],
}
await graph.ainvoke(input, config=config)
```

Habilita filtros brutales: "todos los traces del usuario X en versión Y que llamaron tool Z".

### 15.5 Feedback del usuario

Botones 👍👎 en UI → `POST /feedback` →

```python
langsmith.create_feedback(
    run_id=body.run_id,
    key="user_rating",
    score=1 if body.rating == "up" else 0,
    comment=body.comment,
)
```

Se ve en LangSmith como métrica ("% 👍 por semana") y dataset de regresión.

### 15.6 Datasets + experiments

- **Datasets** — colecciones versionadas, subidas con `langsmith.create_dataset()`.
- **Experiments** — corres el agente contra un dataset.
- **Evaluators** — puntúan cada output.
- **Comparison view** — 2 experiments lado a lado.

### 15.7 Prompt Hub (Fase 2)

LangSmith Prompt Hub — "GitHub para prompts":

```python
prompt = pull_prompt("shopping-copilot/search-v3")
```

Ventajas:
- A/B testing en prod (10 % a v4, 90 % a v3)
- Rollback en un click
- Historial (quién cambió qué cuándo)
- Producto puede iterar prompts sin tocar código

### 15.8 OTel + Prometheus + structlog (Fase 1)

```
app (FastAPI + LangGraph) → auto-instrument at import time:
  - FastAPIInstrumentor
  - HTTPXClientInstrumentor
  - SQLAlchemyInstrumentor
  - RedisInstrumentor
  - PsycopgInstrumentor

→ structlog → stdout JSON
→ prometheus-fastapi-instrumentator → /metrics
```

**Fase 1 basta con:**
- OTel exportando a **console** (spans impresos en terminal — pedagógico).
- Logs JSON a stdout.
- `/metrics` expuesto pero sin Prometheus aún.

**Fase 2:** stack LGTM (Grafana + Loki + Tempo + Prometheus) por Docker Compose.

### 15.9 structlog — logs estructurados

```python
log.info("search_performed", user_id=user_id, query=query, n_results=5)
```

→

```json
{"event":"search_performed","user_id":"u_123","query":"laptop","n_results":5,
 "ts":"2026-04-23T10:34:12Z","level":"info","trace_id":"abc..."}
```

`trace_id` incluido por hook OTel — en LGTM saltás de log a trace en un click.

### 15.10 Alertas (Fase 2-3)

| Métrica | Umbral | Acción |
|---|---|---|
| `evals_faithfulness` < 0.90 | 3 runs seguidos | Slack/email |
| p95 latency > 10 s | 5 min sostenido | Slack |
| Error rate > 5 % | 5 min sostenido | Slack |
| Cost per 1k conv > $80 | 1 h sostenido | Slack |
| `user_rating` % 👍 < 70 % | día | Slack |

### 15.11 Playbook — dónde mirar según el síntoma

| Síntoma | Dónde primero |
|---|---|
| "Respondió cualquier cosa" | LangSmith — trace del turno, ve prompt + retrieval |
| "Está lento" | OTel traces (Tempo) + LangSmith latency por span |
| "Está caro" | LangSmith cost report por proyecto |
| "RAG no trae lo correcto" | LangSmith — inspecciona `search_node` |
| "Fallan checkouts" | structlog filter `event=checkout_failed` |
| "Hay loop infinito" | OTel trace del request — tool calls cuento |
| "Prod down" | Prometheus — `up{job="shopping-api"}` + error logs |

### 15.12 Qué montamos cuándo

| Capa | Fase 1 | Fase 2 | Fase 3 |
|---|---|---|---|
| LangSmith | ✅ tracing + datasets + evaluators + feedback | + Prompt Hub + alerting | + multi-project |
| OTel auto-instrument | ✅ export a console | + export a Tempo | + custom resource attrs |
| Prometheus | `/metrics` expuesto | ✅ scrape + Grafana dashboards | + Mimir long retention |
| Logs | structlog JSON a stdout | + Loki ingesta | + log-based metrics |
| Langfuse self-host | ❌ | ✅ espejo para comparar | opcional primary |
| Alertas | ❌ | Slack básicas | PagerDuty + runbooks |

---

## 16. Roadmap por fases (1–4)

### Prerrequisitos

**Cuentas + API keys:** Anthropic ($30 budget cap), OpenAI ($10), Voyage AI (free 50M tok/mes), LangSmith (free 5k traces/mes), GitHub.

**Software local:** Python 3.12 (pyenv), uv, Docker Desktop, Cursor + PyCharm Community, Git, make.

### Semana 1 — Fundaciones + primer flujo E2E trivial

**Objetivo:** repo scaffoldeado, arquitectura sólida, agente trivial respondiendo y trazado.

Bloques: setup proyecto (uv, ruff, mypy, pre-commit), Docker Compose, pydantic-settings, domain mínimo + puertos, AnthropicAdapter + VoyageAdapter, seed inicial 20 laptops, FastAPI `/chat` echo-con-Claude, Streamlit, LangSmith tracing verificado, CI básica.

**Entregable:** Streamlit → "hola" → Claude responde → trace en LangSmith.

**Conceptos:** Port/Adapter (Protocol), uv, ruff, mypy --strict, pydantic-settings, SQLAlchemy 2 async, Alembic, Pydantic DTOs, LangSmith tracing, token, costo, prompt caching.

### Semana 2 — RAG completo + primer grafo LangGraph

**Objetivo:** búsqueda semántica funcional, cero alucinación de SKU.

Bloques: seed completo (200 productos + 1000 reseñas + 30 FAQs), pipeline ingesta con contextual retrieval, Qdrant + payload indexes, retriever híbrido + rerank Voyage, `SearchProductsUseCase`, primer grafo `START → router → search → output_guardrails → END` con checkpointer Postgres, router (Haiku + structured output), prompts Jinja, RAG evals v1.

**Entregable:** "quiero una laptop para diseño bajo $1500" → 3-5 productos reales, Recall@10 ≥ 0.85.

**Conceptos:** chunking por tipo, embeddings (vectores, dims, normalización, input_type), cosine vs dot, HNSW, payload index, BM25, retrieval híbrido, RRF, cross-encoder vs bi-encoder, contextual retrieval, parent-document, LangGraph basics, checkpointer, structured output, LLM-as-judge faithfulness, Recall@K / MRR / NDCG.

### Semana 3 — Multi-agente completo + guardrails + HITL

**Objetivo:** copiloto end-to-end con carrito, comparaciones, checkout + HITL, guardrails activos.

Bloques: dominio ampliado (Cart, Order, Discount), puertos CartPort/PaymentPort/NotificationPort, adapters (RedisCart, MockPayment), use cases completos, grafo completo, HITL con interrupt + botones Streamlit, NeMo Guardrails (jailbreak, PII Presidio, injection, topic), no-hallucination rail, policies-as-code con tests, red-team v1.

**Entregable:** conversación 8-10 turnos (buscar → comparar → carrito → cupón → checkout → aprobar → orden). Red-team > 90 % bloqueado.

**Conceptos:** LangGraph conditional edges, Command, interrupts + resume, model cascading, NeMo Colang, Presidio, prompt injection defense-in-depth, Guardrails AI, policy-as-code, combinación guardrails + policies + tool calling.

### Semana 4 — Evals completos + CI gates + observabilidad + pulido

**Objetivo:** calidad "defendible", cambios futuros protegidos por evals, listo para Fase 2.

Bloques: suite evals completa (LLM-as-judge + deterministic), datasets LangSmith, calibración del juez (Cohen's kappa), CI gates en GitHub Actions, OTel auto-instrument + console exporter, structlog JSON, prom-fastapi-instrumentator, iteración de prompts, docs finales, opcional migración Next.js + Vercel AI SDK.

**Entregable:** PR → CI corre 130 evals → LangSmith comenta tabla delta → mergeable o bloqueado.

**Conceptos:** LLM-as-judge discipline, Cohen's kappa, regression testing, CI gates, OTel spans/attributes/propagation, auto vs manual instrumentation, correlación logs/traces/metrics, SLOs/SLIs para agentes, (opcional) SSE + Vercel AI SDK + interrupts en cliente.

### Definition of Done — Fase 1

**Funcional:**
- [ ] Conversación multi-turno: buscar → comparar → carrito → checkout → orden
- [ ] HITL operativo (> $500 requiere aprobación)
- [ ] Guardrails bloquean injection, PII, jailbreak, off-topic
- [ ] Cero hallucination de SKU/precio
- [ ] HITL resume funciona tras reinicio

**Calidad:**
- [ ] Router accuracy ≥ 0.90
- [ ] RAG Recall@10 ≥ 0.85, Faithfulness ≥ 0.95
- [ ] Red-team block rate ≥ 0.95
- [ ] E2E task success ≥ 0.80

**Operacional:**
- [ ] CI con evals en PR + gates activos
- [ ] LangSmith tracing + feedback operativo
- [ ] OTel + structlog en console
- [ ] `make up` levanta todo
- [ ] Docs completas

**Económico:**
- [ ] Costo < $0.08 / conversación
- [ ] Latencia p95 < 6 s / turno
- [ ] LangSmith ≤ 4k traces / mes

### Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| LangSmith free tier se agota | Alta | `evals-full` solo en `main`; PRs offline |
| Evals inestables | Media | T=0 en juez + cache verdicts + calibración κ ≥ 0.6 |
| NeMo curva de aprendizaje | Media | Rails built-in primero, custom después |
| Postgres/Qdrant out-of-sync | Media | Seed idempotente + test de consistencia |
| Costo Anthropic dispara | Baja-Media | Budget cap $30; Haiku default; cost guard |
| Scope creep | **Alta** | Lo no listado → Fase 2 por principio |

### Fuera de alcance Fase 1 (explícito)

Autenticación real, multi-tenant, pagos reales, LiteLLM, Kong, Langfuse self-host, Stack LGTM, memoria largo plazo, fine-tuning, multimodalidad.

### Hoja de ruta posterior

- **Fase 2 (2-3 sem):** LiteLLM dev gateway + Spring Boot gateway + Langfuse self-host + LGTM stack + OAuth2
- **Fase 3 (2-3 sem):** Kong AI Gateway al edge + Arize Phoenix + multi-vector retrieval + PagerDuty
- **Fase 4 (opcional):** memoria largo plazo, multi-tenant, fine-tuning, multimodalidad, A/B en prod

---

## Cierre

Este documento captura el proceso de pensamiento del brainstorming inicial.
Las decisiones finales viven en el spec [`2026-04-23-retail-shopping-copilot-design.md`](../superpowers/specs/2026-04-23-retail-shopping-copilot-design.md).
El progreso de ejecución se lleva en [`../progress/plan.html`](../progress/plan.html).

Para la implementación, cada concepto marcado arriba se explicará **inline al aparecer por primera vez en el código**, siguiendo la regla acordada de teaching-by-doing.
