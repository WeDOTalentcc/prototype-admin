# PLATFORM_MAP.md — Auditoria Técnica WeDOTalent

**Data:** 2026-04-13
**Escopo:** Multi-agente de recrutamento (Replit `/home/runner/workspace`)
**Subsistemas inspecionados:** `lia-agent-system/`, `plataforma-lia/`, `.agents/`, `ats-api-copia/`
**Legenda:** `[✓]` implementado e funcional · `[⚠]` parcial/problemas · `[✗]` ausente/placeholder · `[?]` indeterminado

---

## Sumário Executivo

| Domínio | Status geral | Observação |
|---|---|---|
| Agentes (ReAct + Graph) | [✓] | 17 ReAct registrados + 3 LangGraph StateGraphs + sub-agentes. **3 registries coexistindo** — risco de divergência. |
| Orquestração | [✓] | LangGraph nativo + custom `MainOrchestrator` + `CascadedRouter` 8-tier. Sem CrewAI. |
| Tools/Integrações | [✓] | 120+ tools em 28 registries, 15+ APIs externas, 5 webhooks inbound com HMAC. |
| Dados/Persistência | [✓] | Postgres 16 + pgvector (HNSW), 76 migrations, Celery + Redis, cache 3-camadas. |
| Fairness/LGPD/Bias | [✓] | FairnessGuard pré-LLM, DPO, DSR 15d, Four-Fifths Rule, PII masking global. |
| Segurança | [✓] | JWT + WorkOS SSO, TenantGuard com JWT-auth, prompt-injection guard 20+ patterns. |
| API/Frontend | [✓] | 236 routers FastAPI, WS primário + SSE fallback, Zustand (17 stores). |

**Pontos de atenção (resumo):**
- 3 registries de agentes sobrepostos (`AgentRegistry`, `ReactAgentRegistry`, `DomainRegistry`) — mapear canônico.
- `PolicySetupAgent` legado ainda importável (deprecation shim).
- `StateManager` emite warning em produção se Redis não configurado (`LIA-M05`).
- Deepgram aparece no fluxo OpenMic mas **não há serviço dedicado** (`[?]`).
- `LIA_DISABLE_C3B=1` permite bypass da camada de compliance — feature flag perigosa em produção.

---

# 1. AGENTES

## 1.0 Arquitetura de referência

- **Padrão:** Multi-agent v2.2 com LangGraph ReAct
- **Base class:** `LangGraphReActBase` (lia_agents_core) → `create_react_agent()` de LangGraph prebuilt
- **LLM default:** Anthropic `claude-sonnet-4-6`, temperatura 0.3
- **Provider:** Anthropic (primário); OpenAI e Gemini via override por tenant
- **Checkpointer:** `PostgresSaver` em prod, `MemorySaver` em dev
- **Camadas de compliance no loop:** PII auto-sanitize (LIA-C04), FairnessGuard (LIA-C05), AuditCallback, ComplianceDomainPrompt (LIA-C01)
- **Memória:** 3 camadas — `WorkingMemory` (PG, por sessão), `LongTermMemory` (PG, por empresa/domínio), histórico (últimas 10 msgs injetadas)

### Registries de agente [⚠] (três coexistindo)
1. `AgentRegistry` — `lia-agent-system/app/shared/agents/agent_registry.py` — decorator `@register_agent`, singleton, **canônico para dispatch**
2. `ReactAgentRegistry` — `libs/agents-core/lia_agents_core/react_agent_registry.py` — singleton legado, registra 17 agentes
3. `DomainRegistry` — `lia-agent-system/app/domains/registry.py` — `@register_domain`, para DomainPrompt (workflow layer)

### Fluxo de decisão global
`CascadedRouter` (Tiers 0–5) → agente especializado. Tier 6 → `AutonomousReActAgent` (fallback cross-domain).

---

## 1.1 Wizard (Job Planner) — [✓]
| Campo | Valor |
|---|---|
| Arquivo | `lia-agent-system/app/domains/job_management/agents/wizard_react_agent.py` |
| Propósito | Criação de vaga em 6 estágios |
| LLM | `claude-sonnet-4-6` (override: `AGENT_MODEL_JOB_WIZARD`) · T=0.3 |
| System prompt | `wizard_system_prompt.py:WIZARD_DOMAIN_SPECIFIC` |
| Tools | `wizard_tool_registry.py` — market salary, JD enrichment, skills |
| Decisão | ReAct (LangGraph), max 5 iters |
| Memória | `WorkingMemoryService` + `EnhancedAgentMixin` |

## 1.2 Pipeline (CV Screening) — [✓]
`lia-agent-system/app/domains/cv_screening/agents/pipeline_react_agent.py` — `claude-sonnet-4-6` · T=0.3 · prompt `pipeline_system_prompt.py:PIPELINE_DOMAIN_SPECIFIC` · 17+ tools (move, analyze_cv, run_wsi_screening, schedule_interview, generate_offer, check_pipeline_risks…) · ReAct, max 5 iters.

## 1.3 Sourcing — [✓]
`lia-agent-system/app/domains/sourcing/agents/sourcing_react_agent.py` — `claude-sonnet-4-6` · T=0.3 · 5 estágios (criteria → search → analyze → shortlist → outreach).

### 1.3.1 Sub-agentes Sourcing (10)
| Sub-agente | LLM | Tools |
|---|---|---|
| `SourcingPlannerAgent` | haiku-4-5 | set_search_criteria, suggest_skills |
| `SourcingSearchAgent` | haiku-4-5 | search_candidates, filter_results, view_candidate |
| `SourcingEnrichAgent` | sonnet-4-6 | 7: analyze, compare, score, shortlist, rank, report |
| `SourcingEngagementAgent` | sonnet-4-6 | send_outreach (HITL), generate_message, track_response |
| `GithubSourcingAgent` | sonnet-4-6 | github_search_developers, github_get_profile, github_get_repos |
| `StackOverflowSourcingAgent` | sonnet-4-6 | so_search_experts, so_get_user_tags, so_get_user_answers |
| `DiversitySourcingAgent` | sonnet-4-6 | diversity_search_candidates, diversity_get_pool_metrics, diversity_check_goals |
| `PassivePipelineAgent` | sonnet-4-6 | passive_search_archived, passive_calculate_fit_score, passive_check_lgpd_ttl |
| `ReferralAgent` | sonnet-4-6 | referral_identify_connectors, referral_prepare_request, referral_send_request (HITL) |
| `NurtureSequenceAgent` | sonnet-4-6 | 5: create/get/approve/execute/expire |

## 1.4 Talent (Recruiter Assistant) — [✓]
`domains/recruiter_assistant/agents/talent_react_agent.py` · sonnet-4-6 · search_candidates, view_profile, check_search_fairness, compare, rank.

## 1.5 Jobs Management — [✓]
`domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` · sonnet-4-6 · portfolio macro, SLA, FairnessGuard em close/pause.

## 1.6 Kanban — [✓]
`domains/recruiter_assistant/agents/kanban_react_agent.py` · **haiku-4-5** · 22 tools decompostas em 3 sub-agentes:
- `KanbanSearchAgent` — 6 tools read (view_candidate, list_stage, pipeline_summary, stage_metrics, benchmarks, velocity)
- `KanbanInsightAgent` — 8 tools analytics (analyze_stage, bottlenecks, aging, compare, suggest_movements, journey_metrics, at_risk, prediction)
- `KanbanActionAgent` — 8 tools mutação (batch_move HITL, batch_communication HITL, batch_screening HITL, generate_report, check_rejection_fairness, silver_medalists, recruiter_backlog, recruiter_benchmark)

