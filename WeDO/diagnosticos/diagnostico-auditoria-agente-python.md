# Diagnóstico: Auditoria e Compliance do Agente Python

**Data**: 10/03/2026
**Autor**: Análise automatizada cruzando documento do André ("Plano de Auditoria — Agente Python") com código de referência da LIA
**Objetivo**: Mapear gaps de auditabilidade no agente Python (V5) e fornecer blueprints de implementação baseados na LIA

---

## 1. Como Usar Este Documento

Este documento serve como **guia de implementação** para o time de desenvolvimento. Cada gap identificado inclui:

1. **O problema no V5**: Arquivo, linha e descrição do que está errado
2. **Como a LIA resolve**: Arquivos de referência com snippets de código que podem ser adaptados
3. **Passos de implementação**: Instruções numeradas que um desenvolvedor (ou agente IA) pode seguir
4. **Card Jira correspondente**: Identificador do card no projeto WT

### Mapeamento Gap → Card Jira

| Gap | Card | Jira Key | Prioridade | Sprint |
|-----|------|----------|------------|--------|
| GAP 1 — ReAct Agents sem Audit Callbacks | AUD-001 | **WT-1506** | P0 Crítico | Sprint 1 |
| GAP 2 — Tools sem rastreamento por nome | AUD-002 | **WT-1507** | P1 Médio | Sprint 1 |
| GAP 7 — Autonomous sem Circuit Breaker | AUD-003 | **WT-1508** | P1 Médio | Sprint 1 |
| GAP 6 — Sem retention/cleanup | AUD-004 | **WT-1509** | P2 Baixo | Sprint 2 |
| GAP 3 — Sem storage externo | AUD-005 | **WT-1510** | P3 Baixo | Sprint 3 |
| GAP 4 — Sem endpoints REST de timeline | AUD-006 | **WT-1511** | P3 Baixo | Sprint 3 |
| GAP 5 — Sem métricas Prometheus | AUD-007 | **WT-1512** | P3 Baixo | Sprint 3 |

**Epic**: WT-1505 — AUD — Auditoria e Compliance do Agente Python

### Repositório de referência

A LIA está disponível no repositório GitHub (commitado via Replit). Os arquivos referenciados usam paths relativos a partir da raiz `lia-agent-system/`.

---

## 2. Stack Técnico da LIA (Referência para Comparação)

Antes de implementar, compare o ambiente da LIA com o do V5. Se houver diferenças de versão ou biblioteca, adapte os snippets.

| Dependência | Versão LIA | Notas |
|---|---|---|
| Python | ≥3.11 | |
| FastAPI | 0.115.5 | Framework web |
| Uvicorn | 0.32.1 | ASGI server |
| LangGraph | 0.2.53 | Orquestração de agentes |
| LangChain | 0.3.9 | Framework LLM |
| LangSmith | 0.2.5 | Tracing/debugging |
| SQLAlchemy | 2.0.36 | ORM (async) |
| Alembic | 1.14.0 | Migrations |
| asyncpg | 0.30.0 | PostgreSQL async driver |
| psycopg2-binary | 2.9.10 | PostgreSQL sync driver |
| Pydantic | 2.10.3 | Validação de dados |
| Celery | 5.4.0 | Task queue |
| Redis | 5.2.0 | Cache + state |
| prometheus_client | 0.21.0 | Métricas |
| Sentry SDK | 2.19.2 | Error tracking |
| langchain-anthropic | 0.3.22 | Provider Claude |
| langchain-openai | 0.2.9 | Provider OpenAI |
| langchain-google-vertexai | 2.0.8 | Provider Gemini |
| pgvector | 0.3.6 | Vector search |
| aio-pika | 9.5.3 | RabbitMQ async |

### Infra

