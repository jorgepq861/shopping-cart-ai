# Semana 3 — Multi-agente completo + guardrails + HITL (esqueleto)

> **Estado:** esqueleto. Se convertirá en **plan detallado** al terminar Sem 2 con `writing-plans`, incorporando aprendizajes.
> **Cross-ref:** [spec](../specs/2026-04-23-retail-shopping-copilot-design.md) · [tracker](../../progress/plan.html) · [plan Sem 1](2026-04-23-week1-foundations.md) · [esqueleto Sem 2](2026-04-23-week2-rag-langgraph-skeleton.md).

## Objetivo

Tener el copiloto **completo end-to-end**: conversación multi-turno que atraviesa búsqueda → comparación → carrito → checkout, con **Human-in-the-Loop** real (interrupts + resume), **guardrails activos** (NeMo + Presidio + Guardrails AI), **policies-as-code** (pricing, stock, budget) y un **red-team dataset** inicial que validemos antes de mergear nada.

## Prerrequisitos (de Sem 2)

- [ ] `week2-done` tag con CI verde
- [ ] Grafo LangGraph `START → router → search → output_guardrails → END` funcional
- [ ] Checkpointer Postgres con `PostgresSaver`
- [ ] RAG híbrido con Recall@10 ≥ 0.85
- [ ] 200 productos + reseñas + FAQs indexados en Qdrant

## Tasks (~20 tasks)

### Bloque A — Dominio de carrito y checkout

| # | Título | Descripción |
|---|---|---|
| 1 | Value objects `Discount`, `StockLevel` | TDD, reglas de validación (max %, currencies) |
| 2 | Entity `CartItem` + Entity `Cart` | Identidad por `user_id`, invariantes (no duplicar SKU, sumar qty) |
| 3 | Entity `Order` + estado `OrderStatus` | FSM: DRAFT → APPROVED → CONFIRMED |
| 4 | Puertos `CartPort`, `PaymentPort`, `NotificationPort` | `Protocol` en `domain/ports.py` |

### Bloque B — Adaptadores de infra para carrito/checkout

| # | Título | Descripción |
|---|---|---|
| 5 | `RedisCartAdapter` implementando `CartPort` | Serialize Cart a JSON, TTL 24h. Tests integration con Redis real. |
| 6 | `MockPaymentAdapter` implementando `PaymentPort` | Simula charge/refund con delay + random success. Determinístico vía seed en tests. |
| 7 | `ConsoleNotificationAdapter` implementando `NotificationPort` | stdout (Fase 1). En Fase 2 se cambia por email/Slack. |
| 8 | Alembic migration: tabla `orders` | id, user_id, cart_snapshot JSONB, status, created_at |

### Bloque C — Casos de uso

| # | Título | Descripción |
|---|---|---|
| 9 | `CompareProductsUseCase` | Recibe SKUs → RAG sobre reseñas + specs → Sonnet genera tabla comparativa markdown |
| 10 | `AddToCartUseCase` + `RemoveFromCartUseCase` + `UpdateCartUseCase` | Aplican invariantes del Cart. Tests exhaustivos. |
| 11 | `CheckoutUseCase` | Valida stock → aplica pricing → setea `requires_human_approval` si `total > $500` o `discount > 30%` |
| 12 | `EscalateToHumanUseCase` | Usa `NotificationPort`, loggea razón |

### Bloque D — Nodos del grafo nuevos

| # | Título | Descripción |
|---|---|---|
| 13 | Nodo `comparator` | Invoca `CompareProductsUseCase`. Sonnet. |
| 14 | Nodo `cart` | Haiku clasifica sub-intent (add/remove/update) + tool calling sobre `CartPort` |
| 15 | Nodo `checkout` | Sonnet valida + invoca `CheckoutUseCase`. Setea HITL flag. |
| 16 | Nodo `human_approval` — `interrupt()` + resume | Pausa el grafo. Emite evento SSE `interrupt_required` al cliente. Resume vía `Command(resume=decision)` en endpoint `/resume`. |
| 17 | Nodos `smalltalk` + `out_of_scope` | Templates + Haiku barato. |
| 18 | Conditional edges completas | Después del router: 6 ramas posibles. Después de checkout: 2 ramas (HITL o END). |

