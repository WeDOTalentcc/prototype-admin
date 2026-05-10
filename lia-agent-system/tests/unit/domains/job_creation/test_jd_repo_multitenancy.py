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


def _make_mock_db_with_record(record_company_id: str | None):
    """AsyncSession mock whose lookup returns a record bound to record_company_id.

    Returns (db_mock, returned_record). When record_company_id is None,
    lookup returns None (record not found / not owned).
    """
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()

    if record_company_id is None:
        # Result that returns None on .scalar_one_or_none()
        execute_result = MagicMock()
        execute_result.scalar_one_or_none = MagicMock(return_value=None)
        execute_result.scalar = MagicMock(return_value=None)
    else:
        record = MagicMock()
        record.company_id = record_company_id
        record.id = uuid.uuid4()
        execute_result = MagicMock()
        execute_result.scalar_one_or_none = MagicMock(return_value=record)
        execute_result.scalar = MagicMock(return_value=record_company_id)

    db.execute = AsyncMock(return_value=execute_result)
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

        db = _make_mock_db_with_record("co-OTHER")
        repo = JdSimilarHistoryRepository(db)

        async def _run():
            return await repo.get_by_id(record_id=uuid.uuid4(), company_id="co-CALLER")

        result = asyncio.run(_run())
        assert result is None
