# TARGET_ARCHITECTURE.md — Arquitetura Alvo (Estado Desejado)
**Protocolo:** P21  
**Data:** 2026-04-14  
**Arquiteto:** Claude Opus 4.6  
**Baseado em:** 27 documentos de auditoria (P01-P20, PX01-PX07, P15)  
**Contexto:** Frontend + IA no Replit, Backend Rails no GCP. Integracao Rails<>Python via RabbitMQ. Redis/RabbitMQ sendo configurados no GCP.

**Depende de:** P01-P20 (todos os diagnosticos)  
**Alimenta:** P22-P26, P32

---

## PRINCIPIOS ARQUITETURAIS

1. **Compliance-by-construction:** Impossivel que um agente opere sem FairnessGuard + LGPD + PII strip. Enforcement via heranca obrigatoria (ComplianceDomainPrompt), nao convencao.
2. **Trace-through:** Cada acao de cada agente e parte de um trace E2E (request_id -> session -> agent -> tool -> response).
3. **Genuinely intelligent:** Agentes raciocinam, planejam, pedem clarificacao. Nunca respostas genericas quando dados existem.
4. **Modular by default:** Adicionar agente/tool/integracao segue pattern consistente sem reescrever infra.
5. **Single source of truth:** CRUD no Rails (GCP), IA no Python (Replit/GCP). Nunca dados duplicados.
6. **Tenant isolation total:** Company_id enforced em todas as camadas — DB, cache, LLM, budget, guardrails.

---

## A. ARQUITETURA DE AGENTES

### A.1 Registry de Agentes

**Estado atual:** `@register_domain` decorator com `_DOMAIN_REGISTRY` dict. ComplianceDomainPrompt enforced via `LIA-C01` (blocking).

**Estado alvo:** Manter pattern atual — e sofisticado e funciona. Adicionar:

```python
# Adicoes ao registro existente:

@register_domain
class SourcingDomain(ComplianceDomainPrompt):
    domain_id = "sourcing"
    domain_version = "2.1.0"        # NOVO: versionamento semantico
    capabilities = ["search", "enrich", "rank"]  # NOVO: capability discovery
    _compliance_config = {
        "high_impact": True,
        "fairness_action_type": "sourcing",
        "requires_calibration": True,  # NOVO: flag que ativa CalibrationWeight consumption
    }
```

**Migration path:** Adicionar `domain_version` e `capabilities` aos 63 dominios existentes. Backward-compatible (campos opcionais).

### A.2 Padrao de Agente (Contrato)

**Estado atual:** `AgentInterface` ABC com `AgentInput/AgentOutput`. `LangGraphReActBase` como base para ReAct agents. `EnhancedAgentMixin` para memory/learning.

**Estado alvo:** Manter stack atual. E madura. Consolidar em 2 paths:

```
Path 1: ReAct Agent (raciocinio + tools)
  LangGraphReActBase + EnhancedAgentMixin + ComplianceDomainPrompt
  → Para: sourcing, pipeline, wizard, communication, analytics, automation

Path 2: StateGraph Agent (maquina de estados)
  LangGraphBase + ComplianceDomainPrompt
  → Para: interview_scheduling, onboarding, cv_screening_batch

Path 3: Custom Agent (Agent Studio)
  CustomAgentRuntime + EnhancedAgentMixin + ComplianceDomainPrompt
  → Para: agentes criados por tenants
```

**Contrato unificado:**
```python
class AgentContract:
    # Input
    input: AgentInput  # message, context, session_id, company_id, user_id

    # Output
    output: AgentOutput  # content, actions, metadata, fairness_warnings

    # Lifecycle hooks (NOVO)
    async def before_process(self, input: AgentInput) -> AgentInput:
        """Pre-processing: CalibrationWeight loading, memory enrichment."""

    async def after_process(self, output: AgentOutput) -> AgentOutput:
        """Post-processing: learning extraction, feedback recording."""
```

### A.3 Middleware Pipeline

**Estado atual:** FairnessGuard pre-check no MainOrchestrator. PII strip no LangGraphReActBase. PromptInjection guard no AuthEnforcementMiddleware.

