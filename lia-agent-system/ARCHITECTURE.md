
Visit https://docs.replit.com/replit-workspace/ssh to learn more about SSH on Replit.
# Architecture Decision Records — LIA Agent System

> These ADRs define the architectural rules for this codebase.
> Pre-commit hooks enforce G1, G2, G4.
> See also: REFACTOR_PLAN.md, HARDENING_PLAN.md

---

## ADR-001: Repository Pattern (2026-04-06) [ENFORCED by CI]

**Rule:** All database access MUST go through repository classes.

**Layers:**
```
Controller (app/api/)  →  Service (app/domains/*/services/)  →  Repository (app/domains/*/repositories/)  →  DB
```

**Forbidden:**
```python
# ❌ SQL in controller
@router.get("/{id}")
async def get_item(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Item).where(Item.id == id))  # NEVER
```

**Correct:**
```python
# ✅ Repository in controller via DI
@router.get("/{id}", response_model=ItemResponse)
async def get_item(id: int, repo: ItemRepository = Depends(get_item_repo)):
    return await repo.get_by_id(id)
```

**Enforcement:** `scripts/check_no_sql_in_controllers.py` (pre-commit + CI)

---

## ADR-002: Canonical Model Location (2026-04-06, updated 2026-04-16)

**Rule:** SQLAlchemy ORM models are defined ONLY in the `lia_models` package.

**Layers:**
- `lia_models/` → canonical source of truth (all model definitions live here)
- `app/models/*.py` → compatibility proxies (`from lia_models.xyz import *`); no model definitions allowed
- `app/models/__init__.py` → central re-export hub for convenience imports
- `app/domains/*/models/` → re-export from lia_models only

**Valid import paths** (both resolve to the same Python object):
```python
from lia_models.job_vacancy import JobVacancy
from app.models.job_vacancy import JobVacancy
from app.models import JobVacancy
```

**Forbidden** (see ADR-012):
```python
from libs.models.lia_models.job_vacancy import JobVacancy
```

**Proxy file format** (`app/models/xyz.py`):
```python
"""Backwards-compatibility shim — real implementation in libs/models."""
from lia_models.xyz import *  # noqa: F401,F403
```

---

## ADR-003: Prompt Files (2026-04-06)

**Rule:** LLM prompts longer than 3 lines MUST live in `app/prompts/domains/*.yaml`
or `app/prompts/shared/*.yaml`. Use `PromptLoader.get_domain_prompt(domain_id)`.

**Infrastructure:** `app/shared/prompts/loader.py` + `app/prompts/domains/*.yaml`

**Forbidden:**
```python
SYSTEM_PROMPT = """
Você é um assistente...
[50 lines]
"""
```

**Correct:**
```python
from app.prompts import PromptLoader
system_prompt = PromptLoader.get_domain_prompt("my_domain")
```

---

## ADR-004: Hardcoded Data (2026-04-06)

**Rule:** Static data (lists, mappings, job templates, lookups) belongs in
`app/data/fixtures/*.json`, loaded via `app/data/loader.py`.

Python files that are pure data structures are FORBIDDEN.

---

## ADR-005: Response Models (2026-04-06) [ENFORCED by CI]

**Rule:** Every `@router` endpoint MUST declare `response_model`.

```python
# ✅ Always
@router.get("/items", response_model=list[ItemResponse])
@router.post("/items", response_model=ItemResponse, status_code=201)
@router.delete("/items/{id}", status_code=204)  # no body — use Response
```

**Enforcement:** `scripts/check_response_models.py` (pre-commit + CI)

---

## ADR-006: PII in Logs (2026-04-06) [ENFORCED by CI]

**Rule:** No PII (email, CPF, phone, name) in any log call. LGPD Art. 46.

```python
# ❌ Forbidden
logger.info("Sending email", recipient_email=user.email)
logger.error("Failed", candidate_name=candidate.name)

# ✅ Correct
logger.info("Sending email", candidate_id=candidate.id, template="interview")
logger.error("Failed", candidate_id=candidate.id)
```

**Enforcement:** `scripts/check_no_pii_in_logs.py` (pre-commit + CI)

---

## ADR-007: File Size Limits (2026-04-06)

| File Type | Warning | Hard Limit |
|---|---|---|
| API route file | 150 LOC | 300 LOC |
| Service class | 200 LOC | 400 LOC |
| Repository | 150 LOC | 300 LOC |
| Pydantic schema | 100 LOC | 200 LOC |
| Test file | 300 LOC | 600 LOC |

