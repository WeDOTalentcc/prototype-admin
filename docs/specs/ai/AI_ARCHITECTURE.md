# AI Architecture — WeDOTalent / Plataforma LIA

> Última atualização: 2026-03-26
> Fonte: leitura direta do código — `recruiter_agent_v5` (GitHub WeDOTalent) + `lia-agent-system` (Replit)
> **SPEC-DRIVEN DEVELOPMENT** — este documento é fonte da verdade para a arquitetura de IA.

---

## 1. Visão Geral da Arquitetura

O sistema de IA da WeDOTalent opera em duas camadas complementares:

| Camada | Repositório | Stack | Papel |
|--------|-------------|-------|-------|
| **Agente Multi-Domínio** | `recruiter_agent_v5` | Python + LangGraph + Gemini + Celery + RabbitMQ | Processa queries do recrutador via linguagem natural, executando ações no ATS |
| **Serviços LIA** | `lia-agent-system` | Python + FastAPI + LangGraph + Gemini (produção) | 12 domínios, 13 agentes, 3 StateGraphs, CascadedRouter 6-tier, compliance integrado |

### 1.1 Diagrama de Fluxo Geral

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  ats_front   │────▶│  ats_api (Rails)  │────▶│  PostgreSQL  │
│  (Nuxt 3)    │     │  REST API + JWT   │     │  Multi-tenant│
└──────┬───────┘     └────────┬──────────┘     └──────────────┘
       │                      │
       │  WebSocket/HTTP      │  RabbitMQ / HTTP
       │                      │
       ▼                      ▼
┌──────────────┐     ┌──────────────────────────────┐
│  LIA Chat    │     │  recruiter_agent_v5          │
│  (Prompt UI) │────▶│  ┌─────────────────────────┐ │
│              │     │  │ WorkflowOrchestrator     │ │
└──────────────┘     │  │  (LangGraph StateGraph)  │ │
                     │  │                           │ │
                     │  │  intent_analyzer          │ │
                     │  │  → api_planner            │ │
                     │  │  → api_executor           │ │
                     │  │  → plan_validator         │ │
                     │  │  → data_processor         │ │
                     │  │  → answer_formatter       │ │
                     │  └─────────────────────────┘ │
                     │                               │
                     │  Domain Dispatchers:           │
                     │  ┌──────────────────────────┐ │
                     │  │ applies │ jobs │ insights │ │
                     │  │ messaging │ autonomous   │ │
                     │  │ evaluation │ sourcing     │ │
                     │  └──────────────────────────┘ │
                     └──────────────────────────────┘
```

---

## 2. recruiter_agent_v5 — Workflow Pipeline (LangGraph)

O pipeline principal é um `StateGraph` definido em `src/workflow/graph.py`. Todos os agentes operam sobre um estado compartilhado (`QueryState`).

### 2.1 Nós do Grafo

| Nó | Agente | Responsabilidade | Arquivo |
|----|--------|-----------------|---------|
| `intent_analyzer` | `IntentAnalyzerAgent` | Analisa a query, identifica entidades, ação principal, filtros, campos necessários | `src/agents/intent_analyzer.py` |
| `api_planner` | `APIPlannerAgent` | Cria plano de execução com steps sequenciais, cada um mapeando para uma API | `src/agents/api_planner.py` |
| `api_executor` | `APIExecutorAgent` | Executa chamadas REST ao ATS API seguindo o plano | `src/agents/api_executor.py` |
| `plan_validator` | `PlanValidatorAgent` | Valida resultados — pode solicitar re-planejamento se dados insuficientes | `src/agents/plan_validator.py` |
| `data_processor` | `DataProcessorAgent` | Processa e formata dados brutos das APIs | `src/agents/data_processor.py` |
| `answer_formatter` | `AnswerFormatterAgent` | Formata resposta final usando taxonomia de 11 tipos | `src/agents/answer_formatter.py` |

### 2.2 Fluxo de Execução

```
START
  │
  ▼
[intent_analyzer] ──── error? ──── END
  │ continue
  ▼
[api_planner] ──── error? ──── END
  │ continue
  ▼
[api_executor] ──── needs_confirmation? ──── END (aguarda confirmação do usuário)
  │ continue         │ error? ──── END
  ▼
[plan_validator] ──── replan? ──── [api_planner] (loop)
  │ continue         │ abort? ──── [answer_formatter]
  ▼
[data_processor] ──── error? ──── END
  │ continue
  ▼
