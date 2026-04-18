"""
Task #412 — Regression test that proves biased WSI screening questions
get filtered out by FairnessGuard before being returned to the recruiter.

Task #247 restored the FairnessGuard L1 check + AuditService.log_decision
call on ``POST /api/v1/wsi/generate-questions``. Without a regression
test, the protection silently disappeared once before (when the legacy
``wsi_questions.py`` was deleted). This test pins the contract:

* When ``WSIService.generate_from_simple_inputs`` returns a mix of clean
  and explicitly biased question texts, the biased ones are removed from
  the response ``questions`` list.
* ``fairness_blocked_count`` reflects the number of dropped questions.
* ``fairness_warnings`` includes the human-readable summary mentioning
  how many questions FairnessGuard removed.
* ``AuditService.log_decision`` is invoked exactly once per request.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.v1.wsi._shared import GenerateQuestionsRequest
from app.api.v1.wsi.questions import generate_questions
from app.domains.cv_screening.services.wsi_service.models import (
    WSIQuestion as ServiceWSIQuestion,
)


CLEAN_QUESTION_TEXT = (
    "Descreva um projeto recente em que você utilizou Python para "
    "resolver um problema técnico complexo."
)
BIASED_APPEARANCE_TEXT = (
    "Procuramos candidato com excelente aparência física para a vaga."
)
BIASED_AGE_TEXT = "Buscamos apenas jovens para essa vaga."


def _make_service_question(qid: str, text: str) -> ServiceWSIQuestion:
    return ServiceWSIQuestion(
        id=qid,
        competency="Python",
        framework="CBI",
        question_type="contextual",
        question_text=text,
        weight=0.25,
        expected_signals=["uses python", "owns problem"],
        scoring_criteria={"5": "exemplar", "1": "missing"},
    )


@pytest.fixture
def mixed_wsi_questions() -> list[ServiceWSIQuestion]:
    """Mix of two clean questions and two explicitly biased ones."""
    return [
        _make_service_question("q1", CLEAN_QUESTION_TEXT),
        _make_service_question("q2", BIASED_APPEARANCE_TEXT),
        _make_service_question(
            "q3",
            "Conte sobre uma situação em que você precisou liderar um time "
            "remoto distribuído em diferentes fusos horários.",
        ),
        _make_service_question("q4", BIASED_AGE_TEXT),
    ]


@pytest.mark.asyncio
async def test_generate_questions_drops_biased_items_and_audits_once(
    mixed_wsi_questions,
):
    request = GenerateQuestionsRequest(
        job_vacancy_id="job-412",
        company_id="company-412",
        job_title="Engenheiro Backend Sênior",
        skills=["Python", "FastAPI"],
        behavioral_competencies=["Liderança"],
        seniority_level="senior",
        num_questions=5,
        max_questions=8,
    )

    db = AsyncMock()
    sqs_svc = MagicMock()
    sqs_svc.get_active_version = AsyncMock(return_value=None)

    wsi_svc = MagicMock()
    wsi_svc.generate_from_simple_inputs = AsyncMock(
        return_value=mixed_wsi_questions
    )

    audit_svc = MagicMock()
    audit_svc.log_decision = AsyncMock()

    # Bypass the in-route DB persistence — its internals (WsiRepository)
    # would explode against an AsyncMock session, but the route already
    # wraps that block in try/except. Patching keeps the test focused on
    # the FairnessGuard contract instead of repository plumbing.
    with patch("app.api.v1.wsi.questions.WsiRepository") as repo_cls:
        repo_instance = MagicMock()
        repo_instance.upsert_session = AsyncMock()
        repo_instance.upsert_question = AsyncMock()
        repo_cls.return_value = repo_instance

        response = await generate_questions(
            request=request,
            db=db,
            sqs_svc=sqs_svc,
            wsi_svc=wsi_svc,
            audit_svc=audit_svc,
        )

    # WSIService was actually invoked with the recruiter's inputs.
    wsi_svc.generate_from_simple_inputs.assert_awaited_once()

    # Both biased questions must have been filtered out.
    returned_texts = [q.text for q in response.questions]
    assert BIASED_APPEARANCE_TEXT not in returned_texts
    assert BIASED_AGE_TEXT not in returned_texts

    # Both clean questions survive.
    assert CLEAN_QUESTION_TEXT in returned_texts
    assert len(response.questions) == 2

    # fairness_blocked_count reflects the drop.
    assert response.fairness_blocked_count == 2

    # The summary warning is surfaced so the UI can show it.
    assert response.fairness_warnings, "expected at least one fairness warning"
    assert any(
        "FairnessGuard" in w and "2" in w for w in response.fairness_warnings
    ), f"expected summary warning mentioning 2 blocks, got {response.fairness_warnings!r}"

    # AuditService.log_decision called exactly once for the whole request.
    assert audit_svc.log_decision.await_count == 1
    call_kwargs = audit_svc.log_decision.await_args.kwargs
    assert call_kwargs["company_id"] == "company-412"
    assert call_kwargs["agent_name"] == "wsi_question_generator"
    assert call_kwargs["decision_type"] == "generate_wsi_questions"
    assert call_kwargs["job_vacancy_id"] == "job-412"
    # Reasoning trail records how many were kept vs blocked so auditors
    # can reconstruct the decision.
    reasoning_blob = " ".join(call_kwargs["reasoning"])
    assert "questions_kept=2" in reasoning_blob
    assert "blocked=2" in reasoning_blob


@pytest.mark.asyncio
async def test_generate_questions_clean_input_does_not_block_or_warn():
    """Sanity check: a fully clean WSIService payload is passed through
    untouched, fairness_blocked_count is zero, and the audit row is still
    written exactly once."""
    clean_questions = [
        _make_service_question("q1", CLEAN_QUESTION_TEXT),
        _make_service_question(
            "q2",
            "Como você organiza branches e commits em projetos colaborativos?",
        ),
    ]

    request = GenerateQuestionsRequest(
        job_vacancy_id="job-412-clean",
        company_id="company-412",
        job_title="Engenheiro Backend",
        skills=["Python"],
        num_questions=3,
    )

    db = AsyncMock()
    sqs_svc = MagicMock()
    sqs_svc.get_active_version = AsyncMock(return_value=None)

    wsi_svc = MagicMock()
    wsi_svc.generate_from_simple_inputs = AsyncMock(return_value=clean_questions)

    audit_svc = MagicMock()
    audit_svc.log_decision = AsyncMock()

    with patch("app.api.v1.wsi.questions.WsiRepository") as repo_cls:
        repo_instance = MagicMock()
        repo_instance.upsert_session = AsyncMock()
        repo_instance.upsert_question = AsyncMock()
        repo_cls.return_value = repo_instance

        response = await generate_questions(
            request=request,
            db=db,
            sqs_svc=sqs_svc,
            wsi_svc=wsi_svc,
            audit_svc=audit_svc,
        )

    assert len(response.questions) == 2
    assert response.fairness_blocked_count == 0
    # No "FairnessGuard removeu N pergunta(s)" summary should appear when
    # nothing was blocked.
    assert not any(
        "FairnessGuard removeu" in w for w in response.fairness_warnings
    ), f"unexpected block-summary warning: {response.fairness_warnings!r}"
    assert audit_svc.log_decision.await_count == 1
