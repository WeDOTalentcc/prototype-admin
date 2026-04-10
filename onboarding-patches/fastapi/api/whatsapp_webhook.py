"""
WhatsApp webhook handlers for Twilio — production-ready.

Apply to: lia-agent-system/app/api/v1/whatsapp_webhook.py
Register in main.py: app.include_router(whatsapp_router)
"""

import hashlib
import hmac
import json
import logging
import os
from urllib.parse import urlencode
from fastapi import APIRouter, Request, Response, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])

TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")


def verify_twilio_signature(request_url: str, params: dict, signature: str) -> bool:
    """Verify Twilio webhook signature to prevent spoofing."""
    if not TWILIO_AUTH_TOKEN:
        logger.warning("[WhatsApp] No TWILIO_AUTH_TOKEN set — skipping signature check")
        return True  # Allow in dev

    # Build data string: URL + sorted params
    data = request_url
    for key in sorted(params.keys()):
        data += key + params[key]

    # HMAC-SHA1
    expected = hmac.new(
        TWILIO_AUTH_TOKEN.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha1,
    ).digest()

    import base64
    expected_b64 = base64.b64encode(expected).decode("utf-8")
    return hmac.compare_digest(expected_b64, signature)


async def _find_session_by_phone(phone: str):
    """Look up onboarding session by phone number."""
    try:
        from app.shared.database import get_db
        db = await get_db()
        row = await db.fetch_one(
            """
            SELECT oas.* FROM onboarding_agent_state oas
            JOIN whatsapp_sessions ws ON ws.user_id = oas.user_id
            WHERE ws.phone_number = $1 AND ws.session_active = true
            ORDER BY ws.updated_at DESC LIMIT 1
            """,
            [phone],
        )
        if row:
            from app.services.onboarding_orchestrator import OnboardingSession, OnboardingPhase
            session_data = json.loads(row["session_data"]) if row["session_data"] else {}
            wa_context = json.loads(row["whatsapp_context"]) if row["whatsapp_context"] else []
            metadata = json.loads(row["onboarding_metadata"]) if row["onboarding_metadata"] else {}

            return OnboardingSession(
                session_id=str(row["id"]),
                user_id=row["user_id"],
                account_id=row["account_id"],
                user_name=session_data.get("user_name", ""),
                user_email=session_data.get("user_email", ""),
                user_phone=phone,
                phase=OnboardingPhase(row["phase"]),
                channel="whatsapp",
                whatsapp_messages=wa_context,
                onboarding_data=metadata,
            )
    except Exception as e:
        logger.warning(f"[WhatsApp] Session lookup failed: {e}")
    return None


async def _get_orchestrator():
    """Build orchestrator with dependencies."""
    from app.services.onboarding_orchestrator import OnboardingOrchestrator

    db, llm, wa_client = None, None, None

    try:
        from app.shared.database import get_db
        db = await get_db()
    except ImportError:
        pass
    try:
        from app.shared.providers.llm_factory import get_llm
        llm = get_llm(tier="fast")
    except ImportError:
        pass
    try:
        from app.services.whatsapp_client import WhatsAppClient
        wa_client = WhatsAppClient()
    except ImportError:
        pass

    return OnboardingOrchestrator(db=db, llm=llm, whatsapp_client=wa_client), wa_client


