# Agent Specs — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `recruiter_agent_v5` (GitHub) + `lia-agent-system` (Replit)
> **SPEC-DRIVEN DEVELOPMENT** — um bloco por agente/domínio com contratos completos.

---

# PARTE I — recruiter_agent_v5

## 1. Pipeline Agents (Workflow Graph)

Estes agentes formam o pipeline sequencial do `WorkflowOrchestrator` em `src/workflow/graph.py`.

### 1.1 IntentAnalyzerAgent

**O que é:** Primeiro nó do pipeline — analisa a query do recrutador e extrai intent estruturado.

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/intent_analyzer.py` |
| **Como funciona** | Recebe query em português, consulta RAG para documentação de APIs, retorna intent com entities, action, filters |
| **Input** | `QueryState.question` (string em português) |
| **Output** | `QueryState.intent` com: entities, main_action, filters, aggregations, fields_needed, restricted_fields |
| **LLM** | Gemini (via settings) — temperature 0.0 |
| **Tools** | RAGService para consultar documentação de APIs |
| **Limites** | Não executa ações, apenas classifica. Pode retornar erro se query incompreensível |

**Contratos — Actions identificáveis:** `list`, `count`, `filter`, `aggregate`, `analyze`, `create_applies`, `multi_step`

### 1.2 APIPlannerAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/api_planner.py` |
| **Objetivo** | Criar plano de execução sequencial usando APIs disponíveis |
| **Input** | `QueryState.intent` + documentação RAG |
| **Output** | `QueryState.api_plan` — lista de `PlanStep` |
| **LLM** | Gemini — temperature 0.0 |
| **Limites** | Cada step: step, api, params, save_as, description. Máximo ~10 steps |

### 1.3 APIExecutorAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/api_executor.py` |
| **Objetivo** | Executar chamadas REST ao ATS API seguindo o plano |
| **Input** | `QueryState.api_plan` |
| **Output** | `QueryState.api_results` — dict com resultados por save_as |
| **LLM** | Não usa LLM |
| **Limites** | Respeita `requires_confirmation`, suporta `VariableSubstitutor` para interpolação entre steps |

### 1.4 PlanValidatorAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/plan_validator.py` |
| **Objetivo** | Validar resultados da execução — decidir se precisa replanejar |
| **Input** | `QueryState.api_results` |
| **Output** | Decision: continue, replan, ou abort |
| **LLM** | Gemini — temperature 0.0 |
| **Limites** | Máximo 1 re-planejamento (evitar loops infinitos) |

### 1.5 DataProcessorAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/data_processor.py` |
| **Objetivo** | Processar e formatar dados brutos das APIs |
| **Input** | `QueryState.api_results` |
| **Output** | `QueryState.processed_data` — dados formatados com summary |
| **LLM** | Não usa LLM (processamento determinístico) |

### 1.6 AnswerFormatterAgent

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/agents/answer_formatter.py` |
| **Objetivo** | Formatar resposta final usando taxonomia de 11 tipos |
| **Input** | `QueryState.processed_data` + `QueryState.question` |
| **Output** | `QueryState.final_answer` — string formatada em português |
| **LLM** | Gemini — temperature 0.0 |

---

## 2. Domain Agents (recruiter_agent_v5)

### 2.1 AppliesDomain

**O que é:** Domínio para gestão de candidaturas (applications) — busca, movimentação, comparação.

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/applies/domain.py` |
| **Domain ID** | `applies` |
| **Como funciona** | Recebe intent classificada, executa ação correspondente via AppliesCacheManager |
| **LLM** | `create_tracked_llm(temperature=0.0, service_name="AppliesDomain")` |
| **Cache** | `AppliesCacheManager` com tier |

**Contratos — Ações:** `search_applies`, `show_apply_details`, `pipeline_status`, `move_apply`, `compare_candidates`, `bulk_move`, `ranking`, `analytics`, `scoring`

**Limites:** move_apply e bulk_move requerem confirmação do usuário.

### 2.2 JobsDomain

