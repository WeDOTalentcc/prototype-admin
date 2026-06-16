"""Contract sensor — Sprint D+1 partial briefing_frequency canonical migration.

ADR-WT-2025 §Sprint D+1 partial — registered 2026-05-22
=======================================================

Covers 6 invariants for the briefing_frequency canonical migration
(AlertConfig -> HiringPolicy.communication_rules):

1. test_migration_174_backfills_briefing_frequency_to_hiringpolicy
   Migration 174_briefing_frequency_canonical exists, has correct down_revision
   (chains after 173_rls_policy_batch_1), and the upgrade() SQL backfills
   AlertConfig.briefing_frequency into HiringPolicy.communication_rules JSONB.

2. test_briefing_dispatch_reads_from_hiringpolicy_not_alertconfig
   When HiringPolicy.communication_rules.briefing_frequency is present,
   _resolve_briefing_frequency returns it WITHOUT touching AlertConfig.

3. test_briefing_dispatch_logs_warning_when_fallback_alertconfig
   When HiringPolicy missing/empty but AlertConfig has briefing_frequency,
   _resolve_briefing_frequency falls back AND emits logger.warning + counter.

4. test_canary_metric_briefing_legacy_read_emitted
   _emit_legacy_alertconfig_read_counter increments
   briefing_dispatch_legacy_alertconfig_read_total Prometheus counter
   (fail-open when prometheus_client absent).

5. test_canary_metric_alerts_config_endpoint_calls_emitted
   _emit_legacy_alerts_config_endpoint_counter increments
   legacy_alerts_config_endpoint_calls_total Prometheus counter
   (fail-open when prometheus_client absent).

6. test_briefing_default_weekly_when_neither_source
   When BOTH HiringPolicy and AlertConfig lack briefing_frequency,
   _resolve_briefing_frequency returns (None, 'default') so caller
   can apply DEFAULT_BRIEFING_FREQUENCY ('weekly').

Pure-unit: mocked AsyncSession, no real DB or Celery worker.
"""
from __future__ import annotations

import asyncio
import importlib.util
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


# -----------------------------------------------------------------------------
# Test 1 — Migration file exists + structure
# -----------------------------------------------------------------------------
def test_migration_174_backfills_briefing_frequency_to_hiringpolicy():
    """Migration file 174_briefing_frequency_canonical exists with correct
    chain (down_revision = 173_rls_policy_batch_1) and SQL backfills
    HiringPolicy.communication_rules.briefing_frequency."""
    migration_path = (
        REPO_ROOT
        / "alembic"
        / "versions"
        / "174_briefing_frequency_canonical.py"
    )
    assert migration_path.exists(), (
        f"Migration file missing: {migration_path}. "
        f"Sprint D+1 partial requires this migration to backfill "
        f"AlertConfig.briefing_frequency -> HiringPolicy.communication_rules."
    )
    src = migration_path.read_text(encoding="utf-8")

    # Revision chain
    assert 'revision = "174_briefing_frequency_canonical"' in src
    assert 'down_revision = "173_rls_policy_batch_1"' in src

    # Idempotent backfill: JSONB key check + canonical frequency enum filter
    assert "company_hiring_policies" in src
    assert "communication_rules" in src
    assert "briefing_frequency" in src
    assert "jsonb_set" in src
    # WHERE clause that skips already-backfilled rows
    assert re.search(
        r"communication_rules\s*->>?\s*'briefing_frequency'\s*\)\s*IS\s+NULL",
        src,
    ), "Migration should skip already-backfilled rows for idempotency"
    # Filter to valid canonical frequencies
    for freq in ("daily", "weekly", "twice_daily", "monthly"):
        assert freq in src, f"Migration should filter for canonical freq {freq!r}"
    # Filter out NULL company_id (TENANT-EXEMPT global configs)
    assert "company_id IS NOT NULL" in src.upper().replace("\n", " ").replace(
        "  ", " "
    ) or "company_id is not null" in src.lower()


# -----------------------------------------------------------------------------
# Test 2 — Dispatch prefers HiringPolicy over AlertConfig
# -----------------------------------------------------------------------------
def test_briefing_dispatch_reads_from_hiringpolicy_not_alertconfig():
    """When HiringPolicy.communication_rules.briefing_frequency is present,
    _resolve_briefing_frequency returns it and does NOT touch AlertConfig."""
    from app.jobs.tasks.briefing_dispatch import _resolve_briefing_frequency

    db = MagicMock()
    db.execute = AsyncMock()  # must NOT be called

    # Mock HiringPolicy with canonical briefing_frequency = 'weekly'
    policy = MagicMock()
    policy.communication_rules = {"briefing_frequency": "weekly"}

    fake_repo = MagicMock()
    fake_repo.get_by_company = AsyncMock(return_value=policy)

    with patch(
        "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository",
        return_value=fake_repo,
    ):
        freq, source = asyncio.run(
            _resolve_briefing_frequency(db, "company-abc")
        )

    assert freq == "weekly"
    assert source == "hiring_policy"
    # AlertConfig fallback should NOT have been queried
    db.execute.assert_not_called()


