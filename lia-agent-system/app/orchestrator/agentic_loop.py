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

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = int(os.getenv("LIA_MAX_TOOL_ITERATIONS", "8"))


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

    def get_tool_schemas(
        self,
        provider: str = "claude",
        agent_hints: list[str] | None = None,
    ) -> list[dict]:
        """Get tool schemas, optionally scoped by agent_hints.

        Onda 5.3.a (2026-04-22): intent-scoped filtering reduces prompt
        footprint (~40-95% fewer tool schemas when hints are specific).

        Args:
            provider: "claude" or "gemini"
            agent_hints: list of agent_type strings (e.g., ["sourcing",
                "analyst_feedback"]) from intent_heuristic.classify_intent().
                Empty/None → full catalog (current behavior).

        Fail-safe contract:
            - If LIA_TOOL_SCOPING_ENABLED=false → full catalog always
            - If hints empty → full catalog
            - If scoped result < LIA_MIN_SCOPED_TOOLS (default 3) → full
              catalog with warning log
        """
        self._ensure_deps()
        tools_list = self._tool_registry.list_tools()
        if not tools_list:
            return []

        # Feature flag for instant rollback
        scoping_enabled = os.getenv("LIA_TOOL_SCOPING_ENABLED", "true").lower() == "true"
        min_scoped = int(os.getenv("LIA_MIN_SCOPED_TOOLS", "3"))

        if not scoping_enabled or not agent_hints:
            # Full catalog fallback (current behavior preserved)
            if agent_hints and not scoping_enabled:
                logger.debug("[LIA-SCOPE] flag disabled, using full catalog despite hints=%s", agent_hints)
            return self._tool_registry.get_all_schemas(format=provider)

        # Scoped filtering via registry union method
        scoped = self._tool_registry.get_schemas_for_agents(agent_hints, format=provider)
        total = len(tools_list)
        scoped_count = len(scoped)

        if scoped_count < min_scoped:
            logger.warning(
                "[LIA-SCOPE] fallback=low_count hints=%s scoped=%d min=%d total=%d",
                agent_hints, scoped_count, min_scoped, total,
            )
            return self._tool_registry.get_all_schemas(format=provider)

        pct_saved = int(100 * (1 - scoped_count / total)) if total else 0
        logger.info(
            "[LIA-SCOPE] scoped=true hints=%s tools=%d/%d saved=%d%%",
            agent_hints, scoped_count, total, pct_saved,
        )
        return scoped

    # ------------------------------------------------------------------
    # Onda 5.3.c — history compaction helper
    # ------------------------------------------------------------------
    def _compact_history(
        self,
        conversation_history: list | None,
        conversation_summary: str | None = None,
    ) -> list[dict]:
        """Build messages list with optional compaction.

        Contract:
          - None/empty history → []
          - LIA_HISTORY_COMPACTION_ENABLED=false → last-10 slice (legacy)
          - len(history) <= COMPACT_THRESHOLD (default 5):
              * prepend summary if present (short+summary case)
              * else return history verbatim
          - len(history) > threshold AND summary:
              * prepend summary as system-like message
              * keep last KEEP_RECENT messages (default 6)
          - len(history) > threshold WITHOUT summary:
              * fall back to last-10 slice (legacy, no regression)

        Emits [LIA-HISTORY] marker when compaction applied.
        """
        if not conversation_history:
            return []

        enabled = os.getenv("LIA_HISTORY_COMPACTION_ENABLED", "true").lower() == "true"
        threshold = int(os.getenv("LIA_HISTORY_COMPACT_THRESHOLD", "5"))
        keep_recent = int(os.getenv("LIA_HISTORY_KEEP_RECENT", "6"))

        def _to_msg(m):
            return {"role": m.get("role", "user"), "content": m.get("content", "")}

        # Feature flag off → legacy behavior (last-10)
        if not enabled:
            return [_to_msg(m) for m in conversation_history[-10:]]

        total = len(conversation_history)

        # Short conversation: include summary if present; else verbatim
        if total <= threshold:
            result = [_to_msg(m) for m in conversation_history]
            if conversation_summary:
                summary_msg = {
                    "role": "system",
                    "content": f"[Resumo da conversa anterior] {conversation_summary}",
                }
                logger.info(
                    "[LIA-HISTORY] summary_only turns=%d summary_chars=%d",
                    total, len(conversation_summary),
                )
                return [summary_msg] + result
            return result

        # Long + no summary → legacy last-10
        if not conversation_summary:
            logger.debug("[LIA-HISTORY] fallback=no_summary turns=%d", total)
            return [_to_msg(m) for m in conversation_history[-10:]]

        # Long + summary → compact: summary + last keep_recent
        recent = [_to_msg(m) for m in conversation_history[-keep_recent:]]
        summary_msg = {
            "role": "system",
            "content": f"[Resumo da conversa anterior] {conversation_summary}",
        }
        logger.info(
            "[LIA-HISTORY] compacted turns=%d kept=%d summary_chars=%d",
            total, keep_recent, len(conversation_summary),
        )
        return [summary_msg] + recent

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    async def run(
        self,
        user_message: str,
        system_prompt: str = "",
        conversation_history: list | None = None,
        company_id: str | None = None,
        user_id: str | None = None,
        provider: str = "gemini",
        max_iterations: int | None = None,
        agent_hints: list[str] | None = None,
        conversation_summary: str | None = None,
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

        max_iter = max_iterations or MAX_TOOL_ITERATIONS
        tool_schemas = self.get_tool_schemas(provider, agent_hints=agent_hints)

        if not tool_schemas:
            logger.debug("[LIA-A04] No tools registered -- skipping agentic loop")
            return {"response": None, "tool_calls_made": [], "iterations": 0}

        # Onda 5.3.c (2026-04-22) — history compaction with summary reuse.
        # When conversation is long (>N turns) AND conversation_summary exists,
        # prepend summary + keep last K full turns. Fallback: legacy last-10.
        messages: list[dict] = self._compact_history(
            conversation_history, conversation_summary=conversation_summary
        )
        messages.append({"role": "user", "content": user_message})

        # Build security context for tool execution (tenant isolation)
        if not company_id:
            try:
                from app.shared.tenant_llm_context import get_current_llm_tenant
                company_id = get_current_llm_tenant() or ""
            except Exception:
                pass
        exec_context = None
        if company_id and user_id:
            exec_context = self._ToolExecutionContext(
                user_id=user_id,
                company_id=company_id,
            )
        if not exec_context:
            logger.warning(
                "[LIA-A04] ToolExecutionContext not set — company_id=%s user_id=%s. "
                "Tools will run without tenant isolation.",
                company_id, user_id,
            )

        tool_calls_made: list[dict] = []

        for iteration in range(max_iter):
            # --- Call LLM with tool schemas ---
            try:
                llm_response = await asyncio.wait_for(
                    self._llm_service.generate_with_tools(
                        messages=messages,
                        tools=tool_schemas,
                        provider=provider,
                        system_prompt=system_prompt or None,
                    ),
                    timeout=30.0,
                )
            except asyncio.TimeoutError:
                logger.warning("[LIA-A04] LLM tool-call timed out (iter %d)", iteration)
                break
            except Exception as exc:
                logger.warning("[LIA-A04] LLM tool-call failed: %s", exc)
                break

            # --- If LLM responded with text (no tool call), done ---
            if not llm_response.is_tool_call:
                _response_text = llm_response.text_response
                _tool_leak_names = (
                    "search_salary_benchmark", "create_job", "list_jobs",
                    "get_candidates", "validate_job_fields", "search_candidates",
                    "parse_and_create_candidate", "send_whatsapp", "schedule_interview",
                    "wsi_screening", "export_candidates", "generate_enriched_jd",
                    "analyze_cv_match", "analyze_interview_recording", "generate_interview_opinion",
                )
                if _response_text and any(n in _response_text for n in _tool_leak_names):
                    logger.warning("[LIA-A04] Tool name leakage detected -- sanitizing response")
                    _response_text = (
                        "Minhas diretrizes de funcionamento s\u00e3o confidenciais, "
                        "mas posso te contar o que sou capaz de fazer: "
                        "criar vagas, buscar candidatos, avaliar CVs, agendar entrevistas e muito mais. "
                        "Como posso ajudar com seu recrutamento?"
                    )
                return {
                    "response": _response_text,
                    "tool_calls_made": tool_calls_made,
                    "iterations": iteration + 1,
                }

            # --- Execute each requested tool call ---
            for tc in llm_response.tool_calls:
                # FIX 4 — Attach related_tools as suggested_next for proactive UX
                _suggested_next: list[str] = []
                try:
                    _tool_def = (
                        self._tool_executor.registry.get_tool(tc.name)
                        if self._tool_executor else None
                    )
                    if _tool_def is not None:
                        _suggested_next = list(getattr(_tool_def, "related_tools", []) or [])
                except Exception:
                    pass

                _tc_entry: dict[str, Any] = {
                    "name": tc.name,
                    "parameters": tc.parameters,
                    "suggested_next": _suggested_next,
                }
                tool_calls_made.append(_tc_entry)

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
                    # FIX 12 / G8 — persist result dict in the tool_calls_made entry
                    # so main_orchestrator can detect pending_hitl_confirmation and surface it.
                    if result:
                        try:
                            _tc_entry["result"] = result.to_dict()
                        except Exception:
                            pass
                    # FIX 12 / G9 — Central observability helper (replaces inline FIX 6).
                    try:
                        from app.shared.observability.tool_metrics import emit_tool_call
                        _success = bool(getattr(result, "success", False))
                        _governance: list[str] = []
                        _latency_ms = float(getattr(result, "execution_time_ms", 0.0)) or None
                        if self._tool_executor and self._tool_executor.registry.get_tool(tc.name):
                            _governance = list(getattr(
                                self._tool_executor.registry.get_tool(tc.name),
                                "governance_tags", [],
                            ) or [])
                        emit_tool_call(
                            tool_name=tc.name,
                            company_id=getattr(exec_context, "company_id", None),
                            success=_success,
                            first_shot=iteration == 0,
                            call_index=len(tool_calls_made),
                            governance_tags=_governance,
                            has_related_tools=bool(_suggested_next),
                            latency_ms=_latency_ms,
                            error=getattr(result, "error", None),
                        )
                    except Exception:
                        pass  # observability is non-blocking
                except Exception as exc:
                    logger.warning(
                        "[LIA-A04] Tool %s execution failed: %s", tc.name, exc
                    )
                    tool_result_content = json.dumps(
                        {"error": f"Tool {tc.name} failed: {str(exc)[:200]}"},
                        ensure_ascii=False,
                    )

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
        }


# Singleton
agentic_loop = AgenticLoop()
