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
    """Minimal duck-typed adapter — exposes the dual-ID resolvers the
    canonicalization map looks up (candidate / job / application)."""

    def __init__(
        self,
        uuid_to_rails: dict[str, int] | None = None,
        job_uuid_to_rails: dict[str, int] | None = None,
        application_uuid_to_rails: dict[str, int] | None = None,
    ):
        self._mapping = {k.lower(): v for k, v in (uuid_to_rails or {}).items()}
        self._job_mapping = {
            k.lower(): v for k, v in (job_uuid_to_rails or {}).items()
        }
        self._application_mapping = {
            k.lower(): v for k, v in (application_uuid_to_rails or {}).items()
        }

    @staticmethod
    def _resolve(value: str, mapping: dict[str, int]) -> int | None:
        if value and value.isdigit():
            return int(value)
        if value and len(value) == 36:
            return mapping.get(value.lower())
        return None

    async def _resolve_rails_candidate_id(self, candidate_id: str) -> int | None:
        return self._resolve(candidate_id, self._mapping)

    async def _resolve_rails_job_id(self, job_id: str) -> int | None:
        return self._resolve(job_id, self._job_mapping)

    async def _resolve_rails_application_id(self, application_id: str) -> int | None:
        return self._resolve(application_id, self._application_mapping)


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
@pytest.mark.parametrize(
    "param_key,kwarg_name",
    [
        ("job_id", "job_uuid_to_rails"),
        ("vacancy_id", "job_uuid_to_rails"),
        ("application_id", "application_uuid_to_rails"),
        ("apply_id", "application_uuid_to_rails"),
    ],
)
async def test_dual_id_uuid_and_bigint_collapse_for_jobs_and_applications(
    param_key: str, kwarg_name: str
):
    """Task #479 — UUID retry and bigint retry of the same job/application
    operation hash to the same idempotency key."""
    rails_id = 7654
    fork_uuid = "abcdef01-2345-6789-abcd-ef0123456789"
    adapter = _StubResolver(**{kwarg_name: {fork_uuid: rails_id}})
    ctx = ContextManager(session_id="sess-2", user_id="user-2")

    key_uuid = await ctx.generate_idempotency_key_async(
        "update_entity", {param_key: fork_uuid, "field": "stage"}, adapter
    )
    key_bigint = await ctx.generate_idempotency_key_async(
        "update_entity", {param_key: str(rails_id), "field": "stage"}, adapter
    )

    assert key_uuid == key_bigint
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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "param_key,client_method,resolver_attr",
    [
        ("job_id", "find_job_by_fork_uuid", "_resolve_rails_job_id"),
        ("vacancy_id", "find_job_by_fork_uuid", "_resolve_rails_job_id"),
        (
            "application_id",
            "find_application_by_fork_uuid",
            "_resolve_rails_application_id",
        ),
        (
            "apply_id",
            "find_application_by_fork_uuid",
            "_resolve_rails_application_id",
        ),
    ],
)
async def test_real_rails_adapter_collapses_uuid_and_bigint_for_dual_id_entities(
    monkeypatch, param_key: str, client_method: str, resolver_attr: str
):
    """Task #479 integration-style: drive the real `RailsAdapter` job and
    application resolvers through `generate_idempotency_key_async`. Rails
    HTTP is mocked but the adapter's UUID detection / fork_uuid lookup /
    bigint passthrough runs for real."""
    rails_id = 4242
    fork_uuid = "feedface-1111-2222-3333-444455556666"

    adapter = RailsAdapter(db=None, rails_token="test-token")

    fake_client = AsyncMock()
    setattr(
        fake_client,
        client_method,
        AsyncMock(return_value={"id": rails_id, "fork_uuid": fork_uuid}),
    )

    async def _fake_get_client():
        return fake_client

    monkeypatch.setattr(adapter, "_get_rails_client", _fake_get_client)

    # Sanity-check the resolver is wired up on the real adapter.
    assert callable(getattr(adapter, resolver_attr))

    ctx = ContextManager(session_id="sess-int-2", user_id="user-int-2")

    key_from_uuid = await ctx.generate_idempotency_key_async(
        "update_entity", {param_key: fork_uuid, "field": "x"}, adapter
    )
    key_from_bigint = await ctx.generate_idempotency_key_async(
        "update_entity", {param_key: str(rails_id), "field": "x"}, adapter
    )

    assert key_from_uuid == key_from_bigint
    assert getattr(fake_client, client_method).await_count == 1

    assert ctx.check_idempotency(key_from_uuid) is True
    assert ctx.check_idempotency(key_from_bigint) is False


