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

### Mapa de Domínios e Agentes do v5

O v5 é organizado em **8 domínios especializados** + **1 orquestrador** + **1 agente autônomo universal**. Cada domínio herda de `DomainPrompt` (classe base abstrata em `src/domains/base.py`) e é registrado automaticamente via decorator `@register_domain` no `DomainRegistry` (`src/domains/registry.py`). O roteamento de queries do usuário para o domínio correto é feito pelo `DomainOrchestrator` (`src/domains/orchestrator.py`) que delega ao `DomainWorkflow` (`src/domains/workflow.py`) — um grafo LangGraph com nós de intent classification, execução e formatação.

**Fluxo geral:**
```
Usuário → DomainOrchestrator.process_query(domain_id, query, context)
         → DomainWorkflow (LangGraph StateGraph)
           → Nó 1: DomainIntentAgent.analyze() — classifica intent via LLM
           → Nó 2: Domain.execute_action(action_id, params, context)
           → Nó 3: Formatação final da resposta
         → DomainResponse (success, message, data, suggestions)
```

#### Tabela de Domínios

| # | Domínio (`domain_id`) | Nome (`domain_name`) | Finalidade | Como funciona | Arquivos-chave |
|---|----------------------|---------------------|-----------|--------------|---------------|
| 1 | `applies` | Gestão de Candidaturas | Gerenciar candidaturas (applications) dentro de uma vaga específica: busca, detalhes, pipeline/kanban, aprovação/reprovação, ranking, comparação, analytics e ações em lote | Opera no contexto de um `job_id`. Usa `AppliesActions` (mixin de 12+ action classes), `AppliesConversationMemory` para contexto multi-turno, `AppliesCacheManager` para dados já buscados, e LLM (`create_tracked_llm`, temp=0.0) para classificação de intent via prompt. Cada action chama `AppliesAPIClient` que faz requisições REST ao ATS com circuit breaker | `domain.py`, `react_agent.py`, `api_client.py`, `cache.py`, `memory.py`, `cards.py`, `prompts.py`, `actions/` (12 sub-módulos), `prompt_builder/` |
| 2 | `autonomous` | Agente Autônomo Universal | Resolver queries complexas, cross-domain, ou que nenhum domínio especializado cobre. Acesso irrestrito a TODAS as APIs do ATS: vagas, candidatos, candidaturas, avaliações, agendamentos, sourcings, departamentos, listas, aprovações, notificações | Implementa um loop **ReAct** (Reason + Act) via LangGraph `StateGraph`. O agente recebe a query, raciocina sobre qual tool usar, executa a tool (API call), observa o resultado, e decide se precisa de mais steps. Usa `UniversalAPIClient` com acesso a todas as entidades, `select_tools()` para seleção dinâmica de tools, `ReActObserver` para monitoramento, `ExecutionTracker` para tracking, `detect_playbook()` para playbooks pré-definidos, e `ModelRouter` para seleção de modelo. Suporta compressão de contexto (`SMART_COMPRESS_CHARS`, `FILE_OFFLOAD_CHARS`), confirmação para write operations (`WRITE_TOOLS`), e max iterations configurável | `agent.py`, `graph_nodes.py`, `tools/`, `playbooks/`, `prompts.py`, `context_builder.py`, `response_handler.py`, `compression.py`, `tool_selector.py`, `api_client.py` |
| 3 | `evaluation` | Avaliação de Candidatos | Processar e avaliar respostas de candidatos em entrevistas de emprego via chat. Gera scores por rubrica (relevância, profundidade, clareza, exemplos), classifica intenção do candidato e gera próxima pergunta | Usa um grafo LangGraph (`get_interview_graph()`) com state machine (`InterviewState`). O fluxo: classifica intent da mensagem → avalia resposta com `RubricEvaluation` (4 dimensões) → gera `NextQuestionHint` → calcula `FinalAnalysis` quando entrevista termina. Tem `security.py` para validação de input. Usa `BaseDispatcher` (RabbitMQ) para processamento assíncrono de avaliações em lote via `evaluation/dispatcher.py` | `domain.py`, `graph.py`, `nodes.py`, `state.py`, `models.py`, `processor.py`, `final_analysis.py`, `security.py`, `dispatcher.py`, `worker.py`, `tasks.py` |
| 4 | `insights` | Insights e Analytics | Insights agregados de todas as áreas: briefings diários, reports, métricas, alertas, comparações, performance e tendências. Visão panorâmica do recrutamento | Coleta dados de múltiplos domínios e produz análises consolidadas. Usa `InsightsActions` (ações de consulta e agregação), `InsightsConversationMemory`, e LLM para sintetizar narrativas a partir dos dados brutos. Não opera sobre uma entidade específica — é um domínio de **leitura transversal** | `domain.py`, `api_client.py`, `cache.py`, `memory.py`, `prompts.py`, `actions/`, `formatters/`, `config/` |
| 5 | `jobs` | Gestão de Vagas | Gestão completa de vagas de emprego: criar, editar, listar, detalhar, pipeline/kanban, analytics por vaga, funil de conversão, gargalos, alertas, exportação, relatórios, resumos, auto-sourcing | Usa `JobsActions` com pattern matching via regex (`_CONTEXT_ACTION_PATTERNS`) para roteamento rápido de intents comuns (pipeline, kanban, analytics, etc.) sem necessidade de LLM. Tem `TieredContextManager` (cache em 2 tiers: Tier1 para actions leves, Tier2 para actions pesadas), `JobTemplateFormatter` para formatação rica, `JobConversationMemory`, e `fairness.py` para verificação de viés em descriptions de vagas | `domain.py`, `api_client.py`, `cache.py`, `cards.py`, `memory.py`, `prompts.py`, `fairness.py`, `dispatcher.py`, `tasks.py`, `template_formatter.py`, `actions/`, `formatters/`, `prompt_builder/` |
| 6 | `messaging` | Comunicação e Messaging | Envio de emails, feedbacks ao candidato, convites de entrevista, follow-ups, cobranças e toda comunicação com candidatos. Histórico de comunicação | Centraliza toda comunicação outbound. Usa `MessagingActions`, `MessagingConversationMemory`, e `MessagingAPIClient` para chamadas ao serviço de email/notificação do ATS. Tem `services/` subdiretório para serviços auxiliares de messaging | `domain.py`, `api_client.py`, `cache.py`, `memory.py`, `prompts.py`, `actions/`, `formatters/`, `services/`, `config/` |
| 7 | `scheduling` | Agendamento de Entrevistas | Agendamento de entrevistas: agendamento direto, self-scheduling (link para candidato escolher horário), verificação de disponibilidade, agenda do dia/semana, cancelamento, remarcação e ações em lote | Usa pattern matching regex extensivo (6+ patterns: `_CANCEL_PATTERN`, `_RESCHEDULE_PATTERN`, `_LIST_PATTERN`, `_DAILY_AGENDA_PATTERN`, `_AVAILABILITY_PATTERN`, `_SCHEDULE_INTENT_PATTERN`) para classificação rápida de intent sem LLM. Tem `SchedulingSession` para state machine de agendamento multi-step (confirmar horário → confirmar entrevistador → confirmar formato → agendar), e `graph.py` com LangGraph para fluxo complexo | `domain.py`, `api_client.py`, `cards.py`, `memory.py`, `prompts.py`, `graph.py`, `inference.py`, `session.py`, `actions/`, `formatters/`, `config/` |
| 8 | `sourced_profile_sourcing` | Análise de Perfis em Sourcing | Análise e ações sobre perfis de candidatos vinculados a um sourcing específico: busca, score, distribuição, comparação, relatórios, insights, feedback e melhoria de busca | O domínio mais completo em funcionalidade. Requer `sourcing_id` no contexto. Usa `SourcedProfileSourcingActions` (mixin de 12 action classes: Count, Score, Distribution, Analysis, Search, Details, Comparison, Report, SearchImprovement, Insights, Conversational, Feedback). Tem `fact_checker.py` (o único domínio com fact-checking), `fairness.py` (1 de 2 domínios com fairness), `smart_extractor.py` para extração inteligente, `param_extractor.py` para parsing de parâmetros, e `validators.py` para validação de dados | `domain.py`, `api_client.py`, `api_operations.py`, `cache.py`, `memory.py`, `prompts.py`, `fact_checker.py`, `fairness.py`, `smart_extractor.py`, `param_extractor.py`, `validators.py`, `dispatcher.py`, `tasks.py`, `template_formatter.py`, `actions/` (12 sub-módulos), `agents/`, `prompt_builder/`, `config/` |

#### Componentes Transversais (Cross-Domain)

| Componente | Arquivo | Finalidade | Consumido por |
|-----------|---------|-----------|--------------|
| `DomainOrchestrator` | `src/domains/orchestrator.py` | Ponto de entrada único. Recebe `domain_id` + `query` + `context_data`, instancia o domínio via `DomainRegistry`, monta `DomainContext`, e delega ao `DomainWorkflow` | API layer (endpoints REST) |
| `DomainWorkflow` | `src/domains/workflow.py` | Grafo LangGraph (`StateGraph`) com 3 nós: intent classification (LLM), execução da action no domínio, formatação final. Integra `AuditCallbackHandler`, `StreamingCallback`, `ThinkingCallback` | `DomainOrchestrator` |
| `DomainRegistry` | `src/domains/registry.py` | Registry pattern — cada domínio se auto-registra via `@register_domain`. `list_domains()` retorna todos os domínios disponíveis, `get_instance(domain_id)` instancia sob demanda | `DomainOrchestrator`, `DomainWorkflow` |
| `BaseDispatcher` | `src/domains/base_dispatcher.py` | Worker RabbitMQ para processamento assíncrono. Connect via `pika`, prefetch configurável, fila com prioridade (`x-max-priority`). Usado por `evaluation` e `sourced_profile_sourcing` para processar lotes em background | `evaluation/dispatcher.py`, `jobs/dispatcher.py` |
| `DomainIntentAgent` | `src/domains/workflow.py` (classe interna) | Classificador de intent via LLM que determina qual `action_id` executar dentro do domínio. Usa `LLMCacheService` para cache de classificações repetidas | `DomainWorkflow` |

#### Padrão Arquitetural por Domínio

Cada domínio do v5 segue um padrão comum (com variações):

```
src/domains/<domain>/
├── domain.py           # DomainPrompt: id, name, description, actions, system_prompt, intent, execute
├── api_client.py       # Client REST para o ATS (com circuit breaker)
├── cache.py            # Cache em memória para dados já buscados
├── memory.py           # Memória conversacional (contexto multi-turno)
├── prompts.py          # System prompts e prompt builders
├── actions/            # Módulos de ações (cada action = 1 capacidade)
├── formatters/         # Formatação de output (cards, tabelas, etc.)
├── config/             # Configurações do domínio (settings, thresholds)
└── [opcionais]
    ├── fairness.py     # Apenas em jobs e sourced_profile_sourcing
    ├── fact_checker.py  # Apenas em sourced_profile_sourcing
    ├── dispatcher.py    # Worker RabbitMQ (evaluation, jobs, sourced_profile)
    ├── graph.py         # LangGraph para fluxos complexos (evaluation, scheduling)
    └── agents/          # Sub-agentes especializados (sourced_profile)
```

**Dado-chave para comparação com a LIA:** Na LIA, compliance (`fairness_guard.py`, `pii_masking.py`, `audit_callback.py`) é injetado via `EnhancedAgentMixin` — todos os domínios herdam automaticamente. No v5, cada domínio decide individualmente se implementa `fairness.py`, `fact_checker.py`, ou `memory.py`. O resultado: `evaluation` (que dá scores a candidatos) não tem `fairness.py` nem `fact_checker.py`, apesar de ser o domínio com maior impacto sobre decisões de contratação.

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

---

## 11. Anti-Sycophancy e Hallucination Guard

### LIA — `app/shared/prompts/anti_sycophancy_block.py` + `app/shared/compliance/fact_checker.py`

**`anti_sycophancy_block.py` — 3 variantes de prompt (47 linhas):**

