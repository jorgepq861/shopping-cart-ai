# Semana 4 — Evals completos + CI gates + observabilidad + pulido (esqueleto)

> **Estado:** esqueleto. Se convertirá en **plan detallado** al terminar Sem 3 con `writing-plans`.
> **Cross-ref:** [spec](../specs/2026-04-23-retail-shopping-copilot-design.md) · [tracker](../../progress/plan.html) · esqueletos [Sem 2](2026-04-23-week2-rag-langgraph-skeleton.md) · [Sem 3](2026-04-23-week3-multiagent-guardrails-hitl-skeleton.md).

## Objetivo

Llevar el proyecto a calidad **"defendible"**: cualquier cambio futuro protegido por una suite de **evals automatizados** (LLM-as-judge + deterministic + end-to-end), **CI gates** que bloquean merges si rompen umbrales, **observabilidad completa** (OTel auto-instrumentation + console exporter + structlog + `/metrics`), **documentación** runbook-ready, y — opcional — migración inicial a **Next.js + Vercel AI SDK** para aprender streaming real + tool-call UI + HITL en cliente productivo.

## Prerrequisitos (de Sem 3)

- [ ] `week3-done` tag
- [ ] Copiloto end-to-end funcional con HITL, guardrails, policies
- [ ] `make evals-redteam` ≥ 90% block rate
- [ ] RAG Recall@10 ≥ 0.85 (de Sem 2)

## Tasks (~20 tasks)

### Bloque A — Evaluators

| # | Título | Descripción |
|---|---|---|
| 1 | Evaluator `llm_judge_faithfulness` | Prompt canónico (Anthropic public cookbook), T=0, juez = Sonnet (no Haiku para evitar sesgo con Haiku que clasifica). Rubric binario + explicación. |
| 2 | Evaluator `llm_judge_answer_relevance` | Responde la pregunta del usuario. |
| 3 | Evaluator `llm_judge_context_relevance` | Chunks recuperados son pertinentes. |
| 4 | Evaluator `llm_judge_safety` | Respuesta no viola políticas (discriminatoria, sesgada, errónea factualmente). |
| 5 | Evaluator determinístico `sku_valid` | Regex extrae SKUs, query a DB verifica existencia. |
| 6 | Evaluator determinístico `price_valid` | Regex extrae precios, comparar con DB. |
| 7 | Evaluator determinístico `intent_accuracy` | Sobre `router_golden.jsonl`, compara intent predicho vs esperado. |
| 8 | Evaluator `end_to_end_task_success` | LLM-judge revisa transcript completo y dice si el usuario logró su objetivo. |

### Bloque B — Datasets LangSmith

| # | Título | Descripción |
|---|---|---|
| 9 | Subir `golden_conversations.jsonl` a LangSmith | 30 flows completos input→expected_outcomes. |
| 10 | Subir `rag_golden_v2.jsonl` | 40 queries (expandir el v1 de Sem 2). |
| 11 | Subir `router_golden.jsonl` | 50 mensajes + intent esperado. |
| 12 | Subir `redteam/*.jsonl` como datasets separados | Para verlos por tipo de ataque en UI. |

### Bloque C — Calibración

| # | Título | Descripción |
|---|---|---|
| 13 | Protocolo de calibración del juez | 30 juicios manuales vs LLM-judge sobre un mismo dataset. Cálculo de **Cohen's kappa**. Si κ < 0.6, iterar prompt del juez. Documentar resultado. |

### Bloque D — Runners

| # | Título | Descripción |
|---|---|---|
| 14 | `make evals-quick` (local) | Subset de 15 casos (2-3 por evaluator). ~1 min, <$0.05. |
| 15 | `make evals-full` (CI) | Suite completa ~130 casos. ~10 min, ~$0.30. Sube resultados a LangSmith como experiment. |

### Bloque E — CI gates

| # | Título | Descripción |
|---|---|---|
| 16 | GitHub Actions: eval job en PR | Solo en branches PR, no en cada push a main (ahorro traces). Corre `make evals-full`, compara contra baseline de `main-latest`. |
| 17 | Bot de comentarios en PR | Pega tabla delta (métrica actual vs main, indicador 🟢/🔴). Implementación: GitHub Action + LangSmith API. |
| 18 | Gates de merge | Bloquear si cualquier métrica empeora más del delta permitido (tabla en spec §7.9). Override por commit msg `eval-override: <razón>`. |

### Bloque F — OTel y métricas

