# Mapeamento de Capacidades dos Prompts da LIA × v5

**Versão:** 5.0 | **Data:** Março/2026 | **Autoria:** Análise de código LIA local + recruiter_agent_v5 (GitHub WeDOTalent)

---

## Como ler este documento

Este documento mapeia os 4 contextos de prompt da plataforma LIA **com dados paralelos do v5 em cada seção**, com base em **leitura direta do código**:

| Tag | Significado |
|---|---|
| **[LIA-API]** | Chamada real à API via tool registrada (scope ativo) |
| **[LIA-LLM]** | Capacidade conversacional do LLM (dados já em contexto da conversa, sem chamada de API) |
| **[v5]** | Capacidade equivalente no recruiter_agent_v5 (GitHub WeDOTalent) |
| `[ESCRITA]` | Ação que modifica dados — requer confirmação do usuário |
| `[LOTE]` | Ação em massa sobre múltiplos registros |

**Sobre os dois registros de tools LIA:**
- `tool_registry_metadata.yaml` — fonte declarativa com scope por tool (usado pelo `tool_registry_loader.py` para metadados e pelo task spec desta análise)
- `app/tools/scope_config.py` — fonte executável de runtime (`filter_tools_by_scope()` filtra tools por scope no `Orchestrator.get_tools_for_context()`)

Os dois registros têm diferenças. Este documento usa o `tool_registry_metadata.yaml` como fonte primária de tools por contexto (alinhado ao task spec), mencionando divergências relevantes de `scope_config.py` onde aplicável.

---

## Índice

