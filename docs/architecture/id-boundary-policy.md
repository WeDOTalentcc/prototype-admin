# ID Boundary Policy — LIA × Rails

**Status:** Active convention. Derived from [ADR 003](../adr/003-id-strategy-lia-vs-rails.md).
**Audience:** Anyone adding a new endpoint, table column, event payload, or
external integration that crosses the LIA ↔ Rails boundary.
**TL;DR:** Use UUIDs by default. Only accept Rails bigints on routes that touch
entities the legacy ATS still authors. Translate through `RailsAdapter` — never
inline. Name external-id columns `external_<system>_id`.

---

## Quick reference

- **UUID-only by default.** Dual acceptance is a deliberate exception, only for
  entities Rails also authors (jobs, candidates, applications, interview stages).
- **Dual-ID path params:** type as `UUID`, *or* type as `str` with the regex
  `JOB_ID_PATH_PATTERN` (a.k.a. `DUAL_ID_PATH_PATTERN`). Never `str` without it.
- **Static collection routes register before item routes.** A regression test
  enforces this for jobs; extend it for new dual-ID resources.
- **New external-ID columns:** name them `external_<system>_id`, indexed,
  unique on `(company_id, external_<system>_id)` when applicable. Existing
  columns keep their names — no rename.
- **Translation:** only via `RailsAdapter`. No inline `looks_like_uuid`
  branches in handlers or services.
- **Events:** carry UUID; add `external_rails_id` as a separate field if Rails
  needs the bigint. Don't reuse one polymorphic `id`.
- **Audit logs / idempotency keys:** resolve to canonical UUID *before*
  hashing or logging.

---

## 1. Why this exists

The LIA backend speaks UUIDs. The legacy Rails ATS speaks bigints. Both are
allowed to author the same entities (jobs, candidates, applications), so several
endpoints must accept either format. ADR 003 chose to keep this coexistence
rather than refactor the boundary, but only if the convention is written down
and enforced. This document is that convention.

If you find yourself reinventing how to "accept either an UUID or an integer",
you are in the wrong place — read this page first.

---

## 2. When to use UUID-only vs. dual IDs

| Entity is authored… | API accepts | Storage |
|---|---|---|
| Only inside LIA (e.g. `Conversation`, `Message`, `ScreeningQuestion`) | **UUID only** | UUID PK |
| In LIA *and* in the Rails ATS (e.g. `JobVacancy`, `Candidate`, `VacancyCandidate`, `InterviewStage`) | **Dual** (UUID **or** Rails bigint) | UUID PK + `external_<system>_id` column |
| Only in Rails (read-through proxy, no LIA persistence) | Bigint only on the proxy route, but normalized to UUID at the service boundary | n/a (not stored) |

**Default to UUID-only.** Adding dual acceptance is a deliberate decision —
make it because the entity already exists in Rails, not because it might one day.

---

## 3. Path parameter contract

Any route whose path parameter ends in `_id` and refers to a **dual entity**
**must** declare the parameter with the dual-ID regex. This guards against the
Task #455 / #459 family of bugs (a string-typed `{id}` silently capturing a
sibling static segment such as `/job-vacancies/lifecycle-overview`).

The canonical pattern lives in
`lia-agent-system/app/api/v1/job_vacancies/_shared.py` as
`JOB_ID_PATH_PATTERN`. New code should reference it (or, if it has been moved
into a shared location, the renamed `DUAL_ID_PATH_PATTERN`):

```python
from app.api.v1.job_vacancies._shared import JOB_ID_PATH_PATTERN  # alias: DUAL_ID_PATH_PATTERN

@router.get("/{candidate_id}", ...)
async def get_candidate(
    candidate_id: str = Path(..., pattern=JOB_ID_PATH_PATTERN),
):
    ...
```

Routes whose parameter is typed as `UUID` (not `str`) get this for free from
Pydantic and do **not** need the regex.

**Router ordering invariant.** Static collection-scoped routes
(`/job-vacancies/lifecycle-overview`, `/bulk/...`, `/stats/...`) must be
registered before the item route (`/{job_vacancy_id}`). The regression test
`tests/api/test_job_vacancies_route_shadowing.py` protects this for jobs and
should be extended when new dual-ID resources are added.

---

## 4. Storage — naming external-ID columns

When a table needs to remember the identifier that another system uses for the
same logical row, the column **must** be named:

```
external_<system>_id
```

- `<system>` is the lowercase short name of the source (`rails`, `gupy`,
  `pandape`, `merge`, `pearch`, `vindi`, …).
- The column is `VARCHAR(255)` unless the source guarantees a narrower type
  (Rails bigints fit in `VARCHAR(50)`).
