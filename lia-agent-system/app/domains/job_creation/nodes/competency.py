"""competency_node canonical — PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B+C.
Mantém comportamento byte-identical via tests de regressão.

F4+F5: Resolve seniority + calculate question distribution.
"""

import logging
import time
from typing import Any, Dict

from app.domains.job_creation.state import (
    JobCreationState,
    calculate_completeness,
)
from app.domains.job_creation.helpers.ws_payload_builder import (
    build_ws_stage_payload,
)

logger = logging.getLogger(__name__)


def competency_node(state: JobCreationState) -> JobCreationState:
    """F4+F5: Resolve seniority + calculate question distribution.

    F4: Deterministic seniority resolution (5 signals)
    F5: Deterministic question distribution table
    Recruiter chooses screening mode (compact 7q / full 12q).
    """
    # Lazy import of helpers defined in graph.py (avoids circular import).
    from app.domains.job_creation.graph import (  # noqa: E402
        _emit_wizard_step_audit,
        _get_question_distribution,
    )

    t0 = time.time()
    logger.info("[JobCreation:competency] Starting F4+F5")

    jd_enriched = state.get("jd_enriched", {})
    skills = [s.get("skill", "") for s in jd_enriched.get("skills_obrigatorias", [])]

    # F4: Resolve seniority using 5 signals
    seniority_result = resolve_seniority(
        explicit_seniority=state.get("parsed_seniority"),
        job_title=jd_enriched.get("titulo_padronizado") or state.get("parsed_title"),
        job_description=jd_enriched.get("about_role", ""),
        skills=skills,
        salary_min=state.get("salary_min"),
    )

    seniority = seniority_result.final_level
    screening_mode = state.get("screening_mode")

    # F5: Question distribution by mode (deterministic)
    distribution = None
    if screening_mode and seniority:
        distribution = _get_question_distribution(screening_mode, seniority)

    # Build competency tree from enriched JD
    competency_tree = []
    for s in jd_enriched.get("skills_obrigatorias", []):
        competency_tree.append({
            "skill": s.get("skill", ""),
            "contexto": s.get("contexto", ""),
            "block": "technical",
        })
    for c in jd_enriched.get("competencias_comportamentais", []):
        competency_tree.append({
            "skill": c.get("competencia", ""),
            "contexto": c.get("contexto", ""),
            "block": "behavioral",
            "trait": c.get("trait_big_five", ""),
        })

    updates: Dict[str, Any] = {
        "current_stage": "competency",
        "seniority_resolved": seniority,
        "seniority_signals": seniority_result.signals_used,
        "question_distribution": distribution,
        "competency_tree": competency_tree,
        "stage_history": (state.get("stage_history") or []) + ["competency"],
        "completeness": calculate_completeness("competency"),
        "requires_approval": False,
        "ws_stage_payload": build_ws_stage_payload(
            stage="competency",
            completeness=calculate_completeness("competency"),
            requires_approval=False,
            data={
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    f"Resolvi a senioridade ({seniority_result.display_name}) "
                    "e a distribuição de perguntas WSI"
                    + (
                        f" (modo {screening_mode})."
                        if screening_mode
                        else " — escolha entre modo compacto (7q) ou completo (12q)."
                    )
                    + " Quer ajustar ou seguir para gerar as perguntas?"
                ),
                "seniority": seniority,
                "seniority_display": seniority_result.display_name,
                "seniority_confidence": seniority_result.confidence,
                "seniority_signals": seniority_result.signals_used,
                "screening_mode": screening_mode,
                "distribution": distribution,
                "competency_tree": competency_tree,
            },
        ),
    }

    # ── Task #1061: wizard_step_completed audit (EU AI Act Art.13) ──
    _emit_wizard_step_audit(
        stage="competency",
        state=state,
        before={
            "seniority_resolved": state.get("seniority_resolved"),
            "competency_tree_count": len(state.get("competency_tree") or []),
        },
        after={
            "seniority": seniority,
            "screening_mode": screening_mode,
            "distribution": distribution,
            "competency_tree_count": len(competency_tree),
        },
        reasoning_extra=[
            f"seniority_confidence={seniority_result.confidence}",
            f"signals_used={seniority_result.signals_used}",
        ],
        criteria_used=["parsed_seniority", "skills_obrigatorias", "salary_min",
                       "screening_mode"],
    )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:competency] seniority=%s mode=%s | %0.fms", seniority, screening_mode, elapsed)
    return {**state, **updates}