| # | Título | Descripción |
|---|---|---|
| 19 | OTel auto-instrumentation setup | `opentelemetry-distro`, instrumenta FastAPI + httpx + SQLAlchemy + Redis + asyncpg. **Cero código custom** — solo `FastAPIInstrumentor.instrument_app(app)` y similares. |
| 20 | Console exporter OTel | Spans impresos en terminal. Pedagógico — ves lo que captura automágicamente. |
| 21 | `structlog` JSON config con `trace_id` auto-inyectado | Hook OTel en structlog processor. Logs correlacionables con traces. |
| 22 | `prometheus-fastapi-instrumentator` en `/metrics` | Plug-and-play. Expuesto pero no scrapeado aún (eso es Fase 2). |

### Bloque G — Iteración y pulido

| # | Título | Descripción |
|---|---|---|
| 23 | Iteración de prompts con evals | Correr suite, identificar casos regresivos, iterar prompts de `router`, `search`, `comparator`, `output_guardrails`. |
| 24 | Alcanzar Definition of Done (spec §10) | Router acc ≥ 0.90, RAG R@10 ≥ 0.85, Faithfulness ≥ 0.95, red-team ≥ 0.95, E2E success ≥ 0.80 |

### Bloque H — Documentación

| # | Título | Descripción |
|---|---|---|
| 25 | `README.md` completo | Quickstart, arquitectura en una página, links a spec/tracker/journal, troubleshooting común. |
| 26 | `docs/architecture.md` | Diagramas (dependency graph, grafo LangGraph, flujo RAG), explicación de capas. |
| 27 | `docs/runbook.md` | Cómo arrancar, reset, ingest, levantar UI, correr evals; qué hacer si Qdrant/Postgres falla. |
| 28 | Tracker `plan.html` — DoD marcado | Todo en verde al cierre. |

### Bloque I — Opcional: Next.js

| # | Título | Descripción |
|---|---|---|
| 29 | Proyecto `ui-next/` con `create-next-app` | TypeScript, App Router, Tailwind. |
| 30 | Integrar Vercel AI SDK (`useChat`, streaming) | Backend expone SSE via `StreamingResponse`. |
| 31 | Renderizado de tool calls en vivo | Skeleton cards mientras el tool corre → datos reales cuando termina. |
| 32 | HITL con `useInterrupt` | Modal de aprobación en frontend. |

### Review final

| # | Título | Descripción |
|---|---|---|
| 33 | Review Fase 1 completa | Todas las casillas DoD marcadas. Tag `fase1-done`. |

## Entregable demostrable

- **PR** que cambia un prompt → CI corre suite evals en ~10 min → bot comenta tabla delta en el PR → mergeable o bloqueado con razón clara.
- **README.md** permite que un dev nuevo clone y tenga el sistema corriendo en <30 min.
- **OTel console exporter** muestra spans de FastAPI + DB + httpx en cada request, sin haber escrito un span custom.
- **LangSmith** muestra un "project dashboard" con evolución de métricas por semana.
- (Opcional) **Next.js UI** con tool calls streameados + HITL modal renderizado nativamente.

## Conceptos nuevos (explicar inline)

### Sobre evals y LLM-as-judge
- **LLM-as-judge discipline** — juez distinto al generador, T=0, rubric binario, prompt versionado.
- **Rubrics** — criterios de puntuación claros.
- **Cohen's kappa** — métrica de agreement entre juez humano y LLM-judge.
- **Calibración** — iteración para alcanzar κ ≥ 0.6.
- **Regression testing para agentes** — compara delta de métricas entre PR y main.
- **CI gates declarativos** — umbrales + deltas en YAML.

### Sobre OTel
- **Spans** — unidades de trabajo trazado.
- **Attributes** — metadata en spans.
- **Context propagation** — cómo el `trace_id` viaja entre servicios/funciones async.
- **Auto vs manual instrumentation** — por qué preferimos auto.
- **Correlación logs/traces/metrics** — vía `trace_id`.
- **SLOs/SLIs para agentes** — qué signals importan (latencia, costo, faithfulness, user rating).

### Sobre frontend real (opcional Next.js)
- **SSE (Server-Sent Events)** — streaming unidireccional server→client.
- **`useChat` hook** de Vercel AI SDK — maneja estado + streaming.
- **Optimistic UI para tool calls** — render antes de que termine.
- **`useInterrupt`** — HITL nativo en cliente.

## Archivos que se crearán/modificarán

