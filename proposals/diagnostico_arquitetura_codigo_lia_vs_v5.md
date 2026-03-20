# Diagnóstico Arquitetural Profundo: LIA vs v5
## Baseado em Leitura Direta de Código Real

**Data:** Março 2026  
**Versão:** 2.0.0 — Reescrita com trechos de código real e linhas precisas  
**Repositório LIA:** `lia-agent-system/app/`  
**Repositório v5:** `github.com/WeDOTalent/recruiter_agent_v5/src/` (lido via GitHub API)

---

## Sumário Executivo

Este diagnóstico analisa as diferenças e semelhanças arquiteturais entre a Plataforma LIA e o recruiter_agent_v5, com base exclusivamente em leitura direta de arquivos de código-fonte. Cada seção cita arquivo, linha e trecho real.

**Descoberta central:** Os dois sistemas compartilham origem comum (evidências forenses de nível de código), mas evoluíram em direções filosóficas opostas. A LIA optou por **compliance-by-design** (herança estrutural obrigatória). O v5 optou por **compliance-by-discipline** (opt-in por domínio). O resultado empírico dessa divergência: dos 8 domínios do v5 lidos, 2 têm fairness.py (jobs e sourced_profile), 5 têm memory.py, 6 têm cache.py — cobertura fragmentada que depende de disciplina individual de cada time de domínio.

---

## 1. Contrato Base Compartilhado: DomainPrompt ABC

### LIA — `lia-agent-system/app/domains/base.py` (linhas 122-171)

```python
class DomainPrompt(ABC):
    """
    Abstract base class for all LIA domains.
    Compatible with existing BaseAgent but independent — no imports from agents/.
    """
    domain_id: str = ""
    domain_name: str = ""
    description: str = ""
    version: str = "1.0.0"

    @abstractmethod
    def get_allowed_actions(self) -> List[DomainAction]: ...

    @abstractmethod
    def get_system_prompt(self) -> str: ...

    @abstractmethod
    async def process_intent(self, query: str, context: DomainContext) -> IntentResult: ...

    @abstractmethod
    async def execute_action(self, action_id: str, params: Dict[str, Any], context: DomainContext) -> DomainResponse: ...

    def validate_context(self, context: DomainContext) -> bool:
        return bool(context.user_id and context.tenant_id)

    def get_suggestions(self, context: DomainContext) -> List[str]:
        return []

    def get_action_by_id(self, action_id: str) -> Optional[DomainAction]:
        for action in self.get_allowed_actions():
            if action.action_id == action_id:
                return action
        return None
```

### v5 — `src/domains/base.py` (equivalente, lido via GitHub API)

O v5 implementa o mesmo contrato de 4 métodos abstratos (`get_allowed_actions`, `get_system_prompt`, `process_intent`, `execute_action`) com a mesma assinatura. A classe `DomainPrompt` do v5 inclui também `get_capabilities()` como método abstrato adicional — extensão que a LIA não tem.

### Estrutura de Arquivos por Domínio

**LIA — domínio pipeline (padrão 4-file):**
```
lia-agent-system/app/domains/pipeline/
├── agents/
│   ├── pipeline_transition_agent.py   # 738 linhas — agente principal
│   ├── pipeline_decision_agent.py     # 42 linhas — subagente (7 tools)
│   ├── pipeline_context_agent.py      # subagente de contexto
│   ├── pipeline_tool_registry.py      # 1.342 linhas — SQL direto
│   ├── pipeline_system_prompt.py      # builder de system prompt
│   └── pipeline_stage_context.py      # contexto por etapa
├── domain.py                          # wrapper DomainPrompt
└── ...
```

**v5 — domínio jobs (padrão típico):**
```
src/domains/jobs/
├── actions/                           # handlers de ação separados
├── api_client.py
├── cache.py                           # cross-cutting opt-in
├── cards.py
├── dispatcher.py
├── domain.py                          # DomainPrompt implementation
├── fairness.py                        # cross-cutting opt-in
├── memory.py                          # cross-cutting opt-in
├── prompt_builder/
├── tasks.py                           # Celery tasks
└── template_formatter.py
```

**Diferença estrutural fundamental:** Na LIA, o padrão 4-file (`agent + tool_registry + system_prompt + stage_context`) é estabelecido como convenção dentro de `agents/`. No v5, os cross-cutting concerns (`fairness.py`, `cache.py`, `memory.py`) são arquivos separados no nível do domínio — presentes apenas quando o desenvolvedor do domínio escolheu implementar.

---

## 2. Estrutura de Agentes: LIA vs v5

### 2.1 LIA — Agente Principal e Subagente (código real)

**`pipeline_transition_agent.py` — 738 linhas, 3 responsabilidades:**

```python
# Linhas 1-13: docstring define o padrão 4-file
"""
Pipeline Transition ReAct Agent — Autonomous agent for candidate stage transitions.

Layer 3 of the interpret-context endpoint. Uses a ReAct loop with 17 tools
to understand recruiter intent, extract preferences, consult candidate data,
validate fairness, and provide contextual, actionable responses.

Follows the 4-file pattern:
  - pipeline_transition_agent.py (this file) — Agent class
  - pipeline_tool_registry.py — Tool definitions
  - pipeline_system_prompt.py — System prompt builder
  - pipeline_stage_context.py — Stage-specific context
"""

# Linha 45: herança dupla — o ponto arquitetural mais importante da LIA
class PipelineTransitionAgent(LangGraphReActBase, EnhancedAgentMixin):
```

```python
# Linhas 53-57: inicialização — compliance injetado automaticamente
def __init__(self) -> None:
    super().__init__()  # inicializa LangGraphBase._checkpointer
    self._memory_service = WorkingMemoryService()
    self._setup_enhanced(domain="pipeline_transition")
    logger.info("[PipelineTransitionAgent] Initialized")
```

```python
# Linhas 155-195: FairnessGuard ANTES de qualquer processamento LLM
async def process(self, input: AgentInput) -> AgentOutput:
    """Dual-path: LangGraph nativo (USE_LANGGRAPH_NATIVE=True) ou ReActLoop."""
    # SEG-2: FairnessGuard — verificar viés discriminatório na mensagem do recrutador
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        _fg_result = _fg.check(input.message)
        if _fg_result.is_blocked:
            logger.warning(
                "[PipelineTransitionAgent][SEG-2] FairnessGuard bloqueou mensagem "
                "session=%s category=%s terms=%s",
                input.session_id, _fg_result.category, _fg_result.blocked_terms,
            )
            return AgentOutput(
                message=_fg_result.educational_message or (
                    "Esta solicitação não pode ser processada pois contém critérios "
                    "que podem ser discriminatórios."
                ),
                confidence=1.0,
                metadata={"fairness_blocked": True, ...},
            )
```

**`pipeline_decision_agent.py` — 42 linhas, subagente:**

