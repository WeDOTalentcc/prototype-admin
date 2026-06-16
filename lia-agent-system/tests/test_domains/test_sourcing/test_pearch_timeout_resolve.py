"""Regressao: search_candidates com timeout=None NAO pode quebrar com None+10.

hybrid_search (path da busca global) chama search_candidates SEM timeout (default
None). Antes, `httpx.AsyncClient(timeout=None + 10)` levantava TypeError -> RetryError
-> busca global vazia. Agora None resolve para self.timeout.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.sourcing.services.pearch_service import PearchService


class _FakeClientCM:
    def __init__(self, client):
        self._c = client

    async def __aenter__(self):
        return self._c

    async def __aexit__(self, *a):
        return False


@pytest.fixture
def svc():
    s = PearchService(timeout=30)
    s.api_key = "test-key"
    return s


@pytest.mark.asyncio
async def test_timeout_none_does_not_raise_typeerror(svc):
    from lia_models.pearch import PearchSearchRequest, SearchType

    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={
        "uuid": "u", "thread_id": "t", "query": "x", "status": "Done",
        "total_estimate": 0, "credits_remaining": 100, "search_results": [],
    })
    client = MagicMock()
    client.post = AsyncMock(return_value=resp)

    captured = {}

    def _factory(*args, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return _FakeClientCM(client)

    req = PearchSearchRequest(query="product manager", type=SearchType.FAST, limit=10)
    with patch("app.domains.sourcing.services.pearch_service.httpx.AsyncClient", side_effect=_factory), \
         patch.object(PearchService, "_track_pearch_consumption", new=AsyncMock()):
        # timeout=None (como hybrid_search chama) -> NAO deve levantar TypeError
        result = await svc.search_candidates(req, timeout=None, company_id=None)

    assert result.status == "Done"
    # timeout None resolveu para self.timeout (30) + 10 = 40, nao None+10
    assert captured["timeout"] == 40
