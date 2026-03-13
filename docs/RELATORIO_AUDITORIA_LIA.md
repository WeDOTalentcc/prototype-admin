# RELATÓRIO DE AUDITORIA PROFUNDA — Plataforma LIA (WeDO Talent)

**Data:** 2026-03-13
**Versão:** 2.0 (Atualização pós-sprints SEG-1 a SEG-5 + cruzamento com `relatorio_capacidades_prompts_lia.md`)
**Auditor:** Agente IA (Replit Agent) seguindo `PLAYBOOK_AUDITORIA_PROFUNDA.md`
**Escopo:** Auditoria completa do codebase — 14 dimensões, 13 Crenças, 8 Inegociáveis, 18 Production Readiness, Fairness/LGPD/EU AI Act

> **Changelog v2.0 (13/03/2026):** Re-auditoria completa do codebase após sprints SEG-1 a SEG-5. **Achados resolvidos:** ACH-001 (anti-sycophancy em todos os agentes ✅), ACH-004 (circuit breakers OpenAI/Gemini ✅), ACH-005 (HITL em sourcing/communication ✅), ACH-010 (circuit breakers ATS clients ✅). **Parcialmente resolvidos:** ACH-006 (audit trail — 4/5 agentes OK, falta interview_graph), ACH-011 (circuit breakers — email OK, billing ainda sem). **Novas seções:** Seção 7 (Arquitetura dos 3 Níveis de Chat + Scope Config + CascadedRouter), Seção 8 (ActionExecutor + HITL via Chat + 18 Kanban Commands), Seção 9 (Sistema Preditivo e Insights), Seção 10 (Dívidas Técnicas e Limitações), Seção 11 (Oportunidades de Evolução — 15 itens). **Métricas atualizadas:** 15 agentes (era 12), 164 tools (era ~100), 584 componentes TSX (era 466), 37 migrations (era 30+). Cruzamento com `relatorio_capacidades_prompts_lia.md` (1369 linhas, 10 seções).

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

| Métrica | Valor (v1.0 → v2.0) |
|:--------|:------|
| Domínios de agente | 14 (sourcing, job_management, cv_screening, pipeline, recruiter_assistant ×4, hiring_policy, policy, interview_scheduling, analytics, communication, automation, ats_integration) |
| Agentes registrados | **15** (11 ReAct + 2 LangGraph + 1 interview_graph + 1 Orchestrator) — era 12 |
| Tools totais | **164** (91 Alpha 1 + 73 pós-Alpha) — ver `diagnostico-agentes-mvp.md` seção 8 |
| System prompts (domínio) | 16 arquivos |
| Tool registries | 12 domínio + 7 shared |
| Endpoints API (.py) | 210 arquivos |
| Models (.py) | **134** arquivos — era 100 |
| Services (.py) | 236 arquivos |
| Frontend pages | 90 rotas |
| Frontend components (.tsx) | **584** componentes — era 466 |
| Alembic migrations | **37** — era 30+ |
| Python files (lia-agent-system) | **1204** arquivos |

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
- ~~Anti-sycophancy: AUSENTE~~ → ✅ **RESOLVIDO (SEG-1)** — anti-sycophancy adicionado em `sourcing_system_prompt.py`
- Confidence calibration: AUSENTE — grep por `confidence|APPLY_SILENT` em `sourcing_system_prompt.py` retorna 0 resultados
- ~~HITL: AUSENTE~~ → ✅ **RESOLVIDO (SEG-5)** — AuditCallback + HITL gates adicionados em `sourcing_react_agent.py`
- FairnessGuard: OK via `EnhancedAgentMixin` + `_fairness_pre_check` + wiring SEG-2

**Problemas identificados (v2.0):**
- ~~`sourcing_system_prompt.py` — sem seção anti-sycophancy~~ ✅ Resolvido
- ~~`sourcing_react_agent.py` — FairnessGuard inconsistente~~ ✅ Resolvido (SEG-2 wiring)
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
- ~~Anti-sycophancy: AUSENTE~~ → ✅ **RESOLVIDO (SEG-1)** — anti-sycophancy adicionado em `pipeline_system_prompt.py`
- ~~FairnessGuard referenciado apenas via YAML shared~~ → ✅ **RESOLVIDO (SEG-2)** — wiring direto em `pipeline_transition_agent.py`

**Problemas identificados (v2.0):**
- ~~`pipeline_system_prompt.py` — sem anti-sycophancy~~ ✅ Resolvido
- FairnessGuard: OK (SEG-2 — `guard.check(message)` + `check_implicit_bias()` + `log_check()`)
- HITL: OK — revisão humana para zona de fronteira (60-70%)
- PromptInjectionGuard: OK (SEG-1 — wiring em `wsi_interview_graph.py`)

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
- **19 tools** registradas em `analytics_tool_registry.py` (atualizado v2.0 — era 6)
- 8 command templates em `job_analytics_prompt_service.py`

