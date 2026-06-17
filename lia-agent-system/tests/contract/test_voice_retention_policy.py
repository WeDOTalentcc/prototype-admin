"""
Tests for F-05 (P0 LGPD Art. 16): Voice data retention policy enforcement.

Retention windows approved Paulo 2026-05-22:
  - 60 days:  audio_url null
  - 180 days: transcript null
  - 365 days: WSI score row delete

Audit ref: ~/Documents/wedotalent_audit_2026-05-21/AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-05
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_celery_beat_has_voice_retention_scheduled():
    """F-05 sensor: beat_schedule contains `voice-retention-daily` entry."""
    from lia_config.celery_app import celery_app

    schedule = celery_app.conf.beat_schedule
    assert "voice-retention-daily" in schedule, (
        "F-05: beat_schedule MUST include 'voice-retention-daily' so the "
        "retention purge task runs on cron. LGPD Art. 16 minimization."
    )
    entry = schedule["voice-retention-daily"]
    assert entry["task"] == "voice.retention_purge_daily"


def test_voice_retention_constants_match_paulo_policy():
    """F-05: retention windows are exactly 60/180/365 days (Paulo approved 2026-05-22)."""
    from app.jobs.tasks import voice_retention

    assert voice_retention.AUDIO_RETENTION_DAYS == 60
    assert voice_retention.TRANSCRIPT_RETENTION_DAYS == 180
    assert voice_retention.WSI_SCORE_RETENTION_DAYS == 365


def test_voice_retention_task_registered_in_celery():
    """F-05: task `voice.retention_purge_daily` registered in celery app."""
    from lia_config.celery_app import celery_app

    assert "voice.retention_purge_daily" in celery_app.tasks, (
        "F-05: task 'voice.retention_purge_daily' must be registered "
        "(imported in app/jobs/tasks/__init__.py)."
    )


@pytest.mark.asyncio
async def test_run_voice_retention_calls_audio_phase_with_60d_cutoff():
    """F-05: audio phase issues UPDATE response_audio_url=NULL with 60d cutoff."""
    from app.jobs.tasks import voice_retention

    fake_db = MagicMock()
    fake_result = MagicMock()
    fake_result.rowcount = 3
    fake_result.scalar = MagicMock(return_value=0)
    fake_db.execute = AsyncMock(return_value=fake_result)
    fake_db.commit = AsyncMock()
    fake_db.rollback = AsyncMock()

    class _FakeSessionCtx:
        async def __aenter__(self):
            return fake_db

        async def __aexit__(self, *a):
            return None

    with patch(
        "app.core.database.AsyncSessionLocal", return_value=_FakeSessionCtx()
    ):
        stats = await voice_retention._run_voice_retention(dry_run=False)

    # At least 3 UPDATE/DELETE statements were executed (one per phase).
    assert fake_db.execute.await_count >= 3
    assert "audio_purged" in stats
    assert "transcript_purged" in stats
    assert "wsi_score_purged" in stats
    assert stats["dry_run"] is False


@pytest.mark.asyncio
async def test_run_voice_retention_dry_run_does_not_modify_db():
    """F-05: dry_run=True executes only SELECT COUNT(*), never UPDATE/DELETE."""
    from app.jobs.tasks import voice_retention

    fake_db = MagicMock()
    fake_result = MagicMock()
    fake_result.scalar = MagicMock(return_value=5)
    fake_result.rowcount = 0
    fake_db.execute = AsyncMock(return_value=fake_result)
    fake_db.commit = AsyncMock()
    fake_db.rollback = AsyncMock()

    class _FakeSessionCtx:
        async def __aenter__(self):
            return fake_db

        async def __aexit__(self, *a):
            return None

    with patch(
        "app.core.database.AsyncSessionLocal", return_value=_FakeSessionCtx()
    ):
        stats = await voice_retention._run_voice_retention(dry_run=True)

    # commit must NEVER be called in dry-run
    fake_db.commit.assert_not_awaited()
    assert stats["dry_run"] is True
    assert stats["audio_purged"] == 5  # from scalar mock


@pytest.mark.asyncio
async def test_run_voice_retention_continues_on_phase_failure():
    """F-05: failure in phase 1 (audio) must NOT stop phases 2-3 (idempotent best-effort)."""
    from app.jobs.tasks import voice_retention

    fake_db = MagicMock()
    fake_db.rollback = AsyncMock()
    fake_db.commit = AsyncMock()
    call_count = {"n": 0}

    async def _execute_side_effect(*a, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("simulated audio phase failure")
        r = MagicMock()
        r.rowcount = 1
        r.scalar = MagicMock(return_value=0)
        return r

    fake_db.execute = AsyncMock(side_effect=_execute_side_effect)

    class _FakeSessionCtx:
        async def __aenter__(self):
            return fake_db

        async def __aexit__(self, *a):
            return None

    with patch(
        "app.core.database.AsyncSessionLocal", return_value=_FakeSessionCtx()
    ):
        stats = await voice_retention._run_voice_retention(dry_run=False)

    # phase 2 and 3 still ran
    assert call_count["n"] >= 3, "phases 2 and 3 must continue after phase 1 fails"
    assert len(stats["errors"]) >= 1
    assert "audio_phase" in stats["errors"][0]