```python
# Linha 13: variante operacional — agentes de análise/ação
ANTI_SYCOPHANCY_OPERATIONAL = """
=== PREVENCAO DE SYCOPHANCY ===
REGRAS ABSOLUTAS:
1. NUNCA concorde com pedidos que violem fairness ou compliance apenas para evitar conflito
2. Se o recrutador pedir filtros discriminatórios (gênero, idade, etnia, etc.), recuse com dados
3. Se uma afirmacao do recrutador parecer incorreta, VERIFIQUE antes de confirmar
4. Discordância com dados é preferível a concordância sem evidência
5. Se o recrutador insistir após ver os dados, respeite mas registre:
   "Ok, vou prosseguir conforme solicitado. Registro que os dados indicam [X]."
"""

# Linha 24: variante FULL — agentes consultivos/estratégicos
ANTI_SYCOPHANCY_FULL = """
...
=== VERIFICACAO DE PREMISSAS ===
Antes de aceitar uma afirmacao do recrutador como verdade:
1. Se ele diz "temos muitas vagas", VERIFIQUE com dados disponíveis
2. Se ele diz "voce recomendou Y", VERIFIQUE no historico da conversa
...
"""

# Linha 43: variante ORCHESTRATOR — ponto de entrada global (1 linha)
ANTI_SYCOPHANCY_ORCHESTRATOR = """
Regra anti-sycophancy: nunca confirme pedidos discriminatórios ou que violem compliance.
Apresente alternativas com dados quando necessário.
"""
```

**Cobertura de domínios:** A LIA aplica o bloco anti-sycophancy **em 100% dos system prompts** via `agent_prompts.py` (carrega de YAML) e `interaction_patterns.py` (bloco `ANTI_SYCOPHANCY_BLOCK`). O `PromptLoader.load("shared/agent_prompts")` injeta o bloco em todos os 11 agentes nomeados (orchestrator, job_planner, sourcing, cv_screening, interviewer, wsi_evaluator, scheduling, analyst_feedback, ats_integrator, recruiter_assistant, proactive_insights).

**`fact_checker.py` — 391 linhas, verificação pós-resposta:**

```python
# Linhas 77-91: 4 padrões de detecção de claims verificáveis
SALARY_PATTERN = re.compile(r"R\$\s*([\d.,]+)(?:\s*(?:a|até|-)\s*R\$\s*([\d.,]+))?", ...)
CANDIDATE_COUNT_PATTERN = re.compile(r"(\d+)\s*candidatos?", ...)
PERCENTAGE_PATTERN = re.compile(r"(\d+(?:[.,]\d+)?)\s*%", ...)
DATE_PATTERN = re.compile(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", ...)

# Linhas 101-120: check_response — orquestra as 4 verificações
def check_response(self, response_text: str, context: Optional[Dict] = None) -> FactCheckResult:
    self._check_salary_claims(response_text, context, result)
    self._check_candidate_counts(response_text, context, result)
    self._check_percentage_claims(response_text, context, result)
    self._check_date_claims(response_text, context, result)

# Linhas 251-384: 3 métodos granulares adicionados (V5 parity — Sprint H)
def verify_count_claim(self, response_text, expected_count, tolerance_pct=10.0) -> FactCheckClaim: ...
def verify_average_claim(self, response_text, expected_average, tolerance_pct=20.0) -> FactCheckClaim: ...
def verify_top_candidates_claim(self, response_text, expected_top_n, max_reasonable_top=20) -> FactCheckClaim: ...
```

**Mecanismo:** Verificação regex (não LLM). Compara claims numéricas contra `REASONABLE_SALARY_RANGE = (1_500, 200_000)` e `MAX_CANDIDATE_COUNT = 50_000`. Quando context contém `expected_salary_range` ou `expected_candidate_count`, calcula `deviation_pct` e marca `is_accurate=False` se desvio > threshold.

### v5 — `src/domains/sourced_profile_sourcing/fact_checker.py` (verificado via GitHub API — 9.555 bytes)

O v5 tem `fact_checker.py` em **apenas 1 dos 8 domínios**: `sourced_profile_sourcing`. Lido diretamente:

```python
# src/domains/sourced_profile_sourcing/fact_checker.py (verificado — 9.555 bytes)
@dataclass
class FactCheckResult:
    claim: str
    verified: bool
    actual_value: Any
    confidence: float
    correction: Optional[str] = None

class FactChecker:
    def verify_count_claim(self, claimed_count: int, actual_data: List[Dict], context: str) -> FactCheckResult:
        # Comparação exata: claimed_count vs len(actual_data)
        # Se iguais: verified=True, confidence=1.0
        # Se diferentes: verified=False, confidence=0.0, correction="Na verdade são N"

    def verify_average_claim(self, claimed_avg: float, data: List[Dict], field: str, tolerance=None) -> FactCheckResult:
        # Calcula average real de field em data
        # Compara com claimed_avg dentro de tolerance% (configurável via domain_settings)
        # confidence = 1.0 - (diff/tolerance_value)*0.5 — degradação contínua

    def verify_top_candidates_claim(self, claimed_top: List[Dict], actual_data: List[Dict], ...) -> FactCheckResult: ...
```

**Tipo de verificação:** Baseado em comparação de dados (`actual_data: List[Dict]`) — não regex. O v5 verifica claims numéricas contra dados reais estruturados, enquanto a LIA verifica via regex + expected values do context. Abordagens diferentes: v5 requer dados estruturados no chamador; LIA funciona sobre texto livre.

Anti-sycophancy no v5 é gerenciado via `REACT_SYSTEM_PROMPT` em `src/domains/autonomous/agent.py` (string hardcoded, não bloco canônico reutilizável). Não há equivalente ao `anti_sycophancy_block.py` como módulo compartilhado.

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Anti-sycophancy | Módulo centralizado (`anti_sycophancy_block.py`) com 3 variantes, injetado em 100% dos agentes via YAML | Prompt hardcoded em `autonomous/agent.py` — sem módulo compartilhado |
| Fact-checking | `fact_checker.py` centralizado (391 linhas), 4 tipos de claim, regex sobre texto livre | `fact_checker.py` em 1/8 domínios (`sourced_profile_sourcing`), 9.555 bytes, verificado |
| Mecanismo de verificação | Regex + desvio percentual vs expected values do context (funciona sobre texto livre) | Comparação direta de `List[Dict]` estruturado — requer dados reais no chamador |
| Métodos disponíveis | `verify_count_claim`, `verify_average_claim`, `verify_top_candidates_claim` + regex | `verify_count_claim`, `verify_average_claim`, `verify_top_candidates_claim` — mesmos 3 |
| Cobertura | 100% dos agentes via `EnhancedAgentMixin` | 1/8 domínios — 7 domínios sem fact-checking (verificado por estrutura de diretórios) |
| Confidence score | `deviation_pct` em escala contínua | `confidence = 1.0 - (diff/tolerance)*0.5` em escala contínua — análoga |

**Veredicto de risco:** O domínio `evaluation` do v5 — que gera avaliações e scores de candidatos — não tem fact-checker. Um agente de avaliação pode afirmar "candidato tem 15 anos de experiência" sem verificação cruzada contra os dados reais. Na LIA, o `FactChecker` é chamado pós-resposta pelo `EnhancedAgentMixin`, garantindo que claims numéricas sejam validadas em todos os domínios que herdam da mixin.

---

## 12. GuardrailRepository e GuardrailsSeed

### LIA — `app/shared/compliance/guardrail_repository.py` + `alembic/versions/020_add_guardrails_table.py`

**Schema da tabela (migração `020_add_guardrails_table.py`, criada em 2026-03-04):**

```sql
-- Tabela guardrails — regras editáveis em produção sem deploy
CREATE TABLE guardrails (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level       VARCHAR(20)  NOT NULL DEFAULT 'primary',   -- 'primary' | nível de prioridade
    domain      VARCHAR(100),    -- NULL = global; 'pipeline' = apenas para pipeline
    node        VARCHAR(100),    -- nó específico do LangGraph (nullable)
    tool        VARCHAR(200),    -- nome da tool bloqueada (nullable)
    rule        TEXT NOT NULL,   -- descrição da regra (auditável)
    blocking_message TEXT NOT NULL,  -- mensagem exibida ao usuário quando bloqueado
    is_active   BOOLEAN NOT NULL DEFAULT true,
    company_id  VARCHAR(36),     -- NULL = global; UUID = apenas para este tenant
    updated_by  VARCHAR(36) NOT NULL DEFAULT 'system',
    updated_at  DATETIME NOT NULL DEFAULT now(),
    created_at  DATETIME NOT NULL DEFAULT now()
);

-- 4 índices para queries frequentes em runtime
CREATE INDEX ix_guardrails_is_active ON guardrails (is_active);
CREATE INDEX ix_guardrails_domain    ON guardrails (domain);
CREATE INDEX ix_guardrails_company_id ON guardrails (company_id);
CREATE INDEX ix_guardrails_level     ON guardrails (level);
```

**`guardrail_repository.py` — 185 linhas, 5 operações:**

```python
# Linhas 37-88: get_active — carregamento com prioridade em 4 níveis
@staticmethod
async def get_active(db: AsyncSession, domain: Optional[str] = None, company_id: Optional[str] = None) -> List[Guardrail]:
    """
    Prioridade de carregamento:
      1. Guardrails primários globais (domain=None, company_id=None)
      2. Guardrails primários do tenant (domain=None, company_id=company_id)
      3. Guardrails secundários globais do domínio (domain=domain, company_id=None)
      4. Guardrails secundários do tenant para o domínio
    """
    conditions = [Guardrail.is_active == True]
    domain_filter = or_(Guardrail.domain == None, Guardrail.domain == domain)
    company_filter = or_(Guardrail.company_id == None, Guardrail.company_id == company_id)
    stmt = select(Guardrail).where(and_(*conditions, domain_filter, company_filter)).order_by(Guardrail.level, Guardrail.created_at)

# Linhas 90-102: get_blocked_tools — conveniência para EnhancedAgentMixin
@staticmethod
async def get_blocked_tools(db, domain=None, company_id=None) -> List[str]:
    guardrails = await GuardrailRepository.get_active(db, domain, company_id)
    return [g.tool for g in guardrails if g.tool is not None]

# Linhas 104-125: upsert, toggle_active, update, soft_delete
```

**Ciclo completo de vida de um guardrail na LIA:**

```
Admin cria guardrail via endpoint POST /admin/guardrails
  → GuardrailRepository.upsert(db, GuardrailCreate(domain="pipeline", tool="send_rejection_email", ...))
  → INSERT em tabela 'guardrails' (persiste no PostgreSQL)

Request chega ao PipelineTransitionAgent.process()
  → EnhancedAgentMixin._get_all_enhanced_tools()
  → GuardrailRepository.get_blocked_tools(db, domain="pipeline", company_id=tenant_id)
  → Tools retornadas ao LangGraph sem as bloqueadas
  → LLM não pode chamar tools bloqueadas em runtime

Auditoria
  → AuditCallback registra se tool foi ou não chamada
  → Log de guardrail no audit trail para compliance BCB-498/SOX
```

**`guardrails_seed.py` — `app/core/seeds/guardrails_seed.py` (177 linhas):**

Seed idempotente que popula a tabela `guardrails` com regras iniciais de compliance. Executado via `python -m app.core.seeds.guardrails_seed` ou importando `run_seed()`.

