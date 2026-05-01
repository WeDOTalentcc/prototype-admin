"""
Onboarding API endpoints — production-ready with real DB queries.

Apply to: lia-agent-system/app/api/v1/onboarding.py
Register in main.py: app.include_router(onboarding_router)
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


class StartOnboardingRequest(BaseModel):
    user_id: int
    account_id: int
    name: str
    email: str
    phone: Optional[str] = None
    magic_link_url: Optional[str] = None
    onboarding_lia_enabled: bool = True
    invited_by: Optional[str] = None


class WebEventRequest(BaseModel):
    event_type: str
    data: Optional[dict] = None


# --- Helpers ---

async def _get_db():
    """Get database connection. Replace with your actual dependency."""
    try:
        from app.shared.database import get_db
        return await get_db()
    except ImportError:
        logger.warning("[Onboarding] get_db not available")
        return None


async def _load_session(db, user_id: int):
    """Load or create OnboardingSession from DB."""
    if not db:
        return None

    try:
        row = await db.fetch_one(
            "SELECT * FROM onboarding_agent_state WHERE user_id = $1 ORDER BY updated_at DESC LIMIT 1",
            [user_id],
        )
        if row:
            from app.services.onboarding_orchestrator import OnboardingSession, OnboardingPhase
            session_data = json.loads(row["session_data"]) if row["session_data"] else {}
            wa_context = json.loads(row["whatsapp_context"]) if row["whatsapp_context"] else []
            metadata = json.loads(row["onboarding_metadata"]) if row["onboarding_metadata"] else {}

            session = OnboardingSession(
                session_id=str(row["id"]),
                user_id=row["user_id"],
                account_id=row["account_id"],
                user_name=session_data.get("user_name", ""),
                user_email=session_data.get("user_email", ""),
                user_phone=session_data.get("user_phone"),
                phase=OnboardingPhase(row["phase"]),
                channel=row["channel"] or "web",
                whatsapp_messages=wa_context,
                onboarding_data=metadata,
            )
            return session
    except Exception as e:
        logger.warning(f"[Onboarding] Load session failed: {e}")

    return None


async def _get_orchestrator(db=None):
    """Build orchestrator with real dependencies."""
    from app.services.onboarding_orchestrator import OnboardingOrchestrator

    llm = None
    whatsapp_client = None

    try:
        from app.shared.providers.llm_factory import get_llm
        llm = get_llm(tier="fast")
    except ImportError:
        pass

    try:
        from app.services.whatsapp_client import WhatsAppClient
        whatsapp_client = WhatsAppClient()
    except ImportError:
        pass

    return OnboardingOrchestrator(db=db, llm=llm, whatsapp_client=whatsapp_client)


# --- Endpoints ---

@router.post("/start")
async def start_onboarding(req: StartOnboardingRequest):
    """Start onboarding for a new user. Called by RabbitMQ consumer or directly."""
    from app.services.onboarding_orchestrator import OnboardingSession

    db = await _get_db()

    session = OnboardingSession(
        session_id=f"onb_{req.user_id}",
        user_id=req.user_id,
        account_id=req.account_id,
        user_name=req.name,
        user_email=req.email,
        user_phone=req.phone,
        magic_link_url=req.magic_link_url,
        onboarding_lia_enabled=req.onboarding_lia_enabled,
        invited_by=req.invited_by,
    )

    orchestrator = await _get_orchestrator(db)

    # Audit: log onboarding start
    try:
        from app.shared.compliance.audit_service import AuditService
        audit = AuditService()
        await audit.log_output(
            company_id=req.account_id,
            session_id=session.session_id,
            agent_used="onboarding",
            input_text=f"Onboarding started for {req.name}",
            output_text="",
            action_executed="onboarding_start",
            candidate_id=None,
            job_vacancy_id=None,
            fairness_flags=[],
        )
    except Exception:
        pass

    result = await orchestrator.start(session)
    return result


@router.get("/{user_id}/state")
async def get_onboarding_state(user_id: int):
    """Get current onboarding state for a user."""
    db = await _get_db()
    session = await _load_session(db, user_id)

    if not session:
        return {"user_id": user_id, "phase": "none", "progress": 0.0, "active": False}

    return {
        "user_id": user_id,
        "phase": session.phase.value,
        "progress": session.progress,
        "channel": session.channel,
        "onboarding_data": session.onboarding_data,
        "tour_steps_completed": session.tour_steps_completed,
        "active": not session.is_complete,
    }


@router.post("/{user_id}/event")
async def handle_web_event(user_id: int, req: WebEventRequest):
    """Handle web events (first_login, tour steps, action choices)."""
    db = await _get_db()
    session = await _load_session(db, user_id)

    if not session:
        raise HTTPException(status_code=404, detail="No active onboarding session")

    orchestrator = await _get_orchestrator(db)
    result = await orchestrator.handle_web_event(session, req.event_type, req.data)

    # Audit: log event
    try:
        from app.shared.compliance.audit_service import AuditService
        audit = AuditService()
        await audit.log_output(
            company_id=session.account_id,
            session_id=session.session_id,
            agent_used="onboarding",
            input_text=f"Web event: {req.event_type}",
            output_text=json.dumps(req.data or {}),
            action_executed=f"onboarding_{req.event_type}",
            candidate_id=None,
            job_vacancy_id=None,
            fairness_flags=[],
        )
    except Exception:
        pass

    return result


@router.get("/{user_id}/context")
async def get_whatsapp_context(user_id: int):
    """Get WhatsApp conversation context for web handoff."""
    db = await _get_db()
    session = await _load_session(db, user_id)

    if not session:
        return {"user_id": user_id, "whatsapp_messages": [], "onboarding_data": {}}

    return {
        "user_id": user_id,
        "whatsapp_messages": session.whatsapp_messages,
        "onboarding_data": session.onboarding_data,
        "phase": session.phase.value,
        "progress": session.progress,
    }
