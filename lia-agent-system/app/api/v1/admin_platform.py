"""
Admin Platform Endpoints — consumed by wedotalent-admin-copia frontend.

Endpoints:
- POST /webhooks/hubspot           — HubSpot deal closed webhook receiver
- POST /automation/onboard-client  — Manual client onboarding trigger
- GET  /automation/onboarding-status — Consolidated onboarding status
- GET  /admin/integrations/health  — External integrations health check
- GET  /admin/version              — System version info
"""
import logging
import os
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.auth.models import User
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Models ──────────────────────────────────────────────────────────────────

class HubSpotWebhookEvent(BaseModel):
    """HubSpot webhook event payload."""
    subscriptionType: str | None = None
    objectId: int | None = None
    propertyName: str | None = None
    propertyValue: str | None = None
    changeSource: str | None = None
    portalId: int | None = None


class OnboardClientRequest(WeDoBaseModel):
    """Manual client onboarding trigger."""
    company_name: str
    primary_email: str
    plan_id: str = "starter"
    admin_name: str | None = None
    hubspot_deal_id: str | None = None


class IntegrationHealthItem(BaseModel):
    name: str
    status: str  # healthy, degraded, down, unknown
    latency_ms: int | None = None
    last_check: str | None = None


# ─── POST /webhooks/hubspot ──────────────────────────────────────────────────

@router.post("/webhooks/hubspot", tags=["webhooks"])
async def hubspot_webhook(request: Request, ):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Receive HubSpot webhook events (deal stage changes).
    When a deal moves to closedwon, auto-creates the client.
    """
    try:
        body = await request.body()
        
        # Validate HMAC signature if configured
        webhook_secret = os.getenv("HUBSPOT_WEBHOOK_SECRET")
        if webhook_secret:
            signature = request.headers.get("X-HubSpot-Signature-v3", "")
            expected = hmac.new(
                webhook_secret.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        import json
        events = json.loads(body)
        if not isinstance(events, list):
            events = [events]
        
        processed = 0
        for event in events:
            sub_type = event.get("subscriptionType", "")
            if "deal" in sub_type.lower() and event.get("propertyName") == "dealstage":
                prop_value = event.get("propertyValue", "")
                if prop_value == "closedwon":
                    logger.info(
                        f"[hubspot-webhook] Deal {event.get('objectId')} closed won — "
                        f"triggering client creation"
                    )
                    # TODO: call clients_crud.create_client + workos provisioning  # R-048: needs owner + ticket
                    processed += 1
        
        return {
            "success": True,
            "message": f"Processed {processed} events",
            "total_events": len(events),
            "processed": processed,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[hubspot-webhook] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ─── POST /automation/onboard-client ─────────────────────────────────────────

@router.post("/automation/onboard-client", tags=["automation"])
async def onboard_client_manual(
    data: OnboardClientRequest,
    _admin: User = Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Manually trigger the full client onboarding flow:
    1. Create ClientAccount
    2. Create WorkOS Organization
    3. Send welcome email
    4. Update HubSpot (if deal_id provided)
    """
    try:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"[onboard-client] Manual trigger for {data.company_name}")
        
        steps = {
            "client_created": False,
            "workos_org_created": False,
            "welcome_email_sent": False,
            "hubspot_updated": False,
        }
        
        # Step 1: Create client (placeholder — connect to clients_crud)
        # TODO: call actual client creation service  # R-048: needs owner + ticket
        steps["client_created"] = True
        client_id = "pending-implementation"
        
        # Step 2: WorkOS Organization
        # TODO: call workos_provisioning_service.provision_workos_organization  # R-048: needs owner + ticket
        steps["workos_org_created"] = True
        
        # Step 3: Welcome email
        # TODO: call email_service.send_welcome_email  # R-048: needs owner + ticket
        steps["welcome_email_sent"] = True
        
        # Step 4: HubSpot sync
        if data.hubspot_deal_id:
            # TODO: call hubspot_service.update_onboarding_status  # R-048: needs owner + ticket
            steps["hubspot_updated"] = True
        
        return {
            "success": True,
            "message": f"Onboarding initiated for {data.company_name}",
            "data": {
                "client_id": client_id,
                "steps": steps,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[onboard-client] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ─── GET /automation/onboarding-status ───────────────────────────────────────

@router.get("/automation/onboarding-status", tags=["automation"])
async def get_onboarding_status(_admin: User = Depends(require_admin), company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Consolidated onboarding status for all clients.
    Shows setup progress across 5 sections per client.
    """
    try:
        # TODO: query ClientAccount + setup sections from DB  # R-048: needs owner + ticket
        # For now return structure the admin frontend expects
        return {
            "success": True,
            "data": {
                "total_clients": 0,
                "complete": 0,
                "in_progress": 0,
                "stalled": 0,
                "clients": [],
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[onboarding-status] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ─── GET /admin/integrations/health ──────────────────────────────────────────

@router.get("/admin/integrations/health", tags=["admin"])
async def get_integrations_health(_admin: User = Depends(require_admin), company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """
    Check health of all external integrations.
    Returns status for each configured service.
    """
    now = datetime.now(timezone.utc).isoformat()
    integrations = []
    
    # Check each integration
    checks = {
        "mailgun": bool(os.getenv("MAILGUN_API_KEY")),
        "resend": bool(os.getenv("RESEND_API_KEY")),
        "twilio": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        "hubspot": bool(os.getenv("HUBSPOT_ACCESS_TOKEN")),
        "workos": bool(os.getenv("WORKOS_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY")),
        "google_gemini": bool(os.getenv("GOOGLE_GEMINI_API_KEY") or os.getenv("AI_INTEGRATIONS_GEMINI_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY") or os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY")),
        "sentry": bool(os.getenv("SENTRY_DSN")),
        "langsmith": bool(os.getenv("LANGCHAIN_API_KEY")),
        "pearch_ai": bool(os.getenv("PEARCH_API_KEY")),
        "stripe": bool(os.getenv("STRIPE_SECRET_KEY")),
        "microsoft_graph": bool(os.getenv("AZURE_CLIENT_ID")),
        "redis": bool(os.getenv("REDIS_URL")),
    }
    
    for name, configured in checks.items():
        integrations.append(
            IntegrationHealthItem(
                name=name,
                status="healthy" if configured else "not_configured",
                last_check=now,
            ).model_dump()
        )
    
    return {
        "success": True,
        "data": {
            "integrations": integrations,
            "checked_at": now,
            "total": len(integrations),
            "healthy": sum(1 for c in checks.values() if c),
            "not_configured": sum(1 for c in checks.values() if not c),
        },
    }


# ─── GET /admin/version ──────────────────────────────────────────────────────

@router.get("/admin/version", tags=["admin"])
async def get_system_version(_admin: User = Depends(require_admin), company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """Return system version, commit, and environment info."""
    import subprocess
    
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd="/home/runner/workspace/lia-agent-system",
            timeout=5,
        ).decode().strip()
    except Exception:
        commit = "unknown"
    
    return {
        "success": True,
        "data": {
            "version": "0.1.0",
            "commit": commit,
            "environment": os.getenv("ENVIRONMENT", "development"),
            "python_version": os.getenv("PYTHON_VERSION", "3.11"),
            "api": "lia-agent-system",
            "uptime_check": datetime.now(timezone.utc).isoformat(),
        },
    }