[answer_formatter] ──── END
```

### 2.3 Estado Compartilhado (`QueryState`)

Definido em `src/models/state.py`:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `question` | `str` | Query original do usuário |
| `intent` | `dict` | Intent parsed: entities, action, filters, fields |
| `api_plan` | `list[dict]` | Steps de execução planejados |
| `api_results` | `dict` | Resultados das chamadas API |
| `processed_data` | `dict` | Dados processados e formatados |
| `final_answer` | `str` | Resposta final em linguagem natural |
| `error` | `str` | Erro se houver |
| `user_confirmation` | `dict` | Confirmação do usuário para ações destrutivas |

### 2.4 Taxonomia de Respostas (11 tipos)

| Tipo | Quando Usar |
|------|-------------|
| `ACTION_SUCCESS` | Ação executada com sucesso (create/update/delete) |
| `ACTION_FAILED` | Ação falhou |
| `COUNT` | Contagem ("quantos candidatos?") |
| `AGGREGATION` | Médias, somas, distribuições |
| `COMPARISON` | Comparação entre entidades |
| `NOT_FOUND` | 0 resultados |
| `ENTITY_DETAIL` | 1 resultado detalhado |
| `ENTITY_LIST` | 2-15 resultados em lista |
| `DISAMBIGUATION` | Múltiplos resultados quando 1 era esperado |
| `ERROR` | Erro formatado para o usuário |
| `CONVERSATIONAL` | Resposta conversacional |

---

## 3. recruiter_agent_v5 — Sistema Multi-Domínio

### 3.1 Registro de Domínios

Domínios são registrados via decorator `@register_domain` em `src/domains/registry.py`.

### 3.2 Classe Base (`DomainPrompt`)

Definida em `src/domains/base.py`:

```
DomainPrompt (ABC)
├── domain_id: str          — identificador único
├── domain_name: str        — nome legível
├── description: str        — descrição para o router
├── get_allowed_actions()   — lista de ações disponíveis
├── get_system_prompt()     — system prompt para o LLM
├── process_intent()        — classifica intent dentro do domínio
├── execute_action()        — executa a ação identificada
└── format_response()       — formata resposta do domínio
```

### 3.3 Estruturas de Dados Compartilhadas

| Classe | Descrição |
|--------|-----------|
| `DomainAction` | Define uma ação: id, nome, descrição, tipo (QUERY/AGGREGATE/ANALYZE/ACTION), exemplos |
| `DomainContext` | Contexto da sessão: domain_id, dados atuais, metadata, IDs selecionados, auth_token, api_calls_history |
| `DomainResponse` | Resposta: success, message, data, suggestions, needs_confirmation, needs_clarification |
| `APICallRecord` | Registro de chamada API: endpoint, method, params, duration_ms, status_code |
| `ActionType` | Enum: QUERY, AGGREGATE, ANALYZE, ACTION |

---

## 4. recruiter_agent_v5 — Comunicação e Integração

### 4.1 Comunicação com ATS API

```
Domínio → api_client.py → HTTP REST → ats_api (Rails) → PostgreSQL
```

Autenticação: JWT token passado via `DomainContext.auth_token`.

### 4.2 Comunicação com Frontend

| Mecanismo | Uso | Implementação |
|-----------|-----|--------------|
| **RabbitMQ** | Assíncrono — queries longas, batch operations | `BaseDispatcher` + Celery workers |
| **REST API** | Síncrono — queries simples, streaming | `src/api.py` (FastAPI) |

### 4.3 Callbacks para Rails

O `send_to_rails_callback` envia respostas de volta ao Rails via HTTP POST, que propaga via ActionCable/WebSocket ao frontend.

---

## 5. recruiter_agent_v5 — Evaluation Graph (Sub-sistema)

O domínio `evaluation` tem seu próprio LangGraph independente para avaliação de candidatos em entrevistas.

### 5.1 Fluxo

```
[classify_input] ─── answer? ─── [evaluate] ─── [decide_flow] ─── [craft_message] ─── END
       │                                              │
       └── not answer? ──────────── [decide_flow] ────┘
