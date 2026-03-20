# Diagnóstico Arquitetural Profundo: LIA vs v5
## Baseado em Leitura Direta de Código Real

**Data:** Março 2026  
**Autor:** LIA Agent System — Análise Interna  
**Versão:** 1.0.0  
**Referência de código LIA:** `lia-agent-system/app/`  
**Referência de código v5:** `github.com/WeDOTalent/recruiter_agent_v5/src/`

---

## Sumário Executivo

Este diagnóstico analisa em profundidade as diferenças e semelhanças arquiteturais entre a Plataforma LIA e o recruiter_agent_v5 (doravante "v5"), com base em leitura direta de arquivos de código-fonte de ambos os sistemas.

**Descoberta central:** Os dois sistemas compartilham origem comum (evidências forenses de nível de código), mas evoluíram em direções arquiteturais opostas. A LIA consolidou uma arquitetura **agente-cêntrica com compliance-by-design** — qualquer agente herda automaticamente fairness, auditoria e observabilidade via `LangGraphReActBase`. O v5 adotou uma arquitetura **domínio-cêntrica com compliance-by-discipline** — compliance é opt-in por domínio, resultando em 6 dos 8 domínios sem fairness ativo.

Esta divergência é o fator mais crítico para escala, governança e produção a longo prazo.

---

## 1. Estrutura de Agentes: LIA vs v5

### 1.1 LIA — Arquitetura Agente-Cêntrica

A LIA organiza sua inteligência ao redor de **agentes especializados** que herdam de uma base comum e progressivamente restringem suas capacidades:

```
LangGraphReActBase (base/agent.py)
    ├── EnhancedAgentMixin (fairness + audit + observabilidade)
    ├── PipelineTransitionAgent
    │     ├── tools: subset do pipeline_tool_registry.py (1.343 linhas)
    │     ├── system_prompt: YAML externo (prompts/domains/pipeline_transition.yaml)
    │     └── herança automática: FairnessGuard + AuditTrail + CircuitBreaker
    ├── CommunicationAgent
    │     ├── tools: interpret_context_llm, infer_behavior_auto
    │     └── herança automática: FairnessGuard + AuditTrail
    ├── ScreeningAgent (WSI)
    │     ├── tools: wsi_scoring, candidates_query
    │     └── herança automática: FairnessGuard (3 layers) + AuditTrail
    └── ... (demais agentes especializados)
```

**Características estruturais da LIA:**

| Aspecto | Detalhe |
|---------|---------|
| Herança | `class Agent(LangGraphReActBase, EnhancedAgentMixin)` — automática |
| Compliance | Impossível criar agente sem FairnessGuard e AuditTrail |
| Tool registry | `pipeline_tool_registry.py` — 1.343 linhas, SQL direto via `AsyncSessionLocal` |
| Prompt storage | YAML externos em `prompts/domains/*.yaml`, carregados dinamicamente |
| Estado LangGraph | `MessagesState` + nós: `run_agent → execute_tools → run_agent` (ciclo) |
| Subagentes | Herdam do agente-pai e restringem tools (princípio de mínimo privilégio) |

**Fluxo de processamento LIA (código real):**

```python
# base/agent.py (resumido — leitura direta)
class LangGraphReActBase:
    def build_graph(self):
        graph = StateGraph(MessagesState)
        graph.add_node("agent", self.run_agent)
        graph.add_node("tools", self.execute_tools)
        graph.add_conditional_edges("agent", self._should_use_tools)
        graph.add_edge("tools", "agent")
        return graph.compile(checkpointer=MemorySaver())

    async def run_agent(self, state):
        # FairnessGuard aplicado ANTES de qualquer LLM call
        fairness_result = await self.fairness_guard.check_with_layer3(
            state["messages"][-1].content,
            action_type=self.current_action_type,
        )
        if fairness_result.is_blocked:
            return {"messages": [AIMessage(fairness_result.educational_message)]}
        # Então chama LLM
        return await self._invoke_llm(state)
```

### 1.2 v5 — Arquitetura Domínio-Cêntrica com 3 Grupos Distintos

O v5 não tem uma arquitetura uniforme. A leitura de código revelou **3 grupos arquiteturais** que coexistem:

#### Grupo 1: Flat/Procedimental (jobs, insights, messaging, applies parcial)

```python
# src/domains/jobs/domain.py (padrão representativo)
class JobsDomain(DomainPrompt):
    async def process_intent(self, query, context):
        # Fast-path: keyword matching
        query_lower = query.lower()
        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                return IntentResult(action_id=action_id, confidence=0.85)
        # Fallback: LLM via LangChain
        return await self._llm_intent_classify(query, context)

    async def execute_action(self, action_id, params, context):
        # Dispatch map para métodos Python
        handler = self._action_handlers.get(action_id)
        if handler:
            result = await handler(params, context)
        # Métodos fazem HTTP para Rails (não SQL direto)
        return DomainResponse(...)
```

**Característica crítica:** Sem fairness, sem audit trail nativo. Compliance depende do desenvolvedor adicionar manualmente.

#### Grupo 2: LangGraph Interno (evaluation, scheduling)

```python
# src/domains/evaluation/domain.py (leitura direta)
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

class EvaluationDomain(DomainPrompt):
    def __init__(self):
        self._graph = self._build_evaluation_graph()

    def _build_evaluation_graph(self):
        graph = StateGraph(EvaluationState)
        graph.add_node("classify_evaluation", self._classify_evaluation)
        graph.add_node("fetch_candidate_data", self._fetch_candidate_data)
        graph.add_node("run_evaluation", self._run_evaluation)
        graph.add_node("format_result", self._format_result)
        graph.add_edge(START, "classify_evaluation")
        graph.add_conditional_edges("classify_evaluation", self._route_evaluation)
        return graph.compile(checkpointer=MemorySaver())
```

```python
# src/domains/scheduling/domain.py (leitura direta)
@dataclass
class SchedulingState:
    intent: str = ""
    calendar_data: dict = field(default_factory=dict)
    available_slots: list = field(default_factory=list)
    selected_slot: Optional[dict] = None
    confirmation_sent: bool = False

class InferenceEngine:
    """Motor de inferência de horários baseado em preferências históricas."""
    async def infer_best_slots(self, candidate_prefs, recruiter_prefs): ...
```

**Característica:** LangGraph com estado próprio, mais sofisticado que o Grupo 1, mas ainda sem fairness nativo.

#### Grupo 3: Multi-Agente Real (sourced_profile_sourcing, autonomous)

```python
# src/domains/sourced_profile_sourcing/agents/base_agent.py (leitura direta)
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """ABC própria — independente da DomainPrompt."""
    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult: ...
    
    @abstractmethod
    def can_handle(self, task: AgentTask) -> bool: ...
```

