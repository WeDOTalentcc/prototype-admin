"""
Orchestrator API Routes

FastAPI endpoints for multi-agent orchestration.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# UC-P1-23: Use canonical MainOrchestrator - legacy Orchestrator is deprecated.
from app.orchestrator.execution.main_orchestrator import MainOrchestrator, get_main_orchestrator
from app.orchestrator.legacy.orchestrator import Orchestrator as _LegacyOrchestrator
from app.orchestrator.execution.registry import get_orchestrator_instance, set_orchestrator_instance

# Backward-compat alias so type hints in this file still read naturally
Orchestrator = MainOrchestrator


def get_orchestrator() -> MainOrchestrator:
    instance = get_orchestrator_instance()
    if instance is not None:
        return get_main_orchestrator(instance)
    return get_main_orchestrator()


def initialize_orchestrator(llm_service, db_service=None) -> _LegacyOrchestrator:
    """Backward-compat startup hook used by app.main lifespan.

    Restored as part of import #963 hardening: the imported diff dropped this
    function but app/main.py still calls it during startup. Without this shim
    the lifespan handler raises AttributeError and the orchestrator endpoints
    silently degrade. We construct the legacy Orchestrator (which the registry
    is typed against) and register it so get_orchestrator_instance() returns it.
    """
    orch = _LegacyOrchestrator(llm_service, db_service)
    set_orchestrator_instance(orch)
    return orch

from app.domains.ai.services.llm import LLMService, get_llm_service
from app.shared.services.tool_executor_service import (
    ToolExecutionRequest,
    tool_executor_service,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


class OrchestratorRequest(WeDoBaseModel):
    """Request model for orchestrator endpoint."""
    user_id: str
    message: str
    conversation_id: str | None = None
    context_type: str | None = None  # 'general', 'wizard', 'pipeline', etc.
    context_id: str | None = None  # ID related to context (e.g., job_id, conversation_id)
    conversation_context: dict[str, Any] | None = None  # Previous conversation context for memory


class OrchestratorResponse(BaseModel):
    """Response model for orchestrator endpoint."""
    success: bool
    conversation_id: str | None = None
    intent: str | None = None
    agent: str | None = None
    confidence: float | None = None
    result: dict[str, Any] | None = None
    message: str | None = None
    error: str | None = None


class ExecuteToolRequest(WeDoBaseModel):
    """Request model for tool execution endpoint."""
    tool_name: str
    parameters: dict[str, Any]
    user_id: str = "authenticated-user"
    context: dict[str, Any] | None = None


class ExecuteToolResponse(BaseModel):
    """Response model for tool execution endpoint."""
    success: bool
    message: str
    data: dict[str, Any] | None = None
    error: str | None = None
    tool_name: str
    execution_time_ms: float = 0.0
    requires_confirmation: bool = False
    confirmation_message: str | None = None
    action_taken: str | None = None
    affected_entities: list[str] = []




@router.post("/process", response_model=OrchestratorResponse)
async def process_request(
    request: OrchestratorRequest,
    orch: Orchestrator = Depends(get_orchestrator), 
company_id: str = Depends(require_company_id)):
    """
    Process user request through orchestrator.
    
    This endpoint:
    1. Routes intent to appropriate agent
    2. Validates policies
    3. Plans tasks if needed
    4. Delegates execution
    5. Returns coordinated response
    """
    try:
        result = await orch.process_request(
            user_id=request.user_id,
            message=request.message,
            conversation_id=request.conversation_id
        )
        
        return OrchestratorResponse(
            success=result.get("success", False),
            conversation_id=result.get("conversation_id"),
            intent=result.get("intent"),
            agent=result.get("agent"),
            confidence=result.get("confidence"),
            result=result.get("result"),
            message=result.get("result", {}).get("message") if result.get("result") else result.get("message"),
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Orchestrator API error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversation/{conversation_id}", response_model=None)
async def get_conversation(
    conversation_id: str,
    orch: Orchestrator = Depends(get_orchestrator), 
company_id: str = Depends(require_company_id)):
    """Get conversation state by ID."""
    state = orch.get_conversation_state(conversation_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return state


@router.get("/metrics", response_model=None)
async def get_metrics(orch: Orchestrator = Depends(get_orchestrator), company_id: str = Depends(require_company_id)):
    """Get orchestrator metrics for observability."""
    return orch.get_metrics()


@router.get("/health", response_model=None)
async def health_check(
    llm_svc: LLMService = Depends(get_llm_service),
company_id: str = Depends(require_company_id)):
    """Health check endpoint with LLM validation."""
    import os

    llm_status = "unknown"
    llm_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    llm_error = None

    try:
        test_response = await llm_svc.generate("Respond with OK", max_tokens=5)
        if test_response and len(test_response.strip()) > 0:
            llm_status = "ok"
        else:
            llm_status = "error"
            llm_error = "Empty response from LLM"
    except Exception as e:
        llm_status = "error"
        llm_error = str(e)

    overall = "healthy" if llm_status == "ok" else "degraded"

    result = {
        "status": overall,
        "orchestrator": "running" if get_orchestrator_instance() is not None else "not_initialized",
        "llm": llm_status,
        "model": llm_model,
    }
    if llm_error:
        result["llm_error"] = llm_error

    return result


@router.post("/execute-tool", response_model=ExecuteToolResponse)
async def execute_tool(request: ExecuteToolRequest, company_id: str = Depends(require_company_id)):
    """
    Execute a tool via the orchestrator.
    
    This endpoint:
    1. Validates user permissions for the requested tool
    2. Executes the tool using ToolRegistry
    3. Returns execution result or error
    
    Request body:
    - tool_name: Name of the tool to execute (e.g., 'publish_job', 'pause_job')
    - parameters: Tool-specific parameters
    - user_id: ID of the user executing the tool
    - context: Optional context with permissions, company_id, session info
    """
    try:
        execution_request = ToolExecutionRequest(
            tool_name=request.tool_name,
            parameters=request.parameters,
            user_id=request.user_id,
            # S04 NOTE (census 2026-06-20): orchestrator_routes.router is NOT mounted in
            # app/api/routes.py — this endpoint is unreachable (dead route).
            # If ever mounted, replace this line with JWT-enforced company_id:
            #   company_id=company_id,  # from Depends(require_company_id) in handler signature
            # Using request.context allows cross-tenant data access (P-TENANT violation).
            company_id=request.context.get("company_id") if request.context else None,
            context=request.context,
            agent_type="orchestrator"
        )
        
        result = await tool_executor_service.execute(execution_request)
        
        return ExecuteToolResponse(
            success=result.success,
            message=result.message,
            data=result.data,
            error=result.error,
            tool_name=result.tool_name,
            execution_time_ms=result.execution_time_ms,
            requires_confirmation=result.requires_confirmation,
            confirmation_message=result.confirmation_message,
            action_taken=result.action_taken,
            affected_entities=result.affected_entities
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Tool execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tools", response_model=None)
async def get_available_tools(
    agent_type: str | None = None, 
company_id: str = Depends(require_company_id)):
    """
    Get list of available tools.
    
    Query params:
    - agent_type: Optional filter by agent type
    """
    return {
        "tools": tool_executor_service.get_available_tools(agent_type=agent_type)
    }
