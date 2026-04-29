# Theme I3 — Orchestration (4 phases + Cascade 8 tiers)

**Layer:** Infrastructure  |  **Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/app/orchestrator/` no Replit

---

## O que é este tema

O **MainOrchestrator** é o entry point único de todas as mensagens da LIA. Ele implementa um pipeline de 4 fases progressivas — cada fase tenta resolver a mensagem no menor custo possível, passando para a próxima apenas se necessário:

- **Fase 0** — PendingAction: verifica se há ação aguardando confirmação de turno anterior
- **Fase 1** — ActionExecutor: detecta intenções fechadas por padrão e as executa diretamente
- **Fase 1.5** — AgenticLoop: LLM com function calling (feature-flagged `LIA_AGENTIC_LOOP`)
- **Fase 2** — CascadedRouter (8 tiers) → DomainWorkflow → ReAct Agent

O **CascadedRouter** implementa 8 níveis de resolução em custo crescente: desde cache in-process (O(1)) até agente autônomo cross-domain como último recurso antes de pedir clarificação ao usuário.

**Boundary com temas irmãos:**
- **I1 Agent Architecture** — Fase 2 roteia para domínios cujos agentes são gerenciados pelo ReactAgentRegistry (I1)
- **I2 Tool Architecture** — ActionExecutor chama tools diretamente; ReAct loop via CascadedRouter usa tools (I2)
- **I4 LLM Providers** — CascadedRouter Tier 5 usa BYOK via `get_provider_for_tenant()` (I4)
- **I7 Intent Routing** — FastRouter (Tier 4) é alimentado por `intent_classification.yaml` e `capabilities.yaml`
- **C1 Fairness** — FairnessGuard roda ANTES de qualquer fase (pré-check obrigatório)
- **C8 Policy Engine** — PolicyMiddleware injeta policy em `request.state.policy` (C8) antes do orchestrator

---

## Arquivos conectados (17 Python + 1 YAML)

### Camada Config (Python lê — 1 YAML)

| Arquivo | Path canônico | Quando é consumido |
|---------|---------------|--------------------|
| `domain_routing.yaml` | `app/orchestrator/config/domain_routing.yaml` | Lido pelo `FastRouter` (Tier 4) + `CascadedRouter` na inicialização |

### Camada Código (17 arquivos Python)

**Core pipeline:**

| Arquivo | Path canônico | Linhas | Responsabilidade |
|---------|---------------|:---:|-----------------|
| `main_orchestrator.py` | `app/orchestrator/main_orchestrator.py` | 1370 | Entry point único. `MainOrchestrator.process(ctx, db)` → ChatResponse. 4 fases + pré-checks |
| `context_adapter.py` | `app/orchestrator/context_adapter.py` | — | `UniversalContext` dataclass + `PAGE_TO_CONTEXT_TYPE` — normaliza REST/WS/RabbitMQ para estrutura única |
| `cascaded_router.py` | `app/orchestrator/cascaded_router.py` | 792 | 8-tier router. `RouteResult(domain_id, confidence, source, cached)` |
| `fast_router.py` | `app/orchestrator/fast_router.py` | 666 | FastRouter — regex/keyword patterns (Tier 4). Consome `domain_routing.yaml` |
| `agentic_loop.py` | `app/orchestrator/agentic_loop.py` | — | AgenticLoop — LLM com function calling (Fase 1.5, feature-flagged) |
| `orchestrator.py` | `app/orchestrator/orchestrator.py` | — | Orchestrator legacy — ainda usado por `_process_via_orchestrator()` em Fase 2 |
| `llm_cascade.py` | `app/orchestrator/llm_cascade.py` | — | LLMCascade — Haiku→Sonnet→Opus fallback (Tier 5) |
| `pending_action.py` | `app/orchestrator/pending_action.py` | — | PendingActionStore — persiste ações aguardando confirmação entre turnos |
| `state_manager.py` | `app/orchestrator/state_manager.py` | — | Gerenciamento de estado de sessão |
| `domain_mappings.py` | `app/orchestrator/domain_mappings.py` | — | `AGENT_TYPE_TO_DOMAIN` + `resolve_domain()` |

**Action executor (diretório):**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|-----------------|
| `action_executor/executor.py` | `app/orchestrator/action_executor/executor.py` | `ActionExecutorService.try_execute()` — delega para `action_handlers` |
| `action_executor/intents_config.py` | `app/orchestrator/action_executor/intents_config.py` | `ACTIONABLE_INTENTS` dict — mapa intent → configuração de execução |
| `action_executor/action_types.py` | `app/orchestrator/action_executor/action_types.py` | `ActionResult` dataclass |
| `action_executor/utils.py` | `app/orchestrator/action_executor/utils.py` | `_detect_intent_from_message()`, `_extract_entities_from_message()`, `resolve_candidate_from_context()` |

**State / Budget:**

| Arquivo | Path canônico | Responsabilidade |
|---------|---------------|-----------------|
| `wizard_state.py` | `app/orchestrator/wizard_state.py` | `WizardState` Redis-backed, TTL=2h — persiste campos coletados entre turnos do wizard |
| `tenant_budget.py` | `app/orchestrator/tenant_budget.py` | Rastreia tokens por tenant/mês no Redis; alerta a 80%; bloqueia a 100% |
| `semantic_cache.py` | `app/orchestrator/semantic_cache.py` | `SemanticCache` — pgvector cosine similarity ≥ 0.85 (Tier 3) |

### Integration points

- **API Layer** (I6) chama `main_orchestrator.process(ctx, db)` em todos os endpoints de chat
- **PolicyMiddleware** (C8) injeta `request.state.policy` ANTES da chamada ao orchestrator
- **FairnessGuard** (C1) é instanciado no `__init__` do `MainOrchestrator` e chamado em cada request
- **ReactAgentRegistry** (I1) é consultado pelo `Orchestrator.process_request()` (Fase 2)
- **LLMProviderFactory** (I4) é chamado pelo `CascadedRouter` para BYOK no Tier 5
- **AuditCallback** (C7) é registrado em `_audit_output()` após resposta ser construída
- **TenantBudget** rastreia tokens em Redis; `tenant_budget.py` atualizado a cada chamada LLM

---

## Lógica IN → OUT

### UniversalContext — normalização de canais

```python
# context_adapter.py
@dataclass
class UniversalContext:
    message: str
    company_id: str           # sempre do JWT (multi-tenancy)
    user_id: str
    session_id: str
    conversation_id: str
    context_type: str         # "talent_funnel" | "pipeline" | "job_management" | "analytics" | "company_settings" | "general"
    entity_id: str | None     # job_id ou candidate_id em foco
    entity_type: str | None   # "job" | "candidate"
    extra: dict               # metadata adicional (channel, locale, etc.)
    tenant_context_snippet: str  # enriquecido por TenantContextService
    user_name: str            # enriquecido de User model
    user_role: str            # enriquecido de User model
    skip_memory_persist: bool  # True em calls programáticos (evita loop de memória)
    