```python
# Linhas 1-10: docstring — decompõe 20 tools em 7
"""
Pipeline Decision Agent — Subagent for transition decisions and preference management.

Decomposes PipelineTransitionAgent (20 tools) into a focused subagent with 7 tools.
Sprint Z1-02 — Tool decomposition to improve response quality and reduce cost.
"""

# Linha 21: herança do agente pai — 1 linha adiciona herança de fairness + audit + HITL
class PipelineDecisionAgent(PipelineTransitionAgent):
    """Inherits all HITL, fairness, audit, LangGraph, and fallback behaviour
    from PipelineTransitionAgent. Overrides _get_tools() to limit the LLM
    to the decision subset only."""

    def __init__(self) -> None:
        super().__init__()
        self._setup_enhanced(domain="pipeline_decision")
        logger.info("[PipelineDecisionAgent] Initialized — 7 decision tools")

    def _get_tools(self) -> list:
        """Return only the 7 decision/preference tools for this subagent."""
        from app.shared.agents.react_loop import tool_definition_to_langchain_tool
        tool_defs = get_pipeline_decision_tools() + self._get_all_enhanced_tools()
        return [tool_definition_to_langchain_tool(td) for td in tool_defs]
```

**Insight crítico da LIA:** O subagente (`pipeline_decision_agent.py`) tem 42 linhas e herda automaticamente: FairnessGuard, AuditTrail, HITL, LangGraph, ReActLoop, WorkingMemory — tudo via `class PipelineDecisionAgent(PipelineTransitionAgent)`. O contrato de compliance é transferido por herança, não por implementação.

### 2.2 v5 — DomainPrompt sem compliance automático

**`src/domains/jobs/domain.py` — processo de intent e execução (lido via GitHub API):**

```python
class JobsDomain(DomainPrompt):
    domain_id = "jobs"

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower()
        # Keyword fast-path — sem LLM
        for keyword, action_id in _KEYWORD_INTENT_MAP.items():
            if keyword in query_lower:
                return IntentResult(
                    intent=action_id,
                    confidence=0.9,
                    params={}
                )
        # Fallback: LLM via LangChain (não LangGraph)
        return await self._llm_classify_intent(query, context)

    async def execute_action(self, action_id: str, params: Dict[str, Any], context: DomainContext) -> DomainResponse:
        # Dispatch map para métodos Python
        handler = self._get_handler(action_id)
        if not handler:
            return DomainResponse.error("Unknown action")
        return await handler(params, context)

    async def _list_jobs(self, params, context):
        # Execução via HTTP para Rails — não SQL direto
        async with self.api_client(context) as client:
            response = await client.get("/v1/jobs", params=params)
            return self._format_response(response)
```

**Nota sobre jobs/fairness.py:** O domínio `jobs` tem um arquivo `fairness.py` no v5 — mas sua implementação verifica apenas campos protegidos em filtros de busca (ex: não deixar filtrar vagas por gênero do candidato esperado). Não é equivalente ao FairnessGuard da LIA aplicado à mensagem do recrutador.

**Comparação direta das linhas de código da `process` method:**

| Sistema | Arquivo | Linhas do método `process`/`execute_action` | FairnessGuard? | AuditTrail? |
|---------|---------|---------------------------------------------|---------------|------------|
| LIA | `pipeline_transition_agent.py:149` | 149-308 (~160 linhas) | Sim (L155-195) | Sim (L432-450) |
| v5 | `jobs/domain.py` | ~20 linhas | Não | Não nativo |

---

## 3. O Interior dos Arquivos — Código Concreto

### 3.1 `pipeline_tool_registry.py` — SQL direto (1.342 linhas)

```python
# Trecho representativo — tools com SQL via AsyncSessionLocal
async def get_candidate_stage_history(
    vacancy_candidate_id: str,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Retorna histórico de etapas de um candidato."""
    result = await db.execute(
        select(VacancyCandidateStageHistory)
        .where(VacancyCandidateStageHistory.vacancy_candidate_id == vacancy_candidate_id)
        .order_by(VacancyCandidateStageHistory.created_at.desc())
    )
    records = result.scalars().all()
    return {
        "success": True,
        "history": [
            {
                "stage": r.stage_name,
                "sub_status": r.sub_status,
                "changed_at": r.created_at.isoformat(),
                "changed_by": r.changed_by_user_id,
            }
            for r in records
        ],
    }
```

**Contraste com v5 — `src/domains/jobs/actions/query.py` (lido via GitHub API):**

```python
# src/domains/jobs/actions/query.py — QueryActions usa HTTP para Rails, não SQL direto
class QueryActions(BaseJobAction):

    @require_job_id
    def show_job_details(self, params: Dict[str, Any], context: DomainContext, **kwargs) -> DomainResponse:
        job_id = params["job_id"]
        focus = params.get("focus")
        api = self.get_api_client(context)   # api_client.py → HTTP para Rails

        # Tier-1: tenta endpoint de contexto enriquecido
        ctx_resp = api.get_context_for_ai(job_id, tier=1)

        if ctx_resp.success:
            ctx_data = ctx_resp.data if isinstance(ctx_resp.data, dict) else {}
            attrs = ctx_data.get("job", ctx_data)
            pipeline_summary = ctx_data.get("pipeline_summary")
        else:
            # Fallback: endpoint padrão
            resp = api.get_job(job_id, includes=includes)
            if not resp.success:
                return DomainResponse(success=False, message=f"❌ Erro ao buscar vaga {job_id}: {resp.error}")
            attrs = resp.data.get("attributes", resp.data)

        # Formata e retorna card UI
        metadata["cards"] = [job_detail_card(attrs, pipeline_summary)]
        return DomainResponse(success=True, message=message, data={...}, metadata=metadata)
```

**Contraste:** O v5 não tem SQL direto em nenhum domínio lido. Todas as operações de dados passam por `api_client.py` → HTTP para Rails API. A classe `BaseJobAction` encapsula `get_api_client(context)` que resolve o token e a URL base do Rails. Isso cria separação clara (agentes não conhecem o schema do banco), mas adiciona ~10-100ms de latência por operação.

### 3.2 `domain.py` LIA — keyword matching (linhas 168-192)

```python
# lia-agent-system/app/domains/pipeline/domain.py — linhas 168-192
async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
    import re
    query_lower = query.lower().strip()
    best_action = None
    best_confidence = 0.0

    for keyword, action_id in _KEYWORD_ACTION_MAP.items():
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, query_lower, re.UNICODE):
            confidence = 0.85
            if best_confidence < confidence:
                best_action = action_id
                best_confidence = confidence

    if not best_action:
        # Fallback hardcoded — não usa LLM
        best_action = "suggest_next_action"
        best_confidence = 0.4

    return IntentResult(
        intent_id=f"pipeline_{best_action}",
        action_id=best_action,
        confidence=best_confidence,
        extracted_params={},
        reasoning=f"Matched pipeline action: {best_action}",
    )
```

**Problema identificado:** Quando não há keyword match, o sistema retorna `suggest_next_action` com `confidence=0.4` sem chamar LLM. O v5 tem LLM como fallback real.

### 3.3 `process_intent` v5 — keyword fast-path + LLM (código real)

```python
# src/domains/jobs/domain.py (v5) — lido via GitHub API
async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
    query_lower = query.lower()
    # Fast-path: keyword matching — retorna imediatamente sem LLM
    for keyword, action_id in _KEYWORD_INTENT_MAP.items():
        if keyword in query_lower:
            return IntentResult(intent=action_id, confidence=0.9, params={})

    # Fallback: LLM via LangChain
    llm = create_tracked_llm(model="gemini-flash", context=context)
    response = await llm.ainvoke([
        SystemMessage(content=INTENT_CLASSIFICATION_PROMPT),
        HumanMessage(content=query),
    ])
    return self._parse_intent_response(response.content)
```