@router.post("/webhook")
async def whatsapp_message_webhook(request: Request):
    """Twilio webhook for incoming WhatsApp messages."""
    body = await request.form()
    params = dict(body)

    # Verify Twilio signature
    signature = request.headers.get("X-Twilio-Signature", "")
    request_url = str(request.url)
    if not verify_twilio_signature(request_url, params, signature):
        logger.warning("[WhatsApp] Invalid Twilio signature — rejecting")
        raise HTTPException(status_code=403, detail="Invalid signature")

    from_number = params.get("From", "").replace("whatsapp:", "")
    message_body = params.get("Body", "")
    message_sid = params.get("MessageSid", "")

    logger.info(f"[WhatsApp] Incoming from {from_number}: {message_body[:50]}...")

    if not from_number or not message_body:
        return Response(status_code=200)

    # Find session
    session = await _find_session_by_phone(from_number)
    if not session:
        logger.info(f"[WhatsApp] Unknown number: {from_number}")
        return Response(status_code=200)

    # Route to orchestrator
    orchestrator, wa_client = await _get_orchestrator()
    result = await orchestrator.handle_whatsapp_message(session, message_body)

    # Send response
    if result.get("response_text") and wa_client:
        await wa_client.send_message(from_number, result["response_text"])

        # Send buttons if present
        if result.get("buttons"):
            await wa_client.send_buttons(
                from_number,
                "Escolha uma opcao:",
                result["buttons"],
            )

        # Trigger Flow if flagged
        if result.get("trigger_flow"):
            flow_id = os.getenv("WHATSAPP_ONBOARDING_FLOW_ID", "")
            if flow_id:
                await wa_client.trigger_flow(from_number, flow_id)

        # Send CTA if present
        if result.get("cta_url"):
            await wa_client.send_cta(
                from_number,
                "Clique para acessar:",
                result["cta_url"],
                "Abrir plataforma",
            )

    # Audit log
    try:
        from app.shared.compliance.audit_service import AuditService
        audit = AuditService()
        await audit.log_output(
            company_id=session.account_id,
            session_id=session.session_id,
            agent_used="onboarding_whatsapp",
            input_text=message_body[:500],
            output_text=(result.get("response_text") or "")[:500],
            action_executed=f"whatsapp_{result.get('action', 'unknown')}",
            candidate_id=None,
            job_vacancy_id=None,
            fairness_flags=[],
        )
    except Exception:
        pass

    return Response(status_code=200)


@router.post("/flow-webhook")
async def whatsapp_flow_webhook(request: Request):
    """WhatsApp Flow completion webhook."""
    # Verify Twilio signature
    raw_body = await request.body()
    signature = request.headers.get("X-Twilio-Signature", "")
    if TWILIO_AUTH_TOKEN and not verify_twilio_signature(str(request.url), {}, signature):
        logger.warning("[WhatsApp Flow] Invalid Twilio signature — rejecting")
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        body = json.loads(raw_body)
    except Exception:
        body = {}

    phone_number = body.get("phone_number", "").replace("whatsapp:", "")
    flow_data = body.get("data", {})

    logger.info(f"[WhatsApp Flow] Completed by {phone_number}: {list(flow_data.keys())}")

    if not phone_number:
        return {"status": "no_phone"}

    # Validate required fields from flow
    required = ["hiring_focus", "monthly_volume", "biggest_pain", "lgpd_consent"]
    missing = [f for f in required if f not in flow_data]
    if missing:
        logger.warning(f"[WhatsApp Flow] Missing fields: {missing}")

    # Check LGPD consent — REQUIRED
    if not flow_data.get("lgpd_consent"):
        logger.warning(f"[WhatsApp Flow] LGPD consent NOT given by {phone_number} — blocking")
        # Send message asking for consent
        try:
            orchestrator, wa_client = await _get_orchestrator()
            if wa_client:
                await wa_client.send_message(
                    phone_number,
                    "Para continuar, preciso do seu consentimento de dados (LGPD). "
                    "Por favor, complete o formulario novamente e marque a opcao de consentimento.",
                )
        except Exception:
            pass
        return {"status": "consent_required"}

    session = await _find_session_by_phone(phone_number)
    if not session:
        return {"status": "session_not_found"}

    orchestrator, wa_client = await _get_orchestrator()
    result = await orchestrator.handle_whatsapp_flow_complete(session, flow_data)

    # Send post-flow message + CTA
    if result.get("response_text") and wa_client:
        await wa_client.send_message(phone_number, result["response_text"])
        if result.get("cta_url"):
            await wa_client.send_cta(phone_number, "", result["cta_url"], "Abrir minha plataforma")

    return {"status": "processed"}


@router.post("/status-callback")
async def whatsapp_status_callback(request: Request):
    """Twilio delivery status callback."""
    body = await request.form()
    message_sid = body.get("MessageSid", "")
    status = body.get("MessageStatus", "")

    logger.info(f"[WhatsApp Status] {message_sid}: {status}")

    if status == "failed":
        logger.error(f"[WhatsApp] Message {message_sid} FAILED")

    return Response(status_code=200)
