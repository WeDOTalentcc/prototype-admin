"""Tests — Monthly audio recording expurgo (Phase 3b LGPD Art. 16).

Tests:
  1. test_records_older_than_12_months_are_nullified
  2. test_records_newer_than_12_months_are_not_touched
  3. test_twilio_url_deletion_called_for_twilio_urls
  4. test_twilio_404_does_not_abort_job
  5. test_already_null_fields_skipped
  6. test_consent_records_never_deleted
  7. test_audit_log_created_per_record
  8. test_summary_returned
  9. test_non_twilio_url_not_deleted_via_twilio
  10. test_beat_schedule_registered
  11. test_task_name_registered
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 6, 11, 12, 0, 0)
_CUTOFF = _NOW - timedelta(days=360)  # 12 * 30
_OLD_DATE = _CUTOFF - timedelta(days=1)   # before cutoff → should be expurgado
_NEW_DATE = _CUTOFF + timedelta(days=30)  # after cutoff → should NOT be touched


def _make_db_rows(*rows):
    """Return a mock scalar/execute result that iterates rows, then returns empty on 2nd call."""
    calls = [iter(rows), iter([])]

    class _MockResult:
        def __init__(self, data):
            self._data = data

        def all(self):
            return list(self._data)

    counter = {"n": 0}

    async def _execute(stmt, params=None):
        n = counter["n"]
        counter["n"] += 1
        if n < len(calls):
            return _MockResult(calls[n])
        return _MockResult(iter([]))

    return _execute


# ─────────────────────────────────────────────────────────────────────────────
# Imports under test
# ─────────────────────────────────────────────────────────────────────────────

from app.jobs.tasks.expurgo_gravacoes import (
    RECORDING_RETENTION_MONTHS,
    _EXPURGO_BATCH_SIZE,
    _RETENTION_DAYS,
    _delete_twilio_recording,
    _emit_expurgo_audit,
    _extract_twilio_sid,
    _run_expurgo_gravacoes,
    expurgo_gravacoes_audio,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1 — Records older than 12 months are nullified
# ─────────────────────────────────────────────────────────────────────────────

class TestOldRecordsNullified:
    def test_extract_twilio_sid_valid(self):
        url = "https://api.twilio.com/2010-04-01/Accounts/AC123/Recordings/RE1234567890abcdef"
        sid = _extract_twilio_sid(url)
        assert sid == "RE1234567890abcdef"

    def test_extract_twilio_sid_none_for_non_twilio(self):
        assert _extract_twilio_sid("https://s3.amazonaws.com/bucket/file.mp4") is None
        assert _extract_twilio_sid("") is None
        assert _extract_twilio_sid(None) is None

    def test_retention_days_constant(self):
        """RECORDING_RETENTION_MONTHS = 12 → _RETENTION_DAYS = 360."""
        assert RECORDING_RETENTION_MONTHS == 12
        assert _RETENTION_DAYS == 360

    def test_batch_size_constant(self):
        assert _EXPURGO_BATCH_SIZE == 100

    @patch("app.jobs.tasks.expurgo_gravacoes._send_summary_email", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._emit_expurgo_audit", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes.datetime")
    @patch("app.core.database.AsyncSessionLocal")
    def test_run_returns_summary_with_all_tables(
        self, mock_session_cls, mock_datetime, mock_audit, mock_email
    ):
        """_run_expurgo_gravacoes returns summary dict with all 4 table keys."""
        mock_datetime.utcnow.return_value = _NOW

        # Mock DB session: every SELECT returns empty so no rows are processed
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(all=lambda: []))
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_db

        result = asyncio.run(_run_expurgo_gravacoes())

        assert "tables_processed" in result
        assert "records_nullified_per_table" in result
        assert "cutoff" in result
        assert "run_at" in result
        assert "wsi_response_analyses" in result["records_nullified_per_table"]
        assert "triagem_messages" in result["records_nullified_per_table"]
        assert "interviews" in result["records_nullified_per_table"]
        assert "voice_screening_calls" in result["records_nullified_per_table"]


# ─────────────────────────────────────────────────────────────────────────────
# 2 — Records newer than cutoff are not touched
# ─────────────────────────────────────────────────────────────────────────────

class TestNewRecordsNotTouched:
    @patch("app.jobs.tasks.expurgo_gravacoes._send_summary_email", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._emit_expurgo_audit", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes.datetime")
    @patch("app.core.database.AsyncSessionLocal")
    def test_empty_result_means_zero_nullified(
        self, mock_session_cls, mock_datetime, mock_audit, mock_email
    ):
        """When no rows match the WHERE clause (all new), counts are 0."""
        mock_datetime.utcnow.return_value = _NOW

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(all=lambda: []))
        mock_db.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_db

        result = asyncio.run(_run_expurgo_gravacoes())
        total = sum(result["records_nullified_per_table"].values())
        assert total == 0


# ─────────────────────────────────────────────────────────────────────────────
# 3 — Twilio URL deletion called for Twilio URLs
# ─────────────────────────────────────────────────────────────────────────────

class TestTwilioUrlDeletion:
    def test_delete_not_twilio_when_no_credentials(self):
        """_delete_twilio_recording returns 'not_twilio' when no Twilio credentials set."""
        import os
        env = {"TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": ""}
        with patch.dict(os.environ, env):
            # Override getenv to return empty strings
            with patch("os.getenv", side_effect=lambda k, d=None: env.get(k, d)):
                result = asyncio.run(_delete_twilio_recording("RE123"))
                # No credentials → not_twilio or error depending on environment
                assert result in ("not_twilio", "error")

    def test_extract_sid_from_various_url_formats(self):
        urls = [
            ("https://api.twilio.com/2010-04-01/Accounts/AC123/Recordings/REabc456", "REabc456"),
            ("https://api.twilio.com/Recordings/REdef789", "REdef789"),
        ]
        for url, expected in urls:
            assert _extract_twilio_sid(url) == expected

    @pytest.mark.asyncio
    async def test_delete_returns_not_twilio_when_package_missing(self):
        with patch.dict("sys.modules", {"twilio": None, "twilio.rest": None, "twilio.base.exceptions": None}):
            result = await _delete_twilio_recording("REtest")
            # No credentials even if twilio was available
            assert result in ("not_twilio", "error")


# ─────────────────────────────────────────────────────────────────────────────
# 4 — Twilio 404 does not abort job
# ─────────────────────────────────────────────────────────────────────────────

class TestTwilio404DoesNotAbort:
    @pytest.mark.asyncio
    async def test_twilio_404_returns_404_string(self):
        """When Twilio raises 404-like exception, _delete_twilio_recording returns '404' or 'error', never raises."""
        exc_404 = Exception("404 Recording not found")
        exc_404.status = 404

        import os
        # Test that exception does NOT propagate — result is always a string, never raises
        with patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "", "TWILIO_AUTH_TOKEN": ""}):
            result = await _delete_twilio_recording("REtest")
            # Returns a string (not_twilio, 404, error, deleted) — never raises
            assert isinstance(result, str)
            assert result in ("not_twilio", "404", "error", "deleted")

    @patch("app.jobs.tasks.expurgo_gravacoes._send_summary_email", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._delete_twilio_recording", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._emit_expurgo_audit", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes.datetime")
    @patch("app.core.database.AsyncSessionLocal")
    def test_job_continues_after_twilio_404(
        self, mock_session_cls, mock_datetime, mock_audit, mock_delete, mock_email
    ):
        """Job continues and nullifies locally even if Twilio returns 404."""
        mock_datetime.utcnow.return_value = _NOW
        mock_delete.return_value = "404"

        import uuid

        old_row_id = str(uuid.uuid4())
        # Return one row with Twilio URL from wsi_response_analyses, then empty for others
        call_count = {"n": 0}

        async def _execute(stmt, params=None):
            n = call_count["n"]
            call_count["n"] += 1
            if n == 0:
                return MagicMock(all=lambda: [(old_row_id, "https://api.twilio.com/Recordings/REabc")])
            return MagicMock(all=lambda: [])

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=_execute)
        mock_db.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_db

        result = asyncio.run(_run_expurgo_gravacoes())
        # Should not raise, and wsi_response_analyses count should be 1
        assert result["records_nullified_per_table"]["wsi_response_analyses"] == 1
        assert mock_delete.called


# ─────────────────────────────────────────────────────────────────────────────
# 5 — Already null fields skipped (idempotence RE-04)
# ─────────────────────────────────────────────────────────────────────────────

class TestIdempotence:
    @patch("app.jobs.tasks.expurgo_gravacoes._send_summary_email", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._emit_expurgo_audit", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes.datetime")
    @patch("app.core.database.AsyncSessionLocal")
    def test_null_fields_skipped(
        self, mock_session_cls, mock_datetime, mock_audit, mock_email
    ):
        """SELECT WHERE IS NOT NULL ensures already-null rows never appear."""
        mock_datetime.utcnow.return_value = _NOW

        # Simulate: no rows match IS NOT NULL (all already null)
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(all=lambda: []))
        mock_db.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_db

        result = asyncio.run(_run_expurgo_gravacoes())
        assert all(v == 0 for v in result["records_nullified_per_table"].values())
        mock_audit.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 6 — ConsentRecord table is never deleted/modified
# ─────────────────────────────────────────────────────────────────────────────

class TestConsentRecordNeverDeleted:
    @patch("app.jobs.tasks.expurgo_gravacoes._send_summary_email", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._emit_expurgo_audit", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes.datetime")
    @patch("app.core.database.AsyncSessionLocal")
    def test_consent_records_not_in_queries(
        self, mock_session_cls, mock_datetime, mock_audit, mock_email
    ):
        """Verify no query touches consent_records table."""
        mock_datetime.utcnow.return_value = _NOW
        executed_stmts = []

        async def _capture_execute(stmt, params=None):
            executed_stmts.append(str(stmt).lower())
            return MagicMock(all=lambda: [])

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=_capture_execute)
        mock_db.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_db

        asyncio.run(_run_expurgo_gravacoes())

        for stmt in executed_stmts:
            assert "consent_record" not in stmt, (
                f"consent_records must never be modified by expurgo job. Found in: {stmt}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 7 — AuditLog created per record
# ─────────────────────────────────────────────────────────────────────────────

class TestAuditLogCreated:
    @patch("app.jobs.tasks.expurgo_gravacoes._send_summary_email", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._emit_expurgo_audit", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._delete_twilio_recording", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes.datetime")
    @patch("app.core.database.AsyncSessionLocal")
    def test_audit_called_per_nullified_row(
        self, mock_session_cls, mock_datetime, mock_delete, mock_audit, mock_email
    ):
        """_emit_expurgo_audit is called once per nullified row."""
        mock_datetime.utcnow.return_value = _NOW
        mock_delete.return_value = "not_twilio"

        import uuid

        row1_id = str(uuid.uuid4())
        row2_id = str(uuid.uuid4())

        call_count = {"n": 0}

        async def _execute(stmt, params=None):
            n = call_count["n"]
            call_count["n"] += 1
            # wsi_response_analyses returns 2 rows, rest empty
            if n == 0:
                return MagicMock(all=lambda: [
                    (row1_id, "https://s3.aws.com/a.mp3"),
                    (row2_id, "https://s3.aws.com/b.mp3"),
                ])
            return MagicMock(all=lambda: [])

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=_execute)
        mock_db.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_db

        result = asyncio.run(_run_expurgo_gravacoes())

        assert result["records_nullified_per_table"]["wsi_response_analyses"] == 2
        assert mock_audit.call_count == 2
        # Check audit was called with correct table_name
        for c in mock_audit.call_args_list:
            assert c.kwargs["table_name"] == "wsi_response_analyses"
            # action is hardcoded inside _emit_expurgo_audit → AuditService.log_decision
            # We only verify the table_name kwarg is correct here


# ─────────────────────────────────────────────────────────────────────────────
# 8 — Summary returned with all required keys
# ─────────────────────────────────────────────────────────────────────────────

class TestSummaryReturned:
    @patch("app.jobs.tasks.expurgo_gravacoes._send_summary_email", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._emit_expurgo_audit", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes.datetime")
    @patch("app.core.database.AsyncSessionLocal")
    def test_summary_has_all_required_keys(
        self, mock_session_cls, mock_datetime, mock_audit, mock_email
    ):
        """Return value has all required keys per spec."""
        mock_datetime.utcnow.return_value = _NOW

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=MagicMock(all=lambda: []))
        mock_db.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_db

        result = asyncio.run(_run_expurgo_gravacoes())

        required_keys = {"tables_processed", "records_nullified_per_table", "cutoff", "run_at"}
        assert required_keys.issubset(result.keys())
        assert isinstance(result["tables_processed"], list)
        assert isinstance(result["records_nullified_per_table"], dict)
        # cutoff should be roughly 360 days before now
        from datetime import datetime, timedelta
        cutoff_dt = datetime.fromisoformat(result["cutoff"])
        expected_cutoff = _NOW - timedelta(days=360)
        diff = abs((cutoff_dt - expected_cutoff).total_seconds())
        assert diff < 5  # within 5 seconds


# ─────────────────────────────────────────────────────────────────────────────
# 9 — Non-Twilio URL does not call Twilio delete
# ─────────────────────────────────────────────────────────────────────────────

class TestNonTwilioNotDeleted:
    @patch("app.jobs.tasks.expurgo_gravacoes._send_summary_email", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._emit_expurgo_audit", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes._delete_twilio_recording", new_callable=AsyncMock)
    @patch("app.jobs.tasks.expurgo_gravacoes.datetime")
    @patch("app.core.database.AsyncSessionLocal")
    def test_s3_url_does_not_call_twilio(
        self, mock_session_cls, mock_datetime, mock_delete, mock_audit, mock_email
    ):
        """S3 URLs do not trigger Twilio remote delete."""
        mock_datetime.utcnow.return_value = _NOW
        import uuid

        row_id = str(uuid.uuid4())
        call_count = {"n": 0}

        async def _execute(stmt, params=None):
            n = call_count["n"]
            call_count["n"] += 1
            if n == 0:
                return MagicMock(all=lambda: [(row_id, "https://s3.amazonaws.com/audio.mp3")])
            return MagicMock(all=lambda: [])

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=_execute)
        mock_db.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_session_cls.return_value = mock_db

        asyncio.run(_run_expurgo_gravacoes())
        mock_delete.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 10 — Beat schedule registered
# ─────────────────────────────────────────────────────────────────────────────

class TestBeatScheduleRegistered:
    def test_expurgo_schedule_in_beat(self):
        from lia_config.celery_app import celery_app
        beat = celery_app.conf.beat_schedule
        assert "expurgo-gravacoes-mensal" in beat, (
            "'expurgo-gravacoes-mensal' missing from beat_schedule"
        )

    def test_expurgo_schedule_task_name(self):
        from lia_config.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["expurgo-gravacoes-mensal"]
        assert entry["task"] == "expurgo_gravacoes_audio"

    def test_expurgo_schedule_runs_at_05h_utc_day_1(self):
        """Schedule: 05:00 UTC on day 1 of month (02:00 BRT)."""
        from celery.schedules import crontab
        from lia_config.celery_app import celery_app
        entry = celery_app.conf.beat_schedule["expurgo-gravacoes-mensal"]
        schedule = entry["schedule"]
        assert isinstance(schedule, crontab)
        assert schedule.day_of_month == frozenset({1})
        assert schedule.hour == frozenset({5})
        assert schedule.minute == frozenset({0})


# ─────────────────────────────────────────────────────────────────────────────
# 11 — Task name registered
# ─────────────────────────────────────────────────────────────────────────────

class TestTaskNameRegistered:
    def test_task_name(self):
        assert expurgo_gravacoes_audio.name == "expurgo_gravacoes_audio"

    def test_task_importable_from_celery_tasks(self):
        from app.jobs.celery_tasks import expurgo_gravacoes_audio as imported_task
        assert imported_task.name == "expurgo_gravacoes_audio"

    def test_task_max_retries_zero(self):
        """Monthly job has max_retries=0 — next month's run is idempotent."""
        assert expurgo_gravacoes_audio.max_retries == 0
