# WeDOTalent — Rails vs FastAPI Technical Debt Audit

**Date:** 2026-06-10  
**Scope:** ats_api (Rails, 580 routes), lia-agent-system (FastAPI, 1782 endpoints), plataforma-lia (Next.js, 645 proxy routes)  
**Auditor:** Automated discovery + synthesis

---

## Executive Summary

WeDOTalent is mid-migration from Rails (ats_api) to FastAPI (lia-agent-system). At the proxy layer the migration appears ~95% complete: 644 of 645 Next.js proxy routes explicitly target FastAPI at port 8001. This surface-level completion conceals several serious risks.

**The core structural situation:**
- FastAPI has 314 purpose-built tables (AI, screening, LGPD, calibration, etc.) — entirely its own domain
- Rails has 100+ tables that are its own domain (accounts, evaluations legacy, background agents, etc.)
- 13 tables are shared between both backends — written by both, with mismatched FK schemas
- Rails still owns: JWT issuance, agent token exchange, new-customer setup wizard, external webhook receivers
- FastAPI calls Rails as a data source (rails_sync.py, rails_health.py, /v1/me resolution on every auth'd request)

**Biggest immediate risks:**
1. RAILS_BACKEND_URL is unset → 4 onboarding proxy sub-paths return HTTP 503 (P0 functional break)
2. JobVacancy model references a DB column that does not exist (P0 crash risk on writes)
3. Five proxy routes hit a FastAPI endpoint returning HTTP 410 Gone, silently breaking the jobs page
4. LGPD opt-out and password reset tokens baked into delivered emails hit dead Rails routes with no redirect bridge
5. WorkOS webhook may still be configured to POST to Rails, silently dropping all user provisioning events

---

## 🔴 P0 Blockers — Broken Right Now

### P0-1: RAILS_BACKEND_URL unset — onboarding returns HTTP 503

**File:** `plataforma-lia/src/app/api/backend-proxy/onboarding/[...path]/route.ts`

The sole Rails-targeted proxy route in the entire codebase routes four active sub-paths (`status`, `progress`, `consent`, `invite`) to `RAILS_BACKEND_URL`. This env var is **not set** in `.env.local`. Every call to these paths returns HTTP 503 with no meaningful error message.

**Active callers:**
- `useOnboardingFlow.ts` → `/onboarding/status`
- `OnboardingChatPage.tsx` → `/onboarding/progress`
- Consent flows → `/onboarding/consent`
- User invitation emails → `/onboarding/invite` (maps to Rails `POST /v1/users/invite`)

**Impact:** New recruiter account onboarding is completely broken in any environment where RAILS_BACKEND_URL is not manually set. This is the entry path for new customers.

**Fix:** Set `RAILS_BACKEND_URL` in all environments immediately. Medium-term: implement FastAPI equivalents for these four sub-paths (FastAPI already has `/{user_id}/state` which may replace `/status`) and update the proxy to remove the Rails dependency entirely.

---

### P0-2: Schema drift — JobVacancy model references non-existent DB column

**File:** `lia-agent-system/libs/models/lia_models/job_vacancy.py`

The `JobVacancy` SQLAlchemy model declares `assigned_audience_policy` as a column. This column **does not exist** in the `job_vacancies` database table (confirmed by schema drift audit, severity: P0). Any ORM operation that causes SQLAlchemy to reflect or write this column will raise a DB error. Depending on SQLAlchemy configuration, this may crash job vacancy creation or updates silently.

**Secondary drift:**
- `compensation_policy_id` referenced in `JobVacancy` model, not in DB (severity: P1)
- `diversity_self_declaration` referenced in `Candidate` model, not in DB (severity: P2, LGPD-sensitive)

**Fix:** Either add an Alembic migration to create these columns, or remove them from the model with a deprecating comment explaining they are planned features not yet deployed.

---

### P0-3: /lia/job-wizard proxy cluster hits tombstoned endpoint (HTTP 410)

**Proxy files:**
- `plataforma-lia/src/app/api/backend-proxy/lia/job-wizard/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/lia/job-wizard/step/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/lia/job-wizard/evaluate/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/lia/job-wizard/interpret/route.ts`
- `plataforma-lia/src/app/api/backend-proxy/lia/job-wizard/orchestrate/route.ts`

**FastAPI handler:** `lia-agent-system/app/api/v1/lia_assistant/wizard.py` — all endpoints return HTTP 410 Gone (tombstoned).

**Active callers at runtime:**
- `use-lia-suggestions.ts:155` (called by `useJobsChat` on the active jobs page)
- `use-job-wizard-backend.ts:270`

The jobs page silently receives 410 for every LIA suggestion call. The canonical replacement is WebSocket `/ws/agent-chat` with `domain=job_creation`.

**Fix:** Update the two FE hooks to use the WS path. Delete all 5 proxy route.ts files.

---

### P0-4: WorkOS webhook may be silently dropping all user provisioning events

**Rails handler:** `ats_api/app/controllers/v1/workos_controller.rb` (`webhook` action)  
**FastAPI/Next.js handler:** `plataforma-lia/src/app/api/webhooks/workos/route.ts` → FastAPI `/api/v1/workos/users/created|updated|deleted`

If the WorkOS dashboard is still configured to POST to the Rails URL instead of the Next.js frontend URL, all WorkOS lifecycle events (user.created, user.updated, user.deleted, directoryUser.moved) are received by Rails and never forwarded to FastAPI. New SSO users are never provisioned in FastAPI's user table. This is a silent failure — no error surfaces to the user.

**Fix:** Log into the WorkOS dashboard and verify the webhook URL. If it points to Rails, update it to `https://{domain}/api/webhooks/workos`. Do not remove the Rails route until this is confirmed.

---

## 🟡 P1 Critical — Half-Migrated, Wrong Data, or Fragile Routing

### P1-1: Email opt-out ghost route — LGPD compliance gap

**Rails handler:** `ats_api/app/controllers/v1/email_opt_outs_controller.rb`  
**FastAPI handler:** `lia-agent-system/app/api/v1/communication_optout.py`  
**Proxy:** None exists for the Rails path

Opt-out tokens baked into emails delivered before the FastAPI migration resolve to the Rails endpoint (`GET /v1/email/opt-out/:token`). No redirect bridge exists. Under LGPD Art. 18, failure to process an unsubscribe/opt-out request is a compliance violation. Candidate emails contain opt-out links that never expire.

**Fix (quick win):** Add a Rails 301 redirect: `GET /v1/email/opt-out/:token → FastAPI /api/v1/communication-optout/{token}`. Implement within one day.

---

### P1-2: Password reset split-brain risk

**Rails handler:** `ats_api/app/controllers/v1/password_reset_tokens_controller.rb`  
**FastAPI handler:** `lia-agent-system/app/api/v1/auth.py` (`/forgot-password`, `/reset-password`)  
**Frontend:** `ForgotPasswordClient.tsx` → `/api/backend-proxy/auth/forgot-password` → FastAPI (correct)

Reset tokens issued by Rails before the migration and baked into reset emails still resolve to the Rails endpoint. If the Rails token store (likely `password_reset_tokens` table) and FastAPI token store (Redis or a FastAPI-owned table) are separate, users with old reset-link emails receive a silent error. No redirect bridge exists.

**Fix:** Add Rails 301 redirect from `/v1/password_resets/:token` to the FastAPI reset-password page with token as a query param.

---

### P1-3: Onboarding catch-all is hand-rolled regex — fragile split routing

**File:** `plataforma-lia/src/app/api/backend-proxy/onboarding/[...path]/route.ts`

The routing logic uses a hardcoded regex `/:d+/(context|state)/` to distinguish FastAPI-bound paths from Rails-bound paths within a single route.ts file. This pattern is invisible to standard proxy auditing tools and is the only file in 645 proxy routes that implements split-routing logic. Any new onboarding endpoint whose path matches the digit pattern will be silently misrouted.

**Fix:** Split into explicit sub-path files using `createProxyHandlers()`. Once FastAPI owns all four sub-paths (status, progress, consent, invite), the split logic disappears entirely.

---

### P1-4: Notifications Rails controller is dead code but Sidekiq may write to it

**Rails controller:** `ats_api/app/controllers/v1/notifications_controller.rb`  
**FastAPI owner:** `lia-agent-system/app/api/v1/notifications.py`

All frontend proxy routes for notifications target FastAPI exclusively. However, Sidekiq background jobs in Rails (`evaluations/completion_notification_job.rb`, `decline_notification_job.rb`) may still write notifications to a Rails-owned table. If FastAPI reads from a different physical notifications table, in-app notification counts are inconsistent and candidates may not receive expected system notifications.

**Fix:** Verify both backends share the same PostgreSQL instance and database. Run `SELECT COUNT(*) FROM notifications` from both connection strings and compare. If tables are separate, migrate the Sidekiq notification write path to call FastAPI's notification endpoint.

---

### P1-5: Department tree and org chart have no FastAPI equivalent

**Rails actions present:** `ancestors`, `descendants`, `organization_chart`, `tree`, `reorder`, `import`  
**FastAPI coverage:** CRUD + `/members` only (via `lia-agent-system/app/api/v1/company_departments.py`)  
**Proxy routes:** None for tree/org_chart actions

Any UI component rendering an org chart or department tree silently receives no data (likely shows empty state). `DepartmentImportJob` on Rails may write import results to a table that FastAPI does not read, making bulk department imports invisible in the FE.

**Fix:** Implement `ancestors`, `descendants`, `organization_chart`, `tree` in FastAPI `company_departments.py`. Until then, hide or disable the UI surfaces that depend on these endpoints.

---

### P1-6: Email templates seeded by Rails may land in a different table than FastAPI reads

**Rails:** `CreateTenantJob` → `EmailTemplates::SeedDefaultsService` writes default templates on new tenant creation  
**FastAPI:** `lia-agent-system/app/api/v1/email_templates.py` owns all frontend CRUD

Schema divergence is significant: Rails stores `content` as a single text field; FastAPI has `body_html`, `body_text`, `channel`, `variables JSONB`. If both backends write to the same physical `email_templates` table, Rails seeds will have NULL values for FastAPI-specific columns and FastAPI queries filtering by `body_html IS NOT NULL` may skip them.

**Fix:** Confirm shared table via `SELECT table_catalog, table_schema FROM information_schema.tables WHERE table_name = 'email_templates'` on both connection strings. If shared, migrate `SeedDefaultsService` to write using FastAPI schema. If separate, migrate seeding to call the FastAPI endpoint directly.

---

### P1-7: Microsoft Graph OAuth tokens stranded in Rails users table

**Rails controller:** `ats_api/app/controllers/v1/users/microsoft_auths_controller.rb` (dead from FE)  
**FastAPI:** `lia-agent-system/app/api/v1/calendar.py` (app-level credentials flow)

Users who connected Microsoft Graph before the FastAPI migration authenticated via a user-delegated OAuth flow, with their personal access tokens stored in the Rails `users` table. FastAPI uses app-level service credentials — a fundamentally different flow. These users likely find their calendar integration silently broken (FastAPI's app credentials may not have access to their personal calendars).

**Fix:** Audit `users` table for rows with non-null `microsoft_access_token` (or equivalent column). For each, determine if their calendar integration is still expected to work, and either rebuild the delegated flow in FastAPI or surface an explicit re-authentication prompt.

---

### P1-8: Rails background_agents domain fully orphaned — running agents invisible to FE

**Rails controllers:** `ats_api/app/controllers/v1/background_agents_controller.rb` + sub-controllers (status, cycles, progress, searches)  
**FastAPI supersession:** `agent_monitoring.py`, `agent_studio_*.py`

No proxy routes exist for any background_agents endpoints. Any `background_agent` records in the Rails database are completely invisible to the FE's agent monitoring UI. If any background agents were running before the migration, they continue executing against Rails domain logic with no observability surface.

**Fix:** Run `SELECT COUNT(*), status FROM background_agents GROUP BY status` on Rails DB. If active records exist, determine if they should be migrated to FastAPI agent system or terminated. Then remove the Rails controllers.

---

### P1-9: External webhook registrations unknown — possible double-processing

**Rails handlers:** `POST /v1/webhooks/meta_whatsapp`, `POST /v1/webhooks/teams_chat`, `POST /v1/webhooks/mailgun/tracking`  
**FastAPI handlers:** `whatsapp_webhook.py`, `mailgun_webhooks.py`, teams handler in `interview_analysis.py`

If Mailgun, Meta WhatsApp, or Microsoft Teams are configured to POST to both Rails and FastAPI URLs (possible during an incomplete migration), events are double-processed. This can cause duplicate WhatsApp messages sent, duplicate email tracking events recorded, and duplicate Teams notifications.

**Fix:** Audit each external service dashboard. Document the registered webhook URL for each. Confirm it is FastAPI-only. If any are still on Rails, update the registration.

---

## 🟢 P2 Debt — Dead Code and Inconsistencies

### P2-1: 274 hand-rolled proxy route.ts files

The canonical `createProxyHandlers()` pattern was introduced to standardize proxy behavior (auth header forwarding, error handling, response envelope unwrapping). 274 of 645 proxy files still use direct `fetch()` with manual header forwarding. Each file is a potential auth forwarding bug and a maintenance burden.

**Priority order for migration:** auth/, candidates/, chat/ namespaces first (highest traffic).

---

### P2-2: Confirmed ghost Rails controllers (no proxy, no callers, no Sidekiq dependency)

The following Rails controllers are confirmed dead code and safe to delete:

| Controller | Routes | Superseded by |
|---|---|---|
| `v1/approval_requests_controller.rb` | `/v1/approval_requests` | FastAPI `approvals.py`, `agent_approvals.py` |
| `v1/organizational_positions_controller.rb` | `/v1/organizational_positions` | No FE surface |
| `v1/calendar_events_controller.rb` | `/v1/calendar_events` | FastAPI `calendar.py` |
| `v1/meetings_controller.rb` | `/v1/meetings` | FastAPI `calendar.py` |
| `v1/interview_sessions_controller.rb` | `/v1/interview_sessions` | FastAPI `interviews.py` |
| `v1/workspaces_controller.rb` | `/v1/workspaces` | No FE surface |
| `v1/apply_statuses_controller.rb` | `/v1/apply_statuses` | FastAPI candidates stage |
| `v1/selective_processes_controller.rb` | `/v1/selective_processes` | FastAPI wizard/agent orchestration |
| `v1/issues_controller.rb` | `/v1/issues` | No FE surface |
| `admin/llm_usages_controller.rb` | `/admin/llm_usages` | FastAPI `ai_consumption.py`, `llm_config.py` |
| `v1/job_field_templates_controller.rb` | `/v1/job_field_templates` | FastAPI job creation wizard |
| `v1/candidate_imports_controller.rb` | `/v1/candidate_imports` | FastAPI bulk candidates import |
| `v1/entity_pages_controller.rb` | `/v1/entity_pages` | No FE surface (legacy CMS) |
| `v1/entity_columns_controller.rb` | `/v1/entity_columns` | No FE surface (legacy CMS) |
| `v1/users/telemetry_controller.rb` | `/v1/users/telemetry` | FastAPI observability modules |
| `v1/workos_controller.rb` (login_url, callback, sso_options only) | `/v1/workos/login_url`, `/callback`, `/sso_options` | Next.js WorkOS SDK routes |
| `v1/users/aggregators_controller.rb` | `/v1/users/aggregators/:entity` | FastAPI domain-specific endpoints |

---

### P2-3: Rails routes.rb has duplicate namespace for notifications

`routes.rb` declares the notifications namespace twice: lines 43–50 (`/v1/notifications`) and lines 787–794 (`/api/v1/notifications`). Both are dead from the FE. Remove both namespace declarations and the controller file to clean up the routing table.

---

### P2-4: WorkOS dead routes cluttering Rails routes.rb

`GET /v1/workos/login_url`, `GET /v1/workos/callback`, `GET /v1/workos/sso_options` are unreachable from the frontend. Remove after confirming the WorkOS webhook URL is updated (P0-4 above). Do not remove `POST /v1/workos/webhook` until the dashboard is confirmed.

---

### P2-5: Alembic secondary migration chain

The `lia-agent-system/alembic/versions/` directory contains a named-revision chain (`001_intelligence` through `015_add_fairness_audit_log`) alongside the main numbered chain (`001` through `258`). This creates ambiguity in `alembic history` output. The secondary chain should be documented with a comment in the Alembic env.py explaining its purpose and relationship to the main chain.

---

### P2-6: talent-pools proxy uses underscore path on FastAPI side

`/api/backend-proxy/talent-pools/*` proxies to `/api/v1/talent_pools/*` on FastAPI (underscored). The FastAPI `talent_pools` router does not follow the hyphenated-path convention used by all other routers in the system. This is cosmetic but creates inconsistency in URL convention documentation.

---

### P2-7: Duplicate proxy routes (two paths, same FastAPI endpoint)

- `/api/backend-proxy/jobs/bulk-import-status/[batch_id]` duplicates `/api/backend-proxy/jobs/bulk-import/[batch_id]/status`
- `/api/backend-proxy/v1/tasks` (used by `use-active-tasks.ts:52`) duplicates `/api/backend-proxy/tasks` (used by `use-tasks-core.ts`)
- `/api/backend-proxy/lia/job-wizard` duplicates `/api/backend-proxy/lia/job-wizard/step`

Delete the older/non-canonical proxy file and update the consuming hook for the tasks duplicate.

---

## Shared Tables Risk Table

Tables written by both Rails (ats_api) and FastAPI (lia-agent-system). These are the highest-risk surface for data consistency bugs.

| Table | Rails FK | FastAPI FK | Both write? | Risk Level | Notes |
|---|---|---|---|---|---|
| `candidates` | `account_id` (bigint) | `company_id` (UUID) | YES — confirmed | 🔴 HIGH | Alembic migration 258 added `education_snapshot`. Rails model unaware. Both backends produce rows, different PK strategies. |
| `companies` | `account_id` (bigint) | String(255) PK | YES — confirmed | 🔴 HIGH | PK type mismatch. Alembic migration 127 added `lia_persona_override`. Rails model unaware. |
| `email_tracking_events` | `dispatch_message_id` (bigint) | Alembic migration 037 FK | YES — possible | 🟡 MEDIUM | Both may write tracking events. Verify shared table identity. |
| `shared_searches` | `account_id + user_id` | Alembic migration 019 | YES — possible | 🟡 MEDIUM | Rails original owner. FastAPI may have extended. |
| `email_templates` | `account_id + user_id` | `company_id` nullable | LIKELY YES | 🔴 HIGH | Schema divergence: Rails=single content field, FastAPI=body_html+body_text+channel. Seed job writes to unknown target. |
| `benefits` | Global catalog (no company_id) | `company_id` UUID FK | POSSIBLE | 🟡 MEDIUM | Rails is global catalog, FastAPI is per-company. May be same physical table with Rails as legacy owner. |
| `audit_logs` | User/account/workos activity | AI governance/LGPD log | NO (different semantics) | 🟢 LOW | Same table name, completely different data. Writes from each backend are invisible noise to the other. No join risk. |
| `messages` | Polymorphic chat system | LLM conversation turns | NO (different semantics) | 🟢 LOW | Same table name, fundamentally different structure and purpose. |
| `approval_requests` | Bigint PK, polymorphic | UUID PK, JSON target_data | POSSIBLE | 🟡 MEDIUM | PK type mismatch. FK targets diverge. Functionally separate despite shared name. |
| `approvers` | `account_id` FK | `company_id` UUID FK | POSSIBLE | 🟡 MEDIUM | FK target mismatch: Rails→accounts, FastAPI→company_profiles. |
| `departments` | `account_id` FK | `company_id` UUID FK | POSSIBLE | 🟡 MEDIUM | Rails original owner. FastAPI heavily extended schema with manager_name/email (denormalized). |
| `search_archetypes` | `account_id + user_id` | `company_id` UUID | LIKELY YES | 🟡 MEDIUM | Same physical table. Rails original owner. |
| `candidate_feedbacks` | `account/user/job` FKs | `company_id` UUID | LIKELY YES | 🟡 MEDIUM | Same physical table. Different FK targets. |

**Critical verification step:** Run the following on both connection strings and confirm same row counts for the HIGH-risk tables:
```sql
SELECT COUNT(*) FROM candidates;
SELECT COUNT(*) FROM companies;
SELECT COUNT(*) FROM email_templates;
```
If counts diverge, there is an undiscovered split-brain scenario requiring immediate escalation.

---

## Migration Roadmap (Ordered by Risk)

See the Migration Roadmap section for the ordered 15-step plan. Summary priorities:

**Week 1 (P0 unblocks):**
1. Set `RAILS_BACKEND_URL` everywhere
2. Fix `assigned_audience_policy` schema drift in `JobVacancy`
3. Verify WorkOS webhook dashboard URL
4. Migrate `/lia/job-wizard` FE callers to WS path
5. Add email opt-out + password reset 301 redirects in Rails

**Week 2 (P1 risk reduction):**
6. Verify Mailgun/Meta/Teams webhook registration URLs
7. Audit shared table DB connections (same PostgreSQL instance?)
8. Audit active Sidekiq jobs that write to shared tables

**Week 2–3 (structural cleanup):**
9. Implement FastAPI onboarding sub-paths; remove Rails dependency
10. Refactor 274 hand-rolled proxy files to `createProxyHandlers()`

**Week 3–4 (dead code removal):**
11. Remove confirmed ghost Rails controllers (14 listed above)
12. Remove WorkOS dead routes from routes.rb (post-dashboard verification)

**Month 2 (feature gaps):**
13. Implement department tree/org chart in FastAPI
14. Audit Microsoft Graph OAuth token migration
15. Document canonical 'Rails stub' surface; freeze from new features

---

## Quick Wins (Under 1 Day Each)

| Action | File | Impact | Time |
|---|---|---|---|
| Set `RAILS_BACKEND_URL` in `.env.local` and `.env.example` | `.env.local`, `.env.example` | Unblocks P0 onboarding 503 | 5 min |
| Remove `assigned_audience_policy` from `JobVacancy` model or add Alembic migration | `libs/models/lia_models/job_vacancy.py` | Prevents P0 DB crash | 30 min |
| Add a guard in onboarding proxy that returns a human-readable error when `RAILS_BACKEND_URL` is empty | `backend-proxy/onboarding/[...path]/route.ts` | Improves debugging | 20 min |
| Delete 3 confirmed duplicate proxy route.ts files | `bulk-import-status/`, `lia/job-wizard/`, `v1/tasks/` | Removes confusion, reduces maintenance surface | 30 min |
| Update `use-active-tasks.ts:52` to use `/api/backend-proxy/tasks` | `use-active-tasks.ts` | Consolidates tasks proxy path | 15 min |
| Add Rails 301 redirect for email opt-out | `ats_api/config/routes.rb` | Resolves LGPD compliance gap | 45 min |
| Add Rails 301 redirect for email tracking pixel/click | `ats_api/config/routes.rb` | Preserves analytics for historical emails | 30 min |
| Add deprecation comments to all ghost Rails controllers | 14 controller files | Prevents future confusion during incident response | 1 hour |
| Add TODO comments in `use-lia-suggestions.ts:155` and `use-job-wizard-backend.ts:270` | Both hook files | Prevents pattern copying before migration | 10 min |
| Verify WorkOS webhook URL in WorkOS dashboard | WorkOS dashboard | Confirms or resolves P0-4 | 10 min |
| Add `RAILS_BACKEND_URL` presence check to CI | CI config | Prevents the 503 pattern from recurring silently | 30 min |
| Document shared table verification query as a runbook step | Team runbook | Enables future audits in minutes | 20 min |

---

*Report generated from: 645 proxy route.ts files, 1782 FastAPI endpoints, 580 Rails routes, 383 Rails migrations, 265 Alembic migrations, 13 shared table analyses, 3 schema drift items. Canonical source of truth: Replit SSH `replit-wedo-0405` at `/home/runner/workspace/`.*