# ---------------------------------------------------------------- CRUD wiring
#
# Task #484 — RailsAdapter CRUD methods (get_job/update_job/delete_job/
# get_apply/update_apply/create_apply/list_selective_processes/list_messages/
# send_message) must route IDs through the new dual-ID resolvers so a fork
# UUID is transparently translated to the Rails bigint instead of being
# silently dropped as a "non-integer ID".


def _fake_client_with_lookup(lookup_attr: str, rails_id: int) -> AsyncMock:
    """Build an AsyncMock client with a fork_uuid lookup that returns a
    Rails record. Other methods default to AsyncMock too."""
    fake_client = AsyncMock()
    setattr(
        fake_client,
        lookup_attr,
        AsyncMock(return_value={"id": rails_id, "fork_uuid": "x"}),
    )
    return fake_client


def _patch_client(monkeypatch, adapter: RailsAdapter, fake_client: AsyncMock) -> None:
    async def _fake_get_client():
        return fake_client

    monkeypatch.setattr(adapter, "_get_rails_client", _fake_get_client)


@pytest.mark.asyncio
async def test_update_job_translates_fork_uuid_to_bigint(monkeypatch):
    rails_id = 5150
    fork_uuid = "deadbeef-aaaa-bbbb-cccc-1234567890ab"
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = _fake_client_with_lookup("find_job_by_fork_uuid", rails_id)
    fake_client.update_job = AsyncMock(return_value={"id": rails_id, "title": "x"})
    _patch_client(monkeypatch, adapter, fake_client)

    result = await adapter.update_job(fork_uuid, {"title": "new"})

    assert result is not None
    assert result["rails_id"] == rails_id
    fake_client.find_job_by_fork_uuid.assert_awaited_once_with(fork_uuid)
    fake_client.update_job.assert_awaited_once()
    sent_id, sent_payload = fake_client.update_job.await_args.args
    assert sent_id == rails_id
    assert sent_payload == {"title": "new"}


@pytest.mark.asyncio
async def test_update_job_with_bigint_skips_lookup(monkeypatch):
    rails_id = 99
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = _fake_client_with_lookup("find_job_by_fork_uuid", rails_id)
    fake_client.update_job = AsyncMock(return_value={"id": rails_id})
    _patch_client(monkeypatch, adapter, fake_client)

    result = await adapter.update_job(str(rails_id), {"title": "x"})

    assert result is not None
    fake_client.find_job_by_fork_uuid.assert_not_awaited()
    fake_client.update_job.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_apply_translates_fork_uuid_to_bigint(monkeypatch):
    rails_id = 321
    fork_uuid = "feedface-1111-2222-3333-444455556666"
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = _fake_client_with_lookup("find_application_by_fork_uuid", rails_id)
    fake_client.get_apply = AsyncMock(
        return_value={"id": rails_id, "candidate_id": 1, "job_id": 2}
    )
    _patch_client(monkeypatch, adapter, fake_client)

    result = await adapter.get_apply(fork_uuid)

    assert result is not None
    assert result["rails_id"] == rails_id
    fake_client.find_application_by_fork_uuid.assert_awaited_once_with(fork_uuid)
    fake_client.get_apply.assert_awaited_once_with(rails_id)


@pytest.mark.asyncio
async def test_update_apply_translates_fork_uuid_to_bigint(monkeypatch):
    rails_id = 654
    fork_uuid = "feedface-1111-2222-3333-444455556666"
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = _fake_client_with_lookup("find_application_by_fork_uuid", rails_id)
    fake_client.update_apply = AsyncMock(
        return_value={"id": rails_id, "candidate_id": 1, "job_id": 2}
    )
    _patch_client(monkeypatch, adapter, fake_client)

    result = await adapter.update_apply(fork_uuid, {"selective_process_id": 3})

    assert result is not None
    assert result["rails_id"] == rails_id
    fake_client.find_application_by_fork_uuid.assert_awaited_once_with(fork_uuid)
    fake_client.update_apply.assert_awaited_once_with(
        rails_id, {"selective_process_id": 3}
    )