**Problemas (v2.0):**
- ~~Anti-sycophancy: AUSENTE~~ → ✅ **RESOLVIDO (SEG-1)** — adicionado em `analytics_system_prompt.py`
- FairnessGuard: via mixin genérico, sem validação específica de outputs analíticos
- ~~Audit trail: AUSENTE~~ → ✅ **RESOLVIDO** — `AuditCallback` integrado em `analytics_react_agent.py`

## 2.10 Communication Agent

**O que faz:**
- Envio de comunicações (email, WhatsApp, SMS, Teams, in-app)
- Multi-channel routing
- Opt-out management
- Templates

**Problemas (v2.0):**
- ~~Anti-sycophancy: AUSENTE~~ → ✅ **RESOLVIDO (SEG-1)** — adicionado em `communication_system_prompt.py`
- ~~HITL: AUSENTE~~ → ✅ **RESOLVIDO (SEG-5)** — AuditCallback + HITL integrado em `communication_react_agent.py`
- ~~Audit trail: AUSENTE~~ → ✅ **RESOLVIDO** — `AuditCallback` integrado (9 referências)
- Rate limiting: OK (integrado)
- Opt-out: OK (implementado)

## 2.11 Automation Agent

**O que faz:**
- Automações de stage transition
- Triggers configuráveis (8 triggers de evento)
- Scheduler (10 jobs agendados)
- 6 tools (decompose_task, prioritize_tasks, get_execution_plan, build_dag, check_dependencies, get_next_tasks)

**Problemas (v2.0):**
- ~~Anti-sycophancy: AUSENTE~~ → ✅ **RESOLVIDO (SEG-1)** — adicionado em `automation_system_prompt.py`

## 2.12 ATS Integration Agent

**O que faz:**
- Sincronização com ATS externos (Gupy, PandaPé, StackOne, Merge)
- Webhook handling

**Problemas (v2.0):**
- ~~Anti-sycophancy: AUSENTE~~ → ✅ **RESOLVIDO (SEG-1)** — adicionado em `ats_integration_system_prompt.py`
- ~~Circuit breaker: AUSENTE nos ATS clients~~ → ✅ **RESOLVIDO** — circuit breakers adicionados em `gupy.py` (9), `pandape.py` (9), `stackone.py` (9), `merge.py` (10)
- ~~Audit trail: AUSENTE~~ → ✅ **RESOLVIDO** — `AuditCallback` integrado em `ats_integration_react_agent.py`

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
| Anti-Sycophancy | ✅ OK | OK | ✅ OK | OK | OK | OK | OK | OK | OK | N/A | ✅ OK | ✅ OK | ✅ OK | ✅ OK |
| FairnessGuard Middleware | ✅ OK | OK | OK | OK | OK | OK | OK | OK | OK | **FALHA** | PARCIAL | PARCIAL | PARCIAL | PARCIAL |
| Negation Detection | AUSENTE | AUSENTE | OK | AUSENTE | AUSENTE | AUSENTE | OK | OK | AUSENTE | AUSENTE | AUSENTE | AUSENTE | AUSENTE | AUSENTE |
| Confiança Real | **FALHA** | OK | OK | **FALHA** | **FALHA** | **FALHA** | OK | OK | PARCIAL | **FALHA** | **FALHA** | **FALHA** | **FALHA** | **FALHA** |
| Circuit Breaker Direto | OK | PARCIAL | PARCIAL | PARCIAL | OK | PARCIAL | PARCIAL | PARCIAL | PARCIAL | **FALHA** | PARCIAL | PARCIAL | PARCIAL | ✅ OK |
| Pre-call Budget Check | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| PII Masking | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Consent Check | N/A | N/A | PARCIAL | N/A | N/A | N/A | N/A | N/A | N/A | PARCIAL | N/A | PARCIAL | N/A | N/A |
| Multi-Tenant Isolation | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Audit Trail | OK | OK | OK | OK | OK | OK | OK | OK | ✅ OK | **FALHA** | ✅ OK | ✅ OK | OK | ✅ OK |
| Observabilidade | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| Token Tracking | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK | OK |
| HITL Enforcement | ✅ OK | OK | OK | **FALHA** | PARCIAL | PARCIAL | OK | OK | **FALHA** | **FALHA** | N/A | ✅ OK | PARCIAL | N/A |

> **Atualizado v2.0:** ✅ marca itens corrigidos desde v1.0. Anti-sycophancy agora universal (6 agentes corrigidos). HITL adicionado em sourcing e communication. Audit trail adicionado em analytics, communication, ATS, policy. Circuit breakers em ATS clients. Único agente sem audit trail: interview_graph.

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
| Anti-Sycophancy | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| FairnessGuard Pre-check | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Confidence Score | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| HITL Gate | ✅ | ✅ | ✅ | ❌ | ⚠️ | ⚠️ | ✅ | ✅ | N/A | ✅ | ⚠️ | N/A |
| Audit Trail | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Circuit Breaker | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ |
| Few-shot Examples | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Stage Context | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| LLM Fallback | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Token Tracking | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Opt-out | ✅ | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | ✅ | N/A | N/A |