**O que é:** Domínio para gestão completa de vagas — CRUD, analytics, sourcing automático.

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/jobs/domain.py` |
| **Domain ID** | `jobs` |
| **Como funciona** | Executa ações sobre vagas via ATS API. FairnessGuard valida filtros contra campos proibidos. |
| **Fairness** | `JobFairnessGuard` — bloqueia filtros discriminatórios (gender, age, race, religion, marital_status) |

**Contratos — Ações:** `search_jobs`, `show_job_details`, `create_job`, `update_job`, `pipeline_status`, `pipeline_health`, `job_analytics`, `summarize_job`, `alerts`, `account_stats`, `export_job`, `auto_source`, `send_reject_feedback`

**Limites:** create_job e update_job validados pelo FairnessGuard antes de execução.

### 2.3 InsightsDomain

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/insights/domain.py` |
| **Domain ID** | `insights` |

**Ações:** `daily_briefing`, `job_status_report`, `metrics_query`, `pipeline_bottleneck`, `candidate_comparison`, `weekly_summary`, `trend_analysis`, `performance`, `alerts`

### 2.4 MessagingDomain

| Campo | Valor |
|-------|-------|
| **Arquivo** | `src/domains/messaging/domain.py` |
| **Domain ID** | `messaging` |
| **Regra crítica** | NUNCA envia sem confirmação explícita — sempre preview primeiro |

**Ações:** `send_feedback_positive`, `send_feedback_negative`, `send_invite`, `send_followup`, `send_custom`, `check_history`, `bulk_send`

### 2.5 SourcingDomain

| Campo | Valor |
|-------|-------|
| **O que é** | Domínio de busca e atração de candidatos |
| **Arquivo** | `src/domains/sourcing/domain.py` |
| **Domain ID** | `sourcing` |
| **Como funciona** | Delega para ferramentas de busca via LangGraph workflow. Ferramentas de sourcing também disponíveis no AutonomousDomain via `tools/sourcing.py` |

**Contratos — Ações:** `search_candidates`, `source_from_external`, `engagement_outreach`, `pipeline_add`, `market_intelligence`

**Limites:** Sourcing externo depende de Pearch AI (serviço externo); sujeito a rate limits e disponibilidade.

### 2.6 AutonomousDomain

| Campo | Valor |
|-------|-------|
| **O que é** | Agente ReAct universal com acesso completo a todas as APIs |
| **Arquivo** | `src/domains/autonomous/domain.py` |
| **Domain ID** | `autonomous` |
| **Como funciona** | `UniversalReActAgent` — ~73 ferramentas cobrindo todos os domínios |
| **Prompt** | `AUTONOMOUS_SYSTEM_PROMPT` — 28KB |

**Contratos — Playbooks YAML:** `diagnostico_vaga`, `panorama_vagas`, `sourcing_completo`, `triagem_vaga`, `weekly_review`

**Limites:** Contexto longo (~28KB prompt + tools) pode causar compressão. Playbooks são macros compostas (múltiplos tool calls sequenciais).

### 2.7 EvaluationDomain

| Campo | Valor |
|-------|-------|
| **O que é** | Avaliação de candidatos em entrevistas com rubrica estruturada |
| **Arquivo** | `src/domains/evaluation/domain.py` |
| **Domain ID** | `evaluation` |
| **Como funciona** | LangGraph sub-graph: classify → evaluate → decide_flow → craft_message |
| **LLM** | `create_tracked_llm(temperature=0.2, service_name="EvaluationNode")` |
| **Segurança** | `safe_process_input()` — proteção contra prompt injection |

**Contratos — Rubrica:** relevância 30%, profundidade 30%, clareza 20%, exemplos 20%

**Limites:** Temperature 0.2 (única exceção ao 0.0 universal). Segurança contra prompt injection obrigatória.

---

# PARTE II — lia-agent-system

## 3. Agents ReAct — Contratos Completos

### 3.1 WizardReActAgent — Criação de Vagas

