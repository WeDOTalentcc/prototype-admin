# Mapeamento de Capacidades dos Prompts da LIA × v5

**Versão:** 3.0 | **Data:** Março/2026 | **Autoria:** Análise de código LIA local + recruiter_agent_v5 (GitHub WeDOTalent)

---

## Prefácio: como ler este documento

Este documento compara dois sistemas de agentes de IA que compartilham a mesma interface:

- **LIA** (`lia-agent-system/`) — FastAPI + Python. Código local.
- **v5** (`recruiter_agent_v5`) — LangGraph + Python. GitHub WeDOTalent.

Para cada contexto de prompt, as capacidades são divididas em três camadas:

| Tag | Significado |
|---|---|
| **[LIA-API]** | Capacidade com chamada real à API via tool (limitada pelo scope do contexto) |
| **[LIA-LLM]** | Capacidade conversacional do LLM sem chamada de API (depende de dados em contexto) |
| **[v5]** | Capacidade do recruiter_agent_v5 (domínio equivalente no GitHub) |

---

## Índice

1. [Visão geral: os 4 contextos](#visao-geral)
2. [Arquitetura de roteamento da LIA](#roteamento)
3. [Prompt 1 — Flutuante / Global](#prompt-1)
4. [Prompt 2 — Tabela de Vagas](#prompt-2)
5. [Prompt 3 — Dentro da Vaga (Kanban)](#prompt-3)
6. [Prompt 4 — Funil de Talentos](#prompt-4)
7. [Tabela-resumo global](#tabela-resumo)
8. [Glossário técnico](#glossario)

---

## 1. Visão geral: os 4 contextos {#visao-geral}

### Mapeamento frontend → backend (LIA)

O frontend envia `context_page` junto com cada mensagem. O `ContextAdapter` (`app/orchestrator/context_adapter.py`) normaliza esse campo em `context_type`, que determina o **scope de tools** disponíveis:

| Páginas do frontend | context_page | context_type mapeado | Domínios YAML | Scope (scope_config.py) |
|---|---|---|---|---|
| Chat flutuante (todas as páginas) | `general`, `global` | `general` → `global` | `recruiter_assistant` | GLOBAL |
| `/user/jobs`, wizard de vaga | `job`, `jobs`, `vacancies`, `wizard` | `job_management` → `jobs` | `job_management` | JOB_TABLE |
| `/user/jobs/{id}` (kanban) | `pipeline`, `kanban` | `pipeline` → `in_job` | `cv_screening` + `pipeline_transition` + `interview_scheduling` + `communication` | IN_JOB |
| `/user/candidates`, `/user/sourcing/{id}` | `sourcing`, `talent` | `talent_funnel` | `sourcing` + `analytics` | TALENT_FUNNEL |

### Mapeamento frontend → backend (v5)

| Rota frontend | domain no payload | Domínio v5 | Modo |
|---|---|---|---|
| Chat dedicado (`/user/lia`) | `null` + `hub_mode: true` | `autonomous` | HubPlanner (LLM + regex) |
| `/user/jobs` | `"jobs"` | `jobs` | Domain direto |
| `/user/jobs/{id}` | `"applies"` | `applies` | Domain direto |
| `/user/candidates`, `/user/sourcing/{id}/chat` | `"sourced_profile_sourcing"` | `sourced_profile_sourcing` | Domain direto |

---

## 2. Arquitetura de roteamento da LIA {#roteamento}

A LIA usa **dois sistemas de roteamento independentes** que coexistem:

### Sistema A — Scope de tools (por context_page)

Fonte: `app/tools/scope_config.py` → `filter_tools_by_scope()`.

Chamado pelo `Orchestrator.get_tools_for_context()` (linha 311-313, `orchestrator.py`):
```python
def get_tools_for_context(self, prompt_context: str) -> List[Dict[str, Any]]:
    scope = SCOPE_MAPPING.get(prompt_context.lower(), PromptScope.GLOBAL)
    return filter_tools_by_scope(get_all_tool_schemas(format="claude"), scope)
```

- Determina **quais API tools** o LLM pode chamar
- Baseado em `context_page` enviado pelo frontend
- Os scopes são **mutuamente exclusivos** — `filter_tools_by_scope` não faz union de scopes
- O scope GLOBAL não é "base sempre incluída" — é um scope com apenas 2 tools, ativado quando context_page é `general`/`global`

**Tools por scope (fonte executável: `scope_config.py`)**:

```
GLOBAL (2 tools):
  ACTION: generate_report | schedule_report

JOB_TABLE (19 tools):
  QUERY:  search_jobs | get_job_details | get_pipeline_stats | get_recruiter_metrics
          get_velocity_metrics | get_efficiency_metrics | get_comparative_metrics
          get_workload_distribution | get_hiring_quality | get_cost_metrics
          get_trends | get_market_benchmarks
  ACTION: create_job | update_job | pause_job | close_job | publish_job
          export_job_analytics | generate_report

IN_JOB (25 tools):
  QUERY:  get_job_details | get_vacancy_funnel | get_candidate_details
          get_activity_summary | get_pending_actions | compare_candidates
          get_candidate_stats | get_bottleneck_analysis | get_job_velocity
          get_job_quality_metrics | get_stakeholder_metrics | get_prediction_metrics
          get_job_benchmark | get_smart_alerts
  ACTION: update_candidate_stage | bulk_update_candidates_stage | reject_candidate
          shortlist_candidate | add_to_list | hide_candidate | wsi_screening
          send_email | send_whatsapp | schedule_interview | send_feedback

TALENT_FUNNEL (20 tools):
  QUERY:  search_candidates | get_candidate_details | get_candidate_stats
          compare_candidates | get_talent_quality | get_talent_engagement
          get_talent_availability | get_diversity_metrics | get_candidate_history
          get_ml_predictions | get_conversion_patterns
  ACTION: add_candidate_to_vacancy | reject_candidate | shortlist_candidate
          add_to_list | hide_candidate | send_email | send_whatsapp
          send_bulk_email | export_candidates
```

**Nota sobre duas fontes de metadados**: Existe também `tool_registry_metadata.yaml` (carregado por `tool_registry_loader.py`), que provê metadados declarativos (description, allowed_agents, version). Algumas tools nesse YAML (como `search_salary_benchmark`, `validate_job_fields`, `generate_enriched_jd`, `save_job_draft`, `get_company_config`, `capture_wizard_feedback`) não aparecem em `scope_config.py`. O `filter_tools_by_scope` filtra pelo nome da tool — tools não registradas no Python não são chamáveis mesmo que listadas no YAML.

### Sistema B — Domain routing (por intenção da mensagem)

Fonte: `app/orchestrator/cascaded_router.py` → `CascadedRouter.route()`.

Chamado na linha 120 de `orchestrator.py`:
```python
route = await self._cascaded_router.route(sanitized, ctx, session_id=conversation_id)
domain_id, confidence = route.domain_id, route.confidence
```

- Determina **qual domínio Python** processa a ação
- Baseado no **conteúdo da mensagem** (não no context_page)
- Independente do scope de tools
- **6 tiers em custo crescente:**

```
Tier 0: MemoryResolver    — pronomes/referências de contexto (ex: "ele", "esse candidato")
Tier 1: LRU in-process   — hash MD5, O(1), cache de sessão
Tier 2: Redis cache      — distribuído, compartilhado entre workers
Tier 3: VectorSemanticCache — pgvector, cosine similarity ≥ 0.92 (configurável via
                              ROUTER_VECTOR_SIMILARITY_THRESHOLD)
Tier 4: FastRouter       — regex/keyword, O(n) patterns
Tier 5: LLM Cascade      — Haiku → Sonnet → Opus (custo crescente)
Fallback: clarification  — pergunta ao usuário quando tudo falha
```

- Domínios mapeados: `job_management`, `cv_screening`, `interview_scheduling`, `analytics`, `communication`, `recruiter_assistant`, `sourcing`, `automation`, `kanban_search`, `kanban_insight`, `kanban_action`, `pipeline_context`, `pipeline_decision`, `pipeline_action`, `sourcing_planner`, `sourcing_search`, `sourcing_enrich`, `sourcing_engagement`

### Fluxo completo do MainOrchestrator (`main_orchestrator.py`)

```
MENSAGEM RECEBIDA (UniversalContext via ContextAdapter)
    │
    ├── FairnessGuard.check() — bloqueia inputs discriminatórios ANTES de processar
    │
    ├── Phase 0: PendingActionState — se há ação aguardando confirmação/params
    │
    ├── Phase 1: ActionExecutor — ações detectadas por padrão fechado
    │
    └── Phase 2: Orchestrator.process_request_with_memory()
            │
            ├── CascadedRouter.route() → domain_id (por conteúdo da mensagem)
            │
            ├── PolicyEngine.validate_request() → allowed/blocked
            │
            ├── PlanDetector → se multi-step, PlanExecutor.execute()
            │
            └── DomainRegistry.get_instance(domain_id) → DomainWorkflow.process()
                    │
                    └── [se domain=None] → _handle_directly() com LLM direto
```

**Diferença crítica LIA vs v5:**

| Aspecto | LIA | v5 |
|---|---|---|
| Domain routing | CascadedRouter (6 tiers, por conteúdo da mensagem) | HubPlanner (LLM + regex, por intenção da query) |
| Scope de tools | filter_tools_by_scope (por context_page do frontend) | Todas as 73+ tools do autonomous domain |
| Como esses dois se relacionam | Independentes: routing escolhe o domínio; scope limita as tools disponíveis | Não há separação — autonomous tem acesso a tudo |
| Cross-context | CascadedRouter pode rotear para `cv_screening` mesmo em context "general" | HubPlanner navega programaticamente para o domínio certo |

---

## 3. Prompt 1 — Flutuante / Global {#prompt-1}

### O que é e onde aparece

Chat flutuante disponível em **todas as páginas** da plataforma. Ativado quando `context_page: "general"/"global"` → scope GLOBAL.

**Limitação de scope**: No scope GLOBAL, `filter_tools_by_scope` disponibiliza apenas 2 tools de API: `generate_report` e `schedule_report`. O CascadedRouter pode rotear a mensagem para domínios especializados (job_management, cv_screening, etc.), mas as tools chamáveis são limitadas ao scope.

---

### 3.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: GLOBAL — 2 tools)

| Tool | O que faz | Parâmetros |
|---|---|---|
| `generate_report` | Gera relatório de analytics para período/escopo definidos | `report_type`, `date_from`, `date_to`, `format: pdf\|csv\|json` |
| `schedule_report` | Agenda relatório recorrente enviado automaticamente | `report_type`, `schedule` (cron), `recipients[]` |

#### [LIA-LLM] Capacidades conversacionais (dados em contexto de conversa)

Estas capacidades usam o LLM sem chamar API — dependem de dados passados no payload pelo frontend ou mencionados na conversa:

- **Briefing e planejamento de agenda** — organiza e prioriza informações já presentes na conversa (candidatos mencionados, vagas discutidas)
- **Análises e comparações** — compara candidatos se seus dados já foram fornecidos na sessão
- **Resposta a perguntas gerais** — boas práticas de RH, interpretação de dados em contexto, orientações sobre processos
- **Memória de preferências** — lembra decisões e preferências da sessão atual (`ConversationState` + `ConversationMemory`)
- **Clarificação de ambiguidades** — quando CascadedRouter retorna `clarification_needed`, pergunta ao usuário

#### [v5] Capacidades do autonomous domain (73+ tools em 13 módulos)

O v5 autonomous tem acesso a todas as áreas sem restrição de scope:

| Módulo | Tools | Resumo |
|---|---|---|
| **Vagas** (`tools/jobs.py`) | `search_jobs`, `get_job`, `create_job`, `update_job`, `get_job_kanban`, `get_job_analytics`, `get_matching_candidates`, `update_job_status`, `get_all_jobs_stats`, `duplicate_job`, `get_job_selective_processes`, `get_pipeline_health`, `get_multi_job_analytics`, `get_job_context_rich`, `get_job_org_structure`, `get_job_ai_suggestion`, `get_job_questions`, `start_auto_sourcing`, `send_reject_feedback`, `bulk_add_list_to_job`, `get_job_alerts`, `bulk_archive_jobs`, `bulk_pause_jobs`, `bulk_activate_jobs` | CRUD completo de vagas + analytics + alertas + matching + ações em lote |
| **Candidatos** (`tools/candidates.py`) | `search_candidates`, `search_candidates_hybrid`, `get_candidate`, `create_candidate`, `update_candidate`, `get_candidates_stats`, `full_candidate_search` | Busca (text + ES 70%/embeddings 30% + pipeline 3 buscas paralelas) + CRUD |
| **Candidaturas** (`tools/applies.py`) | `search_applies`, `get_apply_details`, `create_apply`, `bulk_create_applies`, `update_apply`, `move_apply_stage`, `get_apply_history`, `get_selective_processes`, `get_apply_stats`, `get_stalled_applies`, `bulk_approve_applies`, `bulk_reject_applies`, `bulk_move_applies`, `send_apply_reject_feedback`, `diagnose_applies` | Pipeline completo + bulk + diagnóstico |
| **Sourcing** (`tools/sourcing.py`) | `search_sourcings`, `start_sourcing`, `get_sourcing_details`, `get_sourcing_stats`, `find_similar_candidates`, `get_sourced_profiles`, `update_sourced_profile`, `import_sourced_profile`, `search_archetypes`, `get_multi_sourcing_stats` | Gestão de sessões de sourcing + pool externo |
| **Agendamento** (`tools/scheduling.py`) | `get_calendar_agenda`, `create_calendar_event`, `get_available_slots`, `generate_self_scheduling_link`, `search_meetings`, `create_internal_meeting`, `get_interview_sessions`, `get_events_without_feedback` | Calendário completo + self-scheduling |
| **Avaliações** (`tools/evaluations.py`) | `search_evaluations`, `get_evaluation`, `create_evaluation`, `list_evaluation_questions`, `create_evaluation_question`, `get_candidates_in_evaluations`, `send_evaluation` | Testes e avaliações |
| **Organização** (`tools/organization.py`) | `search_departments`, `get_department_tree`, `search_teams`, `search_lists`, `create_list`, `add_to_list`, `bulk_add_to_list`, `get_pending_approvals`, `approve_request`, `reject_request`, `daily_briefing_complete`, `get_recruiter_productivity_metrics`, `get_notifications`, `get_unread_notifications_count`, `get_messages` | Estrutura org + listas + aprovações + briefing |
| **Macros** (`tools/macros.py`) | `diagnose_job_complete`, `get_full_candidate_profile`, `get_daily_briefing` | Operações compostas |
| **Planejamento** (`tools/planning.py`) | `write_plan`, `read_plan` | Plano de execução visível (⬜→🔄→✅) |
| **File system** (`tools/file_system.py`) | `save_file`, `read_file`, `list_files` | Armazena resultados >5K chars |
| **Genérico** (`tools/generic.py`) | `think`, `discover_api`, `call_api`, `ask_user`, `get_instructions` | Raciocínio + fallback de API |

**Regras de execução (AUTONOMOUS_SYSTEM_PROMPT):**
- 1 tool: vai direto, sem write_plan
- 2+ tools: SEMPRE write_plan antes + atualiza após cada tool
- Budget: max 40 API calls por sessão (planning/file_system não contam)
- Offloading: resultados >5 itens ou >5K chars → save_file automático
- Resolução de contexto: `viewing_entities` → sessão → URL atual → `ask_user`

---

### 3.2 Restrições OUT (LIA — scope GLOBAL)

| Não disponível como tool de API | Por quê | Scope que tem |
|---|---|---|
| Buscar vagas | Não está em GLOBAL (scope_config.py) | JOB_TABLE |
| Criar vagas | Não está em GLOBAL | JOB_TABLE |
| Buscar candidatos | Não está em GLOBAL | TALENT_FUNNEL |
| Mover candidatos no pipeline | Não está em GLOBAL | IN_JOB |
| Enviar email/WhatsApp | Não está em GLOBAL | IN_JOB / TALENT_FUNNEL |
| Agendar entrevistas | Não está em GLOBAL | IN_JOB |
| Triagem WSI | Não está em GLOBAL | IN_JOB |

**Nota**: O CascadedRouter pode rotear mensagens do chat flutuante para domínios como `job_management` ou `cv_screening`. Nesses casos, o domínio processa a ação via seu próprio workflow, mas as tools de API chamáveis permanecem as do scope GLOBAL. As domains podem retornar informações ricas sem necessariamente precisar de tools de API extras.

---

### 3.3 Comparativo LIA × v5 — Prompt Flutuante

| Dimensão | LIA (scope GLOBAL) | v5 (autonomous, 73+ tools) |
|---|---|---|
| **Tools de API no scope** | 2 (generate_report, schedule_report) | 73+ em 13 módulos |
| **Domain routing** | CascadedRouter (6 tiers, por mensagem) | HubPlanner (LLM + regex) |
| **Busca de vagas via API** | ❌ Fora do scope GLOBAL | ✅ search_jobs, get_job_kanban, etc. |
| **Busca de candidatos via API** | ❌ Fora do scope GLOBAL | ✅ search_candidates, full_candidate_search |
| **Mover candidatos via API** | ❌ Fora do scope GLOBAL | ✅ move_apply_stage, bulk_move_applies |
| **Gerar relatório** | ✅ generate_report (pdf/csv/json) | ✅ Via analytics tools |
| **Agendar relatório** | ✅ schedule_report | ❌ Sem tool equivalente |
| **Briefing do dia via API** | ❌ Sem tool no scope | ✅ daily_briefing_complete |
| **Diagnóstico de vaga** | ❌ Sem tool no scope | ✅ diagnose_job_complete |
| **FairnessGuard** | ✅ Antes de qualquer processamento (MainOrchestrator) | ✅ Implícito no system prompt |
| **Multi-intenção** | ✅ PlanDetector + PlanExecutor | ✅ MULTI_INTENT_RE + HubTask[] paralelo |
| **Progresso visível** | ❌ Sem write_plan | ✅ write_plan (⬜→🔄→✅) |
| **Budget de tools** | ❌ Não controlado | ✅ Max 40 API calls por sessão |
| **Offloading de resultados** | ❌ | ✅ save_file para >5K chars |
| **Streaming SSE** | ⚠️ Via WebSocket | ✅ /chat/stream com SSE nativo |
| **Navegação programática** | ❌ | ✅ NavigationAction(NAVIGATE, target) |
| **Fallback de API genérico** | ❌ | ✅ call_api (qualquer endpoint Rails) |

---

## 4. Prompt 2 — Tabela de Vagas {#prompt-2}

### O que é e onde aparece

Aparece ao lado da listagem de vagas (`/user/jobs`). Ativado quando `context_page: "job"/"jobs"/"vacancies"/"wizard"` → scope JOB_TABLE.

**CascadedRouter**: mensagens sobre vagas → domain `job_management`. O scope JOB_TABLE tem 19 tools para criação, gestão, analytics e métricas de vagas.

---

### 4.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: JOB_TABLE — 19 tools, fonte: scope_config.py)

**Query tools (12):**

| Tool | O que faz |
|---|---|
| `search_jobs` | Busca vagas por título, status, departamento |
| `get_job_details` | Detalhes completos de uma vaga |
| `get_pipeline_stats` | Estatísticas do pipeline (candidatos por etapa, taxas) |
| `get_recruiter_metrics` | Métricas de performance do recrutador |
| `get_velocity_metrics` | Velocidade do processo seletivo (time-to-fill, time-to-hire) |
| `get_efficiency_metrics` | Eficiência: triagens por hora, aprovação por etapa |
| `get_comparative_metrics` | Comparação de vagas entre si |
| `get_workload_distribution` | Distribuição de carga de trabalho entre recrutadores |
| `get_hiring_quality` | Qualidade das contratações |
| `get_cost_metrics` | Custo por contratação, ROI por canal |
| `get_trends` | Tendências temporais do processo seletivo |
| `get_market_benchmarks` | Benchmarks de mercado (tempo, custo, conversão) |

**Action tools (7):**

| Tool | O que faz |
|---|---|
| `create_job` | Cria nova vaga no banco `[ESCRITA]` |
| `update_job` | Edita campos de vaga existente `[ESCRITA]` |
| `pause_job` | Pausa uma vaga (deixa de receber candidatos) `[ESCRITA]` |
| `close_job` | Encerra vaga `[ESCRITA]` |
| `publish_job` | Publica vaga em canais `[ESCRITA]` |
| `export_job_analytics` | Exporta analytics da vaga em CSV |
| `generate_report` | Gera relatório de vagas (compartilhada com GLOBAL) |

#### [LIA-LLM] Capacidades conversacionais

- **Wizard conversacional de criação** — conduz o recrutador passo a passo: título, área, senioridade, tipo de contrato, faixa salarial, localidade, modelo de trabalho, competências WSI, etapas do processo seletivo; uma pergunta por vez com confirmação por seção
- **Job Description gerada por IA** — produz JD profissional com seções padrão (Sobre a empresa | Responsabilidades | Requisitos | Benefícios), garantindo linguagem inclusiva e não discriminatória
- **Alerta de requisitos restritivos** — avisa se requisitos coletados são excessivamente restritivos (risco de pipeline escasso)
- **Sugestão de etapas do processo** — sugere etapas adequadas ao tipo de cargo

**Nota sobre tool_registry_metadata.yaml**: O YAML documenta tools adicionais como `search_salary_benchmark`, `validate_job_fields`, `generate_enriched_jd`, `save_job_draft`, `get_intelligent_salary`, `get_intelligent_skills` com scope JOB_TABLE. Se implementadas em Python e registradas no `tool_registry`, elas seriam filtradas corretamente pelo `filter_tools_by_scope` (pois o filtro é por nome). A confirmação de quais estão efetivamente implementadas requer checar `initialize_tools()`.

#### [v5] Capacidades do domínio `jobs`

| Action | Tipo | O que faz |
|---|---|---|
| `show_job_details` | QUERY | Detalhes completos da vaga |
| `list_jobs` | QUERY | Listagem com abas: active/urgent/paused/archived/all |
| `pipeline_status` | QUERY | Kanban visual com candidatos por etapa |
| `job_analytics` | ANALYZE | Funil, taxas de conversão, gargalos, tempo médio |
| `account_stats` | AGGREGATE | Estatísticas globais de todas as vagas |
| `pipeline_health` | ANALYZE | Saúde de múltiplas vagas: score, gargalos, parados |
| `alerts` | QUERY | Alertas: prazo vencido, urgentes sem finalistas |
| `summarize_job` | ANALYZE | Resumo executivo: dados + analytics |
| `matching_candidates` | QUERY | Candidatos compatíveis via embedding similarity |
| `change_status` | ACTION | Publicar/pausar/fechar/reabrir/arquivar `[ESCRITA]` |
| `copy_job` | ACTION | Duplicar vaga `[ESCRITA]` |
| `bulk_apply_action` | ACTION | Ação em lote no pipeline `[LOTE][ESCRITA]` |
| `export_job` | QUERY | Exportar vaga em CSV |
| `generate_suggestion` | ANALYZE | Sugestões de melhoria para a JD via IA |
| `generate_interview_questions` | ANALYZE | Perguntas de entrevista por competência |
| `auto_source` | ACTION | Inicia sourcing automático de candidatos |
| `send_reject_feedback` | ACTION | Feedback de rejeição em lote `[ESCRITA]` |

**Cache tiered v5** (`TieredContextManager`):
- Tier 1: dados básicos (rápido) — para ações simples
- Tier 2: dados completos + analytics — para análises e relatórios

**Detecção de intenção v5 por regex** (`_CONTEXT_ACTION_PATTERNS`):
```
"pipeline|kanban"          → pipeline_status
"analytics|funil|gargalo"  → job_analytics
"report|relatório|resumo"  → summarize_job
"alertas"                  → alerts
"estatísticas|stats"       → account_stats
"exportar"                 → export_job
"auto-source"              → auto_source
"saúde do pipeline"        → pipeline_health
```

---

### 4.2 Restrições OUT (LIA — scope JOB_TABLE)

| Não disponível como tool de API | Scope que tem |
|---|---|
| Buscar candidatos no pool | TALENT_FUNNEL |
| Mover candidatos no pipeline | IN_JOB |
| Enviar email/WhatsApp a candidatos | IN_JOB / TALENT_FUNNEL |
| Agendar entrevistas | IN_JOB |
| Triagem WSI de CVs | IN_JOB |

---

### 4.3 Comparativo LIA × v5 — Tabela de Vagas

| Dimensão | LIA (scope JOB_TABLE, 19 tools) | v5 (jobs domain) |
|---|---|---|
| **Busca/detalhe de vagas** | ✅ search_jobs, get_job_details | ✅ list_jobs, show_job_details |
| **CRUD de vagas** | ✅ create_job, update_job, pause_job, close_job, publish_job | ✅ change_status + create via autonomous |
| **Pipeline stats** | ✅ get_pipeline_stats | ✅ job_analytics, account_stats |
| **Métricas de recrutador** | ✅ get_recruiter_metrics, get_velocity_metrics, etc. | ✅ via autonomous productivity metrics |
| **Benchmarks de mercado** | ✅ get_market_benchmarks | ✅ via autonomous |
| **Kanban visual** | ❌ Não está em JOB_TABLE (está em IN_JOB) | ✅ pipeline_status disponível |
| **Saúde de múltiplas vagas** | ❌ Sem tool no scope | ✅ pipeline_health |
| **Alertas de prazo** | ❌ Sem tool no scope | ✅ alerts |
| **Matching de candidatos** | ❌ Sem tool no scope JOB_TABLE | ✅ matching_candidates |
| **Sourcing automático** | ❌ Sem tool no scope | ✅ auto_source |
| **Duplicar vaga** | ❌ Sem tool no scope | ✅ copy_job |
| **Wizard conversacional** | ✅ [LIA-LLM] Estruturado passo a passo | ❌ Sem wizard estruturado |
| **JD gerada por IA** | ✅ [LIA-LLM] Com linguagem inclusiva | ✅ generate_suggestion |
| **Cache tiered** | ❌ | ✅ TieredContextManager (Tier1 vs Tier2) |
| **Detecção de intenção** | Via CascadedRouter | ✅ Regex rápido + LLM fallback |
| **Exportação** | ✅ export_job_analytics | ✅ export_job |

---

## 5. Prompt 3 — Dentro da Vaga (Kanban) {#prompt-3}

### O que é e onde aparece

Aparece dentro de uma vaga específica (`/user/jobs/{id}`), ao lado do kanban. Ativado quando `context_page: "pipeline"/"kanban"` → scope IN_JOB.

**Importante**: O scope IN_JOB tem 25 tools, incluindo `send_email`, `send_whatsapp` e `schedule_interview` — capacidades de comunicação e agendamento são disponíveis via API neste contexto.

---

### 5.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: IN_JOB — 25 tools, fonte: scope_config.py)

**Query tools (14):**

| Tool | O que faz |
|---|---|
| `get_job_details` | Dados completos da vaga |
| `get_vacancy_funnel` | Funil com candidatos por etapa e taxas de conversão |
| `get_candidate_details` | Perfil completo de candidato |
| `get_activity_summary` | Resumo de atividades e ações recentes da vaga |
| `get_pending_actions` | Pendências: feedbacks em atraso, candidatos sem resposta |
| `compare_candidates` | Comparação lado a lado de múltiplos candidatos |
| `get_candidate_stats` | Estatísticas do pool de candidatos da vaga |
| `get_bottleneck_analysis` | Análise de gargalos: etapas com alta taxa de rejeição ou abandono |
| `get_job_velocity` | Velocidade do processo: tempo médio por etapa |
| `get_job_quality_metrics` | Qualidade: taxa de oferta-aceite, retenção pós-contratação |
| `get_stakeholder_metrics` | Métricas de stakeholders: satisfação de gestores, tempo de resposta |
| `get_prediction_metrics` | Previsões: probabilidade de fechamento, candidatos em risco |
| `get_job_benchmark` | Benchmark da vaga vs. média da empresa/mercado |
| `get_smart_alerts` | Alertas inteligentes: candidatos parados, SLA expirado |

**Action tools (11):**

| Tool | O que faz |
|---|---|
| `update_candidate_stage` | Move candidato para etapa do pipeline `[ESCRITA]` |
| `bulk_update_candidates_stage` | Move múltiplos candidatos de etapa `[LOTE][ESCRITA]` |
| `reject_candidate` | Rejeita candidato com motivo `[ESCRITA]` |
| `shortlist_candidate` | Adiciona candidato à lista de pré-selecionados `[ESCRITA]` |
| `add_to_list` | Inclui candidato em lista de talentos `[ESCRITA]` |
| `hide_candidate` | Oculta candidato da visualização ativa (soft remove) `[ESCRITA]` |
| `wsi_screening` | Inicia avaliação WSI (voice\|text\|video) `[ESCRITA]` |
| `send_email` | Envia email para candidato(s) `[ESCRITA]` |
| `send_whatsapp` | Envia mensagem WhatsApp `[ESCRITA]` |
| `schedule_interview` | Agenda entrevista no calendário `[ESCRITA]` |
| `send_feedback` | Envia feedback estruturado para candidato `[ESCRITA]` |

#### [LIA-LLM] Capacidades conversacionais

Com dados de candidatos passados pelo frontend no payload (`candidates[]`, `selected_candidate_ids[]`, `job_context`):

- **Triagem curricular (Score WSI em 7 blocos)**:
  1. Hard Skills Técnicas
  2. Soft Skills / Comportamentais (evidências CBI)
  3. Experiência Profissional (anos, empresas, setor, progressão)
  4. Liderança (gestão de pessoas, projetos, equipes)
  5. Comunicação (clareza, persuasão, escrita, oratória)
  6. Alinhamento Cultural (fit com valores e cultura)
  7. Potencial (capacidade de crescimento e aprendizado)
  - Recomendação: Avançar (≥75%) | Revisão (60-74%) | Rejeitar (<60%)
  - Detecção de red flags: gaps de emprego, job hopping, inconsistências de datas
- **FairnessGuard pré-rejeição** — verifica viés antes de qualquer rejeição; ignora: nome, foto, localização, estado civil, idade, etnia (regras do `cv_screening.yaml`)
- **Ranking de candidatos** — ordena por score os candidatos do contexto carregado
- **Condução de entrevista WSI (CBI)** — perguntas comportamentais estruturadas, uma por vez; detecta respostas evasivas (`interview_scheduling.yaml`)
- **Análise de candidatos** — sugestão de próximas ações para cada candidato

---

### 5.2 Restrições OUT (LIA — scope IN_JOB)

| Não disponível | Escopo/contexto que tem |
|---|---|
| Buscar candidatos no pool externo | TALENT_FUNNEL |
| Criar ou editar vagas | JOB_TABLE |
| Relatórios globais (não específicos à vaga) | GLOBAL |
| send_bulk_email | TALENT_FUNNEL |
| Exportação de candidatos | TALENT_FUNNEL |

---

### 5.3 Dados coletados e gerados

**Inputs:**
- `context_page: "pipeline"/"kanban"` → scope IN_JOB
- `entity_id` = job_id — vaga aberta
- `job_context` — dados da vaga (título, requisitos, etapas, competências WSI)
- `candidates[]` — lista de candidatos carregados na tela pelo frontend
- `selected_candidate_ids[]` — candidatos selecionados pelo recrutador

**Outputs (LIA-API):** candidato movido de etapa, rejeitado, em lote movido, sessão WSI iniciada, email/WhatsApp enviados, entrevista agendada, feedback enviado

**Outputs (LIA-LLM):** Score WSI 0-100 com justificativa por bloco, recomendação de avanço/revisão/rejeição, análise de entrevista pós-condução

---

### 5.4 Arquitetura técnica — LIA

```
Frontend (context_page: "pipeline" | "kanban")
    ↓
ContextAdapter → context_type = "pipeline" → scope = IN_JOB
    ↓
MainOrchestrator:
    FairnessGuard.check() → bloqueia mensagens discriminatórias
    Phase 0: PendingActionState
    Phase 1: ActionExecutor
    Phase 2: Orchestrator.process_request_with_memory()
        ↓
        CascadedRouter.route() → domain_id (cv_screening, pipeline_transition,
                                  interview_scheduling, communication, etc.)
        ↓
        DomainWorkflow.process() → multi-YAML (4 domínios ativos):
            cv_screening.yaml        ← triagem e score WSI
            pipeline_transition.yaml ← movimentação no funil
            interview_scheduling.yaml ← condução WSI (CBI) e agendamento
            communication.yaml       ← comunicações multi-canal
        ↓
        filter_tools_by_scope(scope=IN_JOB) → 25 tools disponíveis
```

**Regras dos domínios:**
- `cv_screening.yaml`: NUNCA avalia por nome, foto, localização, estado civil, idade, etnia; FairnessGuard antes de rejeitar
- `interview_scheduling.yaml`: perguntas APENAS sobre competências profissionais; consentimento explícito para transcrição de áudio
- `communication.yaml`: todo email inclui rodapé "Mensagem gerada com assistência de IA pela LIA"; confirmação para >10 destinatários
- `pipeline_transition.yaml`: confirma ações destrutivas/irreversíveis antes de executar

---

### 5.5 Arquitetura técnica — v5

```
Frontend (domain: "applies") OU HubPlanner detecta query sobre candidaturas/kanban
    ↓
AppliesDomain → DomainContext (com job_id)
    ↓
AppliesDynamicPromptBuilder (max_actions_in_prompt=8)
    ↓
AppliesActions:
    analytics.py:    apply_analytics | stage_distribution
    bulk.py:         bulk_approve_applies | bulk_reject_applies | bulk_move_applies (async)
                     | send_apply_reject_feedback
    comparison.py:   compare_candidates
    details.py:      show_apply_details | apply_timeline
    pipeline.py:     get_kanban | move_stage | approve_apply | reject_apply
    scoring.py:      filter_by_score | top_candidates | full_ranking
    search.py:       search_applies | search_by_name | list_applies_by_stage
                     | recent_applies | count_applies
    sourcing.py:     stalled_applies (por severidade) | diagnose_applies (diagnóstico IA)
    ↓
AppliesCacheManager + AppliesAPIClient → ATS Rails API
```

---

### 5.6 Comparativo LIA × v5 — Kanban

| Dimensão | LIA (scope IN_JOB, 25 tools) | v5 (applies domain) |
|---|---|---|
| **Mover candidato** | ✅ update_candidate_stage | ✅ move_stage (com confirmação) |
| **Rejeitar candidato** | ✅ reject_candidate | ✅ reject_apply |
| **Aprovar candidato** | ✅ [via update_candidate_stage para próxima etapa] | ✅ approve_apply |
| **Ações em lote** | ✅ bulk_update_candidates_stage | ✅ bulk_approve/reject/move_applies (async) |
| **Funil da vaga** | ✅ get_vacancy_funnel | ✅ get_kanban + stage_distribution |
| **Analytics completo** | ✅ get_bottleneck_analysis, get_job_velocity, get_job_quality_metrics | ✅ apply_analytics |
| **Alertas inteligentes** | ✅ get_smart_alerts | ✅ stalled_applies (attention/warning/critical) |
| **Score WSI 7 blocos** | ✅ [LIA-LLM] com FairnessGuard explícito | ⚠️ Score via API (sem 7 blocos documentados) |
| **FairnessGuard** | ✅ Antes de toda rejeição (code + prompt) | ⚠️ Via FairnessGuard no MainOrchestrator (não no v5) |
| **Condução de entrevista WSI** | ✅ interview_scheduling.yaml (domínio dedicado) | ⚠️ Via autonomous (sem domínio dedicado) |
| **Agendamento de entrevista** | ✅ schedule_interview | ✅ Via autonomous (create_calendar_event) |
| **send_email / send_whatsapp** | ✅ Disponível no scope IN_JOB | ✅ Via autonomous tools |
| **Diagnóstico completo** | ❌ Sem action dedicada | ✅ diagnose_applies |
| **Timeline da candidatura** | ❌ Sem tool no scope | ✅ apply_timeline |
| **Top N candidatos** | ❌ Sem tool no scope | ✅ top_candidates, full_ranking |
| **Previsões (ML)** | ✅ get_prediction_metrics | ❌ Sem tool v5 explícita |
| **Benchmark da vaga** | ✅ get_job_benchmark | ❌ Sem tool v5 explícita |
| **Métricas de stakeholder** | ✅ get_stakeholder_metrics | ❌ Sem tool v5 explícita |
| **Cache** | ❌ | ✅ AppliesCacheManager |

---

## 6. Prompt 4 — Funil de Talentos {#prompt-4}

### O que é e onde aparece

Aparece em `/user/candidates` ou `/user/sourcing/{id}/chat`. Ativado quando `context_page: "sourcing"/"talent"` → scope TALENT_FUNNEL.

---

### 6.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: TALENT_FUNNEL — 20 tools, fonte: scope_config.py)

**Query tools (11):**

| Tool | O que faz |
|---|---|
| `search_candidates` | Busca candidatos no banco por query + filtros + paginação |
| `get_candidate_details` | Perfil completo com histórico |
| `get_candidate_stats` | Estatísticas agregadas do pool |
| `compare_candidates` | Comparação lado a lado de candidatos |
| `get_talent_quality` | Score de qualidade dos candidatos do pool |
| `get_talent_engagement` | Nível de engajamento dos candidatos |
| `get_talent_availability` | Disponibilidade de candidatos para novas oportunidades |
| `get_diversity_metrics` | Métricas de diversidade do pool |
| `get_candidate_history` | Histórico de candidaturas e processos anteriores |
| `get_ml_predictions` | Previsões de ML: probabilidade de aceite de oferta |
| `get_conversion_patterns` | Padrões de conversão do pool |

**Action tools (9):**

| Tool | O que faz |
|---|---|
| `add_candidate_to_vacancy` | Adiciona candidato ao processo seletivo de uma vaga `[ESCRITA]` |
| `reject_candidate` | Rejeita candidato do pool `[ESCRITA]` |
| `shortlist_candidate` | Adiciona candidato à lista de pré-selecionados `[ESCRITA]` |
| `add_to_list` | Inclui candidato em lista de talentos `[ESCRITA]` |
| `hide_candidate` | Oculta candidato da visualização `[ESCRITA]` |
| `send_email` | Envia email para candidato(s) `[ESCRITA]` |
| `send_whatsapp` | Envia mensagem WhatsApp `[ESCRITA]` |
| `send_bulk_email` | Envia email em massa `[LOTE][ESCRITA]` |
| `export_candidates` | Exporta candidatos em CSV ou XLSX |

#### [LIA-LLM] Capacidades conversacionais

- **Análise de compatibilidade** — score 0-100% para candidatos em contexto vs. vaga alvo
- **Construção de queries booleanas** — sugere e refina queries `Java AND AWS AND (senior OR pleno) NOT júnior`
- **Bias audit / Four-Fifths Rule** — análise de equidade com dados do pool em contexto (`analytics.yaml`)
- **Refinamento de busca** — se <5 resultados: propõe critérios menos restritivos; se >50: sugere filtros adicionais
- **Análise de mercado** — tendências de disponibilidade e benchmarking com dados em contexto

#### [v5] Capacidades do domínio `sourced_profile_sourcing`

| Action | Tipo | O que faz |
|---|---|---|
| `show_candidate_details` | QUERY | Detalhes + análise IA + experiências + skills |
| `search_candidates`, `filter_by_skill`, `filter_by_score`, `list_candidates`, `recent_candidates` | QUERY | Busca e filtros no pool |
| `count_candidates`, `count_by_filter` | AGGREGATE | Contagens |
| `average_score`, `score_distribution`, `score_above`, `top_candidates`, `priority_ranking` | AGGREGATE | Scoring e ranking |
| `average_experience`, `language_distribution`, `education_distribution`, `gender_distribution`, `location_distribution`, `work_model_distribution` | AGGREGATE | Distribuições demográficas |
| `compare_candidates` | ANALYZE | Comparação com análise IA |
| `summarize_search`, `generate_executive_report`, `generate_top_candidates_report` | ANALYZE | Relatórios |
| `diversity_analysis` | ANALYZE | Four-Fifths Rule por dimensão |
| `analyze_skills`, `common_strengths`, `skill_gaps`, `candidates_to_discard`, `needs_screening`, `top_by_experience`, `analyze_search_improvement` | ANALYZE | Análises de pool |
| `approve_candidate`, `reject_candidate`, `add_rating` | ACTION | Avaliação de perfis sourced `[ESCRITA]` |

**StatsManager**: pré-computa e cacheia stats agregadas para 26 ações em `ACTIONS_USING_AGGREGATED` (evita N+1 chamadas para análises demográficas e de scoring).

---

### 6.2 Restrições OUT (LIA — scope TALENT_FUNNEL)

| Não disponível como tool | Scope que tem |
|---|---|
| Mover candidatos no pipeline de vaga | IN_JOB |
| Agendar entrevistas | IN_JOB |
| Criar ou editar vagas | JOB_TABLE |
| Triagem WSI de CVs de candidatos em vaga | IN_JOB |
| Gerar relatório genérico (não de candidatos) | GLOBAL |

---

### 6.3 Comparativo LIA × v5 — Funil de Talentos

| Dimensão | LIA (scope TALENT_FUNNEL, 20 tools) | v5 (sourced_profile_sourcing domain) |
|---|---|---|
| **Busca de candidatos** | ✅ search_candidates, get_candidate_details | ✅ search_candidates, filter_by_skill, filter_by_score |
| **Busca híbrida ES + embeddings** | ❌ Sem tool explícita no scope | ✅ search_candidates_hybrid (70% ES + 30% embeddings) |
| **Previsões de ML** | ✅ get_ml_predictions | ❌ Sem tool explícita |
| **Padrões de conversão** | ✅ get_conversion_patterns | ❌ Sem tool explícita |
| **Engajamento de candidatos** | ✅ get_talent_engagement | ❌ Sem tool explícita |
| **Score médio / distribuição** | ❌ Sem tool no scope | ✅ average_score, score_distribution, top_candidates |
| **Análise demográfica** | ✅ get_diversity_metrics (via scope_config) | ✅ 6 distribution actions (language/education/gender/location/work_model) |
| **Four-Fifths Rule** | ✅ get_diversity_metrics + analytics.yaml [LLM] | ✅ diversity_analysis |
| **Cache de stats agregadas** | ❌ | ✅ StatsManager (ACTIONS_USING_AGGREGATED) |
| **Relatório executivo** | ✅ generate_report (GLOBAL) | ✅ generate_executive_report (pipeline 4 etapas + LLM) |
| **Análise de melhoria de busca** | ⚠️ [LIA-LLM] sem tool | ✅ analyze_search_improvement |
| **Skill gaps** | ⚠️ [LIA-LLM] sem tool | ✅ skill_gaps |
| **Adicionar candidato a vaga** | ✅ add_candidate_to_vacancy | ✅ Via autonomous (create_apply) |
| **Shortlist** | ✅ shortlist_candidate | ✅ Via autonomous (add_to_list) |
| **Envio de email em massa** | ✅ send_bulk_email | ✅ Via autonomous |
| **Exportação** | ✅ export_candidates (csv/xlsx) | ✅ Via autonomous |
| **Aprovação de perfil sourced** | ✅ [via reject_candidate no scope] | ✅ approve_candidate, reject_candidate, add_rating |
| **Arquetipos de busca** | ❌ Sem tool no scope | ✅ search_archetypes (via autonomous) |
| **Comparação de sourcings** | ❌ | ✅ get_multi_sourcing_stats |

---

## 7. Tabela-resumo global {#tabela-resumo}

| Dimensão | Prompt 1 — Flutuante | Prompt 2 — Tabela Vagas | Prompt 3 — Kanban | Prompt 4 — Funil Talentos |
|---|---|---|---|---|
| **context_page (LIA)** | `general`, `global` | `job`, `jobs`, `vacancies`, `wizard` | `pipeline`, `kanban` | `sourcing`, `talent` |
| **domain (v5)** | `null` + hub_mode | `"jobs"` | `"applies"` | `"sourced_profile_sourcing"` |
| **Scope LIA (fonte: scope_config.py)** | GLOBAL | JOB_TABLE | IN_JOB | TALENT_FUNNEL |
| **N° tools LIA** | 2 | 19 | 25 | 20 |
| **N° actions v5** | 73+ (13 módulos) | 17 actions | 30+ actions | 32+ actions |
| **Domain routing LIA** | CascadedRouter (6 tiers) | CascadedRouter | CascadedRouter | CascadedRouter |
| **Domain routing v5** | HubPlanner (LLM + regex) | Domain direto | Domain direto | Domain direto |
| **Buscar vagas (API)** | ❌ | ✅ Ambos | ❌ | ❌ |
| **Criar vagas (API)** | ❌ | ✅ Ambos | ❌ | ❌ |
| **Buscar candidatos (API)** | ❌ | ❌ | ❌ | ✅ Ambos |
| **Mover candidatos (API)** | ❌ | ❌ | ✅ Ambos | ❌ |
| **send_email / send_whatsapp (API)** | ❌ | ❌ | ✅ LIA (IN_JOB) + v5 | ✅ Ambos |
| **schedule_interview (API)** | ❌ | ❌ | ✅ LIA (IN_JOB) + v5 | ❌ |
| **Score WSI 7 blocos** | ❌ | ❌ | ✅ [LIA-LLM] | ❌ |
| **FairnessGuard** | ✅ MainOrchestrator | ✅ MainOrchestrator | ✅ MainOrchestrator + cv_screening.yaml | ✅ MainOrchestrator |
| **Gerar relatório** | ✅ Ambos | ✅ Ambos | ❌ LIA | ✅ Ambos |
| **Agendar relatório** | ✅ LIA | ❌ | ❌ | ❌ |
| **Wizard de vaga** | ❌ | ✅ [LIA-LLM] | ❌ | ❌ |
| **Cache otimizado** | ❌ LIA | ✅ v5 (Tier1/Tier2) | ✅ v5 (AppliesCacheManager) | ✅ v5 (StatsManager) |
| **Progresso write_plan** | ❌ | ❌ | ❌ | ❌ (v5 sim) |
| **Budget de tools** | ❌ LIA | ❌ LIA | ❌ LIA | ❌ LIA |
| **Streaming SSE** | ⚠️ WebSocket | ⚠️ WebSocket | ⚠️ WebSocket | ⚠️ WebSocket |
| **LGPD compliance** | ✅ Ambos | ✅ Ambos | ✅ Ambos | ✅ Ambos |

---

## 8. Glossário técnico {#glossario}

| Termo | Definição |
|---|---|
| **context_page** | Campo enviado pelo frontend junto com cada mensagem. Determina o scope de tools disponíveis. |
| **context_type** | Tipo normalizado de contexto, mapeado pelo `ContextAdapter` a partir do `context_page`. |
| **scope** | Conjunto de tools disponíveis para o LLM em um contexto. Definido em `scope_config.py` (não no `tool_registry_metadata.yaml`). |
| **scope_config.py** | Fonte executável de runtime para filtering de tools. `filter_tools_by_scope()` retorna apenas as tools do scope ativo. Os scopes são mutuamente exclusivos. |
| **tool_registry_metadata.yaml** | Metadados declarativos das tools (description, allowed_agents, scope, version). Carregado por `tool_registry_loader.py` para documentação/audit. Não é a fonte de enforcement de runtime — essa é `scope_config.py`. |
| **CascadedRouter** | Componente LIA de roteamento de domínio por intenção da mensagem. 6 tiers: memory (pronomes) → LRU in-process → Redis → vector (pgvector cosine ≥0.92) → FastRouter (regex/keyword) → LLM (Haiku→Sonnet→Opus) → clarification. Rota para um `domain_id`, independente do scope de tools. |
| **HubPlanner** | Componente v5 equivalente ao CascadedRouter. Analisa query com PLANNER_SYSTEM_PROMPT, detecta FAST_NAV_PATTERNS (regex, sem LLM), MULTI_INTENT_RE (paralelo), e gera HubExecutionPlan. |
| **FairnessGuard** | Camada de proteção anti-discriminação executada ANTES de qualquer processamento no MainOrchestrator LIA. Bloqueia: critérios por gênero, etnia, idade, estado civil, nome, localização. |
| **[LIA-API]** | Capacidade da LIA que faz chamada real à API via tool do scope ativo. |
| **[LIA-LLM]** | Capacidade da LIA executada pelo LLM sem chamada de API (dados em contexto da conversa). |
| **[v5]** | Capacidade do recruiter_agent_v5 no GitHub WeDOTalent. |
| **MainOrchestrator** | Entry point único da LIA. Executa: FairnessGuard → PendingActionState → ActionExecutor → Orchestrator.process_request_with_memory() com CascadedRouter + DomainWorkflow. |
| **DomainWorkflow** | Executa o processamento do domínio: PRE_CHECK → domain action → POST_CHECK + FairnessGuard. Usa ReAct agent para ferramentas. |
| **WSI** | Workforce Screening Interview — avaliação em 7 blocos: Hard Skills, Soft Skills, Experiência, Liderança, Comunicação, Alinhamento Cultural, Potencial. |
| **Four-Fifths Rule** | Regra de equidade: se taxa de aprovação de um grupo for <80% da taxa do grupo mais aprovado, há evidência de disparidade sistemática. |
| **domain_id** | Identificador do domínio Python que processa a ação. Retornado pelo CascadedRouter (LIA) ou HubPlanner (v5). |
| **DomainContext** | Objeto de contexto do domínio (v5): `workspace_id`, `sourcing_id`, `selected_ids`, `conversation_memory`, `auth_token`, `api_calls_history`. |
| **ActionType** | Enum v5: `QUERY` (consulta), `AGGREGATE` (agrega), `ANALYZE` (analisa com IA), `ACTION` (modifica dados). |
| **write_plan** | Tool v5 que cria plano de execução visível ao usuário em tempo real: ⬜ pendente → 🔄 em andamento → ✅ concluído. |
| **StatsManager** | Componente v5 que pré-computa e cacheia stats agregadas para 26 ações em `ACTIONS_USING_AGGREGATED`. |
| **TieredContextManager** | Cache v5 do domínio `jobs`: Tier1 (dados básicos) e Tier2 (dados completos + analytics). |
| **IDOR** | Insecure Direct Object Reference. Prevenido pelo `ContextAdapter.validate_entity_ownership()` na LIA. |
| **CBI** | Competency-Based Interview — metodologia de entrevista estruturada por competências e evidências. Usada nas entrevistas WSI. |
| **MULTI_INTENT_RE** | Regex do v5 que detecta queries com múltiplas intenções distintas, gerando HubTask[] paralelas. |
| **viewing_entities** | Campo v5 enviado pelo frontend: entidades visíveis na tela atual (job_id, candidate_id). Permite resolução de referências implícitas. |
| **NavigationAction** | Ação v5 que instrui o frontend a navegar para uma URL específica sem recarregar. |
| **SSE** | Server-Sent Events — streaming servidor→cliente. O v5 expõe `/chat/stream` com SSE nativo. |
| **PlanDetector** | Componente LIA que detecta queries multi-step e gera ExecutionPlan para o PlanExecutor (análogo ao MULTI_INTENT_RE do v5, mas orientado a passos sequenciais). |

---

*Fontes LIA: `context_adapter.py` (PAGE_TO_CONTEXT_TYPE), `scope_config.py` (SCOPE_TOOL_MAPPING — fonte executável de runtime), `tool_registry_metadata.yaml` (metadados declarativos), `orchestrator.py` (SCOPE_MAPPING, filter_tools_by_scope, CascadedRouter), `main_orchestrator.py` (fluxo de fases), `cascaded_router.py` (6 tiers), `recruiter_assistant.yaml`, `job_management.yaml`, `cv_screening.yaml`, `pipeline_transition.yaml`, `interview_scheduling.yaml`, `communication.yaml`, `sourcing.yaml`, `analytics.yaml`, `interaction_patterns.py`*

*Fontes v5 (GitHub WeDOTalent/recruiter_agent_v5): `hub/catalog.py`, `hub/planner.py`, `domains/base.py`, `domains/autonomous/prompts.py` (AUTONOMOUS_SYSTEM_PROMPT), `domains/autonomous/tools/*.py` (13 módulos, 73+ tools), `domains/jobs/domain.py` + `actions/*.py`, `domains/applies/domain.py` + `actions/*.py`, `domains/sourced_profile_sourcing/domain.py` + `actions/*.py`*

*Para atualizar: reler `scope_config.py` (SCOPE_TOOL_MAPPING), `context_adapter.py` (PAGE_TO_CONTEXT_TYPE), `orchestrator.py` (SCOPE_MAPPING), e os `domain.py` + `actions/*.py` do v5.*