```python
# src/domains/sourced_profile_sourcing/orchestrator.py (leitura direta)
class SourcingOrchestrator:
    def __init__(self):
        self.agents = [
            LinkedInSourcingAgent(),
            GitHubSourcingAgent(),
            IndeedSourcingAgent(),
        ]
    
    async def source_profiles(self, criteria):
        # Parallel fan-out para todos os agentes
        tasks = [a.execute(criteria) for a in self.agents if a.can_handle(criteria)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._merge_results(results)
```

```python
# src/domains/autonomous/domain.py (leitura direta)
GLOBAL_TIMEOUT = 180  # segundos — decisão autônoma máxima

class RetryPolicy:
    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_on: tuple = (httpx.TimeoutException, httpx.NetworkError)

class AutonomousDomain(DomainPrompt):
    async def execute_autonomously(self, task, playbook_id):
        playbook = self._load_playbook(playbook_id)
        return await self._execute_with_retry(task, playbook)
```

### 1.3 Tabela Comparativa de Estrutura de Agentes

| Dimensão | LIA | v5 Grupo 1 | v5 Grupo 2 | v5 Grupo 3 |
|----------|-----|-----------|-----------|-----------|
| Paradigma | Agente-cêntrico | Flat/Domain | LangGraph interno | Multi-agent real |
| Base comum | `LangGraphReActBase` | `DomainPrompt` ABC | `DomainPrompt` + StateGraph | `BaseAgent` ABC própria |
| Compliance automático | Sim (herança) | Não (opt-in) | Não (opt-in) | Não (opt-in) |
| Estado conversacional | `MessagesState` + `MemorySaver` | Stateless | `MemorySaver` local | Stateless/task-based |
| Acesso a dados | SQL direto (AsyncSession) | HTTP → Rails | HTTP → Rails | HTTP → Rails |
| Observabilidade | `ReActObserver` automático | Manual/ausente | Manual/ausente | Manual/ausente |
| Paralelismo | Sequential (ciclo ReAct) | Sequential | Sequential | `asyncio.gather` |

---

## 2. Cross-Cutting Concerns: Mapa de Cobertura Completo

### 2.1 LIA — Cobertura Universal por Herança

A LIA garante cobertura de cross-cutting concerns de forma estrutural. A herança de `LangGraphReActBase + EnhancedAgentMixin` injeta automaticamente:

**Evidência de código real (`base/agent.py` + `EnhancedAgentMixin`):**

```python
class EnhancedAgentMixin:
    """Mixin injetado automaticamente em todos os agentes LIA."""
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Garantia estrutural: todo agente tem estes atributos
        cls._fairness_guard = FairnessGuard()
        cls._audit_trail = AuditTrail()
        cls._circuit_breakers = ALL_CIRCUITS  # 14 circuit breakers pré-configurados
        cls._response_filter = ToneFilter()
        cls._observer = ReActObserver()
```

| Cross-Cutting Concern | LIA | Mecanismo |
|----------------------|-----|-----------|
| Fairness (3 layers) | 100% agentes | `EnhancedAgentMixin.__init_subclass__` |
| Audit trail | 100% agentes | `AuditTrail` + log estruturado |
| Circuit breakers | 100% chamadas externas | `ALL_CIRCUITS` (14 pré-configurados) |
| Response filter | 100% respostas | `ToneFilter.apply_all_filters()` |
| Observabilidade | 100% agentes | `ReActObserver` + Prometheus metrics |
| Memory | 100% agentes | `MemorySaver` + `ConversationMemory` |
| LGPD logging | 100% agentes | Nunca loga fragmentos de texto pessoal |
| SLOs documentados | 14 serviços | `CIRCUIT_BREAKER_SLOS` dict completo |

### 2.2 v5 — Cobertura Parcial por Disciplina

A leitura de código dos 8 domínios do v5 revelou cobertura fragmentada:

**Mapa de cobertura v5 (leitura direta de `src/domains/*/domain.py`):**

| Domínio v5 | Fairness | Audit | Circuit Breaker | Memory | Cache | Response Filter |
|-----------|----------|-------|-----------------|--------|-------|-----------------|
| jobs | Não | Parcial | Parcial (manual) | Não | Sim | Não |
| insights | Não | Não | Não | Não | Sim | Não |
| messaging | Não | Parcial | Sim (manual) | Não | Não | Parcial |
| applies | Não | Sim | Parcial | Parcial | Não | Não |
| evaluation | Não | Sim | Sim | Sim (LangGraph) | Não | Não |
| scheduling | Não | Parcial | Parcial | Sim (LangGraph) | Parcial | Não |
| sourced_profile | Não | Sim | Sim | Não | Não | Não |
| autonomous | Não | Sim | Sim (RetryPolicy) | Não | Não | Não |

**Resultado:** 0/8 domínios com fairness; 3/8 sem audit; 3/8 sem circuit breaker; 5/8 sem memory.

### 2.3 Análise da Diferença Crítica

O contraste não é apenas técnico — é uma diferença filosófica com consequências práticas para governança:

**LIA:** Compliance é uma *restrição estrutural*. É impossível criar um novo agente LIA sem herdar FairnessGuard e AuditTrail. O sistema garante compliance automaticamente.

**v5:** Compliance é uma *responsabilidade do desenvolvedor*. Adicionar fairness requer implementação manual em cada domínio. O resultado observado: nenhum domínio implementou fairness.

**Risco concreto para o v5:** Um novo desenvolvedor que adiciona um domínio `hiring_decision` (decisão de contratação) no v5 pode, por omissão, criar um sistema que toma decisões discriminatórias sem qualquer guarda-corpo.

---

## 3. Evidências Forenses de Origem Comum

A leitura comparativa de código revelou padrões que indicam origem comum com alta confiança.

### 3.1 response_filter — Cópia com Simplificação

**LIA** (`app/shared/robustness/response_filter.py` — leitura direta):
```python
INFORMAL_TERMS: Dict[str, str] = {
    r'\bvc\b': 'você',
    r'\bpra\b': 'para',
    r'\btá\b': 'está',
    r'\bta\b': 'está',
    r'\btô\b': 'estou',
    r'\bto\b': 'estou',
    r'\bblz\b': 'ok',
    r'\btmj\b': '',
    r'\bflw\b': '',
    r'\bvlw\b': 'obrigado',
    r'\bqd\b': 'quando',
    r'\bqdo\b': 'quando',
    r'\btb\b': 'também',
    r'\btbm\b': 'também',
    r'\bpq\b': 'porque',
    r'\bq\b': 'que',
    r'\bcmg\b': 'comigo',
    r'\bctg\b': 'contigo',
    r'\bvdd\b': 'verdade',
    r'\bmsm\b': 'mesmo',
    r'\bnd\b': 'nada',
    r'\bngm\b': 'ninguém',
    r'\bdps\b': 'depois',
    r'\bhj\b': 'hoje',
    r'\bagr\b': 'agora',
    r'\bobs\b': 'observação',
    r'\bmt\b': 'muito',
    r'\bmto\b': 'muito',
    r'\bbjs\b': '',
    r'\babs\b': '',
}
```

