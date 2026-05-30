"""
LGPD consent and communication preferences endpoints.
"""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ._shared import (
    CandidateRepository,
    ConsentCheckerService,
    User,
    get_candidate_repo,
    get_current_user_or_demo,
    logger,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ConsentCreateRequest(WeDoBaseModel):
    consent_type: str
    consent_given: bool
    consent_source: str = "api"
    consent_text: str | None = None
    ip_address: str | None = None


class CommunicationPreferencesUpdate(WeDoBaseModel):
    preferred_channels: list[str] | None = None  # ["email", "whatsapp", "sms"]
    channel_opt_out: list[str] | None = None      # ["marketing_email", "whatsapp"]


# ---------------------------------------------------------------------------
# LGPD consent endpoints
# ---------------------------------------------------------------------------

@router.get("/{candidate_id}/consents", response_model=None)
async def get_candidate_consents(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    """Lista todos os consentimentos LGPD de um candidato."""
    svc = ConsentCheckerService(candidate_repo.db)
    consents = await svc.get_candidate_consents(str(candidate_id), company_id)
    return {"candidate_id": str(candidate_id), "consents": consents}


@router.post("/{candidate_id}/consents", response_model=None)
async def create_or_update_candidate_consent(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: ConsentCreateRequest,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    """Registra ou atualiza consentimento LGPD de um candidato por finalidade."""
    svc = ConsentCheckerService(candidate_repo.db)
    consent = await svc.register_consent(
        candidate_id=str(candidate_id),
        company_id=company_id,
        consent_type=request.consent_type,
        consent_given=request.consent_given,
        consent_source=request.consent_source,
        consent_text=request.consent_text,
        ip_address=request.ip_address,
    )
    await candidate_repo.db.commit()
    return consent.to_dict()


@router.delete("/{candidate_id}/consents/{consent_type}", status_code=200, response_model=None)
async def revoke_candidate_consent(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    consent_type: str,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
company_id: str = Depends(require_company_id)):
    """Revoga consentimento LGPD de um candidato para uma finalidade específica."""
    svc = ConsentCheckerService(candidate_repo.db)
    consent = await svc.register_consent(
        candidate_id=str(candidate_id),
        company_id=company_id,
        consent_type=consent_type,
        consent_given=False,
        consent_source="candidate_request",
    )
    await candidate_repo.db.commit()
    return {
        "success": True,
        "message": f"Consentimento '{consent_type}' revogado",
        "consent": consent.to_dict(),
    }


# ---------------------------------------------------------------------------
# Communication preferences endpoints
# ---------------------------------------------------------------------------

@router.get("/{candidate_id}/communication-preferences", response_model=None)
async def get_communication_preferences(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Retorna preferências de canal de comunicação do candidato."""
    candidate = await candidate_repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidato não encontrado")
    return {
        "candidate_id": str(candidate_id),
        "preferred_channels": candidate.preferred_channels or ["email"],
        "channel_opt_out": candidate.channel_opt_out or [],
        "preferred_contact_method": candidate.preferred_contact_method,
    }


@router.put("/{candidate_id}/communication-preferences", response_model=None)
async def update_communication_preferences(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    request: CommunicationPreferencesUpdate,
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """Atualiza preferências de canal de comunicação do candidato."""
    candidate = await candidate_repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidato não encontrado")
    if request.preferred_channels is not None:
        candidate.preferred_channels = request.preferred_channels
    if request.channel_opt_out is not None:
        candidate.channel_opt_out = request.channel_opt_out
    candidate.updated_at = datetime.utcnow()
    candidate = await candidate_repo.update(candidate)
    return {
        "success": True,
        "candidate_id": str(candidate_id),
        "preferred_channels": candidate.preferred_channels or ["email"],
        "channel_opt_out": candidate.channel_opt_out or [],
    }