- **DB**: PostgreSQL + pgvector
- **Cache/State**: Redis
- **Message Broker**: RabbitMQ (Celery + aio-pika)
- **Storage**: S3 (prod) / LocalFile (dev)
- **Monitoring**: Prometheus + Grafana + Sentry
- **Monorepo**: UV workspaces (`libs/` + `apps/` + `app/`)

---

## 3. Arquitetura do Orquestrador LIA (Referência)

```
WebSocket /ws/chat/{session_id}
  → JWT auth + session register
  → CascadedRouter (6 tiers):
      Tier 0: MemoryResolver (pronomes/contexto)
      Tier 1: LRU In-process Cache (MD5 exact match)
      Tier 2: Redis Hash Cache (distribuído)
      Tier 3: VectorSemanticCache (pgvector cosine ≥0.92)
      Tier 4: FastRouter (regex/keywords)
      Tier 5: LLM Cascade (Haiku→Sonnet→Opus via IntentRouter)
      Fallback: needs_clarification → pergunta ao usuário
  → DomainDispatcher:
      Sync: agent.process() direto (wizard, pipeline)
      Async: RabbitMQ queue → Celery worker → response queue → WS push
  → Agent executa (LangGraph StateGraph ou ReAct loop)
  → AuditCallback captura tudo automaticamente via config["callbacks"]
  → AuditWriter persiste: PG (metadados leves) + S3 (payload completo)
  → Resposta via WebSocket
```

---

## 4. Estrutura de Diretórios da LIA (Referência)

```
lia-agent-system/
├── app/
│   ├── api/v1/              # Endpoints REST + WebSocket (agent_chat_ws.py)
│   ├── domains/             # 12 bounded contexts
│   │   ├── analytics/       # AnalyticsReActAgent
│   │   ├── automation/      # AutomationReActAgent
│   │   ├── communication/   # CommunicationReActAgent
│   │   ├── cv_screening/    # WSIInterviewGraph
│   │   ├── job_management/  # WizardReActAgent + JobWizardGraph
│   │   ├── pipeline/        # PipelineReActAgent + PipelineTransitionAgent
│   │   ├── sourcing/        # SourcingReActAgent (11 sub-agents)
│   │   └── ...
│   ├── orchestrator/        # Roteamento e orquestração
│   │   ├── cascaded_router.py   # CascadedRouter 6-tier
│   │   ├── intent_router.py     # IntentRouter (LLM cascade)
│   │   ├── llm_cascade.py       # LLMCascadeRouter + token recording
│   │   └── tenant_budget.py     # Budget check por empresa
│   ├── shared/
│   │   ├── compliance/      # FairnessGuard, FactChecker, AuditService
│   │   ├── providers/       # LLM factory + claude/gemini/openai providers
│   │   ├── resilience/      # CircuitBreaker, rate_limiter
│   │   ├── prompts/         # PromptLoader, PromptRegistry, agent_prompts
│   │   └── messaging/       # RabbitMQ dispatchers, consumers
│   ├── observability/       # metrics.py (Prometheus), tracing.py
│   └── models/              # SQLAlchemy models
├── libs/
│   ├── agents-core/         # LangGraphBase, LangGraphReActBase
│   ├── audit/               # AuditCallback, AuditWriter, AuditStorage
│   ├── config/              # Settings, database, Redis
│   └── services/            # Shared service abstractions
├── alembic/versions/        # Migrations (025=audit, 032=hitl, etc.)
├── tests/                   # pytest (32%+ coverage)
└── pyproject.toml           # UV workspace config
```

---

## 5. Patterns Arquiteturais da LIA (Referência)

### 5.1 AuditCallback Automático

O callback é injetado via `config["callbacks"]` — **nenhum agente precisa saber que está sendo auditado**.

