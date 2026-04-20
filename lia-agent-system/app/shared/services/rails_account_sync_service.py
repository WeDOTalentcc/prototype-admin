"""
Rails Account Sync Service — propagates admin-created clients to Rails for multi-tenancy.

Problem: AdminPlatform creates clients in FastAPI/WorkOS/HubSpot but NOT in Rails.
Rails uses Apartment gem (schema-per-tenant). Without a ClientAccount row in Rails,
the client's users cannot log in — the Apartment tenant switch fails.

Solution: after FastAPI creates the client, call this service to mirror the record
in Rails via POST /v1/users/client_accounts (requires RAILS_API_TOKEN service token).

Failure mode: non-blocking — if Rails is unreachable, log warning and allow the
admin flow to succeed. The mismatch can be repaired via the reconcile endpoint.
"""
import logging
import os
from typing import Any

from app.domains.ats_integration.services.ats_clients.wedotalent_rails import WeDOTalentATSClient

logger = logging.getLogger(__name__)

async def sync_client_to_rails(client: Any, db: Any = None) -> dict[str, Any]:
    """Mirror a newly created FastAPI ClientAccount into Rails.

    Args:
        client: ClientAccount ORM instance (FastAPI side) — must expose:
                id, name, trade_name, cnpj, industry, company_size, website,
                primary_email, primary_phone, plan_id, status, user_limit,
                job_limit, ai_credits_monthly
        db:     AsyncSession — unused here, kept for signature parity with
                sync_client_to_hubspot.

    Returns:
        {"success": True, "rails_id": <int>}  on success
        {"success": False, "error": <str>}     on failure (non-blocking)
    """
    token = os.environ.get("RAILS_ADMIN_TOKEN") or os.environ.get("RAILS_API_TOKEN", "")
    if not token:
        logger.warning(
            "[RailsSync] RAILS_ADMIN_TOKEN / RAILS_API_TOKEN not set — "
            "skipping Rails account sync for client %s. "
            "Set the env var to enable multi-tenancy sync.",
            getattr(client, "id", "unknown"),
        )
        return {"success": False, "error": "RAILS_ADMIN_TOKEN not configured"}

    payload = _build_rails_payload(client)

    rails = WeDOTalentATSClient(token=token)
    try:
        result = await rails.create_client_account(payload)
        if result:
            rails_id = result.get("id")
            logger.info(
                "[RailsSync] Created Rails ClientAccount %s for FastAPI client %s",
                rails_id,
                getattr(client, "id", "unknown"),
            )
            return {"success": True, "rails_id": rails_id}

        logger.warning(
            "[RailsSync] Rails create_client_account returned None for client %s",
            getattr(client, "id", "unknown"),
        )
        return {"success": False, "error": "Rails returned empty response"}
    except Exception as exc:
        logger.warning(
            "[RailsSync] Rails sync failed for client %s: %s",
            getattr(client, "id", "unknown"),
            exc,
        )
        return {"success": False, "error": str(exc)}
    finally:
        await rails.close()


def _build_rails_payload(client: Any) -> dict[str, Any]:
    """Map FastAPI ClientAccount fields to Rails permitted params."""
    # company_size → Rails uses :size field
    size = getattr(client, "company_size", None)

    payload: dict[str, Any] = {
        "name": getattr(client, "name", "") or "",
        "trade_name": getattr(client, "trade_name", None),
        "cnpj": getattr(client, "cnpj", None),
        "industry": getattr(client, "industry", None),
        "size": size,
        "website": getattr(client, "website", None),
        "email": getattr(client, "primary_email", None),
        "phone": getattr(client, "primary_phone", None),
        "plan_id": getattr(client, "plan_id", None),
        "status": getattr(client, "status", "active"),
        "user_limit": getattr(client, "user_limit", None),
        "job_limit": getattr(client, "job_limit", None),
        "ai_credits_monthly": getattr(client, "ai_credits_monthly", None),
    }
    # Strip None values to avoid sending null for unset fields
    return {k: v for k, v in payload.items() if v is not None}
