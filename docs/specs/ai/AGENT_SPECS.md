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

**Nota:** Não existe domínio "questions" separado. As perguntas WSI são gerenciadas pelo estágio `wsi-questions` do WizardReActAgent (seção 3.1) e pelo serviço `cv_screening/services/wsi_question_generator.py`. Os 12 domínios do lia-agent-system são: job_management, cv_screening, pipeline, sourcing, recruiter_assistant (talent + jobs_mgmt + kanban), hiring_policy, policy, automation, analytics, ats_integration, communication, interview_scheduling.

## 3. Agents ReAct — Contratos Completos

### 3.1 WizardReActAgent — Criação de Vagas

**O que é:** Agente conversacional para criação e edição de vagas em 6 etapas guiadas.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/job_management/agents/` |
| **Registry** | `wizard` |
| **Registry file** | `wizard_tool_registry.py` |
| **Como funciona** | ReAct loop + stage context. Cada estágio filtra tools disponíveis e adapta o system prompt. |
| **Stages** | input-evaluation, jd-enrichment, salary, competencies, wsi-questions, review-publish |
| **Tools** | 10 |
| **max_iterations** | 5 |
| **Limites** | FairnessGuard obrigatório em requisitos/descrição. Drafts salvos permitem retomada. |

| Ferramenta | O que faz |
|-----------|-----------|
| `validate_job_requirements` | FairnessGuard (3 camadas) sobre requisitos, descrição ou perguntas |
| `get_salary_benchmarks` | Histórico interno (SQL) + benchmarks externos (Robert Half, Gupy 2024) |
| `search_salary_benchmark` | Pesquisa rápida por cargo/senioridade |
| `validate_job_fields` | Score de completude, campos faltantes |
| `get_job_suggestions` | Sugestões de IA por campo (skills, benefícios, modelo de trabalho) |
| `save_job_draft` | Salva rascunho no banco |
| `get_company_config` | Configurações da empresa: benefícios, políticas, templates |
| `generate_enriched_jd` | Gera descrição completa enriquecida |
| `check_job_draft_health` | Avalia saúde do rascunho (0-100%, riscos) |
| `generate_report` | Gera relatório de vagas criadas e publicadas no período |

### 3.2 PipelineReActAgent — Triagem de Candidatos

**O que é:** Agente para análise de candidatos e ações no pipeline de recrutamento.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/cv_screening/agents/` |
| **Registry** | `pipeline` |
| **Registry file** | `cv_screening/agents/pipeline_tool_registry.py` |
| **Como funciona** | ReAct loop com tools filtradas por estágio do pipeline. Acessa dados reais PostgreSQL. |
| **Stages** | triage, screening, shortlist, interview, offer, hired |
| **Tools** | 15 |
| **max_iterations** | 5 |
| **Limites** | Todas as movimentações são rastreadas com motivo. WSI scoring via serviço dedicado. |

| Ferramenta | O que faz |
|-----------|-----------|
| `view_candidate_profile` | Perfil completo com skills, scores — dados reais PostgreSQL |
| `move_candidate` | Move de etapa com motivo (rastreabilidade) |
| `analyze_cv` | Análise: fit score, skills, experiência, certificações |
| `run_wsi_screening` | Resultado WSI (técnico, comportamental, overall, percentil) |
| `schedule_interview` | Cria registro de entrevista |
| `send_communication` | Envia mensagem + salva em communication_logs |
| `add_notes` | Nota timestampada ao candidato |
| `batch_move` | Move múltiplos candidatos |
| `add_to_shortlist` | Marca como shortlisted |
| `view_screening_results` | WSI score + LIA score |
| `view_interview_notes` | Histórico de entrevistas |
| `generate_offer` | Estrutura de proposta (salário, cargo, modelo) |
| `finalize_hiring` | Marca como contratado |
| `update_status` | Atualiza status: contratado, rejeitado, desistente |
| `generate_report` | Relatório de métricas do pipeline de seleção |

