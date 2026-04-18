"""Regression tests for ADR 003 / Task #472 — idempotency keys for dual-ID
entities must collapse retries that switch between fork UUID and Rails
bigint onto the same fingerprint, so the operation does not run twice.

Tested at two levels:
- Unit: a stub adapter exercises the canonicalization branch in
  `ContextManager._canonicalize_params` directly.
- Integration: the real `RailsAdapter._resolve_rails_candidate_id` is
  driven through `generate_idempotency_key_async`, with the network call
  out (`WeDOTalentATSClient.find_candidate_by_fork_uuid`) replaced by a
  fake so the test stays hermetic but still exercises the production
  resolver code path.
"""
import os
import sys
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.shared.robustness.context_management import ContextManager
from app.domains.integrations_hub.services.rails_adapter import RailsAdapter


# ---------------------------------------------------------------- unit


class _StubResolver:
    """Minimal duck-typed adapter — only `_resolve_rails_candidate_id`
    matters for the canonicalization map."""

    def __init__(self, uuid_to_rails: dict[str, int]):
        self._mapping = {k.lower(): v for k, v in uuid_to_rails.items()}

    async def _resolve_rails_candidate_id(self, candidate_id: str) -> int | None:
        if candidate_id and candidate_id.isdigit():
            return int(candidate_id)
        if candidate_id and len(candidate_id) == 36:
            return self._mapping.get(candidate_id.lower())
        return None


@pytest.mark.asyncio
async def test_candidate_uuid_and_bigint_collapse_to_same_idempotency_key():
    """Spec-mandated regression: UUID retry and bigint retry of the same
    candidate operation hash to the same idempotency key."""
    rails_id = 4242
    fork_uuid = "11111111-2222-3333-4444-555555555555"
    adapter = _StubResolver({fork_uuid: rails_id})
    ctx = ContextManager(session_id="sess-1", user_id="user-1")

    key_uuid = await ctx.generate_idempotency_key_async(
        "update_candidate", {"candidate_id": fork_uuid, "stage": "screening"}, adapter
    )
    key_bigint = await ctx.generate_idempotency_key_async(
        "update_candidate",
        {"candidate_id": str(rails_id), "stage": "screening"},
        adapter,
    )

    assert key_uuid == key_bigint
    # And the second one is correctly detected as a duplicate.
    assert ctx.check_idempotency(key_uuid) is True
    assert ctx.check_idempotency(key_bigint) is False


@pytest.mark.asyncio
async def test_unrelated_params_still_differentiate_keys():
    """Canonicalization must not over-collapse — different operations or
    different non-ID params still produce different keys."""
    adapter = _StubResolver({})
    ctx = ContextManager(session_id="sess-1", user_id="user-1")

    key_a = await ctx.generate_idempotency_key_async(
        "update_candidate", {"candidate_id": "100", "stage": "screening"}, adapter
    )
    key_b = await ctx.generate_idempotency_key_async(
        "update_candidate", {"candidate_id": "100", "stage": "interview"}, adapter
    )
    key_c = await ctx.generate_idempotency_key_async(
        "update_candidate", {"candidate_id": "101", "stage": "screening"}, adapter
    )

    assert key_a != key_b
    assert key_a != key_c


@pytest.mark.asyncio
async def test_uuid_only_entity_unaffected_when_no_resolver_matches():
    """For params without a registered dual-ID resolver, the value passes
    through verbatim — no behavior change vs. the legacy hashing."""
    adapter = _StubResolver({})
    ctx = ContextManager(session_id="sess-1", user_id="user-1")
    fork_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    key_with_adapter = await ctx.generate_idempotency_key_async(
        "publish_event", {"session_uuid": fork_uuid}, adapter
    )
    key_without_adapter = await ctx.generate_idempotency_key_async(
        "publish_event", {"session_uuid": fork_uuid}, None
    )
    key_sync = ctx.generate_idempotency_key(
        "publish_event", {"session_uuid": fork_uuid}
    )

    assert key_with_adapter == key_without_adapter == key_sync


@pytest.mark.asyncio
async def test_unresolvable_uuid_passes_through_verbatim():
    """When Rails has no `fork_uuid` row yet (resolver returns None), we
    keep the original UUID. The two ID formats won't collapse — but that
    is the best we can do until the backfill completes, and the behavior
    is no worse than before this fix."""
    adapter = _StubResolver({})
    ctx = ContextManager(session_id="sess-1", user_id="user-1")
    fork_uuid = "99999999-2222-3333-4444-555555555555"

    key_uuid = await ctx.generate_idempotency_key_async(
        "update_candidate", {"candidate_id": fork_uuid}, adapter
    )
    key_bigint = await ctx.generate_idempotency_key_async(
        "update_candidate", {"candidate_id": "777"}, adapter
    )

    assert key_uuid != key_bigint


@pytest.mark.asyncio
async def test_sync_method_unchanged_for_simple_params():
    """The legacy sync `generate_idempotency_key` keeps its previous
    semantics — no surprise behavior change for current callers."""
    ctx = ContextManager(session_id="sess-1", user_id="user-1")
    key1 = ctx.generate_idempotency_key("create_job", {"title": "Dev"})
    key2 = ctx.generate_idempotency_key("create_job", {"title": "Dev"})
    assert key1 == key2
    assert ctx.check_idempotency(key1) is True
    assert ctx.check_idempotency(key2) is False


# ---------------------------------------------------------------- integration


@pytest.mark.asyncio
async def test_real_rails_adapter_collapses_uuid_and_bigint(monkeypatch):
    """Integration-style: drive the real `RailsAdapter` resolver through
    `generate_idempotency_key_async`. The Rails HTTP call out is mocked so
    the test stays hermetic, but the adapter's UUID-detection /
    fork_uuid-lookup / bigint-passthrough logic runs for real."""
    rails_id = 9001
    fork_uuid = "deadbeef-1234-5678-9abc-def012345678"

    adapter = RailsAdapter(db=None, rails_token="test-token")

    # Force `_get_rails_client` to return a fake client whose fork_uuid
    # lookup returns the Rails record. The real adapter calls
    # `client.find_candidate_by_fork_uuid(uuid)` — match that surface.
    fake_client = AsyncMock()
    fake_client.find_candidate_by_fork_uuid = AsyncMock(
        return_value={"id": rails_id, "fork_uuid": fork_uuid}
    )

    async def _fake_get_client():
        return fake_client

    monkeypatch.setattr(adapter, "_get_rails_client", _fake_get_client)

    ctx = ContextManager(session_id="sess-int", user_id="user-int")

    key_from_uuid = await ctx.generate_idempotency_key_async(
        "update_candidate",
        {"candidate_id": fork_uuid, "field": "stage"},
        adapter,
    )
    key_from_bigint = await ctx.generate_idempotency_key_async(
        "update_candidate",
        {"candidate_id": str(rails_id), "field": "stage"},
        adapter,
    )

    assert key_from_uuid == key_from_bigint
    # The UUID branch hits Rails; the bigint branch must NOT (it should be
    # resolved locally by `_to_rails_id` and short-circuit).
    assert fake_client.find_candidate_by_fork_uuid.await_count == 1

    # End-to-end safety: feeding both keys into the same context's
    # idempotency set means the second call is rejected as duplicate.
    assert ctx.check_idempotency(key_from_uuid) is True
    assert ctx.check_idempotency(key_from_bigint) is False
