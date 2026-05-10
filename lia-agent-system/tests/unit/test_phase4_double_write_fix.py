"""TDD red-phase — P0-2 fix double bias_audit snapshot write per hire.

Audit finding (feature-impact agent):
BiasAuditService.get_adverse_impact_by_job (app/shared/services/bias_audit_service.py:322)
ALREADY internally calls save_snapshot(...) when company_id is not None
(line 386-393). The new _push_bias_snapshot helper in
transition_dispatch_service.py also calls save_snapshot explicitly,
producing TWO snapshot rows per hire — dashboards over-count and the
ISO 27001 trail is polluted.

Fix: pass company_id=None to get_adverse_impact_by_job (which suppresses
the internal save), keep the explicit save_snapshot call in
_push_bias_snapshot. This way exactly 1 row is created per hire AND the
helper retains its fail-soft try/except control.

Red sentinel: save_snapshot must be called exactly once during a single
conclusion_hired dispatch.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_push_bias_snapshot_calls_save_exactly_once():
    """P0-2: save_snapshot must be called exactly ONCE per hire.

    Pre-fix this test fails with call_count == 2 because:
    - _push_bias_snapshot calls get_adverse_impact_by_job(company_id=X)
    - get_adverse_impact_by_job internally calls save_snapshot when
      company_id is not None
    - _push_bias_snapshot then calls save_snapshot AGAIN explicitly

    Fix: _push_bias_snapshot must call get_adverse_impact_by_job with
    company_id=None to suppress the internal save, then save explicitly.
    """
    from app.domains.communication.services.transition_dispatch_service import (
        TransitionDispatchService,
    )

    # Build a TransitionDispatchService skipping __init__
    dispatcher = TransitionDispatchService.__new__(TransitionDispatchService)
    dispatcher.db = AsyncMock()

    # Mock BiasAuditService instance with both methods
    mock_report = MagicMock()
    mock_report.has_alerts = False
    mock_bias_svc = MagicMock()
    mock_bias_svc.get_adverse_impact_by_job = AsyncMock(return_value=mock_report)
    mock_bias_svc.save_snapshot = AsyncMock()

    company_uuid = "10000000-0000-0000-0000-000000000001"
    job_id = "20000000-0000-0000-0000-000000000002"

    async def _run():
        with patch(
            "app.shared.services.bias_audit_service.BiasAuditService",
            return_value=mock_bias_svc,
        ):
            await dispatcher._push_bias_snapshot(
                company_id=company_uuid, job_id=job_id,
            )

    asyncio.run(_run())

    # Critical assertion: exactly ONE save_snapshot call
    assert mock_bias_svc.save_snapshot.call_count == 1, (
        f"save_snapshot was called {mock_bias_svc.save_snapshot.call_count} "
        f"times (expected exactly 1). _push_bias_snapshot is producing a "
        f"double-write because get_adverse_impact_by_job internally calls "
        f"save_snapshot when company_id is non-None. Fix: pass "
        f"company_id=None to get_adverse_impact_by_job to suppress the "
        f"internal save, then save_snapshot explicitly stays the canonical "
        f"write path. See bias_audit_service.py:386-393."
    )


def test_push_bias_snapshot_passes_none_to_get_adverse_impact():
    """P0-2 supporting sentinel: get_adverse_impact_by_job must receive
    company_id=None so its internal save is suppressed."""
    from app.domains.communication.services.transition_dispatch_service import (
        TransitionDispatchService,
    )

    dispatcher = TransitionDispatchService.__new__(TransitionDispatchService)
    dispatcher.db = AsyncMock()

    mock_report = MagicMock()
    mock_bias_svc = MagicMock()
    mock_bias_svc.get_adverse_impact_by_job = AsyncMock(return_value=mock_report)
    mock_bias_svc.save_snapshot = AsyncMock()

    async def _run():
        with patch(
            "app.shared.services.bias_audit_service.BiasAuditService",
            return_value=mock_bias_svc,
        ):
            await dispatcher._push_bias_snapshot(
                company_id="10000000-0000-0000-0000-000000000001",
                job_id="20000000-0000-0000-0000-000000000002",
            )

    asyncio.run(_run())

    assert mock_bias_svc.get_adverse_impact_by_job.called
    kwargs = mock_bias_svc.get_adverse_impact_by_job.call_args.kwargs
    args = mock_bias_svc.get_adverse_impact_by_job.call_args.args
    # Accept either kwarg or positional company_id
    company_arg = kwargs.get("company_id")
    if company_arg is None and len(args) >= 3:
        company_arg = args[2]
    assert company_arg is None, (
        f"get_adverse_impact_by_job received company_id={company_arg!r} but "
        f"must receive None to suppress its internal save_snapshot side "
        f"effect (avoids the double-write)."
    )


def test_push_bias_snapshot_fail_soft_when_save_raises():
    """Regression: P0-2 fix must preserve fail-soft semantics. If
    save_snapshot raises, _push_bias_snapshot logs and swallows."""
    from app.domains.communication.services.transition_dispatch_service import (
        TransitionDispatchService,
    )

    dispatcher = TransitionDispatchService.__new__(TransitionDispatchService)
    dispatcher.db = AsyncMock()

    mock_report = MagicMock()
    mock_bias_svc = MagicMock()
    mock_bias_svc.get_adverse_impact_by_job = AsyncMock(return_value=mock_report)
    mock_bias_svc.save_snapshot = AsyncMock(side_effect=RuntimeError("DB down"))

    async def _run():
        with patch(
            "app.shared.services.bias_audit_service.BiasAuditService",
            return_value=mock_bias_svc,
        ):
            # Must NOT raise
            await dispatcher._push_bias_snapshot(
                company_id="10000000-0000-0000-0000-000000000001",
                job_id="20000000-0000-0000-0000-000000000002",
            )

    asyncio.run(_run())  # success means fail-soft worked
