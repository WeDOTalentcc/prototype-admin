# RELATÓRIO DE AUDITORIA PROFUNDA — Plataforma LIA (WeDO Talent)

**Data:** 2026-03-12
**Auditor:** Agente IA (Replit Agent) seguindo `PLAYBOOK_AUDITORIA_PROFUNDA.md`
**Escopo:** Auditoria completa do codebase — 14 dimensões, 13 Crenças, 8 Inegociáveis, 18 Production Readiness, Fairness/LGPD/EU AI Act

---

# SEÇÃO 1: MAPEAMENTO DA ARQUITETURA

## 1.1 Visão Geral do Sistema

| Componente | Tecnologia | Localização |
|:-----------|:-----------|:------------|
| **Backend (API)** | FastAPI + Python 3.x | `lia-agent-system/` |
| **Frontend** | Next.js (App Router) + React + TypeScript + Tailwind | `plataforma-lia/` |
| **Banco de Dados** | PostgreSQL (Alembic migrations) | `lia-agent-system/alembic/` |
| **LLM Providers** | Claude (Anthropic), Gemini (Google), OpenAI | `app/shared/providers/` |
| **Orquestrador** | CascadedRouter (6 tiers) + ReAct Agent Registry | `app/orchestrator/` |
| **Mensageria** | RabbitMQ (async events) | `app/shared/messaging/` |
| **Cache** | Redis (token budgets, embeddings, circuit breakers) | `app/services/` |
| **Observabilidade** | Sentry + Prometheus metrics + LangSmith | `app/observability/`, `app/core/sentry.py` |
| **ATS Integrations** | Gupy, PandaPé, StackOne, Merge | `app/services/ats_clients/` |

### Métricas de Escala

| Métrica | Valor |
|:--------|:------|
| Domínios de agente | 12 (sourcing, job_management, cv_screening, pipeline, recruiter_assistant ×3, hiring_policy, policy, analytics, communication, automation, ats_integration) |
| Agentes ReAct registrados | 11 |
| System prompts (domínio) | 16 arquivos |
| Tool registries | 12 domínio + 7 shared |
| Endpoints API (.py) | 210 arquivos |
| Models (.py) | 100 arquivos |
| Services (.py) | 236 arquivos |
| Frontend pages | 90 rotas |
| Frontend components (.tsx) | 466 componentes |
| Alembic migrations | 30+ |

## 1.2 Componentes Compartilhados

| Componente | Arquivo | Função | Status |
|:-----------|:--------|:-------|:-------|
| **FairnessGuard** | `app/shared/compliance/fairness_guard.py` | 3 camadas: Regex (9 categorias) + Léxico implícito (11 termos) + LLM semântico | Implementado |
| **PII Masking** | `app/shared/pii_masking.py` | Regex: CPF, email, telefone, nomes. Global filter no root logger + strip_pii_for_llm_prompt | Implementado |
| **Circuit Breaker** | `app/shared/resilience/circuit_breaker.py` | 3 estados (CLOSED/OPEN/HALF_OPEN) + notificações Teams/Bell + Prometheus | Implementado |
| **Audit Service** | `app/shared/compliance/audit_service.py` | Trilha de auditoria append-only para decisões de IA | Implementado |
| **ConfidencePolicyService** | `app/services/confidence_policy_service.py` | 3 níveis: APPLY_SILENT (≥0.85), APPLY_NOTIFY (0.70-0.84), ASK_USER (<0.70) | Implementado |
| **Human Review Sampling** | `app/services/human_review_sampling_service.py` | 5% sampling determinístico + always-review types + low confidence trigger | Implementado |
| **Token Budget** | `app/services/token_budget_service.py` | Redis-based daily limits por tenant (starter→enterprise) | Implementado |
| **LLM Cascade** | `app/orchestrator/llm_cascade.py` | Haiku→Sonnet→Opus (cost optimization) | Implementado |
| **Anti-Sycophancy Block** | `app/shared/prompts/anti_sycophancy_block.py` | 3 variantes: OPERATIONAL, FULL, ORCHESTRATOR | Implementado |
| **Defensive Prompts** | `app/shared/robustness/defensive_prompts.py` | Ambiguity detection, out-of-scope handling | Implementado |
| **Encryption** | `app/shared/encryption.py` | Fernet at-rest encryption | Implementado |
| **Rate Limiter** | `app/middleware/rate_limiter.py` | HTTP rate limiting per tenant | Implementado |
| **Consent Checker** | `app/services/consent_checker_service.py` | Soft enforcement (bloqueia revoked, warn absent) | Implementado |
| **LGPD Cleanup** | `app/services/lgpd_cleanup_service.py` | Data retention scheduler (90/180/365 dias) | Implementado |
| **Bias Audit** | `app/services/bias_audit_service.py` | Snapshots de viés + four-fifths rule | Implementado |
| **Prompt Registry** | `app/shared/prompts/prompt_registry.py` | YAML-based loader + versioning | Implementado |
| **EnhancedAgentMixin** | `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` | FairnessGuard pre-check + audit callback integrado nos agents | Implementado |

## 1.3 Stack por Domínio de Agente

### Sourcing
| Camada | Componente |
|:-------|:-----------|
| Agent | `SourcingReActAgent` → `app/domains/sourcing/agents/sourcing_react_agent.py` |
| System Prompt | `app/domains/sourcing/agents/sourcing_system_prompt.py` |
| Tool Registry | `app/domains/sourcing/agents/sourcing_tool_registry.py` |
| Stage Context | `app/domains/sourcing/agents/sourcing_stage_context.py` |
| Tools | `app/domains/sourcing/tools/query_tools.py`, `app/domains/sourcing/tools.py` |
| Services | `pearch_service.py`, `vacancy_search.py`, `sourcing_pipeline.py`, `wrf_service.py`, `apify_service.py` |
| Frontend | `/funil-de-talentos`, `/search` |

### Job Management (Wizard)
| Camada | Componente |
|:-------|:-----------|
| Agent | `WizardReActAgent` → `app/domains/job_management/agents/wizard_react_agent.py` |
| System Prompt | `app/domains/job_management/agents/wizard_system_prompt.py` |
| Tool Registry | `app/domains/job_management/agents/wizard_tool_registry.py` |
| Stage Context | `app/domains/job_management/agents/wizard_stage_context.py` |
| Tools | `job_wizard_tools.py`, `job_tools.py`, `query_tools.py` |
| Services | `job_vacancy_service.py`, `jd_generator_service.py`, `wizard_orchestrator_service.py` + 15 mais |
| Frontend | `/jobs/[id]`, `/admin/setup-empresa` |