## 1.7 Policy (Hiring Policy) — [✓]
`domains/hiring_policy/agents/policy_react_agent.py` · haiku-4-5 · 5 blocos (pipeline, scheduling, communication, screening, autonomy).

> **Legacy:** `domains/policy/agents/agent.py:PolicySetupAgent` — questionário linear 19 perguntas, usa `LLMService` direto (não LangGraph). Shim em `app/agents/policy_setup_agent.py` com `DeprecationWarning`. **[⚠] ainda importável.**

## 1.8 Automation — [✓]
`domains/automation/agents/automation_react_agent.py` · haiku-4-5 · DAG decomposition, execution plan. Max 6 iters.

## 1.9 Analytics — [✓]
`domains/analytics/agents/analytics_react_agent.py` · sonnet-4-6 · KPIs, salary benchmark, predictions, agent performance. Max 6 iters.

## 1.10 Communication — [✓]
`domains/communication/agents/communication_react_agent.py` · haiku-4-5 · email/WhatsApp, templates LGPD-compliant.

## 1.11 ATS Integration — [✓]
`domains/ats_integration/agents/ats_integration_react_agent.py` · haiku-4-5 · sync Gupy/Pandape/Merge.

## 1.12 Pipeline Transition (+ sub-agentes) — [✓]
`domains/pipeline/agents/pipeline_transition_agent.py` · sonnet-4-6 · 17–20 tools.
- `PipelineContextAgent` (haiku-4-5) — 7 tools read
- `PipelineDecisionAgent` (sonnet-4-6) — 7 tools validate/preferences
- `PipelineActionAgent` (sonnet-4-6) — 6 tools mutação (3 com guardrails)

## 1.13 Autonomous (Cross-Domain) — [✓]
`domains/autonomous/agents/autonomous_react_agent.py` · sonnet-4-6 · 40+ tools curadas · max steps `AUTONOMOUS_REACT_MAX_STEPS` (default 10) · circuit breaker próprio (threshold=3, recovery=30s, timeout=60s).
**Não** está em `AgentRegistry` — só invocado pelo `CascadedRouter` Tier 6.

## 1.14 InterviewGraph — [✓]
`domains/interview_scheduling/agents/interview_graph.py` — LangGraph StateGraph (não ReAct, ADR-002). Nós: loader → collector → router → validator → scheduler_executor → response_planner. Max 8 iters.

## 1.15 WSIInterviewGraph — [✓]
`domains/cv_screening/agents/wsi_interview_graph.py` — LangGraph StateGraph. Estágios: init → load_context → generate_question → await_response → validate → score → advance → generate_feedback → complete. `interrupt_before=["lg_generate_feedback"]` (HITL). Compliance: BCB 498, SOX — cada nó auditável.

## 1.16 JobWizardGraph — [✓]
`domains/job_management/agents/job_wizard_graph.py` — LangGraph StateGraph paralelo ao WizardReActAgent. Cycle protection `MAX_ITERATIONS=10`. `interrupt_before=["stage_transition"]` (HITL para aprovação de criação).

## 1.17 Gemini Live Voice — [✓]
`app/api/v1/gemini_voice.py` — WebSocket browser↔Gemini (STT+LLM+TTS). Auth HMAC-SHA256 ws_token, sessão pré-criada. CB: `GEMINI_LIVE_CIRCUIT`.

## 1.18 OpenMic Voice Screening — [✓]
`app/services/voice/openmic_service.py` — chamada outbound → webhook callback → Celery WSI scoring. Auth: `OPENMIC_API_KEY`, webhook HMAC-SHA256. CB: `OPENMIC_CIRCUIT`.

## 1.19 Mapa de dependências

```
CascadedRouter (Tiers 0–5) ──► agente especialista (wizard, pipeline, sourcing, talent, kanban, …)
                   Tier 6 ──► AutonomousReActAgent (fallback cross-domain, 40+ tools)

Sourcing:
 SourcingReActAgent ──► Planner ──► Search ──► Enrich ──► Engagement (HITL)
                   ├──► Github / StackOverflow / Diversity / Passive / Referral (HITL) / Nurture

Kanban:
 KanbanReActAgent ──► Search (read) / Insight (analytics) / Action (mutations HITL)

Pipeline:
 PipelineTransitionAgent ──► Context (read) / Decision (validate) / Action (mutate HITL)
```

---

# 2. TOOLS & INTEGRAÇÕES

## 2.1 Registry

- **Central:** `lia-agent-system/app/tools/registry.py` — `ToolRegistry` + `ToolDefinition(name, description, parameters_schema, handler, allowed_agents)`
- **Por domínio:** cada domínio tem `*_tool_registry.py` usando `ToolDefinition` de `lia_agents_core.react_loop`
- **Handler wrapper:** `@tool_handler("domain")` em `app/shared/tool_handler.py` (async + error wrapping)
- **Metadados declarativos:** `app/tools/tool_registry_metadata.yaml` (Sprint G5) — validado contra runtime
- **Conversão LangChain:** `tool_definition_to_langchain_tool()` para `create_react_agent()`

## 2.2 Tools por domínio — totais

| Domínio | Arquivo | Contagem |
|---|---|---|
| Analytics | `analytics_tool_registry.py` | 6 |
| ATS Integration | `ats_integration_tool_registry.py` | 2 |
| Automation | `automation_tool_registry.py` | wrappers PlannedTaskService+LLMService |
| Communication | `communication_tool_registry.py` | send_email/whatsapp + hist |
| Pipeline (CV) | `pipeline_tool_registry.py` | 17–20 |
| Policy | `policy_tool_registry.py` | get_current + update blocks |
| Wizard | `wizard_tool_registry.py` | market_range, JD enrich, skills |
| Kanban | `kanban_tool_registry.py` | 22 |
| Talent | `talent_tool_registry.py` | 5 |
| Sourcing | `sourcing_tool_registry.py` | 12 |
| Github | `github_tool_registry.py` | 3 |
| StackOverflow | `stackoverflow_tool_registry.py` | 3 |
| Diversity | `diversity_tool_registry.py` | 3 |
| Passive | `passive_pipeline_tool_registry.py` | 3 |
| Referral | `referral_tool_registry.py` | 3 |
| Nurture | `nurture_sequence_tool_registry.py` | 5 |
| Pipeline Context/Decision/Action | 3 arquivos | 7+7+6 |
| Autonomous | `autonomous_tool_registry.py` | 40+ |
| **Total estimado** | **28 registries** | **120+ tools** |

### Kanban — destaques (22 tools)
`check_rejection_fairness` (MANDATÓRIO), `view_candidate_full_profile`, `list_stage_candidates`, `get_pipeline_summary`, `get_stage_metrics`, `get_pipeline_benchmarks`, `get_pipeline_velocity`, `analyze_stage`, `identify_bottlenecks`, `get_candidate_aging`, `compare_stages`, `suggest_movements`, `get_journey_metrics`, `get_at_risk_candidates`, `get_pipeline_prediction`, `batch_move_candidates` (HITL), `send_batch_communication` (HITL), `start_screening_batch` (HITL), `generate_pipeline_report`, `find_silver_medalists`, `get_recruiter_backlog`, `get_recruiter_benchmark`.

## 2.3 APIs externas consumidas