If your file exceeds the warning threshold, split it.

---

## The "Is This OK?" Checklist

Before every PR:

- [ ] Does my controller have `db.execute` / SQLAlchemy? → **MOVE TO REPO**
- [ ] Does every endpoint have `response_model`? → **ADD IT**
- [ ] Does any log call have `email`, `cpf`, `name`? → **REMOVE (LGPD)**
- [ ] Is any Python file > 300 LOC? → **SPLIT IT**
- [ ] Does a Python file contain mostly dicts/lists? → **MOVE TO JSON**
- [ ] Is there a multiline prompt > 5 lines in Python? → **MOVE TO YAML**
- [ ] Did I write bare `except:`? → **USE `except Exception:`**
- [ ] Do my new tests have real assertions? → **REQUIRED**
- [ ] Does my import use `from libs.models.lia_models`? → **USE `from lia_models` (ADR-012)**
- [ ] Does my `app/models/*.py` file define a class? → **MOVE TO `lia_models/`, keep proxy only (ADR-002)**

---

*Last updated: 2026-04-16 | See REFACTOR_PLAN.md for phase-by-phase execution plan*

---

## ADR-008: API Response Envelope (2026-04-13) [LIA-E01, LIA-E02]

**Rule:** New API endpoints SHOULD return `APIResponse<T>` from `app.schemas.api_envelope`.

Existing endpoints continue to work. Migrate progressively using:
- Direct usage: `return APIResponse.ok(data=result)`
- Decorator: `@api_envelope` wraps any return value

**Error envelope** (already enforced in main.py):
```json
{"error": true, "status_code": 400, "message": "...", "request_id": "..."}
```

**Success envelope** (new):
```json
{"success": true, "message": "...", "data": {...}, "metadata": {...}, "errors": null}
```

---

## ADR-009: Event Versioning (2026-04-13) [LIA-E03]

**Rule:** All Rails-bound events MUST include `event_version` field.

Registry: `EVENT_VERSIONS` in `app/shared/messaging/rails_event_schemas.py`

**Compatibility:** MAJOR version must match (e.g., 1.0 and 1.1 OK, 1.x and 2.0 NOT OK).
Use `validate_event_version()` before processing incoming events.

---

## ADR-010: Unified Event Publisher (2026-04-13) [LIA-E04]

**Rule:** New code publishing events to Rails MUST use `unified_event_publisher.publish()`.

Legacy paths (RailsAdapter.publish_event, direct RabbitMQ) continue to work but are deprecated.

Features:
- Retry with exponential backoff (3 attempts, 1-4s)
- Timeout per attempt (10s)
- Audit logging (LIA-E04 tag)
- Fail-safe (returns bool, never raises)

---

## ADR-011: WebSocket Message Schema (2026-04-13) [LIA-E05]

**Rule:** WebSocket messages SHOULD use `WSMessage` from `app.schemas.ws_messages`.

Standard types: `user.message`, `assistant.message`, `system.error`, `stream.*`.

Existing raw dict messages continue to work but should migrate.

---

## ADR-012: Forbidden Import Paths (2026-04-16) [ENFORCED by CI]

**Rule:** Never use `from libs.models.lia_models` or `from libs.messaging.lia_messaging` import paths. See ADR-002 for the canonical model location and valid import paths.

These fully-qualified paths cause duplicate SQLAlchemy class registrations because Python treats them as distinct modules from the short-form `lia_models` / `lia_messaging` packages.

**Correct imports:**
- `from lia_models.X import Y` (canonical, preferred)
- `from app.models.xyz import Model` (via proxy shims, resolves to the same object)
- `from lia_messaging.X import Y` (not `from libs.messaging.lia_messaging.X import Y`)

**Forbidden:**
- `from libs.models.lia_models.xyz import ...`
- `from libs.messaging.lia_messaging.X import Y`

**Enforcement:** `scripts/check_forbidden_imports.py` (pre-commit hook **G5** + CI)

---

## ADR-013: Dev Auto-Login Contract (2026-04-16)

**Decision:** A single backend helper (`app.auth.dependencies.ensure_demo_user`) and a single frontend helper (`plataforma-lia/src/lib/auth/dev-auto-login.ts`) own the dev auto-login flow end-to-end.