> **Atualizado v2.0:** Anti-sycophancy agora 12/12 ✅ (era 6/12). HITL adicionado em Sourcing e Communication. Audit Trail adicionado em Analytics, Communication, ATS. Circuit Breaker adicionado em ATS.

## 4.2 Padrões que Deveriam Ser Universais

### Nível 1 — Obrigatório em TODOS
1. **Anti-sycophancy** — ✅ **RESOLVIDO (SEG-1)** — Agora 12/12 agentes (~100%). Era 6/14 (~43%)
2. **FairnessGuard como middleware automático** — Hoje é opt-in via mixin → deveria ser forçado no Orchestrator. Wiring parcial via SEG-2 mas ainda não é interceptor universal
3. **Confidence score em outputs** — Hoje: 4/14 agentes reportam confiança — sem alteração
4. **HITL gate para ações de alto impacto** — Melhorado: sourcing e communication agora têm HITL (SEG-5). Faltam: talent, interview_scheduling, policy

### Nível 2 — Obrigatório em agentes que tocam candidatos
1. **Negation detection** — Apenas 3 agentes (cv_screening, pipeline, policy) — sem alteração
2. **Consent check antes de processar** — Soft enforcement (ACH-003 ainda aberto — default False)
3. **Audit trail em todas as decisões** — ✅ Melhorado: 13/14 agentes com trail (falta apenas interview_graph)

### Nível 3 — Desejável para maturidade
1. **Few-shot examples** — 5/14 agentes com exemplos — sem alteração
2. **Stage context** — 8/14 agentes com contexto de etapa — sem alteração
3. **Métricas por agente** — Prometheus metrics parciais — sem alteração

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

### ACH-001 — ~~Anti-Sycophancy ausente em 6+ de 14 agentes~~ ✅ RESOLVIDO
- **Prioridade:** ~~P0~~ → **FECHADO**
- **Dimensão:** 10 (Qualidade LLM)
- **Runbook:** RM-08
- **Resolução (SEG-1, 13/03/2026):** Anti-sycophancy block adicionado em todos os 6 system prompts que faltavam. Verificação: grep por `sycophancy|anti_sycophancy` agora retorna 2+ matches em cada arquivo.
- **Evidência:** `sourcing_system_prompt.py` (2 matches), `pipeline_system_prompt.py` (2), `communication_system_prompt.py` (2), `analytics_system_prompt.py` (2), `ats_integration_system_prompt.py` (2), `automation_system_prompt.py` (2).
- **Cobertura atual:** 12/12 agentes com anti-sycophancy (100%)

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

### ACH-004 — ~~Circuit breaker ausente em OpenAI e Gemini providers~~ ✅ RESOLVIDO
- **Prioridade:** ~~P0~~ → **FECHADO**
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-10
- **Resolução (SEG, 13/03/2026):** Circuit breaker decorators adicionados em ambos os providers. Verificação: grep por `circuit_breaker` retorna 5 matches em `llm_openai.py` e 5 matches em `llm_gemini.py`.
- **Cobertura atual:** 3/3 LLM providers com circuit breaker (Claude ✅, OpenAI ✅, Gemini ✅)

### ACH-005 — ~~HITL ausente em sourcing e communication~~ ✅ RESOLVIDO
- **Prioridade:** ~~P0~~ → **FECHADO**
- **Dimensão:** 12 (Governança)
- **Runbook:** RM-03
- **Resolução (SEG-5, 13/03/2026):** AuditCallback + HITL gates integrados em ambos os agentes. Verificação: grep por `HITL|AuditCallback|human_review|flag_for_review` retorna 7 matches em `sourcing_react_agent.py` e 9 matches em `communication_react_agent.py`.
- **Cobertura atual:** Sourcing ✅, Communication ✅

### ACH-006 — ~~Audit trail incompleto em 5 agentes~~ ⚠️ PARCIALMENTE RESOLVIDO
- **Prioridade:** ~~P0~~ → **P1** (1 agente restante)
- **Dimensão:** 13 (Segurança)
- **Runbook:** RM-05
- **Resolução parcial (SEG-5, 13/03/2026):** AuditCallback integrado em 4 dos 5 agentes que faltavam.
  - ✅ `analytics_react_agent.py` — 2 matches de `AuditCallback`
  - ✅ `communication_react_agent.py` — 9 matches de `AuditCallback`
  - ✅ `ats_integration_react_agent.py` — 2 matches de `AuditCallback`
  - ✅ `app/domains/policy/agents/agent.py` — 3 matches de `AuditCallback`
  - ❌ `app/domains/interview_scheduling/agents/interview_graph.py` — **0 matches** (AINDA SEM AUDIT TRAIL)
- **Cobertura atual:** 13/14 agentes com audit trail (93%). Falta apenas `interview_graph.py` (Graph agent LangGraph).
- **Esforço residual:** 2h — Backend (adicionar AuditCallback nos nós do interview_graph)

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