1. [Visão Geral — os 4 contextos](#visao-geral)
2. [Arquitetura de roteamento LIA × v5](#roteamento)
3. [Prompt 1 — Flutuante / Global](#prompt-1)
4. [Prompt 2 — Tabela de Vagas](#prompt-2)
5. [Prompt 3 — Dentro da Vaga (Kanban)](#prompt-3)
6. [Prompt 4 — Funil de Talentos](#prompt-4)
7. [Tabela-resumo global (4 prompts × 10 dimensões)](#tabela-resumo)
8. [Domínios v5 exclusivos (Scheduling, Insights, Evaluation)](#dominios-v5-exclusivos)
9. [Canal Microsoft Teams — Notificações e Interação](#teams)
10. [Glossário técnico](#glossario)

---

## 1. Visão Geral — os 4 contextos {#visao-geral}

**LIA** (`lia-agent-system/app/orchestrator/context_adapter.py` → `PAGE_TO_CONTEXT_TYPE`):

| Página da UI | context_page | context_type | Domínios YAML | Scope de tools |
|---|---|---|---|---|
| Chat flutuante (todas as páginas) | `general`, `global` | `general` | `recruiter_assistant` | GLOBAL (4 tools) |
| `/user/jobs`, wizard de vaga | `job`, `jobs`, `vacancies`, `wizard` | `job_management` | `job_management` | JOB_TABLE (13 tools) |
| `/user/jobs/{id}` (kanban) | `pipeline`, `kanban` | `pipeline` | `cv_screening` + `pipeline_transition` + `interview_scheduling` + `communication` | IN_JOB (6 tools) |
| `/user/candidates`, `/user/sourcing/{id}` | `sourcing`, `talent` | `talent_funnel` | `sourcing` + `analytics` | TALENT_FUNNEL (9 tools) |

**v5** (`src/api.py` → `ChatRequest.domain`, `src/hub/catalog.py` → `NAVIGATION_ROUTES`):

| Rota da UI | domain | Domínio v5 | Action files |
|---|---|---|---|
| `/user/lia` (chat global) | `null` + `hub_mode: true` | `autonomous` | 13 módulos de tools, 73+ tools |
| `/user/jobs` | `"jobs"` | `jobs` | analytics, base, conversational, matching, mutations, query, suggestions |
| `/user/jobs/{id}` | `"applies"` | `applies` | analytics, base, bulk, comparison, conversational, details, pipeline, scoring, search, sourcing |
| `/user/candidates`, `/user/sourcing/{id}/chat` | `"sourced_profile_sourcing"` | `sourced_profile_sourcing` | analysis, comparison, count, details, distribution, feedback, insights, report, score, search, search_improvement |

**Domínios v5 adicionais (sem equivalente direto nos 4 prompts LIA):**

| domain_id | domain_name | Responsabilidade |
|---|---|---|
| `scheduling` | Agendamento de Entrevistas | Agendar, remarcar, cancelar entrevistas; self-scheduling (link); agenda diária |
| `insights` | Insights e Analytics | Briefing diário, report de vaga, métricas, alertas, tendências, resumo semanal |
| `evaluation` | Avaliação de Candidatos | Avalia respostas de candidatos em entrevistas via LangGraph |
| `autonomous` | Agente Autônomo Universal | ReAct agent com 73+ tools para queries cross-domain e operações complexas |

---

## 2. Arquitetura de roteamento LIA × v5 {#roteamento}

### 2.1 Arquitetura de roteamento — LIA

A LIA usa **dois sistemas de roteamento independentes** que coexistem:

#### Sistema A — Scope de tools (por context_page do frontend)

- Determina quais API tools o LLM pode chamar
- Baseado no `context_page` enviado pelo frontend → normalizado para `context_type` → mapeado para `PromptScope`
- Implementado em `app/tools/scope_config.py`: `filter_tools_by_scope()` filtra por scope no `Orchestrator.get_tools_for_context()` (`orchestrator.py`, linha 313)
- Os scopes são mutuamente exclusivos (sem union de scopes em runtime)

#### Sistema B — Domain routing (por conteúdo da mensagem)

- Determina qual domínio Python (`domain_id`) processa a ação
- Baseado no **conteúdo da mensagem**, independente do context_page
- Implementado no `CascadedRouter` (`cascaded_router.py`) com 6 tiers em custo crescente:

```
Tier 0: MemoryResolver    — pronomes/referências de contexto ("ele", "esse candidato")
Tier 1: LRU in-process   — hash MD5, O(1), cache local de sessão
Tier 2: Redis cache      — distribuído, compartilhado entre workers
Tier 3: VectorSemanticCache — pgvector, cosine similarity ≥ 0.92
Tier 4: FastRouter       — regex/keyword patterns, O(n)
Tier 5: LLM Cascade      — Haiku → Sonnet → Opus (custo crescente)
Fallback: clarification  — pergunta ao usuário quando tudo falha
```

#### Fluxo MainOrchestrator (`main_orchestrator.py`)

```
MENSAGEM RECEBIDA (UniversalContext via ContextAdapter)
    │
    ├─ FairnessGuard.check() ←── bloqueia inputs discriminatórios ANTES de processar
    │
    ├─ Phase 0: PendingActionState ←── ação aguardando confirmação multi-turn
    │
    ├─ Phase 1: ActionExecutor ←── ações detectadas por padrão fechado
    │
    └─ Phase 2: Orchestrator.process_request_with_memory()
              │
              ├─ CascadedRouter.route() → domain_id (por conteúdo da mensagem)
              │
              ├─ PolicyEngine.validate_request() → allowed / blocked
              │
              ├─ PlanDetector → se multi-step, PlanExecutor.execute()
              │
              └─ DomainWorkflow.process(domain_id, context)
                       │
                       └─ [domain=None] → _handle_directly() com LLM direto
```

---

### 2.2 Arquitetura de roteamento — v5

O v5 usa **MessageRouter** (`src/services/message_router.py`) como entry point único, com **3 caminhos de roteamento** distintos baseados nos campos `hub_mode` e `domain` da `ChatRequest`:

#### 3 caminhos do MessageRouter

```
POST /chat (sync) ou /chat/stream (SSE)
    │
    ├─ configure_ott_from_message(message)  ←── OTT: auth token para callbacks
    │
    ├─ hub_mode=True?
    │     └─ HubOrchestrator.process(query, context_data)
    │
    ├─ domain="jobs"|"applies"|"sourced_profile_sourcing"|"scheduling"|etc?
    │     └─ DomainOrchestrator.process_query(domain_id, query, context_data)
    │
    └─ domain=None, hub_mode=False?
          └─ workflow_orchestrator.process_query(query)
                (LangGraph workflow — fallback global sem session management)
    │
    └─ get_token_for_callback() → OTT adicionado ao response (auth_token)
    └─ RequestTimer.finish() → timing report adicionado ao response
```

#### HubOrchestrator (hub_mode=True) — fluxo completo

```
HubOrchestrator.process(query, context_data)
    │
    ├─ safe_process_input(query) ←── SecurityService: detecta injeção de prompt
    │     is_injection=True → retorna INJECTION_RESPONSE (bloqueio imediato)
    │
    ├─ SessionStore.get_or_create(session_id)
    │     ├─ MAX_HISTORY=50 turns por sessão
    │     ├─ active_context: {job_id, apply_id, candidate_id, sourcing_id,
    │     │                    job_title, candidate_name, candidate_email}
    │     ├─ domain_memories: dict por domain_id
    │     └─ pending_action: PendingAction | None
    │
    ├─ _hydrate_session_from_history(recent_messages) ←── se sessão nova
    │
    ├─ _apply_page_context(context_data, session) ←── injeta contexto de página
    │
    ├─ session.has_pending_action()?
    │     ├─ Sim + respondendo: _resolve_pending_action()
    │     └─ Sim + abandono: clear + nova query
    │
    ├─ _has_active_scheduling_session() + _is_scheduling_continuation()?
    │     └─ Sim: _route_to_scheduling() (bypass do HubPlanner)
    │
    └─ _execute_new_query(session, query, context_data)
          │
          ├─ HubPlanner.plan(query) → HubExecutionPlan
          │     ├─ FAST_NAV_PATTERNS (12 regex, sem LLM) → NavigationAction direto
          │     ├─ _JOB_ID_PATTERN: "vaga 42" → NAVIGATE /user/jobs/42
          │     ├─ _CANDIDATE_ID_PATTERN: "candidato 91" → NAVIGATE /user/candidates/91
          │     ├─ _CANDIDATE_SEARCH_RE: busca de candidatos → pipeline candidate_search
          │     ├─ MULTI_INTENT_RE: 2+ intenções → HubTask[] em paralelo
          │     └─ LLM (PLANNER_SYSTEM_PROMPT) → HubExecutionPlan { tasks[], strategy }
          │
          ├─ HubExecutor.execute(plan, base_context)
          │     ├─ Itera HubTask[] sequencialmente (ou paralelo se strategy=PARALLEL)
          │     ├─ _execute_fan_out_task() se task.iterate_over != None
          │     │     → itera sobre lista de resultados de task anterior
          │     ├─ task.needs_clarification? → HubResult(pending_action_data)
          │     │     → session.set_pending_action(PendingAction)
          │     ├─ task falhou + domain não em _FALLBACK_SKIP_DOMAINS?
          │     │     → _try_autonomous_fallback(task) → retenta com autonomous
          │     └─ HubContextManager.store_result(output_key, result)
          │           → resolve_context(depends_on) para tasks com dependência
          │
          ├─ _extract_context_from_results(result, session)
          │     ← extrai: job_id, apply_id, candidate_id, sourcing_id,
          │               job_title, candidate_name, candidate_email
          │
          └─ SessionStore.save(session)
```

#### SupervisorGraph — LangGraph (USE_SUPERVISOR=False por padrão)

O v5 tem um **segundo orchestrator** baseado em LangGraph StateGraph, controlado pela flag `USE_SUPERVISOR`:

```python
USE_SUPERVISOR = False  # src/hub/orchestrator.py — HubPlanner é o padrão atual
```

Quando `USE_SUPERVISOR=True`:

```
SupervisorGraph (src/hub/supervisor_graph.py)
    │
    ├─ _keyword_fallback(query) ←── ROUTING_KEYWORDS por domínio (regex)
    │     jobs:                    /\b(?:vaga|vagas|job|criar\s+vaga)\b/
    │     applies:                 /\b(?:candidatura|pipeline|kanban|mover|etapa)\b/
    │     sourced_profile_sourcing:/\b(?:sourcing|buscar?\s+candidat|perfil)\b/
    │     scheduling:             /\b(?:agendar?|entrevist|horário|disponibilidade)\b/
    │     evaluation:             /\b(?:avali[aç]|teste|prova|questionário)\b/
    │     autonomous:             /\b(?:departamento|beneficio|aprovac\w+|notifica\w+)\b/
    │
    ├─ LLM (SUPERVISOR_SYSTEM_PROMPT) → next_domain + planned_domains + reasoning
    │
    ├─ MAX_ITERATIONS=3 ←── limite de iterações do supervisor
    │
    └─ StateGraph:
          supervisor_node → domain_agent_node → supervisor_node (até MAX_ITERATIONS)
                                      │
                                      ├─ completed_domains.append(domain_id)
                                      └─ planned_domains: multi-domain planning
```

**6 domínios registrados no SupervisorGraph** (via `DomainRegistry.list_domains()`):

| domain_id | Responsabilidade no supervisor |
|---|---|
| `jobs` | Vagas: criar, listar, editar, pausar, arquivar, duplicar |
| `applies` | Candidaturas: pipeline, mover, aprovar, rejeitar, avaliar |
| `sourced_profile_sourcing` | Sourcing: buscar por habilidades, experiência, localização |
| `scheduling` | Entrevistas: agendar, remarcar, cancelar, disponibilidade |
| `evaluation` | Avaliações: criar, enviar, ver resultados |
| `autonomous` | Universal: cross-domain, entidades não cobertas pelos especializados |

#### OTT — One-Time Token

```
configure_ott_from_message(message) → armazena OTT para callbacks
get_token_for_callback()            → recupera OTT e adiciona ao response (auth_token)

Fluxo:
  Frontend envia one_time_token no payload
  MessageRouter lê + configura no contexto
  API v5 adiciona auth_token no response para callback do frontend
```

---

### 2.3 Comparativo de arquitetura de roteamento LIA × v5

| Dimensão | LIA | v5 |
|---|---|---|
| **Entry point** | `MainOrchestrator.process()` | `MessageRouter.route()` |
| **Proteção anti-injeção** | `FairnessGuard.check()` antes de processar | `safe_process_input()` no HubOrchestrator |
| **Routing por intenção** | `CascadedRouter` (6 tiers: MD5→Redis→pgvector→regex→LLM) | `HubPlanner` (regex rápido + LLM) |
| **Caminhos de roteamento** | 2 (scope de tools + domain routing) | 3 (hub_mode / domain / global) |
| **Multi-agent** | LangGraph implícito via DomainWorkflow | LangGraph explícito (SupervisorGraph, flag=False) |
| **Session management** | `ConversationMemory` + `PendingActionState` | `SessionStore` + `ConversationSession` (MAX_HISTORY=50) |
| **PendingAction (multi-turn)** | `PendingActionState` (Phase 0) | `PendingAction` (SELECT_OPTION / PROVIDE_INFO / CONFIRM) |
| **Resolução de contexto** | Tier 0 CascadedRouter (pronomes) | `active_context` + `domain_memories` por domínio |
| **Fan-out em listas** | `PlanExecutor` (multi-step) | `_execute_fan_out_task()` (iterate_over) |
| **Fallback automático** | Clarification request | Autonomous fallback + clarification |
| **Auth token** | Entity ownership validation (IDOR) | OTT (One-Time Token) para callbacks |
| **Streaming** | WebSocket | SSE nativo (`/chat/stream`) com `EventSourceResponse` |
| **Timeout de request** | Não documentado | 200s (SSE timeout) |
| **Timing** | Não documentado | `RequestTimer` com steps por fase |

---

## 3. Prompt 1 — Flutuante / Global {#prompt-1}

### 3.0 Introdução

O **Prompt Flutuante** aparece como ícone de chat em **todas as páginas** da plataforma. É o copiloto de recrutamento pessoal do recrutador — ativado sem precisar navegar para nenhuma tela específica.

**Ativação LIA:** `context_page: "general"/"global"` → `context_type: "general"` → domínio `recruiter_assistant.yaml` → scope GLOBAL.

**Ativação v5:** `domain: null` + `hub_mode: true` → `HubOrchestrator` → `HubPlanner` → `autonomous` domain (73+ tools em 13 módulos).

**Para que serve:** planejamento do dia, relatórios gerais, configurações da empresa, feedback sobre o wizard de vagas, perguntas gerais sobre processos de RH, briefings e insights baseados em dados já mencionados na conversa.

**Para que NÃO serve (LIA):** qualquer ação que exija acesso ao banco de dados via API (buscar candidatos, criar vagas, mover candidaturas, enviar comunicações). Para essas ações, o usuário deve navegar à página correspondente.

**v5: não existe essa restrição** — o `autonomous` domain tem acesso a 73+ tools e pode executar qualquer operação independente de página.

**Nota sobre roteamento LIA:** mesmo quando o recrutador usa o chat flutuante, o CascadedRouter pode detectar a intenção da mensagem e rotear para domínios especializados (job_management, cv_screening, etc.). Nesses casos, o domínio processa via DomainWorkflow, mas as tools de API disponíveis permanecem as do scope GLOBAL.

---

### 3.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: GLOBAL — 4 tools, fonte: tool_registry_metadata.yaml)

| Tool | O que faz | Parâmetros principais | v5 equivalente |
|---|---|---|---|
| `get_company_config` | Obtém configurações da empresa: workflow de contratação, aprovações, configurações de sistema | `config_type` | `discover_api` + `call_api` (via autonomous) |
| `generate_report` | Gera relatório de analytics para período e tipo definidos | `report_type`, `date_from`, `date_to`, `format: pdf\|csv\|json` | `daily_briefing_complete` / `job_report_complete` (autonomous) |
| `schedule_report` | Agenda relatório recorrente enviado automaticamente | `report_type`, `schedule` (cron), `recipients[]` | ❌ Sem equivalente direto |
| `capture_wizard_feedback` | Registra feedback do recrutador sobre experiência com o wizard de criação de vagas | `feedback_type`, `rating`, `comment` | ❌ Sem equivalente direto |

**Nota sobre divergência de fontes:** `app/tools/scope_config.py` (runtime enforcement — `SCOPE_TOOL_MAPPING`, usado por `filter_tools_by_scope()` em `orchestrator.py` linha 313) lista GLOBAL com apenas 2 tools: `generate_report` e `schedule_report`. `tool_registry_metadata.yaml` lista 4. Verificando o código Python das tools: `get_company_config` e `capture_wizard_feedback` estão declaradas no YAML como scope GLOBAL, mas ausentes do `SCOPE_TOOL_MAPPING` em `scope_config.py` — o que significa que `filter_tools_by_scope(GLOBAL)` **não** as retorna em runtime. A fonte executável é `scope_config.py`; o YAML tem precedência apenas para metadados (description, version).

#### [v5] Tools disponíveis no modo global (autonomous domain — 73+ tools em 13 módulos)

**Módulos de tools do autonomous domain** (`src/domains/autonomous/tools/`):

| Módulo | Tools principais | Capacidade |
|---|---|---|
| `jobs.py` | `get_all_jobs_stats`, `search_jobs`, `get_job_details`, `create_job`, `update_job`, `diagnose_job_complete` | Todas operações de vagas |
| `candidates.py` | `search_candidates`, `full_candidate_search`, `get_candidate_details`, `get_candidate_stats` | Busca e análise de candidatos |
| `applies.py` | `move_apply_stage`, `bulk_move_applies`, `get_applies_stats`, `applies_aging` | Candidaturas e pipeline |
| `sourcing.py` | `auto_source`, `get_sourced_profiles`, `create_sourcing`, `get_sourcing_stats` | Sourcing automático |
| `scheduling.py` | `schedule_interview`, `check_availability`, `list_interviews` | Agendamento |
| `evaluations.py` | `create_evaluation`, `send_evaluation`, `get_evaluation_results` | Avaliações |
| `organization.py` | `get_departments`, `create_department`, `get_benefits`, `get_tags` | Entidades org |
| `planning.py` | `write_plan`, `update_plan` | Progresso visível (⬜→🔄→✅) |
| `file_system.py` | `save_file`, `read_file` | Offloading de resultados >5K chars |
| `generic.py` | `discover_api`, `call_api` | Qualquer endpoint Rails API |
| `macros.py` | `daily_briefing_complete`, `job_report_complete`, `diagnose_job_complete` | Macros compostas multi-API |
| `formatting.py` | Formatação de markdown, tabelas | Formatação de output |
| `tool_search.py` | `ask_user` | Clarificação ao usuário |

**Regras do autonomous (AUTONOMOUS_SYSTEM_PROMPT):**
- 1 tool: vai direto sem write_plan
- 2+ tools: SEMPRE `write_plan` antes; atualiza após cada tool
- Budget: max 40 API calls por sessão
- Offloading: resultados >5K chars → `save_file` automático
- Resolução de contexto: `viewing_entities` → sessão → URL → `ask_user`

#### [LIA-LLM] Capacidades conversacionais (dados já em contexto da conversa)

**Briefing e Planejamento:**
- **Briefing do dia** — organiza e prioriza informações presentes na conversa: candidatos mencionados, vagas discutidas, alertas citados, entrevistas agendadas
- **Planejamento de agenda** — sugere ordem de prioridade para tarefas com base em urgência e impacto declarados na conversa
- **Insights proativos** — antecipa próximas ações com base no histórico da sessão (ex: "Você mencionou 3 candidatos para a vaga X — quer que eu compare?")

**Análises (com dados em contexto):**
- **Comparação de finalistas** — compara candidatos se seus dados foram mencionados ou passados no payload da conversa
- **Análise de pipeline** — interpreta dados de pipeline quando fornecidos pelo recrutador na conversa
- **Ranking de prioridades** — ordena vagas ou candidatos por urgência quando dados estão em contexto
- **Interpretação de relatórios** — explica dados de relatórios gerados via `generate_report`

**Resposta a Perguntas Gerais:**
- Boas práticas de RH e recrutamento
- Explicação de métricas (time-to-fill, time-to-hire, taxa de conversão, etc.)
- Orientações sobre processos seletivos e compliance
- Interpretação de resultados de avaliações WSI

**Gestão de Sessão:**
- **Memória de preferências** — lembra decisões e preferências da sessão (`ConversationState` + `ConversationMemory`)
- **Continuidade multi-turn** — mantém contexto de conversas longas com resolução de pronomes (Tier 0 do CascadedRouter)
- **Clarificação de ambiguidades** — quando CascadedRouter retorna `clarification_needed`, faz pergunta estruturada com opções

---

### 3.2 Restrições OUT

| Capacidade | LIA — Por quê não está disponível | LIA — Para onde delegar | v5 — Disponível? |
|---|---|---|---|
| Buscar vagas via API | `search_jobs` não está no scope GLOBAL | Navegar para `/user/jobs` → Prompt 2 | ✅ `search_jobs` (autonomous / jobs domain) |
| Criar vagas via API | `create_job` não está no scope GLOBAL | Navegar para `/user/jobs` → Prompt 2 | ✅ `create_job` (autonomous) |
| Buscar candidatos via API | `search_candidates` não está no scope GLOBAL | Navegar para `/user/candidates` → Prompt 4 | ✅ `search_candidates`, `full_candidate_search` |
| Mover candidatos no pipeline | `update_candidate_stage` não está no scope GLOBAL | Navegar para `/user/jobs/{id}` → Prompt 3 | ✅ `move_apply_stage`, `bulk_move_applies` |
| Enviar email/WhatsApp via API | `send_email`/`send_whatsapp` não estão no scope GLOBAL | Prompt 3 ou Prompt 4 | ✅ Via autonomous domain |
| Agendar entrevistas via API | `schedule_interview` não está no scope GLOBAL | Navegar para `/user/jobs/{id}` → Prompt 3 | ✅ Via scheduling domain |
| Triagem WSI de CVs | `wsi_screening` não está no scope GLOBAL | Navegar para `/user/jobs/{id}` → Prompt 3 | ⚠️ Score via API (sem 7 blocos WSI explícitos) |
| Briefing do dia via API | `daily_briefing` não é tool no scope GLOBAL | — | ✅ `daily_briefing_complete` (macro autonomous) |
| Diagnóstico de vaga via API | `diagnose_job` não é tool no scope GLOBAL | — | ✅ `diagnose_job_complete` (macro autonomous) |

---

### 3.3 Dados que coleta / gera

#### LIA — Inputs

- `message` — pergunta ou instrução do recrutador
- `context_page: "general"/"global"` — ativa o contexto GLOBAL
- `user_id` + `company_id` — identidade e isolamento multi-tenant
- `conversation_id` — histórico de sessão para memória (`ConversationMemory`)
- Dados mencionados na conversa (candidatos, vagas, alertas) — usados pelo [LIA-LLM]
- `tenant_context_snippet` — contexto enriquecido do tenant injetado pelo `TenantContextService`

#### v5 — Inputs

- `message` (string) — query do recrutador
- `session_id` (uuid4, auto-gerado se não enviado) — chave da `ConversationSession`
- `domain: null` — indica modo hub global
- `hub_mode: true` — ativa `HubOrchestrator`
- `context_data` (dict) — dados adicionais de contexto:
  - `viewing_entities`: `{job_id, candidate_id}` — entidades visíveis na tela atual
  - `recent_messages`: histórico para hidratação de sessão nova
  - `one_time_token`: OTT para autenticação de callbacks
  - `progress_sender`: callback de streaming (SSE)
  - `workspace_id`: ID do workspace multi-tenant
  - `sourcing_id`: ID de sourcing se contexto de sourcing

#### LIA — Outputs

- Relatório gerado (`generate_report`): PDF, CSV ou JSON com analytics de recrutamento
- Relatório agendado (`schedule_report`): confirmação de agendamento com próxima execução
- Config da empresa (`get_company_config`): dados estruturados sobre workflow de contratação
- Feedback registrado (`capture_wizard_feedback`): confirmação de registro
- [LIA-LLM] Briefing textual formatado (bullets: urgentes → importantes → informativos)
- [LIA-LLM] Análises e comparações em markdown (tabelas, listas)
- [LIA-LLM] Respostas a perguntas gerais com sugestões de próximas ações

#### v5 — Outputs

- `message` (string) — resposta formatada em markdown
- `data` (dict) — dados estruturados por output_key de cada task
- `navigation_actions[]` — ações de navegação para o frontend executar
- `suggestions[]` — próximas ações sugeridas (deduplicadas)
- `needs_clarification` (bool) + `clarification_question` + `clarification_options[]`
- `pending_action` — estado de ação multi-turn pendente
- `cards[]` — cards estruturados do frontend
- `metadata` — timing, session_id, has_pending_action, completed_domains
- `auth_token` — OTT para callback do frontend

---

### 3.4 Arquitetura técnica — LIA

```
Frontend (context_page: "general" | "global")
    │
    ▼
ContextAdapter.from_rest() / from_ws() / from_rabbitmq()
    context_type = "general"
    entity_id    = null
    │
    ▼
MainOrchestrator.process()
    ├─ FairnessGuard.check()        ← bloqueia antes de qualquer fase
    ├─ Phase 0: PendingActionState  ← confirmações multi-turn
    ├─ Phase 1: ActionExecutor      ← ações por padrão fechado
    └─ Phase 2: Orchestrator
          │
          ├─ CascadedRouter.route() → domain_id (por intenção da mensagem)
          │     (pode rotear para: recruiter_assistant, job_management,
          │      cv_screening, analytics, etc.)
          │
          ├─ DomainWorkflow.process(domain_id, context)
          │     ← domínios YAML: recruiter_assistant.yaml
          │
          └─ filter_tools_by_scope(GLOBAL)
                → tools disponíveis: get_company_config | generate_report |
                                     schedule_report | capture_wizard_feedback

Agentes disponíveis: orchestrator, recruiter_assistant

Sistema de prompt (recruiter_assistant.yaml):
    Persona: "Assistente pessoal do recrutador: proativo, conciso,
              focado em ações práticas e planejamento inteligente."
    Padrões (interaction_patterns.py):
        NEGATION_DETECTION_BLOCK  → cancela se mensagem contém negação
        CHAIN_OF_THOUGHT_BLOCK    → raciocina em <thought> antes de responder
        ANTI_SYCOPHANCY_BLOCK     → não concorda apenas para evitar conflito
    Formato de resposta:
        Briefing: urgentes → importantes → informativos
        Comparações: tabela markdown
        Insights: [Insight] contexto + ação recomendada
        Encerramento: "Próximas ações sugeridas: [1] [2] [3]"

Segurança:
    ContextAdapter.validate_entity_ownership()
        → IDOR prevention: valida entity_id contra company_id
        → Tabelas validadas: sourcing_sessions | job_vacancies | candidates
```

---

### 3.5 Arquitetura técnica — v5

```
Frontend (domain: null, hub_mode: true)
    │
    ▼
POST /chat ou /chat/stream (SSE — EventSourceResponse)
    │
    ▼
MessageRouter.route(payload)
    ├─ configure_ott_from_message() ← OTT para callbacks
    ├─ hub_mode=True → HubOrchestrator.process()
    │
    ▼
HubOrchestrator
    ├─ safe_process_input() ← injeção bloqueada com INJECTION_RESPONSE
    ├─ SessionStore.get_or_create(session_id)
    │     ConversationSession { MAX_HISTORY=50, active_context, domain_memories }
    ├─ _hydrate_session_from_history(recent_messages)
    ├─ _apply_page_context(context_data, session)
    │
    ├─ PendingAction check:
    │     SELECT_OPTION | PROVIDE_INFO | CONFIRM
    │     is_response_to_pending? → _resolve_pending_action()
    │     abandoned? → clear + nova query
    │
    ├─ SchedulingSession bypass (se em fluxo de agendamento ativo)
    │
    └─ _execute_new_query()
          │
          ▼
      HubPlanner.plan(query) → HubExecutionPlan
          ├─ FAST_NAV_PATTERNS (12 regex) → NavigationAction imediato:
          │     "vá para vagas ativas"     → NAVIGATE /user/jobs?tab=active
          │     "vá para candidatos"       → NAVIGATE /user/candidates?tab=candidatos
          │     "vá para avaliações"       → NAVIGATE /user/evaluations
          ├─ _JOB_ID_PATTERN ("vaga 42")   → NAVIGATE /user/jobs/42 OU detalhes via jobs domain
          ├─ _CANDIDATE_ID_PATTERN         → NAVIGATE /user/candidates/{id}
          ├─ _CANDIDATE_SEARCH_RE          → pipeline candidate_search
          ├─ MULTI_INTENT_RE               → HubTask[] em paralelo
          └─ LLM (PLANNER_SYSTEM_PROMPT)   → HubExecutionPlan JSON
                Sinais → autonomous: 4+ endpoints, "completo/executivo/auditoria",
                          cadeia leitura+análise+escrita, nomes de endpoints explícitos
          │
          ▼
      HubExecutor.execute(plan)
          ├─ HubContextManager (resolve depends_on entre tasks)
          ├─ _execute_fan_out_task (iterate_over, max_iterations=10)
          ├─ _try_autonomous_fallback (retenta domain com autonomous)
          └─ HubResult { cards[], needs_clarification, pending_action_data }
          │
          ▼
      _extract_context_from_results → session.update_context()
      SessionStore.save(session)
      RequestTimer → timing report
      get_token_for_callback() → auth_token no response

Domínio default: autonomous (73+ tools, 13 módulos)
AUTONOMOUS_SYSTEM_PROMPT:
    • 1 tool: executa direto
    • 2+ tools: write_plan obrigatório
    • Budget: max 40 API calls
    • Offloading: save_file para >5K chars
    • Resolução: viewing_entities → sessão → URL → ask_user
```

---

### 3.6 Diagrama de delegação e migração de contexto

#### LIA — Migração controlada pelo frontend (context_page)

```
USUÁRIO ENVIA MENSAGEM NO CHAT FLUTUANTE
                    │
            Frontend detecta:
            qual página o usuário está?
                    │
    ┌───────────────┼─────────────────────┐
    │               │                     │
    ▼               ▼                     ▼
Todas as       /user/jobs           /user/jobs/{id}
páginas        (tabela vagas)       (kanban da vaga)
    │               │                     │
    ▼               ▼                     ▼
context_page:  context_page:        context_page:
"general"      "job"/"wizard"       "pipeline"
    │               │                     │
    ▼               ▼                     ▼
GLOBAL scope   JOB_TABLE scope      IN_JOB scope
4 tools        13 tools             6 tools
(Prompt 1)     (Prompt 2)           (Prompt 3)
                                          │
                               TAMBÉM: /user/candidates
                               ou /user/sourcing/{id}
                                          │
                                    context_page:
                                    "sourcing"/"talent"
                                          │
                                    TALENT_FUNNEL scope
                                    9 tools (Prompt 4)

GATILHOS DE MIGRAÇÃO (sempre via navegação do frontend):
    → Usuário navega para /user/jobs       → JOB_TABLE  (Prompt 2)
    → Usuário abre vaga /user/jobs/{id}    → IN_JOB     (Prompt 3)
    → Usuário vai para /user/candidates    → TALENT_FUNNEL (Prompt 4)
    → Usuário retorna para outra página    → GLOBAL     (Prompt 1)

REGRA CRÍTICA: O backend LIA não migra contexto autonomamente.
O scope de tools é 100% determinado pelo context_page do frontend.
O CascadedRouter pode rotear para domínios diferentes por intenção,
mas as tools chamáveis permanecem as do scope ativo.
```

#### v5 — Roteamento inteligente pelo HubPlanner (sem dependência de página)

```
USUÁRIO ENVIA MENSAGEM NO CHAT GLOBAL (hub_mode: true)
                    │
            HubPlanner analisa
            INDEPENDENTE de qual página está
                    │
    ┌───────────────┼─────────────────────┐
    ▼               ▼                     ▼
FAST_NAV       ID explícito         LLM classifica
(regex)        na mensagem          intenção
    │               │                     │
    ▼               ▼          ┌──────────┼──────────┐
NavigationAction  Open direto  ▼          ▼          ▼
(navega a page)  (job ou    "vagas"    "kanban"  "candidatos"
                  candidate)  query    /pipeline   query
                                │          │          │
                           jobs       applies   sourced_
                           domain     domain    profile_
                                               sourcing

MULTI_INTENT_RE detectado?
→ HubExecutionPlan: HubTask[] em paralelo
  Ex: "briefing do dia E stats de vagas" → 2 tasks simultâneas
→ AUTONOMOUS tem acesso a todas as 73+ tools sem restrição de scope
→ Pode navegar PARA qualquer página sem o usuário navegar manualmente

CANDIDATE_SEARCH_RE detectado?
→ pipeline candidate_search (search_pipeline.py):
  SearchParams { skills, text_terms, location, seniority, min_experience,
                 english_level, remote, companies, limit_per_strategy=25 }
  CandidateResult { id, name, role_name, city, state, skills, score,
                    source_strategies, relevance_score }
  Multi-strategy parallel search com ThreadPoolExecutor
  70+ tecnologias mapeadas (_KNOWN_TECH)
  6 variações de cargo (_ROLE_VARIATIONS: frontend/backend/fullstack/devops/data/mobile)

DOMAIN FALLBACK:
→ Task domain falhou + não em _FALLBACK_SKIP_DOMAINS?
  → _try_autonomous_fallback() → retenta com autonomous
→ domains que não fazem fallback: "autonomous", "scheduling"

GATILHO NO v5: a mensagem em si — o usuário não precisa navegar.
```

---

### 3.7 Comparativo LIA × v5 — Prompt Flutuante

| Dimensão | LIA (scope GLOBAL) | v5 (autonomous, 73+ tools) |
|---|---|---|
| **Tools de API** | 4 (YAML) / 2 (runtime scope_config) | 73+ em 13 módulos |
| **Domain routing** | CascadedRouter (6 tiers, por mensagem) | HubPlanner (LLM + regex) |
| **Busca de vagas via API** | ❌ | ✅ search_jobs, get_all_jobs_stats |
| **Busca de candidatos via API** | ❌ | ✅ search_candidates, full_candidate_search |
| **Mover candidatos via API** | ❌ | ✅ move_apply_stage, bulk_move_applies |
| **Gerar relatório** | ✅ generate_report (pdf/csv/json) | ✅ Via analytics tools |
| **Agendar relatório** | ✅ schedule_report | ❌ Sem equivalente |
| **Config da empresa** | ✅ get_company_config | ✅ Via discover_api + call_api |
| **Briefing do dia via API** | ❌ | ✅ daily_briefing_complete |
| **Diagnóstico de vaga** | ❌ | ✅ diagnose_job_complete |
| **Multi-intenção** | ✅ PlanDetector + PlanExecutor | ✅ MULTI_INTENT_RE + HubTask[] paralelo |
| **Progresso visível** | ❌ | ✅ write_plan (⬜→🔄→✅) |
| **Budget de tools** | ❌ Sem controle | ✅ Max 40 API calls |
| **Offloading de resultados** | ❌ | ✅ save_file para >5K chars |
| **Navegação programática** | ❌ | ✅ NavigationAction(NAVIGATE, target) |
| **Fan-out em listas** | ✅ PlanExecutor (sequencial) | ✅ iterate_over (multi-iteração) |
| **Fallback de domain** | Clarification request | ✅ autonomous fallback automático |
| **Streaming SSE** | ⚠️ Via WebSocket | ✅ /chat/stream com SSE nativo |
| **Session persistence** | ConversationMemory | ✅ SessionStore + ConversationSession (MAX_HISTORY=50) |
| **PendingAction tipos** | 1 tipo (confirmação) | 3 tipos: SELECT_OPTION / PROVIDE_INFO / CONFIRM |
| **Scheduling bypass** | ❌ | ✅ _has_active_scheduling_session() |
| **Candidate search pipeline** | ❌ | ✅ SearchParams + CandidateResult multi-strategy |
| **Fallback genérico de API** | ❌ | ✅ call_api (qualquer endpoint Rails) |
| **FairnessGuard** | ✅ Antes de qualquer fase | ✅ Via system prompt |
| **IDOR prevention** | ✅ validate_entity_ownership() | ✅ Via workspace_id |

---

## 4. Prompt 2 — Tabela de Vagas {#prompt-2}

### 4.0 Introdução

O **Prompt Expandido da Tabela de Vagas** aparece ao lado da listagem de vagas (`/user/jobs`). É o contexto especializado para **criar, configurar, editar e gerir vagas**.

**Ativação LIA:** `context_page: "job"/"jobs"/"vacancies"/"wizard"` → `context_type: "job_management"` → domínio `job_management.yaml` → scope JOB_TABLE.

**Ativação v5:** `domain: "jobs"` → `DomainOrchestrator.process_query(domain_id="jobs")` → `JobsDomain` → `JobsActions`.

**Para que serve:** criar nova vaga via wizard conversacional, gerar job description, benchmark salarial, configurar etapas do processo seletivo, editar vagas existentes, publicar vagas, analytics de vagas.

**Para que NÃO serve:** buscar candidatos, triar CVs, agendar entrevistas, movimentar candidatos no pipeline.

---

### 4.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: JOB_TABLE — 13 tools, fonte: tool_registry_metadata.yaml)

**Query tools:**

| Tool | O que faz | Parâmetros | v5 equivalente |
|---|---|---|---|
| `search_jobs` | Busca vagas por título, status, departamento | `query`, `status`, `department`, `limit` | `list_jobs` (jobs domain) |
| `get_job_details` | Detalhes completos da vaga + candidatos | `job_id`, `include_candidates` | `show_job_details` (jobs domain) |
| `get_pipeline_stats` | Stats do pipeline: candidatos por etapa, taxas de conversão | `job_id`, `date_range` | `job_analytics`, `account_stats` (jobs domain) |
| `search_salary_benchmark` | Benchmark salarial por cargo/senioridade/localidade/setor | `job_title`, `seniority`, `location`, `industry` | ❌ Sem tool explícita |
| `get_intelligent_salary` | Sugestão inteligente de faixa salarial | `job_title`, `seniority`, `location` | ❌ Sem tool explícita |
| `get_intelligent_skills` | Sugestão de competências por cargo e senioridade | `job_title`, `seniority`, `industry` | `generate_interview_questions` (jobs domain) |
| `get_job_suggestions` | Sugestões de melhoria para a JD atual | `job_title`, `current_description`, `industry` | `generate_suggestion` (jobs domain) |
| `validate_job_fields` | Valida campos e detecta informações faltando antes de salvar | `fields` | ❌ Sem equivalente explícito |

**Action tools:**

| Tool | O que faz | Parâmetros | v5 equivalente |
|---|---|---|---|
| `save_job_draft` | Salva rascunho da vaga em criação `[ESCRITA]` | `fields`, `draft_id` | ❌ Sem equivalente (sem wizard estruturado) |
| `generate_enriched_jd` | Gera Job Description por IA a partir dos campos coletados | `fields`, `tone: formal\|creative\|technical` | `generate_suggestion` (jobs domain) |
| `create_job` | Cria nova vaga no banco `[ESCRITA]` | `title`, `description`, `department`, `location`, `salary_range`, `requirements[]` | Via autonomous domain |
| `update_job` | Edita campos de vaga existente `[ESCRITA]` | `job_id`, `fields` | `change_status` (jobs domain) / Via autonomous |
| `publish_job` | Publica vaga em canais definidos `[ESCRITA]` | `job_id`, `channels[]` | Via autonomous domain |

#### [v5] Actions do domínio jobs (src/domains/jobs/actions/)

| Arquivo | Actions | Capacidade |
|---|---|---|
| `analytics.py` | `job_analytics`, `account_stats`, `pipeline_health` | Analytics detalhados de vaga + saúde de todas as vagas ativas |
| `base.py` | `show_job_details` | Detalhes completos da vaga |
| `conversational.py` | `conversational` | Fallback conversacional sem chamada de API |
| `matching.py` | `matching_candidates` | Matching de candidatos por embedding similarity |
| `mutations.py` | `change_status`, `copy_job`, `bulk_apply_action`, `export_job` | Mutations: status, duplicar, bulk, exportar |
| `query.py` | `list_jobs`, `pipeline_status`, `alerts`, `summarize_job` | Listagem, pipeline visual, alertas de vaga, resumo |
| `suggestions.py` | `generate_suggestion`, `generate_interview_questions`, `auto_source` | JD por IA, perguntas CBI, sourcing automático |

**Detecção de intenção v5 (regex _CONTEXT_ACTION_PATTERNS em JobsDomain):**

| Padrão regex | Action mapeada |
|---|---|
| `pipeline\|kanban` | `pipeline_status` |
| `analytics\|funil\|gargalo\|anali[zs]e` | `job_analytics` |
| `report\|relat[oó]rio\|resumo` | `summarize_job` |
| `alertas` | `alerts` |
| `estatísticas\|stats` | `account_stats` |
| `exportar` | `export_job` |
| `saúde do pipeline` | `pipeline_health` |
| `auto.?source\|sourcing automático` | `auto_source` |
| `feedback de rejeição` | `send_reject_feedback` |

**Cache tiered v5 (TieredContextManager):**
- Tier 1: dados básicos (rápido) → ações simples como list_jobs, pipeline_status
- Tier 2: dados completos + analytics → summarize_job, job_analytics
- `ACTIONS_USING_TIER1` e `ACTIONS_USING_TIER2` (frozensets)

**CircuitBreaker v5:** `circuit_breaker_call()` protege todas as chamadas à API do jobs domain

#### [LIA-LLM] Capacidades conversacionais

**Wizard Conversacional de Criação de Vagas:**
- Conduz o recrutador passo a passo coletando: título, área, senioridade, tipo de contrato, faixa salarial, localidade, modelo de trabalho, competências WSI, etapas do processo; uma pergunta por vez com confirmação por seção
- Garante linguagem inclusiva e não discriminatória na JD (sem critérios de idade, estado civil, gênero, origem)
- Alerta se requisitos coletados são excessivamente restritivos (risco de pipeline escasso)
- Sugere etapas do processo seletivo adequadas ao tipo de cargo (ex: Web Response → Triagem → Teste técnico → Entrevista → Proposta)
- Confirma título + senioridade + tipo de contrato antes de finalizar o rascunho

**Análises e Sugestões:**
- Explica dados de analytics retornados pelo `get_pipeline_stats`
- Interpreta benchmark salarial retornado pelo `search_salary_benchmark`
- Sugere ajustes de requisitos baseados no benchmark de mercado

---

### 4.2 Restrições OUT

| Capacidade | LIA — Por quê não está disponível | LIA — Para onde delegar | v5 — Disponível? |
|---|---|---|---|
| Buscar candidatos do banco | `search_candidates` não está em JOB_TABLE | Prompt 4 (TALENT_FUNNEL) | ✅ Via autonomous domain |
| Triar CVs de candidatos em vaga | `wsi_screening` não está em JOB_TABLE | Prompt 3 (IN_JOB) | ⚠️ Via autonomous |
| Mover candidatos no pipeline | `update_candidate_stage` não está em JOB_TABLE | Prompt 3 (IN_JOB) | ✅ Via applies domain |
| Agendar entrevistas | `schedule_interview` não está em JOB_TABLE | Prompt 3 (IN_JOB) | ✅ scheduling domain |
| Enviar email/WhatsApp | `send_email`/`send_whatsapp` não estão em JOB_TABLE | Prompt 3 / Prompt 4 | ✅ Via autonomous domain |
| Ver kanban de uma vaga específica | `get_vacancy_funnel` não está em JOB_TABLE | Prompt 3 (IN_JOB) | ✅ `pipeline_status` no jobs domain |
| Benchmark salarial | ✅ Disponível em LIA | — | ❌ Sem tool explícita no jobs domain |
| Wizard conversacional estruturado | ✅ Disponível em LIA [LLM] | — | ❌ Sem wizard estruturado |
| Validação de campos antes de salvar | ✅ `validate_job_fields` | — | ❌ Sem equivalente explícito |

---

### 4.3 Dados que coleta / gera

#### LIA — Inputs

- `context_page: "job"/"jobs"/"vacancies"/"wizard"` — ativa o scope JOB_TABLE
- `entity_id` — job_id da vaga selecionada (opcional)
- `job_context` — dados da vaga atual passados pelo frontend
- Campos coletados no wizard: título, área, senioridade, tipo de contrato, faixa salarial, localidade, modelo de trabalho, skills, competências WSI, etapas do processo

#### v5 — Inputs (DomainContext para jobs domain)

- `domain: "jobs"` — rota para JobsDomain
- `job_id` (int, context_overrides) — vaga em foco
- `workspace_id` (int) — isolamento multi-tenant
- `conversation_memory` — JobConversationMemory (histórico por domínio)
- `auth_token` — OTT para callbacks
- `api_calls_history` — histórico de chamadas da sessão

#### LIA — Outputs

- Rascunho de vaga salvo no banco (`save_job_draft`)
- Vaga criada e publicada no ATS
- Job Description em Markdown (seções: Sobre a empresa | Responsabilidades | Requisitos | Benefícios)
- Benchmark salarial: faixa min/max por cargo, senioridade, localidade
- Lista de skills sugeridas com justificativa
- Stats do pipeline por etapa (dados para gráficos no frontend)

#### v5 — Outputs (DomainResponse)

- `success` (bool), `message` (markdown), `data` (dict)
- `suggestions[]` — próximas ações (ex: "Ver candidatos desta vaga", "Exportar vaga")
- `needs_confirmation` + `confirmation_message` — para ações destrutivas
- `api_calls[]` — log de chamadas à API Rails
- `metadata` — action_id, tools_used, timing
- NavigationActions (se job_id detectado → NAVIGATE /user/jobs/{job_id})

---

### 4.4 Arquitetura técnica — LIA

```
Frontend (context_page: "job" | "jobs" | "vacancies" | "wizard")
    │
    ▼
ContextAdapter.from_rest() / from_job_chat()
    context_type = "job_management"
    entity_id    = job_id (se disponível)
    job_context  = dados da vaga
    │
    ▼
MainOrchestrator.process()
    │
    └─ Orchestrator.process_request_with_memory()
          │
          ├─ CascadedRouter → domain_id: "job_management" / "job_planner" / "job_intake"
          │
          └─ DomainWorkflow → job_management.yaml
                │
                └─ filter_tools_by_scope(JOB_TABLE) → 13 tools disponíveis

Agentes: orchestrator, job_planner, job_intake, job_wizard

Regras do domínio (job_management.yaml):
    → Nunca incluir critérios discriminatórios na JD
    → Confirmar título + senioridade + tipo antes de salvar
    → Alertar se requisitos excessivamente restritivos
    → Sugerir benchmark salarial quando disponível
    → Wizard: uma pergunta por vez, confirmação por seção
```

---

### 4.5 Arquitetura técnica — v5

```
Frontend (domain: "jobs") OU HubPlanner detecta query sobre vagas
    │
    ▼
JobsDomain (domain_id: "jobs", domain_name: "Gestao de Vagas")
    │
    ▼
JobsDynamicPromptBuilder
    PromptConfig(max_actions_in_prompt=8, max_examples_per_action=2)
    Dois modos:
        has_job_context=True  → prompt enriquecido com detalhes da vaga
        has_job_context=False → prompt genérico para listagem
    │
    ▼
TieredContextManager (cache por tier):
    Tier 1: dados básicos (rápido) → ações simples (list, status)
    Tier 2: dados completos + analytics → análises e relatórios
    │
    ▼
JobsActions (src/domains/jobs/actions/):
    analytics.py:    job_analytics | account_stats | pipeline_health
    base.py:         show_job_details
    conversational.py: conversational (fallback sem API call)
    matching.py:     matching_candidates (embedding similarity)
    mutations.py:    change_status | copy_job | bulk_apply_action | export_job
    query.py:        list_jobs | pipeline_status | alerts | summarize_job
    suggestions.py:  generate_suggestion | generate_interview_questions | auto_source

Detecção de intenção por regex (_CONTEXT_ACTION_PATTERNS):
    "pipeline|kanban"   → pipeline_status
    "analytics|funil"   → job_analytics
    "report|resumo"     → summarize_job
    "alertas"           → alerts
    "estatísticas"      → account_stats
    "exportar"          → export_job
    "saúde do pipeline" → pipeline_health
    "auto_source"       → auto_source

JobConversationMemory: memória de sessão específica do jobs domain
JobsAPIClient: cliente HTTP para Rails API com DomainContext
JobTemplateFormatter: formatação de templates de vagas
CircuitBreaker: proteção contra falhas na API (circuit_breaker_call)
```

---

### 4.6 Comparativo LIA × v5 — Tabela de Vagas

| Dimensão | LIA (JOB_TABLE, 13 tools) | v5 (jobs domain) |
|---|---|---|
| **Busca/detalhe de vagas** | ✅ search_jobs, get_job_details | ✅ list_jobs, show_job_details |
| **CRUD de vagas** | ✅ create_job, update_job, publish_job, save_job_draft | ✅ change_status + create via autonomous |
| **Pipeline stats** | ✅ get_pipeline_stats | ✅ job_analytics, account_stats |
| **Benchmark salarial** | ✅ search_salary_benchmark + get_intelligent_salary | ❌ Sem tool explícita |
| **Skills sugeridas** | ✅ get_intelligent_skills | ✅ generate_interview_questions |
| **JD gerada por IA** | ✅ generate_enriched_jd (tom configurável) + [LLM] | ✅ generate_suggestion |
| **Validação de campos** | ✅ validate_job_fields antes de salvar | ❌ Sem equivalente explícito |
| **Wizard conversacional** | ✅ [LIA-LLM] com save_job_draft por seção | ❌ Sem wizard estruturado |
| **Kanban visual** | ❌ get_vacancy_funnel não está em JOB_TABLE | ✅ pipeline_status no domínio jobs |
| **Saúde de múltiplas vagas** | ❌ | ✅ pipeline_health |
| **Alertas de prazo** | ❌ | ✅ alerts |
| **Matching de candidatos** | ❌ | ✅ matching_candidates (embedding) |
| **Sourcing automático** | ❌ | ✅ auto_source |
| **Duplicar vaga** | ❌ | ✅ copy_job |
| **Ações em lote** | ❌ | ✅ bulk_apply_action |
| **Perguntas de entrevista** | ❌ | ✅ generate_interview_questions |
| **Feedback de rejeição** | ❌ | ✅ send_reject_feedback |
| **Cache tiered** | ❌ | ✅ TieredContextManager (Tier1 + Tier2) |
| **CircuitBreaker** | ❌ | ✅ circuit_breaker_call() |
| **Memória por domínio** | ConversationMemory global | ✅ JobConversationMemory (isolada por domain) |
| **Detecção de intenção** | Via CascadedRouter | ✅ _CONTEXT_ACTION_PATTERNS regex + LLM |

---

## 5. Prompt 3 — Dentro da Vaga (Kanban) {#prompt-3}

### 5.0 Introdução

O **Prompt Expandido do Kanban** aparece dentro de uma vaga específica (`/user/jobs/{id}`), ao lado do kanban de candidatos. É o contexto mais operacional — age diretamente sobre candidatos **de uma vaga específica**.

**Ativação LIA:** `context_page: "pipeline"/"kanban"` → `context_type: "pipeline"` → 4 domínios YAML ativos → scope IN_JOB.

**Ativação v5:** `domain: "applies"` → `DomainOrchestrator.process_query(domain_id="applies")` → `AppliesDomain` → `AppliesActions`.

**Para que serve:** triar CVs com score WSI, mover candidatos entre etapas, conduzir entrevistas CBI, agendar entrevistas, enviar comunicações, ver funil da vaga.

**Para que NÃO serve:** buscar candidatos externos ao processo, criar novas vagas, fazer análises cross-vagas.

---

### 5.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: IN_JOB — 6 tools, fonte: tool_registry_metadata.yaml)

| Tool | O que faz | Parâmetros | v5 equivalente |
|---|---|---|---|
| `update_candidate_stage` | Move candidato para etapa do pipeline `[ESCRITA]` | `candidate_id`, `target_stage`, `job_id`, `notes`, `notify_candidate` | `move_stage` (applies domain) |
| `reject_candidate` | Rejeita candidato com motivo `[ESCRITA]` | `candidate_id`, `vacancy_id`, `reason`, `notify` | `reject_apply` (applies domain) |
| `bulk_update_candidates_stage` | Move múltiplos candidatos de etapa simultaneamente `[LOTE][ESCRITA]` | `candidate_ids[]`, `target_stage`, `job_id` | `bulk_move_applies` (async, applies domain) |
| `wsi_screening` | Inicia avaliação WSI formal para candidato (voz, texto ou vídeo) `[ESCRITA]` | `candidate_id`, `job_id`, `screening_type: voice\|text\|video` | ⚠️ Via autonomous domain |
| `hide_candidate` | Oculta candidato da visualização ativa (soft remove) `[ESCRITA]` | `candidate_id`, `vacancy_id`, `reason` | ❌ Sem equivalente direto |
| `get_vacancy_funnel` | Retorna dados do funil: candidatos por etapa + taxas de conversão | `job_id`, `include_rejected` | `get_kanban` + `stage_distribution` (applies domain) |

**Nota sobre divergência de fontes — IN_JOB:** `app/tools/scope_config.py` (`SCOPE_TOOL_MAPPING`) lista IN_JOB com 25 tools: 14 query tools (`get_job_details`, `get_vacancy_funnel`, `get_candidate_details`, `get_activity_summary`, `get_pending_actions`, `compare_candidates`, `get_candidate_stats`, `get_bottleneck_analysis`, `get_job_velocity`, `get_job_quality_metrics`, `get_stakeholder_metrics`, `get_prediction_metrics`, `get_job_benchmark`, `get_smart_alerts`) + 11 action tools (`update_candidate_stage`, `bulk_update_candidates_stage`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `wsi_screening`, `send_email`, `send_whatsapp`, `schedule_interview`, `send_feedback`). O `tool_registry_metadata.yaml` lista apenas 6 dessas tools. A discrepância é documentada — o `scope_config.py` é a fonte executável de runtime; as 25 tools listadas nele são o teto real de capacidade da API neste escopo.

#### [v5] Actions do domínio applies (src/domains/applies/actions/)

| Arquivo | Actions | Capacidade |
|---|---|---|
| `analytics.py` | `apply_analytics`, `stage_distribution` | Analytics de candidaturas + distribuição por etapa |
| `base.py` | Base classes para as actions | — |
| `bulk.py` | `bulk_approve_applies`, `bulk_reject_applies`, `bulk_move_applies` (async), `send_apply_reject_feedback` | Ações em lote; bulk_move é assíncrono |
| `comparison.py` | `compare_candidates` | Comparação lado a lado de candidatos |
| `conversational.py` | `conversational` | Fallback conversacional sem chamada de API |
| `details.py` | `show_apply_details`, `apply_timeline` | Detalhes completos + histórico da candidatura |
| `pipeline.py` | `get_kanban`, `move_stage`, `approve_apply`, `reject_apply` | Kanban + movimentações do pipeline |
| `scoring.py` | `filter_by_score`, `top_candidates`, `full_ranking` | Filtragem e ranking por score |
| `search.py` | `search_applies`, `search_by_name`, `list_applies_by_stage`, `recent_applies`, `count_applies` | Busca e contagem de candidaturas |
| `sourcing.py` | `stalled_applies` (attention/warning/critical), `diagnose_applies` | Candidatos parados por SLA + diagnóstico completo |

**Componentes de suporte v5 do applies domain:**
- `AppliesCacheManager` + `ACTIONS_NEEDING_CACHE` — cache de dados para ações frequentes
- `AppliesAPIClient` — cliente HTTP para Rails API com DomainContext
- `AppliesConversationMemory` — memória de sessão específica do applies domain
- `AppliesDynamicPromptBuilder` (max_actions_in_prompt=8) — prompt dinâmico por ação
- `react_agent.py` — agente ReAct dedicado para applies (tool calling com raciocínio)
- `cards.py` — cards estruturados para o frontend
- `formatters/` — comparison_formatter, detail_formatter, table_formatter

#### [LIA-LLM] Capacidades conversacionais

Com dados de candidatos no payload (`candidates[]`, `selected_candidate_ids[]`, `job_context`):

**Score WSI (7 blocos):**
1. **Hard Skills Técnicas** — competências específicas do cargo vs. requisitos da vaga
2. **Soft Skills / Comportamentais** — evidências via CBI (Competency-Based Interview)
3. **Experiência Profissional** — anos, empresas, setor, progressão de carreira
4. **Liderança** — evidências de gestão de pessoas, projetos, equipes
5. **Comunicação** — clareza, persuasão, escrita, oratória
6. **Alinhamento Cultural** — fit com valores e cultura da empresa
7. **Potencial** — capacidade de crescimento e aprendizado
- Recomendação: Avançar (≥75%) | Revisão (60-74%) | Rejeitar (<60%)
- Detecção de red flags: gaps de emprego, job hopping, inconsistências de datas, contradições
- Verificação de questões eliminatórias antes de qualquer avaliação

**FairnessGuard (cv_screening.yaml):**
- Verifica viés involuntário antes de toda rejeição
- Ignora completamente: nome, foto, localização, estado civil, idade, etnia

**Entrevista WSI (interview_scheduling.yaml):**
- Condução de entrevista CBI com perguntas comportamentais estruturadas (uma por vez)
- Detecção de respostas evasivas ou inconsistentes
- Análise pós-entrevista: competências avaliadas + evidências coletadas + score parcial
- Consentimento explícito para transcrição de áudio

**Pipeline e Análises:**
- Ranking de candidatos do contexto por score de compatibilidade
- Comparação lado a lado de finalistas
- Identificação de candidatos parados por etapa (com dados do `get_vacancy_funnel`)
- Sugestão de próxima ação para cada candidato

**Comunicação (communication.yaml):**
- Rascunha emails, mensagens WhatsApp e notificações Teams
- Todo email inclui rodapé "Mensagem gerada com assistência de IA pela LIA"
- Confirmação para envios em massa (>10 destinatários)

---

### 5.2 Restrições OUT

| Capacidade | LIA — Por quê não está disponível | LIA — Para onde delegar | v5 — Disponível? |
|---|---|---|---|
| Buscar candidatos externos à vaga | `search_candidates` não está em IN_JOB | Prompt 4 (TALENT_FUNNEL) | ✅ Via autonomous domain |
| Criar ou editar vagas | `create_job`/`update_job` não estão em IN_JOB | Prompt 2 (JOB_TABLE) | ✅ Via jobs domain |
| Analytics cross-vagas | Contexto limitado à vaga atual | Prompt 1 (GLOBAL) | ✅ Via insights domain |
| Exportação bulk de candidatos | `export_candidates` não está em IN_JOB | Prompt 4 (TALENT_FUNNEL) | ✅ Via autonomous |
| Score WSI 7 blocos | ✅ Disponível em LIA [LLM] | — | ⚠️ Score via API (sem 7 blocos WSI explícitos) |
| Condução CBI | ✅ interview_scheduling.yaml | — | ⚠️ Via autonomous |
| WSI Screening formal | ✅ wsi_screening (voice/text/video) | — | ⚠️ Via autonomous |
| Email/WhatsApp | ✅ Via scope_config.py | — | ✅ Via autonomous domain |
| Agendar entrevistas | ✅ Via scope_config.py | — | ✅ scheduling domain |

---

### 5.3 Dados que coleta / gera

#### LIA — Inputs

- `context_page: "pipeline"/"kanban"` — ativa scope IN_JOB
- `entity_id` = job_id — vaga aberta
- `job_context` — dados da vaga (título, requisitos, etapas, competências WSI)
- `candidates[]` — lista de candidatos carregados na tela pelo frontend
- `selected_candidate_ids[]` — candidatos selecionados pelo recrutador

#### v5 — Inputs (DomainContext para applies domain)

- `domain: "applies"` — rota para AppliesDomain
- `job_id` (int) — vaga obrigatória para applies
- `apply_id` (int) — candidatura específica (se foco em uma)
- `selected_ids[]` — candidaturas selecionadas
- `workspace_id` (int) — isolamento multi-tenant
- `conversation_memory` — AppliesConversationMemory
- `api_calls_history` — log de chamadas anteriores na sessão
- `auth_token` — OTT para callbacks

#### LIA — Outputs (API)

- Candidato movido de etapa / rejeitado / oculto
- Múltiplos candidatos movidos em lote
- Sessão WSI iniciada (voz, texto ou vídeo)
- Dados do funil por etapa

#### LIA — Outputs (LLM)

- Score WSI 0-100 por candidato com justificativa para cada bloco
- Recomendação de avanço, revisão ou rejeição
- Análise de entrevista pós-condução (competências + evidências + score parcial)
- Rascunho de comunicações (emails, WhatsApp, Teams)
- Log de auditoria de avaliações (compliance LGPD/SOX — documentado no reasoning)

#### v5 — Outputs (DomainResponse)

- `message` (markdown) — resultado da ação com formatação table_formatter ou detail_formatter
- `data` — dados estruturados (kanban, apply_details, analytics, ranking)
- `suggestions[]` — próximas ações (ex: "Ver candidatos travados", "Comparar top 3")
- `needs_clarification` + `clarification_options` — para ações ambíguas
- `needs_confirmation` — para ações destrutivas (reject, bulk_reject)
- `metadata.cards[]` — cards estruturados para frontend
- `api_calls[]` — log de chamadas à Rails API

---

### 5.4 Arquitetura técnica — LIA

```
Frontend (context_page: "pipeline" | "kanban")
    │
    ▼
ContextAdapter
    context_type          = "pipeline"
    entity_id             = job_id
    candidates            = lista de candidatos da tela
    selected_candidate_ids = selecionados pelo usuário
    │
    ▼
MainOrchestrator.process()
    FairnessGuard.check() ← bloqueia inputs discriminatórios
    │
    └─ Orchestrator
          │
          ├─ CascadedRouter → domain_id: "cv_screening" | "pipeline_transition" |
          │                    "interview_scheduling" | "communication" |
          │                    "kanban_search" | "kanban_insight" | "kanban_action"
          │
          └─ DomainWorkflow → 4 YAMLs ativos simultaneamente:
                cv_screening.yaml        ← triagem + score WSI + FairnessGuard
                pipeline_transition.yaml ← movimentação no funil
                interview_scheduling.yaml ← condução CBI + agendamento
                communication.yaml       ← comunicações multi-canal
                │
                └─ filter_tools_by_scope(IN_JOB) → 6 tools disponíveis

Agentes: orchestrator, recruiter_assistant, screening, analyst_feedback, communication

Regras críticas dos domínios:
    cv_screening.yaml:
        NUNCA avalia por nome, foto, localização, estado civil, idade, etnia
        FairnessGuard antes de toda rejeição
        Verifica questões eliminatórias antes de WSI
    interview_scheduling.yaml:
        Perguntas apenas sobre competências profissionais
        Consentimento explícito antes de transcrição
        Detecta respostas evasivas durante a entrevista
    communication.yaml:
        Rodapé obrigatório em todo email gerado por IA
        Confirmação antes de envios >10 destinatários
    pipeline_transition.yaml:
        Confirmação antes de ações destrutivas/irreversíveis
```

---

### 5.5 Arquitetura técnica — v5

```
Frontend (domain: "applies") OU HubPlanner detecta query sobre candidaturas
    │
    ▼
AppliesDomain (domain_id: "applies")
    "Gestao completa de candidaturas: busca, detalhes, pipeline/kanban,
     aprovacao/reprovacao, ranking, comparacao, analytics, acoes em lote.
     Opera no contexto de uma vaga (job_id)."
    │
    ▼
AppliesDynamicPromptBuilder (max_actions_in_prompt=8)
    │
    ▼
AppliesCacheManager (ACTIONS_NEEDING_CACHE)
    ← pré-cacheia dados antes do LLM para ações frequentes
    │
    ▼
AppliesActions (src/domains/applies/actions/):
    analytics.py:    apply_analytics | stage_distribution
    bulk.py:         bulk_approve_applies | bulk_reject_applies |
                     bulk_move_applies (async) | send_apply_reject_feedback
    comparison.py:   compare_candidates
    conversational.py: conversational (fallback sem API call)
    details.py:      show_apply_details | apply_timeline
    pipeline.py:     get_kanban | move_stage | approve_apply | reject_apply
    scoring.py:      filter_by_score | top_candidates | full_ranking
    search.py:       search_applies | search_by_name | list_applies_by_stage |
                     recent_applies | count_applies
    sourcing.py:     stalled_applies (attention/warning/critical) | diagnose_applies
    │
    ▼
react_agent.py ← ReAct agent dedicado para applies (tool calling com reasoning)
    │
    ▼
AppliesAPIClient → ATS Rails API
    cards.py → cards estruturados para frontend
    formatters/ → comparison_formatter, detail_formatter, table_formatter
    AppliesConversationMemory → memória por sessão (isolada por domain)
    CircuitBreaker → circuit_breaker_call()
```

---

### 5.6 Comparativo LIA × v5 — Kanban

| Dimensão | LIA (IN_JOB, 6 tools YAML) | v5 (applies domain) |
|---|---|---|
| **Mover candidato de etapa** | ✅ update_candidate_stage | ✅ move_stage (com confirmação) |
| **Rejeitar candidato** | ✅ reject_candidate | ✅ reject_apply |
| **Aprovar candidato** | ✅ [via update_candidate_stage] | ✅ approve_apply |
| **Ações em lote** | ✅ bulk_update_candidates_stage | ✅ bulk_approve/reject/move_applies (async) |
| **Funil da vaga** | ✅ get_vacancy_funnel | ✅ get_kanban + stage_distribution |
| **Score WSI 7 blocos** | ✅ [LIA-LLM] com FairnessGuard | ⚠️ Score via API (sem 7 blocos explícitos) |
| **WSI Screening formal** | ✅ wsi_screening (voice/text/video) | ⚠️ Via autonomous domain |
| **FairnessGuard** | ✅ Antes de toda rejeição (code + YAML) | ✅ FairnessMetrics (sourcing) / system prompt |
| **Condução CBI** | ✅ interview_scheduling.yaml dedicado | ⚠️ Via autonomous |
| **Analytics de candidaturas** | ❌ (YAML) / ✅ (scope_config.py: get_bottleneck_analysis, etc.) | ✅ apply_analytics |
| **Diagnóstico completo** | ❌ | ✅ diagnose_applies |
| **Candidatos parados** | ❌ (YAML) / ✅ (scope_config.py: get_smart_alerts) | ✅ stalled_applies (atenção/aviso/crítico por SLA) |
| **Timeline da candidatura** | ❌ | ✅ apply_timeline |
| **Top N candidatos** | ❌ | ✅ top_candidates, full_ranking |
| **Filtrar por score** | ❌ | ✅ filter_by_score |
| **Comparação de candidatos** | ✅ [LIA-LLM] com dados em contexto | ✅ compare_candidates |
| **Feedback de rejeição em lote** | ❌ | ✅ send_apply_reject_feedback |
| **Cache** | ❌ | ✅ AppliesCacheManager |
| **ReAct agent dedicado** | ❌ | ✅ react_agent.py |
| **Cards estruturados** | ❌ | ✅ cards.py |
| **Memória por domínio** | ConversationMemory global | ✅ AppliesConversationMemory |
| **send_email / send_whatsapp** | ❌ (YAML) / ✅ (scope_config.py) | ✅ Via autonomous |
| **schedule_interview** | ❌ (YAML) / ✅ (scope_config.py) | ✅ Via scheduling domain |

---

## 6. Prompt 4 — Funil de Talentos {#prompt-4}

### 6.0 Introdução

O **Prompt Expandido do Funil de Talentos** aparece em `/user/candidates` ou na sessão de sourcing (`/user/sourcing/{id}/chat`). É o contexto especializado em **busca e análise de candidatos** no banco de talentos.

**Ativação LIA:** `context_page: "sourcing"/"talent"` → `context_type: "talent_funnel"` → domínios `sourcing.yaml` + `analytics.yaml` → scope TALENT_FUNNEL.

**Ativação v5:** `domain: "sourced_profile_sourcing"` → `DomainOrchestrator.process_query(domain_id="sourced_profile_sourcing")` → `SourcedProfileSourcingDomain` → `SourcedProfileSourcingActions`.

**Para que serve:** buscar candidatos no banco interno e externo (Pearch AI), construir queries booleanas, analisar compatibilidade, gerar relatórios do pool, exportar candidatos, adicionar candidatos a vagas ou listas.

**Para que NÃO serve:** triar CVs de candidatos já em uma vaga, agendar entrevistas, criar vagas.

---

### 6.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: TALENT_FUNNEL — 9 tools, fonte: tool_registry_metadata.yaml)

**Query tools:**

| Tool | O que faz | Parâmetros | v5 equivalente |
|---|---|---|---|
| `search_candidates` | Busca candidatos no banco por query + filtros + paginação | `query`, `filters`, `limit`, `offset` | `search_candidates`, `filter_by_skill`, `filter_by_score` |
| `get_candidate_details` | Perfil completo do candidato com histórico de processos | `candidate_id`, `include_history` | `show_candidate_details` |
| `get_candidate_stats` | Estatísticas agregadas do pool de candidatos | `filters`, `group_by` | `count_candidates`, `average_score`, `score_distribution` |

**Action tools:**

| Tool | O que faz | Parâmetros | v5 equivalente |
|---|---|---|---|
| `add_candidate_to_vacancy` | Adiciona candidato ao processo seletivo de uma vaga `[ESCRITA]` | `candidate_id`, `vacancy_id`, `stage`, `notes` | Via autonomous domain |
| `shortlist_candidate` | Adiciona à lista de pré-selecionados para uma vaga `[ESCRITA]` | `candidate_id`, `vacancy_id`, `notes` | Via autonomous domain |
| `add_to_list` | Inclui candidato em lista de talentos nomeada `[ESCRITA]` | `candidate_id`, `list_name`, `notes` | Via autonomous domain |
| `export_candidates` | Exporta candidatos em CSV ou XLSX | `candidate_ids[]`, `format: csv\|xlsx`, `fields[]` | Via autonomous domain |
| `send_email` | Envia email para um ou mais candidatos `[ESCRITA]` | `to[]`, `subject`, `body`, `template_id` | Via autonomous domain |
| `send_whatsapp` | Envia mensagem WhatsApp para candidato `[ESCRITA]` | `phone`, `message`, `template_name` | Via autonomous domain |

#### [v5] Actions do domínio sourced_profile_sourcing (src/domains/sourced_profile_sourcing/actions/)

| Arquivo | Actions | Capacidade |
|---|---|---|
| `analysis.py` | `common_strengths`, `skill_gaps`, `diversity_analysis` | Pontos fortes, lacunas de skills, diversidade |
| `comparison.py` | `compare_candidates` | Comparação lado a lado de candidatos |
| `conversational.py` | `conversational` | Fallback conversacional sem API |
| `count.py` | `count_candidates`, `count_by_filter` | Contagem com filtros |
| `details.py` | `show_candidate_details` | Perfil completo do candidato |
| `distribution.py` | `language_distribution`, `education_distribution`, `gender_distribution`, `location_distribution`, `work_model_distribution` | 5 distribuições demográficas |
| `feedback.py` | `approve_candidate`, `reject_candidate`, `add_rating` | Ações sobre perfis do sourcing |
| `insights.py` | `analyze_skills`, `top_by_experience`, `work_model_specific` | Análises de insights |
| `report.py` | `generate_executive_report` (4 steps: planning→data_collection→analysis(LLM,temp=0.3)→formatting), `generate_top_candidates_report`, `summarize_search` | Relatórios |
| `score.py` | `average_score`, `score_distribution`, `score_above`, `top_candidates`, `priority_ranking` | Scoring e ranking |
| `search.py` | `search_candidates`, `filter_by_skill`, `filter_by_score`, `list_candidates`, `recent_candidates` | Busca e listagem |
| `search_improvement.py` | `analyze_search_improvement` | Análise de melhoria de busca |

**Componentes de suporte v5 do sourced_profile_sourcing domain:**
- `StatsManager` (`ACTIONS_USING_AGGREGATED` — frozenset de 26 ações): pré-computa stats agregadas antes de chamar o LLM
- `SourcingAPIClient` — cliente HTTP para Rails API
- `DynamicPromptBuilder` (max_actions_in_prompt=6, enable_cache=True)
- `fact_checker.py` — verificação de fatos nas respostas
- `fairness.py` — FairnessMetrics + SensitiveAttribute enum + SENSITIVE_FILTER_KEYS
- `smart_extractor.py` — extração inteligente de parâmetros
- `param_extractor.py` — extração de parâmetros da query
- `validators.py` — validação de entradas
- Agentes multi-tier (`agents/`): orchestrator, planner, router, search, detail, analytics, comparison, report, action

**Fairness v5 (sourced_profile_sourcing/fairness.py):**

| Componente | Detalhe |
|---|---|
| `FairnessMetrics` | Contadores: blocked_count, warnings_count, pii_scrubbed_count, exceptions_allowed |
| `SensitiveAttribute` enum | GENDER, AGE, RACE, ETHNICITY, DISABILITY, MARITAL_STATUS, RELIGION, NATIONALITY |
| `SENSITIVE_FILTER_KEYS` | gender, genero, sexo, age, idade, birth_date, race, raca, pcd, disability, marital, estado_civil, religion, religiao |
| `FairnessWarning` | Warning com attribute + message |
| `allow_sensitive_filters` | Flag no DomainContext (requer `sensitive_filter_justification`) |

#### [LIA-LLM] Capacidades conversacionais

Com dados do pool carregados na tela (`candidates[]`, `search_context`, `target_job`):

**Busca e Análise:**
- **Score de compatibilidade** — calcula score 0-100% com justificativa para cada candidato em contexto vs. vaga alvo
- **Ranking por compatibilidade** — ordena candidatos por fit com a vaga
- **Construção de queries booleanas** — sugere e refina: `Java AND AWS AND (senior OR pleno) NOT júnior`
- **Refinamento de busca** — se <5 resultados: propõe critérios menos restritivos; se >50: sugere filtros adicionais
- **Candidatos similares** — sugere busca por perfis similares a um candidato específico

**Analytics e Relatórios (analytics.yaml):**
- **Bias audit / Four-Fifths Rule** — analisa equidade de seleção por gênero, PCD, região, idade
- **Análise demográfica** — distribuição do pool por formação, idiomas, localidade, modelo de trabalho
- **Análise de skills** — skills mais comuns, lacunas vs. requisitos da vaga
- **Score médio do pool** — com mediana, faixa min-max, percentis
- **Relatório executivo** — combina demografias, scores, localização, skills, diversidade, formação
- Sempre dados agregados (LGPD-safe) — sem identificação individual em relatórios
- Alerta se amostra <30 registros (baixa confiabilidade estatística)

**Fontes de dados (sourcing.yaml):**
- **Banco interno LIA** — candidatos do ATS da empresa
- **Pearch AI** — 190M+ perfis externos (integração documentada no system prompt)
- Sempre cita a fonte de cada candidato retornado

---

### 6.2 Restrições OUT

| Capacidade | LIA — Por quê não está disponível | LIA — Para onde delegar | v5 — Disponível? |
|---|---|---|---|
| Triagem WSI de candidatos | `wsi_screening` não está em TALENT_FUNNEL | Prompt 3 (IN_JOB) | ⚠️ Via autonomous |
| Mover candidatos no pipeline | `update_candidate_stage` não está em TALENT_FUNNEL | Prompt 3 (IN_JOB) | ✅ Via applies domain |
| Agendar entrevistas | `schedule_interview` não está em TALENT_FUNNEL | Prompt 3 (IN_JOB) | ✅ scheduling domain |
| Criar ou editar vagas | `create_job`/`update_job` não estão em TALENT_FUNNEL | Prompt 2 (JOB_TABLE) | ✅ Via jobs/autonomous |
| Relatório genérico | `generate_report` não está em TALENT_FUNNEL | Prompt 1 (GLOBAL) | ✅ Via autonomous |
| Pearch AI | ✅ Disponível em LIA (sourcing.yaml) | — | ⚠️ Não como tool explícita no sourced_profile_sourcing |
| Queries booleanas | ✅ [LIA-LLM] | — | ⚠️ Suportado via busca, sem tool dedicada |
| Aprovação/rejeição de perfil | ❌ Sem tool no YAML | — | ✅ approve_candidate, reject_candidate, add_rating |
| Análise de melhoria de busca | ✅ [LIA-LLM] | — | ✅ analyze_search_improvement |
| Arquetipos de busca | ❌ | — | ✅ search_archetypes (via autonomous) |

---

### 6.3 Dados que coleta / gera

#### LIA — Inputs

- `context_page: "sourcing"/"talent"` — ativa TALENT_FUNNEL scope
- `entity_id` = `sourcing_id` — ID da sessão de sourcing ativa
- `entity_type: "sourcing"` — tipo da entidade em foco
- `candidates[]` — candidatos do resultado de busca atual (carregados na tela)
- `selected_candidate_ids[]` — candidatos selecionados
- `search_context` — configurações da busca (query, filtros)
- `target_job` — vaga-alvo para cálculo de score de compatibilidade

#### v5 — Inputs (DomainContext para sourced_profile_sourcing)

- `domain: "sourced_profile_sourcing"` — rota para o domínio
- `sourcing_id` (string) — ID de sourcing obrigatório para o domínio
- `workspace_id` (int) — isolamento multi-tenant
- `selected_ids[]` — perfis selecionados na tela
- `allow_sensitive_filters` (bool, default=False) — habilita filtros sensíveis com justificativa
- `sensitive_filter_justification` (string) — justificativa para filtros sensíveis
- `conversation_memory` — memória de sessão do sourcing domain
- `auth_token` — OTT para callbacks

#### LIA — Outputs (API)

- Candidatos buscados e filtrados do banco
- Candidatos adicionados a vaga / lista / shortlist
- Emails / WhatsApp enviados (com confirmação prévia)
- Candidatos exportados em CSV ou XLSX

#### LIA — Outputs (LLM)

- Ranking de candidatos com score de compatibilidade e justificativa
- Relatório executivo de sourcing (Markdown estruturado)
- Análise de diversidade com métricas Four-Fifths Rule
- Sugestão de refinamento de busca quando pool é inadequado

#### v5 — Outputs (DomainResponse)

- `message` (markdown) — resultado da ação formatado
- `data` — dados estruturados (candidatos, stats, distribuições, reports)
- `suggestions[]` — próximas ações (ex: "Ver detalhes do candidato", "Comparar top 3")
- Relatório executivo (4-step pipeline: planning → data_collection → LLM analysis (temp=0.3) → formatting)
- `FairnessWarning[]` — avisos de fairness quando filtros sensíveis são solicitados
- `metadata.cards[]` — cards estruturados

---

### 6.4 Arquitetura técnica — LIA

```
Frontend (context_page: "sourcing" | "talent")
    │
    ▼
ContextAdapter.from_talent_chat() / from_rest()
    context_type = "talent_funnel"
    entity_id    = sourcing_id
    entity_type  = "sourcing"
    candidates   = pool de candidatos da tela
    search_context = configuração da busca
    target_job   = vaga alvo (se existir)
    │
    ▼
MainOrchestrator.process()
    │
    └─ Orchestrator
          │
          ├─ CascadedRouter → domain_id: "sourcing" | "analytics" |
          │                    "sourcing_planner" | "sourcing_search" |
          │                    "sourcing_enrich" | "sourcing_engagement"
          │
          └─ DomainWorkflow → 2 YAMLs ativos:
                sourcing.yaml   ← busca de talentos (interno + Pearch AI)
                analytics.yaml  ← KPIs, relatórios, bias audit
                │
                └─ filter_tools_by_scope(TALENT_FUNNEL) → 9 tools

Agentes: orchestrator, recruiter_assistant, sourcing, analytics

Regras do domínio sourcing.yaml:
    Score de compatibilidade sempre com justificativa
    Nunca inferir gênero, etnia, idade por nome ou localização
    Se <5 resultados: propõe critérios menos restritivos
    Se >50 resultados: pergunta sobre filtro adicional
    Sempre cita a fonte: interno | Pearch AI | externo

Regras do domínio analytics.yaml:
    Dados sempre agregados (LGPD-safe)
    Destaca anomalias com contexto + recomendação
    Se amostra <30: indica baixa confiabilidade estatística
    Compara com benchmark setorial quando disponível
```

---

### 6.5 Arquitetura técnica — v5

```
Frontend (domain: "sourced_profile_sourcing")
OU HubPlanner detecta query sobre candidatos/sourcing
    │
    ▼
SourcedProfileSourcingDomain
    "Análise e ações sobre perfis de candidatos vinculados a um sourcing.
     Sempre requer sourcing_id no contexto."
    │
    ▼
DynamicPromptBuilder
    PromptConfig(max_actions_in_prompt=6, enable_cache=True)
    Injeta total_candidates + aggregated_stats no prompt
    │
    ▼
StatsManager
    ACTIONS_USING_AGGREGATED (frozenset de 26 ações):
        pré-computa e cacheia stats agregadas antes de chamar o LLM
        evita N+1 chamadas para análises demográficas e de scoring
    │
    ▼
SourcedProfileSourcingActions (src/domains/sourced_profile_sourcing/actions/):
    analysis.py:           common_strengths | skill_gaps | diversity_analysis
    comparison.py:         compare_candidates
    conversational.py:     conversational (fallback sem API call)
    count.py:              count_candidates | count_by_filter
    details.py:            show_candidate_details
    distribution.py:       language_distribution | education_distribution |
                           gender_distribution | location_distribution |
                           work_model_distribution
    feedback.py:           approve_candidate | reject_candidate | add_rating
    insights.py:           analyze_skills | top_by_experience | work_model_specific
    report.py:             generate_executive_report (4-step pipeline):
                               planning → data_collection → analysis (LLM, temp=0.3) → formatting
                           generate_top_candidates_report | summarize_search
    score.py:              average_score | score_distribution | score_above |
                           top_candidates | priority_ranking
    search.py:             search_candidates | filter_by_skill | filter_by_score |
                           list_candidates | recent_candidates
    search_improvement.py: analyze_search_improvement
    │
    ▼
fairness.py (FairnessMetrics, SensitiveAttribute, SENSITIVE_FILTER_KEYS)
    ← bloqueia/avisa filtros sensíveis; allow_sensitive_filters+justification para exceções
fact_checker.py
    ← verifica fatos nas respostas antes de retornar ao usuário
smart_extractor.py + param_extractor.py
    ← extração inteligente de parâmetros da query
    │
    ▼
Agentes multi-tier (src/domains/sourced_profile_sourcing/agents/):
    orchestrator.py ← coordena agentes especializados
    planner.py      ← planejamento de queries complexas
    router.py       ← roteamento para agente especializado
    search.py       ← agente de busca
    detail.py       ← agente de detalhes de candidato
    analytics.py    ← agente de analytics
    comparison.py   ← agente de comparação
    report.py       ← agente de relatórios
    action.py       ← agente de ações (approve/reject/rating)
    │
    ▼
SourcingAPIClient → ATS Rails API
```

---

### 6.6 Comparativo LIA × v5 — Funil de Talentos

| Dimensão | LIA (TALENT_FUNNEL, 9 tools YAML) | v5 (sourced_profile_sourcing) |
|---|---|---|
| **Busca de candidatos** | ✅ search_candidates, get_candidate_details | ✅ search_candidates, filter_by_skill, filter_by_score |
| **Stats do pool** | ✅ get_candidate_stats | ✅ count_candidates, average_score, score_distribution |
| **Adicionar a vaga/lista** | ✅ add_candidate_to_vacancy, shortlist_candidate, add_to_list | ✅ Via autonomous |
| **Exportação** | ✅ export_candidates (csv/xlsx) | ✅ Via autonomous |
| **Email / WhatsApp** | ✅ send_email, send_whatsapp | ✅ Via autonomous |
| **Pearch AI (190M+ perfis)** | ✅ Documentado em sourcing.yaml | ⚠️ Não documentado como tool explícita |
| **Queries booleanas** | ✅ [LIA-LLM] | ⚠️ Suportado via busca, sem tool dedicada |
| **Score de compatibilidade** | ✅ [LIA-LLM] 0-100% com justificativa | ✅ average_score, top_candidates, priority_ranking |
| **Análise demográfica** | ✅ [LIA-LLM] analytics.yaml | ✅ 5 distribution actions |
| **Four-Fifths Rule / bias audit** | ✅ [LIA-LLM] analytics.yaml | ✅ diversity_analysis |
| **Cache de stats** | ❌ | ✅ StatsManager (ACTIONS_USING_AGGREGATED — 26 ações) |
| **Relatório executivo** | ✅ via GLOBAL generate_report | ✅ generate_executive_report (4-step LLM, temp=0.3) |
| **Análise de melhoria de busca** | ✅ [LIA-LLM] | ✅ analyze_search_improvement |
| **Skill gaps** | ✅ [LIA-LLM] | ✅ skill_gaps |
| **Aprovação/rejeição de perfil** | ❌ Sem tool no YAML | ✅ approve_candidate, reject_candidate, add_rating |
| **Comparação de sourcings** | ❌ | ✅ get_multi_sourcing_stats (via autonomous) |
| **Arquetipos de busca** | ❌ | ✅ search_archetypes (via autonomous) |
| **Fairness metrics** | [LIA-LLM] FairnessGuard | ✅ FairnessMetrics + SensitiveAttribute (código) |
| **Fact checker** | ❌ | ✅ fact_checker.py |
| **Agentes especializados** | orchestrator, sourcing, analytics | ✅ 9 agentes especializados |
| **Candidate search pipeline** | ❌ | ✅ search_pipeline.py (multi-strategy, ThreadPoolExecutor) |

---

## 7. Tabela-resumo global (4 prompts × 10 dimensões) {#tabela-resumo}

| Dimensão | Prompt 1 — Flutuante | Prompt 2 — Tabela Vagas | Prompt 3 — Kanban | Prompt 4 — Funil Talentos |
|---|---|---|---|---|
| **context_page (LIA)** | `general`, `global` | `job`, `jobs`, `vacancies`, `wizard` | `pipeline`, `kanban` | `sourcing`, `talent` |
| **domain (v5)** | `null` + hub_mode | `"jobs"` | `"applies"` | `"sourced_profile_sourcing"` |
| **Scope + N° tools LIA (YAML)** | GLOBAL — 4 tools | JOB_TABLE — 13 tools | IN_JOB — 6 tools | TALENT_FUNNEL — 9 tools |
| **Domínios YAML LIA** | recruiter_assistant | job_management | cv_screening + pipeline_transition + interview_scheduling + communication | sourcing + analytics |
| **N° actions v5** | 73+ (13 módulos autonomous) | 17+ actions (7 arquivos) | 30+ actions (10 arquivos) | 32+ actions (12 arquivos) |
| **Domain routing LIA** | CascadedRouter (6 tiers) | CascadedRouter | CascadedRouter | CascadedRouter |
| **Domain routing v5** | HubPlanner (LLM + regex + 12 fast nav) | Domain direto + regex | Domain direto + cache | Domain direto + StatsManager |
| **Cache v5** | SessionStore (MAX_HISTORY=50) | TieredContextManager (Tier1/2) | AppliesCacheManager | StatsManager (26 ações) |
| **Memória v5** | ConversationSession | JobConversationMemory | AppliesConversationMemory | sourcing domain memory |
| **PendingAction** | ✅ Ambos | ✅ Ambos | ✅ Ambos | ✅ Ambos |
| **Buscar vagas (API)** | ❌ LIA | ✅ Ambos | ❌ LIA | ❌ LIA |
| **Criar/editar vagas (API)** | ❌ LIA | ✅ Ambos | ❌ LIA | ❌ LIA |
| **Buscar candidatos (API)** | ❌ LIA | ❌ Ambos | ❌ LIA | ✅ Ambos |
| **Mover candidatos (API)** | ❌ LIA | ❌ Ambos | ✅ Ambos | ❌ Ambos |
| **Score WSI 7 blocos** | ❌ | ❌ | ✅ LIA [LLM] | ❌ |
| **FairnessGuard** | ✅ Ambos | ✅ Ambos | ✅ Ambos (+ YAML) | ✅ Ambos |
| **Benchmark salarial** | ❌ | ✅ LIA (YAML) | ❌ | ❌ |
| **JD gerada por IA** | ❌ | ✅ Ambos | ❌ | ❌ |
| **Wizard conversacional** | ❌ | ✅ LIA [LLM] | ❌ | ❌ |
| **Gerar relatório** | ✅ Ambos | ✅ Ambos | ❌ LIA | ✅ Ambos |
| **Entrevista CBI** | ❌ | ❌ | ✅ LIA | ❌ |
| **Email/WhatsApp via API** | ❌ LIA | ❌ Ambos | ❌ LIA (YAML) / ✅ v5 | ✅ Ambos |
| **Bias audit** | ❌ LIA | ❌ LIA | ❌ LIA | ✅ Ambos |
| **Cache otimizado** | ✅ v5 (SessionStore) | ✅ v5 (Tier1/2) | ✅ v5 (AppliesCache) | ✅ v5 (StatsManager) |
| **Progresso write_plan** | ❌ LIA | ❌ LIA | ❌ LIA | ❌ LIA |
| **Streaming SSE** | ⚠️ WebSocket LIA | ⚠️ WebSocket LIA | ⚠️ WebSocket LIA | ⚠️ WebSocket LIA |
| **CircuitBreaker** | ❌ LIA | ✅ v5 | ✅ v5 | ✅ v5 |
| **ReAct agent** | ✅ v5 (autonomous) | ❌ v5 (LLM direto) | ✅ v5 (react_agent.py) | ❌ v5 (agentes multi-tier) |
| **Fallback automático** | ❌ LIA | ❌ LIA | ❌ LIA | ❌ LIA |
| **LGPD compliance** | ✅ Ambos | ✅ Ambos | ✅ Ambos | ✅ Ambos |

---

## 8. Domínios v5 exclusivos (Scheduling, Insights, Evaluation) {#dominios-v5-exclusivos}

Os domínios abaixo **não têm equivalente direto** nos 4 prompts LIA. São domínios v5 que ampliam as capacidades além do mapeamento LIA 1:1.

---

### 8.1 Domínio Scheduling — Agendamento de Entrevistas

**domain_id:** `scheduling` | **Ativação:** `domain: "scheduling"` ou HubPlanner detecta padrão de agendamento

**Descrição:** Agendamento de entrevistas: direto, self-scheduling (link), disponibilidade, agenda diária, cancelamento, remarcação, lote.

#### 8.1.1 Actions disponíveis (src/domains/scheduling/actions/)

| Action | Tipo | Descrição |
|---|---|---|
| `schedule_interview` | ACTION | Agenda entrevista completa: direto (data/hora) ou self-scheduling (link para o candidato escolher) |
| `check_availability` | QUERY | Consulta horários disponíveis sem agendar |
| `list_interviews` | QUERY | Lista entrevistas agendadas (por candidato, vaga ou período) |
| `daily_agenda` | QUERY | Agenda do dia: todas as entrevistas + compromissos do recrutador |
| `cancel_interview` | ACTION | Cancela entrevista com motivo + notificação ao candidato |
| `reschedule_interview` | ACTION | Remarca data/hora de entrevista existente |

#### 8.1.2 Padrões de detecção (regex em SchedulingDomain)

| Regex | Intent mapeado |
|---|---|
| `_SCHEDULE_INTENT_PATTERN` | schedule_interview: "agendar entrevista", "marcar call", "manda link de agendamento" |
| `_CANCEL_PATTERN` | cancel_interview: "cancelar", "desmarcar" |
| `_RESCHEDULE_PATTERN` | reschedule_interview: "remarcar", "reagendar", "mudar horário" |
| `_DAILY_AGENDA_PATTERN` | daily_agenda: "agenda de hoje", "o que tenho hoje", "entrevistas da semana" |
| `_AVAILABILITY_PATTERN` | check_availability: "disponibilidade", "horários disponíveis" |

#### 8.1.3 Componentes de suporte

- `SchedulingPrompts` — prompts do domínio
- `SchedulingConversationMemory` — memória de sessão
- `graph.py` — LangGraph StateGraph para fluxo de agendamento multi-step
- `session.py` — estado de sessão de agendamento (scheduling session)
- `inference.py` — inferência de parâmetros de agendamento
- `cards.py` — cards de confirmação de entrevista
- `formatters/` — confirmation_formatter, slots_formatter
- `STATEFUL_ACTIONS = {"schedule_interview"}` — action com estado (multi-turn)

#### 8.1.4 HubOrchestrator bypass para scheduling

Quando uma sessão de agendamento está ativa, o HubOrchestrator bypassa o HubPlanner e roteia direto para scheduling:

```
HubOrchestrator:
    if _has_active_scheduling_session(session) AND _is_scheduling_continuation(query):
        → _route_to_scheduling(session, query, context_data)  # bypass HubPlanner
```

#### 8.1.5 LIA × v5 — Scheduling

| Dimensão | LIA | v5 |
|---|---|---|
| **Domínio dedicado** | ❌ (parte do interview_scheduling.yaml + scope_config.py) | ✅ SchedulingDomain isolado |
| **Self-scheduling link** | ❌ | ✅ schedule_interview (self-scheduling mode) |
| **Agenda diária** | ❌ | ✅ daily_agenda |
| **Cancelamento** | ❌ (YAML) / ✅ (scope_config.py) | ✅ cancel_interview |
| **Remarcação** | ❌ (YAML) / ✅ (scope_config.py) | ✅ reschedule_interview |
| **LangGraph** | ❌ | ✅ graph.py (scheduling state machine) |
| **Session bypass** | ❌ | ✅ _has_active_scheduling_session() |
| **CBI condução** | ✅ interview_scheduling.yaml | ⚠️ Via autonomous |

---

### 8.2 Domínio Insights — Analytics Consolidado

**domain_id:** `insights` | **Ativação:** `domain: "insights"` ou ROUTING_KEYWORDS `\b(?:report|relat[oó]rio|gargalos?|comparar|métricas?)\b`

**Descrição:** Insights agregados de todas as áreas: briefings, reports, métricas, alertas, comparações, performance, tendências. Visão panorâmica do recrutamento.

#### 8.2.1 Actions disponíveis (src/domains/insights/actions/)

| Action | Tipo | Descrição |
|---|---|---|
| `daily_briefing` | AGGREGATE | Resumo executivo do dia: vagas, candidaturas, agenda, alertas |
| `job_status_report` | ANALYZE | Report completo de uma vaga: funil, velocidade, qualidade, finalistas |
| `metrics_query` | QUERY | Consulta métricas específicas: conversão, velocidade, volume, fontes |
| `alerts_check` | QUERY | Verifica alertas pendentes por severidade |
| `candidate_comparison` | ANALYZE | Comparação detalhada de candidatos |
| `weekly_summary` | AGGREGATE | Resumo da semana: vagas abertas/fechadas, candidaturas, destaques |
| `pipeline_bottleneck` | ANALYZE | Gargalos do pipeline: etapas com maior tempo médio, taxa de rejeição |
| `trend_analysis` | ANALYZE | Análise de tendências: volume ao longo do tempo, variações sazonais |
| `performance_metrics` | QUERY | Métricas de performance: time-to-fill, time-to-hire, taxa de conversão |

#### 8.2.2 Padrões de detecção (regex _INSIGHTS_ACTION_PATTERNS)

| Regex | Action |
|---|---|
| `\breport\b` / `\brelat[oó]rio\b` | `job_status_report` |
| `\bgargalos?\b` / `\bfunil\b` | `pipeline_bottleneck` |
| `\bcompar` | `candidate_comparison` |
| `\bmetricas?\b` / `\bm[eé]trica` | `metrics_query` |

#### 8.2.3 Componentes de suporte

- `InsightsAPIClient` — cliente para busca de briefing data
- `InsightsConversationMemory` — memória de sessão
- `CircuitBreaker` — `circuit_breaker_call()` protege todas as actions
- Formatters: `briefing_formatter`, `metrics_formatter`, `report_formatter`, `comparison_formatter`
- `metrics_config.py` — configuração de métricas

#### 8.2.4 Exemplo de BriefingAction (src/domains/insights/actions/briefing.py)

```python
def execute(self, params, context):
    data = api.get_briefing_data()          # Dados agregados da API
    data["date"] = datetime.now().isoformat()
    message = format_briefing(data)         # Formata em markdown estruturado
    return DomainResponse(
        success=True,
        message=message,
        data={"raw": data},
        suggestions=build_suggestions("daily_briefing", params),
    )
```

#### 8.2.5 LIA × v5 — Insights

| Dimensão | LIA | v5 |
|---|---|---|
| **Briefing diário via API** | ❌ | ✅ daily_briefing (InsightsDomain) |
| **Report de vaga** | ❌ direto / ✅ via generate_report + [LLM] | ✅ job_status_report |
| **Métricas via API** | ✅ get_pipeline_stats (JOB_TABLE) | ✅ metrics_query |
| **Alertas via API** | ❌ GLOBAL / ✅ IN_JOB (scope_config) | ✅ alerts_check |
| **Resumo semanal** | ❌ | ✅ weekly_summary |
| **Gargalos pipeline** | ❌ | ✅ pipeline_bottleneck |
| **Tendências** | ❌ | ✅ trend_analysis |
| **Performance metrics** | ❌ | ✅ performance_metrics |
| **CircuitBreaker** | ❌ | ✅ circuit_breaker_call() |
| **Domínio isolado** | ❌ (distribuído nos 4 prompts) | ✅ InsightsDomain isolado |

---

### 8.3 Domínio Evaluation — Avaliação de Candidatos em Entrevista

**domain_id:** `evaluation` | **Ativação:** `domain: "evaluation"` ou ROUTING_KEYWORDS `\b(?:avali[aç]|teste|prova|questionário)\b`

**Descrição:** Processa e avalia respostas de candidatos em entrevistas de emprego via chat (LangGraph-based).

#### 8.3.1 Actions disponíveis (src/domains/evaluation/domain.py)

| Action | Tipo | Descrição |
|---|---|---|
| `evaluate_response` | ANALYZE | Avalia a resposta de um candidato a uma pergunta da entrevista |
| `classify_intent` | ANALYZE | Classifica o tipo de mensagem do candidato (resposta, pergunta, fuga) |

#### 8.3.2 Arquitetura (LangGraph StateGraph)

```
EvaluationDomain.execute_action("evaluate_response")
    │
    ▼
create_initial_state(InterviewState)
    ← State: pergunta, resposta do candidato, critérios de avaliação
    │
    ▼
get_interview_graph() → LangGraph StateGraph
    Nodes: avaliação por critério → síntese → formatação
    │
    ▼
EvaluationResponse {
    evaluation_details: EvaluationDetails,
    ai_response: AIResponse,
    next_question_hint: NextQuestionHint,
}
```

#### 8.3.3 Modelos (src/domains/evaluation/models.py)

| Modelo | Campos |
|---|---|
| `EvaluationResponse` | evaluation_details, ai_response, next_question_hint |
| `AIResponse` | message, tone, is_closing |
| `EvaluationDetails` | scores por critério, feedback, red_flags |
| `NextQuestionHint` | suggested_question, rationale |

#### 8.3.4 Segurança e fairness (src/domains/evaluation/security.py)

- `security.py` — proteções específicas para avaliação de candidatos
- System prompt: "Você é um sistema de avaliação de candidatos para entrevistas de emprego. Sua função é avaliar respostas de forma justa, objetiva e sem vieses."

#### 8.3.5 LIA × v5 — Evaluation

| Dimensão | LIA | v5 |
|---|---|---|
| **Condução de entrevista CBI** | ✅ interview_scheduling.yaml | ⚠️ Via autonomous |
| **Avaliação de respostas via LangGraph** | ❌ | ✅ EvaluationDomain (evaluate_response) |
| **Classificação de intenção do candidato** | ❌ | ✅ classify_intent |
| **Next question hint** | ❌ | ✅ NextQuestionHint model |
| **Domínio isolado** | ❌ (parte do interview_scheduling.yaml) | ✅ EvaluationDomain isolado |
| **Security module** | FairnessGuard global | ✅ security.py dedicado |
| **Integração interview_ai/** | ❌ | ✅ interview_ai/ (Twilio, Gemini, áudio, beta_call) |

---

### 8.4 Interview AI — Entrevistas por Voz (v5 extra-domain)

O v5 contém um módulo `interview_ai/` separado dos domínios principais, com capacidades de entrevistas via voz e Twilio:

| Módulo | Capacidade |
|---|---|
| `interview_ai/main.py` | FastAPI routes para entrevistas |
| `interview_ai/interview_session.py` | Sessão de entrevista com estado |
| `interview_ai/evaluation_engine.py` | Engine de avaliação de respostas |
| `interview_ai/gemini_client.py` | Integração com Gemini para transcrição/avaliação |
| `interview_ai/twilio_client.py` | Integração Twilio para entrevistas por telefone |
| `interview_ai/audio.py` | Processamento de áudio |
| `interview_ai/prompt_builder.py` | Construção de prompts para entrevista |
| `interview_ai/report_generator.py` | Geração de relatório pós-entrevista |
| `interview_ai/routes/` | Routes: evaluation, interview, reports, speech, twilio |
| `interview_ai/beta_call.py` | Chamadas beta via Twilio |

**LIA equivalente:** `wsi_screening` tool no scope IN_JOB com `screening_type: voice|text|video` — mas sem integração Twilio explícita.

---

## 9. Canal Microsoft Teams — Bot e Notificações {#teams}

### 9.0 Visão Geral

O canal **Microsoft Teams** permite que o recrutador interaja com a LIA **diretamente dentro do Teams**, sem precisar abrir o navegador na plataforma WeDOTalent. A LIA tem um **Teams Bot bidirecional** completo — registrado no Azure Bot Framework — que recebe mensagens do recrutador no Teams, processa com o agente LIA e responde de volta no chat.

Adicionalmente, a LIA usa o canal Teams como **canal de notificação proativa** (outgoing webhook), enviando alertas, Adaptive Cards com ações, lembretes de entrevista e atualizações de candidatos para canais e chats do Teams.

**Resumo das implementações:**

| Componente | Arquivo(s) | Capacidade |
|---|---|---|
| **Teams Bot Framework** | `services/teams_bot.py` | Bot bidirecional completo via Bot Framework SDK |
| **Simple Teams Bot** | `services/teams_simple.py` | Bot bidirecional via REST API (sem SDK) |
| **Teams API Router** | `api/v1/teams.py` | 4 endpoints: messages, webhook, audit-logs, health |
| **Teams Service (outgoing)** | `services/teams_service.py` | 6 métodos de envio via Incoming Webhook |
| **Microsoft Graph Router** | `api/v1/microsoft_graph.py` | Criar reuniões Teams + eventos de calendário |
| **Communication Domain** | `domains/communication/domain.py` | `send_teams_message` como action mapeada |
| **Communication YAML** | `prompts/domains/communication.yaml` | Teams no `scope_in` com intent examples |

**Credenciais necessárias:**
- `MICROSOFT_APP_ID` + `MICROSOFT_APP_PASSWORD` → Teams Bot Framework (bidirecional)
- `TEAMS_WEBHOOK_URL` → Incoming Webhook (notificações outgoing)
- `TEAMS_WEBHOOK_SECRET` → HMAC-SHA256 para segurança do webhook de Adaptive Cards
- `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` + `AZURE_TENANT_ID` → Microsoft Graph API (calendário, reuniões Teams)

---

### 9.1 Teams Bot Bidirecional — Recrutador conversa com a LIA via Teams

A LIA tem um **Teams Bot registrado no Azure** que permite conversação bidirecional: o recrutador digita no Teams e a LIA responde.

**Fluxo de uma mensagem do recrutador via Teams:**

```
Recrutador digita mensagem no Microsoft Teams
    │
    ▼
Microsoft Bot Framework (Azure)
    Valida JWT token da mensagem
    │
    ▼
POST /api/v1/teams/messages (LIA FastAPI)
    Valida JWT: bot_auth.validate_token(authorization, MICROSOFT_APP_ID)
    Se inválido → HTTP 401
    │
    ▼
simple_teams_bot.process_activity(activity)
    activity.type == "message" → _handle_message()
        Extrai texto do recrutador
        → TODO: Integrar com agente LIA (em integração)
        → Atualmente envia acknowledgment
    activity.type == "conversationUpdate" → _handle_conversation_update()
        Novo membro → mensagem de boas-vindas da LIA
    activity.type == "invoke" → _handle_invoke()
        Ação de Adaptive Card
    │
    ▼
simple_teams_bot.send_message(service_url, conversation_id, text)
    GET token OAuth2: POST login.microsoftonline.com/.../token
        grant_type: client_credentials
        scope: https://api.botframework.com/.default
    POST {service_url}/v3/conversations/{id}/activities
    Headers: Authorization: Bearer {token}
    │
    ▼
Recrutador recebe resposta da LIA no Teams

Armazenamento:
    _store_conversation_reference(activity, db)
        → TeamsConversation (PostgreSQL):
            conversation_id, service_url, tenant_id,
            channel_id, user_id, user_name, user_aad_object_id,
            conversation_reference (JSON completo), last_message_at
    _log_teams_message(activity, db)
        → TeamsMessage (PostgreSQL): log da mensagem
```

**Mensagem de boas-vindas (quando bot adicionado ao chat):**

```
"Olá {nome}! 👋

Sou a LIA, assistente de recrutamento da WedoTalent.

Posso te ajudar a:
- Criar vagas
- Buscar candidatos
- Agendar entrevistas
- Organizar sua agenda de recrutamento

Como posso te ajudar hoje?"
```

**Status de integração:**
- Bot Framework SDK: ✅ Implementado (`botbuilder-core`, `botbuilder-schema`)
- Simple Bot (REST API): ✅ Implementado
- Recepção de mensagens: ✅ Implementado
- Boas-vindas automáticas: ✅ Implementado
- Processamento com agente LIA: ⚠️ Em integração (`TODO: Integrate with LIA conversation agent`)
- Armazenamento de conversation reference: ✅ Implementado (PostgreSQL)
- Envio de resposta: ✅ Implementado

---

### 9.2 Adaptive Cards — Recrutador age no Teams sem abrir a plataforma

As **Adaptive Cards** são cards interativos enviados ao recrutador no Teams com botões de ação. O recrutador clica em "Aprovar" ou "Rejeitar" diretamente no Teams — sem abrir a plataforma web — e a LIA processa a ação automaticamente.

**Endpoint de webhook de Adaptive Cards:**

```
POST /api/v1/teams/webhook
Headers:
    X-Teams-Signature: sha256={HMAC-SHA256 do body com TEAMS_WEBHOOK_SECRET}
    X-Company-ID: {company_id} (opcional)
```

**5 ações suportadas:**

| Ação (TeamsCardAction) | Trigger | O que a LIA faz |
|---|---|---|
| **approve** | Recrutador clica "Aprovar" no card | Dispara triagem WhatsApp para o candidato via `communication_dispatcher.send_whatsapp()` |
| **reject** | Recrutador clica "Rejeitar" | Registra rejeição no audit log |
| **schedule** | Recrutador agenda entrevista | Registra agendamento com data/hora |
| **reschedule** | Recrutador reagenda | Registra novo agendamento |
| **request_info** | Recrutador pede mais info | Registra solicitação |

**Fluxo da ação "approve" (o mais complexo):**

```
Recrutador clica "Aprovar" no Adaptive Card no Teams
    │
    ▼
POST /api/v1/teams/webhook
    Payload: { action: "approve", candidate_id, candidate_name,
               candidate_phone, vacancy_id, vacancy_title,
               company_id, recruiter_id, recruiter_name, notes }
    │
    ▼
_verify_teams_webhook_signature(body, X-Teams-Signature)
    HMAC-SHA256 com TEAMS_WEBHOOK_SECRET
    produção: secret obrigatório (HTTP 403 se ausente)
    desenvolvimento: sem secret → aceita tudo (warning)
    │
    ▼
_handle_approve_action(payload, db)
    │
    ├─► _start_whatsapp_screening()
    │       communication_dispatcher.send_whatsapp(
    │           to_phone=candidate_phone,
    │           message="Olá {nome}! Você foi pré-aprovado...
    │                    Responda SIM para iniciar triagem"
    │       )
    │       communication_history_service.log_communication(
    │           type="screening_invite", channel="whatsapp",
    │           trigger="teams_adaptive_card"
    │       )
    │
    └─► _log_teams_action_audit(action="approve", result, actor, ...)
            TeamsActionAuditLog (PostgreSQL):
                id, action, actor_id, actor_name, candidate_id,
                vacancy_id, company_id, result, details{}, created_at

Response: { success, action, message, screening_initiated, audit_id, candidate_id, timestamp }
```

**Tipos de Adaptive Cards geradas pela LIA:**

| Tipo (`notification_type`) | Trigger | Campos no card |
|---|---|---|
| `approval_needed` | Candidato aguarda aprovação | Mensagem + botões "Aprovar" / "Rejeitar" |
| `interview_scheduled` | Entrevista agendada | FactSet: Candidato, Vaga, Data/Hora + botão "Ver Detalhes" |
| Default (genérico) | Qualquer notificação | Título + mensagem |

---

### 9.3 Teams Service — Notificações Outgoing via Incoming Webhook

A `TeamsService` usa **Incoming Webhooks do Teams** para enviar notificações de saída (LIA → Teams channel). Independente do Bot Framework — funciona sem `MICROSOFT_APP_ID`.

**Configuração:** `TEAMS_WEBHOOK_URL` env var (URL do Incoming Webhook criado no canal Teams)

**6 métodos de envio:**

| Método | O que envia | Payload Teams |
|---|---|---|
| `send_message(text, title, subtitle)` | Texto simples | `MessageCard` com `@type` + `@context` |
| `send_card(card)` | Adaptive Card | `message` com `attachments[contentType: adaptive]` |
| `send_adaptive_card(card_payload)` | Adaptive Card (alternativo) | `message` com `attachments` |
| `send_alert(title, message, severity, facts, actions)` | Alerta estruturado | Adaptive Card com FactSet + botões |
| `send_candidate_notification(candidate, event, job, action_url)` | Update de candidato | Alert severity INFO + FactSet + botão "Ver Detalhes" |
| `send_interview_reminder(candidate, job, time, interviewer, meeting_url)` | Lembrete de entrevista | Alert severity INFO + FactSet: Candidato/Vaga/Horário/Entrevistador + botão "Entrar na Reunião" |

**5 níveis de severidade com cores e ícones:**

| Severity | Ícone | Cor (hex) | Quando usar |
|---|---|---|---|
| INFO | ℹ️ | #0078D4 (azul Teams) | Atualizações informativas |
| SUCCESS | ✅ | #107C10 (verde) | Ações concluídas com sucesso |
| WARNING | ⚠️ | #FFB900 (amarelo) | Alertas que precisam de atenção |
| ERROR | ❌ | #D83B01 (laranja) | Erros não críticos |
| CRITICAL | 🚨 | #E81123 (vermelho) | Erros críticos que exigem ação imediata |

**Modo desenvolvimento:** se `TEAMS_WEBHOOK_URL` não configurado → mensagens são logadas (não enviadas), retorna `{ success: true, mode: "development" }`.

---

### 9.4 Microsoft Graph Router — Reuniões Teams via Calendar

A LIA tem um router dedicado para **criar reuniões Teams** integradas ao Microsoft Calendar, usado pelo domínio de agendamento (`interview_scheduling`).

**Endpoint principal:**
```
POST /api/v1/microsoft/meeting
Body: {
    organizer_email: "recrutador@empresa.com",
    subject: "Entrevista - João Silva - Dev Python Senior",
    start_time: "2026-03-25T14:00:00",
    duration_minutes: 60,
    attendees: [{ email, name, type: "required"|"optional" }],
    body_content: "Olá! Segue o link para a entrevista.",
    timezone: "America/Sao_Paulo",
    send_invites: true
}
Response: {
    id, join_url, join_web_url, subject,
    start_time, end_time, organizer_email,
    attendees[], calendar_event_id, dial_in_url
}
```

**Outros endpoints Microsoft Graph:**
```
GET  /api/v1/microsoft/status        → status da conexão + info da organização
GET  /api/v1/microsoft/bookings      → listar Microsoft Bookings businesses
POST /api/v1/microsoft/bookings/appointment → criar appointment no Bookings
```

**Credenciais:** `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` + `AZURE_TENANT_ID`

---

### 9.5 Communication Domain — send_teams_message como ação mapeada

O domínio `communication` (`domain.py`) mapeia palavras-chave do recrutador para a ação `send_teams_message`:

**Keywords mapeadas:**
```python
"enviar teams"    → send_teams_message
"mensagem teams"  → send_teams_message
"teams"           → send_teams_message
"notificar teams" → send_teams_message
```

**Regras do communication.yaml (scope_in + behavioral_rules):**
- `scope_in` inclui explicitamente "Notificações Microsoft Teams"
- Intent example: *"notificar time no Teams sobre candidato aprovado"*
- Toda mensagem gerada por IA inclui rodapé de origem ("Mensagem gerada com assistência de IA pela LIA")
- LGPD: nunca envia sem consentimento registrado
- Confirmação obrigatória antes de envios em massa (>10 destinatários)
- Feedback de rejeição: profissional, encorajador, sem detalhar motivos específicos

---

### 9.6 Dados que coleta / gera

#### Dados coletados (inputs)

| Fonte | Dado | Onde é armazenado |
|---|---|---|
| Bot Framework JWT | Autenticação do recrutador Teams | Validado, não persistido |
| Activity payload | `conversation_id`, `service_url`, `tenant_id`, `channel_id`, `user_id`, `user_name`, `user_aad_object_id` | `TeamsConversation` (PostgreSQL) |
| Activity payload | Texto da mensagem, timestamp, `activity_id` | `TeamsMessage` (PostgreSQL) |
| Adaptive Card action | `action`, `candidate_id`, `candidate_name`, `candidate_phone`, `vacancy_id`, `recruiter_id`, `recruiter_name`, `notes`, `scheduled_date` | `TeamsActionAuditLog` (PostgreSQL) |
| Incoming Webhook | `TEAMS_WEBHOOK_URL` (canal Teams de destino) | Env var, não persistido |

#### Dados gerados (outputs)

| Tipo | Formato | Destino |
|---|---|---|
| Resposta de chat | Texto Markdown (Bot Framework `Activity`) | Chat do recrutador no Teams |
| Mensagem de boas-vindas | Texto formatado com Markdown | Chat do recrutador quando bot adicionado |
| Adaptive Card | JSON Adaptive Card v1.4 (aprovação / entrevista / genérico) | Chat/canal do recrutador |
| Notificação de candidato | Adaptive Card com FactSet + botão "Ver Detalhes" | Canal Teams (Incoming Webhook) |
| Lembrete de entrevista | Adaptive Card com FactSet + botão "Entrar na Reunião" | Canal Teams (Incoming Webhook) |
| Alerta de severidade | Adaptive Card com cor + ícone de severidade | Canal Teams (Incoming Webhook) |
| Invite WhatsApp (trigger) | Mensagem WhatsApp via `communication_dispatcher` | Candidato (não Teams) |
| Reunião Teams | `join_url`, `join_web_url`, calendar event | Calendário do organizador + attendees |
| Audit log | `TeamsActionAuditLog`: action, result, actor, candidate, vacancy, company, details, timestamp | PostgreSQL |

---

### 9.7 Comparativo LIA × v5 — Canal Microsoft Teams

| Dimensão | LIA | v5 |
|---|---|---|
| **Teams Bot bidirecional** | ✅ Bot Framework SDK (`botbuilder-core`) + Simple Bot REST API | ❌ Sem bot dedicado (arquitetura suporta via RabbitMQ) |
| **Receber mensagens do Teams** | ✅ `POST /api/v1/teams/messages` com JWT validation | ❌ Não implementado |
| **Enviar resposta no Teams** | ✅ `SimpleTeamsBot.send_message()` via Bot Framework REST API | ❌ Não implementado |
| **Mensagem de boas-vindas** | ✅ Auto: "Olá! Sou a LIA..." quando bot adicionado | ❌ |
| **Processamento com agente** | ⚠️ Em integração (TODO no código) | ❌ |
| **Adaptive Cards** | ✅ `_create_adaptive_card()`: approval_needed, interview_scheduled, genérico | ⚠️ `cards[]` no payload de `send_teams_message`, dependente do Rails |
| **Adaptive Card actions (webhook)** | ✅ `POST /api/v1/teams/webhook`: approve, reject, schedule, reschedule, request_info | ❌ Não implementado |
| **HMAC-SHA256 no webhook** | ✅ `TEAMS_WEBHOOK_SECRET` + produção obrigatório | ❌ |
| **WhatsApp trigger via Teams** | ✅ Approve → `communication_dispatcher.send_whatsapp()` (triagem WSI) | ❌ |
| **Audit trail PostgreSQL** | ✅ `TeamsActionAuditLog`: action, actor, candidate, vacancy, result | ✅ `APICallRecord` em DomainContext |
| **Conversation reference storage** | ✅ `TeamsConversation` (PostgreSQL): para proactive messaging | ❌ |
| **Proactive messaging** | ✅ `TeamsBot.send_proactive_message()` via stored conversation reference | ✅ ProactiveDetector (5 checks) + ProactiveNotifier |
| **Notificações outgoing (Incoming Webhook)** | ✅ `TeamsService`: 6 métodos, 5 severidades, Adaptive Cards | ✅ `POST /users/microsoft_graph_auth/send_teams_message` (via Microsoft Graph OAuth) |
| **Microsoft Graph (calendário)** | ✅ `microsoft_graph_service.py`: criar reuniões Teams + calendar events + Bookings | ❌ Não implementado no Python (Rails tem Graph Auth OAuth) |
| **OAuth Microsoft 365** | ✅ `AZURE_CLIENT_ID/SECRET/TENANT_ID` (Graph API) | ✅ `useMicrosoftAuth.ts` + OAuth PKCE no frontend |
| **Communication YAML** | ✅ scope_in + intent_examples + behavioral_rules | ✅ system_prompt (context dos prompts) |
| **Teams como canal OUT** | ✅ Incoming Webhook (`TEAMS_WEBHOOK_URL`) | ✅ Microsoft Graph Auth endpoint |
| **Lembrete de entrevista** | ✅ `send_interview_reminder(candidate, job, time, interviewer, meeting_url)` | ❌ |
| **Notificação de candidato** | ✅ `send_candidate_notification(candidate, event, job, action_url)` | ❌ |
| **Feedback de rejeição LGPD** | ✅ Regras no communication.yaml | ✅ `send_apply_reject_feedback` (applies domain) |
| **Proactive checks automáticos** | ❌ (sem ProactiveDetector autônomo) | ✅ 5 checks: aging, stale, feedback, evaluations, bottlenecks |


---

## 10. Glossário técnico {#glossario}

| Termo | Definição |
|---|---|
| **context_page** | Campo enviado pelo frontend junto com cada mensagem. Determina qual scope de tools será ativado na LIA. |
| **context_type** | Tipo normalizado de contexto, mapeado pelo `ContextAdapter` a partir do `context_page` via `PAGE_TO_CONTEXT_TYPE`. |
| **scope** | Conjunto de tools disponíveis para o LLM em um contexto. Definido em `tool_registry_metadata.yaml` (declarativo) e `scope_config.py` (enforcement de runtime). |
| **tool_registry_metadata.yaml** | Fonte declarativa de metadados das tools LIA: nome, description, allowed_agents, scope, version, parameters. Usado pelo task spec desta análise. |
| **scope_config.py** | `app/tools/scope_config.py` — Fonte executável de runtime: `SCOPE_TOOL_MAPPING` + `filter_tools_by_scope()`. Importado diretamente pelo `orchestrator.py`. Tem precedência sobre o YAML em runtime. |
| **CascadedRouter** | Componente LIA de roteamento de domínio por intenção da mensagem. 6 tiers: memory (pronomes) → LRU in-process → Redis → VectorSemanticCache (pgvector ≥0.92) → FastRouter (regex/keyword) → LLM (Haiku→Sonnet→Opus) → clarification. |
| **HubPlanner** | Componente v5 equivalente ao CascadedRouter. Analisa query com PLANNER_SYSTEM_PROMPT, detecta FAST_NAV_PATTERNS (12 regex), MULTI_INTENT_RE, gera HubExecutionPlan com HubTask[] paralelas. |
| **MessageRouter** | Entry point v5. 3 caminhos: hub_mode=True → HubOrchestrator; domain=X → DomainOrchestrator; nenhum → workflow_orchestrator. Adiciona OTT e timing ao response. |
| **HubOrchestrator** | Orquestrador principal v5 (hub_mode=True). Gerencia: injection detection, SessionStore, PendingAction, scheduling bypass, HubPlanner, HubExecutor, context extraction. |
| **MainOrchestrator** | Entry point único da LIA: FairnessGuard → PendingAction → ActionExecutor → Orchestrator (CascadedRouter + DomainWorkflow). |
| **FairnessGuard** | Camada de proteção anti-discriminação executada ANTES de qualquer processamento. Bloqueia: critérios por gênero, etnia, idade, estado civil, nome, localização. |
| **FairnessMetrics** | Classe v5 em sourced_profile_sourcing/fairness.py. Contadores de: blocked_count, warnings_count, pii_scrubbed_count, exceptions_allowed. |
| **SensitiveAttribute** | Enum v5: GENDER, AGE, RACE, ETHNICITY, DISABILITY, MARITAL_STATUS, RELIGION, NATIONALITY. |
| **SENSITIVE_FILTER_KEYS** | Set v5 de chaves sensíveis bloqueadas: gender, genero, sexo, age, idade, birth_date, race, raca, pcd, disability, marital, estado_civil, religion, religiao. |
| **DomainWorkflow** | Executa PRE_CHECK → domain action → POST_CHECK. Usa ReAct agent para chamadas de tools. |
| **DomainOrchestrator** | Componente v5 equivalente ao DomainWorkflow da LIA. Roteia `domain_id` para `DomainPrompt` correspondente. |
| **PlanDetector** | Componente LIA que detecta queries multi-step e gera ExecutionPlan (análogo ao MULTI_INTENT_RE do v5, mas sequencial). |
| **HubExecutor** | Componente v5 que executa HubExecutionPlan: itera tasks, resolve depends_on via HubContextManager, fan-out com iterate_over, fallback automático para autonomous. |
| **HubContextManager** | Componente v5 que armazena resultados de tasks por output_key e resolve dependências entre tasks. |
| **SessionStore** | Componente v5 que persiste ConversationSession por session_id. Análogo ao ConversationMemory da LIA. |
| **ConversationSession** | Objeto v5: session_id, history[] (MAX_HISTORY=50), pending_action, active_context, domain_memories. |
| **PendingAction** | v5: ação aguardando resposta do usuário. Tipos: SELECT_OPTION, PROVIDE_INFO, CONFIRM. Inclui remaining_plan para retomar após resposta. |
| **USE_SUPERVISOR** | Flag v5 (default=False): quando True, usa SupervisorGraph (LangGraph StateGraph) ao invés do HubPlanner. |
| **SupervisorGraph** | LangGraph StateGraph v5 com MAX_ITERATIONS=3, ROUTING_KEYWORDS por domínio, SUPERVISOR_SYSTEM_PROMPT. Alternativa ao HubPlanner. |
| **OTT** | One-Time Token — sistema de autenticação v5 para callbacks do frontend. `configure_ott_from_message()` lê o token; `get_token_for_callback()` retorna no response como `auth_token`. |
| **safe_process_input** | Função v5 de segurança que detecta injeção de prompt. Se `is_injection=True`, retorna INJECTION_RESPONSE imediatamente. |
| **CircuitBreaker** | Padrão v5 de resiliência: `circuit_breaker_call()` protege chamadas à API. Se open, retorna erro imediato sem chamada. Implementado em InsightsDomain, JobsDomain, AppliesDomain, SourcedProfileSourcingDomain. |
| **WSI** | Workforce Screening Interview — avaliação em 7 blocos: Hard Skills, Soft Skills, Experiência, Liderança, Comunicação, Alinhamento Cultural, Potencial. |
| **CBI** | Competency-Based Interview — metodologia de entrevista estruturada por competências e evidências comportamentais. |
| **FairnessGuard (YAML)** | Regras no `cv_screening.yaml` que instruem o LLM a ignorar: nome, foto, localização, estado civil, idade, etnia antes de qualquer rejeição. Complementa o FairnessGuard do código. |
| **Four-Fifths Rule** | Regra de equidade: se taxa de aprovação de um grupo for <80% da taxa do grupo mais aprovado, há evidência de disparidade sistemática. |
| **Pearch AI** | Plataforma de sourcing externo integrada à LIA (190M+ perfis globais). Documentada em `sourcing.yaml`. |
| **write_plan** | Tool v5 que cria plano de execução visível ao usuário em tempo real: ⬜→🔄→✅. Obrigatório para queries com 2+ tools no autonomous. |
| **StatsManager** | Componente v5 que pré-computa stats agregadas para 26 ações (`ACTIONS_USING_AGGREGATED`). Evita N+1 chamadas à API no sourced_profile_sourcing domain. |
| **TieredContextManager** | Cache v5 do domínio `jobs`: Tier1 (dados básicos) e Tier2 (dados completos + analytics). |
| **AppliesCacheManager** | Cache v5 do domínio `applies`: cacheia dados para ações em `ACTIONS_NEEDING_CACHE`. |
| **IDOR** | Insecure Direct Object Reference. Prevenido pelo `ContextAdapter.validate_entity_ownership()` na LIA. No v5, prevenido via `workspace_id` no DomainContext. |
| **DomainContext** | Objeto de contexto compartilhado no v5: `domain_id`, `workspace_id`, `sourcing_id`, `selected_ids`, `filters_applied`, `user_id`, `session_id`, `conversation_memory`, `api_calls_history`, `allow_sensitive_filters`, `sensitive_filter_justification`, `auth_token`. |
| **DomainAction** | Definição de ação v5: id, name, description, action_type (QUERY/AGGREGATE/ANALYZE/ACTION), examples, requires_confirmation, allowed_apis, requires_params. |
| **DomainResponse** | Response padrão v5: success, message, data, suggestions, needs_confirmation, needs_clarification, clarification_question/options, error, metadata, api_calls. |
| **APICallRecord** | Registro v5 de chamada à API: endpoint, method, path, params, timestamp, duration_ms, status_code, success, error. Armazenado em DomainContext.api_calls_history. |
| **ActionType** | Enum v5: `QUERY` (consulta), `AGGREGATE` (agrega), `ANALYZE` (analisa com IA), `ACTION` (modifica dados). |
| **NavigationAction** | Ação v5 que instrui o frontend a navegar. 9 tipos: NAVIGATE, OPEN_EXPANSION, FILTER_TABLE, OPEN_DIALOG, TRIGGER_SEARCH, SCROLL_TO, SELECT_TAB, OPEN_SETTINGS, BULK_ACTION. |
| **MULTI_INTENT_RE** | Regex v5 que detecta queries com múltiplas intenções distintas, gerando HubTask[] paralelas. |
| **HubTask** | Unidade de trabalho v5: task_id, domain_id, query, context_overrides, depends_on, output_key, navigation_actions, iterate_over, max_iterations, iteration_query_template. |
| **HubExecutionPlan** | Plano gerado pelo HubPlanner: tasks[], strategy (SEQUENTIAL/PARALLEL/MIXED), reasoning, navigation_actions[]. |
| **HubResult** | Resultado do HubExecutor: success, message, data, navigation_actions, suggestions, plan, task_results, needs_clarification, clarification_question/options, pending_action_data, cards[]. |
| **TaskStrategy** | Enum v5: SEQUENTIAL, PARALLEL, MIXED — estratégia de execução de tasks no HubExecutor. |
| **FAST_NAV_PATTERNS** | Lista v5 de 12 pares (regex, target_path) no HubPlanner. Detecta intenção de navegação sem LLM. |
| **NAV_TO_DOMAIN_TASK** | Mapa v5: target_path → (domain_id, query). Usado quando is_api_only=True para converter navegação em task de domínio. |
| **SearchParams** | Dataclass v5 do search_pipeline.py: skills[], text_terms, natural_query, location, state, seniority, min_experience, english_level, remote, companies, limit_per_strategy=25. |
| **CandidateResult** | Dataclass v5 do search_pipeline.py: id, name, role_name, city, state, skills[], score, current_company, email, linkedin, source_strategies, skill_match_count. relevance_score = skill_match_count×200 + len(source_strategies)×100 + score. |
| **_KNOWN_TECH** | Set v5 de 70+ tecnologias reconhecidas no search_pipeline.py para parsing de skills da query. |
| **_ROLE_VARIATIONS** | Dict v5 de variações de cargo: frontend, backend, fullstack, devops, data, mobile. |
| **SchedulingDomain** | Domínio v5 exclusivo: agendamento de entrevistas (direto, self-scheduling, cancelamento, remarcação). Tem LangGraph graph.py e session state. |
| **InsightsDomain** | Domínio v5 exclusivo: analytics consolidado — briefing diário, reports, métricas, alertas, tendências. Tem CircuitBreaker em todas as actions. |
| **EvaluationDomain** | Domínio v5 exclusivo: avaliação de candidatos em entrevistas via LangGraph StateGraph. |
| **interview_ai/** | Módulo v5 extra-domain: entrevistas por voz via Twilio + Gemini, rotas de avaliação, relatórios pós-entrevista. |
| **viewing_entities** | Campo v5 em context_data: entidades visíveis na tela atual (job_id, candidate_id). Permite resolução de referências implícitas ("ele", "essa vaga") no autonomous domain. |
| **[LIA-API]** | Capacidade da LIA que faz chamada real à API via tool registrada no scope ativo. |
| **[LIA-LLM]** | Capacidade da LIA executada pelo LLM sem chamada de API — usa dados já em contexto da conversa. |
| **[v5]** | Capacidade do recruiter_agent_v5 (GitHub WeDOTalent/recruiter_agent_v5). |

---

*Fontes LIA lidas: `lia-agent-system/app/orchestrator/context_adapter.py` (PAGE_TO_CONTEXT_TYPE), `lia-agent-system/app/tools/tool_registry_metadata.yaml` (scope por tool), `lia-agent-system/app/tools/scope_config.py` (SCOPE_TOOL_MAPPING — enforcement de runtime), `lia-agent-system/app/orchestrator/orchestrator.py` (SCOPE_MAPPING, process_request, get_tools_for_context), `lia-agent-system/app/orchestrator/main_orchestrator.py` (fluxo de fases, FairnessGuard, _process_via_orchestrator), `lia-agent-system/app/orchestrator/cascaded_router.py` (6 tiers, RouteResult, AGENT_TYPE_TO_DOMAIN), `lia-agent-system/app/tools/tool_registry_loader.py`, `lia-agent-system/app/prompts/domains/{recruiter_assistant,job_management,cv_screening,pipeline_transition,interview_scheduling,communication,sourcing,analytics}.yaml`, `lia-agent-system/app/shared/prompts/interaction_patterns.py`*

*Fontes v5 lidas (GitHub WeDOTalent/recruiter_agent_v5): `src/api.py` (ChatRequest, /chat, /chat/stream SSE, MessageRouter), `src/services/message_router.py` (3 caminhos: hub/domain/global, OTT, timing), `src/hub/planner.py` (FAST_NAV_PATTERNS, _JOB_ID_PATTERN, _CANDIDATE_SEARCH_RE, PLANNER_SYSTEM_PROMPT, NAV_TO_DOMAIN_TASK), `src/hub/models.py` (HubTask, HubExecutionPlan, HubResult, NavigationAction, NavigationActionType, TaskStrategy), `src/hub/context_manager.py` (HubContextManager — store/resolve results), `src/hub/executor.py` (HubExecutor, fan-out, autonomous fallback, candidate_search pipeline), `src/hub/orchestrator.py` (HubOrchestrator, SessionStore, PendingAction, scheduling bypass, USE_SUPERVISOR flag), `src/hub/supervisor_graph.py` (SupervisorGraph LangGraph, MAX_ITERATIONS=3, ROUTING_KEYWORDS, DOMAIN_DESCRIPTIONS), `src/hub/session.py` (ConversationSession MAX_HISTORY=50, PendingAction types, active_context), `src/domains/base.py` (DomainContext completo, DomainAction, DomainResponse, DomainPrompt ABC, APICallRecord, ActionType), `src/domains/jobs/domain.py` + `src/domains/jobs/actions/*.py` (7 arquivos: analytics, base, conversational, matching, mutations, query, suggestions, TieredContextManager, JobConversationMemory), `src/domains/applies/domain.py` + `src/domains/applies/actions/*.py` (10 arquivos: analytics, base, bulk, comparison, conversational, details, pipeline, scoring, search, sourcing, react_agent.py, AppliesCacheManager, AppliesConversationMemory), `src/domains/sourced_profile_sourcing/domain.py` + `src/domains/sourced_profile_sourcing/actions/*.py` (12 arquivos) + `fairness.py` + `fact_checker.py` + `agents/*.py` (9 agentes), `src/domains/scheduling/domain.py` + `src/domains/scheduling/actions/*.py` (5 arquivos) + graph.py + session.py, `src/domains/insights/domain.py` + `src/domains/insights/actions/*.py` (9 arquivos), `src/domains/evaluation/domain.py` + graph.py + models.py + security.py, `src/domains/autonomous/search_pipeline.py` (SearchParams, CandidateResult, _KNOWN_TECH, _ROLE_VARIATIONS), `src/domains/autonomous/tools/*.py` (13 módulos), `src/domains/autonomous/prompts.py` (AUTONOMOUS_SYSTEM_PROMPT)*

*Para atualizar: reler `lia-agent-system/app/tools/tool_registry_metadata.yaml` (scope por tool), `lia-agent-system/app/tools/scope_config.py` (SCOPE_TOOL_MAPPING), `lia-agent-system/app/orchestrator/context_adapter.py` (PAGE_TO_CONTEXT_TYPE), e os `domain.py` + `actions/*.py` do v5. Verificar se USE_SUPERVISOR foi alterado para True em `src/hub/orchestrator.py`.*