**Backend contract:**
- `ensure_demo_user(db)` — idempotent. Creates the `demo@wedotalent.com` user with a real bcrypt hash (`get_password_hash(DEV_AUTO_LOGIN_PASSWORD or "demo123")`); repairs the hash if it does not match the bcrypt prefix.
- Hard-gated on `_is_dev_environment()` (canonical `APP_ENV`, accepts `development`/`dev`/`local`). Defense-in-depth: the helper itself raises 403 outside dev, so a forgotten gate at the call site cannot expose the demo account.
- Eagerly seeded in `app/main.py` lifespan when in dev so the very first request can authenticate.
- `get_current_user_or_demo` is the only consumer of the lazy fallback path; all production paths must use `get_current_user` (strict).

**Frontend contract:**
- `isDevAutoLoginEnabled()` returns `true` only when `NODE_ENV !== 'production'`.
- `loginDemoUser()` returns `{ accessToken, refreshToken? } | null` (used by `/api/auth/auto-login`).
- `getDevToken()` returns a 25-minute cached access token (used by `middleware.ts` and `/api/auth/ws-token`).
- `clearCachedDevToken()` invalidates the cache (e.g. on logout).
- All four touch points — `middleware.ts`, `api/auth/ws-token/route.ts`, `api/auth/auto-login/route.ts`, and any future consumer — MUST import from this helper. Inline duplicates of the demo-login fetch + token cache are forbidden.

**`/api/auth/ws-token` contract:** returns `{ token, authMode }` on success or `{ token: null, code, reason, authMode }` with HTTP 401/503 on failure so the chat WebSocket hook can surface a deterministic reason instead of silently disconnecting.

**Disable mechanism:** Set `NODE_ENV=production` (frontend) or `APP_ENV=production|staging` (backend). Both layers must be flipped before production cutover. WorkOS / future ATS-issued sessions slot into the same `Authorization: Bearer …` slot consumed downstream by the FastAPI app, so swapping auth providers does not require touching protected route handlers.

---

*Last updated: 2026-04-16 | ADR-013: dev auto-login canonical contract*

---

## ADR-014: Canonical API Surface — `/api/v1` (2026-04-17)

**Rule:** Every public HTTP and WebSocket endpoint MUST be mounted under
the `/api/v1` prefix. Routers are declared with relative paths (e.g.
`@router.websocket("/ws/chat/{session_id}")`) and the prefix is applied
at `app.include_router(..., prefix="/api/v1")` time.

**Why:** auth middleware, reverse proxy rules, CORS configuration, and
rate-limit policies all key off the `/api/v1` prefix. An endpoint mounted
at the bare root silently bypasses every one of those controls.

