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
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

# Sprint 2 BE-4 — section → actionId mapping canonical
_SECTION_TO_ACTION_ID: dict[str, str] = {
    "profile": "configure_profile",
    "culture": "configure_culture",
    "tech_stack": "configure_tech_stack",
    "benefits": "configure_benefits",
    "workforce": "configure_workforce",
    "policy": "configure_hiring_policy",
    "lia_persona": "configure_persona",
}

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


class StartOnboardingRequest(WeDoBaseModel):
    user_id: int
    account_id: int
    name: str
    email: str
    phone: Optional[str] = None
    magic_link_url: Optional[str] = None
    onboarding_lia_enabled: bool = True
    invited_by: Optional[str] = None


class WebEventRequest(WeDoBaseModel):
    event_type: str
    data: Optional[dict] = None

class ProgressUpdateRequest(WeDoBaseModel):
    phase: str | None = None
    step_id: str | None = None


class ChatMessageRequest(WeDoBaseModel):
    """Typed request for settings extraction chat. Sprint 2 BE-4."""
    message: str


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

            # BE-3: restore settings_extraction_status_json from DB (graceful — column added in mig 214)
            settings_json = None
            try:
                settings_json = row["settings_extraction_status_json"]
            except (KeyError, IndexError):
                pass

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
                settings_extraction_status_json=settings_json,
            )
            return session
    except Exception as e:
        logger.warning(f"[Onboarding] Load session failed: {e}")

    return None


async def _get_orchestrator(db=None, *, tenant_id: str | None = None):
    """Build orchestrator with real dependencies.

    Multi-tenancy (Wave D2.1, 2026-05-27): tenant_id é o company_id resolvido
    pelo endpoint (via Depends(require_company_id) -> JWT). Threaded até o
    llm_factory para que BYOK / per-tenant model config funcione. Callers
    DEVEM passar tenant_id sempre que houver — fallback None é exclusivamente
    para pre-signup onboarding (caso de uso aceito, documentado abaixo).
    """
    from app.services.onboarding_orchestrator import OnboardingOrchestrator

    llm = None
    whatsapp_client = None

    try:
        # Canonical LLM factory (multi-tenant aware). tenant_id=None aceito
        # APENAS no pre-signup onboarding (user ainda nao associado a company);
        # nesse caso, LLM roda com credenciais globais (env), sem PII tenant.
        # Pos-signup (que é o caso dos endpoints aqui — todos passam por
        # require_company_id), tenant_id DEVE ser threaded pelo caller via
        # _get_orchestrator(db, tenant_id=company_id).
        from app.shared.providers.llm_factory import create_tracked_llm
        llm = create_tracked_llm(
            temperature=0.3,
            service_name="OnboardingOrchestrator",
            operation="onboarding_chat",
            max_output_tokens=512,
            tenant_id=tenant_id,
        )
    except Exception:
        pass

    try:
        from app.services.whatsapp_client import WhatsAppClient
        whatsapp_client = WhatsAppClient()
    except ImportError:
        pass

    return OnboardingOrchestrator(db=db, llm=llm, whatsapp_client=whatsapp_client)


# --- Endpoints ---

@router.post("/start")
async def start_onboarding(req: StartOnboardingRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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

    orchestrator = await _get_orchestrator(db, tenant_id=company_id)

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
async def get_onboarding_state(user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
async def handle_web_event(user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], req: WebEventRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Handle web events (first_login, tour steps, action choices)."""
    db = await _get_db()
    session = await _load_session(db, user_id)

    if not session:
        raise HTTPException(status_code=404, detail="No active onboarding session")

    orchestrator = await _get_orchestrator(db, tenant_id=company_id)
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




@router.post("/{user_id}/chat")
async def handle_settings_chat(
    user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    req: ChatMessageRequest,
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id). company_id NOT in payload (REGRA 2).
    """Settings extraction chat for onboarding — Sprint 2 BE-4+BE-5.

    Typed wrapper around handle_settings_extraction_message that synthesizes
    ui_action so the frontend can advance orchestrator steps without polling.
    Returns:
        {phase, message, is_complete, progress_percent, ui_action}
        ui_action: {type: "settings_saved", actionId, section} | {type: "settings_complete"} | None
    """
    db = await _get_db()
    session = await _load_session(db, user_id)
    if not session:
        raise HTTPException(status_code=404, detail="No active onboarding session")

    orchestrator = await _get_orchestrator(db, tenant_id=company_id)
    result = await orchestrator.handle_settings_extraction_message(session, req.message)

    # Synthesize ui_action from extraction state (Sprint 2 BE-5)
    # After handle_settings_extraction_message, session.settings_extraction_status_json
    # was updated by _persist — use last_asked_field to derive section → actionId.
    ui_action: dict | None = None
    if session.settings_extraction_status_json:
        try:
            status_data = json.loads(session.settings_extraction_status_json)
            last_field = status_data.get("last_asked_field")
            if last_field:
                from app.services.onboarding_settings_runner import _resolve_section_for_field
                section = _resolve_section_for_field(last_field)
                action_id = _SECTION_TO_ACTION_ID.get(section)
                if action_id:
                    ui_action = {
                        "type": "settings_saved",
                        "actionId": action_id,
                        "section": section,
                    }
        except Exception as exc:
            logger.debug("[Onboarding] ui_action synthesis failed (non-blocking): %s", exc)

    if result.get("is_complete"):
        ui_action = {"type": "settings_complete"}

    return {**result, "ui_action": ui_action}

@router.get("/{user_id}/context")
async def get_whatsapp_context(user_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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

@router.get("/status")
async def get_onboarding_status(request: Request, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id)
    """Onboarding status for the current authenticated user (JWT sub claim)."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {"active": False, "phase": "none", "progress": 0.0, "activation_state": "inactive"}
    db = await _get_db()
    session = await _load_session(db, user_id)
    if not session:
        return {"active": False, "phase": "none", "progress": 0.0, "activation_state": "inactive"}
    return {
        "active": not session.is_complete,
        "phase": session.phase.value,
        "progress": session.progress,
        "activation_state": "active" if not session.is_complete else "completed",
    }


@router.patch("/progress")
async def update_onboarding_progress(
    request: Request,
    req: ProgressUpdateRequest,
    company_id: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id)
    """Update onboarding progress for the current authenticated user."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {"updated": False, "reason": "no_user_id"}
    db = await _get_db()
    session = await _load_session(db, user_id)
    if not session:
        return {"updated": False, "reason": "no_session"}
    orchestrator = await _get_orchestrator(db, tenant_id=company_id)
    event_data = {}
    if req.step_id:
        event_data["step_id"] = req.step_id
    if req.phase:
        event_data["phase"] = req.phase
    result = await orchestrator.handle_web_event(session, "progress_update", event_data)
    return {"updated": True, **result}


reorder_collection_before_item(router)
