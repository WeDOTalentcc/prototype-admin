# Rails Elimination Plan — WeDOTalent

## Goal
Shut down the Rails process (ats_api, port 3001) and Sidekiq completely. 100% FastAPI.

## Current state summary
- FastAPI: 1782 endpoints, Python/Celery, port 8001, row-level tenancy (company_id)
- Rails: ~580 routes, port 3001, Apartment gem (per-tenant Postgres schemas), Sidekiq (82 jobs)
- Next.js: 645 proxy routes — only 2 still call Rails (onboarding and magic-link)
- Shared DB: same heliumdb Postgres instance — LIVE RACE CONDITIONS on 12 tables
- Auth: every FastAPI request currently makes a synchronous HTTP call to Rails GET /v1/me
- RailsAdapter: 1250-line bridge class in FastAPI codebase (38 RAILS_API_URL references)

## Feature flag index
Every phase cutover is controlled by an env var (default off = safe):
- `FASTAPI_AUTH_PRIMARY` — Phase 1: FastAPI handles password login, skips Rails JWT fallback
- `FASTAPI_OAUTH_PRIMARY` — Phase 2: FastAPI issues M2M / OAuth service tokens
- `WORKOS_FASTAPI_JWT` — Phase 2: WorkOS SSO callback issues FastAPI JWT
- `FASTAPI_SETUP_WIZARD` — Phase 5: setup wizard served by FastAPI
- `FASTAPI_WSI_TIMEOUT_CHECKER` — Phase 4: FastAPI Celery handles WSI abandoned sessions
- `FASTAPI_DISPATCH_PRIMARY` — Phase 6: FastAPI Celery handles bulk email dispatch
- `FASTAPI_TEAMS_CRON` — Phase 6: FastAPI Celery handles Teams subscription renewal
- `FASTAPI_LINKEDIN_SEARCH` — Phase 7: FastAPI Celery handles LinkedIn sourcing
- `FASTAPI_CHATBOT_REPLY` — Phase 8: FastAPI handles inbound chatbot/WhatsApp replies

## Phase summaries

### Phase 1 (Weeks 1-2): Auth decoupling
**Start criterion:** Rails JWT fallback is the live auth path for all password-login users.
**End criterion:** FASTAPI_AUTH_PRIMARY=true in production, zero calls to Rails /v1/me per request.
**Key work:** Add rails_user_id column to FastAPI users, implement FastAPI password+MFA login, add rails-sync-user upsert endpoint, update NextJS session cookie handling.
**Rollback:** Set FASTAPI_AUTH_PRIMARY=false — instant, no deploy needed.
**Rails deleted:** Nothing yet (Rails still issues JWTs as fallback during this phase).

### Phase 2 (Weeks 3-4): OAuth + WorkOS SSO + magic-link
**Start criterion:** Phase 1 complete and stable for 48h.
**End criterion:** Zero Rails JWT issuance in production. FastAPI is the sole JWT issuer.
**Key work:** FastAPI OAuth2 client_credentials, OTT exchange/refresh, WorkOS callback issues FastAPI JWT, magic-link moved to FastAPI, remove validate_rails_token_from_env fallback.
**Rollback:** Set FASTAPI_OAUTH_PRIMARY=false, WORKOS_FASTAPI_JWT=false.
**Rails deleted:** sessions_controller.rb, agent_tokens_controller.rb, workos_controller.rb (auth parts), magic_link_controller.rb, json_web_token.rb.

### Phase 3 (Weeks 3-4, parallel with Phase 2): Shared table consolidation
**Start criterion:** Phase 1 complete (FK reconciliation does not depend on auth migration).
**End criterion:** All 12 shared tables have a single canonical writer. No FK mismatch on candidates/departments/benefits.
**Key work:** Rename FastAPI messages→conversation_messages, add company_id to Rails candidates+departments, consolidate email_templates+email_tracking+search_archetypes+candidate_feedbacks+audit_logs.
**Rollback:** Per-table feature flags. FK additions are backward-compatible (nullable columns).
**Rails deleted:** tracking_controller.rb, mailgun_controller.rb, email_templates_controller.rb write paths.

### Phase 4 (Weeks 5-6): Sidekiq wave 1 — WSI/eval/embeddings/LLM quota
**Start criterion:** Phase 3 complete.
**End criterion:** 16 Sidekiq jobs deleted. FastAPI Celery beat covers all periodic tasks they handled.
**Key work:** Delete 2 dead jobs immediately. Port WSI timeout/starter/completion, job analytics, LLM quota, cleanup, embedding sync to Celery.
**Rollback:** Feature flags per job. Re-enable Sidekiq job class if needed.

