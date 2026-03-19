# Mapeamento de Capacidades dos Prompts da LIA × v5

**Versão:** 4.0 | **Data:** Março/2026 | **Autoria:** Análise de código LIA local + recruiter_agent_v5 (GitHub WeDOTalent)

---

## Como ler este documento

Este documento mapeia os 4 contextos de prompt da plataforma LIA com base em **leitura direta do código**:

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
2. [Arquitetura de roteamento LIA](#roteamento)
3. [Prompt 1 — Flutuante / Global](#prompt-1)
4. [Prompt 2 — Tabela de Vagas](#prompt-2)
5. [Prompt 3 — Dentro da Vaga (Kanban)](#prompt-3)
6. [Prompt 4 — Funil de Talentos](#prompt-4)
7. [Tabela-resumo global (4 prompts × 10 dimensões)](#tabela-resumo)
8. [Glossário técnico](#glossario)

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

---

## 2. Arquitetura de roteamento LIA {#roteamento}

A LIA usa **dois sistemas de roteamento independentes** que coexistem:

### Sistema A — Scope de tools (por context_page do frontend)

- Determina quais API tools o LLM pode chamar
- Baseado no `context_page` enviado pelo frontend → normalizado para `context_type` → mapeado para `PromptScope`
- Implementado em `app/tools/scope_config.py`: `filter_tools_by_scope()` filtra por scope no `Orchestrator.get_tools_for_context()` (`orchestrator.py`, linha 313)
- Os scopes são mutuamente exclusivos (sem union de scopes em runtime)

### Sistema B — Domain routing (por conteúdo da mensagem)

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

### Fluxo MainOrchestrator (`main_orchestrator.py`)

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

## 3. Prompt 1 — Flutuante / Global {#prompt-1}

### 3.0 Introdução

O **Prompt Flutuante** aparece como ícone de chat em **todas as páginas** da plataforma. É o copiloto de recrutamento pessoal do recrutador — ativado sem precisar navegar para nenhuma tela específica.

**Ativação:** `context_page: "general"/"global"` → `context_type: "general"` → domínio `recruiter_assistant.yaml` → scope GLOBAL.

**Para que serve:** planejamento do dia, relatórios gerais, configurações da empresa, feedback sobre o wizard de vagas, perguntas gerais sobre processos de RH, briefings e insights baseados em dados já mencionados na conversa.

**Para que NÃO serve:** qualquer ação que exija acesso ao banco de dados via API (buscar candidatos, criar vagas, mover candidaturas, enviar comunicações). Para essas ações, o usuário deve navegar à página correspondente.

**Nota sobre roteamento:** mesmo quando o recrutador usa o chat flutuante, o CascadedRouter pode detectar a intenção da mensagem e rotear para domínios especializados (job_management, cv_screening, etc.). Nesses casos, o domínio processa via DomainWorkflow, mas as tools de API disponíveis permanecem as do scope GLOBAL.

---

### 3.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: GLOBAL — 4 tools, fonte: tool_registry_metadata.yaml)

| Tool | O que faz | Parâmetros principais |
|---|---|---|
| `get_company_config` | Obtém configurações da empresa: workflow de contratação, aprovações, configurações de sistema | `config_type` |
| `generate_report` | Gera relatório de analytics para período e tipo definidos | `report_type`, `date_from`, `date_to`, `format: pdf\|csv\|json` |
| `schedule_report` | Agenda relatório recorrente enviado automaticamente | `report_type`, `schedule` (cron), `recipients[]` |
| `capture_wizard_feedback` | Registra feedback do recrutador sobre experiência com o wizard de criação de vagas | `feedback_type`, `rating`, `comment` |

**Nota sobre divergência de fontes:** `app/tools/scope_config.py` (runtime enforcement — `SCOPE_TOOL_MAPPING`, usado por `filter_tools_by_scope()` em `orchestrator.py` linha 313) lista GLOBAL com apenas 2 tools: `generate_report` e `schedule_report`. `tool_registry_metadata.yaml` lista 4. Verificando o código Python das tools: `get_company_config` e `capture_wizard_feedback` estão declaradas no YAML como scope GLOBAL, mas ausentes do `SCOPE_TOOL_MAPPING` em `scope_config.py` — o que significa que `filter_tools_by_scope(GLOBAL)` **não** as retorna em runtime. A fonte executável é `scope_config.py`; o YAML tem precedência apenas para metadados (description, version).

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

| Capacidade | Por quê não está disponível | Para onde delegar |
|---|---|---|
| Buscar vagas via API | `search_jobs` não está no scope GLOBAL | Navegar para `/user/jobs` → Prompt 2 |
| Criar vagas via API | `create_job` não está no scope GLOBAL | Navegar para `/user/jobs` → Prompt 2 |
| Buscar candidatos via API | `search_candidates` não está no scope GLOBAL | Navegar para `/user/candidates` → Prompt 4 |
| Mover candidatos no pipeline | `update_candidate_stage` não está no scope GLOBAL | Navegar para `/user/jobs/{id}` → Prompt 3 |
| Enviar email/WhatsApp via API | `send_email`/`send_whatsapp` não estão no scope GLOBAL | Prompt 3 ou Prompt 4 |
| Agendar entrevistas via API | `schedule_interview` não está no scope GLOBAL | Navegar para `/user/jobs/{id}` → Prompt 3 |
| Triagem WSI de CVs | `wsi_screening` não está no scope GLOBAL | Navegar para `/user/jobs/{id}` → Prompt 3 |

---

### 3.3 Dados que coleta / gera

**Inputs:**
- `message` — pergunta ou instrução do recrutador
- `context_page: "general"/"global"` — ativa o contexto GLOBAL
- `user_id` + `company_id` — identidade e isolamento multi-tenant
- `conversation_id` — histórico de sessão para memória (`ConversationMemory`)
- Dados mencionados na conversa (candidatos, vagas, alertas) — usados pelo [LIA-LLM]
- `tenant_context_snippet` — contexto enriquecido do tenant injetado pelo `TenantContextService`

**Outputs:**
- Relatório gerado (`generate_report`): PDF, CSV ou JSON com analytics de recrutamento
- Relatório agendado (`schedule_report`): confirmação de agendamento com próxima execução
- Config da empresa (`get_company_config`): dados estruturados sobre workflow de contratação
- Feedback registrado (`capture_wizard_feedback`): confirmação de registro
- [LIA-LLM] Briefing textual formatado (bullets: urgentes → importantes → informativos)
- [LIA-LLM] Análises e comparações em markdown (tabelas, listas)
- [LIA-LLM] Respostas a perguntas gerais com sugestões de próximas ações

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
POST /chat ou /chat/stream (SSE)
    │
    ▼
HubPlanner (LLM-based — PLANNER_SYSTEM_PROMPT)
    │
    ├─ FAST_NAV_PATTERNS (regex, sem LLM)
    │   "vá para vagas ativas" → NavigationAction(NAVIGATE, /user/jobs?tab=active)
    │
    ├─ _JOB_ID_PATTERN: "vaga 42" → open job ou navigate /user/jobs/42
    │
    ├─ _CANDIDATE_ID_PATTERN: "candidato 91" → open candidate
    │
    ├─ MULTI_INTENT_RE: detecta 2+ intenções → HubTask[] em paralelo
    │   Ex: "stats de vagas E candidatos" → 2 domains simultâneos
    │
    └─ LLM classifica → HubExecutionPlan { tasks[], strategy, navigation_actions[] }
          │
          ▼
      AutonomousDomain (73+ tools em 13 módulos)
          AUTONOMOUS_SYSTEM_PROMPT (100+ linhas):
              • 1 tool: vai direto (sem write_plan)
              • 2+ tools: SEMPRE write_plan antes; atualiza após cada tool
              • Budget: max 40 API calls por sessão
              • Offloading: resultados >5K chars → save_file automático
              • Resolução de contexto: viewing_entities → sessão → URL → ask_user
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
| **Streaming SSE** | ⚠️ Via WebSocket | ✅ /chat/stream com SSE nativo |
| **Fallback genérico de API** | ❌ | ✅ call_api (qualquer endpoint Rails) |
| **FairnessGuard** | ✅ Antes de qualquer fase | ✅ Via system prompt |
| **IDOR prevention** | ✅ validate_entity_ownership() | ✅ Via workspace_id |

---

## 4. Prompt 2 — Tabela de Vagas {#prompt-2}

### 4.0 Introdução

O **Prompt Expandido da Tabela de Vagas** aparece ao lado da listagem de vagas (`/user/jobs`). É o contexto especializado para **criar, configurar, editar e gerir vagas**.

**Ativação:** `context_page: "job"/"jobs"/"vacancies"/"wizard"` → `context_type: "job_management"` → domínio `job_management.yaml` → scope JOB_TABLE.

**Para que serve:** criar nova vaga via wizard conversacional, gerar job description, benchmark salarial, configurar etapas do processo seletivo, editar vagas existentes, publicar vagas, analytics de vagas.

**Para que NÃO serve:** buscar candidatos, triar CVs, agendar entrevistas, movimentar candidatos no pipeline.

---

### 4.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: JOB_TABLE — 13 tools, fonte: tool_registry_metadata.yaml)

**Query tools:**

| Tool | O que faz | Parâmetros |
|---|---|---|
| `search_jobs` | Busca vagas por título, status, departamento | `query`, `status`, `department`, `limit` |
| `get_job_details` | Detalhes completos da vaga + candidatos | `job_id`, `include_candidates` |
| `get_pipeline_stats` | Stats do pipeline: candidatos por etapa, taxas de conversão | `job_id`, `date_range` |
| `search_salary_benchmark` | Benchmark salarial por cargo/senioridade/localidade/setor | `job_title`, `seniority`, `location`, `industry` |
| `get_intelligent_salary` | Sugestão inteligente de faixa salarial | `job_title`, `seniority`, `location` |
| `get_intelligent_skills` | Sugestão de competências por cargo e senioridade | `job_title`, `seniority`, `industry` |
| `get_job_suggestions` | Sugestões de melhoria para a JD atual | `job_title`, `current_description`, `industry` |
| `validate_job_fields` | Valida campos e detecta informações faltando antes de salvar | `fields` |

**Action tools:**

| Tool | O que faz | Parâmetros |
|---|---|---|
| `save_job_draft` | Salva rascunho da vaga em criação `[ESCRITA]` | `fields`, `draft_id` |
| `generate_enriched_jd` | Gera Job Description por IA a partir dos campos coletados | `fields`, `tone: formal\|creative\|technical` |
| `create_job` | Cria nova vaga no banco `[ESCRITA]` | `title`, `description`, `department`, `location`, `salary_range`, `requirements[]` |
| `update_job` | Edita campos de vaga existente `[ESCRITA]` | `job_id`, `fields` |
| `publish_job` | Publica vaga em canais definidos `[ESCRITA]` | `job_id`, `channels[]` |

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

| Capacidade | Por quê não está disponível | Para onde delegar |
|---|---|---|
| Buscar candidatos do banco | `search_candidates` não está em JOB_TABLE | Prompt 4 (TALENT_FUNNEL) |
| Triar CVs de candidatos em vaga | `wsi_screening` não está em JOB_TABLE | Prompt 3 (IN_JOB) |
| Mover candidatos no pipeline | `update_candidate_stage` não está em JOB_TABLE | Prompt 3 (IN_JOB) |
| Agendar entrevistas | `schedule_interview` não está em JOB_TABLE | Prompt 3 (IN_JOB) |
| Enviar email/WhatsApp | `send_email`/`send_whatsapp` não estão em JOB_TABLE | Prompt 3 / Prompt 4 |
| Ver kanban de uma vaga específica | `get_vacancy_funnel` não está em JOB_TABLE | Prompt 3 (IN_JOB) |

---

### 4.3 Dados que coleta / gera

**Inputs:**
- `context_page: "job"/"jobs"/"vacancies"/"wizard"` — ativa o scope JOB_TABLE
- `entity_id` — job_id da vaga selecionada (opcional)
- `job_context` — dados da vaga atual passados pelo frontend
- Campos coletados no wizard: título, área, senioridade, tipo de contrato, faixa salarial, localidade, modelo de trabalho, skills, competências WSI, etapas do processo

**Outputs:**
- Rascunho de vaga salvo no banco (`save_job_draft`)
- Vaga criada e publicada no ATS
- Job Description em Markdown (seções: Sobre a empresa | Responsabilidades | Requisitos | Benefícios)
- Benchmark salarial: faixa min/max por cargo, senioridade, localidade
- Lista de skills sugeridas com justificativa
- Stats do pipeline por etapa (dados para gráficos no frontend)

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
| **Matching de candidatos** | ❌ | ✅ matching_candidates |
| **Sourcing automático** | ❌ | ✅ auto_source |
| **Duplicar vaga** | ❌ | ✅ copy_job |
| **Cache tiered** | ❌ | ✅ TieredContextManager |
| **Detecção de intenção** | Via CascadedRouter | ✅ Regex + LLM fallback |
| **Perguntas de entrevista** | ❌ | ✅ generate_interview_questions |

---

## 5. Prompt 3 — Dentro da Vaga (Kanban) {#prompt-3}

### 5.0 Introdução

O **Prompt Expandido do Kanban** aparece dentro de uma vaga específica (`/user/jobs/{id}`), ao lado do kanban de candidatos. É o contexto mais operacional — age diretamente sobre candidatos **de uma vaga específica**.

**Ativação:** `context_page: "pipeline"/"kanban"` → `context_type: "pipeline"` → 4 domínios YAML ativos → scope IN_JOB.

**Para que serve:** triar CVs com score WSI, mover candidatos entre etapas, conduzir entrevistas CBI, agendar entrevistas, enviar comunicações, ver funil da vaga.

**Para que NÃO serve:** buscar candidatos externos ao processo, criar novas vagas, fazer análises cross-vagas.

---

### 5.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: IN_JOB — 6 tools, fonte: tool_registry_metadata.yaml)

| Tool | O que faz | Parâmetros |
|---|---|---|
| `update_candidate_stage` | Move candidato para etapa do pipeline `[ESCRITA]` | `candidate_id`, `target_stage`, `job_id`, `notes`, `notify_candidate` |
| `reject_candidate` | Rejeita candidato com motivo `[ESCRITA]` | `candidate_id`, `vacancy_id`, `reason`, `notify` |
| `bulk_update_candidates_stage` | Move múltiplos candidatos de etapa simultaneamente `[LOTE][ESCRITA]` | `candidate_ids[]`, `target_stage`, `job_id` |
| `wsi_screening` | Inicia avaliação WSI formal para candidato (voz, texto ou vídeo) `[ESCRITA]` | `candidate_id`, `job_id`, `screening_type: voice\|text\|video` |
| `hide_candidate` | Oculta candidato da visualização ativa (soft remove) `[ESCRITA]` | `candidate_id`, `vacancy_id`, `reason` |
| `get_vacancy_funnel` | Retorna dados do funil: candidatos por etapa + taxas de conversão | `job_id`, `include_rejected` |

**Nota sobre divergência de fontes — IN_JOB:** `app/tools/scope_config.py` (`SCOPE_TOOL_MAPPING`) lista IN_JOB com 25 tools: 14 query tools (`get_job_details`, `get_vacancy_funnel`, `get_candidate_details`, `get_activity_summary`, `get_pending_actions`, `compare_candidates`, `get_candidate_stats`, `get_bottleneck_analysis`, `get_job_velocity`, `get_job_quality_metrics`, `get_stakeholder_metrics`, `get_prediction_metrics`, `get_job_benchmark`, `get_smart_alerts`) + 11 action tools (`update_candidate_stage`, `bulk_update_candidates_stage`, `reject_candidate`, `shortlist_candidate`, `add_to_list`, `hide_candidate`, `wsi_screening`, `send_email`, `send_whatsapp`, `schedule_interview`, `send_feedback`). O `tool_registry_metadata.yaml` lista apenas 6 dessas tools. A discrepância é documentada — o `scope_config.py` é a fonte executável de runtime; as 25 tools listadas nele são o teto real de capacidade da API neste escopo.

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

| Capacidade | Por quê não está disponível | Para onde delegar |
|---|---|---|
| Buscar candidatos externos à vaga | `search_candidates` não está em IN_JOB | Prompt 4 (TALENT_FUNNEL) |
| Criar ou editar vagas | `create_job`/`update_job` não estão em IN_JOB | Prompt 2 (JOB_TABLE) |
| Analytics cross-vagas | Contexto limitado à vaga atual | Prompt 1 (GLOBAL) |
| Exportação bulk de candidatos | `export_candidates` não está em IN_JOB | Prompt 4 (TALENT_FUNNEL) |

---

### 5.3 Dados que coleta / gera

**Inputs:**
- `context_page: "pipeline"/"kanban"` — ativa scope IN_JOB
- `entity_id` = job_id — vaga aberta
- `job_context` — dados da vaga (título, requisitos, etapas, competências WSI)
- `candidates[]` — lista de candidatos carregados na tela pelo frontend
- `selected_candidate_ids[]` — candidatos selecionados pelo recrutador

**Outputs (API):**
- Candidato movido de etapa / rejeitado / oculto
- Múltiplos candidatos movidos em lote
- Sessão WSI iniciada (voz, texto ou vídeo)
- Dados do funil por etapa

**Outputs (LLM):**
- Score WSI 0-100 por candidato com justificativa para cada bloco
- Recomendação de avanço, revisão ou rejeição
- Análise de entrevista pós-condução (competências + evidências + score parcial)
- Rascunho de comunicações (emails, WhatsApp, Teams)
- Log de auditoria de avaliações (compliance LGPD/SOX — documentado no reasoning)

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
AppliesActions (src/domains/applies/actions/):
    analytics.py:    apply_analytics | stage_distribution
    bulk.py:         bulk_approve_applies | bulk_reject_applies |
                     bulk_move_applies (async) | send_apply_reject_feedback
    comparison.py:   compare_candidates
    details.py:      show_apply_details | apply_timeline
    pipeline.py:     get_kanban | move_stage | approve_apply | reject_apply
    scoring.py:      filter_by_score | top_candidates | full_ranking
    search.py:       search_applies | search_by_name | list_applies_by_stage |
                     recent_applies | count_applies
    sourcing.py:     stalled_applies (attention/warning/critical) | diagnose_applies
    │
    ▼
AppliesCacheManager + AppliesAPIClient → ATS Rails API
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
| **FairnessGuard** | ✅ Antes de toda rejeição (code + YAML) | ✅ No MainOrchestrator (não no v5) |
| **Condução CBI** | ✅ interview_scheduling.yaml dedicado | ⚠️ Via autonomous |
| **Analytics de candidaturas** | ❌ (YAML) / ✅ (scope_config.py: get_bottleneck_analysis, etc.) | ✅ apply_analytics |
| **Diagnóstico completo** | ❌ | ✅ diagnose_applies |
| **Candidatos parados** | ❌ (YAML) / ✅ (scope_config.py: get_smart_alerts) | ✅ stalled_applies (SLA por severidade) |
| **Timeline da candidatura** | ❌ | ✅ apply_timeline |
| **Top N candidatos** | ❌ | ✅ top_candidates, full_ranking |
| **Comparação de candidatos** | ✅ [LIA-LLM] com dados em contexto | ✅ compare_candidates |
| **send_email / send_whatsapp** | ❌ (YAML) / ✅ (scope_config.py) | ✅ Via autonomous |
| **schedule_interview** | ❌ (YAML) / ✅ (scope_config.py) | ✅ Via autonomous |
| **Cache** | ❌ | ✅ AppliesCacheManager |

---

## 6. Prompt 4 — Funil de Talentos {#prompt-4}

### 6.0 Introdução

O **Prompt Expandido do Funil de Talentos** aparece em `/user/candidates` ou na sessão de sourcing (`/user/sourcing/{id}/chat`). É o contexto especializado em **busca e análise de candidatos** no banco de talentos.

**Ativação:** `context_page: "sourcing"/"talent"` → `context_type: "talent_funnel"` → domínios `sourcing.yaml` + `analytics.yaml` → scope TALENT_FUNNEL.

**Para que serve:** buscar candidatos no banco interno e externo (Pearch AI), construir queries booleanas, analisar compatibilidade, gerar relatórios do pool, exportar candidatos, adicionar candidatos a vagas ou listas.

**Para que NÃO serve:** triar CVs de candidatos já em uma vaga, agendar entrevistas, criar vagas.

---

### 6.1 Capacidades IN

#### [LIA-API] Tools disponíveis (scope: TALENT_FUNNEL — 9 tools, fonte: tool_registry_metadata.yaml)

**Query tools:**

| Tool | O que faz | Parâmetros |
|---|---|---|
| `search_candidates` | Busca candidatos no banco por query + filtros + paginação | `query`, `filters`, `limit`, `offset` |
| `get_candidate_details` | Perfil completo do candidato com histórico de processos | `candidate_id`, `include_history` |
| `get_candidate_stats` | Estatísticas agregadas do pool de candidatos | `filters`, `group_by` |

**Action tools:**

| Tool | O que faz | Parâmetros |
|---|---|---|
| `add_candidate_to_vacancy` | Adiciona candidato ao processo seletivo de uma vaga `[ESCRITA]` | `candidate_id`, `vacancy_id`, `stage`, `notes` |
| `shortlist_candidate` | Adiciona à lista de pré-selecionados para uma vaga `[ESCRITA]` | `candidate_id`, `vacancy_id`, `notes` |
| `add_to_list` | Inclui candidato em lista de talentos nomeada `[ESCRITA]` | `candidate_id`, `list_name`, `notes` |
| `export_candidates` | Exporta candidatos em CSV ou XLSX | `candidate_ids[]`, `format: csv\|xlsx`, `fields[]` |
| `send_email` | Envia email para um ou mais candidatos `[ESCRITA]` | `to[]`, `subject`, `body`, `template_id` |
| `send_whatsapp` | Envia mensagem WhatsApp para candidato `[ESCRITA]` | `phone`, `message`, `template_name` |

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

| Capacidade | Por quê não está disponível | Para onde delegar |
|---|---|---|
| Triagem WSI de candidatos | `wsi_screening` não está em TALENT_FUNNEL | Prompt 3 (IN_JOB) |
| Mover candidatos no pipeline | `update_candidate_stage` não está em TALENT_FUNNEL | Prompt 3 (IN_JOB) |
| Agendar entrevistas | `schedule_interview` não está em TALENT_FUNNEL | Prompt 3 (IN_JOB) |
| Criar ou editar vagas | `create_job`/`update_job` não estão em TALENT_FUNNEL | Prompt 2 (JOB_TABLE) |
| Relatório genérico (não de candidatos) | `generate_report` não está em TALENT_FUNNEL | Prompt 1 (GLOBAL) |

---

### 6.3 Dados que coleta / gera

**Inputs:**
- `context_page: "sourcing"/"talent"` — ativa TALENT_FUNNEL scope
- `entity_id` = `sourcing_id` — ID da sessão de sourcing ativa
- `entity_type: "sourcing"` — tipo da entidade em foco
- `candidates[]` — candidatos do resultado de busca atual (carregados na tela)
- `selected_candidate_ids[]` — candidatos selecionados
- `search_context` — configurações da busca (query, filtros)
- `target_job` — vaga-alvo para cálculo de score de compatibilidade

**Outputs (API):**
- Candidatos buscados e filtrados do banco
- Candidatos adicionados a vaga / lista / shortlist
- Emails / WhatsApp enviados (com confirmação prévia)
- Candidatos exportados em CSV ou XLSX

**Outputs (LLM):**
- Ranking de candidatos com score de compatibilidade e justificativa
- Relatório executivo de sourcing (Markdown estruturado)
- Análise de diversidade com métricas Four-Fifths Rule
- Sugestão de refinamento de busca quando pool é inadequado

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
| **Four-Fifths Rule** | ✅ [LIA-LLM] analytics.yaml | ✅ diversity_analysis |
| **Cache de stats** | ❌ | ✅ StatsManager (ACTIONS_USING_AGGREGATED) |
| **Relatório executivo** | ✅ via GLOBAL generate_report | ✅ generate_executive_report (4-step LLM) |
| **Análise de melhoria de busca** | ✅ [LIA-LLM] | ✅ analyze_search_improvement |
| **Skill gaps** | ✅ [LIA-LLM] | ✅ skill_gaps |
| **Aprovação/rejeição de perfil** | ❌ Sem tool no YAML | ✅ approve_candidate, reject_candidate, add_rating |
| **Comparação de sourcings** | ❌ | ✅ get_multi_sourcing_stats (via autonomous) |
| **Arquetipos de busca** | ❌ | ✅ search_archetypes (via autonomous) |

---

## 7. Tabela-resumo global (4 prompts × 10 dimensões) {#tabela-resumo}

| Dimensão | Prompt 1 — Flutuante | Prompt 2 — Tabela Vagas | Prompt 3 — Kanban | Prompt 4 — Funil Talentos |
|---|---|---|---|---|
| **context_page (LIA)** | `general`, `global` | `job`, `jobs`, `vacancies`, `wizard` | `pipeline`, `kanban` | `sourcing`, `talent` |
| **domain (v5)** | `null` + hub_mode | `"jobs"` | `"applies"` | `"sourced_profile_sourcing"` |
| **Scope + N° tools LIA (YAML)** | GLOBAL — 4 tools | JOB_TABLE — 13 tools | IN_JOB — 6 tools | TALENT_FUNNEL — 9 tools |
| **Domínios YAML LIA** | recruiter_assistant | job_management | cv_screening + pipeline_transition + interview_scheduling + communication | sourcing + analytics |
| **N° actions v5** | 73+ (13 módulos) | 17+ actions | 30+ actions | 32+ actions |
| **Domain routing LIA** | CascadedRouter (6 tiers, por mensagem) | CascadedRouter | CascadedRouter | CascadedRouter |
| **Domain routing v5** | HubPlanner (LLM + regex) | Domain direto | Domain direto | Domain direto |
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
| **Cache otimizado** | ❌ LIA | ✅ v5 (Tier1/2) | ✅ v5 (Cache) | ✅ v5 (StatsManager) |
| **Progresso write_plan** | ❌ LIA | ❌ LIA | ❌ LIA | ❌ LIA |
| **Streaming SSE** | ⚠️ WebSocket LIA | ⚠️ WebSocket LIA | ⚠️ WebSocket LIA | ⚠️ WebSocket LIA |
| **LGPD compliance** | ✅ Ambos | ✅ Ambos | ✅ Ambos | ✅ Ambos |

---

## 8. Glossário técnico {#glossario}

| Termo | Definição |
|---|---|
| **context_page** | Campo enviado pelo frontend junto com cada mensagem. Determina qual scope de tools será ativado na LIA. |
| **context_type** | Tipo normalizado de contexto, mapeado pelo `ContextAdapter` a partir do `context_page` via `PAGE_TO_CONTEXT_TYPE`. |
| **scope** | Conjunto de tools disponíveis para o LLM em um contexto. Definido em `tool_registry_metadata.yaml` (declarativo) e `scope_config.py` (enforcement de runtime). |
| **tool_registry_metadata.yaml** | Fonte declarativa de metadados das tools LIA: nome, description, allowed_agents, scope, version, parameters. Usado pelo task spec desta análise. |
| **scope_config.py** | `app/tools/scope_config.py` — Fonte executável de runtime: `SCOPE_TOOL_MAPPING` + `filter_tools_by_scope()`. Importado diretamente pelo `orchestrator.py`. Tem precedência sobre o YAML em runtime. |
| **CascadedRouter** | Componente LIA de roteamento de domínio por intenção da mensagem. 6 tiers: memory (pronomes) → LRU in-process → Redis → VectorSemanticCache (pgvector ≥0.92) → FastRouter (regex/keyword) → LLM (Haiku→Sonnet→Opus) → clarification. |
| **HubPlanner** | Componente v5 equivalente. Analisa query com PLANNER_SYSTEM_PROMPT, detecta FAST_NAV_PATTERNS (regex), MULTI_INTENT_RE, gera HubExecutionPlan com HubTask[] paralelas. |
| **MainOrchestrator** | Entry point único da LIA: FairnessGuard → PendingAction → ActionExecutor → Orchestrator (CascadedRouter + DomainWorkflow). |
| **FairnessGuard** | Camada de proteção anti-discriminação executada ANTES de qualquer processamento. Bloqueia: critérios por gênero, etnia, idade, estado civil, nome, localização. |
| **DomainWorkflow** | Executa PRE_CHECK → domain action → POST_CHECK. Usa ReAct agent para chamadas de tools. |
| **PlanDetector** | Componente LIA que detecta queries multi-step e gera ExecutionPlan (análogo ao MULTI_INTENT_RE do v5, mas sequencial). |
| **WSI** | Workforce Screening Interview — avaliação em 7 blocos: Hard Skills, Soft Skills, Experiência, Liderança, Comunicação, Alinhamento Cultural, Potencial. |
| **CBI** | Competency-Based Interview — metodologia de entrevista estruturada por competências e evidências comportamentais. |
| **FairnessGuard (YAML)** | Regras no `cv_screening.yaml` que instruem o LLM a ignorar: nome, foto, localização, estado civil, idade, etnia antes de qualquer rejeição. Complementa o FairnessGuard do código. |
| **Four-Fifths Rule** | Regra de equidade: se taxa de aprovação de um grupo for <80% da taxa do grupo mais aprovado, há evidência de disparidade sistemática. |
| **Pearch AI** | Plataforma de sourcing externo integrada à LIA (190M+ perfis globais). Documentada em `sourcing.yaml`. |
| **write_plan** | Tool v5 que cria plano de execução visível ao usuário em tempo real: ⬜→🔄→✅. Obrigatório para queries com 2+ tools no autonomous. |
| **StatsManager** | Componente v5 que pré-computa stats agregadas para 26 ações (`ACTIONS_USING_AGGREGATED`). Evita N+1 chamadas à API. |
| **TieredContextManager** | Cache v5 do domínio `jobs`: Tier1 (dados básicos) e Tier2 (dados completos + analytics). |
| **IDOR** | Insecure Direct Object Reference. Prevenido pelo `ContextAdapter.validate_entity_ownership()` na LIA. |
| **DomainContext** | Objeto de contexto compartilhado no v5: `workspace_id`, `sourcing_id`, `selected_ids`, `conversation_memory`, `auth_token`. |
| **ActionType** | Enum v5: `QUERY` (consulta), `AGGREGATE` (agrega), `ANALYZE` (analisa com IA), `ACTION` (modifica dados). |
| **NavigationAction** | Ação v5 que instrui o frontend a navegar para URL específica sem recarregar. |
| **MULTI_INTENT_RE** | Regex v5 que detecta queries com múltiplas intenções distintas, gerando HubTask[] paralelas. |
| **viewing_entities** | Campo v5: entidades visíveis na tela atual (job_id, candidate_id). Permite resolução de referências implícitas ("ele", "essa vaga"). |
| **[LIA-API]** | Capacidade da LIA que faz chamada real à API via tool registrada no scope ativo. |
| **[LIA-LLM]** | Capacidade da LIA executada pelo LLM sem chamada de API — usa dados já em contexto da conversa. |
| **[v5]** | Capacidade do recruiter_agent_v5 (GitHub WeDOTalent/recruiter_agent_v5). |

---

*Fontes LIA lidas: `lia-agent-system/app/orchestrator/context_adapter.py` (PAGE_TO_CONTEXT_TYPE), `lia-agent-system/app/tools/tool_registry_metadata.yaml` (scope por tool), `lia-agent-system/app/tools/scope_config.py` (SCOPE_TOOL_MAPPING — enforcement de runtime), `lia-agent-system/app/orchestrator/orchestrator.py` (SCOPE_MAPPING, process_request, get_tools_for_context), `lia-agent-system/app/orchestrator/main_orchestrator.py` (fluxo de fases, FairnessGuard, _process_via_orchestrator), `lia-agent-system/app/orchestrator/cascaded_router.py` (6 tiers, RouteResult, AGENT_TYPE_TO_DOMAIN), `lia-agent-system/app/tools/tool_registry_loader.py`, `lia-agent-system/app/prompts/domains/{recruiter_assistant,job_management,cv_screening,pipeline_transition,interview_scheduling,communication,sourcing,analytics}.yaml`, `lia-agent-system/app/shared/prompts/interaction_patterns.py`*

*Fontes v5 lidas (GitHub WeDOTalent/recruiter_agent_v5): `src/hub/catalog.py`, `src/hub/planner.py`, `src/domains/base.py`, `src/domains/autonomous/prompts.py` (AUTONOMOUS_SYSTEM_PROMPT + budget rules), `src/domains/autonomous/tools/{jobs,candidates,applies,sourcing,scheduling,evaluations,organization,planning,file_system,generic,macros}.py` (73+ tools), `src/domains/jobs/domain.py` + `src/domains/jobs/actions/*.py`, `src/domains/applies/domain.py` + `src/domains/applies/actions/*.py`, `src/domains/sourced_profile_sourcing/domain.py` + `src/domains/sourced_profile_sourcing/actions/*.py`*

*Para atualizar: reler `lia-agent-system/app/tools/tool_registry_metadata.yaml` (scope por tool), `lia-agent-system/app/tools/scope_config.py` (SCOPE_TOOL_MAPPING), `lia-agent-system/app/orchestrator/context_adapter.py` (PAGE_TO_CONTEXT_TYPE), e os `domain.py` + `actions/*.py` do v5.*