### 3.3 PipelineTransitionAgent — Transições de Etapa

**O que é:** Agente LangGraph ReAct (não registrado no ReactAgentRegistry) para interpretar contexto de transição de estágio.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/pipeline/agents/` |
| **Classe** | `PipelineTransitionAgent(LangGraphReActBase, EnhancedAgentMixin)` |
| **Registry file** | `pipeline/agents/pipeline_tool_registry.py` |
| **Invocação** | `POST /api/v1/pipeline/interpret-context` (direta, não via registry) |
| **Como funciona** | Recebe contexto de transição (from_stage, to_stage, candidate, job), usa ALL_TOOLS do registry |
| **Tools** | 20 |
| **Limites** | FairnessGuard sobre motivos de rejeição. Preferências do recrutador aprendidas automaticamente. |

| Ferramenta | O que faz |
|-----------|-----------|
| `get_candidate_profile` | Perfil completo do candidato (nome, email, telefone, skills, scores) |
| `get_candidate_wsi_scores` | Scores WSI: geral, por competência e percentil |
| `get_candidate_screening_results` | Resultados de triagem: respostas, análise IA |
| `get_candidate_salary_info` | Pretensão salarial CLT/PJ do candidato |
| `update_candidate_field` | Atualiza campo cadastral (telefone, email, LinkedIn) |
| `request_data_collection` | Agenda tarefa para coletar dado específico do candidato |
| `get_stage_sub_statuses` | Lista sub-statuses disponíveis para a etapa de destino |
| `suggest_sub_status` | Sugere sub-status baseado no tipo de ação e contexto |
| `extract_preferences` | Extrai preferências estruturadas do texto do recrutador |
| `validate_transition` | Valida se a transição é permitida pelas regras do pipeline |
| `get_job_context` | Dados da vaga: título, departamento, modelo de trabalho |
| `schedule_secondary_task` | Agenda tarefa secundária combinada com a ação principal |
| `personalize_communication` | Define personalização da comunicação (tom, idioma, canal) |
| `check_rejection_fairness` | FairnessGuard sobre motivo de rejeição |
| `check_candidate_availability` | Disponibilidade baseada em histórico de interações |
| `get_recruiter_preferences` | Preferências aprendidas do recrutador (padrões de agendamento) |
| `save_recruiter_preference` | Salva/atualiza preferência aprendida do recrutador |
| `get_interview_details` | Detalhes da entrevista agendada (data, hora, tipo) |
| `cancel_interview` | Cancela entrevista agendada |
| `reschedule_interview` | Reagenda entrevista para nova data/hora |

### 3.4 SourcingReActAgent — Busca de Candidatos

**O que é:** Agente para busca iterativa de candidatos em fontes internas e externas.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/sourcing/agents/` |
| **Registry** | `sourcing` |
| **Registry file** | `sourcing_tool_registry.py` |
| **Como funciona** | ReAct loop com WorkingMemory + LongTermMemory. Combina busca interna (PostgreSQL) com fontes externas. |
| **Tools** | 15 |
| **max_iterations** | 5 |
| **Limites** | Fontes externas sujeitas a rate limits. FairnessGuard em critérios de busca. |

| Ferramenta | O que faz |
|-----------|-----------|
| `set_search_criteria` | Define parâmetros (cargo, skills, localização, experiência, salário) |
| `suggest_skills` | Sugere skills relacionadas ao cargo |
| `search_candidates` | Busca real no banco com filtros avançados |
| `filter_results` | Filtra resultados de busca por critérios adicionais |
| `view_candidate` | Perfil completo do candidato |
| `analyze_profile` | Análise detalhada de perfil (fit, gaps, pontos fortes) |
| `compare_candidates` | Comparação lado a lado entre candidatos |
| `score_candidate` | Score de match candidato×vaga |
| `add_to_shortlist` | Adiciona à lista de pré-seleção |
| `remove_from_shortlist` | Remove da lista de pré-seleção |
| `rank_candidates` | Ranking por score/critérios |
| `send_outreach` | Mensagem de prospecção (email/WhatsApp) |
| `generate_message` | Gera mensagem personalizada para candidato |
| `track_response` | Rastreia resposta do candidato |
| `generate_report` | Relatório de sourcing com métricas |

