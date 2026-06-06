"""
LIA-A04: Agentic Tool Calling Loop

Implements the core agentic pattern:
  LLM (with tools) -> Tool Call -> Execute -> Result -> LLM -> Response

Uses existing infrastructure:
  - ToolRegistry for tool schemas
  - ToolExecutor for safe execution with ToolExecutionContext
  - LLMService.generate_with_tools() for function calling (Claude & Gemini)

Enabled by default. Disable with LIA_AGENTIC_LOOP=false..
"""
import asyncio
import json
import logging
import os
import time
from app.shared.compliance.c3b_layer import (  # W3-014 (2026-05-23)
    pre_compliance as _c3b_pre,
    post_compliance as _c3b_post,
    ComplianceContext as _C3bCtx,
)

from app.shared.observability.tracing import trace_span

logger = logging.getLogger(__name__)


async def _emit_activity(event: dict) -> None:
    """Empurra evento de atividade ao vivo (tool_started/finished) pelo callback
    de streaming do LLM (ContextVar setado pelo transporte SSE/WS). Fail-safe:
    no-op quando não há callback (ex.: REST puro). #1 orquestrador 2026-06-03."""
    try:
        from app.domains.ai.services.llm import _llm_streaming_callback
        cb = _llm_streaming_callback.get(None)
        if cb is not None:
            await cb(event)
    except Exception:
        pass


# Passos de fase (2026-06-04): emite a CHAVE da fase ('understanding'/'composing'
# /nome de tool); o FE localiza (PT/EN reativo ao toggle) via activity-labels.ts.
async def _emit_phase(key: str) -> None:
    # Emite a CHAVE da fase; o FE localiza (reativo ao toggle PT/EN, page-agnostic).
    await _emit_activity({"type": "reasoning_step", "label": key})


# Sprint 9.2 (NS-5 latency fix, 2026-05-24): agentic LLM timeout configurable.
# Default 60s (was 30s — too tight for Claude API with full tool schema in
# slow-network periods). Env override LIA_AGENTIC_LLM_TIMEOUT_SECONDS for
# ops tuning. Cap at 120s to avoid infinite hang.
def _resolve_agentic_llm_timeout() -> float:
    import os
    raw = os.environ.get("LIA_AGENTIC_LLM_TIMEOUT_SECONDS", "60")
    try:
        v = float(raw)
    except (TypeError, ValueError):
        v = 60.0
    return max(5.0, min(120.0, v))


_AGENTIC_LLM_TIMEOUT_SECONDS = _resolve_agentic_llm_timeout()

MAX_TOOL_ITERATIONS = int(os.getenv("LIA_MAX_TOOL_ITERATIONS", "3"))

# Canonical (2026-06-04): transient provider-overload resilience.
# A single Anthropic/Vertex `overloaded_error` (HTTP 529) is RETRYABLE —
# burning the whole iteration budget on it (old `break`) degraded UX into a
# misleading "reformule a pergunta". We retry the SAME LLM call with bounded
# exponential backoff; on persistent overload we flag
# `failure_reason="provider_overloaded"` so the orchestrator returns an
# honest, overload-specific message (REGRA-4 honesty).
_AGENTIC_OVERLOAD_RETRIES = int(os.getenv("LIA_AGENTIC_OVERLOAD_RETRIES", "2"))
_AGENTIC_OVERLOAD_BACKOFF_BASE = float(
    os.getenv("LIA_AGENTIC_OVERLOAD_BACKOFF_BASE", "0.6")
)
_TRANSIENT_PROVIDER_MARKERS = (
    "overloaded_error",
    "overloaded",
    "rate_limit",
    "rate limit",
    "service unavailable",
    "service_unavailable",
    "internal server error",
    "internal_server_error",
    "temporarily unavailable",
    "try again later",
)


