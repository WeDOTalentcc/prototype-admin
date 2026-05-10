"""TDD red-phase — Phase 2.5: per-candidate OCEAN trait emission.

Closes the data-source gap that blocks BigFiveDepartmentService.record_hire
from being wired in _hook_conclusion_hired (ADR-LGPD-001 prerequisite).

Pipeline change:
  WSIQuestion.big_five_mapping
    -> ResponseAnalysis.trait_ocean   (NEW field, propagated by analyzer)
      -> WSIResult.ocean_traits        (NEW dict, aggregated by score_calculator)
        -> LiaOpinion.behavioral_analysis['ocean_traits']  (persisted by handler)
          -> _hook_conclusion_hired reads LiaOpinion + calls record_hire

Decisions (Paulo 2026-05-10):
  A1 storage: extend LiaOpinion.behavioral_analysis JSON (zero migration)
  A2 method:  Path A (deterministic from big_five_mapping)
  A3 grain:   candidate-level aggregate only
  A4 backfill: no
  A5 boy-scout: cleanup wsi/evaluation.py neuroticism -> stability

Per CLAUDE.md harness-engineering: every assertion message names the file
+ canonical fix when it fires. All sensors are computational/feedback.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── 1. Schema propagation: trait_ocean / ocean_traits exist ─────────────────


def test_response_analysis_has_trait_ocean_field():
    """ResponseAnalysis must carry the BigFive trait of its question.

    Without this field, the score-to-trait association is dropped during
    analyze() and downstream aggregation cannot happen.
    """
    from app.domains.cv_screening.services.wsi_service.models import (
        ResponseAnalysis,
    )

    ra = ResponseAnalysis(
        question_id="q-1",
        competency="conscientiousness",
        response_text="I delivered the project on schedule.",
        evidences=[],
        red_flags=[],
        final_score=4.0,
        justification="OK",
        trait_ocean="conscientiousness",
    )
    assert ra.trait_ocean == "conscientiousness", (
        "ResponseAnalysis.trait_ocean missing or not assignable. Add "
        "trait_ocean: str | None = None to the model in "
        "app/domains/cv_screening/services/wsi_service/models.py "
        "ResponseAnalysis class."
    )


def test_wsi_result_has_ocean_traits_dict():
    """WSIResult must carry a per-trait aggregate dict so persistence
    layer can copy it into LiaOpinion.behavioral_analysis."""
    from app.domains.cv_screening.services.wsi_service.models import (
        ResponseAnalysis, WSIResult,
    )

    result = WSIResult(
        candidate_id="c-1",
        job_vacancy_id="j-1",
        technical_wsi=4.0,
        behavioral_wsi=3.5,
        overall_wsi=3.85,
        classification="alto",
        response_analyses=[],
        ocean_traits={"conscientiousness": 0.8},
    )
    assert isinstance(result.ocean_traits, dict), (
        "WSIResult.ocean_traits missing. Add ocean_traits: dict[str, float] "
        "= Field(default_factory=dict) to WSIResult in "
        "app/domains/cv_screening/services/wsi_service/models.py."
    )


# ── 2. Propagation: WSIResponseAnalyzer carries trait_ocean ─────────────────


def test_response_analyzer_propagates_trait_ocean():
    """When WSIQuestion has big_five_mapping, the ResponseAnalysis emitted
    by analyze() must carry that as trait_ocean."""
    from app.domains.cv_screening.services.wsi_service.models import WSIQuestion
    from app.domains.cv_screening.services.wsi_service.response_analyzer import (
        WSIResponseAnalyzer,
    )

    question = WSIQuestion(
        id="q-1",
        competency="prazos_apertados",
        framework="CBI",
        question_type="contextual",
        question_text="Conte uma situação...",
        weight=0.2,
        expected_signals=[],
        scoring_criteria={},
        big_five_mapping="conscientiousness",
    )
    analyzer = WSIResponseAnalyzer(llm=None)
    analysis = asyncio.run(analyzer.analyze(question, "Entreguei no prazo, x, y, z"))

    assert getattr(analysis, "trait_ocean", None) == "conscientiousness", (
        f"WSIResponseAnalyzer.analyze did not propagate trait_ocean from "
        f"WSIQuestion.big_five_mapping. Got "
        f"trait_ocean={getattr(analysis, 'trait_ocean', None)!r}. Add "
        f"trait_ocean=question.big_five_mapping to the ResponseAnalysis() "
        f"construction in response_analyzer.py."
    )


def test_response_analyzer_handles_missing_big_five_mapping():
    """When big_five_mapping is None (technical questions, non-BigFive
    frameworks), trait_ocean stays None — must NOT crash."""
    from app.domains.cv_screening.services.wsi_service.models import WSIQuestion
    from app.domains.cv_screening.services.wsi_service.response_analyzer import (
        WSIResponseAnalyzer,
    )

    question = WSIQuestion(
        id="q-2",
        competency="python",
        framework="Bloom",
        question_type="microcase",
        question_text="Implemente um decorator...",
        weight=0.2,
        expected_signals=[],
        scoring_criteria={},
        big_five_mapping=None,
    )
    analyzer = WSIResponseAnalyzer(llm=None)
    analysis = asyncio.run(analyzer.analyze(question, "decorator que recebe arg..."))

    assert getattr(analysis, "trait_ocean", "MISSING") is None, (
        "trait_ocean should be None when big_five_mapping is None, not "
        "missing or some default string."
    )


# ── 3. Aggregation: WSIScoreCalculator builds ocean_traits dict ─────────────


def test_score_calculator_aggregates_ocean_traits_by_trait():
    """ResponseAnalysis with trait_ocean must be grouped by trait, scores
    averaged within each trait, and normalized 1-5 → 0-1."""
    from app.domains.cv_screening.services.wsi_service.models import (
        ResponseAnalysis,
    )
    from app.domains.cv_screening.services.wsi_service.score_calculator import (
        WSIScoreCalculator,
    )

    responses = [
        ResponseAnalysis(
            question_id="q-1", competency="prazos",
            response_text="x", evidences=[], red_flags=[],
            final_score=5.0, justification="x",
            trait_ocean="conscientiousness",
        ),
        ResponseAnalysis(
            question_id="q-2", competency="organizacao",
            response_text="x", evidences=[], red_flags=[],
            final_score=3.0, justification="x",
            trait_ocean="conscientiousness",
        ),
        ResponseAnalysis(
            question_id="q-3", competency="ambiguidade",
            response_text="x", evidences=[], red_flags=[],
            final_score=4.0, justification="x",
            trait_ocean="openness",
        ),
    ]
    calc = WSIScoreCalculator()
    result = calc.calculate(
        candidate_id="c-1", job_vacancy_id="j-1",
        responses=responses,
        weights={"prazos": 0.4, "organizacao": 0.3, "ambiguidade": 0.3},
    )

    ocean = result.ocean_traits
    assert "conscientiousness" in ocean, (
        f"WSIResult.ocean_traits should aggregate scores by trait. Got "
        f"{ocean!r}. Implement aggregation in WSIScoreCalculator.calculate "
        f"that groups responses by .trait_ocean, averages final_score, "
        f"and normalizes 1-5 → 0-1 (formula: (score - 1) / 4)."
    )
    # mean(5, 3) = 4 -> (4-1)/4 = 0.75
    assert 0.74 <= ocean["conscientiousness"] <= 0.76, (
        f"conscientiousness expected ~0.75 (mean of [5, 3] normalized "
        f"1-5→0-1), got {ocean['conscientiousness']}."
    )
    # 4 -> (4-1)/4 = 0.75
    assert 0.74 <= ocean["openness"] <= 0.76


def test_score_calculator_skips_responses_without_trait_ocean():
    """Technical responses (trait_ocean=None) must NOT contribute to the
    ocean_traits aggregate."""
    from app.domains.cv_screening.services.wsi_service.models import (
        ResponseAnalysis,
    )
    from app.domains.cv_screening.services.wsi_service.score_calculator import (
        WSIScoreCalculator,
    )

    responses = [
        ResponseAnalysis(
            question_id="q-1", competency="python",
            response_text="x", evidences=[], red_flags=[],
            final_score=5.0, justification="x",
            trait_ocean=None,  # technical
        ),
        ResponseAnalysis(
            question_id="q-2", competency="prazos",
            response_text="x", evidences=[], red_flags=[],
            final_score=3.0, justification="x",
            trait_ocean="conscientiousness",
        ),
    ]
    calc = WSIScoreCalculator()
    result = calc.calculate(
        candidate_id="c-1", job_vacancy_id="j-1",
        responses=responses,
        weights={},
    )
    ocean = result.ocean_traits
    # Only conscientiousness present (3 -> 0.5)
    assert set(ocean.keys()) == {"conscientiousness"}, (
        f"Expected ocean_traits to contain only 'conscientiousness' "
        f"(technical response was skipped), got keys={set(ocean.keys())}."
    )


def test_score_calculator_empty_when_no_trait_responses():
    """If no response carries trait_ocean, ocean_traits is empty dict
    (not None, never raises)."""
    from app.domains.cv_screening.services.wsi_service.models import (
        ResponseAnalysis,
    )
    from app.domains.cv_screening.services.wsi_service.score_calculator import (
        WSIScoreCalculator,
    )

    responses = [
        ResponseAnalysis(
            question_id="q-1", competency="python",
            response_text="x", evidences=[], red_flags=[],
            final_score=5.0, justification="x",
        ),
    ]
    calc = WSIScoreCalculator()
    result = calc.calculate(
        candidate_id="c-1", job_vacancy_id="j-1",
        responses=responses,
        weights={},
    )
    assert result.ocean_traits == {}, (
        f"Expected empty dict when no trait_ocean present, got "
        f"{result.ocean_traits!r}."
    )


# ── 4. record_hire wiring: hook reads LiaOpinion + invokes record_hire ──────


def test_hook_conclusion_hired_invokes_record_hire_when_ocean_exists():
    """Phase 2.5 contract: when LiaOpinion.behavioral_analysis has
    ocean_traits, _hook_conclusion_hired must call
    BigFiveDepartmentService.record_hire with the snapshot."""
    from app.domains.communication.services.transition_dispatch_service import (
        TransitionDispatchService,
    )

    record_hire_mock = AsyncMock()
    dispatcher = TransitionDispatchService.__new__(TransitionDispatchService)

    # Stub LiaOpinion-like object surfaced through the lookup path
    fake_opinion = MagicMock()
    fake_opinion.behavioral_analysis = {
        "ocean_traits": {
            "openness": 0.7,
            "conscientiousness": 0.8,
            "extraversion": 0.6,
            "agreeableness": 0.65,
            "stability": 0.75,
        }
    }
    # vacancy_candidate stub (linked to candidate with the LiaOpinion)
    vc = MagicMock()
    vc.vacancy_id = "00000000-0000-0000-0000-000000000001"
    vc.candidate_id = "00000000-0000-0000-0000-000000000002"
    job = MagicMock()
    from datetime import datetime
    job.created_at = datetime.utcnow()
    job.department = "Engineering"
    job.seniority_level = "senior"

    call_idx = {"i": 0}

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        scalars = MagicMock()
        if call_idx["i"] == 0:
            scalars.first = MagicMock(return_value=vc)
        elif call_idx["i"] == 1:
            scalars.first = MagicMock(return_value=job)
        else:
            scalars.first = MagicMock(return_value=fake_opinion)
            scalars.all = MagicMock(return_value=[])
        result.scalars = MagicMock(return_value=scalars)
        result.scalar_one_or_none = MagicMock(return_value=None)
        result.all = MagicMock(return_value=[])
        call_idx["i"] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=_execute)
    db.commit = AsyncMock()
    dispatcher.db = db

    async def _run():
        with patch(
            "app.domains.job_creation.services.bigfive_service.BigFiveDepartmentService.record_hire",
            new=record_hire_mock,
        ), patch(
            "app.domains.job_creation.services.jd_similar_service.JdSimilarService.mark_filled",
            new=AsyncMock(),
        ), patch(
            "app.shared.compliance.audit_service.get_audit_service",
            return_value=MagicMock(log_action=AsyncMock()),
        ), patch.object(
            dispatcher, "_record_wsi_outcomes_for_candidate", new=AsyncMock(),
        ), patch.object(
            dispatcher, "_push_bias_snapshot", new=AsyncMock(),
        ):
            await dispatcher._hook_conclusion_hired(
                vacancy_candidate_id="vc-1",
                company_id="00000000-0000-0000-0000-0000000000aa",
            )

    asyncio.run(_run())

    assert record_hire_mock.called, (
        "BigFiveDepartmentService.record_hire was NOT invoked even though "
        "LiaOpinion.behavioral_analysis['ocean_traits'] is populated. "
        "Wire the call inside _hook_conclusion_hired AFTER mark_filled, "
        "reading the latest LiaOpinion for the candidate and passing the "
        "snapshot dict to record_hire(company_id=, department=, "
        "seniority_level=, candidate_traits_snapshot=...). Update "
        "ADR-LGPD-001 sentinel accordingly."
    )
    kwargs = record_hire_mock.call_args.kwargs
    assert kwargs.get("candidate_traits_snapshot", {}).get("conscientiousness") == 0.8


def test_hook_conclusion_hired_skips_record_hire_when_no_ocean():
    """When LiaOpinion is missing or has no ocean_traits, record_hire
    must NOT be called (safer than calling with empty dict)."""
    from app.domains.communication.services.transition_dispatch_service import (
        TransitionDispatchService,
    )

    record_hire_mock = AsyncMock()
    dispatcher = TransitionDispatchService.__new__(TransitionDispatchService)

    vc = MagicMock()
    vc.vacancy_id = "00000000-0000-0000-0000-000000000001"
    vc.candidate_id = "00000000-0000-0000-0000-000000000002"
    job = MagicMock()
    from datetime import datetime
    job.created_at = datetime.utcnow()
    job.department = "Engineering"
    job.seniority_level = "senior"

    call_idx = {"i": 0}

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        scalars = MagicMock()
        if call_idx["i"] == 0:
            scalars.first = MagicMock(return_value=vc)
        elif call_idx["i"] == 1:
            scalars.first = MagicMock(return_value=job)
        else:
            # No LiaOpinion or empty behavioral_analysis
            scalars.first = MagicMock(return_value=None)
            scalars.all = MagicMock(return_value=[])
        result.scalars = MagicMock(return_value=scalars)
        result.scalar_one_or_none = MagicMock(return_value=None)
        result.all = MagicMock(return_value=[])
        call_idx["i"] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=_execute)
    db.commit = AsyncMock()
    dispatcher.db = db

    async def _run():
        with patch(
            "app.domains.job_creation.services.bigfive_service.BigFiveDepartmentService.record_hire",
            new=record_hire_mock,
        ), patch(
            "app.domains.job_creation.services.jd_similar_service.JdSimilarService.mark_filled",
            new=AsyncMock(),
        ), patch(
            "app.shared.compliance.audit_service.get_audit_service",
            return_value=MagicMock(log_action=AsyncMock()),
        ), patch.object(
            dispatcher, "_record_wsi_outcomes_for_candidate", new=AsyncMock(),
        ), patch.object(
            dispatcher, "_push_bias_snapshot", new=AsyncMock(),
        ):
            await dispatcher._hook_conclusion_hired(
                vacancy_candidate_id="vc-1",
                company_id="00000000-0000-0000-0000-0000000000aa",
            )

    asyncio.run(_run())

    assert not record_hire_mock.called, (
        "record_hire was invoked despite no ocean_traits being available. "
        "Skip the call when behavioral_analysis['ocean_traits'] is empty "
        "or LiaOpinion is absent — calling with empty dict contaminates "
        "the dept aggregate (ADR-LGPD-001 fail-safe)."
    )


# ── 5. ADR-LGPD-001 sentinel flip: docstring acknowledges record_hire wired ─


def test_adr_lgpd_001_docstring_reflects_phase_2_5_completed():
    """Once Phase 2.5 ships, the ADR docstring must acknowledge that
    record_hire IS wired now (the previous DEFERRED note becomes
    historical context)."""
    import inspect
    from app.domains.communication.services import transition_dispatch_service

    source = inspect.getsource(
        transition_dispatch_service.TransitionDispatchService._hook_conclusion_hired
    )
    # Must reference Phase 2.5 completion
    assert "Phase 2.5" in source, (
        "ADR-LGPD-001 docstring lost the Phase 2.5 reference. Keep it as "
        "history of the deferral, but ensure the doc now states "
        "'record_hire IS wired (Phase 2.5 shipped <date>)' to match "
        "the behavioral contract."
    )
    # The legacy 'NOT wired' assertion in the doc should now name the data
    # source path (LiaOpinion.behavioral_analysis['ocean_traits']).
    assert (
        "behavioral_analysis" in source
        or "ocean_traits" in source
        or "LiaOpinion" in source
    ), (
        "ADR-LGPD-001 docstring must reference the new data source for "
        "ocean_traits (LiaOpinion.behavioral_analysis['ocean_traits']) so "
        "future readers know where the snapshot now comes from."
    )
