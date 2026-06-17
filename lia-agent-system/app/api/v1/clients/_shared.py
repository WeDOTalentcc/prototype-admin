"""
Clients shared helpers — multi-tenant safe.

Onda 4.2f-P0.2 (2026-05-23): substituido X-User-Role/X-User-ID headers
em get_user_from_headers que eram FORJAVEIS = backdoor catastrofico
(privilege escalation cross-tenant em ClientAccount). Pattern canonical
do fix policies.py commit 1b487565: JWT-only via current_user.
"""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_active_user
from app.auth.models import User, UserRole
from app.repositories.dependencies import get_client_repo
from app.repositories.client_account_repository import ClientAccountRepository
from app.domains.communication.services.email_service import EmailService, get_email_service
from app.domains.job_management.services.template_seeder import clone_templates_for_client
from app.models.client_account import CLIENT_STATUS_OPTIONS, COMPANY_SIZE_OPTIONS, ClientAccount, ClientStatus
from app.shared.services.hubspot_service import hubspot_service, sync_client_to_hubspot
from app.shared.services.workos_provisioning_service import provision_workos_organization
from app.shared.tenant_guard import get_verified_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic request models (shared across sub-modules)
# ---------------------------------------------------------------------------

class AddressSchema(BaseModel):
    """Address schema."""
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = "Brasil"


class ClientCreate(WeDoBaseModel):
    """Request model for creating a client."""
    name: str = Field(..., min_length=1, max_length=255)
    trade_name: str | None = Field(None, max_length=255)
    cnpj: str | None = Field(None, max_length=20)
    primary_email: str | None = Field(None, max_length=255)
    primary_phone: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=500)
    address: AddressSchema | None = None
    status: str = Field(default="pending_setup")
    plan_id: str | None = Field(None, max_length=100)
    contract_start_date: datetime | None = None
    contract_end_date: datetime | None = None
    user_limit: int = Field(default=10, ge=1)
    job_limit: int = Field(default=50, ge=1)
    ai_credits_monthly: int = Field(default=1000, ge=0)
    settings: dict[str, Any] | None = None
    features_enabled: list[str] | None = None
    account_manager_id: str | None = None
    implementation_manager_id: str | None = None
    logo_url: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=100)
    company_size: str | None = Field(None, max_length=50)


class ClientUpdate(WeDoBaseModel):
    """Request model for updating a client."""
    name: str | None = Field(None, min_length=1, max_length=255)
    trade_name: str | None = Field(None, max_length=255)
    cnpj: str | None = Field(None, max_length=20)
    primary_email: str | None = Field(None, max_length=255)
    primary_phone: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=500)
    address: AddressSchema | None = None
    plan_id: str | None = Field(None, max_length=100)
    contract_start_date: datetime | None = None
    contract_end_date: datetime | None = None
    user_limit: int | None = Field(None, ge=1)
    job_limit: int | None = Field(None, ge=1)
    ai_credits_monthly: int | None = Field(None, ge=0)
    settings: dict[str, Any] | None = None
    features_enabled: list[str] | None = None
    account_manager_id: str | None = None
    implementation_manager_id: str | None = None
    logo_url: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=100)
    company_size: str | None = Field(None, max_length=50)
    onboarding_completed_at: datetime | None = None


class StatusUpdate(WeDoBaseModel):
    """Request model for updating client status."""
    status: str = Field(..., description="New status")
    reason: str | None = Field(None, description="Reason for status change")


# ---------------------------------------------------------------------------
# Header-based user extractor (used by admin-only endpoints)
# ---------------------------------------------------------------------------

def get_user_from_headers(
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(get_verified_company_id),
) -> dict[str, Any]:
    """Get user context from JWT (NO headers).

    Onda 4.2f-P0.2 (2026-05-23): substituido X-User-Role/X-User-ID headers
    FORJAVEIS que eram backdoor catastrofico. Pattern canonical do fix
    policies.py commit 1b487565: JWT-only via current_user.role.

    Platform admin = role wedotalent_admin APENAS (staff WeDOTalent).
    Tenant admin (UserRole.admin) administra apenas a propria company.
    Nome mantido pra zero impacto callers.
    """
    return {
        "company_id": company_id,
        "user_id": str(current_user.id),
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        # Onda 4.2f-P0.2: is_admin = wedotalent_admin APENAS (era backdoor).
        "is_admin": current_user.role == UserRole.wedotalent_admin,
    }


# ---------------------------------------------------------------------------
# Shared helper: fetch + access-check a client
# ---------------------------------------------------------------------------

async def _get_client_checked(
    client_id: str,
    current_user: dict[str, Any],
    repo: ClientAccountRepository,
) -> ClientAccount:
    """Fetch client by ID and validate admin/owner access.

    Onda 4.2f-P0.2 (2026-05-23): is_admin agora vem do JWT-validated role
    via get_user_from_headers (que retorna wedotalent_admin only).
    """
    # Onda 4.2f-P0.2: get_user_from_headers ja garante is_admin=wedotalent_admin.
    # Removido fallback `role == "admin"` que era espelho do header backdoor.
    is_admin = current_user.get("is_admin", False)
    user_company_id = current_user.get("company_id")
    try:
        client_uuid = UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client ID format")
    client = await repo.get_by_id(client_uuid)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client not found: {client_id}")
    if not is_admin and str(client.id) != user_company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this client")
    return client