### 3.5 TalentReActAgent — Funil de Talentos

**O que é:** Assistente de recrutador para análise e gestão do banco de talentos.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/recruiter_assistant/agents/talent_*` |
| **Registry** | `talent` |
| **Registry file** | `talent_tool_registry.py` |
| **Como funciona** | ReAct loop com 3 stages progressivos: discovery → analysis → action_planning |
| **Stages** | discovery, analysis, action_planning |
| **Tools** | 13 |
| **max_iterations** | 5 |
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
| `generate_report` | Gera relatório completo do banco de talentos |

### 3.6 JobsMgmtReActAgent — Portfólio de Vagas

**O que é:** Agente para gestão do portfólio de vagas do recrutador — métricas, SLA, ações em massa.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/recruiter_assistant/agents/jobs_mgmt_*` |
| **Registry** | `jobs_management` |
| **Registry file** | `jobs_mgmt_tool_registry.py` |
| **Como funciona** | ReAct loop com 3 stages: overview → analysis → action |
| **Stages** | overview, analysis, action |
| **Tools** | 14 |
| **max_iterations** | 5 |
| **Limites** | pause_job e close_job requerem HITL. FairnessGuard sobre justificativas. |

| Ferramenta | O que faz |
|-----------|-----------|
| `validate_job_action_fairness` | FairnessGuard sobre justificativas |
| `get_recruitment_benchmarks` | TTF real vs. mercado (above/at/below) |
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
| `get_pipeline_prediction` | Probabilidade de fechamento por vaga |

### 3.7 KanbanReActAgent — Pipeline Kanban

**O que é:** Agente para operações no quadro Kanban de candidatos — maior número de tools (22).

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/recruiter_assistant/agents/kanban_*` |
| **Registry** | `kanban` |
| **Registry file** | `kanban_tool_registry.py` |
| **Como funciona** | ReAct loop com 3 stages: pipeline_overview → stage_analysis → pipeline_actions |
| **Stages** | pipeline_overview, stage_analysis, pipeline_actions |
| **Tools** | 22 |
| **max_iterations** | 5 |
| **Limites** | batch_move, send_batch_communication, start_screening_batch requerem HITL. |

| Ferramenta | O que faz |
|-----------|-----------|
| `view_candidate_full_profile` | Perfil completo do candidato no contexto do kanban |
| `get_pipeline_benchmarks` | Tempo real vs. média empresa |
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
| `check_rejection_fairness` | FairnessGuard sobre rejeições |
| `find_silver_medalists` | Candidatos prata de processos anteriores |
| `get_recruiter_backlog` | Candidatos aguardando ação |
| `get_recruiter_benchmark` | Performance vs. mediana anônima |
| `get_journey_metrics` | Health score (0–100) + padrões preditivos |
| `get_at_risk_candidates` | EWS score elevado — risco de ghosting |
| `get_pipeline_prediction` | Probabilidade de fechamento (0–100%) |
| `get_pipeline_velocity` | Velocidade real + gargalos vs. benchmark |

### 3.8 PolicyReActAgent — Políticas de Contratação

**O que é:** Agente para configuração de políticas de contratação da empresa — pipeline, agendamento, comunicação, screening, automação.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/hiring_policy/agents/` |
| **Registry** | `policy` |
| **Registry file** | `policy_tool_registry.py` |
| **Como funciona** | ReAct loop com setup wizard por blocos. Cada bloco (pipeline_rules, scheduling_rules, etc.) é salvo independentemente. |
| **Tools** | 13 |
| **max_iterations** | 5 |
| **Limites** | Validação legal/ética obrigatória via `validate_policy_compliance` antes de salvar. |

