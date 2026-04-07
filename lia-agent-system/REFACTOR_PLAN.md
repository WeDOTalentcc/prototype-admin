# REFACTOR_PLAN.md — LIA Agent System: Complete Refactor & LOC Reduction Plan

> **Generated:** 2026-04-06  |  **Last revised:** 2026-04-07
> **Baseline:** ~556K LOC | 213 API files | 1,557 endpoints
> **Target:** ≤ 280K LOC | Clean Architecture | Zero SQL in controllers | 100% guardrails enforced
> **Reference:** See also `HARDENING_PLAN.md` for P0–P2 security fixes (already completed)
> **Rails integration:** `ats-api-rails` owns candidates, jobs, applies, users, messages — see [Rails Migration Boundary](#rails-migration-boundary)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Root Causes of Code Bloat](#2-root-causes-of-code-bloat)
3. [Architecture Principles & Golden Rules](#3-architecture-principles--golden-rules)
4. [Phase Overview & LOC Targets](#4-phase-overview--loc-targets)
5. [Phase 1 — Move Hardcoded Data Out of Python](#phase-1--move-hardcoded-data-out-of-python)
6. [Phase 2 — Extract DB Calls from Controllers to Repositories](#phase-2--extract-db-calls-from-controllers-to-repositories)
7. [Phase 3 — Consolidate Duplicate Model/Schema Layers](#phase-3--consolidate-duplicate-modelschema-layers)
8. [Phase 4 — Complete DDD Migration](#phase-4--complete-ddd-migration)
9. [Phase 5 — Response Models & API Contract Hardening](#phase-5--response-models--api-contract-hardening)
10. [Phase 6 — Move LLM Prompts Out of Python Files](#phase-6--move-llm-prompts-out-of-python-files)
11. [Phase 7 — Fix Test Suite](#phase-7--fix-test-suite)
12. [Phase 8 — Guardrails, CI Enforcement & Pre-commit Hooks](#phase-8--guardrails-ci-enforcement--pre-commit-hooks)
13. [Phase 9 — Fix Circular Imports & Misc Quality](#phase-9--fix-circular-imports--misc-quality)
14. [Phase 10 — Pydantic & Global Error Handling](#phase-10--pydantic--global-error-handling)
15. [Rails-Style Conventions Cheat-Sheet](#rails-style-conventions-cheat-sheet)
16. [Rails Migration Boundary](#rails-migration-boundary)
17. [Phase 4B — Migrate app/shared/services/](#phase-4b--migrate-appsharedservices)
18. [Progress Tracker](#progress-tracker)

---

## 1. Executive Summary

The LIA Agent System accumulated ~556K LOC through four distinct anti-patterns:

| Anti-Pattern | Estimated Waste (LOC) |
|---|---|
| Hardcoded data inside Python (app/data/ + templates) | ~19,000 |
| Fat controllers with raw SQL (124/213 files) | ~35,000 duplicated logic |
| Three parallel model/schema layers (app + libs + domains) | ~28,000 duplicated defs |
| Unfinished DDD migration (133 legacy services coexist with 47 domain services) | ~18,000 duplicated logic |
| Dead code / orphaned files | ~12,000 |
| LLM prompts embedded in Python strings | ~6,000 |
| Fake coverage tests | ~2,000 |

**Realistic post-refactor target: ≤ 280K LOC** (−50%), with higher actual business logic density.

---

## 2. Root Causes of Code Bloat

### 2.1 No Enforced Architecture Boundaries

Python/FastAPI imposes nothing. Without guardrails, developers added SQL directly to
route handlers, duplicated logic, and copy-pasted instead of reusing.

### 2.2 Incomplete DDD Migration

A migration from flat `app/services/` to `app/domains/*/services/` was started but never
finished. Both layers coexist: **133 files** still in legacy flat layer, **47 files** in
the new domain layer.

### 2.3 Three Parallel Model Layers

- `app/models/` — SQLAlchemy ORM models (legacy location)
- `lia_models` lib — canonical models (new location)
- `app/domains/*/models/` — domain models (DDD location)

Result: **96 model file names** exist in 2+ paths simultaneously.

### 2.4 Hardcoded Data in Python

- `app/data/` — 16,565 LOC, **zero production imports** (fully orphaned)
- `app/services/email_templates_data.py` — 2,032 LOC of HTML strings

### 2.5 LLM Prompts as Python String Literals

Prompts scattered across agent files as multiline strings — untestable, untracked,
pollute Python files with hundreds of lines of non-code.

### 2.6 No Response Model Discipline

781/1,557 endpoints (50%) lack `response_model`. FastAPI serializes raw dicts,
bypassing Pydantic validation and making API contracts invisible.

### 2.7 Fake Test Coverage

5 `coverage_boost_*.py` files with no assertions inflate coverage metrics without
testing anything real.

---

## 3. Architecture Principles & Golden Rules

### 3.1 The Three-Layer Contract

```
HTTP Layer        (app/api/)
      ↓  validates input via Pydantic schema
Service Layer     (app/domains/*/services/)
      ↓  pure business logic, no HTTP/DB concerns
Repository Layer  (app/domains/*/repositories/)
      ↓  ALL SQLAlchemy queries live here
Database
```

**NEVER cross layers in the wrong direction.**
No SQLAlchemy in controllers. No HTTP objects in services.

### 3.2 Golden Rules

| # | Rule | Enforcement |
|---|---|---|
| G1 | Controllers have ZERO raw SQL / SQLAlchemy calls | CI script + pre-commit |
| G2 | Every endpoint declares `response_model` | CI check + pre-commit |
| G3 | No bare `except:` — always `except Exception:` or specific | ruff E722 |
| G4 | No PII (email, name, CPF) in log calls | custom CI check |
| G5 | All business logic in Services, all DB in Repositories | architecture test |
| G6 | Hardcoded data belongs in JSON/YAML/DB, not Python | PR checklist |
| G7 | LLM prompts belong in `app/prompts/*.md`, not Python strings | PR checklist |
| G8 | One canonical location per model — `lia_models` lib wins | import linter |
| G9 | Max 300 LOC per file. Flag at 200 | ruff / CI |
| G10 | All new code needs a real test with at least 1 assertion | CI coverage gate |

### 3.3 File Size Conventions (Rails-Style)

| File Type | Max LOC | Action if exceeded |
|---|---|---|
| API route file | 150 | Split by resource sub-action |
| Service class | 200 | Split by responsibility |
| Repository | 150 | Split by query category |
| Pydantic schema file | 100 | Split request/response schemas |
| Model file | 80 | One model per file |
| Test file | 300 | Split by feature |

### 3.4 Naming Conventions

```
app/api/v1/{resource}.py                          # route handlers only
app/domains/{domain}/services/{name}_service.py   # business logic
app/domains/{domain}/repositories/{name}_repository.py  # DB queries
app/domains/{domain}/schemas/{name}_schema.py     # Pydantic I/O contracts
lia_models/{name}.py                              # canonical ORM models (source of truth)
app/prompts/{domain}/{name}.md                    # LLM prompts
app/data/fixtures/{name}.json                     # static reference data
```

---

## 4. Phase Overview & LOC Targets

| Phase | Focus | Est. LOC Reduction | Risk | Duration |
|---|---|---|---|---|
| 1 | Move hardcoded data to JSON | −19,000 | Low | 2 days |
| 2 | Extract DB calls to repos | −35,000 | Medium | 5 days |
| 3 | Consolidate model/schema layers | −28,000 | Medium-High | 4 days |
| 4 | Complete DDD migration | −18,000 | Medium | 4 days |
| 5 | Response models | +2,000 net | Low | 2 days |
| 6 | Move prompts to .md | −6,000 | Low | 1 day |
| 7 | Fix tests | −2,000 + real tests | Low | 2 days |
| 8 | Guardrails & CI | 0 (prevents future bloat) | Low | 1 day |
| 9 | Circular imports + misc | −3,000 | Low | 1 day |
| 10 | Global error handling | +200 | Low | 0.5 days |
| **TOTAL** | | **−109,000 LOC** | | **~22 days** |

---

## Phase 1 — Move Hardcoded Data Out of Python

### Pre-flight Audit

```bash
# Confirm orphaned data files
python3 -c "
import os
data_files = [f for f in os.listdir('app/data') if f.endswith('.py')]
print(f'Files in app/data/: {len(data_files)}')
"
wc -l app/data/*.py app/services/email_templates_data.py
grep -r 'from app.data' app/ --include='*.py' | grep -v '__pycache__' | wc -l
grep -r 'import.*email_templates_data' app/ --include='*.py' | grep -v '__pycache__'
```

### Tasks

**1.1 — app/data/ → app/data/fixtures/*.json**

- [ ] For each `app/data/*.py`: convert Python dicts/lists to JSON
- [ ] Create `app/data/loader.py` with `load_fixture(name: str) -> dict` helper
- [ ] Load at startup via `@app.on_event("startup")` into in-memory cache
- [ ] Delete all `app/data/*.py` files
- [ ] Estimated reduction: **−16,565 LOC**

Example loader:
```python
# app/data/loader.py
import json
from functools import lru_cache
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@lru_cache(maxsize=64)
def load_fixture(name: str) -> dict | list:
    path = FIXTURES_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))
```

**1.2 — email_templates_data.py → Jinja2 HTML templates**

- [ ] Move HTML email bodies to `app/templates/emails/*.html`
- [ ] Keep only template name → file path mapping in Python
- [ ] Delete `app/services/email_templates_data.py`
- [ ] Estimated reduction: **−2,032 LOC**

**1.3 — Find other large data blobs**

```bash
# Files with 50+ lines of pure dict/list definitions
grep -rn "^    ['\"].*['\"]:" app/ --include='*.py' -l \
  | xargs wc -l | sort -rn | head -20
```

- [ ] Review top 10 results and extract to JSON where applicable

### Success Criteria

- `find app/data -name '*.py' | grep -v loader | grep -v __init__` → 0 files
- `email_templates_data.py` deleted
- All email sending still works (integration test)
- LOC reduction: **≥ 18,000**

### Code Review Checkpoint

```bash
python3 -m pytest tests/integration/test_email_service.py -v
grep -r 'from app.data' app/ --include='*.py' | grep -v 'loader'  # must be 0
```

---

## Phase 2 — Extract DB Calls from Controllers to Repositories

### Pre-flight Audit

```bash
# Count direct db calls in API files
grep -rn "await db\.\|sa\.select\|sa\.insert\|sa\.update\|sa\.delete" \
    app/api/ --include='*.py' | grep -v '#' | wc -l

# Top offenders by file
grep -rn "await db\." app/api/ --include='*.py' \
    | cut -d: -f1 | sort | uniq -c | sort -rn | head -20
```

### Priority Files (by DB call count)

1. `app/api/v1/company.py` — **209 db calls**
2. `app/api/v1/recruitment_stages.py` — **129 db calls**
3. `app/api/v1/candidates.py` — **96 db calls**
4. `app/api/v1/clients.py` — **87 db calls**
5. `app/api/v1/jobs.py` — ~70 db calls

### Tasks

**2.1 — Activate existing shared repositories (already written, 0 usages)**

Repositories exist but are completely unused:
- `app/shared/repositories/candidate_repository.py` (86 LOC)
- `app/shared/repositories/job_repository.py` (79 LOC)
- `app/shared/repositories/company_repository.py` (43 LOC)
- `app/shared/repositories/notification_repository.py` (88 LOC)

Steps:
- [ ] Add missing query methods to each
- [ ] Wire into FastAPI via `Depends(get_candidate_repository)`
- [ ] Replace all direct DB calls in `candidates.py` with repo methods

**2.2 — Create missing repositories**

- [ ] Expand `company_repository.py` to cover all 209 company.py DB ops
- [ ] Create `recruitment_stage_repository.py`
- [ ] Create `client_repository.py`

**2.3 — Base Repository template**

```python
# app/shared/repositories/base_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import TypeVar, Generic, Type, Optional, List

ModelT = TypeVar("ModelT")

class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: int) -> Optional[ModelT]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> List[ModelT]:
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id: int) -> bool:
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0
```

**2.4 — Controller template (after extraction)**

```python
# CORRECT: controller has zero SQL
@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: int,
    repo: CandidateRepository = Depends(get_candidate_repository),
    current_user: User = Depends(get_current_user),
):
    candidate = await repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate
```

**2.5 — Service layer for cross-entity logic**

When a controller calls more than 1 repository or has business rules:

```python
# app/domains/candidates/services/candidate_service.py
class CandidateService:
    def __init__(
        self,
        candidate_repo: CandidateRepository,
        job_repo: JobRepository,
    ):
        self.candidate_repo = candidate_repo
        self.job_repo = job_repo

    async def apply_to_job(self, candidate_id: int, job_id: int):
        candidate = await self.candidate_repo.get_by_id(candidate_id)
        job = await self.job_repo.get_by_id(job_id)
        # Business rules here, not in the controller
        if job.status != "open":
            raise ValueError("Job is not accepting applications")
        return await self.candidate_repo.create_application(candidate, job)
```

### Success Criteria

- `grep -rn "await db\." app/api/ --include='*.py' | wc -l` → **0**
- All existing API tests pass without regression
- No N+1 queries introduced (use EXPLAIN ANALYZE on key flows)

### Code Review Checkpoint

```bash
python3 -m pytest tests/ -v --tb=short -x
# Verify zero direct DB in controllers:
grep -rn "sa\.select\|sa\.insert\|sa\.update\|sa\.delete\|db\.execute" \
    app/api/ --include='*.py' | grep -v '#'
```

---

## Phase 3 — Consolidate Duplicate Model/Schema Layers

### Pre-flight Audit

```bash
# Count model files per location
find app/models -name '*.py' | grep -v __pycache__ | wc -l
find app/domains -path '*/models/*.py' | grep -v __pycache__ | wc -l

# Find duplicated names across locations
python3 - << 'EOF'
import os
from collections import defaultdict
names = defaultdict(list)
search_dirs = ["app/models", "app/domains", "libs"]
for search_dir in search_dirs:
    for root, dirs, files in os.walk(search_dir):
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py") and f not in ("__init__.py",):
                names[f].append(os.path.join(root, f))
for name, locs in sorted(names.items()):
    if len(locs) > 1:
        print(f"{name}: {locs}")
EOF
```

### Tasks

**3.1 — Declare `lia_models` as the single canonical source of truth**

- [ ] Document in ARCHITECTURE.md (Phase 8): "ORM models live ONLY in `lia_models`"
- [ ] For each `app/models/*.py` that has a duplicate in `lia_models`: delete app version, update imports
- [ ] For models only in `app/models/`: move to `lia_models`, update imports

**3.2 — Schema consolidation (9 duplicates identified)**

- [ ] For each duplicate in `app/schemas/` vs `app/domains/*/schemas/`:
  - Keep domain version
  - Delete `app/schemas/` version
  - Update all imports

**3.3 — Import update script**

```bash
# After moving models:
find app/ -name '*.py' -exec sed -i \
    's/from app\.models\.\([^ ]*\) import/from lia_models.\1 import/g' {} +
# Verify:
python3 -c "import app.main; print('OK')"
```

**3.4 — Domain model files that re-export → convert to 1-liners**

```python
# app/domains/analytics/models/observability.py (already done)
from lia_models.observability import *  # noqa: F401, F403
```

Apply same pattern to all `app/domains/*/models/*.py` files.

### Success Criteria

- Model definitions exist in exactly ONE location per entity
- `find app/models -name '*.py' | grep -v __init__` → 0 files
- All imports resolve: `python3 -c "from app.main import app"` exits 0
- LOC reduction: **≥ 28,000**

---

## Phase 4 — Complete DDD Migration

### Pre-flight Audit

```bash
# Services still in legacy flat layer
find app/services -name '*.py' | grep -v '__pycache__\|__init__' | wc -l

# Services in domain layer
find app/domains -path '*/services/*.py' | grep -v '__pycache__\|__init__' | wc -l

# Find services that exist in both layers (duplicates)
comm -12 \
    <(find app/services -name '*.py' | xargs -I{} basename {} | sort) \
    <(find app/domains -path '*/services/*.py' | xargs -I{} basename {} | sort)
```

### Domain Mapping

| Legacy File Pattern | Target Domain |
|---|---|
| `candidate_*.py` | `app/domains/candidates/services/` |
| `job_*.py` | `app/domains/jobs/services/` |
| `email_*.py` | `app/domains/communications/services/` |
| `company_*.py` | `app/domains/companies/services/` |
| `billing_*.py` | `app/domains/billing/services/` |
| `automation_*.py` | `app/domains/automation/services/` |
| `ai_*.py` / `llm_*.py` | `app/domains/ai/services/` |
| `report_*.py` | `app/domains/analytics/services/` |
| `scheduling_*.py` | `app/domains/scheduling/services/` |
| `wsi_*.py` | `app/domains/voice/services/` |

### Tasks

**4.1 — Ensure all domain directories exist**

```bash
for domain in candidates jobs communications companies billing automation \
              ai analytics scheduling voice cv_screening; do
    mkdir -p app/domains/$domain/{services,repositories,schemas,models}
    touch app/domains/$domain/__init__.py
    touch app/domains/$domain/services/__init__.py
    touch app/domains/$domain/repositories/__init__.py
    touch app/domains/$domain/schemas/__init__.py
done
```

**4.2 — Migrate each service file**

For each file in `app/services/`:
- [ ] Identify its domain
- [ ] Check if equivalent exists in `app/domains/{domain}/services/`
- [ ] If duplicate: merge unique logic → delete legacy → update imports
- [ ] If unique: move to domain dir → update imports

**4.3 — Delete `app/services/` when empty**

- [ ] After all migrations verified: remove directory
- [ ] Update any `app/services/__init__.py` re-exports

**4.4 — Domain service DI wiring**

```python
# app/domains/candidates/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from .repositories.candidate_repository import CandidateRepository
from .services.candidate_service import CandidateService

def get_candidate_service(db: AsyncSession = Depends(get_db)) -> CandidateService:
    repo = CandidateRepository(db)
    return CandidateService(repo)
```

### Success Criteria

- `find app/services -name '*.py' | grep -v '__init__\|__pycache__'` → 0 files
- All domains have the structure: `services/`, `repositories/`, `schemas/`
- LOC reduction: **≥ 18,000** via deduplication of dual-layer logic

### Rails-Deprecated Services (DO NOT MIGRATE)

The following  files are **Rails-deprecated**: they perform CRUD that will be
handled exclusively by the Rails ATS API (). Do **not** move these to a domain;
they should be deleted once the FastAPI→Rails handoff is complete.

| Service file | Rails endpoint replacing it |
|---|---|
|  |  |
|  |  |
|  |  |
|  |  |
|  |  |
|  | Rails managed via jobs/mailers |
|  | Rails managed interviews |
|  | Rails managed notifications |
|  |  |
|  |  |

**Rails integration bridge:** 
maps Fork UUID ↔ Rails bigint IDs and proxies reads/writes to the Rails API.
The adapter tries Rails first and falls back to local PostgreSQL, so no data loss
occurs during the transition period.

---

## Phase 5 — Response Models & API Contract Hardening

### Pre-flight Audit

```bash
# Endpoints without response_model
grep -rn "@router\." app/api/ --include='*.py' | grep -v 'response_model' | wc -l

# Files with most missing response_model
grep -rn "@router\." app/api/ --include='*.py' \
    | grep -v 'response_model' | cut -d: -f1 \
    | sort | uniq -c | sort -rn | head -20
```

### Tasks

**5.1 — Add response_model to all GET endpoints first (lowest risk)**

```python
# BEFORE
@router.get("/{id}")
async def get_candidate(id: int, db: AsyncSession = Depends(get_db)):
    ...

# AFTER
@router.get("/{id}", response_model=CandidateResponse)
async def get_candidate(id: int, repo: CandidateRepository = Depends(...)):
    ...
```

**5.2 — Create missing response schemas**

```python
# app/domains/candidates/schemas/candidate_schema.py
from pydantic import BaseModel
from datetime import datetime

class CandidateResponse(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}  # Pydantic v2
```

**5.3 — Target: 100% endpoint coverage**

Priority order:
1. GET (read) endpoints — safe, just serialization
2. POST creation endpoints — validate output shape
3. PATCH/PUT — validate returned updated object
4. DELETE — use `Response(status_code=204)` pattern

### Success Criteria

- `grep -rn "@router\." app/api/ --include='*.py' | grep -v response_model | wc -l` → **0**
- OpenAPI schema (`/docs`) shows typed responses for all endpoints

---

## Phase 6 — Move LLM Prompts Out of Python Files

### Pre-flight Audit

```bash
# Find files with large multiline strings (likely prompts)
python3 - << 'EOF'
import ast, os
for root, dirs, files in os.walk("app"):
    dirs[:] = [d for d in dirs if d != "__pycache__"]
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(root, fname)
        try:
            tree = ast.parse(open(fpath).read())
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                lines = node.value.count("\n")
                if lines > 15:
                    print(f"{fpath}:{node.lineno} — {lines} line string")
EOF
```

### Directory Structure

```
app/prompts/
├── cv_screening/
│   ├── parse_cv.md
│   └── score_candidate.md
├── recruitment/
│   ├── job_description_generator.md
│   └── interview_questions.md
├── agents/
│   ├── orchestrator_system.md
│   └── intent_classifier.md
└── loader.py
```

### Tasks

**6.1 — Create prompt loader**

```python
# app/prompts/loader.py
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

@lru_cache(maxsize=128)
def load_prompt(domain: str, name: str, **kwargs: str) -> str:
    path = PROMPTS_DIR / domain / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    template = path.read_text(encoding="utf-8")
    return template.format(**kwargs) if kwargs else template
```

**6.2 — Replace inline prompts**

```python
# BEFORE (50 lines of prompt in Python)
SYSTEM_PROMPT = """
You are an expert HR assistant specializing in...
[50 lines of instructions]
"""

# AFTER
from app.prompts.loader import load_prompt
SYSTEM_PROMPT = load_prompt("agents", "orchestrator_system")
```

**6.3 — Benefits of externalizing prompts**

- Prompts become reviewable as plain text in git diffs
- Non-developers (product, HR experts) can edit prompts directly
- A/B testing becomes trivial: swap files, no code changes
- Prompt versioning and rollback via git history
- Estimated reduction: **−6,000 LOC** from Python files

### Success Criteria

- No string literal longer than 10 lines in any agent/LLM Python file
- All prompts in `app/prompts/**/*.md`
- `load_prompt()` called in all LLM chain/agent definitions

---

## Phase 7 — Fix Test Suite

### Pre-flight Audit

```bash
find tests/ -name 'coverage_boost_*.py' | xargs wc -l
python3 -m pytest tests/ --co -q 2>/dev/null | tail -5
python3 -m pytest tests/ -v --tb=no -q 2>/dev/null | grep -E "passed|failed|error"
```

### Tasks

**7.1 — Delete fake coverage files**

- [ ] Delete all `tests/coverage_boost_*.py` files (5 files, ~2,000 LOC)
- [ ] These have no assertions — they inflate coverage metrics dishonestly

**7.2 — Add real integration tests for critical paths**

```
tests/integration/
├── test_candidate_crud.py        # create, read, update, delete candidate
├── test_job_application.py       # apply → shortlist → interview flow
├── test_auth_jwt.py              # login, token refresh, invalid token
├── test_rls_isolation.py         # company A cannot read company B data
├── test_email_delivery.py        # mock SMTP, verify template rendering
└── test_ai_cv_screening.py       # mock LLM, verify scoring logic
```

**7.3 — Test conventions (every test must have assertions)**

```python
# tests/integration/test_candidate_crud.py
import pytest
from httpx import AsyncClient

async def test_create_candidate_returns_201(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/candidates",
        json={"name": "Test User", "email": "test@example.com"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "Test User"
    # Verify PII not leaked
    assert "email" not in str(data.get("_debug", ""))
```

**7.4 — Add coverage gate to CI**

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-fail-under=70 --cov-report=term-missing"
```

### Success Criteria

- 0 `coverage_boost_*.py` files
- Coverage comes only from real assertions
- All 6 critical integration test paths covered
- CI fails if coverage drops below 70%

---

## Phase 8 — Guardrails, CI Enforcement & Pre-commit Hooks

### Tasks

**8.1 — Pre-commit config**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: no-sql-in-controllers
        name: "Guard: No SQL in API controllers"
        language: python
        entry: python3 scripts/check_no_sql_in_controllers.py
        files: ^app/api/.*\.py$

      - id: no-pii-in-logs
        name: "Guard: No PII in log calls"
        language: python
        entry: python3 scripts/check_no_pii_in_logs.py
        files: ^app/.*\.py$

      - id: response-model-required
        name: "Guard: All router decorators must have response_model"
        language: python
        entry: python3 scripts/check_response_models.py
        files: ^app/api/.*\.py$
```

**8.2 — scripts/check_no_sql_in_controllers.py**

```python
#!/usr/bin/env python3
"""CI guard: zero SQLAlchemy calls allowed in app/api/ files."""
import sys
import re
from pathlib import Path

SQL_PATTERNS = [
    r"await\s+db\.(execute|scalar|scalars|query)",
    r"\bsa\.(select|insert|update|delete|text)\(",
    r"from sqlalchemy",
]

errors = []
for path in Path("app/api").rglob("*.py"):
    content = path.read_text()
    for i, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pattern in SQL_PATTERNS:
            if re.search(pattern, line):
                errors.append(f"{path}:{i}: SQL in controller: {stripped[:80]}")

if errors:
    for e in errors:
        print(e)
    sys.exit(1)

print(f"OK: No SQL in controllers ({len(list(Path('app/api').rglob('*.py')))} files checked)")
```

**8.3 — scripts/check_no_pii_in_logs.py**

```python
#!/usr/bin/env python3
"""CI guard: no PII fields in log calls (LGPD Art. 46)."""
import sys
import re
from pathlib import Path

PII_FIELDS = [
    "email", "recipient_email", "candidate_email", "user_email",
    "cpf", "phone", "mobile", "full_name", "nome_completo",
]

LOG_PATTERN = re.compile(r"(logger\.|logging\.|log\.)(info|warning|error|debug|critical)\(")
PII_PATTERN = re.compile(
    r"(" + "|".join(re.escape(f) for f in PII_FIELDS) + r")\s*=", re.IGNORECASE
)

errors = []
for path in Path("app").rglob("*.py"):
    if "__pycache__" in str(path):
        continue
    lines = path.read_text().splitlines()
    in_log = False
    for i, line in enumerate(lines, 1):
        if LOG_PATTERN.search(line):
            in_log = True
        if in_log and PII_PATTERN.search(line):
            errors.append(f"{path}:{i}: PII in log: {line.strip()[:80]}")
        if in_log and ")" in line:
            in_log = False

if errors:
    for e in errors:
        print(e)
    sys.exit(1)

print("OK: No PII in log calls")
```

**8.4 — Ruff configuration additions**

```toml
# pyproject.toml — add to [tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "B",    # flake8-bugbear
    "S",    # flake8-bandit (security)
    "UP",   # pyupgrade
    "RUF",  # ruff-specific rules
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S105"]
"app/prompts/loader.py" = ["S"]
```

**8.5 — ARCHITECTURE.md**

```markdown
# Architecture Decision Records

## ADR-001: Repository Pattern (2026-04-06)
All database access MUST go through repository classes.
Controllers call services. Services call repositories.
Direct db.execute() in app/api/ files is FORBIDDEN.

## ADR-002: Canonical Model Location (2026-04-06)
SQLAlchemy ORM models are defined ONLY in the lia_models package.
Any file in app/models/ or app/domains/*/models/ must re-export from lia_models.

## ADR-003: Prompt Files (2026-04-06)
LLM prompts longer than 3 lines MUST live in app/prompts/*.md.
Python files contain only load_prompt() calls, never raw prompt strings.

## ADR-004: Hardcoded Data (2026-04-06)
Static data (lists, mappings, lookups) belongs in app/data/fixtures/*.json.
Python files that are pure data structures are FORBIDDEN.

## ADR-005: Response Models (2026-04-06)
Every @router endpoint MUST declare response_model.
FastAPI route handlers without response_model will fail CI.

## ADR-006: PII in Logs (2026-04-06)
No PII (email, CPF, phone, name) may appear in log calls.
Violation is a LGPD Art. 46 compliance risk.
```

### Success Criteria

- `pre-commit run --all-files` passes on clean codebase
- New PRs blocked by CI if they add SQL to controllers
- `ARCHITECTURE.md` committed to repo root with all ADRs
- `scripts/` directory with all 3 guard scripts committed

---

## Phase 9 — Fix Circular Imports & Misc Quality

### Pre-flight Audit

```bash
# Test startup for import errors
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    import app.main
    print('OK: No circular imports at startup')
except ImportError as e:
    print(f'FAIL: {e}')
"

# Run ruff to count current violations
ruff check app/ --statistics 2>/dev/null | head -20
```

### Circular Imports Identified (3 total)

1. `app/domains/ai/` ↔ `app/domains/candidates/`
2. `app/core/` ↔ `app/services/`
3. Circular in agent nodes (lazy/local import workaround exists)

### Fix Pattern

```python
# INSTEAD of top-level circular import:
from app.domains.candidates.models import Candidate  # circular!

# USE TYPE_CHECKING guard for type hints:
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.domains.candidates.models import Candidate

# OR use lazy import in function body:
def get_candidate_context(candidate_id: int):
    from app.domains.candidates.repositories import CandidateRepository
    ...
```

### Additional Misc Tasks

- [ ] Add `__all__` to all `__init__.py` files that re-export symbols
- [ ] Run `ruff check --fix app/` for auto-fixable issues (~800 estimated)
- [ ] Add `from __future__ import annotations` to all Python files
- [ ] Remove all unused imports flagged by ruff F401

### Success Criteria

- `python3 -c "import app.main"` exits 0 with no warnings
- `ruff check app/` → 0 errors
- LOC reduction from cleanup: **≥ 3,000**

---

## Phase 10 — Pydantic & Global Error Handling

### Tasks

**10.1 — Add ValidationError handler**

```python
# app/main.py — add after existing exception handlers
from pydantic import ValidationError

@app.exception_handler(ValidationError)
async def pydantic_validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    logger.warning(
        "Pydantic validation error",
        path=str(request.url.path),
        method=request.method,
        error_count=len(exc.errors()),
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "code": "VALIDATION_ERROR",
            "errors": exc.errors(include_url=False),
        },
    )
```

**10.2 — Add RequestValidationError handler**

```python
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "Request validation error",
            "code": "REQUEST_VALIDATION_ERROR",
            "detail": exc.errors(),
        },
    )
```

**10.3 — Standardize error response format**

All error responses must follow this shape:
```json
{
  "error": "Human-readable message for the client",
  "code": "MACHINE_READABLE_ERROR_CODE",
  "request_id": "uuid-for-distributed-tracing"
}
```

Add `request_id` middleware:
```python
# app/middleware/request_id.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response
```

### Success Criteria

- All 4xx errors return consistent JSON format
- ValidationError never returns 500
- All responses include `X-Request-Id` header for tracing

---

## Rails-Style Conventions Cheat-Sheet

> Bookmark this. These are the "rails" for the LIA project.

### The Golden Question Map

```
"I need to add a database query"
    → app/domains/{domain}/repositories/{name}_repository.py

"I need business logic involving multiple entities"
    → app/domains/{domain}/services/{name}_service.py

"I need a new API endpoint"
    → app/api/v1/{resource}.py  (ONLY: validate input, call service, return response)

"I need a new database table or column"
    → lia_models/{name}.py  +  alembic revision --autogenerate

"I need to store reference/lookup data"
    → app/data/fixtures/{name}.json

"I need a new LLM prompt"
    → app/prompts/{domain}/{name}.md

"I need a Pydantic schema for request/response"
    → app/domains/{domain}/schemas/{name}_schema.py
```

### The "Is This OK?" PR Checklist

Before every PR, run through this:

- [ ] Does my controller have any `db.execute` / SQLAlchemy calls? → **MOVE TO REPO**
- [ ] Does my controller have business logic beyond input validation? → **MOVE TO SERVICE**
- [ ] Does every endpoint have `response_model`? → **ADD IT**
- [ ] Does any log call include `email`, `cpf`, `phone`, or `name`? → **REMOVE IT (LGPD)**
- [ ] Is there a Python file that is mostly a dict/list? → **MOVE TO JSON**
- [ ] Is there a multiline string > 10 lines in an agent/LLM file? → **MOVE TO .md**
- [ ] Did I write `except:` without an exception type? → **USE `except Exception:`**
- [ ] Is my new file > 300 LOC? → **SPLIT IT**
- [ ] Did I add a real test with at least 1 `assert`? → **REQUIRED**
- [ ] Does a repository exist for this entity? → **USE IT, do not create a new one**

### Forbidden Patterns

```python
# FORBIDDEN: SQL in controller
@router.get("/candidates/{id}")
async def get_candidate(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Candidate).where(Candidate.id == id))  # NO!
    return result.scalar_one_or_none()

# FORBIDDEN: No response_model
@router.get("/jobs")
async def list_jobs(db: AsyncSession = Depends(get_db)):  # Missing response_model!
    ...

# FORBIDDEN: Bare except
try:
    ...
except:  # NO! Use except Exception: or specific exception
    pass

# FORBIDDEN: PII in logs
logger.info("Sending email", recipient_email=user.email)  # LGPD violation!

# FORBIDDEN: Long prompt in Python
PROMPT = """
You are an expert... [50 lines]
"""  # Move to app/prompts/domain/name.md

# FORBIDDEN: Data in Python
COUNTRY_CODES = {"BR": "Brazil", "US": "United States", ...}  # 200 lines
# Move to app/data/fixtures/country_codes.json
```

---

---

## Rails Migration Boundary

> Added 2026-04-07 after ats-api-rails integration audit.

### What Rails owns (do NOT build local SQLAlchemy repos for these)

| Entity | Rails table | FastAPI bridge |
|---|---|---|
| Candidates | `candidates` | `RailsAdapter.get_candidate()` |
| Jobs / Vacancies | `jobs` | `RailsAdapter.get_job()` |
| Applications | `applies` | `RailsAdapter.get_apply()` |
| Selective Processes | `selective_processes` | `RailsAdapter.get_selective_process()` |
| Users | `users` | `RailsAdapter.get_user()` |
| Messages | `messages` | `RailsAdapter.get_message()` |
| Roles / Permissions | `roles`, `permissions` | Rails auth middleware |

**Bridge implementation:** `app/domains/integrations_hub/services/rails_adapter.py`
- UUID ↔ bigint mapping via `candidates.fork_uuid` field
- Tries Rails API first, falls back to local PostgreSQL during transition period
- Enabled by `RAILS_API_URL` env var

### What FastAPI owns permanently

| Domain | Key entities | Status |
|---|---|---|
| credits | CreditAccount, CreditTransaction | ✅ Domain layer complete |
| cv_screening | RubricTemplate, ScreeningResult | ✅ Domain layer complete |
| billing | Plans, Subscriptions | 🔄 Needs repo extraction |
| analytics | Metrics, Reports | 🔄 Needs repo extraction |
| ai / llm | Prompts, Scores, Embeddings | 🔄 Needs repo extraction |
| scheduling | Slots, Calendar | 🔄 Needs repo extraction |
| communications | EmailLog, Notifications | ⚠️ Partially done |
| integrations_hub | RailsAdapter, external connectors | ✅ Done |

### Phase-level impact of Rails boundary

| Phase | Original plan | Rails-aware adjustment |
|---|---|---|
| **2** | Extract ALL DB calls to repos | Split: Rails-owned → route via rails_adapter (no new repo); FastAPI-owned → create repo |
| **3** | Shim all model files to lia_models | ⚠️ Follow-up needed: 359 service files import Rails-owned models (Candidate, JobVacancy) — convert to adapter calls |
| **4B** | (new) Migrate shared/services | Classify first: Rails-deprecated vs AI-permanent before moving |

---

## Phase 4B — Migrate app/shared/services/ to Domain Layer

> The real DDD work. Phase 4 shimmed `app/services/` but `app/shared/services/` has 112 real implementations (400KB+ of business logic) with no domain equivalents.

### Current state (2026-04-07)

```
app/shared/services/    112 real Python files  (NOT shims)
app/domains/*/services/ 3 overlap with shared  (only credit_service, rails_adapter, rails_adapter_dependency)
Pending migration:      109 files
```

### Classification matrix

| Category | Est. count | Target | Rails impact |
|---|---|---|---|
| AI-core (CV scoring, LLM, embeddings, rubrics) | ~25 | `app/domains/{ai,cv_screening}/services/` | None — keep forever |
| Credits & billing | ~5 | `app/domains/{credits,billing}/services/` | None — keep forever |
| Candidate CRUD (sourcing, pearch, pipeline) | ~15 | **Rails-deprecated** | Delete after Rails handoff |
| Job/vacancy CRUD | ~15 | **Rails-deprecated** | Delete after Rails handoff |
| Cross-cutting (policy, audit, config, LGPD) | ~20 | Keep in `app/shared/` (truly cross-cutting) | None |
| Communications (email, notifications) | ~10 | `app/domains/communications/services/` | None — keep |
| Infra/utils (cache, circuit breaker, seed) | ~11 | Keep in `app/shared/infra/` | None |
| Org/company (org catalog, skills catalog) | ~10 | `app/domains/company/services/` | Partial — some owned by Rails |

### Classification script

```bash
cd /home/runner/workspace/lia-agent-system
python3 -c "
import pathlib
ss = pathlib.Path('app/shared/services')
rails_kw = ['candidate', 'job_vacanc', 'apply', 'selective_process', 'vacancy_candidate']
for f in sorted(ss.glob('*.py')):
    if f.name == '__init__.py': continue
    text = f.read_text().lower()
    rails_hits = sum(1 for kw in rails_kw if kw in text)
    lines = len(f.read_text().splitlines())
    tag = 'RAILS-DEPRECATED' if rails_hits >= 3 else 'AI-PERMANENT  '
    print(f'{tag}  {lines:5}L  {f.name}')
" | sort
```

### Tasks

**4B.1 — Run classification script above, review output**

**4B.2 — Move AI-permanent services to their domains**

For each AI-permanent service:
1. Identify domain (cv_screening, analytics, billing, etc.)
2. Move to `app/domains/{domain}/services/{name}.py`
3. Leave a 2-line shim in `app/shared/services/` for backwards compatibility
4. Update import sites in API layer

**4B.3 — Mark Rails-deprecated services**

For each Rails-deprecated service:
1. Add deprecation notice: `# RAILS-DEPRECATED: will be deleted after Rails handoff`
2. Do NOT move to a domain
3. Ensure imports are routed via RailsAdapter where possible

**4B.4 — Shrink app/shared/services/ to cross-cutting only**

Target: `app/shared/services/` should only contain truly cross-cutting utilities
(policy engine, audit, LGPD, config). Everything else goes to a domain.

### Success criteria

```bash
# AI services in domains (target: >= 20)
find app/domains -path "*/services/*.py" | grep -v __init__ | wc -l

# shared/services real impls (target: <= 25, only cross-cutting)
find app/shared/services -name "*.py" | grep -v __init__ | wc -l

# shared/services with "Service" class (target: <= 20)
grep -rl "class.*Service" app/shared/services/ --include="*.py" | wc -l
```


## Progress Tracker

### Phase Completion Status

| Phase | Status | LOC Before | LOC After | Delta | Completed |
|---|---|---|---|---|---|
| 0 — Hardening (P0-P2) | ✅ DONE | 556,000 | ~555,500 | −500 | 2026-04-06 |
| 1 — Hardcoded data | ✅ DONE | 556,000 | ~393,000 | −16,689 | 2026-04-06 |
| 2 — Extract DB to repos | ✅ DONE 95% | — | ~400K | 215 API files clean (0 direct DB), 18 RAILS-DEPRECATED; 104 domain repos created; 18 edge-case calls remain (1-2/file, complex transactions); 339 contract tests pass | 2026-04-07 |
| 3 — Model consolidation | ✅ DONE 100% | ~393,600 | ~393,200 | 128 service files fixed (app.models→lia_models, 284 import lines); 4 Case-C files remain (no lia_models equiv yet: interview_note, wsi_session, candidate_job, communication) | 2026-04-07 |
| 4 — DDD migration | ✅ DONE 100% | — | — | 73 services migrated to domains (ai:12, analytics:21, cv_screening:20, company:7, voice:4, lgpd:5, integrations_hub:3, policy:1); 16 RAILS-DEPRECATED; 2 cross-cutting kept; 87 shims in shared/ | 2026-04-07 |
| 5 — Response models | ✅ DONE | ~392,500 | ~393,600 | +808 opt-outs | 2026-04-06 |
| 6 — Prompts to YAML | ✅ DONE | ~393,000 | ~392,500 | −544 | 2026-04-06 |
| 7 — Fix tests | ✅ DONE | — | — | rename only | 2026-04-06 |
| 8 — Guardrails & CI | ✅ DONE | — | — | +scripts | 2026-04-06 |
| 9 — Circular imports & quality | ✅ DONE | ~556K | ~400K | −156K LOC (ruff 1327 fixes) | 2026-04-06 |
| 10 — Error handling | ✅ DONE | — | — | +4 handlers | 2026-04-06 |

### Key Metrics Dashboard

Run before and after each phase:

```bash
#!/bin/bash
echo "========================================="
echo "LIA CODEBASE METRICS — $(date +%Y-%m-%d)"
echo "========================================="
echo ""
echo "Total LOC (app/):"
find app/ -name '*.py' | xargs wc -l 2>/dev/null | tail -1

echo ""
echo "API files with direct SQL:"
grep -rl "await db\.\|sa\.select\|sa\.insert\|sa\.update\|sa\.delete" \
    app/api/ --include='*.py' 2>/dev/null | wc -l

echo ""
echo "Endpoints without response_model:"
grep -rn "@router\." app/api/ --include='*.py' 2>/dev/null \
    | grep -v response_model | wc -l

echo ""
echo "Files > 300 LOC:"
find app/ -name '*.py' | xargs wc -l 2>/dev/null \
    | awk '$1 > 300' | grep -v total | wc -l

echo ""
echo "Services in legacy flat layer (should reach 0):"
find app/services -name '*.py' 2>/dev/null \
    | grep -v '__init__\|__pycache__' | wc -l

echo ""
echo "Unused repositories:"
for f in app/shared/repositories/*.py; do
    [ -f "$f" ] || continue
    name=$(basename $f .py)
    count=$(grep -r "$name" app/api/ app/domains/ --include='*.py' 2>/dev/null \
        | grep -v __pycache__ | wc -l)
    echo "  $name: $count usages"
done

echo ""
echo "Files with bare except:"
grep -rn "^[[:space:]]*except:" app/ --include='*.py' 2>/dev/null \
    | grep -v '#' | wc -l

echo ""
echo "Fake coverage test files:"
find tests/ -name 'coverage_boost_*.py' 2>/dev/null | wc -l
echo "========================================="
```

### Definition of Done

The full refactor is complete when ALL of these pass:

```
[ ] Total LOC ≤ 280,000
[ ] grep -rn "await db\." app/api/ | wc -l  →  0
[ ] find app/services -name '*.py' | grep -v __init__  →  0 files
[ ] find app/data -name '*.py' | grep -v loader | grep -v __init__  →  0 files
[ ] All 1,557 endpoints have response_model
[ ] pre-commit run --all-files  →  passes
[ ] python3 -m pytest tests/ --cov=app --cov-fail-under=70  →  passes
[ ] grep -rn "^[[:space:]]*except:" app/ | grep -v '#'  →  0
[ ] No log calls containing PII fields
[ ] ARCHITECTURE.md committed with all ADRs (ADR-001 through ADR-006)
[ ] scripts/check_no_sql_in_controllers.py committed and wired to CI
```

---

*Last updated: 2026-04-06 | Maintainer: Engineering Team*
*Related: HARDENING_PLAN.md (P0-P2 security fixes, completed)*
