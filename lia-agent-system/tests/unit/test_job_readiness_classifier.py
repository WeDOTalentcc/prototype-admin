"""Unit tests for the JobReadinessService classifier (Task #429).

Pure-function classification tests over the 7 canonical stages.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.domains.job_management.services.job_readiness_service import (
    AUDIENCE_POLICIES,
    HITL_STAGES,
    NEXT_ACTION_BY_STAGE,
    STAGE_EM_TRIAGEM,
    STAGE_IMPORTADA,
    STAGE_JD_ENRIQUECIDO,
    STAGE_JD_RASCUNHO,
    STAGE_PERGUNTAS_TRIAGEM,
    STAGE_PRONTA_DISPARO,
    STAGE_SEM_JD,
    classify,
    compute_blockers,
    next_action,
    requires_human,
)


def _job(**kwargs):
    """Build a stand-in JobVacancy that the classifier can read.

    Only the attributes touched by the classifier need to be present.
    """
    defaults = dict(
        description=None,
        enriched_jd=None,
        screening_questions=[],
        behavioral_competencies=[],
        screening_config=None,
        source_system=None,
        additional_data={},
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── Stage classification ────────────────────────────────────────────────────

def test_classifies_blank_row_as_importada():
    assert classify(_job()) == STAGE_IMPORTADA


def test_ats_imported_without_jd_is_sem_jd():
    job = _job(source_system="gupy")
    assert classify(job) == STAGE_SEM_JD


def test_legacy_ats_marker_via_additional_data_is_sem_jd():
    job = _job(additional_data={"imported_from_ats": True})
    assert classify(job) == STAGE_SEM_JD


def test_lia_created_blank_stays_importada():
    job = _job(source_system="lia_chat")
    assert classify(job) == STAGE_IMPORTADA


def test_description_only_is_jd_rascunho():
    job = _job(description="Buscamos engenheiro Python sênior...", source_system="gupy")
    assert classify(job) == STAGE_JD_RASCUNHO


def test_enriched_jd_is_jd_enriquecido():
    job = _job(
        description="JD",
        enriched_jd={"description": "x", "responsibilities": ["a"]},
    )
    assert classify(job) == STAGE_JD_ENRIQUECIDO


def test_unapproved_questions_land_in_perguntas_triagem():
    """Freshly generated questions are not auto-promoted to pronta_disparo —
    the recruiter has to sign off via approve_stage()."""
    job = _job(
        description="JD",
        enriched_jd={"x": 1},
        screening_questions=[{"id": "q1", "question": "?"}],
    )
    assert classify(job) == STAGE_PERGUNTAS_TRIAGEM


def test_partial_approval_stays_in_perguntas_triagem():
    """If even one question lacks approved=True, the row stays gated."""
    job = _job(
        description="JD",
        enriched_jd={"x": 1},
        screening_questions=[
            {"id": "q1", "approved": True},
            {"id": "q2"},  # not approved
        ],
    )
    assert classify(job) == STAGE_PERGUNTAS_TRIAGEM


def test_legacy_string_questions_stay_in_perguntas_triagem():
    """Legacy string-shaped questions are treated as unapproved so the
    recruiter has to review them explicitly."""
    job = _job(
        description="JD",
        enriched_jd={"x": 1},
        screening_questions=["Conte sobre você", "Por que essa vaga?"],
    )
    assert classify(job) == STAGE_PERGUNTAS_TRIAGEM


def test_all_approved_questions_promote_to_pronta_disparo():
    job = _job(
        description="JD",
        enriched_jd={"x": 1},
        screening_questions=[
            {"id": "q1", "approved": True},
            {"id": "q2", "approved": True},
        ],
    )
    assert classify(job) == STAGE_PRONTA_DISPARO


def test_screening_active_is_em_triagem():
    job = _job(
        description="JD",
        enriched_jd={"x": 1},
        screening_questions=[{"id": "q1", "approved": True}],
        screening_config={"status": {"screening_status": "active"}},
    )
    assert classify(job) == STAGE_EM_TRIAGEM


def test_empty_enriched_dict_does_not_count():
    job = _job(description="JD", enriched_jd={})
    # empty dict is treated as absent — stays at jd_rascunho.
    assert classify(job) == STAGE_JD_RASCUNHO


# ── Blockers ────────────────────────────────────────────────────────────────

def test_blockers_for_importada_lists_everything():
    blockers = compute_blockers(_job())
    assert "missing_jd" in blockers
    assert "missing_competencies" in blockers
    assert "missing_questions" in blockers


def test_blockers_for_pronta_disparo_is_empty():
    job = _job(
        description="JD",
        enriched_jd={"x": 1},
        behavioral_competencies=[{"competency": "c"}],
        screening_questions=[{"id": "q1", "approved": True}],
    )
    assert compute_blockers(job) == []


# ── Next action / HITL ──────────────────────────────────────────────────────

def test_next_action_for_jd_rascunho_is_enrich_jd():
    job = _job(description="JD")
    assert next_action(job) == "enrich_jd"


def test_jd_enriquecido_requires_human():
    job = _job(description="JD", enriched_jd={"x": 1})
    assert requires_human(job) is True
    assert next_action(job) is None


def test_em_triagem_has_no_next_action():
    job = _job(
        description="JD",
        enriched_jd={"x": 1},
        screening_questions=[{"id": "q1", "approved": True}],
        screening_config={"status": {"screening_status": "active"}},
    )
    assert next_action(job) is None
    assert requires_human(job) is False


# ── Full transition path: jd_enriquecido → perguntas → pronta_disparo ───────

@pytest.mark.asyncio
async def test_full_hitl_transition_from_enriched_to_dispatched():
    """Approval flow:
    1. enriched JD waiting (jd_enriquecido)
    2. recruiter approves → service enqueues question generation
    3. questions arrive (still unapproved) → classifier sees perguntas_triagem
    4. recruiter approves questions → all stamped approved → pronta_disparo
    5. dispatch_screening flips screening status → em_triagem
    """
    from app.domains.job_management.services.job_readiness_service import (
        JobReadinessService,
    )

    enqueued: list[str] = []

    class _StubTaskManager:
        async def submit_task(self, **kwargs):
            enqueued.append(kwargs.get("action_id", ""))
            return "task-1"

    class _StubDB:
        async def flush(self):
            return None

    job = _job(
        id="job-1",
        company_id="co-1",
        description="JD",
        enriched_jd={"description": "x"},
        behavioral_competencies=[{"competency": "c"}],
        readiness_stage=None,
        readiness_blockers=[],
        last_readiness_event_at=None,
    )
    assert classify(job) == STAGE_JD_ENRIQUECIDO

    svc = JobReadinessService(_StubDB(), task_manager=_StubTaskManager())

    # Step 2: recruiter approves enriched JD
    await svc.approve_stage(job, actor="recruiter@x")
    assert "readiness_generate_questions" in enqueued
    assert "approved_by" in (job.enriched_jd or {})

    # Step 3: questions land (worker would do this — simulate)
    job.screening_questions = [
        {"id": "q1", "question": "?"},
        {"id": "q2", "question": "?"},
    ]
    assert classify(job) == STAGE_PERGUNTAS_TRIAGEM
    assert requires_human(job) is True

    # Step 4: recruiter approves questions
    await svc.approve_stage(job, actor="recruiter@x")
    assert classify(job) == STAGE_PRONTA_DISPARO
    assert all(q.get("approved") for q in job.screening_questions)

    # Step 5: dispatch
    await svc.dispatch_screening(
        job, actor="recruiter@x", audience_policy="imported_untriaged"
    )
    assert classify(job) == STAGE_EM_TRIAGEM
    assert job.assigned_audience_policy == "imported_untriaged"


def test_hitl_stages_and_action_map_are_consistent():
    # Every stage in HITL_STAGES must have None as next_action.
    for s in HITL_STAGES:
        assert NEXT_ACTION_BY_STAGE.get(s) is None


def test_audience_policies_are_locked():
    assert AUDIENCE_POLICIES == {"new_only", "imported_untriaged", "manual_selection"}