- It **must** carry a database index.
- It **must** carry a uniqueness constraint when the source guarantees the ID
  is unique within the tenant scope. Prefer a composite unique on
  `(company_id, external_<system>_id)` rather than a global unique.

Examples (new code):

```sql
external_rails_id  VARCHAR(50)  NOT NULL,
external_gupy_id   VARCHAR(255) NULL,
UNIQUE (company_id, external_rails_id)
```

**Existing columns do not get renamed.** `job_id`, `ats_candidate_id`,
`pearch_profile_id`, `external_id`, `ats_stage_id`, and the
`additional_data.ats_external_id` JSONB key all predate this policy. They keep
their current names to avoid a destructive migration. Only **new** columns
follow `external_<system>_id`.

---

## 5. Translation — `RailsAdapter` is the only authorized broker

UUID ↔ Rails bigint translation **must** go through
`lia-agent-system/app/domains/integrations_hub/services/rails_adapter.py`
(`RailsAdapter`). It owns:

- `_to_rails_id(...)` — UUID → Rails bigint.
- `_looks_like_uuid(...)` — shape detection at the boundary.
- The `GET /v1/candidates?fork_uuid=<uuid>` lookup that resolves UUID → bigint
  when the LIA needs to call back into Rails.
- The `JOB_FORK_TO_RAILS` / `APPLY_FORK_TO_RAILS` mappings.

What this means in practice:

- **Do not** parse a path parameter as "either UUID or int" inside a handler
  and branch on it. Hand the raw string to the service layer; let the
  repository or adapter resolve it.
- **Do not** add a new ad-hoc `if looks_like_uuid(x): ... else: ...` branch in
  a service. Extend `RailsAdapter` instead.
- **Do not** call the Rails API directly from a handler with a Rails bigint you
  pulled out of a webhook payload. Resolve to a UUID first via the adapter.
- New entities that need symmetric lookup (UUID → external bigint) extend the
  adapter's mapping table and, where appropriate, expose a `fork_uuid`-style
  lookup on the Rails side.

If the adapter does not support what you need, **add it to the adapter** rather
than working around it.

---

## 6. Event payloads

`app/shared/messaging/rails_event_schemas.py` defines the events that cross
the LIA ↔ Rails boundary today (`ScreeningCompletedEvent`,
`InterviewScheduledEvent`, …). The contract:

- Inbound events from Rails carry **bigints** (`apply_id`, `candidate_id`,
  `job_id`). Consumers translate to UUID via `RailsAdapter` before touching
  domain code.
- Outbound events published via `unified_event_publisher` (`lia_rails_events`
  exchange) carry **bigints** for fields Rails will consume.
- New event fields that reference an entity should carry the UUID. If Rails
  needs the bigint too, add it as a separate field named after the column
  convention (`external_rails_id`), not as a polymorphic `id`.

---

## 7. Audit logs and idempotency keys

`audit_logs.resource_id` and idempotency keys (see
`app/shared/robustness/context_management.py`) currently accept any string,
which means the same logical row can produce two distinct entries depending on
which ID format the caller used.

When you write code that contributes to either of these:

- Resolve the ID to its canonical UUID via `RailsAdapter` **before** logging
  or hashing.
- If you cannot (e.g. the row only exists in Rails), log both the bigint and
  a `source_system` tag so a human can deduplicate later.

---

## 8. Checklist for a new dual-ID endpoint

Before opening the PR:

- [ ] Path parameter uses `JOB_ID_PATH_PATTERN` (a.k.a. `DUAL_ID_PATH_PATTERN`)
      or is typed as `UUID`.
- [ ] Static sibling routes are registered before the item route.
- [ ] Translation goes through `RailsAdapter`. No inline `looks_like_uuid`.
- [ ] Any new external-ID column is named `external_<system>_id`, indexed, and
      uniqueness-constrained where appropriate.
- [ ] Event fields use the same convention.
- [ ] If the resource is new, the route shadowing regression test is extended
      to cover it.

---

## 9. Related

- [ADR 003 — Estratégia de IDs LIA × ATS Rails](../adr/003-id-strategy-lia-vs-rails.md)
- `lia-agent-system/app/api/v1/job_vacancies/_shared.py` (`JOB_ID_PATH_PATTERN`)
- `lia-agent-system/app/api/v1/job_vacancies/__init__.py` (router ordering)
- `lia-agent-system/app/domains/integrations_hub/services/rails_adapter.py`
- `lia-agent-system/app/shared/messaging/rails_event_schemas.py`
- `lia-agent-system/tests/api/test_job_vacancies_route_shadowing.py`
- Task #455, Task #459, Task #468 (origin of this policy)
