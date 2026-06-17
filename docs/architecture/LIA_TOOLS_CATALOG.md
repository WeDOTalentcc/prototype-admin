# LIA — Catálogo Completo de Tools (120+ tools em 28+ registries)

> Inventário exaustivo de todas as tools da LIA, organizadas por registry e categoria. Fonte primária: `lia-agent-system/app/` (322 instanciações de `ToolDefinition(`). Fonte canônica curada: `lia-agent-system/app/tools/tool_registry_metadata.yaml` (74 tools com `scope` + `allowed_agents`).

**Legenda de escopo:**
`G` = GLOBAL · `TF` = TALENT_FUNNEL · `JT` = JOB_TABLE · `IJ` = IN_JOB · `U` = UNIVERSAL

---

## 1. Totais

| Métrica | Valor |
|---------|-------|
| Arquivos com `ToolDefinition(` | 48 |
| Arquivos `*tool_registry*.py` | 33 |
| Instanciações `ToolDefinition(` no código | 322 |
| Tools canônicas no YAML | 74 |
| Tools únicas aproximadas (dedup cross-domain) | ~260 |

Muitas tools aparecem redefinidas por agente com comportamento escopado (`search_candidates`, `generate_report`, `get_job_details`, `compare_candidates`, `schedule_interview`, etc.). A LIA trata isso como feature: cada agente consome a sua versão com ACL/contexto.

---

## 2. Índice de Registries

### 2.1 Registries principais (`*tool_registry*.py`)

| # | Arquivo | Domínio | Agente | Tools |
|---|---------|---------|--------|-------|
| 1 | `app/domains/analytics/agents/analytics_tool_registry.py` | analytics | AnalyticsAgent | 6 |
| 2 | `app/domains/ats_integration/agents/ats_integration_tool_registry.py` | ats_integration | AtsIntegrationAgent | 5 |
| 3 | `app/domains/automation/agents/automation_tool_registry.py` | automation | AutomationAgent | 6 |
| 4 | `app/domains/autonomous/agents/autonomous_tool_registry.py` | autonomous (Tier 6) | AutonomousReActAgent | 41 |
| 5 | `app/domains/communication/agents/communication_tool_registry.py` | communication | CommunicationAgent | 5 |
| 6 | `app/domains/company_settings/agents/company_tool_registry.py` | company_settings | CompanySetupAgent | 7 |
| 7 | `app/domains/cv_screening/agents/pipeline_tool_registry.py` | cv_screening | CVScreeningPipelineAgent | 15 |
| 8 | `app/domains/hiring_policy/agents/policy_tool_registry.py` | hiring_policy | HiringPolicyAgent | 13 |
| 9 | `app/domains/job_management/agents/wizard_tool_registry.py` | job_management | JobWizardAgent | 10 |
| 10 | `app/domains/pipeline/agents/pipeline_tool_registry.py` | pipeline | PipelineTransitionAgent | 20 |
| 11 | `app/domains/pipeline/agents/pipeline_action_tool_registry.py` | pipeline | PipelineActionAgent | refs |
| 12 | `app/domains/pipeline/agents/pipeline_context_tool_registry.py` | pipeline | PipelineContextAgent | refs |
| 13 | `app/domains/pipeline/agents/pipeline_decision_tool_registry.py` | pipeline | PipelineDecisionAgent | refs |
| 14 | `app/domains/policy/agents/tool_registry.py` | policy | PolicySetupAgent | 0 |
| 15 | `app/domains/recruiter_assistant/agents/jobs_mgmt_tool_registry.py` | recruiter_assistant | JobsManagementAgent | 14 |
| 16 | `app/domains/recruiter_assistant/agents/kanban_tool_registry.py` | recruiter_assistant | KanbanAgent | 22 |
| 17 | `app/domains/recruiter_assistant/agents/kanban_action_tool_registry.py` | recruiter_assistant | KanbanActionAgent | refs |
| 18 | `app/domains/recruiter_assistant/agents/kanban_insight_tool_registry.py` | recruiter_assistant | KanbanInsightAgent | refs |
| 19 | `app/domains/recruiter_assistant/agents/kanban_search_tool_registry.py` | recruiter_assistant | KanbanSearchAgent | refs |
| 20 | `app/domains/recruiter_assistant/agents/talent_tool_registry.py` | recruiter_assistant | TalentAgent | 13 |
| 21 | `app/domains/sourcing/agents/sourcing_tool_registry.py` | sourcing | SourcingAgent | 18 |
| 22 | `app/domains/sourcing/agents/sourcing_planner_tool_registry.py` | sourcing | SourcingPlannerAgent | refs |
| 23 | `app/domains/sourcing/agents/sourcing_search_tool_registry.py` | sourcing | SourcingSearchAgent | refs |
| 24 | `app/domains/sourcing/agents/sourcing_enrich_tool_registry.py` | sourcing | SourcingEnrichAgent | refs |
| 25 | `app/domains/sourcing/agents/sourcing_engagement_tool_registry.py` | sourcing | SourcingEngagementAgent | refs |
| 26 | `app/domains/sourcing/agents/diversity_tool_registry.py` | sourcing | DiversitySourcingAgent | 3 |
| 27 | `app/domains/sourcing/agents/github_tool_registry.py` | sourcing | GitHubSourcingAgent | 4 |
| 28 | `app/domains/sourcing/agents/stackoverflow_tool_registry.py` | sourcing | StackOverflowSourcingAgent | 3 |
| 29 | `app/domains/sourcing/agents/passive_pipeline_tool_registry.py` | sourcing | PassivePipelineAgent | 3 |
| 30 | `app/domains/sourcing/agents/referral_tool_registry.py` | sourcing | ReferralSourcingAgent | 4 |
| 31 | `app/domains/sourcing/agents/nurture_sequence_tool_registry.py` | sourcing | NurtureSequenceAgent | 5 |
| 32 | `app/shared/global_tool_registry.py` | shared | runtime permission gate | — |
| 33 | `app/tools/tool_registry_loader.py` | shared | YAML validator | — |