```python
# libs/agents-core/lia_agents_core/langgraph_react_base.py
async def _process_langgraph(self, agent_input):
    audit_callback = AuditCallback(
        user_id=agent_input.user_id,
        company_id=agent_input.company_id,
        session_id=agent_input.session_id,
        domain=self.domain,
        agent_type="react_langgraph"
    )
    config = {
        "configurable": {"thread_id": agent_input.session_id},
        "callbacks": [audit_callback, streaming_callback]
    }
    result = await compiled.ainvoke(initial_state, config=config)
    # AuditCallback.on_chain_end → _schedule_persist → AuditWriter.persist()
```

### 5.2 Dual Persistence (Audit)

```
PG (audit_execution_metadata): metadados leves, indexáveis, consulta rápida
Storage (S3/local): payload completo (prompts, respostas, tool I/O, reasoning)
```

### 5.3 Circuit Breaker

```python
# app/shared/resilience/circuit_breaker.py
ANTHROPIC_CIRCUIT = CircuitBreaker(
    "anthropic",
    CircuitBreakerConfig(failure_threshold=5, recovery_timeout=30.0,
                         success_threshold=2, timeout=60.0)
)

# Uso como decorator no provider:
@circuit_breaker_decorator(ANTHROPIC_CIRCUIT)
async def generate(self, prompt, **kwargs):
    ...
```

### 5.4 Prometheus Metrics

```python
# app/observability/metrics.py
llm_requests_total = Counter("lia_llm_requests_total", "...", ["provider", "status"])
llm_latency_seconds = Histogram("lia_llm_latency_seconds", "...", ["provider"])
agent_iterations_total = Counter("lia_agent_iterations_total", "...", ["domain", "action_type"])
circuit_breaker_state = Gauge("lia_circuit_breaker_state", "...", ["service"])
router_tier_hit_total = Counter("lia_router_tier_hit_total", "...", ["tier"])
agent_tool_failures_total = Counter("lia_agent_tool_failures_total", "...", ["domain", "tool"])
llm_cost_usd_total = Counter("lia_llm_cost_usd_total", "...", ["model", "domain"])
```

---

## 6. O que já Existe no V5 (Fonte: Documento André)

| Componente | Arquivo V5 | Status |
|---|---|---|
| AuditCallbackHandler (BaseCallbackHandler) | `src/services/audit/audit_callback.py` | ✅ Intercepta chain/llm/tool start/end/error |
| AuditExecution + AuditEvent models | `src/services/audit/audit_models.py` | ✅ execution_id, session_id, domain_id, tokens, cost, timeline |
| AuditWriter (PostgreSQL) | `src/services/audit/audit_writer.py` | ✅ Tabela `agent_executions`, upsert com timeline JSONB |
| PII masking (CPF, email, telefone) | `src/services/audit/audit_models.py` | ✅ `mask_pii()` com regex |
| Audit injetado no DomainOrchestrator | `src/domains/orchestrator.py` L95-101 | ✅ Funciona para domínios tradicionais |
| Audit injetado no SupervisorGraph | `src/hub/supervisor_graph.py` L324 | ✅ Funciona para o supervisor |
| LLM tracking → Rails API | `src/services/llm_tracking_service.py` | ✅ Envia uso de LLM para Rails |
| Cost calculation (Gemini pricing) | `src/config/llm_tracking_config.py` | ✅ Pricing atualizado |
| StreamingCallback | `src/services/streaming_callback.py` | ✅ Progresso por nó |
| CircuitBreaker | `src/services/circuit_breaker.py` | ✅ Threshold + cooldown por domínio |
| Testes de audit | `tests/test_audit.py` | ✅ mask_pii, AuditExecution, AuditCallbackHandler (8+ tests) |

---

## 7. Gaps Identificados — Detalhamento Completo

### GAP 1 → Card AUD-001: ReAct Agents sem Audit Callbacks [P0 CRÍTICO]

**Problema no V5:**
O `AuditCallbackHandler` é injetado no `DomainOrchestrator.process_query()` via `config["callbacks"]`, mas os ReAct agents (`AppliesReActAgent`, `UniversalReActAgent`) fazem `graph.invoke(initial_state)` **sem passar config/callbacks**. Resultado: execuções autônomas são caixa-preta — nenhuma chamada LLM ou tool é auditada.

