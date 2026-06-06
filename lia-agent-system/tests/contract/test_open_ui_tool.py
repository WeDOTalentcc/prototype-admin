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
from app.domains.recruiter_assistant.agents.ui_tool_registry import _wrap_open_ui
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
        r = await _wrap_open_ui(capability="view_profile", entity_ids={"candidate_id": "c1"})
        assert r["success"] is True
        params = r["data"]["ui_action_params"]
        assert r["data"]["ui_action"] == "open_modal"
        assert params["modal_id"] == "profile"
        assert params["requires_confirmation"] is False
        assert params["data"]["candidate_id"] == "c1"
        # company_id autoritativo do JWT, não do payload da LLM
        assert params["data"]["company_id"] == "test-company-uuid"

    @pytest.mark.asyncio
    async def test_destructive_flags_confirmation(self, _tenant):
        r = await _wrap_open_ui(capability="close_job", entity_ids={"job_id": "j1"})
        assert r["success"] is True
        params = r["data"]["ui_action_params"]
        assert params["modal_id"] == "close_vacancy"
        assert params["requires_confirmation"] is True
        assert params["data"]["requires_confirmation"] is True

    @pytest.mark.asyncio
    async def test_missing_entity_needs_params(self, _tenant):
        r = await _wrap_open_ui(capability="view_profile", entity_ids={})
        assert r["success"] is False
        assert r.get("needs_params") is True
        assert "candidate_id" in r["data"]["missing_params"]

    @pytest.mark.asyncio
    async def test_unknown_capability_honest_fail(self, _tenant):
        r = await _wrap_open_ui(capability="not_a_modal_xyz", entity_ids={})
        assert r["success"] is False
        assert "não conheço" in r["message"].lower() or "modal" in r["message"].lower()

    @pytest.mark.asyncio
    async def test_no_entity_required_ok(self, _tenant):
        r = await _wrap_open_ui(capability="bulk_action", entity_ids={})
        assert r["success"] is True
        assert r["data"]["ui_action_params"]["modal_id"] == "bulk_action"

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
