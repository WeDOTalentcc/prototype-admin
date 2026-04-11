# LIA Platform — Domain Catalog

Classification of all directories under `app/domains/`.

## Classification Criteria

| Type | Criteria | Count |
|------|----------|-------|
| **Agentic** | Has `domain.py` with `@register_domain`, routable by orchestrator, full DomainPrompt implementation | 13 |
| **Micro-Action** | Has `domain.py` with `@register_domain`, lightweight (3-4 files), action-oriented stubs | 3 |
| **Service** | Has `services/` with business logic but no `domain.py` — data access + domain services | 9 |
| **Repository Stub** | Only `__init__.py`, `dependencies.py`, `repositories/` — pure CRUD data access | 30 |
| **Deprecated** | Scheduled for removal or consolidation | 2 |

Total: 57 directories (excluding `__pycache__`)

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

## Service Domains (9)

Provide data access and business logic services. Not routable by orchestrator.
Not registered in DomainRegistry.

| Domain | Files | Description |
|--------|-------|-------------|
| `ai` | 29 | LLM services, response cache, prompt management |
| `billing` | 6 | Billing and subscription management |
| `candidates` | 14 | Candidate CRUD and profile services |
| `company` | 31 | Company settings and configuration |
| `credits` | 7 | Credit/token consumption tracking |
| `integrations_hub` | 10 | Third-party integration management |
| `lgpd` | 11 | LGPD/GDPR data protection compliance |
| `recruitment` | 24 | Recruitment process data and workflows |
| `voice` | 9 | Voice screening services |

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

## Deprecated (2)

| Domain | Status | Notes |
|--------|--------|-------|
| `autonomous` | Legacy | Contains legacy autonomous agents, not registered in DomainRegistry |
| `policy` | Deprecated | Superseded by `hiring_policy`. See `docs/TODO_POLICY_CONSOLIDATION.md` |
