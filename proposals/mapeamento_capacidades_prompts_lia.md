# Mapeamento de Capacidades dos Prompts da LIA × v5

**Versão:** 2.0 | **Data:** Março/2026 | **Autoria:** Análise de código LIA local + recruiter_agent_v5 (GitHub WeDOTalent)

> **Como ler:** Este documento descreve **dois sistemas separados** que compartilham a mesma UI. Para cada contexto de prompt, as capacidades são divididas em três camadas:
> - **[LIA-API]** — capacidades que fazem chamadas reais à API via tools (limitadas ao scope do contexto)
> - **[LIA-LLM]** — capacidades conversacionais do LLM sem chamada de API (dependem de dados já carregados no contexto)
> - **[v5]** — capacidades do recruiter_agent_v5 (domínio equivalente no GitHub)
>
> As tabelas comparativas ao final de cada seção mostram onde cada sistema está à frente.

---

## Índice

1. [Visão geral: os 4 contextos](#visao-geral)
2. [Prompt 1 — Flutuante / Global](#prompt-1)
3. [Prompt 2 — Tabela de Vagas](#prompt-2)
4. [Prompt 3 — Dentro da Vaga (Kanban)](#prompt-3)
5. [Prompt 4 — Funil de Talentos](#prompt-4)
6. [Tabela-resumo global](#tabela-resumo)
7. [Glossário técnico](#glossario)

---

## 1. Visão geral: os 4 contextos {#visao-geral}

O frontend envia `context_page` junto com cada mensagem. O backend usa esse campo para determinar qual domínio carregar e quais tools disponibilizar ao LLM.

### Mapeamento de contextos

**LIA** (`lia-agent-system/app/orchestrator/context_adapter.py` → `PAGE_TO_CONTEXT_TYPE`):

| Páginas do frontend | context_page enviado | context_type mapeado | Domínios YAML ativos | Scope de tools |
|---|---|---|---|---|
| Qualquer página (chat flutuante) | `general`, `global` | `general` | `recruiter_assistant` | GLOBAL |
| `/user/jobs`, wizard de vaga | `job`, `jobs`, `vacancies`, `wizard` | `job_management` | `job_management` | JOB_TABLE |
| `/user/jobs/{id}` (kanban) | `pipeline`, `kanban` | `pipeline` | `cv_screening` + `pipeline_transition` + `interview_scheduling` + `communication` | IN_JOB |
| `/user/candidates`, `/user/sourcing/{id}` | `sourcing`, `talent` | `talent_funnel` | `sourcing` + `analytics` | TALENT_FUNNEL |

**v5** (`src/api.py` → `ChatRequest.domain`, `src/hub/catalog.py` → `NAVIGATION_ROUTES`):

| Rota frontend | domain no payload | Domínio v5 | Modo |
|---|---|---|---|
| `/user/lia` (chat dedicado) | `null` + `hub_mode: true` | `autonomous` | HubPlanner (LLM-based) |
| `/user/jobs` | `"jobs"` | `jobs` | Domain direto |
| `/user/jobs/{id}` | `"applies"` | `applies` | Domain direto |
| `/user/candidates`, `/user/sourcing/{id}/chat` | `"sourced_profile_sourcing"` | `sourced_profile_sourcing` | Domain direto |

### Tools da LIA por scope (fonte: `tool_registry_metadata.yaml`)

```
GLOBAL (4 tools):
  get_company_config | capture_wizard_feedback | generate_report | schedule_report

JOB_TABLE (13 tools):
  search_salary_benchmark | validate_job_fields | get_job_suggestions | save_job_draft
  get_intelligent_salary | get_intelligent_skills | generate_enriched_jd
  search_jobs | get_job_details | get_pipeline_stats | create_job | update_job | publish_job

IN_JOB (6 tools):
  update_candidate_stage | reject_candidate | bulk_update_candidates_stage
  wsi_screening | hide_candidate | get_vacancy_funnel

TALENT_FUNNEL (9 tools):
  search_candidates | get_candidate_details | get_candidate_stats
  add_candidate_to_vacancy | shortlist_candidate | add_to_list
  export_candidates | send_email | send_whatsapp
```

---

## 2. Prompt 1 — Flutuante / Global {#prompt-1}

### O que é e onde aparece

O **Prompt Flutuante** aparece como ícone de chat em **todas as páginas** da plataforma. É o modo mais genérico da LIA — um copiloto de recrutamento que o usuário acessa sem navegar para uma página específica.

**Ativação:** qualquer página → frontend envia `context_page: "general"` → `context_type: "general"` → domínio `recruiter_assistant.yaml` + scope GLOBAL.

**Limitação importante:** no escopo GLOBAL da LIA, apenas 4 tools de API estão disponíveis. Capacidades que exigem busca de dados (vagas, candidatos, pipeline) são conversacionais — o LLM pode analisar dados já presentes no contexto da conversa, mas não pode buscá-los via API neste contexto.

---

### 2.1 Capacidades IN

#### [LIA-API] Capacidades via API (tools GLOBAL disponíveis)

| Tool | O que faz | Parâmetros principais |
|---|---|---|
| `get_company_config` | Obtém configuração da empresa: workflow de contratação, aprovações, configurações de sistema | `config_type` |
| `generate_report` | Gera relatório de analytics de recrutamento para período e escopo definidos | `report_type`, `date_from`, `date_to`, `format: pdf\|csv\|json` |
| `schedule_report` | Agenda relatório recorrente enviado automaticamente por email/etc. | `report_type`, `schedule` (cron), `recipients[]` |
| `capture_wizard_feedback` | Registra feedback do recrutador sobre a experiência com o wizard de criação de vagas | `feedback_type`, `rating`, `comment` |

#### [LIA-LLM] Capacidades conversacionais (sem chamada de API)

Estas capacidades dependem de dados **já carregados no contexto da conversa** (histórico de mensagens, dados passados pelo frontend no payload, preferências da sessão):

- **Briefing diário** — organiza e prioriza informações já presentes na conversa (candidatos mencionados, vagas discutidas, alertas citados)
- **Planejamento de agenda** — sugere ordem de prioridade para tarefas com base no contexto da conversa
- **Comparação de finalistas** — compara candidatos se seus dados já foram mencionados na sessão
- **Insights proativos** — antecipa próximas ações com base no histórico da sessão
- **Resposta a perguntas gerais** — sobre processos seletivos, boas práticas de RH, interpretação de dados já em contexto
- **Calibração de perfil** — ajusta critérios baseado em feedback do recrutador ao longo da conversa
- **Memória de preferências** — lembra preferências e decisões da sessão atual

**Restrição crítica:** O LLM não pode buscar candidatos, vagas, entrevistas ou dados do pipeline via API neste contexto. Para qualquer ação concreta que exija acesso ao banco de dados, o usuário precisa navegar à página correspondente (que ativa o prompt certo com as tools adequadas).

#### [v5] Capacidades do autonomous (73+ tools em 13 módulos)

O v5 não tem essa limitação — o `autonomous` domain acessa todas as áreas via seu conjunto de 73+ tools:

| Módulo | Tools principais | O que faz |
|---|---|---|
| **Vagas** (`tools/jobs.py`) | `search_jobs`, `get_job`, `create_job`, `update_job`, `get_job_kanban`, `get_job_analytics`, `get_matching_candidates`, `update_job_status`, `get_all_jobs_stats`, `duplicate_job`, `get_job_selective_processes`, `get_pipeline_health`, `get_multi_job_analytics`, `get_job_context_rich`, `get_job_org_structure`, `get_job_ai_suggestion`, `get_job_questions`, `start_auto_sourcing`, `send_reject_feedback`, `bulk_add_list_to_job`, `get_job_alerts`, `bulk_archive_jobs`, `bulk_pause_jobs`, `bulk_activate_jobs` | CRUD completo de vagas + analytics + alertas + matching + ações em lote |
| **Candidatos** (`tools/candidates.py`) | `search_candidates`, `search_candidates_hybrid`, `get_candidate`, `create_candidate`, `update_candidate`, `get_candidates_stats`, `full_candidate_search` | Busca (text + ES 70%/embeddings 30% + pipeline 3 buscas paralelas) + CRUD |
| **Candidaturas** (`tools/applies.py`) | `search_applies`, `get_apply_details`, `create_apply`, `bulk_create_applies`, `update_apply`, `move_apply_stage`, `get_apply_history`, `get_selective_processes`, `get_apply_stats`, `get_stalled_applies`, `bulk_approve_applies`, `bulk_reject_applies`, `bulk_move_applies`, `send_apply_reject_feedback`, `diagnose_applies` | Pipeline completo de candidaturas + bulk + diagnóstico |
| **Sourcing** (`tools/sourcing.py`) | `search_sourcings`, `start_sourcing`, `get_sourcing_details`, `get_sourcing_stats`, `find_similar_candidates`, `get_sourced_profiles`, `update_sourced_profile`, `import_sourced_profile`, `search_archetypes`, `get_multi_sourcing_stats` | Busca de talentos + gerenciamento de sessões de sourcing |
| **Agendamento** (`tools/scheduling.py`) | `get_calendar_agenda`, `create_calendar_event`, `get_available_slots`, `generate_self_scheduling_link`, `search_meetings`, `create_internal_meeting`, `get_interview_sessions`, `get_events_without_feedback` | Calendário completo + entrevistas + self-scheduling |
| **Avaliações** (`tools/evaluations.py`) | `search_evaluations`, `get_evaluation`, `create_evaluation`, `list_evaluation_questions`, `create_evaluation_question`, `get_candidates_in_evaluations`, `send_evaluation` | Testes e avaliações para candidatos |
| **Organização** (`tools/organization.py`) | `search_departments`, `get_department_tree`, `search_teams`, `search_lists`, `create_list`, `add_to_list`, `bulk_add_to_list`, `get_pending_approvals`, `approve_request`, `reject_request`, `daily_briefing_complete`, `get_recruiter_productivity_metrics`, `get_notifications`, `get_unread_notifications_count`, `get_messages` | Estrutura org + listas + aprovações + briefing + notificações |
| **Macros** (`tools/macros.py`) | `diagnose_job_complete`, `get_full_candidate_profile`, `get_daily_briefing` | Operações compostas: diagnóstico completo de vaga, perfil completo de candidato, briefing do dia |
| **Planejamento** (`tools/planning.py`) | `write_plan`, `read_plan` | Plano de execução visível ao usuário (⬜→🔄→✅) |
| **File system** (`tools/file_system.py`) | `save_file`, `read_file`, `list_files` | Armazena resultados >5K chars em arquivo virtual |
| **Genérico** (`tools/generic.py`) | `think`, `discover_api`, `call_api`, `ask_user`, `get_instructions` | Raciocínio + fallback de API + clarificação |

---

### 2.2 Restrições OUT

| O que NÃO faz (LIA contexto GLOBAL) | Contexto correto |
|---|---|
| Buscar vagas via API | Prompt 2 (context_page: "job") |
| Buscar candidatos via API | Prompt 4 (context_page: "sourcing") |
| Mover candidatos no pipeline via API | Prompt 3 (context_page: "pipeline") |
| Triagem de CVs com score WSI | Prompt 3 (context_page: "pipeline") |
| Criar vagas via wizard | Prompt 2 (context_page: "wizard") |
| Agendar entrevistas via API | Prompt 3 (context_page: "pipeline") |
| Qualquer ação que exija dados não presentes na conversa | Navegar para a página correta |

---

### 2.3 Arquitetura técnica — LIA

```
Frontend (context_page: "general" ou "global")
    ↓
ContextAdapter.from_rest() / from_ws() / from_rabbitmq()
    → context_type = "general"
    → entity_id = null (sem entidade em foco)
    ↓
MainOrchestrator
    → domínio ativo: recruiter_assistant.yaml
    → scope de tools carregado: GLOBAL (4 tools)
    ↓
LLM recebe:
    system_prompt: recruiter_assistant.yaml → "Você é LIA, Assistente Pessoal do Recrutador..."
    tools disponíveis: get_company_config, generate_report, schedule_report, capture_wizard_feedback
    ↓
Padrões de comportamento (interaction_patterns.py):
    NEGATION_DETECTION_BLOCK → cancela ação se mensagem contém negação
    CHAIN_OF_THOUGHT_BLOCK  → raciocina em <thought> antes de agir
    ANTI_SYCOPHANCY_BLOCK   → não concorda apenas para evitar conflito
    ↓
Canais suportados: REST /api/v1/chat | WebSocket | RabbitMQ
    (RabbitMQ: compatível com formato de payload do v5)
    ↓
Segurança: ContextAdapter.validate_entity_ownership()
    → previne IDOR: valida entity_id contra company_id nas tabelas
       sourcing_sessions | job_vacancies | candidates
```

**Formato de resposta (recruiter_assistant.yaml):**
- Briefing: bullet list urgentes → importantes → informativos
- Comparação: tabela markdown lado a lado
- Insights: `[Insight]` contexto + ação recomendada
- Encerramento: "Próximas ações sugeridas: [1] [2] [3]"

---

### 2.4 Arquitetura técnica — v5

```
Frontend (domain: null, hub_mode: true)
    ↓
POST /chat ou /chat/stream (SSE)
    ↓
MessageRouter.route()
    ↓
HubPlanner (LLM-based — PLANNER_SYSTEM_PROMPT)
    │
    ├── FAST_NAV_PATTERNS (regex, sem LLM)
    │     "vá para vagas ativas" → NavigationAction(NAVIGATE, /user/jobs?tab=active)
    │
    ├── _JOB_ID_PATTERN: "vaga 42" → get_job(42) ou navigate /user/jobs/42
    │
    ├── _CANDIDATE_ID_PATTERN: "candidato 91" → get_candidate(91) ou navigate
    │
    ├── MULTI_INTENT_RE: detecta 2+ intenções → HubTask[] em paralelo
    │     Ex: "estatísticas de vagas E candidatos" → 2 tasks simultâneas
    │
    └── LLM classifica → HubExecutionPlan { tasks[], strategy, navigation_actions[] }
    ↓
AutonomousDomain
    → AUTONOMOUS_SYSTEM_PROMPT (100+ linhas)
    → Regras de execução:
        • 1 tool: vai direto, sem write_plan
        • 2+ tools: SEMPRE write_plan antes + atualiza após cada tool
        • Budget: max 40 chamadas de API (planning/file_system não contam)
        • Offloading: resultados >5 itens ou >5K chars → save_file automático
        • Resolução de contexto: viewing_entities → sessão → URL atual → ask_user
        • ask_user apenas para: nome duplicado, query vaga demais, escrita bloqueada
```

---

### 2.5 Diagrama de delegação e migração de contexto

#### LIA — Migração é sempre controlada pelo frontend

```
                    USUÁRIO ENVIA MENSAGEM
                            │
                     Frontend define
                      context_page
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
    "general"         "job"|"jobs"        "pipeline"|
    "global"         "vacancies"          "kanban"
         │            "wizard"                │
         ▼                  │                 ▼
    context_type:           ▼            context_type:
     "general"        context_type:       "pipeline"
     GLOBAL scope     "job_management"   IN_JOB scope
     4 tools          JOB_TABLE scope    6 tools
                      13 tools           (Prompt 3)
    (Prompt 1)        (Prompt 2)
                                    TAMBÉM:
                               "sourcing"|"talent"
                                     │
                                     ▼
                               context_type:
                               "talent_funnel"
                               TALENT_FUNNEL scope
                               9 tools (Prompt 4)
```

**Regra crítica:** O backend LIA não faz roteamento inteligente. O `context_type` é 100% determinado pelo `context_page` que o frontend envia. Se o frontend enviar `context_page: "general"`, a LIA terá apenas 4 tools disponíveis, mesmo que o usuário esteja perguntando sobre vagas.

#### v5 — Roteamento inteligente pelo HubPlanner

```
         USUÁRIO ENVIA MENSAGEM (hub_mode: true)
                        │
               HubPlanner analisa
                        │
     ┌──────────────────┼──────────────────────────┐
     ▼                  ▼                          ▼
FAST_NAV_PATTERNS   ID explícito         LLM classifica intenção
(regex, sem LLM)    na mensagem
     │                  │                          │
     ▼                  ▼               ┌──────────┼──────────┐
NavigationAction    Open direto         ▼          ▼          ▼
(navega a page)    (job ou          "vagas"    "pipeline"  "candidatos"
                   candidate)        query      query       query
                                       │          │           │
                              jobs   applies  sourced_
                              domain  domain  profile_
                                              sourcing
                                              domain

        MULTI_INTENT_RE detectado?
        → HubExecutionPlan com HubTask[] em paralelo
          Ex: "stats de vagas E candidatos" → 2 domains simultâneos
```

**Diferença crítica:** O v5 roteia para o domínio correto **automaticamente**, independente de qual página o usuário está. Na LIA, o frontend **precisa** enviar o `context_page` correto para que as tools adequadas sejam carregadas.

---

### 2.6 Comparativo LIA × v5 — Prompt Flutuante

| Dimensão | LIA (recruiter_assistant, GLOBAL scope) | v5 (autonomous, 73+ tools) |
|---|---|---|
| **Arquivo/código principal** | `recruiter_assistant.yaml` (4 tools GLOBAL) | `autonomous/prompts.py` (AUTONOMOUS_SYSTEM_PROMPT) |
| **Tools disponíveis** | 4 (get_company_config, generate_report, schedule_report, capture_wizard_feedback) | 73+ em 13 módulos |
| **Busca de vagas via API** | ❌ Fora do scope GLOBAL | ✅ `search_jobs`, `get_job`, `get_all_jobs_stats` |
| **Busca de candidatos via API** | ❌ Fora do scope GLOBAL | ✅ `search_candidates`, `full_candidate_search` |
| **Mover candidatos via API** | ❌ Fora do scope GLOBAL | ✅ `move_apply_stage`, `bulk_move_applies` |
| **Briefing do dia** | [LLM-only] Conversa sem API | ✅ `daily_briefing_complete` (macro) |
| **Diagnóstico de vaga** | ❌ Sem tool | ✅ `diagnose_job_complete` (coleta paralela) |
| **Candidatos parados** | ❌ Sem tool | ✅ `get_stalled_applies` (por severidade) |
| **Gerar relatório** | ✅ `generate_report` (pdf/csv/json) | ✅ Via `get_job_analytics` + `get_recruiter_productivity_metrics` |
| **Agendar relatório recorrente** | ✅ `schedule_report` | ❌ Sem tool equivalente documentada |
| **Configuração da empresa** | ✅ `get_company_config` | ✅ Via `discover_api` + `call_api` |
| **Roteamento** | Determinístico (frontend define) | ✅ HubPlanner (LLM + regex) |
| **Multi-intenção** | ❌ | ✅ MULTI_INTENT_RE + HubTask[] paralelo |
| **Progresso visível** | ❌ | ✅ `write_plan` (⬜→🔄→✅) |
| **Budget de tools** | ⚠️ Não controlado | ✅ Max 40 API calls por sessão |
| **Offloading de resultados** | ❌ | ✅ `save_file` automático para >5K chars |
| **Navegação programática** | ❌ | ✅ `NavigationAction(NAVIGATE, target)` |
| **Streaming SSE** | ⚠️ Via WebSocket | ✅ `/chat/stream` com SSE nativo |
| **Fallback genérico de API** | ❌ | ✅ `call_api` (qualquer endpoint Rails) |
| **Anti-sycophancy** | ✅ `ANTI_SYCOPHANCY_BLOCK` explícito | ✅ Implícito no system prompt |
| **IDOR prevention** | ✅ `validate_entity_ownership()` | ✅ Via `workspace_id` no DomainContext |

---

## 3. Prompt 2 — Tabela de Vagas {#prompt-2}

### O que é e onde aparece

O **Prompt Expandido da Tabela de Vagas** aparece ao lado da listagem de vagas (`/user/jobs`). É o prompt especializado para criar, configurar, editar e gerir vagas. Ativado via `context_page: "job"/"jobs"/"vacancies"/"wizard"`.

**Quando usar:** criar nova vaga, gerar job description, benchmark salarial, editar requisitos, publicar vaga, ver dados da tabela de vagas.

---

### 3.1 Capacidades IN

#### [LIA-API] Capacidades via API (scope: JOB_TABLE — 13 tools)

| Tool | O que faz | Parâmetros principais |
|---|---|---|
| `search_jobs` | Busca vagas por título, status, departamento | `query`, `status`, `department`, `limit` |
| `get_job_details` | Detalhes completos de uma vaga + candidatos | `job_id`, `include_candidates` |
| `get_pipeline_stats` | Estatísticas do pipeline da vaga ou de todas | `job_id`, `date_range` |
| `create_job` | Cria nova vaga no banco `[ESCRITA]` | `title`, `description`, `department`, `location`, `salary_range`, `requirements[]` |
| `update_job` | Edita campos de vaga existente `[ESCRITA]` | `job_id`, `fields` |
| `publish_job` | Publica vaga nos canais selecionados `[ESCRITA]` | `job_id`, `channels[]` |
| `save_job_draft` | Salva rascunho da vaga em criação `[ESCRITA]` | `fields`, `draft_id` |
| `validate_job_fields` | Valida campos e detecta informações faltando | `fields` |
| `generate_enriched_jd` | Gera Job Description enriquecida por IA | `fields`, `tone` |
| `search_salary_benchmark` | Busca benchmark salarial por cargo/senioridade/localidade/setor | `job_title`, `seniority`, `location`, `industry` |
| `get_intelligent_salary` | Sugestão inteligente de faixa salarial (mercado + budget) | `job_title`, `seniority`, `location` |
| `get_intelligent_skills` | Sugestão de competências por cargo e senioridade | `job_title`, `seniority`, `industry` |
| `get_job_suggestions` | Sugestões de IA para melhorar a JD | `job_title`, `current_description`, `industry` |

#### [LIA-LLM] Capacidades conversacionais (sem chamada de API)

- **Wizard conversacional de criação** — conduz o recrutador passo a passo coletando: título, área, senioridade, tipo de contrato, faixa salarial, localidade, modelo de trabalho, competências WSI, etapas do processo; uma pergunta por vez com confirmação por seção
- **Linguagem inclusiva e não-discriminatória** — garante que a JD gerada não contenha critérios discriminatórios (idade, estado civil, gênero, origem)
- **Alerta de requisitos restritivos** — avisa se requisitos coletados são excessivamente restritivos (risco de pipeline escasso)
- **Sugestão de etapas do processo** — sugere etapas adequadas ao tipo de cargo (ex: Web Response → Triagem → Teste técnico → Entrevista → Proposta)

#### [v5] Capacidades do domínio `jobs`

| Action | Tipo | O que faz |
|---|---|---|
| `show_job_details` | QUERY | Detalhes completos: título, status, skills, salário, benefícios, requisitos, localidade, modelo |
| `list_jobs` | QUERY | Listagem com filtros e abas: active / urgent / paused / archived / all |
| `pipeline_status` | QUERY | Kanban visual da vaga: etapas com candidatos em cada uma |
| `job_analytics` | ANALYZE | Funil de candidatos, taxas de conversão, gargalos, tempo médio |
| `account_stats` | AGGREGATE | Estatísticas globais de todas as vagas |
| `pipeline_health` | ANALYZE | Saúde de múltiplas vagas: score, gargalos, parados |
| `alerts` | QUERY | Alertas: prazo vencido, urgentes sem finalistas, paradas, sem candidatos |
| `summarize_job` | ANALYZE | Resumo executivo combinando dados + analytics |
| `matching_candidates` | QUERY | Busca candidatos compatíveis via embedding similarity |
| `change_status` | ACTION | Publicar/pausar/fechar/reabrir/arquivar `[ESCRITA]` |
| `copy_job` | ACTION | Duplicar vaga `[ESCRITA]` |
| `bulk_apply_action` | ACTION | Ação em lote no pipeline (mover/rejeitar/aprovar etapa) `[LOTE][ESCRITA]` |
| `export_job` | QUERY | Exportar dados da vaga em CSV |
| `generate_suggestion` | ANALYZE | Sugestões de melhoria para a JD via IA |
| `generate_interview_questions` | ANALYZE | Perguntas de entrevista por competência |
| `auto_source` | ACTION | Inicia sourcing automático de candidatos para a vaga |
| `send_reject_feedback` | ACTION | Envia feedback de rejeição em lote `[ESCRITA]` |

**Detecção de intenção v5 por regex** (`_CONTEXT_ACTION_PATTERNS`):
```
"pipeline|kanban"          → pipeline_status
"analytics|funil|gargalos" → job_analytics
"report|relatório|resumo"  → summarize_job
"alertas"                  → alerts
"estatísticas|stats"       → account_stats
"exportar"                 → export_job
"auto-source"              → auto_source
"saúde do pipeline"        → pipeline_health
```

---

### 3.2 Restrições OUT (LIA — contexto job_management)

| O que NÃO faz | Delegado para |
|---|---|
| Buscar candidatos no pool | Prompt 4 (context_page: "sourcing") |
| Triar CVs de candidatos em uma vaga | Prompt 3 (context_page: "pipeline") |
| Agendar entrevistas | Prompt 3 (context_page: "pipeline") |
| Mover candidatos no pipeline | Prompt 3 (context_page: "pipeline") |
| Comunicação com candidatos | Prompt 3 (context_page: "pipeline") |

---

### 3.3 Dados coletados e gerados

**Inputs (LIA):**
- `context_page: "job"/"jobs"/"vacancies"/"wizard"` — ativa o contexto JOB_TABLE
- `entity_id` — job_id da vaga selecionada
- `job_context` — dados ricos da vaga atual passados pelo frontend

**Inputs (v5):**
- `domain: "jobs"` ou HubPlanner detectando query sobre vagas
- `context_data.job_id` — ID da vaga se disponível

**Outputs:**
- Job Description em Markdown (seções: Sobre a empresa | Responsabilidades | Requisitos | Benefícios)
- Benchmark salarial (min/max por cargo, senioridade, localidade)
- Lista de skills sugeridas com justificativa
- Dados de pipeline por etapa para gráficos no frontend
- Vaga criada/publicada no ATS

---

### 3.4 Arquitetura técnica — LIA

```
Frontend (context_page: "job"|"jobs"|"vacancies"|"wizard")
    ↓
ContextAdapter.from_rest() OU from_job_chat()
    → context_type = "job_management"
    → entity_id = job_id
    → job_context = dados ricos da vaga
    ↓
MainOrchestrator
    → domínio: job_management.yaml
    → scope: JOB_TABLE (13 tools) + GLOBAL (4 tools)
    ↓
Agentes: orchestrator, job_planner, job_intake, job_wizard
```

**Regras do domínio (job_management.yaml):**
- Nunca incluir critérios discriminatórios na JD (idade, estado civil, gênero, origem étnica)
- Confirmar título + senioridade + tipo de contrato antes de salvar definitivamente
- Alertar se requisitos forem excessivamente restritivos (risco de pipeline escasso)
- Sugerir benchmark salarial sempre que disponível para o cargo/região
- Formato wizard: uma pergunta por vez, confirmação ao final de cada seção

---

### 3.5 Arquitetura técnica — v5

```
Frontend (domain: "jobs") OU HubPlanner detecta query sobre vagas
    ↓
JobsDomain (domain_id: "jobs", domain_name: "Gestao de Vagas")
    ↓
JobsPrompts → JobDynamicPromptBuilder
    → PromptConfig(max_actions_in_prompt=8, max_examples_per_action=2)
    → Dois modos:
        • has_job_context=True: prompt enriquecido com detalhes da vaga
        • has_job_context=False: prompt genérico para listagem
    ↓
TieredContextManager (cache por tier):
    • Tier 1: dados básicos (dados + pipeline) — para ações simples
    • Tier 2: dados completos (+ analytics + atividade recente) — para análises
    ↓
JobsAPIClient → ATS Rails API
```

---

### 3.6 Comparativo LIA × v5 — Tabela de Vagas

| Dimensão | LIA (job_management, JOB_TABLE) | v5 (jobs domain) |
|---|---|---|
| **Tools de consulta de vagas** | ✅ `search_jobs`, `get_job_details`, `get_pipeline_stats` | ✅ `list_jobs`, `show_job_details`, `job_analytics`, `account_stats` |
| **Wizard conversacional** | ✅ Estruturado com `save_job_draft` + `validate_job_fields` | ❌ Sem wizard estruturado — cria diretamente via `create_job` |
| **JD gerada por IA** | ✅ `generate_enriched_jd` (tom configurável) | ✅ `generate_suggestion` via API |
| **Benchmark salarial** | ✅ `search_salary_benchmark` + `get_intelligent_salary` | ⚠️ Não tem tool separada para benchmark |
| **Skills sugeridas** | ✅ `get_intelligent_skills` | ✅ `generate_interview_questions` (por competência) |
| **Validação de campos** | ✅ `validate_job_fields` antes de criar | ⚠️ Sem validação pré-save explícita |
| **Kanban/Pipeline visual** | ❌ Não acessível neste contexto (IN_JOB scope) | ✅ `pipeline_status` disponível no domínio jobs |
| **Saúde de múltiplas vagas** | ❌ Sem tool | ✅ `pipeline_health` |
| **Analytics por vaga** | ✅ `get_pipeline_stats` | ✅ `job_analytics` + `summarize_job` |
| **Analytics múltiplas vagas** | ❌ Uma por vez | ✅ `get_multi_job_analytics` em 1 chamada |
| **Alertas de prazo** | ❌ Sem tool no scope | ✅ `alerts` (prazo vencido, urgentes, paradas) |
| **Matching de candidatos** | ❌ Sem tool no scope JOB_TABLE | ✅ `matching_candidates` (embedding similarity) |
| **Sourcing automático** | ❌ Delegado ao domínio sourcing | ✅ `auto_source` direto |
| **Ações em lote** | ❌ No scope JOB_TABLE (apenas individuais) | ✅ `bulk_archive/pause/activate_jobs` |
| **Exportação** | ✅ `generate_report(format: csv/pdf/json)` | ✅ `export_job` (CSV) |
| **Cache de contexto** | ❌ Sem cache | ✅ TieredContextManager (Tier1 vs Tier2) |
| **Detecção de intenção** | Via LLM | ✅ Regex rápido + LLM fallback |
| **Duplicar vaga** | ❌ Sem tool no scope | ✅ `copy_job` |

---

## 4. Prompt 3 — Dentro da Vaga (Kanban) {#prompt-3}

### O que é e onde aparece

O **Prompt Expandido do Kanban** aparece dentro de uma vaga específica (`/user/jobs/{id}`), ao lado do kanban de candidatos. É o contexto mais operacional — age diretamente sobre os candidatos **de uma vaga específica**.

**Ativação:** `context_page: "pipeline"/"kanban"` → `context_type: "pipeline"` → 4 domínios ativos + 6 tools IN_JOB.

---

### 4.1 Capacidades IN

#### [LIA-API] Capacidades via API (scope: IN_JOB — 6 tools)

| Tool | O que faz | Parâmetros principais |
|---|---|---|
| `update_candidate_stage` | Move candidato para etapa do pipeline `[ESCRITA]` | `candidate_id`, `target_stage`, `job_id`, `notes`, `notify_candidate` |
| `reject_candidate` | Rejeita candidato com motivo `[ESCRITA]` | `candidate_id`, `vacancy_id`, `reason`, `notify` |
| `bulk_update_candidates_stage` | Move múltiplos candidatos de etapa `[LOTE][ESCRITA]` | `candidate_ids[]`, `target_stage`, `job_id` |
| `wsi_screening` | Inicia avaliação WSI para um candidato `[ESCRITA]` | `candidate_id`, `job_id`, `screening_type: voice\|text\|video` |
| `hide_candidate` | Oculta candidato da visualização ativa (soft remove) `[ESCRITA]` | `candidate_id`, `vacancy_id`, `reason` |
| `get_vacancy_funnel` | Retorna dados do funil da vaga (candidatos por etapa) | `job_id`, `include_rejected` |

#### [LIA-LLM] Capacidades conversacionais (sem chamada de API)

O LLM tem acesso aos dados de candidatos passados pelo frontend no payload (`candidates[]`, `selected_candidate_ids[]`, `job_context`) e pode:

- **Triagem curricular de CVs** — análise do CV contra os requisitos da vaga via rubrica:
  - Score WSI em 7 blocos: Hard Skills | Soft Skills | Experiência | Liderança | Comunicação | Alinhamento Cultural | Potencial
  - Recomendação: Avançar (≥75%) | Revisão (60-74%) | Rejeitar (<60%)
  - Detecção de red flags: gaps, job hopping, inconsistências de datas
  - Verificação de questões eliminatórias antes da avaliação
- **FairnessGuard** — verifica viés involuntário antes de qualquer rejeição; ignora: nome, foto, localização, estado civil, idade, etnia (via regras do `cv_screening.yaml`)
- **Ranking de candidatos** — ordena candidatos do contexto por score de compatibilidade
- **Comparação de finalistas** — tabela comparativa de candidatos já carregados
- **Análise do pipeline** — identifica gargalos, candidatos parados, taxas de conversão (com dados do funil via `get_vacancy_funnel`)
- **Condução de entrevista WSI (CBI)** — perguntas comportamentais estruturadas, uma por vez; detecta respostas evasivas (via `interview_scheduling.yaml`)
- **Geração de mensagens de comunicação** — rascunha emails, WhatsApp, Teams (via `communication.yaml`)
- **Sugestão de próximas ações** — após cada análise, sugere etapa seguinte para o candidato

**Nota crítica sobre comunicação no contexto IN_JOB:** As tools `send_email` e `send_whatsapp` têm scope TALENT_FUNNEL, não IN_JOB. No contexto do kanban (IN_JOB), a LIA pode **rascunhar e planejar** comunicações via LLM, mas a **execução via API** (envio real) não está disponível neste scope. O envio real de email/WhatsApp requer o contexto TALENT_FUNNEL (Prompt 4) ou que o recrutador execute manualmente.

---

### 4.2 Restrições OUT

| O que NÃO faz (LIA — IN_JOB scope) | Contexto correto |
|---|---|
| Buscar candidatos no pool externo via API | Prompt 4 (TALENT_FUNNEL) |
| Criar ou editar vagas | Prompt 2 (JOB_TABLE) |
| Enviar email/WhatsApp via API | Prompt 4 (TALENT_FUNNEL) — tools `send_email`/`send_whatsapp` estão em TALENT_FUNNEL |
| Buscar candidatos do banco de talentos | Prompt 4 (TALENT_FUNNEL) |
| Overview cross-vagas / briefing geral | Prompt 1 (GLOBAL) |

---

### 4.3 Dados coletados e gerados

**Inputs (LIA):**
- `context_page: "pipeline"/"kanban"` — ativa IN_JOB scope
- `entity_id` = job_id — vaga aberta
- `job_context` — dados da vaga (título, requisitos, etapas, competências WSI)
- `candidates[]` — lista de candidatos carregados na tela (passada pelo frontend)
- `selected_candidate_ids[]` — candidatos selecionados pelo recrutador para ação em lote

**Outputs (LIA-API):**
- Candidato movido de etapa
- Candidato rejeitado (com motivo e notificação opcional)
- Múltiplos candidatos movidos em lote
- Sessão de WSI iniciada (voz, texto ou vídeo)
- Candidato oculto da visualização
- Dados do funil por etapa

**Outputs (LIA-LLM):**
- Score WSI 0-100 por candidato com justificativa para cada bloco
- Recomendação de avanço, revisão ou rejeição
- Ranking de candidatos por compatibilidade
- Rascunho de mensagem de comunicação (para envio manual)
- Análise pós-entrevista (competências + evidências + score parcial)
- Log de auditoria de todas as avaliações (compliance LGPD/SOX — documentado no reasoning)

---

### 4.4 Arquitetura técnica — LIA

```
Frontend (context_page: "pipeline" | "kanban")
    ↓
ContextAdapter
    → context_type = "pipeline"
    → entity_id = job_id
    → candidates = lista de candidatos da tela
    → selected_candidate_ids = selecionados pelo usuário
    ↓
MainOrchestrator
    → domínios ativos (multi-domínio):
        ├── cv_screening.yaml        ← triagem e score WSI (7 blocos + FairnessGuard)
        ├── pipeline_transition.yaml ← movimentação no funil
        ├── interview_scheduling.yaml ← agendamento e condução WSI (CBI)
        └── communication.yaml       ← rascunho de comunicações multi-canal
    → scope: IN_JOB (6 tools) + GLOBAL (4 tools)
    ↓
Agentes: orchestrator, recruiter_assistant, screening, analyst_feedback, communication
```

**Regras críticas por domínio:**
- `cv_screening.yaml`: NUNCA avalia por nome, foto, localização, estado civil, idade, etnia; sempre consulta FairnessGuard antes de rejeitar
- `interview_scheduling.yaml`: perguntas APENAS sobre competências profissionais (nunca família, filhos, estado civil, saúde); consentimento explícito para transcrição de áudio
- `communication.yaml`: todo email gerado inclui rodapé "Mensagem gerada com assistência de IA pela LIA (WeDOTalent)"; confirmação para envios em massa (>10 destinatários)
- `pipeline_transition.yaml`: confirma ações destrutivas ou irreversíveis antes de executar

---

### 4.5 Arquitetura técnica — v5

```
Frontend (domain: "applies") OU HubPlanner detecta query sobre candidaturas
    ↓
AppliesDomain (domain_id: "applies", domain_name: "Gestao de Candidaturas")
    → "Gestao completa de candidaturas: busca, detalhes, pipeline/kanban,
       aprovacao/reprovacao, ranking, comparacao, analytics, acoes em lote.
       Opera no contexto de uma vaga (job_id)."
    ↓
AppliesPrompts → AppliesDynamicPromptBuilder
    → PromptConfig(max_actions_in_prompt=8)
    → Dois modos: has_job_context=True/False
    ↓
AppliesActions (src/domains/applies/actions/):
    analytics.py: apply_analytics | stage_distribution
    bulk.py: bulk_approve_applies | bulk_reject_applies | bulk_move_applies (async) | send_apply_reject_feedback
    comparison.py: compare_candidates
    details.py: show_apply_details | apply_timeline
    pipeline.py: get_kanban | move_stage | approve_apply | reject_apply
    scoring.py: filter_by_score | top_candidates | full_ranking
    search.py: search_applies | search_by_name | list_applies_by_stage | recent_applies | count_applies
    sourcing.py: stalled_applies (por severidade) | diagnose_applies (diagnóstico completo IA)
    ↓
AppliesCacheManager
AppliesAPIClient → ATS Rails API
```

---

### 4.6 Comparativo LIA × v5 — Kanban

| Dimensão | LIA (pipeline context, IN_JOB scope) | v5 (applies domain) |
|---|---|---|
| **Tools de API disponíveis** | 6 tools (IN_JOB) | 10 action files (30+ ações) |
| **Arquitetura** | Multi-domínio (4 YAMLs) | Domínio unificado |
| **Mover candidato de etapa** | ✅ `update_candidate_stage` | ✅ `move_stage` (com confirmação) |
| **Rejeitar candidato** | ✅ `reject_candidate` | ✅ `reject_apply` (com confirmação) |
| **Ações em lote** | ✅ `bulk_update_candidates_stage` | ✅ `bulk_approve/reject/move_applies` (async) |
| **WSI Screening** | ✅ `wsi_screening(voice\|text\|video)` | ⚠️ Via `autonomous` domain (sem domínio dedicado) |
| **Score WSI 7 blocos** | ✅ [LLM] com FairnessGuard explícito | ⚠️ Score via API (sem 7 blocos documentados) |
| **FairnessGuard** | ✅ Verificado antes de toda rejeição | ⚠️ Implícito nas regras gerais |
| **Funil da vaga** | ✅ `get_vacancy_funnel` | ✅ `get_kanban` + `stage_distribution` |
| **Analytics completo** | ❌ Sem tool IN_JOB para analytics | ✅ `apply_analytics` |
| **Candidatos parados** | ❌ Sem tool IN_JOB específica | ✅ `stalled_applies` (attention/warning/critical) |
| **Diagnóstico completo** | ❌ | ✅ `diagnose_applies` com recomendações IA |
| **Top N candidatos** | ❌ Sem tool IN_JOB específica | ✅ `top_candidates`, `full_ranking` |
| **Comparação de candidatos** | [LLM] Com dados em contexto | ✅ `compare_candidates` com análise IA |
| **Timeline da candidatura** | ❌ Sem tool IN_JOB | ✅ `apply_timeline` |
| **Envio de email/WhatsApp** | ❌ Fora do scope IN_JOB | ✅ Via `autonomous` tools |
| **Entrevista WSI estruturada** | ✅ `interview_scheduling.yaml` dedicado | ⚠️ Via `autonomous` domain |
| **Cache de ações** | ❌ | ✅ `AppliesCacheManager` (ACTIONS_NEEDING_CACHE) |

---

## 5. Prompt 4 — Funil de Talentos {#prompt-4}

### O que é e onde aparece

O **Prompt Expandido do Funil de Talentos** aparece na página de candidatos (`/user/candidates`) ou na sessão de sourcing (`/user/sourcing/{id}/chat`). É o prompt especializado em **busca e análise de candidatos** no banco de talentos.

**Ativação:** `context_page: "sourcing"/"talent"` → `context_type: "talent_funnel"` → domínios `sourcing` + `analytics` + scope TALENT_FUNNEL.

---

### 5.1 Capacidades IN

#### [LIA-API] Capacidades via API (scope: TALENT_FUNNEL — 9 tools)

| Tool | O que faz | Parâmetros principais |
|---|---|---|
| `search_candidates` | Busca candidatos no banco por query, filtros, paginação | `query`, `filters`, `limit`, `offset` |
| `get_candidate_details` | Perfil completo de candidato com histórico | `candidate_id`, `include_history` |
| `get_candidate_stats` | Estatísticas agregadas do pool de candidatos | `filters`, `group_by` |
| `add_candidate_to_vacancy` | Adiciona candidato ao processo seletivo de uma vaga `[ESCRITA]` | `candidate_id`, `vacancy_id`, `stage`, `notes` |
| `shortlist_candidate` | Adiciona candidato à lista de pré-selecionados para uma vaga `[ESCRITA]` | `candidate_id`, `vacancy_id`, `notes` |
| `add_to_list` | Inclui candidato em lista de talentos nomeada `[ESCRITA]` | `candidate_id`, `list_name`, `notes` |
| `export_candidates` | Exporta dados de candidatos para CSV ou XLSX | `candidate_ids[]`, `format: csv\|xlsx`, `fields[]` |
| `send_email` | Envia email para um ou mais candidatos `[ESCRITA]` | `to[]`, `subject`, `body`, `template_id` |
| `send_whatsapp` | Envia mensagem WhatsApp para candidato `[ESCRITA]` | `phone`, `message`, `template_name` |

#### [LIA-LLM] Capacidades conversacionais (sem chamada de API)

Com dados de candidatos carregados na tela (via `candidates[]`, `search_context`, `target_job`):

- **Análise de compatibilidade** — calcula score 0-100% de compatibilidade com a vaga alvo para candidatos em contexto
- **Ranking por compatibilidade** — ordena candidatos por fit com a vaga
- **Construção de queries booleanas** — sugere e refina queries `Java AND AWS AND (senior OR pleno) NOT júnior`
- **Análise de disponibilidade de mercado** — interpreta dados de busca para estimar disponibilidade
- **Bias audit / Four-Fifths Rule** — análise de equidade com dados de candidatos em contexto (via `analytics.yaml`)
- **Refinamento de busca** — se < 5 resultados: propõe critérios menos restritivos; se > 50: sugere filtros adicionais
- **Mapeamento de mercado** — tendências de talentos e benchmarking de disponibilidade com dados em contexto

#### [v5] Capacidades do domínio `sourced_profile_sourcing`

| Action | Tipo | O que faz |
|---|---|---|
| `show_candidate_details` | QUERY | Detalhes + análise IA + experiências + skills |
| `search_candidates` | QUERY | Busca por termo, skill ou critério na API |
| `filter_by_skill` | QUERY | Filtra por skill específica |
| `filter_by_score` | QUERY | Lista candidatos com score acima de mínimo |
| `list_candidates` | QUERY | Todos os candidatos com paginação |
| `recent_candidates` | QUERY | Mais recentes |
| `count_candidates` | AGGREGATE | Total de candidatos no sourcing |
| `count_by_filter` | AGGREGATE | Total por filtro específico |
| `average_score` | AGGREGATE | Média + mediana + faixa + acima de 80/90 |
| `score_distribution` | AGGREGATE | Histograma de scores |
| `score_above` | AGGREGATE | Candidatos acima de threshold |
| `top_candidates` | AGGREGATE | Top N por score |
| `priority_ranking` | AGGREGATE | Ranking urgência + fit + disponibilidade |
| `average_experience` | AGGREGATE | Anos de experiência médio |
| `language_distribution` | AGGREGATE | Nível por idioma |
| `education_distribution` | AGGREGATE | Universidades, cursos, nível |
| `gender_distribution` | AGGREGATE | Percentuais por gênero |
| `location_distribution` | AGGREGATE | Por cidade, estado, região |
| `work_model_distribution` | AGGREGATE | Remoto/híbrido/presencial |
| `compare_candidates` | ANALYZE | Comparação lado a lado com análise IA |
| `summarize_search` | ANALYZE | Relatório completo: demográfico, scores, localização, skills, diversidade |
| `generate_executive_report` | ANALYZE | Relatório executivo (pipeline 4 etapas: planning→collection→analysis→formatting) |
| `generate_top_candidates_report` | ANALYZE | Relatório detalhado dos melhores perfis |
| `diversity_analysis` | ANALYZE | Four-Fifths Rule por dimensão (gênero, PCD, idade, região) |
| `analyze_skills` | ANALYZE | Distribuição e profundidade de competências |
| `common_strengths` | ANALYZE | Pontos fortes comuns do pool |
| `skill_gaps` | ANALYZE | Lacunas vs. requisitos da vaga |
| `candidates_to_discard` | ANALYZE | Perfis claramente fora do critério |
| `needs_screening` | ANALYZE | Perfis na zona de dúvida (precisam de triagem) |
| `top_by_experience` | ANALYZE | Top por anos/qualidade de experiência |
| `analyze_search_improvement` | ANALYZE | Por que pool está fraco + como melhorar |
| `approve_candidate` | ACTION | Aprovar no sourcing `[ESCRITA]` |
| `reject_candidate` | ACTION | Rejeitar do pool `[ESCRITA]` |
| `add_rating` | ACTION | Rating + nota ao perfil sourced `[ESCRITA]` |

**StatsManager (cache de stats agregadas):**
O v5 usa `ACTIONS_USING_AGGREGATED` — frozenset de 26 ações que pré-carregam estatísticas agregadas do pool (evita N+1 chamadas para análises demográficas e de scoring).

---

### 5.2 Restrições OUT

| O que NÃO faz (LIA — TALENT_FUNNEL scope) | Contexto correto |
|---|---|
| Triagem de CVs com score WSI completo | Prompt 3 (IN_JOB) |
| Agendar entrevistas | Prompt 3 (IN_JOB) |
| Mover candidatos no pipeline de uma vaga específica | Prompt 3 (IN_JOB) |
| Criar vagas | Prompt 2 (JOB_TABLE) |
| Briefing geral / agenda do dia | Prompt 1 (GLOBAL) |

---

### 5.3 Dados coletados e gerados

**Inputs (LIA):**
- `context_page: "sourcing"/"talent"` — ativa TALENT_FUNNEL scope
- `entity_id` = `sourcing_id` — ID da sessão de sourcing ativa
- `entity_type: "sourcing"`
- `candidates[]` — candidatos do resultado de busca atual (carregados na tela)
- `selected_candidate_ids[]` — candidatos selecionados pelo recrutador
- `search_context` — configurações da busca (query, filtros aplicados)
- `target_job` — vaga-alvo para cálculo de score de compatibilidade

**Inputs (v5):**
- `domain: "sourced_profile_sourcing"` + `context_data.sourcing_id`
- `total_candidates` + `aggregated_stats` injetados no prompt (via StatsManager)

**Outputs:**
- Lista de candidatos com score de compatibilidade e justificativa
- Relatório executivo de sourcing (Markdown estruturado)
- Análise de diversidade com métricas Four-Fifths Rule
- Candidatos exportados em CSV/XLSX
- Candidatos adicionados a vaga / lista / shortlist

---

### 5.4 Arquitetura técnica — LIA

```
Frontend (context_page: "sourcing" | "talent")
    ↓
ContextAdapter.from_talent_chat() OU from_rest()
    → context_type = "talent_funnel"
    → entity_id = sourcing_id
    → entity_type = "sourcing"
    → candidates = candidatos da tela
    → search_context = configuração da busca
    → target_job = vaga alvo (se existir)
    ↓
MainOrchestrator
    → domínios ativos:
        ├── sourcing.yaml   ← busca de talentos + Pearch AI
        └── analytics.yaml  ← KPIs, relatórios, bias audit
    → scope: TALENT_FUNNEL (9 tools) + GLOBAL (4 tools)
    ↓
Agentes: orchestrator, recruiter_assistant, sourcing, analytics
```

**Regras do domínio `sourcing.yaml`:**
- Score de compatibilidade sempre apresentado com justificativa
- Nunca inferir gênero, etnia, idade a partir de nome ou localização
- Se < 5 resultados: propõe automaticamente critérios menos restritivos
- Se > 50 resultados: pergunta se deseja filtro adicional
- Sempre cita a fonte: banco interno vs. Pearch AI vs. externo

**Regras do domínio `analytics.yaml`:**
- Dados sempre agregados (LGPD-safe) — sem identificação individual em relatórios
- Destaca anomalias com contexto + recomendação de ação
- Quando amostra < 30 registros: indica baixa confiabilidade estatística
- Compara com benchmark setorial quando disponível

---

### 5.5 Arquitetura técnica — v5

```
Frontend (domain: "sourced_profile_sourcing") OU HubPlanner detecta query sobre candidatos
    ↓
SourcedProfileSourcingDomain
    → "Análise e ações sobre perfis de candidatos vinculados a um sourcing específico.
       Sempre requer sourcing_id no contexto."
    ↓
SourcedProfileSourcingPrompts → DynamicPromptBuilder
    → USE_DYNAMIC_BUILDER = env var (padrão: true)
    → PromptConfig(max_actions_in_prompt=6, enable_cache=True)
    → Injeta total_candidates + aggregated_stats no prompt dinamicamente
    ↓
StatsManager
    → Pré-computa stats agregadas para ACTIONS_USING_AGGREGATED (26 ações)
    → Evita N chamadas à API para análises demográficas
    ↓
SourcingAPIClient → ATS Rails API
```

**Pipeline de relatório executivo (report.py):**
```
generate_executive_report:
  1. report_planning    → define estrutura e métricas a coletar
  2. report_data_collection → coleta dados da API
  3. report_analysis    → análise LLM (temperature=0.3)
  4. report_formatting  → formata relatório + dados de gráficos
```

---

### 5.6 Comparativo LIA × v5 — Funil de Talentos

| Dimensão | LIA (talent_funnel, TALENT_FUNNEL scope) | v5 (sourced_profile_sourcing domain) |
|---|---|---|
| **Tools de busca de candidatos** | ✅ `search_candidates`, `get_candidate_details`, `get_candidate_stats` | ✅ `search_candidates`, `filter_by_skill`, `filter_by_score`, `list_candidates` |
| **Busca híbrida ES + embeddings** | ⚠️ Não documentada como separada | ✅ `search_candidates_hybrid` (70% ES + 30% embeddings) |
| **Pearch AI (190M+ perfis)** | ✅ Documentado no `sourcing.yaml` | ⚠️ Não documentado como tool explícita no domínio |
| **Candidatos similares** | ⚠️ Não como tool explícita no scope | ✅ Via scoring por embedding + `find_similar_candidates` no autonomous |
| **Queries booleanas** | [LLM] Suportado conversacionalmente | ⚠️ Suportado via busca mas sem tool dedicada |
| **Score de compatibilidade** | [LLM] 0-100% com justificativa | ✅ Score calculado via API + `average_score`, `score_distribution` |
| **Análise demográfica** | ✅ Via `analytics.yaml` [LLM] | ✅ 5 distribution actions (language/education/gender/location/work_model) |
| **Bias audit (Four-Fifths Rule)** | ✅ `analytics.yaml` [LLM] | ✅ `diversity_analysis` (action dedicada) |
| **Cache de stats agregadas** | ❌ | ✅ `StatsManager` + `ACTIONS_USING_AGGREGATED` |
| **Relatório executivo** | ✅ `generate_report` (GLOBAL) | ✅ `generate_executive_report` (4-step pipeline) |
| **Análise de melhoria de busca** | ⚠️ Sugerida no system prompt [LLM] | ✅ `analyze_search_improvement` (action dedicada) |
| **Skill gaps** | [LLM] Com dados em contexto | ✅ `skill_gaps` (action dedicada) |
| **Candidatos para descartar** | [LLM] | ✅ `candidates_to_discard` (action dedicada) |
| **Adicionar candidato a vaga** | ✅ `add_candidate_to_vacancy` | ✅ Via `autonomous` (`create_apply`) |
| **Shortlist** | ✅ `shortlist_candidate` | ✅ Via `autonomous` (`add_to_list`) |
| **Exportação** | ✅ `export_candidates(csv/xlsx)` | ✅ Via `autonomous` tools |
| **Envio de email** | ✅ `send_email` | ✅ Via `autonomous` (`send_apply_reject_feedback`) |
| **Envio de WhatsApp** | ✅ `send_whatsapp` | ✅ Via `autonomous` tools |
| **Arquetipos de busca** | ❌ | ✅ `search_archetypes` (via autonomous) |
| **Comparação de sourcings** | ❌ Um por vez | ✅ `get_multi_sourcing_stats` (bulk) |
| **Aprovação de perfil sourced** | ⚠️ Sem tool explícita no scope | ✅ `approve_candidate`, `reject_candidate`, `add_rating` |

---

## 6. Tabela-resumo global {#tabela-resumo}

| Dimensão | Prompt 1 — Flutuante | Prompt 2 — Tabela Vagas | Prompt 3 — Kanban | Prompt 4 — Funil Talentos |
|---|---|---|---|---|
| **context_page (LIA)** | `general` | `job`, `jobs`, `vacancies`, `wizard` | `pipeline`, `kanban` | `sourcing`, `talent` |
| **domain payload (v5)** | `null` + hub_mode | `"jobs"` | `"applies"` | `"sourced_profile_sourcing"` |
| **N° tools LIA (scope)** | **4** GLOBAL | **13** JOB_TABLE | **6** IN_JOB | **9** TALENT_FUNNEL |
| **N° actions v5** | 73+ (13 módulos) | 17 (7 action files) | 30+ (10 action files) | 32+ (14 action files) |
| **Buscar vagas via API** | ❌ LIA | ✅ Ambos | ❌ LIA | ❌ LIA |
| **Buscar candidatos via API** | ❌ LIA | ❌ LIA | ❌ LIA | ✅ Ambos |
| **Mover candidatos via API** | ❌ LIA | ❌ LIA | ✅ Ambos | ❌ LIA |
| **Enviar email/WhatsApp via API** | ❌ LIA | ❌ Ambos | ❌ LIA (está em TALENT_FUNNEL) | ✅ Ambos |
| **Score WSI 7 blocos** | ❌ | ❌ | ✅ LIA [LLM] | ❌ |
| **FairnessGuard** | ❌ | ❌ | ✅ LIA [LLM] | ❌ |
| **Bias audit** | ❌ | ❌ | ❌ | ✅ Ambos |
| **Gerar relatório** | ✅ Ambos | ✅ Ambos | ❌ LIA | ✅ Ambos |
| **Agendar relatório recorrente** | ✅ LIA apenas | ❌ | ❌ | ❌ |
| **Wizard de criação de vaga** | ❌ | ✅ LIA [LLM] | ❌ | ❌ |
| **JD gerada por IA** | ❌ | ✅ Ambos | ❌ | ❌ |
| **Analytics de vaga** | ❌ LIA | ✅ Ambos | ✅ v5 | ❌ |
| **Diagnóstico completo** | ❌ LIA | ❌ LIA | ✅ v5 | ❌ |
| **Progresso visível (write_plan)** | ✅ v5 | ✅ v5 | ✅ v5 | ✅ v5 |
| **Streaming SSE** | ✅ v5 | ✅ v5 | ✅ v5 | ✅ v5 |
| **Cache otimizado** | ❌ LIA | ✅ v5 (Tier1/Tier2) | ✅ v5 (AppliesCacheManager) | ✅ v5 (StatsManager) |
| **LGPD compliance** | ✅ Ambos | ✅ Ambos | ✅ Ambos | ✅ Ambos |

---

## 7. Glossário técnico {#glossario}

| Termo | Definição |
|---|---|
| **context_page** | Campo enviado pelo frontend junto com cada mensagem. Determina qual domínio/scope LIA será ativado. |
| **context_type** | Tipo normalizado de contexto, mapeado pelo `ContextAdapter` a partir do `context_page`. |
| **domain payload** | Campo `domain` no payload `POST /chat` do v5. Determina qual domínio Python processar a requisição. |
| **scope** | Conjunto de tools disponíveis para o LLM em um determinado contexto de página. Definido no `tool_registry_metadata.yaml`. |
| **hub_mode** | Flag do v5 que ativa o HubPlanner para roteamento inteligente via LLM + regex. |
| **HubPlanner** | Componente v5 que analisa a query e decide qual(is) domínio(s) usar, em paralelo ou sequencial. |
| **HubExecutionPlan** | Plano de execução v5: lista de `HubTask[]`, `TaskStrategy`, `NavigationAction[]`, `reasoning`. |
| **DomainContext** | Objeto de contexto compartilhado no v5: `workspace_id`, `sourcing_id`, `selected_ids`, `conversation_memory`, `auth_token`, `api_calls_history`. |
| **DomainAction** | Ação definida em cada domínio v5: `id`, `name`, `description`, `ActionType`, `examples[]`, `requires_confirmation`. |
| **ActionType** | Enum v5: `QUERY` (consulta), `AGGREGATE` (agrega), `ANALYZE` (analisa com IA), `ACTION` (modifica dados). |
| **[LIA-API]** | Capacidade da LIA que faz chamada real à API via tool do scope ativo. |
| **[LIA-LLM]** | Capacidade da LIA executada conversacionalmente pelo LLM sem chamada de API (depende de dados em contexto). |
| **[v5]** | Capacidade do recruiter_agent_v5 no GitHub WeDOTalent. |
| **WSI** | Workforce Screening Interview — avaliação em 7 blocos: Hard Skills, Soft Skills, Experiência, Liderança, Comunicação, Alinhamento Cultural, Potencial. |
| **FairnessGuard** | Camada de verificação de viés da LIA executada antes de rejeições. Ignora: nome, foto, localização, estado civil, idade, etnia. |
| **Four-Fifths Rule** | Regra de equidade: se taxa de aprovação de um grupo for <80% da taxa do grupo mais aprovado, há evidência de disparidade sistemática. |
| **Pearch AI** | Plataforma de sourcing externo integrada à LIA (190M+ perfis globais). |
| **write_plan** | Tool v5 que cria plano de execução visível ao usuário em tempo real: ⬜ pendente → 🔄 em andamento → ✅ concluído. |
| **StatsManager** | Componente v5 que pré-computa e cacheia estatísticas agregadas do sourcing para as 26 ações em `ACTIONS_USING_AGGREGATED`. |
| **TieredContextManager** | Cache v5 do domínio `jobs`: Tier1 (dados básicos) e Tier2 (dados completos + analytics). |
| **IDOR** | Insecure Direct Object Reference — vulnerabilidade prevenida pelo `ContextAdapter.validate_entity_ownership()` na LIA. |
| **CBI** | Competency-Based Interview — metodologia de entrevista estruturada por competências e evidências comportamentais (usada nas entrevistas WSI). |
| **MULTI_INTENT_RE** | Regex do v5 que detecta queries com múltiplas intenções, gerando HubTasks executadas em paralelo. |
| **viewing_entities** | Campo v5 enviado pelo frontend com entidades visíveis na tela atual (job_id, candidate_id). Permite resolução de referências implícitas. |
| **NavigationAction** | Ação v5 que instrui o frontend a navegar para uma URL específica sem recarregar. |
| **UniversalContext** | Objeto de contexto normalizado da LIA que o MainOrchestrator consome — abstrai REST, WebSocket e RabbitMQ. |
| **SSE** | Server-Sent Events — streaming unidirecional servidor→cliente. O v5 expõe `/chat/stream` com SSE nativo. |
| **SLA** | Prazo acordado para execução em uma etapa. Candidatos além do SLA: attention (7d) / warning (14d) / critical (30d+). |

---

*Documento gerado a partir da leitura do código `lia-agent-system/` (local) e `WeDOTalent/recruiter_agent_v5` (GitHub) em Março/2026.*

*Fontes LIA: `context_adapter.py`, `tool_registry_metadata.yaml`, `recruiter_assistant.yaml`, `job_management.yaml`, `cv_screening.yaml`, `pipeline_transition.yaml`, `interview_scheduling.yaml`, `communication.yaml`, `sourcing.yaml`, `analytics.yaml`, `automation.yaml`, `interaction_patterns.py`*

*Fontes v5 (GitHub): `hub/catalog.py`, `hub/planner.py`, `domains/base.py`, `domains/autonomous/prompts.py`, `domains/autonomous/tools/*.py`, `domains/jobs/domain.py`, `domains/applies/domain.py` + `actions/*.py`, `domains/sourced_profile_sourcing/domain.py` + `actions/*.py`*

*Para atualizar: reler `context_adapter.py` (PAGE_TO_CONTEXT_TYPE), `tool_registry_metadata.yaml` (scope por tool), YAMLs de domínios LIA, e os `domain.py` + `actions/*.py` do v5.*