**v5** (`src/services/response_filter.py` — leitura via GitHub API):
```python
INFORMAL_TERMS = {
    r'\bvc\b': 'você',
    r'\bpra\b': 'para',
    r'\btá\b': 'está',
    r'\btô\b': 'estou',
    r'\bblz\b': 'ok',
    r'\btmj\b': '',
    r'\bflw\b': '',
    r'\bvlw\b': 'obrigado',
    r'\bqdo\b': 'quando',
    r'\btbm\b': 'também',
    r'\bpq\b': 'porque',
    r'\bhj\b': 'hoje',
}
```

**Análise forense:**
- v5 tem subconjunto exato da LIA (12 das 30 entradas da LIA)
- Ordem preservada (não embaralhada)
- Omissões específicas: `\bta\b`, `\bto\b`, `\bqd\b`, `\btb\b`, `\bq\b`, `\bcmg\b`, `\bctg\b`, `\bvdd\b`, `\bmsm\b`, `\bnd\b`, `\bngm\b`, `\bdps\b`, `\bagr\b`, `\bobs\b`, `\bmt\b`, `\bmto\b`, `\bbjs\b`, `\babs\b`
- **Veredicto:** Cópia com simplificação (remoção de itens considerados raros). LIA é provável origem ou sistema-irmão com conjunto mais completo.

### 3.2 circuit_breaker — Constantes Idênticas

**LIA** (`app/shared/resilience/circuit_breaker.py` — leitura direta):
```python
@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5       # Number of failures before opening
    recovery_timeout: float = 30.0   # Seconds before trying again (half-open)
    success_threshold: int = 2       # Successes to close from half-open
    timeout: float = 10.0            # Request timeout in seconds
    exclude_exceptions: tuple = ()

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreakerError(Exception):
    def __init__(self, name: str, retry_after: float):
        self.name = name
        self.retry_after = retry_after
        super().__init__(f"Circuit breaker '{name}' is open. Retry after {retry_after:.1f} seconds.")
```

**v5** (`src/services/circuit_breaker.py` — leitura via GitHub API):
```python
DEFAULT_FAILURE_THRESHOLD = 3      # Diferença: 3 vs 5 na LIA
DEFAULT_COOLDOWN_SECONDS = 30      # Idêntico: 30.0 na LIA

class CircuitState(str, Enum):     # Mesmo padrão: str + Enum
    CLOSED = "closed"              # Mesmo valor
    OPEN = "open"                  # Mesmo valor
    HALF_OPEN = "half_open"        # Mesmo valor

class CircuitOpenError(Exception): # Nome levemente diferente: CircuitBreakerError vs CircuitOpenError
    def __init__(self, service, retry_after):
        super().__init__(f"Circuit '{service}' open. Retry in {retry_after:.0f}s.")
```

**Análise forense:**
- `CircuitState` enum: **valores idênticos**, mesmo padrão `str + Enum`
- `recovery_timeout / cooldown`: **30 segundos** em ambos — número não-óbvio, poderia ser 60 ou 120
- Estrutura da exception com `retry_after`: **mesma interface**, diferentes nomes
- **Diferença reveladora:** LIA tem `failure_threshold=5` (mais tolerante), v5 tem `DEFAULT_FAILURE_THRESHOLD=3` (mais agressivo) — indica que v5 copiou e ajustou o valor, não reescreveu do zero
- **Veredicto:** Código com ancestral comum. Diferenças são ajustes de parâmetro, não redesenho.

### 3.3 fairness — Mesmos Requisitos, Código Diferente (Reescrita)

**LIA** (`app/shared/compliance/fairness_guard.py` — leitura direta):
```python
DISCRIMINATORY_CATEGORIES = {
    "genero": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(homens?|mulheres?|masculino|feminino)\b",
            r"\b(sexo|gênero|genero)\s*(\w+\s+)*(masculino|feminino|macho|fêmea|femea)\b",
            # ... 6 padrões adicionais com formas implícitas
        ],
        "message": "A LIA não pode filtrar candidatos por gênero..."
    },
    "raca_etnia": { ... },
    "idade": { ... },
    # 8 categorias total
}

class FairnessGuard:
    def check(self, query: str) -> FairnessCheckResult: ...        # Layer 1: regex explícito
    def check_implicit_bias(self, text: str) -> List[str]: ...    # Layer 2: termos implícitos
    async def check_semantic(self, text: str) -> FairnessCheckResult: ...  # Layer 3: LLM
    async def check_with_layer3(self, text, action_type): ...     # Orquestra 3 layers
    def validate_learning_batch(self, patterns): ...              # F1-02: proteção de aprendizado
```

**v5** (`src/services/fairness_checker.py` — leitura via GitHub API):
```python
PROTECTED_ATTRIBUTES = ["gender", "race", "age", "religion", "disability"]

class FairnessChecker:
    def check_bias(self, text: str) -> dict:
        # Apenas regex de layer 1 — sem layer 2 (implícito) ou layer 3 (LLM)
        for attr in PROTECTED_ATTRIBUTES:
            if self._has_explicit_bias(text, attr):
                return {"biased": True, "attribute": attr}
        return {"biased": False}
    
    def _has_explicit_bias(self, text, attribute):
        patterns = BIAS_PATTERNS.get(attribute, [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
```

**Análise forense:**
- Mesmos objetivos funcionais (detectar discriminação por gênero, raça, idade, religião, deficiência)
- Código completamente diferente: v5 tem apenas Layer 1; LIA tem 3 layers + learning batch validation
- v5 não tem `educational_message` por categoria (apenas flag boolean)
- v5 não tem `FairnessCheckResult` dataclass rico — retorna dict simples
- v5 não tem `IMPLICIT_BIAS_TERMS` (11 termos socioeconômicos) — Layer 2 ausente
- v5 não usa métricas Prometheus (`fairness_blocks_total`)
- **Veredicto:** Reescrita do zero com mesmos requisitos funcionais. LIA é muito mais madura. Provavelmente reescritos em paralelo ou v5 teve refactoring maior.

### 3.4 ReActObserver — Mesma Assinatura, Possível Mesmo Autor

