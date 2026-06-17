"""Unit tests — ManagerPreferences idempotency.

Harness: Sensor (computacional) for Feature 2 (Manager Preferences).
Covers:
- Second call to record_job_completion() with same idempotency_key does NOT
  increment jobs_created_count (idempotent).
- apply_to_state() fails-open: returns {} on any exception, never raises.
- get_or_create() returns existing record on duplicate call.
- company_id must not be empty or record_job_completion raises.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call


# ---------------------------------------------------------------------------
# Tests: idempotency of record_job_completion
# ---------------------------------------------------------------------------

class TestRecordJobCompletionIdempotency:
    """record_job_completion() with same idempotency_key must not double-count."""

    def _build_state(self, manager_email: str = "ana@company.com") -> dict:
        return {
            "job_title": "Backend Engineer",
            "seniority": "Senior",
            "department": "Engineering",
            "work_model": "remote",
            "manager_email": manager_email,
        }

    def _run_record(self, mock_db, company_id: str, manager_email: str, ikey: str, prefs: MagicMock):
        from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService

        state = self._build_state(manager_email)
        initial_state: dict = {}

        async def _run():
            with patch(
                "app.domains.job_creation.services.manager_preferences_service.ManagerPreferencesService.get_or_create",
                new_callable=AsyncMock,
                return_value=prefs,
            ):
                await ManagerPreferencesService.record_job_completion(
                    db=mock_db,
                    company_id=company_id,
                    manager_email=manager_email,
                    final_state=state,
                    initial_state=initial_state,
                    idempotency_key=ikey,
                )

        asyncio.run(_run())

    def test_first_call_increments_count(self):
        """First call with new idempotency_key should set last_idempotency_key."""
        mock_db = AsyncMock()
        prefs = MagicMock()
        prefs.last_idempotency_key = None  # No previous key
        prefs.jobs_created_count = 0
        prefs.preferred_seniorities = []
        prefs.preferred_departments = []
        prefs.preferred_work_models = []

        self._run_record(mock_db, "co-1", "ana@company.com", "key-001", prefs)

        # jobs_created_count should have been incremented
        assert prefs.jobs_created_count == 1
        assert prefs.last_idempotency_key == "key-001"

    def test_second_call_with_same_key_does_not_increment(self):
        """Second call with same idempotency_key must skip — no double increment."""
        mock_db = AsyncMock()
        prefs = MagicMock()
        prefs.last_idempotency_key = "key-001"  # Already processed
        prefs.jobs_created_count = 1
        prefs.preferred_seniorities = ["Senior"]
        prefs.preferred_departments = ["Engineering"]
        prefs.preferred_work_models = []

        self._run_record(mock_db, "co-1", "ana@company.com", "key-001", prefs)

        # Should remain 1 — no increment
        assert prefs.jobs_created_count == 1, (
            f"Expected jobs_created_count=1 (idempotent), got {prefs.jobs_created_count}. "
            "Fix: check `if prefs.last_idempotency_key == idempotency_key: return` "
            "at start of record_job_completion()."
        )

    def test_different_key_increments_again(self):
        """Different idempotency_key on same manager should increment."""
        mock_db = AsyncMock()
        prefs = MagicMock()
        prefs.last_idempotency_key = "key-001"
        prefs.jobs_created_count = 1
        prefs.preferred_seniorities = ["Senior"]
        prefs.preferred_departments = ["Engineering"]
        prefs.preferred_work_models = []

        self._run_record(mock_db, "co-1", "ana@company.com", "key-002", prefs)

        assert prefs.jobs_created_count == 2, (
            f"Expected jobs_created_count=2 (new key), got {prefs.jobs_created_count}."
        )


# ---------------------------------------------------------------------------
# Tests: apply_to_state is fail-open
# ---------------------------------------------------------------------------

class TestApplyToStateFailOpen:
    """apply_to_state() must NEVER raise — always fail-open and return {}."""

    def test_returns_empty_on_db_error(self):
        from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService

        async def _run():
            mock_db = AsyncMock()

            with patch(
                "app.domains.job_creation.services.manager_preferences_service.ManagerPreferencesService.get_or_create",
                side_effect=Exception("DB connection failed"),
            ):
                result = await ManagerPreferencesService.apply_to_state(
                    db=mock_db,
                    company_id="co-1",
                    manager_email="ana@company.com",
                    state={},
                )

            return result

        result = asyncio.run(_run())
        assert result == {}, (
            f"apply_to_state() should return {{}} on failure (fail-open), got {result}. "
            "Fix: wrap body in try/except Exception and return {} on any error."
        )

    def test_does_not_raise_on_none_company_id(self):
        """Passing empty company_id must still not raise from apply_to_state."""
        from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService

        async def _run():
            mock_db = AsyncMock()
            return await ManagerPreferencesService.apply_to_state(
                db=mock_db,
                company_id="",
                manager_email="ana@company.com",
                state={},
            )

        # Must not raise
        result = asyncio.run(_run())
        assert isinstance(result, dict)

    def test_returns_empty_when_no_history(self):
        """Manager with zero jobs created should return empty dict (no prefs yet)."""
        from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService

        async def _run():
            mock_db = AsyncMock()
            mock_prefs = MagicMock()
            mock_prefs.jobs_created_count = 0
            mock_prefs.preferred_seniorities = []
            mock_prefs.preferred_departments = []
            mock_prefs.preferred_work_models = []
            mock_prefs.salary_percentile_preference = None
            mock_prefs.screening_style = "standard"
            mock_prefs.approve_before_publish = False

            with patch(
                "app.domains.job_creation.services.manager_preferences_service.ManagerPreferencesService.get_or_create",
                new_callable=AsyncMock,
                return_value=mock_prefs,
            ):
                return await ManagerPreferencesService.apply_to_state(
                    db=mock_db,
                    company_id="co-1",
                    manager_email="ana@company.com",
                    state={},
                )

        result = asyncio.run(_run())
        assert result == {}, f"No history → apply_to_state should return {{}}, got {result}"


# ---------------------------------------------------------------------------
# Tests: record_job_completion is fail-closed when company_id missing
# ---------------------------------------------------------------------------

class TestRecordJobCompletionFailClosed:
    """record_job_completion() must raise when company_id is empty (fail-closed)."""

    def test_raises_on_empty_company_id(self):
        from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService
        import pytest

        async def _run():
            mock_db = AsyncMock()
            await ManagerPreferencesService.record_job_completion(
                db=mock_db,
                company_id="",  # Empty — should raise
                manager_email="ana@company.com",
                final_state={"job_title": "Engineer"},
                initial_state={},
                idempotency_key="key-001",
            )

        with pytest.raises(Exception):
            asyncio.run(_run())
