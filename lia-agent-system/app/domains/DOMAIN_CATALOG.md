# LIA Platform — Domain Catalog

Classification of all directories under `app/domains/`.

## Classification Criteria

| Type | Criteria | Count |
|------|----------|-------|
| **Agentic** | Has `domain.py` with `@register_domain`, routable by orchestrator, full DomainPrompt implementation | 13 |
| **Micro-Action** | Has `domain.py` with `@register_domain`, lightweight (3-4 files), action-oriented stubs | 3 |
| **Service** | Has `services/` with business logic but no `domain.py` — data access + domain services | 11 |
| **Repository Stub** | Only `__init__.py`, `dependencies.py`, `repositories/` — pure CRUD data access | 30 |
| **Canonical Active (legacy path)** | Pre-domain refactor canonical paths still in production use; not deprecated | 2 |

Total: 59 directories (excluding `__pycache__`)

Note: The original audit (DIAGNOSTIC_REPORT_APRIL_2026.md) estimated "10 fully agentic"
based on a narrower definition (domains with both agents/ and services/). This catalog
uses the @register_domain decorator as the definitive criterion, yielding 13 agentic + 3
micro-action = 16 registered domains. The difference reflects agent_studio, job_creation,
and hiring_policy which register via @register_domain but have simpler internal structure.

Sprint 8 Frente C (2026-05-21): Service count corrected 9 → 11 — `modules` e
`interview_intelligence` adicionados (anteriormente missing do catalog). Sensor
`check_stub_invariants.py` agora reconhece SERVICE_DOMAINS canonical e foi promovido
WARN-ONLY → BLOCKING.

Sprint 11 T-09 B+A combo (2026-05-21): premissa V4 corrigida via auditoria 2x.
`autonomous` e `policy` foram **re-classificados de "Deprecated" para "Canonical
Active (legacy path)"** — ambos são código de produção ativo, sem substituto canonical
(hiring_policy é stub 40 LOC, recruiter_assistant não cobre Tier 6 ReAct fallback).
Sensor `check_no_imports_from_deprecated.py` atualizado: não mais reporta esses paths
como deprecated. Shim `app/services/policy_engine_service.py` (9 LOC) e
`app/shared/services/policy_engine_service.py` (2 LOC) **DELETADOS** — callers
migrados para canonical path `app.domains.policy.services.policy_engine_service`.

## Agentic Domains (13)

Registered in `DomainRegistry` via `@register_domain`. Routable by CascadedRouter.
Full implementations with agents/, services/, tools/, and comprehensive domain logic.

| Domain | domain_id | Files | Description |
|--------|-----------|-------|-------------|
| `analytics` | analytics | 68 | Recruitment analytics, reports, dashboards |
| `ats_integration` | ats_integration | 25 | ATS system integration and sync |
| `automation` | automation | 37 | Tasks, reminders, notes, workflow automation |
| `communication` | communication | 75 | Email, WhatsApp, Teams messaging |
| `cv_screening` | cv_screening | 80 | CV analysis, WSI evaluation, candidate scoring |
| `hiring_policy` | hiring_policy | 14 | Hiring policy advisory with FairnessGuard |
| `interview_scheduling` | interview_scheduling | 25 | Interview scheduling and calendar management |
| `job_creation` | job_creation | 13 | Wizard-driven job creation (conditional on deps) |
| `job_management` | job_management | 69 | Job lifecycle management (CRUD, pipeline config) |
| `pipeline` | pipeline_transition | 21 | Pipeline visualization and candidate movement |
| `recruiter_assistant` | recruiter_assistant | 38 | General recruiter assistant (fallback domain) |
| `sourcing` | sourcing | 49 | Candidate sourcing across channels |
| `agent_studio` | agent_studio | 4 | Custom agent creation and management |

## Micro-Action Domains (3)

Registered in `DomainRegistry` via `@register_domain`. Lightweight action stubs
with minimal implementation (3-4 files, no agents/ or services/ directories).

| Domain | domain_id | Files | Description |
|--------|-----------|-------|-------------|
| `digital_twin` | digital_twin | 3 | Digital twin creation and evaluation |
| `recruitment_campaign` | recruitment_campaign | 3 | Multi-stage recruitment campaigns |
| `talent_pool` | talent_pool | 3 | Talent pool management |

## Service Domains (11)

Provide data access and business logic services. Not routable by orchestrator.
Not registered in DomainRegistry. Tracked by sensor `check_stub_invariants.py`
via `SERVICE_DOMAINS` set.