| API | Auth | Endpoint | Circuit Breaker | Status |
|---|---|---|---|---|
| Anthropic Claude | `ANTHROPIC_API_KEY` / `AI_INTEGRATIONS_ANTHROPIC_API_KEY` | `api.anthropic.com/v1` | — | [✓] primário |
| OpenAI | `AI_INTEGRATIONS_OPENAI_API_KEY` | default | — | [✓] override |
| Google Gemini | `AI_INTEGRATIONS_GEMINI_API_KEY` | GenAI | — | [✓] override |
| Gemini Live Audio | API key | WebSocket | `GEMINI_LIVE_CIRCUIT` | [✓] |
| Mailgun | `MAILGUN_API_KEY` | `api.mailgun.net/v3/{domain}/messages` | `MAILGUN_CIRCUIT` | [✓] primário email |
| Resend | `RESEND_API_KEY` | Resend API | — | [✓] fallback |
| Twilio WhatsApp | `TWILIO_ACCOUNT_SID`+`TWILIO_AUTH_TOKEN` | `api.twilio.com/.../Messages.json` | — | [✓] |
| OpenMic.ai | `OPENMIC_API_KEY` | `api.openmic.ai/v1` | `OPENMIC_CIRCUIT` | [✓] |
| Google Calendar | Service Account JSON ou OAuth2 | Calendar API v3 | `GOOGLE_CALENDAR_CIRCUIT` | [✓] |
| Microsoft Graph | `AZURE_CLIENT_ID/SECRET/TENANT_ID` (client creds) | `graph.microsoft.com/v1.0` | — | [✓] Teams + Outlook |
| HubSpot | `HUBSPOT_ACCESS_TOKEN` | SDK `hubspot` | — | [✓] CRM |
| Gupy ATS | per-client | REST | — | [✓] |
| Pandape ATS | per-client | REST | — | [✓] |
| Merge.dev | `MERGE_WEBHOOK_SECRET` | Merge unified | — | [✓] |
| GitHub API | via agent | `api.github.com` | — | [✓] |
| Stack Exchange | via agent | `api.stackexchange.com` | — | [✓] |
| Deepgram | — | STT | — | [?] referenciado no fluxo OpenMic, sem serviço dedicado confirmado |
| LangSmith | `LANGSMITH_API_KEY` | tracing | — | [✓] observability (`app/config/langsmith.py`) |

> Rate limits: Não foi encontrada configuração declarativa de rate limit por API no código-base inspecionado. Proteção é via circuit breaker + timeouts, não throttling RPS. **[⚠] rate limit externo não declarado.**

## 2.4 Integrações — detalhe

### Email [✓]
- **Primário:** `app/services/email_providers/mailgun_provider.py`
- **Fallback:** `app/services/email_providers/resend_provider.py`
- **Factory:** `get_email_provider()` + `get_provider_for_client(client_id, config)` (per-client)
- **Default sender:** `noreply@wedotalent.com` (`MAILGUN_FROM_EMAIL`)
- **Templates:** WSI invite, rejection (Gate 1/2), interview invite, bulk — em `communication_system_prompt.py`
- **Tracking webhook:** delivered/bounce/open/click/complaint

### WhatsApp [✓]
- **Client:** `app/services/whatsapp_client.py` (Twilio WABA)
- **Capabilities:** template messages (Meta-approved), free-form (24h), Flows, buttons, CTAs
- **From:** `LIA_WHATSAPP_NUMBER`
- **Webhook:** `app/api/v1/whatsapp_webhook.py` — HMAC-SHA1
- **Prod policy:** fail-closed sem auth token (fail-open só em dev)

### Microsoft Teams + Outlook [✓]
- `app/domains/communication/services/teams_calendar_service.py` (TeamsCalendarService)
- Base: `app/domains/integrations_hub/services/microsoft_graph_service.py`
- OAuth2 client credentials · escopos: Calendars.ReadWrite, OnlineMeetings.ReadWrite, User.Read
- Cria meetings online + Outlook events + Microsoft Bookings

### Google Calendar [✓]
- `app/domains/integrations_hub/services/google_calendar_client.py`
- Service Account JSON OU OAuth2 user tokens (tabela `company_calendar_credentials`)
- Auto-refresh em token OAuth expirado
- CB: `GOOGLE_CALENDAR_CIRCUIT`

### ATS [✓]
| ATS | Cliente | Status |
|---|---|---|
| Gupy | `domains/ats_integration/services/ats_clients/gupy.py` | [✓] phase mapping, observações, básicos |
| Pandape | `.../pandape.py` | [✓] WSI score, salary expectation, HR assessment |
| Merge.dev | `.../merge.py` | [✓] universal multi-ATS, custom fields |

Serviço central: `ATSSyncService` — push/pull bidirecional, field mapping por ATS, **WeDOTalent é source of truth**, não cria campos no ATS cliente, unsupported fields persistem locais.

### HubSpot CRM [✓]
- `app/domains/company/services/hubspot_service.py` · SDK `hubspot` · `HUBSPOT_ACCESS_TOKEN`
- Mapeia `ClientAccount` → HubSpot Company + Contact + Deal

### Voice [✓]
| Provider | Serviço | Propósito |
|---|---|---|
| OpenMic.ai | `app/services/voice/openmic_service.py` | Outbound voice WSI |
| Gemini Live Audio | `app/api/v1/gemini_voice.py` | Real-time browser↔Gemini |
| Twilio Voice | `app/api/v1/twilio_voice.py` | VoIP legado/alt |

## 2.5 Webhooks

### Inbound (externo → WeDO)

| Endpoint | Source | Assinatura | Propósito |
|---|---|---|---|
| `POST /api/v1/external-webhooks/ats/{platform}` | Gupy/Pandape/Merge | HMAC-SHA256 por plataforma | ATS events (created/updated/stage/hired) |
| `POST /api/v1/webhooks/mailgun` | Mailgun | HMAC-SHA256 (`MAILGUN_WEBHOOK_SIGNING_KEY`) | delivered/failed/bounced/opened/complained/unsubscribed |
| `POST /api/v1/webhooks/merge/` | Merge.dev | HMAC-SHA256 (`MERGE_WEBHOOK_SECRET`) | Candidate/Application events |
| `POST /api/v1/whatsapp` | Twilio | HMAC-SHA1 (`TWILIO_AUTH_TOKEN`) | Inbound msgs, onboarding routing |
| `POST /api/v1/openmic/webhook` | OpenMic.ai | HMAC-SHA256 (`OPENMIC_WEBHOOK_SECRET`) | Call completion → enqueue Celery WSI |

Políticas comuns: fail-closed em prod, background processing (200 imediato), PII masking nos logs, SSRF allowlist no OpenMic (`openmic.ai`, `deepgram.com`, `*.s3.amazonaws.com`, `storage.googleapis.com`).

### Outbound (WeDO → externo)

| Trigger | Target | Via |
|---|---|---|
| Candidate stage change | Gupy/Pandape/Merge | `ATSSyncService` |
| Onboarding cliente/deal | HubSpot | `HubSpotService` |
| Outreach | Mailgun, Twilio | email providers + WA client |
| Scheduling | Google Calendar, MS Graph | calendar services |

---

# 3. ORQUESTRAÇÃO

## 3.1 Framework

**Primário: LangGraph StateGraph [✓]**

| Graph | Arquivo | Linha |
|---|---|---|
| JobWizardGraph | `lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py` | 176–177 |
| WSIInterviewGraph | `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` | 871–872 |
| InterviewGraph | `lia-agent-system/app/domains/interview_scheduling/agents/interview_graph.py` | 129–130 |

Import comum: `from langgraph.graph import StateGraph, END as LEND`.

**Secundário: orquestrador custom [✓]**
- `MainOrchestrator` — `app/orchestrator/main_orchestrator.py` — single entry point
- `CascadedRouter` — `app/orchestrator/cascaded_router.py` — 8-tier cascade
- `AgenticLoop` — `app/orchestrator/agentic_loop.py` — tool-use loop
- `LLMCascadeRouter` — `app/orchestrator/llm_cascade.py` — Flash → Pro → Ultra

**Não usados:** CrewAI, LangChain (apenas tracing passivo via Sentry/LangSmith hooks).

