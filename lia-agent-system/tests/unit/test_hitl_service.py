"""
Testes unitários para HITLService (Sprint C — Item C2).

Cobertura:
  - request_approval retorna string pending_id
  - pending_id é único por chamada
  - receive_approval com approved=True armazena no Redis
  - receive_approval com approved=False armazena False
  - get_pending retorna None quando Redis indisponível (graceful)
  - is_approved retorna None quando pendente
  - is_approved retorna True quando aprovado
  - TTL Redis é 24h (86400s)
  - Redis key contém thread_id
"""
import json
import pytest

pytestmark = pytest.mark.medium

from unittest.mock import AsyncMock, MagicMock, patch


from app.domains.cv_screening.services.hitl_service import HITLService, _HITL_TTL_SECONDS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc():
    """HITLService limpo, sem Redis externo (usa in-memory)."""
    service = HITLService()
    service._memory = {}
    return service


@pytest.fixture
def svc_with_redis():
    """HITLService com Redis mockado."""
    service = HITLService()
    service._memory = {}
    return service


def _mock_redis(stored=None):
    """Retorna mock de Redis com comportamento configurável."""
    if stored is None:
        stored = {}
    r = MagicMock()

    def setex(key, ttl, value):
        stored[key] = (ttl, value)

    def get(key):
        item = stored.get(key)
        if item is None:
            return None
        return item[1] if isinstance(item, tuple) else item

    def keys(pattern):
        import fnmatch
        return [k for k in stored if fnmatch.fnmatch(k, pattern)]

    r.ping.return_value = True
    r.setex.side_effect = setex
    r.get.side_effect = get
    r.keys.side_effect = keys
    return r, stored


# ---------------------------------------------------------------------------
# TTL constant
# ---------------------------------------------------------------------------

def test_ttl_is_24h():
    """TTL deve ser 86400 segundos (24h)."""
    assert _HITL_TTL_SECONDS == 86400


# ---------------------------------------------------------------------------
# request_approval
# ---------------------------------------------------------------------------

class TestRequestApproval:

    @pytest.mark.asyncio
    async def test_returns_string_pending_id(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.api.v1.ws_manager.ws_manager.send_to_session", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id="t-1",
                action="create_job",
                description="Criar vaga",
                data={"title": "Dev"},
                ws_session_id="sess-1",
            )
        assert isinstance(pending_id, str)
        assert len(pending_id) > 0

    @pytest.mark.asyncio
    async def test_pending_id_is_unique_per_call(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.api.v1.ws_manager.ws_manager.send_to_session", new_callable=AsyncMock):
            id1 = await svc.request_approval("t-1", "create_job", "desc", {}, "s-1")
            id2 = await svc.request_approval("t-1", "create_job", "desc", {}, "s-1")
        assert id1 != id2

    @pytest.mark.asyncio
    async def test_stores_in_memory_when_redis_unavailable(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.api.v1.ws_manager.ws_manager.send_to_session", new_callable=AsyncMock):
            pending_id = await svc.request_approval("t-1", "action", "desc", {}, "s-1")
        key = f"hitl:t-1:{pending_id}"
        assert key in svc._memory
        assert svc._memory[key]["approved"] is None  # pendente

    @pytest.mark.asyncio
    async def test_redis_key_contains_thread_id(self, svc):
        r_mock, stored = _mock_redis()
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=r_mock), \
             patch("app.api.v1.ws_manager.ws_manager.send_to_session", new_callable=AsyncMock):
            pending_id = await svc.request_approval("my-thread", "action", "desc", {}, "s-1")
        assert any("my-thread" in k for k in stored)

    @pytest.mark.asyncio
    async def test_redis_ttl_is_24h(self, svc):
        r_mock, stored = _mock_redis()
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=r_mock), \
             patch("app.api.v1.ws_manager.ws_manager.send_to_session", new_callable=AsyncMock):
            pending_id = await svc.request_approval("t-1", "action", "desc", {}, "s-1")
        key = f"hitl:t-1:{pending_id}"
        assert key in stored
        ttl, _ = stored[key]
        assert ttl == _HITL_TTL_SECONDS

    @pytest.mark.asyncio
    async def test_ws_send_failure_does_not_raise(self, svc):
        """Falha no envio WS não deve propagar exceção."""
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.api.v1.ws_manager.ws_manager.send_to_session",
                   side_effect=Exception("WS offline")):
            # Não deve lançar exceção
            pending_id = await svc.request_approval("t-1", "action", "desc", {}, "s-1")
        assert isinstance(pending_id, str)


