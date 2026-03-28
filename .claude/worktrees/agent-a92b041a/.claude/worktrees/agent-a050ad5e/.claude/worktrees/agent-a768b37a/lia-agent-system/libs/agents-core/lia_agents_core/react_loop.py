"""
ReAct Loop - Reason -> Act -> Observe -> Decide

This is the core intelligence loop that makes agents truly autonomous.
Instead of following a fixed pipeline, the agent:
1. REASONS about the current situation (what do I know? what should I do?)
2. ACTS by calling a tool or generating a response
3. OBSERVES the result of the action
4. DECIDES whether to continue acting or respond to the user

The loop is configurable per domain (max iterations, available tools, prompt).

NOTE (Phase 2 → Phase 3 migration):
  This is the current production implementation (Phase 2 — custom ReAct loop).
  Phase 3 will migrate agents incrementally to LangGraph native `create_react_agent`
  with `PostgresSaver` checkpoints (see `langgraph_react_base.py`).
  Migration is opt-in per domain via `USE_LANGGRAPH_NATIVE` feature flag.
  Do NOT remove this module until all agents have been migrated and validated.
"""
import json
import logging
import time
from typing import Any, Callable, Dict, List, Literal, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

try:
    from langsmith import traceable as _traceable
except ImportError:
    def _traceable(**kwargs):  # type: ignore[misc]
        def decorator(fn):
            return fn
        return decorator

try:
    from app.observability.metrics import agent_iterations_total
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False

from lia_config.config import settings
from app.services.llm import llm_service
from lia_agents_core.working_memory import WorkingMemoryService

if TYPE_CHECKING:
    from lia_agents_core.observability import ReActObserver

logger = logging.getLogger(__name__)

# P2-A — Circuit breaker para chamadas LLM no _reason()
# Singleton por módulo: compartilhado entre instâncias do ReActLoop.
# failure_threshold=3: abre após 3 falhas consecutivas (timeouts, 5xx, etc.)
# recovery_timeout=60s: tenta recuperação após 1 minuto
_llm_circuit_breaker = None


def _get_llm_circuit_breaker():
    """Lazy init do circuit breaker LLM — evita erro de import circular."""
    global _llm_circuit_breaker
    if _llm_circuit_breaker is None:
        try:
            from app.shared.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
            _llm_circuit_breaker = CircuitBreaker(
                name="llm_react_reason",
                config=CircuitBreakerConfig(
                    failure_threshold=3,
                    recovery_timeout=60.0,
                    success_threshold=2,
                    timeout=30.0,
                ),
            )
            logger.info("[ReActLoop] LLM circuit breaker initialized (threshold=3, recovery=60s)")
        except Exception as _cb_exc:
            logger.warning("[ReActLoop] Circuit breaker unavailable (fail-open): %s", _cb_exc)
    return _llm_circuit_breaker


class ToolDefinition(BaseModel):
    """Schema for a tool that the ReAct loop can call."""

    name: str = Field(..., description="Unique name of the tool")
    description: str = Field(..., description="What the tool does")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema describing the tool parameters",
    )
    function: Callable = Field(
        ...,
        description="Async function to execute when the tool is called",
    )

    class Config:
        arbitrary_types_allowed = True


class ReActConfig(BaseModel):
    """Configuration for a ReAct loop instance."""

    max_iterations: int = Field(
        default_factory=lambda: settings.REACT_MAX_ITERATIONS_DEFAULT,
        description="Maximum number of reason-act-observe cycles before forcing a response",
    )
    system_prompt: str = Field(
        ...,
        description="System prompt that defines the agent personality and instructions",
    )
    available_tools: List[ToolDefinition] = Field(
        default_factory=list,
        description="Tools the agent can call during reasoning",
    )
    domain: str = Field(
        ...,
        description="The domain this loop operates in (e.g. wizard, pipeline)",
    )
    model_provider: Literal["claude", "openai", "gemini"] = Field(
        default="claude",
        description="LLM provider to use (claude, gemini, openai)",
    )
    model_name: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model name for reference/logging",
    )
    temperature: float = Field(
        default=0.3,
        description="Temperature for LLM generation",
    )
    guardrails: List[str] = Field(
        default_factory=list,
        description="Action types that require user confirmation before execution",
    )
    extra_context: str = Field(
        default="",
        description="Additional context to inject into the system prompt (e.g., long-term memories)",
    )
    max_tokens_per_session: Optional[int] = Field(
        default=None,
        description="Hard token budget per session (estimated via chars/4). None = unlimited.",
    )
    # AuditCallback injetado pelo agente — captura toda a execução automaticamente
    audit_callback: Optional[Any] = Field(
        default=None,
        description="AuditCallback instance for full execution tracing (LangGraph/manual).",
    )

    class Config:
        arbitrary_types_allowed = True


