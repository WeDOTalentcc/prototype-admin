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
| **LLM Providers** | Claude (Anthropic), Gemini (Google), OpenAI — fallback chain `llm_factory.py:L13` `FALLBACK_ORDER = ["claude", "gemini", "openai"]` | `app/shared/providers/` |
| **Orquestrador** | CascadedRouter (6 tiers) + ReAct Agent Registry | `app/orchestrator/` |
| **Mensageria** | RabbitMQ (async events) | `app/shared/messaging/` |
| **Cache** | Redis (token budgets, embeddings, circuit breakers) | `app/services/` |
| **Observabilidade** | Sentry + Prometheus metrics + LangSmith | `app/observability/`, `app/core/sentry.py` |
| **ATS Integrations** | Gupy, PandaPé, StackOne, Merge | `app/services/ats_clients/` |

### Métricas de Escala

| Métrica | Valor |
|:--------|:------|
| Domínios de agente | 14 (sourcing, job_management, cv_screening, pipeline, recruiter_assistant ×3, hiring_policy, policy, interview_scheduling, analytics, communication, automation, ats_integration) |
| Agentes registrados | 12 (11 ReAct + 1 Graph/LangGraph) |
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

### Policy
| Camada | Componente |
|:-------|:-----------|
| Agent | `PolicyAgent` → `app/domains/policy/agents/agent.py` (L1-L371) |
| System Prompt | `app/domains/policy/agents/system_prompt.py` (L1-L55) |
| Tool Registry | `app/domains/policy/agents/tool_registry.py` (L1-L8) |
| Stage Context | `app/domains/policy/agents/stage_context.py` (L1-L306) |
| **Nota** | Domínio duplica funcionalidade de `hiring_policy` — ver ACH-016 |

### Interview Scheduling (Graph Agent)
| Camada | Componente |
|:-------|:-----------|
| Agent | `InterviewGraph` → `app/domains/interview_scheduling/agents/interview_graph.py` (L1-L381) — **Graph agent** (LangGraph), não ReAct |
| Nodes | `app/domains/interview_scheduling/agents/interview_scheduling_nodes.py` (L1-L418) |
| System Prompt | `app/prompts/domains/interview_scheduling.yaml` (L1-L70) |
| State Schema | `app/schemas/interview_scheduling_state.py` (L1-L181) |
| Services | `scheduling_service.py` (L1-L1059), `calendar_service.py` (L1-L423), `deepgram_service.py` (L1-L350), `interview_transcript_analysis_service.py` (L1-L1035) |
| Models | `interview.py` (L1-L163), `self_scheduling.py` (L1-L175) |

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
- Audit trail parcial via `audit_service.log_decision` (`sourcing_react_agent.py:L151-L167`, `L333-L348`)

**O que NÃO faz (gaps):**
- Anti-sycophancy: AUSENTE — grep por `sycophancy|bajula|contra.argument` em `sourcing_system_prompt.py` (188 linhas) retorna 0 resultados
- Confidence calibration: AUSENTE — grep por `confidence|APPLY_SILENT` em `sourcing_system_prompt.py` retorna 0 resultados
- HITL: AUSENTE — grep por `human_review|HumanReview|HITL|flag_for_review` em `sourcing_react_agent.py` retorna 0 resultados
- FairnessGuard no system prompt: referência apenas via `ethical_guidelines` genérico do YAML shared

**Problemas identificados:**
- `sourcing_system_prompt.py` (188 linhas) — sem seção anti-sycophancy (Crença 11 violada)
- `sourcing_react_agent.py` — FairnessGuard via mixin inconsistente vs. Pipeline que faz call manual com `check()` + `check_implicit_bias()` + `log_check()`
- Pearch service tem circuit breaker (OK via `@circuit_breaker_decorator(PEARCH_CIRCUIT)`), mas falta fallback chain se Pearch falhar

## 2.2 Job Management (Wizard) Agent

**O que faz:**
- Criação guiada de vagas (wizard multi-step)
- Geração de JD (Job Description) com IA
- ConfidencePolicy para campos inferidos (APPLY_SILENT/APPLY_NOTIFY/ASK_USER)
- Templates e importação de JDs
- Analytics de vagas

**O que NÃO faz (gaps):**
- FairnessGuard no output de JD: apenas na entrada do wizard (via `_fairness_pre_check`), não verifica JD gerada

**Status:**
- Anti-sycophancy: OK (presente no system prompt — `wizard_system_prompt.py:L150`)
- FairnessGuard: OK (via `_fairness_pre_check` no process — `wizard_react_agent.py:L147`)
- Confidence: OK (ConfidencePolicyService integrado via `wizard_step_service.py`)
- HITL: OK (ASK_USER para low confidence < 0.70)

## 2.3 CV Screening (Pipeline) Agent

**O que faz:**
- Triagem de CVs via WSI (Weighted Scoring Index)
- 4 dimensões canônicas: technical (50%), behavioral (20%), gap_analysis (15%), contextual (15%)
- Scoring determinístico + LLM
- Geração de perguntas WSI
- Pipeline de screening completo

**O que NÃO faz (gaps):**
- Anti-sycophancy: AUSENTE no system prompt direto — grep por `sycophancy|bajula` em `pipeline_system_prompt.py` (186 linhas) retorna 0 resultados
- O screening pipeline carrega via YAML shared (`cv_screening.yaml`) que tem referência genérica, mas o arquivo de domínio não tem menção direta

**Problemas identificados:**
- `pipeline_system_prompt.py` (186 linhas) — sem seção anti-sycophancy explícita
- FairnessGuard: referenciado no YAML shared (`cv_screening.yaml` L54: "Não rejeite candidato sem checar FairnessGuard")
- HITL: OK — revisão humana para zona de fronteira (60-70%)

## 2.4 Recruiter Assistant (Talent)

**O que faz:**
- Assistente conversacional para recrutador
- Busca e análise de candidatos
- Comparação de candidatos

**Status:**
- Anti-sycophancy: OK (presente em `talent_system_prompt.py` — detectado via grep)
- FairnessGuard: OK (via mixin `_fairness_pre_check`)
- Confidence: PARCIAL — sem confidence score explícito no output do system prompt
- HITL: AUSENTE — grep por `human_review|flag_for_review` retorna 0 resultados

## 2.5 Recruiter Assistant (Kanban)

**O que faz:**
- Gestão do kanban de pipeline
- Movimentação de candidatos entre etapas
- Ações em lote

**Status:**
- Anti-sycophancy: OK (presente em `kanban_system_prompt.py`)
- FairnessGuard: OK (via mixin)
- LLM Fallback: OK (Claude→Gemini implementado e testado — `tests/unit/test_kanban_llm_fallback.py`)
- Rate limiting: OK (integrado no `kanban_react_agent.py`)

## 2.6 Recruiter Assistant (Jobs Management)

**O que faz:**
- Gestão de vagas existentes
- Edição, clonagem, fechamento