### ACH-010 — ~~Circuit breaker ausente em ATS clients~~ ✅ RESOLVIDO
- **Prioridade:** ~~P1~~ → **FECHADO**
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-10
- **Resolução:** Circuit breakers adicionados em todos os 4 ATS clients.
  - ✅ `gupy.py` — 9 matches de `circuit_breaker`
  - ✅ `pandape.py` — 9 matches
  - ✅ `stackone.py` — 9 matches
  - ✅ `merge.py` — 10 matches
- **Cobertura atual:** 4/4 ATS clients com circuit breaker (100%)

### ACH-011 — ~~Circuit breaker ausente em email/billing providers~~ ⚠️ PARCIALMENTE RESOLVIDO
- **Prioridade:** ~~P1~~ → **P2** (apenas billing)
- **Dimensão:** 12 (Governança/Resiliência)
- **Runbook:** RM-10
- **Resolução parcial:** Circuit breakers adicionados em email providers.
  - ✅ `sendgrid_provider.py` — 2 matches de `circuit`
  - ✅ `resend_provider.py` — 2 matches de `circuit`
  - ❌ `iugu_provider.py` — 0 matches (AINDA SEM)
  - ❌ `vindi_provider.py` — 0 matches (AINDA SEM)
- **Cobertura atual:** Email 2/2 ✅, Billing 0/2 ❌
- **Esforço residual:** 2h — Backend (adicionar circuit breakers em billing providers)

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

## 6.1 Tabela Consolidada (Atualizada v2.0)

| Prioridade | Qtd. Original | Resolvidos | Restantes | Esforço Restante (h) | Sprint Alvo |
|:----------:|:------------:|:----------:|:---------:|:-------------------:|:-----------:|
| **P0** | 8 | **4** (ACH-001,004,005 ✅ + ACH-006 parcial) | 4 | **64h** (era 90h) | Imediato |
| **P1** | 7 | **1** (ACH-010 ✅) + **1 parcial** (ACH-011) | 5 | **34h** (era 44h) | Sprint N+1 |
| **P2** | 10 | 0 | 10 (+1 billing de ACH-011) | **90h** (era 88h) | Sprint N+2/N+3 |
| **P3** | 6 | 0 | 6 | **104h** | Backlog |
| **Total** | **31** | **5 ✅ + 2 parciais** | **24 restantes** | **292h** (era 326h) | — |

> **Redução v2.0:** 34h de esforço economizadas pelos sprints SEG-1 a SEG-5. 5 achados completamente resolvidos, 2 parcialmente resolvidos.

## 6.2 Detalhamento P0 (Imediato)

| ID | Achado | Esforço | Responsável | Runbook |
|:---|:-------|:-------:|:-----------:|:-------:|
| ACH-001 | ~~Anti-sycophancy em 6 agentes~~ | ~~4h~~ | ✅ RESOLVIDO (SEG-1) | RM-08 |
| ACH-002 | FairnessGuard como middleware | 8h | Backend (Orchestrator) | RM-02 |
| ACH-003 | Consent hard enforcement | 4h | Backend (Compliance) | RM-04 |
| ACH-004 | ~~Circuit breaker OpenAI/Gemini~~ | ~~4h~~ | ✅ RESOLVIDO (SEG) | RM-10 |
| ACH-005 | ~~HITL em sourcing/communication~~ | ~~8h~~ | ✅ RESOLVIDO (SEG-5) | RM-03 |
| ACH-006 | ~~Audit trail em 5 agentes~~ (1 restante) | ~~6h~~ 2h | ⚠️ PARCIAL (falta interview_graph) | RM-05 |
| ACH-007 | WCAG 2.1 AA (aria-labels) | 40h | Frontend | RM-27 |
| ACH-008 | Multi-tenant RLS | 16h | Backend/Infra (Database) | RM-06 |

> **P0 v2.0:** 3 achados totalmente resolvidos, 1 parcialmente. Esforço P0 residual: **70h** (era 90h).

## 6.3 Detalhamento P1 (Sprint N+1)

| ID | Achado | Esforço | Responsável | Runbook |
|:---|:-------|:-------:|:-----------:|:-------:|
| ACH-009 | Confidence em 8 agentes | 8h | Backend (LLM/Prompts) | RM-09 |
| ACH-010 | ~~Circuit breaker ATS clients~~ | ~~6h~~ | ✅ RESOLVIDO | RM-10 |
| ACH-011 | ~~Circuit breaker email/billing~~ (billing restante) | ~~4h~~ 2h | ⚠️ PARCIAL (faltam iugu/vindi) | RM-10 |
| ACH-012 | Few-shot examples | 12h | Backend (LLM/Prompts) | RM-14 |
| ACH-013 | Observabilidade Prometheus | 8h | Backend/Infra (Observabilidade) | RM-12 |
| ACH-014 | WorkOS circuit breaker | 2h | Backend (Auth/Resiliência) | RM-10 |
| ACH-015 | Graceful degradation docs | 4h | Backend/Ops (Documentação) | RM-13 |

> **P1 v2.0:** 1 achado resolvido, 1 parcialmente. Esforço P1 residual: **36h** (era 44h).

## 6.4 Verificação de Crenças

