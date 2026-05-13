# Fluxo do Wizard de Criação de Vagas

> Mapa completo do wizard de criação de vagas da Plataforma LIA, com nós do
> LangGraph, decisões de roteamento, stages, integração com `TenantAwareAgentMixin`
> (Task #1043) e índice de arquivos de referência.

A LIA tem **dois wizards convivendo** durante a migração canônica
(`.planning/adrs/ADR-CANONICAL-001-wizard-domain.md`):

| | Wizard A (legacy) | Wizard B (canônico) |
|---|---|---|
| Entry point | `POST /api/v1/wizard/smart-orchestrate` | Chat principal → `MainOrchestrator` → `WizardReActAgent` |
| Implementação | `JobWizardGraph` (StateGraph custom) | `LangGraphReActBase.create_react_agent` |
| Status | CANONICAL-EXEMPT (mantido só para HITL resume) | Piloto canônico do `TenantAwareAgentMixin` (T-B) |
| Persistência | `PostgresSaver` (LangGraph nativo) | `PostgresSaver` |
| Arquivo principal | `app/domains/job_management/agents/job_wizard_graph.py` | `app/domains/job_management/agents/wizard_react_agent.py` |

---

## 1. Entrada HTTP — wizard A (`/smart-orchestrate`)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  Frontend (chat-first, plataforma-lia/Next.js)                             │
│  POST /api/v1/wizard/smart-orchestrate                                     │
│  body: { message, current_stage, collected_data, conversation_history,     │
│          conversation_id?, company_id?, user_id? }                         │
└────────────────┬───────────────────────────────────────────────────────────┘
                 │  Authorization: Bearer <jwt>?  (opcional → dev fallback)
                 ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  app/api/v1/wizard_smart_orchestrator.py:151  smart_orchestrate()          │
│  ─ Depends(get_current_user_or_demo)  ◄── PR-A: sempre amarra usuário ao   │
│                                            CANONICAL_DEMO_UUID em dev      │
│  ─ session_id = conv_id or create_session_id(user.company_id)              │
│  ─ company_id = req.company_id or get_user_company_id(user)                │
│  ─ backend_stage = map_frontend_to_backend_stage(stage)                    │
│  ─ initial_state: JobWizardState  (TypedDict do lia-agents-core)           │
└────────────────┬───────────────────────────────────────────────────────────┘
                 │  await job_wizard_graph.invoke(initial_state)
                 ▼
                ┌──────────────────────────────────────────┐
                │  JobWizardGraph._invoke_langgraph(state) │
                │  (cria StateGraph na 1ª chamada, lazy)   │
                └────────────────┬─────────────────────────┘
                                 │
                                 ▼
```

## 2. StateGraph — nós, edges e roteadores

`app/domains/job_management/agents/job_wizard_graph.py:181  _build_langgraph()`

```
                              ┌─────────────────────────┐
                              │   set_entry_point       │
                              │ "intent_classifier"     │
                              └────────────┬────────────┘
                                           │
                                           ▼
                  ┌──────────────────────────────────────────┐
                  │  NODE: intent_classifier                 │
                  │  → classifica WizardIntent (LLM)         │
                  │  app/agents/nodes.py                     │
                  │  Intents possíveis (lia_agents_core):    │
                  │   - START_FROM_SCRATCH / USE_EXISTING /  │
                  │     USE_TEMPLATE                         │
                  │   - HELP / ASK_QUESTION                  │
                  │   - PROVIDE_INFO / MODIFY                │
                  │   - SKIP / GO_BACK / CONFIRM             │
                  └────────────┬─────────────────────────────┘
                               │
              add_conditional_edges("intent_classifier",
                                    route_intent_classifier)
                               │
        ┌──────────────────────┼──────────────────────────┐
        │                      │                          │
        │ START/USE/HELP/ASK   │ PROVIDE_INFO / MODIFY    │ SKIP/GO_BACK/CONFIRM
        ▼                      ▼                          ▼
┌──────────────────┐  ┌─────────────────────┐  ┌──────────────────────┐
│ response_        │  │ NODE: field_        │  │ NODE: stage_         │
│   generator      │  │   extractor         │  │   transition         │
│ (atalho —        │  │ (LLM extrai dados   │  │ (avança/volta etapa) │
│  sem extrair)    │  │  do user_message)   │  │                      │
└────────┬─────────┘  └──────────┬──────────┘  └──────────┬───────────┘
         │                       │                        │
         │           add_edge("field_extractor",          │
         │                    "tool_router")              │
         │                       ▼                        │
         │            ┌───────────────────────┐           │
         │            │ NODE: tool_router     │           │
         │            │ (decide se chama tool │           │
         │            │  baseado em stage +   │           │
         │            │  campos coletados)    │           │
         │            └──────────┬────────────┘           │
         │                       │                        │
         │       add_conditional_edges("tool_router",     │
         │                              route_tool_router)│
         │                       │                        │
         │       ┌───────────────┴────────────────┐       │
         │       │ tool_calls > 0  │  tool_calls = 0      │
         │       ▼                 ▼                      │
         │  ┌─────────────┐  (fall through)               │
         │  │ NODE: tool_ │                               │
         │  │  executor   │ ◄── chama get_stage_tools()   │
         │  │             │     wizard_tool_registry.py   │
         │  └──────┬──────┘                               │
         │         │  add_edge("tool_executor",           │
         │         │           "response_generator")      │
         │         ▼                                      │
         └───►┌──────────────────────────────┐            │
              │ NODE: response_generator     │            │
              │ (LIA gera mensagem PT-BR     │            │
              │  com tenant_context_snippet  │            │
              │  + stage_context + memory)   │            │
              └──────────────┬───────────────┘            │
                             │                            │
                  add_edge("response_generator",          │
                           "stage_transition")            │
                             ▼                            ▼
                    ┌──────────────────────────────────────┐
                    │ NODE: stage_transition               │
                    │ (avalia transition_criteria do       │
                    │  STAGE_DEFINITIONS, define           │
                    │  state["should_continue"])           │
                    │                                      │
                    │  ⚠ interrupt_before=["stage_         │
                    │     transition"]  ◄── HITL: pausa    │
                    │     antes de criar a vaga (CONFIRM)  │
                    └──────────────┬───────────────────────┘
                                   │
                  add_conditional_edges("stage_transition",
                                        route_stage_transition)
                                   │
                  ┌────────────────┴────────────────┐
                  │ should_continue = False         │ should_continue = True
                  ▼                                 ▼
                ┌─────┐                  ┌─────────────────────┐
                │ END │                  │ intent_classifier   │
                └─────┘                  │ (loop — multi-turn) │
                                         └─────────────────────┘
```

## 3. Decisões dos roteadores (linhas exatas)

`job_wizard_graph.py:203-225`

```
route_intent_classifier(state) → str        route_tool_router(state) → str
─────────────────────────────────────        ─────────────────────────────────
intent ∈ {START_FROM_SCRATCH,                len(tool_calls) > 0
          USE_EXISTING, USE_TEMPLATE,           → "tool_executor"
          HELP, ASK_QUESTION}                else
   → "response_generator"                       → "response_generator"
intent ∈ {SKIP, GO_BACK, CONFIRM}
   → "stage_transition"                     route_stage_transition(state) → str
default (PROVIDE_INFO, MODIFY)               ─────────────────────────────────
   → "field_extractor"                       not should_continue → "end" (END)
                                             else                → "continue"
                                                                   (loop intent_classifier)
```

## 4. Stages do wizard (`stage_context.py:STAGE_DEFINITIONS`)

```
┌──────────────────┬───────────────────────────┬──────────────────────────────┐
│ Stage            │ required_fields           │ transition_criteria          │
├──────────────────┼───────────────────────────┼──────────────────────────────┤
│ input-evaluation │ title, department         │ ambos preenchidos            │
│ jd-enrichment    │ title                     │ usuário confirmou sugestões  │
│ salary           │ salary_min, salary_max    │ faixa definida               │
│ competencies     │ skills                    │ ≥ 3 skills                   │
│ wsi-questions    │ screening_questions       │ recrutador aprovou perguntas │
│ review/publish   │ todos os anteriores       │ CONFIRM intent → cria vaga   │
└──────────────────┴───────────────────────────┴──────────────────────────────┘
                          ↓ ordem definida em STAGE_DEFINITIONS["next_stage"]
   input-evaluation → jd-enrichment → salary → competencies → wsi-questions → publish
```

## 5. Onde o tenant context entra (fix da Task #1043)

```
get_current_user_or_demo (auth/dependencies.py:271)
        │  PR-A: company_id = CANONICAL_DEMO_UUID  ◄── era "demo_company"
        ▼
WizardReActAgent.__init__   (TenantAwareAgentMixin, tenant_strict_override=True)
        │
        ▼
_get_tenant_context_snippet (shared/agents/tenant_aware_agent.py:514)
        │  PR-C: se snippet pré-existente OU recém-renderizado contém
        │        "sua empresa" → MissingTenantContextError (fail-LOUD)
        ▼
PromptComposer injeta {tenant_context_snippet} no system prompt
        │  PR-B: 8 YAMLs proíbem LLM de re-perguntar dados do snippet
        ▼
LLM responde sobre a vaga, NÃO sobre identidade da empresa/recrutador
```

## 6. Wizard B canônico (chat principal) — fluxo paralelo

```
WebSocket /chat ─→ MainOrchestrator ─→ CascadedRouter
                                              │
                                              ▼ intent=create_job
                                    ┌─────────────────────┐
                                    │ WizardReActAgent    │
                                    │  (LangGraph React)  │
                                    └──────────┬──────────┘
                                               │
              create_react_agent(LLM, tools, checkpointer=PostgresSaver)
                                               │
                                ┌──────────────┴──────────────┐
                                ▼                             ▼
                        ┌──────────────┐              ┌──────────────┐
                        │ agent_node   │  ←─────────  │  tools_node  │
                        │ (LLM thinks) │              │ (executes)   │
                        └──────┬───────┘              └──────────────┘
                               │
                               ▼ tools_condition: continue | end
                            ┌─────┐
                            │ END │
                            └─────┘
```

## 7. Arquivos de referência (todos relativos a `lia-agent-system/`)

| Arquivo | Papel |
|---|---|
| `app/api/v1/wizard_smart_orchestrator.py` | Endpoint REST (wizard A) |
| `app/domains/job_management/agents/job_wizard_graph.py` | StateGraph custom (wizard A) |
| `app/agents/nodes.py` | Implementação dos 6 nós (wizard A) |
| `app/domains/job_management/agents/stage_context.py` | `STAGE_DEFINITIONS` + `get_stage_context()` |
| `app/domains/job_management/agents/wizard_system_prompt.py` | `build_system_prompt(stage_context, memory)` |
| `app/domains/job_management/agents/wizard_tool_registry.py` | 14 tools `@tool_handler("wizard")` |
| `app/domains/job_management/agents/wizard_react_agent.py` | Wizard canônico B (ReAct) |
| `app/domains/job_creation/graph.py` | `JobCreationGraph` (futuro substituto, ADR-CANONICAL-001 fase 2) |
| `app/domains/job_creation/services/` | `WizardSessionService` (canônico) |
| `app/shared/agents/tenant_aware_agent.py` | Mixin com `_get_tenant_context_snippet` (PR-C) |
| `app/auth/dependencies.py` | `get_current_user_or_demo` (PR-A) |
| `app/auth/models.py` | `User.company_id` + `@validates` (PR-D) |
| `app/prompts/domains/job_management.yaml` | Prompt do wizard B com regra anti-T-E (PR-B) |
| `lia_agents_core.state_machine.JobWizardState` | TypedDict do estado |
| `lia_agents_core.checkpointer.get_checkpointer()` | `PostgresSaver` compartilhado |
| `.planning/adrs/ADR-CANONICAL-001-wizard-domain.md` | Plano de migração A → B |

## 8. Cheat-sheet das 14 tools do wizard

`wizard_tool_registry.py` — todas decoradas `@tool_handler("wizard")`, filtradas
por stage via `get_stage_tools(stage)`:

```
input-evaluation  → search_existing_jobs, suggest_job_template, save_job_basics
jd-enrichment     → enrich_responsibilities, enrich_benefits, suggest_description
salary            → fetch_salary_benchmark, validate_salary_range
competencies      → suggest_skills, suggest_behavioral_competencies
wsi-questions     → generate_wsi_questions, customize_wsi_question
review/publish    → validate_job_compliance, publish_job
```

## TL;DR do que acontece em uma mensagem

1. Frontend manda `POST /smart-orchestrate` com a frase do recrutador.
2. `get_current_user_or_demo` resolve o usuário (e desde Task #1043 o
   `company_id` é UUID válido).
3. `JobWizardGraph.invoke()` entra no `intent_classifier` → LLM rotula o intent.
4. Roteador despacha para `field_extractor` (extrai dados) → `tool_router`
   (decide se chama tool) → opcionalmente `tool_executor` → `response_generator`
   (LIA escreve a resposta com `tenant_context_snippet` injetado).
5. `stage_transition` avalia se os `transition_criteria` da stage atual foram
   batidos. Se sim, marca avanço. **`interrupt_before=["stage_transition"]`** dá
   HITL antes de qualquer mutação destrutiva (publicar vaga).
6. Se `should_continue=True`, loopa para `intent_classifier`; senão termina e
   devolve `SmartOrchestrateResponse` para o frontend.