### Phase 5 (Weeks 7-8): Setup wizard + tenant provisioning
**Start criterion:** Phases 2 and 3 complete (needs auth + table consolidation).
**End criterion:** New tenants provisioned entirely by FastAPI. Existing tenant data migrated from Apartment schemas to public schema with company_id.
**Key work:** FastAPI token-gated setup wizard (14 endpoints), Celery provision_tenant_task (seeds 10+ tables), Apartment schema data migration script (batched, kill-switch), Next.js setup pages updated.
**Rollback:** Set FASTAPI_SETUP_WIZARD=false — new signups fall back to Rails wizard. Existing data migration has a dry-run mode.
**Rails deleted:** Entire app/controllers/v1/setups/ namespace, create_tenant_job.rb, apartment_service.rb.
**WARNING:** Apartment schema migration is irreversible once tenant schemas are dropped. Require explicit sign-off before final drop step.

### Phase 6 (Weeks 9-10): Sidekiq wave 2 — comms + Teams
**Start criterion:** Phase 4 complete.
**End criterion:** All email dispatch, MS Teams, and notification jobs on FastAPI Celery.
**Key work:** Port bulk email dispatch, Teams subscription renewal/token refresh/message ingestion, MS Graph email, in-app notifications, ActionCable message publish.
**Rollback:** Feature flags per job group.
**Rails deleted:** 15 job files covering dispatch, Teams, notifications.

### Phase 7 (Weeks 11-13): Sidekiq wave 3 — sourcing + candidates + bulk ops
**Start criterion:** Phases 3 and 4 complete (candidates table has company_id populated).
**End criterion:** All sourcing, candidate import, bulk operation jobs on FastAPI Celery.
**Key work:** Port LinkedIn search/enrichment/batch, local candidate search, resume parser (new LLM pipeline), bulk apply/stage operations, sourced profile conversion.
**Rollback:** Feature flags per sourcing domain.
**Rails deleted:** 25 job files covering sourcing, import, bulk operations.
**NOTE:** Resume parser requires building a new LLM pipeline — the largest new build in this phase (1-week sub-task).

### Phase 8 (Weeks 14-16): Remaining Rails-only jobs
**Start criterion:** Phases 6 and 7 complete.
**End criterion:** Zero active Sidekiq jobs. All 82 jobs either deleted or have running FastAPI equivalents.
**Key work:** ATS sync external integrations (decision gate: audit active tenants first), scheduling notifications, chatbot reply processor, evaluation pipeline, background agents, list management, department import, job copy.
**Rollback:** Feature flags per domain. ATS sync has external provider dependencies — test in staging against real ATS before prod cutover.
**Rails deleted:** 35+ job and worker files.

### Phase 9 (Weeks 17-18): RailsAdapter removal
**Start criterion:** Phases 5 and 8 complete. RAILS_API_URL is empty.
**End criterion:** Zero Rails references in FastAPI non-test code. No-rails-imports sensor passes.
**Key work:** Remove RAILS_API_URL branches from crud.py (job vacancies + candidates), delete rails_adapter.py (1250 lines), rails_health.py, rails_sync.py, rails_event_publisher.py, rails_crud_consumer.py, rails_jwt.py. Remove proxy-handler.ts Rails branch. Clean up onboarding route Rails branches.
**Sensor:** tests/contract/test_no_rails_imports.py blocks any regression.

### Phase 10 (Week 19-20): Rails process shutdown
**Start criterion:** Phase 9 complete. All 10-item pre-shutdown checklist passed.
**End criterion:** Rails Puma and Sidekiq processes stopped. Port 3001 returns connection refused.
**Key work:** Stop Sidekiq, stop Puma, remove env vars, archive ats_api/ directory, update run configs, add CI gate asserting port 3001 is dead.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Auth regression during Phase 1 rollout | Medium | Critical | FASTAPI_AUTH_PRIMARY env var is instant rollback; dual-path runs in parallel for 48h before flag flip |
| Apartment→row-level data migration corrupts tenancy | Low | Critical | Batched migration with dry-run mode, row count verification per tenant before and after, kill switch, require explicit sign-off before DROP SCHEMA |
| ATS sync external provider breaks during Phase 8 | Medium | High | Decision gate: audit active tenants first. If zero active: delete. If active: stage test with real ATS before prod. Feature flag per job |
| Sidekiq job race conditions during dual-write period | Medium | Medium | Feature flags ensure only one system enqueues each job type. Monitor queue depths for unexpected buildup |
| Resume parser (Phase 7) LLM pipeline quality regression | Medium | Medium | A/B test against legacy Rails resume parser for 1 week before deleting Rails job. Keep feature flag |
| Missing data: FastAPI User table not populated for all Rails users | High | High | Phase 1 adds rails-sync-user upsert called on every Rails JWT validation during transition. Backfill job for existing users before FASTAPI_AUTH_PRIMARY=true |
