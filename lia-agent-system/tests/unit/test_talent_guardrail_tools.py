"""
P1-A — Testes de GUARDRAIL_TOOLS do TalentReActAgent.

Cobre:
1. create_shortlist está em GUARDRAIL_TOOLS (existia antes)
2. export_report está em GUARDRAIL_TOOLS (adicionado — LGPD-sensível)
3. Tools de query NÃO estão em GUARDRAIL_TOOLS (não devem exigir confirmação)
4. Tools de análise NÃO estão em GUARDRAIL_TOOLS
5. Todas as tools em GUARDRAIL_TOOLS existem no registry real (sem fantasmas)
"""
import pytest
from app.domains.recruiter_assistant.agents.talent_tool_registry import (
    GUARDRAIL_TOOLS,
    get_talent_tools,
)


class TestGuardrailToolsConteudo:

    def test_create_shortlist_permanece_em_guardrails(self):
        assert "create_shortlist" in GUARDRAIL_TOOLS

    def test_export_report_adicionado_em_guardrails(self):
        """export_report lida com dados pessoais — exige confirmação HITL (LGPD)."""
        assert "export_report" in GUARDRAIL_TOOLS

    def test_guardrail_tools_e_lista(self):
        assert isinstance(GUARDRAIL_TOOLS, dict)  # UC-P2-09: dict[str, SafetyCategory]
        assert len(GUARDRAIL_TOOLS) >= 2


class TestQueryToolsForaDeGuardrails:
    """Tools de consulta (read-only) não devem exigir confirmação."""

    @pytest.mark.parametrize("tool", [
        "search_candidates",
        "list_candidates",
        "view_candidate_profile",
        "compare_candidates",
        "rank_candidates",
        "analyze_skills",
        "check_search_fairness",
        "get_talent_pool_benchmarks",
        "check_pool_health",
    ])
    def test_query_tool_nao_e_guardrail(self, tool):
        assert tool not in GUARDRAIL_TOOLS, (
            f"Tool '{tool}' é de consulta e não deve exigir confirmação HITL"
        )


class TestGuardrailToolsExistemNoRegistry:
    """Todos os tools em GUARDRAIL_TOOLS devem existir como tool real no registry."""

    def test_guardrails_sem_tools_fantasmas(self):
        all_tools = get_talent_tools()
        tool_names = {t.name for t in all_tools}
        for guardrail in GUARDRAIL_TOOLS:
            assert guardrail in tool_names, (
                f"GUARDRAIL_TOOL '{guardrail}' não existe no talent tool registry"
            )