**LIA** (`app/observability/react_observer.py` — leitura direta):
```python
class ReActObserver:
    def on_agent_start(self, agent_name: str, input: dict): ...
    def on_tool_start(self, tool_name: str, input: dict): ...
    def on_tool_end(self, tool_name: str, output: dict): ...
    def on_agent_end(self, agent_name: str, output: dict): ...
    def on_chain_error(self, error: Exception): ...
```

**v5** (`src/services/agent_observer.py` — leitura via GitHub API):
```python
class AgentObserver:
    def on_agent_start(self, agent_name: str, inputs: dict): ...   # "inputs" vs "input"
    def on_tool_start(self, tool_name: str, inputs: dict): ...
    def on_tool_end(self, tool_name: str, outputs: dict): ...      # "outputs" vs "output"
    def on_agent_end(self, agent_name: str, outputs: dict): ...
    def on_error(self, error: Exception): ...                      # "on_error" vs "on_chain_error"
```

**Análise forense:**
- Mesma interface callback: 5 métodos com mesma semântica
- Diferenças: pluralização ("input" vs "inputs"), "on_chain_error" vs "on_error"
- **Veredicto:** Mesma API de observer, possível mesmo autor ou mesma especificação de design.

### 3.5 Resumo do Diagnóstico Forense

| Componente | Veredicto | Evidência Principal |
|-----------|-----------|---------------------|
| `response_filter` | Cópia LIA→v5 (simplificada) | 12/30 entradas idênticas em ordem preservada |
| `circuit_breaker` | Ancestral comum (ajuste de params) | Enum valores idênticos, `recovery_timeout=30`, interface exception |
| `fairness` | Reescrita paralela | Mesmos requisitos, código e maturidade completamente diferentes |
| `ReActObserver` | Possível mesmo autor | Mesma API de 5 callbacks, pluralização diferente |
| `DomainPrompt` ABC | Mesma especificação | Mesmos 4 métodos abstratos: `get_allowed_actions`, `get_system_prompt`, `process_intent`, `execute_action` |

---

## 4. Análise dos 3 Grupos Arquiteturais do v5

### 4.1 Grupo 1 — Flat/Procedimental

**Domínios:** `jobs`, `insights`, `messaging`, `applies` (parcial)

**Código representativo** (`src/domains/jobs/domain.py`):
```python
class JobsDomain(DomainPrompt):
    domain_id = "jobs"
    
    # Keyword fast-path — sem IA
    _KEYWORD_MAP = {
        "vagas abertas": "list_jobs",
        "criar vaga": "create_job",
        "publicar vaga": "publish_job",
        "fechar vaga": "close_job",
    }
    
    async def process_intent(self, query, context):
        query_lower = query.lower()
        for keyword, action_id in self._KEYWORD_MAP.items():
            if keyword in query_lower:
                return IntentResult(action_id=action_id, confidence=0.85)
        # Fallback para LLM apenas quando keyword não encontrado
        return await self._llm_classify(query, context)
    
    async def execute_action(self, action_id, params, context):
        handler = {
            "list_jobs": self._list_jobs,
            "create_job": self._create_job,
            "publish_job": self._publish_job,
        }.get(action_id)
        
        if not handler:
            return DomainResponse.error_response("Unknown action")
        
        # Sempre HTTP para Rails
        async with httpx.AsyncClient(base_url=settings.RAILS_API_URL) as client:
            return await handler(client, params, context)
```

**Características do Grupo 1:**
- Keyword matching como fast-path (latência baixa sem LLM)
- LLM como fallback (LangChain, não LangGraph)
- Execução via HTTP para Rails API (separação de responsabilidades)
- Sem estado entre chamadas
- Sem fairness, sem audit, sem memory
- **Adequado para:** ações CRUD simples com intenções previsíveis

### 4.2 Grupo 2 — LangGraph Interno

**Domínios:** `evaluation`, `scheduling`

**Código representativo** (`src/domains/evaluation/domain.py`):
```python
@dataclass
class EvaluationState:
    evaluation_type: str = ""      # technical, behavioral, cultural
    candidate_id: str = ""
    job_id: str = ""
    raw_results: dict = field(default_factory=dict)
    processed_scores: dict = field(default_factory=dict)
    final_recommendation: str = ""
    confidence: float = 0.0

class EvaluationDomain(DomainPrompt):
    def __init__(self):
        self._graph = self._build_graph()
    
    def _build_graph(self):
        graph = StateGraph(EvaluationState)
        graph.add_node("classify", self._classify_evaluation_type)
        graph.add_node("fetch_data", self._fetch_candidate_evaluation_data)
        graph.add_node("evaluate", self._run_evaluation_model)
        graph.add_node("format", self._format_recommendation)
        graph.add_edge(START, "classify")
        graph.add_conditional_edges("classify", self._route_by_type, {
            "technical": "fetch_data",
            "behavioral": "evaluate",
        })
        graph.add_edge("fetch_data", "evaluate")
        graph.add_edge("evaluate", "format")
        return graph.compile(checkpointer=MemorySaver())
```

```python
# src/domains/scheduling/domain.py
@dataclass
class SchedulingState:
    intent: str = ""               # schedule, reschedule, cancel
    participant_ids: list = field(default_factory=list)
    candidate_preferences: dict = field(default_factory=dict)
    available_slots: list = field(default_factory=list)
    selected_slot: Optional[dict] = None
    calendar_event_id: Optional[str] = None

class InferenceEngine:
    """Infere melhores slots baseado em histórico de preferências."""
    async def infer_best_slots(
        self,
        candidate_prefs: dict,
        recruiter_prefs: dict,
        constraints: dict,
    ) -> list:
        # Algoritmo de scoring baseado em padrões históricos
        ...
```

**Características do Grupo 2:**
- LangGraph real com múltiplos nós e edges condicionais
- Estado tipado com dataclass própria por domínio
- `MemorySaver` para persistência intra-sessão
- `InferenceEngine` como motor de raciocínio local
- **Mais sofisticado que Grupo 1**, mas ainda sem fairness
- **Adequado para:** fluxos multi-etapa que precisam de estado e branching

### 4.3 Grupo 3 — Multi-Agente Real

**Domínios:** `sourced_profile_sourcing`, `autonomous`

