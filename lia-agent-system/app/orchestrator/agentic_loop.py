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

    async def run(
        self,
        user_message: str,
        system_prompt: str = "",
        conversation_history: list | None = None,
        company_id: str | None = None,
        user_id: str | None = None,
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

        max_iter = max_iterations or MAX_TOOL_ITERATIONS
        tool_schemas = self.get_tool_schemas(provider)

        if not tool_schemas:
            logger.debug("[LIA-A04] No tools registered -- skipping agentic loop")
            return {"response": None, "tool_calls_made": [], "iterations": 0}

        # Build messages list for generate_with_tools
        messages: list[dict] = []
        if conversation_history:
            for msg in conversation_history[-10:]:
                role = msg.get("role", "user")
                messages.append({"role": role, "content": msg.get("content", "")})
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
                tool_calls_made.append({
                    "name": tc.name,
                    "parameters": tc.parameters,
                })

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