| Ferramenta | O que faz |
|-----------|-----------|
| `get_current_policy` | Carrega todas as políticas de contratação atuais da empresa |
| `save_policy_field` | Salva um campo específico de política no banco |
| `get_policy_summary` | Resumo formatado de todas as políticas configuradas |
| `validate_policy_compliance` | Verifica se política proposta viola critérios éticos ou legais |
| `get_company_context` | Dados reais da empresa (volume de vagas, candidatos, TTF) |
| `get_industry_benchmarks` | Benchmarks setoriais (ABRH, GPTW, LinkedIn, Robert Half) |
| `explain_policy_impact` | Explica impacto de configuração nos agentes downstream |
| `get_setup_progress` | Progresso da configuração: quais blocos completos |
| `get_platform_benchmarks` | Benchmarks REAIS calculados dos dados da própria plataforma |
| `detect_policy_impact_anomalies` | Detecta anomalias causadas pelas políticas atuais |
| `get_policy_effectiveness_report` | Relatório de efetividade das políticas |
| `save_policy_block` | Salva bloco inteiro de política de uma vez |
| `apply_industry_defaults` | Aplica configurações padrão do setor em todos os blocos |

### 3.9 AutomationReActAgent — Decomposição de Tarefas

**O que é:** Agente para decomposição de tarefas complexas de recrutamento em subtarefas executáveis com DAG de dependências.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/automation/agents/` |
| **Registry** | `automation` |
| **Registry file** | `automation_tool_registry.py` |
| **Como funciona** | Recebe tarefa em linguagem natural, decompõe em subtarefas com agente responsável, estima duração, identifica dependências e oportunidades de paralelismo |
| **Tools** | 6 |
| **max_iterations** | 6 |
| **Limites** | Agentes atribuíveis: job_planner, sourcing, cv_screening, interviewer, wsi_evaluator, scheduling, analyst_feedback |

| Ferramenta | O que faz |
|-----------|-----------|
| `decompose_task` | Decompõe tarefa principal em subtarefas executáveis com duração e agente |
| `prioritize_tasks` | Prioriza tarefas por urgência, impacto, criticidade e eficiência |
| `get_execution_plan` | Gera plano de execução ordenado com paralelismo |
| `build_dag` | Constrói DAG de dependências entre subtarefas |
| `check_dependencies` | Verifica se dependências de uma tarefa estão satisfeitas |
| `get_next_tasks` | Retorna próximas tarefas desbloqueadas para execução |

### 3.10 PolicySetupAgent (LLM Direto)

**O que é:** Agente de configuração inicial de políticas — guia o recrutador por 19 perguntas em 5 blocos.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/policy/agents/agent.py` |
| **Tipo** | LLM direto (não ReAct) |
| **Como funciona** | Fluxo linear de perguntas, cada resposta salva no banco por bloco |
| **Blocos** | pipeline_rules, scheduling_rules, communication_rules, screening_rules, automation_rules |
| **Limites** | Não possui tools — usa chamada LLM direta para interpretar respostas |

### 3.11 AnalyticsReActAgent

**O que é:** Agente de analytics, KPIs e previsões de contratação.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/analytics/agents/` |
| **Registry** | `analytics` |
| **Registry file** | `analytics_tool_registry.py` |
| **Como funciona** | ReAct loop com acesso a dados agregados de vagas, candidatos e agentes |
| **Tools** | 6 |
| **max_iterations** | 6 |
| **Limites** | Dados derivados de PostgreSQL — sem acesso a dados brutos de LLM |

| Ferramenta | O que faz |
|-----------|-----------|
| `get_job_insights` | Insights de vagas (tempo aberto, conversão, comparação) |
| `predict_hiring_metrics` | Previsões de contratação baseadas em dados históricos |
| `generate_job_report` | Relatório de performance de vagas |
| `generate_candidate_report` | Relatório de candidatos por vaga/pipeline |
| `get_search_analytics` | Analytics de buscas realizadas |
| `get_agent_performance` | Métricas de performance dos agentes IA |

### 3.12 ATSIntegrationReActAgent

**O que é:** Agente de integração bidirecional com plataformas ATS externas (Gupy, Pandapé, Merge).

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/ats_integration/agents/` |
| **Registry** | `ats_integration` |
| **Registry file** | `ats_integration_tool_registry.py` |
| **Como funciona** | ReAct loop para sincronizar candidatos entre LIA e ATS externos |
| **Tools** | 5 |
| **max_iterations** | 6 |
| **Limites** | Dependente de APIs externas (Gupy, Pandapé). Rate limits aplicáveis. |