| Domain | Files | Classification | Description |
|--------|-------|----------------|-------------|
| `ai` | 29 | service_domain | LLM services, response cache, prompt management |
| `billing` | 6 | service_domain | Billing and subscription management |
| `candidates` | 14 | service_domain | Candidate CRUD and profile services |
| `company` | 31 | service_domain | Company settings and configuration |
| `credits` | 7 | service_domain | Credit/token consumption tracking |
| `integrations_hub` | 10 | service_domain | Third-party integration management |
| `interview_intelligence` | 9 | **promotion_candidate** | Bias detection, comparative analysis (2026 LOC) — agentic potential |
| `lgpd` | 11 | service_domain | LGPD/GDPR data protection compliance |
| `modules` | 4 | service_domain | Module gating / feature flags |
| `recruitment` | 24 | service_domain | Recruitment process data and workflows |
| `voice` | 9 | **promotion_candidate** | Voice screening services (1725 LOC orchestrator) — agentic potential |

### Service Promotion Candidates (2)

Per ADR-V3.1 + Sprint 8 Frente C audit:
- `interview_intelligence` — 2026 LOC business logic (bias detector + comparative analysis +
  strategic opinion). Cross-call from `talent_intelligence/tools/interview_intelligence_tools.py`.
  Backlog F4+ promotion to agentic domain.
- `voice` — 1725 LOC `voice_screening_orchestrator` + 334 LOC `voice_service`. Voice screening
  could become routable agentic domain in future. Backlog F4+.

## Repository Stubs (30)

Pure data-access layers. Only contain `__init__.py`, `dependencies.py`, and `repositories/`.
These are NOT autonomous agent domains — they provide CRUD repositories consumed by
agentic domains and API routes.

| Domain | Description |
|--------|-------------|
| `admin` | Admin user management |
| `admin_settings` | Platform settings |
| `agent_memory` | Agent conversation memory storage |
| `approvals` | Approval workflow records |
| `auth` | Authentication tokens and sessions |
| `bulk_actions` | Bulk operation records |
| `candidate_lists` | Saved candidate list records |
| `chat` | Chat message storage |
| `clients` | Client/company records |
| `client_users` | Client user records |
| `company_culture` | Company culture profiles |
| `compliance` | Compliance audit records |
| `consent` | User consent records (LGPD) |
| `data_subject` | Data subject request records |
| `email_templates` | Email template storage |
| `goals` | Recruitment goal records |
| `health_check` | System health check records |
| `job_vacancies_analytics` | Job vacancy analytics records |
| `journey_mapping` | Candidate journey records |
| `lia_assistant` | LIA assistant suggestion click records |
| `notifications` | Notification records |
| `observability` | Observability/metrics records |
| `opinions` | User opinion/feedback records |
| `recruitment_journey` | Recruitment journey tracking |
| `saas_metrics` | SaaS metric records |
| `shared_searches` | Saved search records |
| `tasks` | Task records |
| `technical_tests` | Technical test records |
| `triagem` | Screening records (legacy) |
| `trust_center` | Trust center/security records |
| `workforce` | Workforce planning records |

## Canonical Active — Legacy Path (2)

Code paths still in production use. Pre-domain-refactor location, but **not deprecated**:
no canonical substitute exists. Re-classified Sprint 11 (2026-05-21) after auditoria 2x
proved V4 premise wrong.

| Domain | Status | Notes |
|--------|--------|-------|
| `autonomous` | **Canonical Active** | Tier 6 ReAct fallback canonical do CascadedRouter (4 files, 2.218 LOC). Wired em `app/orchestrator/cascaded_router.py:851` + `app/api/v1/agent_chat_ws.py:374` (registration trigger pro `@register_agent`). Sem equivalente em `recruiter_assistant` ou `agent_studio` — esses são tiers diferentes. Mantido como Tier 6 fallback estrutural. |
| `policy` | **Canonical Active** | Canonical policy engine (13 files, 2.343 LOC) + 1.167 LOC v1 endpoints (`app/api/v1/policy_engine.py`, `global_policies.py`, `policies.py`). Cobre `PolicyEngineService` (BusinessRule/RateLimitRule/EscalationRule), `PolicySetupAgent` (chat-driven setup), `ALPHA1_SECTOR_RULES` (sector-dependent FairnessGuard). `hiring_policy/` é stub aspiracional (40 LOC) — **NÃO substitui** `policy/`. |
