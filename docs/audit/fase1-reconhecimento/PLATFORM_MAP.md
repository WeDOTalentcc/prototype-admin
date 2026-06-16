# PLATFORM_MAP.md — Inventário Completo da Plataforma WeDOTalent/LIA
**Protocolo:** P01  
**Data:** 2026-04-13  
**Repositórios auditados:**
- Frontend+IA: `plataforma-lia/` + `lia-agent-system/` (Replit)
- Backend+DB: `ats-api-copia/` (Rails 7.1 + PostgreSQL)

---

## 1. VISÃO GERAL DA ARQUITETURA

### Diagrama de 3 Camadas

```
┌─────────────────────────────────────────────────────────────────────┐
│  CAMADA 1: FRONTEND                                                  │
│  plataforma-lia/  |  Next.js 15 + TypeScript  |  Port 5000          │
│                                                                       │
│  Browser → BFF (478 route handlers) → BACKEND_URL (AI Layer)         │
│  WS: /ws/:path* → BACKEND_URL/ws/:path*                              │
│  Auth: WorkOS SSO + JWT cookie (7d)                                  │
└───────────────────┬─────────────────────────────────────────────────┘
                    │ HTTP/REST (BFF proxy, port 8001)
                    │ WebSocket /ws/chat/{sessionId}
                    │ SSE POST /chat/{sessionId}/stream
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CAMADA 2: AI LAYER                                                   │
│  lia-agent-system/  |  Python + FastAPI  |  Port 8001                │
│                                                                       │
│  MainOrchestrator → CascadedRouter (8 tiers) → Domain Agents         │
│  LangGraph (ReAct + StateGraph) | PostgreSQL (asyncpg) | Redis        │
│  pgvector | Celery | Alembic (76 migrations)                          │
└───────────────────┬─────────────────────────────────────────────────┘
                    │ RabbitMQ (AMQP): messages_exchange
                    │   rails→python: routing_key=messages_created
                    │   python→rails: routing_key=messages_processed
                    │ [✗] NO direct HTTP calls Rails↔Python
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CAMADA 3: RAILS BACKEND                                              │
│  ats-api-copia/  |  Rails 7.1 + PostgreSQL  |  Port 3000 (assumed)   │
│                                                                       │
│  CRUD: Jobs, Candidates, Users, Accounts, Pipeline                    │
│  Sneakers (RabbitMQ consumer) | Sidekiq (ActiveJob) | ActionCable     │
│  Elasticsearch (searchkick) | Apartment (multi-tenant schemas)         │
└─────────────────────────────────────────────────────────────────────┘
```

### Pontos-Chave de Integração

| Canal | Direção | Protocolo | Status |
|-------|---------|-----------|--------|
| Chat primário | Frontend ↔ AI Layer | WebSocket `/ws/chat/{sessionId}` | [✓] |
| Chat fallback | Frontend ↔ AI Layer | SSE `POST /chat/{sessionId}/stream` | [✓] |
| BFF proxy | Frontend → AI Layer | HTTP REST (478 rotas) | [✓] |
| Mensagens criadas | Rails → Python | RabbitMQ `messages_created` | [✓] |
| Respostas IA | Python → Rails | RabbitMQ `messages_processed` | [✓] |
| Importação jobs | Python → Rails | RabbitMQ `jobs_import` | [✓] |
| Onboarding events | Rails → Python | RabbitMQ `onboarding_events` | [✓] |
| ActionCable | Rails → Frontend | WebSocket `/cable` | [✓] |
| Rails → Frontend | direto | [✗] Não conectado — `NEXT_PUBLIC_RAILS_URL` comentado no .env | [✗] |

### Dois Bancos de Dados PostgreSQL Separados

> **CRÍTICO:** A plataforma opera com **DOIS PostgreSQL independentes**:
>
> - **AI Layer DB** — `lia_db` (asyncpg/SQLAlchemy, 76 migrations Alembic, pgvector habilitado)
> - **Rails Backend DB** — banco gerenciado pelo Rails (schema.rb, 85 migrations ActiveRecord, schemas Apartment por tenant)
>
> Não há shared DB, shared schema, nem foreign keys cruzadas. A sincronização ocorre exclusivamente via RabbitMQ.

---

## 2. AGENTES (AI Layer)

### 2.1 MainOrchestrator — Ponto de Entrada
- **Arquivo:** `app/orchestrator/main_orchestrator.py`
- **Propósito:** Único entry point para todas as mensagens LIA. Pipeline unificado (substitui legacy double-delegation).
- **Fluxo:**
  ```
  UniversalContext
    → FairnessGuard (pre-check: bloqueia ou soft-warn)
    → TenantContext enrichment
    → Phase 0: PendingAction (multi-turn / confirmação)
    → Phase 1: ActionExecutor (intents fechados)
    → Phase 2: ConversationMemory + CascadedRouter → DomainWorkflow → Agent ReAct
  ```
- **Status:** [✓]

### 2.2 AutomationReActAgent
- **Arquivo:** `app/domains/automation/agents/automation_react_agent.py`
- **Propósito:** Decomposição de tarefas, planejamento DAG e orquestração de execução.
- **LLM/Temp:** Claude Sonnet (`claude-sonnet-4-6`) / 0.3
- **System Prompt:** `AUTOMATION_DOMAIN_SPECIFIC` — `app/domains/automation/agents/automation_system_prompt.py`
- **Tools:** `get_automation_tools()` — `app/domains/automation/agents/automation_tool_registry.py`
- **Fluxo:** LangGraph `create_react_agent` (ReAct prebuilt). Max steps: `AUTONOMOUS_REACT_MAX_STEPS`
- **Memória:** `WorkingMemoryService` (sessão) + `PostgresSaver` checkpointer (cross-turn)
- **Deps:** `EnhancedAgentMixin` (FairnessGuard + memória longa + aprendizado), `LangGraphReActBase` (PII strip + AuditCallback)
- **Status:** [✓]

### 2.3 InterviewGraph (LangGraph StateGraph)
- **Arquivo:** `app/domains/interview_scheduling/agents/interview_graph.py`
- **Propósito:** Agendamento de entrevistas via máquina de estados discreta.
- **LLM/Temp:** Por nó (herda config do tenant)
- **Fluxo (StateGraph — não ReAct):**
  ```
  LOADER → COLLECTOR → ROUTER
                          ↓ campos faltando → COLLECTOR (loop, max 8 iter)
                          ↓ completo → VALIDATOR → EXECUTOR → RESPONSE → END
                          ↓ inválido → RESPONSE → END
  ```
- **Nós:** `interview_state_loader`, `interview_details_collector`, `interview_router`, `interview_validator`, `interview_scheduler_executor`, `interview_response_planner`
- **Checkpointer:** `PostgresSaver` via `libs/agents-core/lia_agents_core/checkpointer.py`
- **Guard:** `MAX_ITERATIONS = 8` (proteção loop infinito, `interview_graph.py:42`)
- **Status:** [✓]

### 2.4 AutonomousReActAgent (Fallback Tier 6)
- **Arquivo:** `app/domains/autonomous/agents/autonomous_react_agent.py`
- **Propósito:** Agente cross-domain — ativado quando nenhum agente especializado tem confiança suficiente.
- **LLM/Temp:** Claude Sonnet via `LangGraphReActBase` / 0.3
- **System Prompt:** Constante `DOMAIN_INSTRUCTIONS` inline — prompt cross-domain
- **Tools:** 40+ ferramentas de `get_autonomous_tools()` — `app/domains/autonomous/agents/autonomous_tool_registry.py`
- **Resiliência:** `CircuitBreaker` singleton no nível do módulo — `failure_threshold=3`, `recovery_timeout=30s`
- **Status:** [✓]

### 2.5 CustomAgentRuntime (Agent Studio)
- **Arquivo:** `app/domains/agent_studio/custom_agent_runtime.py`
- **Propósito:** Runtime para agentes customizados criados por tenants via Agent Studio.
- **LLM/Temp:** Configurável via `model_override`; default Claude Sonnet / 0.7
- **System Prompt:** Template definido pelo tenant, injetado na inicialização
- **Tools:** Pool de `get_autonomous_tools()` + ferramentas de domínio filtradas por `allowed_tools`. 15 ferramentas perigosas bloqueadas em `_RESTRICTED_TOOLS` (frozenset).
- **Max Steps:** Configurável (default 8)
- **Context Levels:** `full | standard | minimal`
- **Status:** [✓]

### 2.6 PolicySetupAgent
- **Arquivo:** `app/domains/policy/agents/agent.py` (shim: `app/agents/policy_setup_agent.py`)
- **Propósito:** Onboarding conversacional para configuração de políticas de contratação.
- **Status:** [✓] (shim deprecated mantido para backward compat)

### 2.7 CVScreeningBatchService (de-agentificado)
- **Arquivo:** `app/domains/cv_screening/services/cv_screening_batch_service.py`
- **Propósito:** Triagem em lote de CVs. Migrado de `TriagemCurricularAgent` (Sprint 5) — agora serviço chamado diretamente por tarefas Celery.
- **LLM:** Via `rubric_evaluation_service` (Claude Sonnet)
- **Fórmula WSI:** `WSI = (técnico * 0.70) + (comportamental * 0.30)` — auto_approve ≥ 75, review ≥ 55
- **Status:** [✓]

### 2.8 AgentStudioDomain (meta-agente)
- **Arquivo:** `app/domains/agent_studio/domain.py`
- **Propósito:** Intents do Agent Studio (criar/gerenciar agentes customizados, marketplace, calibração).
- **Status:** [✓]

### 2.9 DigitalTwinDomain
- **Arquivo:** `app/domains/digital_twin/domain.py`
- **Propósito:** Clone de raciocínio SME via RAG few-shot — simula julgamento de especialista para avaliação de candidatos.
- **Compliance:** `high_impact: True`, `fairness_action_type: "screening"` — ativa FairnessGuard L3
- **Status:** [⚠] Estrutura confirmada; profundidade do RAG few-shot não verificada sem inspecionar implementações de serviço.