**LangSmith:** tracing opcional via `@langsmith.traceable` com fallback ImportError (`job_wizard_graph.py:21-25`).

## 3.2 Topologia — DAGs com ciclos controlados [✓]

### JobWizardGraph
```
intent_classifier ──(cond)──► response_generator | stage_transition | field_extractor
field_extractor ──► tool_router
tool_router ──(cond)──► tool_executor | response_generator
tool_executor ──► response_generator
response_generator ──► stage_transition
stage_transition ──(cond)──► END | intent_classifier  (CYCLE)
```
- `MAX_ITERATIONS = 10` (`:63`)
- HITL: `interrupt_before=["stage_transition"]`

### WSIInterviewGraph
```
lg_dispatcher ──(cond)──► lg_load_context | lg_validate_response
lg_load_context ──(cond)──► END(error) | lg_generate_question
lg_generate_question ──(cond)──► END | lg_generate_feedback
lg_validate_response ──(cond)──► lg_score_response | lg_advance
lg_score_response ──► lg_advance
lg_advance ──(cond)──► lg_generate_question (CYCLE) | lg_generate_feedback
lg_generate_feedback ──► END
```
- HITL: `interrupt_before=["lg_generate_feedback"]`

### InterviewGraph
```
LOADER ──► COLLECTOR ──► ROUTER
ROUTER ──(cond)──► COLLECTOR (loop) | VALIDATOR | RESPONSE
VALIDATOR ──(cond)──► EXECUTOR | RESPONSE
EXECUTOR ──► RESPONSE ──► END
```
- `MAX_ITERATIONS = 8` (`:112`)

### MainOrchestrator (pipeline linear)
```
UniversalContext → FairnessGuard → TenantContext
  → Phase 0 (PendingAction) → Phase 1 (ActionExecutor)
  → Phase 2 (CascadedRouter → DomainWorkflow → Agent)
```

### CascadedRouter (8-tier fallthrough)
```
T0: MemoryResolver (pronomes/referências)
T1: LRU in-process (MD5, O(1))
T2: Redis hash cache (distribuído)
T3: VectorSemanticCache (pgvector, cosine ≥ 0.85)
T4: FastRouter (regex/keyword)
T5: LLM Cascade (Flash → Pro → Ultra)
T6: AutonomousReActAgent (cross-domain)
Fallback: clarification_needed
```

## 3.3 Estado compartilhado

### Schemas LangGraph
- **JobWizardState** (`libs/agents-core/lia_agents_core/state_machine.py`): TypedDict — `messages`, `current_stage`, `job_draft`, `confidence_scores`, `reasoning_steps`, `tool_calls`, `tool_results`, `session_id`, `company_id`, `user_id`, `should_continue`, `needs_clarification`, `error`, `response_text`, `extracted_fields`. Efêmeros (excluídos do checkpoint merge): `user_message`, `session_id`, `execution_id` (`:47`).
- **WSIInterviewState**: dataclass custom com wrappers `_wsi_state_to_dict` / `_wsi_state_from_dict`.
- **InterviewStateDict**: TypedDict (`session_id`, `company_id`, `user_id`, `message`, `workflow_data`, `conversation_history`).

### Persistência [✓]
- **LangGraph PostgresSaver** — `libs/agents-core/lia_agents_core/checkpointer.py` — prod: `PostgresSaver.from_conn_string()` (via `langgraph-checkpoint-postgres`); dev: `MemorySaver` (com WARNING). `RuntimeError` se indisponível em prod. `thread_id = session_id`.
- **StateManager** — `app/orchestrator/state_manager.py` — dict in-memory por `conversation_id`; integração opcional com `ConversationMemory`. **[⚠] WARNING `LIA-M05` em prod se Redis ausente.**
- **CascadedRouter cache** — resultados de routing em Redis (T2) + pgvector (T3).

### Leitura/escrita
- Nodes LangGraph recebem state dict, retornam atualizado, LangGraph faz merge.
- MainOrchestrator passa `UniversalContext` (Pydantic) pelas fases.
- Cross-agent: `StateManager.state_store[conversation_id]["agent_results"]`.

## 3.4 Erros e fallbacks [✓]

1. **Graph-level:** `_invoke_langgraph` wrapa `ainvoke()` em try/except, seta `error` no state, loga `exc_info=True` (`job_wizard_graph.py:275`, `wsi_interview_graph.py:999`, `interview_graph.py:200+`).
2. **Circuit Breaker** (`app/shared/resilience/circuit_breaker.py`) — states CLOSED/OPEN/HALF_OPEN · defaults: `failure_threshold=5`, `recovery_timeout=30s`, `success_threshold=2`, `timeout=10s` · notificação Bell+Teams no OPEN (Redis-deduped 1/h) · admin API `/api/v1/admin/circuit-breakers`.
3. **DLQ** (`app/shared/resilience/dlq_service.py`) — Celery retries exausto → Redis list `dlq:{queue}` · TTL 7d · cap 1000/queue · admin endpoints inspect/requeue/clear.
4. **LLM Cascade** — Flash → Pro → Ultra por threshold de confidence · timeout independente por tier.
5. **CascadedRouter fallthrough** — 8 tiers antes de pedir clarificação.
6. **Celery `LIATask.on_failure`** — push automático para DLQ (`libs/config/lia_config/celery_app.py:~130`).

## 3.5 Timeouts & retries

| Componente | Timeout | Retries | Localização |
|---|---|---|---|
| LLM calls (WSI) | 30s | — | `app/api/v1/wsi/_shared.py:290` |
| Candidate search (PeArch) | 30s | — | `app/api/v1/candidate_search/contact.py:280` |
| Circuit Breaker request | 10s | — | `circuit_breaker.py` (default) |
| Redis | 0.5s conn + 0.5s socket | — | `app/core/redis_client.py:78-79` |
| Celery webhook tasks | — | 3 · 60/120/240s | `app/jobs/webhook_tasks.py:20-21` |
| Celery wizard async | — | 2 · 30s | `app/jobs/tasks/agents.py:12,70-75` |
| Celery pipeline transition | — | 2 · 20s | `app/jobs/tasks/agents.py:77,117-122` |
| Celery result expiry | 3600s | — | `celery_app.py` |
| WebSocket session | 3h max | — | `app/api/v1/jobs_ws.py:24-25` |
| WebSocket poll | 2s | — | `app/api/v1/jobs_ws.py:22-23` |
| AgenticLoop | — | 3 (`LIA_MAX_TOOL_ITERATIONS`) | `agentic_loop.py:21` |
| JobWizardGraph | — | 10 iters | `job_wizard_graph.py:63` |
| InterviewGraph | — | 8 iters | `interview_graph.py:112` |
| CBI question gen | — | 3 | `wsi/reports.py:231` |

---

# 4. DADOS & PERSISTÊNCIA

## 4.1 Banco de dados

**PostgreSQL 16 + pgvector [✓]**
- Imagem: `pgvector/pgvector:pg16` (docker-compose.yml)
- Conn: `postgresql+asyncpg://` via SQLAlchemy 2.0 async (`lia_config/database.py`)
- ORM: SQLAlchemy `declarative_base` · `async_sessionmaker`
- Multi-tenancy: **RLS** via `SET config('app.company_id', ...)` por sessão · role `lia_app` · deny-by-default (migration `068_rls_deny_by_default.py`)
- Migrations: **76 Alembic** (`001`–`076`)