**Nuevos:**
- `tests/evals/evaluators/llm_judge_*.py`
- `tests/evals/evaluators/deterministic/*.py`
- `tests/evals/evaluators/end_to_end_task_success.py`
- `tests/evals/datasets/golden_conversations.jsonl`
- `tests/evals/datasets/router_golden.jsonl`
- `tests/evals/run.py` — CLI que corre suite
- `tests/evals/calibration/` — 30 juicios manuales + script de Cohen's kappa
- `src/shopping_copilot/observability/otel.py`
- `src/shopping_copilot/observability/logging.py` (structlog JSON + trace_id hook)
- `src/shopping_copilot/observability/metrics.py`
- `.github/workflows/evals.yml`
- `.github/actions/post-eval-delta/` (composite action)
- `docs/architecture.md`
- `docs/runbook.md`
- (Opcional) `ui-next/` proyecto Next.js completo

**Modificados:**
- `src/shopping_copilot/api/main.py` — registrar OTel + instrumentar + expose `/metrics`
- `Makefile` — `evals-quick`, `evals-full`, `calibrate-judge`
- `README.md` — reescribir completo
- `pyproject.toml` — `opentelemetry-*`, `prometheus-fastapi-instrumentator`, `structlog`, `ragas` (si usamos)

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| LangSmith free tier (5k traces/mes) se agota con evals en CI | `evals-full` solo en PRs y main — no en cada push. Cache de verdicts por `hash(input+prompt)`. |
| Juez poco confiable (κ < 0.6) | Iterar prompt hasta 3 veces; si no, downgrade a evaluators determinísticos + human-in-the-loop ad hoc. |
| PR gate bloquea trabajo legítimo | Mecanismo override con commit msg `eval-override: <razón>` auditable. |
| OTel auto-instrumentation pierde spans de LangGraph | LangGraph no instrumenta OTel por defecto; LangSmith cubre esa capa. Documentarlo. |
| Next.js añade 1-2 semanas si se complica | Marcado **opcional**. Si se atrasa, se empuja a Fase 2 (gateway Spring Boot + Next.js). |

## Done criteria — Fase 1 completa

**Funcional:**
- [ ] Conversación multi-turno: buscar → comparar → carrito → checkout → orden
- [ ] HITL operativo (> $500 requiere aprobación)
- [ ] Guardrails bloquean injection, PII, jailbreak, off-topic
- [ ] Cero hallucination de SKU/precio
- [ ] HITL resume funciona tras reinicio del proceso

**Calidad (umbrales):**
- [ ] Router accuracy ≥ 0.90
- [ ] RAG Recall@10 ≥ 0.85, Faithfulness ≥ 0.95
- [ ] Red-team block rate ≥ 0.95
- [ ] End-to-end task success ≥ 0.80
- [ ] Cohen's kappa del juez ≥ 0.6

**Operacional:**
- [ ] CI con evals en PR + gates activos
- [ ] LangSmith tracing + feedback 👍👎 operativo (el feedback se implementa en Sem 4 si no salió antes)
- [ ] OTel + structlog en console, `/metrics` expuesto
- [ ] `make up` levanta todo
- [ ] Docs: README, architecture.md, runbook.md

**Económico:**
- [ ] Costo < $0.08 / conversación promedio
- [ ] Latencia p95 < 6 s / turno
- [ ] LangSmith consumo ≤ 4k traces/mes

**Cierre:**
- [ ] Tracker `plan.html` 100% verde
- [ ] Tag `fase1-done` pusheado
- [ ] Commit final con changelog consolidado

---

## Después de Fase 1 — preview de Fase 2

Cuando cerremos `fase1-done`, el siguiente paso natural es **Fase 2 (realismo empresarial)**:

- **LiteLLM** como dev gateway (virtual keys, budget per-team, caching, fallback Anthropic↔OpenAI)
- **Spring Boot gateway** por delante del agente Python (auth, auditoría, integración legacy simulada)
- **Langfuse self-host** (alternativa OSS a LangSmith)
- **Stack LGTM** (Grafana + Prometheus + Loki + Tempo) por Docker Compose
- **OAuth2 / JWT** auth real
- **Alertas Slack** básicas
- **Prompt Hub** de LangSmith

Cuando llegues ahí, arranca una nueva skill `brainstorming` pidiendo re-diseño de Fase 2 (pues muchas decisiones de Fase 2 dependen de lo que aprendimos en Fase 1).

---

**Cuando lleguemos aquí:** invocaré `writing-plans` con este esqueleto + spec + aprendizajes acumulados para producir el plan detallado. Fase 1 queda cerrada.
