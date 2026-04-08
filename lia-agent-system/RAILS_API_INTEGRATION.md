# Rails API Integration Reference

> **Updated:** 2026-04-08
> **Strategy:** Option A (REST) — FastAPI → Rails via HTTP
> **Auth:** Bearer token (user JWT forwarded) + RAILS_API_TOKEN (service-to-service fallback)

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `RAILS_API_URL` | Yes (for Rails) | `http://localhost:3000` | Base URL of the Rails API |
| `RAILS_API_TOKEN` | Yes (for service calls) | *(empty)* | Static service-to-service token |
| `RAILS_API_TIMEOUT` | No | `30` | HTTP timeout in seconds |
| `RAILS_JWT_SECRET_KEY` | No | *(empty)* | Secret for validating Rails-issued JWTs |

**Enablement semantics:**
- Rails integration is **opt-in**: `RAILS_ENABLED = bool(os.environ.get("RAILS_API_URL"))`.
- When `RAILS_API_URL` is **not** set, `RAILS_ENABLED=False` and **all reads go directly to the local PostgreSQL (fork DB)** — the `localhost:3000` default in `WeDOTalentATSClient` is never reached through the adapter.
- To enable Rails (even locally), you **must** set `RAILS_API_URL=http://localhost:3000` explicitly.
- This design is intentional: it prevents accidental Rails calls in environments where ats-api-copia is not running.

---

## Endpoint Mapping — Rails ↔ FastAPI

### Auth / Session

| Rails Endpoint | Rails Method | FastAPI Proxy | Notes |
|---|---|---|---|
| `/v1/sessions` | `POST` | `POST /api/v1/auth/rails-login` *(future)* | Returns JWT |
| `/v1/me` | `GET` | *(internal only)* | Used by health check and JWT validation |

### Candidates

| Rails Endpoint | Rails Method | FastAPI Proxy | Adapter Method |
|---|---|---|---|
| `/v1/users/candidates` | `GET` | `GET /api/v1/candidates/` | `adapter.list_candidates()` |
| `/v1/users/candidates/:id` | `GET` | `GET /api/v1/candidates/{id}` | `adapter.get_candidate(id)` |
| `/v1/users/candidates` | `POST` | `POST /api/v1/candidates/` | `adapter.create_candidate(data)` |
| `/v1/users/candidates/:id` | `PUT` | `PUT /api/v1/candidates/{id}` | `adapter.update_candidate(id, data)` |
| `/v1/users/candidates/:id` | `DELETE` | `DELETE /api/v1/candidates/{id}` | `adapter.delete_candidate(id)` |

### Jobs (Vagas)

| Rails Endpoint | Rails Method | FastAPI Proxy | Adapter Method |
|---|---|---|---|
| `/v1/users/jobs` | `GET` | `GET /api/v1/jobs/` | `adapter.list_jobs()` |
| `/v1/users/jobs/:id` | `GET` | `GET /api/v1/jobs/{id}` | `adapter.get_job(id)` |
| `/v1/users/jobs` | `POST` | `POST /api/v1/jobs/` | `adapter.create_job(data)` |
| `/v1/users/jobs/:id` | `PUT` | `PUT /api/v1/jobs/{id}` | `adapter.update_job(id, data)` |
| `/v1/users/jobs/:id` | `DELETE` | `DELETE /api/v1/jobs/{id}` | `adapter.delete_job(id)` |

### Applications (Applies)

| Rails Endpoint | Rails Method | FastAPI Proxy | Adapter Method |
|---|---|---|---|
| `/v1/users/applies` | `GET` | `GET /api/v1/applications/` | `adapter.list_applies()` |
| `/v1/users/applies/:id` | `GET` | *(internal)* | `adapter.get_apply(id)` |
| `/v1/users/applies` | `POST` | `POST /api/v1/applications/` | `adapter.create_apply(candidate_id, job_id)` |
| `/v1/users/applies/:id` | `PUT` | *(internal)* | `adapter.update_apply(id, data)` |
| `/v1/users/applies/:id` | `DELETE` | *(future)* | `WeDOTalentATSClient.delete_apply(id)` |

### Selective Processes (Pipeline Stages)

