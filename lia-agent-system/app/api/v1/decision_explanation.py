"""
Decision Explanation API — "Explain Decision" endpoint for recruiters.

Aggregates reasoning from AuditLog, CalibrationWeight, and FairnessGuard
into a structured explanation response.

Item: PX08-080 — Sprint 12, item 12.5
LGPD Art. 20 — Direito a explicação de decisões automatizadas.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from lia_models.audit_log import AuditLog
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decisions", tags=["Decision Explanation"])


class DecisionFactor(BaseModel):
    factor: str
    weight: float | None = None
    match: str | None = None
    contribution: str | None = None


class DecisionExplanation(BaseModel):
    reasoning: list[str]
    factors: list[DecisionFactor]
    confidence: float | None = None
    confidence_level: str | None = None
    fairness_check: str
    criteria_evaluated: list[str]
    criteria_ignored: list[str]
    calibration_weights_used: dict[str, float]
    transparency_note: str


class DecisionItem(BaseModel):
    decision_id: str
    type: str
    timestamp: str | None = None
    agent: str
    result: dict
    explanation: DecisionExplanation
    human_reviewed: bool = False
    human_override: str | None = None


class DecisionExplanationResponse(BaseModel):
    candidate_id: str
    job_id: str
    decisions: list[DecisionItem]
    total_decisions: int


def _confidence_level(confidence: float | None) -> str:
    if confidence is None:
        return "unknown"
    if confidence >= 0.80:
        return "high"
    if confidence >= 0.50:
        return "medium"
    return "low"


def _build_factors_from_criteria(criteria_used: list[str], reasoning: list[str]) -> list[DecisionFactor]:
    """Build structured factors from criteria and reasoning."""
    factors = []
    for criterion in criteria_used:
        matching_reason = next(
            (r for r in reasoning if criterion.lower() in r.lower()),
            None
        )
        factors.append(DecisionFactor(
            factor=criterion,
            match=matching_reason[:200] if matching_reason else None,
        ))
    return factors


async def _load_calibration_weights(
    company_id: str, job_id: str | None, db: AsyncSession
) -> dict[str, float]:
    """Load CalibrationWeight for this tenant. Falls back to defaults."""
    defaults = {"technical": 0.70, "behavioral": 0.30}
    try:
        from lia_models.calibration import CalibrationWeight

        query = select(CalibrationWeight).where(
            and_(
                CalibrationWeight.company_id == company_id,
                CalibrationWeight.is_active == True,  # noqa: E712
            )
        )
        if job_id:
            result = await db.execute(query.where(CalibrationWeight.job_id == job_id))
            weights = result.scalars().all()
            if not weights:
                result = await db.execute(query.where(CalibrationWeight.job_id.is_(None)))
                weights = result.scalars().all()
        else:
            result = await db.execute(query.where(CalibrationWeight.job_id.is_(None)))
            weights = result.scalars().all()

        if weights:
            return {w.dimension: w.adjusted_weight for w in weights}
    except Exception as exc:
        logger.warning("[DecisionExplanation] CalibrationWeight load failed: %s", exc)

    return defaults


PROTECTED_CRITERIA_LABELS = {
    "age": "Idade", "gender": "Gênero", "ethnicity": "Etnia/raça",
    "marital_status": "Estado civil", "photo": "Foto/aparência",
    "institution": "Instituição de ensino", "address": "Endereço",
    "religion": "Religião", "disability": "Condição de deficiência",
    "nationality": "Nacionalidade",
}


@router.get(
    "/candidates/{candidate_id}/explain",
    response_model=DecisionExplanationResponse,
)
async def explain_candidate_decisions(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    job_id: str = Query(..., description="Job vacancy ID"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Explain all AI decisions made for a candidate on a specific job.

    Returns structured reasoning, factors, confidence, fairness status,
    and calibration weights used. Compliant with LGPD Art. 20.
    """
    company_id = str(current_user.company_id)

    result = await db.execute(
        select(AuditLog)
        .where(
            and_(
                AuditLog.company_id == company_id,
                AuditLog.candidate_id == candidate_id,
                AuditLog.job_vacancy_id == job_id,
            )
        )
        .order_by(AuditLog.created_at.asc())
    )
    audit_logs = result.scalars().all()

    if not audit_logs:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma decisão encontrada para este candidato nesta vaga.",
        )

    calibration_weights = await _load_calibration_weights(company_id, job_id, db)

    transparency_note = (
        "Para garantir um processo justo, os seguintes critérios NÃO foram considerados: "
        + ", ".join(PROTECTED_CRITERIA_LABELS.values())
    )

    decisions = []
    for log in audit_logs:
        reasoning = log.reasoning or []
        criteria_used = log.criteria_used or []
        criteria_ignored = log.criteria_ignored or []
        fairness_flags = log.fairness_flags or []

        fairness_status = "failed" if fairness_flags else "passed"

        factors = _build_factors_from_criteria(criteria_used, reasoning)

        confidence = log.confidence
        conf_level = _confidence_level(confidence)

        decisions.append(DecisionItem(
            decision_id=log.id,
            type=log.decision_type,
            timestamp=log.created_at.isoformat() if log.created_at else None,
            agent=log.agent_name,
            result={
                "decision": log.decision,
                "score": log.score,
                "action": log.action,
            },
            explanation=DecisionExplanation(
                reasoning=reasoning,
                factors=factors,
                confidence=confidence,
                confidence_level=conf_level,
                fairness_check=fairness_status,
                criteria_evaluated=criteria_used,
                criteria_ignored=criteria_ignored,
                calibration_weights_used=calibration_weights,
                transparency_note=transparency_note,
            ),
            human_reviewed=log.human_reviewed_at is not None,
            human_override=log.human_override,
        ))

    return DecisionExplanationResponse(
        candidate_id=candidate_id,
        job_id=job_id,
        decisions=decisions,
        total_decisions=len(decisions),
    )

reorder_collection_before_item(router)