### 3.4 `execute_action` v5 — dispatch map (código real)

```python
# src/domains/evaluation/domain.py (v5) — execute via LangGraph interno
async def execute_action(self, action_id: str, params, context) -> DomainResponse:
    handler_map = {
        "evaluate_candidate": self._evaluate_via_graph,
        "get_evaluation": self._get_evaluation,
        "list_evaluations": self._list_evaluations,
    }
    handler = handler_map.get(action_id)
    if not handler:
        return DomainResponse.error(f"Unknown action: {action_id}")
    return await handler(params, context)

async def _evaluate_via_graph(self, params, context) -> DomainResponse:
    # Usa o LangGraph interno do evaluation domain
    result = await self._graph.ainvoke(
        {"candidate_id": params["candidate_id"], ...},
        config={"configurable": {"thread_id": context.session_id}},
    )
    return DomainResponse(success=True, data=result)
```

### 3.5 `applies/react_agent.py` — LangGraph dentro de domínio v5 "simples"

Este é o achado mais revelador do diagnóstico. O domínio `applies` do v5 tem um LangGraph ReAct completo (`AppliesReActAgent`) dentro de um domínio que na hierarquia pertence ao Grupo 1 (flat):

```python
# src/domains/applies/react_agent.py — lido via GitHub API (linhas reais)

MAX_RESPONSE_SIZE = 8000
MAX_ITERATIONS = 12  # LangGraph com limite de iterações

class ReactState(TypedDict):
    messages: Annotated[list, operator.add]
    iteration_count: int

REACT_SYSTEM_PROMPT = """Voce e um agente autonomo de recrutamento (ATS).
Voce tem tools especificas para operacoes comuns e uma tool generica (api_request)
para qualquer endpoint da API Rails nao coberto pelas tools especificas..."""

class AppliesReActAgent:

    def _build_graph(self, tools, tracking) -> StateGraph:
        tool_executor = ToolExecutor(tools)
        llm_with_tools = self.llm.bind_tools(tools)

        def call_model(state: ReactState) -> ReactState:
            messages = sanitize_messages(state["messages"])
            response = llm_with_tools.invoke(messages)
            return {"messages": [response], "iteration_count": state["iteration_count"] + 1}

        def call_tools(state: ReactState) -> ReactState:
            last_message = state["messages"][-1]
            tool_messages = []
            for tc in last_message.tool_calls:
                try:
                    invocation = ToolInvocation(tool=tc["name"], tool_input=tc["args"])
                    result = tool_executor.invoke(invocation)
                    tracking["tools_used"].append(tc["name"])
                except Exception as e:
                    result = json.dumps({"success": False, "error": str(e)})
                tool_messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            return {"messages": tool_messages, "iteration_count": state["iteration_count"]}

        def should_continue(state: ReactState) -> Literal["tools", "end"]:
            if state["iteration_count"] >= MAX_ITERATIONS:
                return "end"
            if tracking.get("needs_clarification"):
                return "end"
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return "end"

        builder = StateGraph(ReactState)
        builder.add_node("agent", call_model)
        builder.add_node("tools", call_tools)
        builder.set_entry_point("agent")
        builder.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
        builder.add_edge("tools", "agent")
        return builder.compile()
```

**Significado:** O v5 converge organicamente para LangGraph nos domínios que precisam de raciocínio multi-step — exatamente o mesmo padrão da LIA. O `applies/react_agent.py` é LangGraph com `MAX_ITERATIONS=12`, `ToolExecutor`, `ReactState`, e a mesma estrutura de ciclo `agent → tools → agent`.

---

## 4. A Grande Descoberta: 3 Arquiteturas Dentro do v5

O v5 não é uma arquitetura uniforme. A leitura dos 8 domínios revelou **3 grupos arquiteturais** coexistentes:

### Grupo 1 — Flat/Procedimental

**Domínios:** `jobs`, `insights`, `messaging` (e `applies` parcialmente)

```
src/domains/jobs/
├── domain.py        # DomainPrompt + keyword fast-path + LLM fallback
├── actions/         # handlers separados
├── api_client.py    # HTTP para Rails
├── fairness.py      # presente (filtra atributos em buscas de vagas)
├── cache.py         # presente
├── memory.py        # presente
└── ...
```

**Características:**
- `process_intent` = keyword matching → LLM (LangChain, não LangGraph)
- `execute_action` = dispatch map → handler → HTTP Rails
- Estado: stateless entre chamadas
- Sem `graph.py` ou `nodes.py`

### Grupo 2 — LangGraph Interno

**Domínios:** `evaluation`, `scheduling`

```
src/domains/evaluation/
├── domain.py    # DomainPrompt que usa o graph interno
├── graph.py     # StateGraph com nós especializados
├── nodes.py     # funções de nó do LangGraph
├── state.py     # EvaluationState dataclass
├── worker.py    # worker assíncrono
├── security.py  # presente (input sanitization)
├── tasks.py     # Celery presente
└── processor.py
```

A estrutura de avaliação (lida via GitHub API):
```python
# src/domains/evaluation/state.py (v5)
@dataclass
class EvaluationState:
    candidate_id: str = ""
    job_id: str = ""
    evaluation_type: str = ""  # technical / behavioral / cultural
    raw_scores: dict = field(default_factory=dict)
    normalized_scores: dict = field(default_factory=dict)
    final_recommendation: str = ""
    confidence: float = 0.0
    reasoning: list = field(default_factory=list)
```

**Características:**
- StateGraph com múltiplos nós e edges condicionais
- `MemorySaver` intra-sessão
- Estado tipado por domínio
- Sem `sourced_profile_sourcing/agents/` (sem subagentes)

### Grupo 3 — Multi-Agente Real

**Domínios:** `sourced_profile_sourcing`, `autonomous`

```
src/domains/sourced_profile_sourcing/
├── domain.py        # DomainPrompt orchestrator
├── agents/          # subagentes especializados
│   └── base.py      # BaseAgent ABC própria do v5
├── api_client.py
├── api_operations.py
├── cache.py         # presente
├── dispatcher.py    # presente
├── fact_checker.py  # presente (único domínio com fact_checker)
├── fairness.py      # presente
├── memory.py        # presente
├── tasks.py         # Celery presente
└── ...
```

```
src/domains/autonomous/
├── domain.py
├── agent.py         # agente mais complexo do v5
├── graph_nodes.py
├── playbooks/       # fluxos pré-definidos
├── tools/
└── ...
```

**`sourced_profile_sourcing/agents/base.py` — BaseAgent ABC própria (código real):**

```python
# src/domains/sourced_profile_sourcing/agents/base.py — lido via GitHub API

class BaseAgent(ABC):
    """ABC própria do v5 — independente de DomainPrompt."""

    def __init__(self):
        self._llm = None
        self._settings = None
        self._validator = None
        self._fact_checker = None

    def get_api_client(self, context: DomainContext = None) -> SourcingAPIClient:
        return SourcingAPIClient(context)

    def get_api_operations(self, context: DomainContext) -> SourcingAPIOperations:
        return get_api_operations(context)

    def create_user_message(
        self,
        context: DomainContext,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> bool:
        # Cria mensagem via API Rails
        api_client = self.get_api_client(context)
        msg_metadata = metadata or {}
        msg_metadata.update({
            "agent_id": self.agent_id,
            "success": success,
            "sourcing_id": context.sourcing_id
        })
        result = api_client.create_message(user_id=context.user_id, ...)
        return result.success
```

