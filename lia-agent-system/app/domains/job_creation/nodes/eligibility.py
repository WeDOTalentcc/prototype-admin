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
from app.domains.job_creation.helpers.i18n import msg
from app.domains.job_creation.internal.audit import _emit_wizard_step_audit
from app.domains.job_creation.helpers.async_audit import run_coro_in_threadpool

logger = logging.getLogger(__name__)



def _eligibility_toggle_active(state) -> bool:
    """Respeita o toggle 'eligibility_questions' das Instrucoes LIA (Configuracoes). Fail-open."""
    company_id = str(state.get("workspace_id") or state.get("company_id") or "")
    if not company_id or company_id in ("default", "unknown"):
        return True

    async def _read():
        import uuid as _uuid
        from sqlalchemy import select as _select
        from app.core.database import AsyncSessionLocal
        from app.models.lia_field_toggles import LiaFieldToggle
        try:
            _cid = _uuid.UUID(company_id)
        except ValueError:
            return True
        async with AsyncSessionLocal() as _db:
            val = (
                await _db.execute(
                    _select(LiaFieldToggle.is_active).where(
                        LiaFieldToggle.company_id == _cid,
                        LiaFieldToggle.field_key == "eligibility_questions",
                    )
                )
            ).scalar_one_or_none()
        return val is not False

    _TG_TIMEOUT_S = float(__import__("os").environ.get("LIA_ELIGIBILITY_TOGGLE_TIMEOUT_S", "5"))
    try:
        return run_coro_in_threadpool(_read, timeout=_TG_TIMEOUT_S)
    except Exception:
        return True


def eligibility_node(state: JobCreationState) -> JobCreationState:
    """Pre-screening: yes/no eliminatory questions configured by recruiter."""
    # Lazy import of helpers defined in graph.py (avoids circular import at
    # module load time — graph.py is fully constructed by the time this runs).

    # Toggle gate: eligibility_questions OFF => skip perguntas eliminatorias
    if not _eligibility_toggle_active(state):
        logger.info("[EligibilityNode] toggle 'eligibility_questions' OFF — skip painel")
        return {
            **state,
            "eligibility_questions": [],
        }

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
                    msg("eligibility.questions_configured", count=len(questions))
                    if questions
                    else msg("eligibility.no_questions")
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