# Mapeamento page → context_type:
PAGE_TO_CONTEXT_TYPE = {
    "sourcing": "talent_funnel",   "pipeline": "pipeline",
    "job": "job_management",       "analytics": "analytics",
    "settings": "company_settings", "global": "general",
    "Vagas": "job_management",     "Candidatos": "talent_funnel",
    # ... + aliases em PT-BR
}
```

### Pipeline de 4 fases — MainOrchestrator.process()

```
PRÉ-CHECKS (antes de qualquer fase):
  1. SecurityPatterns.check_input_security(message)
     → is_blocked → retorna ChatResponse(success=False, agent_used="security_patterns")
  2. FairnessGuard.check(message)  ← L1+L2 (regex + lexical)
     → is_blocked → retorna ChatResponse(success=False, agent_used="fairness_guard")
  3. FairnessGuard.check_implicit_bias(message) → soft_warnings (advisory, não bloqueia)
  4. TenantContextService.get_context(company_id) → ctx.tenant_context_snippet
  5. RecruiterPersonalizationService → ctx.extra["recruiter_context"]
  6. User lookup (nome + role) → ctx.user_name, ctx.user_role

MEMORY SETUP (LIA-M01 — antes de qualquer fase):
  _setup_conversation_memory(ctx, conv_id, db) → persiste mensagem do usuário
  → ctx.extra["conversation_history"], ctx.extra["conversation_summary"]

PHASE 0 — PendingAction:
  _handle_pending_action(ctx, conv_id)
  → pending_action_store.get(session_id) → ação aguardando confirmação?
     SIM → is_confirmation(message)? → executa ação pendente → ChatResponse
     SIM → is_rejection(message)? → cancela ação → ChatResponse
     SIM → aguardando params? → coleta + executa → ChatResponse
     NÃO → None (passa para Phase 1)

PHASE 1 — ActionExecutor:
  _try_action_executor(ctx, conv_id)
  → _detect_intent_from_message(message) → intent em ACTIONABLE_INTENTS?
     SIM → action_executor.try_execute(intent, entities, context) → ActionResult
       → _interpret_action_result(result) → ChatResponse
     NÃO → None (passa para Phase 1.5)
  SKIP para: context_type in {"company_settings", "settings_config", "hiring_policy"}

PHASE 1.5 — AgenticLoop (feature-flagged: LIA_AGENTIC_LOOP=true):
  → precondition_checker.check(ctx) → _proactive_hints  
  → agentic_loop.run(ctx, provider=tenant_provider) → AgenticLoopResult?
     SIM → ChatResponse
     NÃO → None (passa para Phase 2)
  SKIP para: context_type in {"company_settings", "settings_config", "hiring_policy"}

