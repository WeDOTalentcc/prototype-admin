# Theme I1 — Agent Architecture

**Layer:** Infrastructure  |  **Última verificação de código:** 2026-04-24
**Fonte de verdade:** `lia-agent-system/libs/agents-core/lia_agents_core/` no Replit

---

## O que é este tema

A camada de **agentes de domínio** da LIA é o núcleo inteligente do sistema. Cada domínio (pipeline, sourcing, wizard, etc.) possui seu próprio agente ReAct que processa mensagens do usuário, executa ferramentas, e retorna respostas estruturadas. Todo agente herda de uma hierarquia de classes base e segue um contrato formal via Protocols Python.

A arquitetura tem três níveis:
1. **Contratos formais** (`contracts.py`, `agent_interface.py`) — Protocols Python que definem boundaries arquiteturais sem acoplamento por herança
2. **Classes base** (`langgraph_base.py`, `langgraph_react_base.py`) — implementam o loop ReAct via LangGraph `create_react_agent()` com checkpointer, PII strip, AuditCallback e TimedToolNode
3. **Agentes de domínio** (`app/domains/<X>/agents/*_react_agent.py`) — 15 agentes registrados em `agents_registry.yaml`, hot-reloaded via `AgentRegistryWatcher`

**Boundary com temas irmãos:**
- **I2 Tool Architecture** — cada agente declara `available_tools`; as ferramentas são definidas no I2
- **I3 Orchestration** — o `MainOrchestrator` roteia para o agente certo via `ReactAgentRegistry`
- **I4 LLM Providers** — agentes chamam `LLMProviderFactory.get(company_id)` para BYOK
- **C1 Fairness** — `TimedToolNode` aplica `FairnessGuard` em tool args (LIA-C03); `LangGraphReActBase` faz PII strip (LIA-C04)
- **C7 Audit Trail** — `AuditCallback` é injetado automaticamente no grafo via `config["callbacks"]`

---

## Arquivos conectados (18 Python + 1 YAML)

### Camada Persona (LLM vê — 0 YAMLs)

Nenhum YAML específico de agente neste tema. O `agents_registry.yaml` é config técnico (não prompt). Prompts de sistema são colocados em `app/domains/<X>/agents/system_prompt.py` e consumidos via `_get_system_prompt(input)` em cada agente.

### Camada Config (Python lê — 1 YAML)

| Arquivo | Path canônico | Quando é consumido |
|---------|---------------|--------------------|
| `agents_registry.yaml` | `app/agents_registry.yaml` | Na startup + hot-reload via `AgentRegistryWatcher.check_and_reload()` (Celery beat 60s) |

### Camada Código (18 arquivos Python)

**libs/agents-core/lia_agents_core/ (17 arquivos):**

| Arquivo | Linhas | Responsabilidade |
|---------|:---:|-----------------|
| `agent_interface.py` | 213 | Contratos `AgentInput`, `AgentOutput`, `AgentAction`, `NavigationCommand`, `BaseAgent` (ABC) |
| `langgraph_base.py` | 117 | `LangGraphBase` — base com `get_checkpointer()` + compilação lazy de `StateGraph` |
| `langgraph_react_base.py` | 578 | `LangGraphReActBase` — base ReAct nativa: PII strip (LIA-C04), `create_react_agent()`, `TimedToolNode`, `_process_langgraph()` com AuditCallback |
| `react_agent_registry.py` | 522 | `ReactAgentRegistry` singleton + `AgentFactory` + funções de módulo (`register`, `get`, `list_agents`, `reload_from_yaml`) |
| `agent_bus.py` | — | Barramento de eventos entre agentes (sem import cruzado direto) |
| `base_state_machine.py` | — | Máquina de estados base para agentes não-ReAct |
| `state_machine.py` | — | Implementação de state machine para fluxos guiados |
| `react_loop.py` | — | `ReActConfig`, `ReActState`, `ToolDefinition` (legado — mantido para compatibilidade) |
| `agent_scaffold.py` | 360 | `AgentScaffold.generate()` — gera os 4 arquivos boilerplate de um novo agente |
| `autonomy_engine.py` | 182 | `AutonomyEngine` — mapeia `autonomy_level` ("low"/"medium"/"high") para lista de tools que exigem confirmação |
| `confidence.py` | 88 | `compute_confidence()` heurístico + `ConfidenceNode` para grafos LangGraph |
| `contracts.py` | 261 | `OrchestratorProtocol`, `DomainProtocol`, `AgentProtocol`, `LLMProviderProtocol` — structural subtyping |
| `enhanced_agent_mixin.py` | 545 | `EnhancedAgentMixin` — memória, autonomia, learning, fairness pre-check; `_setup_enhanced(domain)` |
| `nodes.py` | — | Nós genéricos para uso em StateGraphs |
| `proactive_worker.py` | — | Worker para hints proativos (AutonomyEngine) |
| `tool_adapter.py` | — | Adapta ferramentas LIA para formato LangChain |
| `timed_tool_node.py` | 356 | `TimedToolNode` — `ToolNode` com timeout 15s, métricas Prometheus, LIA-C03 FairnessGuard em tool args |

