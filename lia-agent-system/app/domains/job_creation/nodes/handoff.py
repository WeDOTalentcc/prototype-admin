"""handoff_node canonical — PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B+C.
Mantém comportamento byte-identical via tests de regressão.

Final node do wizard: navega recrutador para a página da vaga e informa
share link. Após este node, o chat se torna o "job assistant".
"""

import logging
import time
from typing import Any, Dict

from app.domains.job_creation.state import JobCreationState
from app.domains.job_creation.helpers.ws_payload_builder import (
    build_ws_stage_payload,
)
from app.domains.job_creation.helpers.i18n import msg
from app.domains.job_creation.helpers.i18n import msg

logger = logging.getLogger(__name__)


def handoff_node(state: JobCreationState) -> JobCreationState:
    """Navigate recruiter to job page. Inform share link. Chat becomes job assistant."""
    t0 = time.time()
    logger.info("[JobCreation:handoff] Starting handoff")

    job_id = state.get("job_id")
    share_link = state.get("share_link")

    # ── Phase 4G / A2: route whitelist enforcement (Bug P2 fix) ──
    # Use safe_navigate_route to enforce VALID_ROUTES; falls back to None on error.
    handoff_url = None
    if job_id:
        try:
            from app.domains.job_creation.safe_navigation import safe_navigate_route
            handoff_url = safe_navigate_route("/jobs/{job_id}", job_id=job_id)
        except Exception as _nav_exc:
            logger.warning(
                "[JobCreation:handoff] safe_navigate_route failed (fallback): %s", _nav_exc,
            )
            handoff_url = f"/jobs/{job_id}"  # fail-open fallback

    updates: Dict[str, Any] = {
        "current_stage": "handoff",
        "handoff_url": handoff_url,
        "stage_history": (state.get("stage_history") or []) + ["handoff"],
        "completeness": 1.0,
        "requires_approval": False,
        "ws_stage_payload": build_ws_stage_payload(
            stage="handoff",
            completeness=1.0,
            requires_approval=False,
            data={
                # Task #1099 — invariant: data.message obrigatório.
                "message": (
                    (msg("handoff.job_ready_with_url", handoff_url=handoff_url) if handoff_url else msg("handoff.job_ready") + ".")
                    + (msg("handoff.share_link_suffix", share_link=share_link) if share_link else "")
                ),
                "job_id": job_id,
                "handoff_url": handoff_url,
                "share_link": share_link,
            },
        ),
    }

    # NOTE on LL-2 manager preferences learning loop:
    # ManagerPreferencesService.record_job_completion() is invoked by
    # WizardSessionService.process_message() AFTER graph completes
    # (when current_stage == "handoff"). G8 idempotency_key (MD5) is
    # generated there. See wizard_session_service.py:253+.

    # ── Audit EU AI Act Art.13 — single job_creation audit row ──
    # Emitted exactly once per successful wizard run at handoff.
    try:
        from app.domains.job_creation.compliance import emit_job_creation_audit
        emit_job_creation_audit({**state, **updates})
    except Exception as _handoff_audit_exc:
        logger.warning(
            "[JobCreation:handoff] audit emission failed (fail-open): %s", _handoff_audit_exc,
        )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:handoff] url=%s | %0.fms", handoff_url, elapsed)
    return {**state, **updates}
