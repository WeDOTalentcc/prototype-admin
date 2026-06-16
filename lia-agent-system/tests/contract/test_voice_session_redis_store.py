"""
F-15 P0 sentinels: VoiceSessionRedisRepository canonical behavior.

Audit: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-15.

Tests:
- I1  Round-trip save/load preserves state dict (in-memory fallback)
- I2  load returns None when session not stored
- I3  delete_session_state removes from store + reverse index
- I4  Multi-tenancy isolation (company A != company B)
- I5  Active sessions index per-company (list_active_session_ids)
- I6  Reverse index: find_company_id_for_session
- I7  Key pattern canonical (`voice:session:{company_id}:{session_id}`)
- I8  _require_company_id fail-closed (empty/None/non-str raises ValueError)
- I9  Concurrent save/load — 20 sessions no race
- I10 With Redis mocked: pipeline SET EX + SADD + reverse SET issued
- I11 With Redis mocked: delete pipeline DEL + SREM + reverse DEL
- I12 Redis unavailable → falls back to in-memory
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


@pytest.fixture
def repo():
    """Fresh repo per test with Redis FORCE-DISABLED for deterministic in-mem fallback."""
    from app.domains.voice.repositories.voice_session_redis_repository import (
        VoiceSessionRedisRepository,
    )
    r = VoiceSessionRedisRepository()
    # Force _get_redis() to always return None — bypasses lazy init that
    # would otherwise reach the shared singleton Redis client (race across
    # event loops in pytest-asyncio).
    async def _no_redis():
        return None
    r._get_redis = _no_redis  # type: ignore[method-assign]
    r._redis = None
    r._redis_available = False
    return r


@pytest.fixture
def sample_state():
    return {
        "session_id": "sess-1",
        "candidate_id": "cand-1",
        "candidate_name": "Joao da Silva",
        "company_id": "comp-A",
        "phone_number": "+55 11 ****1234",  # masked at rest (F-07)
        "status": "in_progress",
        "language": "pt-BR",
        "transcript_segments": [],
        "questions_asked": [],
        "consent_verified": True,
        "presentation_done": False,
        "started_at": "2026-05-22T10:00:00",
        "ended_at": None,
        "wsi_result": None,
        "error": None,
        "job_id": "job-1",
        "job_title": "DevOps",
        "job_context": {},
        "call_sid": "CA_abc",
        "voice_provider": "twilio",
    }


class TestF15RoundTrip:
    """I1: save/load preserves state dict."""

    async def test_save_then_load_returns_identical_state(self, repo, sample_state):
        await repo.save_session_state(
            company_id="comp-A", session_id="sess-1", state=sample_state,
        )
        loaded = await repo.load_session_state(
            company_id="comp-A", session_id="sess-1",
        )
        assert loaded == sample_state

    async def test_load_nonexistent_returns_none(self, repo):
        result = await repo.load_session_state(
            company_id="comp-A", session_id="never-existed",
        )
        assert result is None


class TestF15Delete:
    """I3: delete removes from primary + active + reverse indices."""

    async def test_delete_removes_state(self, repo, sample_state):
        await repo.save_session_state(
            company_id="comp-A", session_id="sess-1", state=sample_state,
        )
        deleted = await repo.delete_session_state(
            company_id="comp-A", session_id="sess-1",
        )
        assert deleted is True
        assert await repo.load_session_state(
            company_id="comp-A", session_id="sess-1"
        ) is None

    async def test_delete_removes_from_reverse_index(self, repo, sample_state):
        await repo.save_session_state(
            company_id="comp-A", session_id="sess-1", state=sample_state,
        )
        await repo.delete_session_state(
            company_id="comp-A", session_id="sess-1",
        )
        cid = await repo.find_company_id_for_session(session_id="sess-1")
        assert cid is None

    async def test_delete_nonexistent_returns_false(self, repo):
        deleted = await repo.delete_session_state(
            company_id="comp-A", session_id="never-existed",
        )
        assert deleted is False


class TestF15MultiTenancyIsolation:
    """I4: sessions saved under company A never appear under company B."""

    async def test_company_isolation_in_load(self, repo, sample_state):
        await repo.save_session_state(
            company_id="comp-A", session_id="sess-1", state=sample_state,
        )
        # Same session_id but different company → MISS.
        result = await repo.load_session_state(
            company_id="comp-B", session_id="sess-1",
        )
        assert result is None

    async def test_company_isolation_in_active_list(self, repo, sample_state):
        await repo.save_session_state(
            company_id="comp-A", session_id="sess-A1", state=sample_state,
        )
        await repo.save_session_state(
            company_id="comp-B", session_id="sess-B1", state={**sample_state, "session_id": "sess-B1"},
        )
        ids_a = await repo.list_active_session_ids(company_id="comp-A")
        ids_b = await repo.list_active_session_ids(company_id="comp-B")
        assert "sess-A1" in ids_a
        assert "sess-A1" not in ids_b
        assert "sess-B1" in ids_b
        assert "sess-B1" not in ids_a


class TestF15ReverseIndex:
    """I6: session_id → company_id lookup works (Twilio STT pipeline)."""

    async def test_find_company_id_for_session(self, repo, sample_state):
        await repo.save_session_state(
            company_id="comp-A", session_id="sess-1", state=sample_state,
        )
        cid = await repo.find_company_id_for_session(session_id="sess-1")
        assert cid == "comp-A"

    async def test_find_returns_none_for_unknown(self, repo):
        cid = await repo.find_company_id_for_session(session_id="never-existed")
        assert cid is None


class TestF15KeyPattern:
    """I7: keys follow canonical pattern."""

    def test_session_key_pattern(self, repo):
        key = repo._session_key("comp-A", "sess-1")
        assert key == "voice:session:comp-A:sess-1"

    def test_active_index_key_pattern(self, repo):
        key = repo._active_index_key("comp-A")
        assert key == "voice:sessions:active:comp-A"

    def test_reverse_index_key_pattern(self, repo):
        key = repo._reverse_index_key("sess-1")
        assert key == "voice:session_index:sess-1"


class TestF15TenantGuardFailClosed:
    """I8: _require_company_id rejects empty/None/non-str (multi-tenancy invariant)."""

    def test_empty_string_raises(self, repo):
        with pytest.raises(ValueError, match="company_id is required"):
            repo._session_key("", "sess-1")

    def test_none_raises(self, repo):
        with pytest.raises(ValueError, match="company_id is required"):
            repo._session_key(None, "sess-1")  # type: ignore[arg-type]

    def test_non_str_raises(self, repo):
        with pytest.raises(ValueError, match="company_id is required"):
            repo._session_key(123, "sess-1")  # type: ignore[arg-type]


class TestF15Concurrency:
    """I9: 20 concurrent save/load no race."""

    async def test_concurrent_save_load_no_cross_state(self, repo, sample_state):
        async def save_and_load(i: int) -> dict:
            sid = f"sess-{i}"
            state = {**sample_state, "session_id": sid, "candidate_id": f"cand-{i}"}
            await repo.save_session_state(
                company_id="comp-A", session_id=sid, state=state,
            )
            loaded = await repo.load_session_state(
                company_id="comp-A", session_id=sid,
            )
            return loaded

        results = await asyncio.gather(*[save_and_load(i) for i in range(20)])
        for i, r in enumerate(results):
            assert r is not None
            assert r["session_id"] == f"sess-{i}"
            assert r["candidate_id"] == f"cand-{i}"


class TestF15WithMockedRedis:
    """I10 + I11: when Redis is available, atomic pipeline ops are issued."""

    @pytest.fixture
    def mocked_redis(self):
        m = MagicMock()
        # The pipeline returns a chainable mock with set/sadd/expire/execute.
        pipe = MagicMock()
        pipe.set = MagicMock()
        pipe.sadd = MagicMock()
        pipe.expire = MagicMock()
        pipe.delete = MagicMock()
        pipe.srem = MagicMock()
        pipe.execute = AsyncMock(return_value=[True, 1, True])
        m.pipeline = MagicMock(return_value=pipe)
        m.get = AsyncMock(return_value=None)
        m.set = AsyncMock(return_value=True)
        m.delete = AsyncMock(return_value=1)
        m.smembers = AsyncMock(return_value=set())
        m.ping = AsyncMock(return_value=True)
        return m, pipe

    async def test_save_issues_pipeline_with_set_sadd_reverse(self, repo, sample_state, mocked_redis):
        redis_mock, pipe = mocked_redis
        # Override fixture's force-None _get_redis with one that returns our mock.
        async def _yield_mock():
            return redis_mock
        repo._get_redis = _yield_mock  # type: ignore[method-assign]
        repo._redis = redis_mock
        repo._redis_available = True

        await repo.save_session_state(
            company_id="comp-A", session_id="sess-1", state=sample_state,
        )

        # Pipeline must SET state + SADD active + EXPIRE active + SET reverse.
        assert pipe.set.call_count >= 2  # state + reverse index
        assert pipe.sadd.called
        assert pipe.expire.called
        assert pipe.execute.await_count == 1

    async def test_delete_issues_pipeline_with_del_srem_reverse(self, repo, sample_state, mocked_redis):
        redis_mock, pipe = mocked_redis
        async def _yield_mock():
            return redis_mock
        repo._get_redis = _yield_mock  # type: ignore[method-assign]
        repo._redis = redis_mock
        repo._redis_available = True

        await repo.delete_session_state(
            company_id="comp-A", session_id="sess-1",
        )

        assert pipe.delete.call_count >= 2  # state + reverse index
        assert pipe.srem.called
        assert pipe.execute.await_count == 1

    async def test_redis_unavailable_falls_back_to_memory(self, repo, sample_state):
        """I12: when Redis ping fails, fall back to in-memory dict."""
        # Force unavailability path.
        repo._redis = None
        repo._redis_available = False

        await repo.save_session_state(
            company_id="comp-A", session_id="sess-1", state=sample_state,
        )
        # Verify state landed in memory fallback (not Redis).
        assert repo._memory_fallback.get("voice:session:comp-A:sess-1") is not None


class TestF15ListActiveSessions:
    """I5: list_active_session_ids returns SET members for a tenant."""

    async def test_active_sessions_listed(self, repo, sample_state):
        await repo.save_session_state(
            company_id="comp-A", session_id="sess-1", state=sample_state,
        )
        await repo.save_session_state(
            company_id="comp-A", session_id="sess-2", state={**sample_state, "session_id": "sess-2"},
        )
        ids = await repo.list_active_session_ids(company_id="comp-A")
        assert sorted(ids) == ["sess-1", "sess-2"]

    async def test_active_sessions_limit(self, repo, sample_state):
        for i in range(10):
            await repo.save_session_state(
                company_id="comp-A", session_id=f"sess-{i}",
                state={**sample_state, "session_id": f"sess-{i}"},
            )
        ids = await repo.list_active_session_ids(company_id="comp-A", limit=3)
        assert len(ids) == 3
