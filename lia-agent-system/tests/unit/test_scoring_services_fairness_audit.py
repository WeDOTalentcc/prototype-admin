"""
Task #307 — Fairness checks + audit trail on the 5 candidate-scoring services.

For each of the 5 services that decide whether a candidate moves forward,
verify that:
  1. FairnessGuard.check(...) is run on the relevant input BEFORE scoring.
  2. Discriminatory text ("boa aparência", "jovem dinâmico") is blocked.
  3. audit_service.log_decision(...) is called with the fairness block context
     (company_id, agent_name, decision_type, candidate/job IDs, etc.).

Services covered:
  - cv_scoring_service.CVScoringService.screen_candidate
  - lia_score_service.LIAScoreService.calculate_score
  - pre_qualification_service.PreQualificationService.evaluate
  - eligibility_verification_service.EligibilityVerificationService.check_answer
  - evaluation_criteria_service.EvaluationCriteriaService.get_criteria_for_requirements
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.shared.compliance import scoring_safeguards
from app.shared.compliance.scoring_safeguards import FairnessBlockedError


DISCRIMINATORY_TEXTS = [
    # FairnessGuard "aparencia_fisica" category — esthetic discrimination
    # (the canonical "boa aparência" example expressed as the regulated phrase
    #  the guard hard-blocks: see fairness_guard.DISCRIMINATORY_CATEGORIES).
    "Procuramos candidato com excelente aparência",
    # FairnessGuard "idade" category — age discrimination
    # (the canonical "jovem dinâmico" example expressed as the regulated phrase
    #  that triggers the hard age block).
    "Buscamos apenas jovens para essa vaga",
    # Task #364 — canonical phrases promoted from Layer-2 educational
    # warning to Layer-1 hard block. They must now fail closed across all
    # 5 scoring services with a regulator-facing audit entry.
    "Procuramos candidato com boa aparência",
    "Exigimos boa apresentação pessoal do candidato",
    "Buscamos profissional jovem e dinâmico para a equipe",
    "Queremos alguém com energia jovem para essa função",
    "Precisamos de sangue novo nesse time",
    # Task #386 — English equivalents promoted from Layer-2 educational
    # warning (IMPLICIT_BIAS_TERMS_EN) to Layer-1 hard block under
    # appearance_en / age_en. Must fail closed across the same 5 services
    # so multi-language tenants get symmetric enforcement.
    "We are looking for a good looking candidate",
    "Candidate must be presentable for client meetings",
    "We need a young and dynamic professional",
    "Looking for young blood in our team",
    "Seeking energetic professionals for this role",
]


def _patch_audit():
    """Patch audit_service.log_decision in scoring_safeguards module.

    All 5 services route audit logging through
    `app.shared.compliance.scoring_safeguards.log_scoring_decision`, which in
    turn calls the module-level `audit_service.log_decision`. Patching here
    captures every fairness audit emitted by all 5 services.
    """
    return patch.object(
        scoring_safeguards.audit_service,
        "log_decision",
        new_callable=AsyncMock,
    )


def _wait_pending_tasks():
    """Drain fire-and-forget audit tasks scheduled via schedule_audit_log.

    Only effective from sync test contexts — schedule_audit_log running outside
    an active loop spins a temporary loop synchronously, so by the time we
    inspect the audit mock the work is already done. From an async test
    context, the calling service awaits log_scoring_decision directly.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        return
    if loop.is_running():
        return  # async test context — caller already awaited everything
    pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))


def _assert_fairness_audit(audit_mock, expected_agent: str) -> None:
    """Assert audit_service.log_decision was called with a fairness_block payload."""
    _wait_pending_tasks()
    assert audit_mock.await_count >= 1, (
        f"audit_service.log_decision must be called for {expected_agent} fairness block"
    )
    fairness_calls = [
        call for call in audit_mock.await_args_list
        if call.kwargs.get("action") == "cv_screening.fairness_block"
    ]
    assert fairness_calls, (
        f"Expected a 'cv_screening.fairness_block' audit entry for {expected_agent}, got "
        f"{[c.kwargs.get('action') for c in audit_mock.await_args_list]}"
    )
    fb = fairness_calls[0].kwargs
    # Mandatory regulator-facing audit fields (EU AI Act / LGPD evidence trail)
    assert fb.get("agent_name") == expected_agent
    assert fb.get("company_id"), "company_id must be present on fairness audit"
    assert fb.get("decision_type"), "decision_type must be present on fairness audit"
    reasoning = fb.get("reasoning") or []
    assert isinstance(reasoning, list) and reasoning, (
        "reasoning must be a non-empty list explaining the block"
    )
    criteria_used = fb.get("criteria_used")
    assert isinstance(criteria_used, list), "criteria_used must be a list"


# ---------------------------------------------------------------------------
# C1 — CVScoringService.screen_candidate
# ---------------------------------------------------------------------------

