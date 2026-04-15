"""
Testes unitários para os fixes do QA Report 2026-04-15.

Cobre:
  - BUG-01: chat.send_message retorna 502 quando orquestrador devolve response vazio
  - BUG-04: sourcing_agents.list retorna 400 quando company_id ausente
  - BUG-05: hitl_service.get_all_pending_by_company aceita e usa db externo
  - BUG-06: sector_templates_router é registrado ANTES de agent_templates_router
  - BUG-07: briefing.get retorna briefing vazio para user_id=default_user

Não roda o FastAPI — foca em unit-level com mocks, mantendo a suíte rápida.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.medium


# ---------------------------------------------------------------------------
# BUG-05 — hitl_service aceita db externo e reusa a sessão
# ---------------------------------------------------------------------------

class TestHitlServiceAcceptsExternalDb:

    @pytest.mark.asyncio
    async def test_uses_external_db_when_provided(self):
        from app.domains.cv_screening.services.hitl_service import HITLService

        svc = HITLService()
        svc._memory = {}

        external_db = AsyncMock()
        external_db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))

        # Não deve criar AsyncSessionLocal quando db é passado
        with patch("app.core.database.AsyncSessionLocal") as session_local_mock:
            result = await svc.get_all_pending_by_company("company-123", db=external_db)

        assert result == []
        session_local_mock.assert_not_called()  # <- provaria que a session do request foi reutilizada
        external_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_company_id_returns_empty_list(self):
        from app.domains.cv_screening.services.hitl_service import HITLService

        svc = HITLService()
        svc._memory = {}

        result = await svc.get_all_pending_by_company("", db=AsyncMock())
        assert result == []


# ---------------------------------------------------------------------------
# BUG-06 — Ordem de registro dos routers evita colisão {template_id}=sectors
# ---------------------------------------------------------------------------

class TestRouteRegistrationOrder:

    def test_sector_templates_router_registered_before_agent_templates(self):
        """
        agent_templates_router tem GET /agent-templates/{template_id} que captura
        /agent-templates/sectors como template_id='sectors' → 404. Registrar o
        sector_templates_router antes resolve a colisão (FastAPI avalia em ordem).
        """
        from pathlib import Path
        routes_py = Path(
            "app/api/routes.py"
        )
        # Fallback para caminho absoluto quando rodando de cwd diferente
        if not routes_py.exists():
            routes_py = Path(__file__).resolve().parents[2] / "app" / "api" / "routes.py"

        content = routes_py.read_text()
        # Os dois `app.include_router(...)` devem estar em ordem correta
        sector_idx = content.index("sector_templates_router, prefix=\"/api/v1\"")
        agent_idx = content.index("agent_templates_router, prefix=\"/api/v1\"")
        assert sector_idx < agent_idx, (
            "sector_templates_router deve ser incluído ANTES de agent_templates_router "
            "para evitar que /agent-templates/sectors seja capturado por "
            "/agent-templates/{template_id} (BUG-06)."
        )


# ---------------------------------------------------------------------------
# BUG-07 — briefing retorna empty para default_user / anonymous
# ---------------------------------------------------------------------------

class TestBriefingEmptyForDefaultUser:

    @pytest.mark.asyncio
    async def test_default_user_returns_empty_briefing(self):
        from app.api.v1.briefing import get_daily_briefing

        db = AsyncMock()
        result = await get_daily_briefing(user_id="default_user", db=db)

        assert result["success"] is True
        # Campos do _EMPTY_BRIEFING
        data = result["data"]
        assert data["urgent_actions"] == []
        assert data["pipeline_summary"] == {}
        assert data["today_schedule"] == []
        assert data["pending_tasks"] == []
        assert data["active_alerts"] == []
        assert data["insights"] == []

    @pytest.mark.asyncio
    async def test_empty_user_id_returns_empty_briefing(self):
        from app.api.v1.briefing import get_daily_briefing

        db = AsyncMock()
        result = await get_daily_briefing(user_id="", db=db)
        assert result["success"] is True
        assert result["data"]["urgent_actions"] == []


# ---------------------------------------------------------------------------
# BUG-04 — sourcing_agents.list retorna 400 quando company_id ausente
# ---------------------------------------------------------------------------

class TestSourcingAgentsDefensiveList:

    @pytest.mark.asyncio
    async def test_missing_company_id_raises_400(self):
        from fastapi import HTTPException

        from app.api.v1.sourcing_agents import list_sourcing_agents

        fake_user = MagicMock()
        fake_user.company_id = None
        fake_user.id = "user-abc"

        with pytest.raises(HTTPException) as exc_info:
            await list_sourcing_agents(
                job_id=None,
                talent_pool_id=None,
                status=None,
                current_user=fake_user,
                db=AsyncMock(),
            )

        assert exc_info.value.status_code == 400
        assert "empresa" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# BUG-01 — chat.send_message NÃO retorna content vazio silenciosamente
# ---------------------------------------------------------------------------

class TestChatEmptyResponseGuard:
    """
    Teste nível de código: confirma que chat.py contém a guard `if not lia_response`
    que levanta HTTPException(502). Checar o fluxo completo exige FastAPI TestClient
    (coberto em integration tests posteriormente).
    """

    def test_chat_py_has_empty_response_guard(self):
        from pathlib import Path
        chat_py = Path("app/api/v1/chat.py")
        if not chat_py.exists():
            chat_py = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "chat.py"
        src = chat_py.read_text()
        assert 'if not lia_response:' in src, \
            "chat.py deve ter guard `if not lia_response` para evitar content vazio silencioso (BUG-01)"
        assert "status_code=502" in src, \
            "chat.py deve levantar 502 quando orchestrator retorna vazio (BUG-01)"