### Mapa de Dependências dos Agentes
```
MainOrchestrator
  ├── FairnessGuard ──────────── fairness_guard.py
  ├── SecurityPatterns ────────── security_patterns.py
  ├── CascadedRouter ──────────── cascaded_router.py
  │     ├── Tier 0: MemoryResolver
  │     ├── Tier 1: LRU in-process
  │     ├── Tier 2: Redis hash cache
  │     ├── Tier 3: VectorSemanticCache (pgvector)
  │     ├── Tier 4: FastRouter (regex/keyword)
  │     ├── Tier 5: LLMCascadeRouter (Gemini Flash→Sonnet→Opus)
  │     ├── Tier 6: AutonomousReActAgent
  │     └── Fallback: clarification_needed
  ├── DomainWorkflow ──────────── por domínio
  │     ├── AutomationReActAgent
  │     ├── InterviewGraph
  │     ├── CustomAgentRuntime (Studio)
  │     ├── CVScreeningBatchService
  │     └── [sourcing, pipeline, kanban, talent, job_management ReAct agents]
  └── TenantBudget ────────────── Redis token tracking
```

---

## 3. TOOLS E INTEGRAÇÕES

### 3.1 Registry de Tools
- **Arquivos:** `app/tools/registry.py`, `app/tools/tool_registry_metadata.yaml`
- **Padrão:** `ToolRegistry` + `ToolDefinition` dataclass. Suporta schemas duais: `to_claude_schema()` / `to_gemini_schema()`
- **YAML:** `tool_registry_metadata.yaml` é a fonte de verdade (Sprint G5); validado no startup via `ToolRegistry.validate_yaml()`
- **Escopos:** `TALENT_FUNNEL | JOB_TABLE | IN_JOB | GLOBAL`
- **Status:** [✓]

### 3.2 Tools Registradas

#### Job Wizard
| Tool | Descrição | Escopo |
|------|-----------|--------|
| `search_salary_benchmark` | Benchmark de salários por cargo/senioridade/localização | JOB_TABLE |
| `validate_job_fields` | Valida campos de criação de vaga | JOB_TABLE |
| `get_job_suggestions` | Sugestões IA para melhorar JD | JOB_TABLE |
| `save_job_draft` | Salva rascunho de vaga | JOB_TABLE |
| `get_job_templates` | Recupera templates de vaga | JOB_TABLE |
| `get_company_culture` | Dados de cultura da empresa | GLOBAL |

#### Sourcing
`search_candidates`, `boolean_search`, `filter_candidates`, `rank_candidates`, `get_candidate_profile`, `add_to_shortlist`, `search_talent_pool`, `generate_outreach_message`, `send_outreach`

#### Pipeline / Kanban
`get_pipeline_summary`, `move_candidate`, `approve_candidate`, `reject_candidate`, `get_kanban_insights`, `batch_move_candidates`

#### Automation
`decompose_task`, `prioritize_tasks`, `create_goal`, `update_task_status`, `list_tasks`, `get_task_details`, `schedule_automation`

#### Pool Custom Agent (Agent Studio — 15 tools)
```python
# app/domains/agent_studio/custom_agent_runtime.py:22
Read:  search_candidates, list_jobs, get_job_details, get_candidate_details,
       get_pipeline_summary, search_talent_pool, get_analytics_summary,
       get_company_culture, get_evaluation_criteria, summarize_context, clarify_request
Write: move_candidate, send_email, update_candidate_field, schedule_interview, create_note
```
Bloqueadas de agentes Studio: 15 ops perigosas (`delete_*`, `bulk_sync_candidates`, `finalize_hiring`, `batch_move`, `reject_autonomous_action`, `admin_override`).

### 3.3 Integrações Externas

| Serviço | Arquivo | Auth | Status |
|---------|---------|------|--------|
| Mailgun (email) | `app/services/email_providers/mailgun_provider.py` | `MAILGUN_API_KEY` | [✓] |
| Twilio WhatsApp | `app/services/whatsapp_client.py` | `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` | [✓] |
| Microsoft Teams | `app/shared/channels/adapters/teams_adapter.py` | `MICROSOFT_APP_ID/PASSWORD`, `TEAMS_WEBHOOK_URL` | [✓] |
| Microsoft Graph/Calendar | `app/api/v1/microsoft_graph.py`, `app/api/v1/calendar.py` | Azure AD client credentials | [✓] |
| ATS (Gupy/Pandape/Merge.dev) | `app/shared/providers/ats_factory.py` | HMAC-SHA256 (Merge) | [✓] |
| SerpAPI (market benchmark) | `app/domains/analytics/services/market_benchmark_service.py:23` | `SERP_API_KEY` | [⚠] opcional; fallback LLM |
| WorkOS (auth) | `app/api/v1/workos.py` | `WORKOS_CLIENT_ID`, `WORKOS_API_KEY` | [✓] |
| Gemini Live (voz) | `app/shared/providers/voice_gemini_live.py` | API key | [⚠] |
| OpenAI Realtime (voz) | `app/shared/providers/voice_openai_realtime.py` | API key | [⚠] |
| Deepgram (STT) | `app/services/voice/deepgram_service.py` | API key | [⚠] |

### 3.4 Webhooks Inbound (AI Layer)
| Endpoint | Arquivo | Auth |
|----------|---------|------|
| `/webhooks/merge/` | `merge_webhooks.py` | HMAC-SHA256 |
| `/webhooks/mailgun/` | `mailgun_webhooks.py` | Signature verify |
| `/webhooks/job-status/` | `job_status_webhooks.py` | [?] |
| `/webhooks/external/` | `external_webhooks.py` | [?] |

### 3.5 Webhooks (Rails Backend)
- Modelos existem: `Webhook`, `WebhookLog`, `WebhookDeliveryLog`, `WebhookRegistration`
- [✗] Nenhum serviço ou job encontrado executando entrega de webhook outbound

---

## 4. ORQUESTRAÇÃO

### 4.1 Framework
- **Primário:** LangGraph (`create_react_agent` prebuilt ReAct + `StateGraph` para fluxos determinísticos)
- **Lib compartilhada:** `libs/agents-core/lia_agents_core/`
- **Classes base:** `LangGraphReActBase`, `LangGraphBase`, `EnhancedAgentMixin`

### 4.2 CascadedRouter — 8 Tiers
**Arquivo:** `app/orchestrator/cascaded_router.py`

| Tier | Nome | Mecanismo | Config |
|------|------|-----------|--------|
| 0 | MemoryResolver | Resolução de pronomes/referências contextuais (WorkingMemory) | — |
| 1 | LRU in-process | Hash MD5, O(1), dict in-memory, sem TTL | — |
| 2 | Redis hash cache | Distribuído, exact match, TTL=3600s | — |
| 3 | VectorSemanticCache | pgvector cosine similarity | threshold=0.85 |
| 4 | FastRouter | Regex/keyword (~80% queries), O(n) patterns | confidence≥0.70 |
| 5 | LLMCascadeRouter | Gemini Flash → Claude Sonnet → Claude Opus | Flash≥0.80, Sonnet≥0.70, Opus≥0.60 |
| 6 | AutonomousReActAgent | Fallback cross-domain | min_confidence=0.50 |
| — | clarification_needed | Pergunta ao usuário quando todos os tiers falham | — |

**Tracking de stats:** memory_hits, redis_hits, vector_hits, fast_hits, llm_hits, autonomous_hits, studio_agent_hits, clarification_issued, total

### 4.3 FastRouter Domains
**Arquivo:** `app/orchestrator/fast_router.py`

Sets de patterns regex para: `job_management`, `sourcing` (+subdomains: `sourcing_planner`, `sourcing_search`, `sourcing_enrich`, `sourcing_engagement`), `cv_screening`, `wsi_assessment`, `pipeline`, `kanban_search`, `kanban_insight`, `kanban_action`, `analytics`, `communication`, `automation`, `recruiter_assistant`, `agent_studio`, `digital_twin`, `recruitment_campaign`, `ats_integration`, `interview_scheduling`, `hiring_policy`, `talent_pool`

### 4.4 LLM Cascade
**Arquivo:** `app/orchestrator/llm_cascade.py`

- **Tier 3a:** `gemini-2.5-flash` (rápido, barato)
- **Tier 3b:** `claude-sonnet-4-6` (mid-tier)
- **Tier 3c:** `claude-opus-4-6` (fallback, mais caro)
- **Multi-model:** param `preferred_model` por tenant; fallback para cascade se confiança < 0.70
- **Token tracking:** acumulação por `request_id` → reportado para `TenantBudget`

### 4.5 A/B Testing no Router
- Experiment ID: `cascade_router_system_prompt`
- YAML config: `app/prompts/experiments/cascade_router_system_prompt.yaml`
- Seleção de variante por hash de `user_id` ou `session_id`
- Integrado com `PromptVersionRegistry`

### 4.6 Contexto Compartilhado (UniversalContext)
```python
# app/orchestrator/context_adapter.py
{
  "session_id": str,
  "user_id": str,
  "company_id": str,  # chave de isolamento de tenant
  "message": str,
  "domain": str,
  "conversation_history": list,
  "page_context": dict,  # job_id, candidate_ids, page_type
  "workflow_data": dict,
}
```

### 4.7 Tratamento de Erros e Fallbacks
- **Circuit Breakers:** Por provider (`GEMINI_CIRCUIT`, `MAILGUN_CIRCUIT`, `autonomous_react_agent`) — estados: CLOSED/OPEN/HALF_OPEN
- **Cascade em tiers:** Cada tier falha graciosamente e passa para o próximo
- **DLQ:** `app/shared/resilience/dlq_service.py` — dead letter queue para tasks falhas
- **Retry:** `tenacity` no Gemini provider (`stop_after_attempt(2)`, `wait_exponential(max=3s)`)
- **Timeout:** `LLM_TIMEOUT_SECONDS=120s`; `TimedToolNode` default 15s por tool com overrides

### 4.8 HITL (Human-in-the-Loop)
**Arquivo:** `app/domains/cv_screening/services/hitl_service.py`

- LangGraph `interrupt_before` para 3 fluxos críticos: WizardGraph (criação de vaga), PipelineTransitionAgent (movimentação de estágio), WSI Interview (finalização de avaliação)
- Protocolo: WS → `approval_required` → resposta humana → retoma grafo
- Persistência: Redis TTL 24h + PostgreSQL (best-effort) [⚠]

---

## 5. DADOS E PERSISTÊNCIA