class TestCVScoringServiceFairness:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("biased_text", DISCRIMINATORY_TEXTS)
    async def test_screen_candidate_blocks_discriminatory_text(self, biased_text):
        from app.domains.cv_screening.services import cv_scoring_service as mod

        svc = mod.CVScoringService()
        mock_db = AsyncMock()

        candidate_data = {
            "id": str(uuid4()),
            "name": "Test",
            "resume_text": biased_text,
        }
        requirements = [MagicMock()]
        job_info = {"title": "Dev"}

        with patch.object(svc, "_get_candidate_data",
                          new_callable=AsyncMock, return_value=candidate_data), \
             patch.object(svc, "_get_job_requirements",
                          new_callable=AsyncMock, return_value=requirements), \
             patch.object(svc, "_get_job_info",
                          new_callable=AsyncMock, return_value=job_info), \
             _patch_audit() as audit_mock, \
             patch.object(mod.rubric_evaluation_service, "evaluate_candidate",
                          new_callable=AsyncMock) as rubric_mock:
            result = await svc.screen_candidate(
                candidate_id=candidate_data["id"],
                vacancy_id=str(uuid4()),
                company_id="company-001",
                db=mock_db,
            )

        assert result["success"] is False
        assert result["error"] == "fairness_block"
        rubric_mock.assert_not_called()  # scoring must NOT run
        _assert_fairness_audit(audit_mock, "cv_scoring_service")


# ---------------------------------------------------------------------------
# C2 — LIAScoreService.calculate_score
# ---------------------------------------------------------------------------

class TestLIAScoreServiceFairness:
    @pytest.mark.parametrize("biased_text", DISCRIMINATORY_TEXTS)
    def test_calculate_score_blocks_discriminatory_query(self, biased_text):
        from app.domains.cv_screening.services import lia_score_service as mod

        svc = mod.LIAScoreService()
        candidate = {"id": str(uuid4()), "skills": ["python"]}
        criteria = {
            "query": biased_text,
            "company_id": "company-001",
        }

        with _patch_audit() as audit_mock:
            with pytest.raises(FairnessBlockedError) as exc_info:
                svc.calculate_score(candidate=candidate, criteria=criteria)

        assert exc_info.value.result.is_blocked is True
        _assert_fairness_audit(audit_mock, "lia_score_service")


# ---------------------------------------------------------------------------
# C3 — PreQualificationService.evaluate
# ---------------------------------------------------------------------------

class TestPreQualificationServiceFairness:
    @pytest.mark.parametrize("biased_text", DISCRIMINATORY_TEXTS)
    def test_evaluate_blocks_discriminatory_job_title(self, biased_text):
        from app.domains.cv_screening.services import pre_qualification_service as mod

        svc = mod.PreQualificationService()

        with _patch_audit() as audit_mock:
            with pytest.raises(FairnessBlockedError) as exc_info:
                svc.evaluate(
                    adherence_score=80.0,
                    matched_requirements=[],
                    missing_requirements=[],
                    job_title=biased_text,
                    company_name="ACME",
                )

        assert exc_info.value.result.is_blocked is True
        _assert_fairness_audit(audit_mock, "pre_qualification_service")


# ---------------------------------------------------------------------------
# C4 — EligibilityVerificationService.check_answer
# ---------------------------------------------------------------------------

class TestEligibilityVerificationServiceFairness:
    @pytest.mark.parametrize("biased_text", DISCRIMINATORY_TEXTS)
    def test_check_answer_blocks_discriminatory_question(self, biased_text):
        from app.domains.cv_screening.services import (
            eligibility_verification_service as mod,
        )

        svc = mod.EligibilityVerificationService()
        question = mod.EligibilityQuestion(
            id="q1",
            question_text=biased_text,
            question_type="text",
            options=None,
            is_eliminatory=True,
            expected_answer="sim",
            category="default",
        )

        with _patch_audit() as audit_mock:
            with pytest.raises(FairnessBlockedError) as exc_info:
                svc.check_answer(question=question, answer="sim")

        assert exc_info.value.result.is_blocked is True
        _assert_fairness_audit(audit_mock, "eligibility_verification_service")


# ---------------------------------------------------------------------------
# C5 — EvaluationCriteriaService.get_criteria_for_requirements
# ---------------------------------------------------------------------------

class TestEvaluationCriteriaServiceFairness:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("biased_text", DISCRIMINATORY_TEXTS)
    async def test_get_criteria_blocks_discriminatory_requirement(self, biased_text):
        from app.domains.cv_screening.services import evaluation_criteria_service as mod

        svc = mod.EvaluationCriteriaService()
        mock_db = AsyncMock()

        with _patch_audit() as audit_mock:
            with pytest.raises(FairnessBlockedError) as exc_info:
                await svc.get_criteria_for_requirements(
                    db=mock_db,
                    requirements=[biased_text, "Python avançado"],
                )

        assert exc_info.value.result.is_blocked is True
        # DB must NOT have been queried for criteria after the fairness block
        mock_db.execute.assert_not_called()
        _assert_fairness_audit(audit_mock, "evaluation_criteria_service")