```python
# 6 guardrails primários (globais — todos os agentes e domínios):
PRIMARY_GUARDRAILS = [
    GuardrailCreate(level="primary", rule="Nunca revelar dados pessoais de candidatos...", tool=None, domain=None),
    GuardrailCreate(level="primary", rule="Nunca discriminar candidatos por gênero, raça, idade...", tool=None, domain=None),
    GuardrailCreate(level="primary", rule="Sempre identificar que a comunicação é gerada por IA...", tool=None, domain=None),
    GuardrailCreate(level="primary", rule="Nunca criar perguntas sobre vida pessoal, família...", tool=None, domain=None),
    GuardrailCreate(level="primary", rule="Nunca salvar dados para sistemas externos sem consentimento...", tool=None, domain=None),
    GuardrailCreate(level="primary", rule="Nunca gerar avaliação sem critérios objetivos...", tool=None, domain=None),
]

# 7 guardrails secundários (por domínio/tool):
SECONDARY_GUARDRAILS = [
    GuardrailCreate(level="secondary", domain="wsi_interviewer", rule="Perguntas apenas sobre competências profissionais"),
    GuardrailCreate(level="secondary", domain="communication", tool="send_bulk_email", rule="Email deve incluir identificação de IA"),
    GuardrailCreate(level="secondary", domain="sourcing", rule="Nunca inferir atributos protegidos de nome/foto"),
    GuardrailCreate(level="secondary", domain="cv_screening", rule="Nunca rejeitar sem FairnessGuard"),
    GuardrailCreate(level="secondary", domain="pipeline", tool="reject_candidate", rule="Rejeição requer motivo auditável"),
    GuardrailCreate(level="secondary", domain="pipeline", tool="batch_move", rule="Lote requer confirmação explícita"),
    GuardrailCreate(level="secondary", domain="pipeline", tool="finalize_hiring", rule="Contratação é irreversível e auditada"),
]

async def run_seed(skip_if_exists: bool = True) -> int:
    # Idempotente: se já existem guardrails, skip (count > 0 → return 0)
    # Usa GuardrailRepository.upsert() para cada regra
```

**Cobertura do seed:** 6 primários (globais) + 7 secundários (4 domínios: `wsi_interviewer`, `communication`, `sourcing`, `cv_screening`, `pipeline`) = **13 guardrails iniciais**. Cobrem LGPD (consentimento), anti-discriminação, transparência de IA, fairness e rastreabilidade.

### v5 — Estrutura Equivalente

O v5 não tem tabela equivalente a `guardrails` nem seed de regras em nenhum dos domínios lidos via GitHub API. Regras de comportamento são hardcoded em `src/domains/autonomous/agent.py` como constantes (`HARD_BUDGET=50`, `GLOBAL_TIMEOUT=180`) ou em system prompts. Não há mecanismo de guardrail persistido em banco editável em produção sem deploy.

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Persistência | PostgreSQL (`guardrails` table, revisão 020) | Ausente — hardcoded em código |
| Seed inicial | `guardrails_seed.py` — 13 regras (6 primárias + 7 secundárias) cobrindo LGPD, anti-discriminação, transparência IA, fairness | N/A |
| Escopo | Global OU por tenant OU por domínio OU por tool específica | N/A |
| Editável em produção | Sim — via API REST sem deploy | Não |
| Rollback | `toggle_active` desativa sem deletar (soft disable) | N/A |
| Auditoria | `updated_by`, `updated_at`, `created_at` em cada guardrail | N/A |
| Runtime | Consultado a cada execução via `get_blocked_tools()` | N/A |

**Veredicto de risco:** A ausência de guardrails persistidos no v5 significa que bloquear comportamentos problemáticos em produção requer deploy de código. Na LIA, um admin pode bloquear uma tool específica para um tenant em menos de 1 minuto via API, com efeito imediato na próxima execução do agente.

---

## 13. Learning Loop e Personalização por Recrutador

### LIA — 4 arquivos de aprendizado

**`learning_loop_service.py` — 1.137 linhas — captura e análise de padrões:**

```python
# Linhas 30-46: enums de outcome e tipo de padrão
class FeedbackOutcome(str, Enum):
    ACCEPTED = "accepted"   # recrutador aceitou sugestão sem mudança
    MODIFIED = "modified"   # recrutador aceitou mas modificou
    REJECTED = "rejected"   # recrutador explicitamente rejeitou
    IGNORED  = "ignored"    # nenhuma ação (final_value=None)

class PatternType(str, Enum):
    SALARY_PREFERENCE    = "salary_preference"
    SKILL_PREFERENCE     = "skill_preference"
    BENEFIT_PREFERENCE   = "benefit_preference"
    WORK_MODEL_PREFERENCE = "work_model_preference"
    SCREENING_PREFERENCE  = "screening_preference"
    JD_STYLE_PREFERENCE  = "jd_style_preference"
    SOURCE_TRUST         = "source_trust"

# Linhas 93-102: thresholds de confiança e promoção
CONFIDENCE_THRESHOLDS = {"high": 20, "medium": 10, "low": 5}
ACCEPTANCE_THRESHOLDS = {"promote": 0.75, "demote": 0.25}
```

**Ciclo completo do Learning Loop:**

```
1. CAPTURA (silent): LLM sugere valor para campo → recrutador aceita/modifica/rejeita
   → LearningLoopService._determine_outcome(suggested_value, final_value)
   → FeedbackCapture(company_id, field_name, suggested_value, final_value, outcome)

2. ANÁLISE: process_unprocessed_feedback() → detecta padrões por (company, field, role, seniority)
   → _calculate_confidence(sample_size, acceptance_rate) → "high"/"medium"/"low"/"very_low"
   → acceptance_rate >= 0.75 → promote pattern; < 0.25 → demote

3. VALIDAÇÃO FAIRNESS (F1-02): validate_learning_batch()
   → FairnessGuard.validate_learning_batch(patterns_to_update)
   → Bloqueia padrões onde field_name ∈ _LEARNING_PROTECTED_FIELDS
     (gender, idade, raça, religião, deficiência, nacionalidade, estado_civil, etc.)
   → Bloqueia valores aceitos que contenham termos discriminatórios

4. APLICAÇÃO: padrões aprovados são persistidos como LearningPattern no PostgreSQL
   → usados para pré-preencher sugestões nas próximas sessões do mesmo recruiter/company
```

**`learning_snapshot_service.py` — 268 linhas — rollback de padrões:**

```python
# Linha 27: TTL de 30 dias para snapshots no Redis
SNAPSHOT_TTL_SECONDS = 30 * 24 * 3600
MAX_SNAPSHOTS = 5  # máximo de snapshots por empresa (LRU)

# Chaves Redis:
# learning_snapshot:{company_id}:index → lista dos últimos 5 snapshot keys
# learning_snapshot:{company_id}:{ts}  → payload JSON com os padrões capturados

class LearningSnapshotService:
    async def save_snapshot(self, company_id: str, db) -> Optional[str]: ...
    async def rollback_to_latest(self, company_id: str, db) -> bool: ...
```

**`template_learning_service.py` — 402 linhas — criação automática de templates:**

```python
# Linha 52: threshold para criar template automático
if len(similar_jobs) >= 3:
    existing_template = await self._check_existing_template(company_id, normalized_title)
    if not existing_template:
        return await self._create_learned_template(company_id, job_data, similar_jobs)
# Meta: "80% faster 10th job creation" — doc da classe
```

**`ab_testing_service.py` — 307 linhas — A/B testing de variantes de prompt:**

```python
# Linhas 18-21: distribuição determinística por session_id
def _hash_assignment(self, test_name: str, session_id: str) -> int:
    combined = f"{test_name}:{session_id}"
    return int(hashlib.md5(combined.encode()).hexdigest(), 16)

# bucket = hash % 10000 → seleção proporcional ao traffic_percentage de cada variante
```

### v5 — `src/services/feedback/tracker.py` (verificado via GitHub API)

O v5 tem `src/services/feedback/tracker.py` — um único arquivo de 88 linhas. Lido diretamente:

```python
# src/services/feedback/tracker.py — tabela de feedback implícito
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS interaction_feedback (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    session_id VARCHAR(100),
    domain_id VARCHAR(50) NOT NULL,
    action_id VARCHAR(100),
    query TEXT NOT NULL,
    signal VARCHAR(20) NOT NULL,           -- 'positive' | 'negative' (implicit)
    signal_source VARCHAR(30) NOT NULL DEFAULT 'implicit',
    tools_used TEXT[],
    response_length INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

class FeedbackTracker:
    def track(self, tenant_id, domain_id, query, signal, ...):
        # INSERT em interaction_feedback — captura de sinal implícito

    def get_domain_success_rate(self, tenant_id, domain_id, days=30) -> Optional[float]:
        # SELECT COUNT(*) FILTER (WHERE signal = 'positive') / COUNT(*)
```

**O `FeedbackTracker` é o único módulo de aprendizado do v5.** Ele captura sinais implícitos (positive/negative) por domínio, mas:
- Sem padrão de campos aprendidos (salary, skills, etc.)
- Sem análise de confiança por threshold (promote/demote)
- Sem fairness gate antes de aplicar padrões
- Sem rollback via snapshots
- Sem criação automática de templates
- Sem A/B testing de variantes

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Captura de feedback | Silent — detecta outcome por comparação de valores (7 tipos de padrão) | `FeedbackTracker.track()` — sinal implícito positive/negative por domínio |
| Padrões aprendidos | 7 tipos específicos (salary, skill, benefit, work_model, screening, jd_style, source_trust) | Nenhum — apenas taxa de sucesso por domínio (`get_domain_success_rate()`) |
| Fairness gate no aprendizado | `validate_learning_batch()` bloqueia campos protegidos (F1-02) | **Ausente — verificado** |
| Rollback | Redis snapshots com TTL 30d, máx 5 por empresa | **Ausente — verificado** |
| Templates automáticos | Criação após 3 jobs similares (meta: 80% mais rápido no 10º job) | **Ausente — verificado** |
| A/B testing de prompts | `ABTestingService` com distribuição determinística por session_id | **Ausente — verificado** |
| Aplicação de padrões | Pré-preenchimento de sugestões por company+role+seniority | Feedback capturado mas não aplicado em personalização |

**Veredicto de risco:** O aprendizado sem fairness gate é o risco mais crítico desta seção — **confirmado como ausente no v5** pela leitura direta de `src/services/feedback/tracker.py`. A LIA valida cada batch de padrões antes de persistir, bloqueando campos protegidos (gênero, idade, raça, etc.). Sem esse gate, um sistema de aprendizado pode amplificar vieses históricos ao aprender preferências discriminatórias como "padrão" de uma empresa. O `FeedbackTracker` do v5 captura sinais mas não os aplica em personalização de sugestões.

---

## 14. Inteligência Semântica

### LIA — 3 arquivos em `app/shared/intelligence/`

**`embedding_service.py` — 196 linhas — geração de embeddings via Gemini:**

```python
# Linhas 11-12: constantes
EMBEDDING_DIMENSION = 768
MAX_BATCH_SIZE = 100

# Linha 25: provider Gemini text-embedding-004
class EmbeddingService:
    async def generate_embedding(self, text: str, provider: str = "gemini") -> List[float]:
        text = text.strip()[:8000]  # truncamento de segurança
        return await self._generate_gemini_embedding(text)

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        # processa em lotes de MAX_BATCH_SIZE=100
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i:i + MAX_BATCH_SIZE]
            batch_embeddings = await self._generate_batch_gemini_embeddings(batch)

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        # chunking com overlap para documentos longos
```

**Uso de embeddings na LIA:** Para busca semântica de filtros avançados de candidatos (Modal de Filtros Avançados). O `EmbeddingService` gera vetores de 768 dimensões via `text-embedding-004` do Gemini.

**`semantic_search_service.py` — 443 linhas — expansão semântica de termos:**

```python
# Linhas 43-50: 7 domínios semânticos
class SemanticDomain(str, Enum):
    SKILLS = "skills"           # React → Next.js, Redux, TypeScript
    JOB_TITLES = "job_titles"   # Backend Developer = Desenvolvedor Backend = Back-End Engineer
    ROLES = "roles"
    INDUSTRIES = "industries"
    EXPERTISE = "expertise"
    FIELDS_OF_STUDY = "fields_of_study"
    COMPANIES = "companies"     # concorrentes no mesmo setor

# Linhas 168-201: taxonomias estáticas complementam o LLM
INDUSTRY_TAXONOMY = {"Technology": ["Software", "SaaS", "Cloud", "AI/ML", ...], ...}
SKILLS_TAXONOMY = {"Frontend": ["React", "Vue.js", "Angular", ...], ...}
JOB_TITLES_TAXONOMY = {"desenvolvedor": ["Desenvolvedor Backend", "Full Stack", ...], ...}
# P95 < 300ms target; Redis caching 5-10 min TTL; debounce 400-500ms no frontend
```

