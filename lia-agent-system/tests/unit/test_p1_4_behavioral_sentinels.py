"""TDD red-phase — P1-4: behavioral sentinel complementing source-inspection
ADR-LGPD-001 / Phase 2.5 wiring guards.

Audit finding (TDD agent): test_record_hire_is_not_wired_in_hook_conclusion_hired
in test_bigfive_phase3_governance.py uses inspect.getsource — would
break on cosmetic refactor.

Decision (post-audit re-review): the source-inspection sentinel is
defense-in-depth and remains valuable (catches accidental wiring even
if a refactor renames the helper). However it should be COMPLEMENTED
by a behavioral assertion: dispatch a conclusion_hired event and
verify BigFiveDepartmentService.record_hire is not invoked. This test
adds that complement without removing the source-inspection guard.

Behavioral mocking is intentionally tight: only the methods that get
called during normal dispatch get mocked (DB lookups + downstream
helpers), and assertion focuses on the single behavior we care about
(record_hire absence).
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


def _make_dispatcher():
    """Build a TransitionDispatchService bypassing __init__ + DB."""
    from app.domains.communication.services.transition_dispatch_service import (
        TransitionDispatchService,
    )

    dispatcher = TransitionDispatchService.__new__(TransitionDispatchService)

    # Mock db.execute returning empty (no VC found) is the safe path —
    # _hook_conclusion_hired short-circuits when vc is None, but we want
    # to traverse the full path. Provide minimal VC + Job mocks.
    vc_mock = MagicMock()
    vc_mock.vacancy_id = "00000000-0000-0000-0000-000000000001"
    job_mock = MagicMock()
    from datetime import datetime
    job_mock.created_at = datetime.utcnow()

    # First execute returns vc, second returns job
    call_idx = {"i": 0}

    async def _execute(stmt, *args, **kwargs):
        result = MagicMock()
        scalars = MagicMock()
        if call_idx["i"] == 0:
            scalars.first = MagicMock(return_value=vc_mock)
        elif call_idx["i"] == 1:
            scalars.first = MagicMock(return_value=job_mock)
        else:
            scalars.first = MagicMock(return_value=None)
            scalars.all = MagicMock(return_value=[])
        result.scalars = MagicMock(return_value=scalars)
        result.scalar_one_or_none = MagicMock(return_value=None)
        result.scalar = MagicMock(return_value=None)
        result.all = MagicMock(return_value=[])
        call_idx["i"] += 1
        return result

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=_execute)
    db.commit = AsyncMock()
    dispatcher.db = db
    return dispatcher


def test_record_hire_not_invoked_when_no_ocean_traits_available():
    """Phase 2.5 SHIPPED — record_hire is now WIRED, but only when
    LiaOpinion.behavioral_analysis['ocean_traits'] is populated. This
    sentinel covers the graceful-degrade path: when no LiaOpinion
    exists for the candidate (or its behavioral_analysis lacks
    ocean_traits), record_hire MUST NOT be called — calling with
    fabricated/empty snapshot would contaminate dept aggregates per
    ADR-LGPD-001 fail-safe.

    Setup: dispatcher's mocked db.execute returns scalars().first()=None
    for the LiaOpinion lookup (no opinion in DB), so the helper should
    skip the call.
    """
    dispatcher = _make_dispatcher()

    record_hire_mock = AsyncMock()

    async def _run():
        # Patch all downstream collaborators that would otherwise touch
        # network or DB. Note: we do NOT patch _record_bigfive_hire
        # itself — we want the real helper to run and short-circuit on
        # the missing LiaOpinion (db.execute returns None).
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
        "BigFiveDepartmentService.record_hire was invoked despite no "
        "LiaOpinion / no ocean_traits in the dispatcher's mock chain. "
        "_record_bigfive_hire helper MUST short-circuit when the "
        "LiaOpinion lookup returns None or behavioral_analysis lacks "
        "ocean_traits — calling with empty snapshot would contaminate "
        "the dept aggregate (ADR-LGPD-001 fail-safe)."
    )
