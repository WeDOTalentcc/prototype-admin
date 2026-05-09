"""
Extended unit tests for HITLService.

Covers: store_resume_info, get_resume_info, _store/_load helpers,
Redis with real mock data, multi-tenant isolation, domain/company_id fields,
full request→receive→check approval lifecycle.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.cv_screening.services.hitl_service import HITLService, _HITL_TTL_SECONDS


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc():
    """Clean HITLService using in-memory fallback."""
    service = HITLService()
    service._memory = {}
    return service


def _mock_redis(initial_data=None):
    """Redis mock with dict-backed storage."""
    stored = initial_data or {}
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
# store_resume_info + get_resume_info
# ---------------------------------------------------------------------------

class TestStoreResumeInfo:
    @pytest.mark.asyncio
    async def test_store_and_retrieve_resume_info(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            await svc.store_resume_info(
                thread_id="t-100",
                domain="pipeline",
                session_id="sess-abc",
                agent_input_dict={"job_id": "j-1", "candidate_id": "c-2"},
                hitl_context="Aprovação de movimentação",
            )
            result = await svc.get_resume_info("t-100")

        assert result is not None
        assert result["thread_id"] == "t-100"
        assert result["domain"] == "pipeline"
        assert result["session_id"] == "sess-abc"
        assert result["agent_input"]["job_id"] == "j-1"
        assert result["hitl_context"] == "Aprovação de movimentação"

    @pytest.mark.asyncio
    async def test_get_resume_info_returns_none_when_not_found(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = await svc.get_resume_info("nonexistent-thread")
        assert result is None

    @pytest.mark.asyncio
    async def test_store_resume_info_has_stored_at(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            await svc.store_resume_info("t-200", "wizard", "s-1", {})
            result = await svc.get_resume_info("t-200")
        assert "stored_at" in result

    @pytest.mark.asyncio
    async def test_store_resume_overwrites_previous(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            await svc.store_resume_info("t-300", "domain_a", "sess-1", {"v": 1})
            await svc.store_resume_info("t-300", "domain_b", "sess-2", {"v": 2})
            result = await svc.get_resume_info("t-300")
        assert result["domain"] == "domain_b"
        assert result["agent_input"]["v"] == 2


# ---------------------------------------------------------------------------
# _store / _load helpers
# ---------------------------------------------------------------------------

class TestStoreLoadHelpers:
    def test_store_and_load_in_memory(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            svc._store("key-1", {"foo": "bar"})
            result = svc._load("key-1")
        assert result == {"foo": "bar"}

    def test_load_missing_key_returns_none(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = svc._load("does-not-exist")
        assert result is None

    def test_store_overwrites_in_memory(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            svc._store("key-x", {"v": 1})
            svc._store("key-x", {"v": 2})
            result = svc._load("key-x")
        assert result["v"] == 2

    def test_store_with_redis_calls_setex(self, svc):
        r_mock, stored = _mock_redis()
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=r_mock):
            svc._store("hitl:t1:p1", {"test": True})
        assert "hitl:t1:p1" in stored
        ttl, raw = stored["hitl:t1:p1"]
        assert ttl == _HITL_TTL_SECONDS
        assert json.loads(raw)["test"] is True

    def test_load_from_redis_parses_json(self, svc):
        r_mock, _ = _mock_redis({"hitl:t1:p1": (86400, json.dumps({"approved": True}))})
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=r_mock):
            result = svc._load("hitl:t1:p1")
        assert result["approved"] is True


# ---------------------------------------------------------------------------
# Full lifecycle: request → receive → is_approved
# ---------------------------------------------------------------------------

class TestFullApprovalLifecycle:
    @pytest.mark.asyncio
    async def test_full_lifecycle_in_memory(self, svc):
        """request_approval → receive_approval(True) → is_approved returns True"""
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.api.v1.ws_manager.ws_manager.send_to_session", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id="t-lifecycle",
                action="create_job",
                description="Criar vaga Dev Senior",
                data={"title": "Dev Senior"},
                ws_session_id="sess-lifecycle",
            )

        assert isinstance(pending_id, str)

        # Initially pending
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            approved_status = await svc.is_approved(pending_id)
        assert approved_status is None

        # Receive approval
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            await svc.receive_approval("t-lifecycle", pending_id, approved=True)

        # Now should be approved
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            final_status = await svc.is_approved(pending_id)
        assert final_status is True

    @pytest.mark.asyncio
    async def test_full_lifecycle_rejection(self, svc):
        """request_approval → receive_approval(False) → is_approved returns False"""
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.api.v1.ws_manager.ws_manager.send_to_session", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id="t-reject", action="move_candidate",
                description="Mover candidato", data={}, ws_session_id="s-1",
            )

        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            await svc.receive_approval("t-reject", pending_id, approved=False, comment="Não aprovado")

        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = await svc.is_approved(pending_id)
        assert result is False


# ---------------------------------------------------------------------------
# Domain and company_id fields
# ---------------------------------------------------------------------------

class TestDomainAndCompanyFields:
    @pytest.mark.asyncio
    async def test_request_approval_stores_domain(self, svc):
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None), \
             patch("app.api.v1.ws_manager.ws_manager.send_to_session", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id="t-domain", action="create_job",
                description="desc", data={}, ws_session_id="s-1",
                domain="wizard", company_id="corp-123",
            )

        key = f"hitl:t-domain:{pending_id}"
        stored = svc._memory.get(key)
        assert stored is not None
        assert stored["domain"] == "wizard"

    @pytest.mark.asyncio
    async def test_receive_approval_stores_resolved_by(self, svc):
        # Pre-seed pending
        svc._memory["hitl:t-x:p-x"] = {
            "pending_id": "p-x", "thread_id": "t-x",
            "action": "test", "description": "", "data": {},
            "ws_session_id": "", "requested_at": "2026-01-01", "approved": None,
        }
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = await svc.receive_approval(
                "t-x", "p-x", approved=True, resolved_by="manager@acme.com"
            )
        assert result["resolved_by"] == "manager@acme.com"

    @pytest.mark.asyncio
    async def test_receive_approval_stores_comment(self, svc):
        svc._memory["hitl:t-c:p-c"] = {
            "pending_id": "p-c", "thread_id": "t-c",
            "action": "test", "description": "", "data": {},
            "ws_session_id": "", "requested_at": "2026-01-01", "approved": None,
        }
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = await svc.receive_approval("t-c", "p-c", approved=False, comment="Budget insuficiente")
        assert result["comment"] == "Budget insuficiente"


# ---------------------------------------------------------------------------
# Multi-tenant isolation
# ---------------------------------------------------------------------------

class TestMultiTenantIsolation:
    @pytest.mark.asyncio
    async def test_pending_isolated_by_thread_id(self, svc):
        svc._memory["hitl:thread-A:p-A"] = {
            "pending_id": "p-A", "thread_id": "thread-A",
            "approved": None, "requested_at": "2026-01-01T10:00:00"
        }
        svc._memory["hitl:thread-B:p-B"] = {
            "pending_id": "p-B", "thread_id": "thread-B",
            "approved": None, "requested_at": "2026-01-01T10:00:00"
        }
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            pending_a = await svc.get_pending("thread-A")
            pending_b = await svc.get_pending("thread-B")

        assert pending_a is not None
        assert pending_a["pending_id"] == "p-A"
        assert pending_b is not None
        assert pending_b["pending_id"] == "p-B"

    @pytest.mark.asyncio
    async def test_is_approved_not_confused_by_other_threads(self, svc):
        svc._memory["hitl:thread-1:p-111"] = {"pending_id": "p-111", "approved": True}
        svc._memory["hitl:thread-2:p-222"] = {"pending_id": "p-222", "approved": False}
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            r1 = await svc.is_approved("p-111")
            r2 = await svc.is_approved("p-222")
        assert r1 is True
        assert r2 is False


# ---------------------------------------------------------------------------
# get_pending sorting
# ---------------------------------------------------------------------------

class TestGetPendingMostRecent:
    @pytest.mark.asyncio
    async def test_returns_most_recent_pending(self, svc):
        svc._memory["hitl:t-sort:p-1"] = {
            "pending_id": "p-1", "thread_id": "t-sort",
            "approved": None, "requested_at": "2026-01-01T09:00:00"
        }
        svc._memory["hitl:t-sort:p-2"] = {
            "pending_id": "p-2", "thread_id": "t-sort",
            "approved": None, "requested_at": "2026-01-01T11:00:00"
        }
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = await svc.get_pending("t-sort")
        assert result["pending_id"] == "p-2"

    @pytest.mark.asyncio
    async def test_skips_already_approved_when_getting_pending(self, svc):
        svc._memory["hitl:t-skip:p-done"] = {
            "pending_id": "p-done", "thread_id": "t-skip",
            "approved": True, "requested_at": "2026-01-01T08:00:00"
        }
        svc._memory["hitl:t-skip:p-open"] = {
            "pending_id": "p-open", "thread_id": "t-skip",
            "approved": None, "requested_at": "2026-01-01T10:00:00"
        }
        with patch("app.domains.cv_screening.services.hitl_service._get_redis", return_value=None):
            result = await svc.get_pending("t-skip")
        assert result["pending_id"] == "p-open"
