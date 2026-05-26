"""eligibility_node canonical — PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B+C.
Mantém comportamento byte-identical via tests de regressão.

Pre-screening: yes/no eliminatory questions configured by recruiter.
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


def eligibility_node(state: JobCreationState) -> JobCreationState:
    """Pre-screening: yes/no eliminatory questions configured by recruiter."""
    # Lazy import of helpers defined in graph.py (avoids circular import at
    # module load time — graph.py is fully constructed by the time this runs).
    from app.domains.job_creation.graph import _emit_wizard_step_audit

    t0 = time.time()
    logger.info("[JobCreation:eligibility] Starting eligibility questions")

    questions = state.get("eligibility_questions", [])

    updates: Dict[str, Any] = {
        "current_stage": "eligibility",
        "stage_history": (state.get("stage_history") or []) + ["eligibility"],
        "completeness": calculate_completeness("eligibility"),
        "requires_approval": False,
        "ws_stage_payload": build_ws_stage_payload(
            stage="eligibility",
            completeness=calculate_completeness("eligibility"),
            requires_approval=False,
            data={
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    f"Configurei {len(questions)} pergunta(s) eliminatória(s) "
                    "para a triagem inicial."
                    if questions
                    else "Nenhuma pergunta eliminatória configurada — quer "
                    "adicionar alguma ou seguir direto para a revisão final?"
                ),
                "questions": questions,
            },
        ),
    }

    # ── Task #1061: wizard_step_completed audit (EU AI Act Art.13) ──
    _emit_wizard_step_audit(
        stage="eligibility",
        state=state,
        before={"questions_count": len(state.get("eligibility_questions") or [])},
        after={"questions_count": len(questions)},
        reasoning_extra=[f"questions={[q.get('text') if isinstance(q, dict) else str(q) for q in questions[:5]]}"],
        criteria_used=["recruiter_configured_questions"],
    )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:eligibility] %d questions | %0.fms", len(questions), elapsed)
    return {**state, **updates}
