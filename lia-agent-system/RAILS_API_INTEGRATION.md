# Rails API Integration Reference

> **Updated:** 2026-04-09
> **Strategy:** Decision C — FastAPI is source of truth; Rails is opt-in bridge
> **Auth:** Bearer token (user JWT forwarded) + RAILS_API_TOKEN (service-to-service, bidirectional)
> **GitHub Org:** `WeDOTalentcc` (migrated from `WeDOTalent`)
> **Rails Repo:** `ats-api-copia`

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

## Reverse Direction — Rails → FastAPI (Sync API)

Rails can consume FastAPI-sourced data (AI insights, WSI scores, compliance) via the `/api/v1/rails-sync/` router.

### Authentication for Rails Callers

```
Authorization: Bearer <RAILS_API_TOKEN>
```

The same `RAILS_API_TOKEN` is used bidirectionally. Rails sets it as a Bearer token when calling FastAPI sync endpoints.

### Rails Sync Endpoints

| FastAPI Endpoint | Method | Description | Response |
|---|---|---|---|
| `/api/v1/rails-sync/candidates/{id}/enrichment` | `GET` | AI insights, WSI scores, screening results | `{candidate_id, wsi, ai_insights}` |
| `/api/v1/rails-sync/jobs/{id}/intelligence` | `GET` | Sourcing data, saturation, analytics | `{job_id, sourcing_data, saturation}` |
| `/api/v1/rails-sync/compliance/status` | `GET` | LGPD status, platform stats, audit summary | `{lgpd, platform_stats, audit}` |
| `/api/v1/rails-sync/bulk-sync/candidates` | `POST` | Batch enrichment (max 50 per request) | `{enrichments[], missing_ids[]}` |

### Rate Limits

- 120 requests per 60-second window (shared across all rails-sync callers per process)
- Bulk sync limited to 50 candidates per batch
- All requests are audit-logged
- Note: rate limiting is in-memory per worker process; for distributed rate limiting across instances, integrate Redis-based rate limiting

### Example: Rails Calling FastAPI

```ruby
# In Rails controller or service
response = HTTParty.get(
  "#{ENV['FASTAPI_URL']}/api/v1/rails-sync/candidates/#{candidate_id}/enrichment",
  headers: { "Authorization" => "Bearer #{ENV['RAILS_API_TOKEN']}" }
)
enrichment = JSON.parse(response.body)
candidate.update(wsi_score: enrichment.dig("wsi", "wsi_score"))
```

---

## Model Gap Analysis — Rails vs FastAPI

### Rails Models NOT in FastAPI (15 gaps)

| # | Rails Model | Domain | Priority | Notes |
|---|---|---|---|---|
| 1 | `recruitment_sla` | SLA | P2 | SLA tracking for recruitment stages |
| 2 | `sla_violation` | SLA | P2 | Violation events |
| 3 | `campaign_stage_event` | Campaigns | P3 | Event tracking for campaigns |
| 4 | `big_five_question` | Assessment | P3 | Big Five personality questions |
| 5 | `big_five_role_profile` | Assessment | P3 | Big Five role profiles |
| 6 | `technical_question` | Assessment | P2 | Technical test questions |
| 7 | `technical_test_template` | Assessment | P2 | Technical test templates |
| 8 | `planned_headcount` | Workforce | P3 | Workforce planning headcount |
| 9 | `workforce_entry` | Workforce | P3 | Workforce entries |
| 10 | `hiring_plan` | Workforce | P3 | Hiring plans |
| 11 | `import_job` | Import | P2 | Bulk import tracking |
| 12 | `template_category` | Templates | P3 | Already covered by email_templates.category |
| 13 | `template_usage_log` | Templates | P3 | Usage analytics |
| 14 | `shared_search_access` | Search | P3 | Shared search collaboration |
| 15 | `shared_search_feedback` | Search | P3 | Search feedback |
| 16 | `approval_request` | Workflow | P2 | Approval workflow |
| 17 | `pending_approval` | Workflow | P2 | Pending approvals |
| 18 | `automated_decision_explanation` | AI | P1 | AI decision transparency (EU AI Act) |
| 19 | `webhook_delivery_log` | Integration | P2 | Webhook delivery audit |
| 20 | `reschedule_history` | Interviews | P2 | Reschedule audit trail |

### Rails Reality Check

- **97 Ruby model files** but only **12 tables** in `schema.rb`
- 31 out of 49 migrations were never applied
- ~85 models are "orphans" with no database tables

---

## GitHub Repository Information

| Repo | Description | Org |
|---|---|---|
| `ats-api-copia` | Rails API (legacy) | `WeDOTalentcc` |
| `ats-front-copia` | Rails frontend (legacy) | `WeDOTalentcc` |
| `recruiter-agent-v5-copia` | Agent system v5 | `WeDOTalentcc` |
| `data-collector-copia` | Data collector | `WeDOTalentcc` |
| `ats-mcp-copia` | MCP integration | `WeDOTalentcc` |
| `wedo-nuxt-copia` | Nuxt frontend | `WeDOTalentcc` |

> **Note:** Org was migrated from `WeDOTalent` to `WeDOTalentcc`. Use secret `GITHUBWEDOCC2026` for API access (the Replit GitHub integration token is expired).

---

## Security Notes

- **Never log** `RAILS_API_TOKEN` or user JWTs
- The token is forwarded as `Authorization: Bearer <token>` — both directions validate server-side
- For tenant isolation: Rails uses the Apartment gem (schema per account). The user's JWT encodes the tenant — no tenant header needed from FastAPI
- `RAILS_API_TOKEN` should be set in GCP Secret Manager and injected at deploy time
- Rails sync endpoints are rate-limited and audit-logged