| Crença | Status | Achados Relacionados |
|:-------|:------:|:---------------------|
| 01 — Humano em Primeiro Lugar | ✅ OK | ~~ACH-005~~ ✅ RESOLVIDO — HITL em sourcing e communication |
| 02 — Justa e Não-Discriminatória | PARCIAL | ACH-002 (FairnessGuard não é middleware universal) |
| 03 — Transparente e Explicável | OK | Explainability panel implementado |
| 04 — Segura e Respeitosa com Privacidade | PARCIAL | ACH-003 (consent soft), ACH-008 (multi-tenant) |
| 05 — Construída por Humanos, Para Humanos | OK | Audit trimestrais previstas no playbook |
| 06 — Em Melhoria Contínua | PARCIAL | ACH-029 (model drift não implementado) |
| 07 — Resiliente por Design | ✅ MELHORADO | ~~ACH-004~~ ✅, ~~ACH-010~~ ✅, ACH-011 parcial (billing restante) |
| 08 — Observável e Rastreável | ✅ MELHORADO | ~~ACH-006~~ parcial (1 agente restante), ACH-013 (Prometheus parcial) |
| 09 — Consciente de Custos | OK | Token budget, LLM cascade, pre-call check implementados |
| 10 — Inteligência vs Determinismo | OK | ConfidencePolicyService com 3 níveis implementado |
| 11 — Anti-Bajulação | ✅ OK | ~~ACH-001~~ ✅ RESOLVIDO — 12/12 agentes com anti-sycophancy |
| 12 — Autonomia Progressiva | OK | Autonomy engine implementado |
| 13 — Acessível e Inclusiva | **FALHA** | ACH-007 (WCAG ~10.4% cobertura — 61/584 TSX com aria-label) |

## 6.5 Verificação de Inegociáveis

| # | Inegociável | Status | Achado |
|:--|:-----------|:------:|:-------|
| 1 | WSI explicável | OK | Rationale implementado em wsi_service |
| 2 | Review gate em rejeição | ✅ OK | ~~ACH-005~~ ✅ RESOLVIDO — HITL em sourcing/communication |
| 3 | FairnessGuard 100% | **FALHA** | ACH-002 |
| 4 | PII masking todos os logs | OK | Global filter instalado |
| 5 | Consent antes de processamento | **FALHA** | ACH-003 |
| 6 | Dados deletados (SLA 15 dias) | OK | DSR + cleanup implementados |
| 7 | Human override sempre disponível | OK | UI permite override |
| 8 | WCAG 2.1 AA | **FALHA** | ACH-007 |

## 6.6 Production Readiness Gate (18 Critérios)

| # | Critério | Status |
|:--|:---------|:------:|
| 1 | Circuit Breaker em serviços externos | ✅ MELHORADO (~~ACH-004~~ ✅, ~~ACH-010~~ ✅, ACH-011 parcial — faltam billing) |
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

**Score v2.0: 10/18 OK, 2 PARCIAL, 6 FALHA** (era 9/18 OK, 7 FALHA)

---

# SEÇÃO 7: ARQUITETURA DE CHAT — 3 NÍVEIS E ESCOPOS

> **Seção nova v2.0** — Conteúdo cruzado com `relatorio_capacidades_prompts_lia.md`

## 7.1 Os 3 Níveis de Chat

A plataforma possui **3 camadas de chat** com contextos, escopos e lógica de decisão distintos:

### 7.1.1 Float Chat (candidates-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/candidates-page.tsx`
- **Contexto:** Página de funil de talentos (listagem geral de candidatos)
- **Escopo:** `TALENT_FUNNEL` — 20 tools (11 query + 9 action)
- **Endpoint:** `POST /api/backend-proxy/orchestrator/talent-chat`
- **Backend:** `app/api/v1/orchestrated_talent_chat.py` (v3.0 — ActionExecutor + PendingActionState + closed-loop)
- **Estado expandido (Super Prompt):** Gerenciado via `LiaFloatContext` (`lia-float-context.tsx`)

**Lógica de decisão:**
1. Mensagem → normalizar
2. Verificar `analysisCommands[]` → handleAICommand() (8 comandos de análise)
3. Verificar `isGenericQuestion()` → handleOrchestratedTalentMessage() (orquestrador)
4. Senão: executeSearch() (busca de candidatos)

### 7.1.2 Kanban Chat (job-kanban-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/job-kanban-page.tsx`
- **Contexto:** Kanban de uma vaga específica (pipeline de candidatos por etapa)
- **Escopo:** `IN_JOB` — 25 tools (14 query + 11 action)
- **Endpoint:** `POST /api/backend-proxy/orchestrator/job-chat`
- **Backend:** `app/api/v1/orchestrated_job_chat.py` (v2.0 — closed-loop action execution)

**Lógica de decisão (backend):**
1. `detect_command_type(message)` → KanbanCommandType (18 tipos)
2. Se analytical (12 tipos) → análise IA via prompts
3. Se actionable → ActionExecutor
4. Se confirmação/rejeição → PendingActionStore
5. Senão → Orchestrator.process_request()

### 7.1.3 Chat Dedicado (chat-page.tsx)

