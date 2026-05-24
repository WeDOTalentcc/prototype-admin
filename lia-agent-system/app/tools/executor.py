"""
Tool Executor - Executes tools with validation and error handling.

Provides safe execution of tools with parameter validation,
timeout handling, and structured result formatting.

Includes tenant scoping via ToolExecutionContext for multi-tenancy security.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, ValidationError, create_model

from app.tools.registry import ToolRegistry, tool_registry
try:
    from app.shared.compliance.fairness_guard import FairnessGuard
    from app.shared.compliance.audit_service import get_audit_service
    from app.shared.pii_masking import mask_pii
except ImportError as _gov_dep_err:
    raise RuntimeError(f"GovernanceExecutor deps missing: {_gov_dep_err}") from _gov_dep_err


try:
    import sentry_sdk as _sentry_sdk
    _SENTRY_AVAILABLE = True
except ImportError:  # pragma: no cover
    _sentry_sdk = None  # type: ignore[union-attr]
    _SENTRY_AVAILABLE = False

# W3-025 (2026-05-23): Prometheus counter pra tool execution observability.
# Phase A: counter por (tool_name, status). Phase B: cost USD mapping.
try:
    from prometheus_client import Counter as _PromCounter
    _TOOL_EXEC_COUNTER = _PromCounter(
        "lia_tool_executions_total",
        "Tool execution count by name and status (W3-025)",
        ["tool_name", "status"],
    )
    _TOOL_EXEC_AVAILABLE = True
except (ImportError, ValueError) as _w3025_exc:  # pragma: no cover
    # ImportError: prometheus_client missing
    # ValueError: counter already registered (re-import via hot-reload)
    _TOOL_EXEC_COUNTER = None
    _TOOL_EXEC_AVAILABLE = False

logger = logging.getLogger(__name__)
from app.shared.observability.tracing import trace_span


class ToolExecutionContext(BaseModel):
    """
    Security context for tool execution.
    
    Provides tenant isolation and permission enforcement.
    This context should be provided by the orchestrator from authenticated session data,
    NOT from LLM-generated parameters.
    """
    model_config = ConfigDict(extra='forbid')

    user_id: str
    company_id: str
    permissions: list[str] = []
    session_id: str | None = None
    
    def has_permission(self, permission: str) -> bool:
        """Check if context has a specific permission."""
        return permission in self.permissions or "admin" in self.permissions
    
    def can_access_company(self, target_company_id: str) -> bool:
        """Verify tenant isolation - can only access own company data."""
        return self.company_id == target_company_id or self.has_permission("cross_tenant_access")


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    tool_name: str = ""
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for LLM response."""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "tool_name": self.tool_name,
            "execution_time_ms": self.execution_time_ms
        }
    
    def to_llm_content(self) -> str:
        """Format result for sending back to LLM."""
        if self.success:
            return json.dumps(self.result, ensure_ascii=False, default=str)
        else:
            return json.dumps({"error": self.error}, ensure_ascii=False)


@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""
    id: str
    name: str
    parameters: dict[str, Any]


@dataclass
class ToolCallLog:
    """Log entry for tool execution."""
    tool_name: str
    parameters: dict[str, Any]
    result: ToolResult
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent_type: str | None = None
    conversation_id: str | None = None