**Status:**
- Anti-sycophancy: OK (presente em `jobs_mgmt_system_prompt.py`)
- FairnessGuard: OK (via mixin)

## 2.7 Pipeline Transition Agent

**O que faz:**
- Transição de candidatos entre etapas do pipeline
- Validação de regras de negócio
- Feedback ao candidato

**Status:**
- FairnessGuard: OK (manual call com `guard.check(message)` em `pipeline_transition_agent.py:L159` + `check_implicit_bias()` em `L188` + `log_check()`)
- HITL: OK (integrado com `human_review_sampling_service`)
- Anti-sycophancy: OK (presente em `pipeline_system_prompt.py`)

## 2.8 Hiring Policy Agent

**O que faz:**
- Configuração e validação de políticas de contratação
- Guardrails de processo

**Status:**
- Anti-sycophancy: OK (presente em `policy_system_prompt.py`)
- FairnessGuard: OK (manual call — `policy_react_agent.py:L138`)

## 2.9 Analytics Agent

**O que faz:**
- Relatórios e métricas de recrutamento
- Análises preditivas

**Problemas:**
- Anti-sycophancy: AUSENTE — grep em `analytics_system_prompt.py` (47 linhas) retorna 0 resultados
- FairnessGuard: via mixin genérico, sem validação específica de outputs analíticos
- Audit trail: AUSENTE — grep por `audit_service|log_decision` em `analytics_react_agent.py` retorna 0 resultados

## 2.10 Communication Agent

**O que faz:**
- Envio de comunicações (email, WhatsApp, SMS, Teams, in-app)
- Multi-channel routing
- Opt-out management
- Templates

**Problemas:**
- Anti-sycophancy: AUSENTE — grep em `communication_system_prompt.py` (53 linhas) retorna 0 resultados
- HITL: AUSENTE — grep por `human_review|flag_for_review` em `communication_react_agent.py` retorna 0 resultados
- Audit trail: AUSENTE — grep por `audit_service|log_decision` em `communication_react_agent.py` retorna 0 resultados
- Rate limiting: OK (integrado)
- Opt-out: OK (implementado)

## 2.11 Automation Agent

**O que faz:**
- Automações de stage transition
- Triggers configuráveis
- Scheduler

**Problemas:**
- Anti-sycophancy: AUSENTE — grep em `automation_system_prompt.py` (36 linhas) retorna 0 resultados

## 2.12 ATS Integration Agent

**O que faz:**
- Sincronização com ATS externos (Gupy, PandaPé, StackOne, Merge)
- Webhook handling

**Problemas:**
- Anti-sycophancy: AUSENTE — grep em `ats_integration_system_prompt.py` (64 linhas) retorna 0 resultados
- Circuit breaker: AUSENTE nos ATS clients — grep por `circuit|Circuit` em `gupy.py`, `pandape.py`, `stackone.py`, `merge.py` retorna 0 resultados em todos
- Audit trail: AUSENTE — grep por `audit_service|log_decision` em `ats_integration_react_agent.py` retorna 0 resultados

## 2.13 Policy Agent

**O que faz:**
- Agente genérico de políticas (duplica parcialmente `hiring_policy`) — `app/domains/policy/agents/agent.py` (L1-L371)
- Avaliação de conformidade com políticas empresariais

**Problemas:**
- Anti-sycophancy: OK — presente em `system_prompt.py` (L1-L55)
- FairnessGuard: OK — chamada manual em `agent.py`
- Audit trail: AUSENTE — grep por `audit_service|log_decision` em `agent.py` (L1-L371) retorna 0 resultados
- HITL: AUSENTE — sem gate de revisão humana
- Domínio duplicado com `hiring_policy` — ver ACH-016

## 2.14 Interview Scheduling Agent (Graph)

**O que faz:**
- Agendamento automatizado de entrevistas — `app/domains/interview_scheduling/agents/interview_graph.py` (L1-L381)
- **Arquitetura Graph (LangGraph)**, não ReAct — usa nós discretos em `interview_scheduling_nodes.py` (L1-L418)
- Integração com calendários via `calendar_service.py` (L1-L423)
- Transcrição de entrevistas via `deepgram_service.py` (L1-L350) e análise via `interview_transcript_analysis_service.py` (L1-L1035)
- Self-scheduling pelo candidato via `self_scheduling.py` (L1-L175)

**Problemas:**
- Anti-sycophancy: NÃO AVALIADO — usa prompt YAML (`interview_scheduling.yaml`, L1-L70), padrão diferente dos system prompts .py
- FairnessGuard: AUSENTE — sem referência a `fairness_guard` em `interview_graph.py` (L1-L381) ou `interview_scheduling_nodes.py` (L1-L418)
- Audit trail: AUSENTE — grep por `audit_service|log_decision` em `interview_graph.py` (L1-L381) retorna 0 resultados
- HITL: AUSENTE — agendamento pode ocorrer sem revisão humana
- Few-shot: AUSENTE — `interview_scheduling.yaml` (70 linhas) sem exemplos conversacionais
- Circuit breaker: NÃO VERIFICADO — `scheduling_service.py` (L1-L1059) e `calendar_service.py` (L1-L423) fazem chamadas externas sem circuit breaker visível

---

# SEÇÃO 3: AUDITORIA MULTI-DIMENSIONAL (14 Dimensões × 14 Agentes)

## 3.1 Tabela Resumo — 14 Dimensões

| Dimensão | Sourcing | Wizard | CV Screen | Talent | Kanban | Jobs Mgmt | Pipeline Trans | H.Policy | Policy | Interv.Sched | Analytics | Communic. | Automation | ATS Integ. |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1. Wiring/Integração | OK | OK | OK | OK | OK | OK | OK | OK | PARCIAL | OK | OK | OK | OK | OK |
| 2. Data Flow | OK | OK | OK | OK | OK | OK | OK | OK | PARCIAL | OK | OK | OK | OK | OK |
| 3. UI/UX + Design System | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| 4. Backend/API | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| 5. Types/Contracts | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| 6. User Flow | OK | OK | OK | OK | OK | OK | OK | OK | PARCIAL | OK | PARCIAL | OK | PARCIAL | PARCIAL |
| 7. Consistência | PARCIAL | OK | OK | OK | OK | OK | OK | **FALHA** | PARCIAL | OK | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| 8. Documentação | PARCIAL | OK | OK | PARCIAL | PARCIAL | PARCIAL | OK | OK | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| 9. Arquitetura de Agentes | OK | OK | OK | OK | OK | OK | OK | OK | PARCIAL | OK | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| 10. Qualidade LLM | **FALHA** | OK | **FALHA** | PARCIAL | OK | OK | OK | OK | PARCIAL | **FALHA** | **FALHA** | **FALHA** | **FALHA** | **FALHA** |
| 11. Serviços IA/Integrações | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | **FALHA** |
| 12. Governança/Resiliência | **FALHA** | OK | OK | PARCIAL | OK | PARCIAL | OK | OK | **FALHA** | **FALHA** | PARCIAL | **FALHA** | PARCIAL | **FALHA** |
| 13. Segurança/Dados | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | OK | OK | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| 14. Performance/Escalab. | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL | PARCIAL |

