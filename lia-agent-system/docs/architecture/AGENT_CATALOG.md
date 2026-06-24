# WeDOTalent Agent Catalog

**Versão:** 2026-06-17
**Branch:** `feat/benefits-prv-canonical`
**Base path:** `/home/runner/workspace/lia-agent-system`
**Objetivo:** Inventário completo de todos os agentes, domínios, tools e orquestradores do lia-agent-system. Guia de replicação para desenvolvedores que precisam entender a arquitetura ou criar novos agentes.

---

## Arquitetura de Agentes — Visão Geral

O lia-agent-system opera com quatro camadas:

**Camada 1 — Orquestradores de entrada**
Dois orquestradores recebem todas as mensagens. O `agent_chat_sse.py` é o transporte SSE canônico. O `MainOrchestrator` é o supervisor de fase-a-fase. Quando `LIA_FEDERATED_PRIMARY=true` (ativo em `.env`), o SSE roteia diretamente ao agente federado sem passar pelo `CascadedRouter`.

**Camada 2 — Agente Federado**
`RecruiterCopilotReActAgent` é o agente global do chat lateral — um único cérebro com 35+ tools de todos os domínios. Ativado por `LIA_FEDERATED_PRIMARY=true`. Substitui o modelo antigo de agentes separados por tela (kanban vs. funil).

**Camada 3 — Domain Agents**
22 domínios registrados via `@register_domain`. Cada domínio estende `ComplianceDomainPrompt` (LIA-C01, obrigatório). Os 16 domínios Agentic têm um `ReActAgent` próprio com triple-mixin `TenantAwareAgentMixin + LangGraphReActBase + EnhancedAgentMixin`. 2 domínios são Micro-Action (sem agents/, executam inline). 3 são Agentic Stubs (registrados mas `execute()` levanta `NotImplementedError`). 1 é Special Agentic (WizardOrchestrator/LangGraph).

**Camada 4 — Specialized Agents**
Agentes de propósito único: `WizardOrchestrator` (criação de vaga), `CustomAgentRuntime` (Agent Studio per-tenant), sub-agentes de sourcing (GitHub, StackOverflow, diversity, passive pipeline, referral, nurture).

**Modelos LLM canônicos:**
- `CANONICAL_SONNET_MODEL = "claude-sonnet-4-5-20250929"` — todos os agentes de decisão
- `CANONICAL_HAIKU_MODEL = "claude-haiku-4-5-20251001"` — roteamento e classificação

**Multi-tenancy:** `company_id` sempre vem do JWT via `Depends(require_company_id)`. Nunca do payload. Enforçado por `_current_company_id` ContextVar no middleware `auth_enforcement.py`.

---

## Tabela Resumo

| Agente / Domínio | Tipo | Problema de Negócio | Tools (count) | Status |
|---|---|---|---|---|
| MainOrchestrator | Orchestrator | Entry point de todas as mensagens | — | 🟢 |
| RecruiterCopilotReActAgent | Federated Agent | Copiloto global cross-tela | 35+ | 🟢 |
| WizardOrchestrator | Special Agentic | Criação de vaga conversacional | 18 wizard tools | 🟢 |
| CascadedRouter | Router | Roteamento multi-tier | — | 🟢 |
| CustomAgentRuntime | Agent Studio | Execução de agentes per-tenant | platform_tools.yaml | 🟢 |
| analytics | Agentic | KPIs, funil, previsões | 8 tools | 🟢 |
| ats_integration | Agentic | Sync com Gupy/Pandapé/Merge | 8 tools | 🟢 |
| automation | Agentic | Tarefas, automações, lembretes | 9 tools | 🟢 |
| candidate_self_service | Agentic | Portal read-only do candidato | 4 tools | 🟢 |
| communication | Agentic | Email, WhatsApp, Teams, SMS | 14 tools + 4 LLM | 🟢 |
| company_settings | Agentic | Configuração da empresa via chat | 9 tools + 4 LLM | 🟢 |
| cv_screening | Agentic | Triagem de CV, WSI, scoring | 18 tools + 5 LLM | 🟢 |
| digital_twin | Micro-Action | Gêmeo digital de especialista SME | 5 actions | 🟡 |
| hiring_policy | Agentic | Políticas de recrutamento | 12 tools | 🟢 |
| interview_intelligence | Agentic Stub | Análise de entrevistas | 5 actions (NotImplementedError) | 🔴 |
| interview_scheduling | Agentic | Agendamento de entrevistas | 14 tools | 🟢 |
| job_creation | Special Agentic | Wizard LangGraph/WizardOrchestrator | Wizard tools | 🟢 |
| job_management | Agentic | CRUD e lifecycle de vagas | 14 tools + 13 LLM | 🟢 |
| offer | Agentic | Carta-oferta estruturada | 6 actions + 8 LLM | 🟢 |
| pipeline | Agentic | Movimento no pipeline | 19 tools | 🟢 |
| recruiter_assistant | Agentic | Copiloto geral (fallback) | 35+ federados | 🟢 |
| recruitment_campaign | Micro-Action | Orquestração E2E de campanha | 4 actions | 🟡 |
| sourcing | Agentic | Busca multi-canal de talentos | 18+ tools | 🟢 |
| talent_intelligence | Agentic Stub | Ontologia de skills, gaps | 5 actions (NotImplementedError) | 🔴 |
| talent_pool | Agentic | Bancos de talentos | 6 tools | 🟢 |
| workforce | Agentic Stub parcial | Planejamento de headcount | 1 tool live | 🟡 |

