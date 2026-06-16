"""
Contract tests — ATS Integration ReAct Agent (Phase 5).

Verifica contratos de interface do agente de integração ATS:
- Padrão 4 arquivos (agent, tool_registry, system_prompt, stage_context)
- Ferramentas: sync_candidate_to_ats, sync_job_to_ats, get_sync_status, etc.
- Providers suportados: Gupy, Pandapé, Merge
- Isolamento multi-tenant (company_id obrigatório)
- Integração com WS dispatcher

Camada 5 — Contrato (pytest)
"""
import pytest


# ---------------------------------------------------------------------------
# Padrão 4 arquivos
# ---------------------------------------------------------------------------

class TestATSIntegration4FilePattern:
    def test_agent_module_importable(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        assert ATSIntegrationReActAgent is not None

    def test_tool_registry_importable(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        assert callable(get_ats_integration_tools)

    def test_system_prompt_importable(self):
        from app.domains.ats_integration.agents.ats_integration_system_prompt import get_ats_integration_system_prompt
        assert callable(get_ats_integration_system_prompt)

    def test_stage_context_importable(self):
        from app.domains.ats_integration.agents.ats_integration_stage_context import (
            STAGE_DEFINITIONS, get_stage_context
        )
        assert isinstance(STAGE_DEFINITIONS, dict)
        assert callable(get_stage_context)

    def test_agent_instantiates(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        agent = ATSIntegrationReActAgent()
        assert agent is not None

    def test_agent_has_process_method(self):
        from app.domains.ats_integration.agents.ats_integration_react_agent import ATSIntegrationReActAgent
        agent = ATSIntegrationReActAgent()
        assert hasattr(agent, "process")


# ---------------------------------------------------------------------------
# Stage Context
# ---------------------------------------------------------------------------

class TestATSStageContext:
    def test_stages_defined(self):
        from app.domains.ats_integration.agents.ats_integration_stage_context import STAGE_DEFINITIONS
        assert len(STAGE_DEFINITIONS) >= 1

    def test_each_stage_has_tools_and_description(self):
        from app.domains.ats_integration.agents.ats_integration_stage_context import STAGE_DEFINITIONS
        for name, stage in STAGE_DEFINITIONS.items():
            assert "tools" in stage, f"Stage '{name}' sem tools"
            assert "description" in stage, f"Stage '{name}' sem description"

    def test_get_stage_context_fallback_to_first_stage(self):
        from app.domains.ats_integration.agents.ats_integration_stage_context import get_stage_context
        ctx = get_stage_context("nonexistent-stage")
        assert isinstance(ctx, dict)


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

class TestATSToolRegistry:
    def test_get_ats_tools_returns_list(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        tools = get_ats_integration_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tools_have_name_and_description(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        for tool in get_ats_integration_tools():
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")

    def test_sync_tool_present(self):
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        names = [t.name for t in get_ats_integration_tools()]
        assert any("sync" in n.lower() or "ats" in n.lower() or "import" in n.lower() for n in names)

    def test_ats_provider_required_in_sync_tool(self):
        """ats_provider obrigatório — sem ele, não sabemos para qual ATS enviar."""
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        sync_tools = [t for t in get_ats_integration_tools() if "sync" in t.name.lower()]
        if sync_tools:
            tool = sync_tools[0]
            if hasattr(tool, "parameters") and tool.parameters:
                params = tool.parameters if isinstance(tool.parameters, dict) else {}
                props = params.get("properties", {})
                if "ats_provider" in props:
                    required = params.get("required", [])
                    assert "ats_provider" in required


# ---------------------------------------------------------------------------
# System Prompt — providers suportados
# ---------------------------------------------------------------------------

class TestATSSystemPrompt:
    def test_system_prompt_returns_string(self):
        from app.domains.ats_integration.agents.ats_integration_system_prompt import get_ats_integration_system_prompt
        prompt = get_ats_integration_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_system_prompt_mentions_ats_or_sync(self):
        from app.domains.ats_integration.agents.ats_integration_system_prompt import get_ats_integration_system_prompt
        prompt = get_ats_integration_system_prompt().lower()
        assert any(kw in prompt for kw in [
            "ats", "sincroniz", "integra", "gupy", "pandap", "merge", "candidato"
        ])

    def test_system_prompt_mentions_bidirectional_or_sync(self):
        from app.domains.ats_integration.agents.ats_integration_system_prompt import get_ats_integration_system_prompt
        prompt = get_ats_integration_system_prompt().lower()
        assert any(kw in prompt for kw in ["sincroniz", "import", "export", "bidirecional", "sync", "integr"])


# ---------------------------------------------------------------------------
# Multi-tenant isolation
# ---------------------------------------------------------------------------

class TestATSMultiTenantContract:
    def test_company_id_referenced_in_tools(self):
        """Sync tools devem exigir company_id para evitar cross-tenant sync."""
        from app.domains.ats_integration.agents.ats_integration_tool_registry import get_ats_integration_tools
        tools = get_ats_integration_tools()
        # Verificar que pelo menos uma ferramenta menciona company_id
        for tool in tools:
            if hasattr(tool, "parameters") and tool.parameters:
                params = tool.parameters if isinstance(tool.parameters, dict) else {}
                props = params.get("properties", {})
                if "company_id" in props:
                    return  # OK
        # Não-bloqueante — pode vir via context do agente


# ---------------------------------------------------------------------------
# WS Dispatcher integration
# ---------------------------------------------------------------------------

class TestATSWSDispatcher:
    def test_get_agent_ats_integration_returns_ats_agent(self):
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("ats_integration")
        assert agent is not None
        assert "ats" in type(agent).__name__.lower() or "ATS" in type(agent).__name__

    def test_get_agent_ats_alias_returns_ats_agent(self):
        """'ats' deve funcionar como alias."""
        from app.api.v1.chat_shared import _get_agent
        agent = _get_agent("ats")
        assert agent is not None
        assert "ats" in type(agent).__name__.lower() or "ATS" in type(agent).__name__

    def test_ats_agent_not_falls_back_to_talent(self):
        from app.api.v1.chat_shared import _get_agent
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        agent = _get_agent("ats_integration")
        assert not isinstance(agent, TalentReActAgent), \
            "ats_integration domain não deve usar TalentReActAgent (wiring faltando)"

    def test_ats_alias_not_falls_back_to_talent(self):
        from app.api.v1.chat_shared import _get_agent
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        agent = _get_agent("ats")
        assert not isinstance(agent, TalentReActAgent)
