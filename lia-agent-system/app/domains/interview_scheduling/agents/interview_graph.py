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
from typing import Any

try:
    from langsmith import traceable as _traceable
except ImportError:
    def _traceable(**kwargs):  # type: ignore[misc]
        def decorator(fn):
            return fn
        return decorator

from app.domains.interview_scheduling.agents.interview_scheduling_nodes import (
    interview_details_collector,
    interview_response_planner,
    interview_router,
    interview_scheduler_executor,
    interview_state_loader,
    interview_validator,
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
        self._compiled: Any | None = None

    # ------------------------------------------------------------------
    # Roteamento condicional
    # ------------------------------------------------------------------

    def _route_after_collector(self, state: dict[str, Any]) -> str:
        """Após coleta: verifica se ainda há campos pendentes."""
        from app.domains.interview_scheduling.agents.interview_scheduling_nodes import interview_service

        workflow_data = state.get("workflow_data", {})
        interview_state = interview_service.load_from_workflow_data(workflow_data)

        if interview_state and interview_state.get_next_pending_field() is None:
            return _VALIDATOR
        return _ROUTER

    def _route_after_validator(self, state: dict[str, Any]) -> str:
        """Após validação: executa agendamento ou pede campos faltantes."""
        workflow_data = state.get("workflow_data", {})
        if workflow_data.get("interview_ready_for_scheduling"):
            return _EXECUTOR
        return _RESPONSE

    def _route_after_router(self, state: dict[str, Any]) -> str:
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
        from langgraph.graph import END as LEND
        from langgraph.graph import StateGraph
        from lia_agents_core.checkpointer import get_checkpointer

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

    def _lg_route_collector(self, state: dict[str, Any]) -> str:
        """LangGraph routing após COLLECTOR — idêntico ao legado."""
        return self._route_after_collector(state)

    def _lg_route_router(self, state: dict[str, Any]) -> str:
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
        self, state: dict[str, Any], audit_callback=None
    ) -> dict[str, Any]:
        """Executa via StateGraph nativo com PostgresSaver checkpoint.

        P36 Full: injects 3-layer intelligence before graph execution.

        A3 (compliance) — propaga ``state['company_id']`` para o
        ``tenant_llm_context`` antes da execução para que ``get_provider_for_tenant``
        nos nós e qualquer outro consumidor de LLM resolva o provider/key
        correto por tenant (Choose Your AI). Falha-segura: se o middleware
        já tiver setado o contextvar, mantém o valor.
        """
        if self._compiled is None:
            self._compiled = self._build_langgraph()

        # --- A3: tenant LLM context propagation ---
        _tenant_token = None
        try:
            from app.middleware.auth_enforcement import _current_company_id
            _company_id = str(state.get("company_id") or "")
            if _company_id and not _current_company_id.get(""):
                _tenant_token = _current_company_id.set(_company_id)
        except Exception as _tenant_exc:
            self.logger.debug("[InterviewGraph] tenant_llm_context skipped: %s", _tenant_exc)

        try:
            return await self._invoke_langgraph_inner(state, audit_callback)
        finally:
            # A3: garante restauração do contextvar mesmo em exceção fora do try interno
            if _tenant_token is not None:
                try:
                    from app.middleware.auth_enforcement import _current_company_id
                    _current_company_id.reset(_tenant_token)
                except Exception:
                    pass

    async def _invoke_langgraph_inner(
        self, state: dict[str, Any], audit_callback=None
    ) -> dict[str, Any]:
        """Corpo da execução LangGraph (extraído para garantir reset do tenant context)."""
        # --- P36: Camada 3 — Global scheduling insights ---
        try:
            from app.shared.services.global_insights_service import get_global_insights
            insights_svc = get_global_insights()
            insights = await insights_svc.get_scheduling_insights()
            snippet = insights_svc.format_scheduling_for_prompt(insights)
            if snippet:
                wfd = state.get("workflow_data") or {}
                wfd["scheduling_insights"] = snippet
                state["workflow_data"] = wfd
        except Exception as exc:
            self.logger.debug("[InterviewGraph] GlobalInsights injection skipped: %s", exc)

        # --- P36: Camada 2 — Recruiter personalization ---
        try:
            from app.domains.analytics.services.recruiter_personalization_service import get_recruiter_prompt_context
            recruiter_ctx = await get_recruiter_prompt_context(
                recruiter_id=str(state.get("user_id", "")),
                company_id=str(state.get("company_id", "")),
            )
            if recruiter_ctx:
                wfd = state.get("workflow_data") or {}
                wfd["recruiter_context"] = recruiter_ctx
                state["workflow_data"] = wfd
        except Exception as exc:
            self.logger.debug("[InterviewGraph] RecruiterPersonalization skipped: %s", exc)

        # PII masking: sanitize messages before LLM processing (P35-059)
        try:
            from app.shared.pii_masking import strip_pii_for_llm_prompt
            msgs = state.get("messages", [])
            for msg in msgs:
                if hasattr(msg, "content") and isinstance(msg.content, str):
                    msg.content = strip_pii_for_llm_prompt(msg.content)
        except Exception:
            pass  # fail-open: PII masking failure doesn't block scheduling

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
            # Audit de erro — BCB 498 / SOX compliance
            try:
                from app.core.database import get_db as _get_db
                from app.shared.compliance.audit_service import audit_service
                async for db in _get_db():
                    await audit_service.log_decision(
                        db=db,
                        company_id=state.get("company_id"),
                        domain="interview_scheduling",
                        agent_name="interview_graph",
                        decision_type="schedule_interview",
                        decision="error",
                        candidate_id=state.get("candidate_id"),
                        job_id=state.get("job_id"),
                        metadata={"error": str(exc), "path": "langgraph_native"},
                        criteria_ignored=[],
                    )
                    break
            except Exception:
                pass

        _wfd_lg = result.get("workflow_data", {})
        _error_lg = _wfd_lg.get("interview_graph_error")
        _conf_lg = _wfd_lg.get("confidence_score", 0.5 if not _error_lg else 0.3)
        pass
        if audit_callback:
            await audit_callback.on_chain_end_manual(
                confidence=_conf_lg,
                success=not bool(_error_lg),
                error=_error_lg,
            )

        # Audit log após agendamento confirmado — BCB 498 / SOX compliance
        workflow_data_post = result.get("workflow_data", {})
        if workflow_data_post.get("interview_scheduling_complete"):
            try:
                from app.core.database import get_db as _get_db
                from app.shared.compliance.audit_service import audit_service
                interview_sched_post = workflow_data_post.get("interview_scheduling_state", {})
                async for db in _get_db():
                    await audit_service.log_decision(
                        db=db,
                        company_id=state.get("company_id"),
                        domain="interview_scheduling",
                        agent_name="interview_graph",
                        decision_type="schedule_interview",
                        decision="confirmed",
                        candidate_id=state.get("candidate_id"),
                        job_id=state.get("job_id"),
                        metadata={
                            "scheduled_date": interview_sched_post.get("preferred_date"),
                            "created_interview_id": workflow_data_post.get("created_interview_id"),
                            "hitl_pending": workflow_data_post.get("hitl_pending", False),
                            "path": "langgraph_native",
                        },
                        criteria_ignored=[],
                    )
                    break
            except Exception as _audit_exc:
                self.logger.debug(
                    "[InterviewGraph] audit_service skipped (LangGraph path): %s", _audit_exc
                )

        self.logger.info(
            "[InterviewGraph] execução concluída (LangGraph nativo)",
            extra={"session_id": session_id, "graph": "InterviewGraph"},
        )
        return result

    # ------------------------------------------------------------------
    # Execução
    # ------------------------------------------------------------------

    async def invoke(self, state: dict[str, Any], audit_callback=None) -> dict[str, Any]:
        """Invoca o grafo de agendamento via LangGraph nativo."""
        return await self._invoke_langgraph(state, audit_callback)

    def get_graph_structure(self) -> dict[str, Any]:
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