### 5.1 AI Layer — PostgreSQL (lia_db)

**Driver:** `asyncpg` via SQLAlchemy async  
**URL:** `postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db`  
**Pool:** size=20, max_overflow=10  
**Migrations:** Alembic — 76 arquivos (`alembic/versions/`)

| Tabela | Domínio | Notas |
|--------|---------|-------|
| `candidates` | Recrutamento | Core recruitment candidates |
| `job_vacancies` | Recrutamento | Vagas de emprego |
| `job_requirements` | Recrutamento | Requisitos das vagas |
| `audit_logs` | Compliance | Todas decisões IA — retention 730d (scoring) / 1825d (messaging) |
| `hitl_pending_actions` | HITL | Estado de interrupções LangGraph |
| `hitl_audit_trail` | HITL | Histórico de aprovações |
| `routing_cache_vectors` | Router | pgvector para cache semântico (migration 028) |
| `agent_ragas_evaluations` | QA | Scores RAGAS — retention 90d |
| `ai_consumption` | Billing | Métricas de uso de LLM |
| `observability.AIInferenceLog` | Observabilidade | Logs de inferência |
| `rubric_evaluations` | Triagem | Registros de scoring WSI |
| `tenant_llm_configs` | Multi-tenancy | Config LLM por tenant (migration 058) |
| `company_modules` | Multi-tenancy | Gating de módulos por tenant (migration 066) |
| `agent_studio_*` | Agent Studio | Migrations 069-074: deployments, execution_logs, approvals, version_snapshots, webhooks |

**pgvector:**
- Extensão pgvector no PostgreSQL
- Tabela: `routing_cache_vectors`
- Modelo primário: OpenAI `text-embedding-3-small` (1536 dims); fallback: Gemini `text-embedding-004` (768 dims)
- Índice: ivfflat (confirmado em comentário de migration)
- Similaridade: cosine, threshold=0.85 configurável
- Uso: cache de roteamento (Tier 3) + RAG de candidatos (hybrid BM25+pgvector)

**Redis (AI Layer):**
- URL: `redis://localhost:6379/0` (env `REDIS_URL`)
- Fallback: dict in-memory quando Redis indisponível (dev/test)

| Chave Redis | Propósito | TTL |
|-------------|-----------|-----|
| `token_budget:{company_id}:{YYYY-MM}` | Quota mensal de tokens | 32 dias |
| `req_cost:{company_id}:{request_id}` | Custo por request | 7 dias |
| `candidate_list:{conv_id}` | Lista de candidatos em sessão | 30 min |
| `wizard_draft:{session_id}` | Progresso do wizard | 86400s |
| `cb_alert:{service_name}` | Circuit breaker dedup | 1h |
| `hitl:{pending_id}` | HITL pending actions | 24h |
| routing cache | domain_id + confidence | 3600s |

**Filas / Async (AI Layer):**
- Celery: `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` (default Redis)
- RabbitMQ (alternativo): `amqp://guest:guest@localhost:5672/` — exchange `rh_platform`, prefetch=1
- Backend configurável via `BROKER_BACKEND` env: `redis | rabbitmq | pubsub`

**LangGraph Checkpointing:**
- Produção: `PostgresSaver` via `libs/agents-core/lia_agents_core/checkpointer.py`
- Fallback: `MemorySaver` (dev/test)
- Thread ID = `session_id` (persistência por conversa)

---

### 5.2 Rails Backend — PostgreSQL

**Schema version:** `2025_07_14_142059`  
**Total migrations:** 85 (20250630 → 20250716)  
**[⚠] CRÍTICO:** schema.rb só reflete **8 tabelas**. As 77 migrations posteriores (20250716000020→20250716000051) criaram tabelas adicionais que existem no DB mas **não estão em schema.rb**.

#### Tabelas confirmadas em schema.rb

**accounts**
- `id` bigint PK, `name` string, `tenant` string (nome do schema Apartment, indexed), `staging_tenant` string, timestamps
- Cada account mapeia para um schema PostgreSQL separado gerenciado pelo ros-apartment

**users**
- `id` bigint PK, `email` string, `password_digest` string (bcrypt), `account_id` bigint FK, timestamps
- [⚠] Colunas `name`, `phone`, `role`, `activation_state`, `first_login_at`, `last_login_at`, `invited_at`, `onboarding_lia_override`, `lgpd_consent_at` referenciadas no código mas AUSENTES do schema.rb

**jobs**
- `id`, `title` string, `description` text, `user_id` FK, `account_id` FK, `provider` string, `provider_job_id` string
- `company_id` bigint [⚠] sem FK constraint, `published_date`, `application_deadline`, `is_remote` bool
- `city/state/country`, `job_url`, `friendly_badge/disabilities` bool (DEI flags), `workplace_type`
- Índice único em (`provider`, `provider_job_id`) para import idempotente

**candidates**
- `id`, `uid` (indexed), `name/surname`, `email` (unique), `secondary_email`
- `mobile_phone/phone/secondary_phone`, `linkedin/github/portfolio`
- `current_company/role_name/position_level`, `self_introduction/curriculum_text` text
- `date_birth` date, `gender` integer (enum), `nationality`, `marital_status` integer (enum), `cpf` (unique)
- Endereço completo: `street/number/district/zip/city/state/country/complement`
- Salários: `clt_expectation/pj_expectation/freelance_expectation/current_salary/desired_salary` float, `currency` default BRL
- `remote_work/mobility` bool, `source` string, `avatar_url/curriculum_pdf_url`
- [⚠] `account_id` não no schema mas modelo tem `belongs_to :account`

**applies**
- `candidate_id` FK, `job_id` FK, `selective_process_id` FK, `is_deleted` bool (soft-delete)

**selective_processes** (estágios do pipeline)
- `name`, `position` int (ordering), `status` int (enum: web_submission/screening/interview/rejected/hired)
- `job_id` FK, `uid`, `sub_status` jsonb
- 5 estágios padrão auto-criados via `after_create` callback em Job

**messages**
- `content` text, `entity` int (0=system, 1=user), `is_deleted` bool, `status` int
- `parent_message_id` bigint (threading), `reference_type/reference_id` (polymorphic)
- `account_id` FK, `metadata` jsonb (payload de resposta IA)
- `after_create_commit :publish_message_event` → publica no RabbitMQ em mensagens User

**permissions / roles / role_permissions / user_roles / user_permissions**
- RBAC completo modelado mas [✗] não aplicado em controllers

#### Tabelas em models mas NÃO em schema.rb (migrations 20250716+)

| Categoria | Modelos |
|-----------|---------|
| Compliance | `AdminAuditLog`, `AuditLog`, `AuditRetentionPolicy`, `AutomatedDecisionExplanation` |
| Billing/AI | `AiConsumption`, `AiCreditsBalance`, `Subscription`, `Invoice`, `PaymentMethod` |
| ATS Sync | `AtsCandidate`, `AtsConnection`, `AtsJobMapping`, `AtsSyncJob`, `AtsWebhookLog` |
| Pipeline | `ApplyStatus`, `ApprovalRequest`, `PendingApproval` |
| Candidatos | `CandidateAttachment`, `CandidateEducation`, `CandidateExperience` |
| Empresa | `ClientAccount`, `ClientUser`, `CompanyProfile`, `Department`, `CompanyHiringPolicy`, `CompensationPolicy`, `CultureValue`, `IdealProfile` |
| Screening | `BigFiveQuestion`, `BigFiveRoleProfile`, `TechnicalQuestion`, `TechnicalTestTemplate` |
| Entrevistas | `Interview`, `InterviewFeedback`, `InterviewNote`, `InterviewReminder`, `CalendarAvailability`, `SelfSchedulingLink`, `RescheduleHistory` |
| LGPD | `ConsentEvent`, `ConsentRecord`, `ConsentVersion`, `DataSubjectRequest`, `CompanyRetentionPolicy` |
| Comunicação | `ChatNotification`, `EmailLog`, `EmailTemplate`, `EmailTrackingEvent`, `Notification`, `NotificationPolicy` |
| Campanhas | `RecruitmentCampaign`, `CampaignStageEvent`, `RecruitmentSla`, `SlaViolation` |
| Talent Pool | `TalentPool`, `TalentPoolCandidate` |
| Automações | `RecruitmentAutomation`, `Goal`, `GoalTemplate` |
| Onboarding | `OnboardingMessage`, `OnboardingSession`, `UserOnboardingExtension` |
| Templates | `EmailTemplate`, `JobTemplate`, `PipelineTemplate`, `RecruitmentEmailTemplate`, `TemplateCategory`, `TemplateUsageLog` |
| Workforce | `HiringPlan`, `PlannedHeadcount`, `WorkforceEntry` |
| Auth | `MagicLink` |
| Webhooks | `Webhook`, `WebhookDeliveryLog`, `WebhookLog`, `WebhookRegistration` |
| Search | `SharedSearch`, `SharedSearchAccess`, `SharedSearchFeedback`, `SchemaSearchable` |
| Integrações | `IntegrationConnection`, `IntegrationProvider`, `IntegrationSyncLog`, `IntegrationWebhook` |
| Import | `ImportJob` |

---

## 6. API ENDPOINTS

### 6.1 AI Layer (FastAPI — Port 8001)

#### Chat / WebSocket
| Método | Rota | Arquivo | Propósito |
|--------|------|---------|-----------|
| WS | `/ws/chat/{user_id}` | `app/api/v1/chat.py:552` | WS legado |
| WS | `/ws/chat/{session_id}` | `app/api/v1/agent_chat_ws.py:386` | **WS primário** |
| WS | `/ws/jobs/{job_id}` | `app/api/v1/jobs_ws.py:28` | Progresso de job async |
| WS | `/twilio-voice/audio-stream` | `app/api/v1/twilio_voice.py:364` | Audio stream de voz |
| POST | `/chat/stream` | `app/api/v1/chat.py:819` | SSE streaming (fallback) |
| POST | `/chat/{session_id}/stream` | `app/api/v1/agent_chat_sse.py` | SSE agentes |

#### Webhooks Inbound
`POST /webhooks/merge/`, `POST /webhooks/mailgun/`, `POST /webhooks/job-status/`, `POST /webhooks/external/`

