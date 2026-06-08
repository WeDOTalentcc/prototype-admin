"""
AutonomousReActAgent — Agente ReAct cross-domain autônomo (Tier 6 do CascadedRouter).

Resolve queries que cruzam múltiplos domínios sem handoff entre agentes especializados.
Acionado apenas quando nenhum dos Tiers 0-5 tem confiança suficiente para rotear.

Características:
- Pool de 40+ tools curadas de todos os domínios (job, sourcing, pipeline, analytics, scheduling, communication)
- Budget máximo configurável (AUTONOMOUS_REACT_MAX_STEPS, padrão 10)
- Circuit breaker integrado (fail-safe)
- FairnessGuard e PII masking via EnhancedAgentMixin (herdado de LangGraphReActBase)
- LangSmith traces via AuditCallback (herdado de _process_langgraph)
- Fallback para clarification se não resolver em N passos
"""
import contextvars
import functools
import logging
import os
from typing import Any

# ADR-029 §3 / Audit H 2026-05-06: use canonical ContextVar from auth_enforcement
# instead of a sibling ContextVar. Previously this module defined its own
# `_CURRENT_COMPANY_ID` which bypassed the R-008 setter lockdown and the
# Sprint 1B `tool_handler` decorator's ContextVar resolution path.
# The local alias name is kept for backward compat in this file's call sites.
from app.middleware.auth_enforcement import _current_company_id as _CURRENT_COMPANY_ID  # noqa: E402, F401
from app.shared.prompts.prompt_composer import PromptComposer

from lia_agents_core.agent_interface import AgentInput, AgentOutput, AgentAction
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.autonomous.agents.autonomous_tool_registry import (
    get_autonomous_tools,
    get_tool_names,
)
from app.shared.agents.agent_registry import register_agent
from app.shared.agents.tenant_aware_agent import TenantAwareAgentMixin

_AUTONOMOUS_MAX_STEPS_DEFAULT = 10

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singleton circuit breaker — shared across all requests
# ---------------------------------------------------------------------------
_CIRCUIT_BREAKER: Any = None


def _get_circuit_breaker() -> Any:
    """Return (or lazy-create) the module-level singleton circuit breaker."""
    global _CIRCUIT_BREAKER
    if _CIRCUIT_BREAKER is None:
        try:
            from app.shared.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
            _CIRCUIT_BREAKER = CircuitBreaker(
                name="autonomous_react_agent",
                config=CircuitBreakerConfig(
                    failure_threshold=3,
                    recovery_timeout=30.0,
                    timeout=60.0,
                ),
            )
        except Exception as exc:
            logger.debug("[AutonomousReActAgent] CircuitBreaker unavailable: %s", exc)
    return _CIRCUIT_BREAKER