| Ferramenta | O que faz |
|-----------|-----------|
| `sync_candidate_to_ats` | Sincroniza candidato para plataforma ATS externa |
| `fetch_candidate_from_ats` | Importa candidato de plataforma ATS externa |
| `validate_ats_fields` | Valida campos antes de sincronização |
| `bulk_sync_candidates` | Sincronização em massa de candidatos |
| `get_sync_status` | Status da sincronização (sucesso, erro, pendente) |

### 3.13 CommunicationReActAgent

**O que é:** Agente de comunicação multi-canal com conformidade LGPD.

| Campo | Valor |
|-------|-------|
| **Domínio** | `app/domains/communication/agents/` |
| **Registry** | `communication` |
| **Registry file** | `communication_tool_registry.py` |
| **Como funciona** | ReAct loop para envio de mensagens via email e WhatsApp com rate limiting |
| **Tools** | 5 |
| **max_iterations** | 6 |
| **Limites** | Rate limiting obrigatório via `check_rate_limit` antes de envio. Conformidade LGPD. |

| Ferramenta | O que faz |
|-----------|-----------|
| `send_email` | Envia email ao candidato |
| `send_whatsapp` | Envia mensagem WhatsApp |
| `get_communication_history` | Histórico de comunicações com candidato |
| `schedule_message` | Agenda envio de mensagem para data futura |
| `check_rate_limit` | Verifica limites de envio antes de comunicação |

---

## 4. Tool Registries — Sumário

Contagens extraídas por `ToolDefinition(` count em cada arquivo `*_tool_registry.py`.

| Registry file | Agente | Tools | Registry key |
|----------|--------|:-----:|-------------|
| `job_management/agents/wizard_tool_registry.py` | WizardReAct | 10 | `wizard` |
| `cv_screening/agents/pipeline_tool_registry.py` | PipelineReAct | 15 | `pipeline` |
| `pipeline/agents/pipeline_tool_registry.py` | PipelineTransition | 20 | (invocação direta) |
| `sourcing/agents/sourcing_tool_registry.py` | SourcingReAct | 15 | `sourcing` |
| `recruiter_assistant/agents/talent_tool_registry.py` | TalentReAct | 13 | `talent` |
| `recruiter_assistant/agents/jobs_mgmt_tool_registry.py` | JobsMgmtReAct | 14 | `jobs_management` |
| `recruiter_assistant/agents/kanban_tool_registry.py` | KanbanReAct | 22 | `kanban` |
| `hiring_policy/agents/policy_tool_registry.py` | PolicyReAct | 13 | `policy` |
| `automation/agents/automation_tool_registry.py` | AutomationReAct | 6 | `automation` |
| `analytics/agents/analytics_tool_registry.py` | AnalyticsReAct | 6 | `analytics` |
| `ats_integration/agents/ats_integration_tool_registry.py` | ATSIntegrationReAct | 5 | `ats_integration` |
| `communication/agents/communication_tool_registry.py` | CommunicationReAct | 5 | `communication` |
| **TOTAL** | **12 registries** | **144** | |

**Catálogo central:** `app/tools/tool_registry_metadata.yaml`

---

## 5. Guardrails por Agente

| Agente | Tool de confirmação (requer HITL) |
|--------|----------------------------------|
| Talent | `create_shortlist` |
| Kanban | `batch_move_candidates`, `send_batch_communication`, `start_screening_batch` |
| JobsMgmt | `pause_job`, `close_job` |
| PipelineTransition | `validate_transition` (validação pré-transição) |
| Pipeline (cv_screening) | `move_candidate`, `batch_move` |
| Messaging (r_a_v5) | Todos os envios |