**app/ (1 arquivo):**

| Arquivo | Linhas | Responsabilidade |
|---------|:---:|-----------------|
| `app/core/agent_registry_watcher.py` | 151 | `AgentRegistryWatcher` — polling mtime-based para hot-reload de `agents_registry.yaml` e `tool_registry_metadata.yaml` |

### Integration points

- **Orchestrator** (I3) chama `ReactAgentRegistry.get_agent(domain)` ou `AgentFactory.create_agent(domain)`
- **Celery beat** (R4) chama `agent_registry_watcher.check_and_reload()` a cada 60 segundos
- **Tool handler** (I2) fornece LangChain tools retornadas por `_get_tools()`
- **AuditCallback** (C7) é injetado automaticamente por `_process_langgraph()` em cada invocação
- **PII masking** (C2) é chamado em `_sanitize_messages_pii()` antes de enviar ao LLM
- **FairnessGuard** (C1) é chamado pelo `TimedToolNode` em cada tool call (LIA-C03)
- **LLMProviderFactory** (I4) é chamado por `_get_model()` em cada agente de domínio

---

## Lógica IN → OUT

### Contratos formais — agent_interface.py

**AgentInput** (7 campos obrigatórios):
```python
class AgentInput(BaseModel):
    message: str                          # mensagem do usuário
    context: Dict[str, Any]              # contexto de domínio (job, pipeline state, etc.)
    session_id: str                       # identificador único da sessão
    company_id: str                       # multi-tenancy (sempre do JWT)
    user_id: str                          # usuário autenticado
    conversation_history: List[Dict]     # histórico de turnos
    metadata: Dict[str, Any]             # source, channel, locale, etc.
```

**AgentOutput** (8 campos):
```python
class AgentOutput(BaseModel):
    message: str                          # resposta ao usuário
    actions: List[AgentAction]           # ações executadas / solicitadas
    state_updates: Dict[str, Any]        # atualizações de estado do domínio
    navigation: Optional[NavigationCommand]  # mudança de stage
    confidence: float                     # 0.0 a 1.0 (compute_confidence())
    reasoning_steps: List[str]           # chain-of-thought
    tool_results: List[Dict]             # resultados de ferramentas chamadas
    metadata: Dict[str, Any]             # metadados adicionais
```

**BaseAgent** (interface ABC):
```python
class BaseAgent(ABC):
    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput: ...
    
    @property
    @abstractmethod
    def domain_name(self) -> str: ...
    
    @property
    @abstractmethod
    def available_tools(self) -> List[str]: ...
    
    async def get_status(self) -> dict: ...  # implementação padrão
```

### Hierarquia de classes base

```
BaseAgent (ABC — agent_interface.py)
└── LangGraphBase (ABC — langgraph_base.py)
    ├── _checkpointer = get_checkpointer()  ← PostgresSaver prod / MemorySaver dev
    ├── _compiled = None                    ← lazy singleton por instância
    ├── _build_graph() → StateGraph [abstract]
    └── LangGraphReActBase (langgraph_react_base.py)
        ├── _enable_pii_strip = True        ← LIA-C04 (desativar só em casos excepcionais)
        ├── _tool_timeout_seconds = 15      ← override por agente
        ├── _per_tool_timeouts = {}         ← timeout específico por tool
        ├── _sanitize_messages_pii()        ← strip HumanMessage/AIMessage
        ├── _build_graph()                  ← create_react_agent(model, TimedToolNode, checkpointer)
        ├── _get_compiled_graph()           ← lazy singleton
        └── _process_langgraph()            ← main entry: memory + AuditCallback + LLM
```

### Protocolo de execução — _process_langgraph()