class ReActState(BaseModel):
    """State maintained throughout a single ReAct loop execution."""

    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Conversation messages accumulated during the loop",
    )
    current_reasoning: str = Field(
        default="",
        description="The agent's current chain of thought",
    )
    actions_taken: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Actions the agent has performed so far",
    )
    observations: List[str] = Field(
        default_factory=list,
        description="Observations from tool results and environment",
    )
    should_respond: bool = Field(
        default=False,
        description="Whether the agent has decided it is ready to respond",
    )
    final_response: Optional[str] = Field(
        default=None,
        description="The final response to return to the user",
    )
    iteration: int = Field(
        default=0,
        description="Current iteration number in the loop",
    )
    tool_calls_made: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Record of all tool calls made during this execution",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if something went wrong during execution",
    )
    failed_tool_calls: List[str] = Field(
        default_factory=list,
        description="Serialised keys of tool calls that returned success=False",
    )
    consecutive_duplicate_count: int = Field(
        default=0,
        description="Counter for consecutive identical tool call attempts",
    )
    last_tool_call_key: Optional[str] = Field(
        default=None,
        description="Serialised key of the previous tool call for duplicate detection",
    )
    tokens_used_estimate: int = Field(
        default=0,
        description="Running rough token estimate (chars/4) across all LLM calls this session",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session identifier for multi-tenant context propagation",
    )


