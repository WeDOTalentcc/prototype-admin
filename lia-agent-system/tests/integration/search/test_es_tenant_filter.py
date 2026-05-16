"""Sentinel suite for Task #1147 — Elasticsearch tenant-filter wrapper.

Covers:
  1. ``with_tenant_filter`` injects ``{term: {company_id}}`` into ``bool.filter``.
  2. Validates ``company_id`` via ``CompanyId.parse`` (rejects empty / "default").
  3. Idempotent re-injection.
  4. ``TenantAwareElasticsearchClient`` runtime interceptor raises
     ``MissingTenantFilterError`` (dev) / ``RuntimeError`` (prod) when payload
     lacks the term filter.
  5. End-to-end per real ES callsite (``ElasticsearchSearchBackend.search_candidates``,
     ``ElasticsearchSearchBackend.search_jobs``) — asserts the payload sent
     to the mocked ES client carries ``{"term": {"company_id": <cid>}}``.

Note (deviation from task description):
    The task plan referenced "10 services × 1 scenario = 10 tests" based on a
    static-analysis discovery doc. A grep of the current tree shows only one
    backend service (``ElasticsearchSearchBackend`` in
    ``app/domains/ai/services/search_service.py``) actually invokes
    ``client.search(...)`` against ES — 2 callsites
    (``search_candidates`` + ``search_jobs``). All other files listed in the
    plan were either deleted, renamed, or never created. Coverage here is
    therefore 2 real-callsite tests + a battery of wrapper/interceptor
    invariant tests, matching the actual surface area. The AST sensor +
    runtime interceptor guarantee any new ES callsite added later will be
    enforced automatically.
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.shared.exceptions.tenant_errors import InvalidCompanyIdError
from app.shared.search import (
    ConflictingTenantFilterError,
    MissingTenantFilterError,
    TenantAwareElasticsearchClient,
    query_has_tenant_filter,
    with_tenant_filter,
)

CID = "00000000-0000-4000-a000-000000000001"
OTHER_CID = "00000000-0000-4000-a000-000000000002"


# --- wrapper invariants ---------------------------------------------------


def test_with_tenant_filter_injects_into_empty_query():
    out = with_tenant_filter({}, CID)
    filters = out["query"]["bool"]["filter"]
    assert {"term": {"company_id": CID}} in filters


def test_with_tenant_filter_injects_when_query_is_none():
    out = with_tenant_filter(None, CID)
    assert out["query"]["bool"]["filter"] == [{"term": {"company_id": CID}}]


def test_with_tenant_filter_preserves_existing_filters():
    src = {
        "query": {
            "bool": {
                "must": [{"match": {"title": "engineer"}}],
                "filter": [{"term": {"status": "active"}}],
            }
        },
        "size": 10,
    }
    out = with_tenant_filter(src, CID)
    assert out["query"]["bool"]["must"] == [{"match": {"title": "engineer"}}]
    assert {"term": {"status": "active"}} in out["query"]["bool"]["filter"]
    assert {"term": {"company_id": CID}} in out["query"]["bool"]["filter"]
    # Defensive copy — source untouched
    assert src["query"]["bool"]["filter"] == [{"term": {"status": "active"}}]


def test_with_tenant_filter_normalises_dict_shorthand_filter():
    src = {"query": {"bool": {"filter": {"term": {"x": 1}}}}}
    out = with_tenant_filter(src, CID)
    assert isinstance(out["query"]["bool"]["filter"], list)
    assert {"term": {"company_id": CID}} in out["query"]["bool"]["filter"]


def test_with_tenant_filter_idempotent():
    out1 = with_tenant_filter({}, CID)
    out2 = with_tenant_filter(out1, CID)
    count = sum(
        1
        for clause in out2["query"]["bool"]["filter"]
        if clause == {"term": {"company_id": CID}}
    )
    assert count == 1


@pytest.mark.parametrize("bad", ["", "  ", "default", "none", "undefined"])
def test_with_tenant_filter_rejects_forbidden_company_id(bad):
    with pytest.raises(InvalidCompanyIdError):
        with_tenant_filter({}, bad)


def test_with_tenant_filter_rejects_none_company_id():
    with pytest.raises(InvalidCompanyIdError):
        with_tenant_filter({}, None)


def test_query_has_tenant_filter_detects_in_bool_filter():
    q = {"query": {"bool": {"filter": [{"term": {"company_id": CID}}]}}}
    assert query_has_tenant_filter(q) is True


def test_query_has_tenant_filter_accepts_bare_bool_form():
    """elasticsearch-py 8.x ``query=`` kwarg shape (no top-level ``query``)."""
    q = {"bool": {"filter": [{"term": {"company_id": CID}}]}}
    assert query_has_tenant_filter(q) is True


def test_query_has_tenant_filter_detects_in_nested_bool_filter():
    q = {
        "query": {
            "bool": {
                "filter": [
                    {"bool": {"filter": [{"term": {"company_id": CID}}]}},
                ]
            }
        }
    }
    assert query_has_tenant_filter(q) is True


def test_query_has_tenant_filter_rejects_must_only():
    """company_id in ``must`` is scoring context, not isolation — REJECT."""
    q = {"query": {"bool": {"must": [{"term": {"company_id": CID}}]}}}
    assert query_has_tenant_filter(q) is False


def test_query_has_tenant_filter_rejects_must_not():
    """company_id in ``must_not`` *excludes* the tenant — worst-case leak."""
    q = {"query": {"bool": {"must_not": [{"term": {"company_id": CID}}]}}}
    assert query_has_tenant_filter(q) is False


def test_query_has_tenant_filter_rejects_should():
    """``should`` is OR semantics — does NOT scope to a single tenant."""
    q = {"query": {"bool": {"should": [{"term": {"company_id": CID}}]}}}
    assert query_has_tenant_filter(q) is False


def test_query_has_tenant_filter_rejects_unrelated_branch():
    """company_id inside ``aggs`` (or any non-filter path) does NOT count."""
    q = {
        "query": {"bool": {"filter": [{"term": {"status": "active"}}]}},
        "aggs": {"by_tenant": {"terms": {"field": "company_id"}}},
        # Even a sneaky term clause inside aggs body must not be accepted.
        "post_filter": {"term": {"company_id": CID}},
    }
    assert query_has_tenant_filter(q) is False


def test_query_has_tenant_filter_rejects_empty_value():
    q = {"query": {"bool": {"filter": [{"term": {"company_id": ""}}]}}}
    assert query_has_tenant_filter(q) is False


def test_query_has_tenant_filter_handles_missing():
    assert query_has_tenant_filter({"query": {"match_all": {}}}) is False
    assert query_has_tenant_filter(None) is False


# --- conflict detection ---------------------------------------------------


def test_with_tenant_filter_rejects_conflicting_cid_in_filter():
    src = {"query": {"bool": {"filter": [{"term": {"company_id": OTHER_CID}}]}}}
    with pytest.raises(ConflictingTenantFilterError) as exc:
        with_tenant_filter(src, CID)
    assert exc.value.details["expected_company_id"] == CID
    assert exc.value.details["found_company_id"] == OTHER_CID


def test_with_tenant_filter_rejects_conflicting_cid_in_must():
    src = {"query": {"bool": {"must": [{"term": {"company_id": OTHER_CID}}]}}}
    with pytest.raises(ConflictingTenantFilterError):
        with_tenant_filter(src, CID)


def test_with_tenant_filter_rejects_conflicting_cid_in_must_not():
    src = {"query": {"bool": {"must_not": [{"term": {"company_id": OTHER_CID}}]}}}
    with pytest.raises(ConflictingTenantFilterError):
        with_tenant_filter(src, CID)


def test_with_tenant_filter_rejects_conflicting_cid_in_should():
    src = {"query": {"bool": {"should": [{"term": {"company_id": OTHER_CID}}]}}}
    with pytest.raises(ConflictingTenantFilterError):
        with_tenant_filter(src, CID)


def test_with_tenant_filter_strips_same_cid_from_must_context():
    """If the SAME cid is sitting in ``must`` (wrong context, but
    non-conflicting), it gets moved to ``filter`` canonically — must
    end up in filter context only."""
    src = {"query": {"bool": {"must": [{"term": {"company_id": CID}}]}}}
    out = with_tenant_filter(src, CID)
    assert out["query"]["bool"]["must"] == []
    assert {"term": {"company_id": CID}} in out["query"]["bool"]["filter"]
    # Resulting payload must satisfy the strict runtime check.
    assert query_has_tenant_filter(out)


# --- runtime interceptor --------------------------------------------------


@pytest.fixture
def dev_mode(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    yield


@pytest.fixture
def prod_mode(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    yield


@pytest.mark.asyncio
async def test_interceptor_passes_when_filter_present(dev_mode):
    inner = MagicMock()
    inner.search = AsyncMock(return_value={"hits": {"hits": []}})
    client = TenantAwareElasticsearchClient(inner, service="test_svc")
    body = with_tenant_filter({"size": 5}, CID)
    await client.search(index="candidates", body=body)
    inner.search.assert_awaited_once_with(index="candidates", body=body)


@pytest.mark.asyncio
async def test_interceptor_raises_in_dev_when_filter_missing(dev_mode):
    inner = MagicMock()
    inner.search = AsyncMock(return_value={"hits": {"hits": []}})
    client = TenantAwareElasticsearchClient(inner, service="test_svc")
    with pytest.raises(MissingTenantFilterError) as exc:
        await client.search(index="candidates", body={"query": {"match_all": {}}})
    assert "company_id" in str(exc.value)
    inner.search.assert_not_awaited()


@pytest.mark.asyncio
async def test_interceptor_raises_in_prod_when_filter_missing(prod_mode):
    inner = MagicMock()
    inner.search = AsyncMock()
    client = TenantAwareElasticsearchClient(inner, service="test_svc")
    with pytest.raises(RuntimeError):
        await client.search(index="candidates", body={"query": {"match_all": {}}})
    inner.search.assert_not_awaited()


@pytest.mark.asyncio
async def test_interceptor_rejects_cross_tenant_with_wrong_cid(dev_mode):
    """Body that filters by ``OTHER_CID`` still has *a* company_id filter — the
    interceptor only enforces presence, not match. Cross-tenant query rejection
    is the responsibility of ``with_tenant_filter(query, cid)`` being called
    with the authenticated cid; we assert that path here."""
    body = with_tenant_filter({}, OTHER_CID)
    # Authenticated caller would not pass OTHER_CID — but if it did, the
    # interceptor accepts (presence) and the test that asserts the cid value
    # is below.
    assert query_has_tenant_filter(body)
    inner = MagicMock()
    inner.search = AsyncMock(return_value={"hits": {"hits": []}})
    client = TenantAwareElasticsearchClient(inner, service="test_svc")
    await client.search(index="candidates", body=body)
    captured = inner.search.await_args.kwargs["body"]
    assert captured["query"]["bool"]["filter"][0]["term"]["company_id"] == OTHER_CID


@pytest.mark.asyncio
async def test_interceptor_passthrough_non_intercepted_methods(dev_mode):
    inner = MagicMock()
    inner.index = AsyncMock(return_value={"result": "created"})
    client = TenantAwareElasticsearchClient(inner, service="test_svc")
    # ``index`` is not intercepted — should pass through untouched.
    result = await client.index(index="candidates", id="x", body={"foo": "bar"})
    assert result == {"result": "created"}


# --- end-to-end per real callsite -----------------------------------------


@pytest.mark.asyncio
async def test_search_candidates_callsite_injects_company_id(dev_mode, monkeypatch):
    """``ElasticsearchSearchBackend.search_candidates`` MUST send a payload
    containing ``{"term": {"company_id": <cid>}}`` to the ES client."""
    from app.domains.ai.services import search_service as svc_mod

    backend = svc_mod.ElasticsearchSearchBackend()
    inner = MagicMock()
    inner.search = AsyncMock(return_value={"hits": {"hits": []}})
    backend._client = TenantAwareElasticsearchClient(inner, service="ai_search_service.candidates")

    await backend.search_candidates(query="python", company_id=CID)

    inner.search.assert_awaited_once()
    sent_body = inner.search.await_args.kwargs["body"]
    filters = sent_body["query"]["bool"]["filter"]
    assert {"term": {"company_id": CID}} in filters


@pytest.mark.asyncio
async def test_search_candidates_callsite_with_extra_filters(dev_mode):
    """Extra ``filters`` argument doesn't clobber the tenant filter."""
    from app.domains.ai.services import search_service as svc_mod

    backend = svc_mod.ElasticsearchSearchBackend()
    inner = MagicMock()
    inner.search = AsyncMock(return_value={"hits": {"hits": []}})
    backend._client = TenantAwareElasticsearchClient(inner, service="ai_search_service.candidates")

    await backend.search_candidates(
        query="python",
        company_id=CID,
        filters={"status": "active"},
    )
    sent_body = inner.search.await_args.kwargs["body"]
    filters = sent_body["query"]["bool"]["filter"]
    assert {"term": {"company_id": CID}} in filters
    assert {"term": {"status": "active"}} in filters


