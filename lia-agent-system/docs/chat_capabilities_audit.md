# Auditoria Profunda do Chat Unificado — Inventário Real de Capacidades

  **Data:** 19 de abril de 2026
  **Status:** Análise programática completa
  **Substitui (parcialmente):** `fase2c_domain_verification_report.md` (Fev/2026 — incompleto e desatualizado)
  **Auditor:** `scripts/audit_chat_capabilities.py` (introspecção do registry + cross-check ações ↔ tools ↔ handlers)
  **Output bruto:** `docs/chat_capabilities_audit.json`

  ---

  ## TL;DR — O que a LIA REALMENTE consegue executar hoje

  | Métrica | Valor |
  |---|---|
  | Domain dirs no filesystem | **61** |
  | Domain dirs registrados via `@register_domain` | **17** |
  | Total de `DomainAction` declaradas | **263** |
  | Total de tools registradas em `<domain>/tools/` | **93** |
  | Domínios com gaps detectados | **13/17** |
  | Mapeamentos `_ACTION_TOOL_MAP` quebrados | **6** |
  | Tools órfãs (sem action mapeada) | **93** |
  | Actions sem handler nem tool (não executáveis) | **146** |
  | Handlers com import quebrado (`ModuleNotFoundError` / função inexistente) | **81** |

  **Veredito:** o documento `fase2c` afirmava que "all domains properly implement execute_action()". Em termos *estruturais*, sim — todos têm `actions.py` e `execute_action`. **Mas a cadeia de execução real está rompida em ~76% dos domínios**: dos 17 registrados, apenas **4 estão íntegros** (`hiring_policy`, `pipeline_transition`, `recruitment_campaign`, `talent_pool`) — e esses só passam porque não declaram tools.

  ---

  ## 1. Fluxo do chat unificado (ground truth)

  ```
  Recrutador digita no chat
          ↓
  POST /api/v1/chat/message  (app/api/v1/chat.py:get_chat_adapter)
          ↓
  ChatAdapter → MainOrchestrator (app/orchestrator/main_orchestrator.py)
          ↓
  CascadedRouter (8 tiers: memory → LRU → Redis → vector → fast → LLM → autonomous → clarification)
          ↓
  RouteResult{ domain_id, intent, params }
          ↓
  resolve_domain(domain_id) via AGENT_TYPE_TO_DOMAIN
          ↓
  DomainRegistry().get_instance(domain_id).execute_action(action_id, params, context)
          ↓
     ┌─────────────────────────────────────────┐
     │ Dentro de execute_action:               │
     │  1. _ACTION_TOOL_MAP[action_id] → tool  │
     │  2. execute_<domain>_tool(tool_id, ...) │
     │  3. importlib.import_module(handler)    │
     │  4. handler(**params)                   │
     └─────────────────────────────────────────┘
          ↓
  DomainResponse → ChatAdapter → SSE/WebSocket → UI
  ```

  **Pontos de quebra observados (em ordem do fluxo):**
  1. **Tier 5 LLM router** retorna agent-types que não mapeiam para domínios reais (10 órfãos, ver §2).
  2. **`_ACTION_TOOL_MAP`** referencia tool-IDs inexistentes (sourcing tem 6 — ver task #579).
  3. **Handlers das tools** apontam para módulos/funções que não existem (81 handlers, ver §3).
  4. **Actions sem handler nem tool** ficam inalcançáveis ou caem em fallback genérico (146 actions).

  ---

  ## 2. Agent-types órfãos no `AGENT_TYPE_TO_DOMAIN`

  Mapeados em `app/orchestrator/domain_mappings.py`, mas o domain_id de destino **não está registrado no `DomainRegistry`**. Quando o LLM no Tier 5 retorna esses tipos, `get_instance()` devolve `None` e cai silenciosamente no `DEFAULT_DOMAIN = recruiter_assistant`.

  | Agent-type retornado pelo LLM | Domain alvo | Estado |
  |---|---|---|
  | `kanban_action` | `kanban_action` | ❌ não registrado |
| `kanban_insight` | `kanban_insight` | ❌ não registrado |
| `kanban_search` | `kanban_search` | ❌ não registrado |
| `pipeline_action` | `pipeline_action` | ❌ não registrado |
| `pipeline_context` | `pipeline_context` | ❌ não registrado |
| `pipeline_decision` | `pipeline_decision` | ❌ não registrado |
| `sourcing_engagement` | `sourcing_engagement` | ❌ não registrado |
| `sourcing_enrich` | `sourcing_enrich` | ❌ não registrado |
| `sourcing_planner` | `sourcing_planner` | ❌ não registrado |
| `sourcing_search` | `sourcing_search` | ❌ não registrado |

  **Impacto:** intents de Kanban, sub-domínios de Sourcing (planner/search/enrich/engagement) e sub-domínios de Pipeline (context/decision/action) **nunca são roteados corretamente**. Resposta vai cair no recruiter_assistant genérico ou em clarification.

  ---

  ## 3. Inventário por domínio registrado

  
### ⚠️ `agent_studio` — AgentStudioDomain

- Actions declaradas: **20** | Tools registradas: **0** | Mapeamentos: **0**

**Actions sem tool nem handler — não executáveis (3):** `recalibrate_agent`, `pause_agent`, `list_sector_templates`

### ⚠️ `analytics` — AnalyticsDomain

- Actions declaradas: **18** | Tools registradas: **10** | Mapeamentos: **0**

**Handlers com import quebrado (10):**

| tool | handler | erro |
|---|---|---|
| `analytics_generate_kpi` | `app.domains.analytics.services.report_service.generate_kpi_report` | function 'generate_kpi_report' not found in app.domains.analytics.services.report_service |
| `analytics_analyze_funnel` | `app.domains.analytics.services.report_service.analyze_funnel` | function 'analyze_funnel' not found in app.domains.analytics.services.report_service |
| `analytics_job_health` | `app.domains.analytics.services.report_service.job_health_check` | function 'job_health_check' not found in app.domains.analytics.services.report_service |
| `analytics_detect_anomalies` | `app.domains.analytics.services.report_service.detect_anomalies` | function 'detect_anomalies' not found in app.domains.analytics.services.report_service |
| `analytics_get_insights` | `app.domains.analytics.services.job_insights_service.get_job_insights` | function 'get_job_insights' not found in app.domains.analytics.services.job_insights_service |
| … | +5 outros | ver JSON |

**Tools órfãs — registradas mas sem action mapeada (10):** `analytics_generate_kpi`, `analytics_analyze_funnel`, `analytics_job_health`, `analytics_detect_anomalies`, `analytics_get_insights`, `analytics_generate_report`, `analytics_search_analytics`, `analytics_predict`, `analytics_dashboard`, `analytics_monitoring`

**Actions sem tool nem handler — não executáveis (18):** `generate_kpi_report`, `analyze_funnel`, `job_health_check`, `detect_anomalies`, `compare_periods`, `forecast`, `suggest_strategy`, `answer_data_question`, `get_job_insights`, `generate_job_report`, `generate_candidate_report`, `get_search_analytics`, `get_wizard_analytics`, `predict_hiring_probability`, `predict_time_to_fill` … +3

### ⚠️ `ats_integration` — ATSIntegrationDomain

- Actions declaradas: **18** | Tools registradas: **10** | Mapeamentos: **0**

**Handlers com import quebrado (10):**

| tool | handler | erro |
|---|---|---|
| `ats_sync_candidate` | `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.sync_candidate` | ModuleNotFoundError: No module named 'app.domains.ats_integration.services.ats_sync_service.ats_sync |
| `ats_sync_job` | `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.sync_job` | ModuleNotFoundError: No module named 'app.domains.ats_integration.services.ats_sync_service.ats_sync |
| `ats_pull_candidates` | `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.pull_candidates` | ModuleNotFoundError: No module named 'app.domains.ats_integration.services.ats_sync_service.ats_sync |
| `ats_pull_jobs` | `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.pull_jobs` | ModuleNotFoundError: No module named 'app.domains.ats_integration.services.ats_sync_service.ats_sync |
| `ats_check_status` | `app.domains.ats_integration.services.ats_sync_service.ats_sync_service.check_sync_status` | ModuleNotFoundError: No module named 'app.domains.ats_integration.services.ats_sync_service.ats_sync |
| … | +5 outros | ver JSON |

**Tools órfãs — registradas mas sem action mapeada (10):** `ats_sync_candidate`, `ats_sync_job`, `ats_pull_candidates`, `ats_pull_jobs`, `ats_check_status`, `ats_list_connections`, `ats_test_connection`, `ats_view_sync_log`, `ats_update_status`, `ats_send_score`

**Actions sem tool nem handler — não executáveis (18):** `sync_candidate`, `sync_job`, `bulk_sync`, `pull_candidates`, `pull_jobs`, `check_sync_status`, `configure_ats`, `list_connections`, `test_connection`, `map_fields`, `view_sync_log`, `resolve_conflict`, `update_status_ats`, `send_score_ats`, `sync_interview_result` … +3

### ⚠️ `automation` — AutomationDomain

- Actions declaradas: **20** | Tools registradas: **10** | Mapeamentos: **0**

**Handlers com import quebrado (10):**

| tool | handler | erro |
|---|---|---|
| `automation_create_task` | `app.domains.automation.services.task_service.TaskService.create_task` | ModuleNotFoundError: No module named 'app.domains.automation.services.task_service.TaskService'; 'ap |
| `automation_list_tasks` | `app.domains.automation.services.task_service.TaskService.list_tasks` | ModuleNotFoundError: No module named 'app.domains.automation.services.task_service.TaskService'; 'ap |
| `automation_complete_task` | `app.domains.automation.services.task_service.TaskService.complete_task` | ModuleNotFoundError: No module named 'app.domains.automation.services.task_service.TaskService'; 'ap |
| `automation_cancel_task` | `app.domains.automation.services.task_service.TaskService.cancel_task` | ModuleNotFoundError: No module named 'app.domains.automation.services.task_service.TaskService'; 'ap |
| `automation_create_rule` | `app.domains.automation.services.automation_service.AutomationService.create_automation` | ModuleNotFoundError: No module named 'app.domains.automation.services.automation_service.AutomationS |
| … | +5 outros | ver JSON |

**Tools órfãs — registradas mas sem action mapeada (10):** `automation_create_task`, `automation_list_tasks`, `automation_complete_task`, `automation_cancel_task`, `automation_create_rule`, `automation_list_rules`, `automation_enable_rule`, `automation_disable_rule`, `automation_trigger`, `automation_view_log`

**Actions sem tool nem handler — não executáveis (20):** `create_task`, `list_tasks`, `complete_task`, `cancel_task`, `decompose_task`, `plan_execution`, `get_next_tasks`, `create_automation`, `list_automations`, `enable_automation`, `disable_automation`, `trigger_automation`, `view_automation_log`, `configure_stage_automation`, `predict_substatus` … +5

### ⚠️ `candidate_self_service` — CandidateSelfServiceDomain

- Actions declaradas: **4** | Tools registradas: **0** | Mapeamentos: **0**

**Actions sem tool nem handler — não executáveis (4):** `get_status`, `get_interview_info`, `get_feedback`, `get_lgpd_info`

### ⚠️ `communication` — CommunicationDomain

- Actions declaradas: **20** | Tools registradas: **10** | Mapeamentos: **0**

**Handlers com import quebrado (10):**

| tool | handler | erro |
|---|---|---|
| `communication_send_email` | `app.domains.communication.services.email_service.email_service.send_email` | ModuleNotFoundError: No module named 'app.domains.communication.services.email_service.email_service |
| `communication_send_bulk` | `app.domains.communication.services.email_service.email_service.send_bulk_email` | ModuleNotFoundError: No module named 'app.domains.communication.services.email_service.email_service |
| `communication_send_whatsapp` | `app.domains.communication.services.whatsapp_service.send_whatsapp_message` | function 'send_whatsapp_message' not found in app.domains.communication.services.whatsapp_service |
| `communication_send_teams` | `app.domains.communication.services.teams_service.send_teams_message` | function 'send_teams_message' not found in app.domains.communication.services.teams_service |
| `communication_create_template` | `app.domains.communication.services.email_service.email_service.create_template` | ModuleNotFoundError: No module named 'app.domains.communication.services.email_service.email_service |
| … | +5 outros | ver JSON |

**Tools órfãs — registradas mas sem action mapeada (10):** `communication_send_email`, `communication_send_bulk`, `communication_send_whatsapp`, `communication_send_teams`, `communication_create_template`, `communication_list_templates`, `communication_preview_template`, `communication_get_history`, `communication_manage_webhook`, `communication_data_request`

**Actions sem tool nem handler — não executáveis (10):** `send_email`, `send_bulk_email`, `create_template`, `list_templates`, `preview_template`, `send_whatsapp`, `send_teams_message`, `get_communication_history`, `manage_webhook`, `handle_data_request`

### ⚠️ `company_settings` — CompanySettingsDomain

- Actions declaradas: **7** | Tools registradas: **0** | Mapeamentos: **0**

**Actions sem tool nem handler — não executáveis (7):** `configure_profile`, `configure_culture`, `configure_tech_stack`, `configure_benefits`, `configure_workforce`, `analyze_website`, `process_document`

### ⚠️ `cv_screening` — CVScreeningDomain

- Actions declaradas: **24** | Tools registradas: **11** | Mapeamentos: **0**

**Handlers com import quebrado (9):**

| tool | handler | erro |
|---|---|---|
| `parse_cv` | `app.domains.cv_screening.services.cv_parser.parse_cv` | function 'parse_cv' not found in app.domains.cv_screening.services.cv_parser |
| `score_cv` | `app.domains.cv_screening.services.cv_scoring_service.score_cv` | function 'score_cv' not found in app.domains.cv_screening.services.cv_scoring_service |
| `evaluate_rubric` | `app.domains.cv_screening.services.rubric_evaluation_service.evaluate_rubric` | function 'evaluate_rubric' not found in app.domains.cv_screening.services.rubric_evaluation_service |
| `calculate_wsi` | `app.domains.cv_screening.services.wsi_service.calculate_wsi` | function 'calculate_wsi' not found in app.domains.cv_screening.services.wsi_service |
| `adjust_wsi_questions` | `app.domains.cv_screening.services.wsi_question_adjuster.adjust_questions` | function 'adjust_questions' not found in app.domains.cv_screening.services.wsi_question_adjuster |
| … | +4 outros | ver JSON |

**Tools órfãs — registradas mas sem action mapeada (11):** `parse_cv`, `score_cv`, `evaluate_rubric`, `calculate_wsi`, `generate_wsi_questions`, `adjust_wsi_questions`, `normalize_scores`, `assess_seniority`, `send_candidate_feedback`, `pre_qualify_candidate`, `run_screening_pipeline`

**Actions sem tool nem handler — não executáveis (11):** `parse_cv`, `auto_screen`, `calculate_wsi_score`, `evaluate_rubric`, `generate_questions`, `adjust_questions`, `voice_screening`, `normalize_scores`, `assess_seniority`, `send_feedback`, `pre_qualify`

### ⚠️ `digital_twin` — DigitalTwinDomain

- Actions declaradas: **5** | Tools registradas: **0** | Mapeamentos: **0**

**Actions sem tool nem handler — não executáveis (5):** `create_twin`, `evaluate_with_twin`, `list_twins`, `index_twin_audio`, `deactivate_twin`

### ✅ `hiring_policy` — HiringPolicyDomain

- Actions declaradas: **8** | Tools registradas: **0** | Mapeamentos: **0**
- **Sem gaps detectados.** (Nota: domínio sem tools — execução 100% via handlers internos ou agent.)

### ⚠️ `interview_scheduling` — InterviewSchedulingDomain

- Actions declaradas: **20** | Tools registradas: **10** | Mapeamentos: **0**

**Handlers com import quebrado (10):**

| tool | handler | erro |
|---|---|---|
| `scheduling_schedule_interview` | `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.schedule_interview` | ModuleNotFoundError: No module named 'app.domains.interview_scheduling.services.scheduling_service.s |
| `scheduling_reschedule` | `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.reschedule_interview` | ModuleNotFoundError: No module named 'app.domains.interview_scheduling.services.scheduling_service.s |
| `scheduling_cancel` | `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.cancel_interview` | ModuleNotFoundError: No module named 'app.domains.interview_scheduling.services.scheduling_service.s |
| `scheduling_check_availability` | `app.domains.interview_scheduling.services.calendar_service.calendar_service.check_availability` | ModuleNotFoundError: No module named 'app.domains.interview_scheduling.services.calendar_service.cal |
| `scheduling_self_scheduling_link` | `app.domains.interview_scheduling.services.scheduling_service.scheduling_service.generate_self_scheduling_link` | ModuleNotFoundError: No module named 'app.domains.interview_scheduling.services.scheduling_service.s |
| … | +5 outros | ver JSON |

**Tools órfãs — registradas mas sem action mapeada (10):** `scheduling_schedule_interview`, `scheduling_reschedule`, `scheduling_cancel`, `scheduling_check_availability`, `scheduling_self_scheduling_link`, `scheduling_find_slots`, `scheduling_send_reminder`, `scheduling_list_today`, `scheduling_transcribe_audio`, `scheduling_analyze_voice`

**Actions sem tool nem handler — não executáveis (10):** `schedule_interview`, `reschedule_interview`, `cancel_interview`, `check_availability`, `generate_self_scheduling_link`, `find_common_slots`, `send_reminder`, `list_today_interviews`, `transcribe_audio`, `analyze_voice`

### ⚠️ `job_management` — JobManagementDomain

- Actions declaradas: **30** | Tools registradas: **12** | Mapeamentos: **0**

**Handlers com import quebrado (12):**

| tool | handler | erro |
|---|---|---|
| `create_job_vacancy` | `app.tools.job_tools.create_job_vacancy` | ModuleNotFoundError: No module named 'app.tools.job_tools' |
| `update_job_vacancy` | `app.tools.job_tools.update_job_vacancy` | ModuleNotFoundError: No module named 'app.tools.job_tools' |
| `close_job_vacancy` | `app.tools.job_tools.close_job_vacancy` | ModuleNotFoundError: No module named 'app.tools.job_tools' |
| `pause_job_vacancy` | `app.tools.job_tools.pause_job` | ModuleNotFoundError: No module named 'app.tools.job_tools' |
| `generate_job_description` | `app.domains.job_management.services.jd_generator_service.generate_job_description` | function 'generate_job_description' not found in app.domains.job_management.services.jd_generator_se |
| … | +7 outros | ver JSON |

**Tools órfãs — registradas mas sem action mapeada (12):** `create_job_vacancy`, `update_job_vacancy`, `close_job_vacancy`, `pause_job_vacancy`, `generate_job_description`, `enrich_job_description`, `import_job_description`, `search_job_templates`, `get_job_health`, `get_wizard_step`, `advance_wizard`, `get_job_analytics`

**Actions sem tool nem handler — não executáveis (30):** `create_job`, `guided_wizard`, `extract_requirements`, `generate_rubrics`, `update_job`, `health_check`, `suggest_strategy`, `duplicate_job`, `create_from_template`, `clone_job`, `close_job`, `pause_job`, `get_benefits`, `suggest_jd_improvements`, `detect_criteria` … +15

### ✅ `pipeline_transition` — PipelineTransitionDomain

- Actions declaradas: **5** | Tools registradas: **0** | Mapeamentos: **0**
- **Sem gaps detectados.** (Nota: domínio sem tools — execução 100% via handlers internos ou agent.)

### ⚠️ `recruiter_assistant` — RecruiterAssistantDomain

- Actions declaradas: **24** | Tools registradas: **10** | Mapeamentos: **0**

**Handlers com import quebrado (10):**

| tool | handler | erro |
|---|---|---|
| `assistant_pipeline_health` | `app.domains.recruiter_assistant.services.pipeline_service.pipeline_service.get_stale_candidates` | ModuleNotFoundError: No module named 'app.domains.recruiter_assistant.services.pipeline_service.pipe |
| `assistant_stale_candidates` | `app.domains.recruiter_assistant.services.pipeline_service.pipeline_service.get_stale_candidates` | ModuleNotFoundError: No module named 'app.domains.recruiter_assistant.services.pipeline_service.pipe |
| `assistant_move_candidate` | `app.domains.recruiter_assistant.services.pipeline_stage_service.pipeline_stage_service.transition_candidate` | ModuleNotFoundError: No module named 'app.domains.recruiter_assistant.services.pipeline_stage_servic |
| `assistant_search_context` | `app.domains.recruiter_assistant.services.memory_service.memory_service.search_similar_messages` | ModuleNotFoundError: No module named 'app.domains.recruiter_assistant.services.memory_service.memory |
| `assistant_save_memory` | `app.domains.recruiter_assistant.services.memory_service.memory_service.store_message` | ModuleNotFoundError: No module named 'app.domains.recruiter_assistant.services.memory_service.memory |
| … | +5 outros | ver JSON |

**Tools órfãs — registradas mas sem action mapeada (10):** `assistant_pipeline_health`, `assistant_stale_candidates`, `assistant_move_candidate`, `assistant_search_context`, `assistant_save_memory`, `assistant_recall_memory`, `assistant_conversation_summary`, `assistant_kanban_analysis`, `assistant_send_notification`, `assistant_track_goals`

**Actions sem tool nem handler — não executáveis (10):** `pipeline_health`, `stale_candidates`, `move_candidate`, `search_context`, `save_memory`, `recall_memory`, `conversation_summary`, `kanban_analysis`, `send_notification`, `track_goals`

### ✅ `recruitment_campaign` — RecruitmentCampaignDomain

- Actions declaradas: **4** | Tools registradas: **0** | Mapeamentos: **0**
- **Sem gaps detectados.** (Nota: domínio sem tools — execução 100% via handlers internos ou agent.)

### ⚠️ `sourcing` — SourcingDomain

- Actions declaradas: **30** | Tools registradas: **10** | Mapeamentos: **6**

**Mapeamentos quebrados (6):**

| action | tool referenciada (não existe) |
|---|---|
| `search_candidates` | `search_candidates` |
| `global_search` | `pearch_search` |
| `rank_candidates` | `candidate_match` |
| `filter_candidates` | `boolean_search` |
| `compare_candidates` | `search_candidates` |
| `assess_market` | `search_analytics` |

**Tools órfãs — registradas mas sem action mapeada (10):** `sourcing_update_candidate_stage`, `sourcing_reject_candidate`, `sourcing_shortlist_candidate`, `sourcing_add_candidate_to_vacancy`, `sourcing_search_candidates`, `sourcing_rank_candidates`, `sourcing_get_candidate_details`, `sourcing_get_candidate_stats`, `sourcing_get_candidate_history`, `sourcing_get_talent_quality`

### ✅ `talent_pool` — TalentPoolDomain

- Actions declaradas: **6** | Tools registradas: **0** | Mapeamentos: **0**
- **Sem gaps detectados.** (Nota: domínio sem tools — execução 100% via handlers internos ou agent.)


  ---

  ## 4. Categorias de gap por padrão de bug

  ### Padrão A — Handler path com módulo inexistente
  `job_management`: 12 tools apontam para `app.tools.job_tools.*` — esse pacote **não existe** (`app/tools/` tem apenas `executor.py`, `registry.py`, etc). A função real `create_job_vacancy` está em `app/api/v1/job_vacancies/crud.py:706`.

  ### Padrão B — Handler path navega através de instância em vez de módulo
  `communication`: 10 tools usam paths como `app.domains.communication.services.email_service.email_service.send_email`. O `importlib` separa em `(módulo, função)` no último ponto, tentando importar `...email_service.email_service` como módulo. Mas `email_service` (linha 732 de `email_service.py`) é um **singleton da classe** `EmailService`, não um submódulo.

  ### Padrão C — Função declarada mas não implementada no módulo correto
  `analytics`: 10 tools apontam para `app.domains.analytics.services.report_service.generate_kpi_report`. O módulo `report_service.py` existe, mas as funções referenciadas não estão lá.

  ### Padrão D — Action declarada sem nenhum executor
  146 actions distribuídas em 13 domínios não têm entrada em `_ACTION_TOOL_MAP` nem método `_handle_<action>` no `domain.py`. Ao serem invocadas, caem no `return DomainResponse.error_response("Nenhum handler configurado")` (sourcing:172) ou equivalente.

  ### Padrão E — Tool sem action de entrada
  93 tools registradas mas sem nenhuma `DomainAction` que aponte para elas via `_ACTION_TOOL_MAP`. Inalcançáveis pelo roteador de intents.

  ### Padrão F — `_ACTION_TOOL_MAP` aponta para tools com prefixo errado
  `sourcing`: 6 mapeamentos quebrados — já documentado e tem **task #579** aprovada.

  ---

  ## 5. Como verificar se uma capacidade funciona end-to-end

  Não existe atualmente um teste de smoke que cubra o caminho completo `chat → router → execute_action → tool → handler` para cada uma das 263 actions. O único caminho de validação hoje é:

  1. **Eval suite** em `lia-agent-system/eval/eval_runner.py` — cobre cenários, não inventário.
  2. **Pytest por domínio** — cobre alguns serviços, mas raramente o caminho de execute_action.
  3. **Frontend manual** — recrutador testa em `/chat` e vê o que retorna.

  **Gap:** falta um `pytest` parametrizado que, para cada `(domain, action)` em `DomainRegistry().get_all_actions()`:
  - Verifique que `_ACTION_TOOL_MAP` resolve (se mapeada);
  - Que o tool importa o handler sem `ModuleNotFoundError` / `AttributeError`;
  - Que o handler aceita o schema de params declarado;
  - Que `execute_action` retorna um `DomainResponse` válido (mesmo que com dados mock).

  ---

  ## 6. Plano de saneamento priorizado

  | Prioridade | Escopo | Ação | Task |
  |---|---|---|---|
  | **P0** | sourcing | Corrigir `_ACTION_TOOL_MAP` + tools órfãs + assinatura | **#579** (já proposta) |
  | **P0** | job_management | Criar `app/tools/job_tools.py` ou redirecionar 12 handlers para `api/v1/job_vacancies/crud.py` | **a propor** |
  | **P0** | communication | Corrigir 10 handlers — remover navegação através de instância singleton, usar funções módulo | **a propor** |
  | **P0** | analytics | Implementar 10 funções em `report_service.py` ou redirecionar handlers para módulos reais | **a propor** |
  | **P1** | ats_integration, automation, cv_screening, interview_scheduling, recruiter_assistant | Auditar 50 handlers do mesmo padrão B/C | **a propor** |
  | **P1** | domain_mappings | Remover ou registrar 10 agent-types órfãos (kanban_*, pipeline_*, sourcing_*) | **a propor** |
  | **P2** | todos os 17 domínios | Implementar smoke test parametrizado (§5) | **a propor** |
  | **P2** | docs | Aposentar `fase2c_domain_verification_report.md`; promover este doc + JSON como fonte da verdade | **incluído neste doc** |

  ---

  ## 7. Apêndice — Como reproduzir

  ```bash
  cd lia-agent-system
  python3 scripts/audit_chat_capabilities.py
  # → docs/chat_capabilities_audit.json (output bruto)
  # → este markdown é regenerável a partir do JSON
  ```

  O auditor é determinístico (sem rede, sem DB). Ideal para rodar em CI.
  