- **Localização:** `plataforma-lia/src/components/pages/chat-page.tsx`
- **Contexto:** Chat full-page com LIA — acesso a todas as capacidades
- **Escopo:** `GLOBAL` — 2 tools (`generate_report`, `schedule_report`)
- **Endpoint:** `POST /api/backend-proxy/orchestrator/process` (+ WebSocket)
- **Capacidades:** Quick actions (7), busca via Pearch AI, histórico persistente, suporte a anexos, resumo automático

## 7.2 Scope Config (`scope_config.py`)

| Escopo | Tools Query | Tools Action | Total | Contexto |
|:-------|:----------:|:-----------:|:-----:|:---------|
| `TALENT_FUNNEL` | 11 | 9 | 20 | Float Chat (candidates-page) |
| `JOB_TABLE` | 11 | 8 | 19 | Jobs page |
| `IN_JOB` | 14 | 11 | 25 | Kanban Chat (job-kanban-page) |
| `GLOBAL` | 1 | 1 | 2 | Chat dedicado (chat-page) |

**Observação de auditoria:** O escopo `GLOBAL` é excessivamente restritivo (apenas 2 tools). O chat-page envia tudo para o Orchestrator que ignora o scope na execução — inconsistência entre definição e uso real.

## 7.3 CascadedRouter — 6 Tiers de Roteamento

| Tier | Nome | Mecanismo | Custo |
|:----:|:-----|:----------|:-----:|
| 0 | MemoryResolver | Resolução de pronomes/referências via WorkingMemory | Zero |
| 1 | LRU in-process | Hash MD5 em memória local | Zero |
| 2 | Redis hash cache | Distribuído, exato, entre workers | Baixo |
| 3 | VectorSemanticCache | pgvector, cosine similarity ≥ 0.92 | Baixo |
| 4 | FastRouter | Regex/keyword patterns | Baixo |
| 5 | LLM Cascade | Haiku → Sonnet → Opus | Alto |
| FB | Clarification | Pergunta ao usuário (6 opções padrão) | Zero |

**Métricas Prometheus:** `router_tier_hit_total`, `router_latency_ms`, `router_confidence_histogram`

---

# SEÇÃO 8: ACTIONEXECUTOR E HITL VIA CHAT

> **Seção nova v2.0** — Conteúdo cruzado com `relatorio_capacidades_prompts_lia.md`

## 8.1 ActionExecutor — Ações Closed-Loop

**Arquivo:** `lia-agent-system/app/orchestrator/action_executor.py`

Ações executadas diretamente pelo backend (closed-loop, sem modal UI):

| Ação | Método | HITL |
|:-----|:-------|:----:|
| Mover candidato entre etapas | `move_candidate()` | ✅ Sim |
| Enviar email | `send_email()` | ✅ Sim |
| Iniciar triagem WSI | `start_screening()` | ✅ Sim |
| Agendar entrevista | `schedule_interview()` | ✅ Sim |
| Solicitar dados adicionais | `request_data()` | ✅ Sim |
| Analisar perfil | `analyze_profile()` | Não |
| Aprovar candidato | `approve_candidate()` | ✅ Sim |

## 8.2 Fluxo HITL (Human-in-the-Loop)

**Arquivo:** `lia-agent-system/app/orchestrator/pending_action.py`

1. LIA propõe ação → `needs_confirmation: true`
2. Usuário confirma/rejeita → `PendingActionStore` armazena estado
3. Se confirmado → `ActionExecutor` executa ação real
4. Se rejeitado → ação cancelada com log

**Observação de auditoria:** O fluxo HITL está implementado para ações via chat (ActionExecutor), mas não é universal — ações diretas via UI (bulk actions, drag-and-drop kanban) executam sem HITL.

## 8.3 Kanban Command Templates — 18 Tipos

**Arquivo:** `app/domains/recruiter_assistant/prompts/kanban_assistant_prompts.py`

| # | Comando | Tipo | HITL |
|:--|:--------|:-----|:----:|
| 1 | `rankear_candidatos` | Análise IA | Não |
| 2 | `performance_funil` | Análise IA | Não |
| 3 | `gargalos_processo` | Análise IA | Não |
| 4 | `comparar_candidatos` | Análise IA | Não |
| 5 | `resumir_perfil` | Análise IA | Não |
| 6 | `candidatos_ativos` | Query local | Não |
| 7 | `taxa_conversao` | Query local | Não |
| 8 | `tempo_medio` | Query local | Não |
| 9 | `candidatos_parados` | Query local | Não |
| 10 | `top_candidatos` | Análise IA | Não |
| 11 | `mover_candidato` | Ação | ✅ Sim |
| 12 | `enviar_email` | Ação | ✅ Sim |
| 13 | `disparar_triagem` | Ação | ✅ Sim |
| 14 | `agendar_entrevista` | Ação | ✅ Sim |
| 15 | `solicitar_dados` | Ação | ✅ Sim |
| 16 | `analisar_perfil` | Análise IA | Não |
| 17 | `aprovar_candidato` | Ação | ✅ Sim |
| 18 | `analise_geral` | Análise IA (fallback) | Não |

