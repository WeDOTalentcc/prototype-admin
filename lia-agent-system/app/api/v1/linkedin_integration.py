"""
LinkedIn Integration API endpoints.

Provides per-tenant LinkedIn credentials management and job posting.

Multi-tenancy: company_id always from JWT via Depends(require_company_id).
Credentials stored encrypted in IntegrationConnection.credentials_encrypted
using the canonical credentials_crypto helper (Fernet, FIELD_ENCRYPTION_KEY).

Architecture:
  - GET  /status     — check connection status for this company
  - PUT  /connect    — save access_token + org_id (manual token, no OAuth dance)
  - DELETE /disconnect — remove credentials
  - POST /test-post  — post a test social message to verify credentials work
  - POST /publish/{job_id} — publish a specific job to LinkedIn
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.integration_hub import (
    IntegrationConnection,
    IntegrationProvider,
    IntegrationStatus,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.services.credentials_crypto import (
    CredentialsEncryptionError,
    decrypt_credentials,
    encrypt_credentials,
)
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["linkedin-integration"])

_LINKEDIN_PROVIDER_SLUG = "linkedin_jobs"
_LINKEDIN_API_BASE = "https://api.linkedin.com/v2"

# ── Pydantic request schemas ──────────────────────────────────────────────────


class LinkedInConnectRequest(WeDoBaseModel):
    """Request to save LinkedIn credentials (manual token, no OAuth dance)."""

    access_token: str
    org_id: str  # numeric LinkedIn organization ID, e.g. "12345678"
    posting_type: str = "job_posting"  # "job_posting" | "social_only"


class LinkedInTestPostRequest(WeDoBaseModel):
    """Request to post a test social message."""

    message: str | None = None


# ── Provider helpers ──────────────────────────────────────────────────────────


async def _get_or_create_linkedin_provider(db: AsyncSession) -> IntegrationProvider:
    """Return the linkedin_jobs IntegrationProvider row, creating if absent."""
    result = await db.execute(
        select(IntegrationProvider).where(
            IntegrationProvider.slug == _LINKEDIN_PROVIDER_SLUG
        )
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        provider = IntegrationProvider(
            id=uuid.uuid4(),
            name="LinkedIn Jobs",
            category="job_board",
            slug=_LINKEDIN_PROVIDER_SLUG,
            description="Publicação de vagas no LinkedIn Jobs e feed da empresa",
            logo_url="/integrations/linkedin.svg",
            supports_oauth=False,
            supports_api_key=True,
            supports_webhook=False,
            features=["job_posting", "social_feed", "candidate_redirect"],
            is_active=True,
            is_premium=False,
        )
        db.add(provider)
        await db.flush()
    return provider


async def _get_connection(
    company_id: str, db: AsyncSession
) -> IntegrationConnection | None:
    """Return the IntegrationConnection row for this company, or None."""
    provider = await _get_or_create_linkedin_provider(db)
    result = await db.execute(
        select(IntegrationConnection).where(
            IntegrationConnection.company_id == company_id,
            IntegrationConnection.provider_id == provider.id,
        )
    )
    return result.scalar_one_or_none()


async def _get_decrypted_credentials(
    company_id: str, db: AsyncSession
) -> dict[str, Any] | None:
    """Return decrypted credentials dict, or None if not connected."""
    conn = await _get_connection(company_id, db)
    if conn is None or conn.status != IntegrationStatus.CONNECTED:
        return None
    try:
        return decrypt_credentials(conn.credentials_encrypted)
    except CredentialsEncryptionError as exc:
        logger.error(
            "[linkedin] credentials decryption failed for company %s: %s",
            company_id,
            exc,
        )
        return None


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/status", response_model=None)
async def get_linkedin_status(
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Return LinkedIn integration connection status for this company.

    Returns:
        connected: bool — whether valid credentials are stored
        org_id: str | None — the LinkedIn org ID (for display)
        posting_type: str | None — "job_posting" or "social_only"
        status: "connected" | "not_configured"
    """
    conn = await _get_connection(company_id, db)
    if conn is None or conn.status != IntegrationStatus.CONNECTED:
        return {
            "connected": False,
            "status": "not_configured",
            "org_id": None,
            "posting_type": None,
        }
    try:
        creds = decrypt_credentials(conn.credentials_encrypted)
        return {
            "connected": True,
            "status": "connected",
            "org_id": creds.get("org_id"),
            "posting_type": creds.get("posting_type", "job_posting"),
            # access_token deliberately NOT returned — LGPD
        }
    except CredentialsEncryptionError:
        return {
            "connected": False,
            "status": "not_configured",
            "org_id": None,
            "posting_type": None,
        }