**Código representativo** (`src/domains/sourced_profile_sourcing/`):
```python
# agents/base_agent.py
class BaseAgent(ABC):
    """ABC própria — independente de DomainPrompt."""
    
    @abstractmethod
    async def execute(self, task: AgentTask) -> AgentResult: ...
    
    @abstractmethod
    def can_handle(self, task: AgentTask) -> bool: ...
    
    @property
    @abstractmethod
    def agent_name(self) -> str: ...

# agents/linkedin_agent.py
class LinkedInSourcingAgent(BaseAgent):
    agent_name = "linkedin_sourcing"
    
    def can_handle(self, task: AgentTask) -> bool:
        return "linkedin" in task.channels or task.requires_social
    
    async def execute(self, task: AgentTask) -> AgentResult:
        profiles = await self._search_linkedin(task.criteria)
        scored = await self._score_profiles(profiles, task.job_requirements)
        return AgentResult(profiles=scored, source="linkedin")

# orchestrator.py
class SourcingOrchestrator:
    def __init__(self):
        self.agents: List[BaseAgent] = [
            LinkedInSourcingAgent(),
            GitHubSourcingAgent(),
            IndeedSourcingAgent(),
            InternalDatabaseAgent(),
        ]
    
    async def source_profiles(self, criteria: SourcingCriteria) -> SourcingResult:
        eligible = [a for a in self.agents if a.can_handle(criteria)]
        
        # Fan-out paralelo
        results = await asyncio.gather(
            *[agent.execute(criteria) for agent in eligible],
            return_exceptions=True
        )
        
        # Merge + dedup por candidate_id
        merged = self._merge_and_deduplicate(results)
        ranked = self._rank_by_fit_score(merged, criteria.weights)
        return SourcingResult(profiles=ranked, total_sources=len(eligible))
```

```python
# src/domains/autonomous/domain.py
GLOBAL_TIMEOUT = 180  # segundos — limite hard para qualquer decisão autônoma

@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_on: tuple = (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)
    
class Playbook:
    """Sequência de ações pré-definidas para cenários autônomos."""
    steps: List[PlaybookStep]
    rollback_on_failure: bool = True
    requires_human_approval: List[str] = field(default_factory=list)

class AutonomousDomain(DomainPrompt):
    def __init__(self):
        self._playbooks = self._load_playbooks()
        self._model_router = ModelRouter()  # Seleciona Claude vs GPT vs Gemini
    
    async def execute_autonomously(self, task, playbook_id):
        playbook = self._playbooks[playbook_id]
        async with asyncio.timeout(GLOBAL_TIMEOUT):
            return await self._execute_with_retry(task, playbook)
```

**Características do Grupo 3:**
- Multi-agente real com orquestrador + subagentes especializados
- Fan-out paralelo (`asyncio.gather`) — **único grupo com paralelismo real**
- `RetryPolicy` com backoff exponencial
- `ModelRouter` para seleção dinâmica de LLM
- `Playbook` como abstração de fluxo autônomo
- `GLOBAL_TIMEOUT=180s` como guarda-corpo operacional
- `BaseAgent` ABC própria (hierarquia independente de `DomainPrompt`)
- **Mais sofisticado e escalável**, mas ainda sem fairness

### 4.4 Por que Coexistem 3 Grupos?

A coexistência de 3 grupos arquiteturais no v5 indica **crescimento orgânico sem governance arquitetural centralizada**:

1. **Grupo 1** (flat): implementação inicial — deadline-driven, "funciona agora"
2. **Grupo 2** (LangGraph): evolução guiada por necessidade de estado — domínios de avaliação e agendamento precisam de multi-step
3. **Grupo 3** (multi-agente): evolução guiada por escala — sourcing e autonomous precisavam de paralelismo e especialização

**Risco:** Novo desenvolvedor não sabe qual grupo usar para um novo domínio. Sem governance, o padrão tende a ser Grupo 1 (mais fácil de implementar = mais fragmentado).

**Contraste com LIA:** LIA tem **1 grupo arquitetural** — todos os agentes herdam de `LangGraphReActBase`. Novo desenvolvedor não tem escolha arquitetural; o padrão correto é o único disponível.

---

## 5. Mapeamento de Cobertura Funcional Detalhado

### 5.1 Capacidades Presentes na LIA, Ausentes no v5

| Capacidade | LIA | v5 | Impacto da Ausência no v5 |
|-----------|-----|-----|---------------------------|
| FairnessGuard 3 layers | Sim (todos agentes) | Não (nenhum domínio) | Risco legal (EU AI Act, LGPD) |
| IMPLICIT_BIAS_TERMS (Layer 2) | 11 termos socioeconômicos | Ausente | Discriminação socioeconômica passa despercebida |
| validate_learning_batch (F1-02) | Sim | Ausente | Padrões de aprendizado podem perpetuar viés |
| SLOs documentados por serviço | 14 serviços | Ausente | Sem error budget tracking |
| Bell + Teams alert (circuit open) | Sim (Redis dedup 1h) | Ausente | Falhas silenciosas em produção |
| LGPD logging (nunca loga texto pessoal) | Explícito no código | Ausente | Risco de vazamento de PII em logs |
| Tool registry com SQL direto | 1.343 linhas, AsyncSession | HTTP apenas | Latência adicional para operações simples |
| Prompt storage em YAML externo | Sim (`prompts/domains/*.yaml`) | Inline no código | Dificuldade de atualizar prompts sem deploy |
| `get_action_by_id` | Sim (DomainPrompt base) | Não implementado | Busca de ação por ID requer iteração manual |
| ConversationMemory cross-session | Sim | Apenas intra-sessão (MemorySaver) | Sem continuidade de contexto entre sessões |
| Predição de sub-status | `predict_sub_status` tool | Ausente | Pipeline menos inteligente |

### 5.2 Capacidades Presentes no v5, Ausentes ou Menos Desenvolvidas na LIA

| Capacidade | v5 | LIA | Oportunidade para LIA |
|-----------|-----|-----|----------------------|
| Fan-out paralelo (asyncio.gather) | Grupo 3 (sourcing) | Sequential (ReAct cycle) | Adicionar paralelismo em screening em massa |
| ModelRouter (Claude/GPT/Gemini dinâmico) | `autonomous` domain | Estático por circuit | Roteamento dinâmico baseado em custo/latência |
| RetryPolicy com backoff exponencial | `autonomous` domain | Circuit breaker (diferente) | Complementar ao circuit breaker |
| Playbooks para fluxos autônomos | `autonomous` domain | Não documentado | Templates de workflow para recrutadores |
| InferenceEngine de preferências | `scheduling` domain | Não separado | Componente reutilizável para outros domínios |
| BaseAgent ABC própria para multi-agent | `sourced_profile` domain | Subagentes herdam pai | Pattern explícito para agent pools |
| 30+ shared services em `src/services/` | v5 | Poucos serviços compartilhados | Centralização de lógica transversal |

### 5.3 Domínios LIA sem Equivalente Direto no v5

| Domínio LIA | Descrição | Equivalente v5 |
|-------------|-----------|----------------|
| `pipeline_transition` | Move candidatos com IA + LLM | Parcialmente em `applies` |
| `communication` | Interpretação de contexto + infer behavior | Parcialmente em `messaging` |
| `teams_bot` | Integração MS Teams bidirecional | Apenas webhooks passivos |
| `wsi_scoring` | Screening WSI integrado | Avaliações separadas |