### CV Screening (Pipeline)
| Camada | Componente |
|:-------|:-----------|
| Agent | `PipelineReActAgent` → `app/domains/cv_screening/agents/pipeline_react_agent.py` |
| System Prompt | `app/domains/cv_screening/agents/pipeline_system_prompt.py` |
| Tool Registry | `app/domains/cv_screening/agents/pipeline_tool_registry.py` |
| Stage Context | `app/domains/cv_screening/agents/pipeline_stage_context.py` |
| Tools | `candidate_tools.py` |
| Services | `wsi_service.py`, `wsi_screening_pipeline.py`, `wsi_question_service.py`, `wsi_deterministic_scorer.py` |
| Frontend | `/jobs/[id]/kanban`, `/triagem/[token]` |

### Recruiter Assistant (3 sub-agentes)
| Sub-agente | Agent | System Prompt | Tool Registry |
|:-----------|:------|:-------------|:-------------|
| **Talent** | `TalentReActAgent` | `talent_system_prompt.py` | `talent_tool_registry.py` |
| **Jobs Mgmt** | `JobsMgmtReActAgent` | `jobs_mgmt_system_prompt.py` | `jobs_mgmt_tool_registry.py` |
| **Kanban** | `KanbanReActAgent` | `kanban_system_prompt.py` | `kanban_tool_registry.py` |

### Pipeline Transition
| Camada | Componente |
|:-------|:-----------|
| Agent | `PipelineTransitionAgent` → `app/domains/pipeline/agents/pipeline_transition_agent.py` |
| System Prompt | `app/domains/pipeline/agents/pipeline_system_prompt.py` |
| Tool Registry | `app/domains/pipeline/agents/pipeline_tool_registry.py` |
| Services | `kanban_assistant_service.py` |

### Hiring Policy
| Camada | Componente |
|:-------|:-----------|
| Agent | `PolicyReActAgent` → `app/domains/hiring_policy/agents/policy_react_agent.py` |
| System Prompt | `app/domains/hiring_policy/agents/policy_system_prompt.py` |
| Tool Registry | `app/domains/hiring_policy/agents/policy_tool_registry.py` |

### Analytics
| Camada | Componente |
|:-------|:-----------|
| Agent | `AnalyticsReActAgent` → `app/domains/analytics/agents/analytics_react_agent.py` |
| System Prompt | `app/domains/analytics/agents/analytics_system_prompt.py` |
| Tool Registry | `app/domains/analytics/agents/analytics_tool_registry.py` |

### Communication
| Camada | Componente |
|:-------|:-----------|
| Agent | `CommunicationReActAgent` → `app/domains/communication/agents/communication_react_agent.py` |
| System Prompt | `app/domains/communication/agents/communication_system_prompt.py` |
| Tool Registry | `app/domains/communication/agents/communication_tool_registry.py` |

### Automation
| Camada | Componente |
|:-------|:-----------|
| Agent | `AutomationReActAgent` → `app/domains/automation/agents/automation_react_agent.py` |
| System Prompt | `app/domains/automation/agents/automation_system_prompt.py` |
| Tool Registry | `app/domains/automation/agents/automation_tool_registry.py` |

### ATS Integration
| Camada | Componente |
|:-------|:-----------|
| Agent | `ATSIntegrationReActAgent` → `app/domains/ats_integration/agents/ats_integration_react_agent.py` |
| System Prompt | `app/domains/ats_integration/agents/ats_integration_system_prompt.py` |
| Tool Registry | `app/domains/ats_integration/agents/ats_integration_tool_registry.py` |

## 1.4 Mapa de Tools por Scope

| Scope | Tools |
|:------|:------|
| **Query (Read-only)** | `query_tools.py` (sourcing, job_management, analytics), `analytics_query_tools.py` |
| **Action (Write)** | `job_tools.py`, `job_wizard_tools.py`, `candidate_tools.py`, `communication_tools.py`, `pipeline_tools.py` |
| **Shared** | `export_tools.py`, `insight_tools.py`, `predictive_tools.py`, `proactive_tools.py` |
| **HITL** | `pipeline_feedback_tool.py` (feedback do recrutador no pipeline) |

---

# SEÇÃO 2: ANÁLISE DETALHADA POR AGENTE

## 2.1 Sourcing Agent

**O que faz:**
- Busca candidatos via Pearch AI (190M+ profiles)
- Construção de queries de busca inteligente
- Análise de candidatos encontrados vs. requisitos da vaga
- Engagement nodes para abordagem
- Web scraping via Apify MCP

**O que NÃO faz (gaps):**
- Anti-sycophancy: AUSENTE no system prompt (`app/domains/sourcing/agents/sourcing_system_prompt.py`)
- Confidence calibration: AUSENTE — não reporta níveis de confiança nas buscas
- HITL: AUSENTE — não tem gate de revisão humana antes de engajar candidatos
- FairnessGuard no system prompt: referência apenas via ethical_guidelines genérico

**Problemas identificados:**
- `sourcing_system_prompt.py` — sem seção anti-sycophancy (Crença 11 violada)
- `sourcing_react_agent.py` — FairnessGuard via mixin inconsistente vs. outros agentes
- Pearch service tem circuit breaker (OK), mas falta fallback chain se Pearch falhar

## 2.2 Job Management (Wizard) Agent

**O que faz:**
- Criação guiada de vagas (wizard multi-step)
- Geração de JD (Job Description) com IA
- ConfidencePolicy para campos inferidos (APPLY_SILENT/APPLY_NOTIFY/ASK_USER)
- Templates e importação de JDs
- Analytics de vagas

**O que NÃO faz (gaps):**
- FairnessGuard no output de JD: apenas na entrada do wizard, não verifica JD gerada

**Status:**
- Anti-sycophancy: OK (presente no system prompt)
- FairnessGuard: OK (via `_fairness_pre_check` no process())
- Confidence: OK (ConfidencePolicyService integrado)
- HITL: OK (ASK_USER para low confidence)

## 2.3 CV Screening (Pipeline) Agent

**O que faz:**
- Triagem de CVs via WSI (Weighted Scoring Index)
- 4 dimensões canônicas: technical (50%), behavioral (20%), gap_analysis (15%), contextual (15%)
- Scoring determinístico + LLM
- Geração de perguntas WSI
- Pipeline de screening completo

**O que NÃO faz (gaps):**
- Anti-sycophancy: AUSENTE no system prompt direto (`pipeline_system_prompt.py`)
- O screening pipeline carrega via YAML shared mas o arquivo de domínio não tem menção direta

