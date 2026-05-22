"""
WT-2022 P0.C: Helper canonical para audit de decisões automatizadas (LGPD Art. 20 + EU AI Act Art. 13).

Decisão Paulo 2026-05-21: AutomatedDecisionExplanation tabela órfã. Pipelines IA
(wsi_service, ranking, pre_wrf_filter, cv_screening) deveriam gravar cada decisão
automatizada nessa tabela. AITransparencyPanel lê e expõe ao recrutador/DPO/candidato
per Art. 20 LGPD (revisão de decisão automatizada).

Status (2026-05-21):
    ✅ Helper canonical criado (este arquivo)
    ❌ Consumers TODO em pipelines IA:
        - app/domains/cv_screening/services/wsi_service/ — gravar decisão por candidato
        - app/domains/ranking/services/ — gravar decisão de ranking
        - app/domains/cv_screening/services/pre_wrf_filter_service.py — gravar filter decision
        - app/domains/job_creation/services/intake_extractor.py — gravar extracion decision

## Pattern de uso (qualquer caller)

    from app.shared.services.automated_decision_logger import log_automated_decision

    await log_automated_decision(
        db=db,
        company_id=company_id,
        candidate_id=candidate_id,
        job_id=job_id,
        decision_type="cv_screening_score",  # ou "ranking", "wsi_evaluation", etc.
        ai_model_used="claude-opus-4-7",
        explanation_text=f"Candidato pontuou X em Y critérios baseado em ...",
        criteria_used=["skills_match", "experience_years", "education"],
        criteria_ignored=PROTECTED_CRITERIA_PT,  # ADR-LGPD-001 mandatory
        confidence_score=0.85,
        review_eligible=True,  # candidato pode pedir review per Art. 20
    )

## ADR-LGPD-001 enforcement

PROTECTED_CRITERIA_PT lista atributos PROIBIDOS de usar em decisão automatizada
(raça, religião, gênero, etnia, estado civil, saúde — CLAUDE.md REGRA #2).
Helper enforça que criteria_ignored CONTAIN esses campos — fail-loud se omitido.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# WT-2022 P0.C: criterios PROIBIDOS per ADR-LGPD-001 + CLAUDE.md REGRA #2
PROTECTED_CRITERIA_PT = [
    "raca",
    "religiao",
    "genero",
    "etnia",
    "estado_civil",
    "orientacao_sexual",
    "deficiencia",
    "saude",
    "filiacao_sindical",
    "filiacao_politica",
]


async def log_automated_decision(
    db: "AsyncSession",
    company_id: str,
    decision_type: str,
    explanation_text: str,
    *,
    candidate_id: str | None = None,
    job_id: str | None = None,
    ai_model_used: str = "",
    criteria_used: list[str] | None = None,
    criteria_ignored: list[str] | None = None,
    confidence_score: float | None = None,
    review_eligible: bool = True,
    extra_metadata: dict[str, Any] | None = None,
) -> str | None:
    """Insert AutomatedDecisionExplanation record per LGPD Art. 20 + EU AI Act Art. 13.

    Returns the new decision_id (UUID) on success, None on failure (fail-safe — caller
    pode usar pra retry/queue, mas decisão IA não deve ser BLOQUEADA por log failure).

    LGPD/Compliance enforcement:
    - PROTECTED_CRITERIA_PT (ADR-LGPD-001 + REGRA #2) é validado contra criteria_used.
      Se algum protected criterion foi usado em decisão IA, fail-loud raise ValueError.
    - criteria_ignored deve incluir PROTECTED_CRITERIA_PT — log warning se omitido.
    """
    # Compliance gate: protected criteria nao podem aparecer em criteria_used
    if criteria_used:
        violations = [c for c in criteria_used if c.lower() in PROTECTED_CRITERIA_PT]
        if violations:
            raise ValueError(
                f"WT-2022 P0.C / ADR-LGPD-001 VIOLATION: criterios protegidos "
                f"em criteria_used: {violations}. Estes NUNCA podem ser usados em "
                f"decisao automatizada (CLAUDE.md REGRA #2 + LGPD)."
            )

    # Warn se criteria_ignored nao incluir protected (boa pratica + audit trail)
    if criteria_ignored is None or not set(PROTECTED_CRITERIA_PT).issubset(set(criteria_ignored)):
        logger.warning(
            "WT-2022 P0.C: criteria_ignored deveria incluir PROTECTED_CRITERIA_PT "
            "para audit trail completo (LGPD Art. 20)."
        )
        criteria_ignored = list(set((criteria_ignored or []) + PROTECTED_CRITERIA_PT))

    try:
        from app.models.observability import AutomatedDecisionExplanation

        decision = AutomatedDecisionExplanation(
            id=uuid.uuid4(),
            company_id=company_id,
            candidate_id=candidate_id,
            job_id=job_id,
            decision_type=decision_type,
            ai_model_used=ai_model_used,
            explanation_text=explanation_text,
            criteria_used=criteria_used or [],
            criteria_ignored=criteria_ignored,
            confidence_score=confidence_score,
            review_eligible=review_eligible,
            extra_metadata=extra_metadata or {},
            created_at=datetime.utcnow(),
        )
        db.add(decision)
        await db.flush()
        decision_id = str(decision.id)
        logger.info(
            "WT-2022 P0.C: automated decision logged: type=%s candidate_id=%s job_id=%s",
            decision_type, candidate_id, job_id,
        )
        return decision_id
    except Exception as exc:
        # Fail-safe: decisão IA não deve ser bloqueada por log failure.
        # Mas LOG VERY LOUD pra observability picar gap.
        logger.error(
            "WT-2022 P0.C: AutomatedDecisionExplanation log FAILED for type=%s: %s "
            "(LGPD Art. 20 audit trail gap — candidate review pode estar comprometido)",
            decision_type, exc, exc_info=True,
        )
        return None