**Locais no V5:**
- `src/domains/applies/react_agent.py` L376: `graph.invoke(initial_state)` — sem config
- `src/domains/autonomous/agent.py` L170: `graph.invoke(initial_state)` — sem config
- `src/domains/orchestrator.py` L95-116: cria `AuditCallbackHandler`, injeta em `config["callbacks"]`, passa para `self.workflow.process()` — funciona para domínios tradicionais
- `src/domains/workflow.py` L461: `self.graph.invoke(initial_state, config=config)` — config vem do orquestrador

**Como a LIA resolve:**

Arquivo: `libs/agents-core/lia_agents_core/langgraph_react_base.py`
```python
async def _process_langgraph(self, agent_input):
    audit_callback = AuditCallback(
        user_id=agent_input.user_id,
        company_id=agent_input.company_id,
        session_id=agent_input.session_id,
        domain=self.domain,
        agent_type="react_langgraph"
    )
    config = {
        "configurable": {"thread_id": agent_input.session_id},
        "callbacks": [audit_callback, streaming_callback]
    }
    result = await compiled.ainvoke(initial_state, config=config)
```

Arquivo: `libs/agents-core/lia_agents_core/langgraph_base.py`
```python
async def _run_graph(self, graph, initial_state, session_id, audit_callback=None, streaming_callback=None):
    callbacks = []
    if audit_callback:
        callbacks.append(audit_callback)
    if streaming_callback:
        callbacks.append(streaming_callback)
    config = {
        "configurable": {"thread_id": session_id},
        "callbacks": callbacks
    }
    return await graph.ainvoke(initial_state, config=config)
```

**Implementação sugerida:**
1. No `AppliesReActAgent.execute()`, receber `callbacks` como parâmetro (ou extrair do context)
2. Passar `config={"callbacks": callbacks}` em `graph.invoke(initial_state, config=config)`
3. Mesmo fix no `UniversalReActAgent.execute()`
4. No `AutonomousDomain.process()`, passar callbacks do context para `agent.execute()`

**Teste:** Rodar query autônoma → verificar que `agent_executions` tem timeline com tool calls

**Esforço:** 2-3h | **Story Points:** 2

---

### GAP 2 → Card AUD-002: Autonomous Agent sem Rastreamento de Tools [P1 MÉDIO]

**Problema no V5:**
O nó `call_tools` dos agents autônomos incrementa um counter de tools mas não guarda os **nomes** das tools chamadas. O log final mostra count total mas não "list_departments → get_department_tree → create_department".

**Locais no V5:**
- `src/domains/autonomous/agent.py` L102-120: `call_tools` incrementa counter sem acumular nomes
- `src/domains/applies/react_agent.py` L342-353: mesmo problema

**Como a LIA resolve:**

Arquivo: `libs/audit/lia_audit/audit_callback.py`
```python
def on_tool_start(self, serialized, input_str, **kwargs):
    self._current_tool_start = datetime.now(timezone.utc)
    self._current_tool_name = (serialized or {}).get("name", "unknown")

def on_tool_end(self, output, **kwargs):
    latency = self._elapsed_ms(self._current_tool_start)
    self.entries.append({
        "type": "tool_call",
        "timestamp": (self._current_tool_start or datetime.now(timezone.utc)).isoformat(),
        "tool": self._current_tool_name or "unknown",
        "input_preview": str(kwargs.get("input_str", ""))[:500],
        "output_preview": str(output)[:500],
        "latency_ms": latency,
        "success": True,
    })
```

Arquivo: `libs/audit/lia_audit/audit_callback.py` — `_build_record()`:
```python
tools_used = list({e["tool"] for e in self.entries if e.get("type") == "tool_call" and e.get("success")})
```