### Tabelas principais (verificadas)
| Tabela | Domínio | Fonte |
|---|---|---|
| `users` | Auth | `app/auth/models.py:33` |
| `wsi_sessions / questions / response_analyses / results / reports` | CV Screening | `database/wsi_schema.sql` |
| `conversation_memories` | RAG | `app/core/database.py:~1003` |
| `knowledge_base` | RAG | `app/core/database.py:~1020` |
| `talent_pool_candidates / talent_pools` | Talent | `scripts/create_hnsw_indexes.sql` |
| `twin_decisions / digital_twins` | Digital Twin | idem |
| `routing_cache_vectors` | Orchestrator | migration 028 |
| `job_drafts` | Jobs | `app/core/database.py` |
| `interaction_feedback / learning_patterns` | Learning | `app/core/database.py` |

Models adicionais em `app/models/`: `voice_screening`, `activity_feed`, `ats_integration`, `task`, `agent_activity`, `calibration`, `candidate_feedback`, `ui_actions`, `audit_log`, `workforce`, `archetype`, `candidate_list`, `communication_history`, `candidate_attachment`, `lia_opinion`, `journey_mapping`, `integration_hub`, `recruitment_journey`, `admin_settings`, `pearch`.

### Índices HNSW (pgvector)
```sql
-- scripts/create_hnsw_indexes.sql
CREATE INDEX idx_tpc_candidate_embedding       ON talent_pool_candidates USING hnsw (candidate_embedding vector_cosine_ops)        WITH (m=16, ef_construction=64);
CREATE INDEX idx_talent_pools_archetype_embedding ON talent_pools        USING hnsw (archetype_embedding vector_cosine_ops)       WITH (m=16, ef_construction=64);
CREATE INDEX idx_twin_decisions_embedding      ON twin_decisions         USING hnsw (embedding vector_cosine_ops)                 WITH (m=16, ef_construction=64);
CREATE INDEX idx_digital_twins_embedding       ON digital_twins          USING hnsw (twin_embedding vector_cosine_ops)            WITH (m=16, ef_construction=64);
```
B-tree em `conversation_memories(company_id, session_id, user_id, created_at)`, `learning_patterns(pattern_type, pattern_key)`, + índices RLS.

## 4.2 Vector stores — pgvector nativo [✓] (sem DB externo)

| Propósito | Tabela | Dim | Modelo |
|---|---|---|---|
| Conversation memory | `conversation_memories` | 768 | Gemini text-embedding-004 |
| Knowledge base (RAG) | `knowledge_base` | 768 | Gemini text-embedding-004 |
| Talent pool candidates | `talent_pool_candidates` | 768 | — |
| Talent pool archetypes | `talent_pools` | 768 | — |
| Digital twin decisions | `twin_decisions` | 768 | Gemini text-embedding-004 |
| Digital twins | `digital_twins` | 768 | — |
| Routing semantic cache | `routing_cache_vectors` | **1536** | **OpenAI text-embedding-3-small** |

- **Primário (routing):** OpenAI `text-embedding-3-small` (1536) — `vector_semantic_cache.py:30`
- **Fallback (domínio):** Gemini `text-embedding-004` (768) — `vector_semantic_cache.py:31`
- **Hybrid search:** pgvector cosine + tsvector BM25 (`app/api/v1/rag_search.py:4`) — peso configurável (1.0=semantic puro · 0.0=BM25 puro)

### Chunking — factory pattern [✓]
`app/shared/intelligence/chunking/`:
- `sliding_window.py` — chunk=1000, overlap=100, snap em sentença
- `semantic_chunker.py` — agrupamento por similaridade de embedding, max_chunk_size configurável
- `recursive.py`
- `section_aware.py`
- DocumentType (em `base.py`): CV, Job Description, Policy, Generic

## 4.3 Cache — 3 camadas [✓]
`app/shared/resilience/cache_manager_service.py`:
| Layer | Provider | TTL |
|---|---|---|
| L1 Session | dict in-memory | vida da sessão |
| L2 Redis | Redis 7 Alpine | configurável por namespace |
| L3 PostgreSQL | Postgres | configurável por namespace |

### CacheTTL constants (`app/shared/cache_strategy.py`)
- `SESSION` 3.600s · `VOLATILE` 86.400s · `STANDARD` 604.800s (7d) · `STABLE` 2.592.000s (30d) · `PERMANENT` 0

### TTLs por domínio (event-driven invalidation)
| Domain | TTL | Invalidado por |
|---|---|---|
| candidate_search | 300s | candidate_update/create |
| candidate_profile | 600s | candidate_update |
| job_vacancy | 300s | job_update/create/close |
| job_description | 1800s | job_update, jd_regenerate |
| wsi_score | 3600s | screening_complete, candidate_update |
| pipeline_stages | 1800s | stage_update, company_config_update |
| analytics | 600s | pipeline_change, candidate_update |
| routing | 1800s | routing_config_update |

**Embedding cache** (`app/domains/ai/services/embedding_cache_service.py`): Redis prefix `emb:`, TTL 24h; fallback memory; warm-up de job titles ativos no startup.

**Orchestrator domain cache** (`main_orchestrator.py:52-58`): analytics 90s · kanban_search 60s · kanban_insight 120s · recruiter_assistant 300s · pipeline_context 60s.

## 4.4 Filas / Eventos — Celery [✓]

**Broker configurável** (`libs/config/lia_config/celery_app.py`):
- `BROKER_BACKEND=redis` (default) → `REDIS_URL`
- `=rabbitmq` → `RABBITMQ_URL`
- `=pubsub` → `CELERY_BROKER_URL` (migração GCP planejada)
- **Result backend:** sempre Redis (`result_expires=3600`)

### Priority queues
| Queue | Prior | Concur | Domínios |
|---|---|---|---|
| `sourcing_high` | 8 | 4 | Sourcing, candidate search |
| `evaluation_normal` | 5 | 4 | WSI, triagem, screening |
| `vagas_normal` | 5 | — | Wizard, kanban, automation |
| `onboarding_low` | 3 | 2 | Communications, reports, LGPD |
| `celery` | default | — | fallback |

Exchange: `lia_tasks` (direct).

### Beat scheduled (16 jobs)
| Task | Schedule | Queue |
|---|---|---|
| drift.run_batch | Daily 06h BRT | onboarding_low |
| audit.apply_lifecycle_policy | Monthly 1st 03h | — |
| lgpd.run_cleanup_daily | Daily 02h | — |
| conversation.ttl_cleanup | Daily 03h | — |
| briefing.send_daily | Daily 06h | — |
| followup.process_pending | Hourly | — |
| wsi.check_abandoned | Every 4h | — |
| feedback.process_pending_sends | Every 2h | — |
| ragas.evaluate_batch | Daily 00h | — |
| routing.recompute_adjustments | Daily 04h | — |
| data.retention.run | Monthly 1st | — |
| agents.registry.check_reload | Every 1 min | — |
| rag.rebuild_all_domains | Daily 01h | — |
| digest.send_weekly | Monday 08h | — |
| ml.feedback.recompute_active_jobs | Sunday 23h | — |
| memory.compress_old_episodes | Daily 00h | — |

### Retry policies
| Task | Retries | Backoff |
|---|---|---|
| webhook_tasks | 3 | 60/120/240s (exp) |
| agents.wizard.process_async | 2 | 30s fixed |
| agents.pipeline.transition_async | 2 | 20s fixed |

Failed → DLQ Redis (TTL 7d, cap 1000/queue).

### WebSocket / SSE operacionais
- WS `ws/jobs/{job_id}` — progress de Celery (`app/api/v1/jobs_ws.py`)
- SSE agent chat — `app/api/v1/agent_chat_sse.py` + `chat.py` (asyncio.Queue)

### Monitoring
- Flower — `mher/flower:2.0` na 5555 (docker-compose)
- DLQ admin — `/api/v1/admin/dlq`
- Circuit Breaker admin — `/api/v1/admin/circuit-breakers`

---

# 5. CAMADAS CROSS-CUTTING

## 5.1 Fairness

