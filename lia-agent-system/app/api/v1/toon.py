"""
TOON API — Talent Object Of Note (Sprint G7).

GET /api/v1/candidates/{candidate_id}/toon

Returns a structured summary card (TOONCard) for a candidate,
optionally in the context of a job opening.

Multi-tenant: company_id required (query param or X-Company-ID header).
LGPD: anonymize=true masks all PII fields.
Cache: served from Redis (TTL=1h) when available.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, status

from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.toon_service import TOONCard, toon_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["toon"])


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class TOONCardResponse(BaseModel):
    candidate_id: str
    job_id: str | None
    generated_at: str
    headline: str
    highlights: list[str]
    match_score: int | None
    skills_match: list[str]
    name_display: str
    location: str
    experience_years: int
    anonymized: bool
    fairness_reviewed: bool

    class Config:
        from_attributes = True

    @classmethod
    def from_card(cls, card: TOONCard) -> "TOONCardResponse":
        return cls(
            candidate_id=card.candidate_id,
            job_id=card.job_id,
            generated_at=card.generated_at,
            headline=card.headline,
            highlights=card.highlights,
            match_score=card.match_score,
            skills_match=card.skills_match,
            name_display=card.name_display,
            location=card.location,
            experience_years=card.experience_years,
            anonymized=card.anonymized,
            fairness_reviewed=card.fairness_reviewed,
        )


# ---------------------------------------------------------------------------
# Dependency — resolve company_id from header or query param
# ---------------------------------------------------------------------------

def _get_company_id(
    company_id_query: str | None = Query(None, alias="company_id"),
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
) -> str:
    """
    Resolve company_id from either query param or X-Company-ID header.
    Validates it is a well-formed UUID.
    """
    company_id = company_id_query or x_company_id
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="company_id is required (query param or X-Company-ID header)",
        )
    try:
        UUID(company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="company_id must be a valid UUID",
        )
    return company_id


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/candidates/{candidate_id}/toon",
    response_model=TOONCardResponse,
    summary="Get TOON card for a candidate",
    description=(
        "Returns a structured Talent Object Of Note (TOON) card for the given candidate. "
        "Optionally scoped to a job opening (job_id) to compute match_score and skills_match. "
        "LGPD: pass anonymize=true to mask all PII. "
        "Results are cached in Redis for 1 hour per candidate+job+company combination."
    ),
)
async def get_toon_card(
    candidate_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    job_id: str | None = Query(None, description="Job opening UUID for match scoring"),
    anonymize: bool = Query(False, description="When true, masks all PII (LGPD-safe)"),
    company_id: str = Depends(_get_company_id),
    db: AsyncSession = Depends(get_db),
) -> TOONCardResponse:
    """
    Retrieve (or generate) a TOONCard for the given candidate.

    - 200: TOONCard returned successfully (may be served from Redis cache).
    - 404: Candidate not found or does not belong to the company.
    - 422: Invalid candidate_id, job_id, or missing company_id.
    """
    # Validate UUIDs early
    try:
        UUID(candidate_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="candidate_id must be a valid UUID",
        )
    if job_id:
        try:
            UUID(job_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="job_id must be a valid UUID",
            )

    try:
        card = await toon_service.get_or_generate(
            candidate_id=candidate_id,
            job_id=job_id,
            db=db,
            company_id=company_id,
            anonymize=anonymize,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("[TOON] Unexpected error generating card: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar TOON card",
        )

    return TOONCardResponse.from_card(card)