---

# SEÇÃO 9: SISTEMA PREDITIVO E INSIGHTS

> **Seção nova v2.0** — Conteúdo cruzado com `relatorio_capacidades_prompts_lia.md`

## 9.1 Ferramentas Preditivas (Analytics Agent)

| Ferramenta | Input | Surfacing UI |
|:-----------|:------|:-------------|
| `get_prediction_metrics` | `job_id`, `time_range` | Analytics dashboard, Chat |
| `get_ml_predictions` | `job_id`, `model_type` | Analytics dashboard |
| `get_conversion_patterns` | `job_id`/`company_id` | JobReportModal, Chat |
| `get_smart_alerts` | `company_id`, `threshold` | Dashboard, SaturationBadge |
| `get_trends` | `metric`, `time_range` | Analytics dashboard |
| `get_bottleneck_analysis` | `job_id` | Kanban Chat, Dashboard |

## 9.2 Predições Específicas

| Predição | Dados Utilizados | Serviço |
|:---------|:----------------|:--------|
| Probabilidade de contratação | Histórico vagas similares, pool atual | `predictive_analytics_service.py` |
| Time-to-Fill (TTF) | Tempos por etapa, velocidade pipeline | `time_to_fill_prediction` command |
| Risco de dropout | Tempo parado, engajamento, mercado | `get_smart_alerts` + EWS |
| Previsão de pipeline | Conversão histórica, volume atual | `get_ml_predictions` |
| Predição salarial | Mercado, cargo, localização, senioridade | `get_intelligent_salary` |

## 9.3 Serviços de Inteligência Operacional

| # | Serviço | Tipo | Surfacing UI |
|:--|:--------|:-----|:-------------|
| 1 | Pipeline Velocity Engine | Local (query) | Kanban page, Analytics dashboard |
| 2 | Zero-Touch Scheduling | IA + Local | Communication Agent, Calendar API |
| 3 | Silver Medalists | IA (matching) | Sourcing Agent, ProactiveInsightCard |
| 4 | Recruiter Intelligence | Local (metrics) | Analytics dashboard |
| 5 | Early Warning Score (EWS) | IA (anomaly) | SaturationBadge, SmartAlerts |
| 6 | Journey Intelligence | Local + IA | Kanban page |
| 7 | Recruiter Perf. Benchmark | Local (metrics) | Analytics dashboard |
| 8 | Pipeline Prediction | IA (ML model) | JobReportModal, Analytics |

## 9.4 Componentes de Insights na UI

### ProactiveInsightCard
- **Arquivo:** `plataforma-lia/src/components/proactive-insight-card.tsx`
- **Ativação:** Exibido automaticamente após busca de candidatos
- **Dados:** `SearchAnalytics` — distribuições, top skills, top companies, experience range, alertas, ações sugeridas

### SaturationBadge
- **Arquivo:** `plataforma-lia/src/components/kanban/components/SaturationBadge.tsx`
- **Ativação:** Header do kanban de cada vaga
- **Estados:** `normal` (< 90%), `almost` (≥ 90%), `saturated` (orgânico ou sourcing saturado)

### JobReportModal
- **Arquivo:** `plataforma-lia/src/components/job-report-modal.tsx`
- **Exportação:** PDF via `html2canvas` + `jsPDF`
- **⚠️ Dados atualmente mockados no frontend** — funcionalidade incompleta

---

# SEÇÃO 10: DÍVIDAS TÉCNICAS E LIMITAÇÕES

> **Seção nova v2.0** — Conteúdo cruzado com `relatorio_capacidades_prompts_lia.md`

## 10.1 Processamento Local vs IA

| Funcionalidade | Tipo | Observação |
|:---------------|:-----|:-----------|
| LIA Score | Local (sem LLM) | Fórmula ponderada — `lia_score_service.py` |
| Busca de candidatos | Local + API externa | PostgreSQL + Pearch AI |
| Distribuições/Analytics | Local | Contagens e agrupamentos |
| SaturationBadge | Local | Threshold vs contagem |
| JobReportModal | Local | **Dados hardcoded (mock)** |
| Avaliação por rubrica | IA real (Claude) | — |
| WSI Screening | IA real (Claude) | — |
| Comparação candidatos | IA real (Claude) | — |
| Ranking | IA real (Claude) | — |
| JD Enriquecida | IA real (Claude) | — |
| Benchmark salarial | IA real (Claude) | + dados de mercado |

## 10.2 Fallbacks Hardcoded

1. **Orchestrator fallback** — Se LLM falha, retorna mensagem genérica com 3 sugestões fixas
2. **CascadedRouter fallback** — Se nenhum tier resolve, clarificação com 6 opções fixas
3. **VectorSemanticCache** — Se pgvector indisponível, pula silenciosamente
4. **PlanDetector** — Falha silenciosa via try/except (non-blocking)

## 10.3 Detecção de Intenção por Keywords (Fragilidades)