### 2.2 Módulos de handler com `ToolDefinition(` (fora de registries)

| # | Arquivo | Domínio | Tools |
|---|---------|---------|-------|
| 34 | `app/domains/analytics/tools/analytics_query_tools/registry.py` | analytics | 19 |
| 35 | `app/domains/communication/tools/communication_tools.py` | communication | 5 |
| 36 | `app/domains/cv_screening/tools/candidate_tools.py` | cv_screening | 8 |
| 37 | `app/domains/cv_screening/tools/cv_match_tool.py` | cv_screening | 1 |
| 38 | `app/domains/cv_screening/tools/cv_upload_tool.py` | cv_screening | 3 |
| 39 | `app/domains/job_management/tools/job_tools.py` | job_management | 5 |
| 40 | `app/domains/job_management/tools/job_wizard_tools.py` | job_management | 9 |
| 41 | `app/domains/job_management/tools/query_tools.py` | job_management | 5 |
| 42 | `app/domains/recruiter_assistant/tools/pipeline_tools.py` | recruiter_assistant | 1 |
| 43 | `app/domains/sourcing/tools/query_tools.py` | sourcing | 9 |
| 44 | `app/domains/talent_intelligence/tools/registry.py` | talent_intelligence | 15 |
| 45 | `app/shared/tools/export_tools.py` | shared | 4 |
| 46 | `app/shared/tools/insight_tools.py` | shared | 4 |
| 47 | `app/shared/tools/predictive_tools.py` | shared | 4 |
| 48 | `app/shared/tools/proactive_tools.py` | shared | 4 |

### 2.3 Whitelist runtime (não usa `ToolDefinition`)

- `app/domains/agent_studio/custom_agent_runtime.py::PLATFORM_TOOLS_REGISTRY` — dict de 15 tools classificadas `read`/`write` para Tier 7 (Studio Agents).

