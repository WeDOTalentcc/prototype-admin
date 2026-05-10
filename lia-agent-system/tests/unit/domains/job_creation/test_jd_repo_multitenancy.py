"""TDD red-phase — JdSimilarHistoryRepository multi-tenancy hardening (Sprint B Phase 1, gap C5).

Harness taxonomy: Sensor (computacional, feedback) — closes IDOR gap on
methods that operate by record_id (mark_filled, increment_reuse, get_by_id).

Why this exists: those 3 methods previously took only `record_id`. Anyone
holding a record_id from company A could call them from a request scoped
to company B and mutate cross-tenant data. CLAUDE.md non-negotiable rule
#1 (multi-tenancy) requires `company_id` on every read/write.

If a test fails: ensure the method signature now requires `company_id` and
that it validates ownership. The validation should raise ValueError or
return None silently; this suite asserts ValueError (fail-loud per SPEC D3).
"""
from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_mock_db_with_record(
    record_company_id: str | None,
    caller_company_id: str | None = None,
):
    """AsyncSession mock simulating an ownership SELECT and record lookup.

    Behavior:
    - mark_filled / increment_reuse: repo runs `select(JdSimilarHistory.company_id)`
      → scalar_one_or_none() returns the record's company_id (a string), which
      the repo compares against caller's company_id. We return record_company_id
      as the scalar.
    - get_by_id: repo runs `select(JdSimilarHistory).where(id, company_id=caller)`
      → in real DB the WHERE clause filters out cross-tenant rows so result is None.
      We simulate that filter by checking caller_company_id at the mock layer.

    Args:
      record_company_id: company that actually owns the record (or None if missing)
      caller_company_id: company making the call. Used to simulate WHERE filtering
        for get_by_id. If unset, mock returns the record regardless (used when
        only ownership-by-scalar matters, not WHERE filtering).
    """
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    if record_company_id is None:
        execute_result = MagicMock()
        execute_result.scalar_one_or_none = MagicMock(return_value=None)
        execute_result.scalar = MagicMock(return_value=None)
    else:
        # Build a record-like object for get_by_id full-row select
        record = MagicMock()
        record.company_id = record_company_id
        record.id = uuid.uuid4()

        # Simulate WHERE company_id filter for get_by_id: if caller mismatches,
        # the row is filtered out and scalar_one_or_none returns None.
        if caller_company_id is not None and caller_company_id != record_company_id:
            row_for_caller = None
        else:
            row_for_caller = record

        execute_result = MagicMock()
        # For ownership SELECT (select(JdSimilarHistory.company_id)) → scalar value
        # For full-row SELECT (select(JdSimilarHistory)) → record (or None if filtered)
        # The repo decides which based on its query, and uses scalar_one_or_none
        # for both. We pick based on caller intent: ownership check expects the
        # company_id string; full-row select expects the record. Returning the
        # company_id as scalar works for ownership; full-row tests must also
        # accept it because both branches use scalar_one_or_none.
        # To handle both: side_effect-style — but cleaner is to have separate
        # mocks per method. For mark_filled/increment_reuse the repo calls
        # SELECT first (ownership) and we want company_id; for get_by_id the
        # repo calls SELECT once and we want the (filtered) record.

        # Default: return company_id scalar (works for ownership).
        # Override per-test: tests using get_by_id will set scalar_one_or_none
        # to row_for_caller in their own setup if needed.
        execute_result.scalar_one_or_none = MagicMock(return_value=record_company_id)
        execute_result.scalar = MagicMock(return_value=record_company_id)
        # Stash row_for_caller so get_by_id tests can swap it in
        execute_result._row_for_caller = row_for_caller

    db.execute = AsyncMock(return_value=execute_result)
    db._execute_result = execute_result  # expose for per-test tweaks
    return db


