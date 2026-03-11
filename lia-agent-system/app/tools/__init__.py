"""
Tools module for LLM function calling.

Provides tool registration, execution, and management for
enabling LLM agents to call real tools during response generation.

This module implements a complete function-calling system where:
1. Tools are registered with schemas and handlers
2. LLM agents can invoke tools to execute real actions
3. Results are returned to the user with appropriate messaging
"""
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from app.tools.registry import ToolDefinition, ToolRegistry, tool_registry
from app.tools.executor import ToolExecutor, ToolResult, ToolCall, tool_executor, ToolExecutionContext
from app.tools.tool_registry_loader import (
    load_tool_metadata,
    export_registry_to_yaml,
    validate_registry_against_yaml,
)


class ToolStatus(str, Enum):
    """Status of a tool execution."""
    SUCCESS = "success"
    ERROR = "error"
    PENDING_CONFIRMATION = "pending_confirmation"
    REQUIRES_AUTH = "requires_auth"
    PARTIAL = "partial"


class EnhancedToolResult(BaseModel):
    """Enhanced result from tool execution with user-friendly messaging."""
    status: ToolStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None
    action_taken: Optional[str] = None
    affected_entities: List[str] = []
    
    class Config:
        use_enum_values = True


class ToolCallRecord(BaseModel):
    """Record of a tool call for response tracking."""
    tool_name: str
    parameters: Dict[str, Any]
    status: ToolStatus
    result: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    class Config:
        use_enum_values = True


class ToolCallResponse(BaseModel):
    """Response containing tool execution information."""
    tool_calls: List[ToolCallRecord] = []
    pending_confirmations: List[ToolCallRecord] = []
    all_successful: bool = True
    summary: Optional[str] = None


__all__ = [
    "ToolStatus",
    "ToolDefinition",
    "ToolRegistry",
    "tool_registry",
    "ToolExecutor",
    "ToolResult",
    "ToolCall",
    "tool_executor",
    "ToolExecutionContext",
    "EnhancedToolResult",
    "ToolCallRecord",
    "ToolCallResponse",
    "initialize_tools",
    "get_all_tool_schemas",
    "execute_tool",
    # G5 — YAML registry
    "load_tool_metadata",
    "export_registry_to_yaml",
    "validate_registry_against_yaml",
]


def initialize_tools() -> None:
    """Initialize and register all tools."""
    from app.tools.job_wizard_tools import register_job_wizard_tools
    from app.tools.candidate_tools import register_candidate_tools
    from app.tools.communication_tools import register_communication_tools
    from app.tools.job_tools import register_job_tools
    from app.tools.export_tools import register_export_tools
    from app.tools.query_tools import register_query_tools
    from app.domains.recruiter_assistant.tools.pipeline_tools import register_pipeline_tools
    
    register_job_wizard_tools()
    register_candidate_tools()
    register_communication_tools()
    register_job_tools()
    register_export_tools()
    register_query_tools()
    register_pipeline_tools()
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"✅ Initialized {len(tool_registry.list_tools())} tools")


def get_all_tool_schemas(agent_type: Optional[str] = None, format: str = "claude") -> List[Dict[str, Any]]:
    """
    Get all tool schemas for LLM function calling.
    
    Args:
        agent_type: Optional agent type to filter tools
        format: Output format ('claude' or 'gemini')
        
    Returns:
        List of tool schemas
    """
    if agent_type:
        return tool_registry.get_schemas_for_agent(agent_type, format)
    return tool_registry.get_all_schemas(format)


async def execute_tool(
    tool_name: str,
    parameters: Dict[str, Any],
    agent_type: Optional[str] = None,
    conversation_id: Optional[str] = None,
    context: Optional[ToolExecutionContext] = None
) -> EnhancedToolResult:
    """
    Execute a tool and return an enhanced result.
    
    Args:
        tool_name: Name of the tool to execute
        parameters: Parameters to pass to the tool
        agent_type: Type of agent making the call
        conversation_id: ID of the conversation context
        context: Security context with user_id and company_id for tenant isolation
        
    Returns:
        EnhancedToolResult with status and user-friendly message
    """
    result = await tool_executor.execute(
        tool_name=tool_name,
        parameters=parameters,
        agent_type=agent_type,
        conversation_id=conversation_id,
        context=context
    )
    
    if result.success:
        data = result.result or {}
        return EnhancedToolResult(
            status=ToolStatus.SUCCESS,
            message=data.get("message", f"✅ Ação '{tool_name}' executada com sucesso."),
            data=data,
            requires_confirmation=data.get("requires_confirmation", False),
            confirmation_message=data.get("confirmation_message"),
            action_taken=data.get("action_taken", tool_name),
            affected_entities=data.get("affected_entities", [])
        )
    else:
        return EnhancedToolResult(
            status=ToolStatus.ERROR,
            message=f"❌ Erro ao executar '{tool_name}': {result.error}",
            data={"error": result.error}
        )
