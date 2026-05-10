"""TDD red-phase — WSI skill_probed wiring (Sprint B Phase 2, gap W1).

Harness taxonomy: Sensor (computacional, feedback) — verifies that every
question produced by WsiQuestionGenerator.generate_questions carries a
populated skill_probed (and skill_parent) so the downstream effectiveness
loop can aggregate outcomes.

Why this exists: _classify_questions_with_taxonomy is defined inside
wsi_question_generator.py but has zero callers in production code. As a
result GeneratedQuestion.skill_probed always defaults to None, the
transition_dispatch_service skips outcome recording (skill_probed check),
and wsi_question_effectiveness never accumulates samples. CLAUDE.md
"Wiring de features Phase X precisa ser end-to-end" applies — wire it
inside generate_questions so every caller benefits.

If any test below fails: ensure generate_questions calls
_classify_questions_with_taxonomy on the full list before returning, and
that the classifier modifies objects in-place (it already does — see
lines 64-96 of wsi_question_generator.py).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_enriched_jd():
    """Minimal EnrichedJobDescription stub for generator input."""
    from app.domains.job_creation.schemas import (
        EnrichedJobDescription,
        TechnicalSkill,
        BehavioralCompetency,
        ContextSignals,
    )

    return EnrichedJobDescription(
        titulo_padronizado="Backend Engineer",
        senioridade_confirmada="senior",
        skills_obrigatorias=[
            TechnicalSkill(skill="Python", contexto="API design"),
            TechnicalSkill(skill="PostgreSQL", contexto="schema modeling"),
        ],
        competencias_comportamentais=[
            BehavioralCompetency(
                competencia="prioritization",
                contexto="multiple deadlines",
                trait_big_five="conscientiousness",
            ),
        ],
        responsabilidades=["Build APIs", "Mentor juniors"],
        context_signals=ContextSignals(
            nivel_autonomia="alto",
            nivel_inovacao="medio",
            nivel_pressao="medio",
            nivel_colaboracao="alto",
        ),
    )


def _make_generator_with_fake_llm(question_text_template: str = "Conte uma situacao em que voce precisou cumprir um prazo apertado"):
    """Build WsiQuestionGenerator with stub LLMs that return parseable JSON."""
    import json
    from app.domains.job_creation.services.wsi_question_generator import (
        WSIQuestionGenerator,
    )

    # Stub LLM response with 2 questions per block
    def _make_llm():
        m = MagicMock()
        resp = MagicMock()
        resp.content = json.dumps({
            "questions": [
                {
                    "question": question_text_template,
                    "ideal_answer": "candidate explains STAR situation",
                    "scoring_rubric": {"1": "vague", "5": "specific"},
                    "skill": "prioritization",
                    "bloom_level": 4,
                    "dreyfus_level": 3,
                },
                {
                    "question": "Descreva uma vez em que recebeu feedback dificil",
                    "ideal_answer": "candidate accepts and acts",
                    "scoring_rubric": {"1": "defensive", "5": "growth-mindset"},
                    "skill": "feedback",
                    "bloom_level": 4,
                    "dreyfus_level": 3,
                },
            ],
        })
        m.invoke = MagicMock(return_value=resp)
        return m

    gen = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
    # Bypass __init__ which builds real LLMs; cache LLMs and override
    # _get_llm to return our stub regardless of `purpose`.
    stub = _make_llm()
    gen._llm_bigfive = stub
    gen._llm_tech = stub
    gen._llm_behav = stub
    gen._get_llm = lambda purpose: stub  # type: ignore[assignment]
    return gen


def _generate(generator):
    """Run generate_questions with the canonical 5+2 distribution."""
    enriched = _make_enriched_jd()
    return generator.generate_questions(
        enriched=enriched,
        seniority="senior",
        distribution={"technical": 2, "behavioral": 2},
        trait_rankings=[
            {"trait": "conscientiousness", "score": 0.8},
            {"trait": "openness", "score": 0.7},
        ],
    )


# ── AC-1 ────────────────────────────────────────────────────────────────────


def test_generate_questions_populates_skill_probed_on_every_question():
    """Every returned GeneratedQuestion MUST have skill_probed != None.

    If this fails: ensure generate_questions calls
    _classify_questions_with_taxonomy(all_questions, llm=self._behav_llm)
    before returning.
    """
    generator = _make_generator_with_fake_llm()
    questions = _generate(generator)

    assert len(questions) > 0, "generator returned 0 questions — check fake LLM JSON"
    for q in questions:
        assert getattr(q, "skill_probed", None) is not None, (
            f"GeneratedQuestion has skill_probed=None. Wire "
            f"_classify_questions_with_taxonomy inside generate_questions. "
            f"Question text: {q.question[:80]!r}"
        )


# ── AC-2 ────────────────────────────────────────────────────────────────────


def test_generate_questions_skill_probed_is_valid_taxonomy_id():
    """skill_probed must be a valid skill_id from the taxonomy."""
    from app.domains.job_creation.services.wsi_skill_taxonomy import find_skill

    generator = _make_generator_with_fake_llm()
    questions = _generate(generator)

    for q in questions:
        skill_id = getattr(q, "skill_probed", None)
        assert skill_id is not None
        assert find_skill(skill_id) is not None, (
            f"skill_probed={skill_id!r} is not present in wsi_skill_taxonomy. "
            f"Classifier must always fall back to a valid skill_id "
            f"(see DEFAULT_FALLBACK_SKILL in wsi_skill_classifier.py)."
        )


# ── AC-3 ────────────────────────────────────────────────────────────────────


def test_generate_questions_populates_skill_parent():
    """skill_parent should be populated when skill_probed is set."""
    generator = _make_generator_with_fake_llm()
    questions = _generate(generator)

    for q in questions:
        if getattr(q, "skill_probed", None) is not None:
            assert getattr(q, "skill_parent", None) is not None, (
                f"skill_probed={q.skill_probed!r} but skill_parent is None. "
                f"_classify_questions_with_taxonomy must call parent_of(skill_id)."
            )


# ── AC-4 ────────────────────────────────────────────────────────────────────


def test_generate_questions_classifier_crash_is_fail_soft():
    """If WsiSkillClassifier.classify raises, generate_questions must NOT
    propagate the error — questions still come back (with skill_probed=None
    is acceptable here, but generation MUST NOT crash).

    P1-6 hardening (post-audit): we capture the patched mock and assert
    it was actually invoked. Without this, a future refactor that lazy-
    imports `classify` on a different path would silently bypass the
    patch — tests pass for the wrong reason (false-green)."""
    generator = _make_generator_with_fake_llm()

    with patch(
        "app.domains.job_creation.services.wsi_skill_classifier.WsiSkillClassifier.classify",
        side_effect=RuntimeError("classifier exploded"),
    ) as classify_mock:
        # Should NOT raise
        questions = _generate(generator)

    assert classify_mock.called, (
        "WsiSkillClassifier.classify was never invoked. The patch path "
        "is wrong (lazy import elsewhere?) so this test was passing for "
        "the wrong reason — fail-soft was never exercised. Update the "
        "patch path to wherever generate_questions actually imports the "
        "classifier from, and re-run."
    )
    assert len(questions) > 0, (
        "generate_questions returned no questions when classifier crashed. "
        "_classify_questions_with_taxonomy already wraps the call in try/except — "
        "ensure generate_questions doesn't introduce its own crash path."
    )


# ── AC-5 ────────────────────────────────────────────────────────────────────


def test_generate_questions_classification_source_is_known_value():
    """skill_classification_source must be one of: llm | heuristic | default."""
    generator = _make_generator_with_fake_llm()
    questions = _generate(generator)

    valid_sources = {"llm", "heuristic", "default"}
    for q in questions:
        if getattr(q, "skill_probed", None) is not None:
            source = getattr(q, "skill_classification_source", None)
            assert source in valid_sources, (
                f"skill_classification_source={source!r}, expected one of "
                f"{valid_sources}."
            )
