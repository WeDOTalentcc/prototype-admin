"""
Interview Scheduling Graph - LangGraph state machine para agendamento de entrevistas.

Por que Graph (não ReAct)?
- Fluxo discreto e previsível: coletar campos → validar → agendar → confirmar
- Checkpoints auditáveis em cada etapa (compliance BCB 498, SOX)
- Sem raciocínio autônomo — transições por regras explícitas

Conforme ADR-002: fluxos com etapas conhecidas + checkpoint = Graph.

Nós:
  1. interview_state_loader    — carrega/inicializa InterviewSchedulingState
  2. interview_details_collector — extrai campos da mensagem do usuário via LLM
  3. interview_router           — decide: coletar mais campos ou executar agendamento
  4. interview_validator        — valida completude antes de executar
  5. interview_scheduler_executor — agenda via calendar_service + cria registro no DB
  6. interview_response_planner — planeja resposta final para o usuário
"""
import logging
import time
from typing import Any, Dict, Optional

try:
    from langsmith import traceable as _traceable
except ImportError:
    def _traceable(**kwargs):  # type: ignore[misc]
        def decorator(fn):
            return fn
        return decorator

from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
    interview_state_loader,
    interview_router,
    interview_details_collector,
    interview_validator,
    interview_scheduler_executor,
    interview_response_planner,
)

logger = logging.getLogger(__name__)

# LangGraph TypedDict — compatível com os nós existentes (Dict[str, Any])
try:
    from typing import TypedDict as _TypedDict

    class _InterviewStateDict(_TypedDict, total=False):
        session_id: str
        company_id: str
        user_id: str
        message: str
        workflow_data: Any
        conversation_history: list

    _HAS_TYPED_DICT = True
except Exception:
    _HAS_TYPED_DICT = False
    _InterviewStateDict = dict  # type: ignore[assignment,misc]

# Nomes dos nós (constantes para evitar typos nas arestas)
_LOADER = "interview_state_loader"
_COLLECTOR = "interview_details_collector"
_ROUTER = "interview_router"
_VALIDATOR = "interview_validator"
_EXECUTOR = "interview_scheduler_executor"
_RESPONSE = "interview_response_planner"
_END = "END"

MAX_ITERATIONS = 8  # Proteção contra loops infinitos de coleta


