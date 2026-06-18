"""GAP-05-004: Optimistic locking for job vacancy updates.

Uses `updated_at` as the lock token. When a client sends
`expected_updated_at` in the update payload and it does not match
the current DB value, the server returns HTTP 409 Conflict.
Backward-compatible: omitting the field skips the check.
"""

from datetime import datetime

import pytest

# ---------------------------------------------------------------------------
# Lazy import helper — lifecycle.py has a pre-existing parse error that
# blocks the normal package import chain.  We import _shared directly.
# ---------------------------------------------------------------------------

def _load_shared():
    """Import app.api.v1.job_vacancies._shared bypassing __init__.py."""
    import importlib.util, sys
    _KEY = "app.api.v1.job_vacancies._shared"
    if _KEY in sys.modules:
        return sys.modules[_KEY]
    spec = importlib.util.spec_from_file_location(
        _KEY,
        "lia-agent-system/app/api/v1/job_vacancies/_shared.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_KEY] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Schema-level tests
# ---------------------------------------------------------------------------


class TestJobVacancyUpdateSchema:
    """Verify the expected_updated_at field exists and is optional."""

    @pytest.fixture(autouse=True)
    def _import_schema(self):
        mod = _load_shared()
        self.JobVacancyUpdate = mod.JobVacancyUpdate

    def test_expected_updated_at_field_exists(self):
        """Schema accepts expected_updated_at."""
        ts = datetime(2026, 6, 15, 12, 0, 0)
        schema = self.JobVacancyUpdate(title="Test", expected_updated_at=ts)
        assert schema.expected_updated_at == ts

    def test_expected_updated_at_defaults_to_none(self):
        """Omitting expected_updated_at keeps backward compat."""
        schema = self.JobVacancyUpdate(title="Test")
        assert schema.expected_updated_at is None

    def test_expected_updated_at_in_dump(self):
        """expected_updated_at should be in dump so endpoint can read it."""
        ts = datetime(2026, 6, 15, 12, 0, 0)
        schema = self.JobVacancyUpdate(title="New Title", expected_updated_at=ts)
        dump = schema.model_dump(exclude_unset=True, exclude_none=True)
        assert "expected_updated_at" in dump

    def test_expected_updated_at_accepts_iso_string(self):
        """FE typically sends ISO string; Pydantic should coerce."""
        schema = self.JobVacancyUpdate(
            title="Test",
            expected_updated_at="2026-06-15T12:00:00",
        )
        assert isinstance(schema.expected_updated_at, datetime)

    def test_expected_updated_at_not_persisted_after_pop(self):
        """After popping, update_data should not contain the field."""
        ts = datetime(2026, 6, 15, 12, 0, 0)
        schema = self.JobVacancyUpdate(title="T", expected_updated_at=ts)
        dump = schema.model_dump(exclude_unset=True, exclude_none=True)
        dump.pop("expected_updated_at", None)
        assert "expected_updated_at" not in dump


# ---------------------------------------------------------------------------
# Conflict detection helper tests
# ---------------------------------------------------------------------------


class TestCheckOptimisticLock:
    """Test the check_optimistic_lock helper function."""

    def test_passes_when_matching(self):
        from app.shared.optimistic_lock import check_optimistic_lock

        db_ts = datetime(2026, 6, 15, 12, 0, 0)
        check_optimistic_lock(db_ts, db_ts)  # should not raise

    def test_passes_when_expected_is_none(self):
        from app.shared.optimistic_lock import check_optimistic_lock

        db_ts = datetime(2026, 6, 15, 12, 0, 0)
        check_optimistic_lock(db_ts, None)  # skip check

    def test_passes_when_db_is_none(self):
        """Edge case: vacancy never updated (updated_at is None)."""
        from app.shared.optimistic_lock import check_optimistic_lock

        check_optimistic_lock(None, None)  # both None, skip

    def test_raises_409_when_stale(self):
        from app.shared.optimistic_lock import check_optimistic_lock

        db_ts = datetime(2026, 6, 15, 14, 0, 0)
        stale = datetime(2026, 6, 15, 12, 0, 0)
        with pytest.raises(Exception) as exc_info:
            check_optimistic_lock(db_ts, stale)
        assert exc_info.value.status_code == 409

    def test_409_detail_contains_conflict_key(self):
        from app.shared.optimistic_lock import check_optimistic_lock

        db_ts = datetime(2026, 6, 15, 14, 0, 0)
        stale = datetime(2026, 6, 15, 12, 0, 0)
        with pytest.raises(Exception) as exc_info:
            check_optimistic_lock(db_ts, stale)
        detail = exc_info.value.detail
        detail_str = str(detail)
        assert "modified" in detail_str.lower() or "conflict" in detail_str.lower()

    def test_409_includes_current_timestamp(self):
        """409 response should include current updated_at so FE can retry."""
        from app.shared.optimistic_lock import check_optimistic_lock

        db_ts = datetime(2026, 6, 15, 14, 0, 0)
        stale = datetime(2026, 6, 15, 12, 0, 0)
        with pytest.raises(Exception) as exc_info:
            check_optimistic_lock(db_ts, stale)
        detail = exc_info.value.detail
        assert isinstance(detail, dict)
        assert "current_updated_at" in detail

    def test_microsecond_difference_triggers_conflict(self):
        """Even 1-microsecond difference must trigger conflict."""
        from app.shared.optimistic_lock import check_optimistic_lock

        t1 = datetime(2026, 6, 15, 12, 0, 0, 0)
        t2 = datetime(2026, 6, 15, 12, 0, 0, 1)
        with pytest.raises(Exception) as exc_info:
            check_optimistic_lock(t1, t2)
        assert exc_info.value.status_code == 409

    def test_raises_409_when_db_none_but_expected_provided(self):
        """If DB has no updated_at but client expects one, conflict."""
        from app.shared.optimistic_lock import check_optimistic_lock

        with pytest.raises(Exception) as exc_info:
            check_optimistic_lock(None, datetime(2026, 6, 15, 12, 0, 0))
        assert exc_info.value.status_code == 409

    def test_409_detail_includes_expected_timestamp(self):
        """FE should see both current and expected for debugging."""
        from app.shared.optimistic_lock import check_optimistic_lock

        db_ts = datetime(2026, 6, 15, 14, 0, 0)
        stale = datetime(2026, 6, 15, 12, 0, 0)
        with pytest.raises(Exception) as exc_info:
            check_optimistic_lock(db_ts, stale)
        detail = exc_info.value.detail
        assert detail["expected_updated_at"] == stale.isoformat()
        assert detail["current_updated_at"] == db_ts.isoformat()

    def test_409_detail_error_key(self):
        """Detail should include structured error key for FE consumption."""
        from app.shared.optimistic_lock import check_optimistic_lock

        db_ts = datetime(2026, 6, 15, 14, 0, 0)
        stale = datetime(2026, 6, 15, 12, 0, 0)
        with pytest.raises(Exception) as exc_info:
            check_optimistic_lock(db_ts, stale)
        detail = exc_info.value.detail
        assert detail["error"] == "optimistic_lock_conflict"
