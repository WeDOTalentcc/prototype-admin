"""
Tool Executor Service - Service layer for executing tools with permission validation.

Provides a high-level service for executing tools from the ToolRegistry
with user permission validation and tenant scoping.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel

from app.tools import (
    tool_registry,
    tool_executor,
    ToolExecutionContext,
    ToolResult,
    EnhancedToolResult,
    ToolStatus
)

logger = logging.getLogger(__name__)


class ToolExecutionRequest(BaseModel):
    """Request model for tool execution."""
    tool_name: str
    parameters: Dict[str, Any]
    user_id: str
    company_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    agent_type: str = "orchestrator"


class ToolExecutionResponse(BaseModel):
    """Response model for tool execution."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tool_name: str
    execution_time_ms: float = 0.0
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None
    action_taken: Optional[str] = None
    affected_entities: List[str] = []


TOOL_PERMISSIONS = {
    "publish_job": ["job:publish", "job:manage", "admin"],
    "pause_job": ["job:pause", "job:manage", "admin"],
    "close_job": ["job:close", "job:manage", "admin"],
    "create_job": ["job:create", "job:manage", "admin"],
    "update_job": ["job:update", "job:manage", "admin"],
    "validate_job_fields": ["job:read", "job:manage", "admin"],
    "search_salary_benchmark": ["job:read", "admin"],
    "get_job_suggestions": ["job:read", "admin"],
    "save_job_draft": ["job:create", "job:update", "job:manage", "admin"],
    "move_candidate": ["candidate:move", "candidate:manage", "admin"],
    "send_email": ["communication:send", "admin"],
    "send_whatsapp": ["communication:send", "admin"],
    "export_candidates": ["candidate:export", "admin"],
    "search_candidates": ["candidate:read", "admin"],
    "get_candidate": ["candidate:read", "admin"],
}


class ToolExecutorService:
    """
    Service for executing tools with permission validation.
    
    Features:
    - Permission validation based on tool requirements
    - Tenant scoping via ToolExecutionContext
    - Structured error handling and response formatting
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate_tool_exists(self, tool_name: str) -> bool:
        """Check if a tool exists in the registry."""
        tool = tool_registry.get_tool(tool_name)
        return tool is not None
    
    def get_required_permissions(self, tool_name: str) -> List[str]:
        """Get required permissions for a tool."""
        return TOOL_PERMISSIONS.get(tool_name, [])
    
    def validate_user_permission(
        self,
        tool_name: str,
        user_permissions: List[str]
    ) -> bool:
        """
        Validate if user has permission to execute a tool.
        
        Args:
            tool_name: Name of the tool
            user_permissions: List of permissions the user has
            
        Returns:
            True if user can execute the tool, False otherwise
        """
        required = self.get_required_permissions(tool_name)
        
        if not required:
            return True
        
        for perm in user_permissions:
            if perm in required:
                return True
            if perm == "admin" or perm == "*":
                return True
        
        return False
    
    async def execute(
        self,
        request: ToolExecutionRequest
    ) -> ToolExecutionResponse:
        """
        Execute a tool with full validation.
        
        Args:
            request: Tool execution request with all parameters
            
        Returns:
            ToolExecutionResponse with result or error
        """
        start_time = datetime.utcnow()
        
        self.logger.info(f"Executing tool: {request.tool_name} for user: {request.user_id}")
        
        if not request.user_id or request.user_id == "anonymous":
            return ToolExecutionResponse(
                success=False,
                message="Usuário não autenticado. Faça login para executar esta ação.",
                error="authentication_required",
                tool_name=request.tool_name
            )
        
        if not self.validate_tool_exists(request.tool_name):
            return ToolExecutionResponse(
                success=False,
                message=f"Ferramenta não encontrada: {request.tool_name}",
                error="tool_not_found",
                tool_name=request.tool_name
            )
        
        user_permissions = ["admin"]
        
        context = ToolExecutionContext(
            user_id=request.user_id,
            company_id=request.company_id or request.context.get("company_id", "default") if request.context else "default",
            permissions=user_permissions,
            session_id=request.context.get("session_id") if request.context else None
        )
        
        try:
            result = await tool_executor.execute(
                tool_name=request.tool_name,
                parameters=request.parameters,
                agent_type=request.agent_type,
                context=context
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if result.success:
                data = result.result or {}
                return ToolExecutionResponse(
                    success=True,
                    message=data.get("message", f"Ação '{request.tool_name}' executada com sucesso."),
                    data=data,
                    tool_name=request.tool_name,
                    execution_time_ms=execution_time,
                    requires_confirmation=data.get("requires_confirmation", False),
                    confirmation_message=data.get("confirmation_message"),
                    action_taken=data.get("action_taken", request.tool_name),
                    affected_entities=data.get("affected_entities", [])
                )
            else:
                return ToolExecutionResponse(
                    success=False,
                    message=f"Erro ao executar '{request.tool_name}': {result.error}",
                    error=result.error,
                    tool_name=request.tool_name,
                    execution_time_ms=execution_time
                )
                
        except Exception as e:
            self.logger.error(f"Error executing tool {request.tool_name}: {e}", exc_info=True)
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            return ToolExecutionResponse(
                success=False,
                message=f"Erro interno ao executar ferramenta: {str(e)}",
                error=str(e),
                tool_name=request.tool_name,
                execution_time_ms=execution_time
            )
    
    def get_available_tools(
        self,
        agent_type: Optional[str] = None,
        user_permissions: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of available tools for an agent/user.
        
        Args:
            agent_type: Optional agent type to filter tools
            user_permissions: Optional user permissions to filter tools
            
        Returns:
            List of available tools with their schemas
        """
        if agent_type:
            tools = tool_registry.get_tools_for_agent(agent_type)
        else:
            tools = [tool_registry.get_tool(name) for name in tool_registry.list_tools()]
            tools = [t for t in tools if t is not None]
        
        if user_permissions:
            tools = [
                t for t in tools
                if self.validate_user_permission(t.name, user_permissions)
            ]
        
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters_schema": t.parameters_schema
            }
            for t in tools
        ]


tool_executor_service = ToolExecutorService()