**Implementação sugerida:**
1. No state do agent, adicionar `tracking["tools_used"] = []`
2. No `call_tools`, a cada tool call: `tracking["tools_used"].append(tc["name"])`
3. Incluir `tools_used` no metadata da `DomainResponse`

**Teste:** Executar query que chama múltiplas tools → verificar metadata retornada contém lista de nomes

**Esforço:** 1h | **Story Points:** 1

---

### GAP 7 → Card AUD-003: Autonomous Agent sem Circuit Breaker [P1 MÉDIO]

**Problema no V5:**
O `CircuitBreaker` é usado no `DomainWorkflow._execute_with_retry()` para domínios tradicionais, mas o `UniversalAPIClient` faz HTTP direto sem proteção. Se a API Rails estiver down, o agente gasta todas as iterações batendo em erros 5xx.

**Locais no V5:**
- `src/domains/workflow.py` L178-220: CircuitBreaker para domínios tradicionais
- `src/domains/autonomous/api_client.py` L50-100: nenhuma proteção

**Como a LIA resolve:**

Arquivo: `app/shared/resilience/circuit_breaker.py`
```python
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    success_threshold: int = 2
    timeout: float = 10.0
    exclude_exceptions: tuple = ()

class CircuitBreaker:
    def __init__(self, name, config=None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._lock = asyncio.Lock()

    async def call(self, func, *args, **kwargs):
        async with self._lock:
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerError(self.name, self._get_retry_after())
        try:
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=self.config.timeout)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            raise

# Circuitos pré-definidos:
ANTHROPIC_CIRCUIT = CircuitBreaker("anthropic", CircuitBreakerConfig(
    failure_threshold=5, recovery_timeout=30.0, success_threshold=2, timeout=60.0
))
OPENAI_CIRCUIT = CircuitBreaker("openai", CircuitBreakerConfig(...))
GEMINI_CIRCUIT = CircuitBreaker("gemini", CircuitBreakerConfig(...))
```

**Implementação sugerida:**
1. Criar `RAILS_API_CIRCUIT = CircuitBreaker("rails_api", failure_threshold=5, recovery_timeout=60)`
2. No `UniversalAPIClient.request()`, checar estado antes de cada call
3. Se OPEN: retornar `APIResponse(success=False, error="circuit_open")` sem HTTP call
4. Record success/failure após cada chamada

**Teste:** Simular API down 5x → verificar circuito abre → próxima call retorna erro imediato sem HTTP

**Esforço:** 2h | **Story Points:** 2

---

### GAP 6 → Card AUD-004: Retention/Cleanup de agent_executions [P2 BAIXO]

**Problema no V5:**
A tabela `agent_executions` cresce indefinidamente. Não existe job de limpeza.

**Local no V5:**
- `src/services/audit/audit_writer.py` — cria a tabela mas nunca limpa

**Como a LIA resolve:**

Arquivo: `libs/audit/lia_audit/audit_storage.py`
```python
AUDIT_RETENTION_DAYS_HOT = 90       # S3 Standard → Glacier Instant Retrieval
AUDIT_RETENTION_DAYS_COLD = 365     # Glacier Instant → Deep Archive
AUDIT_RETENTION_DAYS_DELETE = 2555  # 7 anos total (SOX compliance) → Delete

async def apply_lifecycle_policy(self) -> bool:
    """Aplica política de lifecycle no bucket S3."""
    ...
```

**Implementação sugerida:**
1. Criar task/script: `DELETE FROM agent_executions WHERE created_at < now() - interval '90 days'`
2. Se storage externo existir (GAP 3): mover para frio antes de deletar
3. Registrar como Celery beat task mensal ou cron

**Teste:** Inserir registros antigos → rodar cleanup → verificar deleção

**Esforço:** 2h | **Story Points:** 1

---

### GAP 3 → Card AUD-005: Storage Externo para Logs Pesados [P3 BAIXO]

