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

# Context variable to carry company_id into tool function calls
_CURRENT_COMPANY_ID: contextvars.ContextVar[str] = contextvars.ContextVar(
    "autonomous_agent_company_id", default=""
)

from lia_agents_core.agent_interface import AgentInput, AgentOutput, AgentAction
from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
from lia_agents_core.langgraph_react_base import LangGraphReActBase
from lia_agents_core.working_memory import WorkingMemoryService

from app.domains.autonomous.agents.autonomous_tool_registry import (
    get_autonomous_tools,
    get_tool_names,
)

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


_AUTONOMOUS_SYSTEM_PROMPT = """Você é LIA, assistente autônoma de recrutamento com acesso cross-domain.

Você foi acionada porque a solicitação do usuário cruza múltiplos domínios de recrutamento
(ex: vagas, sourcing, pipeline, analytics, agendamento) e nenhum agente especializado
pôde resolver sozinho.

## Suas responsabilidades:
1. Entender a query cross-domain do usuário
2. Usar as ferramentas disponíveis para coletar informações de diferentes domínios
3. Consolidar o contexto com a tool `summarize_context`
4. Fornecer uma resposta completa e integrada

## Regras obrigatórias:
- NUNCA invente dados — use apenas informações retornadas pelas tools
- Se não encontrar dados suficientes, use `clarify_request` para pedir mais informações
- Priorize leitura (read) antes de qualquer operação de escrita
- Respeite critérios de equidade: não faça inferências sobre gênero, etnia, idade
- Todos os dados pessoais são mascarados automaticamente (PII masking ativo)
- Se a query for simples e coberta por um único domínio, responda diretamente

## Formato da resposta:
- Seja objetivo e direto
- Inclua dados concretos retornados pelas tools (nomes, scores, contagens)
- Para comparações, use ranking com justificativa clara
- Em português do Brasil

{context_snippet}
"""


class AutonomousReActAgent(LangGraphReActBase, EnhancedAgentMixin):
    """
    Agente ReAct autônomo cross-domain — Tier 6 do CascadedRouter.

    Herda de LangGraphReActBase (create_react_agent + PII masking + AuditCallback)
    e de EnhancedAgentMixin (memória de longa duração + FairnessGuard + learning).
    """

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

    def _get_tools(self) -> list:
        """Retorna o pool completo de tools cross-domain + enhanced tools.

        Wraps every tool function with a tenant-isolation injector that reads the
        company_id from the current context variable and injects it if the caller
        did not already provide it.  This ensures the LLM cannot omit company_id
        and accidentally expose cross-tenant records (IDOR prevention).
        """
        from lia_agents_core.react_loop import tool_definition_to_langchain_tool
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

    def _get_system_prompt(self, input: AgentInput) -> str:
        context_snippet = ""
        if input.context:
            tenant_snippet = input.context.get("tenant_context_snippet", "")
            job_context = input.context.get("job_context", {})
            if tenant_snippet:
                context_snippet += f"\n## Contexto do cliente:\n{tenant_snippet}"
            if job_context:
                context_snippet += f"\n## Contexto da vaga:\n{job_context}"
        return _AUTONOMOUS_SYSTEM_PROMPT.format(context_snippet=context_snippet)

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

        # ── Set tenant context variable so tools auto-inject company_id ─────
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
