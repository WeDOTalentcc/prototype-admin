# LIA AI Layer — Architecture Tree

> **Fonte-da-verdade = código.** This document was produced by walking the real
> filesystem of `lia-agent-system/app/` and `lia-agent-system/libs/agents-core/`
> (not by trusting `ARCHITECTURE.md`, `ARCHITECTURE_TARGET*.md`, or the
> `LIA_REFACTORING_REPORT*.md` files, several of which describe aspirational
> target states). Every path shown below exists in the tree at the time of
> writing. Noise (`__pycache__`, `*.pyc`, test internals, migration internals)
> is collapsed or omitted.

The AI layer is a FastAPI service that turns recruiter/candidate natural-language
input into routed, tenant-scoped, compliance-wrapped agent executions. A request
flows:

```
HTTP / SSE (canonical) / WebSocket (legacy)
        │
   app/main.py  ──(lifespan: install_llm_guards → bootstrap → init_db → DomainRegistry → orchestrator → tools)
        │
   middleware (auth_enforcement → rate_limit → idempotency → audit_access → response_envelope)
        │
   app/api/orchestrator_routes.py
        │
   app/orchestrator/  ── routing → execution → (supervisor / guards / action_executor)
        │
   app/domains/<name>/agents/*react_agent.py   (one of the 16 ReActAgents)
        │
   domain tools  ──(via libs/agents-core react loop + tool_handler)──▶ services / repositories
        │
   app/shared/  (llm · compliance · tenant · audit · messaging) wraps every step
```

> **Review markers (this revision).** Items flagged for follow-up per the
> architecture diagnosis (§14) carry an inline marker: 🔴 FIX (a divergence or
> risk to correct), 🟡 REVIEW (consistency / architecture debt to decide on),
> 🔵 NOTE (minor cleanup or special case to watch). Every marked item is
> consolidated, with the file(s) to touch, in §16 (Action Register).

---

---

## Sumário

> **Dica de leitura:** §0 + Glossário são para orientação inicial; §1–9 são
> infraestrutura (boot, orquestração, domínios, primitivas, compliance); §10–20
> são referência de capabilities; §21–27 são apêndices técnicos e mapas.
> Use Ctrl+F / Cmd+F com o número da seção para navegar.

