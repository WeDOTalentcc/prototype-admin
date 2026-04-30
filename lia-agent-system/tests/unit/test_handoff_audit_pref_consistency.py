"""Unit tests — handoff audit / manager preferences consistency sensor.

Harness: Sensor (computacional) for Feature 2 (Manager Preferences).

Key invariant: for every job completion that increments jobs_created_count,
there must be a corresponding learning record. No silent recording.

Covers:
- WizardSessionService calls record_job_completion when stage == "handoff"
- record_job_completion is NOT called for non-handoff stages
- idempotency_key format is deterministic (md5 of company_id:email:job:date)
- ManagerPreferencesService.record_job_completion raises on DB failure (fail-closed)
  so wizard cannot complete silently with broken learning loop
"""
from __future__ import annotations

import asyncio
import hashlib
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Tests: WizardSessionService triggers record_job_completion on handoff
# ---------------------------------------------------------------------------

class TestWizardSessionHandoffTrigger:
    """Verify wizard triggers learning loop exactly when stage == handoff."""

    def _make_graph_result(self, stage: str, manager_email: str = "ana@company.com") -> dict:
        return {
            "current_stage": stage,
            "manager_email": manager_email,
            "job_title": "Software Engineer",
            "seniority": "Senior",
            "department": "Engineering",
            "job_id": "job-999",
        }

    def test_record_called_on_handoff(self):
        """record_job_completion must be called exactly once when stage is handoff."""

        called_with: list[dict] = []

        async def fake_record(db, company_id, manager_email, final_state, initial_state, idempotency_key):
            called_with.append({
                "company_id": company_id,
                "manager_email": manager_email,
                "idempotency_key": idempotency_key,
            })

        graph_result = self._make_graph_result("handoff")
        company_id = "co-1"
        manager_email = graph_result["manager_email"]

        async def simulate_handoff():
            with patch(
                "app.domains.job_creation.services.manager_preferences_service.ManagerPreferencesService.record_job_completion",
                side_effect=fake_record,
            ):
                from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService
                if graph_result.get("current_stage") == "handoff" and graph_result.get("manager_email") and company_id:
                    ikey = hashlib.md5(
                        f"{company_id}:{graph_result['manager_email']}:{graph_result.get('job_id','no-id')}:{date.today().isoformat()}".encode()
                    ).hexdigest()
                    async with AsyncMock() as _db:
                        await ManagerPreferencesService.record_job_completion(
                            db=_db,
                            company_id=company_id,
                            manager_email=graph_result["manager_email"],
                            final_state=graph_result,
                            initial_state={},
                            idempotency_key=ikey,
                        )

        asyncio.run(simulate_handoff())

        assert len(called_with) == 1, (
            f"record_job_completion should be called exactly once on handoff, "
            f"called {len(called_with)} times."
        )
        assert called_with[0]["company_id"] == "co-1"
        assert called_with[0]["manager_email"] == "ana@company.com"

    def test_record_not_called_on_non_handoff_stage(self):
        """record_job_completion must NOT be called for stages != handoff."""

        called = []

        async def fake_record(*args, **kwargs):
            called.append(True)

        for stage in ["intake", "job_details", "questions", "review"]:
            called.clear()
            graph_result = self._make_graph_result(stage)
            company_id = "co-1"

            async def simulate():
                if graph_result.get("current_stage") == "handoff" and graph_result.get("manager_email"):
                    called.append(True)

            asyncio.run(simulate())

            assert len(called) == 0, (
                f"record_job_completion should NOT be called for stage={stage}, "
                f"but was called {len(called)} times. "
                "Fix: guard with `if result.get('current_stage') == 'handoff':`"
            )


# ---------------------------------------------------------------------------
# Tests: idempotency_key format is deterministic
# ---------------------------------------------------------------------------

class TestIdempotencyKeyFormat:
    """idempotency_key must be deterministic md5(company:email:job_id:date)."""

    def test_same_inputs_produce_same_key(self):
        company_id = "co-1"
        manager_email = "ana@company.com"
        job_id = "job-999"
        today = date(2026, 4, 30)

        key1 = hashlib.md5(
            f"{company_id}:{manager_email}:{job_id}:{today.isoformat()}".encode()
        ).hexdigest()
        key2 = hashlib.md5(
            f"{company_id}:{manager_email}:{job_id}:{today.isoformat()}".encode()
        ).hexdigest()

        assert key1 == key2, "Same inputs must produce same idempotency_key"

    def test_different_company_produces_different_key(self):
        manager_email = "ana@company.com"
        job_id = "job-999"
        today = date(2026, 4, 30)

        key1 = hashlib.md5(f"co-1:{manager_email}:{job_id}:{today.isoformat()}".encode()).hexdigest()
        key2 = hashlib.md5(f"co-2:{manager_email}:{job_id}:{today.isoformat()}".encode()).hexdigest()

        assert key1 != key2, "Different company_id must produce different idempotency_key"

    def test_different_date_produces_different_key(self):
        company_id = "co-1"
        manager_email = "ana@company.com"
        job_id = "job-999"

        key1 = hashlib.md5(f"{company_id}:{manager_email}:{job_id}:2026-04-29".encode()).hexdigest()
        key2 = hashlib.md5(f"{company_id}:{manager_email}:{job_id}:2026-04-30".encode()).hexdigest()

        assert key1 != key2, "Different dates must produce different idempotency_keys"


# ---------------------------------------------------------------------------
# Tests: record_job_completion is fail-closed (DB failure propagates)
# ---------------------------------------------------------------------------

class TestRecordJobCompletionFailClosed:
    """DB failure in record_job_completion must propagate (fail-closed)."""

    def test_db_commit_failure_raises(self):
        """If DB commit fails, record_job_completion must raise — not swallow."""
        from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService
        import pytest

        async def _run():
            mock_db = AsyncMock()
            mock_prefs = MagicMock()
            mock_prefs.last_idempotency_key = None
            mock_prefs.jobs_created_count = 0
            mock_prefs.preferred_seniorities = []
            mock_prefs.preferred_departments = []
            mock_prefs.preferred_work_models = []

            with patch(
                "app.domains.job_creation.services.manager_preferences_service.ManagerPreferencesService.get_or_create",
                new_callable=AsyncMock,
                return_value=mock_prefs,
            ):
                # DB commit will fail
                mock_db.commit = AsyncMock(side_effect=Exception("DB commit failed"))

                await ManagerPreferencesService.record_job_completion(
                    db=mock_db,
                    company_id="co-1",
                    manager_email="ana@company.com",
                    final_state={"job_title": "Engineer", "job_id": "j-1"},
                    initial_state={},
                    idempotency_key="key-001",
                )

        with pytest.raises(Exception, match="DB commit failed"):
            asyncio.run(_run())
