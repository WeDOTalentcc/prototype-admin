"""Sensores de resiliencia do produtor Apify run_apify_actor (G-04 canonical-fix).

Garante o que o path Pearch ja tinha e o Apify nao tinha:
- retry exponencial em falha transitoria (HTTP 5xx/429, actor FAILED)
- falhar ALTO (ApifyError) em falha terminal — nunca {} silencioso (REGRA 4)
- 4xx nao-retentavel falha imediatamente, sem retry
- gate de config (sem API key) retorna {} (nao e falha de runtime)
"""
import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.sourcing.services.apify_service import (
    ApifyError,
    ApifyTransientError,
    ApifyService,
)
from app.shared.resilience.circuit_breaker import reset_circuit


@pytest.fixture(autouse=True)
def _reset_apify_circuit():
    # Circuit breaker e global por processo — isolar entre testes
    reset_circuit("apify")
    yield
    reset_circuit("apify")


@pytest.fixture
def service():
    svc = ApifyService()
    svc.api_key = "test-key"  # bypass config gate
    return svc


def _resp(json_data=None, raise_status=None):
    r = MagicMock()
    if raise_status is not None:
        r.status_code = raise_status
        r.text = "boom"
        err = httpx.HTTPStatusError(
            "err", request=MagicMock(), response=r
        )
        r.raise_for_status.side_effect = err
    else:
        r.raise_for_status.return_value = None
    r.json.return_value = json_data if json_data is not None else {}
    return r


class _FakeClientCM:
    def __init__(self, client):
        self._c = client

    async def __aenter__(self):
        return self._c

    async def __aexit__(self, *a):
        return False


def _patch_client(service, post_side_effect, get_side_effect):
    fake = MagicMock()
    fake.post = AsyncMock(side_effect=post_side_effect)
    fake.get = AsyncMock(side_effect=get_side_effect)
    # _sleep no-op + tenacity sleeps no-op para teste rapido
    service._sleep = AsyncMock(return_value=None)
    return patch(
        "app.domains.sourcing.services.apify_service.httpx.AsyncClient",
        return_value=_FakeClientCM(fake),
    ), fake


@pytest.mark.asyncio
async def test_transient_500_is_retried_then_succeeds(service):
    """1a tentativa HTTP 500 (retentavel) -> retry -> 2a tentativa sucesso."""
    run_ok = _resp({"data": {"id": "run1"}})
    status_ok = _resp({"data": {"status": "SUCCEEDED", "defaultDatasetId": "ds1"}})
    items_ok = _resp([{"name": "Jane"}])

    post_side = [_resp(raise_status=500), run_ok]
    get_side = [status_ok, items_ok]

    cm, fake = _patch_client(service, post_side, get_side)
    with cm, patch("tenacity.nap.time.sleep"), patch("asyncio.sleep", new=AsyncMock()):
        result = await service.run_apify_actor("actor/x", {"q": 1})

    assert result == {"name": "Jane"}
    assert fake.post.call_count == 2  # retry aconteceu


@pytest.mark.asyncio
async def test_persistent_failure_raises_not_silent(service):
    """Falha persistente (todas tentativas 500) levanta ApifyError — nunca {} silencioso."""
    post_side = [_resp(raise_status=500)] * 5
    cm, fake = _patch_client(service, post_side, [])
    with cm, patch("tenacity.nap.time.sleep"), patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises(ApifyError):
            await service.run_apify_actor("actor/x", {"q": 1})
    assert fake.post.call_count == 3  # stop_after_attempt(3)


@pytest.mark.asyncio
async def test_non_retryable_4xx_fails_fast(service):
    """HTTP 400 (nao-retentavel) levanta ApifyError sem retry."""
    post_side = [_resp(raise_status=400)] * 5
    cm, fake = _patch_client(service, post_side, [])
    with cm, patch("tenacity.nap.time.sleep"), patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises(ApifyError):
            await service.run_apify_actor("actor/x", {"q": 1})
    assert fake.post.call_count == 1  # sem retry em 4xx


@pytest.mark.asyncio
async def test_actor_failed_status_is_transient(service):
    """Actor com status FAILED e tratado como transitorio (retry)."""
    run_ok = _resp({"data": {"id": "run1"}})
    status_failed = _resp({"data": {"status": "FAILED"}})
    post_side = [run_ok, run_ok, run_ok]
    get_side = [status_failed, status_failed, status_failed]
    cm, fake = _patch_client(service, post_side, get_side)
    with cm, patch("tenacity.nap.time.sleep"), patch("asyncio.sleep", new=AsyncMock()):
        with pytest.raises(ApifyTransientError):
            await service.run_apify_actor("actor/x", {"q": 1})
    assert fake.post.call_count == 3


@pytest.mark.asyncio
async def test_missing_api_key_returns_empty(service):
    """Sem API key e gate de config (nao falha de runtime) -> {}."""
    service.api_key = ""
    result = await service.run_apify_actor("actor/x", {"q": 1})
    assert result == {}


@pytest.mark.asyncio
async def test_succeeded_no_dataset_returns_empty(service):
    """SUCCEEDED sem dataset = sem dados (nao e falha) -> {} sem raise."""
    run_ok = _resp({"data": {"id": "run1"}})
    status_no_ds = _resp({"data": {"status": "SUCCEEDED"}})
    cm, fake = _patch_client(service, [run_ok], [status_no_ds])
    with cm, patch("tenacity.nap.time.sleep"), patch("asyncio.sleep", new=AsyncMock()):
        result = await service.run_apify_actor("actor/x", {"q": 1})
    assert result == {}