**Estado alvo:** Pipeline explicito, impossivel de bypassar:

```
Request
  → AuthEnforcementMiddleware (JWT + company_id + prompt injection guard)
  → RateLimitMiddleware (per-tenant Redis)
  → RequestIdMiddleware (trace ID)
  → MainOrchestrator
      → FairnessGuard.pre_check (BLOCKING se bias detectado)
      → TenantContext enrichment (LLM config, budget, guardrails)
      → CalibrationWeight.load(company_id)  ← NOVO: fecha loop P19
      → CascadedRouter → DomainWorkflow → Agent
          → PII strip antes do LLM (LIA-C04)
          → FairnessGuard.post_check no output ← NOVO: bias no output
          → LearningExtractor.extract (EnhancedAgentMixin)
          → CalibrationEvent.record ← NOVO: fecha loop P19
  → Response
```

**Design decision:** Middleware no Python (nao no frontend) porque e o unico ponto que todos os agentes atravessam. Frontend e proxy.

### A.4 Memoria

**Estado atual:** WorkingMemoryService (sessao) + LongTermMemoryService (cross-sessao) + PostgresSaver (checkpointer LangGraph).

**Estado alvo:** 4 camadas de memoria (ja parcialmente implementadas):

| Camada | Storage | TTL | Escopo | Status |
|--------|---------|-----|--------|--------|
| **Working Memory** | In-process + Redis | Sessao | Sessao ativa | IMPLEMENTADO |
| **Episodic Memory** | PostgreSQL | 90 dias | Por recrutador + vaga | IMPLEMENTADO (LongTermMemory) |
| **Semantic Memory** | pgvector | Permanente | Por tenant | IMPLEMENTADO (VectorSemanticCache, JobEmbeddings) |
| **Procedural Memory** | CalibrationWeight + FeedbackLearning | Permanente | Por tenant | PARCIAL → FECHAR LOOP |

**NOVO - Fechar o loop procedural:**
```python
# Em cada agente que faz scoring:
async def before_process(self, input: AgentInput) -> AgentInput:
    weights = await CalibrationService.get_weights(input.company_id)
    input.context["calibration_weights"] = weights
    return input

# Apos cada interacao:
async def after_process(self, output: AgentOutput) -> AgentOutput:
    if output.action_executed and output.metadata.get("candidate_id"):
        await CalibrationService.record_implicit_feedback(...)
    return output
```

### A.5 Comunicacao entre Agentes

**Estado atual:** Agentes nao se comunicam diretamente. MainOrchestrator roteia. Eventos via RabbitMQ (Python → Rails).

**Estado alvo:** Manter pattern hub-and-spoke (MainOrchestrator como hub). NAO adicionar comunicacao P2P entre agentes — complexidade desnecessaria. Adicionar:

1. **Event bus interno** (Python): Para eventos leves (screening_completed → pipeline_advance). Usar Redis Pub/Sub.
2. **Event bus externo** (Rails): RabbitMQ existente. Implementar 6 handlers stub do LiaEventsWorker.

---

## B. ORQUESTRACAO

### B.1 Graph Engine

**Estado atual:** LangGraph (ReAct prebuilt + StateGraph custom). CascadedRouter 8 tiers.

**Estado alvo:** Manter LangGraph. E a escolha correta.

**Justificativa:** LangGraph ja e usado em todos os agentes (15+). Mudar framework agora nao traz beneficio. CascadedRouter de 8 tiers e sofisticado e reduce LLM calls em 40-60%.

### B.2 State Schema

**Estado atual:** `UniversalContext` como state object + `ChatResponse` como output.

**Estado alvo:** Formalizar schema com campos obrigatorios:

```python
class OrchestrationState(BaseModel):
    # Identifiers (OBRIGATORIOS)
    request_id: str
    session_id: str
    company_id: str
    user_id: str
    conversation_id: str | None

    # Routing
    domain_id: str | None
    route_confidence: float = 0.0
    route_source: str = ""  # tier que resolveu

    # Compliance (OBRIGATORIOS — nunca None)
    fairness_result: FairnessResult
    pii_stripped: bool = False
    calibration_weights: dict | None = None

    # Memory
    working_memory: dict = {}
    episodic_context: str = ""
    semantic_matches: list = []

    # Execution
    agent_actions: list[AgentAction] = []
    tool_calls: list[dict] = []
    plan_steps: list[dict] = []

    # Output
    response: str = ""
    structured_data: dict | None = None
    fairness_warnings: list[str] = []
    navigation_hint: dict | None = None
```

### B.3 Routing

**Estado atual:** CascadedRouter 8 tiers. Funciona bem.

**Estado alvo:** Manter. Adicionar:
- **Tier 3.5:** CalibrationWeightRouter — se vaga tem calibracao ativa, roteia para dominio com weights pre-carregados
- **Analytics no router:** Registrar metricas de qual tier resolveu (para otimizar)

### B.4 Human-in-the-Loop

**Estado atual:** `PendingAction` no MainOrchestrator + `approval_required` event via WS + UI de approve/reject.

**Estado alvo:** Manter. E completo. Adicionar:
- **Timeout configuravel por tenant** (hoje e infinito — se recrutador nao responde, acao fica pendente para sempre)
- **Escalation path:** Se HITL timeout > 4h, notificar via bell + email

### B.5 Escalation

**Estado atual:** AutonomousReActAgent como Tier 6 (fallback). Clarification como ultimo recurso.

**Estado alvo:** Manter cascade existente. Adicionar:
- **Confidence-based escalation:** Se agente retorna confidence < 0.5, nao executa — pede confirmacao HITL
- **Error escalation:** Se tool call falha 2x, escala para humano em vez de retry infinito

---

## C. INFRAESTRUTURA CROSS-CUTTING

### C.1 Fairness-as-Middleware

**Estado atual:** FairnessGuard pre-check no MainOrchestrator. FairnessGuard post-check no CustomAgentRuntime (Studio).

**Estado alvo:** FairnessGuard pre + post em TODOS os agentes (nao apenas Studio):

```python
class ComplianceDomainPrompt(DomainPrompt):
    async def execute_action(self, action_id, params, context):
        # PRE: FairnessGuard on input
        fg_input = FairnessGuard().check(str(params))
        if fg_input.is_blocked:
            return DomainResponse.blocked(fg_input.educational_message)

        result = await self._execute_action_impl(action_id, params, context)

        # POST: FairnessGuard on output ← NOVO para todos
        fg_output = FairnessGuard().check(result.message)
        if fg_output.soft_warnings:
            result.fairness_warnings = fg_output.soft_warnings

        return result
```

**Migration path:** ComplianceDomainPrompt ja existe e e enforced. Adicionar post-check e backward-compatible.

### C.2 LGPD Enforcement Layer

**Estado atual:** PII masking em logs, Sentry, LLM prompts. Data subject requests. Consent management.

**Estado alvo:** Adicionar:
- **candidates.account_id** (BLK-01 do PX07) — pre-requisito para qualquer enforcement
- **Automatic data retention cleanup** (Celery beat task ja existe — verificar execucao)
- **Consent-aware agent:** Agentes verificam consentimento antes de processar dados do candidato

### C.3 Observability Stack

**Estado atual:** Structured JSON logging + Sentry (Python) + OTEL configurado mas vazio + Flower (Celery).

**Estado alvo:**

| Camada | Ferramenta | Status Atual | Alvo |
|--------|-----------|-------------|------|
| **Logging** | Structured JSON + PIIMasking | ATIVO | Manter + CloudLogging GCP |
| **Error tracking** | Sentry (Python + Frontend) | PARCIAL (DSN ausente) | Configurar DSN em prod |
| **Tracing** | OTEL (endpoint vazio) | INATIVO | GCP Cloud Trace ou Jaeger |
| **Metrics** | Nenhum (Prometheus removido) | INATIVO | GCP Cloud Monitoring ou OTEL metrics |
| **LLM tracing** | LangSmith (desabilitado) | INATIVO | Habilitar em staging |
| **Celery monitoring** | Flower | PARCIAL | Manter + alertas |
| **Agent quality** | agent_quality.py (API existe) | SEM DASHBOARD | Criar dashboard |