class InterviewGraph:
    """
    Grafo LangGraph para agendamento conversacional de entrevistas.

    Fluxo principal:
      LOADER → COLLECTOR → ROUTER
                               ↓ campos pendentes → COLLECTOR (loop)
                               ↓ campos completos → VALIDATOR
      VALIDATOR → EXECUTOR → RESPONSE → END
      VALIDATOR (inválido)  → RESPONSE → END  (pede campos faltantes)
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._node_fns = {
            _LOADER: interview_state_loader,
            _COLLECTOR: interview_details_collector,
            _ROUTER: interview_router,
            _VALIDATOR: interview_validator,
            _EXECUTOR: interview_scheduler_executor,
            _RESPONSE: interview_response_planner,
        }
        self._compiled: Optional[Any] = None

    # ------------------------------------------------------------------
    # Roteamento condicional
    # ------------------------------------------------------------------

    def _route_after_collector(self, state: Dict[str, Any]) -> str:
        """Após coleta: verifica se ainda há campos pendentes."""
        from app.schemas.interview_scheduling_state import InterviewSchedulingState
        from app.domains.interview_scheduling.agents.interview_scheduling_nodes import interview_service

        workflow_data = state.get("workflow_data", {})
        interview_state = interview_service.load_from_workflow_data(workflow_data)

        if interview_state and interview_state.get_next_pending_field() is None:
            return _VALIDATOR
        return _ROUTER

    def _route_after_validator(self, state: Dict[str, Any]) -> str:
        """Após validação: executa agendamento ou pede campos faltantes."""
        workflow_data = state.get("workflow_data", {})
        if workflow_data.get("interview_ready_for_scheduling"):
            return _EXECUTOR
        return _RESPONSE

    def _route_after_router(self, state: Dict[str, Any]) -> str:
        """Após router: volta para coleta ou parte para validação."""
        workflow_data = state.get("workflow_data", {})
        if workflow_data.get("next_collection_target"):
            return _COLLECTOR
        return _VALIDATOR

    # ------------------------------------------------------------------
    # LangGraph nativo — StateGraph
    # ------------------------------------------------------------------

    def _build_langgraph(self):
        """Constrói e compila o StateGraph nativo do LangGraph."""
        from langgraph.graph import StateGraph, END as LEND
        from app.shared.agents.checkpointer import get_checkpointer

        state_schema = _InterviewStateDict if _HAS_TYPED_DICT else dict
        builder = StateGraph(state_schema)

        for name, fn in self._node_fns.items():
            builder.add_node(name, fn)

        builder.set_entry_point(_LOADER)
        builder.add_edge(_LOADER, _COLLECTOR)
        builder.add_conditional_edges(_COLLECTOR, self._lg_route_collector, {
            _VALIDATOR: _VALIDATOR,
            _ROUTER: _ROUTER,
        })
        builder.add_conditional_edges(_ROUTER, self._lg_route_router, {
            _COLLECTOR: _COLLECTOR,
            _VALIDATOR: _VALIDATOR,
            _RESPONSE: _RESPONSE,
        })
        builder.add_conditional_edges(_VALIDATOR, self._route_after_validator, {
            _EXECUTOR: _EXECUTOR,
            _RESPONSE: _RESPONSE,
        })
        builder.add_edge(_EXECUTOR, _RESPONSE)
        builder.add_edge(_RESPONSE, LEND)

        return builder.compile(checkpointer=get_checkpointer())

    def _lg_route_collector(self, state: Dict[str, Any]) -> str:
        """LangGraph routing após COLLECTOR — idêntico ao legado."""
        return self._route_after_collector(state)

    def _lg_route_router(self, state: Dict[str, Any]) -> str:
        """LangGraph routing após ROUTER.

        Diferença do legado: quando há campo pendente, retorna RESPONSE
        (pede ao usuário) em vez de COLLECTOR — o próximo invoke() do
        frontend traz a resposta e o ciclo reinicia.
        """
        workflow_data = state.get("workflow_data", {})
        if workflow_data.get("next_collection_target"):
            return _RESPONSE  # pede campo ao usuário → frontend faz próximo invoke
        return _VALIDATOR

    async def _invoke_langgraph(
        self, state: Dict[str, Any], audit_callback=None
    ) -> Dict[str, Any]:
        """Executa via StateGraph nativo com PostgresSaver checkpoint."""
        try:
            if self._compiled is None:
                self._compiled = self._build_langgraph()
        except Exception as exc:
            self.logger.warning(
                f"[InterviewGraph] LangGraph build failed, falling back to legacy: {exc}"
            )
            return await self._invoke_legacy(state, audit_callback)

        session_id = state.get("session_id", "unknown")
        if audit_callback:
            audit_callback.on_chain_start_manual()

        self.logger.info(
            "[InterviewGraph] iniciando execução (LangGraph nativo)",
            extra={"session_id": session_id, "graph": "InterviewGraph"},
        )

        try:
            result = await self._compiled.ainvoke(
                state,
                config={"configurable": {"thread_id": session_id}},
            )
        except Exception as exc:
            self.logger.error(
                f"[InterviewGraph] StateGraph ainvoke error: {exc}", exc_info=True
            )
            result = dict(state)
            result.setdefault("workflow_data", {})["interview_graph_error"] = str(exc)

        if audit_callback:
            error = result.get("workflow_data", {}).get("interview_graph_error")
            await audit_callback.on_chain_end_manual(
                confidence=0.9 if not error else 0.3,
                success=not bool(error),
                error=error,
            )

        self.logger.info(
            "[InterviewGraph] execução concluída (LangGraph nativo)",
            extra={"session_id": session_id, "graph": "InterviewGraph"},
        )
        return result

    # ------------------------------------------------------------------
    # Execução
    # ------------------------------------------------------------------

    async def invoke(self, state: Dict[str, Any], audit_callback=None) -> Dict[str, Any]:
        """Dual-path: LangGraph nativo (USE_LANGGRAPH_NATIVE=True) ou legado."""
        from app.core.config import settings
        if settings.USE_LANGGRAPH_NATIVE:
            return await self._invoke_langgraph(state, audit_callback)
        return await self._invoke_legacy(state, audit_callback)

    @_traceable(name="InterviewGraph._invoke_legacy", run_type="chain")
    async def _invoke_legacy(self, state: Dict[str, Any], audit_callback=None) -> Dict[str, Any]:
        """
        Executa o grafo de agendamento (implementação legada).

        Sequência de nós:
          LOADER → COLLECTOR → router condicional → VALIDATOR → EXECUTOR → RESPONSE
        """
        session_id = state.get("session_id", "unknown")
        if audit_callback:
            audit_callback.on_chain_start_manual()
        self.logger.info(
            "[InterviewGraph] iniciando execução (legado)",
            extra={"session_id": session_id, "graph": "InterviewGraph"},
        )

        # Nó 1: carrega estado
        state = await self._run_node(_LOADER, state, audit_callback)

        # Nó 2: coleta inicial de campos da mensagem atual
        state = await self._run_node(_COLLECTOR, state, audit_callback)

        # Loop de coleta + roteamento (máx MAX_ITERATIONS)
        iterations = 0
        while iterations < MAX_ITERATIONS:
            iterations += 1
            next_node = self._route_after_collector(state)

            if next_node == _VALIDATOR:
                break  # Todos os campos coletados — sai do loop

            # Router confirma próximo campo e volta para COLLECTOR
            state = await self._run_node(_ROUTER, state, audit_callback)
            next_after_router = self._route_after_router(state)

            if next_after_router == _VALIDATOR:
                break  # Router decidiu que está completo

            # Retorna para coleta, mas nesta execução não há nova mensagem do usuário.
            # O loop encerra aqui — o frontend fará outra chamada com a resposta do usuário.
            state = await self._run_node(_RESPONSE, state, audit_callback)
            self.logger.info("InterviewGraph: aguardando próxima mensagem do usuário")
            return state

        # Nó 3: valida completude
        state = await self._run_node(_VALIDATOR, state, audit_callback)

        next_node = self._route_after_validator(state)

        if next_node == _EXECUTOR:
            # Nó 4: executa agendamento real
            state = await self._run_node(_EXECUTOR, state, audit_callback)

        # Nó 5: planeja resposta final
        state = await self._run_node(_RESPONSE, state, audit_callback)

        if audit_callback:
            error = state.get("workflow_data", {}).get("interview_graph_error")
            await audit_callback.on_chain_end_manual(
                confidence=0.9 if not error else 0.3,
                success=not bool(error),
                error=error,
            )

        self.logger.info(
            "[InterviewGraph] execução concluída (legado)",
            extra={"session_id": session_id, "graph": "InterviewGraph"},
        )
        return state

    async def _run_node(self, node_name: str, state: Dict[str, Any], audit_callback=None) -> Dict[str, Any]:
        """Executa um nó com logging auditável (BCB 498 / SOX) e sem abortar o grafo."""
        fn = self._node_fns.get(node_name)
        if fn is None:
            self.logger.error(f"[InterviewGraph] Nó desconhecido: {node_name}")
            return state

        session_id = state.get("session_id", "unknown")
        t0 = time.perf_counter()
        try:
            self.logger.info(
                f"[InterviewGraph] node_start node={node_name}",
                extra={"session_id": session_id, "node": node_name, "graph": "InterviewGraph"},
            )
            result = await fn(state)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            self.logger.info(
                f"[InterviewGraph] node_end node={node_name} elapsed_ms={elapsed_ms}",
                extra={
                    "session_id": session_id,
                    "node": node_name,
                    "elapsed_ms": elapsed_ms,
                    "graph": "InterviewGraph",
                },
            )
            if audit_callback:
                audit_callback.on_tool_call(
                    tool_name=node_name,
                    input_preview=f"session={session_id}",
                    output_preview="ok",
                    latency_ms=float(elapsed_ms),
                    success=True,
                )
            return result
        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            self.logger.error(
                f"[InterviewGraph] node_error node={node_name} elapsed_ms={elapsed_ms}: {exc}",
                extra={
                    "session_id": session_id,
                    "node": node_name,
                    "elapsed_ms": elapsed_ms,
                    "error": str(exc),
                    "graph": "InterviewGraph",
                },
                exc_info=True,
            )
            if audit_callback:
                audit_callback.on_tool_call(
                    tool_name=node_name,
                    input_preview=f"session={session_id}",
                    output_preview="error",
                    latency_ms=float(elapsed_ms),
                    success=False,
                    error=str(exc),
                )
            state.setdefault("workflow_data", {})["interview_graph_error"] = str(exc)
            return state

    def get_graph_structure(self) -> Dict[str, Any]:
        """Retorna metadata do grafo para observabilidade."""
        return {
            "graph_type": "InterviewGraph",
            "nodes": list(self._node_fns.keys()),
            "start_node": _LOADER,
            "end_node": _RESPONSE,
            "max_iterations": MAX_ITERATIONS,
            "conditional_edges": [
                {"from": _COLLECTOR, "condition": "next_pending_field", "targets": [_VALIDATOR, _ROUTER]},
                {"from": _ROUTER, "condition": "next_collection_target", "targets": [_COLLECTOR, _VALIDATOR]},
                {"from": _VALIDATOR, "condition": "interview_ready_for_scheduling", "targets": [_EXECUTOR, _RESPONSE]},
            ],
        }


# Singleton — importado pelos handlers de API
interview_graph = InterviewGraph()