def _is_transient_provider_error(exc: BaseException) -> bool:
    """True when `exc` is a retryable provider hiccup (overload/429/503/5xx).

    Detection is by message substring (provider-agnostic, no SDK import
    coupling). A false positive costs only a bounded retry (benign); a false
    negative degrades UX into the misleading generic fallback — so we err
    toward retrying.
    """
    s = str(exc).lower()
    return any(marker in s for marker in _TRANSIENT_PROVIDER_MARKERS)


# UI actions a agentic tool result may carry that the orchestrator must ACT on
# (vs. merely feed back to the LLM as text). Additive surfacing: only these
# directives are promoted to ``run()``'s ``tool_directive`` return field.
_ACTIONABLE_TOOL_UI_ACTIONS: frozenset[str] = frozenset(
    {"start_wizard_seeded", "open_modal"}
)


def _extract_response_blocks(result: object) -> list:
    """Pure helper: surface response_blocks (RRP) from a ToolResult.

    AD3: tools-as-renderers podem retornar blocos ricos em
    ``result.result["data"]["response_blocks"]``. O loop acumula e
    promove no return. Defensivo — shape mismatch -> []; nunca raise.
    """
    if result is None:
        return []
    if not getattr(result, "success", False):
        return []
    payload = getattr(result, "result", None)
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    blocks = data.get("response_blocks")
    return blocks if isinstance(blocks, list) else []


def _extract_tool_directive(result: object) -> "dict | None":
    """Pure helper: surface an actionable UI directive from a ToolResult.

    The orchestrator's agentic loop captures only ``tool_calls_made`` (name +
    params) — it never inspects tool *results*. Some tools (e.g.
    ``start_creation_from_source``) return a directive in
    ``result.result["data"]["ui_action"]`` that the orchestrator must consume
    to drive the UX (here: seed a fresh wizard session). This helper extracts
    that directive WITHOUT coupling to any specific tool.

    Returns ``None`` unless the result succeeded AND carries a recognized
    ``data.ui_action`` in ``_ACTIONABLE_TOOL_UI_ACTIONS``. Defensive: any shape
    mismatch yields ``None`` (never raises), so a normal tool result NEVER
    produces a directive — this keeps the consume path strictly additive.
    """
    if result is None:
        return None
    if not getattr(result, "success", False):
        return None
    payload = getattr(result, "result", None)
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    ui_action = data.get("ui_action")
    if ui_action not in _ACTIONABLE_TOOL_UI_ACTIONS:
        return None
    return {
        "ui_action": ui_action,
        "seed_source": data.get("seed_source"),
        # Fase B: open_ui (open_modal) carrega o payload do modal aqui.
        "ui_action_params": data.get("ui_action_params"),
    }


