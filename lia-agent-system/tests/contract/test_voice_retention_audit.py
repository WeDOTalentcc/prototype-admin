"""
Tests for P1 ticket: Audit canonical meta no _run_voice_retention.

Sprint 1b F-05 cron retenção 60d/180d/365d era audit-blind. LGPD Art. 20
trail meta-audit ausente. Cron task só fazia logger.info — sem rastro
canônico de "X registros purgados em fase Y".

Fix: cada phase (audio/transcript/wsi_score) chama AuditService.log_decision
com phase_name + records_purged count. Best-effort: audit failure NUNCA
bloqueia o purge.

Audit ref: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-05 + backlog P1 #2
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_session_ctx(fake_db):
    """Build async-context-manager wrapper around fake_db."""
    class _FakeSessionCtx:
        async def __aenter__(self):
            return fake_db

        async def __aexit__(self, *a):
            return None

    return _FakeSessionCtx()


def _build_fake_db(rowcount: int = 2, scalar: int = 0) -> MagicMock:
    fake_db = MagicMock()
    fake_result = MagicMock()
    fake_result.rowcount = rowcount
    fake_result.scalar = MagicMock(return_value=scalar)
    fake_db.execute = AsyncMock(return_value=fake_result)
    fake_db.commit = AsyncMock()
    fake_db.rollback = AsyncMock()
    return fake_db


@pytest.mark.asyncio
async def test_each_phase_logs_audit_canonical():
    """P1 #2: each retention phase emits AuditService.log_decision row."""
    from app.jobs.tasks import voice_retention

    fake_db = _build_fake_db(rowcount=3)

    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock(return_value=MagicMock())
    mock_audit_cls = MagicMock(return_value=mock_audit)

    with patch(
        "app.core.database.AsyncSessionLocal", return_value=_make_session_ctx(fake_db)
    ), patch(
        "app.shared.compliance.audit_service.AuditService", mock_audit_cls
    ):
        await voice_retention._run_voice_retention(dry_run=False)

    # 3 phases (audio / transcript / wsi_score) → at least 3 log_decision calls
    assert mock_audit.log_decision.await_count >= 3, (
        f"Expected >=3 audit rows (one per phase). "
        f"Got {mock_audit.log_decision.await_count}."
    )

    # Each call must have phase identifier in action field
    actions = [
        c.kwargs.get("action") for c in mock_audit.log_decision.await_args_list
    ]
    assert any("audio" in (a or "") for a in actions), (
        f"Missing audio_purge audit row. Actions logged: {actions}"
    )
    assert any("transcript" in (a or "") for a in actions), (
        f"Missing transcript_purge audit row. Actions logged: {actions}"
    )
    assert any("wsi" in (a or "") for a in actions), (
        f"Missing wsi_purge audit row. Actions logged: {actions}"
    )


@pytest.mark.asyncio
async def test_audit_includes_records_purged_count():
    """P1 #2: reasoning[] must contain records_purged=<count> for forensic queries."""
    from app.jobs.tasks import voice_retention

    fake_db = _build_fake_db(rowcount=7)

    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock(return_value=MagicMock())
    mock_audit_cls = MagicMock(return_value=mock_audit)

    with patch(
        "app.core.database.AsyncSessionLocal", return_value=_make_session_ctx(fake_db)
    ), patch(
        "app.shared.compliance.audit_service.AuditService", mock_audit_cls
    ):
        await voice_retention._run_voice_retention(dry_run=False)

    # At least one row should have records_purged in reasoning
    found_count = False
    for call in mock_audit.log_decision.await_args_list:
        reasoning = call.kwargs.get("reasoning") or []
        if any("records_purged=" in r for r in reasoning):
            found_count = True
            break
    assert found_count, (
        "Expected at least one audit row with records_purged=<n> in reasoning."
    )


@pytest.mark.asyncio
async def test_audit_includes_lgpd_canonical_criteria():
    """P1 #2: criteria_used must include LGPD canonical anchor."""
    from app.jobs.tasks import voice_retention

    fake_db = _build_fake_db(rowcount=1)

    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock(return_value=MagicMock())
    mock_audit_cls = MagicMock(return_value=mock_audit)

    with patch(
        "app.core.database.AsyncSessionLocal", return_value=_make_session_ctx(fake_db)
    ), patch(
        "app.shared.compliance.audit_service.AuditService", mock_audit_cls
    ):
        await voice_retention._run_voice_retention(dry_run=False)

    assert mock_audit.log_decision.await_count >= 1
    # All audit rows should reference LGPD Art. 16 (minimization)
    for call in mock_audit.log_decision.await_args_list:
        criteria = call.kwargs.get("criteria_used") or []
        assert any("lgpd" in c.lower() for c in criteria), (
            f"Audit row missing LGPD criterion. Got: {criteria}"
        )


@pytest.mark.asyncio
async def test_audit_failure_does_not_block_purge():
    """P1 #2: best-effort — AuditService failure must NOT abort retention task."""
    from app.jobs.tasks import voice_retention

    fake_db = _build_fake_db(rowcount=4)

    mock_audit = MagicMock()
    # log_decision raises on every call
    mock_audit.log_decision = AsyncMock(side_effect=RuntimeError("audit DB down"))
    mock_audit_cls = MagicMock(return_value=mock_audit)

    with patch(
        "app.core.database.AsyncSessionLocal", return_value=_make_session_ctx(fake_db)
    ), patch(
        "app.shared.compliance.audit_service.AuditService", mock_audit_cls
    ):
        # Must NOT raise
        stats = await voice_retention._run_voice_retention(dry_run=False)

    # Purge still ran — commits happened
    assert fake_db.commit.await_count >= 3, (
        "Purge phases must complete even if audit emission fails."
    )
    assert "audio_purged" in stats
    assert "transcript_purged" in stats
    assert "wsi_score_purged" in stats


@pytest.mark.asyncio
async def test_dry_run_skips_audit_emission():
    """P1 #2: dry_run mode does not emit audit rows (no actual mutation)."""
    from app.jobs.tasks import voice_retention

    fake_db = _build_fake_db(rowcount=0, scalar=5)

    mock_audit = MagicMock()
    mock_audit.log_decision = AsyncMock(return_value=MagicMock())
    mock_audit_cls = MagicMock(return_value=mock_audit)

    with patch(
        "app.core.database.AsyncSessionLocal", return_value=_make_session_ctx(fake_db)
    ), patch(
        "app.shared.compliance.audit_service.AuditService", mock_audit_cls
    ):
        await voice_retention._run_voice_retention(dry_run=True)

    # No audit emission in dry-run — would create misleading audit trail
    assert mock_audit.log_decision.await_count == 0, (
        f"dry_run=True must NOT emit audit rows. "
        f"Got {mock_audit.log_decision.await_count} calls."
    )