class ToolExecutor:
    """
    Executes tools with validation, timeout, and error handling.
    
    Features:
    - Parameter validation against JSON Schema using Pydantic
    - Configurable execution timeout
    - Structured error handling
    - Execution logging for observability
    """
    
    DEFAULT_TIMEOUT = 30.0
    MAX_TOOL_CALLS_PER_REQUEST = 3
    
    def __init__(self, registry: ToolRegistry | None = None):
        self.registry = registry or tool_registry
        self.logger = logging.getLogger(self.__class__.__name__)
        self._execution_logs: list[ToolCallLog] = []
    
    def _validate_parameters(
        self, 
        parameters: dict[str, Any], 
        schema: dict[str, Any]
    ) -> str | None:
        """
        Validate parameters against JSON Schema.
        
        Returns None if valid, error message if invalid.
        """
        try:
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            for req_field in required:
                if req_field not in parameters:
                    return f"Missing required parameter: {req_field}"
            
            pydantic_fields = {}
            for field_name, field_schema in properties.items():
                field_type = self._json_schema_to_python_type(field_schema)
                is_required = field_name in required
                
                if is_required:
                    pydantic_fields[field_name] = (field_type, ...)
                else:
                    pydantic_fields[field_name] = (Optional[field_type], None)
            
            if pydantic_fields:
                DynamicModel = create_model("ToolParams", **pydantic_fields)
                DynamicModel(**parameters)
            
            return None
            
        except ValidationError as e:
            return f"Parameter validation failed: {str(e)}"
        except Exception as e:
            self.logger.warning(f"Validation error: {e}")
            return None
    
    def _json_schema_to_python_type(self, schema: dict[str, Any]) -> type:
        """Convert JSON Schema type to Python type."""
        schema_type = schema.get("type", "string")
        
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        return type_mapping.get(schema_type, str)
    
    async def execute(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        timeout: float | None = None,
        agent_type: str | None = None,
        conversation_id: str | None = None,
        context: ToolExecutionContext | None = None
    ) -> ToolResult:
        """
        Execute a tool by name with given parameters.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            timeout: Execution timeout in seconds
            agent_type: Type of agent making the call
            conversation_id: ID of the conversation context
            context: Security context with user_id and company_id for tenant isolation
            
        Returns:
            ToolResult with success status and result/error
        """
        start_time = datetime.utcnow()
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        self.logger.info(f"Executing tool: {tool_name} with params: {list(parameters.keys())}")

        # W1-004 Step 2 (multi-tenancy fail-closed) · company_id obrigatório.
        # Sem context.company_id, tool executa sem isolamento de tenant.
        # NOTA: audit log skipped (context inválido); metrics + log_execution
        # ainda firam via _emit_governance_signals.
        if context is None or not context.company_id:
            result = ToolResult(
                success=False,
                error="company_id required for tool execution (multi-tenancy fail-closed)",
                tool_name=tool_name,
            )
            self._emit_governance_signals(tool_name, parameters, result, context, agent_type, conversation_id)
            return result

        tool = self.registry.get_tool(tool_name)
        if not tool:
            result = ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}",
                tool_name=tool_name
            )
            self._emit_governance_signals(tool_name, parameters, result, context, agent_type, conversation_id)
            return result
        
        if tool.allowed_agents and agent_type and agent_type not in tool.allowed_agents:
            result = ToolResult(
                success=False,
                error=f"Agent '{agent_type}' not authorized for tool '{tool_name}'",
                tool_name=tool_name
            )
            self._emit_governance_signals(tool_name, parameters, result, context, agent_type, conversation_id)
            return result
        
        validation_error = self._validate_parameters(parameters, tool.parameters_schema)
        if validation_error:
            result = ToolResult(
                success=False,
                error=validation_error,
                tool_name=tool_name
            )
            self._emit_governance_signals(tool_name, parameters, result, context, agent_type, conversation_id)
            return result
        try:
            # Sprint 8.2 (NS-2 root cause fix, 2026-05-24):
            # NEVER mutate the caller's `parameters` dict. Build a fresh
            # dict for the handler call.
            #
            # Previous code did `parameters["_context"] = context` which
            # mutated the caller's reference. tool.handler(**parameters)
            # unpacks into a NEW kwargs in the handler — pop("_context")
            # in the handler does not propagate back. Result: `tc.parameters`
            # in agentic_loop STILL contains a ToolExecutionContext (not
            # JSON serializable) → next LLM iteration's json.dumps fails
            # silently, agentic loop dies after 1 successful tool call,
            # falls through to Phase 2 V1 that mis-classifies query intents
            # as create_job (NS-2 bug).
            handler_kwargs = dict(parameters)  # shallow copy — never mutate
            if context:
                handler_kwargs["_context"] = context
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                self.logger.debug(f"Tool {tool_name} executing with tenant context: company_id={context.company_id}")

            handler_result = await asyncio.wait_for(
                tool.handler(**handler_kwargs),
                timeout=timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            result = ToolResult(
                success=True,
                result=handler_result,
                tool_name=tool_name,
                execution_time_ms=execution_time
            )
            
        except TimeoutError:
            result = ToolResult(
                success=False,
                error=f"Tool execution timed out after {timeout}s",
                tool_name=tool_name
            )
            
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            self.logger.error(f"Tool execution error for {tool_name}: {e}", exc_info=True)
            if _SENTRY_AVAILABLE:
                _sentry_sdk.add_breadcrumb(
                    category="tool.error",
                    message=f"Tool {tool_name!r} failed: {type(e).__name__}: {e}",
                    level="error",
                    data={
                        "tool_name": tool_name,
                        "agent_type": getattr(self, "_agent_type", agent_type or "unknown"),
                        "error_type": type(e).__name__,
                    },
                )
                _sentry_sdk.set_tag("tool.last_failed", tool_name)
            result = ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
                tool_name=tool_name
            )
        
        # W1-004 · centraliza audit (Step 7) + metrics (Step 8) + observability log.
        self._emit_governance_signals(tool_name, parameters, result, context, agent_type, conversation_id)
        return result
    
    async def execute_batch(
        self,
        tool_calls: list[ToolCall],
        timeout: float | None = None,
        agent_type: str | None = None,
        conversation_id: str | None = None
    ) -> dict[str, ToolResult]:
        """
        Execute multiple tool calls.
        
        Args:
            tool_calls: List of tool calls to execute
            timeout: Timeout per tool
            agent_type: Type of agent making the calls
            conversation_id: ID of the conversation context
            
        Returns:
            Dict mapping tool call ID to result
        """
        results = {}
        
        for tool_call in tool_calls[:self.MAX_TOOL_CALLS_PER_REQUEST]:
            result = await self.execute(
                tool_name=tool_call.name,
                parameters=tool_call.parameters,
                timeout=timeout,
                agent_type=agent_type,
                conversation_id=conversation_id
            )
            results[tool_call.id] = result
        
        if len(tool_calls) > self.MAX_TOOL_CALLS_PER_REQUEST:
            self.logger.warning(
                f"Truncated tool calls: {len(tool_calls)} requested, "
                f"max {self.MAX_TOOL_CALLS_PER_REQUEST} allowed"
            )
        
        return results
    
    def _emit_metrics(
        self,
        tool_name: str,
        *,
        success: bool,
        elapsed_ms: float,
    ) -> None:
        """W1-004 Step 8 + W3-025 (2026-05-23) · canary metric + Prometheus counter.

        Sobrescrever em subclass pra exportar pra StatsD/etc.
        Phase A: log.debug + Prometheus counter (W3-025).
        Phase B: cost USD mapping per tool name.
        """
        self.logger.debug(
            "tool.metric name=%s success=%s elapsed_ms=%.1f",
            tool_name, success, elapsed_ms,
        )
        # W3-025: Prometheus counter (fail-safe se SDK missing)
        if _TOOL_EXEC_AVAILABLE and _TOOL_EXEC_COUNTER is not None:
            try:
                _TOOL_EXEC_COUNTER.labels(
                    tool_name=tool_name,
                    status="success" if success else "failure",
                ).inc()
            except Exception as exc:
                self.logger.debug("counter inc failed (silent): %s", exc)

    def _emit_governance_signals(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: ToolResult,
        context: "ToolExecutionContext | None",
        agent_type: str | None,
        conversation_id: str | None,
    ) -> None:
        """W1-004 helper · emite audit log + metrics + execution log per call.

        Centraliza Step 7 (audit) + Step 8 (metrics) + log de observability
        para evitar duplicação em múltiplos early-returns. Audit é fail-safe
        (NUNCA bloqueia tool execution) e usa asyncio.create_task pra non-blocking.
        """
        # Step 7 (audit log) — só com context válido (company_id required)
        if context is not None and context.company_id:
            try:
                audit_svc = get_audit_service()
                asyncio.create_task(
                    audit_svc.log_action(
                        trace_id=context.session_id or "unknown",
                        company_id=context.company_id,
                        action_type="tool_call",
                        actor=context.user_id,
                        target_id=tool_name,
                        target_type="tool",
                        metadata={
                            "agent_type": agent_type,
                            "conversation_id": conversation_id,
                            "elapsed_ms": result.execution_time_ms,
                            "success": result.success,
                            "error": result.error,
                        },
                    )
                )
            except Exception as _audit_exc:
                self.logger.debug("audit log skipped: %s", _audit_exc)

        # Step 8 (metrics)
        self._emit_metrics(
            tool_name,
            success=result.success,
            elapsed_ms=result.execution_time_ms,
        )

        # Observability log
        self._log_execution(tool_name, parameters, result, agent_type, conversation_id)

    def _log_execution(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: ToolResult,
        agent_type: str | None,
        conversation_id: str | None
    ) -> None:
        """Log tool execution for observability."""
        log_entry = ToolCallLog(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            agent_type=agent_type,
            conversation_id=conversation_id
        )
        self._execution_logs.append(log_entry)
        
        if len(self._execution_logs) > 1000:
            self._execution_logs = self._execution_logs[-500:]
        
        status = "SUCCESS" if result.success else "FAILED"
        self.logger.info(
            f"Tool execution [{status}]: {tool_name} "
            f"(agent={agent_type}, time={result.execution_time_ms:.1f}ms)"
        )
    
    def get_recent_logs(self, limit: int = 100) -> list[ToolCallLog]:
        """Get recent execution logs."""
        return self._execution_logs[-limit:]
    
    def clear_logs(self) -> None:
        """Clear execution logs."""
        self._execution_logs.clear()