class ReActLoop:
    """Reusable Reason-Act-Observe loop for autonomous agent behaviour.

    Each domain agent can instantiate a ReActLoop with its own configuration
    (system prompt, tools, guardrails) and call ``run()`` to process a user
    message through the full reasoning cycle.
    """

    def __init__(
        self,
        config: ReActConfig,
        working_memory_service: WorkingMemoryService,
    ):
        """Initialise the ReAct loop.

        Args:
            config: Loop configuration including prompt, tools, and limits.
            working_memory_service: Service for reading/writing persistent agent state.
        """
        self.config = config
        self.working_memory = working_memory_service
        self._tool_map: Dict[str, ToolDefinition] = {
            tool.name: tool for tool in config.available_tools
        }

    @_traceable(name="ReAct Loop", run_type="chain")
    async def run(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: str,
        observer: Optional["ReActObserver"] = None,
    ) -> ReActState:
        """Execute the full ReAct loop for a user message.

        Args:
            message: The user message to process.
            context: Domain-specific context (job draft, pipeline state, etc.).
            session_id: Session identifier for working memory lookup.

        Returns:
            The final ReActState after the loop completes.
        """
        loop_start = time.time()
        state = ReActState(
            messages=[{"role": "user", "content": message}],
        )

        # Alias curto — usado em todo o método para guardar chamadas de auditoria
        _audit = self.config.audit_callback
        if _audit:
            _audit.on_chain_start_manual()

        logger.info(
            f"[{self.config.domain}] Starting ReAct loop for session={session_id} "
            f"max_iterations={self.config.max_iterations}"
        )

        await self.working_memory.increment_iteration(session_id, self.config.domain)

        token_budget = self.config.max_tokens_per_session
        if token_budget is None and settings.REACT_TOKEN_BUDGET_ENABLED:
            token_budget = settings.REACT_TOKEN_BUDGET_DEFAULT

        # Pre-call budget check: verifica limites reais de token/custo antes de
        # iniciar o loop LLM. Protege contra estouros não detectados em sessões longas.
        # Fail-safe: se o serviço estiver indisponível, o loop prossegue normalmente.
        if settings.REACT_TOKEN_BUDGET_ENABLED:
            _user_id = str(context.get("user_id", "system"))
            _company_id = str(context.get("company_id", ""))
            if _company_id:
                try:
                    from app.services.token_tracking_service import token_tracking_service
                    _within_limits, _limit_reason = await token_tracking_service.check_limits(
                        user_id=_user_id,
                        company_id=_company_id,
                    )
                    if not _within_limits:
                        logger.warning(
                            f"[{self.config.domain}] Budget limit exceeded "
                            f"company={_company_id}: {_limit_reason}"
                        )
                        state.final_response = (
                            f"Limite de uso atingido: {_limit_reason}. "
                            "Entre em contato com o administrador para aumentar os limites."
                        )
                        state.should_respond = True
                        return state
                except Exception as _budget_exc:
                    logger.debug(
                        f"[{self.config.domain}] Budget pre-check skipped: {_budget_exc}"
                    )

        try:
            while state.iteration < self.config.max_iterations:
                # Token budget guard
                if token_budget and state.tokens_used_estimate >= token_budget:
                    logger.warning(
                        f"[{self.config.domain}] Token budget exhausted "
                        f"({state.tokens_used_estimate}/{token_budget}), forcing response"
                    )
                    state.observations.append(
                        f"Token budget ({token_budget}) reached. Generating final response."
                    )
                    state.final_response = await self._generate_response(state, context)
                    state.should_respond = True
                    break

                state.iteration += 1
                iter_start = time.time()
                logger.info(
                    f"[{self.config.domain}] Iteration {state.iteration}/{self.config.max_iterations}"
                )

                if observer:
                    observer.start_iteration(state.iteration)

                _reason_start = time.time()
                reasoning = await self._reason(state, context)
                _reason_latency = (time.time() - _reason_start) * 1000
                state.current_reasoning = reasoning

                if _audit:
                    _audit.on_llm_call(
                        prompt_preview=message[:500],
                        response_preview=reasoning[:500],
                        latency_ms=_reason_latency,
                        model=self.config.model_name,
                        prompt_full=message,
                        reasoning_full=reasoning,
                    )

                if observer:
                    observer.log_reasoning(state.iteration, reasoning)

                try:
                    parsed = self._parse_reasoning(reasoning)
                except Exception as parse_err:
                    logger.warning(
                        f"[{self.config.domain}] Failed to parse reasoning output: {parse_err}"
                    )
                    parsed = {
                        "thought": reasoning,
                        "action": "respond",
                        "response": reasoning,
                    }

                thought = parsed.get("thought", "")
                action = parsed.get("action", "respond")
                logger.info(
                    f"[{self.config.domain}] Thought: {thought[:120]}... | Action: {action}"
                )

                if action == "respond":
                    response_text = parsed.get("response", "")
                    if not response_text:
                        response_text = await self._generate_response(state, context)
                    state.final_response = response_text
                    state.should_respond = True
                    iter_duration = (time.time() - iter_start) * 1000
                    logger.info(
                        f"[{self.config.domain}] Responding after iteration "
                        f"{state.iteration} ({iter_duration:.1f}ms)"
                    )
                    if _METRICS_AVAILABLE:
                        agent_iterations_total.labels(domain=self.config.domain, action_type="respond").inc()
                    if observer:
                        observer.log_decision(state.iteration, "respond")
                    break

                if action == "ask_clarification":
                    state.final_response = parsed.get("response", thought)
                    state.should_respond = True
                    if observer:
                        observer.log_decision(state.iteration, "respond")
                    break

                if action == "call_tool":
                    tool_name = parsed.get("tool_name")
                    _raw_args = parsed.get("tool_args")
                    tool_args = _raw_args if isinstance(_raw_args, dict) else {}

                    if not tool_name or tool_name not in self._tool_map:
                        observation = (
                            f"Tool '{tool_name}' is not available. "
                            f"Available tools: {list(self._tool_map.keys())}"
                        )
                        state.observations.append(observation)
                        logger.warning(
                            f"[{self.config.domain}] Unknown tool requested: {tool_name}"
                        )
                        continue

                    call_key = json.dumps(
                        {"tool": tool_name, "args": tool_args},
                        sort_keys=True,
                        default=str,
                    )

                    if call_key in state.failed_tool_calls:
                        observation = (
                            f"Tool '{tool_name}' already failed with these parameters. "
                            f"Try different parameters or a different approach."
                        )
                        state.observations.append(observation)
                        logger.warning(
                            f"[{self.config.domain}] Skipping previously failed tool call: {tool_name}"
                        )
                        continue

                    if call_key == state.last_tool_call_key:
                        state.consecutive_duplicate_count += 1
                    else:
                        state.consecutive_duplicate_count = 0
                    state.last_tool_call_key = call_key

                    if state.consecutive_duplicate_count >= settings.REACT_DUPLICATE_THRESHOLD:
                        logger.warning(
                            f"[{self.config.domain}] Same tool call repeated {state.consecutive_duplicate_count + 1} "
                            f"times in a row, breaking loop"
                        )
                        state.observations.append(
                            f"Tool '{tool_name}' was called multiple times with the same "
                            f"parameters without progress. Generating a response instead."
                        )
                        state.final_response = await self._generate_response(state, context)
                        state.should_respond = True
                        break

                    if tool_name in self.config.guardrails:
                        state.actions_taken.append(
                            {
                                "type": "guardrail_blocked",
                                "tool": tool_name,
                                "args": tool_args,
                                "reason": "Requires user confirmation",
                            }
                        )
                        state.final_response = (
                            f"I need your confirmation before executing '{tool_name}'. "
                            f"Shall I proceed?"
                        )
                        state.should_respond = True
                        break

                    # Inject ambient context values into tool_args so tool functions
                    # receive multi-tenancy fields without the LLM needing to generate them.
                    if context.get("company_id") and "company_id" not in tool_args:
                        tool_args["company_id"] = context["company_id"]
                    if context.get("vacancy_id") and "vacancy_id" not in tool_args:
                        tool_args["vacancy_id"] = context["vacancy_id"]

                    tool_start = time.time()
                    tool_result = await self._act(state, {"tool_name": tool_name, "tool_args": tool_args})
                    tool_duration = (time.time() - tool_start) * 1000

                    tool_success = tool_result.get("success", False)
                    if _METRICS_AVAILABLE:
                        agent_iterations_total.labels(domain=self.config.domain, action_type="call_tool").inc()
                    if not tool_success:
                        state.failed_tool_calls.append(call_key)

                    if _audit:
                        _audit.on_tool_call(
                            tool_name=tool_name,
                            input_preview=str(tool_args)[:500],
                            output_preview=str(tool_result)[:500],
                            latency_ms=tool_duration,
                            success=tool_success,
                            error=tool_result.get("error"),
                        )

                    if observer:
                        observer.log_tool_call(
                            iteration=state.iteration,
                            tool_name=tool_name,
                            tool_args=tool_args,
                            success=tool_success,
                            duration_ms=tool_duration,
                        )

                    observation = await self._observe(state, tool_result)
                    state.observations.append(observation)

                    if await self._should_respond(state):
                        state.final_response = await self._generate_response(state, context)
                        state.should_respond = True
                        iter_duration = (time.time() - iter_start) * 1000
                        logger.info(
                            f"[{self.config.domain}] Decided to respond after tool call "
                            f"({iter_duration:.1f}ms)"
                        )
                        if observer:
                            observer.log_decision(state.iteration, "respond")
                        break
                    else:
                        if observer:
                            observer.log_decision(state.iteration, "continue")
                else:
                    logger.warning(
                        f"[{self.config.domain}] Unknown action type: {action}, forcing respond"
                    )
                    state.final_response = await self._generate_response(state, context)
                    state.should_respond = True
                    if observer:
                        observer.log_decision(state.iteration, "error")
                    break

            if not state.should_respond:
                logger.warning(
                    f"[{self.config.domain}] Max iterations reached, forcing response generation"
                )
                state.observations.append(
                    f"Maximum iterations ({self.config.max_iterations}) reached. "
                    f"Summarising what was accomplished so far."
                )
                try:
                    state.final_response = await self._generate_response(state, context)
                except Exception as gen_exc:
                    logger.error(
                        f"[{self.config.domain}] Fallback response generation failed: {gen_exc}"
                    )
                    state.final_response = None

                if not state.final_response or not state.final_response.strip():
                    fallback_parts = [
                        "Desculpe, não consegui concluir o processamento completo da sua solicitação."
                    ]
                    if state.observations:
                        fallback_parts.append(
                            "Aqui está o que consegui reunir até agora:"
                        )
                        for obs in state.observations[-3:]:
                            fallback_parts.append(f"- {obs[:200]}")
                    fallback_parts.append(
                        "Por favor, tente reformular ou fornecer mais detalhes."
                    )
                    state.final_response = "\n".join(fallback_parts)

                state.should_respond = True

        except Exception as exc:
            # P2-A: tratamento específico para circuit breaker aberto
            try:
                from app.shared.resilience.circuit_breaker import CircuitBreakerError as _CBError
                if isinstance(exc, _CBError):
                    logger.warning(
                        "[%s] LLM circuit breaker OPEN — respondendo com fallback amigável. "
                        "retry_after=%.1fs",
                        self.config.domain, exc.retry_after,
                    )
                    state.error = "circuit_breaker_open"
                    state.final_response = (
                        "O serviço de IA está temporariamente indisponível devido a instabilidade. "
                        f"Tente novamente em aproximadamente {int(exc.retry_after)} segundos. "
                        "Se o problema persistir, entre em contato com o suporte."
                    )
                    state.should_respond = True
                    return state
            except ImportError:
                pass  # CircuitBreakerError não disponível — cai no handler genérico

            logger.error(
                f"[{self.config.domain}] ReAct loop error: {exc}",
                exc_info=True,
            )
            state.error = str(exc)
            if not state.final_response:
                state.final_response = (
                    "I encountered an error while processing your request. "
                    "Please try again."
                )
            state.should_respond = True

            # Alerta de saúde: registra falha consecutiva (best-effort, não propaga)
            try:
                from app.services.agent_health_alert_service import agent_health_alert_service
                await agent_health_alert_service.record_failure(
                    company_id=context.get("company_id", ""),
                    agent_id=self.config.domain,
                    error=str(exc),
                    notify_user_id=context.get("user_id"),
                )
            except Exception as _health_exc:
                logger.debug("[%s] agent_health_alert skipped: %s", self.config.domain, _health_exc)

        total_duration = (time.time() - loop_start) * 1000
        logger.info(
            f"[{self.config.domain}] ReAct loop completed in {total_duration:.1f}ms "
            f"iterations={state.iteration} tools_called={len(state.tool_calls_made)} "
            f"tokens_est={state.tokens_used_estimate}"
        )

        # Alerta de saúde: reset do contador em caso de sucesso (best-effort)
        if not state.error:
            try:
                from app.services.agent_health_alert_service import agent_health_alert_service
                await agent_health_alert_service.record_success(
                    company_id=context.get("company_id", ""),
                    agent_id=self.config.domain,
                )
            except Exception as _health_exc:
                logger.debug("[%s] agent_health_alert success skipped: %s", self.config.domain, _health_exc)

        # Best-effort async token recording (fire-and-forget)
        user_id = context.get("user_id", "system")
        company_id = context.get("company_id", "")
        if company_id and settings.REACT_TOKEN_BUDGET_ENABLED:
            try:
                from app.services.token_tracking_service import token_tracking_service
                await token_tracking_service.record_usage(
                    user_id=str(user_id),
                    company_id=str(company_id),
                    agent_type=self.config.domain,
                    intent="react_loop",
                    input_tokens=state.tokens_used_estimate // 2,
                    output_tokens=state.tokens_used_estimate // 2,
                    model=self.config.model_name,
                    latency_ms=total_duration,
                )
            except Exception as track_exc:
                logger.debug(f"[{self.config.domain}] Token tracking skipped: {track_exc}")

        # --- Audit: persistir execução completa ---
        if _audit:
            try:
                _audit_success = not bool(state.error)
                _audit_confidence = 0.9 if _audit_success and state.final_response else 0.3
                await _audit.on_chain_end_manual(
                    confidence=_audit_confidence,
                    success=_audit_success,
                    error=state.error,
                )
            except Exception as _audit_exc:
                logger.debug(f"[{self.config.domain}] Audit persist skipped: {_audit_exc}")

        return state

    async def _reason(self, state: ReActState, context: Dict[str, Any]) -> str:
        """Call the LLM to reason about what to do next.

        Constructs a prompt from the system prompt, context, conversation
        history, and any previous observations, then asks the LLM to decide
        on the next action.

        Args:
            state: Current loop state.
            context: Domain-specific context.

        Returns:
            Raw LLM response string (expected to be JSON).
        """
        step_start = time.time()

        tools_description = ""
        if self._tool_map:
            tool_lines = []
            for tool in self.config.available_tools:
                params_str = json.dumps(tool.parameters, ensure_ascii=False) if tool.parameters else "{}"
                tool_lines.append(
                    f"- {tool.name}: {tool.description} | Parameters: {params_str}"
                )
            tools_description = "Available Tools:\n" + "\n".join(tool_lines)

        history_text = ""
        if state.messages:
            history_lines = []
            for msg in state.messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_lines.append(f"[{role}]: {content}")
            history_text = "\n".join(history_lines)

        observations_text = ""
        if state.observations:
            observations_text = "Previous Observations:\n" + "\n".join(
                f"- {obs}" for obs in state.observations
            )

        context_text = json.dumps(context, ensure_ascii=False, default=str) if context else "{}"

        prompt = f"""{self.config.system_prompt}

{self.config.extra_context}

{tools_description}

Current Context:
{context_text}

Conversation:
{history_text}

{observations_text}

Iteration: {state.iteration}

Based on the above, decide what to do next.

IMPORTANT - Strategic Thinking Guidelines:
- In your "thought" field, think DEEPLY: analyze trade-offs, cross-reference data, consider risks
- When you have data from tools, INTERPRET it consultively - explain what the numbers MEAN
- Consider proactive insights: are there risks or opportunities the user hasn't asked about?
- If this is the first interaction about a topic, consider using analytical tools proactively

Respond with a JSON object:
{{
    "thought": "your deep strategic reasoning - analyze multi-factor trade-offs, risks, and opportunities",
    "action": "call_tool" | "respond" | "ask_clarification",
    "tool_name": "name of tool to call (null if not calling a tool)",
    "tool_args": {{}},
    "response": "your response text (null if calling a tool)"
}}

Respond ONLY with the JSON object, no extra text."""

        # P2-A: circuit breaker protege a chamada LLM
        _cb = _get_llm_circuit_breaker()
        if _cb is not None:
            try:
                from app.shared.resilience.circuit_breaker import CircuitBreakerError
                response = await _cb.call(
                    llm_service.generate,
                    prompt=prompt,
                    provider=self.config.model_provider,
                )
            except CircuitBreakerError as _cb_err:
                logger.warning(
                    "[%s] LLM circuit breaker OPEN — rejecting _reason call. retry_after=%.1fs",
                    self.config.domain, _cb_err.retry_after,
                )
                raise  # propaga para o run() tratar com final_response amigável
        else:
            # circuit breaker indisponível → fail-open
            response = await llm_service.generate(
                prompt=prompt,
                provider=self.config.model_provider,
            )

        # Rough token estimate: (prompt + response) chars / 4
        state.tokens_used_estimate += (len(prompt) + len(response)) // 4

        duration = (time.time() - step_start) * 1000
        logger.debug(
            f"[{self.config.domain}] _reason completed in {duration:.1f}ms "
            f"tokens_est={state.tokens_used_estimate}"
        )

        return response

    async def _act(self, state: ReActState, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call.

        Args:
            state: Current loop state (updated in place with tool call record).
            action: Dictionary with 'tool_name' and 'tool_args'.

        Returns:
            Dictionary with the tool execution result.
        """
        step_start = time.time()
        tool_name = action["tool_name"]
        tool_args = action.get("tool_args", {})

        tool_def = self._tool_map.get(tool_name)
        if not tool_def:
            return {"error": f"Tool '{tool_name}' not found", "success": False}

        logger.info(f"[{self.config.domain}] Executing tool: {tool_name}")

        try:
            result = await tool_def.function(**tool_args)

            if not isinstance(result, dict):
                result = {"result": result, "success": True}
            elif "success" not in result:
                result["success"] = True

        except Exception as exc:
            logger.error(
                f"[{self.config.domain}] Tool '{tool_name}' failed: {exc}",
                exc_info=True,
            )
            result = {"error": str(exc), "success": False}

        duration = (time.time() - step_start) * 1000

        tool_record = {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "result": result,
            "duration_ms": duration,
        }
        state.tool_calls_made.append(tool_record)
        state.actions_taken.append(
            {"type": "call_tool", "tool": tool_name, "args": tool_args}
        )

        logger.info(
            f"[{self.config.domain}] Tool '{tool_name}' completed in {duration:.1f}ms "
            f"success={result.get('success', False)}"
        )

        return result

    async def _observe(self, state: ReActState, result: Dict[str, Any]) -> str:
        """Interpret a tool result into a human-readable observation.

        Args:
            state: Current loop state.
            result: The raw tool result dictionary.

        Returns:
            A string observation summarising the tool result.
        """
        if result.get("error"):
            return f"Tool returned an error: {result['error']}"

        result_str = json.dumps(result, ensure_ascii=False, default=str)
        max_obs_chars = settings.REACT_OBSERVATION_MAX_CHARS
        if len(result_str) > max_obs_chars:
            result_str = result_str[:max_obs_chars] + f"... (truncated at {max_obs_chars} chars)"

        return f"Tool result: {result_str}"

    async def _should_respond(self, state: ReActState) -> bool:
        """Decide whether the agent has enough information to respond.

        Simple heuristic: respond if the last tool call succeeded and
        produced a meaningful result, or if we have gathered enough
        observations.

        Args:
            state: Current loop state.

        Returns:
            True if the agent should generate a final response.
        """
        if state.error:
            return True

        if not state.tool_calls_made:
            return False

        last_call = state.tool_calls_made[-1]
        last_result = last_call.get("result", {})

        if not last_result.get("success", False):
            return False

        if state.iteration >= self.config.max_iterations - 1:
            return True

        return False

    async def _generate_response(
        self, state: ReActState, context: Dict[str, Any]
    ) -> str:
        """Generate the final user-facing response.

        Uses the system prompt, context, conversation, and observations
        accumulated during the loop to produce a coherent response.

        Args:
            state: Current loop state with all observations and actions.
            context: Domain-specific context.

        Returns:
            The generated response string.
        """
        step_start = time.time()

        observations_summary = ""
        if state.observations:
            observations_summary = "Information gathered:\n" + "\n".join(
                f"- {obs}" for obs in state.observations
            )

        actions_summary = ""
        if state.actions_taken:
            actions_summary = "Actions performed:\n" + "\n".join(
                f"- {a.get('type', 'unknown')}: {a.get('tool', a.get('reason', ''))}"
                for a in state.actions_taken
            )

        history_text = ""
        if state.messages:
            history_lines = []
            for msg in state.messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_lines.append(f"[{role}]: {content}")
            history_text = "\n".join(history_lines)

        context_text = json.dumps(context, ensure_ascii=False, default=str) if context else "{}"

        prompt = f"""{self.config.system_prompt}

Current Context:
{context_text}

Conversation:
{history_text}

{observations_summary}

{actions_summary}

Based on everything above, generate a helpful and natural response to the user.
Respond directly with the message text, no JSON wrapping."""

        response = await llm_service.generate(
            prompt=prompt,
            provider=self.config.model_provider,
        )

        duration = (time.time() - step_start) * 1000
        logger.debug(
            f"[{self.config.domain}] _generate_response completed in {duration:.1f}ms"
        )

        return response

    def _parse_reasoning(self, raw: str) -> Dict[str, Any]:
        """Parse the LLM reasoning output into a structured dictionary.

        Handles cases where the LLM wraps JSON in markdown code fences.

        Args:
            raw: Raw LLM response string.

        Returns:
            Parsed dictionary with thought, action, tool_name, tool_args, response.

        Raises:
            json.JSONDecodeError: If the response cannot be parsed as JSON.
        """
        text = raw.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)


# ---------------------------------------------------------------------------
# Phase 3 — Adapter: ToolDefinition → LangChain StructuredTool
# ---------------------------------------------------------------------------

def tool_definition_to_langchain_tool(td: "ToolDefinition") -> Any:
    """
    Converte um ToolDefinition (Phase 2 custom ReAct) em LangChain StructuredTool
    compatível com LangGraph create_react_agent (Phase 3).

    Permite migrar agentes para LangGraph nativo sem reescrever os tool registries
    existentes. Async e sync functions são suportados automaticamente.

    Uso em agentes migrados (_get_tools()):
        tool_defs = get_wizard_tools()
        lc_tools = [tool_definition_to_langchain_tool(td) for td in tool_defs]
    """
    import inspect

    try:
        from langchain_core.tools import StructuredTool
    except ImportError as exc:
        raise ImportError("langchain-core não instalado — necessário para Phase 3 LangGraph") from exc

    fn = td.function
    name = td.name
    description = td.description or f"Executa {name}"

    if inspect.iscoroutinefunction(fn):
        return StructuredTool.from_function(
            coroutine=fn,
            name=name,
            description=description,
        )
    return StructuredTool.from_function(
        func=fn,
        name=name,
        description=description,
    )
