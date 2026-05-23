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


# ---------------------------------------------------------------------------
# Recovery #8 (2026-05-23) — FairnessGuard wrappers restaurados.
#
# Perdidos pelo merge commit 02361f41c em 2026-05-01. Compliance gap CRÍTICO
# (EU AI Act Art. 9 Risk Management + Art. 12 Record-keeping pra IA high-risk
# e LGPD Art. 20 explicabilidade). Sem esses wrappers, LIA podia gerar
# mensagens discriminatórias pra candidatos em scheduling sem block.
# ---------------------------------------------------------------------------
_FAIRNESS_BLOCK_FALLBACK_MESSAGE = (
    "Sua solicitação de entrevista foi processada. "
    "Em instantes você receberá uma confirmação por e-mail com os detalhes."
)

# Nós que produzem texto enviado ao candidato (saudação, follow-up,
# confirmação, etc). FairnessGuard wrap aplicado sobre output desses nós.
# Demais nós (loader, router) não escrevem texto candidate-bound.
_FAIRNESS_GUARDED_NODES: tuple[str, ...] = (
    "interview_details_collector",
    "interview_validator",
    "interview_scheduler_executor",
    "interview_response_planner",
)


async def _fairness_check_and_regenerate(
    message: str,
    node_name: str,
    session_id: Any,
    company_id: Any,
    candidate_id: Any,
    job_id: Any,
) -> tuple[str, bool, list[str]]:
    """
    Aplica FairnessGuard.check() sobre uma mensagem candidate-bound; em caso
    de warnings, tenta UMA regeneração (sanitização determinística) e cai em
    fallback seguro se ainda houver violação. Audita o bloqueio via
    ``audit_service.log_decision`` (decision="block",
    criteria_used=["fairness_guard"]).

    Reuso EXCLUSIVO de:
      - ``app.shared.compliance.fairness_guard_middleware.check_fairness``
        (que internamente usa ``FairnessGuard``)
      - ``app.shared.compliance.audit_service.audit_service``

    **Fail-closed (F4 review-fix 2026-04-19)**: se o middleware/import do
    FairnessGuard falhar para uma mensagem candidate-bound, devolvemos a
    mensagem de fallback segura — NUNCA permitimos que conteúdo
    candidate-bound escape sem checagem por erro interno do gate.

    Returns:
        (mensagem_final, was_blocked_after_regen, warnings)
    """
    if not message or not message.strip():
        return message, False, []

    try:
        from app.shared.compliance.fairness_guard_middleware import check_fairness
    except Exception as exc:
        logger.warning(
            "[InterviewGraph][FairnessGuard] FAIL-CLOSED: check_fairness "
            "import failed in node %s: %s — using safe fallback",
            node_name, exc,
        )
        return _FAIRNESS_BLOCK_FALLBACK_MESSAGE, True, [
            f"fairness_guard_unavailable:{type(exc).__name__}"
        ]

    fg_out = check_fairness(
        {"candidate_message": message},
        context=f"interview_graph::{node_name}",
        company_id=str(company_id or ""),
    )
    if not fg_out.has_warnings and not fg_out.is_blocked:
        return message, False, []

    # ---- Regeneração (1 retry) — sanitização determinística -------------
    regenerated = message
    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        regenerated = strip_pii_for_llm_prompt(regenerated)
    except Exception as exc:
        logger.debug(
            "[InterviewGraph][FairnessGuard] PII strip skipped in %s: %s",
            node_name, exc,
        )

    if fg_out.blocked_result and fg_out.blocked_result.blocked_terms:
        for term in fg_out.blocked_result.blocked_terms:
            if term:
                regenerated = regenerated.replace(term, "[REMOVIDO]")

    warnings_aggregated: list[str] = list(fg_out.warnings)
    blocked_after_regen = False
    final_msg = regenerated

    retry_out = check_fairness(
        {"candidate_message": regenerated},
        context=f"interview_graph::{node_name}::retry",
        company_id=str(company_id or ""),
    )
    if retry_out.has_warnings or retry_out.is_blocked:
        for w in retry_out.warnings:
            if w not in warnings_aggregated:
                warnings_aggregated.append(w)
        final_msg = _FAIRNESS_BLOCK_FALLBACK_MESSAGE
        blocked_after_regen = True

    # ---- Audit (decision="block") ---------------------------------------
    try:
        from app.shared.compliance.audit_service import audit_service
        await audit_service.log_decision(
            company_id=str(company_id) if company_id else None,
            agent_name="interview_graph",
            decision_type="send_message",
            action="candidate_message_fairness_block",
            decision="block",
            reasoning=[
                f"FairnessGuard L1/L2 flagged candidate-bound message in node {node_name}",
                f"Regeneration {'failed' if blocked_after_regen else 'succeeded'}",
                f"Warnings: {len(warnings_aggregated)}",
            ],
            criteria_used=["fairness_guard"],
            candidate_id=str(candidate_id) if candidate_id else None,
            job_vacancy_id=str(job_id) if job_id else None,
            human_review_required=blocked_after_regen,
            criteria_ignored=[],
        )
    except Exception as audit_exc:
        logger.warning(
            "[InterviewGraph][FairnessGuard] audit_service.log_decision "
            "FAILED in node %s (decisão de bloqueio mantida): %s",
            node_name, audit_exc,
        )

    logger.warning(
        "[InterviewGraph][FairnessGuard] node=%s blocked_after_regen=%s "
        "warnings=%d session=%s",
        node_name, blocked_after_regen, len(warnings_aggregated), session_id,
    )
    return final_msg, blocked_after_regen, warnings_aggregated