---

## 3. Catálogo por Categoria

### 3.1 Job Wizard
Arquivos: `job_management/agents/wizard_tool_registry.py`, `job_management/tools/job_wizard_tools.py`

- `search_salary_benchmark` — Benchmark salarial por cargo/senioridade/local (JT, agents: job_planner/job_intake/orchestrator/job_wizard)
- `validate_job_fields` — Valida preenchimento dos campos (JT)
- `validate_job_requirements` — Valida qualidade de requisitos (JT)
- `get_salary_benchmarks` — Benchmarks agregados de mercado (JT)
- `get_job_suggestions` — Sugestões IA para JD/requisitos (JT)
- `save_job_draft` — Persiste draft (JT)
- `get_company_config` — Workflow/aprovação/config (G)
- `get_intelligent_salary` — Salário inteligente (mercado + budget) (JT)
- `get_intelligent_skills` — Skills sugeridas por título/senioridade (JT)
- `capture_wizard_feedback` — Feedback do UX do wizard (G)
- `generate_enriched_jd` — Gera JD enriquecida (JT)
- `check_job_draft_health` — Saúde do draft (JT)
- `generate_report` — Relatório do wizard (G)

### 3.2 Job Management
Arquivos: `job_management/tools/job_tools.py`, `query_tools.py`

- `create_job` — Cria vaga (JT)
- `update_job` — Atualiza campos (JT)
- `pause_job` / `close_job` / `publish_job` — Lifecycle (JT)
- `search_jobs` — Busca vagas por critérios (JT)
- `get_job_details` — Detalhes + candidatos opcional (JT)
- `get_job_velocity` — Velocidade da vaga (JT)
- `get_job_quality_metrics` — Qualidade da vaga (JT)
- `get_job_benchmark` — Benchmark de uma vaga (JT)

### 3.3 Candidate / CV Screening
Arquivos: `cv_screening/tools/candidate_tools.py`, `cv_screening/tools/cv_upload_tool.py`, `cv_screening/tools/cv_match_tool.py`, `cv_screening/agents/pipeline_tool_registry.py`

- `update_candidate_stage` — Muda stage do candidato (IJ)
- `add_candidate_to_vacancy` — Talent pool → vaga (TF)
- `reject_candidate` — Rejeita com motivo opcional (IJ)
- `shortlist_candidate` — Adiciona à shortlist (TF)
- `bulk_update_candidates_stage` — Bulk stage move (IJ)
- `add_to_list` — Adiciona a lista nomeada (TF)
- `wsi_screening` — Inicia screening WSI voz/texto/vídeo (IJ)
- `hide_candidate` — Oculta candidato (IJ)
- `view_candidate_profile` — Visualiza perfil (IJ)
- `move_candidate` — Alias de update_candidate_stage (IJ)
- `analyze_cv` — Análise CV (IJ)
- `run_wsi_screening` — Roda WSI (variante autonomous) (IJ)
- `schedule_interview` — Agenda entrevista (IJ)
- `send_communication` — Envia mensagem inline (IJ)
- `add_notes` — Anexa nota/observação (IJ)
- `batch_move` — Batch move (IJ)
- `add_to_shortlist` — Adiciona à shortlist (TF)
- `view_screening_results` — Breakdown de score WSI (IJ)
- `view_interview_notes` — Feedback de entrevista (IJ)
- `generate_offer` — Gera proposta para finalista (IJ)
- `finalize_hiring` — Fecha contratação (IJ)
- `update_status` — Atualiza status do candidato (IJ)
- `parse_and_create_candidate` — Parse CV → cria candidato (TF)
- `add_to_vacancy` — Anexa novo candidato à vaga (IJ)
- `create_and_screen_candidate` — Upload + auto-screen (IJ)
- `analyze_cv_match` — Match candidato × job (IJ)

