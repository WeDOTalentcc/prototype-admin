"""Fase 2 slice 1 contract — apply_table_state tool (ponte in-page).

Sensor: valida que apply_table_state (1) emite a diretiva canonica
ui_action="apply_table_state" com patch camelCase, (2) omite chaves nao
informadas, (3) rejeita surface != candidates, (4) esta federada no
recruiter_copilot, (5) apply_table_state esta na allowlist do agentic_loop
e _extract_tool_directive surfacea ui_action_params, (6) NAO e HITL-gated
(read-only UI — nunca chama hitl_preflight).

Multi-tenancy: company_id vem do ContextVar JWT (nunca do payload).
"""
from __future__ import annotations

import pytest

from app.middleware.auth_enforcement import _current_company_id
from app.domains.recruiter_assistant.agents.ui_tool_registry import (
    _wrap_apply_table_state,
    get_ui_tools,
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


class TestApplyTableStateTool:
    @pytest.mark.asyncio
    async def test_full_patch_snake_to_camel(self, _tenant):
        r = await _wrap_apply_table_state(
            surface="candidates",
            search="João",
            sort_by="score",
            sort_order="desc",
            quick_filters=["approved"],
        )
        assert r["success"] is True
        assert r["data"]["ui_action"] == "apply_table_state"
        assert r["data"]["ui_action_params"] == {
            "surface": "candidates",
            "patch": {
                "search": "João",
                "sortBy": "score",
                "sortOrder": "desc",
                "quickFilters": ["approved"],
            },
        }

    @pytest.mark.asyncio
    async def test_omitted_args_absent_from_patch(self, _tenant):
        r = await _wrap_apply_table_state(surface="candidates", search="João")
        assert r["success"] is True
        params = r["data"]["ui_action_params"]
        assert params["surface"] == "candidates"
        assert params["patch"] == {"search": "João"}
        # snake->camel keys nunca aparecem quando o arg nao foi passado
        assert "sortBy" not in params["patch"]
        assert "sortOrder" not in params["patch"]
        assert "quickFilters" not in params["patch"]

    @pytest.mark.asyncio
    async def test_empty_quick_filters_dropped(self, _tenant):
        r = await _wrap_apply_table_state(
            surface="candidates", sort_by="name", sort_order="asc", quick_filters=[]
        )
        assert r["success"] is True
        patch = r["data"]["ui_action_params"]["patch"]
        assert patch == {"sortBy": "name", "sortOrder": "asc"}
        assert "quickFilters" not in patch

    @pytest.mark.asyncio
    async def test_non_candidates_surface_rejected(self, _tenant):
        r = await _wrap_apply_table_state(surface="jobs", search="x")
        assert r["success"] is False
        assert "candidat" in r["message"].lower()

    @pytest.mark.asyncio
    async def test_company_id_not_required_in_patch(self, _tenant):
        # company_id vem do JWT mas NAO contamina o patch da UI (read-only).
        r = await _wrap_apply_table_state(
            surface="candidates", search="x", company_id="should-not-leak"
        )
        assert r["success"] is True
        assert "company_id" not in r["data"]["ui_action_params"]["patch"]
        assert "company_id" not in r["data"]["ui_action_params"]


class TestApplyTableStateFederationAndLoop:
    def test_tool_in_ui_tools(self):
        names = {t.name for t in get_ui_tools()}
        assert "apply_table_state" in names

    def test_tool_is_federated(self):
        assert "apply_table_state" in get_recruiter_copilot_tool_names(), (
            "apply_table_state deve estar no set federado do recruiter_copilot"
        )

    def test_apply_table_state_in_actionable_allowlist(self):
        assert "apply_table_state" in _ACTIONABLE_TOOL_UI_ACTIONS

    def test_extract_directive_surfaces_params(self):
        class _R:
            success = True
            result = {
                "data": {
                    "ui_action": "apply_table_state",
                    "ui_action_params": {
                        "surface": "candidates",
                        "patch": {"search": "x"},
                    },
                }
            }
        d = _extract_tool_directive(_R())
        assert d is not None
        assert d["ui_action"] == "apply_table_state"
        assert d["ui_action_params"]["surface"] == "candidates"
        assert d["ui_action_params"]["patch"] == {"search": "x"}


class TestApplyTableStateNotHitlGated:
    """apply_table_state e read-only UI — NUNCA pode entrar no gate HITL."""

    def test_tool_source_never_calls_hitl_preflight(self):
        import inspect
        import app.domains.recruiter_assistant.agents.ui_tool_registry as mod

        src = inspect.getsource(mod._wrap_apply_table_state)
        assert "hitl_preflight" not in src, (
            "apply_table_state e read-only — nao deve chamar hitl_preflight"
        )
