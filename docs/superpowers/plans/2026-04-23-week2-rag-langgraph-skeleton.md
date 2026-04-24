# Semana 2 — RAG completo + primer grafo LangGraph (esqueleto)

> **Estado:** esqueleto. Se convertirá en **plan detallado** al terminar Sem 1 con `writing-plans`, incorporando aprendizajes de Sem 1.
> **Cross-ref:** [spec](../specs/2026-04-23-retail-shopping-copilot-design.md) · [tracker](../../progress/plan.html) · [plan Sem 1](2026-04-23-week1-foundations.md).

## Objetivo

Que el agente haga **búsqueda semántica híbrida** sobre un catálogo real (200 productos, 1000 reseñas, 30 FAQs), con **re-ranking** y **cero alucinación de SKU**. Primer grafo LangGraph funcional con router → search → output_guardrails, con checkpointer en Postgres. Al cerrar la semana: métricas de calidad de retrieval reproducibles (Recall@10 ≥ 0.85).

## Prerrequisitos (de Sem 1)

- [ ] `week1-done` tag en git, CI verde
- [ ] 20 laptops ya en Postgres (del seed inicial)
- [ ] LangSmith trazando `/chat` correctamente
- [ ] `VoyageAdapter` y `AnthropicAdapter` con tests verdes
- [ ] `PostgresCatalogAdapter` + tests de integración

## Tasks (~15 tasks)

| # | Título | Descripción breve |
|---|---|---|
| 1 | Extender dominio para RAG | Añadir value objects: `Chunk`, `ScoredDoc`, `RetrievalResult` |
| 2 | Ampliar seed a 200 productos + reseñas + FAQs | Haiku genera 3 categorías × ~67 productos + 3-8 reseñas/producto + 30 FAQs. Persist en Postgres (nuevas tablas `reviews`, `faqs`) |
| 3 | Alembic migration: reviews + faqs + rag_ingestion_log | 3 tablas nuevas, índices básicos |
| 4 | `QdrantAdapter` implementando `VectorStorePort` | Cliente async, upsert, search con filters. Tests con **testcontainers.qdrant** (container efímero por session) — aprovechamos el cambio de infra para introducir el patrón. |
| 5 | Script `setup_qdrant`: crear collection + payload indexes + text index | Idempotente. Reusable en CI. |
| 6 | `VoyageRerankerAdapter` implementando `RerankerPort` | Cross-encoder `rerank-2-lite`. Tests mocked. |
| 7 | Chunking utilities por tipo de documento | `chunk_spec`, `chunk_review`, `chunk_faq`. Pure functions, TDD. |
| 8 | Contextual retrieval helper (Haiku) | Genera header contextual por chunk. Input: doc padre + chunk. Output: `contextual_header`. Cache en `rag_ingestion_log`. |
| 9 | Pipeline de ingesta: `python -m scripts.ingest` | Lee Postgres → chunking → contextual header → Voyage embed batch → Qdrant upsert → log. Idempotente e incremental. |
| 10 | `HybridRetriever`: semántico + BM25 + RRF | Orquesta dos búsquedas paralelas sobre Qdrant, fusiona con Reciprocal Rank Fusion (k=60), devuelve top 20. |
| 11 | `SearchProductsUseCase` | Combina retriever → reranker → catalog enrichment. Devuelve lista de `Product`. |
| 12 | LangGraph: `state.py` + `graph.py` + `StateGraph` builder | `ShoppingState` TypedDict. `PostgresSaver` checkpointer. Primer grafo: `START → router → search → output_guardrails → END`. |
| 13 | Nodo `router` (Haiku + structured output) | Clasifica intent + confidence. Structured output con Pydantic. Tests mocked. |
| 14 | Nodo `search` — invoca `SearchProductsUseCase` | Convierte `search_results` en respuesta Sonnet. Prompts Jinja externos. |
| 15 | Nodo `output_guardrails` — `no_invented_skus` + `price_matches_catalog` | Valida respuesta contra DB. Si viola → mensaje seguro. |
| 16 | Integrar grafo con `/chat` endpoint | Reemplaza el echo de Sem 1 por invocación del grafo. `thread_id` desde header o generado. |
| 17 | Adaptar Streamlit: mantener `thread_id` en sesión + mostrar trace summary | Barra lateral con token cost + link al trace en LangSmith. |
| 18 | RAG evals v1: golden dataset 20 queries | `tests/evals/datasets/rag_golden_v1.jsonl` (20 queries → relevant SKUs). Métricas: Recall@10, MRR@10. Script `make evals-rag`. |
| 19 | Review final Semana 2 | Checklist completo, tag `week2-done`. |

## Entregable demostrable

Escribís en Streamlit: *"quiero una laptop para diseño bajo $1500"*.

- El trace en LangSmith muestra: `input_guardrails` (vacío aún) → `router` (intent=search, conf>0.9, Haiku) → `search` (embed Voyage → Qdrant hybrid → rerank → load Postgres → Sonnet) → `output_guardrails` (valida SKUs existen).
- Respuesta: 3-5 productos reales con SKU, nombre, precio, breve rationale.
- Recall@10 sobre golden dataset ≥ 0.85.
- Conversación de 2-3 turnos mantiene contexto vía checkpointer (turno 2 puede decir "ahora compara las 3 primeras" y funciona).
- Cero alucinación — si un SKU aparece en la respuesta, existe en Postgres.

## Conceptos nuevos (explicar inline al implementar)