- `isGenericQuestion()` — 5 regex + 46 keywords de busca; frágil para termos novos
- `analysisCommands[]` — 8 padrões fixos de string matching
- `detect_command_type()` — keywords por KanbanCommandType; pode falhar para variações
- `_TECHNICAL_PATTERNS` — 5 padrões de string matching para detecção de resposta técnica

## 10.4 Funcionalidades Incompletas

| # | Funcionalidade | Status | Impacto |
|:--|:---------------|:-------|:--------|
| 1 | `handleOpenRubricAnalysis` orphaned | Função sem call sites; modal renderiza mas inacessível | Baixo |
| 2 | JobReportModal com dados mock | Dados hardcoded no frontend; sem backend real | Médio |
| 3 | WSI Voice | Não implementado; WSI é text-only | Baixo |
| 4 | Calibração limitada | Frontend sem agente ReAct; depende 100% do Pearch AI | Médio |
| 5 | Arquivo monolítico | `candidates-page.tsx` (10.398 linhas), `lia-api.ts` (4.943 linhas) | Alto (manutenibilidade) |
| 6 | Notificações WhatsApp | `JobCreatedNotificationRequest` suporta email + Teams; WhatsApp ausente | Baixo |

## 10.5 Dívidas Técnicas

| # | Dívida | Risco |
|:--|:-------|:------|
| 1 | IntentRouter legado coexiste com LLM Cascade como fallback | Duplicação de lógica |
| 2 | `AGENT_TYPE_TO_DOMAIN` hardcoded; sem registro dinâmico | Manutenibilidade |
| 3 | `AgentFactory` vs `get_agent()` — dois padrões coexistem; `get_agent()` NÃO é session-safe | Bugs em produção |
| 4 | PolicyEngine — DB service pode ser `None`; validação pode falhar silenciosamente | Segurança |
| 5 | Detecção de resposta técnica via string matching (`_TECHNICAL_PATTERNS`) | Fragilidade |
| 6 | Escopo `GLOBAL` limita a 2 tools mas Orchestrator ignora scope na execução | Inconsistência |

## 10.6 Compliance (Lacunas Remanescentes)

| # | Lacuna | Status v2.0 |
|:--|:-------|:-----------|
| 1 | Anti-sycophancy runtime guardrail | Presente nos prompts (✅ SEG-1) mas sem verificação automática em runtime |
| 2 | FairnessGuard não-universal | Integrado em 4 agentes; ausente em 8 |
| 3 | LGPD em ATS — lista de campos sensíveis hardcoded | Sem sincronização dinâmica |
| 4 | Audit trail centralizado | 13/14 agentes OK; falta interview_graph |

---

# SEÇÃO 11: OPORTUNIDADES DE EVOLUÇÃO

> **Seção nova v2.0** — Conteúdo cruzado com `relatorio_capacidades_prompts_lia.md`

| # | Oportunidade | Complexidade | Impacto | Status Atual |
|:--|:-------------|:------------|:--------|:-------------|
| 1 | Score clicável no funil (breakdown) | Média | Alto | Ausente — dados existem em `lia_score_service.py` |
| 2 | Análise comparativa com UI dedicada | Média | Alto | Parcial — `compare_candidates` existe mas sem componente visual |
| 3 | Fit cultural com dados de entrevista | Alta | Alto | Ausente — WSI avalia competências mas não cruza com entrevistas |
| 4 | Auto-routing inteligente (aprende com uso) | Alta | Alto | Parcial — CascadedRouter tem cache mas sem aprendizado |
| 5 | Insights proativos no kanban | Média | Alto | Parcial — SaturationBadge é reativo, falta ProactiveAgentWorker |
| 6 | Relatório cross-vagas consolidado | Média | Médio | Parcial — `comparative_analysis` existe mas só vagas selecionadas |
| 7 | ML adaptativo (pesos por feedback) | Alta | Alto | Parcial — `Calibration_Adjustment` existe mas sempre 0 |
| 8 | Benchmark de mercado real | Alta | Alto | Parcial — IA estima, sem integração com Glassdoor/Levels.fyi |
| 9 | WSI assíncrono (candidato responde depois) | Média | Médio | Ausente — WSI é síncrono |
| 10 | Registro dinâmico de agentes (YAML) | Alta | Alto | Ausente |
| 11 | Multi-model por agente (GPT/Gemini) | Média | Alto | Ausente — todos usam Claude |
| 12 | RAG por domínio (embeddings) | Alta | Alto | Ausente |
| 13 | Circuit breaker para Pearch AI | Baixa | Médio | Ausente |
| 14 | Validar escopo de tools no backend | Baixa | Alto | Ausente — backend ignora scope_config |
| 15 | Streaming de pensamentos ReAct via WS | Média | Médio | Ausente |

---

*Relatório gerado por auditoria automatizada seguindo PLAYBOOK_AUDITORIA_PROFUNDA.md (4838 linhas, 44 runbooks de remediação). Atualizado para v2.0 em 13/03/2026 com análise profunda pós-sprints SEG-1 a SEG-5. Cruzado com `relatorio_capacidades_prompts_lia.md`. Todas as evidências baseadas em análise real do código-fonte.*