**Problema no V5:**
O `AuditWriter` salva no PostgreSQL com timeline JSONB, mas trunca dados (user_query limitado a 500 chars, tool outputs não salvos). Sem camada de storage para investigação profunda.

**Local no V5:**
- `src/services/audit/audit_writer.py` — só salva metadata + timeline compacta

**Como a LIA resolve:**

Arquivo: `libs/audit/lia_audit/audit_storage.py`
```python
class AuditStorage(ABC):
    @abstractmethod
    async def save(self, path: str, data: dict) -> str: ...
    @abstractmethod
    async def load(self, path: str) -> Optional[dict]: ...

class LocalFileStorage(AuditStorage):
    def __init__(self, base_dir="./audit_logs"):
        self.base_dir = base_dir
    async def save(self, path, data):
        full_path = os.path.join(self.base_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
        return full_path

class S3Storage(AuditStorage):
    def __init__(self, bucket, prefix="audit", region="us-east-1"):
        ...
    async def save(self, path, data):
        s3_key = f"{self.prefix}/{path}"
        payload = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        client.put_object(Bucket=self.bucket, Key=s3_key, Body=payload,
                          ContentType="application/json", ServerSideEncryption="AES256")
        return f"s3://{self.bucket}/{s3_key}"

def build_storage_path(domain, company_id, execution_id):
    now = datetime.now(timezone.utc)
    date_path = now.strftime("%Y/%m/%d")
    return f"{domain}/{date_path}/{company_id}/{execution_id}.json"

def get_audit_storage():
    """Factory singleton — retorna LocalFileStorage ou S3Storage conforme env."""
    storage_type = settings.AUDIT_STORAGE_TYPE  # "file" | "s3"
    ...
```

Arquivo: `libs/audit/lia_audit/audit_writer.py`
```python
class AuditWriter:
    async def persist(self, record, db=None):
        # 1. Payload completo → Storage (S3/local)
        storage_path = await self._save_full_payload(record)
        record.storage_path = storage_path
        # 2. Metadados leves → PostgreSQL
        await self._save_metadata(record, db)
```

Arquivo: `libs/audit/lia_audit/audit_models.py`
```python
@dataclass
class ExecutionAuditRecord:
    execution_id: str = ""
    session_id: str = ""
    user_id: str = ""
    company_id: str = ""
    domain: str = ""
    agent_type: str = "react"
    start_time: str = ""
    end_time: Optional[str] = None
    total_duration_ms: float = 0.0
    success: bool = True
    confidence: float = 0.0
    tools_used: List[str] = field(default_factory=list)
    nodes_visited: List[str] = field(default_factory=list)
    error: Optional[str] = None
    storage_path: Optional[str] = None
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def to_metadata_dict(self):
        """Campos leves para PG — sem entries."""
        ...
    def to_full_dict(self):
        """Payload completo para storage."""
        base = self.to_metadata_dict()
        base["entries"] = self.entries
        return base
```

**Implementação sugerida:**
1. Criar `AuditStorageWriter` com ABC (save/load)
2. Implementar `LocalFileStorage` (dev) e `GCSStorage` (prod)
3. Conectar ao `AuditCallbackHandler.finalize()` — salvar payload completo
4. Salvar: prompt completo, todas tool responses, state final
5. Guardar `storage_path` na tabela `agent_executions` (adicionar coluna se necessário)

**Teste:** Executar query → verificar arquivo JSON com payload completo no filesystem

**Esforço:** 4-6h | **Story Points:** 3

---

### GAP 4 → Card AUD-006: Endpoints REST de Timeline [P3 BAIXO]

**Problema no V5:**
Os dados de audit estão no PG (`agent_executions` table) mas não existe endpoint REST para consultar/filtrar/reconstruir.

**Referência LIA:**