# -----------------------------------------------------------------------------
# Test 3 — Fallback to AlertConfig + warning log
# -----------------------------------------------------------------------------
def test_briefing_dispatch_logs_warning_when_fallback_alertconfig(caplog):
    """When HiringPolicy missing briefing_frequency, fall back to AlertConfig
    AND emit logger.warning + canary counter increment."""
    import logging

    from app.jobs.tasks.briefing_dispatch import _resolve_briefing_frequency

    # HiringPolicy exists but has no briefing_frequency in communication_rules
    policy = MagicMock()
    policy.communication_rules = {"lia_tone": "professional"}  # no briefing_frequency

    fake_repo = MagicMock()
    fake_repo.get_by_company = AsyncMock(return_value=policy)

    # AlertConfig fallback returns 'daily'
    db = MagicMock()

    async def fake_execute(stmt):
        result = MagicMock()
        scalars = MagicMock()
        scalars.all = MagicMock(return_value=["daily"])
        result.scalars = MagicMock(return_value=scalars)
        return result

    db.execute = AsyncMock(side_effect=fake_execute)

    with patch(
        "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository",
        return_value=fake_repo,
    ), patch(
        "app.jobs.tasks.briefing_dispatch._emit_legacy_alertconfig_read_counter"
    ) as mock_counter:
        with caplog.at_level(logging.WARNING):
            freq, source = asyncio.run(
                _resolve_briefing_frequency(db, "company-xyz")
            )

    assert freq == "daily"
    assert source == "alert_config_legacy"
    # Counter MUST be emitted
    mock_counter.assert_called_once_with("company-xyz")
    # Warning log must mention canonical migration path
    fallback_warnings = [
        r for r in caplog.records
        if r.levelno == logging.WARNING and "fallback" in r.getMessage().lower()
    ]
    assert fallback_warnings, (
        "Expected logger.warning with 'fallback' when HiringPolicy missing "
        "briefing_frequency (REGRA 4 — no silent fallback)"
    )


# -----------------------------------------------------------------------------
# Test 4 — Canary counter: briefing_dispatch_legacy_alertconfig_read_total
# -----------------------------------------------------------------------------
def test_canary_metric_briefing_legacy_read_emitted():
    """_emit_legacy_alertconfig_read_counter increments the canary counter.

    Fail-open: tolerates absence of prometheus_client.
    """
    from app.jobs.tasks.briefing_dispatch import (
        _emit_legacy_alertconfig_read_counter,
    )

    # Import the counter (may be None if prometheus_client unavailable)
    from app.shared.observability import canary_metrics

    counter = canary_metrics.briefing_dispatch_legacy_alertconfig_read_total

    if counter is None:
        # Fail-open mode: just ensure no exception
        _emit_legacy_alertconfig_read_counter("company-abc")
        return

    # Snapshot before
    label_key = ("company_id_hash",)
    sample_before = None
    for sample in counter.collect()[0].samples:
        sample_before = sample.value
        break

    _emit_legacy_alertconfig_read_counter("company-abc")
    _emit_legacy_alertconfig_read_counter("company-abc")

    # Snapshot after — at least one sample should have value > 0
    samples_after = [s for s in counter.collect()[0].samples]
    assert any(s.value > 0 for s in samples_after), (
        "briefing_dispatch_legacy_alertconfig_read_total counter must increment"
    )


# -----------------------------------------------------------------------------
# Test 5 — Canary counter: legacy_alerts_config_endpoint_calls_total
# -----------------------------------------------------------------------------
def test_canary_metric_alerts_config_endpoint_calls_emitted():
    """Endpoint canary counter increments on legacy /alerts/config calls.

    Fail-open: tolerates absence of prometheus_client.
    """
    # Import emitter from alerts.py
    from app.api.v1.alerts import _emit_legacy_alerts_config_endpoint_counter
    from app.shared.observability import canary_metrics

    counter = canary_metrics.legacy_alerts_config_endpoint_calls_total

    if counter is None:
        # Fail-open mode: just ensure no exception
        _emit_legacy_alerts_config_endpoint_counter(
            method="GET", company_id="company-foo"
        )
        return

    _emit_legacy_alerts_config_endpoint_counter(
        method="GET", company_id="company-foo"
    )
    _emit_legacy_alerts_config_endpoint_counter(
        method="PUT", company_id="company-foo"
    )

    samples_after = list(counter.collect()[0].samples)
    assert any(s.value > 0 for s in samples_after), (
        "legacy_alerts_config_endpoint_calls_total counter must increment"
    )


# -----------------------------------------------------------------------------
# Test 6 — Default when no source available
# -----------------------------------------------------------------------------
def test_briefing_default_weekly_when_neither_source():
    """When BOTH HiringPolicy AND AlertConfig lack briefing_frequency,
    _resolve_briefing_frequency returns (None, 'default') so caller can
    apply canonical DEFAULT_BRIEFING_FREQUENCY = 'weekly'."""
    from app.jobs.tasks.briefing_dispatch import (
        DEFAULT_BRIEFING_FREQUENCY,
        _resolve_briefing_frequency,
    )

    # No HiringPolicy row
    fake_repo = MagicMock()
    fake_repo.get_by_company = AsyncMock(return_value=None)

    # AlertConfig fallback returns nothing
    db = MagicMock()

    async def fake_execute(stmt):
        result = MagicMock()
        scalars = MagicMock()
        scalars.all = MagicMock(return_value=[])
        result.scalars = MagicMock(return_value=scalars)
        return result

    db.execute = AsyncMock(side_effect=fake_execute)

    with patch(
        "app.domains.hiring_policy.repositories.hiring_policy_repository.HiringPolicyRepository",
        return_value=fake_repo,
    ):
        freq, source = asyncio.run(
            _resolve_briefing_frequency(db, "company-empty")
        )

    assert freq is None
    assert source == "default"
    # Canonical default is 'weekly' (ADR-WT-2025 + UI default)
    assert DEFAULT_BRIEFING_FREQUENCY == "weekly", (
        "DEFAULT_BRIEFING_FREQUENCY must be 'weekly' per ADR-WT-2025 "
        "(matches plataforma-lia AlertPreferencesPanel UI default)"
    )