tool_executor = ToolExecutor()


class GovernanceExecutor:
    """8-step enterprise governance pipeline for tool execution.

    Pipeline:
      1. Validate input parameters against contract schema
      2. company_id isolation (fail-closed if required)
      3. Execute function with SLA timeout
      4. FairnessGuard (if affects_candidate_decision)
      5. PII masking (if touches_pii)
      6. Output schema validation
      7. AuditService.log_action (non-blocking background task)
      8. _emit_metrics hook
    """

    def __init__(self) -> None:
        self._fairness_guard = FairnessGuard()
        self._audit_service = get_audit_service()

    async def execute(
        self,
        contract: Any,
        parameters: dict[str, Any],
        context: ToolExecutionContext,
        agent_type: str = "unknown",
        conversation_id: str | None = None,
    ) -> ToolResult:
        start = datetime.utcnow()

        # Step 1: validate input parameters
        err = self._validate_params(parameters, contract.parameters)
        if err:
            return ToolResult(success=False, error=err, tool_name=contract.name)

        # Step 2: company_id isolation — fail-closed
        if contract.requires_company_id and not context.company_id:
            return ToolResult(
                success=False,
                error="company_id is required but missing from execution context",
                tool_name=contract.name,
            )

        # Step 3: execute with SLA timeout
        timeout_s = contract.sla_ms / 1000.0
        try:
            raw_result = await asyncio.wait_for(
                contract.function(**parameters),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            self._emit_metrics(contract.name, success=False, elapsed_ms=elapsed)
            return ToolResult(
                success=False,
                error=f"Tool timed out after {contract.sla_ms}ms",
                tool_name=contract.name,
                execution_time_ms=elapsed,
            )
        except Exception as exc:
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            self._emit_metrics(contract.name, success=False, elapsed_ms=elapsed)
            return ToolResult(
                success=False,
                error=str(exc),
                tool_name=contract.name,
                execution_time_ms=elapsed,
            )

        # Step 4: FairnessGuard — only for candidate-decision tools
        if contract.affects_candidate_decision:
            fr = self._fairness_guard.check(json.dumps(raw_result, default=str))
            if fr.is_biased():
                terms = getattr(fr, "blocked_terms", [])
                return ToolResult(
                    success=False,
                    error=f"Fairness check blocked output: {terms}",
                    tool_name=contract.name,
                )

        # Step 5: PII masking on declared output fields
        if contract.touches_pii and contract.pii_output_fields:
            data = raw_result.get("data", {}) if isinstance(raw_result, dict) else {}
            for pii_field in contract.pii_output_fields:
                if pii_field in data:
                    data[pii_field] = mask_pii(str(data[pii_field]))

        # Step 6: output schema validation
        if contract.output_schema:
            required_fields = contract.output_schema.get("required", [])
            if isinstance(raw_result, dict):
                missing = [f for f in required_fields if f not in raw_result]
                if missing:
                    return ToolResult(
                        success=False,
                        error=f"Output schema violation — missing fields: {missing}",
                        tool_name=contract.name,
                    )

        elapsed = (datetime.utcnow() - start).total_seconds() * 1000

        # Step 7: audit log — non-blocking background task
        asyncio.create_task(
            self._audit_service.log_action(
                trace_id=context.session_id or "unknown",
                company_id=context.company_id,
                action_type="tool_call",
                actor=context.user_id,
                target_id=contract.name,
                target_type="tool",
                metadata={
                    "agent_type": agent_type,
                    "conversation_id": conversation_id,
                    "elapsed_ms": elapsed,
                },
            )
        )

        # Step 8: metrics
        self._emit_metrics(contract.name, success=True, elapsed_ms=elapsed)

        return ToolResult(
            success=True,
            result=raw_result,
            tool_name=contract.name,
            execution_time_ms=elapsed,
        )

    def _validate_params(self, parameters: dict[str, Any], schema: dict[str, Any]) -> str | None:
        required = schema.get("required", [])
        for field_name in required:
            if field_name not in parameters:
                return f"Missing required parameter: {field_name}"
        return None

    def _emit_metrics(self, tool_name: str, *, success: bool, elapsed_ms: float) -> None:
        logger.debug(
            "tool.metric name=%s success=%s elapsed_ms=%.1f",
            tool_name,
            success,
            elapsed_ms,
        )


governance_executor = GovernanceExecutor()