### FairnessGuard — bloqueio pré-LLM [✓]
- `lia-agent-system/app/shared/compliance/fairness_guard.py`
- Duas listas: `IMPLICIT_BIAS_TERMS` (PT, 30+) + `IMPLICIT_BIAS_TERMS_EN` (EN, 30+) — normalização unicode antes do match
- Cobre: discriminação estética, proxies socioeconômicos (bairro, escola), religião (afro-brasileiras, "valores cristãos"), deficiência ("sem restrições físicas"), família/maternidade, idade ("energia jovem"), geografia ("periferia", "zona rural")
- Retorno: `FairnessCheckResult(is_blocked, blocked_terms, soft_warnings, educational_message)` — mensagem cita Lei 12.984/14, Lei 13.146/15, CLT Art. 373-A, CF Art. 5
- **Integração:** `c3b_layer.py:pre_compliance()` para domínios HR (recruitment, talent_ranking, talent_pool, job_scoring, performance, salary_benchmark, job_management, candidate_evaluation) + chamado direto em `agent_chat_ws.py`

### Fairness Reports API [✓]
`app/api/v1/fairness_reports.py`:
- `GET /api/v1/fairness/reports/summary` — blocks/warnings agregados por categoria
- `GET /api/v1/fairness/reports/trend` — série temporal diária
- `GET /api/v1/fairness/audit/logs` — audit trail paginado (filter category, blocked_only)
- `GET /api/v1/fairness/reports/export` — CSV/JSON

Auth: `get_current_user`. Data backing: `FairnessReportRepository` (queries reais, não mock).

### Admin Compliance Fairness Report [✓]
`app/api/v1/admin_compliance_fairness.py`:
- `GET /api/v1/admin/compliance/fairness/report` — Four-Fifths Rule sobre `BiasAuditSnapshot`
- HMAC-SHA256 signed (NYC LL 144 / EU AI Act Art. 13) · fallback "unsigned" se `REPORT_SIGNING_KEY` ausente
- Auth: `require_admin`

## 5.2 LGPD / Privacy

### API Compliance (DPO, Breaches, Decisões) [✓]
`app/api/v1/lgpd_compliance.py` — 28+ endpoints:
- `GET /api/v1/lgpd/stats`
- CRUD DPO: `GET|POST|PUT /api/v1/lgpd/dpo`
- Breaches: `GET|POST|PUT /api/v1/lgpd/breaches`, `.../notify-anpd` (rastreio 48h), `.../notify-subjects`, `.../resolve`
- Decisões (Art. 20): `GET|POST /api/v1/lgpd/decisions`, `.../request-human-review`, `.../complete-human-review`
- Exclusão: `POST /api/v1/lgpd/schedule-deletion`, `POST /api/v1/lgpd/run-cleanup`, `GET /api/v1/lgpd/pending-deletions`

Auth: `get_verified_company_id` (JWT) · admin via `require_admin`. Prazo 48h ANPD trackeado por `_hours_since_detection()`.

### Consent — versionado [✓]
`app/api/v1/consent_management.py`:
- `POST|GET /api/v1/consent/versions/` · `.../current/{type}`
- `POST|GET /api/v1/consent/events/` · `/subject/{id}` · `/revoke`
- `GET /api/v1/consent/stats`

SHA256 hash do conteúdo (integridade de versão) + SHA256 proof hash por evento (audit trail). `renewal_period_days`. Multi-channel (WhatsApp).

### Consent granular — per-purpose [✓]
`app/api/v1/granular_consent.py`:
- `GET /api/v1/consent/granular/{candidate_id}`
- `POST /api/v1/consent/granular/{candidate_id}/update`
- Purposes: `ai_screening`, `ai_scoring`, `ai_video_analysis`, `ai_comparison`, `data_retention`, `marketing`, `analytics`
- Flag `all_blocking_given` · service `domains/lgpd/services/granular_consent_service.py`

### DSR — Portal do Titular [✓]
`app/api/v1/data_subject_requests.py`:
- `POST /api/v1/data-subject-requests/` (**público, sem auth** — LGPD Art. 18)
- `GET /api/v1/data-subject-requests/track/{id}` (público)
- CRUD + `assign / verify-identity / process / complete / reject`
- SLA: 15 dias úteis via `calculate_sla_deadline()` · overdue tracking
- Notificações: `NotificationService` fail-safe (nunca bloqueia o DSR)
- Tipos: access, correction, deletion, portability, objection, restriction, explanation, **revisao_decisao_automatizada**

### Retenção & Cleanup [✓]
`app/domains/lgpd/services/lgpd_cleanup_service.py`:
| Dado | TTL |
|---|---|
| rejected/withdrawn candidates | 90d |
| chat_messages | 90d (Art. 18 minimização) |
| interview_data/notes | 180d |
| screening_logs / AI logs | 365d |

Celery Beat `lgpd-cleanup-daily` (02:00 Brasília) · dry-run por default · tabelas whitelist via `_ALLOWED_TTL_TABLES` (`candidates`, `vacancy_candidates`, `ai_consumption`).
Admin: `app/api/v1/admin_lgpd.py` — `POST .../run-cleanup`, `GET .../cleanup-status`, `GET .../retention-policy`.

### PII masking [✓]
- Logs: `app/shared/pii_masking.py` — CPF, email, telefone BR, nomes. `PIIMaskingFilter` via `install_global_pii_masking()` em root logger + handlers + stack traces.
- Sentry: `app/core/sentry.py` — scrub em messages e breadcrumbs via `_before_send` hook. `send_default_pii=False`.
- LLM prompt: `c3b_layer.py:pre_compliance` chama `strip_pii_for_llm_prompt()` para domínios HR.

### Anonimização [✓]
- Bias audit retorna só agregados ("Apenas estatísticas agregadas LGPD-safe sem PII" — `bias_audit.py:1`)
- Fairness logs expõem `query_hash` SHA-256 em vez da query original (`fairness_reports.py:131`)

## 5.3 Bias — detecção, mitigação, monitoramento

### Four-Fifths Rule (Adverse Impact) [✓]
`app/api/v1/bias_audit.py` + `app/shared/services/bias_audit_service.py`
- Dimensões: gender (M/F/other), age_group (<30, 30–44, 45+), disability (PCD/non-PCD), region (estado)
- Métricas: AIR ≥ 0.80 · chi-square (scipy ou fallback puro Python) · EEOC flag (Four-Fifths AND p ≥ 0.05)
- `GET /api/v1/bias-audit/job/{job_id}` + `/history`
- Fonte: `RubricEvaluation` + `Candidate` (approval threshold 60.0)
- Persistência: `BiasAuditSnapshot`

### Pré-query block
Ver 5.1 (FairnessGuard).

### Monitoring via Trust Center [✓]
`app/api/v1/trust_center.py` — `GET /api/v1/trust-center/{slug}/bias-audits` (togglable por empresa via `show_bias_audits`).

## 5.4 Compliance

### Controls Library [✓]
`app/api/v1/compliance_controls.py` — ISO 27001, SOC 2, SOX, LGPD. CRUD de control library, company controls, audits, SOX controls, dashboard, evidence upload, framework seeding. Auth multi-tenant.

### C3b Layer (Strangler) [✓]
`app/shared/compliance/c3b_layer.py` — pre (PII strip + FairnessGuard) e post (FactChecker + AuditService logging) em todo chat WS/SSE.
**[⚠] Feature flag perigosa: `LIA_DISABLE_C3B=1` desativa toda a camada.**
Domínios: recruitment, talent_ranking, talent_pool, job_scoring, performance, salary_benchmark, job_management, candidate_evaluation.