```
1. Cria AuditCallback(user_id, company_id, session_id, domain, agent_type="langgraph_react")
2. EnhancedAgentMixin._get_memory_context(session_id, company_id)  ← se disponível
3. _get_system_prompt(input)  ← implementado por cada agente de domínio
4. Injeção do contexto de autenticação no system prompt:
   "## CONTEXTO DE AUTENTICAÇÃO
    - company_id da sessão atual: {company_id}
    - Use em TODAS as chamadas de ferramenta.
    - NUNCA peça ao usuário pelo company_id."
5. _sanitize_messages_pii(messages)  ← strip PII antes do LLM (LIA-C04)
6. graph.ainvoke(state, config={"callbacks": [audit_callback]})
7. TimedToolNode intercepta cada tool call:
   a. FairnessGuard check em args (LIA-C03)
   b. asyncio.wait_for(tool(), timeout=N)  ← N = _per_tool_timeouts.get(tool) or default_timeout_seconds
   c. TimeoutError → ToolMessage de erro (fail gracefully)
8. EnhancedAgentMixin._post_loop_learning(state, company_id, session_id)
9. _state_to_output(state, input) → AgentOutput
```

### AutonomyEngine — guardrails dinâmicos

```python
# Mapa de tools que exigem confirmação por nível de autonomia
GUARDRAILS_BY_LEVEL = {
    "low": [      # padrão — todas as ações destrutivas exigem confirmação
        "move_candidate", "batch_move", "reject_candidate",
        "schedule_interview", "generate_offer", "finalize_hiring",
        "create_job", "update_job", "delete_job", "send_message", "bulk_send",
    ],
    "medium": [   # apenas ações críticas
        "batch_move", "reject_candidate", "generate_offer",
        "finalize_hiring", "delete_job", "bulk_send",
    ],
    "high": [     # apenas irreversíveis
        "finalize_hiring", "delete_job",
    ],
}
# Cache TTL = 300s (5min). Carrega CompanyHiringPolicy do DB.
```

### Confidence scoring

```python
def compute_confidence(response, tool_calls_made, error, observations_count) -> float:
    # error → 0.0
    # resposta com tools + observações + len > 200 → 0.92
    # resposta com tools + observações → 0.85
    # resposta com tools → 0.80
    # resposta longa (> 300 chars) → 0.75
    # resposta média (> 100 chars) → 0.70
    # resposta curta → 0.50
    # resposta vazia → 0.10
```

### Contratos de boundary — contracts.py

Quatro `@runtime_checkable` Protocols garantem acoplamento por interface, não herança:
- `OrchestratorProtocol` — `route(message, session_id, company_id, user_id, context, history, metadata)` + `get_status()`
- `DomainProtocol` — `domain_id`, `domain_name`, `process_intent()`, `execute_action()`
- `AgentProtocol` — `process(AgentInput) → AgentOutput` + `get_status()`
- `LLMProviderProtocol` — `generate(prompt, ...) → str`

Uso: `isinstance(obj, AgentProtocol)` funciona sem herança.

### Side effects

- **Audit log** (C7): AuditCallback registra cada invocação → `audit_log` table
- **Métricas** (I5): TimedToolNode emite `tool_call_duration_seconds{domain, tool}` + `tool_call_errors_total{domain, tool}`
- **Learning** (R2): EnhancedAgentMixin extrai learnings pós-loop → `LearningExtractor`

### Escalation / HITL

| Cenário | Ação |
|---------|------|
| Tool timeout (>15s) | ToolMessage de erro injeta no grafo; agente responde ao usuário sem crash |
| FairnessGuard bloqueia tool call (LIA-C03) | Tool não executa; `FairnessViolation` logged (C7) |
| LangGraph não disponível (`ImportError`) | `_has_langgraph_prebuilt = False` → `ImportError` explícita na startup |
| Agente não registrado | `ReactAgentRegistry.get_agent()` lança `KeyError` com lista de domínios disponíveis |
| Hot-reload falha | `reload_agents_registry()` retorna `[]` (fail-open) + log WARNING |
| PII strip falha (LIA-C04) | `_sanitize_messages_pii()` retorna lista original (fail-safe) + log WARNING |

---

## Módulo Robustness (`app/shared/robustness/`) — 12 arquivos

O módulo de robustez adiciona uma camada de **sanitização, validação de entidades, tratamento de cancelamento e métricas** sobre o `BaseAgent`. É opcional mas recomendado para agentes que lidam com inputs não-estruturados.

### Estrutura do diretório

