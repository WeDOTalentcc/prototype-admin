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


def test_bigfive_department_history_default_is_on():
    """Sprint B Phase 3, decision D2: bigfive_department_history default is
    True (was False; flipped after Paulo confirmed comfort with homogeneity-
    bias risk vs disclosure-UI sequencing).

    If this fails: edit
    libs/models/lia_models/company_hiring_policy.py
    AUTOMATION_RULES_DEFAULTS["learning_loops"]["bigfive_department_history"]
    """
    from app.models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS

    loops = AUTOMATION_RULES_DEFAULTS["learning_loops"]
    assert loops["bigfive_department_history"] is True, (
        "AUTOMATION_RULES_DEFAULTS.learning_loops.bigfive_department_history "
        "should default to True per Sprint B Phase 3 decision D2."
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


def test_record_hire_is_not_wired_in_hook_conclusion_hired():
    """Sprint B Phase 2.5 prerequisite: candidate OCEAN traits snapshot is
    NOT yet emitted by the WSI scoring pipeline. Until that data source
    exists, _hook_conclusion_hired must NOT invoke
    BigFiveDepartmentService.record_hire — calling it with fabricated or
    empty snapshots would contaminate dept profiles with junk data.

    This sentinel inspects the source of _hook_conclusion_hired to ensure
    no caller appears, plus an explicit ADR-LGPD-001 reference is present
    in the docstring/comments.

    If this fails: someone wired record_hire prematurely. Either:
      (a) revert the wiring until candidate_traits_snapshot pipeline
          lands (Phase 2.5 ticket), OR
      (b) update this sentinel + ADR-LGPD-001 with the new contract for
          how snapshot is sourced.
    """
    import inspect
    from app.domains.communication.services import transition_dispatch_service

    source = inspect.getsource(
        transition_dispatch_service.TransitionDispatchService._hook_conclusion_hired
    )

    # Negative assertion: record_hire must not be called in current scope
    assert ".record_hire(" not in source, (
        "BigFiveDepartmentService.record_hire is being called in "
        "_hook_conclusion_hired but the candidate OCEAN traits snapshot "
        "data source does not exist yet (Phase 2.5 prerequisite). "
        "Either land the snapshot pipeline first, or drop this call. "
        "See ADR-LGPD-001 in the function's docstring."
    )

    # Positive assertion: ADR reference must be present so future readers
    # know why this hook intentionally skips record_hire.
    assert "ADR-LGPD-001" in source or "Phase 2.5" in source, (
        "_hook_conclusion_hired must reference ADR-LGPD-001 (or 'Phase 2.5') "
        "in its docstring/comments to document why BigFive.record_hire is "
        "deliberately not wired today. Add a docstring section explaining: "
        "(1) candidate_traits_snapshot data source is missing, and "
        "(2) aggregate-not-PII ANPD analysis for LGPD Art. 18."
    )