Arquivo: `alembic/versions/025_add_agent_execution_metadata.py`
```python
op.create_table(
    "audit_execution_metadata",
    sa.Column("execution_id", sa.String(255), primary_key=True),
    sa.Column("session_id", sa.String(255), nullable=True),
    sa.Column("company_id", sa.String(255), nullable=False),
    sa.Column("user_id", sa.String(255), nullable=True),
    sa.Column("domain", sa.String(100), nullable=True),
    sa.Column("agent_type", sa.String(50), nullable=True),
    sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    sa.Column("duration_ms", sa.Float, nullable=True),
    sa.Column("nodes_visited", JSONB, nullable=True),
    sa.Column("tools_used", JSONB, nullable=True),
    sa.Column("success", sa.Boolean, nullable=True),
    sa.Column("confidence", sa.Float, nullable=True),
    sa.Column("storage_path", sa.String(500), nullable=True),
    sa.Column("error", sa.Text, nullable=True),
)
# Índices: company_id, session_id, domain, (company_id, timestamp)
```

Arquivo: `libs/audit/lia_audit/audit_writer.py`
```python
async def load_full(self, storage_path):
    """Carrega payload completo pelo storage_path."""
    storage = get_audit_storage()
    return await storage.load(storage_path)
```

**Implementação sugerida:**
1. `GET /v1/agent/executions?session_id=X&domain=Y&from=Z&to=W&success=bool`
   - Query `agent_executions` com filtros + paginação (limit/offset)
   - Retorna lista de metadados leves
2. `GET /v1/agent/executions/{execution_id}`
   - Retorna registro completo (metadados + timeline JSONB)
3. `GET /v1/agent/executions/{execution_id}/timeline`
   - Retorna timeline formatada com steps numerados
   - Se storage externo existir: carregar payload completo
4. Proteger com JWT, filtrar por company_id do usuário

**Teste:** Criar execuções de teste → consultar via endpoints → verificar filtros e paginação

**Esforço:** 3-4h | **Story Points:** 3

---

### GAP 5 → Card AUD-007: Métricas Prometheus [P3 BAIXO]

**Problema no V5:**
Sem métricas em formato Prometheus para observabilidade em produção.

**Como a LIA resolve:**

Arquivo: `app/observability/metrics.py`
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# LLM
llm_requests_total = Counter("lia_llm_requests_total", "Total LLM API calls", ["provider", "status"])
llm_latency_seconds = Histogram("lia_llm_latency_seconds", "LLM latency", ["provider"],
                                buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0])

# Agents
agent_iterations_total = Counter("lia_agent_iterations_total", "ReAct iterations", ["domain", "action_type"])

# Compliance
fairness_blocks_total = Counter("lia_fairness_blocks_total", "FairnessGuard blocks", ["category"])

# Resilience
circuit_breaker_state = Gauge("lia_circuit_breaker_state", "CB state (0=closed,1=half_open,2=open)", ["service"])

# HTTP
http_request_duration_seconds = Histogram("lia_http_request_duration_seconds", "HTTP duration",
                                          ["method", "endpoint", "status_code"])

# Business
pipeline_transitions_total = Counter("lia_pipeline_transitions_total", "Stage transitions", ["from_stage", "to_stage"])
candidates_evaluated_total = Counter("lia_candidates_evaluated_total", "Candidates evaluated", ["job_id", "evaluation_type"])

# Router
router_tier_hit_total = Counter("lia_router_tier_hit_total", "Router tier hits", ["tier"])
router_latency_ms = Histogram("lia_router_latency_ms", "Router latency", ["tier"])

# Tools
agent_tool_failures_total = Counter("lia_agent_tool_failures_total", "Tool failures", ["domain", "tool"])

# Cost
llm_cost_usd_total = Counter("lia_llm_cost_usd_total", "LLM cost USD", ["model", "domain"])

def generate_latest_metrics():
    return generate_latest()