@pytest.mark.asyncio
async def test_unresolvable_fork_uuid_returns_none_without_calling_rails(monkeypatch):
    """When the fork_uuid lookup yields nothing, the CRUD method must not
    invoke the actual Rails write — it returns None like before."""
    fork_uuid = "00000000-0000-0000-0000-000000000000"
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = AsyncMock()
    fake_client.find_application_by_fork_uuid = AsyncMock(return_value=None)
    fake_client.update_apply = AsyncMock()
    _patch_client(monkeypatch, adapter, fake_client)

    result = await adapter.update_apply(fork_uuid, {"x": 1})

    assert result is None
    fake_client.update_apply.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_job_translates_fork_uuid_to_bigint(monkeypatch):
    rails_id = 808
    fork_uuid = "deadbeef-1010-2020-3030-404050506060"
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = _fake_client_with_lookup("find_job_by_fork_uuid", rails_id)
    fake_client.delete_job = AsyncMock(return_value=True)
    _patch_client(monkeypatch, adapter, fake_client)

    assert await adapter.delete_job(fork_uuid) is True
    fake_client.find_job_by_fork_uuid.assert_awaited_once_with(fork_uuid)
    fake_client.delete_job.assert_awaited_once_with(rails_id)


@pytest.mark.asyncio
async def test_delete_job_unresolvable_uuid_returns_false(monkeypatch):
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = AsyncMock()
    fake_client.find_job_by_fork_uuid = AsyncMock(return_value=None)
    fake_client.delete_job = AsyncMock()
    _patch_client(monkeypatch, adapter, fake_client)

    assert await adapter.delete_job("11111111-2222-3333-4444-555555555555") is False
    fake_client.delete_job.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_apply_translates_both_fork_uuids(monkeypatch):
    cand_rails_id = 11
    job_rails_id = 22
    cand_uuid = "aaaaaaaa-1111-2222-3333-444444444444"
    job_uuid = "bbbbbbbb-1111-2222-3333-444444444444"
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = AsyncMock()
    fake_client.find_candidate_by_fork_uuid = AsyncMock(
        return_value={"id": cand_rails_id}
    )
    fake_client.find_job_by_fork_uuid = AsyncMock(
        return_value={"id": job_rails_id}
    )
    fake_client.create_apply = AsyncMock(
        return_value={"id": 999, "candidate_id": cand_rails_id, "job_id": job_rails_id}
    )
    _patch_client(monkeypatch, adapter, fake_client)

    result = await adapter.create_apply(cand_uuid, job_uuid)
    assert result is not None
    fake_client.create_apply.assert_awaited_once_with(cand_rails_id, job_rails_id)


@pytest.mark.asyncio
async def test_create_apply_skipped_when_either_id_unresolvable(monkeypatch):
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = AsyncMock()
    fake_client.find_candidate_by_fork_uuid = AsyncMock(return_value=None)
    fake_client.find_job_by_fork_uuid = AsyncMock(return_value={"id": 1})
    fake_client.create_apply = AsyncMock()
    _patch_client(monkeypatch, adapter, fake_client)

    result = await adapter.create_apply(
        "aaaaaaaa-1111-2222-3333-444444444444",
        "bbbbbbbb-1111-2222-3333-444444444444",
    )
    assert result is None
    fake_client.create_apply.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_selective_processes_translates_fork_uuid(monkeypatch):
    rails_id = 7
    fork_uuid = "ccccdddd-1111-2222-3333-444444444444"
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = _fake_client_with_lookup("find_job_by_fork_uuid", rails_id)
    fake_client.list_selective_processes = AsyncMock(
        return_value=[{"id": 100, "name": "Triagem", "job_id": rails_id}]
    )
    _patch_client(monkeypatch, adapter, fake_client)

    out = await adapter.list_selective_processes(job_id=fork_uuid)
    assert len(out) == 1
    fake_client.list_selective_processes.assert_awaited_once_with(job_id=rails_id)