def _wrap_node_with_fairness(node_fn, node_name: str):
    """
    Decorator-style wrapper que aplica ``_fairness_check_and_regenerate``
    sobre ``response_data["message"]`` após cada nó relevante. Mantém o nó
    canônico intacto (princípio canonical-fix: não duplicar lógica nos nós).
    """
    async def _wrapped(state: dict[str, Any]) -> dict[str, Any]:
        result = await node_fn(state)
        try:
            wd = (result.get("workflow_data") or {}) if isinstance(result, dict) else {}
            rd = wd.get("response_data") or {}
            msg = rd.get("message") or ""
            if not msg:
                return result
            final_msg, blocked, warnings = await _fairness_check_and_regenerate(
                message=msg,
                node_name=node_name,
                session_id=state.get("session_id") if isinstance(state, dict) else None,
                company_id=state.get("company_id") if isinstance(state, dict) else None,
                candidate_id=state.get("candidate_id") if isinstance(state, dict) else None,
                job_id=state.get("job_id") if isinstance(state, dict) else None,
            )
            if final_msg != msg or warnings:
                rd["message"] = final_msg
                if blocked:
                    rd["fairness_blocked"] = True
                if warnings:
                    rd["fairness_warnings"] = warnings
                wd["response_data"] = rd
                result["workflow_data"] = wd
        except Exception as exc:
            logger.debug(
                "[InterviewGraph][FairnessGuard] node wrap error on %s: %s",
                node_name, exc,
            )
        return result

    _wrapped.__name__ = f"{node_name}__fairness_guarded"
    _wrapped.__wrapped__ = node_fn  # type: ignore[attr-defined]
    return _wrapped


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

        # Recovery #8 (2026-05-23) — F4 (AUDIT 2026-04 paridade WSI): aplica
        # FairnessGuard como wrapper sobre os nós que produzem texto
        # candidate-bound. Demais nós permanecem inalterados (LOADER/ROUTER
        # não escrevem mensagem).
        for name, fn in self._node_fns.items():
            if name in _FAIRNESS_GUARDED_NODES:
                builder.add_node(name, _wrap_node_with_fairness(fn, name))
            else:
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
        """
        if self._compiled is None:
            self._compiled = self._build_langgraph()

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

        # REGRA-4-EXEMPT: LangGraph ainvoke wrapper — except sets
        # result["workflow_data"]["interview_graph_error"] as canonical inline
        # error envelope. Audit trail logged. Downstream checks result dict
        # for the error key, not silent.
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
        """Invoca o grafo de agendamento via LangGraph nativo.

        Recovery #8 (2026-05-23): post-graph FairnessGuard safety net
        restaurado (defesa em profundidade — wrappers por-nó + check final).
        """
        result = await self._invoke_langgraph(state, audit_callback)
        return await self._apply_fairness_guard_to_response(
            result,
            session_id=state.get("session_id") if isinstance(state, dict) else None,
            company_id=state.get("company_id") if isinstance(state, dict) else None,
            candidate_id=state.get("candidate_id") if isinstance(state, dict) else None,
            job_id=state.get("job_id") if isinstance(state, dict) else None,
        )

    async def _apply_fairness_guard_to_response(
        self,
        result: dict[str, Any],
        session_id: str | None,
        company_id: Any,
        candidate_id: Any,
        job_id: Any,
    ) -> dict[str, Any]:
        """
        Defesa em profundidade: re-aplica FairnessGuard sobre
        ``response_data["message"]`` após a execução completa do grafo. A
        verificação por-nó (via ``_wrap_node_with_fairness``) já cobre cada
        gerador de texto — este método é uma rede de segurança final.

        Delega à fonte canônica ``_fairness_check_and_regenerate`` (princípio
        canonical-fix: lógica única, reutilizada pelos wrappers e pelo
        post-graph). Política BLOCK + REGENERATE (1 retry) + audit.
        """
        try:
            workflow_data_post = result.get("workflow_data") or {}
            response_data = workflow_data_post.get("response_data") or {}
            candidate_msg = response_data.get("message") or ""
            if not candidate_msg:
                return result

            final_msg, blocked, warnings = await _fairness_check_and_regenerate(
                message=candidate_msg,
                node_name="post_graph",
                session_id=session_id,
                company_id=company_id,
                candidate_id=candidate_id,
                job_id=job_id,
            )
            if final_msg == candidate_msg and not warnings:
                return result

            response_data["message"] = final_msg
            if blocked:
                response_data["fairness_blocked"] = True
            if warnings:
                response_data["fairness_warnings"] = [str(w) for w in warnings]
            workflow_data_post["response_data"] = response_data
            result["workflow_data"] = workflow_data_post
        except Exception as fg_exc:
            self.logger.debug(
                "[InterviewGraph][A3] FairnessGuard check skipped: %s", fg_exc
            )
        return result

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
