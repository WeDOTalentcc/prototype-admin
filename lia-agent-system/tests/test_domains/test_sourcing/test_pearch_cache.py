"""G-12: cache de busca Pearch sem PII de contato.

- cache miss -> chama Pearch + grava (sem email/telefone no payload)
- cache hit -> 0 chamadas Pearch (economia de creditos)
- modo reveal (show_emails/show_phone) -> bypassa cache (nunca cacheia PII)
- chave isola por company_id
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.sourcing.services.pearch_service import PearchService
from app.shared.resilience.cache_manager_service import CacheResult
from lia_models.pearch import (
    PearchSearchRequest,
    PearchSearchResponse,
    PearchSearchResult,
    SearchType,
)
from lia_models.pearch import CandidateProfile


def _profile(name="Ana Lima"):
    return CandidateProfile(name=name)


def _response():
    return PearchSearchResponse(
        uuid="u1", thread_id="t1", query="dev", status="success",
        total_estimate=1,
        search_results=[PearchSearchResult(docid="d1", score=90, profile=_profile())],
    )


@pytest.fixture
def svc():
    s = PearchService(timeout=5)
    s.api_key = "test-key"
    return s


def _req(show_emails=False, show_phone=False):
    return PearchSearchRequest(query="dev backend", type=SearchType.FAST,
                               show_emails=show_emails, show_phone_numbers=show_phone, limit=10)


@pytest.mark.asyncio
async def test_cache_miss_calls_pearch_and_stores(svc):
    svc._search_cache.get = AsyncMock(return_value=CacheResult(hit=False, value=None))
    svc._search_cache.set = AsyncMock(return_value=True)

    fake_post = MagicMock()
    fake_post.raise_for_status = MagicMock()
    fake_post.json = MagicMock(return_value={})

    with patch.object(svc, "_parse_response", return_value=_response()), \
         patch.object(svc, "_track_pearch_consumption", new=AsyncMock()), \
         patch("app.domains.sourcing.services.pearch_service.httpx.AsyncClient") as _cli:
        client = AsyncMock()
        client.post = AsyncMock(return_value=fake_post)
        _cli.return_value.__aenter__ = AsyncMock(return_value=client)
        _cli.return_value.__aexit__ = AsyncMock(return_value=False)

        resp = await svc.search_candidates(_req(), timeout=5, company_id="comp-A")

    assert resp.uuid == "u1"
    client.post.assert_called_once()           # Pearch foi chamado
    svc._search_cache.set.assert_awaited_once()  # gravou no cache
    # payload cacheado nao tem PII de contato
    stored = svc._search_cache.set.await_args.args[1]
    prof0 = stored["search_results"][0]["profile"]
    assert prof0.get("email") in (None, "", [])
    assert prof0.get("phone") in (None, "", [])


@pytest.mark.asyncio
async def test_cache_hit_skips_pearch(svc):
    cached = _response().model_dump(mode="json")
    svc._search_cache.get = AsyncMock(return_value=CacheResult(hit=True, value=cached))
    svc._search_cache.set = AsyncMock()

    with patch("app.domains.sourcing.services.pearch_service.httpx.AsyncClient") as _cli:
        resp = await svc.search_candidates(_req(), timeout=5, company_id="comp-A")
        _cli.assert_not_called()  # Pearch NAO foi chamado -> 0 creditos

    assert resp.uuid == "u1"
    svc._search_cache.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_reveal_mode_bypasses_cache(svc):
    svc._search_cache.get = AsyncMock(return_value=CacheResult(hit=True, value=_response().model_dump(mode="json")))
    svc._search_cache.set = AsyncMock()

    fake_post = MagicMock()
    fake_post.raise_for_status = MagicMock()
    fake_post.json = MagicMock(return_value={})

    with patch.object(svc, "_parse_response", return_value=_response()), \
         patch.object(svc, "_track_pearch_consumption", new=AsyncMock()), \
         patch("app.domains.sourcing.services.pearch_service.httpx.AsyncClient") as _cli:
        client = AsyncMock()
        client.post = AsyncMock(return_value=fake_post)
        _cli.return_value.__aenter__ = AsyncMock(return_value=client)
        _cli.return_value.__aexit__ = AsyncMock(return_value=False)

        await svc.search_candidates(_req(show_emails=True), timeout=5, company_id="comp-A")

    # show_emails=True -> nao le nem grava cache
    svc._search_cache.get.assert_not_awaited()
    svc._search_cache.set.assert_not_awaited()
    client.post.assert_called_once()


def test_cache_key_isolates_by_company(svc):
    r = _req()
    k_a = svc._search_cache_key(r, "comp-A")
    k_b = svc._search_cache_key(r, "comp-B")
    assert k_a != k_b
    assert k_a.startswith("pearch_search:comp-A:")


def test_strip_contact_pii_nulls_contact_fields(svc):
    resp = _response()
    # injeta contato no profile
    p = resp.search_results[0].profile
    for f in ("email", "phone"):
        if hasattr(p, f):
            setattr(p, f, "leak@x.com" if f == "email" else "+5511999999999")
    safe = svc._strip_contact_pii(resp)
    sp = safe.search_results[0].profile
    for f in ("email", "phone"):
        if hasattr(sp, f):
            assert getattr(sp, f) is None
