"""Manus F1 — tools open_panel/close_panel (padrão navigate_to_jobs)."""
from __future__ import annotations

from app.domains.job_creation.orchestrator.wizard_tools import (
    OPEN_PANEL,
    CLOSE_PANEL,
    PURE_TOOLS,
    ToolContext,
    _handle_open_panel,
    _handle_close_panel,
)

CTX = ToolContext(company_id="c1")


def test_tools_registradas_em_pure_tools():
    names = {t.name for t in PURE_TOOLS}
    assert "open_panel" in names
    assert "close_panel" in names


def test_open_panel_seta_panel_pref_expanded():
    res = _handle_open_panel({}, {}, CTX)
    assert res.error is not True
    assert res.state_updates == {"panel_pref": "expanded"}
    assert "painel" in res.llm_message.lower()


def test_close_panel_seta_panel_pref_docked():
    res = _handle_close_panel({}, {}, CTX)
    assert res.error is not True
    assert res.state_updates == {"panel_pref": "docked"}


def test_schema_sem_propriedades_e_fechado():
    for tool in (OPEN_PANEL, CLOSE_PANEL):
        assert tool.input_schema["properties"] == {}
        assert tool.input_schema["additionalProperties"] is False


def test_rejeita_tenant_keys_no_input():
    res = _handle_open_panel({}, {"company_id": "x"}, CTX)
    assert res.error is True