**O que é:** Agente conversacional para criação e edição de vagas em 6 etapas guiadas.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/job_management/agents/` |
| **Registry** | `wizard` |
| **Como funciona** | ReAct loop + stage context. Cada estágio filtra tools disponíveis e adapta o system prompt. |
| **Stages** | input-evaluation, jd-enrichment, salary, competencies, wsi-questions, review-publish |
| **Tools** | 9 |
| **Limites** | FairnessGuard obrigatório em requisitos/descrição. Drafts salvos permitem retomada. |

| Ferramenta | O que faz | Stage(s) |
|-----------|-----------|---------|
| `validate_job_requirements` | FairnessGuard (3 camadas) sobre requisitos, descrição ou perguntas | input-eval, competencies, review |
| `get_salary_benchmarks` | Histórico interno (SQL) + benchmarks externos (Robert Half, Gupy 2024) | salary |
| `search_salary_benchmark` | Pesquisa rápida por cargo/senioridade | salary |
| `validate_job_fields` | Score de completude, campos faltantes | input-eval, salary, review |
| `get_job_suggestions` | Sugestões de IA por campo (skills, benefícios, modelo de trabalho) | jd-enrichment, competencies |
| `save_job_draft` | Salva rascunho no banco | todas |
| `get_company_config` | Configurações da empresa: benefícios, políticas, templates | todas |
| `generate_enriched_jd` | Gera descrição completa enriquecida | jd-enrichment |
| `check_job_draft_health` | Avalia saúde do rascunho (0-100%, riscos) | input-eval, salary, review |

### 3.2 PipelineReActAgent — Triagem de Candidatos

**O que é:** Agente para análise de candidatos e ações no pipeline de recrutamento.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/cv_screening/agents/` |
| **Registry** | `pipeline` |
| **Como funciona** | ReAct loop com tools filtradas por estágio do pipeline. Acessa dados reais PostgreSQL. |
| **Stages** | triage, screening, shortlist, interview, offer, hired |
| **Tools** | 14 |
| **Limites** | Todas as movimentações são rastreadas com motivo. WSI scoring via serviço dedicado. |

| Ferramenta | O que faz | Stage(s) |
|-----------|-----------|---------|
| `view_candidate_profile` | Perfil completo com skills, scores — dados reais PostgreSQL | triage, shortlist |
| `analyze_cv` | Análise: fit score, skills, experiência, certificações | triage |
| `run_wsi_screening` | Resultado WSI (técnico, comportamental, overall, percentil) | screening |
| `schedule_interview` | Cria registro de entrevista | interview |
| `send_communication` | Envia mensagem + salva em communication_logs | interview, offer |
| `add_notes` | Nota timestampada ao candidato | todas |
| `move_candidate` | Move de etapa com motivo (rastreabilidade) | todas |
| `batch_move` | Move múltiplos candidatos | shortlist |
| `add_to_shortlist` | Marca como shortlisted | shortlist |
| `view_screening_results` | WSI score + LIA score | screening |
| `view_interview_notes` | Histórico de entrevistas | interview |
| `generate_offer` | Estrutura de proposta (salário, cargo, modelo) | offer |
| `finalize_hiring` | Marca como contratado | hired |
| `update_status` | Atualiza status: contratado, rejeitado, desistente | hired |

### 3.3 PipelineTransitionAgent — Transições de Etapa

**O que é:** Agente ReAct de invocação direta para validar e executar transições de estágio no pipeline.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/pipeline/agents/` |
| **Invocação** | `POST /api/v1/pipeline/interpret-context` (direta, não via registry) |
| **Como funciona** | Recebe contexto de transição, valida regras, executa com HITL pre-check |
| **Tools** | 17 |
| **Limites** | FairnessGuard sobre motivos de transição. HITL obrigatório para execute_stage_transition. |

| Ferramenta | O que faz |
|-----------|-----------|
| `get_candidate_profile` | Dados do candidato para contexto |
| `get_vacancy_details` | Detalhes da vaga alvo |
| `get_pipeline_stage_config` | Regras de cada etapa |
| `validate_stage_transition` | Valida se transição é permitida |
| `execute_stage_transition` | Executa a transição |
| `check_candidate_preferences` | Preferências de trabalho (modelo, localização, salário) |
| `update_candidate_preferences` | Atualiza preferências extraídas da conversa |
| `extract_candidate_preferences` | Extrai preferências de texto livre com NLP |
| `check_fairness` | FairnessGuard sobre motivo da transição |
| `log_recruiter_learning` | Registra aprendizado do recrutador |
| `get_company_policy` | Política de contratação da empresa |
| `generate_stage_checklist` | Checklist da etapa de destino |
| `calculate_lia_score` | Recalcula LIA score |
| `get_historical_transitions` | Histórico de transições |
| `notify_stakeholders` | Notifica interessados |
| `schedule_next_action` | Agenda próxima ação |
| `generate_transition_summary` | Resumo da transição |

### 3.4 SourcingReActAgent — Busca de Candidatos

**O que é:** Agente para busca iterativa de candidatos em fontes internas e externas (Pearch AI).

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/sourcing/agents/` |
| **Registry** | `sourcing` |
| **Como funciona** | ReAct loop com WorkingMemory + LongTermMemory. Combina busca interna (PostgreSQL) com Pearch AI (190M+ perfis). |
| **Tools** | 10 |
| **Limites** | Pearch AI sujeito a rate limits. FairnessGuard em critérios de busca. |

