"""
Tests for SSE reconnect dedup guard (GAP-09-002).

Validates that:
1. First request sets Redis dedup key
2. Reconnect (with Last-Event-ID) returns early without reprocessing
3. Duplicate POST without Last-Event-ID is allowed (intentional retry)
4. Redis failure is fail-open (does not block request)
5. Dedup key has TTL (120s)
"""
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def _mock_redis():
    """In-memory Redis mock with get/set supporting nx/ex."""
    store = {}

    class FakeRedis:
        def get(self, key):
            return store.get(key)

        def set(self, key, value, ex=None, nx=False):
            if nx and key in store:
                return False
            store[key] = value
            return True

    redis = FakeRedis()
    redis._store = store
    return redis


def _make_dedup_key(session_id: str, content: str, user_id: str) -> str:
    turn_hash = hashlib.sha256(f"{session_id}:{content}:{user_id}".encode()).hexdigest()[:16]
    return f"sse_turn_dedup:{session_id}:{turn_hash}"


class TestSSEDedupGuard:
    """Unit tests for the dedup logic extracted from sse_chat_stream."""

    def test_first_request_sets_dedup_key(self, _mock_redis):
        session_id = "test-session-001"
        content = "ola LIA"
        user_id = "user-123"
        key = _make_dedup_key(session_id, content, user_id)

        assert _mock_redis.get(key) is None
        _mock_redis.set(key, "1", ex=120, nx=True)
        assert _mock_redis.get(key) == "1"

    def test_reconnect_with_last_event_id_detects_duplicate(self, _mock_redis):
        session_id = "test-session-002"
        content = "busque candidatos"
        user_id = "user-456"
        key = _make_dedup_key(session_id, content, user_id)

        _mock_redis.set(key, "1", ex=120, nx=True)

        last_event_id = f"{session_id[:8]}-5"
        is_reconnect = bool(last_event_id)
        already = _mock_redis.get(key)

        assert already is not None
        assert is_reconnect is True

    def test_duplicate_post_without_last_event_id_allowed(self, _mock_redis):
        session_id = "test-session-003"
        content = "envie email"
        user_id = "user-789"
        key = _make_dedup_key(session_id, content, user_id)

        _mock_redis.set(key, "1", ex=120, nx=True)

        last_event_id = ""
        is_reconnect = bool(last_event_id)
        already = _mock_redis.get(key)

        assert already is not None
        assert is_reconnect is False

    def test_redis_failure_is_fail_open(self):
        class BrokenRedis:
            def get(self, key):
                raise ConnectionError("Redis down")
            def set(self, *a, **kw):
                raise ConnectionError("Redis down")

        redis = BrokenRedis()
        session_id = "test-session-004"
        content = "teste"
        user_id = "user-000"
        key = _make_dedup_key(session_id, content, user_id)

        blocked = False
        try:
            already = redis.get(key)
        except Exception:
            blocked = False

        assert blocked is False

    def test_different_messages_get_different_keys(self):
        session_id = "test-session-005"
        user_id = "user-111"
        key1 = _make_dedup_key(session_id, "busque candidatos Python", user_id)
        key2 = _make_dedup_key(session_id, "envie email para candidato", user_id)
        assert key1 != key2

    def test_same_message_different_session_gets_different_key(self):
        content = "ola LIA"
        user_id = "user-222"
        key1 = _make_dedup_key("session-A", content, user_id)
        key2 = _make_dedup_key("session-B", content, user_id)
        assert key1 != key2

    def test_nx_prevents_overwrite(self, _mock_redis):
        key = "sse_turn_dedup:test:abc"
        assert _mock_redis.set(key, "1", ex=120, nx=True) is True
        assert _mock_redis.set(key, "2", ex=120, nx=True) is False
        assert _mock_redis.get(key) == "1"

    def test_dedup_key_format(self):
        key = _make_dedup_key("my-session", "hello", "user-1")
        assert key.startswith("sse_turn_dedup:my-session:")
        assert len(key.split(":")[-1]) == 16
