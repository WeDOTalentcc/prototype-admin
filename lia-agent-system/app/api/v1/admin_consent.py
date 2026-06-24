"""T-21c admin endpoints — Company-level training data consent (ADR-RLHF-001).

Surface admin-facing canonical para extend ConsentPanel.tsx com tab
"Training Data" — opt-in/out company-level usado pelo training_data_service
(T-21b wired anonymizer) + GranularConsentService training_data purpose
(T-11 B.1.1).

Endpoints:
  GET  /api/v1/admin/consent/company-training-consent
       — Retorna status do consent record (None se nunca opt-in)
  POST /api/v1/admin/consent/company-training-consent/grant
       — Admin opta in para training data export (LGPD Art. 7 §I)
  POST /api/v1/admin/consent/company-training-consent/revoke
       — Admin revoga (LGPD Art. 18 cascade)

Multi-tenancy: fail-closed via require_admin + require_company_id (JWT).
NUNCA aceita company_id no payload (REGRA 6 — anti-pattern x_company_id Header).

Audit trail:
  - audit_service.log_decision para grant/revoke com decision_type=
    "company_settings_change" (retention 7 anos SOX).
  - AUDIT-NO-DEMO: company-level consent admin action — não pode ser silenciado
    em modo demo (compliance-critical).

Refs: T-11 B.1.2 (commit 9d7970c9e), T-21 ADR-LGPD-002, LGPD Art. 7/8/18/33.
"""
from __future__ import annotations

import logging
from app.shared.errors import LIAInternalError
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.auth.models import User
from app.core.database import get_db
from app.domains.lgpd.repositories.company_training_consent_repository import (
    CompanyTrainingConsentRepository,
)
from app.shared.compliance.audit_service import AuditService
from app.shared.security.require_company_id import require_company_id
from app.shared.tenant_guard import get_verified_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin/consent",
    tags=["Admin - Consent"],
)


# ---------------------------------------------------------------------------
# Schemas (Pydantic Conventions canonical — extra='forbid' via WeDoBaseModel)
# ---------------------------------------------------------------------------


class CompanyTrainingConsentStatus(WeDoBaseModel):
    """T-11 B.1.2 read-side DTO. None-equivalent status when record missing."""

    consent_given: bool = False
    is_active: bool = False
    granted_at: Optional[str] = None
    revoked_at: Optional[str] = None
    version: str = "1.0"
    legal_basis: str = "LGPD_ART_7_I"
    consent_text: Optional[str] = None
    consent_source: Optional[str] = None
    user_id_granted: Optional[str] = None
    user_id_revoked: Optional[str] = None
    revoke_reason: Optional[str] = None
    last_updated: Optional[str] = None


class GrantConsentRequest(WeDoBaseModel):
    """T-21c grant request canonical. company_id NUNCA aqui (vem do JWT)."""

    consent_text: str
    version: str = "1.0"
    ip_address: Optional[str] = None


class RevokeConsentRequest(WeDoBaseModel):
    """T-21c revoke request canonical. company_id NUNCA aqui (vem do JWT)."""

    reason: str


class GrantConsentResponse(WeDoBaseModel):
    success: bool
    consent_given: bool
    granted_at: Optional[str] = None


class RevokeConsentResponse(WeDoBaseModel):
    success: bool
    revoked_at: Optional[str] = None
    revoke_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/company-training-consent",
    response_model=CompanyTrainingConsentStatus,
)
async def get_company_training_consent(
    _user: User = Depends(require_admin),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
    _company_gate: str = Depends(require_company_id),
) -> CompanyTrainingConsentStatus:
    """T-21c GET company-level training data consent status.

    Returns default DENY shape when record absent (consent_given=False,
    is_active=False) — fail-CLOSED per ADR-RLHF-001.
    """
    repo = CompanyTrainingConsentRepository(db)
    record = await repo.get_by_company(company_id)
    if record is None:
        return CompanyTrainingConsentStatus()

    return CompanyTrainingConsentStatus(
        consent_given=record.consent_given,
        is_active=record.is_active,
        granted_at=record.granted_at.isoformat() if record.granted_at else None,
        revoked_at=record.revoked_at.isoformat() if record.revoked_at else None,
        version=record.version,
        legal_basis=record.legal_basis,
        consent_text=record.consent_text,
        consent_source=record.consent_source,
        user_id_granted=record.user_id_granted,
        user_id_revoked=record.user_id_revoked,
        revoke_reason=record.revoke_reason,
        last_updated=record.updated_at.isoformat() if record.updated_at else None,
    )


