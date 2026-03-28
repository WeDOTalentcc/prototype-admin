"""
LIA Assistant — Graph Orchestration Endpoints.

Sprint 7 split: extracted from lia_assistant.py.

Endpoints:
  POST /lia-assistant/job-wizard/graph-orchestrate
  GET  /lia-assistant/job-wizard/session/{session_id}
  DELETE /lia-assistant/job-wizard/session/{session_id}
  GET  /lia-assistant/job-wizard/graph-info
  GET  /lia-assistant/job-wizard/sessions
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.graph_runner import graph_runner_service
from app.shared.agents.state_machine import WizardStage
from app.domains.recruiter_assistant.services.wizard_analytics_service import (
    wizard_analytics,
    detect_wizard_analytics_command,
)
from app.domains.recruiter_assistant.services.wizard_action_executor import (
    wizard_action_executor,
    detect_wizard_action,
    WIZARD_ACTIONABLE_INTENTS,
)
from app.orchestrator.pending_action import PendingActionState, pending_action_store
from app.orchestrator.action_executor import is_confirmation, is_rejection

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------ #
# Schemas                                                              #
# ------------------------------------------------------------------ #

class GraphOrchestratorRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    company_id: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    user_id: str = "default_user"
    current_stage: Optional[str] = None
    existing_draft: Optional[Dict[str, Any]] = None


class GraphOrchestratorResponse(BaseModel):
    execution_id: str
    session_id: str
    response_text: str
    job_draft: Dict[str, Any]
    current_stage: str
    confidence_scores: Dict[str, float] = {}
    reasoning_steps: List[str] = []
    extracted_fields: Dict[str, Any] = {}
    intent: Optional[str] = None
    is_complete: bool = False
    error: Optional[str] = None
    action_executed: bool = False
    action_type: Optional[str] = None
    action_result: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
    needs_params: bool = False
    pending_action_id: Optional[str] = None
    draft_updates: Optional[Dict[str, Any]] = None


class SessionStateResponse(BaseModel):
    session_id: str
    current_stage: Optional[str] = None
    job_draft: Dict[str, Any] = {}
    confidence_scores: Dict[str, float] = {}
    messages: List[Dict[str, str]] = []
    last_response: Optional[str] = None
    is_complete: bool = False


class GraphInfoResponse(BaseModel):
    nodes: List[str]
    edges: Dict[str, List[str]]
    conditional_edges: Dict[str, List[Dict[str, Any]]]
    start_node: str
    end_node: str
    max_iterations: int


# ------------------------------------------------------------------ #
# Endpoints                                                            #
# ------------------------------------------------------------------ #

@router.post("/job-wizard/graph-orchestrate", response_model=GraphOrchestratorResponse)
async def graph_orchestrate_wizard_message(request: GraphOrchestratorRequest):
    """LangGraph-based orchestrator for job wizard conversations."""
    try:
        session_id = request.session_id or str(uuid4())

        # Phase 0: Check pending wizard action
        pending = pending_action_store.get(session_id)
        if pending:
            if pending.awaiting_confirmation:
                if is_confirmation(request.message):
                    config = WIZARD_ACTIONABLE_INTENTS.get(pending.intent, {})
                    exec_result = await wizard_action_executor._execute(
                        action_id=config.get("action_id", pending.action_id),
                        draft=request.existing_draft or {},
                        session_id=session_id,
                        current_stage=request.current_stage,
                        params=pending.collected_params,
                        context={"user_id": request.user_id},
                    )
                    pending_action_store.remove(session_id)
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text=exec_result.message,
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=[f"action:{pending.intent}:confirmed"],
                        intent=pending.intent,
                        action_executed=True,
                        action_type=exec_result.action_type,
                        action_result=exec_result.data,
                        draft_updates=exec_result.draft_updates,
                    )
                elif is_rejection(request.message):
                    pending_action_store.remove(session_id)
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text="Ok, ação cancelada. Como posso te ajudar com a vaga?",
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=["action:cancelled"],
                        intent="cancelamento",
                    )
                else:
                    pending_action_store.remove(session_id)
            elif pending.missing_params:
                next_param = pending.next_missing_param()
                if next_param:
                    pending.add_param(next_param, request.message.strip())
                    if pending.is_complete:
                        config = WIZARD_ACTIONABLE_INTENTS.get(pending.intent, {})
                        if config.get("requires_confirmation", False):
                            summary = wizard_action_executor._build_confirmation_summary(
                                pending.intent, config, request.existing_draft or {}, pending.collected_params
                            )
                            pending.awaiting_confirmation = True
                            pending.confirmation_summary = summary
                            pending_action_store.save(session_id, pending)
                            return GraphOrchestratorResponse(
                                execution_id=str(uuid4()),
                                session_id=session_id,
                                response_text=summary["message"],
                                job_draft=request.existing_draft or {},
                                current_stage=request.current_stage or "input-evaluation",
                                reasoning_steps=[f"action:{pending.intent}:confirm_needed"],
                                intent=pending.intent,
                                needs_confirmation=True,
                                pending_action_id=pending.pending_id,
                            )
                        exec_result = await wizard_action_executor._execute(
                            action_id=config.get("action_id", pending.action_id),
                            draft=request.existing_draft or {},
                            session_id=session_id,
                            current_stage=request.current_stage,
                            params=pending.collected_params,
                            context={"user_id": request.user_id},
                        )
                        pending_action_store.remove(session_id)
                        return GraphOrchestratorResponse(
                            execution_id=str(uuid4()),
                            session_id=session_id,
                            response_text=exec_result.message,
                            job_draft=request.existing_draft or {},
                            current_stage=request.current_stage or "input-evaluation",
                            reasoning_steps=[f"action:{pending.intent}:executed"],
                            intent=pending.intent,
                            action_executed=True,
                            action_type=exec_result.action_type,
                            action_result=exec_result.data,
                            draft_updates=exec_result.draft_updates,
                        )
                    else:
                        next_param2 = pending.next_missing_param()
                        config = WIZARD_ACTIONABLE_INTENTS.get(pending.intent, {})
                        prompt = config.get("clarification_prompts", {}).get(
                            next_param2, f"Informe: {next_param2}"
                        )
                        pending_action_store.save(session_id, pending)
                        return GraphOrchestratorResponse(
                            execution_id=str(uuid4()),
                            session_id=session_id,
                            response_text=prompt,
                            job_draft=request.existing_draft or {},
                            current_stage=request.current_stage or "input-evaluation",
                            reasoning_steps=[f"action:{pending.intent}:collecting_params"],
                            intent=pending.intent,
                            needs_params=True,
                            pending_action_id=pending.pending_id,
                        )
                else:
                    pending_action_store.remove(session_id)

        # Phase 0.5: Detect wizard action commands
        wizard_action = detect_wizard_action(request.message)
        if wizard_action:
            wz_intent, wz_confidence = wizard_action
            if wz_confidence >= 0.7:
                exec_result = await wizard_action_executor.try_execute(
                    intent=wz_intent,
                    draft=request.existing_draft or {},
                    session_id=session_id,
                    current_stage=request.current_stage,
                    entities={},
                    context={"user_id": request.user_id},
                )
                if exec_result.status == "executed":
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text=exec_result.message,
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=[f"wizard_action:{wz_intent}"],
                        intent=wz_intent,
                        action_executed=True,
                        action_type=exec_result.action_type,
                        action_result=exec_result.data,
                        draft_updates=exec_result.draft_updates,
                    )
                elif exec_result.status == "needs_params":
                    pending_state = PendingActionState(
                        pending_id=exec_result.pending_action_id or str(uuid4()),
                        intent=wz_intent,
                        action_id=exec_result.action_type or "",
                        domain_id="wizard",
                        collected_params=exec_result.data.get("collected_params", {}) if exec_result.data else {},
                        missing_params=exec_result.missing_params or [],
                        conversation_id=session_id,
                    )
                    pending_action_store.save(session_id, pending_state)
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text=exec_result.message,
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=[f"wizard_action:{wz_intent}:needs_params"],
                        intent=wz_intent,
                        needs_params=True,
                        pending_action_id=exec_result.pending_action_id,
                    )
                elif exec_result.status == "needs_confirmation":
                    pending_state = PendingActionState(
                        pending_id=exec_result.pending_action_id or str(uuid4()),
                        intent=wz_intent,
                        action_id=exec_result.action_type or "",
                        domain_id="wizard",
                        collected_params=exec_result.data.get("collected_params", {}) if exec_result.data else {},
                        missing_params=[],
                        conversation_id=session_id,
                        awaiting_confirmation=True,
                        confirmation_summary=exec_result.confirmation_summary,
                    )
                    pending_action_store.save(session_id, pending_state)
                    return GraphOrchestratorResponse(
                        execution_id=str(uuid4()),
                        session_id=session_id,
                        response_text=exec_result.message,
                        job_draft=request.existing_draft or {},
                        current_stage=request.current_stage or "input-evaluation",
                        reasoning_steps=[f"wizard_action:{wz_intent}:needs_confirmation"],
                        intent=wz_intent,
                        needs_confirmation=True,
                        pending_action_id=exec_result.pending_action_id,
                    )

        # Phase 1: Analytics shortcut
        analytics_cmd = detect_wizard_analytics_command(request.message)
        if analytics_cmd and len(request.message.strip().split()) <= 12:
            cmd_type, confidence = analytics_cmd
            if confidence >= 0.8:
                collected_data = request.existing_draft or {}
                current_stage = request.current_stage or "input-evaluation"
                response_text = wizard_analytics.build_status_response(
                    collected_data=collected_data,
                    current_stage=current_stage,
                    command_type=cmd_type,
                )
                return GraphOrchestratorResponse(
                    execution_id=str(uuid4()),
                    session_id=session_id,
                    response_text=response_text,
                    job_draft=collected_data,
                    current_stage=current_stage,
                    reasoning_steps=[f"analytics:{cmd_type}"],
                    intent=cmd_type,
                )

        # Phase 2: Full graph orchestration
        company_id = request.company_id
        try:
            from uuid import UUID as _UUID
            _UUID(company_id)
        except (ValueError, AttributeError):
            from app.core.config import settings
            company_id = settings.DEFAULT_COMPANY_UUID

        result = await graph_runner_service.run_job_wizard(
            session_id=session_id,
            user_message=request.message,
            company_id=company_id,
            user_id=request.user_id,
            existing_draft=request.existing_draft,
            current_stage=request.current_stage,
        )

        return GraphOrchestratorResponse(
            execution_id=result.get("execution_id", ""),
            session_id=result.get("session_id", session_id),
            response_text=result.get("response_text", ""),
            job_draft=result.get("job_draft", {}),
            current_stage=result.get("current_stage", WizardStage.INITIAL.value),
            confidence_scores=result.get("confidence_scores", {}),
            reasoning_steps=result.get("reasoning_steps", []),
            extracted_fields=result.get("extracted_fields", {}),
            intent=result.get("intent"),
            is_complete=result.get("is_complete", False),
            error=result.get("error"),
        )

    except Exception as exc:
        logger.error(f"Error in graph orchestrator: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Graph orchestration failed: {exc}")


@router.get("/job-wizard/session/{session_id}", response_model=SessionStateResponse)
async def get_wizard_session_state(session_id: str):
    """Get the current state of a wizard session."""
    try:
        state = await graph_runner_service.get_session_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        return SessionStateResponse(
            session_id=session_id,
            current_stage=state.get("current_stage"),
            job_draft=state.get("job_draft", {}),
            confidence_scores=state.get("confidence_scores", {}),
            messages=state.get("messages", []),
            last_response=state.get("last_response"),
            is_complete=state.get("is_complete", False),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error getting session state: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to get session state: {exc}")


@router.delete("/job-wizard/session/{session_id}")
async def reset_wizard_session(session_id: str):
    """Reset a wizard session, clearing all state."""
    try:
        was_reset = await graph_runner_service.reset_session(session_id)
        if not was_reset:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        return {"success": True, "message": f"Session {session_id} has been reset", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error resetting session: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to reset session: {exc}")


@router.get("/job-wizard/graph-info", response_model=GraphInfoResponse)
async def get_wizard_graph_info():
    """Get information about the wizard graph structure."""
    try:
        info = graph_runner_service.get_graph_info()
        return GraphInfoResponse(
            nodes=info.get("nodes", []),
            edges=info.get("edges", {}),
            conditional_edges=info.get("conditional_edges", {}),
            start_node=info.get("start_node", ""),
            end_node=info.get("end_node", ""),
            max_iterations=info.get("max_iterations", 10),
        )
    except Exception as exc:
        logger.error(f"Error getting graph info: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to get graph info: {exc}")


@router.get("/job-wizard/sessions")
async def list_wizard_sessions():
    """List all active wizard sessions."""
    try:
        sessions = graph_runner_service.list_active_sessions()
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as exc:
        logger.error(f"Error listing sessions: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {exc}")