### Bloque E — Guardrails

| # | Título | Descripción |
|---|---|---|
| 19 | NeMo Guardrails `config.yml` + Colang flows | Input rails: `check_jailbreak`, `self_check_input`, `detect_pii`, `topic_restriction`, `injection_heuristics` |
| 20 | Presidio integration (PII detection) | Bloquea CC/DNI. Redacta email/teléfono. Recognizers español + inglés. |
| 21 | Custom rail `no_invented_skus` (refinado) | Actualizar el de Sem 2 para cubrir también nombres de producto parciales |
| 22 | Custom rail `price_matches_catalog` | Regex + DB check |
| 23 | Guardrails AI — structured output validator | Integrar en `/chat` response |
| 24 | Moderation rail | Llama Guard local o endpoint Anthropic moderation |

### Bloque F — Policies-as-code

| # | Título | Descripción |
|---|---|---|
| 25 | `PricingService` + `DiscountPolicy` | Max 30%, no stackable, min order $20. Tests exhaustivos. |
| 26 | `StockService` | No checkout si stock < qty. Lock optimista en Redis. |
| 27 | `BudgetService` | HITL threshold $500 / 30% descuento. Configurable por env var. |

### Bloque G — Red-team + HITL UI

| # | Título | Descripción |
|---|---|---|
| 28 | Red-team dataset v1 en `tests/evals/redteam/` | 30-50 ataques: `prompt_injection.jsonl` (15), `pii_leak.jsonl` (10), `jailbreak.jsonl` (8), `hallucination.jsonl` (10), `off_topic.jsonl` (5), `cost_attacks.jsonl` (2) |
| 29 | Runner `make evals-redteam` | Corre dataset, mide `block_rate`, falla CI si < 0.90 |
| 30 | HITL en Streamlit | Detectar `interrupt_required` del backend → mostrar tarjeta con carrito + botones "Aprobar" / "Rechazar" → POST `/resume` |
| 31 | Endpoint `/resume` | Recibe `thread_id` + decisión, invoca `graph.invoke(Command(resume=...))`, devuelve siguiente respuesta |
| 32 | Review final Semana 3 | Checklist, tag `week3-done` |

## Entregable demostrable

Conversación **8-10 turnos** vía Streamlit:

1. "quiero una laptop potente para programación, menos de $1500"
2. "compara las 3 más ligeras"
3. "la ThinkPad qué tal batería?"
4. "agrégala al carrito"
5. "añade el cargador extra"
6. "tengo un cupón BAYTEQ10"
7. "checkout"
8. → **Streamlit muestra tarjeta de aprobación** (total > $500)
9. "aprobar"
10. → "Orden `ORD-xyz` confirmada"

Ataques del red-team bloqueados > 90%. Política de descuento 30% máx enforced (cupón absurdo 80% → rechazado por policy, no por LLM). LangSmith muestra traces completos con guardrail outcomes.

## Conceptos nuevos (explicar inline al implementar)

### Sobre LangGraph avanzado
- **Conditional edges** — función que lee state y devuelve string con nombre del siguiente nodo.
- **`Command`** — objeto para enviar instrucciones al grafo (resume, goto).
- **`interrupt()`** — pausa el grafo, devuelve control al caller.
- **Resume con `Command(resume=value)`** — re-entra al grafo tras HITL.
- **Model cascading** — Haiku para clasificar/decidir, Sonnet para razonar. Patrón productivo.