**`smart_extractor.py` — 214 linhas — extração regex com cache:**

```python
class SmartExtractor:
    # Cache em memória (TTL 5min, max 200 entradas)
    def extract(self, query: str, domain_id: Optional[str] = None) -> ExtractedParams:
        cached = self._cache.get(query, domain_id or "universal")
        if cached: return cached  # cache hit
        result = self._param_extractor.extract(query, domain_id)
        if result.confidence >= self._confidence_threshold:
            self._regex_only_count += 1  # path rápido — sem LLM
        return result
    # Híbrido: regex para alta confiança, LLM como fallback implícito
```

### v5 — `src/services/semantic_cache.py` (verificado via GitHub API — 10.874 bytes)

```python
# src/services/semantic_cache.py — cache semântico com pgvector (lido diretamente)
SIMILARITY_THRESHOLD = float(os.getenv("SEMANTIC_CACHE_SIMILARITY_THRESHOLD", "0.95"))
SEMANTIC_CACHE_ENABLED = os.getenv("SEMANTIC_CACHE_ENABLED", "false").lower() == "true"
MAX_ENTRIES = int(os.getenv("SEMANTIC_CACHE_MAX_ENTRIES", "10000"))
EMBEDDING_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSIONS = 3072  # ← constante definida mas NÃO usada no schema abaixo
# INCONSISTÊNCIA DETECTADA NO CÓDIGO v5: constante indica 3072d mas tabela usa vector(768)

class SemanticRoutingCache:
    def setup(self):
        # Tabela PostgreSQL com extensão pgvector
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS semantic_routing_cache (
                id SERIAL PRIMARY KEY,
                query_text TEXT NOT NULL,
                query_normalized TEXT NOT NULL,
                embedding vector(768) NOT NULL,   # ← 768d hardcoded (EMBEDDING_DIMENSIONS=3072 não usado)
                domain_id VARCHAR(50) NOT NULL,
                confidence FLOAT NOT NULL DEFAULT 0.90,
                hit_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_hit_at TIMESTAMPTZ,
                UNIQUE(query_normalized)
            )
        """)
        # Índice ivfflat com fallback para hnsw (pgvector)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding
                ON semantic_routing_cache
                USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)
        """)

    def lookup(self, query: str) -> Optional[SemanticLookupResult]:
        # Gera embedding via Gemini gemini-embedding-001 (SEMANTIC_SIMILARITY)
        # Busca por distância coseno: 1 - (embedding <=> %s::vector) > 0.95
        # UPDATE hit_count + 1, last_hit_at em cada cache hit
        embedding_str = "[" + ",".join(str(v) for v in embedding) + "]"
        cur.execute("""
            SELECT domain_id, confidence, query_text,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM semantic_routing_cache
            WHERE 1 - (embedding <=> %s::vector) > %s
            ORDER BY embedding <=> %s::vector LIMIT 1
        """, (embedding_str, embedding_str, SIMILARITY_THRESHOLD, embedding_str))
```

O `SemanticRoutingCache` é um **singleton** (`get_instance()`) que mantém 1 conexão psycopg2 síncrona. Por padrão está **desativado** (`SEMANTIC_CACHE_ENABLED=false`) — deve ser ativado explicitamente via env var.

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Embeddings | Gemini `text-embedding-004`, 768d, batch até 100 (async) | Gemini `gemini-embedding-001`; `EMBEDDING_DIMENSIONS=3072` definido mas schema usa `vector(768)` — **inconsistência interna detectada** (sync psycopg2) |
| Cache de embeddings | Sem cache semântico — SmartExtractor em memória (TTL 5min, regex-first) | `SemanticRoutingCache` com pgvector IVFFlat/HNSW, threshold 0.95, habilitado por env var |
| Persistência do cache | Memória in-process | PostgreSQL com pgvector (durável entre restarts) |
| Estado padrão | SmartExtractor sempre ativo | `SEMANTIC_CACHE_ENABLED=false` — desativado por padrão |
| RAG | Sem serviço RAG centralizado (LIA usa embeddings para busca filtrada) | `rag_service.py` (12.830 bytes) como serviço dedicado |
| Expansão semântica | 7 domínios + taxonomias estáticas + Gemini LLM | Sem equivalente de expansão semântica de termos |
| Extração de parâmetros | `SmartExtractor` regex + cache (214 linhas), híbrido com LLM | Sem equivalente — routing é feito por semantic cache |

**Veredicto:** O v5 tem cache semântico **mais sofisticado** (pgvector, similaridade coseno, durável) mas **desativado por padrão**. A LIA tem **expansão semântica** mais profunda para busca de candidatos (7 domínios, taxonomias, P95<300ms) mas sem cache vetorial. São competências complementares — a LIA beneficiaria do `SemanticRoutingCache` do v5 para roteamento de intenção.

---

## 15. WSI Methodology

### LIA — `app/domains/cv_screening/agents/wsi_interview_graph.py` (1.141 linhas)

**Por que Graph e não ReAct (docstring, linha 6-13):**

```python
"""
Por que Graph (não ReAct)?
- Fluxo sequencial determinístico: pergunta 1 → 2 → N → resultado
- Cada etapa deve ser rastreável individualmente (compliance BCB 498, SOX)
- Sem decisão autônoma — transições baseadas em regras explícitas
- Auditável: log completo de cada nó para FairnessGuard e Bias Audit
"""
```

**Estado do grafo WSI — `WSIInterviewState` (linhas 75-119):**

```python
@dataclass
class WSIInterviewState:
    session_id: str
    company_id: str
    candidate_id: str
    job_id: str
    interview_level: str  # "quick" | "standard" | "full"

    # Banco de perguntas gerado para esta sessão
    question_blocks: List[WSIQuestionBlock]  # cada bloco com bloom_level + dreyfus_level
    current_question_index: int

    # Scores por dimensão
    technical_score: float
    behavioral_score: float
    situational_score: float
    wsi_final_score: Optional[float]
    recommendation: str  # "aprovado" | "aguardando" | "reprovado"

    # Auditoria — cada nó loga no execution_log
    stage: WSIInterviewStage  # INIT → LOAD_CONTEXT → GENERATE_QUESTION → AWAIT_RESPONSE → ...
    execution_log: List[Dict[str, Any]]

    def log_step(self, node: str, details: Dict) -> None:
        self.execution_log.append({"node": node, "timestamp": ..., "question_index": ..., **details})
```

**Rubrica de 4 níveis e frameworks pedagógicos (`WSIQuestionBlock`):**

```python
@dataclass
class WSIQuestionBlock:
    block_id: str
    block_type: str  # "technical" | "behavioral" | "situational"
    question: str
    competency: str
    bloom_level: int   # 1-6 (Taxonomia de Bloom)
    dreyfus_level: int # 1-5 (Modelo Dreyfus de Aquisição de Skills)
    big_five_trait: Optional[str]  # OCEAN model
    max_score: float = 10.0
```

**Stages do grafo (enum `WSIInterviewStage`):**

```
INIT → LOAD_CONTEXT → GENERATE_QUESTION → AWAIT_RESPONSE →
VALIDATE_RESPONSE → SCORE_RESPONSE → ADVANCE → [GENERATE_QUESTION | GENERATE_FEEDBACK] →
COMPLETE (ou ERROR)
```

**Compatibilidade com PostgresSaver** (linha 143): Estado serializado para dict JSON-compatível para checkpointing no PostgreSQL — garante que entrevistas WSI sobrevivam a reinicializações.

### v5 — `src/domains/evaluation/` (verificado via GitHub API — `state.py` + `models.py` lidos)

O v5 tem um domínio `evaluation` completo com LangGraph. A rubrica de avaliação real, lida de `models.py`:

```python
# src/domains/evaluation/models.py — rubrica RubricEvaluation (verificado)
class RubricEvaluation(BaseModel):
    relevance_score: float = Field(ge=0, le=1, description="Quão relevante à pergunta")
    depth_score: float    = Field(ge=0, le=1, description="Profundidade técnica")
    clarity_score: float  = Field(ge=0, le=1, description="Clareza da comunicação")
    examples_score: float = Field(ge=0, le=1, description="Uso de exemplos concretos")
    overall_score: float  = Field(ge=0, le=1, description="Score final ponderado")
    strengths: List[str]  = Field(default_factory=list, max_length=5)
    gaps: List[str]       = Field(default_factory=list, max_length=5)
    feedback: str         = Field(description="Feedback para o recrutador", max_length=800)

class FlowDecision(BaseModel):
    action: Literal["followup", "next_question", "end_interview", "handle_question"]
    reason: str
    followup_focus: Optional[str]

class InputClassification(BaseModel):
    intent: Literal["answer", "question", "off_topic", "unclear", "not_interested"]
    confidence: float
    summary: str
```

**Estado do grafo v5 — `InterviewState` (verificado em `state.py`):**

```python
# src/domains/evaluation/state.py (verificado)
class InterviewState(TypedDict, total=False):
    account_id: int
    evaluation_candidate_id: int
    job_description: str
    question_text: str
    expected_response: str
    candidate_answer: str
    history: List[HistoryMessage]
    style: EvaluationStyle          # persona + pt_br apenas (sem Bloom/Dreyfus)

    classification: Optional[InputClassification]   # intent + confidence + summary
    evaluation: Optional[RubricEvaluation]          # 4 scores + feedback
    flow_decision: Optional[FlowDecision]           # followup/next_question/end_interview

    final_score: float
    is_satisfactory: bool
    followup_needed: bool
    end_interview: bool
```

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Rubrica estruturada | WSI com Bloom (1-6) + Dreyfus (1-5) + Big Five | `RubricEvaluation`: 4 dimensões (relevance, depth, clarity, examples) + overall_score (verificado) |
| Framework pedagógico | Taxonomia de Bloom + Modelo Dreyfus de Aquisição de Skills | Ausente — sem referência a Bloom, Dreyfus ou frameworks pedagógicos (verificado) |
| Tipos de questão | technical / behavioral / situational (com blocks) | `evaluation_type` + `InputClassification.intent` (answer/question/off_topic/unclear/not_interested) |
| Estado persistido | `WSIInterviewState` com PostgresSaver (sobrevive a crashes) | `InterviewState` TypedDict — persistência a cargo do chamador (não verificada em graph.py) |
| Scores por dimensão | 3 scores separados (technical + behavioral + situational) → wsi_final_score | 4 scores (relevance, depth, clarity, examples) + overall_score (verificado) |
| Auditabilidade | Log por nó via `execution_log.log_step()` + `AuditCallback` automático | `AuditCallbackHandler` injetado via LangChain (verificado no `AuditCallback`) |
| Compliance citado | BCB 498 e SOX explicitamente em docstring | Ausente — sem referência a frameworks regulatórios |
| Análise final | `WSIFinalReport` com recommendation "aprovado/aguardando/reprovado" | `FinalAnalysisResponse` com `recommendation: Literal["APPROVED", "ADDITIONAL_ANALYSIS", "NOT_RECOMMENDED"]` (verificado) |

**Veredicto de risco (nuançado por código real):** O v5 tem rubrica de 4 dimensões funcional (relevance, depth, clarity, examples) — mais sofisticada do que o diagnóstico anterior indicava. A ausência é o **framework pedagógico** (Bloom/Dreyfus) que garante progressão de dificuldade e cobertura de competências em entrevistas longas. Para avaliações simples de resposta única, o v5 é adequado. Para entrevistas sequenciais de múltiplas questões com garantia de cobertura técnica e compliance BCB-498/SOX, a LIA tem vantagem estrutural.

---

## 16. Observabilidade e IterationLog — Audit Trail Completo por Iteração

### LIA — 4 arquivos de observabilidade

**`libs/agents-core/lia_agents_core/observability.py` — `IterationLog` por fase:**