### 3.4 Pipeline (split em 3 sub-agentes)
Arquivos: `pipeline/agents/pipeline_tool_registry.py`, `pipeline_action_tool_registry.py`, `pipeline_context_tool_registry.py`, `pipeline_decision_tool_registry.py`

**Context (7):**
- `get_candidate_profile` (IJ)
- `get_candidate_wsi_scores` (IJ)
- `get_candidate_screening_results` (IJ)
- `get_candidate_salary_info` (IJ)
- `get_job_context` (IJ)
- `get_stage_sub_statuses` (IJ)
- `check_candidate_availability` (IJ)

**Action (6 — guardrail):**
- `update_candidate_field` (IJ, HITL)
- `personalize_communication` (IJ)
- `check_rejection_fairness` (IJ, MANDATORY)
- `get_interview_details` (IJ)
- `cancel_interview` (IJ, HITL)
- `reschedule_interview` (IJ, HITL)

**Decision (7):**
- `validate_transition` (IJ)
- `suggest_sub_status` (IJ)
- `extract_preferences` (G)
- `request_data_collection` (IJ)
- `get_recruiter_preferences` (G)
- `save_recruiter_preference` (G)
- `schedule_secondary_task` (IJ)

### 3.5 Recruiter Assistant — Kanban (split em 3)
Arquivos: `kanban_tool_registry.py` (superset 22), `kanban_action_tool_registry.py`, `kanban_insight_tool_registry.py`, `kanban_search_tool_registry.py`

**Search (6):**
- `view_candidate_full_profile` (IJ)
- `list_stage_candidates` (IJ)
- `get_pipeline_summary` (IJ)
- `get_stage_metrics` (IJ)
- `get_pipeline_benchmarks` (IJ)
- `get_pipeline_velocity` (IJ)

**Insight (8):**
- `analyze_stage` (IJ)
- `identify_bottlenecks` (IJ)
- `get_candidate_aging` (IJ)
- `compare_stages` (IJ)
- `suggest_movements` (IJ)
- `get_journey_metrics` (IJ)
- `get_at_risk_candidates` (IJ)
- `get_pipeline_prediction` (IJ)

**Action (8 — guardrail):**
- `batch_move_candidates` (IJ, HITL)
- `send_batch_communication` (IJ, HITL)
- `start_screening_batch` (IJ, HITL)
- `generate_pipeline_report` (IJ)
- `check_rejection_fairness` (IJ, MANDATORY)
- `find_silver_medalists` (TF)
- `get_recruiter_backlog` (G)
- `get_recruiter_benchmark` (G)

### 3.6 Recruiter Assistant — Talent (13)
- `search_candidates` · `list_candidates` · `view_candidate_profile` · `compare_candidates` · `rank_candidates` · `analyze_skills` · `recommend_actions` · `create_shortlist` · `export_report` · `check_search_fairness` · `get_talent_pool_benchmarks` · `check_pool_health` · `generate_report`

### 3.7 Recruiter Assistant — Jobs Management (14)
- `validate_job_action_fairness` · `get_recruitment_benchmarks` · `list_jobs` · `view_job_details` · `get_portfolio_metrics` · `compare_jobs` · `check_sla` · `analyze_bottlenecks` · `pause_job` · `reopen_job` · `close_job` · `update_priority` · `generate_report` · `get_pipeline_prediction`

### 3.8 Communication (8)
Arquivos: `communication/tools/communication_tools.py`, `communication/agents/communication_tool_registry.py`

- `send_email` (TF)
- `send_whatsapp` (TF)
- `schedule_interview` (IJ)
- `send_bulk_email` (TF)
- `send_feedback` (TF)
- `get_communication_history` (G)
- `schedule_message` (G)
- `check_rate_limit` (G)

### 3.9 Sourcing (parent + sub-agents)