**Problemas identificados:**
- `pipeline_system_prompt.py` — sem seção anti-sycophancy explícita
- FairnessGuard: referenciado no YAML shared (`cv_screening.yaml` linha 54)
- HITL: OK — revisão humana para zona de fronteira (60-70%)

## 2.4 Recruiter Assistant (Talent)

**O que faz:**
- Assistente conversacional para recrutador
- Busca e análise de candidatos
- Comparação de candidatos

**Status:**
- Anti-sycophancy: OK (presente no system prompt)
- FairnessGuard: OK (via mixin)
- Confidence: PARCIAL — sem confidence score explícito
- HITL: AUSENTE — não tem gate de revisão

## 2.5 Recruiter Assistant (Kanban)

**O que faz:**
- Gestão do kanban de pipeline
- Movimentação de candidatos entre etapas
- Ações em lote

**Status:**
- Anti-sycophancy: OK
- FairnessGuard: OK (via mixin)
- LLM Fallback: OK (Claude→Gemini implementado e testado)
- Rate limiting: OK (integrado)

## 2.6 Recruiter Assistant (Jobs Management)

**O que faz:**
- Gestão de vagas existentes
- Edição, clonagem, fechamento

**Status:**
- Anti-sycophancy: OK
- FairnessGuard: OK (via mixin)

## 2.7 Pipeline Transition Agent

**O que faz:**
- Transição de candidatos entre etapas do pipeline
- Validação de regras de negócio
- Feedback ao candidato

**Status:**
- FairnessGuard: OK (manual call com check + check_implicit_bias + audit log)
- HITL: OK (integrado com human review)
- Anti-sycophancy: OK (presente no system prompt)

## 2.8 Hiring Policy Agent

**O que faz:**
- Configuração e validação de políticas de contratação
- Guardrails de processo

**Status:**
- Anti-sycophancy: OK
- FairnessGuard: OK (manual call)

## 2.9 Analytics Agent

**O que faz:**
- Relatórios e métricas de recrutamento
- Análises preditivas

**Problemas:**
- Anti-sycophancy: AUSENTE no system prompt
- FairnessGuard: via mixin genérico, sem validação específica de outputs analíticos

## 2.10 Communication Agent

**O que faz:**
- Envio de comunicações (email, WhatsApp, SMS, Teams, in-app)
- Multi-channel routing
- Opt-out management
- Templates

**Problemas:**
- Anti-sycophancy: AUSENTE no system prompt
- Rate limiting: OK (integrado)
- Opt-out: OK (implementado)

## 2.11 Automation Agent

**O que faz:**
- Automações de stage transition
- Triggers configuráveis
- Scheduler

**Problemas:**
- Anti-sycophancy: AUSENTE no system prompt

## 2.12 ATS Integration Agent

**O que faz:**
- Sincronização com ATS externos (Gupy, PandaPé, StackOne, Merge)
- Webhook handling

**Problemas:**
- Anti-sycophancy: AUSENTE no system prompt
- Circuit breaker: AUSENTE nos ATS clients (Gupy, PandaPé, StackOne usam httpx direto)

---

# SEÇÃO 3: AUDITORIA MULTI-DIMENSIONAL

## 3.1 Tabela Resumo

| Verificação | Sourcing | Wizard | CV Screen | Talent | Kanban | Jobs Mgmt | Pipeline Trans | Policy | Analytics | Communic. | Automation | ATS Integ. |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Anti-Sycophancy | **FALHA** | OK | **FALHA** | OK | OK | OK | OK | OK | **FALHA** | **FALHA** | **FALHA** | **FALHA** |
| FairnessGuard | PARCIAL | OK | OK | OK | OK | OK | OK | OK | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| Negation Detection | N/A | N/A | OK | N/A | N/A | N/A | OK | OK | N/A | N/A | N/A | N/A |
| Confiança Real | **FALHA** | OK | OK | **FALHA** | **FALHA** | **FALHA** | OK | OK | **FALHA** | **FALHA** | **FALHA** | **FALHA** |
| Circuit Breaker | OK | PARCIAL | PARCIAL | PARCIAL | OK | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | **FALHA** |
| Pre-call Budget | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| PII Masking | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Consent Check | N/A | N/A | PARCIAL | N/A | N/A | N/A | N/A | N/A | N/A | PARCIAL | N/A | N/A |
| Multi-Tenant | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Audit Trail | PARCIAL | OK | OK | OK | OK | OK | OK | OK | PARCIAL | PARCIAL | OK | PARCIAL |
| Observabilidade | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Token Tracking | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| HITL Enforcement | **FALHA** | OK | OK | **FALHA** | PARCIAL | PARCIAL | OK | OK | N/A | **FALHA** | PARCIAL | N/A |

## 3.2 Detalhamento por Dimensão

### Dimensão 1 — Wiring/Integração

**Status:** PARCIAL

- Orquestrador CascadedRouter (6 tiers) → bem implementado, custo otimizado
- Domain Registry com auto-discovery via decorator → OK
- ReAct Agent Registry → 11 agentes registrados → OK
- **Gap:** Orquestrador Phase 1 (ActionExecutor) pode bypasses FairnessGuard em atalhos
- **Evidência:** `app/orchestrator/orchestrator.py` — short-cut commands processados antes do domain agent

### Dimensão 2 — Data Flow

**Status:** OK

- Dados fluem: Frontend → API → Orchestrator → Domain Agent → Services → DB
- PII stripping antes de enviar ao LLM (`strip_pii_for_llm_prompt`)
- Token budget check antes de cada invocação LLM no WebSocket (`agent_chat_ws.py` linha 459)

### Dimensão 3 — UI/UX + Design System

**Status:** PARCIAL

- 466 componentes React com Tailwind + shadcn/ui (Radix primitives)
- Acessibilidade: 77/466 componentes (16.5%) com aria-labels — **abaixo do esperado para WCAG 2.1 AA**
- AI Explainability Panel implementado (`agent-explainability-panel.tsx`)
- AI Disclaimer component existe
- Consent flow para candidatos: presente na triagem (WelcomeCard.tsx)
- **Gap:** Mock data em várias páginas admin (faturamento, usuarios)
- **Gap:** Cobertura de aria-labels em apenas 16.5% dos componentes

### Dimensão 4 — Backend/API

**Status:** OK

- 210 arquivos de endpoint API
- Rate limiting via middleware (`RateLimitMiddleware`)
- Request ID tracking (`RequestIdMiddleware`)
- Structured logging (`StructuredLoggingMiddleware`)
- Exception handlers com Sentry integration
- CORS configurado