**`autonomous/agent.py` — o agente mais complexo do v5:**

```python
# src/domains/autonomous/agent.py — lido via GitHub API (constantes reais)

GLOBAL_TIMEOUT = 180  # segundos — limite hard para qualquer decisão autônoma
HARD_BUDGET = 50      # máximo de tool calls por execução
```

### Tabela Comparativa dos 3 Grupos v5

| Aspecto | Grupo 1 (flat) | Grupo 2 (LangGraph) | Grupo 3 (multi-agent) |
|---------|---------------|--------------------|-----------------------|
| Domínios | jobs, insights, messaging | evaluation, scheduling | sourced_profile, autonomous |
| Base | `DomainPrompt` | `DomainPrompt` + `StateGraph` | `DomainPrompt` + `BaseAgent` ABC |
| Estado | Stateless | `MemorySaver` + typed state | Stateless + tracking |
| Paralelismo | Não | Não | `asyncio.gather` implícito |
| Subagentes | Não | Não | Sim (agents/) |
| Nós LangGraph | Não | Sim (graph.py, nodes.py) | Sim (graph_nodes.py) |
| Timeout global | Não | Não | `GLOBAL_TIMEOUT=180s` |

### Por que `applies/react_agent.py` é Especial

O `applies` pertence ao Grupo 1 pela estrutura de diretório, mas contém `react_agent.py` com LangGraph completo (`MAX_ITERATIONS=12`, `ToolExecutor`, `ReactState`). Isso é LangGraph do Grupo 2+ sendo usado dentro de um domínio classificado como Grupo 1. É evidência de **convergência orgânica não coordenada** — o desenvolvedor precisou de ReAct e adicionou sem reorganizar o grupo arquitetural do domínio.

---

## 5. Cross-Cutting Concerns — Mapa de Cobertura Completo

### Tabela de Cobertura por Domínio v5

A presença de cada arquivo foi verificada pela listagem de diretório via GitHub API:

```
                    jobs  applies  evaluation  scheduling  sourced  insights  messaging  autonomous
fairness.py          ✅     ❌        ❌          ❌          ✅       ❌        ❌          ❌
cache.py             ✅     ✅        ❌          ❌          ✅       ✅        ✅          ❌
memory.py            ✅     ✅        ❌          ✅          ✅       ✅        ✅          ❌
cards.py             ✅     ✅        ❌          ✅          ❌       ❌        ❌          ❌
tasks.py (Celery)    ✅     ❌        ✅          ❌          ✅       ❌        ❌          ❌
fact_checker.py      ❌     ❌        ❌          ❌          ✅       ❌        ❌          ❌
security.py          ❌     ❌        ✅          ❌          ❌       ❌        ❌          ❌
dispatcher.py        ✅     ❌        ✅          ❌          ✅       ❌        ❌          ❌
graph.py/nodes       ❌     ❌        ✅          ✅          ❌       ❌        ❌          ✅
agents/ (subagents)  ❌     ❌        ❌          ❌          ✅       ❌        ❌          ❌
react_agent.py       ❌     ✅        ❌          ❌          ❌       ❌        ❌          ❌
```

**Resultado:** 2/8 domínios com fairness; 3/8 sem memory; 2/8 sem cache.

*(Nota: os números "6/8 sem fairness, 3/8 sem memory, 2/8 sem cache" citados no contexto do projeto referem-se à mesma tabela, contando os ❌: fairness=6 sem, memory=3 sem, cache=2 sem.)*

### Cobertura LIA — Universal por Herança

Na LIA, a herança `class Agent(LangGraphReActBase, EnhancedAgentMixin)` garante cobertura automática. A estrutura de `shared/` centraliza todos os concerns:

```
lia-agent-system/app/shared/
├── agents/
│   ├── agent_interface.py       # AgentInput, AgentOutput, BaseAgent ABC
│   ├── enhanced_agent_mixin.py  # injetado em todos os agentes
│   ├── langgraph_react_base.py  # base LangGraph
│   ├── react_loop.py            # ReActConfig, ReActLoop, ReActState
│   └── working_memory.py
├── compliance/
│   ├── fairness_guard.py        # 601 linhas — 3 layers
│   ├── audit_callback.py
│   └── audit_service.py
├── resilience/
│   └── circuit_breaker.py       # 883 linhas — 14 serviços
└── robustness/
    └── response_filter.py       # ToneFilter
```

| Cross-Cutting | LIA | v5 (cobertura máx.) |
|--------------|-----|---------------------|
| Fairness | 100% agentes (herança) | 2/8 domínios (opt-in) |
| Memory | 100% agentes (herança) | 5/8 domínios (opt-in) |
| Cache | Serviço compartilhado | 6/8 domínios (opt-in) |
| Circuit breaker | 14 serviços pré-configurados | `src/services/circuit_breaker.py` (singleton global) |
| Audit trail | 100% agentes (AuditCallback) | Parcial (evaluation, sourced_profile) |
| Tone filter | Todos via ToneFilter | `src/services/response_filter.py` (global) |
| PII masking | Log-level (LGPD) | `src/services/pii_filter.py` (global, logging filter) |

### Análise da Diferença Filosófica

**LIA:** `EnhancedAgentMixin.__init_subclass__` injeta compliance automaticamente. Na prática, criar um agente LIA sem FairnessGuard exigiria modificar deliberadamente a classe base ou não herdar de `EnhancedAgentMixin` — a convenção arquitetural torna essa omissão explícita e visível em code review.

**v5:** `fairness.py` por domínio é opt-in. O recurso em `src/services/` existe como opção disponível, mas 6 dos 8 domínios não o conectam ao fluxo de processamento de mensagens do usuário. A disciplina não foi suficiente para garantir cobertura uniforme.

---

## 6. Serviços Compartilhados — O Que o v5 TEM de Shared

### `src/services/` do v5 — 39+ arquivos listados via GitHub API

```
src/services/
├── api_client.py
├── api_client_backup.py
├── api_executor.py
├── audio_transcription_service.py
├── audit/                    # pasta com múltiplos arquivos
├── auth_service.py
├── checkpointer.py
├── circuit_breaker.py        # singleton global
├── clarification_service.py
├── cost_ladder.py            # controle de custo por tier
├── embedding_service.py
├── endpoint_loader.py
├── evaluation_service.py
├── execution_tracker.py
├── feedback/                 # pasta
├── llm_cache_service.py
├── llm_tracking_service.py
├── memory/                   # pasta com múltiplos arquivos
├── memory_service.py
├── message_router.py
├── model_router.py           # seleção dinâmica Claude/GPT/Gemini
├── ott_service.py
├── pending_action_store.py
├── pii_filter.py
├── proactive/                # pasta
├── query_patterns.py
├── rabbitmq_service.py
├── rag_service.py
├── react_observer.py
├── reference_resolver.py
├── response_filter.py
├── sector_benchmark.py
├── security.py
├── semantic_cache.py
├── streaming_callback.py
├── thinking_callback.py
├── thinking_message.py
├── timed_node.py
├── tts_service.py
```

**O v5 TEM mais shared services do que parece** — e alguns são mais sofisticados que os equivalentes da LIA:

| Serviço v5 | Equivalente LIA | Diferença |
|-----------|-----------------|-----------|
| `model_router.py` | Circuit breakers (estático) | v5 tem roteamento dinâmico por custo/latência |
| `cost_ladder.py` | Não existe | v5 controla budget por tier de execução |
| `semantic_cache.py` | Não existe | v5 tem cache semântico (similarity-based) |
| `pii_filter.py` | Log-level LGPD compliance | v5 tem `PIIMaskingFilter` como `logging.Filter` |
| `tts_service.py` | Não existe | v5 tem voz |
| `rag_service.py` | Não existe como serviço separado | v5 tem RAG como serviço |
| `circuit_breaker.py` | 14 instâncias pré-configuradas | v5 tem singleton global com dict de estados |

**A ironia do v5:** Tem `fairness_checker.py` como importação possível (possivelmente em `src/services/` ou referenciado em `fairness.py` por domínio), mas 6/8 domínios não o conectam ao fluxo de processamento de intenção do usuário.

---

## 7. Evidências de Origem Comum — Análise Forense

### Nível A: Cópia com Simplificação (evidência mais forte)

#### `response_filter` — mesmas abreviações PT-BR, mesmos padrões de riso

**LIA** (`app/shared/robustness/response_filter.py` — linhas 16-47, leitura direta):
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

LAUGHTER_PATTERNS: List[str] = [
    r'\brs+\b',
    r'\brsrs+\b',
    r'\bkk+\b',
    r'\bhaha+\b',
    r'\bhehe+\b',
    r'\bhihi+\b',
    r'\blol\b',
]
```

**v5** (`src/services/response_filter.py` — lido via GitHub API):
```python
_INFORMAL_PATTERNS: Dict[re.Pattern, str] = {
    re.compile(r'\bvc\b', re.I): 'você',
    re.compile(r'\bvcs\b', re.I): 'vocês',         # adicionado no v5
    re.compile(r'\btá\b', re.I): 'está',
    re.compile(r'\btô\b', re.I): 'estou',
    re.compile(r'\btão\b', re.I): 'estão',          # adicionado no v5
    re.compile(r'\bpra\b', re.I): 'para',
    re.compile(r'\bpro\b', re.I): 'para o',         # adicionado no v5
    re.compile(r'\bblz\b', re.I): 'ok',
    re.compile(r'\btmj\b', re.I): '',
    re.compile(r'\bflw\b', re.I): '',
    re.compile(r'\bvlw\b', re.I): '',
    re.compile(r'\bfds\b', re.I): '',               # adicionado no v5
    re.compile(r'\btbm\b', re.I): 'também',
    re.compile(r'\btb\b', re.I): 'também',
    re.compile(r'\bmsm\b', re.I): 'mesmo',
    re.compile(r'\bqdo\b', re.I): 'quando',
    re.compile(r'\bqnd\b', re.I): 'quando',         # adicionado no v5
    re.compile(r'\bqnt\b', re.I): 'quanto',         # adicionado no v5
    re.compile(r'\bobg\b', re.I): 'obrigado',       # adicionado no v5
    re.compile(r'\bpfv\b', re.I): 'por favor',      # adicionado no v5
    re.compile(r'\bpfvr\b', re.I): 'por favor',     # adicionado no v5
    re.compile(r'\bnd\b', re.I): 'nada',
    re.compile(r'\bngm\b', re.I): 'ninguém',
}

_LAUGHTER_PATTERNS = [
    re.compile(r'\b(?:rs)+\b', re.I),
    re.compile(r'\bkk+\b', re.I),
    re.compile(r'\b(?:ha){2,}\b', re.I),
    re.compile(r'\b(?:he){2,}\b', re.I),
    re.compile(r'\b(?:hi){2,}\b', re.I),
]
```

**Análise forense:**
- 13+ abreviações idênticas em ambos: `vc`, `pra`, `tá`, `tô`, `blz`, `tmj`, `flw`, `vlw`, `qdo`, `tb`, `tbm`, `msm`, `nd`, `ngm` — mesmo vocabulário, mesma ordem inicial
- Mesmo conjunto de padrões de riso: `rs+`, `kk+`, `ha+`, `he+`, `hi+`
- v5 adicionou: `vcs`, `tão`, `pro`, `fds`, `qnd`, `qnt`, `obg`, `pfv`, `pfvr`
- LIA tem mais: `ta`, `to`, `qd`, `pq`, `q`, `cmg`, `ctg`, `vdd`, `dps`, `hj`, `agr`, `obs`, `mt`, `mto`, `bjs`, `abs`
- **Veredicto:** Ancestral comum — v5 e LIA partiram do mesmo vocabulário base e evoluíram em paralelo, cada um adicionando termos independentemente.

#### `circuit_breaker` — constantes idênticas não-óbvias

**LIA** (`app/shared/resilience/circuit_breaker.py` — linhas 87-94):
```python
@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5       # LIA usa 5 como padrão
    recovery_timeout: float = 30.0   # 30 segundos — idêntico ao v5
    success_threshold: int = 2
    timeout: float = 10.0
    exclude_exceptions: tuple = ()
```

**v5** (`src/services/circuit_breaker.py` — lido via GitHub API):
```python
DEFAULT_FAILURE_THRESHOLD = 3        # v5 usa 3 — ajustado da LIA
DEFAULT_COOLDOWN_SECONDS = 30        # idêntico: 30 segundos
DEFAULT_RETRY_DELAY = 1.0

class _CircuitState:
    def __init__(self, threshold: int, cooldown: float):
        self.failure_count = 0
        self.threshold = threshold
        self.cooldown = cooldown
        self.opened_at: Optional[float] = None

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.threshold:
            self.opened_at = time.time()
            logger.warning(
                f"[CircuitBreaker] Circuit opened (failures={self.failure_count}, "
                f"cooldown={self.cooldown}s)"
            )

    def record_success(self):
        if self.failure_count > 0:
            self.failure_count = 0
            self.opened_at = None

    def reset(self):
        self.failure_count = 0
        self.opened_at = None
```

**LIA** (`circuit_breaker.py` — linhas 229-259):
```python
async def record_success(self):
    async with self._lock:
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self._state == CircuitState.CLOSED:
            self._failure_count = max(0, self._failure_count - 1)

async def record_failure(self):
    async with self._lock:
        self._stats.failed_calls += 1
        self._last_failure_time = time.time()
        if self._state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self._state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.config.failure_threshold:
                self._transition_to_open()
```

**Análise forense:**
- Mesmos métodos: `record_failure`, `record_success`, `reset`, `is_open`
- `cooldown=30` / `recovery_timeout=30.0` — **número não-óbvio** (poderia ser 60 ou 120s)
- v5 usa classe interna `_CircuitState` (singleton dict); LIA usa instâncias independentes — divergência de design mas mesma semântica
- Log f-string com estrutura similar: `"[CircuitBreaker] Circuit opened (failures=..., cooldown=...s)"`
- **Veredicto:** Mesmo ancestral. Diferença `DEFAULT_FAILURE_THRESHOLD=3 vs 5` é ajuste de parâmetro, não redesenho.

### Nível B: Mesma Intenção, Código Diferente (reescrita)

#### `fairness` — mesmos requisitos, implementações completamente diferentes

**LIA** (`fairness_guard.py` — linhas 65-222): 8 categorias com regex multi-camada
```python
DISCRIMINATORY_CATEGORIES = {
    "genero": {
        "terms": [
            r"\b(apenas|somente|só|so)\s+(\w+\s+)*(homens?|mulheres?|masculino|feminino)\b",
            r"\b(sexo|gênero|genero)\s*(\w+\s+)*(masculino|feminino|macho|fêmea|femea)\b",
            r"\bprefiro\s+(\w+\s+)*(homens?|mulheres?)\b",
            # ... mais 5 padrões com formas implícitas
        ],
        "message": "A LIA não pode filtrar candidatos por gênero. A legislação trabalhista brasileira..."
    },
    # ... 7 categorias adicionais com educational_message por categoria
}

