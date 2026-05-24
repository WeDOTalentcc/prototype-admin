"""TDD red-phase — Sprint B Phase 3 governance + canonical defaults.

Three concerns covered:

1. D2 — AUTOMATION_RULES_DEFAULTS.learning_loops.bigfive_department_history
   should default to True (Paulo decision 2026-05-10). Current default is
   False (opt-in); tests below assert the new canonical default.

2. C5 — BigFiveDepartmentProfileRepository must enforce company_id on
   every public method. The repo already does this by design (composite
   key (company_id, department, seniority_level) + _require_company_id),
   so these tests pass today as regression sentinels — if anyone later
   adds a record_id-keyed method without company_id, they fail loud.

3. ADR-LGPD-001 — _hook_conclusion_hired must NOT call
   BigFiveDepartmentService.record_hire today (Sprint B Phase 2.5
   prerequisite: candidate OCEAN traits snapshot is not yet emitted by
   the WSI scoring pipeline). Sentinel guard: refuse premature wiring
   that would contaminate dept profiles with fabricated/empty snapshots.

Harness taxonomy: computational sensors (feedback). Error messages
point to the exact file + canonical decision when violated.
"""
from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── 1. D2 — Canonical default toggle ────────────────────────────────────────


def test_bigfive_department_history_default_is_off_for_lgpd():
    """ADR-LGPD-001 (reaffirmed 2026-05-24): bigfive_department_history
    default is False (opt-in via UI disclosure modal).

    History: D2 (2026-05-10) flipped default to True invocando aggregate-not-PII
    analysis. F2.1 audit 2026-05-24 reverteu para False ao descobrir que:
      - Frontend UI canonical (LearningLoopsPanel) já mostra requiresDisclosure
      - Helper canonical docstring sempre documentou default False
      - Quatro fontes paralelas (constant, helper docstring, UI, consumer literal)
        divergiam silenciosamente
    Conservative defaults preservam ADR-LGPD-001 (opt-in explícito) + ANPD Art.
    12 §1: empresa nova começa OFF, ativa via consentimento via modal canonical.

    If this fails: edit
    libs/models/lia_models/company_hiring_policy.py
    AUTOMATION_RULES_DEFAULTS["learning_loops"]["bigfive_department_history"]
    """
    from app.models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS

    loops = AUTOMATION_RULES_DEFAULTS["learning_loops"]
    assert loops["bigfive_department_history"] is False, (
        "AUTOMATION_RULES_DEFAULTS.learning_loops.bigfive_department_history "
        "deve default False (ADR-LGPD-001 conservative + opt-in via UI canonical "
        "disclosure modal). F2.1 audit 2026-05-24 reverteu D2 (2026-05-10)."
    )


def test_other_learning_loops_defaults_unchanged():
    """Regression guard: D2 only flipped bigfive_department_history.
    Other Sprint B loops keep their canonical defaults.
    """
    from app.models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS

    loops = AUTOMATION_RULES_DEFAULTS["learning_loops"]
    assert loops["enabled"] is True, "master switch unchanged"
    assert loops["bigfive_company_culture"] is True, (
        "DNA cultural is static description, default ON unchanged"
    )
    assert loops["wsi_question_effectiveness"] is False, (
        "WSI Effectiveness is opt-in (Phase 3), default OFF unchanged"
    )
    assert loops["jd_similar_suggestion"] is True, (
        "JD Similar low-risk, default ON unchanged"
    )


# ── 2. C5 — BigFiveDepartmentProfileRepository multi-tenancy sentinels ──────


@pytest.mark.asyncio
async def test_bigfive_repo_get_or_none_requires_company_id():
    """company_id='' must raise ValueError (regression guard)."""
    from app.domains.job_creation.repositories.bigfive_department_profile_repository import (
        BigFiveDepartmentProfileRepository,
    )

    db = AsyncMock()
    repo = BigFiveDepartmentProfileRepository(db)
    with pytest.raises(ValueError, match="company_id"):
        await repo.get_or_none(company_id="", department="Eng", seniority_level="senior")