| Ferramenta | O que faz |
|-----------|-----------|
| `set_search_criteria` | Define parâmetros (cargo, skills, localização, experiência, salário) |
| `search_candidates` | Busca real no banco com filtros avançados |
| `search_external_candidates` | Fontes externas (Pearch AI — 190M+ perfis) |
| `analyze_search_results` | Analytics: distribuição, qualidade, alertas proativos |
| `save_search` | Salva critérios para reutilização |
| `add_to_pipeline` | Adiciona candidato a uma vaga |
| `send_outreach` | Mensagem de prospecção (email/WhatsApp) |
| `create_shortlist` | Cria lista selecionada |
| `check_sourcing_fairness` | FairnessGuard nos critérios |
| `get_market_intelligence` | Inteligência de mercado |

### 3.5 TalentReActAgent — Funil de Talentos

**O que é:** Assistente de recrutador para análise e gestão do banco de talentos.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/recruiter_assistant/agents/talent_*` |
| **Registry** | `talent` |
| **Como funciona** | ReAct loop com 3 stages progressivos: discovery → analysis → action_planning |
| **Stages** | discovery, analysis, action_planning |
| **Tools** | 12 |
| **Limites** | FairnessGuard em critérios de busca. create_shortlist requer HITL. |

| Ferramenta | O que faz |
|-----------|-----------|
| `search_candidates` | Busca por query + filtros ordenados por LIA score |
| `list_candidates` | Lista com filtro de status e vacancy_id |
| `view_candidate_profile` | Perfil completo (skills, languages, work_history) |
| `compare_candidates` | Comparação lado a lado |
| `rank_candidates` | Ranking por LIA score ou match |
| `analyze_skills` | Match técnico candidato×vaga (matched, missing, extra) |
| `recommend_actions` | Recomendações data-driven (avançar ≥4.2, entrevistar ≥3.5, revisar <3.0) |
| `create_shortlist` | Cria CandidateList + Members (requer confirmação) |
| `export_report` | Relatório com summary, avg score, lista completa |
| `check_search_fairness` | FairnessGuard (3 camadas) |
| `get_talent_pool_benchmarks` | Benchmarks: tamanho, score, distribuição |
| `check_pool_health` | Saúde do pool: riscos com severidade |

### 3.6 JobsMgmtReActAgent — Portfólio de Vagas

**O que é:** Agente para gestão do portfólio de vagas do recrutador — métricas, SLA, ações em massa.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/recruiter_assistant/agents/jobs_mgmt_*` |
| **Registry** | `jobs_management` |
| **Como funciona** | ReAct loop com 3 stages: overview → analysis → action |
| **Stages** | overview, analysis, action |
| **Tools** | 14 |
| **Limites** | pause_job e close_job requerem HITL. FairnessGuard sobre justificativas. |

| Ferramenta | O que faz |
|-----------|-----------|
| `list_jobs` | Vagas com contagem, dias em aberto, prioridade |
| `view_job_details` | Detalhes + candidatos por status |
| `get_portfolio_metrics` | Total ativas/pausadas/fechadas, avg TTF, fill rate |
| `compare_jobs` | Comparação: dias, candidatos, score, rejeitados |
| `check_sla` | Compliance: vencidas, em risco (≤7d/≤14d), conformes |
| `analyze_bottlenecks` | Gargalos: estagnados >14d, abertas >60d |
| `pause_job` | Pausa vaga (requer motivo) |
| `reopen_job` | Reabre vaga pausada/fechada |
| `close_job` | Fecha definitivamente (requer motivo) |
| `update_priority` | Prioridade alta/média/baixa |
| `generate_report` | Relatório portfolio: TTF, fill rate, totais |
| `get_recruitment_benchmarks` | TTF real vs. mercado (above/at/below) |
| `validate_job_action_fairness` | FairnessGuard sobre justificativas |
| `get_pipeline_prediction` | Probabilidade de fechamento por vaga |

### 3.7 KanbanReActAgent — Pipeline Kanban