### Sobre guardrails
- **Input vs output rails** — qué se valida cuándo.
- **NeMo Colang** — DSL declarativo para rails.
- **Presidio entities + recognizers** — engine de detección PII extensible.
- **Anonymization modes** — block / redact / warn.
- **Prompt injection defense-in-depth** — regex + LLM-judge + signatures.
- **Guardrails AI validators** — Pydantic++ para outputs.
- **Moderation models** — Llama Guard, OpenAI moderation.

### Sobre políticas y HITL
- **Policy-as-code** — reglas de negocio tipadas con tests, **no en prompts**.
- **FSM (Finite State Machine)** — para estados de Order.
- **Optimistic locking** — Redis WATCH/MULTI.
- **HITL** — Human-in-the-Loop.

## Archivos que se crearán/modificarán

**Nuevos archivos principales:**
- `src/shopping_copilot/domain/` — `Discount`, `StockLevel`, `CartItem`, `Cart`, `Order`, ampliar ports
- `src/shopping_copilot/infrastructure/cart/redis_cart.py`
- `src/shopping_copilot/infrastructure/payment/mock_payment.py`
- `src/shopping_copilot/infrastructure/notification/console_notif.py`
- `src/shopping_copilot/application/use_cases/{compare_products,add_to_cart,remove_from_cart,update_cart,checkout,escalate_to_human}.py`
- `src/shopping_copilot/domain/services/{pricing,stock,budget}.py`
- `src/shopping_copilot/agents/nodes/{comparator,cart,checkout,human_approval,smalltalk,out_of_scope}.py`
- `src/shopping_copilot/guardrails/config.yml` + `flows.co`
- `src/shopping_copilot/guardrails/{input_rails,output_rails,pii_presidio}.py`
- `src/shopping_copilot/guardrails/policies/{pricing,stock,budget}.py`
- `src/shopping_copilot/api/routers/resume.py`
- `tests/evals/redteam/*.jsonl`
- `tests/evals/run_redteam.py`
- `migrations/versions/0003_orders.py`

**Modificados:**
- `src/shopping_copilot/agents/graph.py` — grafo completo con 9+ nodos
- `src/shopping_copilot/agents/state.py` — agregar campos cart/checkout/HITL
- `src/shopping_copilot/api/routers/chat.py` — detectar interrupts y emitir SSE
- `ui/app.py` — renderizar tarjeta HITL + botones
- `pyproject.toml` — `nemoguardrails`, `presidio-analyzer`, `presidio-anonymizer`, `guardrails-ai`

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| NeMo Guardrails curva de aprendizaje | Arrancar con rails built-in (`check_jailbreak`, `self_check_input`), custom rails después. |
| Presidio recognizers español incompletos | Complementar con recognizers custom (DNI/RUC ecuatoriano) si aparece. |
| HITL con Streamlit se siente raro | Documentar limitación; migración a Next.js en Sem 4 lo arregla bien. |
| Red-team block rate < 90% en primera corrida | Iterar rails, agregar signatures. Documentar cada ataque que pasa. |
| Grafo con 9 nodos se vuelve complejo | Visualizar con `graph.get_graph().print_ascii()`. LangFlow opcional para debug. |

## Done criteria

- [ ] Conversación de 8-10 turnos end-to-end funciona
- [ ] HITL: compra > $500 → Streamlit muestra aprobación → tras aprobar, orden creada
- [ ] Policies validadas: cupón > 30% rechazado, stock 0 bloquea checkout, budget excedido dispara HITL
- [ ] `make evals-redteam` ≥ 90% block rate
- [ ] Tests: ≥ 15 nuevos unit tests de policies, ≥ 10 de guardrails, ≥ 5 de nodos nuevos
- [ ] `ruff`/`mypy`/CI verdes
- [ ] Trace LangSmith muestra guardrail outcomes en metadata
- [ ] Tag `week3-done`

---

**Cuando lleguemos aquí:** invocaré `writing-plans` con este esqueleto + spec + aprendizajes de Sem 1-2, para producir el plan detallado.