PHASE 2 — CascadedRouter:
  _process_via_orchestrator(ctx, conv_id) →
  _route_with_tenant_llm(ctx) → RouteResult →
  Orchestrator.process_request() → DomainWorkflow → ReAct Agent → ChatResponse

PÓS-PROCESSAMENTO:
  _persist_response(ctx, conv_id, conv, result, db)   ← LIA-M02
  _write_cache(cache_service, cache_key, result)       ← para _CACHEABLE_DOMAINS
  _persist_candidate_list(conv_id, result)             ← quando result contém candidates
  _audit_output(ctx, conv_id, result)                  ← C7 audit
  _inject_module_tasting_hints(result)                 ← C8 module gating hints
```

### CascadedRouter — 8 tiers (custo crescente)

```
Tier 0: MemoryResolver
  → Detecta pronomes ("ele", "aquele candidato", "essa vaga")
  → Resolve para entity_id do contexto anterior
  → Sem LLM — só lookup do UniversalContext

Tier 1: LRU in-process
  → Hash MD5 da mensagem normalizada → dict[hash → RouteResult]
  → O(1) — só para mensagens idênticas já roteadas na sessão

Tier 2: Redis hash cache
  → Hash distribuído (compartilhado entre workers)
  → Cache exato — expiração por TTL

Tier 3: VectorSemanticCache
  → pgvector cosine similarity ≥ 0.85
  → semantic_cache.py — embedding da mensagem vs. queries cached

Tier 4: FastRouter (fast_router.py)
  → regex/keyword patterns do domain_routing.yaml
  → O(n) patterns — retorna (domain, confidence, matched_pattern)
  → Threshold: confidence ≥ 0.8 para aceitar resultado

Tier 5: LLM Cascade (llm_cascade.py)
  → Haiku → Sonnet → Opus (custo crescente, qualidade crescente)
  → Usa tenant's chat provider (BYOK via get_provider_for_tenant)
  → A/B experiment: cascade_router_system_prompt (2 variantes)

Tier 6: AutonomousReActAgent
  → Fallback cross-domain quando Tier 5 não classifica com confiança
  → Agente autônomo com acesso a todas as tools

Fallback: clarification_needed
  → RouteResult(needs_clarification=True, clarification_question=..., clarification_options=[...])
  → SystemPromptBuilder.build_clarification() gera pergunta contextual
```

### ChatResponse — 20 campos

```python
# main_orchestrator.py — resposta unificada de todas as fases
class ChatResponse(BaseModel):
    success: bool
    content: str                          # mensagem ao usuário
    agent_used: str = "main_orchestrator"
    agents_consulted: list[str] = []
    intent_detected: str = "general"
    confidence: float = 1.0
    structured_data: dict | None = None   # score_breakdown, candidates, etc.
    suggested_prompts: list[str] = []     # sugestões de próximas perguntas
    actions: list[dict] = []              # ações executadas
    conversation_id: str | None = None
    ui_action: str | None = None          # ação na UI (ex: "open_panel", "navigate")
    ui_action_params: dict | None = None
    action_executed: bool = False
    action_result: dict | None = None
    action_type: str | None = None
    needs_confirmation: bool = False      # Phase 0: ação aguarda confirmação
    needs_params: bool = False            # Phase 0: aguarda parâmetros adicionais
    pending_action_id: str | None = None  # Phase 0: ID da ação pendente
    fairness_warnings: list[str] = []    # soft warnings do FairnessGuard (advisory)
    from_cache: bool = False
```

### WizardState — persistência de wizard entre turnos

```python
# wizard_state.py — Redis-backed, TTL = 7200s (2h)
@dataclass
class WizardState:
    conversation_id: str
    company_id: str
    recruiter_id: str
    draft_id: str | None
    # Campos coletados:
    title: str | None
    department: str | None
    # + outros campos do job wizard
    
