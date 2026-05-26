"""calibration_node canonical — PR-10 split (2026-05-26).

Movido de graph.py durante refactor estrutural ONDA 3 sub-sprint B+C.
Mantém comportamento byte-identical via tests de regressão.

Present 3+ candidates for calibration (approve/reject).
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


def calibration_node(state: JobCreationState) -> JobCreationState:
    """Present 3+ candidates for calibration (approve/reject).

    Fetches calibration candidates from Rails API if not already loaded.
    """
    # Lazy import of helpers defined in graph.py (avoids circular import).
    from app.domains.job_creation.graph import (  # noqa: E402
        _get_api_client,
    )

    t0 = time.time()
    logger.info("[JobCreation:calibration] Starting calibration")

    candidates = list(state.get("calibration_candidates", []))
    job_id = state.get("job_id")

    # Fetch candidates from API if we have a job_id but no candidates yet
    if job_id and not candidates:
        try:
            api = _get_api_client(state)
            resp = api.get_calibration_candidates(job_id, limit=5)
            if resp.success and resp.data:
                raw = resp.data.get("candidates", resp.data.get("data", []))
                for c in raw:
                    attrs = c.get("attributes", c)
                    candidates.append({
                        "id": str(attrs.get("id", "")),
                        "name": attrs.get("name", ""),
                        "current_title": attrs.get("current_title", ""),
                        "current_company": attrs.get("current_company", ""),
                        "match_score": float(attrs.get("match_score", 0)),
                        "match_criteria": attrs.get("match_criteria", []),
                    })
                logger.info("[JobCreation:calibration] Fetched %d candidates from API", len(candidates))
        except Exception as e:
            logger.warning("[JobCreation:calibration] Failed to fetch candidates: %s", e)

    threshold = state.get("calibration_threshold", 3)
    approved_count = sum(1 for c in candidates if c.get("decision") == "approved")
    complete = approved_count >= threshold

    # Sprint O.3 — detect fresh-publish boundary: publish_node ran in this same
    # graph invocation (stage_history tail) and vacancy was just created with
    # zero candidates loaded. Without this branch, the calibration message
    # ("Carreguei 0 candidato(s)...") overwrites publish's success message
    # since LangGraph auto-transitions publish->calibration in the same turn
    # (route_after_publish line ~4515). Tracked: Sprint N commit 98082cef8
    # only handled review_gate->publish boundary; this is the publish->calibration
    # sibling fix. Sensor: tests/wizard/test_publish_calibration_message.py.
    _stage_history = state.get("stage_history") or []
    _just_published = (
        "publish" in _stage_history[-3:]
        and bool(job_id)
        and not state.get("error")
    )
    _fresh_publish_zero_cands = (
        _just_published and len(candidates) == 0 and not complete
    )

    if _fresh_publish_zero_cands:
        _share_link = state.get("share_link") or ""
        _wsi_n = len(state.get("wsi_questions") or [])
        _calib_message = (
            "🎉 Vaga publicada com sucesso! "
            + (f"Link de divulgação: {_share_link}. " if _share_link else "")
            + (
                f"Já está visível para captação. Quando os primeiros candidatos "
                f"se inscreverem, vou usar suas {_wsi_n} perguntas WSI para "
                "calibrar a triagem inicial — é só voltar para revisar."
                if _wsi_n
                else "Já está visível para captação. Quando candidatos se "
                "inscreverem, vou ajudar você a calibrar a triagem por aqui."
            )
        )
    elif complete:
        _calib_message = (
            f"Calibração concluída — {approved_count}/{threshold} "
            "candidatos aprovados. Posso encerrar a configuração da vaga?"
        )
    else:
        _calib_message = (
            f"Carreguei {len(candidates)} candidato(s) para "
            f"calibração ({approved_count}/{threshold} aprovados). "
            "Continue avaliando para liberar a publicação completa."
        )

    updates: Dict[str, Any] = {
        "current_stage": "calibration",
        "calibration_complete": complete,
        "stage_history": _stage_history + ["calibration"],
        "completeness": calculate_completeness("calibration"),
        "requires_approval": False,
        "ws_stage_payload": build_ws_stage_payload(
            stage="calibration",
            completeness=calculate_completeness("calibration"),
            requires_approval=False,
            data={
                # Task #1099 — invariant: data.message obrigatório.
                # Sprint O.3 — fresh-publish branch above for UX celebratory.
                "message": _calib_message,
                # Sprint O.1: propagate job_id so the orchestrator can link
                # the response to the created vacancy after calibration
                # overwrites ws_stage_payload.
                "job_id": str(job_id) if job_id else None,
                "candidates": candidates,
                "threshold": threshold,
                "approved_count": approved_count,
                "complete": complete,
                "fresh_publish": _fresh_publish_zero_cands,
            },
        ),
    }

    # ── LL-1 — Calibration delta loop (canonical wiring) ──
    # For each candidate with a recruiter decision, record feedback.
    # Service maintains a running score_delta per job_id used in future evaluations.
    try:
        from app.domains.cv_screening.services.rubric_evaluation_service import calibration_feedback as _cal_fb
        _job_id = str(state.get("job_id") or "")
        _recorded = 0
        if _job_id:
            for _cand in candidates:
                if not isinstance(_cand, dict):
                    continue
                _decision = _cand.get("recruiter_decision")
                if not _decision:
                    continue
                _original = _cand.get("original_score")
                _adjusted = _cand.get("recruiter_adjusted_score")
                _eval_id = str(_cand.get("evaluation_id") or _cand.get("id") or "")
                _cand_id = str(_cand.get("id") or _cand.get("candidate_id") or "")
                if _eval_id and _cand_id and _original is not None:
                    _cal_fb.record_feedback(
                        evaluation_id=_eval_id,
                        candidate_id=_cand_id,
                        job_id=_job_id,
                        original_score=float(_original),
                        recruiter_adjusted_score=(
                            float(_adjusted) if _adjusted is not None else None
                        ),
                        recruiter_decision=str(_decision),
                        feedback_notes=_cand.get("feedback_notes"),
                    )
                    _recorded += 1
            if _recorded > 0:
                logger.info(
                    "[JobCreation:calibration] LL-1 recorded %d feedback entries for job_id=%s",
                    _recorded, _job_id,
                )
    except Exception as _cal_exc:
        logger.warning(
            "[JobCreation:calibration] LL-1 calibration feedback failed (fail-open): %s",
            _cal_exc,
        )

    elapsed = (time.time() - t0) * 1000
    logger.info("[JobCreation:calibration] %d/%d approved | %0.fms", approved_count, threshold, elapsed)
    return {**state, **updates}

