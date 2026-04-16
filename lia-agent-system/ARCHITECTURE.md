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

## ADR-002: Canonical Model Location (2026-04-06)

**Rule:** SQLAlchemy ORM models are defined ONLY in the `lia_models` package.

- `app/models/` → DELETE (migrate to lia_models)
- `app/domains/*/models/` → re-export from lia_models only
- `lia_models/` → canonical source of truth

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

---

*Last updated: 2026-04-06 | See REFACTOR_PLAN.md for phase-by-phase execution plan*

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

## ADR-012: Canonical Model Import Path (2026-04-16) [LIA-M01]

**Rule:** All model imports MUST use the installed package path `from lia_models.xyz import ...`.

Forbidden: `from libs.models.lia_models.xyz import ...` — this filesystem path creates duplicate class registrations in SQLAlchemy's mapper, causing `Multiple classes found` errors at runtime.

Allowed alternatives:
- `from lia_models.xyz import Model` (canonical, preferred)
- `from app.models.xyz import Model` (via proxy shims, resolves to the same object)

**Never** import models using the raw filesystem path through `libs.models.lia_models`.

---

*Last updated: 2026-04-16 | Phase 6 Batch 2: Unified model imports*