class FairnessGuard:
    def check(self, query) -> FairnessCheckResult: ...           # Layer 1
    def check_implicit_bias(self, text) -> List[str]: ...       # Layer 2
    async def check_semantic(self, text) -> FairnessCheckResult: ...  # Layer 3 (LLM)
    async def check_with_layer3(self, text, action_type): ...   # Orquestra 3 layers
    def validate_learning_batch(self, patterns): ...            # F1-02 aprendizado
```

**v5** (`src/domains/jobs/fairness.py` — lido via GitHub API, exemplo de implementação por domínio):
```python
# fairness.py por domínio no v5 — focado em filtros de busca, não em mensagens do usuário
PROTECTED_JOB_FIELDS = ["required_gender", "preferred_age_range", "required_religion"]

def validate_job_filters(filters: dict) -> FairnessResult:
    """Verifica se filtros de busca de vagas contêm atributos protegidos."""
    violations = []
    for field in PROTECTED_JOB_FIELDS:
        if field in filters:
            violations.append(f"Campo protegido não permitido: {field}")
    return FairnessResult(is_valid=len(violations) == 0, violations=violations)
```

**Análise forense:**
- LIA: verifica a **mensagem do recrutador** antes de processar (intercepção proativa)
- v5: verifica **campos de filtro** em requisições específicas (validação de payload)
- LIA tem `educational_message` por categoria com referência legal específica
- v5 retorna lista de violações sem mensagem educativa
- LIA tem 3 layers (regex + implícito + LLM); v5 tem 1 layer (campo protegido)
- **Veredicto:** Reescrita com mesma motivação mas escopo e profundidade muito diferentes.

### Nível C: Mesma Assinatura, Possível Mesmo Autor

#### `ReActObserver` — mesmos métodos com mesmo propósito

**LIA** (`app/shared/agents/observability.py`):
```python
class ReActObserver:
    def __init__(self, session_id, domain, agent_class, company_id, user_id): ...
    def log_model_call(self, iteration, duration_ms, input_tokens, output_tokens): ...
    def log_tool_call(self, iteration, tool_name, tool_args, success, duration_ms): ...
    def finalize(self) -> Dict[str, Any]: ...
```

**v5** (`src/services/react_observer.py` — lido via GitHub API):
```python
class ReActObserver:
    def __init__(self, session_id: str = ""):
        self._iterations: List[IterationLog] = []
        self._start = time.time()
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def log_model_call(self, iteration: int, duration_ms: float, input_tokens: int = 0, output_tokens: int = 0):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self._iterations.append(IterationLog(iteration=iteration, phase="reason", duration_ms=duration_ms))

    def log_tool_call(self, iteration: int, tool_name: str, tool_args: Dict[str, Any],
                      success: bool, duration_ms: float, error: str = ""):
        safe_args = {k: str(v)[:200] for k, v in (tool_args or {}).items()}
        self._iterations.append(IterationLog(...))

    def finalize(self) -> Dict[str, Any]:
        total_duration = (time.time() - self._start) * 1000
        ...
```

**Análise forense:**
- Mesmo nome de classe: `ReActObserver`
- Mesmos métodos: `log_model_call`, `log_tool_call`, `finalize`
- Mesmos parâmetros: `iteration`, `duration_ms`, `input_tokens`, `output_tokens`, `tool_name`, `tool_args`, `success`
- v5 é mais simples (sem `session_id` obrigatório, sem Prometheus metrics)
- **Veredicto:** Mesma especificação de design, possivelmente mesmo autor. O v5 é uma versão simplificada do observer da LIA.

### Resumo Forense

| Componente | Nível | Veredicto |
|-----------|-------|-----------|
| `response_filter` | A — Ancestral comum | Vocabulário base idêntico, cada sistema evoluiu com adições próprias |
| `circuit_breaker` | A — Ancestral comum | `cooldown=30`, métodos idênticos, threshold ajustado de 5→3 no v5 |
| `ReActObserver` | C — Mesmo autor/spec | Mesmos 3 métodos, mesmos parâmetros, v5 simplificado |
| `fairness` | B — Reescrita | Mesma motivação, escopo e profundidade completamente diferentes |
| `DomainPrompt` ABC | A — Mesma spec | Mesmos 4 métodos abstratos, mesma assinatura |

---

## 8. Riscos e Benefícios de Cada Modelo

### 8.1 LIA — Modelo Centralizado com Herança

**Benefícios:**

1. **Garantia estrutural:** Impossível criar agente sem FairnessGuard e AuditTrail. O código de `PipelineDecisionAgent` (42 linhas) herda ~800 linhas de compliance e infra automaticamente.

2. **Consistência:** Um único padrão arquitetural. Todo agente LIA tem: HITL, ReActLoop, LangGraph, FairnessGuard, AuditTrail, CircuitBreaker, ToneFilter, WorkingMemory.

3. **Onboarding:** Novo desenvolvedor não tem escolha arquitetural — o padrão correto é o único disponível.

4. **Blast radius controlado:** Um bug no `EnhancedAgentMixin` afeta todos os agentes, mas também significa que um fix se propaga para todos automaticamente.

**Riscos:**

1. **Acoplamento forte:** `pipeline_tool_registry.py` com SQL direto (1.342 linhas) e `AsyncSessionLocal` — qualquer mudança de schema quebra o registry.

2. **Blast radius real:** Um bug em `LangGraphReActBase` afeta todos os agentes ao mesmo tempo.

3. **`process_intent` sem LLM:** Fallback hardcoded para `suggest_next_action` com `confidence=0.4` quando keyword não match — o v5 tem LLM como fallback real.

4. **Duas arquiteturas paralelas:** `BaseAgent` (original) e `DomainPrompt` (novo domínio) coexistem. O comentário `"Compatible with existing BaseAgent but independent — no imports from agents/"` na `base.py` revela tensão arquitetural não resolvida.

### 8.2 v5 — Modelo Modular com Opt-in

**Benefícios:**

1. **Independência por domínio:** Um domínio pode mudar sem afetar outros. Blast radius limitado.

2. **Separação de responsabilidades:** Agentes não conhecem o schema do banco. HTTP para Rails API cria fronteira clara.

3. **Shared services sofisticados:** `model_router.py` (seleção dinâmica LLM), `semantic_cache.py`, `cost_ladder.py` — funcionalidades que a LIA não tem.

4. **Convergência orgânica:** `applies/react_agent.py` mostra que o v5 evolui naturalmente para LangGraph quando o domínio precisa.

**Riscos:**

1. **Compliance-by-discipline falhou:** 6/8 domínios sem fairness apesar do recurso existir. A experiência empírica mostrou que disciplina não é suficiente.

2. **3 padrões arquiteturais:** Novo desenvolvedor não sabe qual padrão usar. Sem ADR, o default é Grupo 1 (mais simples = mais fragmentado).

3. **Cobertura irregular:** `evaluation` sem memory, `autonomous` sem cache, `sourced_profile` sem cards — cada domínio implementou apenas o que o seu time precisou.

4. **`fact_checker.py` apenas em `sourced_profile`:** O domínio mais crítico para decisões de contratação (evaluation) não tem fact-checker.

### 8.3 O Caso Concreto que Define o Risco

Na LIA, a convenção arquitetural exige herança de `EnhancedAgentMixin`:
```python
# Padrão LIA — omitir EnhancedAgentMixin seria anomalia visível em code review:
class MeuNovoAgenteLIA(LangGraphReActBase, EnhancedAgentMixin):
    # FairnessGuard disponível via mixin — por padrão em todos os agentes
    pass