---

## 6. Background & Automações

### 6.1 ProactiveAgentWorker

Ciclo: 30 min | Arquivo: `libs/agents-core/lia_agents_core/proactive_worker.py`

Checks executados por `run_all_checks()` (10 checks ativos, na ordem do código):

| Check | Trigger | Severidade |
|-------|---------|-----------|
| `check_velocity_bottleneck` | Acima do threshold por etapa | warning/critical |
| `check_recruiter_backlog` | Aguardando ação (por recrutador) | warning/critical |
| `check_early_warning` | EWS ≥0.6 (por recrutador) | warning/critical |
| `check_journey_intelligence` | Health <50 (por recrutador) | warning/critical |
| `check_pipeline_prediction` | Prob <30% (por recrutador) | warning/critical |
| `check_stale_pipeline` | Candidato parado ≥7d | warning; ≥14d critical |
| `check_low_pipeline` | Vaga <3 candidatos | warning; zero critical |
| `check_high_scorers` | Score >80% em "Novo" | warning |
| `check_deadlines` | Prazo ≤7d | warning; ≤2d critical |
| `check_silver_medalists` | Candidatos prata disponíveis | info |

Nota: `check_engagement_gaps()` existe como método mas NÃO está na lista de `run_all_checks()`.

### 6.2 Workers (recruiter_agent_v5)

| Worker | Queue | Função |
|--------|-------|--------|
| `celery_worker.py` | default | Queries de domínio via RabbitMQ |
| `evaluation_worker.py` | evaluation | Avaliações de candidatos |

### 6.3 Celery Tasks (lia-agent-system)

Arquivo: `app/jobs/celery_tasks.py` — 27 tasks registradas.

| Categoria | Tasks | Schedule |
|-----------|-------|---------|
| **Agentes (execute)** | `agents.wizard.execute`, `agents.pipeline.execute`, `agents.sourcing.execute`, `agents.screening.execute`, `agents.kanban.execute`, `agents.policy.execute`, `agents.automation.execute` | On-demand |
| **Agentes (processo)** | `agents.wizard.process_async`, `agents.pipeline.transition_async` | On-demand |
| **Agentes (legacy)** | `agents.wsi_interview.start`, `agents.triagem.run`, `agents.sourcing.search` | On-demand |
| **Compliance** | `audit.apply_lifecycle_policy`, `lgpd.run_cleanup_daily` | Diário |
| **ML/Feedback** | `ml.feedback.process_weights`, `ml.feedback.recompute_active_jobs` | On-demand |
| **RAG** | `rag.rebuild_all_domains`, `rag.rebuild_domain_index` | On-demand |
| **Comunicação** | `communication.email.send_bulk`, `followup.process_pending`, `briefing.send_daily` | Diário / On-demand |
| **Manutenção** | `drift.run_batch`, `memory.compress_old_episodes`, `routing.recompute_adjustments`, `wsi.check_abandoned`, `ragas.evaluate_batch`, `agents.registry.check_reload` | Diário / On-demand |

---

## Referências

| Componente | Arquivo |
|-----------|---------|
| Domain Registry (r_a_v5) | `recruiter_agent_v5/src/domains/registry.py` |
| Base Domain (r_a_v5) | `recruiter_agent_v5/src/domains/base.py` |
| ReactAgentRegistry (lia) | `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py` |
| Tool Registry Metadata | `lia-agent-system/app/tools/tool_registry_metadata.yaml` |
| Proactive Worker | `lia-agent-system/libs/agents-core/lia_agents_core/proactive_worker.py` |
| MAPA_INTELIGENCIA | `docs/analises/MAPA_INTELIGENCIA_LIA_COMPLETO.md` |
| GUIA_ARQUITETURA_IA | `docs/GUIA_ARQUITETURA_IA_v1.0.md` |
