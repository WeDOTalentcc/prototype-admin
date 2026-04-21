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

from pydantic import BaseModel, ValidationError, create_model

from app.tools.registry import ToolRegistry, tool_registry

logger = logging.getLogger(__name__)


class ToolExecutionContext(BaseModel):
    """
    Security context for tool execution.
    
    Provides tenant isolation and permission enforcement.
    This context should be provided by the orchestrator from authenticated session data,
    NOT from LLM-generated parameters.
    """
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
    MAX_TOOL_CALLS_PER_REQUEST = 10
    
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
    
    # ------------------------------------------------------------------
    # FIX 8 G1 — FairnessGuard helper
    # ------------------------------------------------------------------

    _TEXT_PARAM_NAMES = frozenset({
        "text", "message", "description", "content", "query", "prompt",
        "body", "notes", "comment", "comments", "search_query", "q",
        "job_description", "jd", "filter", "requirements",
    })

    def _check_fairness(self, parameters: dict[str, Any]) -> dict[str, Any] | None:
        """Return dict with bias info if any text param is explicitly biased.
        Returns None if all text params pass FairnessGuard Layer 1.

        Non-blocking if FairnessGuard is unavailable (import error, init fail).
        """
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
        except ImportError:
            return None

        try:
            guard = FairnessGuard()
        except Exception:
            return None

        for pname, pvalue in parameters.items():
            if pname.startswith("_"):
                continue  # internal flags (_context, _hitl_confirmed)
            if pname not in self._TEXT_PARAM_NAMES:
                continue
            if not isinstance(pvalue, str) or not pvalue.strip():
                continue
            try:
                result = guard.check(pvalue)
            except Exception:
                continue
            if getattr(result, "is_blocked", False):
                return {
                    "blocked_terms": list(getattr(result, "blocked_terms", [])),
                    "category": getattr(result, "category", None),
                    "educational_message": getattr(result, "educational_message", None),
                    "parameter": pname,
                }
        return None

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
        
        self.logger.info(f"Executing tool: {tool_name} with params: {list(parameters.keys())}")
        
        tool = self.registry.get_tool(tool_name)
        if not tool:
            result = ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}",
                tool_name=tool_name
            )
            self._log_execution(tool_name, parameters, result, agent_type, conversation_id)
            return result
        
        if tool.allowed_agents and agent_type and agent_type not in tool.allowed_agents:
            result = ToolResult(
                success=False,
                error=f"Agent '{agent_type}' not authorized for tool '{tool_name}'",
                tool_name=tool_name
            )
            self._log_execution(tool_name, parameters, result, agent_type, conversation_id)
            return result

        governance_tags = getattr(tool, "governance_tags", []) or []

        # FIX 8 G1 — FairnessGuard enforcement before execution.
        # If the tool declares fairness_guard, scan text-shaped parameters for
        # explicit bias (Layer 1 regex). Blocked queries return an educational
        # message and never reach the handler. This is LGPD / CF Art. 5º compliance.
        if "fairness_guard" in governance_tags:
            _bias_result = self._check_fairness(parameters)
            if _bias_result is not None:
                result = ToolResult(
                    success=False,
                    error=f"FairnessGuard blocked: {_bias_result.get('blocked_terms')}",
                    result={
                        "blocked_by_fairness_guard": True,
                        "blocked_terms": _bias_result.get("blocked_terms"),
                        "category": _bias_result.get("category"),
                        "educational_message": _bias_result.get("educational_message"),
                        "tool_name": tool_name,
                    },
                    tool_name=tool_name,
                )
                self._log_execution(tool_name, parameters, result, agent_type, conversation_id)
                return result

        # FIX 3 — Check governance_tags for HITL requirement before executing.
        if "requires_hitl" in governance_tags and not parameters.get("_hitl_confirmed"):
            result = ToolResult(
                success=True,
                result={
                    "status": "pending_hitl_confirmation",
                    "requires_hitl": True,
                    "tool_name": tool_name,
                    "parameters": {k: v for k, v in parameters.items() if k != "_context"},
                    "governance_tags": list(governance_tags),
                    "message": (
                        f"A ferramenta '{tool_name}' requer confirmação humana antes de executar "
                        f"(governance_tags={governance_tags}). Confirme para prosseguir."
                    ),
                },
                tool_name=tool_name,
            )
            self._log_execution(tool_name, parameters, result, agent_type, conversation_id)
            return result
        
        validation_error = self._validate_parameters(parameters, tool.parameters_schema)
        if validation_error:
            result = ToolResult(
                success=False,
                error=validation_error,
                tool_name=tool_name
            )
            self._log_execution(tool_name, parameters, result, agent_type, conversation_id)
            return result
        
        try:
            if context:
                parameters["_context"] = context
                self.logger.debug(f"Tool {tool_name} executing with tenant context: company_id={context.company_id}")
            
            handler_result = await asyncio.wait_for(
                tool.handler(**parameters),
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
            self.logger.error(f"Tool execution error for {tool_name}: {e}", exc_info=True)
            result = ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}",
                tool_name=tool_name
            )
        
        self._log_execution(tool_name, parameters, result, agent_type, conversation_id)
        return result
    
    async def execute_batch(
        self,
        tool_calls: list[ToolCall],
        timeout: float | None = None,
        agent_type: str | None = None,
        conversation_id: str | None = None,
        context: ToolExecutionContext | None = None
    ) -> dict[str, ToolResult]:
        """
        Execute multiple tool calls.
        
        Args:
            tool_calls: List of tool calls to execute
            timeout: Timeout per tool
            agent_type: Type of agent making the calls
            conversation_id: ID of the conversation context
            context: Security context with user_id and company_id for tenant isolation
            
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
                conversation_id=conversation_id,
                context=context
            )
            results[tool_call.id] = result
        
        if len(tool_calls) > self.MAX_TOOL_CALLS_PER_REQUEST:
            self.logger.warning(
                f"Truncated tool calls: {len(tool_calls)} requested, "
                f"max {self.MAX_TOOL_CALLS_PER_REQUEST} allowed"
            )
        
        return results
    
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