## 3.2 Tabela de Verificações Críticas (Checks Transversais)

| Verificação | Sourcing | Wizard | CV Screen | Talent | Kanban | Jobs Mgmt | Pipeline Trans | H.Policy | Policy | Interv.Sched | Analytics | Communic. | Automation | ATS Integ. |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Anti-Sycophancy | **FALHA** | OK | **FALHA** | OK | OK | OK | OK | OK | OK | N/A | **FALHA** | **FALHA** | **FALHA** | **FALHA** |
| FairnessGuard Middleware | PARCIAL | OK | OK | OK | OK | OK | OK | OK | OK | **FALHA** | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| Negation Detection | AUSENTE | AUSENTE | OK | AUSENTE | AUSENTE | AUSENTE | OK | OK | AUSENTE | AUSENTE | AUSENTE | AUSENTE | AUSENTE | AUSENTE |
| Confiança Real | **FALHA** | OK | OK | **FALHA** | **FALHA** | **FALHA** | OK | OK | PARCIAL | **FALHA** | **FALHA** | **FALHA** | **FALHA** | **FALHA** |
| Circuit Breaker Direto | OK | PARCIAL | PARCIAL | PARCIAL | OK | PARCIAL | PARCIAL | PARCIAL | PARCIAL | **FALHA** | PARCIAL | PARCIAL | PARCIAL | **FALHA** |
| Pre-call Budget Check | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| PII Masking | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Consent Check | N/A | N/A | PARCIAL | N/A | N/A | N/A | N/A | N/A | N/A | PARCIAL | N/A | PARCIAL | N/A | N/A |
| Multi-Tenant Isolation | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Audit Trail | OK | OK | OK | OK | OK | OK | OK | OK | **FALHA** | **FALHA** | **FALHA** | **FALHA** | OK | **FALHA** |
| Observabilidade | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Token Tracking | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| HITL Enforcement | **FALHA** | OK | OK | **FALHA** | PARCIAL | PARCIAL | OK | OK | **FALHA** | **FALHA** | N/A | **FALHA** | PARCIAL | N/A |

## 3.2 Detalhamento por Dimensão

### Dimensão 1 — Wiring/Integração

**Status:** PARCIAL

- Orquestrador CascadedRouter (6 tiers) → bem implementado, custo otimizado
- Domain Registry com auto-discovery via decorator → OK
- ReAct Agent Registry → 11 agentes registrados → OK
- **Gap:** Orquestrador Phase 1 (ActionExecutor) pode bypassar FairnessGuard em atalhos
- **Evidência:** `orchestrator.py:L104` (`process_request`) — short-cut commands processados antes do domain agent

### Dimensão 2 — Data Flow

**Status:** OK

- Dados fluem: Frontend → API → Orchestrator → Domain Agent → Services → DB
- PII stripping antes de enviar ao LLM (`strip_pii_for_llm_prompt`)
- Token budget check antes de cada invocação LLM no WebSocket (`agent_chat_ws.py:L459` — `check_budget(company_id, _plan)`)

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
- `DomainWorkflow` (`app/domains/workflow.py:L83-L109`) com FairnessGuard automático (flag `enable_fairness_guard=True`)
- Prompt YAML loading com versioning
- Memory: conversation_memory + working_memory + long_term_memory
- Autonomy engine com níveis progressivos

### Dimensão 10 — Qualidade LLM

**Status:** PARCIAL

- Anti-sycophancy block existe com 3 variantes (OPERATIONAL, FULL, ORCHESTRATOR)
- **Gap crítico:** 6 de 14 agentes NÃO incluem anti-sycophancy no system prompt (+ interview_scheduling não avaliado — prompt YAML)
- Few-shot examples: biblioteca extensiva em `app/shared/prompts/examples/`
- Defensive prompts: ambiguity detection + out-of-scope handling
- **Gap:** Negation detection não é universal (apenas em cv_screening, pipeline, policy)
- **Gap:** Confidence calibration ausente em 10 de 14 agentes

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
  - **Evidência:** `enhanced_agent_mixin.py:L212-L231` — `_fairness_pre_check` é opt-in via mixin, não forçado no entry-point do Orchestrator (`orchestrator.py:L104`)
  - **Gap:** Orchestrator ActionExecutor pode bypassar em short-cut commands
- Circuit breaker: implementado mas incompleto
  - OK: Claude (`llm_claude.py:L59,L88` — `@circuit_breaker_decorator(ANTHROPIC_CIRCUIT)`), Pearch, Google Calendar, Deepgram, OpenMic
  - FALHA: OpenAI (`llm_openai.py` — grep `circuit` retorna 0), Gemini (`llm_gemini.py` — grep `circuit` retorna 0), ATS clients (`gupy.py`, `pandape.py`, `stackone.py`, `merge.py` — grep `circuit` retorna 0 em todos), Email/Billing providers, WorkOS (`workos.py` 1662 linhas — grep `circuit` retorna 0)
- Human Review: 5% sampling + always-review types + low confidence → OK para pipeline
  - **Gap:** Não integrado em sourcing (`sourcing_react_agent.py` — grep `human_review` retorna 0), communication (`communication_react_agent.py` — grep `human_review` retorna 0)
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
- **Gap:** Consent check é "soft enforcement" — `consent_checker_service.py:L105` (`LGPD_CONSENT_ABSENT_HARD_BLOCK` default False), `L136-L141` (absent → `allowed=True`, `soft_warning=True`)
- **Gap:** Multi-tenant isolation: via `company_id` em queries (`rate_limiter.py:L90`), não via Row Level Security no DB
- **Gap:** Rate limiting: HTTP level OK, mas token-level por tenant apenas no chat WebSocket (`agent_chat_ws.py:L459`)

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
| Audit Trail | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Circuit Breaker | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ❌ |
| Few-shot Examples | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Stage Context | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| LLM Fallback | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Token Tracking | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Opt-out | ✅ | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | ✅ | N/A | N/A |

## 4.2 Padrões que Deveriam Ser Universais

### Nível 1 — Obrigatório em TODOS (hoje ausente em muitos)
1. **Anti-sycophancy** — Crença #11 exige em TODOS os prompts. Hoje: 6/14 agentes (~43%) → **FALHA CRÍTICA**
2. **FairnessGuard como middleware automático** — Hoje é opt-in via mixin → deveria ser forçado no Orchestrator
3. **Confidence score em outputs** — Hoje: 4/14 agentes reportam confiança
4. **HITL gate para ações de alto impacto** — Hoje: inconsistente entre agentes

