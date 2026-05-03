"""UC-P2-01: Tests for MemoryResolver Redis persistence."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_action_history_persisted_to_redis_when_available():
    """add_action should push to Redis when _REDIS is available."""
    mock_redis = MagicMock()

    with patch("app.shared.memory_resolver._REDIS", mock_redis):
        from app.shared.memory_resolver import MemoryResolver
        resolver = MemoryResolver(session_id="session_123")
        resolver.add_action(domain="cv_screening", action="shortlist_candidate")

    # rpush called once with the action JSON and the correct key
    assert mock_redis.rpush.called, "rpush should be called when Redis is available"
    call_args = mock_redis.rpush.call_args
    assert call_args[0][0] == "lia:action_history:session_123"
    # expire called with 86400 TTL
    assert mock_redis.expire.called
    expire_args = mock_redis.expire.call_args
    assert expire_args[0][0] == "lia:action_history:session_123"
    assert expire_args[0][1] == 86400


def test_get_action_history_reads_from_redis_when_available():
    """get_action_history should return Redis data when Redis responds."""
    import json

    mock_redis = MagicMock()
    mock_redis.lrange.return_value = [
        json.dumps({"domain": "pipeline", "action": "move_candidate",
                    "timestamp": "2026-05-02T00:00:00+00:00", "metadata": {}, "success": True})
    ]

    with patch("app.shared.memory_resolver._REDIS", mock_redis):
        from app.shared.memory_resolver import MemoryResolver
        resolver = MemoryResolver(session_id="session_123")
        history = resolver.get_action_history()

    assert len(history) == 1
    assert history[0]["action"] == "move_candidate"


def test_get_recent_actions_uses_redis_backed_history():
    """get_recent_actions should respect limit from Redis-backed history."""
    import json

    mock_redis = MagicMock()
    actions = [
        json.dumps({"domain": "d", "action": f"a{i}", "timestamp": "2026-05-02T00:00:00+00:00",
                    "metadata": {}, "success": True})
        for i in range(10)
    ]
    mock_redis.lrange.return_value = actions

    with patch("app.shared.memory_resolver._REDIS", mock_redis):
        from app.shared.memory_resolver import MemoryResolver
        resolver = MemoryResolver(session_id="session_abc")
        recent = resolver.get_recent_actions(limit=3)

    assert len(recent) == 3
    assert recent[-1]["action"] == "a9"  # last 3 from 10


def test_action_history_falls_back_to_memory_when_redis_unavailable():
    """get_action_history should return in-memory list when _REDIS is None."""
    with patch("app.shared.memory_resolver._REDIS", None):
        from app.shared.memory_resolver import MemoryResolver
        resolver = MemoryResolver(session_id="session_456")
        resolver.add_action(domain="search", action="find_candidates")
        history = resolver.get_action_history()

    assert len(history) == 1
    assert history[0]["action"] == "find_candidates"


def test_add_action_does_not_raise_when_redis_write_fails():
    """A Redis failure in add_action must not propagate (fail-open)."""
    mock_redis = MagicMock()
    mock_redis.rpush.side_effect = ConnectionError("Redis down")

    with patch("app.shared.memory_resolver._REDIS", mock_redis):
        from app.shared.memory_resolver import MemoryResolver
        resolver = MemoryResolver(session_id="session_789")
        # Should NOT raise even when Redis is unavailable
        record = resolver.add_action(domain="test", action="noop")

    assert record.action == "noop"
    # In-memory fallback should still hold the record
    assert len(resolver._action_history) == 1


def test_get_action_history_falls_back_to_memory_on_redis_error():
    """get_action_history should fall back to in-memory on Redis read error."""
    mock_redis = MagicMock()
    mock_redis.lrange.side_effect = ConnectionError("Redis down")

    with patch("app.shared.memory_resolver._REDIS", mock_redis):
        from app.shared.memory_resolver import MemoryResolver
        resolver = MemoryResolver(session_id="session_999")
        resolver.add_action(domain="fallback", action="test_action")
        history = resolver.get_action_history()

    assert any(h["action"] == "test_action" for h in history)
