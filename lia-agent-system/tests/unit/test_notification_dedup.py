"""
TDD — GAP-09-007: Notification deduplication via Redis.

Tests that lia_messaging.notification_dedup:
1. First send marks the key and returns NOT a duplicate.
2. Second send within TTL is detected as a duplicate and skipped.
3. Different event_type produces a different key (not a duplicate).
4. Different candidate (user_id) produces a different key.
5. After TTL expires the key is gone and a re-send is allowed.
6. Redis unavailable -> fail-open (is_duplicate returns False).
7. build_idempotency_key is stable (deterministic for same inputs).

All Redis interactions are mocked via a FakeRedis helper so no real Redis
connection is opened during pytest collection or execution.
"""
from __future__ import annotations

import asyncio
import uuid
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeRedis:
    """Minimal in-memory Redis substitute for unit tests.

    Supports: SET NX EX, GET, DEL, aclose.
    Simulates the TTL by tracking expiry in a separate dict.
    """

    def __init__(self):
        self._store: dict[str, str] = {}
        self._closed = False
        self.raise_on_next_set: Exception | None = None

    async def set(self, key: str, value: str, *, ex: int | None = None, nx: bool = False) -> bool | None:
        """Returns True (truthy) if key was set, None if NX failed (key existed)."""
        if self.raise_on_next_set is not None:
            exc = self.raise_on_next_set
            self.raise_on_next_set = None
            raise exc
        if nx and key in self._store:
            return None  # key already exists — NX failure
        self._store[key] = value
        return True

    async def delete(self, key: str) -> int:
        """Simulate TTL expiry by explicitly deleting a key."""
        return self._store.pop(key, None) and 1 or 0

    async def aclose(self):
        self._closed = True


def _fake_redis() -> _FakeRedis:
    return _FakeRedis()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_notification_sends_and_marks():
    """is_duplicate returns False on first call and sets the key."""
    from lia_messaging.notification_dedup import build_idempotency_key, is_duplicate

    redis = _fake_redis()
    key = build_idempotency_key(
        event_type="screening_completed",
        user_id="user-abc",
        company_id="co-xyz",
        title="Triagem concluída",
        message="Candidato aprovado",
    )
    result = await is_duplicate(key, ttl_seconds=3600, _redis=redis)

    assert result is False, "First send should NOT be a duplicate"
    # Key must be present in the fake store
    redis_key = f"notif_sent:{key}"
    assert redis_key in redis._store, "Key must be marked in Redis after first send"


@pytest.mark.asyncio
async def test_duplicate_within_ttl_is_skipped():
    """Second call with same inputs within TTL returns True (is a duplicate)."""
    from lia_messaging.notification_dedup import build_idempotency_key, is_duplicate

    redis = _fake_redis()
    key = build_idempotency_key(
        event_type="new_application",
        user_id="recruiter-1",
        company_id="co-1",
        title="Nova candidatura",
        message="João Silva aplicou para Dev Sênior",
    )

    first = await is_duplicate(key, ttl_seconds=86400, _redis=redis)
    second = await is_duplicate(key, ttl_seconds=86400, _redis=redis)

    assert first is False, "First call must not be a duplicate"
    assert second is True, "Second call within TTL must be a duplicate"


@pytest.mark.asyncio
async def test_different_event_type_not_duplicate():
    """Same user+company+content but different event_type => different key, not a dup."""
    from lia_messaging.notification_dedup import build_idempotency_key, is_duplicate

    redis = _fake_redis()
    common = dict(
        user_id="user-1",
        company_id="co-1",
        title="Atualização",
        message="Alguma coisa aconteceu",
    )
    key_a = build_idempotency_key(event_type="screening_completed", **common)
    key_b = build_idempotency_key(event_type="new_application", **common)

    assert key_a != key_b, "Keys must differ by event_type"

    await is_duplicate(key_a, ttl_seconds=3600, _redis=redis)
    result_b = await is_duplicate(key_b, ttl_seconds=3600, _redis=redis)

    assert result_b is False, "Different event_type must not be treated as duplicate"


@pytest.mark.asyncio
async def test_different_candidate_not_duplicate():
    """Same event+company+title but different user_id => different key, not a dup."""
    from lia_messaging.notification_dedup import build_idempotency_key, is_duplicate

    redis = _fake_redis()
    common = dict(
        event_type="candidates_added",
        company_id="co-1",
        title="5 candidatos adicionados",
        message="Novos candidatos no pipeline",
    )
    key_alice = build_idempotency_key(user_id="recruiter-alice", **common)
    key_bob = build_idempotency_key(user_id="recruiter-bob", **common)

    assert key_alice != key_bob, "Keys must differ by user_id"

    await is_duplicate(key_alice, ttl_seconds=3600, _redis=redis)
    result_bob = await is_duplicate(key_bob, ttl_seconds=3600, _redis=redis)

    assert result_bob is False, "Different user_id must not be treated as duplicate"


@pytest.mark.asyncio
async def test_after_ttl_can_resend():
    """Simulating TTL expiry: after deleting the key a re-send is allowed."""
    from lia_messaging.notification_dedup import build_idempotency_key, is_duplicate, _redis_key

    redis = _fake_redis()
    key = build_idempotency_key(
        event_type="morning_briefing",
        user_id="recruiter-2",
        company_id="co-2",
        title="Bom dia!",
        message="Resumo do dia",
    )

    first = await is_duplicate(key, ttl_seconds=1, _redis=redis)
    assert first is False

    # Simulate TTL expiry by manually removing the key
    rkey = _redis_key(key)
    await redis.delete(rkey)

    # After TTL expiry re-send must be allowed
    after_ttl = await is_duplicate(key, ttl_seconds=1, _redis=redis)
    assert after_ttl is False, "After TTL expiry a re-send must be allowed"


@pytest.mark.asyncio
async def test_redis_unavailable_fail_open():
    """When Redis raises an exception, is_duplicate returns False (fail-open)."""
    from lia_messaging.notification_dedup import build_idempotency_key, is_duplicate

    redis = _fake_redis()
    redis.raise_on_next_set = ConnectionError("Redis is down")

    key = build_idempotency_key(
        event_type="vacancy_expiring",
        user_id="u-1",
        company_id="c-1",
        title="Vaga expirando",
        message="A vaga X expira amanhã",
    )

    result = await is_duplicate(key, ttl_seconds=3600, _redis=redis)
    assert result is False, "Redis error must fail-open (allow send)"


def test_build_idempotency_key_is_deterministic():
    """build_idempotency_key is a pure function — same inputs always produce same key."""
    from lia_messaging.notification_dedup import build_idempotency_key

    inputs = dict(
        event_type="calibration_needed",
        user_id="recruiter-x",
        company_id="co-y",
        title="Calibração necessária",
        message="Por favor calibre a vaga Z",
    )

    k1 = build_idempotency_key(**inputs)
    k2 = build_idempotency_key(**inputs)

    assert k1 == k2, "Same inputs must always produce the same idempotency key"
    assert len(k1) == 64, "SHA-256 hex digest must be 64 chars"


def test_build_idempotency_key_different_message_produces_different_key():
    """Different message text => different key (allows re-sending with new content)."""
    from lia_messaging.notification_dedup import build_idempotency_key

    common = dict(event_type="info", user_id="u1", company_id="c1", title="Título")
    key_a = build_idempotency_key(**common, message="Mensagem A")
    key_b = build_idempotency_key(**common, message="Mensagem B")

    assert key_a != key_b, "Different message must produce different idempotency key"