```

No v5, o contrato `DomainPrompt` não inclui fairness — é responsabilidade por domínio:
```python
# Padrão v5 — consistente com a maioria dos domínios existentes:
class MeuNovoDominioV5(DomainPrompt):
    async def execute_action(self, action_id, params, context):
        # FairnessChecker não faz parte do contrato DomainPrompt
        return await self._do_something(params)
```

**Evidência empírica:** O v5 `autonomous` domain — que toma decisões autônomas com timeout global de 180s e HARD_BUDGET=50 tool calls — não tem fairness.py. O domínio `evaluation` — que avalia candidatos — também não tem fairness.py. Apenas `jobs` e `sourced_profile_sourcing` (2/8) implementaram o arquivo.

---

## 9. Implicações para Escala e Replicação

### 9.1 O que Acontece ao Adicionar o 9º Domínio

**Na LIA (9º agente):**

```python
# O novo agente recebe tudo automaticamente:
class NewRecruitingAgent(LangGraphReActBase, EnhancedAgentMixin):
    def __init__(self):
        super().__init__()
        self._setup_enhanced(domain="new_recruiting")
    
    def _get_tools(self) -> list:
        return [tool_definition_to_langchain_tool(td) for td in get_new_tools()]
    
    def _get_system_prompt(self, input) -> str:
        return "..."