### Nível 2 — Obrigatório em agentes que tocam candidatos
1. **Negation detection** — Apenas 3 agentes (cv_screening, pipeline, policy)
2. **Consent check antes de processar** — Apenas no screening, soft enforcement
3. **Audit trail em todas as decisões** — 8/14 agentes com trail completo (policy e interview_scheduling ausentes)

### Nível 3 — Desejável para maturidade
1. **Few-shot examples** — 5/14 agentes com exemplos (interview_scheduling também ausente)
2. **Stage context** — 8/14 agentes com contexto de etapa
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

### ACH-001 — Anti-Sycophancy ausente em 6+ de 14 agentes
- **Prioridade:** P0
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-08
- **Arquivo(s) afetado(s):**
  - `sourcing_system_prompt.py` (188 linhas — grep `sycophancy|bajula|contra.argument` retorna 0)
  - `pipeline_system_prompt.py` (186 linhas — grep `sycophancy|bajula` retorna 0)
  - `communication_system_prompt.py` (53 linhas — grep `sycophancy` retorna 0)
  - `analytics_system_prompt.py` (47 linhas — grep `sycophancy` retorna 0)
  - `ats_integration_system_prompt.py` (64 linhas — grep `sycophancy` retorna 0)
  - `automation_system_prompt.py` (36 linhas — grep `sycophancy` retorna 0)
- **Referência positiva:** `wizard_system_prompt.py:L150` — anti-sycophancy presente
- **Descrição:** Crença #11 do Manifesto WeDO Talent exige anti-sycophancy em TODOS os prompts sem exceção. 6 system prompts de domínio não incluem a seção. O bloco existe em `anti_sycophancy_block.py` mas não é injetado nos prompts destes domínios.
- **Impacto se não corrigido:** IA concorda silenciosamente com pedidos problemáticos do recrutador, comprometendo qualidade das contratações e fairness.
- **Esforço estimado:** 4h — Backend (LLM/Prompts)
- **Depende de:** Nenhum

### ACH-002 — FairnessGuard não é middleware automático universal
- **Prioridade:** P0
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-02
- **Arquivo(s) afetado(s):**
  - `enhanced_agent_mixin.py:L212-L231` — `_fairness_pre_check` é método opt-in, não interceptor automático
  - `orchestrator.py:L104` — `process_request` pode processar sem chamar FairnessGuard