| Seção | Título | Para quem |
|---|---|---|
| [§0](#0-o-que-é-a-wedotalent--contexto-para-novos-leitores) | O que é a WeDOTalent | Todos |
| [Glossário](#glossário) | Termos canônicos do projeto | Todos |
| **Infraestrutura** | | |
| [§1](#1-entry-point--cross-cutting-bootstrap) | Entry point & bootstrap | Dev backend |
| [§2](#2-orchestration-layer--apporchestratorion) | Orchestration layer | Dev backend / IA |
| [§3](#3-core-agents--appagents) | Core agents (inventory) | Dev IA |
| [§4](#4-domains--appdomains) | Domains (mapa completo) | Dev backend / IA |
| [§5](#5-cross-cutting-ai-infrastructure--appshared) | Cross-cutting AI infrastructure | Dev IA |
| [§6](#6-top-level-ai-plumbing--appprompts-apptools) | AI plumbing (prompts, tools) | Dev IA |
| [§7](#7-low-level-primitives--libsagents-core) | Low-level primitives (libs) | Dev IA |
| [§8](#8-cross-cutting-concerns) | Compliance, controles, PII | Dev compliance / IA |
| [§8.1](#81-cross-cutting-control-coverage-matrix) | ↳ Coverage matrix (controles × agentes) | Dev compliance |
| [§8.2](#82-pii-data-flow-map) | ↳ PII data-flow map | Dev compliance |
| [§8.3](#83-embeddings-which-feature-embeds-what-with-which-provider-and-is-it-byok) | ↳ Embeddings & BYOK | Dev IA |
| [§9](#9-fastapi--rails-boundary-one-line-note) | FastAPI ↔ Rails boundary | Dev backend |
| **Referência** | | |
| [§10](#10-domain--agent-glossary) | Domain & agent glossary | Dev IA / produto |
| [§10.1](#101-the-16-canonical-reactagents-what-each-does) | ↳ Os 16 agentes canônicos (capabilities) | Dev IA |
| [§10.2](#102-domains-by-class-one-line-purpose) | ↳ Domínios por classe | Dev backend |
| [§11](#11-capability-catalog) | Capability catalog | Produto / dev |
| [§12](#12-federated-vs-supervisor-orchestration-what-is-on--off) | Federated vs Supervisor (ON/OFF) | Dev IA |
| [§13](#13-agent-studio-custom-agents) | Agent Studio | Dev produto |
| [§14](#14-enterprise-architecture-diagnosis) | Diagnóstico de arquitetura | Tech lead |
| [§15](#15-effort-estimate-relocating-the-30-repository-stubs) | Estimativa de esforço (repository stubs) | Tech lead |
| [§16](#16-action-register-follow-up-backlog) | Action Register (backlog técnico) | Tech lead |
| **Integrações & features avançadas** | | |
| [§17](#17-microsoft-teams--microsoft-graph-integration) | Microsoft Teams integration | Dev integração |
| [§18](#18-proactive-alerts--monitoring) | Alertas proativos & monitoring | Dev produto |
| [§19](#19-learning-loops--adaptive-intelligence) | Learning loops & Big Five | Dev IA |
| [§20](#20-chat-first-navigation) | Chat-first navigation | Dev produto |
| **Apêndices técnicos** | | |
| [§21](#21-chat-transport-architecture) | Chat transport (SSE vs WS) | Dev backend |
| [§22](#22-rich-response-protocol-rrp) | Rich Response Protocol (RRP) | Dev IA / frontend |
| [§23](#23-eligibility-questions--canonical-shape-and-producer) | Eligibility questions (canonical) | Dev IA |
| [§24](#24-wsi--workplace-science-index) | WSI — Workplace Science Index | Dev IA / produto |
| [§25](#25-triagem-session--lifecycle-completo) | Triagem session lifecycle | Dev IA |
| [§26](#26-mapa-da-api-surface) | Mapa da API surface (293 endpoints) | Dev backend |
| [§27](#27-mapa-de-funcionalidades-de-ia-por-página) | Mapa de funcionalidades de IA por página | Produto |

---

## 0. O que é a WeDOTalent — contexto para novos leitores

### 0.1 O produto

A **WeDOTalent** é uma plataforma SaaS de recrutamento e seleção voltada para
equipes de RH corporativas. Ela cobre o ciclo completo de contratação: da
abertura de uma vaga à oferta de emprego, passando por sourcing, triagem de
currículos, entrevistas, avaliação comportamental e analytics de pipeline.

O diferencial central é que **a IA não é um add-on** — ela está embutida em
cada etapa. O recrutador interage com a plataforma via chat conversacional;
a IA interpreta a intenção, executa as ações (buscar candidatos, mover no
pipeline, enviar comunicações, gerar relatórios) e retorna resultados
estruturados com evidências. O modelo mental correto não é "chat + sistema"
— é um sistema que tem chat como interface primária.

### 0.2 A persona de IA (LIA é o padrão; o tenant pode trocar)

A persona conversacional tem um nome, um tom de voz e um conjunto de
instruções. Por padrão o nome é **LIA** e o tom é "profissional e objetivo".
Mas isso é configurável por empresa: em **Configurações → Inteligência →
Personalidade da IA**, cada tenant pode definir:

- **Nome** da IA (ex: "Maya", "Recru", ou qualquer nome da marca)
- **Tom** (6 opções canônicas: profissional, empático, direto, consultivo,
  energético, formal)

A mudança é puramente de persona — o mesmo agente, as mesmas ferramentas, as
mesmas regras de compliance continuam operando. O que muda é como a IA se
apresenta e escreve. Portanto, ao longo deste documento "LIA" refere-se à
**camada de IA**, não ao nome que um tenant específico configurou.

> Implementação: `app/domains/persona/services/ai_persona_validator.py`
> (validação) + `app/shared/prompts/system_prompt_builder.py`
> (`_append_ai_persona_override` — a persona base é imutável; o override
> apenas appenda seções). Detalhes em `CLAUDE.md §Per-tenant AI persona`.

### 0.3 Quem deve ler este documento e como

| Perfil | O que buscar primeiro |
|---|---|
| Dev entrando no projeto | §0 (contexto) → Glossário → §1–2 (fluxo de request) → §4 (domínio relevante) |
| Dev de IA / LLM | §7 (primitivas) → §2 (orquestração) → §12 (federated path) → §8 (compliance) |
| Tech lead / arquiteto | §14 (diagnóstico) → §8 (controles) → §15–16 (dívida técnica) |
| Líder de produto | §0 → Glossário → §10 (glossário de agentes) → §11 (capabilities) → §27 (IA por página) |
| Dev de compliance | §8 → §8.1 (matriz) → §8.2 (PII) → §8.3 (embeddings) → §24 (WSI scoring) |

### 0.4 Como uma mensagem no chat vira uma ação no pipeline

Para tornar a arquitetura concreta, aqui está o que acontece quando um
recrutador digita "mova a Ana Silva para a etapa de entrevista técnica":

```
1. HTTP POST /api/v1/chat/{session_id}/stream  (SSE, §21)
   └─ AuthEnforcementMiddleware seta _current_company_id ContextVar
   └─ PromptInjectionGuard filtra a mensagem de entrada
   └─ EntityResolver faz lookup fuzzy "Ana Silva" → candidate_id no DB
      (company-scoped; resultado injetado como hint no prompt)

2. CascadedRouter (§12) escolhe o agente:
   Tier 1 LRU → miss → Tier 4 FastRouter → regex "mova" + "etapa" → domain: pipeline

3. PipelineReActAgent recebe a mensagem + o hint da Ana
   └─ Prompt: lia_persona + compliance_block + tenant_snippet + mensagem
   └─ ReAct loop: LLM raciocina → chama tool move_candidate_stage
   └─ tool_handler garante company_id do ContextVar (não do LLM)

4. @require_hitl na tool move_candidate_stage:
   └─ LIA_HITL_GATE=OFF → prossegue; ON → emite `approval_required` SSE

5. move_candidate_stage executa:
   └─ PipelineTransitionService valida a transição (regras de negócio)
   └─ FairnessGuard C1-C5 (LGPD Art.20) passa no write
   └─ AuditService.log_decision (obrigatório neste domínio)
   └─ Evento disparado via RabbitMQ → Rails atualiza o ATS-of-record

6. SSE emite:
   └─ `reasoning_step` (raciocínio progressivo, se ativado)
   └─ `tool_started` / `tool_finished`
   └─ `message` { content: "Ana Silva movida para Entrevista Técnica ✓",
                   response_blocks: [CandidateCardBlock, FunnelBlock] }
```

Esse fluxo — middleware → entity resolver → router → agent → tool → audit →
SSE — é invariante para todas as ações do chat. O que muda é qual agente é
escolhido e quais ferramentas ele chama.

---

## Glossário

Termos usados neste documento com significado específico ao projeto.

| Termo | Definição |
|---|---|
| **Agent / Agente** | Unidade de IA que raciocina em loop (ReAct: Razão → Ação → Observação) e usa ferramentas para completar tarefas. Diferente de uma função simples porque decide sozinho quais passos executar. |
| **ReActAgent** | Implementação de agente que usa o padrão ReAct (LangGraph). Herda `LangGraphReActBase` + `TenantAwareAgentMixin`. 16 agentes canônicos. |
| **Tool / Ferramenta** | Função Python que um agente pode chamar. Recebe parâmetros, executa lógica de negócio, retorna resultado estruturado. Decorada com `@tool_handler`. |
| **Domain / Domínio** | Agrupamento funcional do código (ex: `cv_screening`, `sourcing`). Domínios agenticos têm agente + tools + services + repositories. |
| **CascadedRouter** | O roteador em cascata que decide qual agente atende uma mensagem. 6–8 tiers de custo crescente: LRU → Redis → pgvector → regex → LLM. |
| **WSI** | Workplace Science Index. A metodologia proprietária de triagem estruturada da WeDOTalent. Um conjunto de perguntas geradas por IA (comportamentais + técnicas) com scoring OCEAN. Veja §24. |
| **HITL** | Human-In-The-Loop. Gates que pausam a execução aguardando confirmação humana antes de ações irreversíveis (enviar email, mover candidato, publicar vaga). |
| **Tenant** | Uma empresa cliente da WeDOTalent. Todo dado é isolado por `company_id`; nenhum agente pode ver dados de outro tenant. |
| **BYOK** | Bring Your Own Key. Capacidade de um tenant usar sua própria chave de API LLM (Claude/Gemini/OpenAI) em vez da chave da plataforma. |
| **C3b layer** | Camada de compliance realtime no chat: HateSpeechGuard + PII strip + PromptInjectionGuard + FairnessGuard L3 + FactChecker + AuditService. Envolve cada turno do chat. |
| **FairnessGuard** | Sistema de 3 camadas (L1 regex, L2 implicit-bias, L3 HR-sensitive) que bloqueia outputs discriminatórios baseados em atributos protegidos (gênero, raça, idade, etc). |
| **LangGraph** | Framework para orquestração de agentes como grafos de nós. Cada nó é uma função; o grafo define as transições. Usado no wizard de criação de vagas (15 nós). |
| **interrupt()** | Primitiva do LangGraph que pausa o grafo e aguarda input humano antes de continuar. Usado nos 4 HITL gates do wizard. |
| **RRP** | Rich Response Protocol. Sistema de blocos tipados (prose, evidence_stack, score_explainer, comparison_table, funnel, candidate_card) que a IA retorna no lugar de markdown bruto. |
| **OCEAN / Big Five** | Modelo psicológico dos 5 grandes traços de personalidade: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism. Usado no WSI para mapear comportamentos a traços. |
| **Triagem session** | A sessão de triagem de um candidato para uma vaga. Inclui consent → eligibility → WSI → scoring → resultado. Canônica em `TriagemSessionService`. |
| **SSE** | Server-Sent Events. O protocolo de transporte canônico do chat (HTTP streaming unidirecional). O cliente abre um POST e o servidor retorna eventos em tempo real. |
| **PII** | Personally Identifiable Information. CPF, RG, email, telefone, nome — dados mascarados em logs e, parcialmente, em prompts enviados ao LLM. |
| **ContextVar** | `contextvars.ContextVar` do Python. Variável isolada por contexto de request (equivalente a thread-local em async). Usado para `_current_company_id`, `_active_vacancy_id`, etc. |
| **Persona** | Nome + tom configuráveis por tenant para a IA. "LIA" é o padrão; cada empresa pode renomear. Veja §0.2. |
| **Action Register** | Registro de ações pendentes de implementação ou correção. Veja §16. |
| **ADR** | Architecture Decision Record. Documento que registra uma decisão arquitetural com contexto, alternativas e consequências. Em `docs/specs/ai/ADR-*.md`. |

---

## 1. Entry point & cross-cutting bootstrap

```
lia-agent-system/
├── app/
│   ├── main.py                     # FastAPI app; lifespan boots LLM guards, checkpointer,
│   │                               #   DomainRegistry, orchestrator, tools, schedulers.
│   │                               #   Fail-fast prod guards (Redis enc, LLM keys, tenant-strict).
│   ├── agents_registry.yaml        # Declarative agent registry (name→class_path→model_id),
│   │                               #   hot-reloaded by app/core/agent_registry_watcher.py.
│   ├── api/
│   │   └── orchestrator_routes.py  # initialize_orchestrator() + chat entry routes
│   ├── middleware/                 # auth_enforcement (sets _current_company_id ContextVar),
│   │                               #   rate_limiter, idempotency, request_id,
│   │                               #   audit_access_middleware, response_envelope
│   └── core/                       # config, database, sentry, logging, prompt_version_loader
```

`main.py` imports `app.shared.llm_bootstrap.install_llm_guards` **first** — before
any module instantiates an LLM client — so every SDK call is monkey-patched for
PII stripping, per-tenant credit gating, and audit logging.

---

## 2. Orchestration layer — `app/orchestrator/`

The orchestrator decides *who* handles a request and *how* it executes. Routing
picks a domain/agent; execution runs the agentic loop; guards, supervisor, and
action layers wrap state-changing work.

```
app/orchestrator/
├── routing/
│   ├── cascaded_router.py            # CascadedRouter — multi-tier severity-based routing,
│   │                                 #   Tier 6 ReAct fallback wires app/domains/autonomous
│   ├── fast_router.py                # Cheap heuristic first-pass router
│   ├── llm_cascade.py                # LLM-backed cascade classification
│   ├── domain_mappings.py            # intent/keyword → domain_id maps
│   ├── confirmation_classifier.py    # PT-BR natural confirmation detection ("sim", "vamos")
│   ├── job_creation_disambiguator.py # detect_job_creation — composite-phrase guard so
│   │                                 #   Plan&Execute NEVER creates a job (wizard-only)
│   ├── post_wizard_continuation.py   # conversational continuation after wizard terminal stage
│   └── pe_add_to_vacancy_continuation.py
├── execution/
│   ├── main_orchestrator.py          # MainOrchestrator — top-level execution coordinator
│   ├── agentic_loop.py               # ReAct loop driver (defense-in-depth credit gate)
│   ├── task_planner.py               # Plan&Execute planner (LIA_V2_USE_PLAN_SERVICE)
│   ├── state_manager.py              # per-turn execution state
│   ├── pending_action.py             # deferred/HITL action representation
│   └── registry.py                   # execution-level registry
├── supervisor/
│   └── handoff_tools.py              # CrewAI-style supervisor pre-graph handoff tools
├── action_executor/
│   ├── executor.py                   # ActionExecutorService — closed-loop cross-chat action exec
│   ├── action_types.py               # action enum/types
│   ├── intents_config.py             # intent→action config
│   └── utils.py
├── action_handlers/                  # per-domain action handler implementations
│   ├── candidate_actions.py
│   ├── job_actions.py
│   ├── pipeline_actions.py
│   ├── communication_actions.py
│   ├── interview_actions.py
│   ├── sourcing_actions.py
│   ├── analytics_actions.py
│   ├── handler_deps.py
│   └── _handler_hooks.py
├── guards/
│   ├── precondition_checker.py       # preconditions before state change
│   ├── rail_a_capability_check.py    # capability gating
│   ├── tenant_budget.py              # per-tenant budget guard
│   └── wizard_state.py               # wizard-state guard
├── context/
│   ├── navigation_intent.py          # useNavigationIntent backend counterpart (T-1165)
│   ├── chat_adapter.py
│   ├── context_adapter.py
│   ├── view_context.py
│   ├── intent_types.py
│   ├── temporal_resolver.py
│   └── empty_result_guidance.py
├── heuristics/
│   ├── cv_matching_detector.py
│   └── technical_response_detector.py
├── memory/
│   ├── memory_resolver.py
│   ├── semantic_cache.py
│   └── vector_semantic_cache.py
├── observability/
│   └── _observability.py
├── services/
│   ├── plan_orchestration_service.py # PlanExecutor wiring (real DomainRegistry+DomainWorkflow)
│   ├── policy_gate_service.py        # policy gate before execution
│   ├── fallback_react_service.py     # ReAct fallback service
│   ├── rail_a_hint_override.py
│   └── context_type_override.py
├── legacy/
│   ├── orchestrator.py               # pre-refactor orchestrator (still referenced)
│   └── tasting_engine.py
└── config/
    └── domain_routing.yaml           # declarative routing config
```

---

## 3. Core agents — `app/agents/`

A thin layer of non-domain agent primitives. The bulk of agents live inside each
domain (§4); this folder holds shared graph nodes and the policy-setup agent.

```
app/agents/
├── nodes.py                # shared LangGraph node helpers
└── policy_setup_agent.py   # chat-driven policy setup agent (pairs with app/domains/policy)
```

### The 16 canonical ReActAgents

> Esta tabela mostra o **inventário** (classe + path). Para ver o que cada agente **faz / quando dispara**, veja [§10.1](#101-the-16-canonical-reactagents-what-each-does).

The inventory is sentinel-locked by
`tests/integration/agents/test_tenant_aware_rollout_t_d.py` — adding a 17th
without following the T-D pattern (TenantAwareAgentMixin) breaks the build.

| # | Agent class | Lives in |
|---|---|---|
| 1 | `AnalyticsReActAgent` | `app/domains/analytics/agents/analytics_react_agent.py` |
| 2 | `ATSIntegrationReActAgent` | `app/domains/ats_integration/agents/ats_integration_react_agent.py` |
| 3 | `AutomationReActAgent` | `app/domains/automation/agents/automation_react_agent.py` |
| 4 | `AutonomousReActAgent` | `app/domains/autonomous/agents/autonomous_react_agent.py` |
| 5 | `CommunicationReActAgent` | `app/domains/communication/agents/communication_react_agent.py` |
| 6 | `CompanySettingsReActAgent` | `app/domains/company_settings/agents/company_react_agent.py` |
| 7 | `PipelineReActAgent` | `app/domains/cv_screening/agents/pipeline_react_agent.py` |
| 8 | `PolicyReActAgent` | `app/domains/hiring_policy/agents/policy_react_agent.py` |
| 9 | `JobsManagementReActAgent` | `app/domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` |
| 10 | `KanbanReActAgent` | `app/domains/recruiter_assistant/agents/kanban_react_agent.py` |
| 11 | `TalentFunnelReActAgent` | `app/domains/recruiter_assistant/agents/talent_funnel_react_agent.py` |
| 12 | `SourcingReActAgent` | `app/domains/sourcing/agents/sourcing_react_agent.py` |
| 13 | `TalentPoolReActAgent` | `app/domains/talent_pool/agents/talent_pool_agent.py` |
| 14 | `WizardReActAgent` | `app/domains/job_management/agents/wizard_react_agent.py` |
| 15 | `CandidateSelfServiceAgent` | `app/domains/candidate_self_service/agents/candidate_react_agent.py` |
| 16 | `PipelineTransitionAgent` | `app/domains/pipeline/agents/pipeline_transition_agent.py` |

> Each domain typically also has parent/sub-agents and a `*_tool_registry.py`,
> `*_stage_context.py`, and `*_system_prompt.py` triple (see §4). The 16 above
> are the canonical *routable* ReActAgents; sub-agents (e.g. sourcing's
> search/enrich/diversity/github/nurture agents) are reachable via tool registries.

> **Nota — 17º agente em desenvolvimento:** `RecruiterCopilotReActAgent`
> (`app/domains/recruiter_assistant/agents/recruiter_copilot_react_agent.py`, 344 linhas)
> existe com herança T-D completa mas **não consta nos 16 canônicos** porque ainda não é
> roteável pelo `CascadedRouter` — está em desenvolvimento como agente federado único
> para consolidar o chat (ver [§12](#12-federated-vs-supervisor-orchestration-what-is-on--off)).
> Quando for promovido, atualizar o sentinel-lock em `test_tenant_aware_rollout_t_d.py` para 17.

---

## 4. Domains — `app/domains/`

**65 directories** no filesystem atual (o `DOMAIN_CATALOG.md` registra 59 — desatualizado desde Sprint 11; os 6 domínios adicionais são stubs pós-Sprint criados sem catalogar), classified as: **13 Agentic** + **3
Micro-Action** (= 16 `@register_domain`), **11 Service**, **30 Repository-stub**,
**2 Canonical-Active-legacy**. Registration is via `@register_domain` in
`app/domains/registry.py`; base contracts in `app/domains/base.py` and
`app/domains/compliance_base.py` (all domains MUST extend `ComplianceDomainPrompt`).

Each domain shows only the canonical sub-parts that **actually exist**.
AI-heavy domains are flagged ⭐.

### Agentic domains (routable by CascadedRouter)

```
app/domains/
├── cv_screening/ ⭐               # CV analysis, WSI evaluation, candidate scoring
│   ├── agents/                    #   pipeline_react_agent, wsi_interview_graph,
│   │                              #   pipeline_{stage_context,system_prompt,tool_registry}
│   ├── tools/                     #   candidate_tools, cv_match_tool, cv_upload_tool
│   ├── services/                  #   cv_parser, cv_scoring_service, rubric_evaluation_service,
│   │                              #   lia_score_service, hitl_service, calibration_profiles,
│   │                              #   personalized_feedback_service, … (30+ services)
│   ├── prompts/
│   ├── config/
│   ├── constants/
│   ├── models/
│   ├── schemas/
│   └── repositories/
├── sourcing/ ⭐                   # Candidate sourcing across channels
│   ├── agents/                    #   sourcing_react_agent (parent) + search/enrich/diversity/
│   │                              #   github/stackoverflow/nurture/passive/referral/planner/
│   │                              #   engagement sub-agents, each w/ *_tool_registry
│   ├── tools/                     #   query_tools, enrichment_tools
│   ├── ports/
│   ├── services/
│   ├── config/
│   └── repositories/
├── job_management/ ⭐             # Job lifecycle + the canonical WizardReActAgent
│   ├── agents/                    #   wizard_react_agent, wizard_{system_prompt,tool_registry},
│   │                              #   stage_context
│   ├── tools/                     #   job_tools, job_wizard_tools, query_tools, job_tools_compat
│   ├── prompts/
│   ├── schemas/
│   ├── services/
│   ├── config/
│   └── repositories/
├── job_creation/ ⭐               # Wizard graph (15 nodes: 11 functional + 4 HITL gates)
│   ├── nodes/                     #   intake, jd_enrichment, competency, wsi_questions,
│   │                              #   salary, bigfive, eligibility, pipeline_template, publish,
│   │                              #   + gate nodes: intake_gate, jd_gate, competency_gate,
│   │                              #   wsi_questions_gate, review_gate, calibration, handoff
│   ├── orchestrator/              #   wizard_orchestrator, wizard_tools, wizard_service_tools,
│   │                              #   wsi_canonical_adapter
│   ├── graph.py
│   ├── domain.py
│   ├── state.py
│   ├── policy_gate.py
│   ├── compliance.py
│   ├── feature_flag.py
│   ├── actions/
│   ├── helpers/
│   ├── internal/
│   ├── services/
│   └── repositories/
├── recruiter_assistant/ ⭐        # General recruiter copilot (fallback domain)
│   ├── agents/                    #   recruiter_copilot, jobs_mgmt, kanban (+action/insight/
│   │                              #   search sub-agents), talent / talent_funnel react agents
│   ├── tools/
│   ├── prompts/
│   ├── services/
│   ├── config/
│   └── repositories/
├── pipeline/ ⭐                   # Pipeline visualization + candidate movement
│   ├── agents/                    #   pipeline_transition_agent + action/context/decision agents
│   ├── tools/
│   ├── models/
│   ├── services/
│   ├── config/
│   └── repositories/
├── communication/ ⭐             # Email / WhatsApp / Teams messaging
│   ├── agents/                    #   communication_react_agent + tool_registry/system_prompt
│   ├── tools/
│   ├── schemas/
│   ├── models/
│   ├── services/
│   ├── config/
│   └── repositories/
├── analytics/                     # Recruitment analytics, reports, dashboards
│   ├── agents/
│   ├── tools/
│   ├── schemas/
│   ├── models/
│   ├── services/
│   ├── config/
│   └── repositories/
├── ats_integration/               # ATS sync (Gupy, Pandapé, Merge)
│   ├── agents/
│   ├── tools/
│   ├── models/
│   ├── services/
│   ├── config/
│   └── repositories/
├── automation/                    # Tasks, reminders, notes, workflow automation
│   ├── agents/
│   ├── tools/
│   ├── models/
│   ├── services/
│   ├── config/
│   └── repositories/
├── hiring_policy/                 # Hiring policy advisory w/ FairnessGuard (PolicyReActAgent)
│   ├── agents/
│   ├── actions/
│   ├── tools/
│   ├── services/
│   ├── config/
│   └── repositories/
├── interview_scheduling/ ⭐       # Scheduling + calendar (LangGraph interview_graph)
│   ├── agents/                    #   interview_graph, interview_scheduling_nodes, system_prompt
│   ├── tools/                     #   scheduling_tools
│   ├── schemas/
│   ├── models/
│   ├── services/
│   ├── config/
│   └── repositories/
└── agent_studio/ ⭐               # Custom agent creation/marketplace (tenant-scoped templates)
    ├── config/                    #   resolved via registry.get_domain_for_company()
    └── repositories/
```

### Micro-action domains (`@register_domain`, lightweight)

```
├── digital_twin/ ⭐                           # Digital twin creation/evaluation
│   └── config/
├── recruitment_campaign/                      # Multi-stage recruitment campaigns
│   └── config/
└── talent_pool/                               # TalentPoolReActAgent
    ├── agents/
    ├── config/
    └── repositories/
```

### Service domains (business logic, not orchestrator-routable)

```
├── ai/                            # LLMService, response cache, prompt mgmt
│   ├── repositories/
│   └── services/
├── interview_intelligence/ ⭐     # bias_detector, comparative_analysis,
│   │                              #   strategic_opinion, interview_wsi,
│   │                              #   feedback_generator, transcription
│   └── services/
├── voice/ ⭐                      # gemini_live_audio, voice_screening_orchestrator,
│   │                              #   voice_core_orchestrator, realtime_credit_session
│   ├── services/
│   ├── plugins/
│   ├── protocols/
│   ├── schemas/
│   └── repositories/
├── persona/ ⭐                    # ai_persona_service + validators
│   └── services/
├── talent_intelligence/ ⭐        # skills ontology, internal mobility, workforce
│   │                              #   planning, market intel, candidate nurture,
│   │                              #   interview_intelligence_tools (cross-call)
│   ├── tools/
│   └── services/
├── company/
├── candidates/
├── recruitment/
├── compliance/
├── consent/
├── credits/
├── billing/
├── integrations_hub/
├── lgpd/
└── modules/
```

### Other domains

```
# Canonical-Active (legacy path, NOT deprecated):
├── autonomous/                    # Tier 6 ReAct fallback for CascadedRouter
│   └── agents/
├── policy/                        # PolicyEngineService, PolicySetupAgent,
│   │                              #   ALPHA1_SECTOR_RULES (sector FairnessGuard)
│   ├── agents/
│   ├── services/
│   └── repositories/
# AI-relevant service domains worth noting:
├── company_settings/ ⭐           # CompanySettingsReActAgent
│   ├── agents/
│   ├── tools/
│   ├── config/
│   └── repositories/
├── candidate_self_service/ ⭐
│   ├── agents/
│   ├── actions/
│   ├── tools/
│   ├── services/
│   ├── config/
│   └── repositories/
├── offer/                         # offer mgmt (SOX audit)
│   ├── agents/
│   ├── tools/
│   ├── models/
│   ├── services/
│   ├── config/
│   └── repositories/
└── opinions/                      # (+ digital_twin/, shown above)
# Repository-stub domains (pure CRUD: __init__.py + dependencies.py + repositories/):
#   admin, admin_settings, agent_memory, approvals, auth, bulk_actions, candidate_lists,
#   chat, clients, client_users, company_culture, data_subject, email_templates, goals,
#   health_check, job_vacancies_analytics, journey_mapping, lia_assistant, notifications,
#   observability, recruitment_journey, saas_metrics, shared_searches, tasks,
#   technical_tests, triagem, trust_center, workforce
```

> Files of note: `app/domains/registry.py` (DomainRegistry singleton +
> `@register_domain` + `get_domain_for_company` Agent-Studio resolution +
> `_YamlDomainProxy`), `app/domains/DOMAIN_CATALOG.md` (authoritative
> classification), `app/domains/base.py`, `app/domains/compliance_base.py`,
> `app/domains/workflow.py`.

---

## 5. Cross-cutting AI infrastructure — `app/shared/`

This is the wrapper layer every agent passes through: LLM access, prompts,
compliance, tenant isolation, audit, messaging, memory, and RAG.

```
app/shared/
├── llm_bootstrap.py            # monkey-patches Anthropic/OpenAI/genai SDK constructors:
│                               #   API-key + base_url injection, PII strip, per-call credit gate,
│                               #   audit log. Single chokepoint for ALL SDK usage.
├── tenant_llm_context.py       # _current_company_id ContextVar reader; per-tenant LLM config
│                               #   (provider/key/model/region) + tenant Gemini/Claude clients
├── domain_action_registry.py   # DomainActionRegistry — single-owner action mapping + aliases
├── tool_catalog.py             # ToolCatalog — system-wide tool inventory
├── tool_handler.py             # ToolHandler — executes tool calls w/ tenant context
├── pii_masking.py              # install_global_pii_masking + strip_pii_for_llm_prompt
├── prompt_injection.py         # prompt-injection detection helpers
├── tenant_guard.py
├── tenant_session.py
├── runtime_context.py
├── llm/
│   ├── callbacks.py            # LangChain callbacks (tracing/metrics)
│   └── safe_response.py        # safe LLM response wrapping
├── prompts/
│   ├── system_prompt_builder.py    # SystemPromptBuilder — central prompt assembly
│   ├── prompt_composer.py
│   ├── loader.py
│   ├── templates.py
│   ├── agent_prompts.py
│   ├── job_wizard.py
│   ├── voice_system_prompt.py
│   ├── persona_aware_prompt.py
│   ├── training_persona.py
│   ├── anti_sycophancy_block.py
│   ├── cot.py
│   ├── few_shot_examples.py
│   ├── intent_few_shot_examples.py
│   ├── interaction_patterns.py
│   ├── glossary_loader.py
│   └── examples/
├── compliance/                 # 3-pillar compliance (LGPD + SOX + EU AI Act)
│   ├── fairness_guard.py
│   ├── fairness_guard_middleware.py
│   ├── fairness_recursive.py
│   ├── fact_checker.py
│   ├── prompt_injection_guard.py
│   ├── hate_speech_guard.py
│   ├── protected_attributes.py
│   ├── scoring_safeguards.py
│   ├── safety_category.py
│   ├── c3b_layer.py            # C3b layer (PII strip + Fairness L3 + FactCheck + Audit)
│   ├── audit_service.py
│   ├── audit_writer.py
│   ├── audit_storage.py
│   ├── audit_callback.py
│   ├── audit_decorators.py
│   ├── audit_models.py
│   ├── domain_validators.py
│   └── guardrail_repository.py
├── agents/
│   ├── agent_registry.py       # AgentRegistry (legacy intent map, coexists w/ DomainRegistry)
│   ├── agent_bus.py            # AgentBus — inter-agent message bus
│   ├── tenant_aware_agent.py   # TenantAwareAgentMixin + is_tenant_strict_mode +
│   │                           #   resolve_tenant_snippet_for_non_react (canonical non-ReAct seam)
│   ├── crew_executor.py
│   ├── crew_context.py
│   ├── crew_audit.py
│   ├── crew_models.py
│   ├── crew_examples.py
│   └── agent_types.py
├── tools/
│   ├── export_tools.py
│   ├── insight_tools.py
│   ├── predictive_tools.py
│   └── proactive_tools.py
├── messaging/                  # BrokerInterface abstraction (Redis / RabbitMQ / Pub-Sub)
│   ├── broker_interface.py
│   ├── rabbitmq_producer.py
│   ├── rabbitmq_consumer.py
│   ├── rails_crud_consumer.py
│   ├── rails_event_publisher.py
│   ├── rails_event_schemas.py
│   ├── unified_event_publisher.py
│   ├── platform_events.py
│   ├── dispatchers.py
│   └── celery_config.py
├── memory/
│   ├── conversation_state.py
│   ├── reference_resolver.py
│   └── candidate_list_store.py
├── rag/
│   ├── hybrid_search.py
│   ├── reranker.py
│   ├── realtime_fact_checker.py
│   └── response_watermarker.py
├── hitl/
│   ├── agent_gate.py
│   └── hitl_approval_context.py    # (+ shared/hitl_decorator.py at root)
├── governance/
│   ├── agent_monitoring_service.py
│   └── feature_flag_service.py
├── intelligence/
│   ├── embedding_service.py
│   ├── semantic_search_service.py
│   ├── smart_extractor.py
│   ├── param_patterns.py
│   ├── chunking/              # RecursiveTextSplitter + section_aware/semantic/sliding_window
│   ├── ab_testing/           # thompson_sampler, bandit_posterior_repository
│   └── template_learning/
├── learning/                  # learning loop: correction_capture, feedback_writer,
│                              #   finetuning_export, learning_loop_service, golden curation
└── ml/
    └── ttf_predictor.py       # time-to-fill predictor
```

---

## 6. Top-level AI plumbing — `app/prompts/`, `app/tools/`

```
app/prompts/                    # YAML + Python prompt catalog (registered at startup by
│                               #   app/core/prompt_version_loader.py)
├── domains/                    # per-domain system prompts (YAML):
│   ├── cv_screening.yaml
│   ├── sourcing.yaml
│   ├── job_management.yaml
│   ├── job_creation.yaml
│   ├── company_settings.yaml
│   ├── communication.yaml
│   ├── pipeline.yaml
│   ├── analytics.yaml
│   ├── autonomous.yaml
│   ├── hiring_policy.yaml
│   ├── interview_scheduling.yaml
│   ├── offer.yaml
│   ├── wsi_evaluation.yaml
│   ├── wsi_interview.yaml
│   ├── wsi_layer2_extraction.yaml
│   ├── intent_classification.yaml
│   ├── orchestrator.yaml
│   ├── agent_studio.yaml
│   └── …                       # (31 files total)
├── job_creation/              # wizard gate prompts: gate_classifier, gate_competency,
│   │                          #   gate_review, gate_wsi_questions, wizard_supervisor,
│   │                          #   intake_gate_classifier, wsi_question_distribution, messages
├── shared/                    # lia_persona, compliance_block, guardrails_block,
│   │                          #   defensive, few_shot_template, agent_prompts, policy_setup
├── experiments/              # A/B prompt variants (cascade_router, job_wizard_field_extraction)
├── tenants/                  # per-tenant prompt overrides (__test_tenant__)
├── cot.py
├── examples.py
├── templates.py
├── job_wizard.py
└── *_prompts.py              # jobs_management / kanban_assistant / talent_assistant

app/tools/                      # function-calling tool registry (initialize_tools() in lifespan)
├── registry.py                # central tool registry
├── executor.py                # tool executor
├── categories.py
├── scope_config.py
├── context_helpers.py
├── tool_registry_loader.py
├── tool_registry_metadata.yaml
├── tool_permissions_loader.py
└── tool_permissions.yaml
```

---

## 7. Low-level primitives — `libs/agents-core/`

The reusable agent runtime package (imported as `lia_agents_core`). Domain
ReActAgents build on these primitives; the package has no domain knowledge.

```
libs/agents-core/lia_agents_core/
├── agent_bus.py               # low-level AgentBus primitive
├── react_agent_registry.py    # ReactAgentRegistry — @register_agent decorator + lookup
├── langgraph_react_base.py    # LangGraphReActBase — base class for all ReActAgents
├── langgraph_base.py          # LangGraphBase (sync checkpointer seam)
├── react_loop.py              # the ReAct reason→act loop
├── checkpointer.py            # AsyncPostgresSaver canonical (fail-closed in prod, §main.py)
├── tool_adapter.py
├── timed_tool_node.py
├── nodes.py
├── agent_interface.py
├── agent_scaffold.py
├── contracts.py
├── confidence.py
├── enhanced_agent_mixin.py
├── autonomy_engine.py
├── state_machine.py
├── base_state_machine.py
├── long_term_memory.py
├── working_memory.py
├── memory_integration.py
├── streaming_callback.py
├── observability.py
├── execution_log_store.py
├── learning_extractor.py
├── proactive_worker.py
└── sourcing_engagement_nodes.py
```

> Sibling `libs/` packages (`audit`, `config`, `messaging`, `models`, `schemas`,
> `services`, `utils`) provide shared infra (e.g. `lia_config.database`,
> `lia_models`) consumed across the AI layer.

---

## 8. Cross-cutting concerns

These wrap **every** agent execution regardless of domain:

- **Tenant isolation** — `TenantAwareAgentMixin`
  (`app/shared/agents/tenant_aware_agent.py`) + the `CompanyId` value object +
  the `_current_company_id` ContextVar (set by `AuthEnforcementMiddleware`, read
  by `tenant_llm_context.py` and `llm_bootstrap.py`). Fail-closed in prod via
  `LIA_AGENT_TENANT_STRICT`. Non-ReAct callsites MUST use
  `resolve_tenant_snippet_for_non_react(...)` — the only canonical seam — never
  read `ctx["tenant_context_snippet"]` directly. This is the blast door against
  the recurring *"LIA pergunta company_id no chat"* bug.

- **Compliance 3-pillar (LGPD + SOX + EU AI Act)** — `FairnessGuard`
  (`fairness_guard.py` + recursive + middleware), `FactChecker`
  (`fact_checker.py`), and `BiasAuditService`
  (`app/domains/interview_intelligence/services/bias_detector_service.py`). All
  domains MUST extend `ComplianceDomainPrompt` (`app/domains/compliance_base.py`)
  — enforced at `@register_domain` time, escape hatch
  `LIA_ALLOW_NON_COMPLIANT_DOMAINS=1` (emergency only).

- **Prompt-injection guard** — `app/shared/compliance/prompt_injection_guard.py`
  (+ `app/shared/prompt_injection.py`) screens recruiter/candidate text and LLM
  output before tool execution.

- **PII protection** — `install_global_pii_masking()` masks CPF/email/phone/name
  in all logs; `llm_bootstrap` strips PII from prompts before SDK calls. Both the
  regex layers (CPF/email/phone/RG/CNPJ + quasi-identifiers) and the Presidio NER
  layer for names (PERSON/NRP) are ON by default
  (`LLM_PROMPT_PII_STRIPPING_ENABLED=true`, `LLM_PROMPT_PRESIDIO_ENABLED=true`).
  The full data-flow map and the residual name-leak gap (recruiter chat runs
  `mask_names=False`) are in §8.2.

- **HITL gates** — Two layers:
  1. **Wizard gates** (4): `app/shared/hitl/agent_gate.py` + `app/shared/hitl_decorator.py`;
     LangGraph `interrupt()` at the 4 gate nodes in the job-creation graph for human
     approval of generated content (JD, competencies, WSI questions, final review).
  2. **Tool-level gates** (7): `send_email`, `send_whatsapp`, `bulk_communicate`,
     `reject_candidate`, `bulk_update_stage`, `publish_job`, `close_job` — each decorated
     with `@require_hitl` via the `hitl_preflight()` helper
     (`app/shared/hitl/agent_gate.py`). Guarded by the `LIA_HITL_GATE` feature flag
     (default OFF = zero regression in production). When the flag is ON, the gate emits
     an `approval_required` SSE event; the recruiter clicks Confirm; the frontend
     re-POSTs with `approve_pending_id=<uuid>`; the backend replays the tool call with
     the gate bypassed. Sentinel: `tests/contract/test_hitl_tool_gate.py`.

- **Audit logging** — `app/shared/compliance/audit_service.py` (+ writer/storage/
  decorators). `AuditService.log_decision[_in_session]` is mandatory on mutative
  public service methods in interview/offer domains (SOX 7-year). `main.py`
  registers the main event loop so sync LangGraph nodes can redispatch audit
  writes without poisoning the asyncpg pool.

- **AgentBus / CrewAI-style delegation** — `app/shared/agents/agent_bus.py` (+
  `libs/agents-core/lia_agents_core/agent_bus.py`) carries inter-agent messages;
  `crew_executor.py` / `crew_context.py` formalize multi-agent delegation. The
  orchestrator supervisor (`app/orchestrator/supervisor/handoff_tools.py`) issues
  handoffs across domains.

- **Per-tenant credit gating** — `llm_bootstrap` wraps every SDK message-creation
  primitive with `check_credit_budget`, reading `company_id` from the same
  ContextVar; defense-in-depth gates also live in the orchestrator and agentic
  loop.

---

## 8.1 Cross-cutting control coverage matrix

The §8 bullets describe each control in prose. This matrix answers the practical
question: *which controls touch ALL domains/agents vs. only some, how are they
enforced, and where are the gaps?* "Scope" = how broadly the control fires.
Status uses `OK` (covers its intended surface), `PARTIAL` (covered only on a
subset that should arguably be wider), `GAP` (a known hole, by design or debt).

| Control | Seam (file) | Scope | Enforcement | Status / gap |
|---|---|---|---|---|
| Tenant isolation | `shared/agents/tenant_aware_agent.py` + `_current_company_id` ContextVar | ALL 16 ReActAgents + every non-ReAct callsite | `TenantAwareAgentMixin`; `resolve_tenant_snippet_for_non_react` is the only non-ReAct seam; `LIA_AGENT_TENANT_STRICT` fail-closed in prod | OK |
| Compliance domain prompt | `domains/compliance_base.py` (`ComplianceDomainPrompt`) | ALL `@register_domain` domains | enforced at registration; escape `LIA_ALLOW_NON_COMPLIANT_DOMAINS` (emergency) | OK |
| FairnessGuard (L1 regex / L2 implicit-bias / L3 HR-sensitive) | `shared/compliance/fairness_guard.py` + `fairness_recursive.py` (nested payloads) + `fairness_guard_middleware.py` (FastAPI dep) | scoring / hiring-policy / screening writes + recruiter `save_*` tools | C3b pre-step (L3) + `scoring_safeguards.py` C1-C5 gate (LGPD Art.20 / EU AI Act) + recursive guard on agent payloads | OK (selective by design; depends on the protected-attributes registry loading) |
| Protected-attributes registry | `shared/compliance/protected_attributes.py` + `config/protected_attributes.yaml` | foundation for FairnessGuard + BiasAudit (`PROTECTED_ATTRIBUTE_IDS` / `PROTECTED_DB_FIELDS` / `BIAS_AUDIT_DIMENSIONS`) | loaded at startup; `is_registry_loaded()` sanity check | 🔴 **FIX** — OK, but FAIL-OPEN if the YAML is missing/empty (ADR-031 path bug made FairnessGuard run fail-open Mar-May 2026) |
| FactChecker (+ domain validators, LIA-C06) | `shared/compliance/fact_checker.py` + `compliance/domain_validators.py` + `shared/rag/realtime_fact_checker.py` | LLM output before it reaches the user | C3b post-step + RAG path | OK |
| BiasAuditService (FAR-5 disparate-impact / four-fifths) | `shared/services/bias_audit_service.py` (canonical, cross-domain) + `domains/interview_intelligence/services/bias_detector_service.py` (interview-specific) | periodic / annual bias audits over decisions across domains | `bias_audit_service` singleton; reads `BIAS_AUDIT_DIMENSIONS` from the registry | OK |
| Prompt-injection guard | `shared/compliance/prompt_injection_guard.py` (+ `shared/prompt_injection.py`) | recruiter/candidate text + LLM output | pre-tool screen | OK |
| Hate-speech guard | `shared/compliance/hate_speech_guard.py` | generated output | C3b step | OK |
| PII strip to LLM | `shared/pii_masking.py::strip_pii_for_llm_prompt` + `shared/llm_bootstrap.py` monkey-patch | ALL SDK calls (single chokepoint) | bootstrap wraps `.create`/`.stream`; ON by default | 🔴 **FIX** — PARTIAL: recruiter chat + some recruiter-facing tools run `mask_names=False`, so candidate NAMES still reach the LLM (see §8.2) |
| PII masking in logs | `shared/pii_masking.py::install_global_pii_masking` (`PIIMaskingFilter`) | root logger + all handlers + stack traces | installed at boot | OK |
| HITL gates + tool safety governance | `shared/hitl/agent_gate.py` + `hitl_decorator.@require_hitl` + `compliance/safety_category.py` (`SafetyCategory` enum) | wizard 4 gates + tools tagged in each registry's `GUARDRAIL_TOOLS` (destructive_write / bulk_action / pii_export / outreach / pipeline_move / offer) | LangGraph `interrupt()` + decorator | OK (selective by design) |
| Entity resolver (deterministic entity lookup) | `shared/entity_resolver.py` | ALL SSE turns (set per-turn before CascadedRouter fires) | fuzzy difflib + ≥2 significant-token overlap, scoped by `company_id`; hint injected into prompt | OK — fail-open: unresolved → hint empty, turn proceeds |
| Navigation route whitelist | `shared/navigation_routes.py` (`VALID_ROUTES` + `_DYNAMIC_PATTERNS` + `validate_navigate_route`) | every `ui_action: navigate_to` emitted by any agent | validated before emission; invalid path → None (caller falls back to dashboard) | OK — CI sensor |
| Audit logging | `shared/compliance/audit_service.py` (+ writer/storage/decorators) | mutative public service methods | mandatory + ratchet sentinel in `interview_scheduling`/`interview_intelligence`/`offer` + `company`; SOX 7-year on offer | PARTIAL: strictly enforced only on those domains; others are best-effort |
| Credit gating | `shared/llm_bootstrap.py::check_credit_budget` | ALL SDK message-creation primitives | bootstrap + orchestrator + agentic-loop (defense-in-depth) | OK |
| BYOK (chat / completion) | `shared/tenant_llm_context.py::get_gemini_client_for_tenant` / `get_claude_model_for_tenant` | Gemini / Claude / OpenAI chat | per-tenant `tenant_llm_configs.providers`; platform key only as fallback | OK |
| BYOK (embeddings) | `shared/providers/embedding_factory.py::_get_tenant_provider` | embedding generation | tenant-key branch exists only for `gemini` | 🔴 **FIX** — GAP: OpenAI embeddings and the semantic-routing cache always use the platform key (see §8.3) |
| Per-tenant custom guardrails | `shared/compliance/guardrail_repository.py` + `models/guardrail.py` | DB-backed per-domain / per-company agent guardrails | repository read at agent build; scoped by `is_active` / `domain` / `company_id` | OK |
| C3b layer (kill-switch) | `shared/compliance/c3b_layer.py` | realtime chat (WS/SSE) | wraps pre/post compliance; `LIA_DISABLE_C3B` kill-switch | OK |

Reading the matrix: tenant isolation, compliance-domain-prompt, prompt-injection,
PII-in-logs, and credit gating are the truly *universal* controls (they fire for
every agent/domain). FairnessGuard, BiasAudit, HITL, and strict Audit are
*selective by design* (only the decisions that need them). The
protected-attributes registry is *foundational*: FairnessGuard and BiasAudit both
read it, so if `config/protected_attributes.yaml` fails to load they silently run
fail-open (this already happened, ADR-031), which makes registry-load monitoring
part of the compliance surface rather than an afterthought.

The realtime chat pipeline (`c3b_layer.py`) runs these guards in a fixed order:
HateSpeechGuard, then PII strip, then PromptInjectionGuard, then FairnessGuard L3
(pre-step); FactChecker plus AuditService (post-step). Each guard is wrapped in
its own try/except and logs a skip warning if it cannot validate, so a single
guard failure degrades gracefully instead of taking the turn down.

Known holes to watch: (1) the PII name-leak on recruiter-facing paths (§8.2),
(2) the embedding BYOK gap (§8.3), and (3) the fail-open behavior of the
protected-attributes registry above. Everything else marked `OK` covers its
intended surface; the `PARTIAL` rows (PII-to-LLM, strict Audit) are correct but
narrower than a maximalist reading would want.

### 8.1.1 Coverage grid - controls x the 16 canonical agents

The table above is the per-control reference (seam / enforcement / status). This
grid is the per-cell view (which control actually fires on which agent), in the
"transversal bands" style. Columns are the 16 canonical ReActAgents from §3, in
the same order; the legend maps the short codes. The point this grid makes: most
controls are `OK` on every agent not because each domain re-implements them, but
because every ReActAgent inherits them from `LangGraphReActBase` +
`TenantAwareAgentMixin` + `ComplianceDomainPrompt` + the `llm_bootstrap`
chokepoint. Individual modules implement few of these on their own; the agent
layer unifies the whole band.

Legend: `✓` enforced · `⚠` enforced but with a documented gap · `○` not
applicable / does not fire by design.
Columns: `Anlt`=Analytics, `ATS`=ATSIntegration, `Auto`=Automation,
`Anon`=Autonomous, `Comm`=Communication, `Cfg`=CompanySettings,
`CVSc`=Pipeline/cv_screening, `Pol`=Policy/hiring_policy, `JobM`=JobsManagement,
`Kanb`=Kanban, `Funl`=TalentFunnel, `Src`=Sourcing, `Pool`=TalentPool,
`Wiz`=Wizard, `CSS`=CandidateSelfService, `PTr`=PipelineTransition.

| Control | Anlt | ATS | Auto | Anon | Comm | Cfg | CVSc | Pol | JobM | Kanb | Funl | Src | Pool | Wiz | CSS | PTr |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Tenant isolation | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Compliance domain prompt | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FairnessGuard (L1/L2; L3 high-impact) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Protected-attrs registry [a] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FactChecker | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Prompt-injection guard | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Hate-speech guard [b] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PII strip to LLM [c] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PII masking in logs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HITL + tool safety [d] | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ○ | ✓ |
| Audit logging [e] | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ○ | ✓ |
| BiasAudit [f] (periodic) | ○ | ○ | ○ | ○ | ○ | ○ | ✓ | ✓ | ○ | ○ | ✓ | ✓ | ✓ | ✓ | ○ | ○ |
| Credit gating | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BYOK (chat / completion) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BYOK (embeddings) [g] | ○ | ○ | ○ | ○ | ⚠ | ○ | ⚠ | ○ | ⚠ | ⚠ | ⚠ | ⚠ | ○ | ⚠ | ○ | ○ |
| Per-tenant custom guardrails | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| C3b layer [b] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Footnotes:

- **[a]** Foundational config (`config/protected_attributes.yaml`). Shown `✓`
  everywhere because every agent inherits FairnessGuard, which reads it. If the
  YAML fails to load, FairnessGuard and BiasAudit run FAIL-OPEN (ADR-031), so the
  whole column is only as strong as registry-load monitoring.
- **[b]** Hate-speech and the C3b wrapper fire on realtime chat turns
  (`c3b_layer.py`). Background / proactive invocations that skip the chat pipeline
  (e.g. Automation or Autonomous running headless) are covered only by the
  bootstrap-level controls, not by C3b.
- **[c]** Enforced for every agent at the `llm_bootstrap` chokepoint, BUT recruiter
  chat strips with `mask_names=False`, so candidate NAMES still reach the LLM on
  recruiter-facing turns (§8.2). The cell stays `✓` because identifiers
  (CPF/email/phone) are always stripped; the name gap is the row-level caveat.
- **[d]** `✓` where the agent's tool registry declares `GUARDRAIL_TOOLS` /
  `@require_hitl`, plus the Wizard's 4 `interrupt()` gates. `○` = the agent has no
  state-changing tool that needs a human gate.
- **[e]** Best-effort `log_decision` across these agents. The mandatory,
  sentinel-enforced ratchet (SOX 7-year) lives in the `interview_scheduling` /
  `interview_intelligence` / `offer` services, which are not routable ReActAgents,
  so they do not appear as columns. `Cfg` is `○` because `company_settings`
  persists through `save_company_*` without a direct `log_decision` call.
- **[f]** BiasAudit runs periodically / annually over stored decisions (FAR-5
  disparate impact / four-fifths). `✓` marks the agents whose scoring or ranking
  decisions feed those audits, not a per-turn check.
- **[g]** `⚠` = the agent generates embeddings, which use the platform key, not
  the tenant key (§8.3). `○` = the agent does not embed.

Coverage read: 13 of the 17 rows are universal (`✓` on all 16 agents, purely by
inheritance). The 4 scoped rows are HITL/tool-safety and Audit (fire where an
action warrants), BiasAudit (periodic, over decision-producing agents), and BYOK
embeddings (the one true gap: platform key on every agent that embeds).

---

## 8.2 PII data-flow map

PII enters from candidate and recruiter input, is minimized at well-defined seams
before any external boundary, and exits only as masked text. The canonical engine
is `app/shared/pii_masking.py`:

- `mask_pii(text)` -> log redaction (`***CPF***`, `***EMAIL***`, ...), with a
  UUID-v4 guard so tenant/job IDs are not eaten by the phone regex.
- `strip_pii_for_llm_prompt(text, mask_names=True)` -> data-minimization before
  LLM/embedding calls (LGPD Art. 12). Layers: (0) UUID guard, (1) direct
  identifiers CPF/email/phone/RG/CNPJ via regex, (3) quasi-identifiers
  (graduation year, explicit age, address) via regex, (4) Presidio NER for
  names (PERSON) and NRP (nationality/religion/politics).

Defaults (all verified in code): `LLM_PROMPT_PII_STRIPPING_ENABLED=true`,
`LLM_PROMPT_PRESIDIO_ENABLED=true`, `LLM_PROMPT_PRESIDIO_LANG=pt`
(spaCy `pt_core_news_sm`), `LLM_PROMPT_PRESIDIO_ENTITIES=PERSON,EMAIL_ADDRESS,PHONE_NUMBER,NRP`.
If Presidio fails to load, `strip_pii_for_llm_prompt` logs a CRITICAL because
names would then leak unmasked.

```
PII ENTRY                       MINIMIZATION SEAM                              PII SINK / BOUNDARY
---------                       -----------------                              -------------------
CV / resume (pdf, docx) --+
voice transcript ---------+
candidate chat -----------+--> c3b_layer.pre_compliance --> strip_pii_for_llm_prompt --+
recruiter chat / notes ---+        (recruiter: mask_names=False  <-- NAME LEAK)         |
ATS inbound notes --------+                                                             v
                                                       defense-in-depth (independent):  LLM SDK
                                            llm_bootstrap monkey-patch on every  -------> (Anthropic /
                                            .create / .stream call (chokepoint)          OpenAI / genai)

embedding text -----------> embedding_service.generate_* --> strip_pii_for_llm_prompt --> vector DB +
                                            (mask_names forwarded)                        embedding cache

any log / exception ------> install_global_pii_masking (PIIMaskingFilter) --------------> logs / Sentry /
                                                                                          stack traces

ATS outbound fields ------> ats_pii_filter.filter_outbound (consent gate: ats_sharing) -> external ATS
```

🔴 **FIX — Residual name-leak gap (the one to flag):** `c3b_layer.pre_compliance` calls
`strip_pii_for_llm_prompt(message, mask_names=False)` for recruiter chat (both
the chat-page and `agent_chat_ws` callers), on the rationale that recruiters are
authorized to see candidate names and NER was producing false positives on job
titles. Net effect: structured identifiers (CPF/email/phone) are still stripped,
but candidate NAMES on recruiter-facing prompts reach the LLM. `mask_names=True`
remains the default everywhere else (embeddings, candidate-facing paths). The
opt-in `LIA_RECRUITER_CHAT_MASK_PII` re-enables name masking for the recruiter UI.

---

## 8.3 Embeddings: which feature embeds what, with which provider, and is it BYOK?

Per-tenant LLM config (BYOK) lives in the `tenant_llm_configs` table, resolved by
`app/shared/tenant_llm_context.py` (`get_tenant_llm_config`, in-memory
`_tenant_configs` cache, keyed off the `_current_company_id` ContextVar). That
config drives **chat / completion** calls (Gemini / Claude / OpenAI), which DO
honor BYOK. **Embeddings are a separate path** and are the subject of this
section, because in practice they behave very differently from chat.

### How an embedding call resolves its provider and key

Three independent things decide what any embedding call does:

1. **Default provider + fallback.** `EMBEDDING_DEFAULT_PROVIDER` (code default
   `gemini`) picks the first provider; `EMBEDDING_FALLBACK_ORDER = ["gemini",
   "openai"]` is tried if the first fails. The design note in
   `app/shared/providers/embedding_openai.py` intends OpenAI
   `text-embedding-3-small` as the primary for the routing cache and RAG, so a
   deployment can set `EMBEDDING_DEFAULT_PROVIDER=openai`.
2. **Which entry function the caller uses** (this is what controls BYOK
   eligibility, in `app/shared/providers/embedding_factory.py` and
   `app/shared/intelligence/embedding_service.py`):
   * `EmbeddingProviderFactory.embed_with_fallback(text, preferred_provider, company_id)`:
     accepts `company_id` and has fallback. BYOK-eligible ONLY if the caller
     actually passes `company_id`.
   * `EmbeddingProviderFactory.get_default()`: no `company_id`, no fallback.
     Never BYOK.
   * `EmbeddingService.generate_embedding(text, provider=None, *, mask_names=False)`:
     has fallback and optional PII name masking, but **no `company_id` parameter
     at all**. Never BYOK.
3. **The tenant-key branch.** `EmbeddingProviderFactory._get_tenant_provider`
   swaps in a tenant key ONLY when the provider is `gemini` AND `company_id` is
   passed AND the tenant has a Gemini key configured. The OpenAI provider always
   uses the platform key (`AI_INTEGRATIONS_OPENAI_API_KEY` or `OPENAI_API_KEY`).

### Feature map (every call site that actually generates embeddings)

| Product feature | File :: entry function | Provider (resolved) | Dims | company_id passed? | BYOK |
|---|---|---|---|---|---|
| **Chat router semantic cache** (CascadedRouter Tier 3; caches intent routing in table `routing_cache_vectors`) | `orchestrator/memory/vector_semantic_cache.py` :: `_generate_embedding` -> `embed_with_fallback(text)` | default + fallback (design: OpenAI primary) | 768 (see note) | No | **No** |
| **RAG hybrid search** (BM25 + pgvector; the SQL queries are tenant-scoped, the embedding call is not) | `domains/ai/services/rag_pipeline_service.py` :: `generate_embedding` -> `embed_with_fallback(text)` | default + fallback | 768 | No | **No** |
| **In-memory RAG ranking** (RRF over a loaded doc set) | `shared/rag/hybrid_search.py` :: `_semantic_search` -> `get_default()` | default only | 768 | No | **No** |
| **JD similarity** ("similar past jobs" suggested in the job-creation wizard) | `domains/job_creation/services/jd_similar_service.py` :: `find_similar` / `record_jd` -> `EmbeddingService.generate_embedding(text)` | default + fallback | 1536 required (see note) | No | **No** |
| **Rejected-candidate re-discovery** (CV screening Gate 2) | `domains/cv_screening/tools/candidate_tools.py` :: `_generate_rediscovery_embedding` -> `JobEmbeddingService.create_or_update_job_embedding` -> `generate_job_embedding` -> `embedding_service.generate_embedding(text)` | default + fallback | 768 | No (`company_id` only scopes the stored row, not the embedding key) | **No** |
| **Recruiter assistant memory + company knowledge base** | `domains/recruiter_assistant/services/memory_service.py` :: `store_message` / `add_to_knowledge_base` / `search` -> `embedding_service.generate_embedding(text, mask_names=True)` | default + fallback (PII names masked) | 768 | No | **No** |
| **Skills ontology proximity** (Talent Intelligence skills matching) | `domains/talent_intelligence/services/skills_ontology_engine.py` :: `_load_embeddings` -> `get_default()` | default only | 768 | No | **No** |
| **Voice screening + interview transcription** | (none) | n/a | n/a | n/a | **No embeddings**: STT/TTS only, via Gemini Live Audio and Deepgram (Whisper/TTS as PSTN fallback) |

Provider / model reference: Gemini `text-embedding-004` (768 dims); OpenAI
`text-embedding-3-small` (768 dims by default to match the shared `Vector(768)`
columns, 1536 dims only when a caller explicitly instantiates the provider with
`output_dimensions=1536`). **Note on the routing cache:** its module comments
mention 1536 as OpenAI's native size, but it resolves the OpenAI provider through
the factory default and never overrides `output_dimensions`, so it actually
stores 768-dim vectors for both providers.

**Note on JD similarity:** its table `jd_similar_history` is `Vector(1536)` and
the service rejects any vector whose length is not 1536 (Gemini 768 is explicitly
unsupported), failing open. Because the shared `EmbeddingService` defaults to 768
via the same factory, this feature only returns matches when the embedding
actually comes back at 1536 (OpenAI `text-embedding-3-small` native size); on any
other length it fails open and returns no suggestions.

🔴 **The real state today: embeddings run on the platform key, never the tenant
key.** None of the production call sites above pass `company_id`, and
`EmbeddingService.generate_embedding` (the path most features use) cannot accept
one. The Gemini tenant-key branch in `_get_tenant_provider` is therefore never
reached from these features, so **every embedding uses a platform key regardless
of provider**. Tenant isolation on these surfaces comes from the SQL / pgvector
queries being scoped by `company_id`, not from the embedding key. Chat /
completion still honors BYOK; only the embedding layer is platform-pinned.

**Why the routing cache must stay platform-pinned anyway:** its vectors live in a
*shared* table at one fixed dimension (768 via the factory default, for either
provider). Letting tenants swap embedding provider or model would risk mixing
vector dimensions in one cache and corrupt similarity lookups, so a single
platform embedding key is required there even if BYOK threading were added to the
other features.

---

## 9. FastAPI ↔ Rails boundary (one-line note)

`lia-agent-system` (this AI layer, the production backend) accepts both locally
signed JWTs and Rails JWTs from `ats_api` (the legacy Ruby-on-Rails
system-of-record); the cross-service trust contract is documented in
`docs/architecture/RAILS_BOUNDARY.md`. The Rails service is out of scope for this
AI-layer tree.

---

## 10. Domain & agent glossary

§3 lists *where* each agent lives and §4 lists the domain tree. This section adds
the *what it does / when it fires* dimension. Source of truth for the domain
classification is `app/domains/DOMAIN_CATALOG.md`; the inventory of the 16
canonical ReActAgents is `tests/integration/agents/test_tenant_aware_rollout_t_d.py`.

### 10.1 The 16 canonical ReActAgents (what each does)

| Agent | Domain | What it does / when it fires |
|---|---|---|
| `AnalyticsReActAgent` | analytics | Recruitment analytics, reports, dashboards, KPIs. Narrates metrics and trends in chat. |
| `ATSIntegrationReActAgent` | ats_integration | Connects and syncs jobs/candidates with external ATS (Gupy, Pandape, Merge). |
| `AutomationReActAgent` | automation | Tasks, reminders, notes, lightweight workflow automation. |
| `AutonomousReActAgent` | autonomous (legacy) | Cross-domain ReAct fallback. Historically the router "Tier 6" fallback; see §12 for its disputed current status. |
| `CommunicationReActAgent` | communication | Composes and sends email / WhatsApp / Teams, progress reports, daily briefings. |
| `CompanySettingsReActAgent` | company_settings | Conversational company configuration (profile, benefits, workforce plan, culture) with prefill tags and FairnessGuard on every save. |
| `PipelineReActAgent` | cv_screening | CV analysis, WSI scoring, candidate screening and ranking. |
| `PolicyReActAgent` | hiring_policy | Hiring-policy advisory with FairnessGuard and diversity rules. |
| `JobsManagementReActAgent` | recruiter_assistant | Job CRUD, pipeline configuration, job queries. |
| `KanbanReActAgent` | recruiter_assistant | Kanban / pipeline board operations and candidate-movement insights. |
| `TalentFunnelReActAgent` | recruiter_assistant | The canonical Talent Funnel: multi-mode candidate search across 3 sources. |
| `SourcingReActAgent` | sourcing | Candidate sourcing across channels; parent of the search / enrich / diversity / github / nurture / passive / referral sub-agents. |
| `TalentPoolReActAgent` | talent_pool | Talent-pool management (list, add candidate, move pool to job). |
| `WizardReActAgent` | job_management | Drives the HITL job-creation wizard (15 nodes, 4 `interrupt()` gates). |
| `CandidateSelfServiceAgent` | candidate_self_service | Candidate-facing self-service (public screening chat, application status). |
| `PipelineTransitionAgent` | pipeline | Validates and executes candidate stage transitions. |

Note: the 16 ReActAgents are NOT the same set as the 16 `@register_domain`
domains. Some agents live in domains that are classified as service or legacy
(e.g. `company_settings`, `candidate_self_service`, `autonomous`), and some
`@register_domain` domains (e.g. `digital_twin`, `recruitment_campaign`) have no
routable ReActAgent. See §14 for why this matters.

### 10.2 Domains by class (one-line purpose)

**Agentic (13, `@register_domain`, router-routable):** `analytics` (reports,
dashboards) · `ats_integration` (external ATS sync) · `automation` (tasks /
reminders / notes) · `communication` (email / WhatsApp / Teams) · `cv_screening`
(CV analysis + WSI scoring) · `hiring_policy` (policy advisory + FairnessGuard) ·
`interview_scheduling` (scheduling + calendar) · `job_creation` (the wizard graph)
· `job_management` (job lifecycle + WizardReActAgent) · `pipeline` (stage
transitions) · `recruiter_assistant` (general copilot + fallback) · `sourcing`
(candidate sourcing) · `agent_studio` (custom-agent creation, see §13).

**Micro-action (3, lightweight `@register_domain`):** `digital_twin` (candidate
digital-twin creation/eval) · `recruitment_campaign` (multi-stage campaigns) ·
`talent_pool` (pool management).

**Service (11, business logic, not router-routable):** `ai` (LLM services,
response cache, prompt mgmt) · `billing` · `candidates` (candidate CRUD) ·
`company` (company config) · `credits` (token consumption) · `integrations_hub`
(third-party integration mgmt) · `interview_intelligence` (bias detection,
comparative analysis; promotion candidate) · `lgpd` (data-protection compliance) ·
`modules` (feature gating) · `recruitment` (process data) · `voice` (voice
screening; promotion candidate). Also AI-relevant: `persona` (AI persona
personalization), `talent_intelligence` (skills ontology, internal mobility,
workforce planning), `offer` (offer mgmt with SOX audit), `candidate_self_service`,
`company_settings`.

🟡 **Repository-stub (30):** pure CRUD (`__init__.py` + `dependencies.py` +
`repositories/` only). Consumed by agentic domains and routes; not agents. Full
list in `DOMAIN_CATALOG.md`.

🟡 **Canonical-active legacy (2):** `autonomous` (ReAct fallback) and `policy` (the
real `PolicyEngineService` + `PolicySetupAgent` + sector FairnessGuard rules).
Production code in the pre-refactor location; `hiring_policy` does NOT replace
`policy`.

---

## 11. Capability catalog

What the platform can actually *do*, grounded in the implementing code. Business
actions are reached either through the deterministic `action_handlers` (Phase 1 of
the orchestrator) or through a domain agent's tools (Phase 2); state-changing ones
pass an HITL confirmation.

### 11.1 Business / recruiting actions

| Capability | Implemented in | HITL |
|---|---|---|
| Generate report / daily briefing | `orchestrator/action_handlers/analytics_actions.py`, `communication_actions.py` (`_send_progress_report`, `_generate_daily_briefing`) + analytics domain tools | no |
| Compare candidates | `orchestrator/action_handlers/sourcing_actions.py` (`_compare_candidates`) | no |
| Move candidate across stages | `orchestrator/action_handlers/candidate_actions.py` (`_move_candidate`, `_batch_move_candidates`) + `PipelineTransitionAgent` | yes |
| Schedule / reschedule interview | `orchestrator/action_handlers/interview_actions.py`, `communication_actions.py` | yes |
| Send communication (email / WhatsApp) | `orchestrator/action_handlers/communication_actions.py` (`_send_email`, `_send_whatsapp`) | yes |
| Source / search candidates | `orchestrator/action_handlers/sourcing_actions.py` (`_search_candidates`), `domains/sourcing/tools/query_tools.py` | no |
| Screen CV / WSI score | `orchestrator/action_handlers/candidate_actions.py` (`_start_screening`), `domains/cv_screening/services/wsi_service/` | no |
| Create job (wizard) | `domains/job_management/tools/job_wizard_tools.py`, `domains/job_creation/graph.py` | yes (4 gates) |
| Publish job / sync to ATS | `domains/ats_integration/services/`, `domains/job_creation/nodes/publish.py` | yes |
| Manage offers | `domains/offer/tools/`, `domains/offer/services/` (SOX audit) | yes |
| Talent-pool operations | `domains/talent_pool/agents/talent_pool_tool_registry.py` (list / add / move pool to job) | move = yes |

> Creation of a job is ALWAYS and ONLY the canonical wizard; Plan & Execute never
> creates a job (see `replit.md` Plan & Execute section).

### 11.2 AI / platform capabilities

| Capability | Lives in | Status |
|---|---|---|
| Learning Loop / feedback | `app/shared/learning/` (`learning_loop_service`, `feedback_writer`, `implicit_feedback_service`, `correction_capture`, `ab_testing_service`, `learning_golden_curation_service`, `learning_snapshot_service`, `template_learning_service`, `finetuning_export`) | active |
| Personalization / persona | `app/domains/persona/services/` (AI persona) | active |
| Plan & Execute | `app/shared/execution/` (`plan_detector`, `plan_executor`), `app/orchestrator/execution/task_planner.py`, `app/orchestrator/services/plan_orchestration_service.py` | built, OFF in prod (`LIA_V2_USE_PLAN_SERVICE`, canary) |
| ML / predictive | `app/services/ml/` (`outcome_predictor`, `model_registry`, `feature_engineering`) | active |
| RAG / retrieval | `app/shared/rag/` (`hybrid_search`, `reranker`, `realtime_fact_checker`, `response_watermarker`), `app/shared/intelligence/semantic_search_service.py` + `chunking/recursive` (RecursiveTextSplitter), `app/domains/ai/services/hybrid_search_service.py` | active |
| Semantic routing cache | `app/orchestrator/routing/` (`cascaded_router` tiers 0-5: LRU, Redis, pgvector, FastRouter, LLM cascade) | active |
| Voice analysis | `app/domains/voice/services/voice_screening_orchestrator.py` (Gemini Live + Twilio PSTN fallback) | active, per-agent flag |
| Rich Response Protocol (RRP) | `app/shared/rrp_blocks.py` (6 typed block kinds) + `app/shared/rrp_ranking_builder.py` (canonical producer) + `app/shared/rrp_block_sink.py` (ContextVar tee for agentic path) | active |
| Anti-sycophancy | `app/shared/prompts/` anti-sycophancy block (`ANTI_SYCOPHANCY_ORCHESTRATOR` / `ANTI_SYCOPHANCY_OPERATIONAL`) injected into prompts | active |
| Calibration | `domains/cv_screening/services/calibration_profiles`, `domains/job_creation` calibration node | active |

---

## 12. Federated vs Supervisor orchestration (what is ON / OFF)

The `MainOrchestrator` (`app/orchestrator/execution/main_orchestrator.py`) runs a
multi-phase pipeline. Two macro-strategies coexist: the **federated** path (live)
and the **supervisor / plan** path (built but mostly OFF in production). This is
the "agente federado ligado, supervisor desligado" state.

```
request
  │
  ├─ Phase 0  PendingAction        (resume a previous action / collect params)
  ├─ Phase 1  ActionExecutor       (deterministic intent -> action_handlers; LLM narrates result)
  ├─ Phase 1.3 Plan & Execute      (multi-step plan)         [SUPERVISOR — OFF in prod]
  └─ Phase 2  Federated routing    (CascadedRouter -> domain specialist ReAct agent)  [LIVE]
```

### 12.1 Federated path (ENABLED, primary)

A request is mapped to ONE domain specialist by the `CascadedRouter`
(`app/orchestrator/routing/cascaded_router.py`), an 8-tier funnel from cheap to
expensive:

```
Tier 0  MemoryResolver + EntityResolver   pronoun / context-reference resolution
                                              + deterministic DB entity lookup (vacancy/candidate
                                              name → UUID; fuzzy difflib + token overlap ≥2;
                                              result injected as hint via ContextVar
                                              _active_vacancy_id / _active_candidate_id; fail-open)
Tier 1  LRU in-process        MD5 hash, O(1), per company_id
Tier 2  Redis hash cache      distributed exact match across workers
Tier 3  VectorSemanticCache   pgvector cosine >= 0.85   (ROUTER_VECTOR_CACHE_ENABLED)
Tier 4  FastRouter            regex / keyword patterns
Tier 5  LLM Cascade           Haiku -> Sonnet -> Opus   (expensive, last resort)
Tier 6  REMOVED (Sprint 12.3-B)  was the AutonomousReActAgent cross-domain fallback
```

The matched domain loads its specialist agent (one of the 16 ReActAgents) and runs
the ReAct loop. This is the default conversational path for single-domain
requests and it is what is live today.

> **Multi-turn correctness (P0 fix, 2026-06-06).** LangGraphBase uses a stable
> `thread_id = f"{session_id}::{domain}"` + PostgreSQL checkpointer so state persists
> across turns. `_messages_for_continuation` in
> `libs/agents-core/lia_agents_core/langgraph_base.py` strips the System message from
> the *input* of continuation turns (turn 2+), because `add_messages` appends to the
> checkpointed state and Anthropic rejects `[System, Human, AI, System, Human]` sequences.
> This is the canonical LangGraph multi-turn pattern.
> Sentinel: `tests/unit/test_langgraph_base_system_dedup.py`.

### 12.2 Supervisor / Plan path (mostly OFF)

Two distinct "supervisor" implementations exist:

- **Plan & Execute (Phase 1.3)** decomposes multi-step requests (e.g. "publish the
  job and find 5 candidates") into a plan executed across domains. Components:
  `plan_detector` + `plan_executor` (`app/shared/execution/`), `task_planner`,
  `plan_orchestration_service`. **Default OFF in prod** (`LIA_V2_USE_PLAN_SERVICE`,
  canary rollout, ON only where explicitly enabled). It NEVER creates a job.
- **Wizard supervisor classifier** is a pre-graph 6-intent classifier specific to
  the job-creation wizard (`LIA_WIZARD_SUPERVISOR_CLASSIFIER`). **ON in dev/test,
  OFF in prod.**

> 🔴 **FIX** — Open inconsistency to reconcile: the router header marks Tier 6 (the autonomous
> cross-domain fallback) as REMOVED in Sprint 12.3-B "env never set in prod", while
> `DOMAIN_CATALOG.md` still documents `autonomous` as the live Tier 6 fallback. The
> two disagree; the catalog entry is likely stale and should be updated to match
> the router.

### 12.3 The 3-way orchestration switch (and where `autonomous` fits)

The three orchestration strategies above are **not** layered on top of each other
at runtime — they are a **mutually-exclusive 3-way switch**, selected per request
by feature flags in the SSE handler (`app/api/v1/agent_chat_sse.py`, ~L650-666):

```
if LIA_BUBBLE_VIA_SUPERVISOR:          # Supervisor / MainOrchestrator (handoff)
    agent = None                        #   → orchestrator routes everything
elif LIA_FEDERATED_PRIMARY:            # Federated single agent (recruiter_copilot)
    agent = _get_agent("recruiter_copilot")
else:                                   # CascadedRouter → domain specialist  [LIVE TODAY]
    agent = _get_agent(resolved_domain)
```

| Strategy | Flag | Status (2026-06-08) | Cross-domain mechanism |
|---|---|---|---|
| **CascadedRouter → domain** | (default) | ✅ **LIVE** in dev + prod | one specialist per turn; no cross-domain in a single turn |
| **Federated** (`RecruiterCopilotReActAgent`) | `LIA_FEDERATED_PRIMARY` (+ `LIA_FEDERATED_SCOPED_TOOLS`) | 🟡 dormant — parity measurement | ONE agent, federated toolset, **dynamic tool scoping** per turn |
| **Supervisor** (`MainOrchestrator`) | `LIA_BUBBLE_VIA_SUPERVISOR` | 🟡 dormant — parity measurement | explicit **handoff** to N domain sub-agents, composed into one voice |

> **Não confundir os dois "autonomous".** Há dois símbolos com esse nome:
> 1. **`AutonomousAgentService`** (`app/domains/automation/services/`) — serviço de
>    **background jobs + proactive actions** (`create_job`, `create_proactive_action`,
>    `check_and_execute_scheduled_jobs`), consumido por `proactive_actions.py`. **Vivo,
>    não-redundante, fora deste debate.** É o motor dos alertas proativos (§18).
> 2. **`AutonomousReActAgent`** (`app/domains/autonomous/agents/`, 515 LOC + 1705 LOC de
>    tool registry / 41 tools) — agente ReAct **cross-domain**. Era o **Tier 6** do
>    CascadedRouter. É *este* que está em discussão abaixo.

**O papel do `AutonomousReActAgent` nesta arquitetura: legado redundante.**

- Era o **Tier 6** (fallback cross-domain do CascadedRouter), **removido do hot path
  no Sprint 12.3-B**. A env que o ligava (`AUTONOMOUS_REACT_ENABLED`) **nunca foi
  setada em prod** — invocações em canary = 0. Ou seja, **nunca teve tráfego real**.
- Seu papel cross-domain (um único ReAct com todas as tools) é **funcionalmente
  substituído pelo Federado**, que é a versão moderna do mesmo conceito — porém com
  **escopo dinâmico de tools** (resolve o problema das "41 tools sempre carregadas"
  do autonomous) e governança herdada via `TenantAwareAgentMixin` / `GovernanceToolNode`.
- O **Supervisor** resolve cross-domain por uma filosofia diferente (handoff explícito
  a especialistas), também cobrindo o caso de uso.
- Hoje o `AutonomousReActAgent` só é alcançável por: (a) `orchestrator/legacy/orchestrator.py`
  (orquestrador legado, fora do caminho SSE/WS atual) e (b) `delegate_to_autonomous`
  do supervisor — que está com a **descrição desalinhada** (ver 🔴 abaixo). O import em
  `agent_chat_ws.py:419` é apenas *registration trigger* (`# noqa: F401`), não invocação.

> 🔴 **FIX — descrição de handoff desalinhada.** Em
> `app/orchestrator/supervisor/handoff_tools.py:54`, o domínio `"autonomous"` é descrito
> como *"listar, confirmar ou rejeitar ações pendentes"* (semântica de
> `AutonomousAgentService` / proactive actions), mas `delegate_to_autonomous` resolve via
> `AgentRegistry().get_instance("autonomous")` → o **`AutonomousReActAgent`** (ReAct
> cross-domain). Se o supervisor for ativado, ele pode delegar "ações pendentes" a um
> agente que faz outra coisa. Remover essa entrada do mapa de handoff fecha o gap.

**Recomendação (2 etapas, alinhada ao cleanup Sprint 12.6 já planejado):**
1. **Imediato, baixo risco:** remover a entrada `"autonomous"` de `handoff_tools.py`
   (corrige a descrição desalinhada) e a delegação em `app/tools/categories.py`.
2. **Sprint de cleanup:** antes de deletar os ~2.2k LOC, **portar 3 tools agregadoras
   cross-domain** que têm lógica de consolidação não-trivial — `candidate_360_view`,
   `cross_domain_funnel_analysis`, `get_tenant_hiring_overview` — para o
   `recruiter_copilot_tool_registry` (federado), para o federado ganhar essas views
   consolidadas em uma chamada. As outras ~38 tools são wrappers que delegam aos
   registries canônicos (já existem na origem) — zero perda. Depois deletar o agente,
   o import-trigger em `agent_chat_ws.py:419`, os contadores zerados
   (`autonomous_hits`/`autonomous_hit_rate`) e o branch dead em `legacy/orchestrator.py`.

> **Não há "planejamento multi-step autônomo" exclusivo a preservar:** o loop ReAct
> multi-step vem da base class compartilhada (`LangGraphReActBase` / `create_react_agent`),
> que o Federado herda igual. A única coisa com valor próprio são as 3 tools agregadoras
> acima.

---

## 13. Agent Studio (custom agents)

`agent_studio` lets a tenant create its own agents without code. It is one of the
more mature domains: model, runtime, API, marketplace, and safety controls are all
present.

- **Model** (`libs/models/lia_models/custom_agent.py`): `CustomAgent` with
  `name`, `role`, `description`, `system_prompt`, `allowed_tools[]`,
  `excluded_tools[]`, `domain` / `category`, `status` (draft / active / paused /
  archived), `version`, `max_steps` (default 8), `temperature`, `model_override`,
  `enable_memory`, `context_level`, channel flags (`voice_enabled`, `voip_enabled`,
  `whatsapp_enabled`, `triagem_invite_enabled`), sourcing-only payloads
  (`search_strategy` / `preferences` / `outreach_config`), and runtime metrics
  (`total_executions`, `avg_confidence`). Tenant-scoped (`company_id`, FK ON DELETE
  CASCADE for LGPD erasure).
- **Creatable categories** (`category`, source of truth): `screening`, `sourcing`,
  `communication`, `analytics`, `automation`, `job_management` (plus `general`
  default). Sourcing agents have their own quota bucket.
- **Runtime** (`app/domains/agent_studio/custom_agent_runtime.py`):
  `CustomAgentRuntime` extends `LangGraphReActBase`, so a custom agent inherits the
  same compliance / tenant band as a built-in agent (§8.1). `context_level` chooses
  how much context is composed into the prompt: `full` (persona + domain + tenant +
  user + history + few-shot + intelligence_floor + custom), `standard` (no history,
  no few-shot), `minimal` (intelligence_floor + custom instructions only).
- **Safety controls**: a `_RESTRICTED_TOOLS` denylist removes dangerous tools;
  write tools require `confirm=True` and pass the canonical HITL gate (AUD-4 audit);
  a `dry_run` sandbox runs the real reasoning but intercepts side effects and
  returns "would do" actions; `FairnessGuard` validates the prompt on create /
  update; `intelligence_floor.yaml` is injected into every custom prompt as a
  quality / safety floor; `_CURRENT_COMPANY_ID` ContextVar enforces tenant
  isolation on every tool call; `studio_audit` logs creation / update / test /
  execution.
- **Marketplace** (`app/services/agent_marketplace_service.py`,
  `app/api/v1/custom_agents.py`): `AgentMarketplaceListing` (pending_review ->
  approved / rejected / unpublished) with a review workflow, `AgentInstallation`
  tracks cross-tenant installs, and `PoolAgentAssignment` binds an agent to a
  talent pool.

Verdict: well-structured and safe to represent as a first-class part of the AI
layer. 🔵 **NOTE** — the main remaining work is shifting some advanced filter logic from the
service layer down into `CustomAgentRepository`; the core lifecycle, runtime, and
guardrails are solid.

---

## 14. Enterprise-architecture diagnosis

Honest assessment against an enterprise checklist, grounded in the code audited
above. Verdict: the *agent layer* is enterprise-grade; the *domain layer* is
enterprise-grade at its core but still in transition at the edges.

### 14.1 Where it is enterprise-grade

- **Multi-tenancy**: `TenantAwareAgentMixin` on all 16 ReActAgents (sentinel-
  enforced), `CompanyId` value object, PostgreSQL RLS, tenant-scoped repositories.
- **Compliance**: 3-pillar (LGPD + SOX + EU AI Act), FairnessGuard (3 forms +
  L1/L2/L3), FactChecker, BiasAudit, protected-attributes registry, mandatory
  audit ratchet on interview / offer with SOX 7-year retention (§8.1).
- **Safety by inheritance**: 13 of 17 cross-cutting controls fire on every agent
  purely through the shared base classes and the `llm_bootstrap` chokepoint
  (§8.1.1) - including custom Studio agents.
- **Cost / observability**: per-tenant credit gating on every SDK call, external
  cost ledger, structured logging with PII masking, Sentry, health endpoints,
  canary monitoring of bypass flags.
- **Routing efficiency**: 6-tier cache-first router (memory / LRU / Redis / pgvector
  / regex / LLM cascade) keeps the expensive LLM tier as a last resort.
- **Testing discipline**: offline sentinels, AST validators, eval gates, and
  baselines guard the critical contracts (the `replit.md` contracts section is
  itself evidence of a mature regression-prevention culture).

### 14.2 Where the domain layer is NOT yet uniform

What "consistency" means here: every domain of the same class should share the same
anatomy, the same registration, the same naming, and the same layering, so a
newcomer can tell at a glance what is an agent, what is data access, and where each
rule lives. Concretely that means: every agentic domain registers the same way
(`domain.py` + `@register_domain` + inherits `ComplianceDomainPrompt`); all agentic
logic lives in an agentic domain (not in a "service domain"); the data-access (CRUD)
layer is separated from the agent layer; no two packages do the same job; and the
docs match the code. The items below are where that is not yet true. The gap is
consistency (form), not capability (function): everything works.

- 🟡 **Two architectures coexist.** Modern domains register via `@register_domain` +
  `ComplianceDomainPrompt`; legacy `autonomous` and `policy` (about 2.3k LOC each)
  still use the pre-refactor `agents/` + `@register_agent` shape.
- 🟡 **Namespace bloat.** 30 of 59 `app/domains/` entries are pure repository stubs
  (CRUD only). Putting data-access packages in the same namespace as autonomous
  agent domains makes the system look larger and less consistent than it is.
- 🟡 **Duplication / overlap.** `hiring_policy` (a ~40-LOC registered stub) overlaps
  conceptually with `policy` (the real engine, ~2,343 LOC, legacy: `PolicyEngineService`
  + `PolicySetupAgent` + sector FairnessGuard rules) - a reader cannot tell from
  the namespace where hiring rules are actually enforced. `hiring_policy` does NOT
  replace `policy`.
- 🟡 **Migration debt.** `interview_intelligence` and `voice` carry agentic-grade
  logic (2026 / 1725 LOC) but are still classified as service domains (promotion
  candidates). `talent_intelligence` similarly has tools/services without a
  `domain.py`.
- 🟡 **Two overlapping "16"s.** The 16 routable ReActAgents and the 16
  `@register_domain` domains are different sets (§10.1), which is a recurring source
  of confusion.
- 🔴 **Doc drift.** At least one authoritative doc (`DOMAIN_CATALOG.md`) is stale vs
  the code (the Tier 6 / autonomous status in §12).

### 14.3 Recommendation

The platform clears the enterprise bar on the dimensions that are hardest to
retrofit: tenant isolation, compliance, auditability, and cost control. The gap is
consistency, not capability. The highest-leverage cleanups are: (1) move the 30
repository stubs out of `app/domains/` (or mark them clearly as data-access), (2)
finish promoting `interview_intelligence` / `voice` / `talent_intelligence` to the
canonical agentic shape, (3) resolve the `policy` vs `hiring_policy` ownership, and
(4) reconcile `DOMAIN_CATALOG.md` with the router. None of these are blockers; they
are the difference between "enterprise-grade core" and "uniformly enterprise".

---

## 15. Effort estimate: relocating the 30 repository stubs

Recurring question: can the 30 repository-stub "domains" be removed, and what does
it take to clean them up? They CANNOT be deleted (each is imported by live routes
and services), but they CAN be relocated out of `app/domains/` (e.g. to
`app/data/` or `app/repositories/`) so the namespace stops conflating data-access
packages with autonomous agent domains. This section sizes that refactor. Numbers
below were measured by grep at the time of writing; re-measure before executing.

### 15.1 The de-risking fact: no models, no migrations

None of the 30 stubs contain a SQLAlchemy model (`__tablename__` / `Base`
subclass) - all models live under `libs/models/`. Therefore relocating these
directories carries **zero Alembic / migration risk**. It is a pure import-path
refactor, not a schema change. This is the single biggest reason the work is
low-risk.

### 15.2 Coupling surface (what actually has to change)

| Coupling point | Count | Notes |
|---|---|---|
| External import sites (`from app.domains.<stub> ...`) | ~96 files | Caught at import time / by the test suite if any are missed. |
| Structural sensors that hardcode the layout | 4 scripts | `scripts/check_stub_invariants.py`, `scripts/validate_stubs.py`, `scripts/check_canonical_domain_structure.py`, `scripts/check_no_imports_from_deprecated.py`. Must be updated in lockstep or CI fails. |
| Dynamic / string-based module paths | 1 known | `app/shared/tool_catalog.py` references `app.domains.workforce.agents.workforce_tool_registry` as a string via `importlib`. A blind import find-replace will NOT catch this; it would fail only at runtime. |

Import-site distribution (uneven - a few stubs carry most of the churn):

- Trivial (1-3 import sites): ~22 stubs (e.g. `triagem`, `auth`, `chat`, `consent`,
  `goals`, `health_check`, `saas_metrics`). Bulk find-replace.
- Moderate (4-7): `admin` (5), `notifications` (7), `tasks` (6), `workforce` (7),
  `compliance` (4), `data_subject` (4), `opinions`* .
- Careful (10-14): `approvals` (14), `opinions` (10). Review case by case.

### 15.3 What does NOT break

- Data / tables (no models in the stubs, so no migrations).
- The 16 core ReActAgents (they do not depend on these CRUD stubs).
- API routes - as long as each stub's `dependencies.py` is moved together with its
  `repositories/`.

### 15.4 Verdict and recommended execution

Effort: **low to medium, mostly mechanical.** Risk: **low**, because there are no
migrations and the imports are static (so the test suite + sensors catch anything
left behind). The only non-static catch point is the `workforce` string reference.

- Fits in a single focused change, but is best done in batches (trivial ->
  moderate -> careful) with the test + sensor suite run between batches.
- 🔵 Treat `workforce` separately: it has `agents/` plus the dynamic string path, so it
  is not a pure stub. It belongs with the "promote to agentic" group
  (`voice`, `interview_intelligence`, `talent_intelligence`), not the
  "relocate data-access" group.
- Minimum-risk variant: move the directories and leave a thin re-export
  `__init__.py` at the old path. This recreates the kind of shim `DOMAIN_CATALOG.md`
  records as being deleted, so use it only as an intermediate migration step, not as
  the destination.

> *`opinions` is listed under "Other domains" in §4 but classified as a repository
> stub in `DOMAIN_CATALOG.md`; treat it as a stub for this refactor.

---

## 16. Action Register (follow-up backlog)

Single index of every item flagged inline above, with the file(s) to touch.
Markers: 🔴 FIX (a divergence or risk to correct), 🟡 REVIEW (consistency /
architecture debt to decide on), 🔵 NOTE (minor cleanup or special case). The
section column points back to the rationale. None of these are production
blockers; they are the cleanup backlog behind the §14 diagnosis.

| # | Mark | Item | Section | Target file(s) |
|---|:--:|---|---|---|
| 1 | 🟡 | **`AutonomousReActAgent` legado redundante** (investigado 2026-06-08, §12.3): Tier 6 removido, sem tráfego de prod, substituído pelo Federado. Deprecar em 2 etapas — (a) remover entrada `autonomous` do handoff (descrição desalinhada: diz "ações pendentes" mas invoca ReAct cross-domain), (b) portar 3 tools agregadoras p/ registry federado + deletar ~2.2k LOC no Sprint 12.6. Reconciliar `DOMAIN_CATALOG.md` (ainda lista como live). | §12.3, §14.2 | `app/orchestrator/supervisor/handoff_tools.py`, `app/domains/autonomous/`, `app/tools/categories.py`, `app/domains/DOMAIN_CATALOG.md` |
| 2 | 🔵 | Candidate NAMES reach the LLM on recruiter-facing chat (`mask_names=False`) — **decisão de produto intencional** (busca por entidade). ✅ O gap real (candidate-facing PII) foi fechado — Gap F, commit `9284313a3`. | §8.1, §8.2 | `app/shared/compliance/c3b_layer.py`, `app/shared/pii_masking.py` (opt-in flag `LIA_RECRUITER_CHAT_MASK_PII`) |
| 3 | ✅ | ~~Protected-attributes registry FAIL-OPEN if YAML fails (ADR-031)~~ **RESOLVIDO (Gap A, commit `991a24981`)**: FairnessGuard honra `APP_ENV` + healthcheck `is_registry_loaded()` no startup (fail-fast em prod). | §8.1 [a], §8.1.1 | `app/shared/compliance/fairness_guard.py`, `app/main.py` |
| 4 | ✅ | ~~BYOK gap: embeddings e o cache de roteamento sempre usam a chave da plataforma~~ **RESOLVIDO (Gap E, commit `b833358ad`)**: `company_id` propagado em 3 call sites (VectorSemanticCache, rag generate_embedding, memory_service). Gap 4 (alias dead-code) não tocado. | §8.1, §8.3 | `app/orchestrator/memory/vector_semantic_cache.py`, `app/domains/ai/services/rag_pipeline_service.py` |
| 5 | 🟡 | 30 repository stubs pollute `app/domains/`; relocate to a data-access namespace | §4, §14.2, §15 | the 30 stub dirs + sensors `scripts/check_stub_invariants.py`, `validate_stubs.py`, `check_canonical_domain_structure.py`, `check_no_imports_from_deprecated.py` + `app/shared/tool_catalog.py` |
| 6 | 🟡 | `hiring_policy` vs `policy` ownership overlap (where are hiring rules actually enforced?) | §4, §10.2, §14.2 | `app/domains/hiring_policy/`, `app/domains/policy/` |
| 7 | 🟡 | Promote `interview_intelligence` / `voice` / `talent_intelligence` to the canonical agentic shape | §4, §10.2, §14.2 | those domain dirs (add `domain.py` + `@register_domain`) |
| 8 | 🟡 | Two different "16"s (routable agents vs `@register_domain` domains) confuse readers | §10.1, §14.2 | doc-level + `app/domains/DOMAIN_CATALOG.md` |
| 9 | 🔵 | Agent Studio: move advanced filter logic from the service layer into `CustomAgentRepository` | §13 | `app/domains/agent_studio/` |
| 10 | 🔵 | `workforce` is a stub with `agents/` + a dynamic string path; handle separately from the pure stubs | §15.4 | `app/domains/workforce/`, `app/shared/tool_catalog.py` |
| 11 | ✅ | ~~`CustomAgentRuntime` (Agent Studio) escapava do `TenantAwareAgentMixin` e do token-budget fence~~ **RESOLVIDO (Gap G, commit `2b6d5ff4d`)**: mixin no MRO (strict-mode gate herdado) + budget gate HTTP 429 no `/execute` + `except: pass`→log. | §13 | `app/domains/agent_studio/custom_agent_runtime.py`, `app/api/v1/custom_agents.py` |
| 12 | 🟡 | **Sprint 2 (do relatório enterprise-readiness 2026-06-08):** desbloquear `talent_intelligence` (module provisioning, ~0.5d); promover mutation-testing de compliance a blocking + criar `scripts/check_agent_mro_compliance.py` (sensor AST: detecta `LangGraphReActBase` sem `TenantAwareAgentMixin` — pegaria regressões do tipo Gap G). | §14.2 | `.github/workflows/ci.yml`, `scripts/`, DB `modules` |

---

## 17. Microsoft Teams + Microsoft Graph integration

LIA ships as a **Microsoft Teams app** (conversational bot + Adaptive Card actions
+ proactive notifications) backed by a **Microsoft Graph** integration for
calendar, Teams online meetings, and meeting transcripts. There are two distinct
trust boundaries: **inbound** (Bot Framework, Teams calling us) and **outbound**
(Graph API, us calling Microsoft 365). Most Teams files live in
`app/domains/communication/services/`; the Graph layer lives in
`app/domains/integrations_hub/services/`.

> The bot reuses the *same* orchestrator and the same 16 ReActAgents as web chat.
> Teams is a channel, not a separate brain. Text typed in Teams flows through the
> normal chat pipeline (so the embedding / BYOK story is exactly §8.3; nothing
> Teams-specific embeds).

### 17.1 Capabilities (what the Teams app can actually do)

| Capability | How |
|---|---|
| Conversational recruiting | Recruiter chats with LIA inside Teams; routed through the orchestrator. Slash commands `/buscar`, `/triagem`, `/relatorio` are rewritten to natural-language prompts. |
| Multimodal input | CV attachments parsed, images via Gemini Vision, voice notes via STT (`teams_orchestrator_bridge.py`). |
| Adaptive Card actions | **Approve / Reject / Schedule** a candidate straight from a card; the action runs server-side (Approve can kick off WhatsApp WSI screening via `_start_whatsapp_screening`). |
| Proactive nudges | New top candidate, screening complete, daily digest, SLA alerts (`teams_proactivity_engine.py` + `/proactive/*` endpoints). Feeds from the alert system in §18. |
| Interview scheduling | Create a Teams online meeting + Outlook calendar event, cancel/reschedule (`/calendar/schedule`, `/calendar/cancel`). |
| Meeting intelligence | Fetch transcripts (VTT) and recordings from Graph for interview analysis (`teams_recording_service.py`). |
| Smart routing to web | Intents that need the web UI (e.g. "criar vaga") return a deep link to the platform (`WEDOTALENT_PLATFORM_URL`). |
| SSO linking | `/auth/sso-page` + `/auth/callback` link the Teams user to a company/tenant. |

### 17.2 File map

| Layer | File | Role |
|---|---|---|
| Bot (NL) | `communication/services/teams_simple.py` | Core LIA bot: slash-command parsing, message handling. |
| Bot (SDK) | `communication/services/teams_bot.py` | `botbuilder` adapter; proactive messaging, conversation updates. |
| Bot bridge | `communication/services/teams_orchestrator_bridge.py` | Connects Teams activities to the orchestrator; CV / Gemini Vision / STT. |
| Cards | `communication/services/teams_card_renderer.py` | Agent responses -> Adaptive Cards (screening results, candidate lists, plans). |
| Channel webhooks | `communication/services/teams_service.py` | Incoming-webhook posts to specific channels (alerts/notifications). |
| Proactivity | `communication/services/teams_proactivity_engine.py` | Periodic digest / stalled-pipeline checks. |
| Calendar (high-level) | `communication/services/teams_calendar_service.py` | Scheduling UX, `render_schedule_card` (date/time pickers). |
| Recordings | `communication/services/teams_recording_service.py` | Transcripts (VTT) + recordings from Graph. |
| Graph service | `integrations_hub/services/microsoft_graph_service.py` | `create_teams_meeting_with_calendar_event`, `create_standalone_teams_meeting`, `get/update/cancel_calendar_event`, `get_delegated_access_token_for_company`, `check_calendar_permission`. |
| Graph client | `integrations_hub/services/graph_client.py` | Low-level MSAL + `httpx` client. |
| Dual-provider scheduling | `interview_scheduling/services/calendar_service.py` | Picks Google vs Microsoft; interviewer availability. |
| Bot auth | `communication/services/teams_auth.py` | Validates Bot Framework JWTs via Microsoft OpenID / JWKS. |
| API | `app/api/v1/teams.py` | All `/api/v1/teams/*` routes (see §17.3). |
| Models | `libs/models/lia_models/teams.py` | See §17.6. |

### 17.3 Endpoints (`app/api/v1/teams.py`, prefix `/api/v1/teams`)

- `POST /webhook` - Adaptive Card actions (Approve / Reject / Schedule), HMAC-verified.
- `GET  /webhook/audit-logs` - read the action audit trail.
- `POST /messages` - inbound bot activities (messages / events / invokes).
- `POST /send-notification`, `POST /proactive/check`, `POST /proactive/new-candidate`, `POST /proactive/screening-complete`, `POST /proactive/daily-digest` - proactive pushes.
- `POST /feedback` - card feedback capture.
- `GET  /auth/sso-page`, `GET /auth/callback` - SSO tenant linking.
- `POST /calendar/schedule`, `POST /calendar/cancel` - interview meetings.
- `GET  /health` - per-company Teams health.

### 17.4 Microsoft Graph layer (outbound)

`graph_client.py` authenticates with **MSAL** and issues `httpx` calls.
`microsoft_graph_service.py` exposes the business operations: it creates Teams
online meetings together with the Outlook calendar event, reads/updates/cancels
events, and checks calendar permission. Transcripts and recordings are pulled
from `/communications/onlineMeetings/{id}/transcripts` by
`teams_recording_service.py` (Teams transcription is included, no extra STT cost).

### 17.5 Auth & trust boundaries

- **Inbound (Teams -> LIA).** Bot messages: Bot Framework JWT validated against
  Microsoft's OpenID config + JWKS in `teams_auth.py`. Adaptive-card webhook
  (`POST /webhook`): after JSON parse, `verify_webhook_owner` cross-checks the
  `X-Company-ID` header / `payload.company_id` against the JWT-resolved tenant
  AND the candidate/vacancy ownership, then validates the `X-Teams-Signature`
  HMAC-SHA256 against the per-tenant secret (global `TEAMS_WEBHOOK_SECRET` as
  fallback). If `TEAMS_WEBHOOK_SECRET` is unset, the endpoint allows all requests
  (development mode). The legacy global-secret `_verify_teams_webhook_signature`
  was removed from this path.
- **Outbound (LIA -> Graph).** MSAL tokens. **Application** permissions for
  tenant-wide reads (recordings/transcripts). **Delegated** permissions via
  `get_delegated_access_token_for_company`, which uses a stored per-company
  refresh token to act on behalf of the recruiter (e.g. `Calendars.ReadWrite`).

### 17.6 Data models (`libs/models/lia_models/teams.py`)

| Model | Table | Purpose |
|---|---|---|
| `TeamsConversation` | `teams_conversations` | Maps a Teams user/conversation to a company/tenant; holds the conversation reference used for proactive messaging. |
| `TeamsMessage` | `teams_messages` | Log of every incoming/outgoing activity. |
| `TeamsNotification` | `teams_notifications` | Scheduled/sent notifications with the Adaptive Card payload, status, retries, and related job/candidate. |
| `TeamsActionAuditLog` | `teams_action_audit_logs` | Strict audit trail for card actions (approve/reject/schedule), with actor, result, candidate/vacancy/company. |

> `TeamsConversation` and `TeamsActionAuditLog` are explicitly `TENANT-EXEMPT`
> (RLS-enforced / cross-tenant admin audit). `company_id` is `String`, nullable
> for legacy rows pre-migration 097.

### 17.7 Config (env vars)

`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` (Graph credentials);
`MICROSOFT_APP_ID`, `MICROSOFT_APP_PASSWORD` (Bot Framework);
`TEAMS_WEBHOOK_SECRET` (card-webhook HMAC, global fallback), `TEAMS_WEBHOOK_URL`
(default alert channel); `WEDOTALENT_PLATFORM_URL` (deep links back to the web
UI).

---

## 18. Proactive alerts & monitoring

A cross-tenant background system that nudges recruiters when the pipeline needs
attention. **The detectors are deterministic SQL heuristics, not LLM output;**
the LLM only composes the human-readable nudge text when an alert surfaces in
chat. Config has a single source of truth (the `alert_preferences` table); see
the canonical contract `Alertas proativos - fonte-unica-da-verdade (T-1295)` in
`replit.md` and `docs/runbooks/alert-config-single-source.md`.

- **Generation.** `MonitoringLoop` (`recruiter_assistant/services/monitoring_loop.py`)
  runs periodically and piggybacks on `ProactiveDetectorService`
  (`shared/services/proactive_detector_service.py`, 15+ detectors).
  `ProactiveAlertService` (`automation/services/proactive_alert_service.py`) is a
  separate pipeline (notifications / automation), not driven by `MonitoringLoop`.
  Alert types: `STALE_CANDIDATE`, `SLA_BREACH`, `SLA_APPROACHING`,
  `FUNNEL_BOTTLENECK`, `NO_CANDIDATES` (the `_check_stale_candidates` /
  `_check_sla_risks` / `_check_funnel_bottlenecks` checks).
- **Config resolver.** `resolve_alert_config`
  (`shared/services/alert_config_resolver.py`) reads `AlertPreference`
  (`libs/models/lia_models/alert.py`: enable / threshold / cooldown / per-channel
  toggles), fail-loud with a `source` of tenant / default / error. The detector
  honors enable/threshold/channels per rule (no hardcoded constants).
- **Channels.** `bell`, `chat`, `email`, `teams`, `whatsapp`, carried on
  `ProactiveAlert.channels` (Teams digests route through §17).
- **Surfacing in the UI.** Chat cards (proactive hints via the shared
  `useProactiveHints` SWR), the bell, and the daily briefing.
- **Frontend.** `components/settings/AlertPreferencesPanel.tsx`,
  `hooks/settings/use-alert-preferences.ts`, `hooks/ai/use-proactive-alerts.ts`.

---

## 19. Learning loops & adaptive intelligence

LIA has three tiers of "learning". Only the second and third are genuine
feedback loops; the first is similarity retrieval. All three are gated per tenant
by `load_learning_loops_toggles`
(`shared/services/learning_loops_toggles.py`), which reads
`CompanyHiringPolicy.automation_rules.learning_loops` (master `enabled` plus
`jd_similar_suggestion`, `bigfive_department_history`,
`wsi_question_effectiveness`). The feedback-driven loop (tier 2) runs
`FairnessGuard` batch validation before patterns are persisted; Big Five learning
emits a non-blocking fairness warning rather than a hard gate.

1. **Similarity retrieval (not learning).** `JdSimilarService`
   (`job_creation/services/jd_similar_service.py`): `find_similar` /
   `record_jd` / `mark_filled` suggest "similar past jobs" in the wizard and
   record outcomes (time-to-fill, candidate count). It stores 1536-dim vectors
   (`jd_similar_history` is `Vector(1536)`) and rejects any other length, failing
   open (Gemini 768 is explicitly unsupported); see §8.3 for the provider nuance.
   No BYOK. Brazilian PII is redacted before embedding.
2. **Feedback-driven learning.** `LearningLoopService`
   (`shared/learning/learning_loop_service.py`): `capture_feedback` records
   whether an AI suggestion was accepted / modified / rejected,
   `process_unprocessed_feedback` aggregates those into `LearnedPattern`s, and
   `get_patterns_for_context` biases future LLM suggestions toward what the
   recruiter previously preferred. (Files indexed in §11.1.)
3. **Outcome-driven profile learning.** Big Five department history (§19.1),
   plus `confidence_policy_service` (auto-approve thresholds that tighten/loosen
   with history) and `model_drift_service` (flags AI degradation when negative
   feedback rises).

### 19.1 Big Five / personality (job creation AND screening)

Personality is used on both sides of the funnel, and the department-history
portion is a real learning loop.

- **Target profile (job creation).** `BigFiveDepartmentService.get_blend_weights`
  (`job_creation/services/bigfive_service.py`) computes a hybrid OCEAN target
  from four layers: LLM extraction `0.40` + O*NET prior `0.20` + Company Culture
  `0.15` (only approved / human-authored culture feeds the blend) + Department
  History `0.25` (the learning loop). It falls back to a 3-layer blend when there
  is no department history. The result weights WSI `rank_traits` for the vacancy.
- **Scoring (screening).** In WSI (`cv_screening/services/wsi_service/`),
  behavioral questions map to OCEAN traits (`big_five_mapping`) and
  `WSIScoreCalculator` aggregates the candidate's OCEAN profile.
- **Loop closure.** On hire, `record_hire` feeds the candidate's Big Five
  snapshot back into the department aggregate (marked stale for recompute), so
  future vacancies in that department lean toward the profile of successful
  hires. Recruiters see a notice when `bigfive_department_history` is active.

---

## 20. Chat-first navigation

Navigation is mostly a frontend concern, so it is light here. The whole path is
deterministic, with no LLM: intent detection (`navigation_intent.py` uses
keyword/pattern matching) and PT-BR confirmation classification
(`confirmation_classifier.py` regex) are both rule-based, and routing itself is
deterministic. The pattern: LIA suggests a page, the recruiter confirms in
natural Portuguese, and only then does the route change. See the
canonical contract `Roteamento context-aware (T-1165)` in `replit.md` and
`ARCHITECTURE.md` §6.6.

- **Backend.** Intent endpoint `app/api/v1/navigation_intent.py` +
  `app/orchestrator/context/navigation_intent.py`;
  `confirmation_classifier.classify_confirmation`
  (`app/orchestrator/routing/confirmation_classifier.py`) decides whether a PT-BR
  reply (e.g. "pode ser", "bora", "agora não") is a yes or no.
- **Frontend.** `useNavigationIntent`
  (`hooks/shared/use-navigation-intent.ts`, confidence `> 0.65` -> `mode: "ask"`,
  `CHAT_FIRST_TARGET_PAGES`); the `lia:navigation-hint` CustomEvent;
  `DashboardApp` renders a `NavigationHintCard` instead of force-redirecting;
  `useWizardFlow.ts` dispatches the hint on `SPLIT_STAGE`; `lib/navigation/routes.ts`
  (`PAGE_ROUTES`) and `sidebar.tsx` (`navigateOnClick`).


---

## 21. Chat transport architecture

The recruiter chat uses two transports. **SSE is the canonical path** (default
since mid-2026); WebSocket remains available as a legacy option.

### 21.1 SSE (Server-Sent Events) — canonical

File: `app/api/v1/agent_chat_sse.py`

```
POST /api/v1/chat/{session_id}/stream
    Authorization: Bearer <jwt>
    Body: {
      "message": "...",
      "domain": "...",
      "context": {...},
      "approve_pending_id": "<uuid | null>"   # HITL approval replay
    }
Server: text/event-stream
    id: <event_id>
    data: { "type": "<event_type>", ... }
```

**Event types** (`app/shared/chat_event_serializer.py`):

| Type | When | Key payload fields |
|---|---|---|
| `thinking` | Progressive reasoning disclosure | `text` |
| `token` | Partial LLM output (streaming) | `token` |
| `token_done` | Full response assembled | `full_text` |
| `message` | Complete AI turn | `content`, `role`, `response_blocks?` |
| `tool_started` | Tool execution began | `name`, `id` |
| `tool_finished` | Tool execution complete | `name`, `id`, `result_summary` |
| `reasoning_step` | Internal ReAct step (verbose mode) | `step`, `detail` |
| `panel_update` | Wizard side-panel content | `panel_type`, `stage`, `data`, `thread_id`, `completeness` |
| `error` | Non-fatal error | `message`, `code` |
| `approval_required` | HITL gate fired | `pending_id`, `action`, `approve_url` |
| `budget_exhausted` | Daily token budget reached | `plan`, `limit` |

**Budget gating.** Every SSE request runs through
`app/domains/credits/services/token_budget_service.check_budget`. Dev tenants
with `APP_ENV=development` receive an unlimited "enterprise(-1)" budget via
`_is_unlimited_dev_tenant` (avoids exhausting credits during local iteration).
Redis key `token_budget:<company_id>:<date>` tracks daily consumption. The gate
emits `budget_exhausted` and returns early; it does not raise.

**HITL approval flow.** When a tool-level HITL gate fires:
1. The SSE stream emits `approval_required` with `pending_id`.
2. The frontend shows a confirmation card; recruiter clicks Confirm.
3. The client re-POSTs the same message with `approve_pending_id=<pending_id>`.
4. The backend `_detect_hitl_approval` resolves the pending action and re-runs
   the tool with the gate bypassed.

### 21.2 WebSocket — legacy

File: `app/api/v1/agent_chat_ws.py`

Bidirectional WS connection with equivalent functionality to SSE. Maintained for
backwards-compatibility. The frontend selects the transport via the env var
`NEXT_PUBLIC_CHAT_TRANSPORT` (`sse` | `ws`; default: `sse`).

### 21.3 Session and domain scoping

- `session_id` maps to a recruiter session in `company_sessions`.
- LangGraph checkpointer uses `thread_id = f"{session_id}::{domain}"` — isolated
  state per domain within a session. Context bleed between domains is structurally
  impossible.
- The active company is resolved from the JWT and set into `_current_company_id`
  ContextVar before the agentic loop runs.
- The entity resolver sets `_active_vacancy_id` / `_active_candidate_id` ContextVars
  per turn (deterministic DB lookup); these are consumed by tools as fallback
  `vacancy_id` / `candidate_id` when the LLM does not pass the ID explicitly.

---

## 22. Rich Response Protocol (RRP)

RRP is the typed block system for structured visual responses. Instead of raw
markdown that the frontend parses heuristically, agents emit typed blocks that
render as native UI components (score cards, tables, funnel charts, etc.).

**Design principle:** the LLM narrates in prose; the data lives in blocks. When
a block already displays information, the LLM is instructed not to re-render it
as markdown (`RRP_TABLE_HINT` in `rrp_ranking_builder.py`).

### 22.1 Block catalog (`app/shared/rrp_blocks.py`)

All blocks are Pydantic models with `extra='forbid'`. Base envelope: `_BlockBase`
(fields: `block_id`, `role`, `layout`, `state`, `error`).

| `kind` | Class | Purpose |
|---|---|---|
| `prose` | `ProseBlock` | Rich markdown narrative (role: answer). The default text block. |
| `evidence_stack` | `EvidenceStackBlock` | Evidence items per candidate: `source_type` (linkedin / resume / assessment / interview / internal_record), `headline`, `detail`, `confidence`. |
| `score_explainer` | `ScoreExplainerBlock` | Score breakdown: overall score + list of `ScoreFactor` (name, weight, value, justification). **Provenance rule:** only populated from real `lia_opinions` data (requires `opinion_id`). |
| `comparison_table` | `ComparisonTableBlock` | Multi-column table for N entities (candidates or jobs). Typed `columns: list[ComparisonColumn]` + `rows: list[ComparisonRow]` with arbitrary cells. |
| `funnel` | `FunnelBlock` | Pipeline funnel: list of stages with candidate counts and conversion rates. |
| `candidate_card` | `CandidateCardBlock` | Compact card: name, stage, LIA score, recommendation label. |

**Provenance invariant.** `verify_block_provenance()` and
`tests/contract/test_rrp_provenance_gate.py` enforce that every block with a
score or evidence attribution has a verifiable source. Without real retrieval:
`unverified=True` + `confidence='low'` + explicit label. Never cite a data
source for a number generated purely from LLM parametric knowledge.

### 22.2 Data flow (two paths → one SSE event)

```
Path A — ActionExecutor (deterministic action_handlers):
  action_handler builds blocks → returns { data: { response_blocks: [...] } }
  MainOrchestrator extracts blocks from structured result
  SSE serializer includes in `message` event as `response_blocks`

Path B — Agentic loop (LangGraph ReAct tools):
  tool builds blocks → calls rrp_block_sink.append_from_result(result)
  ContextVar _rrp_blocks_sink accumulates blocks during the turn
  LangGraphReActBase._run_graph drains the sink at end of turn
  AgentOutput.metadata['response_blocks'] → SSE serializer
```

`app/shared/rrp_block_sink.py` is the Path B tee: a per-request ContextVar
that never raises (defensive tee — a block-sink bug must not crash the tool).

### 22.3 Canonical producer (`app/shared/rrp_ranking_builder.py`)

`build_candidate_ranking_blocks(job_id, rows)` is the **single source of truth**
for candidate ranking blocks. It produces `ScoreExplainerBlock` +
`EvidenceStackBlock` + `ComparisonTableBlock` + `CandidateCardBlock` from a
normalized list of candidate dicts. Rows with `opinion_id` get the full moat
(score explainer + evidence); rows without get only the comparison table.

Two consumers (same producer — canonical-fix principle):
- `sourcing_actions._rank_candidates` (ActionExecutor path)
- `talent_tool_registry.rank_candidates` (agentic-loop path)

`build_table_block(title, entity_type, columns, rows, source_tool)` is the generic
table producer used for job lists, analytics tables, etc.

### 22.4 Frontend integration

`ResponseBlockRenderer` in `plataforma-lia/src/components/chat/` renders each
`kind` to its visual component. The renderer uses TypeScript `assertNever`
exhaustiveness (compiler catches a missing `kind` at build time). CI guard: the
6-kind schema-sync sensor `scripts/check_rrp_block_schema_sync.py` runs as
BLOCKING (baseline 0).

---

## 23. Eligibility questions — canonical shape and producer

Eligibility questions are go/no-go screening gates asked **before WSI**:
"Tem CNH?", "Aceita trabalho presencial?", "Disponível para viagens?". They are
configured per-vacancy, can be *eliminatory* (wrong answer = disqualify) or
non-eliminatory, and map to a category that drives the reconsideration UX.

### 23.1 Background: the ghost-feature problem

Before 2026-06-03, four divergent shapes coexisted (wizard, vacancy editor,
settings catalog, backend extractor) that did not match. Even when a recruiter
configured eligibility questions, they never reached the candidate. The feature
was live in the UI and inert in the code. Fixed by canonicalizing to a single
shape, a single producer, and two consumers.

### 23.2 Canonical shape — `EligibilityQuestionItem`

Single source of truth: `app/schemas/eligibility_question_item.py`.

```python
class EligibilityQuestionItem(BaseModel):
    id: str
    question: str
    question_type: str               # "yes_no" | "multiple_choice" | "text"
    options: list[str]               # choices for multiple_choice
    is_eliminatory: bool
    expected_answer: str | None      # the answer that passes the gate
    category: str                    # work_model | location | availability | legal | default
    order: int
```

`category` selects the reconsideration template shown to a candidate who fails
an eliminatory question (allowing 2× reconsideration attempts before rejection).

A `model_validator(mode="before")` normalizes the 4 legacy shapes into this
canonical form on parse — old JSONB data in `JobVacancy.eligibility_questions`
is upgraded transparently on read without a migration.

### 23.3 Single producer

`EligibilityVerificationService.get_eligibility_questions_from_job()`
(`app/domains/cv_screening/services/eligibility_verification_service.py`) is
the **only** parser of `job.eligibility_questions`. All consumers call this
method; none read the JSONB directly.

### 23.4 Two consumers, one producer

| Consumer | Path | Notes |
|---|---|---|
| Web screening | `triagem_session_service/eligibility_phase.py` | Called at `start_session`; eligibility runs BEFORE WSI. WSI messages use `wsi_block=999` sentinel so eligibility answers are excluded from WSI scoring. |
| WhatsApp screening | `conversation_manager` | Same producer; questions sent as WhatsApp messages with structured reply options. |

### 23.5 Compliance wiring

- **Consent gate.** `start_session` calls
  `ConsentCheckerService.check_candidate_consent(purpose="ai_screening")` before
  the first eligibility question. The frontend checkbox is defense-in-depth; the
  backend gate is authoritative.
- **Fairness.** Questions configured by the recruiter pass `FairnessGuard` at
  save time. Protected attributes (CLT Art. 373-A, LGPD) cannot appear as
  eliminatory criteria. Guard reads `config/protected_attributes.yaml`.
- **Reconsideration.** 2× reconsideration offers are made before final rejection
  on eliminatory questions. After 2 failed answers the candidate is logged to the
  talent pool for future non-eliminatory matches.
- **Talent pool routing.** Rejected-by-eligibility candidates are NOT deleted —
  they enter the talent pool so they can be re-invited to future vacancies that
  don't have the same requirement.

**Sentinels:** `tests/contract/test_eligibility_producer_contract.py` (13 tests) +
`tests/unit/test_eligibility_phase.py` (7 tests).


---

## 24. WSI — Workplace Science Index

O WSI é a **metodologia proprietária de triagem estruturada** da WeDOTalent.
É o principal diferencial técnico da plataforma: em vez de triagem ad-hoc por
chat livre (onde o candidato pode se preparar para respostas esperadas), o WSI
gera perguntas calibradas à vaga e avalia as respostas usando frameworks
psicométricos estabelecidos, produzindo um score OCEAN + recomendação
auditável.

### 24.1 O que é e por que existe

**O problema:** Triagem de CVs por keywords é rápida mas superficial. Chat
livre revela personalidade mas não é comparável entre candidatos. Entrevistas
presenciais são caras e tardias no funil.

**A solução WSI:** Um conjunto de 12 perguntas geradas por IA — calibradas
especificamente para a combinação vaga + senioridade + departamento — que o
candidato responde de forma assíncrona (WhatsApp, web, ou voz). As respostas
são avaliadas por LLM usando rubricas estruturadas (Bloom + Dreyfus), mapeadas
a traços OCEAN, e combinadas em um score final ponderado.

**O resultado:** Um `lia_score` de 0–100 com breakdown por dimensão, evidências
citadas das respostas, e recomendação de ação — auditável e comparável entre
candidatos da mesma vaga.

### 24.2 Composição das perguntas

A distribuição canônica é **70% técnico + 30% comportamental**, mas o split
é ajustável por senioridade via `wsi_distribution.py`:

| Senioridade | Técnicas | Comportamentais | Total |
|---|---|---|---|
| Júnior (0–2 anos) | 8 | 4 | 12 |
| Pleno (2–5 anos) | 7 | 5 | 12 |
| Sênior (5+ anos) | 5 | 7 | 12 |
| Liderança (10+ anos) | 5 | 7 | 12 |

Cada pergunta tem nível mínimo de exigência:
- **Técnicas:** Dreyfus nível 3 (Competente) como mínimo para pleno/sênior
- **Comportamentais:** Bloom nível 4 (Analisar) como mínimo

Fonte única das distribuições: `app/domains/job_creation/services/wsi_distribution.py`
(YAML per-senioridade). Substituiu o split 12-vs-13 anterior que era
split-brain entre dois arquivos de configuração.

### 24.3 Geração das perguntas (job creation)

No wizard de criação de vagas (§4, `job_creation/`), o nó `wsi_questions`
gera as perguntas para a vaga usando:

1. **Job description + competências** já geradas nos nós anteriores
2. **Big Five blend** do departamento (se disponível — o learning loop §19.1)
3. **WSI skill taxonomy** (`app/shared/wsi_skill_taxonomy.py`) — ontologia de
   habilidades mapeadas a dimensões OCEAN + frameworks de avaliação
4. LLM gera o banco de perguntas; o gate `wsi_questions_gate` apresenta ao
   recrutador para aprovação (`interrupt()`)

As perguntas aprovadas ficam em `JobVacancy.wsi_questions` (JSONB).

### 24.4 Execução da triagem (triagem session)

Durante a triagem de um candidato (§25), as perguntas são entregues
sequencialmente via WhatsApp, web ou voz. Cada resposta é armazenada em
`wsi_responses` com o `wsi_block` (número sequencial da pergunta).

Respostas de elegibilidade (§23) usam `wsi_block=999` como sentinela para
serem excluídas do scoring WSI.

### 24.5 Scoring

O scoring acontece em `app/domains/cv_screening/services/wsi_service/`:

```
wsi_score_calculator.py:
  1. Para cada resposta (exceto block=999):
     a. LLM avalia a resposta usando rubrica 4 níveis (Bloom/Dreyfus)
     b. Mapeia à dimensão OCEAN via big_five_mapping
     c. Aplica peso da pergunta (técnica vs comportamental)

  2. WSIScoreCalculator.calculate():
     - Agrega scores por dimensão OCEAN
     - Aplica os pesos de competência da vaga (rank_traits)
     - Produz: {ocean_profile, lia_score, score_breakdown, recommendation}

  3. lia_score_service.py:
     - Combina CV score + WSI score
     - Gera o parecer final (opinion) em lia_opinions
     - Campos: recommendation (Altamente Recomendado / Recomendado /
       Avaliar com Ressalvas / Não Recomendado), summary, strengths[], concerns[]
```

O `lia_score` final é o que aparece no Kanban como badge no card do candidato.
O parecer completo abre no modal de análise.

### 24.6 Big Five learning loop (§19.1 complementado)

Quando um candidato é contratado (`status=hired`), `record_hire()` alimenta
o perfil de departamento: o snapshot OCEAN do candidato contratado entra no
agregado running com decay temporal. Futuras vagas do mesmo departamento
recebem `blend_weights` que já carregam o perfil histórico de quem deu certo.

Gate LGPD (ADR-LGPD-001): mínimo `MIN_DEPT_SAMPLES = 10` contratações antes
de ativar o blend histórico. Com N < 10 o departamento usa só LLM + O*NET.

### 24.7 Fluxo ponta-a-ponta

```
Vaga criada (WSI questions aprovadas pelo recrutador via wizard HITL)
   │
   ▼
Candidato adicionado ao pipeline
   │
   ▼
[Eligibility phase]  perguntas eliminatórias (§23), ANTES do WSI
   │                 wsi_block=999 (excluído do scoring)
   ▼
[WSI phase]  12 perguntas entregues via canal escolhido
   │         WhatsApp: data_request_whatsapp_service
   │         Web:      triagem_session_service
   │         Voz:      voice_screening_orchestrator (§25.3)
   ▼
Todas as respostas coletadas
   │
   ▼
[Scoring]  wsi_score_calculator → lia_score_service → opinion salva
   │
   ▼
Candidato recebe status + lia_score no Kanban
   │
   ▼
[Recrutador]  vê score + evidências no RRP (score_explainer + evidence_stack)
              aprova/rejeita/avança para próxima etapa
```

**Arquivos canônicos:**
- Geração: `job_creation/services/wsi_question_generator.py`
- Distribuição: `job_creation/services/wsi_distribution.py`
- Taxonomy: `shared/wsi_skill_taxonomy.py`
- Scoring: `cv_screening/services/wsi_service/wsi_score_calculator.py`
- Score final: `cv_screening/services/lia_score_service.py`
- Opinião: tabela `lia_opinions` (is_current=true para o parecer vigente)

---

## 25. Triagem session — lifecycle completo

A "triagem" é a jornada que um candidato percorre desde o momento em que é
adicionado a uma vaga até a obtenção do score final. O `TriagemSessionService`
(`app/domains/cv_screening/services/triagem_session_service.py`) é o
orquestrador canônico desse ciclo.

### 25.1 Estados da sessão

```
CREATED → CONSENT_PENDING → CONSENT_GIVEN → ELIGIBILITY → WSI_IN_PROGRESS
       → WSI_COMPLETE → SCORING → SCORED → (REJECTED | APPROVED_FOR_NEXT_STAGE)
```

Cada transição de estado é auditada via `AuditService.log_decision_in_session`.
Estados terminais: `REJECTED` (reprovou na eligibility ou no score mínimo),
`SCORED` (score calculado, aguarda decisão do recrutador).

### 25.2 Etapas em detalhe

**1. CONSENT (LGPD gate)**

`ConsentCheckerService.check_candidate_consent(purpose="ai_screening")` é
chamado antes de qualquer pergunta. O candidato deve ter consentido
explicitamente. O gate é no backend — o checkbox do frontend é
defense-in-depth.

Se o candidato não consentiu: a sessão fica em `CONSENT_PENDING`; uma
comunicação de solicitação de consentimento é disparada via canal configurado
(WhatsApp/email).

**2. ELIGIBILITY (antes do WSI)**

`eligibility_phase.py` entrega as perguntas eliminatórias (§23). Se o
candidato falha numa pergunta eliminatória:
- 2× reconsideração (por categoria)
- Após 2 falhas: sessão → `REJECTED`; candidato → talent pool

As respostas de elegibilidade usam `wsi_block=999` para não contaminar o
scoring WSI.

**3. WSI IN PROGRESS**

As 12 perguntas são entregues pelo canal configurado para a vaga:

| Canal | Orquestrador |
|---|---|
| Web (portal do candidato) | `triagem_session_service.deliver_next_question()` |
| WhatsApp | `data_request_whatsapp_service.start_collection()` |
| Voz (Gemini Live) | `voice_screening_orchestrator.start_voice_session()` |

O candidato pode responder de forma assíncrona (sem um humano na outra ponta).
O sistema aguarda as respostas e avança a sessão conforme chegam.

**4. SCORING**

Quando todas as respostas chegam (ou o timeout expira com respostas parciais):
`wsi_score_calculator` → `lia_score_service` → salva `opinion` em
`lia_opinions` → atualiza `VacancyCandidate.lia_score` → dispara evento
"triagem concluída" para o recrutador.

### 25.3 Canal de voz

`app/domains/voice/services/voice_screening_orchestrator.py` orquestra a
triagem por voz via **Gemini Live Audio** (para candidatos web/app) com
fallback Twilio PSTN (para candidatos sem internet). O realtime credit session
(`realtime_credit_session.py`) contabiliza tokens de áudio por tenant. A
transcrição entra no mesmo pipeline de scoring que o texto.

### 25.4 Candidato auto-serviço

`CandidateSelfServiceAgent` (`app/domains/candidate_self_service/`) é o
agente público (sem autenticação de recrutador) que o candidato encontra:
- No portal de triagem (`/triagem/preview/chat`)
- Via link compartilhado pela vaga
- No WhatsApp via `data_request_whatsapp_service`

Este agente tem tools limitadas (apenas candidato-facing), aplica FairnessGuard
extra (candidato é parte mais vulnerável) e NÃO tem acesso a dados de outros
candidatos.

### 25.5 Integração com o pipeline

Após a triagem, o recrutador vê o candidato no Kanban com:
- Badge `lia_score` (0–100)
- Cor do badge (verde/amarelo/vermelho por threshold configurável)
- Ao abrir o perfil: RRP blocks `score_explainer` + `evidence_stack` +
  `comparison_table` com os demais candidatos da vaga

A decisão final (mover para próxima etapa, aprovar para entrevista, reprovar)
é sempre do recrutador. A IA recomenda; o humano decide.

---

## 26. Mapa da API surface

O serviço tem aproximadamente **350 arquivos** de endpoint em `app/api/v1/` (contagem verificada em 2026-06-08; o número cresce a cada sprint). Esta seção fornece
a taxonomia para que um dev saiba onde encaixar endpoints novos e onde procurar
o que já existe.

### 26.1 Taxonomia por categoria

**Chat e orquestração (os endpoints mais críticos):**
- `agent_chat_sse.py` — chat SSE canônico (§21)
- `agent_chat_ws.py` — chat WebSocket legacy
- `ws_manager.py` / `_ws_stream_helpers.py` — helpers de WS
- `orchestrator_routes.py` — bootstrap do orquestrador (não em v1/)
- `wizard_smart_orchestrator.py` — endpoints do wizard de criação de vagas

**Candidatos e pipeline:**
- `applications.py`, `candidates.py` — CRUD de candidatos
- `screening.py`, `screening_questions.py` — triagem e perguntas WSI
- `triagem.py` — sessões de triagem (lifecycle §25)
- `stage_transition_automation.py` — transições automatizadas
- `talent_funnel.py`, `talent_pools.py` — funil e bancos de talentos
- `short_lists.py` — shortlists manuais

**Vagas:**
- `jobs.py` — CRUD de vagas
- `skills_catalog.py`, `wizard_suggestions.py`, `wizard_analytics.py` — wizard
- `search_archetypes.py` — arquétipos de busca

**Triagem WSI:**
- `wsi/` (pasta) + `wsi_questions.py`, `wsi_async.py`, `wsi_observability.py`
- `wsi_question_adjust.py` — ajuste fino de perguntas geradas
- `wsi_screening_pipeline_endpoint.py` — pipeline de scoring

**Comunicação:**
- `whatsapp.py`, `whatsapp_webhook.py` — integração WhatsApp
- `teams.py` — Microsoft Teams (§17)
- `twilio_voice.py`, `voice.py`, `voice_screening.py`, `voice_stream.py` — voz

**Sourcing:**
- `sourcing.py`, `sourcing_agents.py`, `sourcing_pipeline.py`
- `sourcing_orchestrator.py` — orquestrador de sourcing
- `search_assistant.py` — busca assistida por IA

**Agentes e Studio:**
- `agent_studio_channels.py`, `agent_studio_quality.py`
- `agent_studio_triagem_invite.py`, `agent_studio_voice.py`
- `agent_studio_whatsapp.py`
- `agent_templates.py`, `agent_template_catalog.py`

**Analytics e observabilidade:**
- `analysis.py`, `ai_performance.py`, `ai_consumption.py`
- `agent_quality.py`, `agent_quality_dashboard.py`
- `wsi_observability.py`, `traces.py`
- `wizard_analytics.py`

**Admin (acesso restrito `wedotalent_admin`):**
- `admin.py`, `admin_agents.py`, `admin_audit_decisions.py`
- `admin_bias_audit.py`, `admin_circuit_breakers.py`
- `admin_compliance_fairness.py`, `admin_consent.py`
- `admin_lgpd.py`, `admin_persona.py`, `admin_platform.py`
- `admin_prompts.py` — editor de YAMLs de prompt por tenant

**Integrações externas:**
- `ats.py` — sincronização com ATS externos (Gupy, Pandapé, Merge)
- `webhooks.py`, `webhook_event_types.py`
- `workos.py` — SSO via WorkOS
- `ai_transparency.py` — EU AI Act transparency endpoints

**LGPD / compliance:**
- `auth.py`, `affirmative.py` — autenticação + ação afirmativa
- `trust_center.py`, `ai_transparency.py`
- `admin_lgpd.py`, `admin_consent.py`

**Utilitários:**
- `system_health.py` — health checks
- `stubs.py` — endpoints placeholder (**router não registrado em `app/api/routes.py`** — os endpoints nunca sobem em runtime; código morto; deletar ou manter como documentação de intenção)
- `settings_progress.py` — progresso de configuração da empresa

### 26.2 Onde colocar endpoints novos

| Tipo de endpoint | Localização |
|---|---|
| Novo recurso de domínio (ex: nova feature de sourcing) | `app/api/v1/sourcing_<feature>.py` |
| Extensão de domínio existente | Adicionar rota ao arquivo existente (ex: `sourcing.py`) |
| Novo endpoint admin (staff WeDOTalent only) | `app/api/v1/admin_<feature>.py` + role gate `wedotalent_admin` |
| Endpoint de IA / agente | `app/api/v1/agent_<feature>.py` |
| Webhook entry point | `app/api/v1/webhooks.py` ou arquivo dedicado se tiver HMAC/auth próprio |
| Endpoint público (sem auth de recrutador) | `app/api/v1/<feature>_public.py` |

**Convenção de registro:** todo arquivo de rotas é importado em
`app/main.py` (`include_router`). Ao criar um arquivo novo, lembrar de
adicioná-lo lá.

---

## 27. Mapa de funcionalidades de IA por página

Esta seção é para líderes de produto e devs que querem entender "o que a IA
faz em cada parte da plataforma" sem precisar ler o código. As funcionalidades
estão listadas por superfície do produto.

### 27.1 Painel de Controle (`/dashboard`)

| Funcionalidade de IA | Agente / Serviço | Descrição |
|---|---|---|
| Tarefas priorizadas do dia | `AnalyticsReActAgent` | Lista de ações pendentes (candidatos aguardando triagem, vagas SLA em risco) ordenada por urgência |
| Alertas proativos | `ProactiveDetectorService` (§18) | Detectores determinísticos (SQL) que identificam candidatos parados, SLA breaches, funil com gargalo — não são LLM |
| Briefing diário | `CommunicationReActAgent` | Narrativa condensada do pipeline do dia, gerada por LLM com base em métricas reais |
| Resumo de pipeline | `AnalyticsReActAgent` | Contagens por etapa, taxa de conversão, comparativo semana anterior |

### 27.2 Vagas (`/jobs`)

| Funcionalidade de IA | Agente / Serviço | Descrição |
|---|---|---|
| **Wizard de criação de vaga** | `WizardReActAgent` + grafo LangGraph (15 nós) | Fluxo guiado para criar uma vaga completa: intake → JD enrichment → competências → WSI questions → salário → Big Five → eligibility → pipeline template → publicação. 4 HITL gates. |
| Enriquecimento de JD | `job_creation/nodes/jd_enrichment.py` | LLM enriquece a descrição da vaga com base no setor, senioridade e cultura da empresa |
| Sugestão de competências | `job_creation/nodes/competency.py` | Extração de competências + O*NET + cultura da empresa |
| Geração de perguntas WSI | `job_creation/nodes/wsi_questions.py` | 12 perguntas calibradas para a vaga (§24) |
| Estimativa de salário | `job_creation/nodes/salary.py` + `MarketBenchmarkService` | Benchmarking de mercado (com flag de proveniência: pesquisado vs estimado, §CLAUDE.md proveniência) |
| JD similar | `JdSimilarService` (§19) | Sugere vagas passadas similares como referência para o recrutador |
| Faixa salarial herdada | `_shared.resolve_inherited_salary_ranges` | Herda a faixa salarial configurada em Configurações para o nível + departamento |
| Score de aderência do JD | `cv_screening/services/cv_scoring_service.py` | Score automático do JD gerado vs requisitos da vaga |

### 27.3 Funil de Talentos / Kanban (`/talent-funnel`)

| Funcionalidade de IA | Agente / Serviço | Descrição |
|---|---|---|
| Busca de candidatos | `TalentFunnelReActAgent` | Busca multi-modal: banco interno + LinkedIn + GitHub + StackOverflow |
| Score LIA no card | `lia_score_service` | Badge de 0–100 em cada candidato, calculado pelo WSI scoring (§24) |
| Parecer expandido | RRP `score_explainer` + `evidence_stack` | Ao abrir perfil: breakdown do score por dimensão + evidências citadas das respostas |
| Ranking de candidatos | `rrp_ranking_builder.build_candidate_ranking_blocks` | Tabela comparativa dos candidatos da vaga com scores, evidências e recomendação |
| Mover candidato (HITL) | `PipelineTransitionAgent` + `@require_hitl` | Move candidato entre etapas; gate de confirmação se `LIA_HITL_GATE=ON` |
| Análise de CV | `cv_screening/services/cv_scoring_service.py` | Score de aderência CV vs requisitos + rubrica por dimensão |
| Comparar candidatos | `sourcing_actions._compare_candidates` | Comparação lado-a-lado de N candidatos pelo chat |
| Digital twin | `digital_twin/` | Criação de perfil sintético do candidato ideal para a vaga |
| Triagem WSI (iniciar) | `TriagemSessionService` (§25) | Inicia sessão de triagem; entrega perguntas via canal escolhido |
| Triagem por voz | `voice_screening_orchestrator` | Versão voice-first do WSI via Gemini Live ou Twilio PSTN |
| Alertas de SLA | `MonitoringLoop` + `ProactiveDetectorService` | Alerta quando candidato está parado há N dias sem movimentação |

### 27.4 Configurações (`/configuracoes`)

| Seção | Funcionalidade de IA | Descrição |
|---|---|---|
| **Dados da Empresa** | Auto-preenchimento via website | LLM faz scraping do site da empresa e preenche missão, visão, valores, stack |
| **Cultura** | Revisão FairnessGuard | Qualquer campo de cultura salvo passa pelo FairnessGuard (evita critérios discriminatórios escondidos em "valores") |
| **Personalidade da IA** | Persona customizável | Nome + tom da IA por empresa (§0.2). Muda como a IA se comunica, não o que ela faz. |
| **Instruções LIA por Campo** | `LiaFieldConfigService` | 34 toggles + instruções por campo. Quando ativo, o agente injeta a instrução do recrutador no prompt. Toggle OFF = campo ignorado. |
| **Política de Recrutamento** | `PolicyReActAgent` | Conversa guiada para configurar regras de hiring (diversidade, aprovações, etc). FairnessGuard em cada save. |
| **Processo Seletivo** | Pipeline stages | Etapas do processo configuráveis por empresa; herança + override por vaga |
| **Faixas Salariais** | `salary_bands/` | Faixas por nível + departamento; herdadas automaticamente no wizard de vaga |
| **Inteligência / Alertas** | `alert_preferences` | Configuração de alertas proativos (§18): limiares, canais, cooldowns |
| **BYOK** | `tenant_llm_context.py` | Chave de LLM própria do tenant (Claude/Gemini/OpenAI) para uso em chat + completion |

### 27.5 Indicadores (`/indicadores`)

| Funcionalidade de IA | Agente / Serviço | Descrição |
|---|---|---|
| Narrativa de métricas | `AnalyticsReActAgent` | LLM interpreta os dados e gera análise em linguagem natural ("Seu tempo médio de contratação aumentou 12% — o funil de Engenharia está represado na etapa técnica") |
| Relatório de diversidade | `BiasAuditService` (FAR-5) | Análise de disparate impact por dimensão protegida; four-fifths rule |
| Predição de time-to-fill | `ml/ttf_predictor.py` | Modelo ML que estima quantos dias para fechar a vaga baseado em histórico + pipeline atual |
| Exportação de relatório | `orchestrator/action_handlers/analytics_actions.py` | Geração de relatório em PDF/Excel via LLM + dados estruturados |
| Aprendizado de padrões | `LearningLoopService` (§19) | Mostra quais sugestões de IA foram aceitas/rejeitadas (feedback loop visível) |

### 27.6 Chat lateral (disponível em todas as páginas)

O chat lateral está disponível em toda a plataforma (widget fixo). Dependendo
do contexto da página aberta, o `CascadedRouter` usa o **view_context** para
enriquecer o roteamento:

| Página atual | Contexto injetado | Efeito no chat |
|---|---|---|
| Kanban de vaga X | `view_context: { vacancy_id: X }` | EntityResolver já sabe qual vaga; perguntas sobre "os candidatos dessa vaga" funcionam sem precisar nomear |
| Perfil do candidato Y | `view_context: { candidate_id: Y }` | Chat já tem o candidato em contexto; "analise ele" funciona diretamente |
| Indicadores | domínio: analytics | Router preferencia `AnalyticsReActAgent` |
| Configurações | domínio: company_settings | Router preferencia `CompanySettingsReActAgent` |

O chat pode navegar o usuário para outras páginas via `ui_action: navigate_to`
(validado pelo whitelist `navigation_routes.py`, §8.1) e abrir modais via
`open_ui` tool. O histórico de contexto é mantido por sessão.
