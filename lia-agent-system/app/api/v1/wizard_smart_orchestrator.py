"""
Wizard Smart Orchestrator API - REST wrapper over canonical WizardSessionService.

Task #1085 / T2 superseded the legacy JobWizardGraph engine. This endpoint is
the REST counterpart of the canonical WebSocket flow in agent_chat_ws.py:1108,
delegating to ``WizardSessionService.process_message(...)`` which drives the
12-stage JobCreationGraph (intake → jd_enrichment → bigfive → salary →
competency → wsi_questions → eligibility → review → publish → calibration →
handoff → done).

Frontend contract (plataforma-lia/src/services/chat-api.ts:188) is preserved:
same SmartOrchestrateRequest/SmartOrchestrateResponse schemas.
"""
import logging
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.security.require_company_id import require_company_id
from app.shared.sessions.thread_id import derive_thread_id
from app.shared.tenant_session import create_session_id
from app.shared.types import WeDoBaseModel

router = APIRouter()

# Pendencia 4 (2026-05-27): soft deprecation marker.
# Frontend proxy + caller deletados no Fix F (commit 3f1d34b42). Tests E2E
# em tests/e2e/test_wizard_job_creation.py (7 callers) ainda dependem deste
# endpoint -- mantemos canonical mas sinalizamos deprecation para observar
# uso real em prod e potenciais callers externos (mobile, webhook, scripts)
# antes de delete em sprint dedicada.
_DEPRECATION_MODULE = "wizard_smart_orchestrator"
_DEPRECATION_SUNSET = "2026-07-01"  # sunset target (revisar em sprint)


def _emit_smart_orchestrate_deprecation_log(
    endpoint_name: str,
    company_id: str | None,
    user_agent: str | None,
) -> None:
    """Emit structured 'wizard.smart_orchestrate.deprecated_call' log."""
    logger.warning(
        "wizard.smart_orchestrate.deprecated_call",
        extra={
            "tenant.company_id": company_id,
            "caller": f"{_DEPRECATION_MODULE}.{endpoint_name}",
            "user_agent": user_agent,
            "sunset_date": _DEPRECATION_SUNSET,
            "canonical_replacement": "WS /ws/agent-chat with domain=job_creation",
        },
    )
logger = logging.getLogger(__name__)


# Frontend uses the 9-stage UI taxonomy. Backend canonical (JobCreationGraph)
# uses the 12-stage WizardStage from app/domains/job_creation/state.py.
# Mappings are best-effort: when frontend sends an ambiguous stage we let the
# graph's prior_state decide the actual stage (frontend hint is advisory).
FRONTEND_TO_BACKEND_STAGE: dict[str, str] = {
    "initial": "intake",
    "input-evaluation": "intake",
    "title-department": "intake",
    "job-summary": "jd_enrichment",
    "jd-enrichment": "jd_enrichment",
    "job_summary": "jd_enrichment",
    "salary": "salary",
    "competencies": "competency",
    "wsi-questions": "wsi_questions",
    "screening": "wsi_questions",
    "review-publish": "review",
    "review": "review",
    "complete": "done",
}

BACKEND_TO_FRONTEND_STAGE: dict[str, str] = {
    "intake": "input-evaluation",
    "jd_enrichment": "jd-enrichment",
    "bigfive": "competencies",
    "salary": "salary",
    "competency": "competencies",
    "wsi_questions": "wsi-questions",
    "eligibility": "review-publish",
    "review": "review-publish",
    "publish": "review-publish",
    "calibration": "review-publish",
    "handoff": "complete",
    "done": "complete",
}