class AgenticLoop:
    """Executes user queries using LLM function calling with registered tools."""

    def __init__(self):
        self._tool_registry = None
        self._tool_executor = None
        self._llm_service = None

    def _ensure_deps(self):
        """Lazy import to avoid circular deps at module load time."""
        if self._tool_registry is None:
            from app.tools.registry import tool_registry
            from app.tools.executor import ToolExecutor, ToolExecutionContext
            from app.domains.ai.services.llm import LLMService

            self._tool_registry = tool_registry
            self._tool_executor = ToolExecutor()
            self._llm_service = LLMService()
            self._ToolExecutionContext = ToolExecutionContext

    # ------------------------------------------------------------------
    # Schema helpers
    # ------------------------------------------------------------------

    def get_tool_schemas(self, provider: str = "claude") -> list[dict]:
        """Get tool schemas in the format needed by the LLM provider."""
        self._ensure_deps()
        tools = self._tool_registry.list_tools()
        if not tools:
            return []
        return self._tool_registry.get_all_schemas(format=provider)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    @trace_span("orchestrator.phase_1_5_agentic_loop", attributes={"phase": "1.5"})
    async def run(
        self,
        user_message: str,
        system_prompt: str = "",
        conversation_history: list | None = None,
        company_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        provider: str = "claude",
        max_iterations: int | None = None,
    ) -> dict:
        """
        Run the agentic loop.

        Returns:
            {
                "response": str | None,
                "tool_calls_made": list[dict],
                "iterations": int,
            }
        """
        self._ensure_deps()

        # UC-P0-10: Fail-closed tenant guard — both required before ANY processing
        if not company_id or not user_id:
            logger.warning(
                "[AgenticLoop] Missing tenant context (company_id=%r, user_id=%r) — "
                "returning empty response without LLM/tool execution.",
                company_id,
                user_id,
            )
            return {"response": None, "tool_calls_made": [], "iterations": 0}

        # W3-014 (2026-05-23): c3b pre_compliance ANTES do LLM loop.
        # Strip PII, FairnessGuard L3, HateSpeech, PromptInjection (W1-005/007).
        # Mensagem bloqueada → returna early sem invocar LLM.
        try:
            _c3b_pre_result = await _c3b_pre(
                message=user_message,
                company_id=company_id,
                domain="agentic_loop",
            )
            if _c3b_pre_result.hate_speech_blocked or _c3b_pre_result.injection_blocked:
                logger.warning(
                    "[AgenticLoop] c3b pre_compliance BLOCKED · hate=%s injection=%s",
                    _c3b_pre_result.hate_speech_blocked,
                    _c3b_pre_result.injection_blocked,
                )
                return {
                    "response": _c3b_pre_result.block_reason or "Mensagem bloqueada por compliance",
                    "tool_calls_made": [],
                    "iterations": 0,
                    "blocked_reason": "c3b_compliance",
                }
            # Use clean_message (PII stripped) downstream
            user_message = _c3b_pre_result.clean_message or user_message
        except Exception as _c3b_exc:
            # Fail-open · c3b failure NÃO bloqueia execução (defense-in-depth)
            logger.warning("[AgenticLoop] c3b pre_compliance skipped: %s", _c3b_exc)

        max_iter = max_iterations or MAX_TOOL_ITERATIONS
        tool_schemas = self.get_tool_schemas(provider)

        if not tool_schemas:
            logger.debug("[LIA-A04] No tools registered -- skipping agentic loop")
            return {"response": None, "tool_calls_made": [], "iterations": 0}

        # WT-2022 P0.AIC1: ai_credits_balance gate antes do loop multi-iteracao.
        # Loop pode rodar ate MAX_TOOL_ITERATIONS chamadas LLM — estima ~3k per iter.
        # fail-safe ALLOW se DB outage. chokepoint canonical e llm_factory, mas
        # bail-out cedo aqui economiza iteracoes desperdicadas.
        try:
            from app.shared.services.ai_credit_gate import check_credit_budget, AICreditExhausted
            from lia_config.database import AsyncSessionLocal
            async with AsyncSessionLocal() as _credit_db:
                await check_credit_budget(
                    _credit_db,
                    str(company_id),
                    estimated_tokens=int(max_iter) * 3000,
                )
        except AICreditExhausted:
            logger.warning(
                "[AgenticLoop] AI credit budget exhausted: company=%s — skipping loop",
                company_id,
            )
            return {
                "response": None,
                "tool_calls_made": [],
                "iterations": 0,
                "blocked_reason": "ai_credit_exhausted",
            }
        except Exception as _aic_exc:
            logger.debug("[AgenticLoop] ai_credit_gate skipped (fail-safe): %s", _aic_exc)

        # Build messages list for generate_with_tools
        messages: list[dict] = []
        if conversation_history:
            for msg in conversation_history[-10:]:
                role = msg.get("role", "user")
                messages.append({"role": role, "content": msg.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        # Build security context for tool execution (tenant isolation)
        exec_context = None
        if company_id and user_id:
            exec_context = self._ToolExecutionContext(
                user_id=user_id,
                company_id=company_id,
            )

        tool_calls_made: list[dict] = []
        # Additive (2026-06-04): last actionable UI directive surfaced by a tool
        # result (e.g. start_creation_from_source -> start_wizard_seeded). Stays
        # None for normal turns; consumed by main_orchestrator after run().
        tool_directive: "dict | None" = None
        # AD3: acumula response_blocks (RRP) emitidos por tools-as-renderers.
        response_blocks_acc: list = []

        # Card de fase: entendendo a solicitação (localizado).
        await _emit_phase("understanding")

        for iteration in range(max_iter):
            # --- Call LLM with tool schemas (retry transient overload) ---
            llm_response = None
            for _attempt in range(_AGENTIC_OVERLOAD_RETRIES + 1):
                try:
                    _t_llm_start = asyncio.get_event_loop().time()
                    llm_response = await asyncio.wait_for(
                        self._llm_service.generate_with_tools(
                            messages=messages,
                            tools=tool_schemas,
                            provider=provider,
                            system_prompt=system_prompt or None,
                        ),
                        timeout=_AGENTIC_LLM_TIMEOUT_SECONDS,
                    )
                    break
                except asyncio.TimeoutError:
                    _t_elapsed = asyncio.get_event_loop().time() - _t_llm_start
                    logger.warning(
                        "[LIA-A04] LLM tool-call timed out (iter %d, provider=%s, "
                        "elapsed=%.1fs, limit=%.1fs). Falling through to Phase 2 V1 — "
                        "if frequent, bump LIA_AGENTIC_LLM_TIMEOUT_SECONDS env.",
                        iteration, provider, _t_elapsed, _AGENTIC_LLM_TIMEOUT_SECONDS,
                    )
                    return {
                        "response": None,
                        "tool_calls_made": tool_calls_made,
                        "iterations": iteration + 1,
                        "failure_reason": "llm_timeout",
                        "tool_directive": tool_directive,
                    }
                except Exception as exc:
                    _transient = _is_transient_provider_error(exc)
                    if _transient and _attempt < _AGENTIC_OVERLOAD_RETRIES:
                        _backoff = _AGENTIC_OVERLOAD_BACKOFF_BASE * (2 ** _attempt)
                        logger.warning(
                            "[LIA-A04] transient provider error (iter %d, attempt "
                            "%d/%d) — retrying in %.1fs: %s",
                            iteration, _attempt + 1,
                            _AGENTIC_OVERLOAD_RETRIES + 1, _backoff, exc,
                        )
                        await asyncio.sleep(_backoff)
                        continue
                    if _transient:
                        logger.warning(
                            "[LIA-A04] provider overloaded after %d attempts — "
                            "returning honest overload signal: %s",
                            _attempt + 1, exc,
                        )
                        return {
                            "response": None,
                            "tool_calls_made": tool_calls_made,
                            "iterations": iteration + 1,
                            "failure_reason": "provider_overloaded",
                            "tool_directive": tool_directive,
                        }
                    logger.warning("[LIA-A04] LLM tool-call failed: %s", exc)
                    return {
                        "response": None,
                        "tool_calls_made": tool_calls_made,
                        "iterations": iteration + 1,
                        "failure_reason": "llm_error",
                        "tool_directive": tool_directive,
                    }

            if llm_response is None:
                # Defensive: retries exhausted without a returnable branch.
                return {
                    "response": None,
                    "tool_calls_made": tool_calls_made,
                    "iterations": iteration + 1,
                    "failure_reason": "provider_overloaded",
                    "tool_directive": tool_directive,
                }

            # --- If LLM responded with text (no tool call), done ---
            if not llm_response.is_tool_call:
                # Card de fase: preparando a resposta (localizado).
                await _emit_phase("composing")
                # W3-014 (2026-05-23): c3b post_compliance · FactChecker + audit log
                # antes de retornar pro caller. Fail-safe (não bloqueia em error).
                _final_response = llm_response.text_response or ""
                try:
                    _c3b_ctx = _C3bCtx(
                        company_id=company_id or "unknown",
                        user_id=user_id or "unknown",
                        session_id=session_id or "unknown",
                        domain="agentic_loop",
                        agent_id="agentic_loop",
                        original_message=user_message,
                    )
                    _final_response = await _c3b_post(_final_response, _c3b_ctx)
                except Exception as _c3b_exc:
                    logger.warning("[AgenticLoop] c3b post_compliance skipped: %s", _c3b_exc)
                return {
                    "response": _final_response,
                    "tool_calls_made": tool_calls_made,
                    "iterations": iteration + 1,
                    "tool_directive": tool_directive,
                    "response_blocks": response_blocks_acc or None,
                }

            # --- Execute each requested tool call ---
            for tc in llm_response.tool_calls:
                tool_calls_made.append({
                    "name": tc.name,
                    "parameters": tc.parameters,
                })

                # #1 (2026-06-03): atividade ao vivo p/ o timeline do chat.
                await _emit_activity({"type": "tool_started", "name": tc.name})
                _tool_t0 = time.monotonic()
                _tool_status = "ok"
                try:
                    result = await asyncio.wait_for(
                        self._tool_executor.execute(
                            tool_name=tc.name,
                            parameters=tc.parameters,
                            agent_type="orchestrator",
                            context=exec_context,
                        ),
                        timeout=15.0,
                    )
                    tool_result_content = (
                        result.to_llm_content() if result else "Tool returned no result."
                    )
                    # Additive: capture the LAST actionable UI directive a tool
                    # result carries (e.g. start_wizard_seeded). Defensive —
                    # None for normal results, never raises (REGRA-4 fail-loud
                    # is N/A here: the LLM still gets the result via content).
                    _directive = _extract_tool_directive(result)
                    if _directive is not None:
                        tool_directive = _directive
                    _blocks = _extract_response_blocks(result)
                    if _blocks:
                        response_blocks_acc.extend(_blocks)
                        # Anti-renarracao (computacional): a tool ja exibiu os
                        # dados em blocos ricos. Alimenta o LLM com uma nota
                        # curta em vez do payload, p/ ele NAO repetir a
                        # tabela/scores em prosa (tabela + texto duplicado).
                        tool_result_content = (
                            f"[{len(_blocks)} bloco(s) visual(is) rico(s) ja "
                            f"exibido(s) ao usuario (tabela/scores/fontes). De "
                            f"apenas 1 frase curta de enquadramento; NAO repita "
                            f"os dados em texto.]"
                        )
                except Exception as exc:
                    _tool_status = "error"
                    logger.warning(
                        "[LIA-A04] Tool %s execution failed: %s", tc.name, exc
                    )
                    tool_result_content = json.dumps(
                        {"error": f"Tool {tc.name} failed: {str(exc)[:200]}"},
                        ensure_ascii=False,
                    )
                await _emit_activity({
                    "type": "tool_finished",
                    "name": tc.name,
                    "status": _tool_status,
                    "duration_ms": int((time.monotonic() - _tool_t0) * 1000),
                })

                # Append assistant + tool-result messages for the next iteration.
                # The format depends on the provider:
                if provider == "claude":
                    # Claude expects tool_use content blocks + tool_result
                    messages.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": tc.id,
                                "name": tc.name,
                                "input": tc.parameters,
                            }
                        ],
                    })
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tc.id,
                                "content": tool_result_content,
                            }
                        ],
                    })
                else:
                    # Gemini expects function_call on model role + function_response
                    messages.append({
                        "role": "assistant",
                        "content": "",
                        "function_call": {
                            "name": tc.name,
                            "args": tc.parameters,
                        },
                    })
                    messages.append({
                        "role": "function_response",
                        "name": tc.name,
                        "response": (
                            json.loads(tool_result_content)
                            if isinstance(tool_result_content, str)
                            else tool_result_content
                        ),
                    })

        # Exhausted iterations without a final text response
        logger.info(
            "[LIA-A04] Exhausted %d iterations with %d tool calls",
            max_iter,
            len(tool_calls_made),
        )
        return {
            "response": None,
            "tool_calls_made": tool_calls_made,
            "iterations": max_iter,
            "tool_directive": tool_directive,
        }


# Singleton
agentic_loop = AgenticLoop()