**O que é:** Agente para operações no quadro Kanban de candidatos — maior número de tools (21).

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/recruiter_assistant/agents/kanban_*` |
| **Registry** | `kanban` |
| **Como funciona** | ReAct loop com 3 stages: pipeline_overview → stage_analysis → pipeline_actions |
| **Stages** | pipeline_overview, stage_analysis, pipeline_actions |
| **Tools** | 21 |
| **Limites** | batch_move, send_batch_communication, start_screening_batch requerem HITL. |

| Ferramenta | O que faz |
|-----------|-----------|
| `get_pipeline_summary` | Contagem por etapa, conversão, total |
| `get_stage_metrics` | Candidatos, tempo médio, LIA score, risco |
| `list_stage_candidates` | Candidatos de etapa com days_in_stage |
| `analyze_stage` | Saúde (healthy/attention/critical), riscos |
| `identify_bottlenecks` | Etapas com avg >14d ou >30% estagnados |
| `get_candidate_aging` | Parados além de N dias |
| `compare_stages` | Métricas entre etapas |
| `suggest_movements` | Avançar ≥4.2, follow-up >14d, desqualificar <3.0 |
| `batch_move_candidates` | Move em lote (requer confirmação) |
| `send_batch_communication` | Massa por email/WhatsApp/SMS (requer confirmação) |
| `start_screening_batch` | WSI em lote (requer confirmação) |
| `generate_pipeline_report` | Relatório consolidado |
| `get_pipeline_benchmarks` | Tempo real vs. média empresa |
| `check_rejection_fairness` | FairnessGuard sobre rejeições |
| `get_pipeline_velocity` | Velocidade real + gargalos vs. benchmark |
| `find_silver_medalists` | Candidatos prata de processos anteriores |
| `get_at_risk_candidates` | EWS score elevado — risco de ghosting |
| `get_journey_metrics` | Health score (0–100) + padrões preditivos |
| `get_recruiter_backlog` | Candidatos aguardando ação |
| `get_recruiter_benchmark` | Performance vs. mediana anônima |
| `get_pipeline_prediction` | Probabilidade de fechamento (0–100%) |

### 3.8 PolicyReActAgent — Políticas de Contratação

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/hiring_policy/agents/` |
| **Registry** | `policy` |
| **Tools** | 12 |

| Ferramenta | O que faz |
|-----------|-----------|
| `get_current_policy` | Política atual (pipeline, scheduling, communication, screening, automation rules, learned_patterns, autonomy_level) |
| `update_pipeline_rules` | Regras de progressão de etapas |
| `update_scheduling_rules` | Regras de agendamento (horários, buffers) |
| `update_communication_rules` | Templates e regras de comunicação |
| `update_screening_rules` | WSI, triagem, qualificação |
| `update_automation_rules` | Automações e thresholds |
| `validate_policy` | Validação legal + FairnessGuard |
| `get_policy_analytics` | Eficácia das políticas |
| `get_industry_benchmarks` | Benchmarks setoriais (ABRH, GPTW, LinkedIn, Robert Half) |
| `setup_pipeline_templates` | Templates de pipeline |
| `get_setup_status` | Setup progress por seção |
| `validate_policy_fairness` | FairnessGuard sobre políticas |

### 3.9 AutomationReActAgent

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/automation/agents/` |
| **Registry** | `automation` |
| **Tools** | 7 |

| Ferramenta | O que faz |
|-----------|-----------|
| `list_automations` | Lista configuradas com status e histórico |
| `create_automation` | Nova automação: trigger + ações encadeadas |
| `update_automation` | Edita existente |
| `toggle_automation` | Habilita/desabilita |
| `test_automation` | Executa em modo teste (sem efeitos reais) |
| `view_execution_log` | Histórico de execuções |
| `get_automation_metrics` | Volume, taxa de sucesso, economia de tempo |

### 3.10 PolicySetupAgent (LLM Direto)

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/policy/agents/agent.py` |
| **Tipo** | LLM direto (não ReAct) |
| **Função** | 19 perguntas em 5 blocos de configuração de política |
| **Blocos** | pipeline_rules, scheduling_rules, communication_rules, screening_rules, automation_rules |

### 3.11 AnalyticsReActAgent

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/analytics/agents/` |
| **Registry** | `analytics` |
| **Função** | Métricas, relatórios, insights de recrutamento |

### 3.12 ATSIntegrationReActAgent

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/ats_integration/agents/` |
| **Registry** | `ats_integration` |
| **Função** | Sincronização bidirecional com Gupy/Pandapé/Merge |