class SmartOrchestrateRequest(WeDoBaseModel):
    """Request for smart orchestration using the canonical wizard graph.

    Two modes:

    1. **Normal turn** (default): user sends free text. Handler calls
       ``WizardSessionService.process_message(...)`` → drives the
       JobCreationGraph forward.

    2. **HITL gate resume** — REMOVED (Fase 8 A2). Fields kept for
       backward compat; handler ignores them.
       wsi_questions). Handler calls
       ``wizard_gate_service.resume_gate(...)`` → unblocks the graph at the
       ``langgraph.types.interrupt()`` checkpoint. The ``message`` field is
       ignored in this mode (the gate decision is what matters).

    The two modes are mutually exclusive: ``approval_decision`` requires
    ``pending_id``, and presence of either short-circuits the normal-turn
    path.
    """
    message: str = Field(
        default="",
        description="User message to process. Ignored when approval_decision is set."
    )
    current_stage: str = Field(
        default="input-evaluation",
        description="Current wizard stage (frontend format, advisory)"
    )
    collected_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Data already collected in the wizard (carried as right_panel_form context)"
    )
    conversation_history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Previous conversation messages"
    )
    conversation_id: str | None = Field(
        None,
        description="Conversation ID for context continuity"
    )
    user_id: str | None = Field(None, description="User ID override (ignored; comes from JWT)")

    # ── HITL gate resume signaling ────────────────────────────────────────
    # Frontend sets these when the user clicks Approve/Reject on a pending
    # wizard gate card. Mirrors the WS pattern in agent_chat_ws.py:683-687.
    approval_decision: Literal["approved", "rejected"] | None = Field(
        None,
        description=(
            "When set, this request is a HITL gate resume — NOT a new "
            "message. Backend invokes wizard_gate_service.resume_gate() "
            "instead of process_message(). Requires pending_id."
        ),
    )
    pending_id: str | None = Field(
        None,
        description=(
            "UUID4 of the hitl_service.request_approval() that produced "
            "the pending gate. Required when approval_decision is set."
        ),
    )
    approval_comment: str | None = Field(
        None,
        description="Optional approver comment, persisted in audit trail.",
    )

    def hitl_validation_error(self) -> str | None:
        """Return canonical error string if HITL fields are inconsistent.

        Pydantic-level validator was avoided here because the global
        ``ResponseEnvelopeMiddleware`` cannot JSON-serialize ``ValueError``
        bubbled from a model_validator. Handler invokes this and returns
        a structured 422 response when non-None.
        """
        if (self.approval_decision is None) ^ (self.pending_id is None):
            return (
                "approval_decision and pending_id must be provided together. "
                "Set both to resume a HITL gate, or neither for a normal turn."
            )
        return None


class SmartOrchestrateResponse(BaseModel):
    """Response from smart orchestration."""
    success: bool = Field(..., description="Whether processing succeeded")
    lia_message: str = Field(default="", description="LIA's response generated by LLM")
    detected_criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted/accumulated fields from job_draft"
    )
    next_stage: str | None = Field(
        None,
        description="Next stage if transition occurred (frontend format)"
    )
    auto_transition: bool = Field(default=False)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning_steps: list[str] = Field(default_factory=list)
    intent: str | None = Field(None, description="Detected user intent")
    error: str | None = Field(None, description="Error message if processing failed")
    awaiting_confirmation: bool = Field(
        default=False,
        description="True when wizard is paused at a HITL gate (jd_enrichment, wsi_questions)"
    )
    job_vacancy_id: str | None = Field(None)
    job_published: bool = Field(default=False)
    conversation_id: str | None = Field(
        None,
        description="Send back in next request to maintain multi-turn memory"
    )


def _map_frontend_to_backend_stage(frontend_stage: str) -> str:
    return FRONTEND_TO_BACKEND_STAGE.get(frontend_stage, "intake")


def _map_backend_to_frontend_stage(backend_stage: str | None) -> str | None:
    if not backend_stage:
        return None
    return BACKEND_TO_FRONTEND_STAGE.get(backend_stage, "input-evaluation")