```
app/shared/robustness/
├── __init__.py
├── context_management.py   ← ContextManager + idempotency keys
├── defensive_prompts.py    ← get_defensive_prompt_section() por agent_type
├── document_scanner.py     ← validação de conteúdo de documentos
├── enhanced_base.py        ← EnhancedBaseAgent + RobustAgentMixin  ← principal
├── enhanced_registry.py    ← registro de schemas de intent
├── error_handling.py       ← AgentErrorCode enum + AgentErrorResponse
├── idempotency.py          ← dedup cross-request (TTL 300s, max 10k entries)
├── input_validation.py     ← sanitize_text()
├── intent_schemas.py       ← IntentSchema + EntityRequirement
├── response_filter.py      ← filtragem de resposta
└── security_patterns.py    ← padrões de segurança aplicados a input
```

### `EnhancedBaseAgent` (herda de `BaseAgent`)

```python
class EnhancedBaseAgent(BaseAgent):
    def __init__(self):
        self._intent_schemas: list[IntentSchema] = []   # via get_agent_intents(self.agent_type)
        self._metrics: dict = {
            "total_requests": 0, "successful_requests": 0,
            "failed_requests": 0, "avg_response_time_ms": 0, "cancellations": 0
        }
    
    def can_handle(self, intent: str, entities: dict) -> float:
        # 1. Exact intent match → schema.calculate_confidence(entities, {}, "")
        # 2. Keyword match → min(0.6, 0.3 + keyword_matches * 0.1)
        # 3. No match → 0.0
    
    async def process_with_robustness(self, intent, entities, context) -> AgentResponse:
        # Pipeline:
        # 1. _sanitize_entities(entities)       ← sanitize_text() em str values
        # 2. CancellationHandler.is_cancellation_request()  ← early return
        # 3. get_missing_entities()             ← se required_missing → clarification
        # 4. await self.process(intent, entities, context)  ← lógica do agente
        # 5. _update_metrics()
        # Catch: AgentError → user_message; Exception → create_user_friendly_error(INTERNAL_ERROR)
```

### `RobustAgentMixin` — alternativa para agentes existentes

```python
class RobustAgentMixin:
    """Mixin para adicionar robustez a agentes que já herdam de LangGraphReActBase.
    Usage: class MyAgent(RobustAgentMixin, LangGraphReActBase): ...
    """
    def init_robustness(self): ...        # chamar em __init__ para carregar schemas
    def can_handle_robust(self, intent, entities) -> float: ...
    def check_cancellation(self, message: str) -> AgentResponse | None: ...
    def sanitize_input(self, entities: dict) -> dict: ...
```

### `AgentErrorCode` (enum de 15 valores)

```python
class AgentErrorCode(StrEnum):
    VALIDATION_ERROR, MISSING_REQUIRED_ENTITY, INVALID_INPUT, NOT_FOUND,
    PERMISSION_DENIED, RATE_LIMITED, EXTERNAL_SERVICE_ERROR, LLM_ERROR,
    DATABASE_ERROR, TIMEOUT, INTERNAL_ERROR, UNSUPPORTED_OPERATION,
    CONTEXT_MISSING, CANCELLED, PARTIAL_SUCCESS
```

### `idempotency.py` — dedup cross-request

