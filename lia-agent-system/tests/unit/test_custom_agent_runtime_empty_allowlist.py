"""P1-10: allowlist vazia no CustomAgentRuntime deve ser fail-closed.

Comportamento esperado após o fix:
  - allowed_tools=[] sem flag allow_all_tools explícita → agente recebe 0 tools
  - logger.warning emitido com agent_id + company_id para observabilidade
  - allowed_tools não-vazio → comportamento inalterado (ferramentas filtradas)

Comportamento BUG (antes do fix):
  - allowed_tools=[] → tool_names_to_use = list(all_available.keys())
    (acesso a TODAS as tools da plataforma — fail-open)
"""
from __future__ import annotations

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Fixture canônica (espelha test_custom_agent_runtime_fairness_fail_open) ─

@pytest.fixture(autouse=True)
def _patch_checkpointer_and_tenant():
    """Substitui get_checkpointer() e tenant snippet para testes unitários."""
    from unittest.mock import patch as _patch, AsyncMock as _AsyncMock
    with (
        _patch("lia_agents_core.langgraph_base.get_checkpointer", return_value=None),
        _patch(
            "app.shared.agents.tenant_aware_agent.TenantAwareAgentMixin._get_tenant_context_snippet",
            new_callable=_AsyncMock,
            return_value="",
        ),
    ):
        yield


# ─── helpers ─────────────────────────────────────────────────────────────────

def _make_runtime(allowed_tools: list[str], company_id: str = "comp-test-1"):
    from app.domains.agent_studio.custom_agent_runtime import CustomAgentRuntime
    return CustomAgentRuntime(
        agent_id="ag-allowlist-test",
        agent_name="AllowlistTestAgent",
        system_prompt="Você é um assistente.",
        allowed_tools=allowed_tools,
        company_id=company_id,
    )


def _fake_tool_definition(name: str):
    """Cria um ToolDefinition fake com função async stub."""
    td = MagicMock()
    td.name = name
    td.function = AsyncMock(return_value={"result": f"output_of_{name}"})
    td.model_copy = lambda update=None, **_kw: _merge_td(td, update or {})
    return td


def _merge_td(td, update: dict):
    copy = MagicMock()
    copy.name = td.name
    copy.function = update.get("function", td.function)
    return copy


# ─── Testes fail-closed ───────────────────────────────────────────────────────

class TestEmptyAllowlistFailClosed:
    """allowed_tools=[] não deve conceder acesso a todas as tools."""

    def test_empty_allowlist_returns_zero_tools(self):
        """_get_tools() com allowed_tools=[] deve retornar lista vazia."""
        runtime = _make_runtime(allowed_tools=[])

        fake_tools = [_fake_tool_definition(f"tool_{i}") for i in range(5)]

        with (
            patch.object(runtime, "_get_all_enhanced_tools", return_value=fake_tools),
            patch(
                "app.domains.agent_studio.custom_agent_runtime._load_domain_loaders",
                return_value={},
            ),
        ):
            tools = runtime._get_tools()

        assert tools == [], (
            "allowed_tools=[] deve resultar em 0 tools (fail-closed), "
            f"mas retornou {len(tools)} tools"
        )

    def test_empty_allowlist_emits_warning(self, caplog):
        """_get_tools() com allowed_tools=[] deve emitir logger.warning."""
        runtime = _make_runtime(allowed_tools=[])

        fake_tools = [_fake_tool_definition("some_tool")]

        with (
            patch.object(runtime, "_get_all_enhanced_tools", return_value=fake_tools),
            patch(
                "app.domains.agent_studio.custom_agent_runtime._load_domain_loaders",
                return_value={},
            ),
            caplog.at_level(logging.WARNING, logger="app.domains.agent_studio.custom_agent_runtime"),
        ):
            runtime._get_tools()

        warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("allowlist" in m.lower() or "allowed_tools" in m.lower() or "empty" in m.lower()
                   for m in warning_msgs), (
            f"Esperado warning sobre allowlist vazia, mas warnings foram: {warning_msgs}"
        )

    def test_empty_allowlist_warning_includes_agent_id(self, caplog):
        """Warning de allowlist vazia deve incluir agent_id para observabilidade."""
        runtime = _make_runtime(allowed_tools=[])

        with (
            patch.object(runtime, "_get_all_enhanced_tools", return_value=[_fake_tool_definition("t1")]),
            patch(
                "app.domains.agent_studio.custom_agent_runtime._load_domain_loaders",
                return_value={},
            ),
            caplog.at_level(logging.WARNING, logger="app.domains.agent_studio.custom_agent_runtime"),
        ):
            runtime._get_tools()

        all_log_text = " ".join(r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING)
        assert "ag-allowlist-test" in all_log_text, (
            f"agent_id 'ag-allowlist-test' deve aparecer no warning, log: {all_log_text!r}"
        )


class TestNonEmptyAllowlistUnchanged:
    """Comportamento com allowed_tools não-vazio não deve ser alterado pelo fix."""

    def test_nonempty_allowlist_returns_only_allowed_tools(self):
        """Com allowed_tools=['tool_0','tool_2'], apenas essas devem ser retornadas."""
        runtime = _make_runtime(allowed_tools=["tool_0", "tool_2"])

        fake_tools = [_fake_tool_definition(f"tool_{i}") for i in range(5)]

        with (
            patch.object(runtime, "_get_all_enhanced_tools", return_value=fake_tools),
            patch(
                "app.domains.agent_studio.custom_agent_runtime._load_domain_loaders",
                return_value={},
            ),
        ):
            tools = runtime._get_tools()

        returned_names = {t.name for t in tools}
        assert returned_names == {"tool_0", "tool_2"}, (
            f"Esperado {{'tool_0','tool_2'}}, retornou {returned_names}"
        )

    def test_nonempty_allowlist_no_spurious_warning(self, caplog):
        """Com allowed_tools não-vazio, não deve emitir warning de allowlist vazia."""
        runtime = _make_runtime(allowed_tools=["tool_1"])

        fake_tools = [_fake_tool_definition("tool_1")]

        with (
            patch.object(runtime, "_get_all_enhanced_tools", return_value=fake_tools),
            patch(
                "app.domains.agent_studio.custom_agent_runtime._load_domain_loaders",
                return_value={},
            ),
            caplog.at_level(logging.WARNING, logger="app.domains.agent_studio.custom_agent_runtime"),
        ):
            runtime._get_tools()

        allowlist_warnings = [
            r for r in caplog.records
            if r.levelno == logging.WARNING
            and ("allowlist" in r.getMessage().lower() or "allowed_tools" in r.getMessage().lower())
        ]
        assert allowlist_warnings == [], (
            f"Não esperado warning de allowlist, mas ocorreu: {allowlist_warnings}"
        )

    def test_nonempty_allowlist_tool_not_in_available_is_skipped(self):
        """Tools em allowed_tools que não existem em all_available são silenciosamente ignoradas."""
        runtime = _make_runtime(allowed_tools=["tool_0", "nonexistent_tool"])

        fake_tools = [_fake_tool_definition("tool_0")]

        with (
            patch.object(runtime, "_get_all_enhanced_tools", return_value=fake_tools),
            patch(
                "app.domains.agent_studio.custom_agent_runtime._load_domain_loaders",
                return_value={},
            ),
        ):
            tools = runtime._get_tools()

        returned_names = {t.name for t in tools}
        assert returned_names == {"tool_0"}, (
            f"'nonexistent_tool' não deve aparecer; retornou {returned_names}"
        )