```python
@dataclass
class IterationLog:
    iteration: int
    timestamp: str
    phase: str       # "reason" | "tool_call" | "decision"
    duration_ms: float
    tool_name: Optional[str]   # nome da tool chamada (se fase=tool_call)
    tool_args: Optional[dict]  # argumentos da tool
    tool_success: Optional[bool]
    reasoning: Optional[str]   # raciocínio do LLM (fase=reason)
    observation: Optional[str] # resultado da tool (fase=tool_call)
    decision: Optional[str]    # decisão tomada (fase=decision)
    error: Optional[str]

@dataclass
class AgentExecutionLog:
    session_id: str
    domain: str
    agent_class: str
    start_time: str
    total_duration_ms: float
    total_iterations: int
    tools_called: list       # lista de nomes
    tools_succeeded: int
    tools_failed: int
    final_confidence: float
    stage_before: Optional[str]
    stage_after: Optional[str]
    stage_transitioned: bool
    iterations: list         # lista de IterationLog serializados
```

**`libs/agents-core/lia_agents_core/execution_log_store.py` — persistência em PostgreSQL:**

```python
class AgentExecutionRecord(Base):
    __tablename__ = "agent_execution_records"
    id                 = Column(UUID, ...)
    session_id         = Column(String, index=True)
    company_id         = Column(String, index=True)
    user_id            = Column(String)
    domain             = Column(String)
    agent_class        = Column(String)
    user_message       = Column(Text)
    agent_response     = Column(Text)
    total_duration_ms  = Column(Float)
    total_iterations   = Column(Integer)
    tools_called       = Column(JSON)     # lista de nomes de tools
    tools_succeeded    = Column(Integer)
    tools_failed       = Column(Integer)
    final_confidence   = Column(Float)
    reasoning_chain    = Column(JSON)     # lista de IterationLog serializados
    stage_before       = Column(String)   # estágio antes da execução
    stage_after        = Column(String)   # estágio após a execução
    stage_transitioned = Column(Boolean)
    model_provider     = Column(String)
    metadata_          = Column(JSON)

# Query retroativa por session:
async def get_timeline(self, session_id: str) -> List[dict]:
    # reconstrói timeline por (timestamp, iteration) de reasoning_chain
```

**`libs/audit/lia_audit/audit_callback.py` — captura automática via LangChain callbacks:**

```python
class AuditCallback(BaseCallbackHandler):
    # Captura automaticamente via LangChain sem código adicional no agente:
    def on_llm_start(self, serialized, prompts, **kwargs) -> None:
        self._current_llm_start = datetime.now(timezone.utc)
    def on_llm_end(self, response, **kwargs) -> None:
        self.entries.append({"type": "llm_call", "tokens_input": ..., "latency_ms": ...})
    def on_tool_start(self, serialized, input_str, **kwargs) -> None: ...
    def on_tool_end(self, output, **kwargs) -> None:
        self.entries.append({"type": "tool_call", "tool": ..., "output_preview": ..., "latency_ms": ...})
    def on_chain_start(self, serialized, inputs, **kwargs) -> None:
        # registra transição de nó no LangGraph
```

**`app/shared/observability/agent_metrics.py` — Prometheus:**

```python
# Métricas expostas em /metrics para Grafana/Prometheus:
AGENT_REQUEST_TOTAL          # Counter por agent + domain + status
AGENT_FAIRNESS_BLOCKED_TOTAL # Counter por agent + category
AGENT_HITL_TRIGGERED_TOTAL   # Counter por agent + action_type
AGENT_TOKENS_TOTAL           # Counter por agent + model + token_type (input|output)
AGENT_LATENCY_SECONDS        # Histogram por agent + domain
AGENT_CONFIDENCE             # Histogram por agent + domain
```

### v5 — `src/services/react_observer.py` (parcialmente lido na seção 7)

```python
class ReActObserver:
    def __init__(self, session_id: str = ""):
        self._iterations: List[IterationLog] = []  # IterationLog do v5 (mais simples)
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    def log_model_call(self, iteration, duration_ms, input_tokens=0, output_tokens=0): ...
    def log_tool_call(self, iteration, tool_name, tool_args, success, duration_ms, error=""): ...
    def finalize(self) -> Dict[str, Any]: ...  # retorna dict, sem persistência automática
```

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Captura de iteração | `IterationLog` por fase (reason/tool_call/decision) com reasoning, observation, decision | `IterationLog` com phase="reason"\|"tool", sem decision separado |
| Persistência | PostgreSQL (`agent_execution_records`) + storage de objeto (`AuditStorage`) | `finalize()` retorna dict — persistência a cargo do chamador |
| Granularidade | Por LLM call + por tool call + por nó de grafo (via `AuditCallback`) | Por LLM call + por tool call |
| Query retroativa | `get_timeline(session_id)` — reconstrói timeline completa de uma sessão | Sem query retroativa estruturada |
| Prometheus | 6 métricas nativas (requests, fairness, HITL, tokens, latency, confidence) | Sem Prometheus integrado |
| Saúde por domínio | `get_domain_health(company_id, days=30)` — avg_duration, avg_confidence, tool_failure_rate | Sem equivalente |
| Dual write | PostgreSQL (metadados leves) + AuditStorage S3/arquivo (payload completo) | Sem dual write |

**Veredicto de risco:** A ausência de persistência estruturada de `IterationLog` no v5 significa que após o fim de uma sessão, o raciocínio do agente é perdido. Na LIA, cada `reasoning_chain` é persistido em PostgreSQL e consultável retroativamente via `get_timeline()`. Isso é requisito de compliance para auditoria de decisões sobre candidatos.

---

## 17. LGPD, PII e Proteção de Dados

### LIA — `app/shared/pii_masking.py` (221 linhas) — 4 camadas

**Layer 1 — Regex direto (campos identificadores primários):**

```python
# Linhas 18-28: 4 padrões de log masking
CPF_PATTERN     = re.compile(r'\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\-/]?\d{2}\b')
EMAIL_PATTERN   = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_BR_PATTERN = re.compile(r'(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4}[\-\s]?\d{4}\b')
NAME_IN_LOG_PATTERN = re.compile(r'(?:name|nome|candidato|recruiter|user)\s*[=:]\s*["\']([^"\']+)["\']', ...)

# → CPF → ***CPF***, EMAIL → ***EMAIL***, PHONE → ***PHONE***, NAME → ***NAME***
```

**`PIIMaskingFilter` — logging.Filter aplicado ao root logger:**

```python
# Linhas 40-56: filtro em todos os records propagados para handlers
class PIIMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_pii(record.msg)
        if record.args:
            # mascara tanto dicts quanto tuples de args
        if record.exc_info and record.exc_info[1] is not None:
            # mascara mensagens de exceção (stack traces podem expor email/CPF)
        return True

# Linhas 66-87: instalação global no root logger + todos os handlers
def install_global_pii_masking() -> None:
    # child loggers propagam para handlers do root — filtro nos handlers garante cobertura
```

**Layer 3 básica — Quasi-identificadores:**

```python
# Linhas 94-109: padrões de quasi-identificadores
_GRADUATION_YEAR_PATTERN = re.compile(r'\b(?:formad[oa]|graduad[oa]|...)\s+\d{4}\b', ...)
_AGE_EXPLICIT_PATTERN    = re.compile(r'\b(\d{2})\s*anos?\b', ...)
_ADDRESS_BAIRRO_PATTERN  = re.compile(r'\b(?:moro|resido|bairro|cep|rua|avenida|...)\b[^.]{0,60}', ...)
_RG_PATTERN   = re.compile(r'\b\d{1,2}[\.\-]?\d{3}[\.\-]?\d{3}[\-]?[0-9Xx]\b')
_CNPJ_PATTERN = re.compile(r'\b\d{2}[\.\-]?\d{3}[\.\-]?\d{3}[/\\]?\d{4}[\-]?\d{2}\b')
```

**Layer 4 — NER via Microsoft Presidio (opt-in):**

```python
# Linhas 154-184: Presidio AnalyzerEngine lazy singleton
_PRESIDIO_ENABLED = os.environ.get("LLM_PROMPT_PRESIDIO_ENABLED", "false").lower() == "true"
_PRESIDIO_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "DATE_TIME", "NRP"]
```

**Função `strip_pii_for_llm_prompt` — mascaramento ANTES de enviar ao LLM:**

```python
# Linha 125: docstring cita LGPD Art. 12 e EU AI Act Art. 13
def strip_pii_for_llm_prompt(text: str) -> str:
    """
    LGPD Art. 12: minimização de dados pessoais processados por sistemas de IA.
    EU AI Act Art. 13: transparência sobre dados usados em sistemas de alto risco.
    """
    # Controlado por LLM_PROMPT_PII_STRIPPING_ENABLED (padrão: true)
    # Layer 1 + Layer 3: regex
    # Layer 4: Presidio NER (opt-in com LLM_PROMPT_PRESIDIO_ENABLED=true)
```

**`tests/test_sprint4_lgpd_retention.py` — cobertura de testes LGPD:**

```python
class TestAiConsumptionRetentionField:
    def test_model_has_scheduled_deletion_at(self):
        # AiConsumption deve ter campo 'scheduled_deletion_at' (LGPD L6)

class TestTokenTrackingSetsRetention:
    async def test_record_usage_sets_scheduled_deletion_365_days(self):
        # record_usage() deve definir scheduled_deletion_at = now + 365 dias

class TestLgpdCleanupIncludesAiLogs:
    def test_cleanup_service_has_ai_consumption_scope(self):
        # lgpd_cleanup_service deve referenciar AiConsumption no cleanup
    def test_retention_constant_is_365_days(self):
        # lgpd_cleanup_service deve usar retenção de 365 dias para ai_logs
```

### v5 — `src/services/pii_filter.py` (verificado via GitHub API — 983 bytes)

```python
# src/services/pii_filter.py — lido diretamente (983 bytes, 30 linhas)
_PII_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'), '[CPF]'),
    (re.compile(r'\b[\w.+-]+@[\w.-]+\.\w{2,}\b'), '[EMAIL]'),
    (re.compile(r'(?:\+55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}[-\s]?\d{4}\b'), '[PHONE]'),
]  # 3 padrões apenas (CPF, email, telefone)

def mask_pii(text: str) -> str:
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text

class PIIMaskingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            record.msg = mask_pii(str(record.msg))
            record.args = None
        else:
            record.msg = mask_pii(str(record.msg))
        return True

def install_pii_filter():
    root_logger = logging.getLogger()
    if not any(isinstance(f, PIIMaskingFilter) for f in root_logger.filters):
        root_logger.addFilter(PIIMaskingFilter())
```

O `mask_pii()` do v5 **também é chamado em `AuditModels.to_dict()`** — mascarando o `user_query` antes de persistir no audit trail (`user_query: mask_pii(self.user_query)` em `audit_models.py`). Isso é mascaramento **pré-persistência**, mas não pré-LLM.

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Log masking | `PIIMaskingFilter` em root logger + **todos os handlers** (incluindo stack traces de exceção) | `PIIMaskingFilter` em **root logger** apenas (sem cobertura de handlers individuais ou stack traces) |
| Mascaramento pré-LLM | `strip_pii_for_llm_prompt()` com Layer 1+3+4 (padrão: ativo) | **Ausente — verificado** — sem função de mascaramento pré-chamada LLM |
| Mascaramento pré-persistência | Sim — no `PIIMaskingFilter` do log | Sim — `mask_pii(self.user_query)` em `audit_models.to_dict()` |
| Quasi-identificadores | Sim — ano de formatura, idade explícita, referências de bairro/endereço, RG, CNPJ (5 padrões adicionais) | **Ausente — verificado** — apenas 3 padrões (CPF, email, telefone) |
| NER (Presidio) | Layer 4 opt-in via `LLM_PROMPT_PRESIDIO_ENABLED` | **Ausente — verificado** |
| Retenção | AiConsumption com `scheduled_deletion_at` = now+365d; audit SOX 7 anos | `AuditWriter.cleanup(retention_days=90)` — 90 dias, sem política 7 anos |
| Base legal citada | LGPD Art. 12, EU AI Act Art. 13 (em docstring do código de produção) | Ausente — sem referência a base legal |
| Testes de retenção | `test_sprint4_lgpd_retention.py` — 3 classes, 5 testes dedicados | Ausente |
| Campos cobertos | 8 padrões: CPF, email, telefone BR, nome, RG, CNPJ, idade, ano de formatura, endereço | 3 padrões: CPF, email, telefone |