#### Automations
`app/api/v1/automation/`, `app/api/v1/automations.py`, `app/api/v1/automation_rules.py`, `app/api/v1/stage_transition_automation.py`

#### Microsoft / Calendar
`app/api/v1/microsoft_graph.py`, `app/api/v1/calendar.py`

#### Auth
`app/api/v1/workos.py` (WorkOS SSO)

#### Async Jobs
`app/api/v1/async_endpoints.py` — retorna task_id + `/ws/jobs/{job_id}` WS para progresso

#### Admin / Compliance
`app/api/v1/admin_bias_audit.py`, `app/api/v1/admin_compliance_fairness.py`, `app/api/v1/bias_audit.py`, `app/api/v1/fairness_reports.py`

#### Fine-tuning Export
`app/api/v1/finetuning_export.py`

#### Voice
`app/api/v1/twilio_voice.py`

#### Candidates
`POST /candidates/rag-search` — Hybrid BM25+pgvector semantic search

---

### 6.2 Rails Backend (Rails — Port 3000)

Todas as rotas sob `/v1`. ActionCable em `/cable`.

#### Auth
| Método | Rota | Notes |
|--------|------|-------|
| POST | `/v1/sessions` | Login email+password → JWT |
| GET | `/v1/me` | Perfil do usuário atual |
| POST | `/v1/logout` | Logout stateless (sem revogação) |
| GET | `/v1/auth/magic-link/verify` | [✗] Controller existe mas rota NÃO registrada em routes.rb |

#### Users namespace `/v1/users/`
CRUD completo para: `applies`, `jobs`, `selective_processes`, `candidates`, `users`, `messages`, `client_accounts`, `client_users`, `company_profiles`, `departments`, `email_templates`, `interviews`, `notifications`, `talent_pools`, `recruitment_campaigns`

Ações especiais talent_pools: `candidates`, `add_candidates`, `move_to_job`, `create_job_from_pool`
Ações especiais recruitment_campaigns: `advance_stage`, `complete_stage`, `add_checkpoint`

#### Onboarding [✗]
`OnboardingController` tem: `invite`, `status`, `progress`, `settings`, `consent` — **NENHUMA registrada em routes.rb**

#### Utility
`GET /up` (health), `GET /service-worker` (PWA), `GET /manifest` (PWA), `WS /cable` (ActionCable)

---

### 6.3 Frontend BFF Proxies (Next.js — Port 5000)

**478 route handlers** sob `src/app/api/`

| Área | Prefixo BFF | Destino |
|------|-------------|---------|
| Candidatos | `/api/backend-proxy/candidates/` | AI Layer |
| Vagas | `/api/backend-proxy/job-vacancies/` | AI Layer |
| Chat | `/api/backend-proxy/chat/` | AI Layer |
| Agent Studio | `/api/backend-proxy/agent-marketplace/`, `agent-templates/`, `agent-monitoring/` | AI Layer |
| Auth | `/api/backend-proxy/auth/` | AI Layer |
| Billing | `/api/backend-proxy/billing/` | AI Layer |
| Email Templates | `/api/backend-proxy/email-templates/` | AI Layer |
| Audit Logs | `/api/backend-proxy/audit-logs/` | AI Layer |
| ATS Integrations | `/api/backend-proxy/ats/` | AI Layer |
| Approvals | `/api/backend-proxy/approvals/`, `agent-approvals/` | AI Layer |
| WSI/Triagem | `/api/backend-proxy/wsi/` | AI Layer |
| Analytics | `/api/backend-proxy/analytics/` | AI Layer |
| Async Jobs | `/api/backend-proxy/async/jobs/` | AI Layer |
| Wizard | `/api/backend-proxy/wizard/*` → `BACKEND_URL/api/v1/wizard/*` | AI Layer |

**Rewrites em next.config.js:**
```
/api/v1/:path*              → BACKEND_URL/api/v1/:path*
/api/backend-proxy/wizard/* → BACKEND_URL/api/v1/wizard/*
/api/lia/chat/stream        → BACKEND_URL/api/v1/chat/stream
/ws/:path*                  → BACKEND_URL/ws/:path*
```

**[✗] Rails não conectado ao Frontend** — `NEXT_PUBLIC_RAILS_URL` está comentado no `.env.example`. Zero chamadas para Rails em código TypeScript/TSX.

---

## 7. FRONTEND

### 7.1 Stack Técnico
| Item | Valor |
|------|-------|
| Framework | Next.js 15 (App Router, `src/app`) |
| Linguagem | TypeScript (strict) |
| Porta | 5000 (dev + prod) |
| Package Manager | bun (bun.lock) |
| UI Library | shadcn/ui + Radix UI primitives |
| Estilo | Tailwind CSS + tokens customizados (`lia-*`, `wedo-*` CSS vars) |
| Rich Text | Tiptap v3 |
| Charts | Chart.js + Recharts |
| DnD | @dnd-kit (Kanban drag-and-drop) |
| Voice | @twilio/voice-sdk |
| i18n | next-intl (`src/i18n/request.ts`) |
| Auth | WorkOS SSO + JWT session cookie |
| Testing | Vitest (unit/hooks/components) + Playwright e2e |
| Monitoring | Sentry (`sentry.client.config.ts`, `sentry.server.config.ts`) |
| Componentes TSX | 1037 |

### 7.2 Páginas / Rotas (src/app/[locale]/)

| Rota | Propósito |
|------|-----------|
| `/chat` | Chat principal LIA AI |
| `/agent-studio` | Agent Studio (agentes, marketplace, digital twins) |
| `/jobs`, `/jobs/[id]` | Lista de vagas + Kanban pipeline |
| `/funil-de-talentos`, `/funil-de-talentos/candidato/[id]` | Funil de talentos + detalhe candidato |
| `/bancos-de-talentos` | Talent pools |
| `/tasks` | Gestão de tarefas |
| `/configuracoes`, `/configuracoes/ai-credits` | Configurações + créditos IA |
| `/triagem/[token]` | **Triagem WSI candidato** (público, sem auth) |
| `/portal/data-request/[token]` | Portal LGPD — direito de acesso |
| `/vagas/[slug]` | Página pública de vaga |
| `/teams-tab`, `/teams-tab/candidatos`, `/teams-tab/vagas` | Microsoft Teams embed |
| `/shared/[token]` | Link compartilhado de relatório |
| `/trust`, `/privacidade` | Compliance / privacidade |
| `/login`, `/register`, `/forgot-password`, `/reset-password` | Auth |
| `/accept-invitation`, `/aceitar-convite` | Convite de equipe |
| `/upgrade` | Plano / billing |

### 7.3 Interface de Chat — Arquitetura

**Dual-transport model (WebSocket primário, SSE fallback):**
```
LiaFloatProvider (Context)
  └── useLiaChatConnection (facade)
        ├── useChatSocket       ← roteamento de eventos (HITL, panel_update, bg_tasks)
        │     └── useAgentStreaming
        │           └── useChatTransport  ← raw WS / SSE transport
        └── useChatMessages     ← envio/recebimento/histórico de mensagens
```

**Transporte (src/hooks/chat/useChatTransport.ts):**
- Primário: WebSocket em `NEXT_PUBLIC_WS_URL/ws/chat/{sessionId}`
- Fallback: SSE via `POST /api/v1/chat/{sessionId}/stream` (após 3 falhas WS)
- Auto-reconnect: backoff exponencial, máx 3 tentativas, depois SSE permanente
- Auth: token WS obtido de `/api/auth/ws-token`

**Tipos de eventos tratados (src/hooks/chat/useChatSocket.ts):**

| Evento | Handler |
|--------|---------|
| `token` | Streaming real-time `setTokens()` |
| `token_done` | Marca streaming completo |
| `message` | Resposta completa final |
| `thinking` | Estado "pensando" + coleta de steps |
| `plan_progress` | Rastreia execução de plano multi-step |
| `approval_required` (HITL) | Define `hitlPending` → renderiza `HITLConfirmCard` |
| `panel_update` | Roteia para `onPanelUpdate` callback |
| `background_task_update` | Atualiza array `backgroundTasks` |
| `fairness_warnings` | Define banner de aviso de fairness |

**Entry points do chat:**
| Componente | Arquivo | Contexto |
|-----------|---------|---------|
| Página completa | `src/components/pages/chat-page/` | Rota `/chat` |
| UnifiedChat (atual) | `src/components/unified-chat/UnifiedChat.tsx` | Arquitetura Phase 6 |
| InlineChatBridge | `src/components/unified-chat/InlineChatBridge.tsx` | Substitui LiaChatPanel |
| Onboarding | `src/components/onboarding/OnboardingChatPage.tsx` | First-use |
| LiaChatPanel | `src/components/lia-float/LiaChatPanel.tsx` | [@deprecated] |
| KanbanSuperChatSection | `src/components/pages/job-kanban/KanbanSuperChatSection.tsx` | [@deprecated] |

### 7.4 State Management — Zustand Stores

**Arquivo base:** `src/stores/`

| Store | Arquivo | Persistido | Propósito |
|-------|---------|-----------|-----------|
| `useAuthStore` | `auth-store.ts` | Não | Auth state, login/logout, SSO |
| `useChatStateStore` | `chat-state-store.ts` | Sim | IDs de conversa, snapshots wizard |
| `useKanbanStore` | `kanban-store.ts` | Não | View mode, seleções, candidatos por coluna |
| `useWizardStore` | `wizard-store.ts` | Sim | Rascunho wizard de vaga |
| `useCandidatesStore` | `candidates-store.ts` | Não | Lista, filtros, seleções |
| `useOnboardingStore` | `onboarding-store.ts` | Não | Progresso de onboarding |
| `useAgentStudioStore` | `agent-studio-store.ts` | Não | Estado Agent Studio |
| `useTriagemStore` | `triagem-store.ts` | Não | Estado sessão triagem WSI |

**Reset pattern:** Todos os stores registram `resetStore` via `registerStoreReset()` em `auth-store.ts`. No logout, todos resetam atomicamente.

**Global context:** `LiaFloatProvider` (`src/contexts/lia-float-context.tsx`) — envolve o app inteiro; gerencia lifecycle de chat, context switching (`general`, `job_chat`, `talent_chat`, `kanban_chat`, `candidates_chat`), painéis dinâmicos, split view.