# Redis key: f"wizard:{conversation_id}"
# TTL: 7200s — reset a cada update
```

### TenantBudget — controle de tokens

```python
# tenant_budget.py
# Redis keys:
#   token_budget:{company_id}:{YYYY-MM}       → int (tokens usados no mês)
#   req_cost:{company_id}:{request_id}        → hash (tokens_input, tokens_output, cost_usd)
# TTL: 32 dias (reset mensal implícito)
# Alert threshold: 80% (configurável via settings)
# Block at: 100% (tenant recebe HTTP 429)
```

### Cache de domínios específicos

```python
_CACHEABLE_DOMAINS: set[str] = {
    "analytics", "kanban_search", "kanban_insight",
    "recruiter_assistant", "pipeline_context",
}
_CACHE_TTL_BY_DOMAIN: dict[str, int] = {
    "analytics": 90,         # 90s
    "kanban_search": 60,     # 60s
    "kanban_insight": 120,   # 120s
    "recruiter_assistant": 300,  # 5min
    "pipeline_context": 60,  # 60s
}
```

### Side effects

- **Audit log** (C7): `_audit_output()` chama `AuditCallback` com `ctx`, `result`
- **Métricas** (I5): performance por domain em `_perf_metrics` dict (últimos 100 → avg/p95 ms)
- **Memória** (P3): mensagem + resposta persistidas em `conversation_memory` table (LIA-M01/M02)
- **TenantBudget**: tokens incrementados no Redis a cada chamada LLM com custo
- **A/B Testing** (R2): `cascade_router_system_prompt` experiment com 2 variantes no Tier 5

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| SecurityPatterns bloqueia input | ChatResponse `success=False, agent_used="security_patterns"` + log WARNING |
| FairnessGuard bloqueia (C1) | ChatResponse `success=False, agent_used="fairness_guard"` + mensagem educativa |
| Todos os 8 tiers falham | RouteResult `needs_clarification=True` → pergunta ao usuário |
| TenantBudget 100% | HTTP 429 antes de entrar no pipeline |
| Phase 1.5 timeout | `asyncio.wait_for(timeout=X)` → passa para Phase 2 |
| Memory persist falha (LIA-M01/M02) | Log WARNING + continua (não bloqueia resposta) |

---

## Instruções para Claude Code / Cursor

### "Implementa Orchestration no v5"

```
1. COPIE app/orchestrator/ completo:
   cp -r app/orchestrator/ <v5>/app/orchestrator/

2. GARANTA que UniversalContext recebe company_id DO JWT:
   # context_adapter.py deve pegar company_id de request.state.company_id
   # NUNCA de request.body ou query param (anti-IDOR, C5)

3. REGISTRE FairnessGuard no __init__ do MainOrchestrator:
   from app.shared.compliance.fairness_guard import FairnessGuard
   self._fairness_guard = FairnessGuard()
   # OBRIGATÓRIO — sem FairnessGuard o orchestrator não pode ser chamado

4. CONFIGURE CascadedRouter com domain_routing.yaml:
   fast_router = FastRouter(routing_config_path="app/orchestrator/config/domain_routing.yaml")

5. CONFIGURE caches:
   # Tier 2: Redis (app/core/redis_client.py)
   # Tier 3: SemanticCache (pgvector — requer migrations I9)
   # Tier 1: LRU in-process (sem config — automático)

6. FEATURE FLAGS necessários:
   LIA_AGENTIC_LOOP=true       # Fase 1.5 ligada/desligada
   LIA_AGENTIC_INTERPRET=true  # Interpretação LLM de resultados de ação

7. INTEGRE com API Layer (I6):
   from app.orchestrator.main_orchestrator import MainOrchestrator, UniversalContext
   orchestrator = MainOrchestrator()
   ctx = UniversalContext(message=..., company_id=request.state.company_id, ...)
   response = await orchestrator.process(ctx, db)

8. CONFIGURE TenantBudget:
   # Redis key: token_budget:{company_id}:{YYYY-MM}
   # TENANT_TOKEN_BUDGET_ALERT_THRESHOLD=0.8
   # TENANT_TOKEN_BUDGET_HARD_LIMIT=1000000  # tokens/mês

9. VERIFIQUE:
   - pytest tests/unit/test_main_orchestrator.py
   - pytest tests/integration/test_cascade_routing.py
   - pytest tests/integration/test_pending_action.py
```

### "Adiciona novo contexto de roteamento"

```
1. Adicione mapeamento em PAGE_TO_CONTEXT_TYPE (context_adapter.py):
   "nova_pagina": "meu_dominio",

2. Adicione patterns no domain_routing.yaml para o novo domínio

3. Registre agente no agents_registry.yaml (I1) se há ReAct agent

4. Se contexto deve pular ActionExecutor, adicione em _DOMAIN_SPECIFIC_CONTEXTS:
   _DOMAIN_SPECIFIC_CONTEXTS = {"company_settings", "hiring_policy", "meu_dominio"}

5. Se resultado deve ser cacheado, adicione em _CACHEABLE_DOMAINS + TTL
```

### Setup em CLAUDE.md

```markdown
## Infrastructure: Orchestration (I3)

- **Entry point único:** `MainOrchestrator.process(ctx, db)` → ChatResponse
- **Pipeline:** SecurityPatterns → FairnessGuard → Memory → Phase0 → Phase1 → Phase1.5 → Phase2
- **8-tier cascade:** LRU → Redis → pgvector → FastRouter → LLM Haiku→Sonnet→Opus → Autonomous → clarification
- **company_id:** Em UniversalContext SEMPRE de request.state.company_id (JWT, nunca body)
- **FairnessGuard pré-check:** Obrigatório antes de qualquer fase (bloqueio + soft warnings)
- **PendingAction:** Confirmações multi-turno persistidas em Redis entre requests
- **TenantBudget:** Tokens rastreados no Redis; block a 100%, alert a 80%
- **Feature flags:** LIA_AGENTIC_LOOP, LIA_AGENTIC_INTERPRET