**Audit history:** findings W17 + W2 (Task #319, 2026-04-17) confirmed
that `agent_chat_ws_router` was being mounted **without** a prefix at
`app/api/routes.py:495`, exposing the chat WebSocket as
`/ws/chat/{session_id}`. Fix: include the router with
`prefix="/api/v1"`. Public path is now
`wss://<host>/api/v1/ws/chat/{session_id}`. Frontend touchpoint:
`plataforma-lia/src/hooks/chat/useChatTransport.ts` (`buildWsUrl`).

**Enforcement:** regression test
`tests/unit/test_agent_chat_ws_prefix.py` pins the canonical path. Any
new router must follow the same `include_router(..., prefix="/api/v1")`
pattern; the only sanctioned exceptions are health/liveness probes and
the legacy `jobs_ws.router` (tracked separately).

---

## ADR-015: Audit Guards — Shim SLA, Registry anti-revival, Legacy `@tool` ban (2026-04-17) [ENFORCED by CI]

These three rules close the §9 audit recommendations (S7.1, S7.2, S7.3) and
prevent regression of debt that was paid down in tasks #124 / #242 / #308.

### S7.1 — Shim SLA (90 days, 0 importers ⇒ deletion)

A "shim" is a backwards-compatibility proxy file that re-exports symbols from
a canonical location (typically `lia_models.*` / `lia_messaging.*`). Shims
accumulate without a deletion contract, which is how 156 dead files lived in
`app/models/` before task #242.

**Rule:** any shim with **0 importers anywhere in the repo** AND **≥ 90 days
old** (creation date via `git log --diff-filter=A`) is eligible for automated
deletion. The script lists candidates and exits non-zero.

**Enforcement:** `scripts/check_shim_sla.py` (pre-commit hook `shim-sla` + CI
job "S7.1: Shim SLA").

```bash
python3 scripts/check_shim_sla.py            # human-readable
python3 scripts/check_shim_sla.py --json     # CI-friendly
```

### S7.2 — `GlobalToolRegistry` retired (Task #350)

Task #308 retired eager `GlobalToolRegistry.register(...)` calls; tool routing
goes through `ToolRegistry` + `tool_permissions.yaml`. Task #350 then removed
the now-empty `app/shared/global_tool_registry.py` shim and its anti-revival
guard tests, since they had no production callers and the surrounding rules
(S7.3 below + scope checks via `tool_permissions.yaml`) already prevent the
old pattern from coming back.

### S7.3 — No `from langchain_core.tools import tool` in domain tools

Domain tools live under `app/domains/*/tools/` and MUST use the in-house
`@tool_handler` decorator so audit, scope, fail-closed, and permission
semantics are applied uniformly. Importing the legacy `@tool` decorator from
`langchain_core.tools` defeats this.

**Rule:** `from langchain_core.tools import tool` is banned in
`app/domains/*/tools/`. A small `ALLOW_LIST` inside the script grandfathers
the five files that pre-date the rule; new entries to the allow list are not
accepted and existing entries should be removed as they migrate.

**Enforcement:** `scripts/check_no_legacy_tool_decorator.py` (pre-commit hook
`no-legacy-tool-decorator` + CI job "S7.3").

### S7.4 — Superfície canônica de autoria de tools (Task #351, ADR-016)

Três peças coexistem com papéis **diferentes**, não duplicados:

- **Autoria** → `@tool_handler` decorator (`app/shared/tool_handler.py`) +
  `app/domains/*/agents/*_tool_registry.py`. É onde toda tool nova nasce.
- **Execução** → `ToolRegistry` global em `app/tools/registry.py`. É o índice
  por-nome que o orchestrator/executor consultam. **Não é superfície de
  autoria**; só `app/tools/__init__.py:initialize_tools()` chama
  `tool_registry.register(...)`, agregando os `get_*_tools()` de cada domínio.
- **Escopo / governança** → `app/tools/tool_permissions.yaml` mantém
  `scopes:` (mapeamento UI-context → tools) e `restricted_tools:` (HITL).
  A config `llm_provider` / `llm_fallback_order` por tenant **migra para DB**
  (`tenant_llm_config`); a YAML conserva apenas defaults de sistema.

Bridge `rails-ats-api`: tools continuam registradas em Python; o que muda é a
implementação interna delas (chamam `RailsAdapter` HTTP em vez do repo local
quando `RAILS_API_URL` estiver setado). Tenant check, escopo e HITL ficam num
só lugar.

Detalhes, plano de migração e não-decisões: `docs/specs/ai/ADR-016-tool-registration-canonical.md`.

### S7.5 — Direct `tool_registry.register(` calls blocked outside the canonical entry point (Task #354)

The S7.4 contract above is only as strong as the guard that enforces it.
Without an automated check, a future contributor will quietly bypass tenant
checks and HITL by calling `tool_registry.register(...)` from a new domain
module — exactly the regression that S7.1–S7.3 already prevent for the
other rules.

**Rule:** the literal call `tool_registry.register(` is banned everywhere
under `app/` except the two canonical files:

- `app/tools/__init__.py` — `initialize_tools()` aggregates
  `get_*_tools()` from each domain and is the **only** legitimate caller.
- `app/tools/registry.py` — defines `ToolRegistry.register` itself.

A small `ALLOW_LIST` inside the script grandfathers the domain modules that
pre-date ADR-016 (`app/domains/*/tools/*.py` + `app/shared/tools/export_tools.py`)
so the guard can land without a big-bang migration. New entries to the allow
list are **not** accepted; existing entries should be removed as each domain
flips to `@tool_handler` + `get_<domain>_tools()` and `initialize_tools()`
starts aggregating its tools.

**Enforcement:** `scripts/check_tool_authoring_surface.py` (pre-commit hook
`tool-authoring-surface` + CI job "S7.5"). The header docstring of
`app/tools/registry.py` cross-references this guard so a contributor reading
the registry source learns the rule from either direction.

```bash
python3 scripts/check_tool_authoring_surface.py
```

---

## ADR-017: Canonical Observability Location — `app.shared.observability.*` (2026-04-17) [ENFORCED by CI]

**Decision.** All observability code — tracing, structured logging, LLM
callbacks, agent monitoring/health, model drift, token tracking/budget,
WSI observability, and LangSmith configuration — lives under the single
package `app/shared/observability/`. There is **one** canonical import
path per module and **no** re-export shims.

**Canonical modules (11):**

| Concern | Canonical path |
|---|---|
| Sentry / OpenTelemetry tracing | `app.shared.observability.tracing` |
| Structured logging | `app.shared.observability.structured_logging` |
| LLM callbacks (Langfuse + audit) | `app.shared.observability.callbacks` |
| Agent monitoring service | `app.shared.observability.agent_monitoring_service` |
| Agent health alerts | `app.shared.observability.agent_health_alert_service` |
| Model drift detection | `app.shared.observability.model_drift_service` |
| Drift alerting | `app.shared.observability.drift_alert_service` |
| Token tracking | `app.shared.observability.token_tracking_service` |
| Token budget enforcement | `app.shared.observability.token_budget_service` |
| WSI-specific observability | `app.shared.observability.wsi_observability` |
| LangSmith configuration | `app.shared.observability.langsmith` |

**Deleted legacy paths (forbidden, do not reintroduce — 11 concerns
across 16 distinct import paths, since some concerns had duplicates in
both `shared/services/` and `domains/*/services/`):**

- `app.shared.tracing`
- `app.shared.structured_logging`
- `app.shared.llm.callbacks`
- `app.shared.governance.agent_monitoring_service`
- `app.shared.services.agent_health_alert_service`
- `app.shared.services.model_drift_service`
- `app.shared.services.drift_alert_service`
- `app.shared.services.token_tracking_service`
- `app.shared.services.token_budget_service`
- `app.domains.ai.services.model_drift_service`
- `app.domains.lgpd.services.drift_alert_service`
- `app.domains.analytics.services.token_tracking_service`
- `app.domains.analytics.services.wsi_observability`
- `app.domains.analytics.services.agent_monitoring_service`
- `app.domains.credits.services.token_budget_service`
- `app.config.langsmith`

**Why.** Before Tarefa #343 these eleven modules and several re-export
shims were spread across `app/shared/{tracing,structured_logging}`,
`app/shared/llm/callbacks.py`, `app/shared/governance/`,
`app/shared/services/`, four `app/domains/*/services/` folders, and
`app/config/langsmith.py`. Multiple call sites imported the same
behavior from different paths, which made it impossible to reason about
which callbacks/handlers were actually wired in, fragmented LangSmith
configuration, and let drift / token-budget logic drift between domain
copies. Collapsing to one package gives every consumer a single source
of truth and lets the package-level `__init__.py` document the contract.

**Enforcement.** `scripts/check_forbidden_imports.py` (pre-commit hook
**G5** + CI) blocks every legacy path listed above. Any reintroduction
fails CI with the same `ADR-012`-style violation message. The package
header at `app/shared/observability/__init__.py` cross-references the CI
guard so future contributors discover the rule from either direction.

**Audit history.** Reconciliation in
`docs/audits/AUDIT_STATUS_REPORT_2026-04-FINAL.md` §0 / Top-10 #3
confirmed code at 100% (11/11 modules canonical, 41 importers on the new
path, 0 importers on legacy paths) and flagged the documentation refresh
as the only remaining residual — closed by this ADR plus the parallel
updates in `docs/specs/CANONICAL_SOURCES_SPEC.md` and the root
`CLAUDE.md`.

---

*Last updated: 2026-04-17 | ADR-015 (S7.1/S7.2/S7.3) + ADR-016 (S7.4) + ADR-017 (observability canonical location)*

---

## ADR-017: Canonical Observability Layer (2026-04-17) [ENFORCED by CI]

**Rule:** All tracing, structured logging, LLM callbacks, agent monitoring,
drift detection, token tracking/budget, and LangSmith configuration live in
**one** package: `app/shared/observability/`. There is no other valid home.

**Background.** Task #343 collapsed eleven scattered modules — previously
spread across `app/shared/tracing.py`, `app/shared/llm/callbacks.py`,
`app/shared/governance/`, `app/shared/services/`,
`app/domains/{ai,lgpd,analytics,credits}/services/`, and
`app/config/langsmith.py` — into a single canonical package. The legacy
files and the five re-export shims that briefly bridged the move were then
deleted to leave a single source of truth.

**Canonical layout — `app/shared/observability/`:**

| Concern | Module |
|---|---|
| Sentry / OpenTelemetry tracing | `tracing.py` |
| Structured logging (structlog) | `structured_logging.py` |
| LangChain LLM callback handlers | `callbacks.py` |
| Agent monitoring service | `agent_monitoring_service.py` |
| Agent health alerting | `agent_health_alert_service.py` |
| Model drift detection | `model_drift_service.py` |
| Drift alerting | `drift_alert_service.py` |
| Token usage tracking | `token_tracking_service.py` |
| Token / spend budget | `token_budget_service.py` |
| WSI-specific observability | `wsi_observability.py` |
| LangSmith configuration | `langsmith.py` |

**Correct imports:**
```python
from app.shared.observability.tracing import setup_tracing
from app.shared.observability.callbacks import LIACallbackHandler
from app.shared.observability.langsmith import configure_langsmith
from app.shared.observability.agent_monitoring_service import AgentMonitoringService
from app.shared.observability.token_tracking_service import TokenTrackingService
from app.shared.observability.token_budget_service import TokenBudgetService
from app.shared.observability.model_drift_service import ModelDriftService
from app.shared.observability.drift_alert_service import DriftAlertService
from app.shared.observability.wsi_observability import WSIObservability
```

**Forbidden — every legacy path is rejected by CI:**
- `from app.shared.tracing …`
- `from app.shared.structured_logging …`
- `from app.shared.llm.callbacks …`
- `from app.shared.governance.agent_monitoring_service …`
- `from app.shared.services.{agent_health_alert_service,model_drift_service,drift_alert_service,token_tracking_service,token_budget_service} …`
- `from app.domains.ai.services.model_drift_service …`
- `from app.domains.lgpd.services.drift_alert_service …`
- `from app.domains.analytics.services.{token_tracking_service,wsi_observability,agent_monitoring_service} …`
- `from app.domains.credits.services.token_budget_service …`
- `from app.config.langsmith …`

**Enforcement:** `scripts/check_forbidden_imports.py` (pre-commit hook **G5**
+ CI). The script's `FORBIDDEN_PATTERNS` list pins all 11 legacy paths; any
new code reintroducing them fails the build with an actionable diff.

**See also:** `docs/CANONICAL_SOURCES_SPEC.md` for the full module-level
mapping and the rationale behind the consolidation.

---

*Last updated: 2026-04-17 | ADR-017: canonical observability layer*



---

## ADR-018: LLM Factory — Choose Your AI / BYOK Contract

**Status**: Implementado (2026-04-19)

### Decisão

O sistema de LLM opera via **LLM Factory**, composto por três camadas canônicas:

| Camada | Classe | Responsabilidade |
|--------|--------|-----------------|
| Registry global | `LLMProviderFactory` | Catálogo de providers; factory de clientes LLM |
| Container por tenant | `ProviderContainer` | Chave do tenant + fallback_order + Quality Tier Guard |
| Registro de tenants | `TenantProviderRegistry` | Singleton `tenant_id → ProviderContainer`; carregado do DB |

### Contratos Não-Negociáveis

1. **BYOK**: Quando um tenant configura sua própria API key, ela é SEMPRE usada. Qualquer fallback para key da plataforma gera log `WARN [LIA-BYOK]`.
2. **Quality Tier Guard**: Modelos Tier 2 (`claude-haiku-3-5`, `gemini-2.0-flash`, `gpt-4o-mini`) são bloqueados para tasks `screening` e `wsi` — a plataforma substitui pelo modelo Tier 1 e registra `WARN [LIA-QUALITY]`.
3. **Audit trail**: Toda chamada LLM bem-sucedida registra `key_source="tenant"|"system"` via `audit_service.log_decision()`.
4. **Embedding lock**: Fallback cross-provider em embeddings (Gemini 768 dims → OpenAI 1536 dims) gera `CRITICAL [EmbeddingFactory]`; bloqueável via `EMBEDDING_LOCK_PROVIDER`.

### Paths Canônicos

- **Chat / Orchestrator**: `TenantProviderRegistry.load_from_db()` → `ProviderContainer.generate_with_fallback(task_type="chat")`
- **Triagem WSI**: `wsi_compact_pipeline` → `generate_with_fallback(task_type="screening")` — Quality Tier Guard ativo
- **LangGraph agents**: `langgraph_react_base._get_model()` + budget check antes de `_run_graph()`

### Referência Operacional

Ver `LLM_FACTORY_HANDOFF_v2.md` para: tabela de gaps, constantes de referência (`QUALITY_TIERS`, `TASK_MINIMUM_TIER`), guia de logs, env vars e matriz Provider × Capacidade × Tier.

*Last updated: 2026-04-19 | ADR-018: LLM Factory / Choose Your AI BYOK contract*
