"""
TDD: open_panel tool no wizard_tools.py

Verifica:
  1. ToolResult retorna mensagem canônica sem erro (sem sink)
  2. Best-effort: company_id no tool_input é rejeitado (REGRA multi-tenancy)
  3. OPEN_PANEL está em PURE_TOOLS (não em SERVICE_TOOLS — é I/O-free)
  4. Schema não aceita company_id (REGRA 2 — anti-tenant)
  5. Schema tem additionalProperties=False
"""
import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_ctx(company_id: str = "co-test") -> "ToolContext":
    from app.domains.job_creation.orchestrator.wizard_tools import ToolContext
    return ToolContext(company_id=company_id, user_id="u1")


# ── 1. ToolResult OK sem sink ─────────────────────────────────────────────────

def test_open_panel_returns_ok_no_sink():
    from app.domains.job_creation.orchestrator.wizard_tools import _handle_open_panel

    result = _handle_open_panel({}, {}, _make_ctx())

    assert result.error is False
    # Mensagem canônica confirma que o painel foi aberto
    assert "painel" in result.llm_message.lower()
    # state_updates sinaliza preferência de painel ao FE
    assert result.state_updates.get("panel_pref") == "expanded"


# ── 2. Rejeita company_id no tool_input (multi-tenancy fail-closed) ──────────

def test_open_panel_rejects_tenant_key_in_input():
    from app.domains.job_creation.orchestrator.wizard_tools import _handle_open_panel

    result = _handle_open_panel({}, {"company_id": "outra-empresa"}, _make_ctx())

    assert result.error is True
    # Mensagem de erro deve mencionar o campo proibido
    assert "company_id" in result.llm_message.lower()


# ── 3. OPEN_PANEL está em PURE_TOOLS ─────────────────────────────────────────

def test_open_panel_in_pure_tools():
    from app.domains.job_creation.orchestrator.wizard_tools import (
        PURE_TOOLS,
        OPEN_PANEL,
    )

    names = {t.name for t in PURE_TOOLS}
    assert "open_panel" in names, f"open_panel ausente em PURE_TOOLS: {names}"
    assert any(t is OPEN_PANEL for t in PURE_TOOLS)


# ── 4. Schema não aceita company_id (REGRA 2 Pydantic) ───────────────────────

def test_open_panel_schema_no_company_id():
    from app.domains.job_creation.orchestrator.wizard_tools import OPEN_PANEL

    props = OPEN_PANEL.input_schema.get("properties", {})
    assert "company_id" not in props, (
        "open_panel não deve aceitar company_id no schema (viola multi-tenancy)"
    )


# ── 5. Schema tem additionalProperties=False ──────────────────────────────────

def test_open_panel_schema_no_additional_properties():
    from app.domains.job_creation.orchestrator.wizard_tools import OPEN_PANEL

    assert OPEN_PANEL.input_schema.get("additionalProperties") is False, (
        "additionalProperties deve ser False para rejeitar campos extras inesperados"
    )


# ── 6. ToolResult OK idempotente — chamar duas vezes não lança ───────────────

def test_open_panel_idempotent():
    from app.domains.job_creation.orchestrator.wizard_tools import _handle_open_panel

    result1 = _handle_open_panel({}, {}, _make_ctx())
    result2 = _handle_open_panel({"panel_pref": "expanded"}, {}, _make_ctx())

    assert result1.error is False
    assert result2.error is False