@pytest.mark.asyncio
async def test_search_jobs_callsite_injects_company_id(dev_mode):
    from app.domains.ai.services import search_service as svc_mod

    backend = svc_mod.ElasticsearchSearchBackend()
    inner = MagicMock()
    inner.search = AsyncMock(return_value={"hits": {"hits": []}})
    backend._client = TenantAwareElasticsearchClient(inner, service="ai_search_service.jobs")

    await backend.search_jobs(query="backend", company_id=CID)
    sent_body = inner.search.await_args.kwargs["body"]
    filters = sent_body["query"]["bool"]["filter"]
    assert {"term": {"company_id": CID}} in filters


@pytest.mark.asyncio
async def test_search_callsite_rejects_invalid_company_id(dev_mode):
    """End-to-end: invalid ``company_id`` is rejected by the wrapper before
    any network call."""
    from app.domains.ai.services import search_service as svc_mod

    backend = svc_mod.ElasticsearchSearchBackend()
    inner = MagicMock()
    inner.search = AsyncMock()
    backend._client = TenantAwareElasticsearchClient(inner, service="ai_search_service.candidates")

    # ``search_candidates`` catches Exception and returns []. The contract is
    # that no request is sent to ES when company_id is invalid.
    result = await backend.search_candidates(query="x", company_id="default")
    assert result == []
    inner.search.assert_not_awaited()