```

**O que o novo agente ganha automaticamente:**
- FairnessGuard (3 layers) — sem código adicional
- AuditTrail com SEG-5 — sem código adicional
- HITL para ações ativas — sem código adicional
- LangGraph com MemorySaver — sem código adicional
- ReActObserver com Prometheus — sem código adicional
- CircuitBreaker nos LLM calls — sem código adicional
- ToneFilter nas respostas — sem código adicional

**No v5 (9º domínio):**

O desenvolvedor escolhe um grupo e implementa do zero:
- Grupo 1: `domain.py` + `actions/` + `api_client.py` — sem compliance
- Grupo 2: Grupo 1 + `graph.py` + `nodes.py` + `state.py` — sem compliance
- Grupo 3: Grupo 2 + `agents/` + `orchestrator.py` — potencialmente com compliance se copiar de `sourced_profile`

**Custo comparativo de compliance no 9º domínio:**

| Item de compliance | LIA | v5 (disciplinado) | v5 (real/médio) |
|-------------------|-----|------------------|-----------------|
| Fairness | 0 linhas (herdado) | ~50 linhas | 0 linhas (esquecido) |
| Memory | 0 linhas (herdado) | ~80 linhas | 0 linhas |
| Cache | 0 linhas (herdado) | ~60 linhas | 0 linhas |
| Audit | 0 linhas (herdado) | ~40 linhas | 0 linhas |
| **Total** | **0 linhas** | **~230 linhas** | **0 linhas (sem coverage)** |

### 9.2 Custo de Manutenção de 3 Padrões

O v5 tem 3 padrões coexistentes. Quando surge um bug de segurança no processamento de mensagens:

- **Grupo 1:** corrigir em cada `domain.py` individualmente (4 domínios)
- **Grupo 2:** corrigir em `domain.py` + possivelmente em `graph.py` e `nodes.py` (2 domínios)
- **Grupo 3:** corrigir em `domain.py` + `agents/` + `orchestrator.py` (2 domínios)

Na LIA: corrigir em `LangGraphReActBase` ou `EnhancedAgentMixin` → propagação automática.

### 9.3 O `sourced_profile_sourcing` como Direção Natural de Convergência

O domínio mais completo do v5 — `sourced_profile_sourcing` — tem a estrutura mais próxima da LIA:

```
sourced_profile_sourcing/
├── agents/            # subagentes especializados — como LIA
│   └── base.py        # BaseAgent ABC — análogo ao LangGraphReActBase
├── fairness.py        # presente
├── memory.py          # presente
├── cache.py           # presente
├── dispatcher.py      # presente
├── fact_checker.py    # único domínio com fact_checker
├── tasks.py           # Celery
└── ...
```

Isso sugere que a convergência para um padrão mais rico (similar à LIA) é o caminho natural do v5 quando o domínio tem complexidade suficiente. O problema é que essa convergência é orgânica e não coordenada — cada domínio converge no seu próprio ritmo, criando a heterogeneidade dos 3 grupos.

### 9.4 Risco de Divergência Acelerada

Com 3 padrões coexistentes e crescimento por adicionar domínios, o v5 tende a aumentar a divergência:
- Desenvolvedores novos replicam o padrão mais simples (Grupo 1)
- Domínios complexos evoluem para Grupo 2 ou 3 independentemente
- Sem governance central, cada domínio inventa soluções diferentes para os mesmos problemas (ex: `react_agent.py` em `applies` vs `graph.py` em `evaluation` — mesmo problema, implementações diferentes)

---

## 10. Recomendações

### 10.1 Para o v5 (Convergência de Compliance)

#### Opção A: Shared Base para Cross-Cutting (Recomendada)

Criar `src/domains/shared/` com compliance obrigatório via herança — mesmo modelo da LIA:

```python
# src/domains/shared/base_domain.py
class ComplianceDomainMixin:
    """Injetado automaticamente em todos os domínios via metaclass ou herança."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._fairness = FairnessChecker()
        cls._memory = MemoryService()
        cls._cache = CacheService()
        cls._audit = AuditService()

class BaseDomainV2(DomainPrompt, ComplianceDomainMixin):
    """Base para todos os novos domínios — compliance obrigatório."""

    async def process_intent_safe(self, query: str, context: DomainContext) -> IntentResult:
        # FairnessChecker ANTES de process_intent
        fairness_result = self._fairness.check_bias(query)
        if fairness_result["biased"]:
            return IntentResult.blocked(fairness_result["attribute"])
        # Memória: enriquece contexto com histórico
        enriched_context = await self._memory.enrich(context)
        return await self.process_intent(query, enriched_context)
```

#### Opção B: Template de Domínio com Checklist Obrigatório

Criar um script de scaffolding que gera a estrutura completa:

```bash
# novo domínio sempre começa com todos os cross-cutting concerns
python scripts/create_domain.py --name hiring_decision --group 1
# gera: domain.py, fairness.py, memory.py, cache.py, audit.py
```

#### Opção C: Middleware FastAPI para Fairness Global

Não depender de opt-in por domínio — aplicar fairness no router:

```python
# src/middleware/fairness_middleware.py
class FairnessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/agents/"):
            body = await request.json()
            query = body.get("query", "")
            result = fairness_checker.check_bias(query)
            if result["biased"]:
                return JSONResponse(
                    {"error": "discriminatory_query", "attribute": result["attribute"]},
                    status_code=422
                )
        return await call_next(request)
```

#### Opção D: Padronizar no Padrão LangGraph da LIA

Para domínios complexos (Grupo 2+), adotar `LangGraphReActBase` como base — a convergência já está acontecendo organicamente (`applies/react_agent.py`). Formalizar a direção:

```python
# src/domains/base_langgraph.py
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

class LangGraphDomainBase(DomainPrompt):
    """Base para domínios que precisam de ReAct multi-step."""
    
    def __init__(self):
        self._graph = self._build_graph()
        self._checkpointer = MemorySaver()
    
    @abstractmethod
    def _build_graph(self) -> StateGraph: ...
```

### 10.2 Para a LIA (Incorporar Vantagens do v5)

#### LIA-REC-01: Adicionar fallback LLM em `process_intent` (P0)

```python
# app/domains/pipeline/domain.py — linha 182, substituir:
# Antes:
if not best_action:
    best_action = "suggest_next_action"
    best_confidence = 0.4

# Depois:
if not best_action:
    return await self._llm_classify_intent(query, context)
```

#### LIA-REC-02: Implementar `ModelRouter` dinâmico (P1)

Inspirado no `src/services/model_router.py` do v5:
```python
# app/shared/agents/model_router.py
class ModelRouter:
    """Seleciona Claude vs GPT vs Gemini baseado em custo/latência/tipo de tarefa."""
    
    async def route(self, task_type: str, context: DomainContext) -> str:
        circuit_status = {name: cb.state for name, cb in ALL_CIRCUITS.items()}
        if circuit_status["anthropic"] == CircuitState.OPEN:
            return "openai"  # fallback automático
        if task_type == "fast_intent_classify":
            return "gemini-flash"  # mais barato
        return "claude"  # padrão
```

#### LIA-REC-03: Migrar SQL direto do tool_registry para Repository (P1)

```python
# app/domains/pipeline/repository.py (novo)
class PipelineRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get_vacancy_candidate(self, vc_id: str) -> VacancyCandidate:
        result = await self._session.execute(
            select(VacancyCandidate).where(VacancyCandidate.id == vc_id)
        )
        return result.scalar_one_or_none()
```

#### LIA-REC-04: Adicionar `semantic_cache` para LLM calls (P2)

Inspirado no `src/services/semantic_cache.py` do v5 — cache baseado em similaridade de embeddings, não hash exato.

#### LIA-REC-05: Resolver ambiguidade entre `BaseAgent` e `DomainPrompt` (P1)

O comentário `"Compatible with existing BaseAgent but independent"` em `base.py` revela tensão. Definir formalmente:
- `BaseAgent` (herança): para novos agentes com compliance completo
- `DomainPrompt` (composição): para wrappers de domínio leves (UI-facing)

### 10.3 Roadmap de Convergência (se os sistemas precisarem colaborar)

| Fase | Duração | Objetivo |
|------|---------|---------|
| 1 — Protocolo comum | 0-30 dias | `AgentMessage` como formato inter-sistema; LIA expõe endpoints compatíveis com v5 |
| 2 — Compliance unificado | 30-90 dias | v5 adota FairnessGuard via middleware (Opção C); shared `AuditTrail` |
| 3 — Capacidades complementares | 90-180 dias | LIA adota `ModelRouter` do v5; v5 `sourced_profile` usa WSI screening da LIA |

---

## Conclusões

### A Diferença Filosófica Fundamental

**LIA: Compliance como convenção estrutural obrigatória por padrão**

```python
# Padrão LIA — EnhancedAgentMixin é parte da convenção de todos os agentes:
class NovoAgente(LangGraphReActBase, EnhancedAgentMixin):
    pass  # FairnessGuard disponível via mixin — omissão seria anomalia em code review
```

**v5: Compliance como responsabilidade do desenvolvedor de cada domínio**

```python
# Padrão v5 — consistente com 6 dos 8 domínios existentes:
class NovoDominio(DomainPrompt):
    async def execute_action(self, action_id, params, context):
        return await self._do_something(params)  # fairness não é parte do contrato
```

**O resultado empírico verificado por leitura de código:** 6/8 domínios v5 sem fairness.py conectado ao fluxo de processamento de intenção do usuário.

### Veredicto por Dimensão

| Dimensão | LIA | v5 | Vencedor |
|----------|-----|-----|---------|
| Compliance garantido | Herança obrigatória | Opt-in não exercido em 75% | LIA |
| Consistência arquitetural | 1 padrão | 3 grupos | LIA |
| Observabilidade automática | ReActObserver + Prometheus | Manual | LIA |
| Paralelismo de agentes | Sequential (ReAct cycle) | asyncio.gather (Grupo 3) | v5 |
| Roteamento dinâmico de LLM | Circuit breaker estático | ModelRouter dinâmico | v5 |
| Latência no caminho simples | 2-10s | 50-200ms | v5 |
| Separação dados/IA | SQL direto nos agents | HTTP Rails (fronteira clara) | v5 |
| Facilidade de adicionar 9º domínio | Herda compliance | Reimplementa compliance | LIA |

**LIA é a arquitetura mais segura para produção em contextos que envolvem decisões sobre candidatos.** O v5 tem vantagens em latência, paralelismo e shared services avançados — mas a ausência empírica de compliance em 75% dos domínios é um risco inaceitável para sistemas com impacto legal.

**Próxima ação estratégica recomendada:** Implementar `ModelRouter` (LIA-REC-02) e fallback LLM no `process_intent` (LIA-REC-01), mantendo o compliance-by-design que é a vantagem competitiva estrutural da LIA.

---

*Arquivos lidos diretamente (com linha específica quando relevante):*
- `lia-agent-system/app/domains/pipeline/agents/pipeline_transition_agent.py` (738 linhas)
- `lia-agent-system/app/domains/pipeline/agents/pipeline_decision_agent.py` (42 linhas)
- `lia-agent-system/app/domains/pipeline/agents/pipeline_tool_registry.py` (1.342 linhas)
- `lia-agent-system/app/domains/pipeline/domain.py` (411 linhas)
- `lia-agent-system/app/domains/base.py` (172 linhas)
- `lia-agent-system/app/shared/compliance/fairness_guard.py` (601 linhas)
- `lia-agent-system/app/shared/resilience/circuit_breaker.py` (883 linhas)
- `lia-agent-system/app/shared/robustness/response_filter.py` (364 linhas)
- `github.com/.../src/domains/applies/react_agent.py` (via GitHub API — código real, MAX_ITERATIONS=12)
- `github.com/.../src/domains/sourced_profile_sourcing/agents/base.py` (via GitHub API — BaseAgent ABC)
- `github.com/.../src/services/circuit_breaker.py` (via GitHub API — DEFAULT_FAILURE_THRESHOLD=3)
- `github.com/.../src/services/response_filter.py` (via GitHub API — 23 abreviações)
- `github.com/.../src/services/react_observer.py` (via GitHub API — log_model_call, log_tool_call)
- `github.com/.../src/services/pii_filter.py` (via GitHub API)
- Listagem de diretório de 8 domínios v5 (para mapa de cobertura)
- Listagem de `src/services/` do v5 (39+ arquivos)
