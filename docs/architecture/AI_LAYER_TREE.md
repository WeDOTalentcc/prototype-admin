# LIA AI Layer — Architecture Tree

> **Fonte-da-verdade = código.** Este documento é gerado por auditoria exaustiva do código em `lia-agent-system/app/`. Onde houver divergência entre este doc e o código, o código vence. Última auditoria: 2026-06-09.

---

## Índice

1. [Visão Geral — Árvore de Componentes](#1-visão-geral--árvore-de-componentes)
2. [Entry Points](#2-entry-points)
3. [Main Orchestrator — Pipeline Unificado](#3-main-orchestrator--pipeline-unificado)
4. [Routing Layer — CascadedRouter (8 Tiers)](#4-routing-layer--cascadedrouter-8-tiers)
5. [16 Canonical ReActAgents](#5-16-canonical-reactagents)
6. [Sub-Agentes Especializados](#6-sub-agentes-especializados)
7. [LangGraph State Machines](#7-langgraph-state-machines)
8. [Tools Layer (~260 tools)](#8-tools-layer-260-tools)
9. [LLM Layer — Factory, Bootstrap & Modelos](#9-llm-layer--factory-bootstrap--modelos)
10. [Messaging & AgentBus](#10-messaging--agentbus)
11. [Plan & Execute (LIA_V2_USE_PLAN_SERVICE)](#11-plan--execute-lia_v2_use_plan_service)
12. [Compliance Layer — C3b, FairnessGuard, FactChecker, Audit](#12-compliance-layer--c3b-fairnessguard-factchecker-audit)
13. [WSI Screening Pipeline](#13-wsi-screening-pipeline)
14. [Voice Architecture](#14-voice-architecture)
15. [Knowledge Base & RAG](#15-knowledge-base--rag)
16. [Tenant Context System](#16-tenant-context-system)
17. [Agent Studio — Tier 7 (Custom Agents)](#17-agent-studio--tier-7-custom-agents)
18. [Feature Flags de Comportamento AI](#18-feature-flags-de-comportamento-ai)
19. [Observabilidade & Monitoramento](#19-observabilidade--monitoramento)
20. [Domain Catalog — Resumo](#20-domain-catalog--resumo)

---

## 1. Visão Geral — Árvore de Componentes

```
LIA AI Layer
│
├── ENTRY POINTS
│   ├── WebSocket / SSE  (orchestrator_routes.py, orchestrated_talent_chat.py)
│   ├── REST API         (api/v1/*, api/public/*)
│   ├── Teams Bot        (communication/teams_orchestrator_bridge.py)
│   └── WhatsApp Webhook (whatsapp_agent_plugin.py)
│
├── MAIN ORCHESTRATOR  (orchestrator/execution/main_orchestrator.py — 3 286 LOC)
│   ├── Phase 0 — PendingAction         (multi-turn / confirmação)
│   ├── Phase 1 — ActionExecutor        (ações fechadas por intent)
│   ├── Phase 1.3 — Plan & Execute      (LIA_V2_USE_PLAN_SERVICE — flag OFF default)
│   └── Phase 2 — CascadedRouter ──────► DomainWorkflow ──────► ReAct Agent
│
├── ROUTING LAYER  (orchestrator/routing/)
│   ├── Tier 0  MemoryResolver       (pronomes / referências de contexto)
│   ├── Tier 1  LRU in-process       (MD5 hash, O(1))
│   ├── Tier 2  Redis hash cache     (distribuído, exato)
│   ├── Tier 3  VectorSemanticCache  (pgvector cosine ≥ 0.85)
│   ├── Tier 4  FastRouter           (regex/keyword, ~80% hits)
│   ├── Tier 5  LLM Cascade          (Gemini Flash → Claude Sonnet → Claude Opus)
│   ├── Tier 6  REMOVIDO             (Sprint 12.3-B — era AutonomousReActAgent)
│   └── Fallback clarification_needed
│
├── 16 CANONICAL ReActAgents  (todos: TenantAwareAgentMixin + LangGraphReActBase + EnhancedAgentMixin)
│   ├── AnalyticsReActAgent         (domain: analytics)
│   ├── ATSIntegrationReActAgent    (domain: ats_integration)
│   ├── AutomationReActAgent        (domain: automation)
│   ├── CandidateSelfServiceAgent   (domain: candidate_self_service)
│   ├── CommunicationReActAgent     (domain: communication)
│   ├── CompanySettingsReActAgent   (domain: company_settings)
│   ├── PipelineReActAgent          (domain: cv_screening)
│   ├── PolicyReActAgent            (domain: hiring_policy)
│   ├── WizardReActAgent            (domain: job_management, tenant_strict_override=True)
│   ├── PipelineTransitionAgent     (domain: pipeline_transition)
│   ├── JobsManagementReActAgent    (domain: recruiter_assistant)
│   ├── KanbanReActAgent            (domain: recruiter_assistant)
│   ├── SourcingReActAgent          (domain: sourcing)
│   ├── TalentFunnelReActAgent      (domain: recruiter_assistant)
│   ├── TalentPoolReActAgent        (domain: talent_pool)
│   └── RecruiterCopilotReActAgent  (domain: recruiter_assistant)
│
├── SUB-AGENTES ESPECIALIZADOS  (herdam do ReActAgent do domínio)
│   ├── Kanban  — KanbanActionAgent, KanbanInsightAgent, KanbanSearchAgent
│   ├── Sourcing — SourcingPlannerAgent, SourcingSearchAgent, SourcingEnrichAgent,
│   │              SourcingEngagementAgent, DiversitySourcingAgent, GithubSourcingAgent,
│   │              StackOverflowSourcingAgent, PassivePipelineAgent, ReferralAgent,
│   │              NurtureSequenceAgent
│   └── Pipeline — PipelineActionAgent, PipelineContextAgent, PipelineDecisionAgent
│
├── LANGGRAPH STATE MACHINES  (StateGraph nativo + PostgresSaver checkpoint)
│   ├── Job Creation Wizard Graph  (job_creation/graph.py — 15 nós, 4 HITL gates)
│   ├── WSI Interview Graph        (cv_screening/agents/wsi_interview_graph.py)
│   └── Interview Scheduling Graph (interview_scheduling/agents/interview_graph.py)
│
├── TOOLS LAYER  (~260 tools únicas, 322 ToolDefinition() instantiações, 33 registries)
│
├── LLM LAYER
│   ├── llm_bootstrap.py   (monkey-patch Anthropic/OpenAI/GenAI SDK no startup)
│   ├── LLMProviderFactory (registro global de classes de provider)
│   ├── ProviderContainer  (DI container por tenant com fallback chain)
│   └── get_provider_for_tenant()  (entry point canônico)
│
├── MESSAGING & AGENT BUS
│   ├── AgentBus          (Redis Pub/Sub — fire-and-forget + request-reply/crew)
│   └── BrokerInterface   (Redis | RabbitMQ | PubSub stub)
│
├── COMPLIANCE LAYER
│   ├── C3b Layer         (PII strip + FairnessGuard pré | FactChecker + Audit pós)
│   ├── FairnessGuard     (20+ categorias discriminatórias — hard block + soft warn)
│   ├── FactChecker       (valida respostas LLM contra hallucinations)
│   └── BiasAuditService  (audit trail unificado de bias detection)
│
├── WSI SCREENING  (Blocos 0-5: Abordagem → Técnico → Comportamental → Encerramento)
│
├── VOICE ARCHITECTURE
│   ├── Primary  — GeminiLiveAudioService (VoIP browser, ~$0.065/15min)
│   └── Fallback — Twilio + OpenAI Whisper/TTS (PSTN, ~$0.41/15min)
│
├── KNOWLEDGE BASE & RAG
│   ├── RAGPipelineService (hybrid: pgvector cosine + tsvector BM25, alpha blending)
│   ├── HybridSearchService (vagas + candidatos)
│   └── DomainEmbeddingService (embeddings por domínio)
│
└── AGENT STUDIO — TIER 7
    └── CustomAgentRuntime (mesma base TenantAwareAgentMixin + LangGraphReActBase)
```

---

## 2. Entry Points

| Canal | Arquivo | Protocolo |
|-------|---------|-----------|
| Chat principal (recruiter) | `app/api/orchestrator_routes.py` | WebSocket / SSE |
| Chat de vagas | `app/api/v1/orchestrated_job_chat.py` | WebSocket / SSE |
| Chat de talentos | `app/api/v1/orchestrated_talent_chat.py` | WebSocket / SSE |
| Wizard smart | `app/api/v1/wizard_smart_orchestrator.py` | REST POST |
| Pipeline | `app/api/v1/pipeline_orchestrator.py` | REST |
| Sourcing | `app/api/v1/sourcing_orchestrator.py` | REST |
| Teams Bot | `app/domains/communication/services/teams_orchestrator_bridge.py` | Bot Framework |
| WhatsApp | `app/domains/agent_studio/whatsapp_agent_plugin.py` | Webhook |
| Candidate self-service | `app/api/public/*` | REST público |

**Contratos SSE:** tokens incrementais chegam via `ChatResponse` (Pydantic BaseModel, 3 286 LOC em `main_orchestrator.py`). Campos-chave: `content`, `agent_used`, `intent_detected`, `structured_data`, `actions`, `needs_confirmation`, `fairness_warnings`, `response_blocks`, `ui_action`.

---

## 3. Main Orchestrator — Pipeline Unificado

**Arquivo canônico:** `app/orchestrator/execution/main_orchestrator.py` (3 286 LOC)

Este é o ponto de entrada único para **todas** as mensagens da LIA. Consolida a lógica que antes estava espalhada em `orchestrated_talent_chat.py` (500 LOC), `orchestrated_job_chat.py`, `pipeline_orchestrator.py` e `agent_chat_ws.py`.

```
mensagem do recrutador
  │
  ▼
UniversalContext  (context/context_adapter.py)
  │
  ├── Security check          (shared/robustness/security_patterns.py)
  │
  ├── FairnessGuard           (shared/compliance/fairness_guard.py)
  │   └── hard block          → resposta educativa imediata
  │   └── soft warnings       → propagados em fairness_warnings[]
  │
  ├── TenantContext enrichment (shared/services/tenant_context_service.py)
  │
  ├── Phase 0: PendingAction   (execution/pending_action.py)
  │   └── confirmação/rejeição de ação multi-turn pendente
  │
  ├── Phase 1: ActionExecutor  (action_executor/)
  │   └── ações fechadas (mover candidato, agendar, etc.) detectadas por intent
  │
  ├── Phase 1.3: Plan & Execute (flag LIA_V2_USE_PLAN_SERVICE — default OFF)
  │   └── PlanOrchestrationService → task_planner → PlanExecutor
  │
  └── Phase 2: CascadedRouter → DomainWorkflow → ReAct Agent
      └── ConversationMemory (memory/memory_resolver.py)
```

### Severity-Based Delegation (Task #811)

Antes de chegar ao Phase 2, o orquestrador avalia `_decide_agent_type_from_hints()`:

- Se intent está em `_COMPANY_SETTINGS_INTENTS` → roteia direto para `company_settings`
- Se hints têm severity `warning`/`critical` → roteia para `company_settings` (resolve o bloqueio primeiro)
- Caso contrário → fluxo normal pelo CascadedRouter

```python
# _COMPANY_SETTINGS_INTENTS (frozenset — lowercase)
{"company_settings", "configure_company", "settings_config", "hiring_policy", ...}
```

### Response Schema Unificado (`ChatResponse`)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `success` | bool | Sucesso do turn |
| `content` | str | Texto da resposta LIA |
| `agent_used` | str | Agent que processou o turn |
| `intent_detected` | str | Intent classificado (coerced para str) |
| `structured_data` | dict? | Dados estruturados para UI |
| `actions` | list | Ações sugeridas |
| `needs_confirmation` | bool | Requer confirmação do recrutador |
| `pending_action_id` | str? | ID da ação pendente multi-turn |
| `fairness_warnings` | list[str] | Avisos de fairness (soft) |
| `ui_action` | str? | Hint de navegação para o frontend |
| `ui_action_params` | dict? | Parâmetros do hint de navegação |
| `response_blocks` | list? | Blocos estruturados (cards, tabelas) |

---

## 4. Routing Layer — CascadedRouter (8 Tiers)

**Arquivo canônico:** `app/orchestrator/routing/cascaded_router.py` (1 011 LOC)

Hierarquia de resolução por **custo crescente**:

| Tier | Componente | Arquivo | Custo | Cobertura |
|------|-----------|---------|-------|-----------|
| 0 | MemoryResolver | `orchestrator/memory/memory_resolver.py` | O(1) | Pronomes/referências de contexto ("ele", "aquela vaga") |
| 1 | LRU in-process | `cascaded_router.py` | O(1) | Hash MD5 exact match — memória local |
| 2 | Redis hash cache | `cascaded_router.py` | ~1ms | Distribuído, exato, compartilhado entre workers |
| 3 | VectorSemanticCache | `memory/vector_semantic_cache.py` | ~5ms | pgvector cosine similarity ≥ 0.85 |
| 4 | FastRouter | `routing/fast_router.py` | O(n) | Regex/keyword — resolve ~80% das queries |
| 5 | LLM Cascade | `routing/llm_cascade.py` | $$ | Gemini Flash → Claude Sonnet → Claude Opus |
| 6 | ~~Autonomous~~ | REMOVIDO Sprint 12.3-B | — | Era AutonomousReActAgent; env nunca setado em prod |
| FB | clarification_needed | `cascaded_router.py` | — | Pergunta ao usuário quando tudo falha |

### RouteResult (dataclass)

```python
@dataclass
class RouteResult:
    domain_id: str
    confidence: float
    source: str                   # "lru" | "redis" | "vector" | "fast" | "llm"
    matched_pattern: str | None
    intent_details: OrchestratorIntentResult | None
    cached: bool
    needs_clarification: bool
    clarification_question: str | None
    clarification_options: list[str] | None
```

### FastRouter — Tier 4

**Arquivo:** `routing/fast_router.py` (727 LOC)

Padrões regex por domínio (YAML primário em `config/domain_routing.yaml`). Exemplos de domínios roteados:

| domain_id | Exemplos de padrão |
|-----------|-------------------|
| `wizard` | `criar.*\bvaga\b`, `\bnova\s+vaga\b`, `abrir.*\bvaga\b(?!.*\b[vV]\d{3})` |
| `job_management` | `editar?\s+\w*\s*vaga`, `atualizar?\s+\w*\s*vaga` |
| `kanban` | `kanban`, `pipeline de candidatos`, `mover candidato` |
| `analytics` | `relatório`, `dashboard`, `métricas`, `KPI` |
| `sourcing` | `buscar candidatos`, `prospectar`, `talent hunt` |
| `communication` | `enviar.*email`, `WhatsApp`, `agendar mensagem` |
| `cv_screening` | `triagem`, `WSI`, `avaliar currículo`, `score` |
| `pipeline_transition` | `avançar candidato`, `mover para`, `próxima etapa` |

Também mantém um `KeywordIntentMatcher` shadow (telemetria) paralelo ao regex.

### LLM Cascade — Tier 5

**Arquivo:** `routing/llm_cascade.py`

```
Confiança baixa no Tier 4
  ├── Tier 5a: Gemini Flash     (fast/cheap — threshold LLM_CASCADE_FAST_THRESHOLD)
  ├── Tier 5b: Claude Sonnet    (pro/medium — se confiança < threshold 5a)
  └── Tier 5c: Claude Opus      (ultra — se confiança < LLM_CASCADE_MID_THRESHOLD)
```

A/B testing registrado via `PromptExperiment` no `cascaded_router_system_prompt.yaml`.

---

## 5. 16 Canonical ReActAgents

**Sentinela:** `tests/integration/agents/test_tenant_aware_rollout_t_d.py`

> Adicionar um 17º agente canônico quebra o build se não seguir o padrão T-D.

**Base de herança comum:** `TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin`

| # | Classe | Arquivo | agent_name | domain_id | Notas |
|---|--------|---------|------------|-----------|-------|
| 1 | `AnalyticsReActAgent` | `domains/analytics/agents/analytics_react_agent.py` | `analytics_react_agent` | `analytics` | Cache TTL 90s |
| 2 | `ATSIntegrationReActAgent` | `domains/ats_integration/agents/ats_integration_react_agent.py` | `ats_integration_react_agent` | `ats_integration` | Gupy, Pandapé, Merge.dev |
| 3 | `AutomationReActAgent` | `domains/automation/agents/automation_react_agent.py` | `automation_react_agent` | `automation` | Tasks, reminders, notes |
| 4 | `CandidateSelfServiceAgent` | `domains/candidate_self_service/agents/candidate_react_agent.py` | — | `candidate_self_service` | Candidate-facing (não recruiter) |
| 5 | `CommunicationReActAgent` | `domains/communication/agents/communication_react_agent.py` | `communication_react_agent` | `communication` | Email, WhatsApp, Teams, SMS |
| 6 | `CompanySettingsReActAgent` | `domains/company_settings/agents/company_react_agent.py` | `company_react_agent` | `company_settings` | Prefill tags `[ACTION:prefill_section]` |
| 7 | `PipelineReActAgent` | `domains/cv_screening/agents/pipeline_react_agent.py` | `pipeline_react_agent` | `cv_screening` | WSI + CV scoring |
| 8 | `PolicyReActAgent` | `domains/hiring_policy/agents/policy_react_agent.py` | — | `hiring_policy` | FairnessGuard integrado |
| 9 | `WizardReActAgent` | `domains/job_management/agents/wizard_react_agent.py` | — | `job_management` | **`tenant_strict_override = True`** — nunca degrada para "sua empresa" |
| 10 | `PipelineTransitionAgent` | `domains/pipeline/agents/pipeline_transition_agent.py` | `pipeline_transition_agent` | `pipeline_transition` | Movimentação de candidatos no funil |
| 11 | `JobsManagementReActAgent` | `domains/recruiter_assistant/agents/jobs_mgmt_react_agent.py` | `jobs_mgmt_react_agent` | `recruiter_assistant` | CRUD de vagas (ver/editar/fechar) |
| 12 | `KanbanReActAgent` | `domains/recruiter_assistant/agents/kanban_react_agent.py` | `kanban_react_agent` | `recruiter_assistant` | Cache TTL 60s (insight 120s) |
| 13 | `SourcingReActAgent` | `domains/sourcing/agents/sourcing_react_agent.py` | `sourcing_react_agent` | `sourcing` | Orquestra sub-agentes de sourcing |
| 14 | `TalentFunnelReActAgent` | `domains/recruiter_assistant/agents/talent_funnel_react_agent.py` | `talent_funnel_react_agent` | `recruiter_assistant` | Funil de Talentos (busca multi-fonte) |
| 15 | `TalentPoolReActAgent` | `domains/talent_pool/agents/talent_pool_agent.py` | `talent_pool_react_agent` | `talent_pool` | Gestão de talent pools |
| 16 | `RecruiterCopilotReActAgent` | `domains/recruiter_assistant/agents/recruiter_copilot_react_agent.py` | `recruiter_copilot_react_agent` | `recruiter_assistant` | Copiloto geral (fallback domain) |

### Cache de Domínios (Main Orchestrator)

```python
_CACHEABLE_DOMAINS = {
    "analytics", "kanban_search", "kanban_insight",
    "recruiter_assistant", "pipeline_context",
}
_CACHE_TTL_BY_DOMAIN = {
    "analytics": 90, "kanban_search": 60,
    "kanban_insight": 120, "recruiter_assistant": 300, "pipeline_context": 60,
}
```

### Non-ReAct Callsites

> Para injetar snippet de tenant **fora** dos 16 agentes canônicos, usar **exclusivamente** `resolve_tenant_snippet_for_non_react(...)`. NUNCA ler `ctx["tenant_context_snippet"]` direto.
> **Sentinela:** `tests/integration/agents/test_non_react_tenant_helper_t_f.py`

---

## 6. Sub-Agentes Especializados

Sub-agentes herdam do ReActAgent do seu domínio pai e adicionam comportamento escopado.

### Kanban (herdam de `KanbanReActAgent`)

| Classe | Arquivo | Foco |
|--------|---------|------|
| `KanbanActionAgent` | `recruiter_assistant/agents/kanban_action_agent.py` | Ações mutativas no kanban (mover, atualizar) |
| `KanbanInsightAgent` | `recruiter_assistant/agents/kanban_insight_agent.py` | Análises e insights sobre candidatos |
| `KanbanSearchAgent` | `recruiter_assistant/agents/kanban_search_agent.py` | Busca e filtragem de candidatos |

### Sourcing (herdam de `SourcingReActAgent`)

| Classe | Arquivo | Canal |
|--------|---------|-------|
| `SourcingPlannerAgent` | `sourcing/agents/sourcing_planner_agent.py` | Planejamento de estratégia |
| `SourcingSearchAgent` | `sourcing/agents/sourcing_search_agent.py` | Busca em bases de dados |
| `SourcingEnrichAgent` | `sourcing/agents/sourcing_enrich_agent.py` | Enriquecimento de perfil |
| `SourcingEngagementAgent` | `sourcing/agents/sourcing_engagement_agent.py` | Engajamento de candidatos |
| `DiversitySourcingAgent` | `sourcing/agents/diversity_sourcing_agent.py` | DEI / diversidade |
| `GithubSourcingAgent` | `sourcing/agents/github_sourcing_agent.py` | GitHub |
| `StackOverflowSourcingAgent` | `sourcing/agents/stackoverflow_sourcing_agent.py` | Stack Overflow |
| `PassivePipelineAgent` | `sourcing/agents/passive_pipeline_agent.py` | Candidatos passivos |
| `ReferralAgent` | `sourcing/agents/referral_agent.py` | Indicações |
| `NurtureSequenceAgent` | `sourcing/agents/nurture_sequence_agent.py` | Nurture sequences |

### Pipeline (sub-agentes do domínio `pipeline`)

| Classe | Arquivo | Foco |
|--------|---------|------|
| `PipelineActionAgent` | `pipeline/agents/pipeline_action_agent.py` | Execução de ações no pipeline |
| `PipelineContextAgent` | `pipeline/agents/pipeline_context_agent.py` | Contexto e visualização |
| `PipelineDecisionAgent` | `pipeline/agents/pipeline_decision_agent.py` | Decisões inteligentes de movimentação |

---

## 7. LangGraph State Machines

Três grafos nativos `StateGraph` com `PostgresSaver` checkpoint para persistência de sessão.

### 7.1 Job Creation Wizard Graph

**Arquivo:** `app/domains/job_creation/graph.py`

```python
from langgraph.graph import StateGraph, END
builder = StateGraph(JobCreationState)
```

- **15 nós:** 11 funcionais + 4 gates HITL com `interrupt()` canônico
- **Continuidade de sessão:** `derive_thread_id` puro + pin handler-level
- **Classifier LLM:** ativado por `LIA_WIZARD_LLM_GATES=true` nos 4 gates
- **Orquestrador:** `job_creation/orchestrator/wizard_orchestrator.py`
- **Contrato completo:** `docs/architecture/wizard-flow.md`

```
jd_upload_node
  ├── intake_node           [HITL gate — interrompe para confirmação]
  ├── salary_benchmark_node
  ├── requirements_node     [HITL gate]
  ├── culture_fit_node
  ├── pipeline_config_node  [HITL gate]
  ├── sourcing_profile_node
  ├── approval_node         [HITL gate — aprovação final]
  ├── publish_node
  └── END
```

### 7.2 WSI Interview Graph

**Arquivo:** `app/domains/cv_screening/agents/wsi_interview_graph.py`

```python
builder = StateGraph(schema)  # _WSILangGraphState
```

- Operações: `start` (inicia sessão) e `submit` (processa resposta)
- Estado: `WSIInterviewState` com `question_blocks: list[WSIQuestionBlock]`
- Bloco de questões: `WSIQuestionBlock(block_id, block_type, ...)` — types: `technical`, `behavioral`, `situational`

### 7.3 Interview Scheduling Graph

**Arquivo:** `app/domains/interview_scheduling/agents/interview_graph.py`

```python
builder = StateGraph(state_schema)
```

- Nós: disponibilidade, proposta de slots, confirmação, criação no calendário, notificação
- PostgresSaver para checkpoint de sessão multi-turn

---

## 8. Tools Layer (~260 tools)

**Fonte canônica:** `app/tools/tool_registry_metadata.yaml` (74 tools curadas com `scope` + `allowed_agents`)

### Totais

| Métrica | Valor |
|---------|-------|
| Arquivos com `ToolDefinition(` | 48 |
| Arquivos `*tool_registry*.py` | 33 |
| Instanciações `ToolDefinition(` | 322 |
| Tools canônicas no YAML | 74 |
| Tools únicas aproximadas (dedup cross-domain) | ~260 |
| PLATFORM_TOOLS_REGISTRY (Studio/Tier 7) | 15 |

### Escopos (legenda YAML)

| Símbolo | Escopo |
|---------|--------|
| `G` | GLOBAL — disponível em qualquer contexto |
| `TF` | TALENT_FUNNEL — Funil de Talentos |
| `JT` | JOB_TABLE — tabela de vagas |
| `IJ` | IN_JOB — dentro de uma vaga específica |
| `U` | UNIVERSAL — multi-contexto |

### Principais Registries por Domínio

| Domínio | Arquivo | Agent | Tools |
|---------|---------|-------|-------|
| analytics | `analytics/agents/analytics_tool_registry.py` | AnalyticsReActAgent | 6 |
| analytics (query) | `analytics/tools/analytics_query_tools/registry.py` | AnalyticsReActAgent | 19 |
| ats_integration | `ats_integration/agents/ats_integration_tool_registry.py` | ATSIntegrationReActAgent | 5 |
| automation | `automation/agents/automation_tool_registry.py` | AutomationReActAgent | 6 |
| autonomous (Tier 6, removido de prod) | `autonomous/agents/autonomous_tool_registry.py` | AutonomousReActAgent | 41 |
| communication | `communication/agents/communication_tool_registry.py` | CommunicationReActAgent | 5 |
| company_settings | `company_settings/agents/company_tool_registry.py` | CompanySettingsReActAgent | 7 |
| cv_screening | `cv_screening/agents/pipeline_tool_registry.py` | PipelineReActAgent | 15 |
| hiring_policy | `hiring_policy/agents/policy_tool_registry.py` | PolicyReActAgent | 13 |
| job_management | `job_management/agents/wizard_tool_registry.py` | WizardReActAgent | 10 |
| pipeline | `pipeline/agents/pipeline_tool_registry.py` | PipelineTransitionAgent | 20 |
| recruiter_assistant | `recruiter_assistant/agents/jobs_mgmt_tool_registry.py` | JobsManagementReActAgent | 14 |
| recruiter_assistant | `recruiter_assistant/agents/kanban_tool_registry.py` | KanbanReActAgent | 22 |
| recruiter_assistant | `recruiter_assistant/agents/talent_tool_registry.py` | TalentFunnelReActAgent | 13 |
| sourcing | `sourcing/agents/sourcing_tool_registry.py` | SourcingReActAgent | 18 |
| talent_intelligence | `talent_intelligence/tools/registry.py` | — | 15 |
| shared | `shared/global_tool_registry.py` | runtime permission gate | — |
| shared | `shared/tools/export_tools.py` | — | 4 |
| shared | `shared/tools/insight_tools.py` | — | 4 |
| shared | `shared/tools/predictive_tools.py` | — | 4 |
| shared | `shared/tools/proactive_tools.py` | — | 4 |

### PLATFORM_TOOLS_REGISTRY (Studio/Tier 7)

**Arquivo:** `app/domains/agent_studio/custom_agent_runtime.py`

15 platform tools classificadas `read`/`write` para agentes customizados do Tier 7. Controla o que um Custom Agent pode fazer (sem ToolDefinition, via dict direto).

---

## 9. LLM Layer — Factory, Bootstrap & Modelos

### 9.1 LLM Bootstrap

**Arquivo:** `app/shared/llm_bootstrap.py`

Chamado UMA vez no startup via `install_llm_guards()` (em `app/main.py`). Monkey-patcha os SDKs antes de qualquer módulo instanciar um cliente LLM.

**Patches aplicados:**

| SDK | O que patcha | Por quê |
|-----|-------------|---------|
| `anthropic.Anthropic` / `AsyncAnthropic` | Injeta API key + audit | LangChain `ChatAnthropic` pode ignorar `base_url` |
| `anthropic.messages.create/stream` | PII strip + credit gate | Garante que chamadas diretas ao SDK são contabilizadas |
| `google.genai.Client` | Injeta API key + audit | Gemini Live e SDK direto |
| `openai.OpenAI` / `AsyncOpenAI` | Injeta API key + credit gate | Whisper, TTS, fallback |

**`_inject_anthropic_env`:** Sobrescreve `base_url` para o proxy modelfarm (`AI_INTEGRATIONS_ANTHROPIC_BASE_URL`). Crítico — sem isso, `ChatAnthropic` bate direto em `api.anthropic.com` com a wrapper key, causando 401 e degradação de qualidade ~20%.

**Universal ai_credit_gate (Wave 3):** Intercepta primitivas de criação de mensagem em todos os SDKs para enforcement de budget por tenant, fechando o gap de 7+ domain services que chamavam o SDK diretamente (intake_extractor, voice_service, interview_scheduling, multimodal_service, etc.).

### 9.2 LLM Provider Factory

**Arquivo:** `app/shared/providers/llm_factory.py`

```
LLMProviderFactory          — registro global de classes de provider
  └── register(provider_class)
  └── get(name)

ProviderContainer           — DI container por tenant
  ├── primary_provider      — provider principal (configurável por tenant)
  ├── fallback_order        — chain de fallback
  └── load_from_db()        — carrega config do banco (API key, provider, região)

TenantProviderRegistry      — singleton: tenant_id → ProviderContainer

get_provider_for_tenant()   — entry point recomendado para todo acesso LLM
```

**Fallback padrão:** `FALLBACK_ORDER = ["claude", "gemini", "openai"]`

> Claude primeiro porque o proxy modelfarm (localhost:1106) está quebrado para Gemini e OpenAI no ambiente de dev/Replit.

### 9.3 Modelos em Uso

| Papel | Modelo | Onde |
|-------|--------|------|
| Agentes primários (produção) | Claude Sonnet | 16 ReActAgents via `LangChain ChatAnthropic` |
| LLM Cascade Tier 5a | Gemini Flash | `llm_cascade.py` — roteamento rápido/barato |
| LLM Cascade Tier 5b | Claude Sonnet | `llm_cascade.py` — threshold médio |
| LLM Cascade Tier 5c | Claude Opus | `llm_cascade.py` — máxima qualidade |
| Voice STT/Transcrição | Gemini Live Audio | `gemini_live_audio_service.py` |
| Voice STT fallback | OpenAI Whisper | PSTN fallback only |
| Voice TTS fallback | OpenAI TTS | PSTN fallback only |
| Embedding | Configurable | `DomainEmbeddingService` (padrão: text-embedding-3-small) |

### 9.4 Configuração por Tenant

Cada tenant pode ter:
- `primary_provider`: qual LLM usar como primário
- `fallback_order`: ordem de fallback customizada
- `region`: para compliance LGPD (ex.: dados no Brasil)
- API keys próprias (opcional, sobrepõem as system-wide)

Armazenado em tabela `llm_config` e acessado via `LLMConfigRepository`.

---

## 10. Messaging & AgentBus

### 10.1 AgentBus

**Arquivo:** `app/shared/agents/agent_bus.py` (336 LOC)
**Re-export shim:** `libs/agents-core/lia_agents_core/agent_bus.py` (backward compat)

Redis Pub/Sub para comunicação Agent-to-Agent.

```
Channel pattern: lia:agent_bus:{company_id}:{to_agent}
Reply channel:   lia:agent_bus:reply:{correlation_id}
```

**Dois modos:**

| Modo | Método | Descrição |
|------|--------|-----------|
| Fire-and-forget | `publish()` | Envia evento, sem resposta esperada |
| Request-reply (crew) | `request()` | Envia + aguarda reply com timeout (default 30s) |
| Subscriber | `subscribe()` | Registra handler no startup |

**`AgentEvent` (dataclass):**

```python
@dataclass
class AgentEvent:
    from_agent: str
    to_agent: str
    event_type: str
    payload: dict
    company_id: str
    event_id: str          # uuid4
    published_at: str      # ISO datetime
    correlation_id: str?   # para request-reply
    reply_to: str?         # reply channel
```

### 10.2 BrokerInterface

**Arquivo:** `app/shared/messaging/broker_interface.py`

| Implementação | Backend | Status |
|---------------|---------|--------|
| `RedisBroker` | aioredis / Redis Lists (`LPUSH`/`BRPOP`) | **Default / Produção** |
| `RabbitMQBroker` | aio-pika / AMQP | On-prem agent chat |
| `PubSubBroker` | Google Cloud Pub/Sub | Stub — `NotImplementedError` (futuro GCP) |

Factory: `get_broker()` — seleciona via `BROKER_BACKEND` env var.

### 10.3 Crew Executor

**Arquivo:** `app/shared/agents/crew_executor.py`

Delegação formal multi-agente ao estilo CrewAI sobre o AgentBus. Suporta `crew_audit.py` para trilha de auditoria de delegações cross-agent.

---

## 11. Plan & Execute (LIA_V2_USE_PLAN_SERVICE)

**Status:** Feature flag OFF por padrão. Promoção para produção sem flag: 2026-07-01.

### Componentes

| Arquivo | Responsabilidade |
|---------|-----------------|
| `orchestrator/execution/task_planner.py` | Gera plano multi-step a partir da intent |
| `orchestrator/services/plan_orchestration_service.py` | Orquestra execução do plano |
| `shared/execution/plan_executor.py` (549 LOC) | Executa tasks do plano sequencialmente |
| `shared/execution/execution_plan.py` | Schemas: `ExecutionPlan`, `AgentTask`, `PlanStatus`, `TaskStatus` |
| `shared/execution/discrete_actions.py` | Handlers de ações discretas |
| `orchestrator/routing/job_creation_disambiguator.py` | Guard contra criação de vaga via Plan & Execute |

### Regra Inviolável

> **Criação de vaga é SEMPRE e SÓ o Wizard Canônico.** Plan & Execute NUNCA cria vaga.

O `plan_detector` tem guard de import-time: `_assert_no_creation_steps` + `JOB_CREATION_ACTION_IDS`. Qualquer pattern que reintroduza step de criação **falha em import-time**.

### PlanExecutor

```python
class PlanExecutor:
    def __init__(self, domain_registry=None, domain_workflow=None):
        # DomainRegistry() + DomainWorkflow() reais (não fake)
```

- `TASK_TIMEOUT_SECONDS = 15` por task
- `_safe_eval_condition()`: avaliador seguro de condições (AST parser, sem `eval()`)
- Honest handoff: qualquer falha propaga explicitamente (nunca fake success)

### Continuidade Pós-Wizard

Após o wizard atingir stage terminal, a LIA **oferece** a etapa restante no chat. Só executa (`publish/sync` via `ats_integration.sync_job`, vinculado ao `job_id` criado) mediante confirmação natural PT-BR (`classify_confirmation`).

---

## 12. Compliance Layer — C3b, FairnessGuard, FactChecker, Audit

### 12.1 C3b Layer

**Arquivo:** `app/shared/compliance/c3b_layer.py`

Strangler pattern para WS/SSE compliance. Envolve toda interação chat.

```
Mensagem entrada
  ├── [PRÉ-COMPLIANCE]
  │   ├── PII stripping      → strip_pii_for_llm_prompt()
  │   └── FairnessGuard L3   → check() para domínios HR-sensitivos
  │
  └── resposta LLM
      ├── [PÓS-COMPLIANCE]
      │   ├── FactChecker    → valida claims factuais
      │   └── AuditService   → log_decision()
      └── resposta entregue ao recrutador
```

**Kill-switch:** `LIA_DISABLE_C3B=1` — bypass total (passthrough). Em prod/staging: emite audit event (`_emit_c3b_disabled_audit_once`), log CRITICAL + Sentry. Uso em produção é **proibido**.

### 12.2 FairnessGuard

**Arquivo:** `app/shared/compliance/fairness_guard.py`

```python
class FairnessGuard:
    def check(message: str) -> FairnessResult
```

**Dois níveis de detecção:**

| Nível | Tipo | Ação | Exemplos |
|-------|------|------|---------|
| Hard Block | 20+ categorias discriminatórias via regex | Bloqueia + resposta educativa | "só homens", "excluir maiores de 50", raça, religião |
| Soft Warning (L2) | Termos de viés implícito | `soft_warnings[]` — não bloqueia | "jovem e dinâmico", "boa aparência", "nativo digital" |

**Integração:** Chamada em dois pontos:
1. `MainOrchestrator` (pré-processamento — Phase 0)
2. `C3b Layer` (pré-compliance — antes do LLM)

**Middleware standalone:** `app/shared/compliance/fairness_guard_middleware.py`

### 12.3 FactChecker

**Arquivo:** `app/shared/compliance/fact_checker.py` (classe `FactChecker`)
**Base:** `app/shared/evaluation/fact_checker.py` (classe `FactChecker(_BaseFactChecker)`)

Valida respostas LLM para acurácia técnica e alucinações. Sinaliza "inaccurate claims" nos metadados de auditoria.

### 12.4 BiasAuditService

**Arquivo:** `app/shared/services/bias_audit_service.py`

```python
class BiasAuditReport:  # linha 86
class BiasAuditService:  # linha 315
```

Consolida bias detection de múltiplos domínios (Interview, Job Creation, Sourcing) em trilha de auditoria unificada.

### 12.5 AuditService

**Arquivo:** `app/shared/compliance/audit_service.py`

| Ação | Retenção | Mandato |
|------|----------|---------|
| Offer decisions | 7 anos | SOX |
| Interview transcripts | — | LGPD Art. 46 |
| Todos os saves mutativas em `interview_scheduling`, `interview_intelligence`, `offer` | — | Auditoria obrigatória |

**Métodos:** `log_decision()`, `log_decision_in_session()`

**Regra de ouro:** Todo `async def` público mutativo em `domains/{interview_scheduling,interview_intelligence,offer}/services/*.py` DEVE chamar `AuditService.log_decision`.

### 12.6 Hate Speech Guard

**Arquivo:** `app/shared/compliance/hate_speech_guard.py`

Camada adicional de detecção de discurso de ódio (complementa FairnessGuard).

### 12.7 Compliance Bypass Flags (R-007)

> Detalhamento completo em `docs/runbooks/operational-flags.md`

| Flag | Default | Efeito |
|------|---------|--------|
| `LIA_DISABLE_C3B` | OFF | **KILL SWITCH** — desativa toda camada C3b |
| `LIA_ALLOW_NON_COMPLIANT_DOMAINS` | OFF | Rollback ComplianceDomainPrompt |
| `LIA_ALLOW_NON_COMPLIANT_AGENTS` | OFF | Rollback compliance agent layer |
| `LIA_ALLOW_REGISTRY_DRIFT` | OFF | Rollback emergencial agents_registry |
| `LIA_DISABLE_COMPANY_AUDIT` | OFF | Rollback audit_logs (viola SOX) |

---

## 13. WSI Screening Pipeline

**Arquivo principal:** `app/domains/cv_screening/services/wsi_screening_pipeline.py`
**Constantes:** `app/domains/cv_screening/services/wsi_question_adjuster.py` (WSI_BLOCKS dict)
**Grafo interativo:** `app/domains/cv_screening/agents/wsi_interview_graph.py`

### Os 6 Blocos WSI

| Bloco | Tipo | Conteúdo | Gerador |
|-------|------|----------|---------|
| **Bloco 0** | Abordagem Inicial | Abertura da sessão, apresentação da LIA | voice_orchestrator / public chat |
| **Bloco 1** | Apresentação da Oportunidade | Detalhes da vaga, empresa | wsi_service |
| **Bloco 2** | Perguntas da Empresa + Elegibilidade | Questões padrão do tenant + critérios de elegibilidade configurados pelo recrutador | wsi_screening_pipeline (DB) |
| **Bloco 3** | Competências Técnicas | Bloom/Dreyfus via WSIService | wsi_service (question_generator) |
| **Bloco 4** | Competências Comportamentais e Fit | Big Five/CBI via WSIService | wsi_service (question_generator) |
| **Bloco 5** | Resultado e Encerramento | Score WSI + feedback | wsi_feedback_generator |

### Fluxo do Pipeline

```
WSIScreeningPipeline.build_pipeline()
  ├── Block 2: Company questions (DB) + elegibilidade + ação afirmativa (se configurado)
  ├── Block 3: Technical questions (Bloom taxonomy × Dreyfus seniority stages)
  ├── Block 4: Behavioral questions (Big Five × CBI)
  └── F5 adaptive distribution — distribui perguntas por senioridade
```

### Scoring

- **Determinístico:** `wsi_deterministic_scorer.py` — Dreyfus stage labels
- **LLM-based:** `wsi_service/question_generator.py` — `inc_wsi_bias_block` para bias tracking
- **Feedback:** `wsi_feedback_generator.py` — Bloco 2 (Conhecimento Técnico) + feedback por competência

### WSI Voice (Twilio path)

**Arquivo:** `app/domains/cv_screening/services/wsi_voice_orchestrator.py`

Conecta Twilio Voice com WSI scoring para entrevistas por telefone (PSTN fallback).

---

## 14. Voice Architecture

### Primário — GeminiLiveAudioService (VoIP Browser)

**Arquivo:** `app/domains/voice/services/gemini_live_audio_service.py`

```python
class GeminiLiveSession:
    voice_provider: str = "gemini_live"
    transcript_segments: list[dict]

class GeminiLiveAudioService:
    _sessions: dict[str, GeminiLiveSession]
```

- **Custo:** ~$0.065/entrevista de 15min
- **Transporte:** WebSocket bidirecional browser ↔ Gemini Live API
- **Transcrição:** via `VoiceScreeningOrchestrator._build_job_context_summary()`
- **Expiração:** `is_session_expired()` — TTL por sessão
- **Métricas:** `record_turn_latency()`, `get_session_metrics()`

### Fallback — Twilio + OpenAI (PSTN)

| Componente | Papel | Custo/15min |
|-----------|-------|-------------|
| Twilio Voice | PSTN call management | — |
| OpenAI Whisper | STT (Speech-to-Text) | ~$0.41 total |
| OpenAI TTS | TTS (Text-to-Speech) | — |

### Orquestradores de Voice

| Arquivo | Responsabilidade | LOC |
|---------|-----------------|-----|
| `voice/services/voice_core_orchestrator.py` | Entry point de voz unificado | — |
| `voice/services/voice_screening_orchestrator.py` | Fluxo completo de screening por voz | ~1 725 |
| `cv_screening/services/wsi_voice_orchestrator.py` | WSI × Twilio Voice integration | — |

### Deepgram (STT)

**Externo:** Deepgram como provider alternativo de STT/transcrição de voz. Configurável via tenant LLM config.

---

## 15. Knowledge Base & RAG

### 15.1 RAG Pipeline Service

**Arquivo:** `app/domains/ai/services/rag_pipeline_service.py` (236 LOC classe)

```
Query do usuário
  ├── Tier: rag_query_analysis    — análise da query para otimização
  ├── Tier: rag_bm25_search       — tsvector BM25 (keyword match)
  ├── Tier: rag_semantic_search   — pgvector cosine similarity
  ├── Tier: rag_hybrid_blending   — alpha blend (alpha=1.0 → só semântico)
  └── Tier: rag_reranking         — rerank por relevância
```

- **Alpha=0.0:** apenas BM25 (keyword)
- **Alpha=1.0:** apenas semântico (pgvector)
- **Alpha=0.5:** híbrido balanceado

**Chunking:** `RecursiveTextSplitter` com chunking hierárquico (docstrings, seções, parágrafos).

### 15.2 Hybrid Search Service

**Arquivo:** `app/domains/ai/services/hybrid_search_service.py`

```python
class HybridSearchService:
    async def search_jobs(query, company_id, ...)   # tsvector + pgvector
    async def search_candidates(query, company_id, ...)  # tsvector + pgvector
```

Singleton: `hybrid_search_service = HybridSearchService()`

### 15.3 Domain Embedding Service

**Arquivo:** `app/domains/ai/services/domain_embedding_service.py`

```python
class DomainEmbeddingService:
    async def embed_document(source_type, source_id, domain, text)
    async def rebuild_domain_index(domain, company_id)
```

Isolamento por domínio: embeddings de `analytics` não vazam para `cv_screening`.

Singleton: `domain_embedding_service = DomainEmbeddingService()`

### 15.4 Serviços de Cache

| Serviço | Arquivo | Backend |
|---------|---------|---------|
| `EmbeddingCacheService` | `domains/ai/services/embedding_cache_service.py` | Redis |
| `SemanticCache` | `orchestrator/memory/semantic_cache.py` | pgvector (Tier 3) |
| `VectorSemanticCache` | `orchestrator/memory/vector_semantic_cache.py` | pgvector cosine ≥ 0.85 |
| `ResponseCacheService` | `domains/ai/services/response_cache_service.py` | Redis |
| `AICacheService` | `domains/ai/services/ai_cache_service.py` | Redis |

### 15.5 Knowledge Base Service

**Arquivo:** `app/domains/ai/services/knowledge_base_service.py`

Gerencia documentos indexados por tenant (JDs, políticas, perfis de empresa) para injeção no contexto do LLM.

### 15.6 RAGAS Evaluation

**Arquivo:** `app/domains/ai/services/ragas_evaluation_service.py`

Framework de avaliação de qualidade RAG (faithfulness, answer relevance, context precision).

---

## 16. Tenant Context System

**Detalhamento completo:** `docs/architecture/tenant-context-history.md`

### TenantAwareAgentMixin

**Arquivo:** `app/shared/agents/tenant_aware_agent.py`

```python
class TenantAwareAgentMixin:
    tenant_strict_override: bool | None = None
    # True → NUNCA degrada para "sua empresa"/"geral" (usado pelo WizardReActAgent)
```

Todos os 16 ReActAgents canônicos herdam este mixin como **primeiro** na MRO.

**Capacidades fornecidas:**
1. Injeta `tenant_context_snippet` automaticamente no system prompt
2. Valida que `company_id` está sempre presente
3. Respeita `LIA_AGENT_TENANT_STRICT` (ON em prod)
4. Se `tenant_strict_override=True`: erro explícito se tenant não resolvido (sem degradação)

### CompanyId Value Object

Impede que `company_id` seja tratado como string genérica. Tipagem forte com validação de formato UUID v4.

### TenantContextService

**Arquivo:** `app/shared/services/tenant_context_service.py`

Resolve tenant context a partir de JWT → `company_id` → enriquecimento (plano, setor, headcount, nome).

### Regra Inviolável — T-A → T-F

> `TenantAwareAgentMixin` + `CompanyId` value object blindam o sistema contra a recorrência do bug *"LIA pergunta `company_id` no chat"*.

```
T-A: TenantAwareAgentMixin introduzida
T-B: WizardReActAgent com tenant_strict_override=True
T-C: Demo Company canônica (UUID 00000000-0000-4000-a000-000000000001)
T-D: Sentinela de 16 agents canônicos (quebra build se violado)
T-E: Eval gate 0.85 threshold
T-F: Sentinela non-React callsites
```

### Runbook Tenant Context

**Arquivo:** `docs/runbooks/missing_tenant_context.md`

---

## 17. Agent Studio — Tier 7 (Custom Agents)

**Arquivo:** `app/domains/agent_studio/custom_agent_runtime.py`

```python
class CustomAgentRuntime(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    # Mesma base dos 16 canônicos
```

### Componentes

| Arquivo | Responsabilidade |
|---------|-----------------|
| `custom_agent_runtime.py` | Runtime de execução de agentes customizados |
| `actions.py` | Ações disponíveis para custom agents |
| `domain.py` | Registro no DomainRegistry |
| `reasoning_trace_builder.py` | Trace de raciocínio para auditoria |
| `whatsapp_agent_plugin.py` | Plugin de canal WhatsApp |
| `repositories/custom_agent_repository.py` | CRUD de agentes customizados |
| `repositories/agent_marketplace_repository.py` | Templates do marketplace |
| `repositories/digital_twin_repository.py` | Digital twins de candidatos |
| `repositories/pool_agent_assignment_repository.py` | Atribuição de agentes a pools |
| `repositories/pool_agent_run_repository.py` | Histórico de execuções |

### PLATFORM_TOOLS_REGISTRY

15 tools da plataforma disponíveis para custom agents, classificadas:
- `read`: acesso a dados (candidatos, vagas, pipeline, etc.)
- `write`: ações mutativas (mover candidato, enviar mensagem, etc.)

### Marketplace de Agentes

Templates de custom agents acessíveis via `agent_marketplace_repository.py`. Ativação via POST `/custom-agents` (proxy autenticado `createProxyHandlers({ auth: true })`).

---

## 18. Feature Flags de Comportamento AI

> Detalhamento completo: `docs/runbooks/operational-flags.md`

### Flags de Comportamento (não-compliance)

| Flag | Default | Efeito em produção |
|------|---------|-------------------|
| `LIA_V2_USE_PLAN_SERVICE` | OFF | Liga path Plan & Execute (multi-step) |
| `LIA_WIZARD_LLM_GATES` | **ON** (pós-GA) | Classifier LLM nos 4 gates HITL do wizard |
| `LIA_WIZARD_FALLBACK_LLM_DISABLED` | OFF | Testes offline — canned reply hard-prefixada |
| `LIA_WIZARD_SUPERVISOR_CLASSIFIER` | ON dev / OFF prod | Supervisor pre-graph 6-intents |

### Flags de Compliance (R-007 — emergency only)

| Flag | Default | Efeito |
|------|---------|--------|
| `LIA_AGENT_TENANT_STRICT` | **ON** em prod | OFF reabre bug "LIA pergunta company_id" |
| `LIA_DISABLE_C3B` | OFF | **KILL SWITCH** C3b inteira |
| `LIA_ALLOW_NON_COMPLIANT_DOMAINS` | OFF | Rollback ComplianceDomainPrompt |
| `LIA_ALLOW_NON_COMPLIANT_AGENTS` | OFF | Rollback compliance agent layer |
| `LIA_ALLOW_REGISTRY_DRIFT` | OFF | Rollback emergencial agents_registry |
| `LIA_DISABLE_COMPANY_AUDIT` | OFF | Rollback audit_logs (viola SOX) |

**Em produção, qualquer flag ON dispara:** log CRITICAL, `capture_message` Sentry, exposure em `/api/v1/health/compliance/bypass-status`.

---

## 19. Observabilidade & Monitoramento

### Tracing

| Componente | Arquivo | Descrição |
|-----------|---------|-----------|
| Datadog APM | `ddtrace` no comando de startup | Distributed tracing em produção |
| `trace_span` | `shared/observability/tracing.py` | Decorator de span para funções críticas |
| LangSmith | `shared/providers/llm_factory.py` | `@traceable` para LLM calls (graceful se não instalado) |

### Métricas de Performance

```python
# main_orchestrator.py
_perf_metrics: dict[str, list[float]] = {}  # últimas 100 por domain
get_perf_summary() → {domain: {count, avg_ms, p95_ms}}
```

### Agent Monitoring

**Arquivo:** `app/domains/analytics/services/agent_monitoring_service.py`

Histórico de execuções de agentes, disponível via `/api/backend-proxy/agent-monitoring/recent-executions`.

### Routing Learning

**Arquivo:** `app/shared/services/routing_learning_service.py` (e `app/domains/analytics/services/routing_learning_service.py`)

Ajusta pesos de roteamento por domain_id baseado em feedback e outcomes. Executado no loop diário do `MonitoringLoop`.

### Alertas Proativos

**Arquivo:** `app/shared/services/proactive_detector_service.py`

- Fonte única de configuração: `AlertPreference` (tabela `alert_preferences`)
- `resolve_alert_config()` em `app/shared/services/alert_config_resolver.py`
- Sentinela: `tests/contract/test_alert_config_single_source.py`
- Detalhamento: `docs/runbooks/alert-config-single-source.md`

### Logging Estruturado

```python
# Formato lia.request
logger = logging.getLogger("lia.request")
# INFO request: método, path, status, latency_ms, company_id, agent_used
```

### Sentry

Integrado para error tracking em produção. Captura:
- `capture_message` para compliance flag violations
- Exception tracking via global exception handlers

### RAGAS Evaluation Gate

```bash
python -m eval.eval_runner --gate eval/golden/<domain>.jsonl
```

Exemplo (company_settings): 18 cenários × threshold 0.85.

---

## 20. Domain Catalog — Resumo

> Fonte canônica: `app/domains/DOMAIN_CATALOG.md`

### Agentic Domains (13) — registrados via `@register_domain`

| Domain | domain_id | LOC aprox. | Descrição |
|--------|-----------|-----------|-----------|
| `analytics` | analytics | 68 files | Analytics, relatórios, dashboards |
| `ats_integration` | ats_integration | 25 files | ATS: Gupy, Pandapé, Merge.dev |
| `automation` | automation | 37 files | Tasks, lembretes, notas, workflow |
| `communication` | communication | 75 files | Email, WhatsApp, Teams, SMS |
| `cv_screening` | cv_screening | 80 files | WSI, avaliação de CV, scoring |
| `hiring_policy` | hiring_policy | 14 files | Política de contratação + FairnessGuard |
| `interview_scheduling` | interview_scheduling | 25 files | Agendamento + Microsoft Calendar |
| `job_creation` | job_creation | 13 files | Wizard de criação de vaga (HITL) |
| `job_management` | job_management | 69 files | CRUD de vagas, pipeline config |
| `pipeline` | pipeline_transition | 21 files | Movimentação de candidatos |
| `recruiter_assistant` | recruiter_assistant | 38 files | Copiloto geral (fallback domain) |
| `sourcing` | sourcing | 49 files | Sourcing multi-canal |
| `agent_studio` | agent_studio | 4 files | Custom agents marketplace |

### Micro-Action Domains (3)

| Domain | domain_id | Descrição |
|--------|-----------|-----------|
| `digital_twin` | digital_twin | Digital twin de candidato |
| `recruitment_campaign` | recruitment_campaign | Campanhas multi-etapa |
| `talent_pool` | talent_pool | Gestão de talent pools |

### Service Domains (11) — sem `@register_domain`

| Domain | Classif. | Descrição |
|--------|---------|-----------|
| `ai` | service | LLM services, cache, prompts |
| `billing` | service | Assinaturas e billing |
| `candidates` | service | CRUD e perfil de candidatos |
| `company` | service | Settings e configuração de empresa |
| `credits` | service | Tracking de consumo AI |
| `integrations_hub` | service | Third-party integration management |
| `interview_intelligence` | **promotion_candidate** | Bias detection, análise comparativa (2 026 LOC) |
| `lgpd` | service | LGPD/GDPR compliance e purge |
| `modules` | service | Feature gating por tier |
| `recruitment` | service | Dados de processos seletivos |
| `voice` | **promotion_candidate** | Voice screening (~1 725 LOC orchestrator) |

### Repository Stubs (30)

Pure CRUD data access layers. Não roteáveis pelo orquestrador. Incluem: `admin`, `agent_memory`, `approvals`, `auth`, `bulk_actions`, `candidate_lists`, `chat`, `clients`, `client_users`, `company_culture`, `compliance`, `consent`, `data_subject`, `email_templates`, `goals`, `health_check`, `integrations_hub` (repo), `journey_mapping`, `notifications`, `observability`, `offers`, `opinions`, `persona`, `policy` (legacy), `recruitment_journey`, `saas_metrics`, `shared_searches`, `talent_intelligence`, `tasks`, `trust_center`.

---

## Apêndice — Arquivos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `docs/architecture/ARCHITECTURE.md` | Source of truth técnico (~1 300 LOC) |
| `docs/architecture/wizard-flow.md` | Contratos completos do wizard de criação |
| `docs/architecture/tenant-context-history.md` | Histórico T-A → T-F tenant context |
| `docs/architecture/LIA_TOOLS_CATALOG.md` | Catálogo completo de tools (120+ tools, 28+ registries) |
| `docs/architecture/TIER_6_7_REACT_FALLBACK_AND_STUDIO_AGENTS.md` | Tier 6 (removido) e Tier 7 (Studio) |
| `docs/architecture/id-boundary-policy.md` | Política de boundary de IDs |
| `docs/runbooks/operational-flags.md` | Feature flags, bypass flags, runbook E2E |
| `docs/runbooks/task-1161-three-bugs.md` | Bug A (base_url) · Bug B (checkpointer) · Bug C (culture leak) |
| `docs/runbooks/missing_tenant_context.md` | Runbook on-call para tenant context |
| `docs/runbooks/alert-config-single-source.md` | Alertas proativos — fonte única |
| `docs/runbooks/audit-interview-offer.md` | Audit obrigatório nos 3 domínios Interview + Offer |
| `app/domains/DOMAIN_CATALOG.md` | Catálogo completo de todos os 59 domínios |
