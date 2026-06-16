"""
Interview Consent — Public endpoint for LGPD consent recording during triagem.

PUBLIC endpoint authenticated via session token (not JWT). Candidate records
their consent before or during the screening process.

Endpoint:
  POST /api/v1/interview/{session_token}/consent

Security model:
  - Token is UUID v4 non-guessable (~10^36 space). Token = auth credential.
  - company_id, candidate_id, vaga_id resolved from session — NEVER from payload.
  - Fail-closed: DB write failure → HTTP 500 (RN-04, no silent swallowing).
  - RN-06: ConsentRecord is immutable (DB trigger prevents UPDATE/DELETE).

Legal basis mapping:
  - "ai_screening"   → "LGPD Art. 7 §I — consentimento"
  - "data_processing"→ "LGPD Art. 7 §II — legítimo interesse"
  - "profiling"      → "LGPD Art. 7 §I — consentimento"
  - default          → "LGPD Art. 7 §I — consentimento"

Multi-tenancy: canonical — company_id resolved from session.company_id (set by
authenticated recruiter at invite time). Never trusted from payload.

Refs: ADR-LGPD-001, LGPD Art. 7/8, Phase 1a LGPD Consent spec (2026-06-11).
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_tenant_db
from app.domains.recruitment.repositories.triagem_session_repository import (
    TriagemSessionRepository,
)
from app.repositories.observability_repository import ObservabilityRepository
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/interview", tags=["interview-consent"])

# ── Legal basis mapping (canonical — single source of truth) ──────────────────
_LEGAL_BASIS_MAP: dict[str, str] = {
    "ai_screening": "LGPD Art. 7 §I — consentimento",
    "data_processing": "LGPD Art. 7 §II — legítimo interesse",
    "profiling": "LGPD Art. 7 §I — consentimento",
    "voice_recording": "LGPD Art. 7 §I — consentimento",
    "data_collection": "LGPD Art. 7 §II — legítimo interesse",
}
_DEFAULT_LEGAL_BASIS = "LGPD Art. 7 §I — consentimento"

# ── Valid canal values (enum-enforced at validation time) ─────────────────────
_VALID_CANAIS = frozenset(
    {"chat_web", "whatsapp", "chamada_online", "chamada_telefonica"}
)


# ── Request / Response schemas (extra='forbid' via WeDoBaseModel) ─────────────


class InterviewConsentRequest(WeDoBaseModel):
    """Body for recording LGPD consent during a triagem session.

    REGRA 2 canonical: NO company_id, candidate_id, or vaga_id here.
    All are resolved from the session token (set by authenticated recruiter).
    """

    consent_type: str
    canal: str
    versao_disclaimer: str
    user_agent: str | None = None
    is_affirmative_data: bool = False  # reserved for future affirmative action consent


class InterviewConsentResponse(WeDoBaseModel):
    ok: bool
    consent_id: str


# ── Dependencies ──────────────────────────────────────────────────────────────


def _get_triagem_repo(db: AsyncSession = Depends(get_tenant_db)) -> TriagemSessionRepository:
    return TriagemSessionRepository(db)


def _get_observability_repo(db: AsyncSession = Depends(get_tenant_db)) -> ObservabilityRepository:
    return ObservabilityRepository(db)


# ── Endpoint ──────────────────────────────────────────────────────────────────


@router.post("/{session_token}/consent", response_model=InterviewConsentResponse)
async def record_interview_consent(
    session_token: str,
    body: InterviewConsentRequest,
    request: Request,
    triagem_repo: TriagemSessionRepository = Depends(_get_triagem_repo),
    obs_repo: ObservabilityRepository = Depends(_get_observability_repo),
) -> InterviewConsentResponse:
    """Record LGPD consent for a triagem session (PUBLIC — no JWT required).

    The session token acts as the authentication credential. All tenant/candidate
    context is resolved from the session, never from the request body.

    Fail-closed (RN-04): any DB write failure propagates as HTTP 500 —
    never swallowed silently.
    """
    # ── 1. Validate session token ─────────────────────────────────────────────
    session = await triagem_repo.get_session_by_token(session_token)

    if session is None:
        raise HTTPException(status_code=404, detail="Token inválido ou sessão não encontrada")

    if session.expires_at and session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Link expirado")

    # ── 2. Validate canal value ───────────────────────────────────────────────
    if body.canal not in _VALID_CANAIS:
        raise HTTPException(
            status_code=422,
            detail=f"Canal inválido: '{body.canal}'. Valores aceitos: {sorted(_VALID_CANAIS)}",
        )

    # ── 3. Resolve tenant context from session (multi-tenancy canonical) ──────
    # company_id, candidate_id, vaga_id come from the session — NEVER from payload.
    try:
        company_uuid = uuid.UUID(str(session.company_id))
        candidate_uuid = uuid.UUID(str(session.candidate_id))
        vaga_uuid = uuid.UUID(str(session.job_id)) if session.job_id else None
        processo_uuid = session.id if isinstance(session.id, uuid.UUID) else uuid.UUID(str(session.id))
    except (ValueError, AttributeError) as exc:
        logger.error(
            "[InterviewConsent] Failed to parse session UUIDs: %s token=%s",
            exc,
            session_token[:8] + "...",
        )
        raise HTTPException(status_code=500, detail="Erro interno ao processar sessão")

    # ── 4. Determine legal basis from consent_type ────────────────────────────
    legal_basis = _LEGAL_BASIS_MAP.get(body.consent_type, _DEFAULT_LEGAL_BASIS)

    # ── 5. Create ConsentRecord — fail-closed (RN-04) ─────────────────────────
    # Any exception propagates as 500. Never silently swallow.
    try:
        consent = await obs_repo.create_consent(
            {
                "company_id": company_uuid,
                "candidate_id": candidate_uuid,
                "consent_type": body.consent_type,
                "version": body.versao_disclaimer,
                "granted_at": datetime.utcnow(),
                "is_active": True,
                "source": "triagem_interview",
                "legal_basis": legal_basis,
                # Phase 1a extended fields:
                "canal": body.canal,
                "user_agent": body.user_agent,
                "processo_id": processo_uuid,
                "vaga_id": vaga_uuid,
                "versao_disclaimer": body.versao_disclaimer,
            }
        )
    except Exception as exc:
        # RN-04: fail-closed — never swallow DB errors
        logger.error(
            "[InterviewConsent] DB write failed: %s | company=%s candidate=%s",
            exc,
            str(company_uuid)[:8],
            str(candidate_uuid)[:8],
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao registrar consentimento. Tente novamente.",
        )

    logger.info(
        "[InterviewConsent] Consent recorded: id=%s type=%s canal=%s company=%s",
        consent.id,
        body.consent_type,
        body.canal,
        str(company_uuid)[:8],
    )

    return InterviewConsentResponse(ok=True, consent_id=str(consent.id))