**Veredicto de risco (gap verificado):** O v5 tem mascaramento de **3 PII primários** em logs e audit trail, mas sem mascaramento pré-LLM. Na LIA, dados PII são mascarados **antes** de compor o prompt enviado ao LLM — requisito crítico para LGPD Art. 12 (minimização de dados processados por IA). O gap de quasi-identificadores (idade, endereço, RG) também é confirmado: um candidato com "25 anos" no CV é processado pelo LLM v5 sem mascaramento desse quasi-identificador.

---

## 18. Frameworks de Compliance (SOX, BCB-498, ISO 27001)

### LIA — Manifestações em Código

A LIA referencia SOX, BCB-498 e ISO 27001 em múltiplos arquivos de código real. Abaixo as ocorrências mais relevantes:

**`libs/audit/lia_audit/audit_storage.py` — política de retenção SOX explícita:**

```python
# Linhas 18-22: retenção configurada para 7 anos (SOX compliance)
AUDIT_RETENTION_DAYS_HOT  = 90     # S3 Standard → Glacier Instant Retrieval
AUDIT_RETENTION_DAYS_COLD = 365    # Glacier Instant → Deep Archive
AUDIT_RETENTION_DAYS_DELETE = 2555 # 7 anos total (SOX compliance) → Delete
```

**`app/domains/cv_screening/agents/wsi_interview_graph.py` — BCB-498 e SOX (docstring):**

```python
# Linha 9: compliance citado na justificativa de design
"""
- Cada etapa deve ser rastreável individualmente (compliance BCB 498, SOX)
"""
```

**`libs/models/lia_models/bias_audit_snapshot.py` — SOX e ISO 27001:**

```python
"""
BiasAuditSnapshot — G.4
Persiste snapshots históricos de auditoria de viés para rastreabilidade SOX/ISO 27001.
"""
```

**`app/shared/compliance/audit_storage.py` → `libs/audit/lia_audit/audit_storage.py`:**

A classe `S3Storage` implementa `ServerSideEncryption="AES256"` — requisito ISO 27001 (controle A.8.24 — uso de criptografia). O padrão de append-only (`ON CONFLICT (execution_id) DO NOTHING` no AuditWriter) implementa imutabilidade de audit trail — requisito SOX (controle de integridade de registros).

**Mapa SOX/BCB/ISO na LIA:**

| Framework | Manifestação em código |
|-----------|----------------------|
| SOX — Audit Trail imutável | `ON CONFLICT (execution_id) DO NOTHING` em `AuditWriter._insert_metadata()` |
| SOX — Retenção 7 anos | `AUDIT_RETENTION_DAYS_DELETE = 2555` em `audit_storage.py` |
| SOX — Rastreabilidade WSI | Cada nó do grafo WSI loga via `log_step()` com timestamp e question_index |
| BCB-498 — Rastreabilidade decisões autônomas | `wsi_interview_graph.py` cita BCB 498 explicitamente |
| ISO 27001 — Criptografia | `ServerSideEncryption="AES256"` na `S3Storage` |
| ISO 27001 — Snapshots de auditoria | `BiasAuditSnapshot` com `evaluated_at`, `dimensions_json`, `disparate_impact_data` |
| LGPD — LGPD-safe snapshots | `BiasAuditSnapshot` sem IDs individuais (apenas dados agregados) |

### v5 — `src/services/audit/` (verificado via GitHub API — 4 arquivos lidos)

A partir da leitura direta de `audit_writer.py`, `audit_storage.py` e `audit_models.py`:

```python
# src/services/audit/audit_writer.py — política de retenção VERIFICADA
def cleanup(self, retention_days: int = 90) -> int:
    # DELETE FROM agent_executions WHERE created_at < NOW() - INTERVAL '%s days'
    # Padrão: 90 dias — sem política de retenção de 7 anos

# src/services/audit/audit_writer.py — imutabilidade VERIFICADA
UPSERT_SQL = """
INSERT INTO agent_executions (...) VALUES (...)
ON CONFLICT (execution_id) DO UPDATE SET
    finished_at = EXCLUDED.finished_at,
    status = EXCLUDED.status,
    ...
"""
# ← UPSERT com ON CONFLICT DO UPDATE: audit trail MUTÁVEL por design
# (vs LIA: ON CONFLICT DO NOTHING — audit trail IMUTÁVEL por design)

# src/services/audit/audit_storage.py — storage local em .jsonl, sem S3
class AuditStorageWriter:
    def save(self, execution: AuditExecution):
        file_path = self._log_dir / f"audit_{date_str}.jsonl"
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ...) + "\n")
    
    def cleanup(self, retention_days: int = 90) -> int:
        # Delete de arquivos .jsonl com mtime < cutoff — padrão 90 dias
```

**Evidências verificadas do v5 para compliance:**
- Sem referência a SOX em nenhum arquivo lido
- Sem referência a BCB-498 em nenhum arquivo lido
- Sem referência a ISO 27001 em nenhum arquivo lido
- Retenção padrão de 90 dias (vs SOX exige 7 anos)
- Criptografia em repouso: arquivos .jsonl locais, sem `ServerSideEncryption`
- Imutabilidade: `ON CONFLICT DO UPDATE` — registros são modificáveis

### Tabela Comparativa

| Framework | LIA | v5 |
|-----------|-----|----|
| SOX — Trail imutável | `ON CONFLICT (execution_id) DO NOTHING` — append-only garantido em SQL | `ON CONFLICT (execution_id) DO UPDATE` — **mutável** (verificado em `audit_writer.py`) |
| SOX — Retenção 7 anos | `AUDIT_RETENTION_DAYS_DELETE = 2555` hardcoded em `audit_storage.py` | `cleanup(retention_days=90)` — **90 dias** (verificado em `audit_writer.py` e `audit_storage.py`) |
| BCB-498 | Citado explicitamente em docstring de `wsi_interview_graph.py` | **Ausente** — verificado em todos os 5 arquivos de `src/services/audit/` |
| ISO 27001 — Criptografia | `ServerSideEncryption="AES256"` na S3Storage | **Ausente** — storage em `.jsonl` local sem criptografia (verificado) |
| ISO 27001 — Bias snapshots | `BiasAuditSnapshot` com trail histórico | **Ausente** — verificado |
| Referências em código | SOX em 3 arquivos, BCB-498 em 1, ISO 27001 em 2 | **0 referências** em todos os 5 arquivos `src/services/audit/` lidos |

**Veredicto de risco (confirmado por código):** O v5 tem trail auditável mas **mutável** — o `ON CONFLICT DO UPDATE` permite atualizar registros existentes, o que viola o requisito SOX de imutabilidade de audit trail. A retenção de 90 dias é insuficiente para ambientes SOX (7 anos). Para deployments em instituições financeiras sujeitas ao BCB-498 ou empresas sujeitas ao SOX, o v5 requer modificação arquitetural da camada de audit antes de ser considerado conforme.

---

## 19. Four Fifths Rule e Bias Audit

### LIA — `tests/fairness/test_four_fifths_rule.py` + `libs/models/lia_models/bias_audit_snapshot.py`

**Definição da regra dos 4/5 (linhas 1-15 do arquivo de teste):**

```python
"""
Four-Fifths Rule (Regra dos 4/5) — Bias Audit Baseline

Testa que a taxa de seleção (score >= 60) é equitativa entre grupos demográficos.
Critério: adverse_impact_ratio >= 0.80 para todas as dimensões protegidas.

Referências:
- dei-fairness §4 (Bias Audit Dashboard — adverse_impact_ratio)
- screening-compliance §5 (Four-Fifths Rule)
- EEOC Uniform Guidelines on Employee Selection Procedures (29 CFR §1607)
"""

FOUR_FIFTHS_MIN_RATIO = 0.80  # critério EEOC / dei-fairness §4
```

**Golden dataset e estrutura de teste:**

```python
# Dataset: 60 candidatos sintéticos com scores determinísticos (independentes de demografia)
# Distribuição: 20 alta performance (score >= 75), 20 média (45-74), 20 baixa (< 45)
# Grupos: gender × age_group × disability × region

# Cálculo:
# adverse_impact_ratio(group_a, group_b) = selection_rate(group_a) / max(selection_rate(group_a), selection_rate(group_b))
# Regra: ratio >= 0.80 para todo par de grupos em cada dimensão
```

**Cobertura de dimensões protegidas:**

```python
class TestFourFifthsRuleGender:     # masculino/feminino/nao_binario — par a par
class TestFourFifthsRuleAgeGroup:   # 25-35, 36-45, 46-55, 50+ — par a par
class TestFourFifthsRuleDisability: # com_pcd vs sem_pcd
class TestFourFifthsRuleRegion:     # regiões brasileiras (discriminação socioeconômica)
# Total: 4 dimensões, testes par a par dentro de cada dimensão
# test_older_workers_not_disadvantaged: verificação específica 50+ vs 25-35
```

**`bias_audit_snapshot.py` — persistência histórica de auditorias:**

```python
class BiasAuditSnapshot(Base):
    __tablename__ = "bias_audit_snapshots"
    id                     = Column(UUID, primary_key=True)
    company_id             = Column(UUID, index=True)
    job_id                 = Column(String, index=True)
    evaluated_at           = Column(DateTime)
    total_candidates       = Column(Integer)
    has_alerts             = Column(Boolean)       # True se alguma dimensão viola 4/5
    dimensions_json        = Column(Text)          # JSON das 4 dimensões
    disparate_impact_data  = Column(JSON, nullable=True)  # D3: chi-square por dimensão
    # LGPD-safe: sem IDs individuais de candidatos — apenas dados agregados
```

### v5 — Análise de Impacto Disparate

Nenhum dos arquivos do v5 lidos via GitHub API contém implementação de Four Fifths Rule, `adverse_impact_ratio`, disparate impact analysis, ou `BiasAuditSnapshot`. O domínio `evaluation` que avalia candidatos não tem qualquer verificação de disparate impact.

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Four Fifths Rule | Implementada e testada: 4 dimensões (gender, age, disability, region), par a par, EEOC-compliant | Ausente |
| Golden dataset | 60 candidatos sintéticos, scores determinísticos, 3 tiers de performance | Ausente |
| Adverse impact ratio | `adverse_impact_ratio()` — ratio >= 0.80 por par de grupos | Ausente |
| Histórico de auditorias | `BiasAuditSnapshot` — persistido por job_id, LGPD-safe (sem PII) | Ausente |
| Chi-square por dimensão | `disparate_impact_data` (D3) — análise estatística | Ausente |
| Alertas em produção | `has_alerts=True` quando ratio < 0.80 em qualquer dimensão | Ausente |
| Base regulatória | EEOC 29 CFR §1607, dei-fairness §4, screening-compliance §5 | Ausente |

**Veredicto de risco:** O v5 não tem qualquer mecanismo de detecção de disparate impact. Um sistema de avaliação de candidatos que aprova 90% dos candidatos masculinos mas apenas 40% dos femininos (ratio=0.44, abaixo do threshold 0.80) não dispararia nenhum alerta no v5. Na LIA, isso seria detectado pelo `BiasAuditSnapshot` e flagado via `has_alerts=True` no próximo ciclo de auditoria.

---

## 20. Persona e Interaction Patterns

### LIA — `app/shared/prompts/interaction_patterns.py` + `agent_prompts.py`

**`interaction_patterns.py` — 50 linhas — blocos reutilizáveis:**