@router.post(
    "/company-training-consent/grant",
    response_model=GrantConsentResponse,
)
async def grant_company_training_consent(
    payload: GrantConsentRequest,
    request: Request,
    user: User = Depends(require_admin),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
    _company_gate: str = Depends(require_company_id),
) -> GrantConsentResponse:
    """T-21c grant company-level training data consent (LGPD Art. 7 §I).

    Admin opt-in para fine-tune Claude via AWS Bedrock (ADR-RLHF-001).
    Idempotent: re-grant após revoke clears revoked_at + sets new granted_at.

    AUDIT-NO-DEMO: company-level consent admin action — não pode ser silenciado
    em modo demo (compliance-critical).
    """
    if not payload.consent_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="consent_text required (LGPD Art. 8 §I inequívoco)",
        )

    client_ip = payload.ip_address or (
        request.client.host if request.client else None
    )

    repo = CompanyTrainingConsentRepository(db)
    try:
        record = await repo.grant_consent(
            company_id,
            user_id=str(user.id),
            consent_text=payload.consent_text,
            consent_source="admin_ui",
            ip_address=client_ip,
            version=payload.version,
        )
        await db.commit()
    except ValueError as exc:
        logger.error("[T-21c] grant_consent failed company=%s err=%s", company_id, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover — defensive
        logger.exception("[T-21c] grant_consent unexpected company=%s", company_id)
        await db.rollback()
        raise LIAInternalError("Erro ao registrar consent training data") from exc

    # AUDIT-NO-DEMO: company-level consent admin action — SOX 7 anos
    try:
        await AuditService().log_decision(
            company_id=str(company_id),
            agent_name="admin_consent_api",
            decision_type="company_settings_change",
            action="grant_training_data_consent",
            decision="approved",
            reasoning=[
                "T-21c admin opted in for training data export",
                f"consent_text_len={len(payload.consent_text)}",
                f"version={payload.version}",
                f"ip={client_ip}",
            ],
            criteria_used=[
                "LGPD_ART_7_I",
                "LGPD_ART_8_I",
                "ADR_RLHF_001",
            ],
            actor_user_id=str(user.id),
        )
    except Exception:  # pragma: no cover — audit best-effort
        logger.exception(
            "[T-21c] AUDIT-NO-DEMO grant audit log failed company=%s", company_id
        )

    return GrantConsentResponse(
        success=True,
        consent_given=record.consent_given,
        granted_at=record.granted_at.isoformat() if record.granted_at else None,
    )


@router.post(
    "/company-training-consent/revoke",
    response_model=RevokeConsentResponse,
)
async def revoke_company_training_consent(
    payload: RevokeConsentRequest,
    user: User = Depends(require_admin),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
    _company_gate: str = Depends(require_company_id),
) -> RevokeConsentResponse:
    """T-21c revoke company-level training data consent (LGPD Art. 18 cascade).

    Sets revoked_at + revoke_reason. existing fine-tuned models are NOT
    rolled back retroactively (vivem em AWS Bedrock conta WeDOTalent);
    novos exports BLOCKED via check_consent_filter_training_data sensor.

    AUDIT-NO-DEMO: company-level consent admin action — não pode ser silenciado
    em modo demo (compliance-critical).
    """
    if not payload.reason.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="reason required (LGPD Art. 18 audit trail)",
        )

    repo = CompanyTrainingConsentRepository(db)
    try:
        record = await repo.revoke_consent(
            company_id,
            user_id=str(user.id),
            reason=payload.reason,
        )
        await db.commit()
    except ValueError as exc:
        logger.error("[T-21c] revoke_consent failed company=%s err=%s", company_id, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover — defensive
        logger.exception("[T-21c] revoke_consent unexpected company=%s", company_id)
        await db.rollback()
        raise LIAInternalError("Erro ao revogar consent training data") from exc

    if record is None:
        # Nada para revogar — never opted in
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum consent ativo para revogar",
        )

    # AUDIT-NO-DEMO: company-level consent admin action — SOX 7 anos
    try:
        await AuditService().log_decision(
            company_id=str(company_id),
            agent_name="admin_consent_api",
            decision_type="company_settings_change",
            action="revoke_training_data_consent",
            decision="approved",
            reasoning=[
                "T-21c admin revoked training data consent",
                f"reason={payload.reason[:200]}",
                "LGPD Art. 18 cascade — novos exports BLOCKED",
            ],
            criteria_used=[
                "LGPD_ART_18",
                "ADR_RLHF_001",
                "consent_filter_training_data",
            ],
            actor_user_id=str(user.id),
        )
    except Exception:  # pragma: no cover — audit best-effort
        logger.exception(
            "[T-21c] AUDIT-NO-DEMO revoke audit log failed company=%s", company_id
        )

    return RevokeConsentResponse(
        success=True,
        revoked_at=record.revoked_at.isoformat() if record.revoked_at else None,
        revoke_reason=record.revoke_reason,
    )