### Hiring Policy Engine [✓]
`app/api/v1/hiring_policy.py` — blocos (pipeline, scheduling, communication, screening, automation) · setup conversacional via `PolicyReActAgent` · decisões dos agentes respeitam policy da empresa (auto_screening thresholds, rejection deadlines, autonomy levels).

### Trust Center (portal público) [✓]
`app/api/v1/trust_center.py` — público (overview, certifications, controls, bias audits, subprocessors, resources, updates) + admin (settings CRUD, uploads). Slug-based por empresa.

### Observability/Governance API [✓]
`app/api/v1/observability.py` — AI inference logs (explainability), data access logs (LGPD), consent, incidents (SOC2/ISO27001), model evals, controls, dashboard.

## 5.5 Logging / Observabilidade

### Structured JSON [✓]
`app/core/logging_config.py` — Prod: JSON com `timestamp, level, logger, message, request_id, user_id, exception?, data?`. Dev: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`. Level via `LOG_LEVEL`.

### Request middleware [✓]
`app/core/logging_middleware.py` — `request_id, method, path, status_code, duration_ms, company_id, user_id, tier` · tiers: `agent` (lia-assistant/agent/wsi/wizard), `management` (admin/compliance/audit/drift/bias), `data` (resto).

### Sentry [✓]
`app/core/sentry.py` — FastAPI/Starlette · sample rate configurável · PII scrub no before_send · fail-safe (no SDK/DSN/failure).

### Audit Timeline [✓]
`app/api/v1/audit_timeline.py` — `GET /api/v1/audit/executions/{id}/timeline` (step-by-step agent reasoning: llm_call, tool_call, node_transition — com model, tokens, latency, previews) + `GET /api/v1/audit/executions`.

### Agent Explainability [✓]
`app/api/v1/agent_explainability.py` — `GET /api/v1/explainability/timeline/{session_id}` + stats/summary · backing `ExecutionLogStore`.

### WSI Observability [✓]
`app/api/v1/wsi_observability.py`.

## 5.6 Segurança

### AuthN — JWT + WorkOS SSO [✓]
- `app/auth/dependencies.py` — HTTPBearer · `decode_token()` (tipo `access`) · user via UUID do `sub`
- Models: `app/auth/models.py` + `UserRole` enum
- WorkOS: `app/auth/workos_schemas.py`, `workos_models.py`
- Front: `plataforma-lia/src/stores/auth-store.ts` (Zustand — login, loginWithSSO, register, logout, refreshUser, initAuth)

### AuthZ — Role-Based [✓]
`app/auth/dependencies.py:99-123` — `require_admin`, `require_admin_or_recruiter` (:122-123), factory `require_role()`, `get_current_active_user` (403 se inativo), `get_current_user_or_demo` (:155).

### Multi-tenant — TenantGuard [✓]
`app/shared/tenant_guard.py`:
- Primário: `company_id` JWT-validated em `request.state` (setado por `AuthEnforcementMiddleware`)
- Header `X-Company-ID`: precisa **bater** com JWT — cross-tenant logado e bloqueado (403)
- Prod/stage: resolução não-JWT rejeita com 401
- Dev: header/query param aceito

### Prompt injection guard [✓]
`app/shared/prompt_injection.py` (facade) + `app/shared/robustness/security_patterns.py` (engine):
- 10 categorias: jailbreak, data exfiltration, bias elicitation, score manipulation, privilege escalation, PII extraction, fairness bypass, system override, delimiter injection, role manipulation
- 5 risk levels (none/low/medium/high/critical) · 20+ regex PT/EN
- Integração: `agent_chat_ws.py`, `agent_chat_sse.py` antes de LLM

### Token budget [✓]
Referenciado em `agent_chat_sse.py`/`agent_chat_ws.py` — `check_budget()`, `get_plan_for_company()`, `increment_usage()` · `app.domains.credits.services.token_budget_service`. Budget checado antes do LLM, usage incrementado depois.

---

# 6. FRONTEND → BACKEND

## 6.1 Endpoints API — FastAPI v1

**236 router files** em `lia-agent-system/app/api/v1/`. Agrupamento por módulo (rotas principais):

### Auth & Users
| Rota | Arquivo |
|---|---|
| `/api/v1/auth/*` | `auth.py` |
| `/api/v1/workos/*` | `workos.py` |
| `/api/v1/admin/*` | `admin.py` |
| `/api/v1/admin/settings/*` | `admin_settings.py` |
| `/api/v1/admin/agents/*` | `admin_agents.py` |
| `/api/v1/admin/prompts/*` | `admin_prompts.py` |
| `/api/v1/admin/token-budget/*` | `admin_token_budget.py` |
| `/api/v1/admin/circuit-breakers/*` | `admin_circuit_breakers.py` |
| `/api/v1/admin/dlq/*` | `admin_dlq.py` |
| `/api/v1/admin/platform/*` | `admin_platform.py` |

### LGPD / Privacy / Consent
Ver §5.2 para lista exaustiva. Arquivos: `lgpd_compliance.py`, `admin_lgpd.py`, `consent_management.py`, `granular_consent.py`, `data_subject_requests.py`.

### Fairness & Bias
| Rota | Arquivo |
|---|---|
| `GET /api/v1/fairness/reports/summary` | `fairness_reports.py` |
| `GET /api/v1/fairness/reports/trend` | `fairness_reports.py` |
| `GET /api/v1/fairness/audit/logs` | `fairness_reports.py` |
| `GET /api/v1/fairness/reports/export` | `fairness_reports.py` |
| `GET /api/v1/bias-audit/job/{job_id}` | `bias_audit.py` |
| `GET /api/v1/bias-audit/job/{job_id}/history` | `bias_audit.py` |
| `GET /api/v1/admin/compliance/fairness/report` | `admin_compliance_fairness.py` |

### Compliance & Observability
`compliance_controls.py`, `observability.py`, `trust_center.py`, `audit_timeline.py`, `audit_logs.py`, `compliance_status.py`.

### LIA Agent Chat & Assistant
| Rota | Arquivo |
|---|---|
| `POST /api/v1/chat/{session_id}/stream` (SSE) | `agent_chat_sse.py` |
| `WS /ws/chat/{session_id}` | `agent_chat_ws.py` |
| `/api/v1/lia-assistant/*` | `lia_assistant_*.py` (7 arquivos) |
| `/api/v1/lia-autonomous/*` | `lia_autonomous.py` |
| `/api/v1/lia-feedback/*` | `lia_feedback.py` |
| `/api/v1/lia-voice/*` | `lia_voice.py` |
| `/api/v1/lia-multimodal/*` | `lia_multimodal.py` |
| `/api/v1/orchestrated-talent-chat/*` | `orchestrated_talent_chat.py` |
| `/api/v1/orchestrated-job-chat/*` | `orchestrated_job_chat.py` |
| `/api/v1/navigation-intent/*` | `navigation_intent.py` |
| `/api/v1/kanban-assistant/*` | `kanban_assistant.py` |

### Agent Studio & Explainability
`agent_templates.py`, `agent_deployments.py`, `agent_approvals.py`, `agent_monitoring.py`, `agent_memory.py`, `agent_quality.py`, `agent_explainability.py`, `custom_agents.py`.

### Jobs & Pipeline
`pipeline.py`, `pipeline_templates.py`, `pipeline_velocity.py`, `pipeline_prediction.py`, `pipeline_policy.py`, `pipeline_orchestrator.py`, `sourcing.py`, `sourcing_pipeline.py`, `sourcing_agents.py`, `triagem.py`, `screening.py`, `interviews.py`, `scheduling.py`, `activities.py`.

### Async Jobs
| Rota | Arquivo |
|---|---|
| `POST /api/v1/async/triagem/run-batch` | `async_endpoints.py` |
| `POST /api/v1/async/interviews/wsi/start` | `async_endpoints.py` |
| `WS /ws/jobs/{job_id}` | `jobs_ws.py` |

### Search & Candidates
`semantic_search.py`, `search_archetypes.py`, `search_assistant.py`, `rag_search.py`, `candidate_lists.py`, `candidate_compare.py`, `talent_funnel.py`, `talent_pools.py`.

### WSI
`wsi/sessions.py`, `wsi/evaluation.py`, `wsi_questions.py`, `wsi_observability.py`, `wsi_async.py`.

### Communication
`communication.py`, `communications.py`, `multi_channel.py`, `whatsapp.py`, `email.py`, `voice.py`.

### Company & Settings
`company.py`, `company_culture.py`, `hiring_policy.py` (`/api/v1/company-hiring-policy/*` + `.../{id}/chat`), `settings_progress.py`, `integrations.py`.

### Webhooks
`webhooks.py`, `external_webhooks.py`, `whatsapp_webhook.py`, `mailgun_webhooks.py`, `merge_webhooks.py`.

### ML & Analytics
`ml_predictions.py`, `predictive_analytics.py`, `dashboard_data.py`, `saas_metrics.py`, `recruiter_metrics.py`.

### Health
`health_check.py`, `health_langgraph.py`, `rails_health.py`.

## 6.2 WebSocket / SSE

### WS chat principal [✓]
- Backend: `app/api/v1/agent_chat_ws.py` — `ws://host/ws/chat/{session_id}`
- Protocolo JSON bidir — cliente: `message`, `ping`, `abort` · servidor: `thinking`, `token`, `message`, `panel_update`, `background_task_update`, `error`, `pong`
- Pipeline segurança: `check_input_security()` → `FairnessGuard` → `pre_compliance()` → `check_budget()`
- `WSManager` em `ws_manager.py` para tracking de sessão
- Front: `plataforma-lia/src/hooks/chat/useChatTransport.ts` — auto-reconnect (`maxReconnectAttempts`, `reconnectBaseDelay`), parse `fairness_warnings`, fallback SSE

### SSE fallback [✓]
- Backend: `app/api/v1/agent_chat_sse.py` — `POST /api/v1/chat/{session_id}/stream`
- Eventos: `thinking, token, message, error` · keepalive pings · `Last-Event-ID` header aceito
- Mesmo pipeline de segurança (prompt injection + budget)
- Front: `useChatTransport.ts:305-315` (`sendMessageViaSSE()`) · proxy Next.js `/api/lia/chat/stream` (`plataforma-lia/src/app/api/lia/chat/stream/route.ts`)
- Outros SSE: `use-return-events.ts:152` — EventSource para stage transitions

### WS async jobs [✓]
`app/api/v1/jobs_ws.py` — `ws://host/ws/jobs/{job_id}` — poll Celery task state 1s · `status, progress, completed, failed` · max 3h (WSI longos). Front: `AsyncJobProgress.tsx:56-62` com `useRef<WebSocket>` + fallback HTTP polling.

### WS VoIP [✓]
Front: `plataforma-lia/src/components/triagem/VoIPCallButton.tsx:39-213`.

### WS Workflow Rail (ActionCable) [✓]
Front: `plataforma-lia/src/components/workflow-rail/useWorkflowRail.ts:48-112` — Rails ActionCable (`/cable?auth_token=`) · fallback polling.

## 6.3 Estado do Frontend — Zustand exclusivo

**17 stores** em `plataforma-lia/src/stores/`:
| Store | Propósito |
|---|---|
| `auth-store` | Auth state, JWT/SSO, permissions · devtools · reset registry |
| `chat-state-store` | Conversation IDs, wizard snapshots, user commands, LIA templates · `persist` (localStorage) |
| `kanban-store` | Kanban board |
| `candidates-store` | Candidate list/selection |
| `onboarding-store` | Onboarding wizard |
| `job-ui-store` | Job UI prefs |
| `job-filters-store` | Filtros de busca de job |
| `talent-funnel-store` | Funnel |
| `wizard-store` | Job creation wizard |
| `template-store` | Templates |
| `triagem-store` | Screening |
| `recent-items-store` | Recentes |
| `table-features-store` | Tabela (col/sort) |
| `navigation-store` | Nav |
| `ui-preferences-store` | Tema/prefs |
| `agent-studio-store` | Agent Studio |
| `index.ts` | barrel |

### Mecanismos de atualização
- **WS → Zustand:** respostas de chat via WS parseadas em `useChatTransport.ts` atualizam stores (ex: `chat-state-store` para conversation IDs)
- **SSE → React/Zustand:** consumido em `useChatPageHandlers.tsx` + `useChatTransport.ts`
- **Polling fallback:** `useWorkflowRail.ts` e `AsyncJobProgress.tsx`
- **Persistência:** `chat-state-store` via `persist` (localStorage) · `auth-store` via `devtools` (re-hidrata com `initAuth()`)
- **Reset:** `registerStoreReset()` em `auth-store.ts` — todos os stores registram cleanup, disparado no logout (`resetAllStores()`)

### React Context
Usado apenas para DI (providers em `app/[locale]/layout.tsx`, `SearchScopeControls.tsx`, `IntegrationCard.tsx`, `IntegrationsHub.tsx`). **Não é primary state** — Zustand faz isso.

---

# Apêndice — Estatísticas consolidadas

| Métrica | Valor |
|---|---|
| ReAct agents registrados (`ReactAgentRegistry`) | 17 |
| Total de classes de agente (incl. sub e não-registrados) | ~35 |
| LangGraph StateGraphs (não-ReAct) | 3 |
| Tool registries | 28 arquivos |
| Tools totais (estimado) | 120+ |
| APIs externas | 15+ |
| Webhooks inbound | 5 |
| LLM providers | 3 (Anthropic, OpenAI, Gemini) |
| Email providers | 2 (Mailgun + Resend) |
| ATS connectors | 3 (Gupy, Pandape, Merge) |
| Voice providers | 3 (OpenMic, Gemini Live, Twilio) |
| Calendar providers | 2 (Google, MS Graph) |
| Circuit breakers nomeados | 5+ (MAILGUN, OPENMIC, GOOGLE_CALENDAR, GEMINI_LIVE, AutonomousReActAgent) |
| Alembic migrations | 76 |
| Celery queues | 5 (4 priority + default) |
| Celery beat jobs | 16 |
| Router files FastAPI | 236 |
| Zustand stores | 17 |

---

# Apêndice — Itens marcados [⚠] / [?] (para revisão)

| # | Item | Marcador | Motivo |
|---|---|---|---|
| 1 | 3 registries de agentes (`AgentRegistry`, `ReactAgentRegistry`, `DomainRegistry`) | [⚠] | Sobreposição — decidir canônico e deprecar os demais |
| 2 | `PolicySetupAgent` em `app/agents/policy_setup_agent.py` | [⚠] | Shim com `DeprecationWarning` ainda importável |
| 3 | `StateManager` sem Redis em prod | [⚠] | WARNING `LIA-M05` — memória volátil por worker |
| 4 | `LIA_DISABLE_C3B=1` | [⚠] | Flag bypass de toda camada de compliance |
| 5 | Deepgram no fluxo OpenMic | [?] | Domínio allowlist do webhook OpenMic menciona deepgram.com mas sem serviço dedicado confirmado |
| 6 | Rate limits externos por API | [⚠] | Proteção é via CB + timeout, não throttling RPS declarado |
| 7 | `conversation.ttl_cleanup` + LGPD cleanup | [✓] | OK — listado para completude |
| 8 | HMAC-SHA1 no webhook Twilio | [⚠] | SHA1 é o exigido pela Twilio, mas é fraco — monitorar migração |