Consultar `themes/infrastructure/I3_ORCHESTRATION.md`.
```

### Setup em `.cursor/rules/orchestration.mdc`

```
---
description: "I3 Orchestration"
alwaysApply: false
---

Quando o usuário pedir para:
- Adicionar novo domínio de roteamento
- Modificar o pipeline de processamento
- Adicionar nova fase ao orchestrator
- Debugar por que uma mensagem foi para o agente errado

1. Leia themes/infrastructure/I3_ORCHESTRATION.md
2. Nunca bypassar FairnessGuard ou SecurityPatterns pré-checks
3. company_id sempre de UniversalContext.company_id (vem do JWT)
4. Novo domínio: PAGE_TO_CONTEXT_TYPE + domain_routing.yaml + agents_registry.yaml
5. Checar qual fase está tratando: logs [MainOrchestrator] Phase X
6. CascadedRouter: cada tier tem log de qual resolveu (source no RouteResult)
```

---

## TastingEngine — Hints Proativos de Módulos

**Arquivo:** `app/orchestrator/tasting_engine.py` (520L)

O `TastingEngine` gera **insights proativos** de funcionalidades premium (módulos BETA) com base nas mensagens e contexto da sessão. Chamado pelo `MainOrchestrator._inject_module_tasting_hints()` após a Fase 2 da resposta.

### `TastingInsight` dataclass

```python
@dataclass
class TastingInsight:
    module_name: str    # "talent_intelligence_pro" | "internal_mobility"
    module_label: str   # "Talent Intelligence Pro" | "Internal Mobility Suite"
    insight_type: str   # "skill_gap" | "market_intelligence" | "internal_mobility"
    summary: str        # texto markdown com insight (pode ter **bold**)
    cta: str            # call-to-action para ativar o módulo
    context_key: str    # chave de dedup (por company + candidate/job + tipo)
    badge: str = "BETA"
```

### Triggers de insights (lógica de disparo)

`generate_insights()` combina `f"{ctx_intent} {ctx_domain} {ctx_message}".lower()` em `signals` e testa contra 3 pattern sets:

| Pattern set | Insight gerado | Módulo |
|-------------|---------------|--------|
| `_CANDIDATE_ANALYSIS_PATTERNS` | skill_gap | Talent Intelligence Pro |
| `_JOB_SALARY_PATTERNS` | market_intelligence | Talent Intelligence Pro |
| `_INTERNAL_MOBILITY_PATTERNS` | internal_mobility | Internal Mobility Suite |

Máximo **2 insights** por chamada. Cada insight é deduplicado por `_FrequencyCache` antes de ser retornado.

### Cache de dedup (`_FrequencyCache`)

```python
_DISPLAY_TTL_SECONDS = 86400    # 24h antes de reexibir o mesmo insight
_INSIGHT_TIMEOUT_SECONDS = 5    # asyncio.wait_for por generator

# context_key por tipo:
# skill_gap:          "skill_gap:{company_id}:{candidate_id}:{job_id}"
# market_intel:       "market_intel:{company_id}:{job_id or title or 'none'}"
# internal_mobility:  "internal_mobility:{company_id}:{job_id or 'none'}"
```

Purge automático quando cache excede 5.000 entradas (remove > TTL).

### Formato de output

```python
format_tasting_block(insights: list[TastingInsight]) -> str
# Renderiza como markdown: "🧪 **[BETA]** ..."
# Appended ao content da ChatResponse (campo tasting_insights não forwarded via WS ainda)
```

### Multi-tenancy

- `company_id` obrigatório — `generate_insights()` retorna `[]` imediatamente se ausente
- Sem feature flags por módulo neste arquivo — disponibilidade é implícita pelo pattern que dispara

### Singleton

```python
tasting_engine = TastingEngine()  # singleton de módulo
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- TTLs de cache (`_CACHE_TTL_BY_DOMAIN`)
- `_CACHEABLE_DOMAINS` (adicionar/remover domínios cacheáveis)
- Threshold de confiança do FastRouter (0.8 é sugestão)
- Tier ordering (mas custo crescente deve ser mantido)
- `LIA_AGENTIC_LOOP` flag (pode desabilitar Fase 1.5)
- Budget thresholds (80% alert, 100% block)
- `WizardState` fields (específicos do produto)

### NÃO pode adaptar