### C.4 Evaluation Framework

**Estado atual:** Nao existe formalmente. Calibration e manual.

**Estado alvo:**

```
Avaliacao Continua de Agentes:
  1. Metricas automaticas (por agente):
     - Acceptance rate (CalibrationService — ja coleta)
     - Tool call success rate (AuditCallback — ja registra)
     - Response latency (perf_metrics — ja coleta)
     - Confidence distribution (CascadedRouter — ja registra)

  2. Eval periodico (semanal):
     - Batch de queries reais → agente → score humano
     - Comparar com baseline da semana anterior
     - Flag agentes com regressao > 5%

  3. A/B testing (ja tem infra):
     - ab_testing.py existe
     - Usar para testar novos prompts/modelos por tenant
```

---

## D. PADROES DE CODIGO

### D.1 Estrutura de Diretorios Alvo

```
lia-agent-system/
  app/
    api/v1/          # REST endpoints (FastAPI routers)
    domains/         # Dominios DDD (63 dominios)
      {domain}/
        domain.py        # @register_domain class
        actions.py       # DomainAction definitions
        agents/          # ReAct/StateGraph agents
        services/        # Business logic
        repositories/    # DB queries
        config/          # YAML configs (capabilities, prompts)
    orchestrator/    # MainOrchestrator + CascadedRouter
    middleware/      # Auth, rate limit, request ID
    shared/          # Cross-cutting (compliance, providers, tools, channels)
    models/          # SQLAlchemy model shims → libs/models
    jobs/            # Celery tasks
    scripts/         # One-off scripts
  libs/
    agents-core/     # Agent interface, ReAct base, mixin
    config/          # Pydantic Settings
    models/          # SQLAlchemy models reais
  tests/             # 419 test files
  alembic/           # 76 migrations

ats-api-copia/       # Rails 7.1 (GCP)
  app/
    controllers/v1/  # CRUD controllers
    models/          # ActiveRecord models
    workers/         # Sneakers + Sidekiq workers
    services/        # Business services
  config/            # Rails config, initializers
  db/                # Migrations (85) + schema.rb

plataforma-lia/      # Next.js 15 (Replit)
  src/
    app/             # App Router (32 pages, API routes)
    components/      # UI components (55 directories)
    hooks/           # React hooks (15 directories)
    stores/          # Zustand stores (16)
    services/        # API client services
    contexts/        # React contexts (3)
    lib/             # Utilities, API helpers
```

**Design decision:** Manter estrutura atual. Ela ja segue DDD. Nao reorganizar — risco de breaking imports supera beneficio cosmetic.

### D.2 Naming Conventions

| Elemento | Pattern | Exemplo |
|----------|---------|---------|
| Domain class | `{Name}Domain(ComplianceDomainPrompt)` | `SourcingDomain` |
| ReAct agent | `{name}_react_agent.py` | `sourcing_react_agent.py` |
| Tool registry | `{name}_tool_registry.py` | `sourcing_tool_registry.py` |
| Service | `{name}_service.py` | `calibration_service.py` |
| Repository | `{name}_repository.py` | `learning_outcome_repository.py` |
| Config YAML | `capabilities.yaml` | per-domain |
| API router | `{name}.py` em app/api/v1/ | `calibration.py` |

### D.3 Padrao para Prompts

**Estado atual:** Mix de inline constants + PromptLoader + YAML capabilities.

**Estado alvo:** Centralizar em PromptLoader + YAML versionados:

```yaml
# app/domains/sourcing/config/prompts.yaml
version: "2.1"
system_prompt:
  template: |
    Voce e um especialista em sourcing de talentos...
    {tenant_context}
    {calibration_weights}
  variables:
    - tenant_context: "injected by TenantContextService"
    - calibration_weights: "injected by CalibrationService"
  a_b_variants:
    - id: "sourcing_v2_concise"
      weight: 0.3
      template: "..."
```