**Main (18):**
- `set_search_criteria` · `suggest_skills` · `search_candidates` · `filter_results` · `view_candidate` · `analyze_profile` · `compare_candidates` · `score_candidate` · `add_to_shortlist` · `remove_from_shortlist` · `rank_candidates` · `send_outreach` (HITL) · `generate_message` · `track_response` · `generate_report` · `enrich_candidate_contact` (Apify) · `enrich_candidate_profile` (Apify) · `rag_search`

**Subsets por sub-agente:**
- Planner → `set_search_criteria`, `suggest_skills`
- Search → `search_candidates`, `filter_results`, `view_candidate`
- Enrich → `analyze_profile`, `compare_candidates`, `score_candidate`, `add_to_shortlist`, `remove_from_shortlist`, `rank_candidates`, `generate_report`
- Engagement → `send_outreach` (HITL), `generate_message`, `track_response`

**Diversity (3):**
- `diversity_search_candidates` · `diversity_get_pool_metrics` · `diversity_check_goals`

**GitHub (4):**
- `github_search_developers` · `github_get_profile` · `github_get_repos` · `github_get_contributions`

**StackOverflow (3):**
- `so_search_experts` · `so_get_user_tags` · `so_get_user_answers`

**Passive Pipeline (3):**
- `passive_search_archived` · `passive_calculate_fit_score` · `passive_check_lgpd_ttl`

**Referral (4):**
- `referral_identify_connectors` · `referral_prepare_request` · `referral_send_request` (HITL) · `referral_approve_request`

**Nurture Sequence (5):**
- `nurture_create_sequence` · `nurture_get_sequence_status` · `nurture_approve_step` · `nurture_execute_step` · `nurture_expire_sequence`

**Query helpers (`sourcing/tools/query_tools.py`, 9):**
- `search_candidates` · `get_candidate_details` · `get_candidate_stats` · `get_candidate_history` · `get_talent_quality` · `get_talent_engagement` · `get_talent_availability` · `get_diversity_metrics` · `get_market_benchmarks`

### 3.10 Autonomous (Tier 6 — cross-domain, 41 tools)
Arquivo: `autonomous/agents/autonomous_tool_registry.py`

- **Job:** `list_jobs`, `get_job_details`, `get_job_insights`, `predict_hiring_metrics`, `get_salary_benchmark`, `validate_job_requirements`, `get_company_config`
- **Sourcing:** `search_candidates`, `filter_candidates`, `analyze_candidate_profile`, `compare_candidates`, `score_candidate_for_job`, `match_candidates_to_job`, `suggest_skills`, `rank_candidates`, `add_to_shortlist`
- **Pipeline/Screening:** `get_pipeline_status`, `get_candidates_in_stage`, `view_candidate_profile`, `view_screening_results`, `view_interview_notes`, `run_wsi_screening`, `add_candidate_notes`
- **Analytics:** `generate_report`, `get_agent_performance`, `get_search_analytics`
- **Scheduling:** `get_scheduled_interviews`, `schedule_interview`
- **Communication:** `get_communication_history`
- **Cross-domain / meta:** `summarize_context`, `clarify_request`, `get_candidate_by_id`, `search_candidates_by_name`, `get_job_applications_summary`, `cross_domain_funnel_analysis`, `candidate_360_view`, `list_jobs_with_candidates`, `get_shortlists`, `get_job_history`, `get_tenant_hiring_overview`
- **Semantic:** `rag_search`

### 3.11 Analytics (25)

**Query registry (19 — `analytics/tools/analytics_query_tools/registry.py`):**
- Funnel: `get_pipeline_stats`, `get_vacancy_funnel`, `compare_candidates`
- Activity: `get_activity_summary`, `get_pending_actions`
- Recruiter: `get_recruiter_metrics`, `get_velocity_metrics`, `get_efficiency_metrics`, `get_comparative_metrics`
- Workload: `get_workload_distribution`
- Pipeline analytics: `get_bottleneck_analysis`, `get_stakeholder_metrics`
- Quality: `get_hiring_quality`, `get_prediction_metrics`
- Finance/Trends: `get_cost_metrics`, `get_trends`
- Intelligence: `get_ml_predictions`, `get_conversion_patterns`, `get_smart_alerts`