```

**Implementação sugerida:**
1. Instalar `prometheus_client`
2. Criar `src/services/metrics.py`:
   - `agent_requests_total{domain, status}`
   - `agent_duration_seconds{domain}` (Histogram)
   - `agent_tool_calls_total{tool_name, domain}`
   - `agent_llm_tokens_total{type=input|output, model}`
   - `agent_errors_total{domain, error_type}`
3. Instrumentar no AuditCallbackHandler ou orquestrador
4. Expor `/metrics` endpoint no FastAPI

**Teste:** Rodar queries → acessar `/metrics` → verificar counters incrementados

**Esforço:** 4-5h | **Story Points:** 3

---

## 8. Mapeamento Gap → Card Jira

| GAP | Card | Título | Sprint | SP | Prioridade |
|---|---|---|---|---|---|
| GAP 1 | AUD-001 | Propagar AuditCallback para ReAct Agents | 1 | 2 | P0 High |
| GAP 2 | AUD-002 | Rastrear Tools Chamadas por Nome | 1 | 1 | P1 High |
| GAP 7 | AUD-003 | Circuit Breaker no Autonomous Agent | 1 | 2 | P1 High |
| GAP 6 | AUD-004 | Retention/Cleanup de agent_executions | 2 | 1 | P2 Medium |
| GAP 3 | AUD-005 | Storage Externo para Logs Pesados (S3/GCS) | 3 | 3 | P3 Medium |
| GAP 4 | AUD-006 | Endpoints REST de Timeline | 3 | 3 | P3 Medium |
| GAP 5 | AUD-007 | Métricas Prometheus | 3 | 3 | P3 Medium |

**Total:** 7 cards, 15 SP, ~19h de esforço

---

## 9. Priorização por Sprint

### Sprint 1 — Fundação (P0 + P1) — ~5h
1. **AUD-001**: Propagar AuditCallback para ReAct Agents
2. **AUD-002**: Rastrear Tools Chamadas por Nome
3. **AUD-003**: Circuit Breaker no Autonomous Agent

### Sprint 2 — Higiene (P2) — ~2h
4. **AUD-004**: Retention/Cleanup de agent_executions

### Sprint 3 — Observabilidade Avançada (P3) — ~12h
5. **AUD-005**: Storage Externo para Logs Pesados
6. **AUD-006**: Endpoints REST de Timeline
7. **AUD-007**: Métricas Prometheus

---

## 10. Arquivos-Chave de Referência na LIA

```
AUDITORIA:
  libs/audit/lia_audit/audit_callback.py     — AuditCallback (BaseCallbackHandler) — 263 linhas
  libs/audit/lia_audit/audit_writer.py        — Dual persist (PG + Storage) — 115 linhas
  libs/audit/lia_audit/audit_storage.py       — LocalFileStorage + S3Storage + lifecycle — 260 linhas
  libs/audit/lia_audit/audit_models.py        — ExecutionAuditRecord, LLMCallRecord, ToolCallRecord — 99 linhas
  app/shared/compliance/audit_service.py      — AuditService (decisões IA) — 14.5K
  alembic/versions/025_add_agent_execution_metadata.py — Schema da tabela — 70 linhas

AGENTES:
  libs/agents-core/lia_agents_core/langgraph_base.py       — _run_graph() com callback injection
  libs/agents-core/lia_agents_core/langgraph_react_base.py  — _process_langgraph(), TimedToolNode

RESILIÊNCIA:
  app/shared/resilience/circuit_breaker.py    — CircuitBreaker + decorator + circuitos pré-definidos — 552 linhas

OBSERVABILIDADE:
  app/observability/metrics.py                — 13 métricas Prometheus — 131 linhas

DOCUMENTAÇÃO:
  docs/analise-comparativa-v5-vs-lia.md       — Análise completa v9.0 (14 dimensões)
  docs/GUIA_ARQUITETURA_IA_v1.0.md            — Guia de arquitetura IA
```