### D.4 Padrao para Testes

```
tests/
  unit/               # Testa funcoes isoladas (mock DB/LLM)
  integration/        # Testa com DB real (pytest-asyncio + postgres)
  e2e/                # Testa fluxos completos (API -> agente -> response)
  eval/               # NOVO: Eval de agentes (queries reais, scoring)
    eval_sourcing.py
    eval_wizard.py
    eval_screening.py
    datasets/          # Golden datasets por dominio
```

---

## E. CONTRATOS E INTERFACES

### E.1 Agent Contract

```python
# Ja implementado em libs/agents-core/agent_interface.py
AgentInput:  message, context, session_id, company_id, user_id, conversation_history, metadata
AgentOutput: content, actions, metadata, context_updates, conversation_state
```

### E.2 Tool Contract

```python
# Ja implementado em app/tools/registry.py + tool_registry_metadata.yaml
ToolDefinition:
  name: str
  description: str
  input_schema: dict (JSON Schema)
  output_schema: dict
  scope: TALENT_FUNNEL | JOB_TABLE | IN_JOB | GLOBAL
  requires_confirmation: bool
```

### E.3 Event Schema (RabbitMQ)

```python
# Estado alvo — padronizar eventos:
class PlatformEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str     # "screening.completed", "pipeline.moved", etc.
    timestamp: datetime
    company_id: str
    user_id: str | None
    payload: dict
    source: str         # "python" | "rails"
    version: str = "1.0"
```

### E.4 Error Contract

```python
# Ja implementado parcialmente em proxy-handler.ts e FastAPI
ErrorResponse:
  error: str            # Human-readable message
  error_code: str       # Machine-readable code (e.g., "TENANT_NOT_FOUND")
  details: dict | None  # Additional context
  request_id: str       # For correlation
  timestamp: str
```

---

## F. INTEGRACAO COM PLATAFORMA

### F.1 Como Agentes Consomem LLM Factory

**Estado atual:** `get_provider_for_tenant()` → `ProviderContainer` per-tenant. Funciona.

**Estado alvo:** Manter. Remover `LLMProviderFactory` deprecated (class-level global state). Todos usam `ProviderContainer`.

### F.2 Como Agentes Consomem Tenant Model

**Estado atual:** `AuthEnforcementMiddleware` → `_current_company_id` ContextVar → flui para DB, LLM, budget.

**Estado alvo:** Manter. Adicionar:
- `CalibrationWeight` carregado por tenant no inicio de cada request (before_process hook)
- `TenantPreferences` (futuro): vocabulario, tom de voz, regras de negocio por tenant

### F.3 Como ML Models Sao Consumidos

**Estado atual:** OutcomePredictor (rule-based) desconectado dos agentes. CalibrationWeight desconectado.

**Estado alvo:**

```
Agente process():
  1. before_process():
     - CalibrationWeight.load(company_id, job_id) → inject weights no context
     - OutcomePredictor.predict_time_to_fill(job_data) → inject insight no context
     - FeedbackLearningService.get_adjustments(company_id, role) → inject adjustments

  2. execute():
     - Agente usa weights/insights para decisoes
     - Tool calls incluem calibration context

  3. after_process():
     - CalibrationEvent.record(candidate_id, lia_score, action)
     - LearningExtractor.extract(state)
     - OutcomePredictor.record_prediction(model_id, predicted_value)
```

### F.4 Como Automacoes Se Integram

**Estado atual:** `automation/event_handlers/` com 4 handlers (ATS sync, interview, lifecycle, screening). `stage_transition_automation.py`.

**Estado alvo:** Manter pattern de event handlers. Adicionar:
- Automacoes disparam via event bus Redis (nao HTTP)
- Cada automacao passa pelo middleware pipeline (FairnessGuard, etc.)

---

## G. SCHEMA CANONICO DE DADOS

### G.1 Resolucao de Desalinhamentos (P17)