### 7.5 Ações IA → Reflexo na UI

```
Python AI Agent (evento WS/SSE)
  → useChatTransport.handleParsedEvent()
  → useChatSocket.handleEvent()
      ├── "panel_update"           → onPanelUpdateRef.current(event)
      │     → LiaFloatProvider.openDynamicPanel() [⚠ wiring não confirmado explicitamente]
      ├── "background_task_update" → setBackgroundTasks()
      │     → LiaChatPanel: <BackgroundAgentsStatus> + <BackgroundTaskNotification>
      ├── "approval_required"      → setHitlPending()
      │     → <HITLConfirmCard> inline no chat
      ├── "plan_progress"          → setPlanProgressSteps() / setActivePlanId()
      ├── "thinking"               → setIsThinking() + setThinkingSteps()
      ├── "fairness_warnings"      → <FairnessWarningBanner>
      └── "message"               → appenda em messages[]
```

### 7.6 Autenticação Frontend
| Método | Arquivos | Notas |
|--------|---------|-------|
| WorkOS SSO | `src/app/api/auth/workos/callback/route.ts`, `sso/route.ts` | SAML/OIDC via WorkOS SDK |
| JWT (email/pwd) | `src/app/api/auth/session/route.ts` | JWT customizado, validado server-side |
| Magic Link | `src/app/api/auth/magic-link/route.ts` | One-time login links |
| WS Token | `src/app/api/auth/ws-token/route.ts` | Short-lived token para auth WebSocket |
| Dev auto-login | `src/app/api/auth/auto-login/route.ts` | Só em `NODE_ENV=development` |

**Sessão:** Cookie assinado (`workos_session`) via `jose` JWT, TTL 7 dias.

---

## 8. CAMADAS CROSS-CUTTING

### 8.1 Fairness / Anti-Bias [✓]
**Arquivo principal:** `app/shared/compliance/fairness_guard.py`

**FairnessGuard — 3 camadas:**

**Camada 1 — Bias Explícito (síncrona, pré-LLM):**
- Sets de padrões: `DISCRIMINATORY_CATEGORIES` dict com regex compiladas para:
  - `genero`, `raca_etnia`, `idade` — padrões PT+EN (15+ regex para idade incluindo edge cases)
  - Retorna mensagem educativa + citação legal (CLT, LGPD, Lei 9.029/95, Lei 7.716/89)
- Chamado no pre-check do orchestrator; **bloqueia** queries correspondentes

**Camada 2 — Termos de Bias Implícito (soft warnings):**
- `IMPLICIT_BIAS_TERMS` dict — 40+ termos PT + 35+ termos EN
- Normalização via `unicodedata.NFD` antes do match
- Categorias proxy: localização socioeconômica, elitismo acadêmico, religião, deficiência, status familiar
- Retorna `soft_warnings` — não bloqueado, mas flagged e appendado à resposta

**Camada 3 — Fairness Semântica via LLM:**
- `check_semantic()` / `check_with_layer3()` / `check_with_sector()`
- Setor-aware: L3 habilitado para `saude`, `rpo`; desabilitado para `varejo`, `logistica`
- Chamada LLM async com contexto específico de setor

**C3b Layer** (`app/shared/compliance/c3b_layer.py`):
- Pré-compliance: PII strip → FairnessGuard L3 (para `_FAIRNESS_DOMAINS`)
- Pós-compliance: FactChecker + AuditService log
- Feature flag: `LIA_DISABLE_C3B=1` (passthrough para testes)
- Domínios de fairness: recruitment, talent_ranking, talent_pool, job_scoring, performance, salary_benchmark, job_management, candidate_evaluation

**RAG Search fairness:** `_FAIRNESS_MAX_SINGLE_GENDER_RATIO = 0.70` — top-10 resultados devem ter ≤ 70% de um único gênero (`rag_pipeline_service.py`)

**Admin UI:** `app/api/v1/admin_bias_audit.py`, `app/api/v1/admin_compliance_fairness.py` (estende FairnessComplianceHub existente em Configurações — não cria nova página)

### 8.2 LGPD / Privacidade [✓]
**Arquivos:** `app/domains/lgpd/`, `app/domains/consent/`, `app/domains/data_subject/`

| Serviço | Propósito |
|---------|-----------|
| `consent_checker_service.py` | Valida consentimento antes de processar dados |
| `lgpd_cleanup_service.py` | Deleção e anonimização de dados |
| `dsr_export_service.py` | Exportações DSR (Art. 18 LGPD) |
| `granular_consent_service.py` | Rastreamento granular de consentimento |
| `drift_alert_service.py` | Monitora compliance de consentimento ao longo do tempo |

**PII Masking (2 camadas):**
1. **Camada de logging** (`app/shared/pii_masking.py`): `PIIMaskingFilter` em root logger + todos os handlers. Padrões: CPF, email, telefone BR, nome. `install_global_pii_masking()` no startup.
2. **Camada de prompt LLM** (`strip_pii_for_llm_prompt()`): strips PII antes de enviar ao LLM. `LLM_PROMPT_PII_STRIPPING_ENABLED=true`. Padrões: ano de formatura (inferência de idade), idade explícita, CPF, email, telefone.
3. **Nível de agente** (`LangGraphReActBase._sanitize_messages_pii()`): auto-strip PII de HumanMessage/AIMessage antes do call LLM.

**Quasi-identificadores** (LGPD Art. 12): ano de formatura → inferência de idade, referências de idade explícitas — stripped na camada de prompt.

**Retenção de dados:**
- Logs de scoring/aprovação/rejeição: 730 dias
- Logs de messaging: 1825 dias
- Logs de scheduling: 365 dias
- Avaliações RAGAS: 90 dias

**Criptografia:** Migration `060_encrypt_pii_fields_and_ttl_indexes.py` — criptografia a nível de campo + índices TTL para expiração automática.

**Rails Backend LGPD:** Modelos `ConsentEvent`, `ConsentRecord`, `ConsentVersion`, `DataSubjectRequest`, `CompanyRetentionPolicy` existem mas detalhes de implementação não inspecionados.

### 8.3 Compliance / Governança [✓]
**Audit Service** (`app/shared/compliance/audit_service.py`): Loga cada decisão IA com: company_id, agent_name, decision_type, action, decision, reasoning list, criteria_used, criteria_ignored (anti-bias), score, confidence, human_review_required. `PROTECTED_CRITERIA`: age, gender, ethnicity, marital_status, photo, institution, address, religion, disability, cv_gaps.

**AuditCallback** (`libs/audit/lia_audit/audit_callback.py`): LangChain callback injetado em todo `create_react_agent` — loga todos LLM calls, tool invocations, chain starts/ends. Estima custo via `_estimate_cost()`.

### 8.4 Segurança [✓]
**Prompt Injection Guard** (`app/shared/robustness/security_patterns.py`, `app/shared/prompt_injection.py`):
- 20+ threat patterns em 10 categorias: `JAILBREAK`, `DATA_EXFILTRATION`, `BIAS_ELICITATION`, `SCORE_MANIPULATION`, `PRIVILEGE_ESCALATION`, `PII_EXTRACTION`, `FAIRNESS_BYPASS`, `SYSTEM_OVERRIDE`, `DELIMITER_INJECTION`, `ROLE_MANIPULATION`
- Níveis: NONE < LOW < MEDIUM < HIGH < CRITICAL (confidence 0.92-0.95 para CRITICAL)
- Aplicado em: WebSocket handler, SSE streaming, MainOrchestrator pre-check

**JWT:**
- AI Layer: `SECRET_KEY` + `ALGORITHM=HS256` (local), WorkOS SSO, `RAILS_JWT_SECRET_KEY` (cross-service)
- Rails Backend: JWT customizado, 24h expiry, sem blacklist/revogação [⚠]

**Isolamento de Tenant:**
- AI Layer: RLS (migration 068: `068_rls_deny_by_default.py`) + `company_id` em todas as queries
- Rails: `TenantScoped` concern (não aplicado uniformemente) [⚠]

**CORS:** Rails: `rack-cors` gem. AI Layer: FastAPI CORS middleware.

**[⚠] Frontend security gap:** `PATCH /candidates/{id}/stage` não encaminha headers de auth (apenas `Content-Type: application/json`).

### 8.5 Logging / Observabilidade [✓]
**Tracing** (`app/shared/tracing.py`):
- OpenTelemetry (OTLP export quando `OTEL_EXPORTER_OTLP_ENDPOINT` definido; ex: Jaeger porta 4318)
- Fallback: `LightweightTracer` interno (zero deps)
- Cobertura de spans: CascadedRouter 8 tiers, RAG pipeline, EmbeddingService, HITL, Celery tasks, DLQ, LearningLoop, WebSocket handle, ReAct loop `_act()`

**LangSmith:** flag `LANGCHAIN_TRACING_V2`; projeto `lia-agent-system`

**Logs estruturados** (`app/shared/structured_logging.py`): JSON com filtro PII masking

**Model Drift Detection** (`app/domains/ai/services/model_drift_service.py`):
- 4 triggers (janela deslizante de 7 dias vs 7 dias anteriores):
  - `score_drift`: variação de média WSI > 0.5
  - `approval_drift`: variação de taxa de aprovação > 10 pp
  - `cost_drift`: variação de custo > 20%
  - `latency_drift`: variação P95 latência > 50%
- Níveis: ok / warning / critical

**RAGAS Evaluation** (`app/domains/ai/services/ragas_evaluation_service.py`):
- Métricas: faithfulness, answer_relevancy, context_precision, context_recall
- Threshold de qualidade: 0.70 overall score
- Celery batch task: diário 03h UTC
- Fail-safe: falha de avaliação NÃO afeta operação do agente

**Sentry:** `SENTRY_DSN` config (AI Layer + Frontend)

