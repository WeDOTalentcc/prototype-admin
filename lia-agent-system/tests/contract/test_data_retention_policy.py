"""
Contract tests for data retention policy — GAP-10-001 (LOTE-002).

These tests pin the retention policy constants and ensure the cleanup
service has entries for all required retention categories.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from app.domains.lgpd.services.lgpd_cleanup_service import (
    RETENTION_DAYS,
    schedule_deletion_for_candidate,
)


class TestRetentionDaysPolicy:
    """Pin the retention constants so accidental changes surface as test failures."""

    def test_rejected_candidates_retained_365_days(self):
        assert RETENTION_DAYS["rejected"] == 365, (
            "LGPD + spec LOTE-002: rejected candidate PII must be retained for 365 days. "
            "Do not reduce this value without legal review."
        )

    def test_withdrawn_retained_90_days(self):
        assert RETENTION_DAYS["withdrawn"] == 90

    def test_draft_candidate_retained_90_days(self):
        assert "draft_candidate" in RETENTION_DAYS, (
            "GAP-10-001: draft_candidate retention key must exist in RETENTION_DAYS"
        )
        assert RETENTION_DAYS["draft_candidate"] == 90

    def test_expired_job_retained_730_days(self):
        assert "expired_job" in RETENTION_DAYS, (
            "GAP-10-001: expired_job retention key must exist in RETENTION_DAYS"
        )
        assert RETENTION_DAYS["expired_job"] == 730

    def test_ai_logs_retained_365_days(self):
        assert RETENTION_DAYS["ai_logs"] == 365

    def test_screening_logs_retained_365_days(self):
        assert RETENTION_DAYS["screening_logs"] == 365

    def test_chat_messages_retained_90_days(self):
        assert RETENTION_DAYS["chat_messages"] == 90


class TestRunCleanupSummaryKeys:
    """Ensure run_cleanup() returns summary keys for new retention categories."""

    @pytest.mark.asyncio
    async def test_summary_includes_draft_candidates_deleted(self):
        from app.domains.lgpd.services.lgpd_cleanup_service import run_cleanup

        with patch(
            "app.domains.lgpd.services.lgpd_cleanup_service.AsyncSessionLocal"
        ) as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_session_cls.return_value = mock_session

            summary = await run_cleanup(dry_run=True)

        assert "draft_candidates_deleted" in summary, (
            "run_cleanup() must include 'draft_candidates_deleted' in the summary dict"
        )

    @pytest.mark.asyncio
    async def test_summary_includes_expired_jobs_deleted(self):
        from app.domains.lgpd.services.lgpd_cleanup_service import run_cleanup

        with patch(
            "app.domains.lgpd.services.lgpd_cleanup_service.AsyncSessionLocal"
        ) as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)

            mock_result = MagicMock()
            mock_result.all.return_value = []
            mock_session.execute = AsyncMock(return_value=mock_result)

            mock_session_cls.return_value = mock_session

            summary = await run_cleanup(dry_run=True)

        assert "expired_jobs_deleted" in summary, (
            "run_cleanup() must include 'expired_jobs_deleted' in the summary dict"
        )
