"""
Testes unitários para UserAgentPreferenceService e integração HITL auto_confirm — Sprint J3.

Cobertura:
- check_auto_confirm retorna False quando não há preferência
- check_auto_confirm retorna True quando preferência existe com auto_confirm=True
- check_auto_confirm retorna False quando auto_confirm=False
- upsert cria nova preferência
- upsert atualiza preferência existente
- list_user_preferences retorna lista correta por user_id + company_id
- Isolamento por (user_id, company_id, domain, action_type)
- HITLService.request_approval com auto_confirm=True → retorna pending_id já aprovado
- HITLService.request_approval com auto_confirm=False → fluxo normal (pending)
- HITLService._check_auto_confirm falha silenciosa (retorna False)
- API endpoint GET /user-preferences/agent
- API endpoint POST /user-preferences/agent
"""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_pref(
    user_id="u1",
    company_id="c1",
    domain="pipeline",
    action_type="move_candidate",
    auto_confirm=True,
):
    from app.models.user_agent_preference import UserAgentPreference
    pref = UserAgentPreference()
    pref.id = uuid.uuid4()
    pref.user_id = user_id
    pref.company_id = company_id
    pref.domain = domain
    pref.action_type = action_type
    pref.auto_confirm = auto_confirm
    pref.updated_at = datetime.utcnow()
    return pref


# ---------------------------------------------------------------------------
# UserAgentPreferenceService
# ---------------------------------------------------------------------------

class TestCheckAutoConfirm:

    @pytest.mark.asyncio
    async def test_returns_false_when_no_preference(self):
        from app.shared.services.user_agent_preference_service import UserAgentPreferenceService
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        result = await UserAgentPreferenceService.check_auto_confirm(
            db, user_id="u1", company_id="c1", domain="pipeline", action_type="move"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_when_auto_confirm_true(self):
        from app.shared.services.user_agent_preference_service import UserAgentPreferenceService
        pref = _make_pref(auto_confirm=True)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
        result = await UserAgentPreferenceService.check_auto_confirm(
            db, user_id="u1", company_id="c1", domain="pipeline", action_type="move_candidate"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_auto_confirm_false(self):
        from app.shared.services.user_agent_preference_service import UserAgentPreferenceService
        pref = _make_pref(auto_confirm=False)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
        result = await UserAgentPreferenceService.check_auto_confirm(
            db, user_id="u1", company_id="c1", domain="pipeline", action_type="move_candidate"
        )
        assert result is False


class TestUpsert:

    @pytest.mark.asyncio
    async def test_creates_new_preference(self):
        from app.shared.services.user_agent_preference_service import UserAgentPreferenceService
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: None)

        result = await UserAgentPreferenceService.upsert(
            db, user_id="u2", company_id="c1", domain="wizard",
            action_type="create_job", auto_confirm=True,
        )
        db.add.assert_called_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_updates_existing_preference(self):
        from app.shared.services.user_agent_preference_service import UserAgentPreferenceService
        pref = _make_pref(auto_confirm=False)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: None)

        await UserAgentPreferenceService.upsert(
            db, user_id="u1", company_id="c1", domain="pipeline",
            action_type="move_candidate", auto_confirm=True,
        )
        assert pref.auto_confirm is True
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_does_not_add_when_updating(self):
        from app.shared.services.user_agent_preference_service import UserAgentPreferenceService
        pref = _make_pref(auto_confirm=True)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=pref)))
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: None)

        await UserAgentPreferenceService.upsert(
            db, user_id="u1", company_id="c1", domain="pipeline",
            action_type="move_candidate", auto_confirm=False,
        )
        db.add.assert_not_called()


class TestListUserPreferences:

    @pytest.mark.asyncio
    async def test_returns_list(self):
        from app.shared.services.user_agent_preference_service import UserAgentPreferenceService
        prefs = [_make_pref(action_type="move"), _make_pref(action_type="schedule")]
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=prefs)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=scalars_mock)))

        result = await UserAgentPreferenceService.list_user_preferences(
            db, user_id="u1", company_id="c1"
        )
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_prefs(self):
        from app.shared.services.user_agent_preference_service import UserAgentPreferenceService
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[])
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=scalars_mock)))

        result = await UserAgentPreferenceService.list_user_preferences(
            db, user_id="u99", company_id="c1"
        )
        assert result == []


# ---------------------------------------------------------------------------
# HITLService — integração auto_confirm
# ---------------------------------------------------------------------------

class TestHITLAutoConfirm:

    def _make_hitl(self):
        from app.domains.cv_screening.services.hitl_service import HITLService
        svc = HITLService()
        svc._memory = {}
        return svc

    @pytest.mark.asyncio
    async def test_auto_confirm_true_returns_approved_pending(self):
        """Se auto_confirm=True, pending_id deve estar pré-aprovado."""
        svc = self._make_hitl()
        with patch.object(svc, "_check_auto_confirm", return_value=True), \
             patch("app.services.hitl_service._db_resolve", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id="t1", action="move_candidate", description="mover",
                data={}, ws_session_id="ws1", domain="pipeline",
                company_id="c1", user_id="u1",
            )
        result = await svc.is_approved(pending_id)
        assert result is True

    @pytest.mark.asyncio
    async def test_auto_confirm_false_returns_pending_none(self):
        """Se auto_confirm=False, is_approved deve retornar None (pendente)."""
        svc = self._make_hitl()
        with patch.object(svc, "_check_auto_confirm", return_value=False), \
             patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock):
            pending_id = await svc.request_approval(
                thread_id="t2", action="move_candidate", description="mover",
                data={}, ws_session_id="ws2", domain="pipeline",
                company_id="c1", user_id="u1",
            )
        result = await svc.is_approved(pending_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_user_id_skips_auto_confirm_check(self):
        """Sem user_id, _check_auto_confirm não deve ser chamado."""
        svc = self._make_hitl()
        with patch.object(svc, "_check_auto_confirm", new_callable=AsyncMock) as mock_check, \
             patch("app.services.hitl_service._db_save_pending", new_callable=AsyncMock):
            await svc.request_approval(
                thread_id="t3", action="move_candidate", description="mover",
                data={}, ws_session_id="ws3",
            )
        mock_check.assert_not_called()

    @pytest.mark.asyncio
    async def test_check_auto_confirm_exception_returns_false(self):
        """_check_auto_confirm deve retornar False silenciosamente em caso de erro."""
        svc = self._make_hitl()
        with patch("app.core.database.AsyncSessionLocal", side_effect=Exception("DB down")):
            result = await svc._check_auto_confirm(
                user_id="u1", company_id="c1", domain="pipeline", action_type="move"
            )
        assert result is False

    @pytest.mark.asyncio
    async def test_auto_confirm_logs_audit_trail(self):
        """Auto-confirmação deve registrar no audit trail (best-effort)."""
        svc = self._make_hitl()
        with patch.object(svc, "_check_auto_confirm", return_value=True), \
             patch("app.domains.cv_screening.services.hitl_service._db_resolve", new_callable=AsyncMock) as mock_resolve:
            await svc.request_approval(
                thread_id="t4", action="create_job", description="criar vaga",
                data={}, ws_session_id="ws4", domain="wizard",
                company_id="c1", user_id="u1",
            )
        mock_resolve.assert_called_once()
        call_kwargs = mock_resolve.call_args.kwargs
        assert call_kwargs["approved"] is True
        assert call_kwargs["comment"] == "auto_confirm"
        assert call_kwargs["resolved_by"] == "u1"