---

## Orquestradores e Infraestrutura

### MainOrchestrator

**Arquivo:** `app/orchestrator/execution/main_orchestrator.py`
**Tipo:** Orchestrator — entry point unificado para todas as mensagens LIA

**Responsabilidade:** Pipeline multi-fase que consolida lógica antes distribuída entre `orchestrated_talent_chat.py`, `orchestrated_job_chat.py`, `pipeline_orchestrator.py`, e `agent_chat_ws.py`.

**Pipeline de fases:**
1. FairnessGuard pre-check sobre o texto do recrutador
2. TenantContext enrichment (carrega contexto do tenant)
3. Phase 0 — PendingAction / confirmação multi-turn
4. Phase 1 — ActionExecutor (intents de conjunto fechado)
5. Phase 2 — ConversationMemory + CascadedRouter → DomainWorkflow → ReAct agent

**Flags que alteram o comportamento:**
- `LIA_FEDERATED_PRIMARY=true` → roteia para `RecruiterCopilotReActAgent` diretamente
- `LIA_BUBBLE_VIA_SUPERVISOR=true` → usa MainOrchestrator como supervisor

**Frozensets importantes:**
- `_COMPANY_SETTINGS_INTENTS` → delega para `CompanySettingsReActAgent` (task #811)

---

### CascadedRouter

**Arquivo:** `app/orchestrator/routing/cascaded_router.py`
**Tipo:** Router multi-tier

**Tiers de roteamento (por custo crescente):**
| Tier | Nome | Mecanismo | Custo |
|---|---|---|---|
| 0.0 | Rail A hint override | `domain_hint` metadata do FE curto-circuita tudo | Zero |
| 0 | Memory Resolver | Resolve pronomes/referências | Mínimo |
| 1 | LRU in-process cache | MD5 do texto → resultado em memória | Zero |
| 2 | Redis distributed cache | Cache distribuído cross-instância | Mínimo |
| 3 | VectorSemanticCache | pgvector cosine >= 0.85 | Baixo |
| 4 | FastRouter | Regex/keyword matching | Baixo |
| 5 | LLM Cascade | Haiku → Sonnet → Opus | Médio/Alto |
| 6 | REMOVIDO | AutonomousReActAgent (Sprint 12.3-B) | — |
| Fallback | Clarification | `needs_clarification=True`, option chips | — |

**Modo federado:** Com `LIA_FEDERATED_PRIMARY=true`, o CascadedRouter é repurposado como **scope provider** (ferramentas dinâmicas ~15/turno) em vez de seletor de agente.

**Singleton:** `get_router()` em `cascaded_router.py:999`

---

### RecruiterCopilotReActAgent (Agente Federado)

**Arquivo:** `app/domains/recruiter_assistant/agents/recruiter_copilot_react_agent.py`
**Registro:** `@register_agent("recruiter_copilot")`
**Classe:** `RecruiterCopilotReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin)`
**LLM:** `CANONICAL_SONNET_MODEL`
**Ativado por:** `LIA_FEDERATED_PRIMARY=true` (ativo em `.env:182`)

**Responsabilidade:** Agente global único do chat lateral. Substitui o modelo anterior com agentes separados por tela (kanban vs. funil vs. vagas).

**FEDERATION_SPEC — tools disponíveis:**

| Categoria | Tools |
|---|---|
| Vagas (jobs_mgmt_tool_registry) | `list_jobs`, `view_job_details`, `get_portfolio_metrics`, `compare_jobs`, `check_sla`, `pause_job`, `reopen_job`, `close_job` |
| Candidatos (talent_tool_registry) | `list_candidates`, `search_candidates`, `view_candidate_profile`, `compare_candidates`, `rank_candidates`, `get_candidate_bigfive` |
| Pipeline (kanban_tool_registry) | `get_pipeline_summary`, `list_stage_candidates`, `batch_move_candidates`, `send_batch_communication`, `update_candidate_stage`, `reject_candidate` |
| Comunicação | `send_email`, `send_whatsapp` |
| Agendamento | `schedule_interview`, `check_interviewer_availability` |
| Wizard/Criação | `list_job_creation_sources`, `start_creation_from_source` |
| UI/Navegação (ui_tool_registry) | `open_ui`, `apply_table_state`, `select_rows`, `close_ui`, `close_panel` |
| Workforce | `get_workforce_plan_summary` |

**HITL:** Write tools gateadas (sensor G-FED-HITL, commit `f4b0bbff5`). `_HITL_ACTION_TYPES` inclui `batch_move_candidates`, `send_batch_communication`, `pause_job`, `reopen_job`, `publish_vacancy`.

**Escopo dinâmico:** `LIA_FEDERATED_SCOPED_TOOLS` (flag) ativa subconjunto de ~15 tools/turno via `get_scoped_tool_definitions()` baseado no `scope` ContextVar da página atual.

**Registry:** `app/domains/recruiter_assistant/agents/recruiter_copilot_tool_registry.py`

---

### WizardOrchestrator

**Arquivo:** `app/domains/job_creation/orchestrator/wizard_orchestrator.py`
**Tipo:** Special Agentic — single-LLM tool-calling loop
**LLM:** `CANONICAL_SONNET_MODEL` (override via `LIA_WIZARD_ORCHESTRATOR_MODEL`)
**Ativado por:** `LIA_WIZARD_ORCHESTRATOR=1` (ativo em `.env`)

**Responsabilidade:** Substitui o pipeline rígido LangGraph multi-nó (graph.py). Um único cérebro com visibilidade completa do job card, navega não-linearmente pelos campos.

**Fluxo canônico:**
```
intake → jd_enrichment → jd_gate → bigfive → competency
       → wsi_questions → eligibility → salary → configure_publish → review
```

**Entry point:** `app/domains/job_creation/services/wizard_session_service.py:987`

**Wizard tools disponíveis (`app/domains/job_creation/orchestrator/wizard_tools.py`):**
`set_job_fields`, `get_job_fields`, `generate_jd`, `enrich_jd`, `generate_wsi_questions`, `publish_job`, `validate_job_fields`, `get_job_suggestions`, `save_job_draft`, `get_company_config`, `generate_enriched_jd`, `check_job_draft_health`, `suggest_eligibility_templates`, `apply_eligibility_template_to_vacancy`, `suggest_pipeline_stage_templates`, `apply_pipeline_stage_template_to_vacancy`, `update_competencies`, `get_salary_benchmarks`

**Nós LangGraph legados (tombstoned):**
`nodes/publish.py`, `nodes/review.py`, `nodes/calibration.py` — levantam `RuntimeError` quando `RAILS_API_URL` ausente.

---

## Domínios — Catálogo Completo

### DOMAIN-01 · analytics

**Tipo:** Agentic
**Classe:** `AnalyticsDomain` em `app/domains/analytics/domain.py`
**Agente:** `AnalyticsReActAgent` em `app/domains/analytics/agents/analytics_react_agent.py`
**high_impact:** False

**Problema de negócio:** KPIs de recrutamento, análise de funil, detecção de anomalias, previsões, relatórios gerados por IA.

**Tools disponíveis:**
| Tool | Função |
|---|---|
| `_wrap_get_job_insights` | Insights de saúde e velocidade por vaga |
| `_wrap_predict_hiring_metrics` | Previsão de time-to-fill, probabilidade de contratação |
| `_wrap_generate_job_report` | Relatório completo de uma vaga |
| `_wrap_generate_candidate_report` | Relatório de candidato |
| `_wrap_get_search_analytics` | Analytics de buscas no funil |
| `_wrap_get_agent_performance` | Métricas de performance dos agentes IA |
| `_wrap_interpret_fairness_report` | LLM-as-judge: interpretação do relatório de fairness |
| `_wrap_generate_lgpd_audit_summary` | LLM-as-judge: sumário de auditoria LGPD |

**Como invocar:** "me dê os KPIs do mês", "analise o funil da vaga X", "quando vou fechar a vaga de Engenheiro?"

**Status:** 🟢

---

### DOMAIN-02 · ats_integration

**Tipo:** Agentic
**Classe:** `ATSIntegrationDomain` em `app/domains/ats_integration/domain.py`
**Agente:** `ATSIntegrationReActAgent` em `app/domains/ats_integration/agents/ats_integration_react_agent.py`

**Problema de negócio:** Sincronização bidirecional com ATS externos (Gupy, Pandapé, Merge). Importa candidatos e vagas, exporta dados.

**Tools disponíveis:**
`_wrap_sync_candidate_to_ats`, `_wrap_fetch_candidate_from_ats`, `_wrap_validate_ats_fields`, `_wrap_bulk_sync_candidates`, `_wrap_get_sync_status`, `_wrap_recommend_integrations_by_industry`, `_wrap_apply_integration_catalog_entry`, `_wrap_create_custom_integration_catalog_entry`

**Como invocar:** "sincronize com o Gupy", "importe candidatos do Pandapé para a vaga X"

**Status:** 🟢

---

### DOMAIN-03 · automation

**Tipo:** Agentic
**Classe:** `AutomationDomain` em `app/domains/automation/domain.py`
**Agente:** `AutomationReActAgent` em `app/domains/automation/agents/automation_react_agent.py`

**Problema de negócio:** Criação e gerenciamento de tarefas, decomposição de trabalho complexo em subtarefas, configuração de regras de automação.

**Tools disponíveis:**
`_wrap_decompose_task`, `_wrap_prioritize_tasks`, `_wrap_get_execution_plan`, `_wrap_build_dag`, `_wrap_check_dependencies`, `_wrap_get_next_tasks`, `_wrap_suggest_webhook_event_types`, `_wrap_apply_webhook_event_subscription`, `_wrap_create_custom_webhook_event_type`

**Como invocar:** "crie uma tarefa para revisar os 10 candidatos da vaga X", "quais são minhas próximas tarefas?"

**Status:** 🟢

---

### DOMAIN-04 · candidate_self_service

**Tipo:** Agentic
**Classe:** `CandidateSelfServiceDomain` em `app/domains/candidate_self_service/domain.py`
**Agente:** `CandidateSelfServiceAgent` em `app/domains/candidate_self_service/agents/candidate_react_agent.py`
**high_impact:** True (`fairness_action_type=candidate_response`)
**Aliases:** `candidate_status`, `candidate_portal`

**Problema de negócio:** Portal read-only para candidatos verificarem status da candidatura, entrevistas, feedback do WSI, e direito de explicação LGPD Art. 20.

**Tools disponíveis:**
| Tool | Função |
|---|---|
| `get_status` | Status da candidatura do candidato |
| `get_interview_info` | Informações sobre entrevistas agendadas |
| `get_feedback` | Feedback do processo de triagem WSI |
| `get_lgpd_info` | Explicação LGPD Art. 20 do processo decisório |

**Status:** 🟢

---

### DOMAIN-05 · communication

**Tipo:** Agentic
**Classe:** `CommunicationDomain` em `app/domains/communication/domain.py`
**Agente:** `CommunicationReActAgent`

**Problema de negócio:** Gerenciamento de comunicação multi-canal (email, WhatsApp, Teams, SMS). Templates, envio bulk, alertas configuráveis.

**Tools disponíveis:**
`_wrap_send_email` (HITL), `_wrap_send_whatsapp` (HITL), `_wrap_get_communication_history`, `_wrap_schedule_message`, `_wrap_check_rate_limit`, `_wrap_suggest_communication_policy`, `_wrap_suggest_alert_rule_templates`, `_wrap_apply_alert_rule_template`, `_wrap_create_custom_alert_rule_template`

**Como invocar:** "envie um email de atualização para os candidatos em entrevista da vaga X"

**Status:** 🟢

**Notas:** `send_email` e `send_whatsapp` são HITL-gateados via `hitl_preflight` (quando `LIA_HITL_GATE=on`, atualmente DORMANT).

---

### DOMAIN-06 · company_settings

**Tipo:** Agentic
**Classe:** `CompanySettingsDomain` em `app/domains/company_settings/domain.py`
**Agente:** `CompanySettingsReActAgent`

**Problema de negócio:** Configuração conversacional da empresa via chat: perfil, cultura e EVP, stack tecnológico, benefícios, planejamento de headcount.

**Tools disponíveis:**
`_wrap_get_company_profile`, `_wrap_save_company_field`, `_wrap_save_company_section`, `_wrap_analyze_company_website`, `_wrap_process_uploaded_document`, `_wrap_import_workforce_plan`, `_wrap_save_hiring_policy`, `_wrap_get_company_completion`, `_wrap_toggle_learning_loop`, `_wrap_toggle_lia_field`, `_wrap_record_dsr_action`, `_wrap_suggest_recruiting_policy`, `_wrap_import_benefits_from_data`, `_wrap_save_hiring_policy_global`

**Como invocar:** "atualize nossa missão", "analise nosso site e preencha o perfil", "desative o campo stack tecnológico para a IA"

**Status:** 🟢

---

### DOMAIN-07 · cv_screening

**Tipo:** Agentic
**Classe:** `CVScreeningDomain` em `app/domains/cv_screening/domain.py`
**Agente:** `PipelineReActAgent`
**high_impact:** True (`fairness_action_type=shortlist`)

**Problema de negócio:** Análise de CVs, avaliação WSI, scoring de candidatos, mapeamento Big Five, classificação Dreyfus/Bloom, triagem em lote.

**Tools disponíveis (seleção):**
`_wrap_view_candidate_profile`, `_wrap_move_candidate` (HITL), `_wrap_analyze_cv`, `_wrap_run_wsi_screening`, `_wrap_schedule_interview`, `_wrap_send_communication` (HITL), `_wrap_add_notes`, `_wrap_batch_move` (HITL), `_wrap_add_to_shortlist`, `_wrap_view_screening_results`, `_wrap_generate_offer` (HITL), `_wrap_finalize_hiring` (HITL), `_wrap_update_status`, `_wrap_get_evaluation_criteria`, `_wrap_get_pipeline_summary`, `_wrap_search_talent_pool`, `_wrap_get_company_culture`, `_wrap_get_analytics_summary`

**Como invocar:** "faça a triagem do João Silva para a vaga X", "quais são os 5 melhores candidatos por WSI?"

**Status:** 🟢

---

### DOMAIN-08 · digital_twin

**Tipo:** Micro-Action (sem agents/)
**Classe:** `DigitalTwinDomain` em `app/domains/digital_twin/domain.py`
**high_impact:** True (`fairness_action_type=screening`)

**Problema de negócio:** Cria e usa gêmeos digitais de especialistas SME via RAG few-shot evaluation.

**Actions disponíveis:** `create_twin`, `evaluate_with_twin`, `list_twins`, `index_twin_audio`, `deactivate_twin`

**Status:** 🟡 — registrado e funcional, sem agente dedicado. Executa inline no domain.py.

---

### DOMAIN-09 · hiring_policy

**Tipo:** Agentic
**Classe:** `HiringPolicyDomain` em `app/domains/hiring_policy/domain.py`
**Agente:** `PolicyReActAgent`

**Problema de negócio:** Configuração de políticas de contratação via conversa: regras de pipeline, agendamento, padrões de comunicação, critérios de triagem.

**Tools disponíveis:**
`_wrap_get_current_policy`, `_wrap_save_policy_field`, `_wrap_get_policy_summary`, `_wrap_validate_policy_compliance`, `_wrap_get_company_context`, `_wrap_get_industry_benchmarks`, `_wrap_get_platform_benchmarks`, `_wrap_explain_policy_impact`, `_wrap_get_setup_progress`, `_wrap_detect_policy_impact_anomalies`, `_wrap_get_policy_effectiveness_report`, `_wrap_save_policy_block`, `_wrap_apply_industry_defaults`

**Como invocar:** "configure para aprovar candidatos automaticamente acima de 85%", "como está nossa conformidade LGPD?"

**Status:** 🟢

---

### DOMAIN-10 · interview_intelligence

**Tipo:** Agentic Stub (registrado — `execute()` levanta `NotImplementedError`)
**Classe:** `InterviewIntelligenceDomain` em `app/domains/interview_intelligence/domain.py`

**Actions disponíveis (não executáveis):** `analyze_interview_recording`, `detect_interview_bias`, `compare_interview_performance`, `generate_interview_opinion`, `generate_candidate_feedback`

**Status:** 🔴 — `capabilities.yaml` tem `intent_keywords: {}` (nunca roteado em produção).

---

### DOMAIN-11 · interview_scheduling

**Tipo:** Agentic
**Classe:** `InterviewSchedulingDomain` em `app/domains/interview_scheduling/domain.py`

**Problema de negócio:** Agendamento e gestão de entrevistas: agendar, reagendar, cancelar, link de auto-agendamento, lembretes.

**Tools disponíveis:**
`_wrap_schedule_interview`, `_wrap_check_interviewer_availability`

**Actions do domínio (14):** `schedule_interview`, `reschedule_interview`, `cancel_interview`, `check_availability`, `generate_self_scheduling_link`, `find_common_slots`, `send_reminder`, `schedule_reminders`, `list_today_interviews`, `resolve_conflict`, `start_wsi_interview`, `send_question`, `analyze_response`, `transcribe_audio`

**Como invocar:** "agende uma entrevista técnica com Maria para quinta às 14h"

**Status:** 🟢

---

### DOMAIN-12 · job_creation

**Tipo:** Special Agentic (LangGraph + WizardOrchestrator)
**Classe:** `JobCreationDomain` em `app/domains/job_creation/domain.py`

**Engine de execução:**
- Com `LIA_WIZARD_ORCHESTRATOR=1` (ativo): `WizardOrchestrator`
- Sem a flag (legado/tombstoned): `get_job_creation_graph()` em `graph.py`

**Como invocar:** Ativado via `/criar vaga` slash command.

**Status:** 🟢

---

### DOMAIN-13 · job_management

**Tipo:** Agentic
**Classe:** `JobManagementDomain` em `app/domains/job_management/domain.py`
**Agente:** `JobsManagementReActAgent`

**Problema de negócio:** Operações de lifecycle de vagas fora do wizard: CRUD, configuração de pipeline, publicação, otimização de JD, gerenciamento de templates.

**Tools disponíveis (seleção):**
`_wrap_generate_screening_questions`, `_wrap_dispatch_screening`, `_wrap_request_approval`, `_wrap_publish_vacancy` (HITL), `_wrap_change_vacancy_status` (HITL), `_wrap_validate_job_requirements`, `_wrap_get_salary_benchmarks`, `_wrap_update_competencies`, `_wrap_suggest_eligibility_templates`, `_wrap_apply_eligibility_template_to_vacancy`, `_wrap_suggest_pipeline_stage_templates`, `_wrap_list_job_creation_sources`, `_wrap_start_creation_from_source`, `_wrap_search_jobs`, `_wrap_get_job_details`, `_wrap_pause_job` (HITL), `_wrap_close_job` (HITL), `_wrap_publish_job` (HITL), `_wrap_get_job_velocity`, `_wrap_get_job_quality_metrics`, `_wrap_get_job_benchmark`

**Como invocar:** "pause a vaga de Analista de Dados", "gere perguntas WSI para Engenheiro Sênior"

**Status:** 🟢

---

### DOMAIN-14 · offer

**Tipo:** Agentic
**Classe:** `OfferDomain` em `app/domains/offer/domain.py`
**Agente:** `OfferConciergeAgent` em `app/domains/offer/agents/offer_concierge_agent.py`
**high_impact:** True (`fairness_action_type=offer`)
**Aliases:** `offer_agent`, `send_offer`, `proposal_agent`

**Problema de negócio:** Lifecycle completo da carta-oferta: criação, atualização, envio (HITL-gateado), cancelamento, histórico de negociação.

**Tools disponíveis:**
| Tool | HITL? |
|---|---|
| `create_offer_draft` | Não |
| `update_offer_draft` | Não |
| `get_offer_draft` | Não |
| `send_offer` | **Sim** |
| `prepare_offer_manual_send` | Não |
| `cancel_offer` | Não |
| `_wrap_get_offer_status` (LLM) | Não |
| `_wrap_suggest_next_start_date` (LLM) | Não |
| `_wrap_escalate_to_recruiter` (LLM) | Não |
| `_wrap_log_negotiation_event` (LLM) | Não |
| `_wrap_draft_response_to_candidate` (LLM) | Não |

**Como invocar:** "crie uma proposta para a Maria com salário de R$ 8.000", "envie a carta-oferta para o João"

**Status:** 🟢

**Notas:** `OfferService.check_can_send()` enforça `manager_approval_for_offer` como hard gate fail-closed. Defense-in-depth: `mark_sent()` também enforça o mesmo gate.

---

### DOMAIN-15 · pipeline

**Tipo:** Agentic
**Classe:** `PipelineDomain` em `app/domains/pipeline/domain.py`
**high_impact:** True (`fairness_action_type=rejection`)

**Problema de negócio:** Visualização do pipeline e movimentação de candidatos entre etapas. Previsão de sub-status, sugestão de próximas ações.

**Tools disponíveis (seleção):**
`_wrap_get_candidate_profile`, `_wrap_get_candidate_wsi_scores`, `_wrap_get_candidate_screening_results`, `_wrap_get_candidate_salary_info`, `_wrap_update_candidate_field`, `_wrap_request_data_collection`, `_wrap_get_stage_sub_statuses`, `_wrap_suggest_sub_status`, `_wrap_extract_preferences`, `_wrap_validate_transition`, `_wrap_get_job_context`, `_wrap_schedule_secondary_task`, `_wrap_personalize_communication`, `_wrap_check_rejection_fairness`, `_wrap_check_candidate_availability`, `_wrap_get_recruiter_preferences`, `_wrap_save_recruiter_preference`, `_wrap_get_interview_details`, `_wrap_cancel_interview`, `_wrap_reschedule_interview`

**Como invocar:** "mova o João para entrevista técnica", "qual sub-status usar para candidato aguardando documentação?"

**Status:** 🟢

---

### DOMAIN-16 · recruiter_assistant

**Tipo:** Agentic (fallback do CascadedRouter)
**Classe:** `RecruiterAssistantDomain` em `app/domains/recruiter_assistant/domain.py`
**Agente primário:** `RecruiterCopilotReActAgent` (ver seção dedicada)

**Sub-agentes hospedados:**
| Sub-agente | Contexto |
|---|---|
| `RecruiterCopilotReActAgent` | Global (federated) |
| `KanbanReActAgent` | Kanban de vaga |
| `TalentFunnelReActAgent` | Funil de talentos |
| `jobs_mgmt_react_agent` | Lista de vagas |
| `kanban_action_agent` | Ações no kanban |
| `kanban_insight_agent` | Insights do kanban |
| `kanban_search_agent` | Busca no kanban |

**Status:** 🟢

---

### DOMAIN-17 · recruitment_campaign

**Tipo:** Micro-Action (sem agents/)
**Classe:** `RecruitmentCampaignDomain` em `app/domains/recruitment_campaign/domain.py`

**Actions disponíveis:** `create_campaign`, `get_campaign_progress`, `advance_campaign` (HITL), `list_campaigns`

**Status:** 🟡 — arquitetura de wrapper pattern. Funcional mas limitado — sem ReActAgent.

---

### DOMAIN-18 · sourcing

**Tipo:** Agentic
**Classe:** `SourcingDomain` em `app/domains/sourcing/domain.py`
**Agente:** `SourcingReActAgent` em `app/domains/sourcing/agents/sourcing_react_agent.py`
**high_impact:** True (`fairness_action_type=sourcing`)

**Problema de negócio:** Busca e atração de talentos em múltiplos canais: Pearch AI, Apify, LinkedIn, banco interno, GitHub, StackOverflow.

**Tools do sourcing_tool_registry:**
`_wrap_set_search_criteria`, `_wrap_suggest_skills`, `_wrap_search_candidates`, `_wrap_filter_results`, `_wrap_analyze_profile`, `_wrap_compare_candidates`, `_wrap_score_candidate`, `_wrap_add_to_shortlist`, `_wrap_remove_from_shortlist`, `_wrap_rank_candidates`, `_wrap_send_outreach` (HITL), `_wrap_generate_message`, `_wrap_track_response`, `_wrap_view_candidate`, `_wrap_generate_report`, `_wrap_enrich_candidate_profile`, `_wrap_enrich_candidate_contact`, `_wrap_rag_search`

**Sub-registries:** `github_tool_registry`, `stackoverflow_tool_registry`, `diversity_tool_registry`, `passive_pipeline_tool_registry`, `referral_tool_registry`, `nurture_sequence_tool_registry`

**Como invocar:** "busque desenvolvedores React Sênior com experiência em TypeScript no sul do Brasil"

**Status:** 🟢

---

### DOMAIN-19 · talent_intelligence

**Tipo:** Agentic Stub (registrado — `execute()` levanta `NotImplementedError`)
**Classe:** `TalentIntelligenceDomain` em `app/domains/talent_intelligence/domain.py`

**Actions disponíveis (não executáveis):** `infer_related_skills`, `get_skill_adjacencies`, `analyze_skill_gaps`, `map_candidate_skills_to_ontology`, `match_internal_candidates`, `forecast_hiring_needs`

**Status:** 🔴 — `capabilities.yaml` vazio, nunca roteado.

**Notas:** `get_workforce_plan_summary` do `workforce_tool_registry` está LIVE — consumido pelo `RecruiterCopilotReActAgent`.

---

### DOMAIN-20 · talent_pool

**Tipo:** Agentic
**Classe:** `TalentPoolDomain` em `app/domains/talent_pool/domain.py`
**Agente:** `TalentPoolReActAgent`
**high_impact:** True (`fairness_action_type=sourcing`)

**Problema de negócio:** Gerenciamento de bancos de talentos: criação, listagem, adição de candidatos, migração para vagas.

**Tools disponíveis:**
`_wrap_list_talent_pools`, `_wrap_get_pool_candidates`, `_wrap_create_talent_pool`, `_wrap_add_candidate_to_pool`, `_wrap_move_pool_to_job` (HITL), `_wrap_create_job_from_pool` (HITL)

**Como invocar:** "liste nossos bancos de talentos", "mova os 10 melhores candidatos do banco React para a vaga X"

**Status:** 🟢

---

### DOMAIN-21 · workforce

**Tipo:** Agentic Stub parcial
**Classe:** `WorkforceDomain` em `app/domains/workforce/domain.py`

**Tools disponíveis:**
`_wrap_get_workforce_plan_summary` (LIVE como ferramenta federada)

**Status:** 🟡 — `execute()` levanta `NotImplementedError` (stub), mas `get_workforce_plan_summary` está LIVE como ferramenta no `RecruiterCopilotReActAgent`.

---

### DOMAIN-22 · agent_studio

**Tipo:** Special Agentic
**Classe:** `AgentStudioDomain` em `app/domains/agent_studio/domain.py`
**Agente de execução:** `CustomAgentRuntime`

**Problema de negócio:** Plataforma para recrutadores criarem e gerenciarem agentes customizados. Marketplace, instalação, dry-run.

**Actions do domínio:**
`create_sourcing_agent`, `calibrate_agent`, `get_agent_status`, `list_agents`, `run_multi_strategy`, `create_custom_agent`, `list_custom_agents`, `test_custom_agent`, `execute_custom_agent`, `publish_to_marketplace`, `browse_marketplace`, `install_from_marketplace`, `assign_to_crew`, `get_studio_consumption`, `deactivate_agent`, `uninstall_agent`, `explain_agent_studio`

**Como invocar:** "crie um agente para sourcing de desenvolvedores iOS", "instale o agente de diversidade do marketplace"

**Status:** 🟢

---

### CustomAgentRuntime

**Arquivo:** `app/domains/agent_studio/custom_agent_runtime.py`
**Classe:** `CustomAgentRuntime(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin)`

**Mecanismos de segurança:**
- **P0-2 Review gate:** agentes instalados do marketplace ficam em `pending_review` até aprovação de `wedotalent_admin`
- **Dry-run:** ContextVar `_DRY_RUN` intercepta write tools
- **Multi-tenancy:** usa ContextVar `_current_company_id` canônico
- **HITL:** `HITL_REQUIRED_TOOLS` carregado de `platform_tools.yaml`

**Cache:** `get_or_create_runtime(agent_id)` — cached per agent_id

---

## Padrões de Implementação para Novos Agentes

### Padrão 1 — ReActAgent completo (16 domínios canônicos)

```python
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin

@register_agent("meu_dominio")
class MeuDominioReActAgent(
    TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin
):
    def _get_tools(self) -> list:
        return get_meu_dominio_tools()
```

- `TenantAwareAgentMixin` injeta contexto do tenant no system prompt (cached 300s)
- `LangGraphReActBase` fornece `_process_langgraph` com streaming, drain de RRP, HITL, ui_actions
- `EnhancedAgentMixin` adiciona observabilidade

### Padrão 2 — Domínio registrado (@register_domain)

```python
from app.domains.registry import register_domain
from app.domains.compliance_base import ComplianceDomainPrompt

@register_domain  # LIA-C01: obrigatório ser ComplianceDomainPrompt
class MeuDomain(ComplianceDomainPrompt):
    domain_id = "meu_dominio"
    _compliance_config = {
        'high_impact': False,
        'fairness_action_type': 'general'
    }
```

**BLOQUEANTE:** `registry.py` verifica `issubclass(cls, ComplianceDomainPrompt)` na decoração. Falhar = `TypeError` no boot.

### Padrão 3 — Tool wrapper canônico

```python
from app.shared.tool_handler import tool_handler
from app.shared.runtime_context import with_runtime_context

@with_runtime_context("company_id")    # declarativo (opcional)
@tool_handler("meu_dominio")           # segurança fail-closed (obrigatório)
async def _wrap_minha_tool(**kwargs) -> dict:
    company_id = kwargs["company_id"]  # garantido pelo tool_handler
    ...
```

**Regras:**
- `company_id` NUNCA vem do payload — sempre do JWT/ContextVar
- `@tool_handler` é obrigatório (fail-closed se `_current_company_id` ContextVar vazio)
- `@with_runtime_context` acima de `@tool_handler`

### Padrão 4 — FairnessGuard em novo endpoint

```python
from app.shared.compliance.fairness_guard import FairnessGuard

_fg = FairnessGuard()

result = _fg.check(user_text)
if result.is_blocked:
    _fg.log_check(result=result, session_id=req.session_id, company_id=company_id)
    raise HTTPException(400, detail={
        "error": "fairness_blocked",
        "fairness_blocked": True,
        "educational_message": result.educational_message,
        "category": result.category,
        "blocked_terms": result.blocked_terms or []
    })
```

---

## Infraestrutura de Compliance e Segurança

### Multi-tenancy
- `_current_company_id` ContextVar em `app/middleware/auth_enforcement.py`
- `require_company_id` dependency garante que o JWT tem `company_id`
- `get_verified_company_id`: retorna 403 se header `X-Company-ID` divergir do JWT
- PROIBIDO: `company_id` no payload, `Header(alias="X-Company-ID")` como fonte principal

### FairnessGuard
- 13+ superfícies wired (audit 2026-06-14: 100% coverage confirmada)
- `FairnessAuditLog.session_id` e `FairnessPolicyViolation.correlation_id` populados desde migration 283
- Legal: CLT Art. 373-A, CF Art. 5º, Lei 9.029/95, LGPD Art. 20

### HITL Gate
- `LIA_HITL_GATE` DORMANT (comentado em `.env:186`)
- 7 tools gateadas: `close_job`, `send_email`, `send_whatsapp`, `bulk_send`, `reject_candidate`, `bulk_update_stage`, `publish_job`
- Para ativar: setar `LIA_HITL_GATE=on` no ambiente

### PII
- `app/shared/pii_masking.py` é shim para `libs/lia-pii/lia_pii/masking.py`
- ADR-LGPD-002: 3 camadas distintas (output→recrutador = passthrough, input→LLM vendor = strip, logs = sempre mascara)

### Learning Loops
- Gate mestre: `load_learning_loops_toggles()` em `app/shared/services/learning_loops_toggles.py`
- Defaults: `enabled=True`, `jd_similar_suggestion=True`, `bigfive_department_history=False`, `wsi_question_effectiveness=False`
- Todos os writes são fail-soft (try/except, log + continue)

---

## Flags de Ambiente Críticas

| Flag | Valor em Dev | Efeito |
|---|---|---|
| `LIA_WIZARD_ORCHESTRATOR` | `1` | Ativa WizardOrchestrator em vez do LangGraph rígido |
| `LIA_FEDERATED_PRIMARY` | `true` (line 182) | Chat lateral roteia direto ao RecruiterCopilotReActAgent |
| `LIA_BUBBLE_VIA_SUPERVISOR` | não definido | Quando true, usa MainOrchestrator como supervisor |
| `LIA_HITL_GATE` | comentado (OFF) | Quando `on`, ativa gates de confirmação humana nas 7 tools |
| `LIA_FEDERATED_SCOPED_TOOLS` | não definido | Quando true, ativa subset dinâmico de ~15 tools/turno |
| `RAILS_API_URL` | não definido | Ausência = nodes LangGraph legados tombstoned |
| `APP_ENV` | `development` | Ativa bypass de token budget para dev tenants |