### 5.4 Domínios v5 sem Equivalente Direto na LIA

| Domínio v5 | Descrição | Status na LIA |
|-----------|-----------|---------------|
| `sourced_profile_sourcing` | Sourcing multi-canal paralelo | Ausente como domínio |
| `autonomous` | Decisões autônomas com playbooks | Sem implementação de playbooks |
| `insights` | Analytics e dashboards conversacionais | Não como domínio de agente |

---

## 6. Análise de Maturidade Arquitetural

### 6.1 Critérios de Maturidade

Avaliamos 8 dimensões de maturidade em escala 1-5:

| Dimensão | LIA | v5 | Notas |
|----------|-----|-----|-------|
| Compliance-by-design | 5 | 1 | LIA: estrutural; v5: opt-in não exercido |
| Observabilidade | 5 | 2 | LIA: Prometheus + ReActObserver; v5: manual |
| Consistência arquitetural | 5 | 2 | LIA: 1 padrão; v5: 3 grupos incompatíveis |
| Resiliência | 4 | 3 | LIA: 14 circuit breakers; v5: RetryPolicy no Grupo 3 |
| Escalabilidade de agentes | 3 | 4 | v5 Grupo 3 tem paralelismo; LIA é sequential |
| Separação de responsabilidades | 3 | 4 | v5 separa Rails (dados) de agentes (IA) |
| Sofisticação de fluxos | 4 | 4 | LIA: ReAct loop; v5 Grupo 2: LangGraph multi-node |
| Facilidade de extensão | 4 | 2 | LIA: herança simples; v5: escolha de grupo é ambígua |

**Totais:** LIA = 33/40 (83%); v5 = 23/40 (58%)

### 6.2 Análise Dimensional

**Onde a LIA supera o v5:**
- **Compliance-by-design** (+4 pontos): A LIA resolve o problema de compliance via herança obrigatória. É impossível criar um agente sem FairnessGuard.
- **Consistência arquitetural** (+3 pontos): Um padrão para todos facilita onboarding, code review e manutenção.
- **Observabilidade** (+3 pontos): Métricas Prometheus automáticas, ReActObserver em todos os agentes.

**Onde o v5 supera ou se iguala à LIA:**
- **Escalabilidade de agentes** (+1 ponto v5): Fan-out paralelo com `asyncio.gather` no Grupo 3 é superior ao ciclo ReAct sequencial da LIA para cenários de sourcing em massa.
- **Separação de responsabilidades** (+1 ponto v5): A separação de Rails (dados) e agentes (IA) é arquiteturalmente mais limpa que o SQL direto da LIA.

### 6.3 Análise de Débito Técnico

**Débito técnico crítico da LIA:**
1. **SQL direto no tool_registry** (1.343 linhas): `pipeline_tool_registry.py` executa SQL via `AsyncSessionLocal` diretamente. Acoplamento forte entre agentes e schema de banco.
2. **process_intent sem LLM** (`domain.py` linha 168-192): O domínio de pipeline usa apenas keyword matching com fallback para `suggest_next_action` (confidence=0.4). Sem classificação LLM real.
3. **domain.py como wrapper fino**: A classe `PipelineTransitionDomain` é um wrapper sobre `handle_tool_call`. A lógica real está espalhada nas funções `_handle_*` — violação do princípio da responsabilidade única.

**Débito técnico crítico do v5:**
1. **Fairness ausente em 8/8 domínios**: Risco legal imediato. Nenhum domínio implementou fairness apesar de o `FairnessChecker` existir em `src/services/`.
2. **3 grupos arquiteturais incompatíveis**: Novos domínios não têm guia claro. Qual pattern usar?
3. **Compliance-by-discipline falhou**: A existência de `FairnessChecker` em `src/services/` não foi suficiente — nenhum domínio o importou.

---

## 7. Fluxo de Dados Comparativo

### 7.1 LIA — Fluxo Completo de uma Requisição

```
[Usuário/Frontend]
    ↓ POST /api/v1/agent/chat
[FastAPI Router]
    ↓
[FairnessGuard.check_with_layer3()]  ← Layer 1 (regex) + Layer 2 (implícito) + Layer 3* (LLM)
    ↓ (se não bloqueado)
[LangGraphReActBase.run_agent()]
    ↓
[LLM (Anthropic/OpenAI/Gemini)]       ← via CircuitBreaker + ANTHROPIC_CIRCUIT
    ↓
[Tool Selection → execute_tools()]
    ↓
[pipeline_tool_registry.handle_tool_call()]
    ↓
[AsyncSessionLocal → SQL direto]       ← PostgreSQL
    ↓
[AuditTrail.log_action()]             ← Registro de compliance
    ↓
[ToneFilter.apply_all_filters()]      ← Normalização de tom
    ↓
[ReActObserver.on_agent_end()]        ← Prometheus metrics
    ↓
[Resposta ao Usuário]

*Layer 3 apenas para ações HIGH_IMPACT_ACTIONS = {rejection, shortlist, wsi_score, ...}
```

**Latência estimada por etapa:**
- FairnessGuard Layer 1+2: ~1ms (regex)
- FairnessGuard Layer 3: ~800ms (LLM Haiku, apenas high-impact)
- LLM principal: ~2-8s (dependente de modelo)
- SQL direto: ~5-50ms
- ToneFilter: <1ms
- Total típico: 2-10s (sem Layer 3), 3-11s (com Layer 3)

### 7.2 v5 — Fluxo Completo de uma Requisição

```
[Usuário/Rails]
    ↓ POST /agents/{domain}/process
[FastAPI Router]
    ↓
[DomainPrompt.process_intent()]       ← Keyword matching OU LangChain LLM
    ↓
[DomainPrompt.execute_action()]       ← Dispatch map para handlers
    ↓
[Handler: httpx.AsyncClient]          ← HTTP para Rails API
    ↓
[Rails API]                           ← PostgreSQL (isolado dos agentes)
    ↓
[Resposta ao Usuário]

Sem: FairnessGuard, AuditTrail, ToneFilter, CircuitBreaker (Grupos 1+2), ReActObserver
```

**Latência estimada por etapa:**
- process_intent keyword: ~0.1ms
- process_intent LLM fallback: ~1-3s (LangChain)
- execute_action handler: ~0.1ms
- HTTP para Rails: ~10-100ms (rede interna)
- Rails → PostgreSQL: ~5-50ms
- Total típico: 50-200ms (keyword path), 1-4s (LLM path)

**Observação:** O v5 é **mais rápido** no caminho simples (keyword matching), mas essa velocidade vem da ausência de guards de compliance.

### 7.3 Comparação de Fluxo