| Invariante | Por quê | Consequência |
|-----------|---------|--------------|
| FairnessGuard pré-check ANTES de qualquer fase | Discriminação pode entrar em qualquer fase (C1) | Mensagem discriminatória processada por tool/LLM |
| SecurityPatterns ANTES de FairnessGuard | Prompt injection pode confundir FairnessGuard | Injection bypassa fairness check |
| `company_id` de UniversalContext (JWT) | Multi-tenancy (C5) — orchestrator não pode confiar no body | Dados de tenant A acessados por tenant B |
| Memory persist (LIA-M01) ANTES de qualquer fase | Se Phase 0 responde, a mensagem já está persistida | Mensagens perdidas em crash de Phase 0/1 |
| `needs_clarification` antes de AutonomousAgent | Autonomous é caro — clarificação é mais barata | Custo LLM desnecessário em mensagens ambíguas |
| TenantBudget block a 100% | Billing protection — tenant não pode consumir além do limite | Custo infinito sem controle |

---

## Execution Planning — Planos Multi-Step de Linguagem Natural

> **Verificado via SSH 2026-04-24.** Fontes: `app/shared/execution/` — 5 arquivos, 1.259 linhas total.

O módulo `app/shared/execution/` transforma mensagens de linguagem natural em **planos de execução DAG** de múltiplas tarefas de domínio, com retry, rollback e templates pré-definidos.

Usado pelo Orchestrator quando o `PlanDetector` identifica que uma mensagem contém um padrão de **"A e B"** — ex.: "triar candidatos e agendar entrevistas".

### Hierarquia de Classes

```
PlanExecutor          (plan_executor.py — base)
  └── ActionPlanner   (action_planner.py — retry + rollback)
```

### Arquivos e Responsabilidades

| Arquivo | Linhas | Responsabilidade |
|---------|:---:|-----------------|
| `execution_plan.py` | 154 | `ExecutionPlan` + `AgentTask` + `TaskStatus` + `PlanStatus` |
| `plan_executor.py` | 436 | `PlanExecutor`: execução serial/DAG, condições, context resolution, `execute_crew()` |
| `plan_detector.py` | 345 | `PlanDetector` + `PLAN_PATTERNS` (8 regex) → `ExecutionPlan` |
| `action_planner.py` | 195 | `ActionPlanner(PlanExecutor)`: `RetryPolicy` + `RollbackHook` + backoff |
| `plan_templates.py` | 124 | `PlanTemplateRegistry`: 4 templates pré-definidos |
| `__init__.py` | 5 | Package init |

### ExecutionPlan + AgentTask

```python
# execution_plan.py

class TaskStatus(StrEnum):
    PENDING | RUNNING | COMPLETED | FAILED | SKIPPED

class PlanStatus(StrEnum):
    PENDING | IN_PROGRESS | COMPLETED | PARTIAL | FAILED

@dataclass
class AgentTask:
    task_id: str
    domain_id: str          # ex: "cv_screening", "sourcing"
    action_id: str          # ex: "screen_candidates", "search_top"
    params: dict            # parâmetros passados ao domain.execute_action()
    depends_on: list[str]   # IDs de tasks predecessoras (DAG)
    status: TaskStatus = PENDING
    result: Any = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 1
    is_critical: bool = True       # True → falha cancela plano; False → skip
    context_mappings: dict = {}    # {"param_key": "task_id.result_key"}
    condition: str | None = None   # ex: "task_0.match_score >= 40"

class ExecutionPlan:
    plan_id: str            # uuid4()[:8]
    tasks: list[AgentTask]
    status: PlanStatus
    context_data: dict      # dados compartilhados entre tasks
    detected_pattern: str   # nome do PLAN_PATTERN que gerou o plano

    def get_next_tasks() -> list[AgentTask]:
        """Tasks prontas: status=PENDING e todas as deps COMPLETED."""

    def inject_context(key, value) -> None   # compartilha dados entre tasks
    def get_context(key, default) -> Any
    def get_summary() -> dict                # plan_id, status, counts, durations
```

### PlanDetector + PLAN_PATTERNS (8 padrões)

```python
# plan_detector.py
PLAN_PATTERNS: list[PlanPattern] = [
    PlanPattern(
        name="buscar_e_comparar",
        patterns=[r"buscar?\s+.*\s+e\s+comparar?", ...],
        pipeline=[
            PipelineStep("sourcing", "search_candidates"),
            PipelineStep("sourcing", "compare_candidates", context_from="task_0.candidate_ids"),
        ]
    ),
    # + 7 outros:
    # buscar_top_e_detalhar  → search_top + show_candidate_details
    # gerar_jd_e_avaliar     → generate_jd + evaluate_against_jd
    # triagem_e_agendar      → screen_candidates + schedule_interview
    # avaliar_e_notificar    → evaluate_candidate + send_notification
    # filtrar_e_reportar     → filter_candidates + generate_report
    # criar_vaga_e_publicar  → create_job + sync_job
    # analisar_e_planejar    → analyze_funnel + plan_next_steps
]
```

