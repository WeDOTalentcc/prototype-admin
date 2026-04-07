"""
Shared imports, constants, Pydantic models, and helpers for all clients sub-modules.
"""
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.domains.clients.dependencies import get_client_repo
from app.domains.clients.repositories.client_account_repository import ClientAccountRepository
from app.domains.communication.services.email_service import EmailService, get_email_service
from app.domains.job_management.services.template_seeder import clone_templates_for_client
from app.models.client_account import CLIENT_STATUS_OPTIONS, COMPANY_SIZE_OPTIONS, ClientAccount, ClientStatus
from app.services.hubspot_service import hubspot_service, sync_client_to_hubspot
from app.services.workos_provisioning_service import provision_workos_organization

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


class ClientCreate(BaseModel):
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


class ClientUpdate(BaseModel):
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


class StatusUpdate(BaseModel):
    """Request model for updating client status."""
    status: str = Field(..., description="New status")
    reason: str | None = Field(None, description="Reason for status change")


# ---------------------------------------------------------------------------
# Header-based user extractor (used by admin-only endpoints)
# ---------------------------------------------------------------------------

def get_user_from_headers(
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
) -> dict[str, Any]:
    return {
        "company_id": x_company_id,
        "user_id": x_user_id,
        "role": x_user_role,
        "is_admin": x_user_role == "admin",
    }


# ---------------------------------------------------------------------------
# Shared helper: fetch + access-check a client
# ---------------------------------------------------------------------------

async def _get_client_checked(
    client_id: str,
    current_user: dict[str, Any],
    repo: ClientAccountRepository,
) -> ClientAccount:
    """Fetch client by ID and validate admin/owner access. Raises HTTPException on failure."""
    is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)
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