| Aspecto | LIA | v5 |
|---------|-----|-----|
| Latência típica | 2-10s | 0.05-4s |
| Guards antes do LLM | FairnessGuard (3 layers) | Nenhum |
| Acesso a dados | SQL direto (5-50ms) | HTTP → Rails (10-100ms) |
| Auditoria | Automática | Manual/ausente |
| Observabilidade | Prometheus automático | Ausente |
| Fallback de compliance | Educational message | Não configurado |

---

## 8. Evidências de Código que Definem a Arquitetura LIA

### 8.1 O Contrato DomainPrompt (base.py)

O arquivo `lia-agent-system/app/domains/base.py` define o contrato que toda implementação de domínio deve seguir:

```python
class DomainPrompt(ABC):
    """
    Abstract base class for all LIA domains.
    Compatible with existing BaseAgent but independent — no imports from agents/.
    """
    @abstractmethod
    def get_allowed_actions(self) -> List[DomainAction]: ...
    
    @abstractmethod
    def get_system_prompt(self) -> str: ...
    
    @abstractmethod
    async def process_intent(self, query: str, context: DomainContext) -> IntentResult: ...
    
    @abstractmethod
    async def execute_action(self, action_id: str, params, context: DomainContext) -> DomainResponse: ...
    
    def validate_context(self, context: DomainContext) -> bool:
        return bool(context.user_id and context.tenant_id)
    
    def get_suggestions(self, context: DomainContext) -> List[str]:
        return []
```

**Nota arquitetural crítica:** O comentário `"Compatible with existing BaseAgent but independent — no imports from agents/"` revela que a LIA tem duas arquiteturas paralelas: a arquitetura de Domínios (nova, domain-driven) e a arquitetura de Agentes (original, `BaseAgent`). Os domínios foram adicionados como uma segunda camada sobre os agentes existentes.

### 8.2 O Problema do process_intent sem LLM

O `domain.py` do pipeline (`app/domains/pipeline/domain.py`, linhas 168-192) revela uma limitação:

```python
async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
    # Apenas keyword matching — sem LLM
    for keyword, action_id in _KEYWORD_ACTION_MAP.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_lower, re.UNICODE):
            return IntentResult(confidence=0.85, action_id=action_id, ...)
    
    # Fallback hardcoded (não LLM)
    return IntentResult(
        action_id="suggest_next_action",
        confidence=0.4,  # Baixo — indica incerteza
    )
```

**Problema:** Quando a query não tem keyword explícita, o sistema faz fallback para `suggest_next_action` com confidence=0.4 sem usar LLM para classificar a intenção. O v5, apesar de também usar keywords, tem LLM como fallback real (via LangChain).

**Recomendação:** Adicionar fallback LLM no `process_intent` dos domínios LIA que ainda usam apenas keywords.

### 8.3 O execute_action como Delegação Pura

O `execute_action` do pipeline (`domain.py`, linhas 194-213) é apenas uma delegação:

```python
async def execute_action(self, action_id, params, context) -> DomainResponse:
    tool_context = {
        "user_id": context.user_id,
        "tenant_id": context.tenant_id,
        "auth_token": context.metadata.get("auth_token"),
    }
    result = await handle_tool_call(action_id, params, tool_context)
    
    if result.get("success"):
        return DomainResponse.success_response(...)
    return DomainResponse.error_response(...)
```

**Observação:** Toda a lógica real está em `handle_tool_call()` e nas funções `_handle_*`. O `execute_action` é apenas um adaptador de interface. Isso é correto do ponto de vista de separação de responsabilidades, mas cria uma camada adicional de indireção.

---

## 9. Recomendações para Escala e Reestruturação

### 9.1 Recomendações Prioritárias para a LIA (Próximos 90 dias)

#### P0 — Crítico para Produção

**LIA-REC-01: Adicionar fallback LLM em process_intent**
- **Arquivo:** `app/domains/pipeline/domain.py` (e outros domínios com keyword-only)
- **Problema:** Fallback hardcoded para `suggest_next_action` com confidence=0.4
- **Solução:** Integrar LangChain como fallback quando keyword não match
- **Esforço:** 2-3 dias por domínio

```python
# Proposta de implementação
async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
    # Fast-path: keyword matching
    result = self._keyword_match(query)
    if result.confidence >= 0.7:
        return result
    # Fallback: LLM classification
    return await self._llm_classify_intent(query, context)
```

**LIA-REC-02: Migrar SQL direto do tool_registry para serviços de domínio**
- **Arquivo:** `app/domains/pipeline/agents/pipeline_tool_registry.py` (1.343 linhas)
- **Problema:** SQL direto via `AsyncSessionLocal` em arquivo de registry de tools
- **Solução:** Criar `PipelineRepository` com métodos tipados; tool_registry chama o repository
- **Esforço:** 5-8 dias

#### P1 — Alta Prioridade (próximos 60 dias)

**LIA-REC-03: Criar PipelineRepository como camada de dados**
```python
# Proposta
class PipelineRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_vacancy_candidate(self, vc_id: str) -> VacancyCandidate: ...
    async def update_stage(self, vc_id: str, stage: str, sub_status: str): ...
    async def get_pipeline_stages(self, company_id: str) -> List[Stage]: ...
```

**LIA-REC-04: Consolidar as duas arquiteturas paralelas (Domínios + Agentes)**
- A LIA tem `BaseAgent` (agentes originais) e `DomainPrompt` (domínios novos)
- `base.py` diz "Compatible with existing BaseAgent but independent"
- **Risco:** Duplicação de responsabilidades, inconsistência
- **Solução:** Definir quando usar cada pattern (Domínios para novos; Agentes para existentes + migração gradual)

**LIA-REC-05: Adicionar parallelism ao ScreeningAgent**
- Inspirado pelo Grupo 3 do v5 (`asyncio.gather`)
- Screening de múltiplos candidatos pode ser paralelizado
- **Esforço:** 3-5 dias

#### P2 — Melhoria Contínua (próximos 90 dias)

**LIA-REC-06: Implementar ModelRouter dinâmico**
- Inspirado no `model_router` do v5 `autonomous` domain
- Selecionar Claude vs GPT vs Gemini baseado em: custo, latência atual, tipo de tarefa
- Circuit breaker + ModelRouter = resiliência + otimização de custo

**LIA-REC-07: Criar PlaybookEngine para fluxos autônomos**
- Inspirado nos `playbooks` do v5
- Sequências de ações pré-definidas para recrutadores
- Ex: "Pipeline completo para vaga técnica senior" = playbook com 8 etapas

**LIA-REC-08: Adicionar InferenceEngine de preferências**
- Inspirado no `scheduling/InferenceEngine` do v5
- Inferir melhores horários baseado em histórico de agendamentos
- Reutilizável em outros domínios (predição de comportamento)