**Fluxo de detecção:**
```
user_message → PlanDetector.detect(message)
  → testa cada PLAN_PATTERN.patterns (regex)
  → primeiro match: gera ExecutionPlan com tasks do pipeline
  → plan.detected_pattern = nome do padrão
  → retorna ExecutionPlan | None (None = sem padrão detectado)
```

### PlanExecutor — Loop de Execução

```python
# TASK_TIMEOUT_SECONDS = 15  (por task)

async def execute(plan, user_id, session_id, tenant_id, base_context, progress_callback):
    plan.status = PlanStatus.IN_PROGRESS
    iteration_limit = len(plan.tasks) * 3

    while not plan.is_complete and iterations < iteration_limit:
        next_tasks = plan.get_next_tasks()   # tasks com deps satisfeitas

        if not next_tasks:
            # deps com falha → FAILED (is_critical) ou SKIPPED (não crítico)
            resolve_blocked_tasks(plan)
            continue

        for task in next_tasks:
            await _execute_task(task, plan, ...)   # chama domain.execute_action()

    # Resolução final: COMPLETED / PARTIAL / FAILED
```

**Condições em tasks (`_safe_eval_condition`):**
```python
# condition: "task_0.match_score >= 40"
# AST-based safe eval (NÃO usa eval() — sem risco de injeção)
_safe_eval_condition("task_0.match_score >= 40", ctx={"task_0": {"match_score": 75}})
# → True
# Suporta: >, >=, <, <=, ==, !=, and, or
```

**Context resolution (`_resolve_context_path`):**
```python
# context_from="task_0.candidate_ids" → plan.get_task("task_0").result["candidate_ids"]
# Injetado em task.params antes de chamar domain
```

### ActionPlanner — Retry + Rollback

```python
# action_planner.py

@dataclass
class RetryPolicy:
    max_retries: int = 2
    backoff_type: str = "exponential"   # "exponential" | "linear" | "fixed"
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0

    def get_delay(attempt: int) -> float:
        # exponential: base * 2^(attempt-1), capped at max_delay

@dataclass
class RollbackHook:
    task_id: str        # qual task disparou o rollback
    action_id: str      # ação de rollback a executar
    domain_id: str      # domain responsável
    params: dict

# Fluxo de rollback:
# critical task FAILED → _rollback_completed_tasks (reverse order)
# → chama domain.execute_action(rollback_action_id)
# → _mark_remaining_as_blocked(plan, failed_task_id)
```

### PlanTemplateRegistry — 4 Templates Pré-definidos

| Template | Descrição | Tasks | Critical? |
|----------|-----------|:---:|:---------:|
| `schedule_interviews_batch` | Agendar entrevistas em lote para finalistas | 5 | parcial |
| `batch_rejection_feedback` | Feedback personalizado para reprovados | 4 | parcial |
| `advance_top_candidates` | Mover candidatos com score alto para próxima etapa | 4 | todas |
| `sourcing_expansion` | Expandir sourcing quando funil está fraco | 4 | parcial |

```python
# Uso:
plan = PlanTemplateRegistry.build_plan("schedule_interviews_batch", params={"vacancy_id": "..."})
planner = PlanTemplateRegistry.build_planner("schedule_interviews_batch", domain_registry=..., domain_workflow=...)
result = await planner.execute(plan, user_id="...", tenant_id=company_id)
report = planner.get_execution_report(plan)
```

### Relação com I3 Orchestration

```
MainOrchestrator.process()
  ├── PlanDetector.detect(message)        → detecta padrão "A e B"
  │     └── retorna ExecutionPlan | None
  ├── Se plan → ActionPlanner.execute(plan, tenant_id=company_id)
  │     └── PlanExecutor loop → chama cada domain.execute_action()
  └── PlanExecutor.build_consolidated_response(plan)
        └── merges task results → DomainResponse para o ChatResponse
```

**Boundary:** `PlanDetector` roda **antes** do `CascadedRouter` (é detectado no pre-processing do Orchestrator). Se nenhum padrão detectado, o fluxo segue o cascade normal.

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `FairnessGuard.check()` chamado no início de `process()` (antes de qualquer fase)
- [ ] **(P0)** `SecurityPatterns.check_input_security()` chamado antes do FairnessGuard
- [ ] **(P0)** `UniversalContext.company_id` populado EXCLUSIVAMENTE do JWT
- [ ] **(P0)** `_setup_conversation_memory()` (LIA-M01) antes das 4 fases
- [ ] **(P0)** `PendingActionStore` funcional (Phase 0 responde a confirmações multi-turno)
- [ ] **(P0)** `ActionExecutor.ACTIONABLE_INTENTS` configurado com intents do produto
- [ ] **(P0)** `CascadedRouter` com todos os 8 tiers inicializados
- [ ] **(P0)** `FastRouter` lê `domain_routing.yaml` na startup
- [ ] **(P1)** `SemanticCache` (Tier 3) configurado com pgvector (migrations I9)
- [ ] **(P1)** `TenantBudget` rastreando tokens no Redis (alert 80% + block 100%)
- [ ] **(P1)** `WizardState` com TTL=2h no Redis para wizard job creation
- [ ] **(P1)** `LIA_AGENTIC_LOOP=true` testado em staging antes de habilitar em prod
- [ ] **(P1)** `_CACHEABLE_DOMAINS` com TTLs apropriados para cada domínio
- [ ] **(P2)** A/B experiment `cascade_router_system_prompt` configurado (R2)
- [ ] **(P2)** `get_perf_summary()` exposto em endpoint de admin (I5)
- [ ] **(P2)** `ChatResponse.fairness_warnings` propagado para o frontend