Resolve o problema de retries: um cliente que retenta a mesma operação (possivelmente alternando entre UUID v4 e Rails bigint para o mesmo candidato, conforme ADR-003 / Task #472) executa apenas uma vez.

```python
DEFAULT_TTL_SECONDS = 300   # 5 minutos
MAX_ENTRIES = 10_000        # purge LRU quando exceder
```

Usa `ContextManager.generate_idempotency_key_async()` para chave canônica (dual-ID collapse). Lança `HTTP 409 Conflict` em retry dentro do TTL.

### Integração com LangGraphReActBase

`EnhancedBaseAgent` herda de `BaseAgent`, não de `LangGraphReActBase`. A integração é via `process_with_robustness()` que chama `await self.process(...)` — o qual é sobrescrito pelo subclasse que usa LangGraph. Para agentes que já herdam de `LangGraphReActBase`, usar `RobustAgentMixin`.

---

## Instruções para Claude Code / Cursor

### "Implementa Agent Architecture no v5"

```
1. COPIE libs/agents-core/ completo como pacote Python:
   cp -r libs/agents-core/ <v5>/libs/agents-core/

2. INSTALE dependências:
   # langgraph>=0.2.x, langchain-core, pydantic>=2
   pip install langgraph langchain-core

3. CRIE checkpointer (langgraph_base.py importa get_checkpointer()):
   # app/shared/checkpointer.py
   from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
   from langgraph.checkpoint.memory import MemorySaver
   from lia_config.config import settings
   
   def get_checkpointer():
       if settings.ENVIRONMENT == "production":
           return AsyncPostgresSaver(settings.DATABASE_URL)
       return MemorySaver()

4. CRIE agents_registry.yaml em app/agents_registry.yaml (ver exemplo)

5. CRIE AgentRegistryWatcher singleton:
   # app/core/agent_registry_watcher.py — já existe, copie direto
   # Apontar AGENTS_REGISTRY_YAML para app/agents_registry.yaml
   # Apontar TOOLS_REGISTRY_YAML para app/tools/tool_registry_metadata.yaml

6. REGISTRE watcher no Celery beat (R4):
   CELERY_BEAT_SCHEDULE = {
       'agent-registry-watcher-60s': {
           'task': 'app.core.agent_registry_watcher.check_and_reload',
           'schedule': 60,  # 60 segundos
       }
   }

7. CRIE primeiro agente de domínio com AgentScaffold:
   from lia_agents_core.agent_scaffold import AgentScaffold
   files = AgentScaffold.generate(
       domain_name="my_domain",
       domain_path="app.domains.my_domain",
       description="Descrição do propósito do agente"
   )
   # Gera 4 arquivos: my_domain_react_agent.py, tool_registry.py,
   #                  system_prompt.py, stage_context.py

8. REGISTRE agente em agents_registry.yaml:
   agents:
     - name: my_domain
       domain: my_domain
       class_path: app.domains.my_domain.agents.my_domain_react_agent.MyDomainReActAgent
       model_id: claude-sonnet-4-6
       system_prompt_path: app/domains/my_domain/agents/system_prompt.py
       enabled: true

9. VERIFIQUE:
   - pytest tests/unit/test_agent_interface.py
   - pytest tests/unit/test_react_agent_registry.py
   - pytest tests/integration/test_agent_hot_reload.py
```

### "Cria novo agente de domínio"

```
1. Gere boilerplate com AgentScaffold (passo 7 acima)

2. Implemente os 4 métodos abstratos em *_react_agent.py:
   
   @register_agent("<domain_name>")
   class MyDomainReActAgent(LangGraphReActBase, EnhancedAgentMixin):
       
       def __init__(self):
           super().__init__()               # inicializa checkpointer
           self._setup_enhanced("my_domain")  # memória + autonomia + learning
       
       @property
       def domain_name(self) -> str:
           return "my_domain"
       
       @property
       def available_tools(self) -> list[str]:
           from app.domains.my_domain.agents.tool_registry import ALL_TOOLS
           return [t.name for t in ALL_TOOLS]
       
       def _get_tools(self) -> list:
           from app.domains.my_domain.agents.tool_registry import ALL_TOOLS
           return ALL_TOOLS
       
       def _get_model(self):
           from app.shared.providers.llm_factory import LLMProviderFactory
           return LLMProviderFactory.get(company_id=None)  # company_id injetado no process()
       
       def _get_system_prompt(self, input: AgentInput) -> str:
           return get_my_domain_system_prompt(input.context)
       
       def _state_to_output(self, state, input) -> AgentOutput:
           messages = state.get("messages", [])
           last = messages[-1].content if messages else ""
           return AgentOutput(message=last, confidence=0.8)
       
       async def process(self, input: AgentInput) -> AgentOutput:
           return await self._process_langgraph(input)

3. ADICIONE ao agents_registry.yaml

4. TESTES:
   # Unit: mock AgentInput → AgentOutput tem company_id correto
   # Integration: agente responde a mensagem simples
   # Fairness: tool call com campo de raça é bloqueado (LIA-C03)
```

### "Adiciona guardrail de autonomia a um agente"

```
1. Agente já usa EnhancedAgentMixin._setup_enhanced(domain)

2. Antes de executar tools destrutivas:
   guardrails = await self._resolve_guardrails(input.company_id)
   if "move_candidate" in guardrails:
       # retorna AgentOutput com requires_confirmation=True
       return AgentOutput(
           message="Confirmar: mover candidato para entrevista?",
           actions=[AgentAction(
               action_type="confirm",
               params={"pending_action": "move_candidate"},
               requires_confirmation=True,
           )],
       )

3. AutonomyEngine resolve automaticamente o nível (low/medium/high)
   via CompanyHiringPolicy do DB (cache 5min)
```

### Setup em CLAUDE.md

```markdown
## Infrastructure: Agent Architecture (I1)

- **Base class:** `LangGraphReActBase` (libs/agents-core) — extends via `create_react_agent()`
- **Contrato:** `AgentInput` (session_id, company_id, user_id, message, context) / `AgentOutput`
- **15 agentes registrados** em `app/agents_registry.yaml` — hot-reload via `AgentRegistryWatcher`
- **PII strip automático** antes de enviar ao LLM (LIA-C04, `_enable_pii_strip=True`)
- **FairnessGuard** em cada tool call via `TimedToolNode` (LIA-C03)
- **AuditCallback** injetado em `config["callbacks"]` de cada invocação de grafo
- **AutonomyEngine** — guardrails dinâmicos por `autonomy_level` (low/medium/high)
- **Novo agente:** `AgentScaffold.generate()` → 4 arquivos + adicionar em `agents_registry.yaml`

Consultar `themes/infrastructure/I1_AGENT_ARCHITECTURE.md`.
```

### Setup em `.cursor/rules/agent-architecture.mdc`

```
---
description: "I1 Agent Architecture"
alwaysApply: false
---

Quando o usuário pedir para:
- Criar novo agente de domínio
- Modificar comportamento de um agente existente
- Adicionar guardrails de autonomia
- Configurar timeout de tools

1. Leia themes/infrastructure/I1_AGENT_ARCHITECTURE.md
2. Herde LangGraphReActBase + EnhancedAgentMixin
3. Implemente domain_name, available_tools, _get_tools(), _get_model(), _get_system_prompt(), _state_to_output()
4. Use AgentScaffold.generate() para boilerplate
5. Adicione ao agents_registry.yaml
6. _enable_pii_strip = True (nunca setar False sem justificativa LGPD)
7. company_id SEMPRE de input.company_id (nunca hardcoded)
```

---

## Adaptação à estrutura diferente do v5

### Pode adaptar sem quebrar

- Nome de classes de agente de domínio (ex: `MyReActAgent` → `MyAgentV2`)
- Model IDs por agente (sonnet vs haiku vs gpt4)
- Timeout por tool (`_per_tool_timeouts`)
- Sistema de cache do checkpointer (PostgresSaver → Redis com interface compatível)
- `_DEFAULT_WEIGHTS` em `EnhancedAgentMixin` (pesos técnico/comportamental)
- Intervalo do watcher (60s é sugestão)
- Formato de `AgentOutput.metadata`

### NÃO pode adaptar

| Invariante | Por quê | Consequência |
|-----------|---------|--------------|
| `company_id` em `AgentInput` sempre do JWT | Multi-tenancy (C5) | Agente responde com dados de outro tenant |
| `_enable_pii_strip = True` por padrão | LGPD Art. 12 + EU AI Act Art. 13 | PII enviado ao LLM → vazamento de dados |
| `FairnessGuard` em `TimedToolNode` (LIA-C03) | NYC LL144 + LGPD | Discriminação não detectada em tool calls |
| `AuditCallback` injetado em TODA invocação | EU AI Act Art. 12 (logging obrigatório) | Sem rastreabilidade de decisões de alto risco |
| `BaseAgent` interface (process/domain_name/available_tools) | Contratos arquiteturais — orquestrador usa `AgentProtocol` | Orquestrador não consegue chamar o agente |
| `agents_registry.yaml` com hot-reload | Permite deploy de novos agentes sem downtime | Agentes novos só disponíveis após restart |
| `AutonomyEngine` cache TTL 5min | Mudanças de política propagam em <5min | Guardrails desatualizados por mais tempo |

---

## CrewPlanExecutor — DAG Multi-Agent Execution

> **Verificado via SSH 2026-04-24.** Seção adicionada pela auditoria de 2026-04-24. Fontes: `app/domains/agent_studio/crew_executor.py`, `libs/agents-core/lia_agents_core/agent_bus.py`.

O `CrewPlanExecutor` é a ponte entre a camada de agentes (I1) e o subsistema de Crews (AS1). Do ponto de vista da infraestrutura de agentes, é o componente que:
- Resolve o **DAG de tarefas** de um `CrewPlan`
- Executa tarefas em **paralelo via `asyncio.gather`** quando sem dependências
- Delega para outros agentes via **`AgentBus`** (pub/sub Redis) quando `use_bus_delegation=True`

### Fluxo de Execução

```
CrewPlanExecutor.execute(crew_plan, company_id)
  │
  ├─ [1] feature_flag: CREW_DELEGATION_ENABLED check → abort se False
  ├─ [2] dag_validation: verifica `depends_on` para ciclos
  ├─ [3] main_loop:
  │       while tasks_pending:
  │           ready = [t for t in pending if all deps in completed]
  │           results = await asyncio.gather(*[_run_task(t) for t in ready])
  │           completed.update(results)
  ├─ [4] status_resolution → COMPLETED / FAILED / PARTIAL
  └─ [5] context_cleanup → CrewContext.cleanup() (TTL Redis, não delete)
```

### AgentBus — Implementação de Infraestrutura

```python
# libs/agents-core/lia_agents_core/agent_bus.py

# Canais Redis:
AGENT_BUS_CHANNEL = "lia:agent_bus:{company_id}:{to_agent}"
AGENT_BUS_REPLY   = "lia:agent_bus:reply:{correlation_id}"

async def request(to_agent, payload, company_id, timeout_seconds=30.0) -> dict:
    correlation_id = str(uuid4())
    await redis.publish(
        f"lia:agent_bus:{company_id}:{to_agent}",
        json.dumps({"correlation_id": correlation_id, **payload})
    )
    # aguarda resposta em canal dedicado com timeout
    response = await redis.subscribe_one(
        f"lia:agent_bus:reply:{correlation_id}",
        timeout=timeout_seconds
    )
    return response  # raises AgentBusTimeoutError se timeout
```

**Isolamento multi-tenant:** `company_id` no canal = impossível receber mensagens de outros tenants mesmo com `agent_type` idêntico.

### CrewContext — Redis TTL-backed

```python
# CREW_CONTEXT_PREFIX = "lia:crew_ctx"
# DEFAULT_TTL_SECONDS = 3600

# Chave Redis por execução:
"lia:crew_ctx:{company_id}:{execution_id}"

# context_mappings resolve dependências de dados entre tasks:
# Task B declara: params["profile"] = "{task_a.top_candidate}"
# CrewContext.resolve_mapping("task_a.top_candidate") → crew_ctx["task_a"]["top_candidate"]
```

### Integração com Agentes de Domínio

Quando `use_bus_delegation=True`, cada agente alvo deve:
1. Assinar `lia:agent_bus:{company_id}:{agent_type}` (feito em `agent_bus.register_handler()`)
2. Processar o payload via `AgentInput` standard
3. Publicar resposta em `lia:agent_bus:reply:{correlation_id}`

```python
# Registro de handler (feito durante startup de cada domínio agent):
agent_bus.register_handler(
    agent_type="sourcing",
    company_id=company_id,
    handler=sourcing_agent.process  # AgentInput → AgentOutput
)
```

**Para documentação completa de modelos, CRUD e exemplos de crew:** ver `themes/agent_studio/AS1_CUSTOM_AGENTS.md` seção "CrewExecutor".

---

## Checklist de completude (P0/P1/P2)

- [ ] **(P0)** `LangGraphReActBase` importa e `create_react_agent` disponível (LangGraph ≥0.2.x)
- [ ] **(P0)** `get_checkpointer()` retorna `AsyncPostgresSaver` em produção
- [ ] **(P0)** `agents_registry.yaml` presente em `app/agents_registry.yaml`
- [ ] **(P0)** `AgentRegistryWatcher.check_and_reload()` chamado no Celery beat (60s)
- [ ] **(P0)** `TimedToolNode` com `FairnessGuard` ativo (env `FAIRNESS_TOOL_CHECK_ENABLED=true`)
- [ ] **(P0)** `AuditCallback` injetado em `_process_langgraph()` (todos os agentes)
- [ ] **(P0)** `_enable_pii_strip = True` em todos os agentes (LIA-C04)
- [ ] **(P0)** `company_id` injetado no system prompt de todo agente (nunca pede ao usuário)
- [ ] **(P1)** `EnhancedAgentMixin._setup_enhanced()` em todos os 15 agentes
- [ ] **(P1)** `AutonomyEngine` conectado ao `CompanyHiringPolicy` DB
- [ ] **(P1)** `AgentScaffold.generate()` gera 4 arquivos sem erros
- [ ] **(P1)** `compute_confidence()` retorna valor no range [0.0, 1.0]
- [ ] **(P1)** Hot-reload funciona sem restart (mtime change → reload automático)
- [ ] **(P2)** `contracts.py` Protocols usados nas type annotations (não só herança)
- [ ] **(P2)** `ConfidenceNode` conectado ao grafo para score explícito
- [ ] **(P2)** `LangGraphReActBase._tool_timeout_seconds` configurável por agente

---

## Gotchas e erros comuns

| Sintoma | Causa | Como evitar |
|---------|-------|-------------|
| `ImportError: LangGraph prebuilt não disponível` na startup | `langgraph` não instalado | `pip install langgraph>=0.2.x` antes de subir |
| Agente novo não aparece após deploy | `agents_registry.yaml` atualizado mas watcher ainda não rodou | Chamar `agent_registry_watcher.check_and_reload()` via admin endpoint |
| PII do candidato aparece em logs | `_enable_pii_strip = False` setado explicitamente | Auditar qualquer agente com `_enable_pii_strip = False` — deve ter justificativa |
| Tool nunca retorna (hanging) | `TimedToolNode` não configurado ou timeout muito alto | Confirmar `default_timeout_seconds=15`; ferramentas lentas têm `_per_tool_timeouts` |
| `KeyError: domain 'X' não registrado` | Agente em `agents_registry.yaml` mas `class_path` inválido | Verificar `class_path` com `python -c "from X import Y"` antes de adicionar ao YAML |
| FairnessGuard bloqueia tool em produção | `FAIRNESS_TOOL_CHECK_ENABLED=false` esquecido | Verificar env antes de cada deploy — default deve ser `true` |
| Checkpointer perde estado entre sessões | `MemorySaver` em produção | Confirmar `settings.ENVIRONMENT == "production"` → `AsyncPostgresSaver` |
| `AgentFactory.create_agent` vs `registry.get_agent` | `get_agent` retorna instância **cacheada** (não session-safe) | Usar `AgentFactory.create_agent()` para instâncias isoladas por sessão |

---

## Testes obrigatórios

| Teste | Path sugerido | Cenário |
|-------|--------------|---------|
| AgentInput/Output schema | `tests/unit/test_agent_interface.py` | Validar required fields + tipo de confidence (0-1) |
| ReactAgentRegistry singleton | `tests/unit/test_react_agent_registry.py` | register() → get_agent() → instância correta |
| Hot-reload YAML | `tests/integration/test_agent_hot_reload.py` | Modificar YAML → `check_and_reload()` → novo agente disponível |
| PII strip (LIA-C04) | `tests/unit/test_langgraph_react_base.py` | HumanMessage com CPF → sanitized antes do LLM |
| TimedToolNode timeout | `tests/unit/test_timed_tool_node.py` | Tool que dorme >15s → ToolMessage de erro (não crash) |
| FairnessGuard em tool call (LIA-C03) | `tests/unit/test_timed_tool_node.py` | Args com `race="negro"` → blocked antes de executar |
| AutonomyEngine levels | `tests/unit/test_autonomy_engine.py` | company policy "low" → 11 tools em guardrails; "high" → 2 |
| AuditCallback injetado | `tests/integration/test_audit_callback.py` | `process(input)` → audit_log registrado com domain + company_id |
| AgentScaffold gera 4 arquivos | `tests/unit/test_agent_scaffold.py` | `generate("test", "app.test", "desc")` → 4 keys no dict retornado |
| Confidence range | `tests/unit/test_confidence.py` | `compute_confidence(error="err")` → 0.0; resposta longa + tools → ≥0.85 |

---

## Referências

### Bundles verbatim
- `INFRASTRUCTURE_YAMLS_CANONICAL_BUNDLE.md` — `technical_config/agents_registry.yaml`

### Reconstruction guides
- `INFRASTRUCTURE_RECONSTRUCTION_GUIDE.md` §B (Agent Bus) + §C (LangGraph agents)

### Cross-references
- **I2 Tool Architecture** — `_get_tools()` retorna LangChain tools definidas no I2
- **I3 Orchestration** — `ReactAgentRegistry` é consumido pelo `MainOrchestrator`
- **I4 LLM Providers** — `_get_model()` chama `LLMProviderFactory.get(company_id)` (BYOK)
- **I5 Observability** — `TimedToolNode` emite métricas; `execution_log_store` via AuditCallback
- **C1 Fairness** — `TimedToolNode` chama `FairnessGuard` em tool args (LIA-C03)
- **C2 LGPD PII** — `_sanitize_messages_pii()` chama `strip_pii_for_llm_prompt()` (LIA-C04)
- **C7 Audit Trail** — `AuditCallback` injetado em `config["callbacks"]`
- **R2 Learning Loop** — `EnhancedAgentMixin._post_loop_learning()` chama `LearningExtractor`
- **R4 Background Jobs** — Celery beat chama `agent_registry_watcher.check_and_reload()`

---

*Documento gerado em 2026-04-24 | Zero invenção — todo conteúdo verificado via SSH no Replit*