# ---------------------------------------------------------------------------
# receive_approval
# ---------------------------------------------------------------------------

class TestReceiveApproval:

    @pytest.mark.asyncio
    async def test_stores_approved_true(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            # Pre-store pendente
            svc._memory["hitl:t-1:p-1"] = {
                "pending_id": "p-1", "thread_id": "t-1",
                "action": "x", "description": "", "data": {},
                "ws_session_id": "", "requested_at": "2026-01-01", "approved": None,
            }
            result = await svc.receive_approval("t-1", "p-1", approved=True)
        assert result["approved"] is True

    @pytest.mark.asyncio
    async def test_stores_approved_false(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            svc._memory["hitl:t-2:p-2"] = {
                "pending_id": "p-2", "thread_id": "t-2",
                "action": "x", "description": "", "data": {},
                "ws_session_id": "", "requested_at": "2026-01-01", "approved": None,
            }
            result = await svc.receive_approval("t-2", "p-2", approved=False)
        assert result["approved"] is False

    @pytest.mark.asyncio
    async def test_stores_comment(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = await svc.receive_approval("t-3", "p-3", approved=True, comment="ok")
        assert result["comment"] == "ok"

    @pytest.mark.asyncio
    async def test_creates_record_when_not_exists(self, svc):
        """receive_approval cria registro mesmo quando não existe pending anterior."""
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = await svc.receive_approval("t-new", "p-new", approved=True)
        assert result["approved"] is True
        assert result["thread_id"] == "t-new"


# ---------------------------------------------------------------------------
# get_pending
# ---------------------------------------------------------------------------

class TestGetPending:

    @pytest.mark.asyncio
    async def test_returns_none_when_redis_unavailable(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_get_pending", return_value=None):
            result = await svc.get_pending("t-99")
        # sem nada in-memory → None
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_pending(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.domains.cv_screening.services.hitl_service._db_get_pending", return_value=None):
            # Adicionar apenas aprovado (não pendente)
            svc._memory["hitl:t-1:p-done"] = {
                "pending_id": "p-done", "thread_id": "t-1",
                "approved": True, "requested_at": "2026-01-01"
            }
            result = await svc.get_pending("t-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_pending_item(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            svc._memory["hitl:t-2:p-1"] = {
                "pending_id": "p-1", "thread_id": "t-2",
                "approved": None, "requested_at": "2026-01-01T10:00:00"
            }
            result = await svc.get_pending("t-2")
        assert result is not None
        assert result["pending_id"] == "p-1"

    @pytest.mark.asyncio
    async def test_graceful_on_exception(self, svc):
        """get_pending não deve lançar exceção mesmo com falha interna."""
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", side_effect=Exception("boom")):
            result = await svc.get_pending("t-99")
        assert result is None


# ---------------------------------------------------------------------------
# is_approved
# ---------------------------------------------------------------------------

class TestIsApproved:

    @pytest.mark.asyncio
    async def test_returns_none_when_pending(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            svc._memory["hitl:t-1:p-1"] = {
                "pending_id": "p-1", "approved": None
            }
            result = await svc.is_approved("p-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_true_when_approved(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            svc._memory["hitl:t-1:p-2"] = {
                "pending_id": "p-2", "approved": True
            }
            result = await svc.is_approved("p-2")
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_rejected(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            svc._memory["hitl:t-1:p-3"] = {
                "pending_id": "p-3", "approved": False
            }
            result = await svc.is_approved("p-3")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = await svc.is_approved("p-nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_graceful_on_redis_exception(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", side_effect=Exception("redis down")):
            result = await svc.is_approved("p-any")
        assert result is None
