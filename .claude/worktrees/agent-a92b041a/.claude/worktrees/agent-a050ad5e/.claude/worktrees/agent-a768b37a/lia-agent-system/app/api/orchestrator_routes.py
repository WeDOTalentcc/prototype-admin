"""
Orchestrator API Routes

FastAPI endpoints for multi-agent orchestration.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from app.orchestrator import Orchestrator
from app.services.llm import LLMService
from app.services.tool_executor_service import (
    ToolExecutorService,
    ToolExecutionRequest,
    ToolExecutionResponse,
    tool_executor_service
)
from app.services.wizard_orchestrator_service import (
    WizardOrchestratorService,
    wizard_orchestrator_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


class OrchestratorRequest(BaseModel):
    """Request model for orchestrator endpoint."""
    user_id: str
    message: str
    conversation_id: Optional[str] = None
    context_type: Optional[str] = None  # 'general', 'wizard', 'pipeline', etc.
    context_id: Optional[str] = None  # ID related to context (e.g., job_id, conversation_id)
    conversation_context: Optional[Dict[str, Any]] = None  # Previous conversation context for memory


class OrchestratorResponse(BaseModel):
    """Response model for orchestrator endpoint."""
    success: bool
    conversation_id: Optional[str] = None
    intent: Optional[str] = None
    agent: Optional[str] = None
    confidence: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ExecuteToolRequest(BaseModel):
    """Request model for tool execution endpoint."""
    tool_name: str
    parameters: Dict[str, Any]
    user_id: str = "authenticated-user"
    context: Optional[Dict[str, Any]] = None


class ExecuteToolResponse(BaseModel):
    """Response model for tool execution endpoint."""
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


class WizardIntentRequest(BaseModel):
    """Request model for wizard intent detection."""
    message: str
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None


class WizardIntentResponse(BaseModel):
    """Response model for wizard intent detection."""
    intent: str
    confidence: float
    entities: Dict[str, Any] = {}
    suggested_tool_call: Optional[Dict[str, Any]] = None
    conversational_response: Optional[str] = None
    injected_context: Optional[str] = None
    conversation_id: Optional[str] = None


# Global orchestrator instance (initialized on startup)
orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Dependency to get orchestrator instance."""
    if orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return orchestrator


def initialize_orchestrator(llm_service: LLMService, db_service=None):
    """Initialize global orchestrator instance."""
    global orchestrator
    orchestrator = Orchestrator(llm_service, db_service)
    logger.info("✅ Orchestrator API initialized")


@router.post("/process", response_model=OrchestratorResponse)
async def process_request(
    request: OrchestratorRequest,
    orch: Orchestrator = Depends(get_orchestrator)
):
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
        
    except Exception as e:
        logger.error(f"❌ Orchestrator API error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    orch: Orchestrator = Depends(get_orchestrator)
):
    """Get conversation state by ID."""
    state = orch.get_conversation_state(conversation_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return state


@router.get("/metrics")
async def get_metrics(orch: Orchestrator = Depends(get_orchestrator)):
    """Get orchestrator metrics for observability."""
    return orch.get_metrics()


@router.get("/health")
async def health_check():
    """Health check endpoint with LLM validation."""
    import os

    llm_status = "unknown"
    llm_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    llm_error = None

    try:
        llm = LLMService()
        test_response = await llm.generate("Respond with OK", provider="claude", max_tokens=5)
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
        "orchestrator": "running" if orchestrator is not None else "not_initialized",
        "llm": llm_status,
        "model": llm_model,
    }
    if llm_error:
        result["llm_error"] = llm_error

    return result


@router.post("/execute-tool", response_model=ExecuteToolResponse)
async def execute_tool(request: ExecuteToolRequest):
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
        
    except Exception as e:
        logger.error(f"❌ Tool execution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wizard/detect-intent", response_model=WizardIntentResponse)
async def detect_wizard_intent(request: WizardIntentRequest):
    """
    Detect intent from wizard message and suggest tool calls.
    
    This endpoint:
    1. Analyzes the user message for actionable intents
    2. Maps detected intents to available tools
    3. Returns suggested tool call with pre-filled parameters
    4. If conversation_id provided, injects conversation context
    
    Request body:
    - message: User message text
    - context: Optional context with job_id, job_data, etc.
    - conversation_id: Optional conversation ID for memory injection
    - user_id: Optional user ID
    """
    try:
        if request.conversation_id:
            from app.database import get_db
            async for db in get_db():
                result = await wizard_orchestrator_service.process_wizard_message_with_memory(
                    db=db,
                    message=request.message,
                    context=request.context,
                    conversation_id=request.conversation_id,
                    user_id=request.user_id,
                    include_response=True
                )
                break
        else:
            result = wizard_orchestrator_service.process_wizard_message(
                message=request.message,
                context=request.context,
                include_response=True
            )
        
        return WizardIntentResponse(
            intent=result.get("intent", "unknown"),
            confidence=result.get("confidence", 0.0),
            entities=result.get("entities", {}),
            suggested_tool_call=result.get("suggested_tool_call"),
            conversational_response=result.get("conversational_response"),
            injected_context=result.get("injected_context"),
            conversation_id=result.get("conversation_id")
        )
        
    except Exception as e:
        logger.error(f"❌ Intent detection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wizard/intents")
async def get_available_intents():
    """Get list of available wizard intents and their tool mappings."""
    return {
        "intents": wizard_orchestrator_service.get_available_intents()
    }


@router.get("/tools")
async def get_available_tools(
    agent_type: Optional[str] = None
):
    """
    Get list of available tools.
    
    Query params:
    - agent_type: Optional filter by agent type
    """
    return {
        "tools": tool_executor_service.get_available_tools(agent_type=agent_type)
    }
