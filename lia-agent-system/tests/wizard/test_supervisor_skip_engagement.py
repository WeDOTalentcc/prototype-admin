"""Sprint F.4 iter 3 (2026-05-20) — Sensors: supervisor skip log engagement
+ WSI question generator None-distribution guard.

Background — observed bug in F.2 retest 2026-05-20 19:27 UTC:
- Turn 5 sent "modo compacto, 7 perguntas" while wizard paused at
  competency_gate.
- Supervisor skip DID engage (we can see classifier resolve
  ``select_compact`` in the audit log) BUT the HTTP reply was the
  silent-fallback message ("Parece que a mensagem da vaga foi cortada").
- Root cause: graph routed ``competency_gate -> wsi_questions`` correctly,
  then ``wsi_question_generator.generate_questions`` crashed with
  ``AttributeError: 'NoneType' object has no attribute 'get'`` because
  ``distribution`` was passed as None. Exception propagated up to
  ``wizard_session_service.process_message:L958`` which caught it and
  emitted the LLM-generated fallback.

Two sensors below:

R1 — ``test_supervisor_skip_emits_info_log`` — the skip code MUST log at
INFO level (was logger.debug, invisible in prod). Without this log, a
future regression where _prior_stage is silently None (and supervisor
re-runs erroneously) is unobservable.

R2 — ``test_wsi_generator_tolerates_none_distribution`` — defensive
guard inside ``generate_questions`` MUST coerce ``distribution=None``
to the canonical default dict so the graph never crashes mid-resume.
"""
from __future__ import annotations

import logging
import pytest


# ---------------------------------------------------------------------- #
# R1 — supervisor decision log MUST be INFO (visible in prod logs)
# ---------------------------------------------------------------------- #
def test_supervisor_skip_log_uses_info_level():
    """The diagnostic skip-decision log was upgraded from DEBUG to INFO
    in Sprint F.4 iter 3. Asserting via source inspection so the test
    runs without spinning up the full wizard graph."""
    from pathlib import Path
    src = Path(
        "app/domains/job_creation/services/wizard_session_service.py"
    ).read_text()
    # Diagnostic log marker added 2026-05-20.
    assert (
        'logger.info(\n'
        '            "[WizardSession] supervisor decision: prior_stage=%r '
        'skip=%s "\n'
        '            "msg_len=%d thread=%s",'
    ) in src, (
        "Supervisor decision INFO log missing. The diag line "
        "'[WizardSession] supervisor decision: ...' must be logger.info, "
        "not logger.debug. Format updated by Sprint F.2-v2 (2026-05-26) "
        "to include msg_len for correlating skip decisions with content "
        "length — see test_supervisor_skip_long_content_threshold.py."
    )
    # The original "supervisor SKIPPED" line must also be INFO so we can
    # confirm in prod logs that the skip path engaged.
    assert (
        'logger.info(\n'
        '                "[WizardSession] supervisor SKIPPED (active stage=%s "'
    ) in src, (
        "'supervisor SKIPPED' log must be logger.info (was logger.debug). "
        "Without INFO visibility we cannot detect future regressions where "
        "_prior_stage silently mismatches _ACTIVE_WIZARD_STAGES."
    )


# ---------------------------------------------------------------------- #
# R2 — WSI generator MUST tolerate distribution=None (don't crash graph)
# ---------------------------------------------------------------------- #
def test_wsi_generator_tolerates_none_distribution(monkeypatch):
    """When ``state['question_distribution']`` is explicitly None
    (observed during Command(resume=...) before dispatcher writes the
    dict), ``generate_questions`` must coerce to default rather than
    raise AttributeError. The AttributeError previously propagated to
    ``wizard_session_service:L958`` triggering the silent LLM fallback
    ('vaga foi cortada') — see Sprint F.4 iter 3 post-mortem."""
    from app.domains.job_creation.services.wsi_question_generator import (
        WSIQuestionGenerator,
    )

    gen = WSIQuestionGenerator()

    # Stub the per-block generator so we don't hit the LLM in unit test.
    monkeypatch.setattr(
        gen, "_generate_block", lambda *args, **kwargs: []
    )

    # CRITICAL: distribution=None must NOT raise. Pre-fix this raised
    # AttributeError: 'NoneType' object has no attribute 'get' at
    # wsi_question_generator.py:403.
    result = gen.generate_questions(
        enriched=None,           # also defensive — fallback path
        seniority="pleno",
        distribution=None,        # <-- the bug trigger
        trait_rankings=[],
    )
    assert result == [], (
        "With distribution=None the generator should fall back to the "
        "canonical default {technical: 5, behavioral: 2} and proceed "
        "(stubbed _generate_block returns []) — instead got %r" % (result,)
    )


def test_wsi_generator_tolerates_non_dict_distribution(monkeypatch):
    """Defense in depth — any non-dict distribution (list, str, int)
    must be coerced to the canonical default."""
    from app.domains.job_creation.services.wsi_question_generator import (
        WSIQuestionGenerator,
    )

    gen = WSIQuestionGenerator()
    monkeypatch.setattr(
        gen, "_generate_block", lambda *args, **kwargs: []
    )
    for bogus in (None, "compact", 7, [], object()):
        result = gen.generate_questions(
            enriched=None,
            seniority="pleno",
            distribution=bogus,  # type: ignore[arg-type]
            trait_rankings=[],
        )
        assert result == [], (
            "distribution=%r should coerce to default dict, not crash. "
            "Got %r" % (bogus, result)
        )