### Sobre RAG / Information Retrieval
- **Chunking** — partir documentos en trozos para indexar. Estrategias por tipo de doc.
- **Chunk / ScoredDoc** — unidades de texto que entran al índice.
- **Embeddings (dense vectors)** — representación numérica de semántica.
- **Dimensiones y normalización** — 512 en Voyage; normalizado permite usar `dot product` == `cosine`.
- **Input types** — `document` al indexar, `query` al consultar (Voyage).
- **Cosine vs dot product** — distancias para buscar vecinos.
- **HNSW** — Hierarchical Navigable Small World, algoritmo detrás del índice de Qdrant.
- **Payload index** — índice sobre metadata. Sin él, filtros son O(n).
- **BM25** — algoritmo clásico de ranking léxico (TF-IDF evolucionado).
- **Retrieval híbrido** — semántico + léxico combinados.
- **RRF (Reciprocal Rank Fusion)** — `score(d) = Σ 1/(k + rank_i(d))` con `k=60`. Fusiona rankings.
- **Cross-encoder vs bi-encoder** — embeddings son bi-encoder (texto y query por separado). Re-ranker es cross-encoder (texto + query juntos → más preciso, más caro).
- **Contextual Retrieval** — técnica Anthropic 2024: prepend contextual header por chunk. +35-50% recall.
- **Parent-document retrieval** — indexar chunks chicos, devolver doc padre al LLM.

### Sobre LangGraph
- **StateGraph** — máquina de estados. Nodos funciones async, edges condicionales.
- **TypedDict state + reducers** — `add_messages` acumula mensajes automáticamente.
- **Checkpointer (`PostgresSaver`)** — persiste estado por `thread_id`. Permite multi-turno + recuperación.
- **`thread_id`** — identifica conversación. Lo generamos con UUID.

### Sobre calidad
- **Structured output (Pydantic)** — obligás al LLM a devolver JSON con schema.
- **LLM-as-judge (faithfulness)** — métrica de si la respuesta sólo usa info del contexto.
- **Métricas de IR** — Recall@K, MRR (Mean Reciprocal Rank), NDCG (Normalized Discounted Cumulative Gain).

## Archivos que se crearán/modificarán

**Nuevos archivos:**
- `src/shopping_copilot/domain/rag.py` — value objects RAG (Chunk, ScoredDoc, RetrievalResult)
- `src/shopping_copilot/infrastructure/vectorstore/qdrant_adapter.py`
- `src/shopping_copilot/infrastructure/reranker/voyage_reranker.py`
- `src/shopping_copilot/infrastructure/catalog/models.py` — **añadir** ReviewRow, FaqRow, RagIngestionLog
- `src/shopping_copilot/application/rag/chunking.py`
- `src/shopping_copilot/application/rag/contextual.py`
- `src/shopping_copilot/application/rag/hybrid_retriever.py`
- `src/shopping_copilot/application/use_cases/search_products.py`
- `src/shopping_copilot/agents/state.py`
- `src/shopping_copilot/agents/graph.py`
- `src/shopping_copilot/agents/nodes/{router,search,output_guardrails}.py`
- `src/shopping_copilot/agents/prompts/{router,search}.jinja`
- `scripts/setup_qdrant.py`
- `scripts/ingest.py`
- `migrations/versions/0002_reviews_faqs_ingestion_log.py`
- `tests/unit/domain/test_rag.py`
- `tests/unit/application/test_chunking.py`
- `tests/unit/application/test_hybrid_retriever.py`
- `tests/integration/test_qdrant_adapter.py`
- `tests/integration/test_ingest_pipeline.py`
- `tests/unit/agents/test_graph.py`
- `tests/evals/datasets/rag_golden_v1.jsonl`
- `tests/evals/run_rag.py`

**Modificados:**
- `scripts/seed.py` — extender a 3 categorías + reseñas + FAQs
- `src/shopping_copilot/api/routers/chat.py` — invocar grafo en vez de echo
- `src/shopping_copilot/api/deps.py` — providers para vector store, reranker, retriever, grafo
- `ui/app.py` — `thread_id` en sesión, link a trace
- `Makefile` — `make setup-qdrant`, `make ingest`, `make evals-rag`
- `pyproject.toml` — `qdrant-client`, `langgraph`, `langgraph-checkpoint-postgres`

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Seed 200 productos dispara costo Haiku | Batch en 2-3 llamadas, budget local $2 máx |
| Qdrant lento por falta de payload index | Step dedicado 5 crea índices antes del primer upsert |
| Recall@10 < 0.85 en la primera corrida | Iteramos en: chunking strategy, input_type, contextual retrieval on/off, reranker on/off. Documentar experiments en LangSmith |
| `PostgresSaver` requiere tabla propia | LangGraph hace la migración solo en primer arranque. Validar en CI |
| Costo LangSmith se dispara con traces de ingesta | Desactivar `LANGCHAIN_TRACING_V2` para scripts (solo app web trackeada) |

## Done criteria

- [ ] `make evals-rag` corre y muestra Recall@10, MRR, con ≥ 0.85 recall
- [ ] Streamlit → pregunta catálogo real → respuesta con SKUs válidos
- [ ] Checkpointer funciona (turno 2 ve contexto del turno 1)
- [ ] Todos los tests en verde: unit domain (rag) + application (chunking, retriever) + integration (qdrant, ingest) + agents (grafo)
- [ ] `ruff`/`mypy`/CI verdes
- [ ] LangSmith muestra span tree claro por turno
- [ ] Tag `week2-done` pusheado

---

**Cuando lleguemos aquí:** invocaré `writing-plans` nuevamente, tomando este esqueleto + el spec + aprendizajes de Sem 1, para producir el plan detallado paso-a-paso con código.