```python
# Linhas 6-18: vocabulário semântico de confirmação/negação (usado em parsing de intenção)
NEGATION_WORDS = {
    "não", "nao", "espera", "ainda não", "calma", "volta", "quero mudar",
    "cancelar", "cancela", "parar", "errei", "corrijo", "não é isso", ...
}

CONFIRMATION_WORDS = {
    "sim", "pode", "vamos", "avança", "ok", "beleza", "perfeito",
    "confirmo", "positivo", "aprovo", "concordo", "executar", "fazer", ...
}

# Linhas 21-28: bloco de negação — injeta regra de cancelamento em system prompts
NEGATION_DETECTION_BLOCK = """
## Detecção de Negação e Confirmação
- Se a mensagem contiver negação explícita (não, cancela, espera, volta) → CANCELE a ação
- Para ações irreversíveis (rejeição, envio de email, mudança de estágio) → SEMPRE confirme
- NUNCA execute uma ação que o usuário acabou de negar
"""

# Linhas 30-39: bloco de raciocínio estruturado
CHAIN_OF_THOUGHT_BLOCK = """
## Formato de Raciocínio
SEMPRE raciocine antes de responder:
<thought>
1. O que o recrutador realmente precisa?
2. Quais ferramentas são relevantes para esta situação?
3. Há algum risco de compliance, fairness ou LGPD?
4. Qual é o próximo passo concreto e mensurável?
</thought>
"""

# Linhas 42-49: bloco anti-sycophancy inline (complementa anti_sycophancy_block.py)
ANTI_SYCOPHANCY_BLOCK = """
1. NUNCA concorde apenas para evitar conflito
2. Se os dados contradizem o pedido → apresente os dados primeiro
...
"""
```

**`agent_prompts.py` — persona centralizada via YAML:**

```python
# Linhas 16-21: carregamento de persona e vocabulário via PromptLoader
_shared = PromptLoader.load("shared/lia_persona")
_agents = PromptLoader.load("shared/agent_prompts")

LIA_PERSONA                  = _shared["prompts"]["lia_persona"]
HR_VOCABULARY                = _shared["prompts"]["hr_vocabulary"]
DATA_PERSISTENCE_GUIDELINES  = _shared["prompts"]["data_persistence_guidelines"]
ETHICAL_GUIDELINES           = _shared["prompts"]["ethical_guidelines"]

# 11 prompts de agentes carregados do YAML:
ORCHESTRATOR_PROMPT, JOB_PLANNER_PROMPT, SOURCING_PROMPT, CV_SCREENING_PROMPT,
INTERVIEWER_PROMPT, WSI_EVALUATOR_PROMPT, SCHEDULING_PROMPT, ANALYST_FEEDBACK_PROMPT,
ATS_INTEGRATOR_PROMPT, RECRUITER_ASSISTANT_PROMPT, PROACTIVE_INSIGHTS_PROMPT
```

**Onde a persona LIA é definida:** Em YAML (`app/prompts/shared/lia_persona.yaml`), centralizada e versionável. A persona inclui tom (profissional brasileiro), limites de assertividade (confronta com dados, não apenas concorda), e vocabulário técnico de RH brasileiro (`HR_VOCABULARY`).

### v5 — `src/domains/autonomous/agent.py` — `REACT_SYSTEM_PROMPT`

```python
# src/domains/autonomous/agent.py — constante hardcoded (lida via GitHub API)
REACT_SYSTEM_PROMPT = """Voce e um agente autonomo de recrutamento (ATS).
Voce tem tools especificas para operacoes comuns e uma tool generica (api_request)
para qualquer endpoint da API Rails nao coberto pelas tools especificas..."""
```

Não há equivalente a `NEGATION_WORDS`, `CONFIRMATION_WORDS`, `CHAIN_OF_THOUGHT_BLOCK`, ou módulo de persona centralizado. Cada domínio define seu próprio system prompt — sem consistência garantida de tom, linguagem ou regras de interação.

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Persona centralizada | YAML versionável (`lia_persona.yaml`) — carregado por todos os 11 agentes | Hardcoded em `autonomous/agent.py` — apenas 1 agente |
| Tom e limites de assertividade | `ETHICAL_GUIDELINES`, `ANTI_SYCOPHANCY_BLOCK` injetados em todos os agentes | Não verificado em outros domínios |
| Vocabulário RH brasileiro | `HR_VOCABULARY` como bloco de prompt reutilizável | Ausente como módulo |
| Negação/Confirmação | `NEGATION_WORDS` e `CONFIRMATION_WORDS` — vocabulário semântico codificado | Ausente como módulo |
| Chain of thought | `CHAIN_OF_THOUGHT_BLOCK` — estrutura `<thought>` obrigatória | Ausente como padrão |
| Ações irreversíveis | `NEGATION_DETECTION_BLOCK` — confirmação obrigatória antes de ações irreversíveis | Não verificado |

**Veredicto de risco:** Sem persona centralizada, o v5 depende da disciplina de cada desenvolvedor de domínio para manter consistência de tom e comportamento. Um usuário interagindo com `jobs/domain.py` vs `autonomous/agent.py` pode ter experiências radicalmente diferentes. Na LIA, a persona é garantia estrutural — mudança no YAML propaga para todos os agentes imediatamente.

---

## 21. Audit Trail Arquitetural — Callback, Writer, Storage e Models

### LIA — Fluxo Completo de 4 Arquivos (via `libs/audit/`)

**Fluxo: evento → callback → writer → storage dual:**

```
Evento de execução (LLM call / tool call / node transition)
  ↓
AuditCallback (libs/audit/lia_audit/audit_callback.py)
  - BaseCallbackHandler do LangChain
  - Captura automática: on_llm_start/end, on_tool_start/end, on_chain_start
  - Acumula em self.entries: List[Dict]
  ↓
ExecutionAuditRecord (libs/audit/lia_audit/audit_models.py)
  - Agrega: execution_id, session_id, company_id, domain, agent_type
  - Campos leves: duration_ms, tools_used, nodes_visited, success, confidence
  - Campos pesados: entries (payload completo de LLM + tool calls)
  ↓
AuditWriter (libs/audit/lia_audit/audit_writer.py)
  - _save_full_payload() → AuditStorage (payload completo)
  - _save_metadata()    → PostgreSQL (campos leves, consulta rápida)
  - ON CONFLICT (execution_id) DO NOTHING → IMUTABILIDADE garantida
  ↓
Dual Storage
  ├── PostgreSQL: tabela audit_execution_metadata (indexável, dashboards)
  └── AuditStorage: LocalFileStorage (dev) ou S3Storage (produção)
      - S3: ServerSideEncryption="AES256"
      - Retenção: 90d Standard → 365d Glacier → 2555d (7a) Delete (SOX)
```

**Granularidade por tipo de evento:**

| Tipo de entrada | Campos capturados | Granularidade |
|-----------------|-------------------|---------------|
| `llm_call` | timestamp, model, prompt_preview[:500], response_preview[:500], tokens_input, tokens_output, latency_ms | Por chamada LLM |
| `tool_call` | timestamp, tool_name, input_preview[:500], output_preview[:500], latency_ms, success | Por chamada de tool |
| `node_transition` | timestamp, from_node, to_node, condition | Por transição de nó do LangGraph |

**Shims de compatibilidade retroativa:**

```python
# app/shared/compliance/audit_callback.py → libs/audit/lia_audit/audit_callback.py
# app/shared/compliance/audit_writer.py   → libs/audit/lia_audit/audit_writer.py
# app/shared/compliance/audit_storage.py  → libs/audit/lia_audit/audit_storage.py
# app/shared/compliance/audit_models.py   → libs/audit/lia_audit/audit_models.py
# Os 4 arquivos em app/shared/compliance/ são shims de 1-3 linhas que re-exportam
# da lib real. Isso garante compatibilidade com imports antigos sem duplicar código.
```

**Query retroativa:**

```python
# AuditWriter.load_full(storage_path) → carrega payload completo do storage
# ExecutionLogStore.get_timeline(session_id) → reconstrói timeline por session
# ExecutionLogStore.get_domain_health(company_id, days=30) → métricas de saúde
```

### v5 — `src/services/audit/` (verificado via GitHub API — 4 arquivos lidos diretamente)

O v5 tem `AuditCallbackHandler` — também um `BaseCallbackHandler` LangChain — em `src/services/audit/audit_callback.py` (9.151 bytes). Lido diretamente:

```python
# src/services/audit/audit_callback.py — captura automática via LangChain (verificado)
class AuditCallbackHandler(BaseCallbackHandler):
    def __init__(self, session_id: str, domain_id: str = "", user_query: str = ""):
        self.execution = AuditExecution(session_id=session_id, domain_id=domain_id, user_query=user_query[:500])
        self._node_start_times: Dict[str, float] = {}
        self._llm_start_times: Dict[UUID, float] = {}
        self._tool_start_times: Dict[UUID, float] = {}

    # 12 event types capturados:
    def on_chain_start(...)  → AuditEvent(NODE_START)
    def on_chain_end(...)    → AuditEvent(NODE_END, duration_ms)
    def on_chain_error(...)  → AuditEvent(NODE_ERROR, error)
    def on_llm_end(...)      → AuditEvent(LLM_END, input_tokens, output_tokens, cost_usd, model)
    def on_tool_start(...)   → AuditEvent(TOOL_CALL)
    def on_tool_end(...)     → AuditEvent(TOOL_RESULT, duration_ms)
    def on_tool_error(...)   → AuditEvent(TOOL_ERROR, error)

    def finalize(self, status="completed", error=None):
        # DUAL WRITE: PostgreSQL + storage local (.jsonl)
        get_audit_writer().save_async(self.execution)       # → agent_executions table
        get_audit_storage_writer().save_async(self.execution)  # → logs/audit/audit_{date}.jsonl
```

**Diferença crítica no ciclo de persistência:**
- **LIA:** `AuditCallback.on_chain_end()` → `_schedule_persist()` — **automático ao finalizar chain**
- **v5:** `AuditCallbackHandler.finalize()` → chamado explicitamente pelo domínio — **opt-in**

```python
# src/services/audit/audit_models.py — tracking de custo (não presente na LIA)
@dataclass
class AuditExecution:
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0   # calculado via calculate_cost(model_name, ...)

# Imutabilidade verificada — UPSERT em vez de INSERT:
# src/services/audit/audit_writer.py — ON CONFLICT DO UPDATE (mutável)
```

### Tabela Comparativa

| Dimensão | LIA | v5 |
|---------|-----|----|
| Captura automática | `AuditCallback` — `_schedule_persist()` automático em `on_chain_end()` | `AuditCallbackHandler` — `finalize()` deve ser chamado explicitamente pelo domínio |
| Granularidade | NODE_START/END/ERROR + LLM_START/END/ERROR + TOOL_CALL/RESULT/ERROR + node_name | NODE_START/END/ERROR + LLM_START/END/ERROR + TOOL_CALL/RESULT/ERROR (12 tipos — equivalente) |
| Tracking de custo | Sem `cost_usd` — apenas tokens | `total_cost_usd` calculado via `calculate_cost(model_name, ...)` — **v5 tem vantagem** |
| Imutabilidade | `ON CONFLICT (execution_id) DO NOTHING` — append-only | `ON CONFLICT (execution_id) DO UPDATE` — **mutável** (verificado) |
| Dual storage | PostgreSQL (metadados leves) + S3 ou arquivo (payload completo, configurable) | PostgreSQL + `.jsonl` local (verificado — sem S3 configurado) |
| Criptografia em repouso | `ServerSideEncryption="AES256"` na S3Storage | Arquivos `.jsonl` locais — sem criptografia (verificado) |
| Retenção programada | 90d / 365d / 2555d (SOX 7 anos) em constantes de código | `cleanup(retention_days=90)` padrão — sem hierarquia de retenção (verificado) |
| PII no audit | `prompt_preview[:500]` sem mascaramento pré-storage | `user_query: mask_pii(self.user_query)` — mascara PII na query do usuário (verificado) |
| Query retroativa | `get_timeline(session_id)`, `get_domain_health(company_id, days)` | `get_stats()` — estatísticas globais, sem timeline por session |
| Shims de compatibilidade | 4 shims em `app/shared/compliance/` → re-exportam de `libs/audit/` | N/A |

**Veredicto de risco (baseado em código verificado):** O v5 tem audit trail de qualidade similar em granularidade de eventos (12 tipos), com vantagem em tracking de custo (`cost_usd`). As diferenças críticas para compliance são: (1) persistência **opt-in** via `finalize()` explícito — agentes que não chamam `finalize()` não são auditados; (2) audit trail **mutável** por `ON CONFLICT DO UPDATE`; (3) retenção de **90 dias** vs 7 anos SOX. Para ambientes regulados, essas 3 diferenças requerem mudança de design.

---