class TestMarkFilledCompanyId:
    def test_mark_filled_requires_company_id(self):
        """company_id='' must raise ValueError (multi-tenancy fail-closed)."""
        from app.domains.job_creation.repositories.jd_similar_history_repository import (
            JdSimilarHistoryRepository,
        )

        db = _make_mock_db_with_record("co-A")
        repo = JdSimilarHistoryRepository(db)

        async def _run():
            await repo.mark_filled(
                record_id=uuid.uuid4(),
                company_id="",
                time_to_fill_days=10,
                candidates_count=20,
            )

        with pytest.raises(ValueError, match="company_id"):
            asyncio.run(_run())

    def test_mark_filled_rejects_cross_tenant_record(self):
        """Calling with company_id != record's company_id must raise."""
        from app.domains.job_creation.repositories.jd_similar_history_repository import (
            JdSimilarHistoryRepository,
        )

        db = _make_mock_db_with_record("co-OTHER")  # record belongs to other company
        repo = JdSimilarHistoryRepository(db)

        async def _run():
            await repo.mark_filled(
                record_id=uuid.uuid4(),
                company_id="co-CALLER",
                time_to_fill_days=15,
                candidates_count=12,
            )

        with pytest.raises(ValueError, match="company_id mismatch|not found|access denied"):
            asyncio.run(_run())

    def test_mark_filled_accepts_owned_record(self):
        """Same company_id should proceed (no exception)."""
        from app.domains.job_creation.repositories.jd_similar_history_repository import (
            JdSimilarHistoryRepository,
        )

        db = _make_mock_db_with_record("co-OWNER")
        repo = JdSimilarHistoryRepository(db)

        async def _run():
            await repo.mark_filled(
                record_id=uuid.uuid4(),
                company_id="co-OWNER",
                time_to_fill_days=10,
                candidates_count=20,
            )

        # No exception expected
        asyncio.run(_run())


class TestIncrementReuseCompanyId:
    def test_increment_reuse_requires_company_id(self):
        from app.domains.job_creation.repositories.jd_similar_history_repository import (
            JdSimilarHistoryRepository,
        )

        db = _make_mock_db_with_record("co-A")
        repo = JdSimilarHistoryRepository(db)

        async def _run():
            await repo.increment_reuse(record_id=uuid.uuid4(), company_id="")

        with pytest.raises(ValueError, match="company_id"):
            asyncio.run(_run())

    def test_increment_reuse_rejects_cross_tenant_record(self):
        from app.domains.job_creation.repositories.jd_similar_history_repository import (
            JdSimilarHistoryRepository,
        )

        db = _make_mock_db_with_record("co-OTHER")
        repo = JdSimilarHistoryRepository(db)

        async def _run():
            await repo.increment_reuse(record_id=uuid.uuid4(), company_id="co-CALLER")

        with pytest.raises(ValueError, match="company_id mismatch|not found|access denied"):
            asyncio.run(_run())


class TestGetByIdCompanyId:
    def test_get_by_id_requires_company_id(self):
        from app.domains.job_creation.repositories.jd_similar_history_repository import (
            JdSimilarHistoryRepository,
        )

        db = _make_mock_db_with_record("co-A")
        repo = JdSimilarHistoryRepository(db)

        async def _run():
            await repo.get_by_id(record_id=uuid.uuid4(), company_id="")

        with pytest.raises(ValueError, match="company_id"):
            asyncio.run(_run())

    def test_get_by_id_returns_none_for_cross_tenant(self):
        """get_by_id with mismatched company_id returns None (not raise) —
        consistent with 'record not found' semantics for read ops."""
        from app.domains.job_creation.repositories.jd_similar_history_repository import (
            JdSimilarHistoryRepository,
        )

        # Simulate WHERE company_id=co-CALLER filtering out row owned by co-OTHER.
        db = _make_mock_db_with_record("co-OTHER", caller_company_id="co-CALLER")
        # get_by_id selects full row, so scalar_one_or_none must return the
        # filtered row (None when caller mismatches).
        db._execute_result.scalar_one_or_none = MagicMock(
            return_value=db._execute_result._row_for_caller
        )
        repo = JdSimilarHistoryRepository(db)

        async def _run():
            return await repo.get_by_id(record_id=uuid.uuid4(), company_id="co-CALLER")

        result = asyncio.run(_run())
        assert result is None