@pytest.mark.asyncio
async def test_bigfive_repo_get_all_for_company_requires_company_id():
    from app.domains.job_creation.repositories.bigfive_department_profile_repository import (
        BigFiveDepartmentProfileRepository,
    )

    db = AsyncMock()
    repo = BigFiveDepartmentProfileRepository(db)
    with pytest.raises(ValueError, match="company_id"):
        await repo.get_all_for_company(company_id="")


@pytest.mark.asyncio
async def test_bigfive_repo_upsert_requires_company_id():
    from app.domains.job_creation.repositories.bigfive_department_profile_repository import (
        BigFiveDepartmentProfileRepository,
    )

    db = AsyncMock()
    repo = BigFiveDepartmentProfileRepository(db)
    with pytest.raises(ValueError, match="company_id"):
        await repo.upsert(
            company_id="",
            department="Eng",
            seniority_level="senior",
            trait_delta={"openness": 0.7},
        )


@pytest.mark.asyncio
async def test_bigfive_repo_upsert_rejects_non_ocean_traits():
    """Defense-in-depth: upsert rejects any trait outside OCEAN whitelist.
    PII guard against accidentally inserting protected-class fields like
    age/gender as 'traits'."""
    from app.domains.job_creation.repositories.bigfive_department_profile_repository import (
        BigFiveDepartmentProfileRepository,
    )

    db = AsyncMock()
    repo = BigFiveDepartmentProfileRepository(db)
    with pytest.raises(ValueError, match="invalid keys"):
        await repo.upsert(
            company_id="co-1",
            department="Eng",
            seniority_level="senior",
            trait_delta={"age": 35, "gender": "M"},  # ← non-OCEAN, must reject
        )


# ── 3. ADR-LGPD-001 sentinel — record_hire NOT wired in conclusion_hired ────


def test_record_hire_is_wired_via_record_bigfive_hire_helper():
    """Phase 2.5 SHIPPED (was: record_hire NOT wired). Sentinel flipped.

    Originally guarded against premature wiring — record_hire must not
    be called until per-candidate OCEAN traits snapshot exists. Phase 2.5
    closed that gap (LiaOpinion.behavioral_analysis['ocean_traits']
    populated by handlers_screening). The hook now invokes record_hire
    via the _record_bigfive_hire helper, which reads the latest
    LiaOpinion and forwards the snapshot.

    This sentinel now ensures:
      (a) The _record_bigfive_hire helper exists in the dispatcher.
      (b) _hook_conclusion_hired calls it.
      (c) ADR-LGPD-001 docstring acknowledges Phase 2.5 shipped.

    If this fails: either record_hire wiring was reverted (look for the
    helper), or the docstring lost the Phase 2.5 reference.
    """
    import inspect
    from app.domains.communication.services import transition_dispatch_service

    cls = transition_dispatch_service.TransitionDispatchService
    hook_source = inspect.getsource(cls._hook_conclusion_hired)

    # Helper must exist on the class
    assert hasattr(cls, "_record_bigfive_hire"), (
        "TransitionDispatchService no longer has the "
        "_record_bigfive_hire helper. Phase 2.5 introduced it to read "
        "LiaOpinion.behavioral_analysis['ocean_traits'] and call "
        "BigFiveDepartmentService.record_hire. If the helper was renamed, "
        "update this sentinel; if removed, restore Phase 2.5 wiring."
    )

    # Hook must call the helper
    assert "_record_bigfive_hire" in hook_source, (
        "_hook_conclusion_hired no longer calls _record_bigfive_hire. "
        "Phase 2.5 wired this call after _push_bias_snapshot — restore "
        "or update this sentinel if the call moved."
    )

    # Docstring must reference Phase 2.5 + LiaOpinion data source
    assert "Phase 2.5" in hook_source, (
        "Docstring lost the Phase 2.5 reference. Keep Phase 2.5 mention "
        "as historical anchor for the data-source change."
    )
    assert (
        "behavioral_analysis" in hook_source
        or "ocean_traits" in hook_source
        or "LiaOpinion" in hook_source
    ), (
        "Docstring must reference the new data source for ocean_traits "
        "(LiaOpinion.behavioral_analysis['ocean_traits']) so future "
        "readers know where the snapshot now comes from."
    )