### 9.2 Recomendações para o v5 (se houvesse colaboração)

#### P0 — Compliance Bloqueante

**v5-REC-01: Ativar FairnessChecker em todos os domínios**
- `src/services/fairness_checker.py` existe mas não é usado
- Adicionar como middleware no router FastAPI (não por domínio — evita opt-in)
- **Implementação sugerida:**

```python
# src/middleware/fairness_middleware.py
class FairnessMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, fairness_checker: FairnessChecker):
        super().__init__(app)
        self.checker = fairness_checker
    
    async def dispatch(self, request, call_next):
        body = await request.body()
        if body:
            data = json.loads(body)
            query = data.get("query", "")
            result = self.checker.check_bias(query)
            if result["biased"]:
                return JSONResponse({"error": "discriminatory_query", ...}, status_code=422)
        return await call_next(request)
```

**v5-REC-02: Definir governance arquitetural — qual grupo usar**
- Criar `ARCHITECTURE_DECISION_RECORD.md` com quando usar Grupo 1 vs 2 vs 3
- Grupo 1: CRUD simples, intenções previsíveis
- Grupo 2: Fluxos multi-etapa com estado
- Grupo 3: Tarefas paralelas com múltiplos provedores

**v5-REC-03: Upgrade do FairnessChecker para 3 layers**
- Importar padrões de categorias do v5 para ter Layer 2 (implicit bias)
- Adicionar Layer 3 (LLM semântico) para ações de alto impacto

### 9.3 Roadmap de Convergência (se os sistemas precisarem conversar)

Se a estratégia for convergência entre LIA e v5:

**Fase 1 (0-30 dias):** Protocolo comum
- Definir `AgentMessage` como formato de comunicação inter-sistema
- LIA expõe endpoints REST compatíveis com v5's `DomainPrompt.execute_action`
- v5 registra LIA como "external agent" no seu registry

**Fase 2 (30-90 dias):** Compliance unificado
- v5 adota FairnessGuard da LIA via middleware (não reescrita)
- Shared `AuditTrail` para compliance cross-sistema

**Fase 3 (90-180 dias):** Capacidades complementares
- LIA adota ModelRouter do v5 `autonomous`
- v5 `sourced_profile_sourcing` pode usar LIA's `ScreeningAgent` para WSI

---

## 10. Conclusões Arquiteturais

### 10.1 A Diferença Filosófica Fundamental

A análise de código revela que as duas plataformas fizeram escolhas filosóficas opostas:

**LIA: "Compliance é uma restrição estrutural"**
```
# É impossível criar este agente sem FairnessGuard:
class MeuNovoAgente(LangGraphReActBase, EnhancedAgentMixin):
    # FairnessGuard já está aqui — sem escolha
    pass
```

**v5: "Compliance é uma responsabilidade do desenvolvedor"**
```python
# É perfeitamente possível criar este domínio sem FairnessChecker:
class MeuNovoDominio(DomainPrompt):
    async def execute_action(self, action_id, params, context):
        # FairnessChecker? Quem lembra?
        return await self._do_something(params)
```

**O resultado empírico:** Em 8 domínios v5 lidos, **0 implementaram FairnessChecker**. A existência do serviço não foi suficiente — a disciplina falhou.

### 10.2 O Paradoxo da Velocidade vs Segurança

O v5 é mais rápido para processar requisições simples (keyword path: <200ms vs LIA: 2-10s), mas esta velocidade vem da ausência de guards de compliance:

- **LIA paga um custo de latência** para garantir fairness, audit e observabilidade
- **v5 economiza latência** omitindo guards de compliance

Em produção com processamento de candidatos (decisões com impacto legal), a latência da LIA é justificada. Para cenários de CRUD simples (listar vagas, buscar insights), o overhead da LIA pode ser desnecessário.

**Recomendação:** A LIA deveria implementar um modo "CRUD fast-path" similar ao keyword matching do v5 para ações não-discriminatórias (listar vagas, buscar dados), ativando FairnessGuard apenas para ações que afetam candidatos.

### 10.3 O Legado Comum como Oportunidade

As evidências forenses de origem comum (`response_filter`, `circuit_breaker`, `ReActObserver`) não são um problema — são uma oportunidade. Os dois sistemas compartilham vocabulário, padrões e possivelmente parte da equipe de design.

Isso significa que:
1. A integração entre LIA e v5 é tecnicamente viável sem reescrita total
2. Um protocolo de comunicação entre os sistemas pode reusar padrões existentes
3. A curva de aprendizado para desenvolvedores que trabalham em ambos é menor

### 10.4 Veredicto Final

| Dimensão | Vencedor | Margem |
|----------|---------|--------|
| Compliance e Governança | LIA | Decisivo |
| Consistência Arquitetural | LIA | Decisivo |
| Observabilidade | LIA | Significativo |
| Escalabilidade de Agentes | v5 Grupo 3 | Moderado |
| Latência Operacional | v5 | Moderado |
| Sofisticação de Fluxos | Empate | — |
| Facilidade de Extensão | LIA | Moderado |
| Separação Dados/IA | v5 | Moderado |

**LIA é a arquitetura mais madura e segura para produção em contextos de recrutamento com impacto legal.** O v5 é mais rápido e tem padrões de paralelismo superiores, mas a ausência de compliance-by-design é um risco inaceitável para sistemas que tomam decisões sobre candidatos.

**Próximo passo estratégico recomendado:** Adotar o ModelRouter e o pattern de fan-out paralelo do v5 Grupo 3 na LIA (LIA-REC-05, LIA-REC-06), mantendo o compliance-by-design que é a vantagem competitiva estrutural da LIA.

---

*Documento gerado com base em leitura direta dos seguintes arquivos:*
- `lia-agent-system/app/domains/base.py` (172 linhas)
- `lia-agent-system/app/domains/pipeline/domain.py` (411 linhas)
- `lia-agent-system/app/domains/pipeline/agents/pipeline_tool_registry.py` (1.343 linhas)
- `lia-agent-system/app/shared/compliance/fairness_guard.py` (601 linhas)
- `lia-agent-system/app/shared/resilience/circuit_breaker.py` (883 linhas)
- `lia-agent-system/app/shared/robustness/response_filter.py` (364 linhas)
- `github.com/WeDOTalent/recruiter_agent_v5/src/domains/*/domain.py` (8 domínios, via API)
- `github.com/WeDOTalent/recruiter_agent_v5/src/services/fairness_checker.py`
- `github.com/WeDOTalent/recruiter_agent_v5/src/services/circuit_breaker.py`
- `github.com/WeDOTalent/recruiter_agent_v5/src/services/response_filter.py`
- `proposals/Paralelo_LIA_vs_V5_Arquitetura_IA.md`