### Dimensão 5 — Types/Contracts

**Status:** PARCIAL

- Pydantic schemas amplamente usados
- Modelos SQLAlchemy com tipagem forte
- **Gap:** Alguns serviços usam `Dict[str, Any]` como tipo de retorno (perda de contrato)

### Dimensão 6 — User Flow

**Status:** OK

- Wizard multi-step com ConfidencePolicy (3 níveis)
- Kanban com drag-and-drop e ações em lote
- Triagem de candidatos com perguntas geradas por IA
- Portal do candidato com DSR (data subject requests)

### Dimensão 7 — Consistência

**Status:** PARCIAL

- Pattern de 4 arquivos (system_prompt, tool_registry, stage_context, react_agent) seguido por maioria
- **Gap:** Domínios `policy` vs `hiring_policy` duplicam padrão
- **Gap:** Tools duplicados (`app/tools/` vs `app/domains/*/tools/`)

### Dimensão 8 — Documentação

**Status:** PARCIAL

- Playbook de auditoria completo (4838 linhas) com 44 runbooks
- Docstrings em componentes críticos (FairnessGuard, PII Masking, Human Review)
- **Gap:** Documentação de API incompleta (sem OpenAPI descriptions em muitos endpoints)
- **Gap:** Sem ADR (Architecture Decision Records) formalizados além do playbook

### Dimensão 9 — Arquitetura de Agentes

**Status:** OK

- ReAct loop pattern consistente via `lia_agents_core`
- EnhancedAgentMixin com FairnessGuard pre-check, audit callback
- DomainWorkflow com FairnessGuard automático (flag `enable_fairness_guard=True`)
- Prompt YAML loading com versioning
- Memory: conversation_memory + working_memory + long_term_memory
- Autonomy engine com níveis progressivos

### Dimensão 10 — Qualidade LLM

**Status:** PARCIAL

- Anti-sycophancy block existe com 3 variantes (OPERATIONAL, FULL, ORCHESTRATOR)
- **Gap crítico:** 6 de 12 agentes NÃO incluem anti-sycophancy no system prompt
- Few-shot examples: biblioteca extensiva em `app/shared/prompts/examples/`
- Defensive prompts: ambiguity detection + out-of-scope handling
- **Gap:** Negation detection não é universal (apenas em cv_screening, pipeline, policy)
- **Gap:** Confidence calibration ausente em 8 de 12 agentes

### Dimensão 11 — Serviços IA/Integrações

**Status:** OK

- LLM fallback chain: Claude→Gemini→OpenAI implementado (`llm_factory.py`)
- Cascaded routing: 6 tiers (Memory→LRU→Redis→Vector→Regex→LLM)
- LLM cascade: Haiku→Sonnet→Opus (cost optimization)
- ATS clients: Gupy, PandaPé, StackOne, Merge
- Pearch AI: candidate search 190M+ profiles
- OpenMic.ai: voice screening
- Deepgram: speech-to-text

### Dimensão 12 — Governança/Resiliência

**Status:** PARCIAL

- FairnessGuard: 3 camadas implementadas, mas NÃO é middleware automático universal
  - **Evidência:** É opt-in via mixin, não forçado no entry-point do Orchestrator
  - **Gap:** Orchestrator ActionExecutor pode bypassar em short-cut commands
- Circuit breaker: implementado mas incompleto
  - OK: Claude, Pearch, Google Calendar, Deepgram, OpenMic
  - FALHA: OpenAI (definido mas não decorado), Gemini (definido mas não decorado), ATS clients, Email providers, Billing providers, WorkOS
- Human Review: 5% sampling + always-review types + low confidence → OK para pipeline
  - **Gap:** Não integrado em sourcing, communication
- Dead Letter Queue: implementada (`enhanced_task_manager.py`, `task_persistence.py`)
- PolicyEngine: business rules + rate limit rules + escalation rules seeded no startup

### Dimensão 13 — Segurança/Proteção de Dados

**Status:** PARCIAL

- PII Masking: global filter no root logger + strip_pii_for_llm_prompt → OK
- Encryption: Fernet at-rest para dados sensíveis → OK
- LGPD Consent: versioned, SHA256 proof hash, granular → OK
- DSR: fluxo end-to-end com SLA 15 dias úteis → OK
- Data Retention: scheduler com cleanup automático (90/180/365 dias) → OK
- Audit Trail: append-only (sem PUT/PATCH), proof hashes → OK
- **Gap:** Consent check é "soft enforcement" (absent = warn, não block) por padrão
- **Gap:** Multi-tenant isolation: via company_id em queries, não via Row Level Security no DB
- **Gap:** Rate limiting: HTTP level OK, mas token-level por tenant apenas no chat WebSocket

### Dimensão 14 — Performance/Escalabilidade

**Status:** PARCIAL