@register_agent("autonomous")
class AutonomousReActAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):
    # W4-032 (2026-05-23): Tier 6 cross-domain agent. ANY action via
    # this agent triggers HITL gate (highest risk surface).
    _HITL_ACTION_TYPES = frozenset({
        "autonomous_delegate",
        "autonomous_action",
        "cross_domain_action",
        "tier6_fallback_action",
    })

    """
    Agente ReAct autônomo cross-domain — Tier 6 do CascadedRouter.

    Herda de LangGraphReActBase (create_react_agent + PII masking + AuditCallback)
    e de EnhancedAgentMixin (memória de longa duração + FairnessGuard + learning).
    """

    DOMAIN_INSTRUCTIONS = PromptComposer.compose(
        agent_type="autonomous",
        domain_specific=(
        "Você foi acionada porque a solicitação cruza múltiplos domínios de recrutamento "
        "(vagas, sourcing, pipeline, analytics, agendamento) e nenhum agente especializado "
        "pôde resolver sozinho.\n\n"
        "## Suas responsabilidades:\n"
        "1. Entender a query cross-domain do usuário\n"
        "2. Usar as ferramentas disponíveis para coletar informações de diferentes domínios\n"
        "3. Consolidar o contexto com a tool `summarize_context`\n"
        "4. Fornecer uma resposta completa e integrada\n\n"
        "## Regras obrigatórias:\n"
        "- NUNCA invente dados — use apenas informações retornadas pelas tools\n"
        "- Se não encontrar dados suficientes, use `clarify_request` para pedir mais informações\n"
        "- Priorize leitura (read) antes de qualquer operação de escrita\n"
        "- Se a query for simples e coberta por um único domínio, responda diretamente\n\n"
        "## Formato da resposta:\n"
        "- Seja objetivo e direto\n"
        "- Inclua dados concretos retornados pelas tools (nomes, scores, contagens)\n"
        "- Para comparações, use ranking com justificativa clara"
    ),
    ).text

    def __init__(self) -> None:
        super().__init__()
        self._memory_service = WorkingMemoryService()
        self._all_tool_names = get_tool_names()
        self._max_steps = int(os.getenv("AUTONOMOUS_REACT_MAX_STEPS", "10"))
        self._setup_enhanced(domain="autonomous")
        logger.info(
            "[AutonomousReActAgent] Initialized — tools=%d max_steps=%d",
            len(self._all_tool_names),
            self._max_steps,
        )

    @property
    def domain_name(self) -> str:
        return "autonomous"

    @property
    def available_tools(self) -> list[str]:
        return list(self._all_tool_names)


    
    def _get_runtime_domain_instructions(self, input: "AgentInput") -> str:  # type: ignore[override]
        """Phase 3.4: runtime compliance injection for cross-domain autonomous agent.

        Falls back gracefully to static DOMAIN_INSTRUCTIONS if composition fails.
        """
        try:
            ctx = input.context or {}
            return self._compose_runtime_prompt(
                input,
                agent_type="autonomous",
                domain_specific=(
                    "Você foi acionada porque a solicitação cruza múltiplos domínios de "
                    "recrutamento (vagas, sourcing, pipeline, analytics, agendamento) e "
                    "nenhum agente especializado pôde resolver sozinho.\n\n"
                    "## Suas responsabilidades:\n"
                    "1. Entender a query cross-domain do usuário\n"
                    "2. Usar as ferramentas disponíveis para coletar informações de diferentes domínios\n"
                    "3. Consolidar o contexto com a tool `summarize_context`\n"
                    "4. Fornecer uma resposta completa e integrada\n\n"
                    "## Regras obrigatórias:\n"
                    "- NUNCA invente dados — use apenas informações retornadas pelas tools\n"
                    "- Se não encontrar dados suficientes, use `clarify_request` para pedir mais informações\n"
                    "- Priorize leitura (read) antes de qualquer operação de escrita\n"
                    "- Se a query for simples e coberta por um único domínio, responda diretamente\n\n"
                    "## Formato da resposta:\n"
                    "- Seja objetivo e direto\n"
                    "- Inclua dados concretos retornados pelas tools (nomes, scores, contagens)\n"
                    "- Para comparações, use ranking com justificativa clara"
                ),
                memory_summary=ctx.get("memory_summary", ""),
                stage_context=ctx.get("stage_context", ""),
            ).text
        except Exception as exc:
            logger.warning(
                "[autonomous] runtime prompt composition failed: %s — "
                "falling back to static DOMAIN_INSTRUCTIONS",
                exc,
            )
            return self.DOMAIN_INSTRUCTIONS

    def _get_tool_contracts(self) -> list:
        """Ativa GovernanceToolNode para este agente."""
        try:
            from app.domains.autonomous.agents.autonomous_tool_registry import get_autonomous_tools
            return get_autonomous_tools()
        except ImportError:
            return []

    def _get_tools(self) -> list:
        """Retorna o pool completo de tools cross-domain + enhanced tools.

        Wraps every tool function with a tenant-isolation injector that reads the
        company_id from the current context variable and injects it if the caller
        did not already provide it.  This ensures the LLM cannot omit company_id
        and accidentally expose cross-tenant records (IDOR prevention).
        """
        from lia_agents_core.tool_adapter import tool_definition_to_langchain_tool
        from dataclasses import replace as dataclass_replace
        from app.domains.autonomous.agents.autonomous_tool_registry import TOOL_PERMISSION_SCOPE

        raw_defs = get_autonomous_tools() + self._get_all_enhanced_tools()
        wrapped_defs = []
        for td in raw_defs:
            original_fn = td.function
            _is_write_tool = TOOL_PERMISSION_SCOPE.get(td.name, "read") == "write"

            @functools.wraps(original_fn)
            async def _tenant_safe_wrapper(
                *args: Any,
                _fn=original_fn,
                _write=_is_write_tool,
                **kwargs: Any,
            ) -> Any:
                # 1. Enforce server-side tenant scope — model cannot override (IDOR prevention).
                request_company_id = _CURRENT_COMPANY_ID.get("")
                if request_company_id:
                    kwargs["company_id"] = request_company_id
                else:
                    # No request context — remove any model-supplied value to fail closed.
                    kwargs.pop("company_id", None)

                # 2. Write guard — write-scoped tools require explicit confirmation.
                if _write and not kwargs.get("confirm"):
                    return {
                        "success": False,
                        "data": {},
                        "message": (
                            "Operação de escrita bloqueada: forneça confirm=True para executar "
                            "esta ação. Confirme explicitamente antes de prosseguir."
                        ),
                    }

                return await _fn(*args, **kwargs)

            try:
                # ToolDefinition is a Pydantic BaseModel — must use model_copy()
                wrapped_td = td.model_copy(update={"function": _tenant_safe_wrapper})
            except AttributeError:
                # Fallback for non-Pydantic ToolDefinition implementations
                try:
                    wrapped_td = dataclass_replace(td, function=_tenant_safe_wrapper)
                except Exception:
                    wrapped_td = td
            wrapped_defs.append(wrapped_td)

        return [tool_definition_to_langchain_tool(td) for td in wrapped_defs]

    async def _run_graph(
        self,
        initial_state: dict,
        session_id: str,
        audit_callback: Any | None = None,
        streaming_callback: Any | None = None,
        conversation_id: str | None = None,
    ) -> dict:
        """Override: aplica recursion_limit (budget máximo) no run config do LangGraph."""
        compiled = self._get_compiled_graph()
        if compiled is None:
            raise RuntimeError("[AutonomousReActAgent] Grafo LangGraph não disponível")

        config: dict[str, Any] = {
            "configurable": {"thread_id": session_id},
            "recursion_limit": self._max_steps * 2 + 1,
        }
        callbacks = [cb for cb in [audit_callback, streaming_callback] if cb is not None]
        if callbacks:
            config["callbacks"] = callbacks

        result = await compiled.ainvoke(initial_state, config=config)
        return result

    # _get_system_prompt is now inherited from LangGraphReActBase.
    # It uses SystemPromptBuilder.build() + DOMAIN_INSTRUCTIONS automatically.

    async def _process_langgraph(self, input: AgentInput) -> AgentOutput:
        """P36 Full: 3-layer intelligence for cross-domain safety net.

        Injects ALL domain insights (not just one) since this agent
        handles queries spanning multiple domains.
        """
        try:
            weights = await self.load_calibration_weights(str(input.company_id or ""), input.context.get("job_id"))
            if weights and weights != self._DEFAULT_WEIGHTS:
                input.context["calibration_weights"] = weights
        except Exception:
            pass
        try:
            from app.shared.services.global_insights_service import get_global_insights
            svc = get_global_insights()
            snippet = svc.format_autonomous_for_prompt(await svc.get_autonomous_insights())
            if snippet:
                existing = input.context.get("extra_instructions", "")
                input.context["extra_instructions"] = f"{existing}\n\n{snippet}" if existing else snippet
        except Exception:
            pass
        try:
            from app.domains.analytics.services.recruiter_personalization_service import get_recruiter_prompt_context
            ctx = await get_recruiter_prompt_context(str(input.user_id or ""), str(input.company_id or ""))
            if ctx:
                input.context["recruiter_context"] = ctx
        except Exception:
            pass
        return await super()._process_langgraph(input)

    def _state_to_output(self, state: dict, input: AgentInput) -> AgentOutput:
        """Converte estado final LangGraph em AgentOutput com detecção de clarificação."""
        messages = state.get("messages", [])
        response = ""

        for m in reversed(messages):
            content = getattr(m, "content", None) or (
                m.get("content", "") if isinstance(m, dict) else ""
            )
            if content and not getattr(m, "tool_call_id", None) and not (
                isinstance(m, dict) and m.get("tool_call_id")
            ):
                response = self._extract_text_content(content)
                break

        if not response:
            response = (
                "Não consegui resolver sua solicitação com as informações disponíveis. "
                "Poderia fornecer mais detalhes para que eu possa ajudá-lo melhor?"
            )

        actions = []
        for m in messages:
            for tc in (getattr(m, "tool_calls", None) or []):
                name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
                actions.append(AgentAction(action_type="call_tool", params={"tool": name}))

        needs_clarification = "clarify_request" in [
            a.params.get("tool", "") for a in actions
        ]

        return AgentOutput(
            message=response,
            actions=actions,
            confidence=0.75 if not needs_clarification else 0.0,
            metadata={
                "source": "autonomous_react_agent",
                "domain": self.domain_name,
                "tool_calls": len(actions),
                "needs_clarification": needs_clarification,
                "tier": 6,
            },
        )

    async def process(self, input: AgentInput) -> AgentOutput:
        """
        Processa a query cross-domain via LangGraph ReAct.

        1. FairnessGuard check (SEG-2)
        2. Circuit breaker (fail-safe)
        3. LangGraph nativo via _process_langgraph (herdado)
        4. AuditService log (SEG-5)
        """
        _soft_warnings: list[str] = []

        # ── FairnessGuard (SEG-2) ────────────────────────────────────────────
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            _fg = FairnessGuard()
            _fg_result = _fg.check(input.message)
            if _fg_result.is_blocked:
                logger.warning(
                    "[AutonomousReActAgent][SEG-2] FairnessGuard blocked: user=%s",
                    input.user_id,
                )
                return AgentOutput(
                    message=_fg_result.educational_message or (
                        "Não posso processar essa solicitação pois viola critérios de equidade."
                    ),
                    confidence=1.0,
                    metadata={"blocked": True, "reason": "fairness_guard", "tier": 6},
                )
            _soft_warnings = list(getattr(_fg_result, "soft_warnings", None) or [])
        except Exception as _fg_exc:
            logger.debug("[AutonomousReActAgent] FairnessGuard skipped: %s", _fg_exc)

        # ── W4-032 (2026-05-23) HITL gate cross-domain Tier 6 ──────────────
        from app.shared.hitl.agent_gate import maybe_request_hitl_approval
        _hitl_response = await maybe_request_hitl_approval(
            agent_input=input,
            domain=self.domain_name,
            action_types=self._HITL_ACTION_TYPES,
            agent_name="autonomous_react_agent",
            description_template=(
                "Confirmar **{action_type}** via agent autônomo (Tier 6). "
                "Maior superfície de ação cross-domain — exige revisão humana."
            ),
        )
        if _hitl_response is not None:
            return _hitl_response

        # ── Set tenant context variable so tools auto-inject company_id ─────
        # ADR-029-EXEMPT (audit Wave 2 2026-05-21): runtime-scope ContextVar set por
        # autonomous_react_agent.process(). JWT verificado upstream via middleware
        # auth_enforcement; runtime re-set garante company_id correto em contexto
        # não-HTTP (agent-to-agent invoke). Scope reset em finally do _process_langgraph.
        _token = _CURRENT_COMPANY_ID.set(str(input.company_id or ""))
        try:
            output = await self._execute_with_circuit_breaker(input)
        finally:
            # Always reset — even if early-return paths inside raise
            _CURRENT_COMPANY_ID.reset(_token)

        if _soft_warnings:
            existing = output.metadata or {}
            existing["fairness_warnings"] = _soft_warnings
            output.metadata = existing

        # ── AuditService (SEG-5) ─────────────────────────────────────────────
        try:
            from app.shared.compliance.audit_service import PROTECTED_CRITERIA, audit_service
            tool_calls = [a.params.get("tool", "") for a in (output.actions or [])]
            await audit_service.log_decision(
                company_id=str(input.company_id or ""),
                agent_name="autonomous_react_agent",
                decision_type="cross_domain_query",
                action="autonomous_langgraph:tier6",
                decision="completed",
                reasoning=[f"Cross-domain ReAct via {len(tool_calls)} tool calls"],
                criteria_used=tool_calls[:10],
                criteria_ignored=list(PROTECTED_CRITERIA),
                confidence=output.confidence,
            )
        except Exception as _audit_exc:
            logger.debug("[AutonomousReActAgent][SEG-5] AuditService skipped: %s", _audit_exc)

        return output

    async def _execute_with_circuit_breaker(self, input: AgentInput) -> AgentOutput:
        """Execute _process_langgraph wrapped by the circuit breaker.

        Returns AgentOutput with:
          - confidence=0, needs_clarification=True  → budget exhausted
          - confidence=0, circuit_open=True         → circuit breaker tripped
          - confidence from LangGraph result        → normal success
        """
        _cb = _get_circuit_breaker()

        async def _run_langgraph() -> AgentOutput:
            return await self._process_langgraph(input)

        _budget_err_msg = (
            "Não consegui resolver sua solicitação dentro do número máximo de passos. "
            "Pode dividir sua pergunta em partes menores ou ser mais específico?"
        )
        _generic_err_msg = (
            "Ocorreu um erro ao processar sua solicitação cross-domain. "
            "Tente reformular ou divida em perguntas menores."
        )

        def _is_recursion_err(exc: Exception) -> bool:
            _s = str(exc)
            return "recursion" in _s.lower() or "GraphRecursionError" in _s

        if _cb is not None:
            try:
                from app.shared.resilience.circuit_breaker import CircuitBreakerError
                return await _cb.call(_run_langgraph)
            except CircuitBreakerError:
                logger.warning("[AutonomousReActAgent] Circuit breaker OPEN — fallback")
                return AgentOutput(
                    message=(
                        "O agente autônomo está temporariamente indisponível. "
                        "Tente novamente em instantes ou reformule sua pergunta."
                    ),
                    confidence=0.0,
                    metadata={"circuit_open": True, "tier": 6, "needs_clarification": False},
                )
            except Exception as exc:
                if _is_recursion_err(exc):
                    logger.warning(
                        "[AutonomousReActAgent] Step budget exceeded (max_steps=%d)", self._max_steps
                    )
                    return AgentOutput(
                        message=_budget_err_msg,
                        confidence=0.0,
                        metadata={"budget_exhausted": True, "needs_clarification": True, "tier": 6},
                    )
                logger.error("[AutonomousReActAgent] LangGraph error: %s", exc, exc_info=True)
                return AgentOutput(
                    message=_generic_err_msg,
                    confidence=0.0,
                    metadata={"error": str(exc), "tier": 6},
                )
        else:
            # Circuit breaker unavailable — run directly
            try:
                return await _run_langgraph()
            except Exception as exc:
                if _is_recursion_err(exc):
                    logger.warning(
                        "[AutonomousReActAgent] Step budget exceeded (max_steps=%d)", self._max_steps
                    )
                    return AgentOutput(
                        message=_budget_err_msg,
                        confidence=0.0,
                        metadata={"budget_exhausted": True, "needs_clarification": True, "tier": 6},
                    )
                logger.error("[AutonomousReActAgent] LangGraph error: %s", exc, exc_info=True)
                return AgentOutput(
                    message=_generic_err_msg,
                    confidence=0.0,
                    metadata={"error": str(exc), "tier": 6},
                )


# ---------------------------------------------------------------------------
# Singleton para uso no CascadedRouter
# ---------------------------------------------------------------------------

_autonomous_agent: AutonomousReActAgent | None = None


def get_autonomous_react_agent() -> AutonomousReActAgent:
    """Return singleton instance of AutonomousReActAgent."""
    global _autonomous_agent
    if _autonomous_agent is None:
        _autonomous_agent = AutonomousReActAgent()
    return _autonomous_agent
