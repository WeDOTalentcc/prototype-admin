"""Fase B contract — open_ui tool (mecanismo determinístico de abrir modal).

Sensor: valida que open_ui (1) abre read-only direto, (2) flag HITL em
destrutivos, (3) exige entidades, (4) falha honesto p/ capability desconhecida,
(5) está federada no recruiter_copilot, (6) open_modal está na allowlist do
agentic_loop e _extract_tool_directive surfacea ui_action_params.

Multi-tenancy: company_id vem do ContextVar JWT (nunca do payload).
"""
from __future__ import annotations

import pytest

from app.middleware.auth_enforcement import _current_company_id
from app.domains.recruiter_assistant.agents.ui_tool_registry import (
    _wrap_open_ui,
    _ui_capabilities,
    _role_allows,
)
from app.domains.recruiter_assistant.agents.recruiter_copilot_tool_registry import (
    get_recruiter_copilot_tool_names,
)
from app.orchestrator.execution.agentic_loop import (
    _ACTIONABLE_TOOL_UI_ACTIONS,
    _extract_tool_directive,
)


@pytest.fixture
def _tenant():
    tok = _current_company_id.set("test-company-uuid")
    yield "test-company-uuid"
    _current_company_id.reset(tok)


class TestOpenUiTool:
    @pytest.mark.asyncio
    async def test_readonly_opens_directly(self, _tenant):
        r = await _wrap_open_ui(capability="view_score", entity_ids={"candidate_id": "c1"})
        assert r["success"] is True
        params = r["data"]["ui_action_params"]
        assert r["data"]["ui_action"] == "open_modal"
        assert params["modal_id"] == "general_score"
        assert params["requires_confirmation"] is False
        assert params["data"]["candidate_id"] == "c1"
        # company_id autoritativo do JWT, não do payload da LLM
        assert params["data"]["company_id"] == "test-company-uuid"

    @pytest.mark.asyncio
    async def test_destructive_navigates_to_surface(self, _tenant):
        # close_job é ação-acoplada → open_ui NAVEGA pra vaga (ação + HITL lá)
        r = await _wrap_open_ui(capability="close_job", entity_ids={"job_id": "j1"})
        assert r["success"] is True
        assert r["data"]["ui_action"] == "navigate_to"
        params = r["data"]["ui_action_params"]
        assert params["page"] == "vaga_detalhe"
        assert params["id"] == "j1"

    @pytest.mark.asyncio
    async def test_missing_entity_needs_params(self, _tenant):
        r = await _wrap_open_ui(capability="view_score", entity_ids={})
        assert r["success"] is False
        assert r.get("needs_params") is True
        assert "candidate_id" in r["data"]["missing_params"]

    @pytest.mark.asyncio
    async def test_unknown_capability_honest_fail(self, _tenant):
        r = await _wrap_open_ui(capability="not_a_modal_xyz", entity_ids={})
        assert r["success"] is False
        assert "não conheço" in r["message"].lower() or "modal" in r["message"].lower()

    @pytest.mark.asyncio
    async def test_navigate_cap_no_entity_ok(self, _tenant):
        # bulk_action exige seleção → navega pro funil (sem id)
        r = await _wrap_open_ui(capability="bulk_action", entity_ids={})
        assert r["success"] is True
        assert r["data"]["ui_action"] == "navigate_to"
        assert r["data"]["ui_action_params"]["page"] == "funil_talentos"

    @pytest.mark.asyncio
    async def test_no_company_blocked(self):
        # sem ContextVar de tenant → bloqueia (fail-closed)
        r = await _wrap_open_ui(capability="view_profile", entity_ids={"candidate_id": "c1"})
        assert r["success"] is False


class TestOpenUiFederationAndLoop:
    def test_open_ui_is_federated(self):
        assert "open_ui" in get_recruiter_copilot_tool_names(), (
            "open_ui deve estar no set federado do recruiter_copilot"
        )

    def test_open_modal_in_actionable_allowlist(self):
        assert "open_modal" in _ACTIONABLE_TOOL_UI_ACTIONS

    def test_extract_directive_surfaces_open_modal_params(self):
        class _R:
            success = True
            result = {
                "data": {
                    "ui_action": "open_modal",
                    "ui_action_params": {"modal_id": "profile", "data": {"candidate_id": "c1"}},
                }
            }
        d = _extract_tool_directive(_R())
        assert d is not None
        assert d["ui_action"] == "open_modal"
        assert d["ui_action_params"]["modal_id"] == "profile"

    def test_extract_directive_none_for_normal_result(self):
        class _R:
            success = True
            result = {"data": {"foo": "bar"}}
        assert _extract_tool_directive(_R()) is None


class TestOpenUiSafetyInvariants:
    """Fase D: pin do design de segurança (HITL estrutural + role-gate)."""

    def test_role_allows_fail_closed(self):
        # Sem role → nega cap restrita (não vaza tela staff).
        assert _role_allows("wedotalent_admin", None) is False
        assert _role_allows("wedotalent_admin", "") is False
        # Papel exato passa.
        assert _role_allows("wedotalent_admin", "wedotalent_admin") is True
        # Papel diferente nega.
        assert _role_allows("wedotalent_admin", "recruiter") is False
        # Privilegiado sempre passa.
        assert _role_allows("wedotalent_admin", "admin") is True

    @pytest.mark.asyncio
    async def test_open_ui_never_executes_only_opens_or_navigates(self, _tenant):
        """INVARIANTE HITL: open_ui só EMITE open_modal ou navigate_to —
        nunca executa mutação. A ação destrutiva fica sempre atrás da
        confirmação do modal/página (open_ui é abrir/navegar, não mutar)."""
        # ids amplos p/ satisfazer os entity_required comuns.
        ids = {"candidate_id": "c1", "job_id": "j1", "stage_target": "entrevista"}
        for intent in _ui_capabilities().keys():
            r = await _wrap_open_ui(capability=intent, entity_ids=ids)
            # needs_params/denial NÃO é violação; o invariante é: QUANDO abre,
            # só emite open_modal/navigate_to — nunca um ui_action de mutação.
            if r.get("success") and isinstance(r.get("data"), dict) and r["data"].get("ui_action"):
                ui = r["data"]["ui_action"]
                assert ui in ("open_modal", "navigate_to"), (
                    f"open_ui('{intent}') emitiu '{ui}' — só pode abrir/navegar, "
                    f"NUNCA executar mutação (HITL fica no modal/página)"
                )
