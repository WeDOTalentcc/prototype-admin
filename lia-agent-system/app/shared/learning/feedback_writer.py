"""T-10 Fase 2 canonical helper: wire_feedback_outcome() (ADR-032).

Helper canonical reusável para WIRE incremental de feedback signals em agentic
domains. Aplica taxonomia ADR-032 + fail-open + lazy import.

Uso canonical em agentic services:
    from app.shared.learning.feedback_writer import wire_feedback_outcome

    # Em transition handler (vacancy hired)
    await wire_feedback_outcome(
        db=db,
        domain="pipeline",
        outcome_type="HIRED",
        company_id=company_id,
        job_id=job_id,
        context={"vacancy_candidate_id": vc_id},
    )

    # Em ATS webhook (hired externo)
    await wire_feedback_outcome(
        db=db,
        domain="ats_integration",
        outcome_type="HIRED_EXTERNAL",
        company_id=company_id,
        job_id=job_id,
        context={"source": "gupy_webhook"},
    )

Refs:
- ADR-032 feedback wire canonical
- T-10 Fase 1 mirror writer (alimenta InteractionFeedback → training data)
- feedback_learning_service.record_outcome canonical
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


# Taxonomia ADR-032 — outcome types mapeáveis a JobOutcomeType
OUTCOME_TYPES = {
    "HIRED",           # Candidate contratado (internal pipeline)
    "HIRED_EXTERNAL",  # Hired via ATS sync (Gupy, Lever, etc)
    "REJECTED",        # Candidato rejeitado final
    "CANCELED",        # Vaga cancelada
    "FILLED",          # Vaga preenchida
    "WITHDRAWN",       # Candidato desistiu
}


async def wire_feedback_outcome(
    *,
    db,
    domain: str,
    outcome_type: str,
    company_id: str | UUID,
    job_id: str | UUID,
    context: dict[str, Any] | None = None,
    time_to_fill_days: int | None = None,
    role: str | None = None,
    seniority: str | None = None,
    department: str | None = None,
) -> bool:
    """Wire canonical para feedback_learning_service.record_outcome.

    Fail-open: nunca raises. Falhas viram logger.warning.

    Returns:
        True se outcome persistido com sucesso, False senão.

    LGPD: passa por mirror writer T-10 Fase 1 → also persiste em
    InteractionFeedback (training data pipeline).
    """
    if outcome_type not in OUTCOME_TYPES:
        logger.warning(
            "[wire_feedback_outcome] outcome_type '%s' não canonical "
            "(esperado %s) — skip",
            outcome_type, OUTCOME_TYPES,
        )
        return False

    try:
        from app.domains.analytics.services.feedback_learning_service import (
            FeedbackLearningService,
        )
        from lia_models.feedback_learning import JobOutcomeType
    except ImportError as e:
        logger.warning(
            "[wire_feedback_outcome] FeedbackLearningService unavailable: %s",
            e,
        )
        return False

    # Map outcome string → enum
    try:
        outcome_enum = JobOutcomeType[outcome_type] if hasattr(JobOutcomeType, outcome_type) else None
        if outcome_enum is None:
            # Fallback string match
            for member in JobOutcomeType:
                if member.value.upper() == outcome_type.upper():
                    outcome_enum = member
                    break
        if outcome_enum is None:
            logger.warning(
                "[wire_feedback_outcome][%s] outcome_type %s não em JobOutcomeType — skip",
                domain, outcome_type,
            )
            return False
    except Exception as e:
        logger.warning("[wire_feedback_outcome][%s] enum lookup fail: %s", domain, e)
        return False

    try:
        # Convert IDs to UUID se string
        job_uuid = UUID(str(job_id)) if not isinstance(job_id, UUID) else job_id

        service = FeedbackLearningService()
        await service.record_outcome(
            db=db,
            company_id=str(company_id),
            job_id=job_uuid,
            outcome=outcome_enum,
            time_to_fill_days=time_to_fill_days,
            role=role,
            seniority=seniority,
            department=department,
            notes=f"wired_via=wire_feedback_outcome domain={domain}",
            created_by=f"system:{domain}",
        )
        logger.info(
            "[wire_feedback_outcome][%s] persisted outcome=%s job_id=%s",
            domain, outcome_type, job_uuid,
        )
        return True
    except Exception as e:
        # Fail-open: feedback nunca derruba caminho crítico (ADR-032 invariant)
        logger.warning(
            "[wire_feedback_outcome][%s] persist failed (non-blocking): %s",
            domain, str(e)[:200],
            exc_info=True,
        )
        return False