### 3.13 CommunicationReActAgent

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/communication/agents/` |
| **Registry** | `communication` |
| **Função** | Comunicações multi-canal (email, WhatsApp, Teams) |

---

## 4. Tool Registries — Sumário

| Registry | Agente | Tools | Dados acessados |
|----------|--------|:-----:|-----------------|
| `wizard_tool_registry.py` | WizardReAct | 9 | Vagas, benchmarks, FairnessGuard |
| `pipeline_tool_registry.py` (cv_screening) | PipelineReAct | 14 | Triagem, scoring, WSI |
| `pipeline_tool_registry.py` (pipeline) | PipelineTransition | 17 | Transições de estágio |
| `sourcing_tool_registry.py` | SourcingReAct | 10 | Candidatos, Pearch AI |
| `talent_tool_registry.py` | TalentReAct | 12 | Banco de talentos |
| `jobs_mgmt_tool_registry.py` | JobsMgmtReAct | 14 | Vagas, métricas |
| `kanban_tool_registry.py` | KanbanReAct | 21 | Pipeline, movimentação |
| `policy_tool_registry.py` | PolicyReAct | 12 | Políticas, compliance |
| `automation_tool_registry.py` | AutomationReAct | 7 | Automações |
| `analytics_tool_registry.py` | AnalyticsReAct | — | Métricas, dashboards |
| `ats_integration_tool_registry.py` | ATSIntegrationReAct | — | Gupy, Pandapé, Merge |
| `communication_tool_registry.py` | CommunicationReAct | — | Email, WhatsApp, Teams |

**Catálogo central:** `app/tools/tool_registry_metadata.yaml` — 32 tools com `allowed_agents` e `scope`.

---

## 5. Guardrails por Agente

| Agente | Tool de confirmação (requer HITL) |
|--------|----------------------------------|
| Talent | `create_shortlist` |
| Kanban | `batch_move_candidates`, `send_batch_communication`, `start_screening_batch` |
| JobsMgmt | `pause_job`, `close_job` |
| PipelineTransition | `execute_stage_transition` |
| Messaging (r_a_v5) | Todos os envios |

---

## 6. Background & Automações

### 6.1 ProactiveAgentWorker

Ciclo: 30 min | Arquivo: `app/shared/agents/proactive_worker.py`

| Check | Trigger | Severidade |
|-------|---------|-----------|
| `check_stale_pipeline` | Candidato parado ≥7d | warning; ≥14d critical |
| `check_low_pipeline` | Vaga <3 candidatos | warning; zero critical |
| `check_high_scorers` | Score >80% em "Novo" | warning |
| `check_deadlines` | Prazo ≤7d | warning; ≤2d critical |
| `check_engagement_gaps` | Sem contato ≥10d | info |
| `check_velocity_bottleneck` | Acima do threshold por etapa | warning/critical |
| `check_silver_medalists` | Candidatos prata disponíveis | info |
| `check_recruiter_backlog` | Aguardando ação (por recrutador) | warning/critical |
| `check_early_warning` | EWS ≥0.6 (por recrutador) | warning/critical |
| `check_journey_intelligence` | Health <50 (por recrutador) | warning/critical |
| `check_pipeline_prediction` | Prob <30% (por recrutador) | warning/critical |

### 6.2 Workers (recruiter_agent_v5)

| Worker | Queue | Função |
|--------|-------|--------|
| `celery_worker.py` | default | Queries de domínio via RabbitMQ |
| `evaluation_worker.py` | evaluation | Avaliações de candidatos |

### 6.3 Celery Tasks (lia-agent-system)

| Task | Schedule |
|------|---------|
| `drift.run_batch` | Diário 06h Brasília |
| `agents.wsi_interview.start` | On-demand |
| `agents.triagem.run` | On-demand |
| `agents.sourcing.search` | On-demand |
| `communication.email.send_bulk` | On-demand |

---

## Referências

| Componente | Arquivo |
|-----------|---------|
| Domain Registry (r_a_v5) | `recruiter_agent_v5/src/domains/registry.py` |
| Base Domain (r_a_v5) | `recruiter_agent_v5/src/domains/base.py` |
| ReactAgentRegistry (lia) | `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py` |
| Tool Registry Metadata | `lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| Proactive Worker | `lia-agent-system/app/shared/agents/proactive_worker.py` |
| MAPA_INTELIGENCIA | `docs/analises/MAPA_INTELIGENCIA_LIA_COMPLETO.md` |
| GUIA_ARQUITETURA_IA | `docs/GUIA_ARQUITETURA_IA_v1.0.md` |