@pytest.mark.asyncio
async def test_list_selective_processes_unresolvable_uuid_returns_empty(monkeypatch):
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = AsyncMock()
    fake_client.find_job_by_fork_uuid = AsyncMock(return_value=None)
    fake_client.list_selective_processes = AsyncMock()
    _patch_client(monkeypatch, adapter, fake_client)

    out = await adapter.list_selective_processes(
        job_id="11111111-2222-3333-4444-555555555555"
    )
    assert out == []
    fake_client.list_selective_processes.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "reference_type,lookup_attr",
    [
        ("Job", "find_job_by_fork_uuid"),
        ("Apply", "find_application_by_fork_uuid"),
        ("Candidate", "find_candidate_by_fork_uuid"),
    ],
)
async def test_list_messages_resolves_reference_id_by_type(
    monkeypatch, reference_type: str, lookup_attr: str
):
    rails_id = 4242
    fork_uuid = "feedbeef-1111-2222-3333-444444444444"
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = _fake_client_with_lookup(lookup_attr, rails_id)
    fake_client.list_messages = AsyncMock(
        return_value=[{"id": 1, "content": "hi", "reference_id": rails_id}]
    )
    _patch_client(monkeypatch, adapter, fake_client)

    out = await adapter.list_messages(
        reference_type=reference_type, reference_id=fork_uuid
    )
    assert len(out) == 1
    getattr(fake_client, lookup_attr).assert_awaited_once_with(fork_uuid)
    fake_client.list_messages.assert_awaited_once_with(
        page=1, limit=30, reference_type=reference_type, reference_id=rails_id
    )


@pytest.mark.asyncio
async def test_list_messages_unknown_reference_type_falls_back_to_bigint(monkeypatch):
    """Unknown reference_type must keep the legacy bigint passthrough so
    integer IDs continue to work and never trigger a fork_uuid lookup."""
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = AsyncMock()
    fake_client.find_job_by_fork_uuid = AsyncMock()
    fake_client.find_application_by_fork_uuid = AsyncMock()
    fake_client.find_candidate_by_fork_uuid = AsyncMock()
    fake_client.list_messages = AsyncMock(return_value=[])
    _patch_client(monkeypatch, adapter, fake_client)

    out = await adapter.list_messages(reference_type="SomethingElse", reference_id="42")
    assert out == []
    fake_client.find_job_by_fork_uuid.assert_not_awaited()
    fake_client.find_application_by_fork_uuid.assert_not_awaited()
    fake_client.find_candidate_by_fork_uuid.assert_not_awaited()
    fake_client.list_messages.assert_awaited_once_with(
        page=1, limit=30, reference_type="SomethingElse", reference_id=42
    )


@pytest.mark.asyncio
async def test_send_message_resolves_apply_reference_uuid(monkeypatch):
    rails_id = 555
    fork_uuid = "feedface-9999-8888-7777-666655554444"
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = _fake_client_with_lookup("find_application_by_fork_uuid", rails_id)
    fake_client.send_message = AsyncMock(
        return_value={"id": 1, "content": "ok", "reference_id": rails_id}
    )
    _patch_client(monkeypatch, adapter, fake_client)

    result = await adapter.send_message(
        content="ok", reference_type="apply", reference_id=fork_uuid
    )
    assert result is not None
    fake_client.find_application_by_fork_uuid.assert_awaited_once_with(fork_uuid)
    sent_kwargs = fake_client.send_message.await_args.kwargs
    assert sent_kwargs["reference_id"] == rails_id


@pytest.mark.asyncio
async def test_send_message_unknown_type_falls_back_to_bigint(monkeypatch):
    adapter = RailsAdapter(db=None, rails_token="test-token")
    fake_client = AsyncMock()
    fake_client.send_message = AsyncMock(return_value={"id": 1})
    _patch_client(monkeypatch, adapter, fake_client)

    result = await adapter.send_message(
        content="hi", reference_type="ChatRoom", reference_id="7"
    )
    assert result is not None
    sent_kwargs = fake_client.send_message.await_args.kwargs
    assert sent_kwargs["reference_id"] == 7