| Campo | Python | Rails | Frontend | Alvo (SSOT) |
|-------|--------|-------|----------|-------------|
| ID candidato | UUID | bigint | string | **UUID everywhere** — Rails adiciona `fork_uuid` column |
| Nome candidato | `full_name` | `name` | `name` | **`name`** — Python renomeia |
| Telefone | `phone` | `phone_number` | `phone` | **`phone`** — Rails renomeia |
| Score WSI | `wsi_score` (Python) | N/A | `matchScore` | **`wsi_score`** — frontend adapta |
| Status vaga | `status` enum | `status` string | `jobStatus` | **`status` enum** — Rails migra |
| Tenant ID | `company_id` | `account_id` | `companyId` | **`company_id`** — Rails renomeia em API (mantem account_id no DB por Apartment) |

### G.2 Estrategia de ID Unificado

**Decisao:** UUID como ID canonico.

```
Python: UUID nativo (ja usa)
Rails:  Manter bigint como PK interna, adicionar `fork_uuid` column indexada
Frontend: Usa UUID string
RabbitMQ: Eventos sempre incluem UUID
Mapeamento: RailsAdapter usa fork_uuid para lookup (nao bigint)
```

**Migration path:** Migration Rails `add_column :candidates, :fork_uuid, :uuid, index: true`.

---

## H. ROADMAP DE MIGRACAO (RESUMO)

### Fase A — Desbloqueadores (Semana 1-2)
Sprint 0: Config (CORS, RAILS_API_URL, JWT, MAILGUN, rotas) — ~4h
Sprint 1: Tenant isolation (account_id, schema dump, ResourceLoader) — 3-5d
Sprint 2: Workers + WebSocket (LiaEventsWorker, WSManager Redis) — 3-5d

### Fase B — Agentes (Semana 3-6)
Sprint 3: Fechar loops ML (CalibrationWeight → agents, SearchFeedback → re-ranking)
Sprint 4: CRUD migration (Python CRUD → Rails API via RAILS_API_URL)
Sprint 5: Agent eval framework + dashboards frontend (ML, calibration)
Sprint 6: Candidate lifecycle model + person concept

### Fase C — Otimizacao (Semana 7+)
CI/CD completo (Python + Frontend)
Redis HA (Sentinel/Cluster)
OpenTelemetry ativo
CSP com nonce
Cleanup (code morto, models sem tabela, pagina legacy)

---

## RESUMO EXECUTIVO

### O que ja esta certo e deve ser MANTIDO
1. **LangGraph como engine** — 15+ agentes, CascadedRouter 8 tiers, checkpointer
2. **ComplianceDomainPrompt enforced** — LIA-C01 blocking, impossivel registrar dominio sem compliance
3. **LLM Factory per-tenant** — ProviderContainer, fallback chain, budget tracking
4. **EnhancedAgentMixin** — unica capacidade real de aprendizado (nivel 3/5)
5. **BFF pattern** — 478 rotas consistentes, auth chain robusta
6. **Domain-driven design** — 63 dominios com registry automatico

### O que precisa MUDAR
1. **Fechar loops de feedback** — CalibrationWeight + SearchFeedback + OutcomePredictor consumidos pelos agentes
2. **Completar integracao Rails** — 15 bloqueadores do PX07 (Sprint 0-2)
3. **CRUD para Rails** — eliminar dados duplicados
4. **UUID como ID canonico** — resolver mismatch UUID/bigint
5. **Observability** — Sentry DSN + OTEL endpoint + Cloud Monitoring
6. **CI/CD** — pipeline para Python e Frontend (hoje so Rails tem)
7. **ML real** — treinar primeiro modelo (feature engineering pronta, faltam dados)

### Metafora final
A plataforma e como um carro de F1 com motor sofisticado (LangGraph + 15 agentes + CascadedRouter) mas chassi ainda em montagem (Rails nao integrado, feedback loops abertos, observability cego). O motor esta pronto — o trabalho e montar o chassi e conectar a telemetria. A arquitetura alvo NAO e uma reescrita — e completar a montagem do que ja existe.