---

## Gotchas e erros comuns

| Sintoma | Causa | Como evitar |
|---------|-------|-------------|
| Mensagem vai para domínio errado | Tier 4 (FastRouter) tem padrão muito genérico | Ver log `[CascadedRouter] Tier 4 matched` + ajustar regex em domain_routing.yaml |
| FairnessGuard bloqueia mensagem legítima | Regex muito abrangente na categoria errada | Testar com `fairness_guard.check()` diretamente; ajustar threshold L1 |
| Phase 0 responde quando não deveria | PendingAction preso no Redis sem expirar | Verificar TTL do PendingActionStore; inspecionar `pending_action_store` |
| company_id vazio no orchestrator | `UniversalContext` populado antes de `request.state.company_id` ser setado | Verificar ordem de middleware: AuthEnforcement → TenantGuard → Orchestrator |
| Cache retorna resultado de outro tenant | Cache key não inclui `company_id` | Sempre incluir `company_id` na composição de cache keys |
| Phase 1.5 timeout (AgenticLoop) | Tool call lenta sem timeout | Verificar `asyncio.wait_for` na Fase 1.5; ajustar timeout |
| Billing alert nunca dispara | `TenantBudget` não está sendo chamado após LLM calls | Verificar se `_try_cache_lookup` e `_route_with_tenant_llm` registram custo |
| Clarification loop infinito | Clarification response tratada como nova mensagem que também gera clarification | Garantir que `ChatResponse.needs_clarification=True` não re-entra no pipeline |

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| FairnessGuard bloqueio | `tests/unit/test_main_orchestrator.py` | Mensagem com atributo protegido → `agent_used="fairness_guard"` |
| SecurityPatterns bloqueio | `tests/unit/test_main_orchestrator.py` | Prompt injection → `agent_used="security_patterns"` |
| Phase 0 confirmação | `tests/unit/test_pending_action.py` | "sim" após ação pendente → ação executada |
| Phase 1 intent detection | `tests/unit/test_action_executor.py` | "mover candidato X para entrevista" → `action_executed=True` |
| Phase 2 cascade | `tests/integration/test_cascade_routing.py` | Mensagem não-trivial → RouteResult com domain correto |
| Tenant isolation | `tests/unit/test_main_orchestrator.py` | company_id no ctx ≠ company_id em cache → cache miss |
| Memory persist (LIA-M01) | `tests/integration/test_conversation_memory.py` | `process()` → mensagem salva na DB |
| TenantBudget block | `tests/unit/test_tenant_budget.py` | Budget 100% → HTTP 429 antes de entrar no pipeline |
| CascadedRouter 8 tiers | `tests/unit/test_cascaded_router.py` | Mock cada tier → verificar qual resolve + source no RouteResult |
| company_id JWT only | `tests/unit/test_context_adapter.py` | body.company_id ≠ JWT.company_id → ctx usa JWT value |

---

## Referências

### Bundles verbatim
- `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md` — `technical_config/domain_routing.yaml`

### Reconstruction guides
- `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` §E (Orchestration + CascadedRouter)

### Cross-references
- **I1 Agent Architecture** — `ReactAgentRegistry` usado em Fase 2
- **I2 Tool Architecture** — `ActionExecutor` chama tools (Phase 1); ReAct loop via tools (Phase 2)
- **I4 LLM Providers** — `get_provider_for_tenant(company_id)` no Tier 5 (BYOK)
- **I7 Intent Routing** — `FastRouter` (Tier 4) consome `intent_classification.yaml` + `capabilities.yaml`
- **I9 Data Layer** — SemanticCache usa pgvector (migration necessária)
- **C1 Fairness** — FairnessGuard obrigatório no início de `process()`
- **C5 Multi-tenancy** — TenantGuard garante company_id antes do orchestrator
- **C7 Audit Trail** — `_audit_output()` registra cada request/response
- **C8 Policy Engine** — PolicyMiddleware injeta policy em `request.state` antes do orchestrator
- **P3 Memory** — `_setup_conversation_memory()` + `_persist_response()` (LIA-M01/M02)
- **R2 Learning** — A/B experiment no Tier 5 (cascade_router_system_prompt)

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit*