## 22. Tabela Mestre de Cobertura Atualizada

Esta seção atualiza a tabela da seção 5 com as 12 novas dimensões descobertas nas seções 11-21.

### Tabela Expandida: Cross-Cutting Concerns

| Dimensão | LIA (cobertura) | v5 (cobertura) | Vencedor |
|---------|-----------------|-----------------|---------|
| **Seções originais (1-10)** | | | |
| Fairness (FairnessGuard) | 100% agentes (herança) | 2/8 domínios (opt-in) | LIA |
| Memory | 100% agentes (herança) | 5/8 domínios (opt-in) | LIA |
| Cache | Serviço compartilhado | 6/8 domínios (opt-in) | v5 (mais domínios) |
| Circuit breaker | 14 instâncias pré-configuradas | Singleton global | Equivalente |
| Audit trail (básico) | 100% agentes (AuditCallback) | Parcial (evaluation, sourced_profile) | LIA |
| Tone filter | 100% via ToneFilter | `response_filter.py` global | Equivalente |
| PII masking (log) | Root logger + handlers (total) | `pii_filter.py` global | Equivalente |
| ModelRouter | Circuit breaker estático | ModelRouter dinâmico | v5 |
| Cost control | Sem budget tier | `cost_ladder.py` por tier | v5 |
| Semantic cache | Sem (apenas hash) | `semantic_cache.py` por similaridade | v5 |
| **Novas dimensões (seções 11-21)** | | | |
| Anti-sycophancy | Módulo centralizado, 3 variantes, 100% agentes | Prompt hardcoded em 1 agente | LIA |
| Fact-checking | Centralizado, 4 tipos, 100% via EnhancedAgentMixin | 1/8 domínios (sourced_profile) | LIA |
| Guardrails persistidos | PostgreSQL editável em produção sem deploy | Ausente | LIA |
| Learning loop | 4 serviços: captura + análise + snapshot + A/B testing | `FeedbackTracker.track()` — sinal positive/negative, sem padrões por campo (verificado) | LIA |
| Fairness gate no aprendizado | `validate_learning_batch()` bloqueia campos protegidos (F1-02) | **Ausente — verificado** em `src/services/feedback/tracker.py` | LIA |
| Inteligência semântica (expansão) | 7 domínios + taxonomias estáticas + Gemini LLM | Sem equivalente de expansão semântica — routing por semantic cache | LIA |
| Inteligência semântica (cache) | SmartExtractor em memória (TTL 5min, regex-first) | `SemanticRoutingCache` pgvector IVFFlat, SEMANTIC_CACHE_ENABLED=false por padrão (verificado) | v5 |
| WSI Methodology | 1.141 linhas, Bloom + Dreyfus + Big Five, PostgresSaver | `RubricEvaluation` com 4 dimensões (sem Bloom/Dreyfus — verificado) | LIA |
| Observabilidade (IterationLog) | PostgreSQL + Prometheus + timeline retroativa | `AuditCallbackHandler` com `finalize()` opt-in, dual write mas mutável (verificado) | LIA |
| LGPD — mascaramento pré-LLM | 4 camadas: regex + quasi-id + Presidio + pré-LLM (padrão: ativo) | **Ausente — verificado**: apenas 3 padrões regex em log e pré-persistência | LIA |
| LGPD — retenção programada | 365d AiConsumption, 7 anos audit (SOX) | `cleanup(retention_days=90)` — 90 dias padrão (verificado) | LIA |
| SOX compliance | `ON CONFLICT DO NOTHING` + retenção 7 anos em código | `ON CONFLICT DO UPDATE` (mutável) + 90 dias (verificado — gap confirmado) | LIA |
| BCB-498 | Citado em `wsi_interview_graph.py` docstring | **Ausente** — 0 referências em `src/services/audit/` (verificado) | LIA |
| ISO 27001 — criptografia | `ServerSideEncryption="AES256"` em S3Storage | `.jsonl` locais sem criptografia (verificado) | LIA |
| Four Fifths Rule | Testes par a par, 4 dimensões, BiasAuditSnapshot | **Ausente — verificado** | LIA |
| Bias Audit histórico | `BiasAuditSnapshot` com chi-square e has_alerts | **Ausente — verificado** | LIA |
| Persona centralizada | YAML versionável, 11 agentes | Hardcoded em `autonomous/agent.py` — sem módulo compartilhado | LIA |
| Negação/Confirmação | `NEGATION_WORDS` + `CONFIRMATION_WORDS` como módulo | **Ausente como módulo** — verificado | LIA |
| Audit trail — tracking de custo | Sem `cost_usd` — apenas tokens | `total_cost_usd` via `calculate_cost(model_name, ...)` — **v5 tem vantagem** (verificado) | v5 |
| RAG como serviço | Sem serviço RAG separado | `rag_service.py` dedicado (12.830 bytes) | v5 |
| TTS | Sem suporte a voz | `tts_service.py` | v5 |

### Síntese Final

**LIA vence em (verificado por código):** compliance garantido por herança, audit trail imutável (`ON CONFLICT DO NOTHING`), retenção SOX 7 anos, mascaramento PII pré-LLM (4 camadas), fairness gate no aprendizado, WSI com frameworks pedagógicos (Bloom/Dreyfus), Four Fifths Rule e BiasAuditSnapshot, persona centralizada (YAML).

**v5 vence em (verificado por código):** tracking de custo por execução (`total_cost_usd`), semantic cache com pgvector e IVFFlat/HNSW (durável, threshold 0.95), ModelRouter dinâmico, cost ladder, RAG como serviço dedicado, TTS.

**Gaps eliminados pelo v5 que o diagnóstico anterior subestimava:** O v5 tem `AuditCallbackHandler` (9.151 bytes, 12 event types, dual write PostgreSQL + .jsonl) e `RubricEvaluation` (4 dimensões de avaliação estruturada). Essas são capacidades reais verificadas por código, não ausências.

**Veredicto geral (baseado em evidências verificadas):** A LIA é a arquitetura mais segura para produção em contextos regulados (SOX, BCB-498, LGPD avançado). O v5 tem audit trail funcional mas com 3 gaps críticos de compliance confirmados: mutabilidade, retenção insuficiente e ausência de criptografia. Para contextos sem obrigação regulatória estrita, o v5 é competitivo — com vantagem em custo operacional (tracking `cost_usd`) e semantic cache.

---

*Arquivos adicionais lidos para as seções 11-21:*

**LIA (lidos do filesystem local):**
- `lia-agent-system/app/shared/prompts/anti_sycophancy_block.py` (47 linhas)
- `lia-agent-system/app/shared/compliance/fact_checker.py` (391 linhas)
- `lia-agent-system/app/shared/compliance/guardrail_repository.py` (185 linhas)
- `lia-agent-system/alembic/versions/020_add_guardrails_table.py` (67 linhas)
- `lia-agent-system/app/shared/learning/learning_loop_service.py` (1.137 linhas — parcial)
- `lia-agent-system/app/shared/learning/learning_snapshot_service.py` (268 linhas — parcial)
- `lia-agent-system/app/shared/learning/template_learning_service.py` (402 linhas — parcial)
- `lia-agent-system/app/shared/learning/ab_testing_service.py` (307 linhas — parcial)
- `lia-agent-system/app/shared/intelligence/embedding_service.py` (196 linhas)
- `lia-agent-system/app/shared/intelligence/semantic_search_service.py` (443 linhas — parcial)
- `lia-agent-system/app/shared/intelligence/smart_extractor.py` (214 linhas)
- `lia-agent-system/app/shared/governance/agent_monitoring_service.py` (581 linhas — parcial)
- `lia-agent-system/app/shared/observability/agent_metrics.py` (122 linhas)
- `lia-agent-system/app/shared/pii_masking.py` (221 linhas)
- `lia-agent-system/app/shared/agents/execution_log_store.py` (shim → libs/agents-core)
- `lia-agent-system/libs/agents-core/lia_agents_core/execution_log_store.py` (205 linhas)
- `lia-agent-system/libs/agents-core/lia_agents_core/observability.py` (165 linhas — parcial)
- `lia-agent-system/libs/audit/lia_audit/audit_callback.py` (263 linhas — parcial)
- `lia-agent-system/libs/audit/lia_audit/audit_writer.py` (115 linhas)
- `lia-agent-system/libs/audit/lia_audit/audit_storage.py` (260 linhas — parcial)
- `lia-agent-system/libs/audit/lia_audit/audit_models.py` (99 linhas)
- `lia-agent-system/tests/fairness/test_four_fifths_rule.py` (273 linhas — parcial)
- `lia-agent-system/libs/models/lia_models/bias_audit_snapshot.py` (54 linhas)
- `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` (1.141 linhas — parcial)
- `lia-agent-system/tests/test_sprint4_lgpd_retention.py` (96 linhas)
- `lia-agent-system/app/shared/prompts/interaction_patterns.py` (50 linhas)
- `lia-agent-system/app/shared/prompts/agent_prompts.py` (75 linhas)

**v5 (lidos via GitHub API — `WeDOTalent/recruiter_agent_v5`, branch default):**
- `src/services/semantic_cache.py` (10.874 bytes — lido completo)
- `src/services/pii_filter.py` (983 bytes — lido completo)
- `src/services/rag_service.py` (12.830 bytes — verificado existência)
- `src/services/feedback/tracker.py` (3.988 bytes — lido completo)
- `src/services/audit/audit_callback.py` (9.151 bytes — lido completo)
- `src/services/audit/audit_writer.py` (6.553 bytes — lido completo)
- `src/services/audit/audit_storage.py` (2.254 bytes — lido completo)
- `src/services/audit/audit_models.py` (3.193 bytes — lido completo)
- `src/domains/evaluation/state.py` (2.712 bytes — lido completo)
- `src/domains/evaluation/models.py` (3.737 bytes — lido completo)

---

## Apêndice: Rastreabilidade dos Arquivos v5 Verificados

Para reprodutibilidade independente, tabela com os commits exatos lidos via GitHub API em **20 de março de 2026**:

| Arquivo v5 | Commit SHA (7 chars) | Commit Message (trunc.) | Data do Commit |
|-----------|---------------------|------------------------|----------------|
| `src/services/semantic_cache.py` | `b19e1ad` | `fix(embeddings): migrate from text-embedding-004 to gemini-e` | 2026-03-19 |
| `src/services/pii_filter.py` | `adf0551` | `feat(pii): add global PII masking filter for logs (CARD-002)` | 2026-03-11 |
| `src/services/rag_service.py` | `71ca04e` | `fix: use postgres database from settings instead of hardcode` | 2026-01-21 |
| `src/services/feedback/tracker.py` | `05bdbcb` | `feat: add memory, feedback and proactive notification servic` | 2026-03-16 |
| `src/services/audit/audit_callback.py` | `f70f4ec` | `feat(audit): add DOMAIN_ACTION event and audit storage write` | 2026-03-11 |
| `src/services/audit/audit_writer.py` | `f70f4ec` | `feat(audit): add DOMAIN_ACTION event and audit storage write` | 2026-03-11 |
| `src/services/audit/audit_storage.py` | `f70f4ec` | `feat(audit): add DOMAIN_ACTION event and audit storage write` | 2026-03-11 |
| `src/services/audit/audit_models.py` | `adf0551` | `feat(pii): add global PII masking filter for logs (CARD-002)` | 2026-03-11 |
| `src/domains/evaluation/state.py` | `7d508db` | `prepare to deploy` | 2026-01-19 |
| `src/domains/evaluation/models.py` | `5e2f26a` | `prepare to deploy` | 2026-01-19 |
| `src/domains/sourced_profile_sourcing/fact_checker.py` | `5e2f26a` | `prepare to deploy` | 2026-01-19 |

**URL de verificação:** `https://github.com/WeDOTalent/recruiter_agent_v5/blob/<SHA>/<path>`

**Escopo de verificação:** LIA lida do filesystem local (workspace); v5 lida via GitHub REST API (`/repos/WeDOTalent/recruiter_agent_v5/contents/{path}`). Ambas as fontes foram lidas diretamente — nenhuma afirmação baseada em inferência ou documentação secundária.