**[⚠] Prometheus removido (Task #138):** `cascaded_router.py:_get_metrics()` retorna `None, None, None`. Métricas de tier do router não são mais exportadas.

### 8.6 Multi-tenancy [✓/⚠]

| Aspecto | AI Layer | Rails Backend |
|---------|---------|---------------|
| Chave de tenant | `company_id` (UUID) | `account_id` (bigint) + Apartment schema |
| Isolamento DB | RLS PostgreSQL (migration 068) + WHERE company_id | ros-apartment (schema per account) + account_id FK |
| Isolamento LLM | `TenantProviderRegistry` por company_id | N/A |
| Isolamento Redis | Key prefix `{company_id}` | N/A |
| Consistência | [✓] RLS + all queries scoped | [⚠] `scope_to_tenant` não aplicado uniformemente |
| Multi-tenant search | N/A | Elasticsearch indices per tenant: `{tenant}_{model}_{env}` |

---

## 9. CONCEITOS DE PLATAFORMA

### 9.1 LLM Factory [✓]
**Arquivos:** `app/shared/providers/llm_factory.py`, `libs/config/lia_config/config.py`

**Arquitetura em 2 camadas:**
1. `LLMProviderFactory` — registry global a nível de classe (backward compat, deprecated para uso multi-tenant)
2. `ProviderContainer` — container DI por tenant, isolado por `TenantProviderRegistry`

**`get_provider_for_tenant(company_id)`** — retorna container escopado por tenant

**Ordem de fallback de provider:** `gemini → claude → openai` (configurável `FALLBACK_ORDER`)

**Modelos:**
| Config | Valor | Uso |
|--------|-------|-----|
| `LLM_DEFAULT_PROVIDER` | `"gemini"` (Gemini 2.5 Flash) | Provider padrão |
| `LLM_PRIMARY_MODEL` | `"claude-sonnet-4-6"` | Execução de agentes |
| `LLM_FAST_MODEL` | `"gemini-2.5-flash"` | Roteamento, tier barato |
| `LLM_POWERFUL_MODEL` | `"claude-opus-4-6"` | Tier final do cascade |
| `LLM_AGENT_MODEL` | `"claude-sonnet-4-6"` | Execução ReAct |

**Budget check:** `check_request_budget_before_llm()` chamado antes de QUALQUER invocação LLM (enforcement a nível de factory).

**[⚠] `LLMProviderFactory.generate_with_fallback()` deprecated mas ainda chamável** — emite `DeprecationWarning`, usa estado global compartilhado, bypassa isolamento por tenant.

### 9.2 Modelo de Tenant

**AI Layer:**
- `company_id` (UUID/string) é a chave universal de tenant
- `TenantProviderRegistry`: cada tenant pode ter API keys customizadas + seleção de provider
- Budget: Redis `token_budget:{company_id}:{YYYY-MM}`
- Config LLM por tenant: tabela `tenant_llm_configs` (migration 058)
- Gating de módulos: `app/shared/module_gating.py`, tabela `company_modules` (migration 066)

**Rails Backend:**
- `account_id` (bigint) + Apartment PostgreSQL schema por conta
- `AccountScopable` concern (ApplicationRecord): auto-assign `account_id` no create
- `TenantScoped` controller concern: `scope_to_tenant(relation)`, `verify_tenant!(record)`
- [⚠] Não aplicado uniformemente: Jobs, Candidates, Applies, SelectiveProcesses, Interviews sem `scope_to_tenant`

**Mapeamento de tenant entre camadas:**
- [?] Relação entre `company_id` (AI Layer) e `account_id` (Rails) não evidenciada via FK. Provavelmente mapeada via mensagem RabbitMQ payload ou convenção de string.

### 9.3 Ciclo de Vida de Pessoas (Person Lifecycle) [?]

| Estágio | AI Layer | Rails Backend |
|---------|---------|---------------|
| Candidato | Tabela `candidates`, domínio sourcing, pipeline | Modelo `Candidate`, `Apply`, `SelectiveProcess` |
| Talent Pool | Domínio `talent_pool`, `search_talent_pool` tool | Modelos `TalentPool`, `TalentPoolCandidate` |
| Contratado | Não evidenciado explicitamente | `SelectiveProcess.status = hired` |
| Funcionário | [✗] Não encontrado | [?] Pode estar em migrations não inspecionadas |
| Alumni | [✗] Não encontrado | [✗] Não encontrado |

Pipeline formal candidate→hired→employee→alumni não está documentado em nenhuma camada. Pós-contratação provável no Rails mas sem confirmação.

### 9.4 Agent Studio [✓]
**Arquivos:** `app/domains/agent_studio/`, `app/domains/agent_studio/custom_agent_runtime.py`

- Tenants criam agentes customizados com: name, system_prompt, allowed_tools, domain, max_steps, temperature, model_override
- Runtime: `CustomAgentRuntime` estende `LangGraphReActBase + EnhancedAgentMixin`
- Tool pools: autonomous tools (40+) + domain-specific filtradas por allowed list
- Marketplace: `browse_marketplace`, `publish_to_marketplace`, `install_from_marketplace`
- DB tables (migrations 069-074): `agent_studio_parity_fields`, `agent_deployments`, `agent_execution_logs`, `agent_approvals`, `agent_version_snapshots`, `webhooks`
- Frontend: `src/components/pages-agent-studio/AgentStudioPage.tsx` — Tabs: CustomAgentsTab, MarketplaceTab, TwinsList, MultiStrategySearchPanel

### 9.5 Template Engine [✓]
**Arquivos:** `app/prompts/templates.py`, `app/prompts/__init__.py` (PromptLoader)

- Prompts por domínio: `app/prompts/domains/`
- CoT (Chain-of-Thought): `app/prompts/cot.py`
- Version registry: `app/domains/ai/services/prompt_version_registry.py` — rastreia versões com hashes
- A/B experiments: `app/shared/prompt_experiment.py` — seleção de variante por hash de user_id, pesos configuráveis
- YAML experiments: `app/prompts/experiments/cascade_router_system_prompt.yaml`

### 9.6 Automações / Triggers [✓]
**Arquivos:** `app/api/v1/automation/`, `app/api/v1/automations.py`, `app/api/v1/automation_rules.py`, `app/api/v1/stage_transition_automation.py`

- Event-driven: `app/api/v1/automation/event_handlers/` — `handlers_interview.py`, `handlers_lifecycle.py`
- Tipos de trigger: `app/api/v1/automation/triggers.py`
- Celery tasks: RAGAS batch (diário 03h UTC), learning loop, model drift analysis
- Rails: `RecruitmentAutomation` model existe; Sidekiq para `MessageJob`

### 9.7 Modelos ML Além de LLM [⚠]
- **WSI Scoring:** `wsi_deterministic_scorer.py` — algoritmo rule-based usando Bloom taxonomy + Dreyfus model + Big Five dimensions. NÃO é ML — algoritmo determinístico.
- **BARS Evaluator:** `app/shared/bars_evaluator.py` — Behaviorally Anchored Rating Scale
- **Market Benchmark:** SerpAPI + estimativa LLM — sem modelo treinado
- **Score normalization:** `score_normalization_service.py` — normalização matemática
- **Seniority resolver:** `seniority_resolver.py` — rule-based
- [✗] Nenhum modelo ML treinado (sklearn, PyTorch, TensorFlow, XGBoost) encontrado em produção

---

## 10. ML E APRENDIZADO

### 10.1 Modelos Treinados (não-LLM) [✗]
Nenhum modelo ML treinado encontrado. Todo scoring é LLM-based ou rule-based.

### 10.2 Feedback Loops [✓]
**Learning Loop Service** (`app/shared/learning/learning_loop_service.py`):
- **Captura:** Silenciosa — registra todas sugestões e outcomes (accepted/modified/rejected/ignored)
- **Padrões:** 7 tipos — SALARY_PREFERENCE, SKILL_PREFERENCE, BENEFIT_PREFERENCE, WORK_MODEL_PREFERENCE, SCREENING_PREFERENCE, JD_STYLE_PREFERENCE, SOURCE_TRUST
- **Thresholds de confiança:** high ≥ 20 amostras, medium ≥ 10, low ≥ 5
- **Promote/demote:** aceitação ≥ 75% → promove padrão; ≤ 25% → demove
- **Operação invisível:** captura sem exigir feedback explícito na UI

**Fine-tuning Export** (`app/shared/learning/finetuning_export.py`, `app/api/v1/finetuning_export.py`):
- Exporta dados de interação rotulados para potencial fine-tuning futuro

**LearningExtractor** (`libs/agents-core/lia_agents_core/learning_extractor.py`):
- Hooks pré/pós-loop em `LangGraphReActBase._process_langgraph()` para captura a nível de agente

### 10.3 Personalização [✓]
- **Por tenant:** `user_agent_preference_service.py` — rastreia preferências de recruiter por tipo de agente
- **Por vaga:** Padrões de aprendizado por `job_id` (campo `FeedbackCapture`)
- **Por departamento/localização/senioridade/papel:** Dimensões de filtro em `FeedbackCapture`
- **A/B testing por tenant:** `app/shared/learning/ab_testing_service.py`
- **Prompt A/B experiments:** Variantes de system prompt do router selecionadas por hash de `user_id`

### 10.4 RAGAS (Qualidade de Agentes) [✓]
**Arquivo:** `app/domains/ai/services/ragas_evaluation_service.py`

- Métricas: faithfulness, answer_relevancy, context_precision, context_recall
- Threshold: 0.70 overall score
- Celery batch: diário 03h UTC
- Storage: tabela `agent_ragas_evaluations`, 90-day retention
- Fail-safe: falha de avaliação NÃO afeta operação do agente

---

## 11. INTEGRAÇÃO ENTRE CAMADAS

### 11.1 Frontend ↔ AI Layer

| Canal | Protocolo | Direção | Status |
|-------|-----------|---------|--------|
| Chat principal | WebSocket `/ws/chat/{sessionId}` | Bidirecional | [✓] |
| Chat fallback | SSE `POST /chat/{sessionId}/stream` | Servidor→cliente | [✓] |
| REST API | HTTP via BFF (478 routes) | Frontend→AI | [✓] |
| Async job status | WebSocket `/ws/jobs/{job_id}` | AI→Frontend | [✓] |

**BFF (Backend For Frontend):**
- Todas as chamadas do browser vão para Next.js Route Handlers
- Next.js encaminha para `BACKEND_URL` (AI FastAPI, porta 8001) server-side
- `BACKEND_URL` nunca exposto ao browser
- Auth headers: [⚠] não encaminhados uniformemente em todos os 478 proxy routes

### 11.2 AI Layer ↔ Rails Backend

**Mecanismo primário: RabbitMQ (AMQP) via Bunny gem (Rails) e `pika`/Celery (Python)**

| Evento | Publisher | Exchange | Routing Key | Consumer |
|--------|-----------|---------|-------------|---------|
| Nova mensagem de user | Rails (`MessageService::EventPublisher`) | `messages_exchange` | `messages_created` | Python AI (processa com LLM) |
| Resposta IA processada | Python AI | `messages_exchange` | `messages_processed` | Rails (`MessageWorker`) |
| Import de vaga | Python AI | — | `jobs_import` | Rails (`JobImportWorker`) |
| Evento de onboarding | Rails (`OnboardingEventPublisher`) | `messages_exchange` | `onboarding_events` | Python AI |

**Payload RabbitMQ (Rails → Python):**
```json
{ "event_type": "...", "payload": {}, "timestamp": "ISO8601", "source": "rails" }
```

**[✗] Sem chamadas HTTP diretas Rails↔Python** — Sem Faraday, Net::HTTP, RestClient ou HTTParty do Rails para Python. Desacoplamento total via message broker.

**[⚠] Connection-per-publish (Rails):** `MessageService::EventPublisher` e `OnboardingEventPublisher` abrem nova conexão TCP Bunny por chamada de publish. Sem connection pooling — risco de latência e esgotamento de conexões sob carga.

### 11.3 Frontend ↔ Rails Backend

**[✗] NÃO CONECTADO.** `NEXT_PUBLIC_RAILS_URL` está comentado no `.env.example`. Zero código TypeScript/TSX chamando Rails diretamente. Todo o tráfego frontend vai exclusivamente para o AI Layer Python.

**Implicação:** O Rails recebe eventos apenas via RabbitMQ (publicados pelo Python AI). O frontend nunca acessa o Rails diretamente. A UI só vê dados que o Python AI reexpõe.

### 11.4 ActionCable (Rails → Frontend via WebSocket)
- Canal `MessageChannel` (`messages_user_#{user.id}`): `MessageWorker` transmite respostas IA para o browser
- Canal `WorkflowChannel` (`workflow_user_#{user.id}`): `RecruitmentCampaign#broadcast_update!` em mudanças de estágio
- Auth: JWT via query param `?auth_token=` no handshake WebSocket

**[?] Gap:** ActionCable Rails e WebSocket `/ws/chat/` Python AI são dois sistemas de WebSocket paralelos. O browser pode estar conectado a ambos simultaneamente — não documentado no frontend audit.

### 11.5 Gaps Críticos de Integração

| Gap | Severidade | Descrição |
|-----|-----------|-----------|
| Rails não acessível pelo Frontend | [⚠] ALTO | Frontend não conectado ao Rails. Migração planejada mas não implementada. |
| Mapeamento tenant company_id vs account_id | [⚠] ALTO | Sem FK cruzada entre DBs. Sincronização implícita via payload RabbitMQ. |
| Connection-per-publish RabbitMQ | [⚠] ALTO | Abre TCP por publicação — não escalável. |
| Dois sistemas WebSocket paralelos | [⚠] MÉDIO | Python AI WS + Rails ActionCable — sem orquestração unificada. |
| schema.rb Rails desatualizado | [⚠] ALTO | 77 migrations não refletidas — base de dados real é desconhecida sem `db:schema:dump`. |

---

## 12. GAPS CRÍTICOS CONSOLIDADOS

Consolidados de todas as três camadas, ranqueados por severidade.

### CRÍTICO (bloqueia funcionalidade ou é risco de segurança imediato)

| ID | Camada | Gap | Evidência |
|----|--------|-----|-----------|
| C1 | Rails | **schema.rb desatualizado** — apenas 8 tabelas refletidas; 77 migrations adicionais criam tabelas no DB mas não em schema.rb | `ats-api-copia/db/schema.rb` (schema version `2025_07_14_142059`) |
| C2 | Rails | **Rota MagicLink não registrada** — `v1/auth/magic_links#verify` existe mas não está em routes.rb. Onboarding passwordless quebrado. | `ats-api-copia/config/routes.rb` |
| C3 | Rails | **Rotas Onboarding não registradas** — `invite`, `status`, `progress`, `settings`, `consent` existem no controller mas sem rota | `ats-api-copia/app/controllers/onboarding_controller.rb` |
| C4 | Rails | **Autorização não aplicada** — RBAC modelado mas `User#can?()` nunca chamado em controllers. `only_admin` referencia coluna `is_admin` ausente no schema. Qualquer usuário autenticado pode executar qualquer CRUD. | Todos controllers em `ats-api-copia/app/controllers/` |
| C5 | Rails | **JWT logout sem revogação** — tokens válidos por 24h após logout. Sem blacklist no Redis. | `ats-api-copia/app/controllers/v1/sessions_controller.rb` |
| C6 | AI Layer | **WSManager não distribuído** — `app/shared/websocket/ws_manager.py:ws_manager` é singleton in-process. Com múltiplos workers Uvicorn, `panel_update` do worker A não alcança cliente conectado no worker B. | `app/shared/websocket/ws_manager.py` |
| C7 | AI Layer | **HITL DB best-effort** — persistência DB para HITL pending actions é "best-effort" (comentário explícito). Redis TTL 24h é primário. Falha do Redis durante aprovação crítica → estado perdido. | `app/domains/cv_screening/services/hitl_service.py` |

### ALTO (degradação funcional ou risco de vazamento de dados)

| ID | Camada | Gap | Evidência |
|----|--------|-----|-----------|
| H1 | Rails | **Isolamento de tenant inconsistente** — `scope_to_tenant` aplicado em TalentPools e RecruitmentCampaigns mas NÃO em Jobs, Candidates, Applies, SelectiveProcesses, Interviews → vazamento de dados entre contas | `ats-api-copia/app/controllers/users/` |
| H2 | Rails | **RabbitMQ connection-per-publish** — `MessageService::EventPublisher` + `OnboardingEventPublisher` abrem nova conexão TCP por chamada. Sem connection pool → latência e esgotamento sob carga | `ats-api-copia/app/services/message_service/event_publisher.rb` |
| H3 | Rails | **`JobImportWorker` hardcoded user_id: 1, account_id: 1** — Jobs importados de fontes externas sempre atribuídos a user/account fixo. Import cross-tenant quebrado. | `ats-api-copia/app/workers/job_import_worker.rb` |
| H4 | Rails | **`company_id` em jobs sem FK constraint** — referencia ClientAccount/CompanyProfile mas sem constraint → registros órfãos | `ats-api-copia/db/schema.rb` |
| H5 | Integração | **Frontend não conectado ao Rails** — `NEXT_PUBLIC_RAILS_URL` comentado. Todo tráfego frontend vai apenas para Python AI. Migração planejada não implementada. | `plataforma-lia/.env.example`, `plataforma-lia/next.config.js` |
| H6 | Integração | **Mapeamento company_id ↔ account_id não documentado** — dois DBs PostgreSQL independentes; sincronização apenas via RabbitMQ payload; sem FK cruzada ou tabela de mapeamento explícita | P01_AI_LAYER.md §6.2, P01_BACKEND.md §multi-tenancy |
| H7 | AI Layer | **`LLMProviderFactory.generate_with_fallback()` deprecated mas ativo** — emite `DeprecationWarning` em runtime; usa estado global compartilhado; bypassa isolamento por tenant | `app/shared/providers/llm_factory.py` |
| H8 | Frontend | **Auth headers não encaminhados uniformemente** — 478 proxy routes: alguns usam `getAuthHeaders()`, outros enviam sem auth. `PATCH /candidates/{id}/stage` verificado sem header de auth. | `plataforma-lia/src/app/api/backend-proxy/candidates/[id]/stage/route.ts` |

### MÉDIO (degradação de qualidade, UX ou observabilidade)

| ID | Camada | Gap | Evidência |
|----|--------|-----|-----------|
| M1 | Rails | **Cobertura de testes ~10%** — 12 spec files para 95+ models, 24+ controllers, 6 services, 2 workers. Zero testes para auth, multi-tenancy, onboarding, campanhas, talent pools, mailers. | `ats-api-copia/spec/` |
| M2 | Rails | **Email mailer sender padrão** — `from@example.com` em `ApplicationMailer`. Entrega em produção vai falhar sem config SMTP/Mailgun. | `ats-api-copia/app/mailers/application_mailer.rb` |
| M3 | Rails | **Webhook outbound não implementado** — Modelos (`Webhook`, `WebhookDeliveryLog`) existem mas nenhum serviço ou job executa entrega | `ats-api-copia/app/models/webhook.rb` |
| M4 | Rails | **Sem rate limiting** — Sem rack-attack ou similar. Combinado com connection-per-publish, cria superfície DoS. | Gemfile |
| M5 | AI Layer | **Prometheus removido (Task #138)** — `cascaded_router.py:_get_metrics()` retorna `None, None, None`. Métricas de tier do router (hit rates, latências, confiança) não exportadas. OTEL existe mas dashboards Prometheus quebrados. | `app/orchestrator/cascaded_router.py` |
| M6 | AI Layer | **FairnessGuard L3 não habilitado em todos os domínios** — Só para `saude`, `rpo`. Domínios `varejo`, `logistica` sem verificação semântica. | `app/shared/compliance/fairness_guard.py` |
| M7 | AI Layer | **Digital Twin RAG few-shot não verificado** — Estrutura do domínio confirmada; profundidade do RAG few-shot não inspecionada. | `app/domains/digital_twin/domain.py` |
| M8 | AI Layer | **SerpAPI opcional com fallback LLM** — Sem chave SERP_API_KEY, benchmark de salários usa estimativa LLM (risco de qualidade para dados de remuneração). | `app/domains/analytics/services/market_benchmark_service.py:23` |
| M9 | Frontend | **`panel_update` → `openDynamicPanel()` wiring não confirmado** — Evento recebido e despachado mas consumidor-side não encontrado em ponto único claro. Provável em `useLiaChatPanelState.ts`. | `plataforma-lia/src/hooks/chat/useChatSocket.ts` |
| M10 | Frontend | **`backgroundTasks` em estado local do hook** — Estado em `useChatSocket`, não no Zustand. Se LIA panel desmontar, tasks em progresso são perdidas. | `plataforma-lia/src/hooks/chat/useChatSocket.ts` |
| M11 | Frontend | **Duas arquiteturas de chat coexistindo** — `KanbanSuperChatSection` e `LiaChatPanel` com `@deprecated` — migração para `UnifiedChat` via `InlineChatBridge` em andamento mas incompleta. | `plataforma-lia/src/components/` |
| M12 | Integração | **Dois sistemas WebSocket paralelos** — Python AI WS e Rails ActionCable. Frontend pode estar conectado a ambos simultaneamente sem orquestração documentada. | P01_AI_LAYER.md §8.1, P01_BACKEND.md §ActionCable |

### BAIXO (dívida técnica ou risco futuro)

| ID | Camada | Gap | Evidência |
|----|--------|-----|-----------|
| L1 | Rails | **`data_applies_days/weeks/months`** — referenciam gem `groupdate` não declarada no Gemfile | `ats-api-copia/app/models/` |
| L2 | Rails | **Elasticsearch index lifecycle não automatizado** — criação e re-indexação não automatizadas após migrations | Gemfile (searchkick) |
| L3 | Rails | **Duas stacks de background jobs** — Sidekiq (ActiveJob) + Sneakers (RabbitMQ). Requer dois processos separados; sem monitoramento unificado. | `ats-api-copia/Gemfile` |
| L4 | Rails | **Sem Swagger/OpenAPI** — `rswag-specs` no Gemfile mas sem arquivos de spec. API completamente não documentada. | `ats-api-copia/spec/` |
| L5 | AI Layer | **Sem modelos ML treinados** — Todo scoring usa LLMs ou algoritmos rule-based. Em volume, WSI scoring via LLM é custoso. Sem planos para inferência cacheada ou modelos menores especializados. | Inspeção geral do codebase |
| L6 | AI Layer | **Voice pipeline (3 providers) pode ter latência** — Composite strategy: Gemini STT + Claude LLM + Gemini TTS. Status por provider não uniforme. | `app/shared/providers/voice_composite.py` |

---

---

## APPENDIX — MATRIZ DE STATUS

### AI Layer

| Componente | Status | Notas |
|-----------|--------|-------|
| MainOrchestrator | [✓] | Pipeline unificado Sprint 5 |
| AutomationReActAgent | [✓] | LangGraph ReAct, circuit breaker |
| InterviewGraph (StateGraph) | [✓] | MAX_ITERATIONS=8, PostgresSaver |
| AutonomousReActAgent | [✓] | Circuit breaker, 40+ tools |
| CustomAgentRuntime (Studio) | [✓] | 15 tools whitelist, configurable |
| PolicySetupAgent | [✓] | Shim deprecated mantido |
| CVScreeningBatchService | [✓] | De-agentificado Sprint 5 |
| AgentStudioDomain | [✓] | Marketplace funcional |
| DigitalTwinDomain | [⚠] | Estrutura confirmada; RAG few-shot profundidade não verificada |
| CascadedRouter (8 tiers) | [✓] | Stats tracking ativo |
| FastRouter | [✓] | ~80% queries resolvidas |
| LLM Cascade (Flash→Sonnet→Opus) | [✓] | Thresholds configuráveis |
| A/B Testing Router | [✓] | YAML experiment, hash selection |
| Tool Registry (YAML) | [✓] | Validado no startup |
| Mailgun | [✓] | Circuit breaker ativo |
| Twilio WhatsApp | [✓] | Template messages + flows |
| Microsoft Teams | [✓] | Alert notifications |
| Microsoft Graph/Calendar | [✓] | Azure AD OAuth |
| ATS (Gupy/Pandape/Merge.dev) | [✓] | HMAC-SHA256 webhooks |
| SerpAPI | [⚠] | Opcional; fallback LLM |
| WorkOS | [✓] | SSO configurado |
| Voice (Gemini Live / OpenAI / Deepgram) | [⚠] | 3 providers; composite pipeline |
| pgvector (routing cache + RAG) | [✓] | ivfflat index, cosine 0.85 |
| Redis (routing cache + budget) | [✓] | Fallback in-memory dev/test |
| PostgreSQL (asyncpg, 76 migrations) | [✓] | Pool 20+10 |
| LangGraph Checkpointing (PostgresSaver) | [✓] | Thread ID = session_id |
| Celery Tasks | [✓] | RAGAS, learning loop, drift |
| FairnessGuard (3 layers) | [✓] | L3 não em todos domínios [⚠] |
| LGPD / Privacy / PII Masking | [✓] | 3 camadas de mascaramento |
| Prompt Injection Guard | [✓] | 20 patterns, 10 categorias |
| RLS PostgreSQL (migration 068) | [✓] | Deny by default |
| AuditService | [✓] | Toda decisão IA logada |
| AuditCallback (LangChain) | [✓] | Injetado em todos agents |
| HITL | [✓] | Redis TTL 24h; DB best-effort [⚠] |
| Model Drift Detection | [✓] | 4 triggers, Celery daily |
| RAGAS Evaluation | [✓] | Threshold 0.70, 90d retention |
| LangSmith Tracing | [✓] | `LANGCHAIN_TRACING_V2` |
| OpenTelemetry | [✓] | OTLP export; fallback LightweightTracer |
| Sentry | [✓] | `SENTRY_DSN` configurável |
| Prometheus | [✗] | Removido Task #138 |
| WSManager (WebSocket) | [⚠] | Singleton por processo — não distribuído |
| SSE Streaming | [✓] | Token-by-token via Claude |
| LLM Factory (multi-tenant) | [✓] | `ProviderContainer` por tenant |
| `LLMProviderFactory.generate_with_fallback()` | [⚠] | Deprecated mas chamável |
| Learning Loop | [✓] | Passivo; sem re-training ativo |
| Fine-tuning Export | [✓] | Pipeline pronto; não ativado |
| Personalization | [✓] | Por tenant, vaga, dept |
| Agent Studio Marketplace | [⚠] | Parcialmente funcional |
| Modelos ML não-LLM | [✗] | Nenhum; tudo rule-based ou LLM |

---

### Frontend

| Componente | Status | Notas |
|-----------|--------|-------|
| Next.js 15 App Router | [✓] | TypeScript strict, bun |
| shadcn/ui + Tailwind | [✓] | Design tokens customizados |
| Zustand stores (16 stores) | [✓] | devtools + persist seletivo |
| LiaFloatProvider | [✓] | Global context lifecycle |
| useChatTransport (WS/SSE) | [✓] | Auto-reconnect, backoff |
| useChatSocket (event routing) | [✓] | Todos event types mapeados |
| UnifiedChat (Phase 6) | [✓] | Arquitetura atual |
| LiaChatPanel | [⚠] | @deprecated, coexiste |
| KanbanSuperChatSection | [⚠] | @deprecated, coexiste |
| HITLConfirmCard | [✓] | approval_required → UI |
| BackgroundAgentsStatus | [✓] | background_task_update → UI |
| FairnessWarningBanner | [✓] | fairness_warnings → UI |
| panel_update → openDynamicPanel | [⚠] | Wiring não confirmado explicitamente |
| backgroundTasks state | [⚠] | Hook local, não Zustand |
| WorkOS SSO auth | [✓] | Cookie 7d, SAML/OIDC |
| JWT auth | [✓] | Server-side validation |
| Magic Link auth | [✓] | One-time login |
| BFF Proxies (478 routes) | [⚠] | Auth headers não uniformes |
| PATCH /candidates/:id/stage | [⚠] | Sem headers de auth |
| WS proxy (next.config.js) | [✓] | `/ws/:path*` → BACKEND_URL |
| Rails integration | [✗] | NEXT_PUBLIC_RAILS_URL comentado |
| i18n (next-intl) | [✓] | Todas rotas [locale] prefixadas |
| Vitest + Playwright | [✓] | Unit + e2e coverage |
| Sentry | [✓] | Client + server configs |
| TransportModeIndicator | [✓] | WS vs SSE visível em prod |
| WSI triagem (público) | [✓] | `/triagem/[token]` sem auth |
| LGPD portal | [✓] | `/portal/data-request/[token]` |

---

### Rails Backend

| Componente | Status | Notas |
|-----------|--------|-------|
| Rails 7.1 | [✓] | |
| PostgreSQL (pg gem) | [✓] | |
| Sidekiq (ActiveJob) | [✓] | MessageJob |
| Sneakers (RabbitMQ) | [✓] | MessageWorker, JobImportWorker |
| ActionCable | [✓] | MessageChannel, WorkflowChannel |
| Elasticsearch (searchkick) | [✓] | Per-tenant indices |
| ros-apartment (multi-tenant) | [⚠] | Parcialmente integrado |
| JWT auth (custom) | [✓] | 24h, sem revogação [⚠] |
| RBAC (roles/permissions) | [⚠] | Modelado; não aplicado em controllers |
| MagicLink auth | [⚠] | Implementado; rota ausente [✗] |
| AccountScopable | [✓] | Auto-assign account_id |
| TenantScoped | [⚠] | Não uniforme em todos controllers |
| MessageService::EventPublisher | [⚠] | Connection-per-publish |
| OnboardingEventPublisher | [⚠] | Connection-per-publish |
| MessageWorker (RabbitMQ consumer) | [✓] | Processa resp IA → ActionCable |
| JobImportWorker | [⚠] | Hardcoded user_id: 1, account_id: 1 |
| OnboardingController routes | [✗] | Controller existe; rotas ausentes |
| schema.rb | [✗] | Apenas 8 tabelas; 77 migrations faltando |
| Authorization enforcement | [✗] | RBAC não aplicado |
| Webhook outbound delivery | [✗] | Modelos existem; sem serviço |
| API rate limiting | [✗] | Sem rack-attack ou similar |
| Swagger/OpenAPI docs | [✗] | rswag no Gemfile; sem specs |
| Email sender config | [⚠] | from@example.com default |
| RSpec coverage | [⚠] | ~10% (12 spec files) |
| Integration tests (onboarding, campaigns) | [✗] | Zero cobertura |

---

*Documento gerado em 2026-04-13 — Protocolo P01*  
*Fonte: P01_AI_LAYER.md (807 linhas) + P01_FRONTEND.md (416 linhas) + P01_BACKEND.md (687 linhas)*
