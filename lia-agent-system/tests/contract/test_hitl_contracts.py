"""
Contract Tests: HITL (Human-in-the-Loop) — Sprint C Item C2.

Verifica:
  - Endpoint POST /hitl/{thread_id}/approve existe no router
  - HITLService tem métodos obrigatórios
  - WS agent_chat_ws trata mensagem approval_response
  - Resposta do endpoint tem campos obrigatórios (thread_id, pending_id, approved)
"""
import inspect
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Contract: HITLService métodos obrigatórios
# ---------------------------------------------------------------------------

class TestHITLServiceContract:

    def test_has_request_approval_method(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        assert hasattr(HITLService, "request_approval")
        assert callable(HITLService.request_approval)

    def test_has_receive_approval_method(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        assert hasattr(HITLService, "receive_approval")
        assert callable(HITLService.receive_approval)

    def test_has_get_pending_method(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        assert hasattr(HITLService, "get_pending")
        assert callable(HITLService.get_pending)

    def test_has_is_approved_method(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        assert hasattr(HITLService, "is_approved")
        assert callable(HITLService.is_approved)

    def test_request_approval_signature(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        sig = inspect.signature(HITLService.request_approval)
        params = list(sig.parameters.keys())
        assert "thread_id" in params
        assert "action" in params
        assert "description" in params
        assert "data" in params
        assert "ws_session_id" in params

    def test_receive_approval_signature(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        sig = inspect.signature(HITLService.receive_approval)
        params = list(sig.parameters.keys())
        assert "thread_id" in params
        assert "pending_id" in params
        assert "approved" in params

    def test_singleton_hitl_service_exists(self):
        from app.domains.cv_screening.services.hitl_service import hitl_service, HITLService
        assert isinstance(hitl_service, HITLService)


# ---------------------------------------------------------------------------
# Contract: Router HITL endpoints
# ---------------------------------------------------------------------------

class TestHITLRouterContract:

    def test_router_imported_without_error(self):
        from app.api.v1.hitl import router
        assert router is not None

    def test_approve_endpoint_exists(self):
        from app.api.v1.hitl import router
        routes = {r.path: r for r in router.routes}
        assert "/hitl/{thread_id}/approve" in routes

    def test_approve_endpoint_is_post(self):
        from app.api.v1.hitl import router
        for route in router.routes:
            if "/hitl/{thread_id}/approve" in getattr(route, "path", ""):
                assert "POST" in route.methods
                break

    def test_approve_endpoint_requires_auth(self):
        """O endpoint deve ter get_current_user nas dependências."""
        from app.api.v1.hitl import router
        from app.auth.dependencies import get_current_user
        for route in router.routes:
            if "/hitl/{thread_id}/approve" in getattr(route, "path", ""):
                # Verificar que get_current_user está presente nas dependências
                deps = getattr(route, "dependencies", [])
                dep_names = [str(d) for d in deps]
                # Alternativa: inspecionar endpoint function
                endpoint_source = inspect.getsource(route.endpoint)
                assert "get_current_user" in endpoint_source
                break


# ---------------------------------------------------------------------------
# Contract: ApprovalResponse campos obrigatórios
# ---------------------------------------------------------------------------

class TestApprovalResponseContract:

    def test_approval_response_has_required_fields(self):
        from app.api.v1.hitl import ApprovalResponse
        required = {"thread_id", "pending_id", "approved", "comment", "timestamp"}
        model_fields = set(ApprovalResponse.model_fields.keys())
        assert required.issubset(model_fields), (
            f"Campos faltando: {required - model_fields}"
        )

    def test_approval_response_instantiation(self):
        from app.api.v1.hitl import ApprovalResponse
        resp = ApprovalResponse(
            thread_id="t-1",
            pending_id="p-1",
            approved=True,
            comment=None,
            timestamp="2026-01-01T00:00:00+00:00",
        )
        assert resp.thread_id == "t-1"
        assert resp.pending_id == "p-1"
        assert resp.approved is True

    def test_approval_request_schema(self):
        from app.api.v1.hitl import ApprovalRequest
        req = ApprovalRequest(pending_id="p-1", approved=True)
        assert req.pending_id == "p-1"
        assert req.approved is True
        assert req.comment is None

    def test_approval_request_with_comment(self):
        from app.api.v1.hitl import ApprovalRequest
        req = ApprovalRequest(pending_id="p-2", approved=False, comment="Motivo de rejeição")
        assert req.comment == "Motivo de rejeição"


# ---------------------------------------------------------------------------
# Contract: WS agent_chat_ws trata approval_response
# ---------------------------------------------------------------------------

class TestWSApprovalResponseContract:

    def test_ws_handler_contains_approval_response_handling(self):
        """Verifica que agent_chat_ws.py contém tratamento para approval_response."""
        import app.api.v1.agent_chat_sse as ws_module
        source = inspect.getsource(ws_module)
        assert "approval_response" in source

    def test_ws_handler_contains_approval_confirmed(self):
        """Verifica que approval_confirmed está definido no serializer."""
        import app.shared.chat_event_serializer as ws_module
        source = inspect.getsource(ws_module)
        assert "approval_confirmed" in source

    def test_ws_handler_calls_hitl_service(self):
        """Verifica que agent_chat_ws importa/usa hitl_service."""
        import app.api.v1.agent_chat_sse as ws_module
        source = inspect.getsource(ws_module)
        assert "hitl_service" in source

    @pytest.mark.asyncio
    async def test_approval_response_message_triggers_receive_approval(self):
        """Simula recebimento de approval_response via WS."""
        from app.domains.cv_screening.services.hitl_service import HITLService

        svc = HITLService()
        svc._memory = {}

        with patch("app.services.hitl_service._get_redis", return_value=None):
            result = await svc.receive_approval(
                thread_id="ws-thread-1",
                pending_id="ws-pending-1",
                approved=True,
                comment="Aprovado via WS",
            )

        assert result["approved"] is True
        assert result["thread_id"] == "ws-thread-1"
        assert result["pending_id"] == "ws-pending-1"


# ---------------------------------------------------------------------------
# Contract: HybridSearchService interface pública
# ---------------------------------------------------------------------------

class TestHybridSearchServiceContract:

    def test_has_search_jobs_method(self):
        from app.domains.ai.services.hybrid_search_service import HybridSearchService
        assert hasattr(HybridSearchService, "search_jobs")

    def test_has_search_candidates_method(self):
        from app.domains.ai.services.hybrid_search_service import HybridSearchService
        assert hasattr(HybridSearchService, "search_candidates")

    def test_has_benchmark_method(self):
        from app.domains.ai.services.hybrid_search_service import HybridSearchService
        assert hasattr(HybridSearchService, "benchmark")

    def test_search_jobs_signature(self):
        from app.domains.ai.services.hybrid_search_service import HybridSearchService
        sig = inspect.signature(HybridSearchService.search_jobs)
        params = list(sig.parameters.keys())
        assert "query" in params
        assert "company_id" in params
        assert "db" in params
        assert "embedding" in params

    def test_singleton_exists(self):
        from app.domains.ai.services.hybrid_search_service import hybrid_search_service, HybridSearchService
        assert isinstance(hybrid_search_service, HybridSearchService)

    def test_alpha_configurable(self):
        from app.domains.ai.services.hybrid_search_service import HybridSearchService
        svc = HybridSearchService(alpha=0.3)
        assert svc.alpha == 0.3