| Rails Endpoint | Rails Method | FastAPI Proxy | Adapter Method |
|---|---|---|---|
| `/v1/users/selective_processes` | `GET` | *(internal)* | `adapter.list_selective_processes(job_id)` |

### Messages

| Rails Endpoint | Rails Method | FastAPI Proxy | Adapter Method |
|---|---|---|---|
| `/v1/users/messages` | `GET` | *(internal)* | `adapter.list_messages(page, limit, ...)` |
| `/v1/users/messages` | `POST` | *(internal)* | `adapter.send_message(content, ...)` |

### Health / Observability

| FastAPI Endpoint | Description |
|---|---|
| `GET /api/v1/rails/health` | Probe Rails reachability + circuit breaker state |
| `GET /api/v1/rails/status` | Circuit breaker stats only (no HTTP call to Rails) |
| `GET /api/v1/admin/circuit-breakers` | All circuit breakers including `rails_api` |

---

## Field Mapping: Fork (UUID model) ↔ Rails (bigint model)

Canonical mappings are defined in `app/domains/integrations_hub/services/rails_adapter.py`:

| Mapping Dict | Direction |
|---|---|
| `CANDIDATE_FORK_TO_RAILS` | Fork field → Rails field |
| `CANDIDATE_RAILS_TO_FORK` | Rails field → Fork field (auto-generated) |
| `JOB_FORK_TO_RAILS` | Fork field → Rails field |
| `APPLY_FORK_TO_RAILS` | Fork field → Rails field |
| `SELECTIVE_PROCESS_FORK_TO_RAILS` | Fork field → Rails field |
| `USER_FORK_TO_RAILS` | Fork field → Rails field |
| `MESSAGE_FORK_TO_RAILS` | Fork field → Rails field |

### Key Differences

| Concept | Fork (LIA) | Rails (ats-api) |
|---|---|---|
| Primary Key | UUID | bigint |
| Candidate name | `name` (single field) | `name` + `surname` |
| LinkedIn URL | `linkedin_url` | `linkedin` |
| Resume text | `resume_text` | `curriculum_text` |
| Resume file | `resume_url` | `curriculum_pdf_url` |
| Job location | `location` (single) | `city` + `state` + `country` |
| Remote work | `work_model` | `workplace_type` / `is_remote` |
| Active application | `is_active` | `is_deleted` (inverted) |
| Pipeline stage | `stage_id` → `recruitment_stages` | `selective_process_id` |

---

## Architecture Flow

```
Frontend
  │
  ▼
FastAPI (lia-agent-system)
  │
  ├─ [RAILS_API_URL set] ──► WeDOTalentATSClient
  │                             │  Bearer: user JWT or RAILS_API_TOKEN
  │                             │  Circuit: RAILS_CIRCUIT (5 fail → OPEN 30s)
  │                             │  Retry: 3x w/ exponential backoff (0.5s → 8s)
  │                             ▼
  │                          ats-api-copia (Rails 7)
  │                             │
  │                             ▼
  │                          PostgreSQL (Rails schema)
  │
  └─ [RAILS_API_URL not set OR Rails fails] ──► Local PostgreSQL (fork schema)
```

---

## Circuit Breaker — `rails_api`

| Parameter | Value |
|---|---|
| `failure_threshold` | 5 consecutive failures → OPEN |
| `recovery_timeout` | 30 seconds before HALF_OPEN |
| `success_threshold` | 2 successes to CLOSE |
| `timeout` | 15 seconds per request |
| SLO target | 99.9% availability |
| On OPEN | Adapter falls back to local DB (reads) |

---

## Adding a New Rails Endpoint

1. Add the HTTP method to `WeDOTalentATSClient` in `app/services/ats_clients/wedotalent_rails.py`
2. Add a mapping dict if needed in `rails_adapter.py`
3. Add a high-level method to `RailsAdapter` with local DB fallback
4. Wire into a FastAPI endpoint using `Depends(get_rails_adapter)`

---

## Security Notes

- **Never log** `RAILS_API_TOKEN` or user JWTs
- The token is forwarded as `Authorization: Bearer <token>` — Rails validates it server-side
- For tenant isolation: Rails uses the Apartment gem (schema per account). The user's JWT encodes the tenant — no tenant header needed from FastAPI
- `RAILS_API_TOKEN` should be set in GCP Secret Manager and injected at deploy time
