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


