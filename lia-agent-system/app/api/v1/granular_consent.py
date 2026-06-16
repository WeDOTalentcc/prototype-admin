"""
Granular Consent API — D5 (LGPD Art. 7 / EU AI Act Art. 13)

GET  /api/v1/consent/granular/{candidate_id}          — resumo completo
POST /api/v1/consent/granular/{candidate_id}/update   — atualiza múltiplas finalidades

Requer X-Company-ID header para isolamento multi-tenant.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.tenant_guard import get_verified_company_id
from app.shared.services.granular_consent_service import (
    ALL_PURPOSES,
    GranularConsentService,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consent/granular", tags=["granular-consent"])



# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ConsentStatusItem(BaseModel):
    purpose: str
    consent_type: str
    given: bool
    revoked: bool
    consent_date: str | None = None
    revoked_at: str | None = None
    source: str | None = None


class GranularConsentSummaryResponse(BaseModel):
    candidate_id: str
    company_id: str
    all_blocking_given: bool
    consents: list[ConsentStatusItem]


class BulkConsentUpdateRequest(WeDoBaseModel):
    """Mapa de finalidade → consentimento (True=conceder, False=revogar)."""
    updates: dict[str, bool]
    source: str = "api"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/{candidate_id}", response_model=GranularConsentSummaryResponse)
async def get_granular_consents(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)) -> GranularConsentSummaryResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Retorna resumo de todos os consentimentos LGPD granulares do candidato.

    Inclui uma entrada por finalidade suportada, mesmo que o registro não exista
    (nesse caso given=False, revoked=False).

    Finalidades suportadas: ai_screening, ai_scoring, ai_video_analysis,
    ai_comparison, data_retention, marketing, analytics.
    """
    try:
        service = GranularConsentService(db)
        summary = await service.get_summary(candidate_id, company_id)
        return GranularConsentSummaryResponse(
            candidate_id=summary.candidate_id,
            company_id=summary.company_id,
            all_blocking_given=summary.all_blocking_given,
            consents=[
                ConsentStatusItem(
                    purpose=c.purpose,
                    consent_type=c.consent_type,
                    given=c.given,
                    revoked=c.revoked,
                    consent_date=c.consent_date.isoformat() if c.consent_date else None,
                    revoked_at=c.revoked_at.isoformat() if c.revoked_at else None,
                    source=c.source,
                )
                for c in summary.consents
            ],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("granular_consent/%s erro: %s", candidate_id, exc)
        raise HTTPException(status_code=500, detail="Erro ao buscar consentimentos")


@router.post("/{candidate_id}/update", response_model=None)
async def update_granular_consents(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    payload: BulkConsentUpdateRequest,
    request: Request,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)) -> dict:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Atualiza múltiplos consentimentos LGPD em lote.

    Aceita um mapa {finalidade: True/False} onde True=conceder, False=revogar.
    Finalidades inválidas são ignoradas silenciosamente.

    Exemplo:
        {"updates": {"ai_scoring": true, "marketing": false}}
    """
    # Filtra apenas finalidades suportadas
    valid_updates = {k: v for k, v in payload.updates.items() if k in ALL_PURPOSES}
    if not valid_updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Nenhuma finalidade válida encontrada. Suportadas: {ALL_PURPOSES}",
        )

    client_ip = request.client.host if request.client else None

    try:
        service = GranularConsentService(db)
        updated = await service.bulk_update(
            candidate_id=candidate_id,
            company_id=company_id,
            updates=valid_updates,
            source=payload.source,
            ip_address=client_ip,
        )
        return {
            "candidate_id": candidate_id,
            "updated_count": len(updated),
            "consents": [
                {
                    "purpose": c.purpose,
                    "given": c.given,
                    "consent_type": c.consent_type,
                }
                for c in updated
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("granular_consent/%s/update erro: %s", candidate_id, exc)
        raise HTTPException(status_code=500, detail="Erro ao atualizar consentimentos")

reorder_collection_before_item(router)
