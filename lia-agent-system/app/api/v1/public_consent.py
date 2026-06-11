"""
Public Consent Lookup API — Phase 4 LGPD Portal (2026-06-11)

Allows candidates to query their own consent records by CPF or email
without authentication. This is a public endpoint (portal /privacidade)
that returns cross-tenant consent records for the candidate.

LGPD Art. 18 — candidates have the right to access their consent data.
Rate-limiting: handled at infrastructure level (nginx/cloudflare).
"""
import hashlib
import logging
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from lia_models.candidate import Candidate
from lia_models.observability import ConsentRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/consents", tags=["public-consents"])


def _email_hash(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()


def _cpf_hash(cpf: str) -> str:
    digits = "".join(c for c in cpf if c.isdigit())
    return hashlib.sha256(digits.encode()).hexdigest()


@router.get("", summary="List candidate consents by CPF or email (public, no auth)")
async def list_public_consents(
    cpf: str | None = Query(None, description="CPF do candidato (com ou sem formatação)"),
    email: str | None = Query(None, description="E-mail do candidato"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Retorna os registros de consentimento de um candidato identificado por CPF ou e-mail.

    - Endpoint público (sem auth) para o portal de privacidade /privacidade.
    - Busca cross-tenant: retorna consentimentos de TODAS as empresas com que o candidato interagiu.
    - Ao menos um parâmetro (cpf OU email) é obrigatório.
    - LGPD Art. 18: direito do titular de acessar seus dados de consentimento.
    """
    if not cpf and not email:
        raise HTTPException(
            status_code=422,
            detail="Ao menos um parâmetro é obrigatório: 'cpf' ou 'email'.",
        )

    try:
        # Resolve candidate IDs by email_hash and/or cpf_hash (encrypted-at-rest safe lookup)
        candidate_conditions = []
        if email:
            eh = _email_hash(email)
            candidate_conditions.append(
                or_(
                    Candidate.email_hash == eh,
                    sa.func.lower(Candidate._email_raw) == email.strip().lower(),
                )
            )
        if cpf:
            ch = _cpf_hash(cpf)
            candidate_conditions.append(Candidate.cpf_hash == ch)

        # OR across identifier conditions — find any matching candidate
        combined = or_(*candidate_conditions) if len(candidate_conditions) > 1 else candidate_conditions[0]

        candidate_result = await db.execute(
            select(Candidate.id).where(combined).limit(20)
        )
        candidate_ids = [row[0] for row in candidate_result.fetchall()]

        if not candidate_ids:
            return {"consents": [], "total": 0}

        # Fetch consents for all matching candidate IDs (cross-tenant intentional — portal)
        # ADR-001-EXEMPT: cross-tenant read is intentional; candidate is the data owner (LGPD Art. 18)
        consents_result = await db.execute(
            select(ConsentRecord)
            .where(ConsentRecord.candidate_id.in_(candidate_ids))
            .order_by(desc(ConsentRecord.created_at))
            .limit(200)
        )
        consents = list(consents_result.scalars().all())

        return {
            "consents": [c.to_dict() for c in consents],
            "total": len(consents),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("public_consents lookup error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Erro ao consultar consentimentos.")