- Embedding cache com warm-up → OK
- Redis caching para token budgets → OK
- AI cache service → OK
- **Gap:** Sem load test documentado (Production Readiness #14)
- **Gap:** Sem backup verification documentado (Production Readiness #12)
- **Gap:** Sem rollback procedure documentado (Production Readiness #13)

---

# SEÇÃO 4: ANÁLISE COMPARATIVA DE CAPACIDADES

## 4.1 Mapa de Capacidades (Agente × Capacidade)

| Capacidade | Sourcing | Wizard | CV Screen | Talent | Kanban | Jobs Mgmt | Pipeline | Policy | Analytics | Communic. | Automation | ATS |
|:-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Anti-Sycophancy | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| FairnessGuard Pre-check | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Confidence Score | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| HITL Gate | ❌ | ✅ | ✅ | ❌ | ⚠️ | ⚠️ | ✅ | ✅ | N/A | ❌ | ⚠️ | N/A |
| Audit Trail | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ |
| Circuit Breaker | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| Few-shot Examples | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Stage Context | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| LLM Fallback | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Token Tracking | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Opt-out | ✅ | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | ✅ | N/A | N/A |

## 4.2 Padrões que Deveriam Ser Universais

### Nível 1 — Obrigatório em TODOS (hoje ausente em muitos)
1. **Anti-sycophancy** — Crença #11 exige em TODOS os prompts. Hoje: 6/12 agentes (50%) → **FALHA CRÍTICA**
2. **FairnessGuard como middleware automático** — Hoje é opt-in via mixin → deveria ser forçado no Orchestrator
3. **Confidence score em outputs** — Hoje: 4/12 agentes reportam confiança
4. **HITL gate para ações de alto impacto** — Hoje: inconsistente entre agentes

### Nível 2 — Obrigatório em agentes que tocam candidatos
1. **Negation detection** — Apenas 3 agentes (cv_screening, pipeline, policy)
2. **Consent check antes de processar** — Apenas no screening, soft enforcement
3. **Audit trail em todas as decisões** — 8/12 agentes com trail completo

### Nível 3 — Desejável para maturidade
1. **Few-shot examples** — 5/12 agentes com exemplos
2. **Stage context** — 8/12 agentes com contexto de etapa
3. **Métricas por agente** — Prometheus metrics parciais

## 4.3 Tools Declarados vs Usados

| Tool Registry | Tools Declarados | Observação |
|:--------------|:-----------------|:-----------|
| `sourcing_tool_registry.py` | Query tools + engagement | OK — tools coerentes com domínio |
| `wizard_tool_registry.py` | Wizard + job tools | OK |
| `pipeline_tool_registry.py` | Candidate + screening tools | OK |
| `talent_tool_registry.py` | Pipeline + analysis tools | OK |
| `kanban_tool_registry.py` | Pipeline + movement tools | OK |
| `communication_tool_registry.py` | Communication + opt-out tools | OK |
| `automation_tool_registry.py` | Stage automation tools | OK |
| **Shared tools** | `export_tools`, `insight_tools`, `predictive_tools`, `proactive_tools` | Parcialmente integrados |

---

# SEÇÃO 5: PRIORIDADES DE CORREÇÃO COM RUNBOOKS

## P0 — Crítico (Violação de Inegociáveis)

### ACH-001 — Anti-Sycophancy ausente em 6 de 12 agentes
- **Prioridade:** P0
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-09
- **Arquivo(s) afetado(s):** `app/domains/sourcing/agents/sourcing_system_prompt.py`, `app/domains/cv_screening/agents/pipeline_system_prompt.py`, `app/domains/communication/agents/communication_system_prompt.py`, `app/domains/analytics/agents/analytics_system_prompt.py`, `app/domains/ats_integration/agents/ats_integration_system_prompt.py`, `app/domains/automation/agents/automation_system_prompt.py`
- **Descrição:** Crença #11 do Manifesto WeDO Talent exige anti-sycophancy em TODOS os prompts sem exceção. 6 system prompts de domínio não incluem a seção. O bloco existe em `anti_sycophancy_block.py` mas não é injetado nos prompts destes domínios.
- **Impacto se não corrigido:** IA concorda silenciosamente com pedidos problemáticos do recrutador, comprometendo qualidade das contratações e fairness.
- **Esforço estimado:** 4h — Backend
- **Depende de:** Nenhum

### ACH-002 — FairnessGuard não é middleware automático universal
- **Prioridade:** P0
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-02
- **Arquivo(s) afetado(s):** `app/orchestrator/orchestrator.py`, `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py`
- **Descrição:** O playbook exige que FairnessGuard seja middleware automático que intercepta TODAS as interações (Inegociável #3). Atualmente é opt-in via mixin — agentes devem chamar `_fairness_pre_check` manualmente. O Orchestrator Phase 1 (ActionExecutor) pode processar short-cut commands sem passar pelo guard.
- **Impacto se não corrigido:** Queries discriminatórias podem bypassar o guard se agente não chamar manualmente.
- **Esforço estimado:** 8h — Backend
- **Depende de:** Nenhum

### ACH-003 — Consent check em modo soft enforcement
- **Prioridade:** P0
- **Dimensão:** 13 (Segurança/Dados)
- **Runbook:** RM-05
- **Arquivo(s) afetado(s):** `app/services/consent_checker_service.py`
- **Descrição:** Quando consentimento está AUSENTE (não revogado, mas não dado), o sistema faz soft warning e permite processamento. LGPD Art. 7 exige base legal ANTES do processamento. A env `LGPD_CONSENT_ABSENT_HARD_BLOCK` existe mas default é False.
- **Impacto se não corrigido:** Processamento de dados sem base legal registrada — violação LGPD.
- **Esforço estimado:** 4h — Backend
- **Depende de:** Nenhum

### ACH-004 — Circuit breaker ausente em OpenAI e Gemini providers
- **Prioridade:** P0
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-11
- **Arquivo(s) afetado(s):** `app/shared/providers/llm_openai.py`, `app/shared/providers/llm_gemini.py`
- **Descrição:** Circuits `OPENAI_CIRCUIT` e `GEMINI_CIRCUIT` estão DEFINIDOS mas não decorados nos providers. Quando Claude cai e fallback vai para Gemini/OpenAI, esses providers operam sem proteção de circuit breaker.
- **Impacto se não corrigido:** Falha em cascata quando provider LLM fica instável. Custos descontrolados com retries infinitos.
- **Esforço estimado:** 4h — Backend
- **Depende de:** Nenhum

### ACH-005 — HITL ausente em sourcing e communication
- **Prioridade:** P0
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-03
- **Arquivo(s) afetado(s):** `app/domains/sourcing/agents/sourcing_react_agent.py`, `app/domains/communication/agents/communication_react_agent.py`
- **Descrição:** Inegociável #2 exige review gate para decisões de alto impacto. Sourcing pode engajar candidatos sem revisão humana. Communication pode enviar mensagens sem aprovação (parcial — tem opt-out mas não HITL no envio).
- **Impacto se não corrigido:** Contato com candidatos sem supervisão humana — violação de Crença #1 (Humano em Primeiro Lugar).
- **Esforço estimado:** 8h — Backend
- **Depende de:** Nenhum

### ACH-006 — Audit trail incompleto em 4 agentes
- **Prioridade:** P0
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-06
- **Arquivo(s) afetado(s):** `app/domains/sourcing/agents/sourcing_react_agent.py`, `app/domains/analytics/agents/analytics_react_agent.py`, `app/domains/communication/agents/communication_react_agent.py`, `app/domains/ats_integration/agents/ats_integration_react_agent.py`
- **Descrição:** Crença #8 exige trilha de auditoria em toda saída de agente. 4 agentes têm trail parcial — não logam todas as decisões no audit_service.
- **Impacto se não corrigido:** Decisões de IA sem rastreabilidade — violação EU AI Act (auditabilidade obrigatória).
- **Esforço estimado:** 6h — Backend
- **Depende de:** Nenhum

### ACH-007 — Acessibilidade (WCAG 2.1 AA) abaixo do requerido
- **Prioridade:** P0
- **Dimensão:** 3 (UI/UX)
- **Runbook:** RM-08
- **Arquivo(s) afetado(s):** `plataforma-lia/src/components/` (389 de 466 componentes sem aria-labels)
- **Descrição:** Inegociável #8 exige WCAG 2.1 AA em todas as interfaces. Apenas 16.5% dos componentes (77/466) têm aria-labels. Falta verificação sistemática de contraste, navegação por teclado, screen reader.
- **Impacto se não corrigido:** Plataforma inacessível para pessoas com deficiência — violação Crença #13 e Lei 13.146/15.
- **Esforço estimado:** 40h — Frontend
- **Depende de:** Nenhum

### ACH-008 — Multi-tenant sem Row Level Security
- **Prioridade:** P0
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-07
- **Arquivo(s) afetado(s):** `lia-agent-system/app/core/database.py`, modelos
- **Descrição:** Isolamento multi-tenant implementado via filtro `company_id` nas queries (application-level). Sem Row Level Security (RLS) no PostgreSQL. Um bug em qualquer query pode expor dados de outro tenant.
- **Impacto se não corrigido:** Vazamento de dados entre tenants — violação LGPD, SOC-2, ISO-27001.
- **Esforço estimado:** 16h — Backend/Infra
- **Depende de:** Nenhum

## P1 — Alto (Qualidade e Resiliência)

### ACH-009 — Confidence calibration ausente em 8 agentes
- **Prioridade:** P1
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-10
- **Arquivo(s) afetado(s):** System prompts de sourcing, talent, kanban, jobs_mgmt, analytics, communication, automation, ats_integration
- **Descrição:** EU AI Act Art. 13 exige que sistemas de alto risco reportem confiança. 8 de 12 agentes não reportam confidence score nos outputs.
- **Impacto se não corrigido:** Sem confiança, recrutador não sabe quando questionar a IA.
- **Esforço estimado:** 8h — Backend
- **Depende de:** Nenhum

### ACH-010 — Circuit breaker ausente em ATS clients
- **Prioridade:** P1
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-11
- **Arquivo(s) afetado(s):** `app/services/ats_clients/gupy.py`, `pandape.py`, `stackone.py`, `merge.py`
- **Descrição:** 4 ATS clients usam httpx sem circuit breaker. Merge tem circuit definido (`MERGE_CIRCUIT`) mas não decorado.
- **Impacto se não corrigido:** Falha de ATS externo causa timeout e degradação do sistema.
- **Esforço estimado:** 6h — Backend
- **Depende de:** Nenhum

### ACH-011 — Circuit breaker ausente em email/billing providers
- **Prioridade:** P1
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-11
- **Arquivo(s) afetado(s):** `app/services/email_providers/`, `app/services/billing_providers/`
- **Descrição:** SendGrid, Resend, Iugu, Vindi providers sem circuit breaker.
- **Impacto se não corrigido:** Falha de provider externo bloqueia comunicações e billing.
- **Esforço estimado:** 4h — Backend
- **Depende de:** Nenhum

### ACH-012 — Few-shot examples ausentes em 7 agentes
- **Prioridade:** P1
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-17
- **Arquivo(s) afetado(s):** System prompts de talent, kanban, jobs_mgmt, analytics, communication, automation, ats_integration
- **Descrição:** Few-shot examples melhoram significativamente a qualidade de output do LLM. 7 agentes não têm exemplos no prompt.
- **Impacto se não corrigido:** Output inconsistente e baixa qualidade em agentes sem exemplos.
- **Esforço estimado:** 12h — Backend
- **Depende de:** Nenhum

### ACH-013 — Observabilidade Prometheus parcial
- **Prioridade:** P1
- **Dimensão:** 14 (Performance)
- **Runbook:** RM-14
- **Arquivo(s) afetado(s):** `app/observability/metrics.py`
- **Descrição:** Métricas Prometheus existem para FairnessGuard e circuit breaker, mas faltam métricas por agente (latência, tokens, erros por domínio).
- **Impacto se não corrigido:** Sem visibilidade de performance por agente; difícil detectar regressões.
- **Esforço estimado:** 8h — Backend/Infra
- **Depende de:** Nenhum

### ACH-014 — WorkOS circuit breaker definido mas não implementado
- **Prioridade:** P1
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-11
- **Arquivo(s) afetado(s):** `app/api/v1/workos.py`
- **Descrição:** `WORKOS_CIRCUIT` definido no registry mas endpoint usa httpx direto.
- **Impacto se não corrigido:** Falha de WorkOS (auth provider) bloqueia login de todos os users.
- **Esforço estimado:** 2h — Backend
- **Depende de:** Nenhum

### ACH-015 — Degradação graceful sem documentar
- **Prioridade:** P1
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-15
- **Arquivo(s) afetado(s):** Documentação
- **Descrição:** Sistema tem fallbacks (LLM cascade, circuit breakers) mas sem documentação de graceful degradation (o que o user vê quando cada componente falha).
- **Impacto se não corrigido:** Ops team sem playbook para incidentes.
- **Esforço estimado:** 4h — Backend/Ops
- **Depende de:** Nenhum

## P2 — Médio (Melhorias de Arquitetura)

### ACH-016 — Duplicação de domínio policy vs hiring_policy
- **Prioridade:** P2
- **Dimensão:** 7 (Consistência)
- **Runbook:** RM-30
- **Arquivo(s) afetado(s):** `app/domains/policy/`, `app/domains/hiring_policy/`
- **Descrição:** Dois domínios para policy com padrões levemente diferentes.
- **Impacto se não corrigido:** Confusão de routing, manutenção duplicada.
- **Esforço estimado:** 8h — Backend
- **Depende de:** Nenhum

### ACH-017 — Tools duplicados entre app/tools e app/domains/*/tools
- **Prioridade:** P2
- **Dimensão:** 7 (Consistência)
- **Runbook:** RM-30
- **Arquivo(s) afetado(s):** `app/tools/`, `app/domains/*/tools/`
- **Descrição:** Mesmos tools existem em dois locais (legado em `app/tools/`, novo em `app/domains/*/tools/`).
- **Impacto se não corrigido:** Edição no lugar errado não tem efeito; riscos de divergência.
- **Esforço estimado:** 6h — Backend
- **Depende de:** Nenhum

### ACH-018 — Mock data em páginas admin de produção
- **Prioridade:** P2
- **Dimensão:** 3 (UI/UX)
- **Runbook:** RM-35
- **Arquivo(s) afetado(s):** Páginas admin (faturamento, usuarios)
- **Descrição:** `MOCK_BILLING_DATA`, `mockUsers` hardcoded em componentes admin que deveriam mostrar dados reais.
- **Impacto se não corrigido:** Admin vê dados falsos, decisões baseadas em informação incorreta.
- **Esforço estimado:** 12h — Frontend
- **Depende de:** Nenhum

### ACH-019 — Stage context ausente em 4 agentes
- **Prioridade:** P2
- **Dimensão:** 9 (Arquitetura de Agentes)
- **Runbook:** RM-20
- **Arquivo(s) afetado(s):** Analytics, communication, automation, ats_integration agents
- **Descrição:** Stage context dá ao agente visão do pipeline. 4 agentes não implementam.
- **Impacto se não corrigido:** Agentes sem contexto de onde o candidato/vaga está no processo.
- **Esforço estimado:** 8h — Backend
- **Depende de:** Nenhum

### ACH-020 — Documentação de API incompleta
- **Prioridade:** P2
- **Dimensão:** 8 (Documentação)
- **Runbook:** RM-32
- **Arquivo(s) afetado(s):** 210 arquivos de endpoint API
- **Descrição:** Muitos endpoints sem OpenAPI descriptions, examples, response schemas.
- **Impacto se não corrigido:** Integrações externas difíceis de implementar.
- **Esforço estimado:** 20h — Backend
- **Depende de:** Nenhum

### ACH-021 — Negation detection não universal
- **Prioridade:** P2
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-26
- **Arquivo(s) afetado(s):** System prompts dos domínios sem negation detection
- **Descrição:** Detecção de negação (quando recrutador diz "não quero X") implementada em apenas 3 agentes. Agentes sem detecção podem interpretar incorretamente pedidos negativos.
- **Impacto se não corrigido:** IA inclui candidatos que deveriam ser excluídos (ou vice-versa).
- **Esforço estimado:** 6h — Backend
- **Depende de:** ACH-001

### ACH-022 — Bias audit baseline não verificável em runtime
- **Prioridade:** P2
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-25
- **Arquivo(s) afetado(s):** `app/services/bias_audit_service.py`, `app/api/v1/bias_audit.py`
- **Descrição:** Bias audit service e API existem, mas sem Golden Dataset de 100 candidatos representativos para baseline automático (Production Readiness #9).
- **Impacto se não corrigido:** Sem baseline, impossível detectar drift de viés.
- **Esforço estimado:** 16h — Backend
- **Depende de:** Nenhum

### ACH-023 — Load test não documentado
- **Prioridade:** P2
- **Dimensão:** 14 (Performance)
- **Runbook:** RM-42
- **Arquivo(s) afetado(s):** Documentação
- **Descrição:** Production Readiness #14 exige load test com P95 < 5s. Sem evidência de load test executado.
- **Impacto se não corrigido:** Sistema pode falhar sob carga sem saber.
- **Esforço estimado:** 8h — Infra
- **Depende de:** Nenhum

### ACH-024 — Backup e rollback não documentados
- **Prioridade:** P2
- **Dimensão:** 14 (Performance)
- **Runbook:** RM-43
- **Arquivo(s) afetado(s):** Documentação
- **Descrição:** Production Readiness #12 e #13 exigem backup verificado e rollback documentado.
- **Impacto se não corrigido:** Impossível recuperar de falha catastrófica.
- **Esforço estimado:** 4h — Infra/Ops
- **Depende de:** Nenhum

### ACH-025 — Security scan não evidenciado
- **Prioridade:** P2
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-44
- **Arquivo(s) afetado(s):** CI/CD
- **Descrição:** Production Readiness #15 exige security scan limpo (0 critical/high).
- **Impacto se não corrigido:** Vulnerabilidades podem existir sem detecção.
- **Esforço estimado:** 4h — Infra/Security
- **Depende de:** Nenhum

## P3 — Baixo (Futuro/Backlog)

### ACH-026 — FairnessGuard sem Camada 3 (LLM semântico) ativa por padrão
- **Prioridade:** P3
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-02
- **Arquivo(s) afetado(s):** `app/shared/compliance/fairness_guard.py`
- **Descrição:** Camada 3 (análise semântica via LLM) implementada mas não ativada automaticamente. Requer chamada explícita de `check_semantic()`.
- **Impacto se não corrigido:** Vieses sutis que escapam regex e léxico passam despercebidos.
- **Esforço estimado:** 8h — Backend
- **Depende de:** ACH-002

### ACH-027 — RAGAS evaluation framework não implementado
- **Prioridade:** P3
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-41
- **Arquivo(s) afetado(s):** Novo serviço
- **Descrição:** Playbook define metas RAGAS (Faithfulness ≥0.90, Relevance ≥0.85, etc.) mas sem implementação.
- **Impacto se não corrigido:** Sem métricas de qualidade de output do LLM.
- **Esforço estimado:** 24h — Backend
- **Depende de:** Nenhum

### ACH-028 — Red teaming framework não implementado
- **Prioridade:** P3
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-40
- **Arquivo(s) afetado(s):** Testes
- **Descrição:** 6 cenários obrigatórios de red teaming (prompt injection, data exfiltration, bias elicitation, jailbreak, escalação de privilégios, manipulação de score) não implementados como suite de testes automatizados.
- **Impacto se não corrigido:** Vulnerabilidades de segurança de IA não detectadas.
- **Esforço estimado:** 32h — Backend/Security
- **Depende de:** Nenhum

### ACH-029 — Model drift detection não implementado
- **Prioridade:** P3
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-24
- **Arquivo(s) afetado(s):** `app/api/v1/drift.py` (endpoint existe, lógica incompleta)
- **Descrição:** Triggers de alerta (score WSI varia >0.5 em 30 dias, etc.) definidos no playbook mas sem implementação de monitoramento contínuo.
- **Impacto se não corrigido:** Degradação silenciosa de qualidade do modelo.
- **Esforço estimado:** 16h — Backend
- **Depende de:** Nenhum

### ACH-030 — Score normalization entre versões de perguntas WSI
- **Prioridade:** P3
- **Dimensão:** 5 (Types/Contracts)
- **Runbook:** RM-34
- **Arquivo(s) afetado(s):** `app/domains/cv_screening/services/wsi_service.py`
- **Descrição:** Score normalization definido no playbook (trigger: variância >5%, factor: 0.7-1.3) mas implementação não verificada.
- **Impacto se não corrigido:** Candidatos avaliados com versões diferentes de perguntas recebem scores incomparáveis.
- **Esforço estimado:** 8h — Backend
- **Depende de:** Nenhum

### ACH-031 — FRIA (Fundamental Rights Impact Assessment) não documentado
- **Prioridade:** P3
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-39
- **Arquivo(s) afetado(s):** Documentação
- **Descrição:** EU AI Act Art. 6+Anexo III exige FRIA antes do deploy para sistemas de alto risco (IA em recrutamento).
- **Impacto se não corrigido:** Non-compliance com EU AI Act.
- **Esforço estimado:** 16h — Legal/Compliance
- **Depende de:** Nenhum

---

# SEÇÃO 6: RESUMO EXECUTIVO DE ESFORÇO

## 6.1 Tabela Consolidada

| Prioridade | Qtd. Achados | Esforço Total (h) | Responsável Principal | Sprint Alvo |
|:----------:|:------------:|:-----------------:|:---------------------:|:-----------:|
| **P0** | 8 | 90h | Backend + Frontend | Imediato |
| **P1** | 7 | 44h | Backend | Sprint N+1 |
| **P2** | 10 | 92h | Backend + Frontend + Infra | Sprint N+2/N+3 |
| **P3** | 6 | 104h | Backend + Security + Legal | Backlog |
| **Total** | **31** | **330h** | — | — |

## 6.2 Detalhamento P0 (Imediato)

| ID | Achado | Esforço | Responsável | Runbook |
|:---|:-------|:-------:|:-----------:|:-------:|
| ACH-001 | Anti-sycophancy em 6 agentes | 4h | Backend | RM-09 |
| ACH-002 | FairnessGuard como middleware | 8h | Backend | RM-02 |
| ACH-003 | Consent hard enforcement | 4h | Backend | RM-05 |
| ACH-004 | Circuit breaker OpenAI/Gemini | 4h | Backend | RM-11 |
| ACH-005 | HITL em sourcing/communication | 8h | Backend | RM-03 |
| ACH-006 | Audit trail em 4 agentes | 6h | Backend | RM-06 |
| ACH-007 | WCAG 2.1 AA (aria-labels) | 40h | Frontend | RM-08 |
| ACH-008 | Multi-tenant RLS | 16h | Backend/Infra | RM-07 |

## 6.3 Detalhamento P1 (Sprint N+1)

| ID | Achado | Esforço | Responsável | Runbook |
|:---|:-------|:-------:|:-----------:|:-------:|
| ACH-009 | Confidence em 8 agentes | 8h | Backend | RM-10 |
| ACH-010 | Circuit breaker ATS clients | 6h | Backend | RM-11 |
| ACH-011 | Circuit breaker email/billing | 4h | Backend | RM-11 |
| ACH-012 | Few-shot examples | 12h | Backend | RM-17 |
| ACH-013 | Observabilidade Prometheus | 8h | Backend/Infra | RM-14 |
| ACH-014 | WorkOS circuit breaker | 2h | Backend | RM-11 |
| ACH-015 | Graceful degradation docs | 4h | Backend/Ops | RM-15 |

## 6.4 Verificação de Crenças

| Crença | Status | Achados Relacionados |
|:-------|:------:|:---------------------|
| 01 — Humano em Primeiro Lugar | PARCIAL | ACH-005 (HITL ausente em sourcing/communication) |
| 02 — Justa e Não-Discriminatória | PARCIAL | ACH-002 (FairnessGuard não é middleware universal) |
| 03 — Transparente e Explicável | OK | Explainability panel implementado |
| 04 — Segura e Respeitosa com Privacidade | PARCIAL | ACH-003 (consent soft), ACH-008 (multi-tenant) |
| 05 — Construída por Humanos, Para Humanos | OK | Audit trimestrais previstas no playbook |
| 06 — Em Melhoria Contínua | PARCIAL | ACH-029 (model drift não implementado) |
| 07 — Resiliente por Design | PARCIAL | ACH-004, ACH-010, ACH-011 (circuit breakers incompletos) |
| 08 — Observável e Rastreável | PARCIAL | ACH-006, ACH-013 (audit trail e observabilidade parciais) |
| 09 — Consciente de Custos | OK | Token budget, LLM cascade, pre-call check implementados |
| 10 — Inteligência vs Determinismo | OK | ConfidencePolicyService com 3 níveis implementado |
| 11 — Anti-Bajulação | **FALHA** | ACH-001 (6 agentes sem anti-sycophancy) |
| 12 — Autonomia Progressiva | OK | Autonomy engine implementado |
| 13 — Acessível e Inclusiva | **FALHA** | ACH-007 (WCAG 16.5% cobertura) |

## 6.5 Verificação de Inegociáveis

| # | Inegociável | Status | Achado |
|:--|:-----------|:------:|:-------|
| 1 | WSI explicável | OK | Rationale implementado em wsi_service |
| 2 | Review gate em rejeição | PARCIAL | ACH-005 |
| 3 | FairnessGuard 100% | **FALHA** | ACH-002 |
| 4 | PII masking todos os logs | OK | Global filter instalado |
| 5 | Consent antes de processamento | **FALHA** | ACH-003 |
| 6 | Dados deletados (SLA 15 dias) | OK | DSR + cleanup implementados |
| 7 | Human override sempre disponível | OK | UI permite override |
| 8 | WCAG 2.1 AA | **FALHA** | ACH-007 |

## 6.6 Production Readiness Gate (18 Critérios)

| # | Critério | Status |
|:--|:---------|:------:|
| 1 | Circuit Breaker em serviços externos | **FALHA** (ACH-004, ACH-010, ACH-011) |
| 2 | LLM fallback chain testada | OK |
| 3 | PII Masking ativo em todos os logs | OK |
| 4 | Rate Limiting por tenant | OK |
| 5 | Dead Letter Queue | OK |
| 6 | Token budget por company | OK |
| 7 | Consent management ativo | PARCIAL (ACH-003) |
| 8 | FairnessGuard ativo em todas as interações | **FALHA** (ACH-002) |
| 9 | Bias audit baseline | **FALHA** (ACH-022) |
| 10 | Health check endpoint | OK |
| 11 | Error alerting (P0/P1) | OK (Sentry) |
| 12 | Backup verificado | **FALHA** (ACH-024) |
| 13 | Rollback documentado | **FALHA** (ACH-024) |
| 14 | Load test (P95 < 5s) | **FALHA** (ACH-023) |
| 15 | Security scan limpo | **FALHA** (ACH-025) |
| 16 | LGPD compliance checklist | PARCIAL |
| 17 | WCAG 2.1 AA | **FALHA** (ACH-007) |
| 18 | PII Masking global | OK |

**Score: 9/18 OK, 2 PARCIAL, 7 FALHA**

---

*Relatório gerado por auditoria automatizada seguindo PLAYBOOK_AUDITORIA_PROFUNDA.md (4838 linhas, 44 runbooks de remediação). Todas as evidências baseadas em análise real do código-fonte.*