**Agent (6 — `analytics/agents/analytics_tool_registry.py`):**
- `get_job_insights` (JT)
- `predict_hiring_metrics` (JT)
- `generate_job_report` (JT)
- `generate_candidate_report` (TF)
- `get_search_analytics` (G)
- `get_agent_performance` (G)

### 3.12 Talent Intelligence (15)
Arquivo: `talent_intelligence/tools/registry.py`

**Skills Ontology (4):** `infer_related_skills` · `get_skill_adjacencies` · `analyze_skill_gaps` · `map_candidate_skills_to_ontology`

**Internal Mobility (1):** `match_internal_candidates`

**Workforce Planning (1):** `forecast_hiring_needs`

**Interview Intelligence (5):** `analyze_interview_recording` · `detect_interview_bias` · `generate_interview_opinion` · `generate_candidate_feedback` · `compare_interview_performance`

**Passive Nurture (3):** `create_nurture_sequence` · `get_engagement_metrics` · `suggest_reengagement`

**Market Intelligence (1):** `get_market_intelligence`

### 3.13 Hiring Policy (13)
Arquivo: `hiring_policy/agents/policy_tool_registry.py`

- `get_current_policy` · `save_policy_field` · `save_policy_block` · `get_policy_summary` · `validate_policy_compliance` · `get_company_context` · `get_industry_benchmarks` · `explain_policy_impact` · `get_setup_progress` · `get_platform_benchmarks` · `detect_policy_impact_anomalies` · `get_policy_effectiveness_report` · `apply_industry_defaults`

### 3.14 Company Settings (7)
- `get_company_profile` · `save_company_field` · `save_company_section` · `analyze_company_website` · `process_uploaded_document` · `import_workforce_plan` · `get_company_completion`

### 3.15 Automation (6)
- `decompose_task` · `prioritize_tasks` · `get_execution_plan` · `build_dag` · `check_dependencies` · `get_next_tasks`

### 3.16 ATS Integration (5)
- `sync_candidate_to_ats` · `fetch_candidate_from_ats` · `validate_ats_fields` · `bulk_sync_candidates` · `get_sync_status`

### 3.17 Shared — Insight/Predictive/Proactive/Export (16)

**Insight (4):** `get_pipeline_health` · `get_conversion_rates` · `get_time_to_fill` · `get_candidate_quality_distribution`

**Predictive (4):** `predict_dropout_risk` · `predict_time_to_fill` · `get_pipeline_forecast` · `get_strategic_recommendations`

**Proactive (4):** `check_stagnant_candidates` · `check_pending_offers` · `check_overdue_tasks` · `check_pipeline_risks`

**Export (4):** `export_candidates` · `generate_report` · `export_job_analytics` · `schedule_report`

### 3.18 Proactive Intelligence (YAML-only, 7)
- `get_proactive_alerts` · `get_autonomous_actions` · `confirm_autonomous_action` · `reject_autonomous_action` · `detect_pending_decisions` · `get_learning_insights` · `record_hiring_outcome`

### 3.19 Talent Pool (YAML-only, 5)
- `create_talent_pool` · `list_talent_pools` · `add_to_talent_pool` · `move_pool_to_job` · `get_pool_candidates`

### 3.20 Agent Studio (YAML-only, 4)
- `create_sourcing_agent` · `calibrate_sourcing_agent` · `get_agent_status` · `run_multi_strategy_search`

### 3.21 Digital Twins (YAML-only, 3)
- `create_digital_twin` · `evaluate_with_twin` · `list_digital_twins`

### 3.22 Recruitment Campaigns (YAML-only, 3)
- `create_recruitment_campaign` · `get_campaign_progress` · `advance_campaign_stage`

### 3.23 Job Flow Completion (YAML-only, 4)
- `create_offer_letter` · `confirm_placement` · `cancel_vacancy` · `pause_vacancy`