- **Descrição:** O playbook exige que FairnessGuard seja middleware automático que intercepta TODAS as interações (Inegociável #3). Atualmente é opt-in via mixin — agentes devem chamar `_fairness_pre_check` manualmente. O Orchestrator Phase 1 (ActionExecutor) pode processar short-cut commands sem passar pelo guard.
- **Impacto se não corrigido:** Queries discriminatórias podem bypassar o guard se agente não chamar manualmente.
- **Esforço estimado:** 8h — Backend (Orchestrator)
- **Depende de:** Nenhum

### ACH-003 — Consent check em modo soft enforcement
- **Prioridade:** P0
- **Dimensão:** 13 (Segurança/Dados)
- **Runbook:** RM-04
- **Arquivo(s) afetado(s):**
  - `consent_checker_service.py:L8` — docstring confirma: "consent ausente → aviso + audit log + CONTINUA"
  - `consent_checker_service.py:L105` — `_hard_block = settings.LGPD_CONSENT_ABSENT_HARD_BLOCK` (default False)
  - `consent_checker_service.py:L136-L141` — quando absent: `event="consent_absent_soft_warning"`, `allowed=True`, `soft_warning=True`
- **Descrição:** Quando consentimento está AUSENTE (não revogado, mas não dado), o sistema faz soft warning e permite processamento. LGPD Art. 7 exige base legal ANTES do processamento. A env `LGPD_CONSENT_ABSENT_HARD_BLOCK` existe mas default é False.
- **Impacto se não corrigido:** Processamento de dados sem base legal registrada — violação LGPD.
- **Esforço estimado:** 4h — Backend (Compliance)
- **Depende de:** Nenhum

### ACH-004 — Circuit breaker ausente em OpenAI e Gemini providers
- **Prioridade:** P0
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-10
- **Arquivo(s) afetado(s):**
  - `llm_openai.py` — grep por `circuit_breaker|CircuitBreaker|@circuit` retorna 0 resultados
  - `llm_gemini.py` — grep por `circuit_breaker|CircuitBreaker|@circuit` retorna 0 resultados
  - **Referência positiva:** `llm_claude.py:L8` (import `circuit_breaker_decorator`), `L59` e `L88` (`@circuit_breaker_decorator(ANTHROPIC_CIRCUIT)`)
- **Descrição:** Circuits `OPENAI_CIRCUIT` e `GEMINI_CIRCUIT` estão DEFINIDOS no registry mas não decorados nos providers. Quando Claude cai e fallback vai para Gemini/OpenAI, esses providers operam sem proteção de circuit breaker.
- **Impacto se não corrigido:** Falha em cascata quando provider LLM fica instável. Custos descontrolados com retries infinitos.
- **Esforço estimado:** 4h — Backend (Resiliência)
- **Depende de:** Nenhum

### ACH-005 — HITL ausente em sourcing e communication
- **Prioridade:** P0
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-03
- **Arquivo(s) afetado(s):**
  - `app/domains/sourcing/agents/sourcing_react_agent.py` (L1-L702) — nenhuma referência a `human_review`, `HumanReview`, `HITL`, ou `flag_for_review`
  - `app/domains/communication/agents/communication_react_agent.py` (L1-L253) — idem
- **Descrição:** Inegociável #2 exige review gate para decisões de alto impacto. Sourcing pode engajar candidatos sem revisão humana. Communication pode enviar mensagens sem aprovação (parcial — tem opt-out mas não HITL no envio).
- **Impacto se não corrigido:** Contato com candidatos sem supervisão humana — violação de Crença #1 (Humano em Primeiro Lugar).
- **Esforço estimado:** 8h — Backend (Agentes)
- **Depende de:** Nenhum

### ACH-006 — Audit trail incompleto em 5 agentes
- **Prioridade:** P0
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-05
- **Arquivo(s) afetado(s):**
  - `analytics_react_agent.py` — grep por `audit_service|log_decision` retorna 0 resultados
  - `communication_react_agent.py` — grep por `audit_service|log_decision` retorna 0 resultados
  - `ats_integration_react_agent.py` — grep por `audit_service|log_decision` retorna 0 resultados
  - `app/domains/policy/agents/agent.py` (L1-L371) — grep por `audit_service|log_decision` retorna 0 resultados
  - `app/domains/interview_scheduling/agents/interview_graph.py` (L1-L381) — grep por `audit_service|log_decision` retorna 0 resultados
  - **Nota:** Sourcing TEM audit trail (`sourcing_react_agent.py:L151-L167`, `L333-L348`) — corrigido para 5 agentes
- **Descrição:** Crença #8 exige trilha de auditoria em toda saída de agente. 5 agentes não logam decisões no `audit_service`.
- **Impacto se não corrigido:** Decisões de IA sem rastreabilidade — violação EU AI Act (auditabilidade obrigatória).
- **Esforço estimado:** 6h — Backend (Compliance)
- **Depende de:** Nenhum

### ACH-007 — Acessibilidade (WCAG 2.1 AA) abaixo do requerido
- **Prioridade:** P0
- **Dimensão:** 3 (UI/UX)
- **Runbook:** RM-27
- **Arquivo(s) afetado(s):**
  - `plataforma-lia/src/components/` — 466 arquivos .tsx escaneados (L1-Lfim de cada)
  - Com `aria-label`: 60/466 (12.9%) — grep retorna 60 arquivos
  - Com `sr-only`: 12/466 (2.6%) — grep retorna 12 arquivos
  - Com `focus-visible`: 24/466 (5.2%) — grep retorna 24 arquivos
  - 406 componentes sem nenhum atributo de acessibilidade (aria-label, sr-only, focus-visible)
- **Descrição:** Inegociável #8 exige WCAG 2.1 AA em todas as interfaces. Apenas ~16.5% dos componentes têm algum atributo WCAG. Falta verificação sistemática de contraste, navegação por teclado, screen reader.
- **Impacto se não corrigido:** Plataforma inacessível para pessoas com deficiência — violação Crença #13 e Lei 13.146/15.
- **Esforço estimado:** 40h — Frontend
- **Depende de:** Nenhum

### ACH-008 — Multi-tenant sem Row Level Security
- **Prioridade:** P0
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-06
- **Arquivo(s) afetado(s):**
  - `rate_limiter.py:L90` — `check_rate_limit(self, user_id: str, company_id: str)` — isolamento via filtro application-level
  - `database.py` — sem configuração de RLS
  - Modelos SQLAlchemy: `company_id` como coluna FK, não como RLS policy
- **Descrição:** Isolamento multi-tenant implementado via filtro `company_id` nas queries (application-level). Sem Row Level Security (RLS) no PostgreSQL. Um bug em qualquer query pode expor dados de outro tenant.
- **Impacto se não corrigido:** Vazamento de dados entre tenants — violação LGPD, SOC-2, ISO-27001.
- **Esforço estimado:** 16h — Backend/Infra (Database)
- **Depende de:** Nenhum

## P1 — Alto (Qualidade e Resiliência)

### ACH-009 — Confidence calibration ausente em 8 agentes
- **Prioridade:** P1
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-09
- **Arquivo(s) afetado(s):**
  - `app/domains/sourcing/agents/sourcing_system_prompt.py` (L1-L188) — nenhuma referência a `confidence`, `APPLY_SILENT`, `APPLY_NOTIFY` ou `ASK_USER`
  - `app/domains/recruiter_assistant/agents/talent_system_prompt.py` (L1-L176) — idem
  - `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` (L1-L186) — idem
  - `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` (L1-L185) — idem
  - `app/domains/analytics/agents/analytics_system_prompt.py` (L1-L47) — idem
  - `app/domains/communication/agents/communication_system_prompt.py` (L1-L53) — idem
  - `app/domains/automation/agents/automation_system_prompt.py` (L1-L36) — idem
  - `app/domains/ats_integration/agents/ats_integration_system_prompt.py` (L1-L64) — idem
  - **Referência positiva:** `app/services/confidence_policy_service.py` — serviço existe com 3 níveis (APPLY_SILENT ≥0.85, APPLY_NOTIFY 0.70-0.84, ASK_USER <0.70), mas 10/14 agentes não o invocam
- **Descrição:** EU AI Act Art. 13 exige que sistemas de alto risco reportem confiança. 10 de 14 agentes não reportam confidence score nos outputs.
- **Impacto se não corrigido:** Sem confiança, recrutador não sabe quando questionar a IA.
- **Esforço estimado:** 8h — Backend (LLM/Prompts)
- **Depende de:** Nenhum

### ACH-010 — Circuit breaker ausente em ATS clients
- **Prioridade:** P1
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-10
- **Arquivo(s) afetado(s):**
  - `app/services/ats_clients/gupy.py` (329 linhas) — nenhuma referência a `circuit_breaker` ou `@circuit` em L1-L329
  - `app/services/ats_clients/pandape.py` (341 linhas) — nenhuma referência a `circuit_breaker` em L1-L341
  - `app/services/ats_clients/stackone.py` (460 linhas) — nenhuma referência a `circuit_breaker` em L1-L460
  - `app/services/ats_clients/merge.py` (441 linhas) — nenhuma referência a `circuit_breaker` em L1-L441
  - **Referência positiva:** `llm_claude.py:L8,L59,L88` — padrão esperado com `@circuit_breaker_decorator`
- **Descrição:** 4 ATS clients usam httpx sem circuit breaker.
- **Impacto se não corrigido:** Falha de ATS externo causa timeout e degradação do sistema.
- **Esforço estimado:** 6h — Backend (Resiliência)
- **Depende de:** Nenhum

### ACH-011 — Circuit breaker ausente em email/billing providers
- **Prioridade:** P1
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-10
- **Arquivo(s) afetado(s):**
  - `app/services/email_providers/sendgrid_provider.py` (226 linhas) — sem `circuit_breaker` em L1-L226
  - `app/services/email_providers/resend_provider.py` (187 linhas) — sem `circuit_breaker` em L1-L187
  - `app/services/billing_providers/iugu_provider.py` (489 linhas) — sem `circuit_breaker` em L1-L489
  - `app/services/billing_providers/vindi_provider.py` (492 linhas) — sem `circuit_breaker` em L1-L492
- **Descrição:** SendGrid, Resend, Iugu, Vindi providers sem circuit breaker.
- **Impacto se não corrigido:** Falha de provider externo bloqueia comunicações e billing.
- **Esforço estimado:** 4h — Backend (Resiliência)
- **Depende de:** Nenhum

### ACH-012 — Few-shot examples ausentes em 7 agentes
- **Prioridade:** P1
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-14
- **Arquivo(s) afetado(s):**
  - `app/domains/recruiter_assistant/agents/talent_system_prompt.py` (L1-L176) — nenhuma seção `Recrutador:`/`LIA (thought):` de few-shot
  - `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` (L1-L186) — idem
  - `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` (L1-L185) — idem
  - `app/domains/analytics/agents/analytics_system_prompt.py` (L1-L47) — idem
  - `app/domains/communication/agents/communication_system_prompt.py` (L1-L53) — idem
  - `app/domains/automation/agents/automation_system_prompt.py` (L1-L36) — idem
  - `app/domains/ats_integration/agents/ats_integration_system_prompt.py` (L1-L64) — idem
  - **Referência positiva:** `wizard_system_prompt.py:L145-L155` — contém `Recrutador:` e `LIA (thought):`
  - **Referência positiva:** `sourcing_system_prompt.py` (L1-L188) — contém seção de exemplos
- **Descrição:** Few-shot examples melhoram significativamente a qualidade de output do LLM. 7 agentes não têm exemplos no prompt.
- **Impacto se não corrigido:** Output inconsistente e baixa qualidade em agentes sem exemplos.
- **Esforço estimado:** 12h — Backend (LLM/Prompts)
- **Depende de:** Nenhum

### ACH-013 — Observabilidade Prometheus parcial
- **Prioridade:** P1
- **Dimensão:** 14 (Performance)
- **Runbook:** RM-12
- **Arquivo(s) afetado(s):**
  - `app/observability/metrics.py` (130 linhas) — contém métricas para FairnessGuard e circuit breaker
  - L1-L130 escaneadas: nenhuma métrica com prefixo `agent_` ou `domain_` para tracking per-agent (latência, tokens, erros)
- **Descrição:** Métricas Prometheus existem para FairnessGuard e circuit breaker, mas faltam métricas por agente (latência, tokens, erros por domínio).
- **Impacto se não corrigido:** Sem visibilidade de performance por agente; difícil detectar regressões.
- **Esforço estimado:** 8h — Backend/Infra (Observabilidade)
- **Depende de:** Nenhum

### ACH-014 — WorkOS circuit breaker definido mas não implementado
- **Prioridade:** P1
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-10
- **Arquivo(s) afetado(s):**
  - `app/api/v1/workos.py` (L1-L1662) — nenhuma referência a `circuit_breaker`, `@circuit`, ou `CircuitBreaker` em 1662 linhas
  - `app/shared/resilience/circuit_breaker.py` — `WORKOS_CIRCUIT` definido no registry mas não importado/decorado no endpoint
- **Descrição:** `WORKOS_CIRCUIT` definido no registry mas endpoint usa httpx direto.
- **Impacto se não corrigido:** Falha de WorkOS (auth provider) bloqueia login de todos os users.
- **Esforço estimado:** 2h — Backend (Auth/Resiliência)
- **Depende de:** Nenhum

### ACH-015 — Degradação graceful sem documentação operacional
- **Prioridade:** P1
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-13
- **Arquivo(s) afetado(s):**
  - Fallback LLM existe: `llm_factory.py:L13` (`FALLBACK_ORDER = ["claude", "gemini", "openai"]`), `L55-L89` (`generate_with_fallback`)
  - Redis graceful: `token_budget_service.py:L87` — "Redis indisponível → permitir com warning"
  - Sentry graceful: `sentry.py:L11` — "módulo é gracefully degradável"
  - **Ausente:** Nenhum documento de runbook operacional mapeando componente→impacto_no_user→ação_ops. Nenhum arquivo `docs/RUNBOOK_DEGRADATION.md` ou similar encontrado
- **Descrição:** Sistema tem fallbacks (LLM cascade, circuit breakers) mas sem documentação de graceful degradation (o que o user vê quando cada componente falha).
- **Impacto se não corrigido:** Ops team sem playbook para incidentes.
- **Esforço estimado:** 4h — Backend/Ops (Documentação)
- **Depende de:** Nenhum

## P2 — Médio (Melhorias de Arquitetura)

### ACH-016 — Duplicação de domínio policy vs hiring_policy
- **Prioridade:** P2
- **Dimensão:** 7 (Consistência)
- **Runbook:** RM-42
- **Arquivo(s) afetado(s):**
  - `app/domains/policy/agents/system_prompt.py` (L1-L55) — prompt genérico
  - `app/domains/hiring_policy/agents/policy_system_prompt.py` (L1-L272) — prompt expandido com mesma finalidade
  - `app/domains/policy/agents/` (740 linhas total: agent.py, system_prompt.py, tool_registry.py, stage_context.py)
  - `app/domains/hiring_policy/agents/` (2376 linhas total: policy_react_agent.py, policy_system_prompt.py, policy_tool_registry.py, policy_stage_context.py)
- **Descrição:** Dois domínios para policy com padrões levemente diferentes.
- **Impacto se não corrigido:** Confusão de routing, manutenção duplicada.
- **Esforço estimado:** 8h — Backend (Arquitetura)
- **Depende de:** Nenhum

### ACH-017 — Tools duplicados entre app/tools e app/domains/*/tools
- **Prioridade:** P2
- **Dimensão:** 7 (Consistência)
- **Runbook:** RM-42
- **Arquivo(s) afetado(s):**
  - `app/tools/query_tools.py` (L1-Lfim) — tools legados em diretório flat (13 arquivos .py)
  - `app/domains/sourcing/tools/query_tools.py` (L1-Lfim) — mesma funcionalidade em estrutura por domínio
  - Duplicação potencial em sourcing, cv_screening, pipeline onde ambos os diretórios existem
- **Descrição:** Mesmos tools existem em dois locais (legado em `app/tools/`, novo em `app/domains/*/tools/`).
- **Impacto se não corrigido:** Edição no lugar errado não tem efeito; riscos de divergência.
- **Esforço estimado:** 6h — Backend (Refatoração)
- **Depende de:** Nenhum

### ACH-018 — Mock data em páginas admin de produção
- **Prioridade:** P2
- **Dimensão:** 3 (UI/UX)
- **Runbook:** RM-35
- **Arquivo(s) afetado(s):**
  - `plataforma-lia/src/app/admin/clientes/[clientId]/usuarios/page.tsx:L73` — `const mockUsers: User[] = [` hardcoded
  - `plataforma-lia/src/app/admin/clientes/[clientId]/usuarios/page.tsx:L160,L163,L167` — `setUsers(mockUsers)` em produção
  - `plataforma-lia/src/app/admin/clientes/[clientId]/faturamento/page.tsx:L84` — `const MOCK_BILLING_DATA: BillingData = {` hardcoded
- **Descrição:** `MOCK_BILLING_DATA`, `mockUsers` hardcoded em componentes admin que deveriam mostrar dados reais.
- **Impacto se não corrigido:** Admin vê dados falsos, decisões baseadas em informação incorreta.
- **Esforço estimado:** 12h — Frontend
- **Depende de:** Nenhum

### ACH-019 — Stage context: arquivos existem mas não integrados em 4 agentes
- **Prioridade:** P2
- **Dimensão:** 9 (Arquitetura de Agentes)
- **Runbook:** RM-19
- **Arquivo(s) afetado(s):**
  - `app/domains/analytics/agents/analytics_stage_context.py` (L1-L79) — arquivo existe mas não importado em `analytics_react_agent.py`
  - `app/domains/communication/agents/communication_stage_context.py` (L1-L64) — idem
  - `app/domains/automation/agents/automation_stage_context.py` (L1-L46) — idem
  - `app/domains/ats_integration/agents/ats_integration_stage_context.py` (L1-L67) — idem
- **Descrição:** Stage context files existem mas podem não estar integrados no fluxo de execução dos agentes menores.
- **Impacto se não corrigido:** Agentes com contexto de pipeline disponível mas potencialmente não utilizado.
- **Esforço estimado:** 4h — Backend (Agentes)
- **Depende de:** Nenhum

### ACH-020 — Documentação de API incompleta
- **Prioridade:** P2
- **Dimensão:** 8 (Documentação)
- **Runbook:** RM-43
- **Arquivo(s) afetado(s):**
  - `app/api/v1/` — 210 arquivos de endpoint
  - Exemplo: `app/api/v1/workos.py:L186` — `@public_auth_router.get("/check-sso-domain")` sem `description=`
  - Exemplo: `app/api/v1/workos.py:L257` — `@auth_router.post("/sync-user")` sem documentação de exemplos
- **Descrição:** Muitos endpoints sem OpenAPI descriptions, examples, response schemas.
- **Impacto se não corrigido:** Integrações externas difíceis de implementar.
- **Esforço estimado:** 20h — Backend (Documentação)
- **Depende de:** Nenhum

### ACH-021 — Negation detection não universal
- **Prioridade:** P2
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-17
- **Arquivo(s) afetado(s):**
  - **Referência positiva:** `app/shared/prompts/job_wizard.py:L278` — `rejection: Rejeição/negação de sugestão`
  - `app/domains/sourcing/agents/sourcing_system_prompt.py` (L1-L188) — sem negation detection
  - `app/domains/recruiter_assistant/agents/talent_system_prompt.py` (L1-L176) — idem
  - `app/domains/recruiter_assistant/agents/kanban_system_prompt.py` (L1-L186) — idem
  - `app/domains/recruiter_assistant/agents/jobs_mgmt_system_prompt.py` (L1-L185) — idem
  - `app/domains/analytics/agents/analytics_system_prompt.py` (L1-L47) — idem
  - `app/domains/communication/agents/communication_system_prompt.py` (L1-L53) — idem
  - `app/domains/automation/agents/automation_system_prompt.py` (L1-L36) — idem
  - `app/domains/ats_integration/agents/ats_integration_system_prompt.py` (L1-L64) — idem
- **Descrição:** Detecção de negação (quando recrutador diz "não quero X") implementada parcialmente no wizard. Outros agentes podem interpretar incorretamente pedidos negativos.
- **Impacto se não corrigido:** IA inclui candidatos que deveriam ser excluídos (ou vice-versa).
- **Esforço estimado:** 6h — Backend (LLM/Prompts)
- **Depende de:** ACH-001

### ACH-022 — Bias audit baseline não verificável em runtime
- **Prioridade:** P2
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-23
- **Arquivo(s) afetado(s):**
  - `app/services/bias_audit_service.py` (289 linhas) — serviço implementado com métricas de viés
  - `app/api/v1/bias_audit.py` (148 linhas) — endpoints REST existem
  - L1-L289 de `bias_audit_service.py` e L1-L148 de `bias_audit.py` escaneadas: nenhuma referência a `golden_dataset`, `baseline_candidates` ou `representative_sample` (Production Readiness #9 exige 100 candidatos baseline)
- **Descrição:** Bias audit service e API existem, mas sem Golden Dataset de 100 candidatos representativos para baseline automático.
- **Impacto se não corrigido:** Sem baseline, impossível detectar drift de viés.
- **Esforço estimado:** 16h — Backend (Compliance/Data)
- **Depende de:** Nenhum

### ACH-023 — Load test existente mas sem integração CI e sem evidência de execução
- **Prioridade:** P2
- **Dimensão:** 14 (Performance)
- **Runbook:** RM-44
- **Arquivo(s) afetado(s):**
  - `tests/load/locustfile.py` (L1-L9844) — configuração Locust existe
  - `tests/load/load_test_config.py` (L1-L2982) — config complementar existe
  - `tests/load/README.md` — documentação mínima
  - Nenhum `.github/workflows/` ou CI step referenciando load tests encontrado
  - Production Readiness #14 exige P95 < 5s em carga — sem relatório de execução
- **Descrição:** Load tests existem (Locust) mas sem evidência de execução regular, integração CI, ou relatório de resultados.
- **Impacto se não corrigido:** Load tests não executados regularmente perdem efetividade.
- **Esforço estimado:** 4h — Infra/QA
- **Depende de:** Nenhum

### ACH-024 — Backup e rollback não documentados
- **Prioridade:** P2
- **Dimensão:** 14 (Performance)
- **Runbook:** RM-44
- **Arquivo(s) afetado(s):**
  - `docs/` (65+ arquivos .md, L1-Lfim cada) — nenhum `RUNBOOK_BACKUP.md`, `DISASTER_RECOVERY.md` ou procedimento de rollback
  - `alembic/versions/` (37 migrations, L1-Lfim cada) — migrations existem mas sem procedimento documentado de rollback
  - `.github/workflows/deploy.yml` (L1-Lfim) — pipeline de deploy sem step de backup pré-deploy
  - Production Readiness #12 (backup verificado) e #13 (rollback documentado) não atendidos
- **Descrição:** Sem documento de backup/restore ou rollback procedure.
- **Impacto se não corrigido:** Impossível recuperar de falha catastrófica.
- **Esforço estimado:** 4h — Infra/Ops
- **Depende de:** Nenhum

### ACH-025 — Security scan não evidenciado
- **Prioridade:** P2
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-44
- **Arquivo(s) afetado(s):**
  - `.github/workflows/ci.yml` (L1-Lfim) — sem step de security scanning (Snyk, Trivy, Bandit, safety)
  - `.github/workflows/deploy.yml` (L1-Lfim) — sem step de security scanning pré-deploy
  - `.github/workflows/e2e-tests.yml` (L1-Lfim) — apenas testes E2E, sem security
  - Nenhum `Snykfile`, `.trivyignore`, `.bandit`, `safety` config no repositório
  - Production Readiness #15 exige 0 vulnerabilidades critical/high
- **Descrição:** Sem pipeline de security scanning automatizado.
- **Impacto se não corrigido:** Vulnerabilidades podem existir sem detecção.
- **Esforço estimado:** 4h — Infra/Security
- **Depende de:** Nenhum

## P3 — Baixo (Futuro/Backlog)

### ACH-026 — FairnessGuard sem Camada 3 (LLM semântico) ativa por padrão
- **Prioridade:** P3
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-15
- **Arquivo(s) afetado(s):**
  - `fairness_guard.py` — método `check_semantic()` implementado mas requer chamada explícita
  - `enhanced_agent_mixin.py:L212-L231` — `_fairness_pre_check` chama apenas `check()` (Camadas 1+2), não `check_semantic()` (Camada 3)
- **Descrição:** Camada 3 (análise semântica via LLM) implementada mas não ativada automaticamente. Requer chamada explícita de `check_semantic()`.
- **Impacto se não corrigido:** Vieses sutis que escapam regex e léxico passam despercebidos.
- **Esforço estimado:** 8h — Backend (Compliance)
- **Depende de:** ACH-002

### ACH-027 — RAGAS evaluation framework não implementado
- **Prioridade:** P3
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-21
- **Arquivo(s) afetado(s):**
  - `lia-agent-system/` (241 arquivos .py de testes, L1-Lfim) — nenhum importa `ragas`, `faithfulness_score`, ou `relevance_score`
  - `app/services/` — nenhum arquivo `*ragas*`, `*evaluation*quality*` encontrado
  - `docs/PLAYBOOK_AUDITORIA_PROFUNDA.md` define metas (Faithfulness ≥0.90, Relevance ≥0.85) mas sem implementação correspondente
- **Descrição:** Playbook define metas RAGAS mas framework de avaliação de qualidade LLM não existe no código.
- **Impacto se não corrigido:** Sem métricas de qualidade de output do LLM.
- **Esforço estimado:** 24h — Backend (LLM Quality)
- **Depende de:** Nenhum

### ACH-028 — Red teaming framework não implementado
- **Prioridade:** P3
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-23
- **Arquivo(s) afetado(s):**
  - `tests/` (241 arquivos .py, L1-Lfim, em 10 subdiretórios: contract/, e2e/, fairness/, integration/, load/, test_agents/, test_domains/) — nenhum `test_red_team*`, `test_prompt_injection*`, `test_jailbreak*`
  - `tests/fairness/` (L1-Lfim de cada arquivo) — testes de fairness existem mas não cobrem cenários adversariais de red teaming
  - 6 cenários obrigatórios (prompt injection, data exfiltration, bias elicitation, jailbreak, privilege escalation, score manipulation) sem cobertura
- **Descrição:** Suite de red teaming para segurança de IA não existe como testes automatizados.
- **Impacto se não corrigido:** Vulnerabilidades de segurança de IA não detectadas.
- **Esforço estimado:** 32h — Backend/Security (QA)
- **Depende de:** Nenhum

### ACH-029 — Model drift detection não implementado
- **Prioridade:** P3
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-21
- **Arquivo(s) afetado(s):**
  - `app/api/v1/drift.py` (138 linhas) — endpoints existem: `run_drift_batch` (L93), `get_drift_status` (L118)
  - L1-L138 escaneadas: nenhuma referência a monitoramento contínuo (`continuous_monitor`, `scheduler`, `cron`, `periodic_check`)
  - `_to_response` helper (L58) converte status mas sem trigger de alerta automático
- **Descrição:** Endpoints de drift existem mas sem scheduler de monitoramento contínuo. Triggers de alerta (score WSI varia >0.5 em 30 dias) definidos no playbook mas sem implementação.
- **Impacto se não corrigido:** Degradação silenciosa de qualidade do modelo.
- **Esforço estimado:** 16h — Backend (ML Ops)
- **Depende de:** Nenhum

### ACH-030 — Score normalization entre versões de perguntas WSI
- **Prioridade:** P3
- **Dimensão:** 5 (Types/Contracts)
- **Runbook:** RM-09
- **Arquivo(s) afetado(s):**
  - `app/domains/cv_screening/services/wsi_service.py` (1295 linhas) — `normalize_weights()` existe em L77-L101 mas normaliza pesos, não scores entre versões
  - `wsi_service.py:L397` — `normalized_weights = normalize_weights(weights)` — usado internamente
  - Playbook define trigger: variância >5% entre versões, factor: 0.7-1.3 — sem implementação de `version_score_normalization` encontrada em L1-L1295
- **Descrição:** Weight normalization existe mas score normalization entre VERSÕES de perguntas (playbook requirement) não implementado.
- **Impacto se não corrigido:** Candidatos avaliados com versões diferentes de perguntas recebem scores incomparáveis.
- **Esforço estimado:** 8h — Backend (Screening)
- **Depende de:** Nenhum

### ACH-031 — FRIA (Fundamental Rights Impact Assessment) não documentado
- **Prioridade:** P3
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-26
- **Arquivo(s) afetado(s):**
  - `docs/` (65+ arquivos .md, L1-Lfim cada) — nenhum `FRIA.md`, `FUNDAMENTAL_RIGHTS.md`, `EU_AI_ACT_ASSESSMENT.md`
  - `lia-agent-system/docs/` (7 arquivos .md, L1-Lfim cada: `CONCEITOS_IA_WEDOTALENT.md`, `MAPA_CAMADA_INTELIGENCIA.md`, `ai-architecture-audit.md`) — nenhum cobre FRIA
  - `docs/DIAGNOSTICO_COMPLIANCE_IA_COMPLETO.md` (L1-Lfim) — cobre compliance geral mas não FRIA específico (Art. 6 + Anexo III)
  - EU AI Act Art. 6 + Anexo III exige documento FRIA antes do deploy para sistemas high-risk (IA em recrutamento)
- **Descrição:** FRIA é documento obrigatório pelo EU AI Act para sistemas de IA em recrutamento. Não existe no repositório.
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
| **P2** | 10 | 88h | Backend + Frontend + Infra | Sprint N+2/N+3 |
| **P3** | 6 | 104h | Backend + Security + Legal | Backlog |
| **Total** | **31** | **326h** | — | — |

## 6.2 Detalhamento P0 (Imediato)

| ID | Achado | Esforço | Responsável | Runbook |
|:---|:-------|:-------:|:-----------:|:-------:|
| ACH-001 | Anti-sycophancy em 6 agentes | 4h | Backend (LLM/Prompts) | RM-08 |
| ACH-002 | FairnessGuard como middleware | 8h | Backend (Orchestrator) | RM-02 |
| ACH-003 | Consent hard enforcement | 4h | Backend (Compliance) | RM-04 |
| ACH-004 | Circuit breaker OpenAI/Gemini | 4h | Backend (Resiliência) | RM-10 |
| ACH-005 | HITL em sourcing/communication | 8h | Backend (Agentes) | RM-03 |
| ACH-006 | Audit trail em 3 agentes | 6h | Backend (Compliance) | RM-05 |
| ACH-007 | WCAG 2.1 AA (aria-labels) | 40h | Frontend | RM-27 |
| ACH-008 | Multi-tenant RLS | 16h | Backend/Infra (Database) | RM-06 |

## 6.3 Detalhamento P1 (Sprint N+1)

| ID | Achado | Esforço | Responsável | Runbook |
|:---|:-------|:-------:|:-----------:|:-------:|
| ACH-009 | Confidence em 8 agentes | 8h | Backend (LLM/Prompts) | RM-09 |
| ACH-010 | Circuit breaker ATS clients | 6h | Backend (Resiliência) | RM-10 |
| ACH-011 | Circuit breaker email/billing | 4h | Backend (Resiliência) | RM-10 |
| ACH-012 | Few-shot examples | 12h | Backend (LLM/Prompts) | RM-14 |
| ACH-013 | Observabilidade Prometheus | 8h | Backend/Infra (Observabilidade) | RM-12 |
| ACH-014 | WorkOS circuit breaker | 2h | Backend (Auth/Resiliência) | RM-10 |
| ACH-015 | Graceful degradation docs | 4h | Backend/Ops (Documentação) | RM-13 |

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