@router.post("/smart-orchestrate", response_model=SmartOrchestrateResponse)
async def smart_orchestrate(
    request: SmartOrchestrateRequest,
    current_user: User = Depends(get_current_user_or_demo),
    company_id: str = Depends(require_company_id),
) -> SmartOrchestrateResponse:
    """
    Execute the canonical JobCreationGraph via WizardSessionService.

    REST counterpart of the WebSocket wizard path in agent_chat_ws.py:1108.
    Same service, same graph, same checkpointer — just synchronous request/
    response instead of streaming WS frames.

    Pendencia 4 (2026-05-27) soft deprecation: frontend proxy + caller
    deletados no Fix F. Endpoint mantido pra 7 tests E2E + potenciais
    callers externos. Log estruturado emitido por chamada para rastreio.
    Sunset target: _DEPRECATION_SUNSET (revisar em sprint dedicada).
    """
    # Pendencia 4 soft deprecation -- emit log para rastreio de uso real.
    _emit_smart_orchestrate_deprecation_log(
        endpoint_name="smart_orchestrate",
        company_id=company_id,
        user_agent=None,  # endpoint sem Request param; OK
    )

    hitl_err = request.hitl_validation_error()
    if hitl_err is not None:
        raise HTTPException(status_code=422, detail=hitl_err)

    user_id = str(current_user.id) if getattr(current_user, "id", None) else "anonymous"
    session_id = request.conversation_id or create_session_id(company_id)
    thread_id = derive_thread_id(company_id, session_id)

    logger.info(
        "smart_orchestrate request: stage=%s msg_len=%d session=%s thread=%s",
        request.current_stage, len(request.message), session_id, thread_id,
    )

    context: dict[str, Any] = {
        # WizardSessionService carries these context keys forward into state:
        # right_panel_form, attached_file_text, tenant_context_snippet.
        # Frontend's collected_data maps to right_panel_form (the wizard form
        # state mirrored from UI).
        "right_panel_form": request.collected_data or {},
        "conversation_history": request.conversation_history or [],
        "frontend_stage_hint": _map_frontend_to_backend_stage(request.current_stage),
    }

    try:
        from app.domains.job_creation.services.wizard_session_service import (
            WizardSessionService,
        )

        recruiter_message, stage_payload, tokens_emitted = (
            await WizardSessionService.process_message(
                thread_id=thread_id,
                user_message=request.message,
                user_id=user_id,
                company_id=company_id,
                session_id=session_id,
                context=context,
                on_token=None,
            )
        )

        stage_payload = stage_payload or {}
        backend_stage = stage_payload.get("stage") or stage_payload.get("current_stage")
        next_stage = _map_backend_to_frontend_stage(backend_stage)
        # Canonical: `requires_approval` is the structured HITL gate signal
        # (jd_enrichment, wsi_questions). `awaiting_confirmation` kept for
        # legacy callers that may inspect both.
        awaiting = bool(
            stage_payload.get("requires_approval")
            or stage_payload.get("awaiting_confirmation")
        )
        job_draft = stage_payload.get("data") or stage_payload.get("job_draft") or {}

        detected_criteria: dict[str, Any] = {}
        # Drop the LIA reply itself when the service mirrors it under
        # data["message"] — it already comes through `lia_message`.
        _skip_keys = {"message"}
        for key, value in (job_draft or {}).items():
            if value is None or key in _skip_keys:
                continue
            if key not in request.collected_data or request.collected_data.get(key) != value:
                detected_criteria[key] = value

        response = SmartOrchestrateResponse(
            success=True,
            lia_message=recruiter_message or "",
            detected_criteria=detected_criteria,
            next_stage=next_stage,
            auto_transition=bool(stage_payload.get("auto_transition", False)) and not awaiting,
            tool_results=stage_payload.get("tool_results") or [],
            confidence=float(stage_payload.get("confidence") or 0.95),
            reasoning_steps=stage_payload.get("reasoning_steps") or [],
            intent=stage_payload.get("intent"),
            awaiting_confirmation=awaiting,
            job_vacancy_id=(
                # Sprint O.1 canonical: WizardSessionService injects job_vacancy_id
                # into stage_payload from result["job_id"] (top-level state). The
                # data.* fallbacks below cover legacy nodes that still set job_id
                # only inside ws_stage_payload.data (publish_node:graph.py:2371).
                stage_payload.get("job_vacancy_id")
                or (stage_payload.get("data") or {}).get("job_id")
                or (stage_payload.get("data") or {}).get("job_vacancy_id")
                or (stage_payload.get("data") or {}).get("id")
            ),
            job_published=(
                bool(stage_payload.get("job_published", False))
                or (backend_stage in ("publish", "calibration", "handoff", "done"))
            ),
            conversation_id=session_id,
        )

        logger.info(
            "smart_orchestrate complete: session=%s backend_stage=%s next=%s awaiting=%s tokens=%d",
            session_id, backend_stage, next_stage, awaiting, tokens_emitted,
        )
        return response

    except Exception as exc:
        logger.exception("smart_orchestrate failed for session=%s: %s", session_id, exc)
        return SmartOrchestrateResponse(
            success=False,
            lia_message="Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.",
            detected_criteria={},
            next_stage=None,
            auto_transition=False,
            tool_results=[],
            confidence=0.0,
            reasoning_steps=[f"Error: {type(exc).__name__}: {exc}"],
            intent=None,
            error=str(exc),
            awaiting_confirmation=False,
            job_vacancy_id=None,
            job_published=False,
            conversation_id=session_id,
        )



@router.get("/stage-mapping", response_model=None)
async def get_stage_mapping(
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    """Debug endpoint: frontend↔backend stage mapping."""
    _emit_smart_orchestrate_deprecation_log(
        endpoint_name="stage_mapping",
        company_id=company_id,
        user_agent=None,  # debug endpoint, no request param available
    )

    return {
        "frontend_to_backend": FRONTEND_TO_BACKEND_STAGE,
        "backend_to_frontend": BACKEND_TO_FRONTEND_STAGE,
        "backend_stages": [
            "intake", "jd_enrichment", "bigfive", "salary", "competency",
            "wsi_questions", "eligibility", "review", "publish",
            "calibration", "handoff", "done",
        ],
    }