### 3.24 Marketplace (YAML-only, 3)
- `publish_to_job_board` (IJ) · `get_external_applications` (IJ) · `search_candidates_pearch` (TF, 800M+ perfis)

### 3.25 Platform (Tier 7 Studio whitelist, 15)
Arquivo: `agent_studio/custom_agent_runtime.py::PLATFORM_TOOLS_REGISTRY`

**Read (11):** `search_candidates` · `list_jobs` · `get_job_details` · `get_candidate_details` · `get_pipeline_summary` · `search_talent_pool` · `get_analytics_summary` · `get_company_culture` · `get_evaluation_criteria` · `summarize_context` · `clarify_request`

**Write (4):** `move_candidate` · `send_email` · `update_candidate_field` · `schedule_interview` · `create_note`

---

## 4. Tools com Guardrail / HITL Obrigatório

Disparam aprovação humana via `interrupt_before` no LangGraph:

| Tool | Registry | Gate |
|------|----------|------|
| `send_outreach` | sourcing_engagement | HITL |
| `update_candidate_field` | pipeline_action | HITL |
| `cancel_interview` | pipeline_action | HITL |
| `reschedule_interview` | pipeline_action | HITL |
| `batch_move_candidates` | kanban_action | HITL |
| `send_batch_communication` | kanban_action | HITL |
| `start_screening_batch` | kanban_action | HITL |
| `referral_send_request` | referral | HITL |
| `check_rejection_fairness` | pipeline_action + kanban_action | MANDATORY pre-rejection |

---

## 5. Como a LIA Monta o Pool de Tools Por Agente

Padrão 4 arquivos por domínio (`app/domains/<d>/agents/`):

```
agent.py              ← extends LangGraphReActBase
tool_registry.py      ← ToolDefinition(...) × N
system_prompt.py      ← instructions
stage_context.py      ← pipeline stage mapping
```

Fluxo de resolução no runtime:

```
1. agent._get_tools()
2.   → tool_registry.DOMAIN_TOOLS          ← lista Python
3.   → ToolPermissionsLoader.filter()      ← ACL YAML
4.   → allowed_agents whitelist check      ← metadata YAML
5.   → scope filter (contexto da UI)        ← UI mandou TF/JT/IJ?
6.   → _tenant_safe_wrapper                ← ContextVar company_id
7.   → tool_definition_to_langchain_tool   ← bridge para LangChain
8.   → TimedToolNode(tools=..., domain=..) ← Node do grafo
```

---

## 6. Como Replicar em Projeto LangChain/LangGraph

### 6.1 Estrutura mínima

```
shared/
  tools/
    types.py          ← ToolDefinition dataclass
    registry.py       ← ToolRegistry singleton
    permissions.py    ← ACL YAML loader
domains/
  <domain>/
    tools/<name>_tools.py    ← handlers
    agents/<agent>_tool_registry.py  ← monta subset
    agents/<agent>.py              ← consome via LangGraph
```

### 6.2 `types.py`

```python
from dataclasses import dataclass, field
from typing import Callable, Literal, Any

Scope = Literal["GLOBAL", "TALENT_FUNNEL", "JOB_TABLE", "IN_JOB"]

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict              # JSON Schema
    handler: Callable[..., Any]
    allowed_agents: list[str] = field(default_factory=list)
    scope: Scope = "GLOBAL"
    requires_hitl: bool = False
    requires_fairness_check: bool = False
```

### 6.3 `registry.py`

```python
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get_for_agent(self, agent: str, scope: Scope | None = None,
                      tenant_acl: set[str] | None = None) -> list[ToolDefinition]:
        out = []
        for t in self._tools.values():
            if agent not in t.allowed_agents: continue
            if scope is not None and t.scope != scope: continue
            if tenant_acl is not None and t.name not in tenant_acl: continue
            out.append(t)
        return out

    def to_langchain(self, agent: str, **kw) -> list:
        from langchain_core.tools import StructuredTool
        return [StructuredTool.from_function(
            name=t.name, description=t.description,
            func=t.handler,
        ) for t in self.get_for_agent(agent, **kw)]

tool_registry = ToolRegistry()
```