```

### 5.2 Nós

| Nó | Função |
|----|--------|
| `classify_input` | Classifica input do candidato: answer, question, off_topic, unclear, not_interested |
| `evaluate` | Avalia resposta com rubrica: relevância (30%), profundidade (30%), clareza (20%), exemplos (20%) |
| `decide_flow` | Decide próximo passo: continuar, fazer follow-up, encerrar |
| `craft_message` | Gera mensagem para o candidato com persona configurável |

---

## 6. recruiter_agent_v5 — Autonomous Agent (ReAct)

O domínio `autonomous` implementa um agente ReAct universal com acesso a ~73 ferramentas que cobrem toda a API do ATS.

```
UniversalReActAgent
├── Tools (~73 ferramentas)
│   ├── applies.py     — busca, pipeline, scoring, bulk
│   ├── candidates.py  — CRUD, busca, perfis
│   ├── jobs.py        — CRUD, publicação, templates
│   ├── evaluations.py — avaliações, rubricas
│   ├── sourcing.py    — sourcing externo
│   ├── scheduling.py  — agendamentos
│   ├── organization.py — departamentos, estrutura
│   ├── macros.py      — playbooks compostos
│   └── file_system.py — export, relatórios
├── Playbooks (YAML)
│   ├── diagnostico_vaga.yaml
│   ├── panorama_vagas.yaml
│   ├── sourcing_completo.yaml
│   ├── triagem_vaga.yaml
│   └── weekly_review.yaml
└── Context Builder
    └── Resolve referências UI (viewing_entities)
```

---

## 7. lia-agent-system — Arquitetura Geral

```
┌──────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js 15)                           │
│  WebSocket (AsyncJobProgress) · API Proxy /backend-proxy             │
│  Admin: /admin/compliance/guardrails, /admin/monitoring/agents       │
└────────────────┬─────────────────────────────┬───────────────────────┘
                 │ HTTP/REST sync               │ WebSocket /ws/chat/{session_id}
                 ▼                             ▼
