# LIA Platform — Domain Catalog

Classification of all directories under `app/domains/`.

## Classification Criteria

| Type | Criteria | Count |
|------|----------|-------|
| **Agentic** | Has `domain.py` with `@register_domain`, routable by CascadedRouter, full DomainPrompt implementation | 13 |
| **Micro-Action** | Has `domain.py` with `@register_domain`, lightweight (3-4 files), action-oriented | 3 |
| **Service** | Has `services/` with business logic but no `domain.py` — data access + domain services | 9 |
| **Agent Studio em Desenvolvimento** | Lógica de serviço pronta; sem `domain.py` por decisão arquitetural — serão criados como agentes no Agent Studio, não como agentic domains canônicos | 3 |
| **Canonical Active (legacy path)** | `policy/` — motor canônico em uso; `autonomous/` — código órfão (Tier 6 removido Sprint 12.3-B) | 2 |

Total: 30 domains ativos + arquivos de suporte (`base.py`, `compliance_base.py`, `registry.py`, `workflow.py`)

> **2026-06-10 — limpeza de namespace:** 27 diretórios-fantasma de repository stubs
> foram deletados de `app/domains/`. Seus repositórios já estavam consolidados em
> `app/repositories/` — ver lá. Dirs deletados: `admin`, `admin_settings`, `agent_memory`,
> `approvals`, `auth`, `bulk_actions`, `candidate_lists`, `chat`, `clients`, `client_users`,
> `company_culture`, `data_subject`, `email_templates`, `goals`, `health_check`,
> `job_vacancies_analytics`, `journey_mapping`, `lia_assistant`, `notifications`,
> `observability`, `opinions`, `recruitment_journey`, `saas_metrics`, `shared_searches`,
> `tasks`, `technical_tests`, `trust_center`.
> Repositórios CRUD agora em `app/repositories/` (namespace único, ~40 arquivos).

---

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
| `hiring_policy` | hiring_policy | 14 | Entry point registrado no DomainRegistry — delega para o motor real em `policy/`. **NÃO é substituto de `policy/`** (ver nota abaixo). |
| `interview_scheduling` | interview_scheduling | 25 | Interview scheduling and calendar management |
| `job_creation` | job_creation | 13 | Wizard-driven job creation (conditional on deps) |
| `job_management` | job_management | 69 | Job lifecycle management (CRUD, pipeline config) |
| `pipeline` | pipeline_transition | 21 | Pipeline visualization and candidate movement |
| `recruiter_assistant` | recruiter_assistant | 38 | General recruiter assistant (fallback domain) |
| `sourcing` | sourcing | 49 | Candidate sourcing across channels |
| `agent_studio` | agent_studio | 4 | Custom agent creation and management |

> **Nota `hiring_policy` vs `policy/`:** `hiring_policy/` é um entry point fino (~40 LOC)
> registrado no DomainRegistry para roteamento conversacional de tópicos de política de
> contratação. O motor real — regras de negócio, FairnessGuard setorial, `PolicySetupAgent`,
> `PolicyEngineService` — vive integralmente em `app/domains/policy/` (2.343 LOC).
> Qualquer lógica nova de política de contratação vai em `policy/`, nunca em `hiring_policy/`.

---

## Micro-Action Domains (3)

Registered in `DomainRegistry` via `@register_domain`. Lightweight action stubs
with minimal implementation (3-4 files, no agents/ or services/ directories).

| Domain | domain_id | Files | Description |
|--------|-----------|-------|-------------|
| `digital_twin` | digital_twin | 3 | Digital twin creation and evaluation |
| `recruitment_campaign` | recruitment_campaign | 3 | Multi-stage recruitment campaigns |
| `talent_pool` | talent_pool | 3 | Talent pool management |

---

## Service Domains (9)

Provide data access and business logic services. Not routable by CascadedRouter.
Not registered in DomainRegistry.

| Domain | Files | Description |
|--------|-------|-------------|
| `ai` | 29 | LLM services, response cache, RAG pipeline, prompt management |
| `billing` | 6 | Billing and subscription management |
| `candidates` | 14 | Candidate CRUD and profile services |
| `company` | 31 | Company settings and configuration |
| `compliance` | — | Compliance audit records |
| `consent` | — | User consent records (LGPD) |
| `credits` | 7 | Credit/token consumption tracking |
| `lgpd` | 11 | LGPD/GDPR data protection and purge compliance |
| `modules` | 4 | Module gating / feature flags |
| `recruitment` | 24 | Recruitment process data and workflows |

---

## Agent Studio em Desenvolvimento (3)

Domínios com lógica de serviço substancial já implementada. **Não têm `domain.py` por
decisão arquitetural**: serão criados como agentes customizados no **Agent Studio**
(`agent_studio` domain), não promovidos ao namespace de agentic domains canônicos.

| Domain | Conteúdo atual | Plano |
|--------|---------------|-------|
| `interview_intelligence` | `services/`: bias_detector, comparative_analysis, feedback_generator, interview_wsi, strategic_opinion, transcription (7 arquivos, ~2.026 LOC). `repositories/`: interview_repository | Agent Studio — agente de inteligência de entrevistas |
| `voice` | `services/`: gemini_live_audio, voice_core_orchestrator, voice_screening, voice_service, realtime_credit_session (10 arquivos, ~2.059 LOC). `plugins/`: data_collection, studio_voice, wsi_voice. `protocols/`: voice_core_plugin | Agent Studio — agente de triagem por voz |
| `talent_intelligence` | `services/`: skills_ontology_engine. `tools/`: candidate_nurture, internal_mobility, interview_intelligence_tools, market_intelligence, skills_ontology, workforce_planning + registry (8 arquivos) | Agent Studio — agente de inteligência de talentos |

> **Por que Agent Studio e não agentic domain?** Esses módulos têm escopo especializado e
> interface rica o suficiente para serem agentes autônomos configuráveis por tenant — o
> modelo de Agent Studio. Isso evita adicionar um 17º+ ReActAgent canônico ao inventário
> sentinela (`test_tenant_aware_rollout_t_d.py`) sem necessidade.

---

## Canonical Active — Legacy Path (2)

| Domain | Status | Notes |
|--------|--------|-------|
| `policy` | **Canonical Active** | Motor canônico de políticas de contratação (13 files, 2.343 LOC) + 1.167 LOC em endpoints v1 (`app/api/v1/policy_engine.py`, `global_policies.py`, `policies.py`). Cobre `PolicyEngineService` (BusinessRule/RateLimitRule/EscalationRule), `PolicySetupAgent` (chat-driven setup), `ALPHA1_SECTOR_RULES` (FairnessGuard setorial). `hiring_policy/` é entry point de roteamento — **NÃO substitui** `policy/`. |
| `autonomous` | **Código órfão** (sem roteamento ativo) | Tier 6 do CascadedRouter foi **REMOVIDO em Sprint 12.3-B** (2026-05-24). O env `AUTONOMOUS_REACT_ENABLED` nunca foi SET em prod (invocações = 0 nos canary metrics). O helper `_route_via_autonomous_agent` e `autonomous_react_agent.py` foram removidos em Sprint 12.6 (T13). O diretório `app/domains/autonomous/agents/` ainda existe mas **não é roteado por nenhum caller ativo**. Candidato a remoção completa na próxima limpeza de namespace. |