### 6.4 Registro por domínio

```python
# domains/sourcing/agents/sourcing_tool_registry.py
from shared.tools.registry import tool_registry
from shared.tools.types import ToolDefinition
from domains.sourcing.tools.search import search_candidates_handler
from domains.sourcing.tools.outreach import send_outreach_handler

tool_registry.register(ToolDefinition(
    name="search_candidates",
    description="Busca candidatos no talent pool e em Pearch.ai",
    parameters={"type": "object", "properties": {
        "query": {"type": "string"}, "limit": {"type": "integer"}}},
    handler=search_candidates_handler,
    allowed_agents=["sourcing_search", "sourcing", "autonomous"],
    scope="TALENT_FUNNEL",
))

tool_registry.register(ToolDefinition(
    name="send_outreach",
    description="Envia mensagem de outreach para candidato (requer aprovação)",
    parameters={"type": "object", "properties": {
        "candidate_id": {"type": "string"}, "message": {"type": "string"}}},
    handler=send_outreach_handler,
    allowed_agents=["sourcing_engagement"],
    scope="TALENT_FUNNEL",
    requires_hitl=True,
))
```

### 6.5 Consumo pelo agente LangGraph

```python
# domains/sourcing/agents/sourcing_search_agent.py
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from shared.tools.registry import tool_registry

class SourcingSearchAgent:
    name = "sourcing_search"

    def __init__(self, checkpointer, tenant_acl: set[str]):
        tools = tool_registry.to_langchain(
            agent=self.name,
            scope="TALENT_FUNNEL",
            tenant_acl=tenant_acl,
        )
        self.graph = create_react_agent(
            model=ChatAnthropic(model="claude-sonnet-4-6"),
            tools=tools,
            checkpointer=checkpointer,
        )
```

### 6.6 Sub-agentes que compartilham parent registry

Padrão LIA (Pipeline/Kanban/Sourcing têm 1 registry "parent" e N subsets). Implementação:

```python
# domains/sourcing/agents/sourcing_search_tool_registry.py
from .sourcing_tool_registry import tool_registry  # parent já registrou

SEARCH_AGENT_TOOLS = {"search_candidates", "filter_results", "view_candidate"}

def get_search_tools(tenant_acl: set[str] | None = None):
    return tool_registry.get_for_agent(
        agent="sourcing_search",
        tenant_acl=(tenant_acl & SEARCH_AGENT_TOOLS) if tenant_acl else SEARCH_AGENT_TOOLS,
    )
```

### 6.7 ACL YAML (opcional mas recomendado)

```yaml
# tool_permissions.yaml
global:
  scopes:
    talent_funnel:
      query:
        - search_candidates
        - get_candidate_details
      action:
        - add_to_shortlist

tenants:
  company_a:
    scopes:
      talent_funnel:
        action:
          - add_to_shortlist
          - send_outreach    # liberado só pra este tenant
```

Loader com `@lru_cache` para não recarregar YAML a cada request.

---

## 7. Referências

| Item | Caminho |
|------|---------|
| Metadata canônico | `lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| Validador YAML | `lia-agent-system/app/tools/tool_registry_loader.py` |
| ACL YAML | `lia-agent-system/app/tools/tool_permissions.yaml` |
| Loader ACL | `lia-agent-system/app/tools/tool_permissions_loader.py` |
| ToolRegistry Python | `lia-agent-system/app/tools/registry.py` |
| Bridge LangChain | `lia-agent-system/libs/agents-core/lia_agents_core/react_loop.py` |
| TimedToolNode | `lia-agent-system/libs/agents-core/lia_agents_core/langgraph_react_base.py` |