┌───────────────────────┐   ┌──────────────────────────────────────────┐
│   API REST síncrona   │   │  WebSocket agent_chat_ws.py              │
│   /api/v1/*           │   │  JWT + session + WS dispatch             │
│   362+ endpoints      │   └──────────────────────────────────────────┘
└────────┬──────────────┘                      │
         ▼                                     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                ORCHESTRATOR (6-Tier CascadedRouter)                   │
│   app/orchestrator/orchestrator.py                                    │
│   app/orchestrator/cascaded_router.py                                 │
│                                                                        │
│   Tier 0: MemoryResolver — pronomes/referências de contexto           │
│   Tier 1: LRU in-process — hash MD5 em memória local (O(1))          │
│   Tier 2: Redis hash cache — distribuído, compartilhado               │
│   Tier 3: VectorSemanticCache — pgvector, cosine >= 0.92              │
│   Tier 4: FastRouter — regex/keyword (O(n) patterns)                  │
│       app/orchestrator/fast_router.py                                 │
│       ROUTER_FAST_CONFIDENCE_THRESHOLD = 0.7                          │
│   Tier 5: LLM Cascade — Haiku→Sonnet→Opus (caro)                     │
│       app/orchestrator/intent_router.py                               │
│   Fallback: clarification_needed — pergunta ao usuário                │
└──────────────────────────────┬────────────────────────────────────────┘
                               │ Roteia para:
        ┌──────────────────────┼───────────────────────────┐
        │                      │                           │
        ▼                      ▼                           ▼
┌──────────────────┐   ┌──────────────────────┐   ┌──────────────────┐
│ GRAPH AGENTS (3) │   │  REACT AGENTS (11)   │   │   REST DIRECT    │
│  (previsível)    │   │  (imprevisível)      │   │   (CRUD)         │
│                  │   │                      │   │                   │
│ • JobWizardGraph │   │ via ReactAgentRegistry│   │ • Criar/editar   │
│   6 nós, criação │   │ (11 registrados) +   │   │   registros      │
│   de vagas       │   │ PipelineTransition   │   │ • CRUD candidatos│
│                  │   │ (invocação direta)   │   │                   │
│ • WSIInterview   │   │ + PolicySetupAgent   │   │                   │
│   Graph          │   │ (LLM direto)         │   │                   │
│   ~9 estágios    │   │                      │   │                   │
│                  │   │                      │   │                   │
│ • InterviewGraph │   │                      │   │                   │
│   6 nós, agenda- │   │                      │   │                   │
│   mento          │   │                      │   │                   │
└──────────────────┘   └──────────┬───────────┘   └──────────────────┘
                                  │
                   ┌──────────────▼──────────────────────────────────┐
                   │           SHARED INFRASTRUCTURE                 │
                   │                                                  │
                   │  LLMService (Gemini em produção; cascade          │
                   │  Haiku→Sonnet→Opus no código, não ativo)        │
                   │    app/services/llm.py                          │
                   │    Cascade: Haiku→Sonnet→Opus (thresholds       │
                   │    0.80→0.70→0.60)                              │
                   │                                                  │
                   │  EnhancedAgentMixin                             │
                   │    Memory (working + long-term) + Autonomy      │
                   │    + Learning Extractor + Tool categories       │
                   │                                                  │
                   │  ReActLoop (react_loop.py)                      │
                   │    max_iterations=5, max_tool_calls=3           │
                   │    duplicate_threshold=2                        │
                   │                                                  │
                   │  GuardrailRepository (3-tier)                   │
                   │    global → tenant → domain                     │
                   │                                                  │
                   │  FairnessGuard (3 camadas)                      │
                   │    Regex ~40 padrões → léxico implícito → LLM   │
                   │                                                  │
                   │  ReActObserver (Observabilidade)                 │
                   │    company_id + user_id + tool timing           │
                   │    LangSmith @traceable em cada iteração        │
                   └─────────────────────────────────────────────────┘
                                        │
                   ┌────────────────────▼──────────────────────────────┐
                   │              ASYNC LAYER (Celery 5.4)             │
                   │                                                    │
                   │  app/core/celery_app.py — broker=REDIS_URL        │
                   │  app/jobs/celery_tasks.py — 27 tasks:             │
                   │    7 agent execute + 2 async process + 3 legacy   │
                   │    2 compliance + 2 ML + 2 RAG + 3 comunicação   │
                   │    6 manutenção (drift, memory, routing, etc.)   │
                   │  Beat: drift-run-batch-daily (06h Brasília)       │
                   └───────────────────────────────────────────────────┘
```

### 7.1 Domínio ↔ Roteamento do Orchestrador

```python
# app/orchestrator/cascaded_router.py — AGENT_TYPE_TO_DOMAIN
AGENT_TYPE_TO_DOMAIN = {
    "job_planner":         "job_management",
    "job_intake":          "job_management",
    "sourcing":            "sourcing",
    "cv_screening":        "cv_screening",
    "screening":           "cv_screening",
    "wsi_evaluator":       "cv_screening",
    "interviewer":         "interview_scheduling",
    "scheduling":          "interview_scheduling",
    "analyst_feedback":    "analytics",
    "analytics":           "analytics",
    "communication":       "communication",
    "ats_integrator":      "ats_integration",
    "recruiter_assistant": "recruiter_assistant",
    "task_planner":        "automation",
    # Kanban subagents (Z1-01)
    "kanban_search":       "kanban_search",
    "kanban_insight":      "kanban_insight",
    "kanban_action":       "kanban_action",
    # Pipeline subagents (Z1-02)
    "pipeline_context":    "pipeline_context",
    "pipeline_decision":   "pipeline_decision",
    "pipeline_action":     "pipeline_action",
    # Sourcing subagents (Z2-02)
    "sourcing_planner":    "sourcing_planner",
    "sourcing_search":     "sourcing_search",
    "sourcing_enrich":     "sourcing_enrich",
    "sourcing_engagement": "sourcing_engagement",
}
```

### 7.2 Orchestrator — Fases de Processamento

O orchestrator processa mensagens em 3 fases antes de invocar o router:

| Fase | Componente | O que faz |
|------|-----------|-----------|
| Phase 0 | `PendingAction` | HITL multi-turn — resolve ações pendentes de confirmação do recrutador |
| Phase 1 | `ActionExecutor` | Intents fechadas — ações diretas sem precisar de roteamento de domínio |
| Phase 2 | `CascadedRouter` | Roteamento 6-tier (memory → in-process → redis → vector → fast → LLM + clarification) |

### 7.3 CascadedRouter — 6 Tiers (Detalhado)

Arquivo: `app/orchestrator/cascaded_router.py`

| Tier | Nome | Custo | O que faz |
|:----:|------|:-----:|-----------|
| 0 | MemoryResolver | Free | Resolve pronomes/referências de contexto ("ele", "essa vaga") |
| 1 | LRU in-process | Free | Hash MD5 da mensagem → cache em memória local (O(1)) |
| 2 | Redis hash cache | Free | Cache distribuído, compartilhado entre workers |
| 3 | VectorSemanticCache | Baixo | pgvector, cosine similarity >= 0.92 |
| 4 | FastRouter | Baixo | regex/keyword patterns (O(n)), threshold confiança >= 0.7 |
| 5 | LLM Cascade | Alto | Haiku→Sonnet→Opus via `generate_with_cascade()` |
| — | Clarification | — | Pergunta ao usuário quando tudo falha (fallback final) |

### 7.4 PolicyEngine (Limites por Plano)

```
app/orchestrator/policy_engine.py
Planos: Starter / Pro / Enterprise
Limita: tokens mensais, agentes disponíveis, automações
PLAN_LIMITS_ENFORCE=true
```

---

## 8. lia-agent-system — 3 LangGraph StateGraphs

### 8.1 JobWizardGraph

| Campo | Valor |
|-------|-------|
| **Arquivo** | `app/domains/job_management/agents/job_wizard_graph.py` |
| **Nós** | 6: intent_classifier → field_extractor → tool_router → tool_executor → response_generator → stage_transition |
| **Estado** | `JobWizardState`: company_id, user_id, session_id, messages, wizard_stage (WizardStage enum), job_data, execution_log |
| **MAX_ITERATIONS** | 10 |
| **HITL** | `interrupt_before=["stage_transition"]` |
| **Checkpoints** | `checkpoint_service.py` — save/restore/delete para retomar após desconexão |
| **Ephemeral fields** | `user_message`, `session_id`, `execution_id` (excluídos do merge de checkpoint) |

**WizardIntent (8 intenções):** CREATE_JOB, EDIT_JOB, REVIEW_JOB, SAVE_JOB, CANCEL, CLARIFY, CONFIRM, GENERAL_QUERY

**6 Estágios do Wizard:**

| Stage | Descrição |
|-------|-----------|
| `input-evaluation` | Avalia input inicial, valida campos básicos |
| `jd-enrichment` | Enriquece descrição da vaga com sugestões de IA |
| `salary` | Pesquisa e recomenda benchmarks salariais |
| `competencies` | Sugere competências técnicas e comportamentais |
| `wsi-questions` | Gera perguntas de triagem WSI |
| `review-publish` | Revisão final, validação e publicação |

### 8.2 WSIInterviewGraph

| Campo | Valor |
|-------|-------|
| **Arquivo** | `app/domains/cv_screening/agents/wsi_interview_graph.py` |
| **Estágios (WSIInterviewStage enum)** | 10: INIT → LOAD_CONTEXT → GENERATE_QUESTION → AWAIT_RESPONSE → VALIDATE_RESPONSE → SCORE_RESPONSE → ADVANCE → GENERATE_FEEDBACK → COMPLETE \| ERROR |
| **Estado (WSIInterviewState @dataclass)** | `session_id`, `company_id`, `candidate_id`, `job_id`, `interview_level` ("quick"\|"standard"\|"full"), `job_requirements`, `candidate_profile`, `question_blocks: List[WSIQuestionBlock]`, `current_question_index`, `responses: List[WSIResponseRecord]`, `current_question`, `awaiting_response`, `technical_score`, `behavioral_score`, `situational_score`, `wsi_final_score`, `recommendation` ("aprovado"\|"aguardando"\|"reprovado"), `stage`, `execution_log`, `started_at`, `completed_at`, `error` |
| **WSIQuestionBlock** | `block_id`, `block_type` ("technical"\|"behavioral"\|"situational"), `question`, `competency`, `bloom_level` (1-6), `dreyfus_level` (1-5), `big_five_trait`, `max_score` (10.0), `trait_weight` (1.0) |
| **HITL** | `interrupt_before=["lg_generate_feedback"]` |
| **Scoring** | Determinístico via `wsi_deterministic_scorer.py` — substituiu AvaliadorWSIAgent (zero latência, zero custo LLM) |
| **Invocação** | Celery: `agents.wsi_interview.start` — sessões longas (30–120 min) via WebSocket |
| **Compliance** | BCB 498, SOX — logs auditáveis node_start/node_end/node_error com session_id e elapsed_ms |

### 8.3 InterviewGraph

| Campo | Valor |
|-------|-------|
| **Arquivo** | `app/domains/interview_scheduling/agents/interview_graph.py` |
| **Nós** | 6: interview_state_loader → interview_details_collector → interview_router → interview_validator → interview_scheduler_executor → interview_response_planner |
| **Estado** | `InterviewSchedulingState`: session_id, company_id, user_id, candidate_id, job_id, interview_type, scheduled_at, location/meeting_link, workflow_data, interview_ready_for_scheduling |
| **MAX_ITERATIONS** | 8 (proteção contra loop infinito de coleta) |

**Fluxo condicional:**
```
LOADER → COLLECTOR → router condicional
                         ↓ campos pendentes → COLLECTOR (loop até MAX_ITERATIONS=8)
                         ↓ campos completos → VALIDATOR
VALIDATOR ──── pronto ──→ EXECUTOR → RESPONSE → END
         ──── inválido ─→ RESPONSE → END  (pede campos faltantes ao usuário)
```

**Substituições:** SchedulingAgent → REMOVIDO → InterviewGraph. EntrevistadorAgent → REMOVIDO → InterviewGraph.

### 8.4 ADR: Graph vs ReAct

Arquivo: `docs/adr/002-graph-vs-react.md` (raiz do repo lia-agent-system)

| Critério | Graph (LangGraph) | ReAct Loop |
|----------|-------------------|-----------|
| **Quando usar** | Fluxo previsível, etapas fixas, auditável | Fluxo imprevisível, raciocínio livre |
| **HITL** | `interrupt_before` nativo | Manual via PendingAction |
| **Compliance** | Checkpoints rastreáveis (BCB 498, SOX) | Logs por iteração |
| **Exemplos** | JobWizard, WSI Interview, Interview Scheduling | Sourcing, Kanban, Talent, Pipeline |

---

## 9. lia-agent-system — 13 Agentes de Domínio

### 9.1 Padrão de 4 Arquivos (Obrigatório)

```
app/domains/<domain>/agents/
├── <prefix>_react_agent.py      ← Agente (herda LangGraphReActBase + EnhancedAgentMixin)
├── <prefix>_tool_registry.py    ← Ferramentas disponíveis
├── <prefix>_system_prompt.py    ← System prompt contextualizado por stage
└── <prefix>_stage_context.py    ← Contexto e validação por estágio
```

### 9.2 11 Agentes Registrados no ReactAgentRegistry

Contagens verificadas por `ToolDefinition(` count em cada `*_tool_registry.py`.

| # | Agente | Registry key | Tools | max_iterations |
|---|--------|-------------|:-----:|:--------------:|
| 1 | WizardReActAgent | `wizard` | 10 | 5 |
| 2 | PipelineReActAgent | `pipeline` | 15 | 5 |
| 3 | SourcingReActAgent | `sourcing` | 15 | 5 |
| 4 | TalentReActAgent | `talent` | 13 | 5 |
| 5 | JobsMgmtReActAgent | `jobs_management` | 14 | 5 |
| 6 | KanbanReActAgent | `kanban` | 22 | 5 |
| 7 | PolicyReActAgent | `policy` | 13 | 5 |
| 8 | AutomationReActAgent | `automation` | 6 | 6 |
| 9 | AnalyticsReActAgent | `analytics` | 6 | 6 |
| 10 | CommunicationReActAgent | `communication` | 5 | 6 |
| 11 | ATSIntegrationReActAgent | `ats_integration` | 5 | 6 |

### 9.3 Agente LangGraph ReAct de Invocação Direta

| # | Agente | Invocação | Tools |
|---|--------|-----------|:-----:|
| 12 | PipelineTransitionAgent | `POST /api/v1/pipeline/interpret-context` | 20 |

### 9.4 Agente LLM Direto (não ReAct)

| # | Agente | Tipo | Descrição |
|---|--------|------|-----------|
| 13 | PolicySetupAgent | LLM direto | 19 perguntas em 5 blocos de configuração de política |

### 9.5 Onde Cada Agente Atua no Produto

| Agente | Tela / Componente |
|--------|-------------------|
| WizardReAct | Modal de chat ao criar/editar vaga (`/jobs`) |
| PipelineReAct | Prompt expandido dentro da vaga (`/jobs/[id]`) |
| SourcingReAct | Chat geral LIA (`/chat`) — busca de candidatos |
| TalentReAct | Funil de Talentos (`/candidates`) |
| JobsMgmtReAct | Kanban da Vaga + Gestão de Vagas |
| KanbanReAct | Kanban da Vaga (`/jobs/[id]`) |
| PolicyReAct | Configurações → Políticas de Contratação |
| PolicySetupAgent | Configurações → onboarding de política (19 perguntas) |
| AnalyticsReAct | Painel de Analytics |
| ATSIntegrationReAct | Configurações → Integrações ATS |
| CommunicationReAct | Multi-canal (email, WhatsApp, Teams) |
| AutomationReAct | Automação de tarefas |
| PipelineTransitionAgent | Modal de transição de status no Kanban |
| WSIInterviewGraph | Entrevista WSI (via WebSocket + HITL) |
| JobWizardGraph | Wizard step-by-step (via WebSocket + HITL) |
| InterviewGraph | Agendamento conversacional de entrevistas |

---

## 10. lia-agent-system — Infraestrutura Compartilhada

### 10.1 EnhancedAgentMixin

Arquivo: `libs/agents-core/lia_agents_core/enhanced_agent_mixin.py`

Todo agente ReAct herda deste mixin:

| Capability | Arquivo | Função |
|-----------|---------|--------|
| WorkingMemory | `working_memory.py` | Histórico da sessão atual |
| LongTermMemory | `long_term_memory.py` | Learnings persistidos entre sessões |
| MemoryIntegration | `memory_integration.py` | Combina working + long-term no prompt |
| AutonomyEngine | `autonomy_engine.py` | Decide nível de autonomia (SUPERVISED/ASSISTED/AUTONOMOUS) |
| LearningExtractor | `learning_extractor.py` | Extrai aprendizados pós-loop ReAct |
| Insight Tools | `shared/tools/insight_tools.py` | Ferramentas de insight |
| Proactive Tools | `shared/tools/proactive_tools.py` | Ferramentas proativas |
| Predictive Tools | `shared/tools/predictive_tools.py` | Ferramentas preditivas |

### 10.2 BaseAgent Interface

Arquivo: `libs/agents-core/lia_agents_core/agent_interface.py`

```python
class BaseAgent(ABC):
    @property
    @abstractmethod
    def domain_name(self) -> str: ...

    @property
    @abstractmethod
    def available_tools(self) -> List[str]: ...

    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput: ...

class AgentInput(BaseModel):
    message: str
    context: Dict[str, Any] = {}
    session_id: str
    company_id: str
    user_id: str
    conversation_history: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

class AgentOutput(BaseModel):
    message: str                              # resposta ao usuário
    actions: List[AgentAction] = []
    state_updates: Dict[str, Any] = {}
    navigation: Optional[NavigationCommand] = None
    confidence: float = 0.0
    reasoning_steps: List[str] = []
    tool_results: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    error: Optional[str] = None
```

### 10.3 ReAct Loop

**O que é:** Motor de raciocínio iterativo que executa o padrão Reason→Act→Observe até convergir ou atingir limites.

**Arquivo:** `app/shared/agents/react_loop.py`

**Como funciona:**
```
Loop (até REACT_MAX_ITERATIONS_DEFAULT = 5):
  1. REASON  — LLM analisa contexto e histórico
  2. ACT     — Executa tool chamada pelo LLM
  3. OBSERVE — Formata resultado da tool como observação
  4. DECIDE  — Continuar, tentar diferente, ou finalizar
```

**Contratos (settings em `libs/config/lia_config/config.py`):**

| Setting | Valor (código) | Descrição |
|---------|:--------------:|-----------|
| `REACT_MAX_ITERATIONS_DEFAULT` | 5 | Máximo de iterações reason→act→observe |
| `REACT_MAX_TOOL_CALLS` | 3 | Máximo de tool calls por request |
| `REACT_DUPLICATE_THRESHOLD` | 2 | Mesma ação N vezes → para |
| `REACT_OBSERVATION_MAX_CHARS` | 5000 | Trunca resultado de tool |

**Limites:** LangSmith `@traceable` em cada iteração. ReActObserver logga company_id, user_id, tool timing.

### 10.4 Memória em 3 Níveis

```
Sessão atual        → Working Memory    (StateManager, minutos/horas)
Cross-sessão        → Conversation Memory (PostgreSQL + pgvector, dias/semanas)
Permanente          → Long-Term Memory  (agent_long_term_memory, meses/anos)
                                          ↓
                      MemoryIntegration.get_enriched_context()
                      → Injetado no prompt do agente como extra_context
```

| Nível | Armazenamento | Escopo | Limite/Threshold |
|-------|--------------|--------|-----------------|
| Working Memory | StateManager (memória) | Sessão atual | Últimas N mensagens |
| Conversation Memory | PostgreSQL + pgvector Vector(768) | Cross-sessão | Similaridade mínima 0.7, max 5 mensagens |
| Long-Term Memory | `agent_long_term_memory` table | Permanente | relevance_score com decay 0.95 |

### 10.5 Compliance (Cross-cutting)

| Componente | Arquivo | Função |
|-----------|---------|--------|
| FairnessGuard | `shared/compliance/fairness_guard.py` | 3 camadas: regex (~40 padrões) → léxico implícito → LLM opt-in |
| GuardrailRepository | `shared/compliance/guardrail_repository.py` | Guardrails do banco — hierarquia global → tenant → domain |
| FactChecker | `shared/compliance/fact_checker.py` | Verifica fatos em avaliações |
| AuditService | `shared/compliance/audit_service.py` | Log de auditoria SOX |
| PII Masking | `shared/pii_masking.py` | Remove PII de logs (telefones, emails, CPFs) |
| Prompt Injection Guard | `shared/prompt_injection.py` | Detecta tentativas de injection |

### 10.6 Observabilidade

| Componente | Função |
|-----------|--------|
| LangSmith | `@traceable` em agentes e grafos |
| Prometheus | 13+ métricas em `app/observability/metrics.py` |
| ReActObserver | Logs por iteração com company_id, user_id, tool timing |
| Drift Detection | 4 triggers: score, aprovação, custo, latência P95 |
| AgentQualityEvaluator | Sampling 10% das interações |
| AgentHealthAlertService | 3 falhas → WARNING, 5 → CRITICAL (Bell + Teams) |

---

## 11. Fairness Guard (Ambos Repositórios)

### 11.1 recruiter_agent_v5 (`src/domains/jobs/fairness.py`)

Filtros bloqueados: gender, genero, sexo, age, idade, birth_date, race, raca, ethnicity, etnia, marital, estado_civil, religion

### 11.2 lia-agent-system (`app/shared/compliance/fairness_guard.py`)

| Camada | O que verifica | Quando ativa |
|--------|---------------|-------------|
| Camada 1 | Regex sobre 40+ padrões explícitos (gênero, idade, raça, religião, estado civil) | Sempre |
| Camada 2 | Léxico de viés implícito (`IMPLICIT_BIAS_TERMS`) | Sempre |
| Camada 3 | Análise semântica por LLM (detecta viés sutil) — Gemini em produção | Opt-in via `FAIRNESS_LAYER3_ENABLED` (+2s latência) |

**Agentes que usam FairnessGuard:**

| Agente | Onde aplica |
|--------|------------|
| Wizard | Requisitos, descrição, perguntas de triagem |
| Talent | Critérios de busca |
| Kanban | Justificativas de rejeição |
| JobsManagement | Justificativas de ações sobre vagas |
| PipelineTransition | Motivos de transição |
| Policy | Políticas de contratação |
| CandidateReport | Seções 3, 4 e 6 do parecer |

---

## 12. Deploy Topology

| Componente | Deploy | Porta |
|-----------|--------|-------|
| ats_api (Rails) | Cloud (GCP) | 8080 |
| ats_front (Nuxt) | Cloud | 3000 |
| recruiter_agent_v5 | Cloud (GCP) + Workers | 8000 |
| lia-agent-system | Replit | 8000 |
| RabbitMQ | CloudAMQP | 5672 |
| PostgreSQL | Neon (Cloud) | 5432 |
| Redis | Cloud | 6379 |
| LangSmith | SaaS | — |

---

## 13. Determinístico vs Não-Determinístico

| Componente | Tipo | Por quê |
|-----------|------|---------|
| T1/T2 Router (hash, regex) | Determinístico | Routing não pode variar |
| FairnessGuard L1/L2 | Determinístico | Compliance binário, reproduzível |
| Four-Fifths Rule | Determinístico | Fórmula matemática |
| Drift Detection | Determinístico | Comparação com thresholds fixos |
| WSI Deterministic Scorer | Determinístico | Funções puras sem LLM |
| Cache de avaliação (hash) | Determinístico | Mesmo candidato = mesmo resultado |
| Agentes ReAct (reasoning) | Não-determinístico | Raciocínio livre do LLM |
| Avaliação WSI por rubrica (recruiter_agent_v5) | Não-determinístico | LLM julga qualidade textual — scoring numérico WSI usa Deterministic Scorer acima |
| FairnessGuard L3 | Não-determinístico | LLM detecta viés sutil |
| Geração de feedback | Não-determinístico | LLM redige texto personalizado |

**Regra de ouro:** IA no meio, extremidades (entrada/saída) sempre determinísticas.

---

## Referências

| Arquivo | Localização |
|---------|-------------|
| Workflow Graph | `recruiter_agent_v5/src/workflow/graph.py` |
| Base Domain | `recruiter_agent_v5/src/domains/base.py` |
| LLM Factory | `recruiter_agent_v5/src/utils/llm_factory.py` |
| Orchestrator | `lia-agent-system/app/orchestrator/orchestrator.py` |
| CascadedRouter | `lia-agent-system/app/orchestrator/cascaded_router.py` |
| LLMService | `lia-agent-system/app/services/llm.py` |
| ReactAgentRegistry | `lia-agent-system/libs/agents-core/lia_agents_core/react_agent_registry.py` |
| EnhancedAgentMixin | `lia-agent-system/libs/agents-core/lia_agents_core/enhanced_agent_mixin.py` |
| ReActLoop | `lia-agent-system/app/shared/agents/react_loop.py` |
| FairnessGuard | `lia-agent-system/app/shared/compliance/fairness_guard.py` |
| JobWizardGraph | `lia-agent-system/app/domains/job_management/agents/job_wizard_graph.py` |
| WSIInterviewGraph | `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` |
| InterviewGraph | `lia-agent-system/app/domains/interview_scheduling/agents/interview_graph.py` |
| ADR Graph vs ReAct | `docs/adr/002-graph-vs-react.md` (raiz do repo lia-agent-system) |