@router.put("/connect", response_model=None)
async def connect_linkedin(
    request: LinkedInConnectRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Save LinkedIn access_token + org_id for this company (encrypted at rest).

    The caller pastes their LinkedIn access_token and org ID from their
    LinkedIn Developer App — no OAuth dance required for manual token entry.

    Credentials stored:
        access_token, org_id, org_urn, posting_type
    """
    if not request.access_token.strip():
        raise HTTPException(status_code=422, detail="access_token não pode ser vazio")
    if not request.org_id.strip().isdigit():
        raise HTTPException(
            status_code=422,
            detail="org_id deve ser numérico (ex: 12345678)",
        )
    if request.posting_type not in ("job_posting", "social_only"):
        raise HTTPException(
            status_code=422,
            detail="posting_type deve ser 'job_posting' ou 'social_only'",
        )

    credentials = {
        "access_token": request.access_token.strip(),
        "org_id": request.org_id.strip(),
        "org_urn": f"urn:li:organization:{request.org_id.strip()}",
        "posting_type": request.posting_type,
    }

    try:
        encrypted = encrypt_credentials(credentials)
    except CredentialsEncryptionError as exc:
        logger.error(
            "[linkedin] credentials encryption failed for company %s: %s",
            company_id,
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao criptografar credenciais",
        ) from exc

    try:
        provider = await _get_or_create_linkedin_provider(db)
        result = await db.execute(
            select(IntegrationConnection).where(
                IntegrationConnection.company_id == company_id,
                IntegrationConnection.provider_id == provider.id,
            )
        )
        conn = result.scalar_one_or_none()
        if conn is None:
            conn = IntegrationConnection(
                id=uuid.uuid4(),
                company_id=company_id,
                provider_id=provider.id,
                status=IntegrationStatus.CONNECTED,
                auth_type="api_token",
                credentials_encrypted=encrypted,
            )
            db.add(conn)
        else:
            conn.credentials_encrypted = encrypted
            conn.status = IntegrationStatus.CONNECTED
            conn.auth_type = "api_token"
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error(
            "[linkedin] save credentials failed for company %s: %s", company_id, exc
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao salvar credenciais",
        ) from exc

    logger.info(
        "[linkedin] credentials saved for company %s, org_id=%s, posting_type=%s",
        company_id,
        request.org_id,
        request.posting_type,
    )
    return {
        "success": True,
        "connected": True,
        "status": "connected",
        "org_id": request.org_id.strip(),
        "posting_type": request.posting_type,
    }


@router.delete("/disconnect", response_model=None)
async def disconnect_linkedin(
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Remove LinkedIn credentials for this company."""
    conn = await _get_connection(company_id, db)
    if conn is None:
        return {"success": True, "connected": False, "message": "Não estava conectado"}

    try:
        conn.status = IntegrationStatus.DISCONNECTED
        conn.credentials_encrypted = None
        await db.commit()
    except Exception as exc:
        await db.rollback()
        logger.error(
            "[linkedin] disconnect failed for company %s: %s", company_id, exc
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao desconectar",
        ) from exc

    logger.info("[linkedin] disconnected for company %s", company_id)
    return {"success": True, "connected": False, "status": "not_configured"}


@router.post("/test-post", response_model=None)
async def test_linkedin_post(
    request: LinkedInTestPostRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Post a test social message to the LinkedIn organization feed.

    Fail-loud: if the API call fails, returns success=False with error details.
    NEVER marks anything as published on API failure.
    """
    creds = await _get_decrypted_credentials(company_id, db)
    if not creds:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn não está configurado. Conecte primeiro em Configurações > Integrações.",
        )

    access_token = creds["access_token"]
    org_urn = creds["org_urn"]
    message = request.message or (
        "✅ Conexão com LinkedIn verificada pela plataforma WeDOTalent. "
        "Esta é uma mensagem de teste — pode ser removida."
    )

    ugc_payload = {
        "author": org_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": message},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{_LINKEDIN_API_BASE}/ugcPosts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
                json=ugc_payload,
            )
    except httpx.TimeoutException as exc:
        logger.error("[linkedin] test-post timeout for company %s: %s", company_id, exc)
        return {
            "success": False,
            "error": "timeout",
            "message": "LinkedIn API não respondeu a tempo. Verifique sua conexão.",
        }
    except httpx.RequestError as exc:
        logger.error(
            "[linkedin] test-post request error for company %s: %s", company_id, exc
        )
        return {
            "success": False,
            "error": "request_error",
            "message": f"Erro de conexão: {exc}",
        }

    if resp.status_code in (200, 201):
        post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-Restli-Id")
        logger.info(
            "[linkedin] test-post success for company %s, post_id=%s",
            company_id,
            post_id,
        )
        return {
            "success": True,
            "post_id": post_id,
            "message": "Post de teste enviado com sucesso ao LinkedIn.",
        }
    else:
        error_body: dict[str, Any] = {}
        try:
            error_body = resp.json()
        except Exception:
            error_body = {"raw": resp.text[:500]}
        logger.error(
            "[linkedin] test-post failed for company %s: status=%s body=%s",
            company_id,
            resp.status_code,
            error_body,
        )
        return {
            "success": False,
            "error": f"linkedin_api_error_{resp.status_code}",
            "linkedin_error": error_body,
            "message": (
                f"LinkedIn retornou erro {resp.status_code}. "
                "Verifique se o access_token tem permissão 'w_organization_social'."
            ),
        }


@router.post("/publish/{job_id}", response_model=None)
async def publish_job_to_linkedin(
    job_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
    company_id: str = Depends(require_company_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Publish a job vacancy to LinkedIn Jobs and/or org social feed.

    Fail-loud: never marks job as published if the API call fails.
    Delegates to JobBoardService.publish_to_linkedin() with credentials
    resolved from the per-tenant IntegrationConnection.
    """
    import uuid as _uuid

    from sqlalchemy import select as _select

    from app.domains.job_management.repositories.job_vacancy_crud_repository import (
        JobVacancyCRUDRepository,
    )
    from app.domains.job_management.services.job_board_service import JobBoardService

    # Resolve job — multi-tenancy enforced by company_id filter
    repo = JobVacancyCRUDRepository(db)
    try:
        job_uuid = _uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="job_id deve ser um UUID válido")

    from lia_models.job_vacancy import JobVacancy

    result = await db.execute(
        _select(JobVacancy).where(
            JobVacancy.id == job_uuid,
            JobVacancy.company_id == company_id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")

    creds = await _get_decrypted_credentials(company_id, db)
    if not creds:
        raise HTTPException(
            status_code=400,
            detail="LinkedIn não está configurado. Conecte primeiro em Configurações > Integrações.",
        )

    service = JobBoardService()
    result = await service.publish_to_linkedin(
        job=job,
        db=db,
        company_id=company_id,
        credentials=creds,
    )
    return result
