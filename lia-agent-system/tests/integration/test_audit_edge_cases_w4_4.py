"""
W4.4 — Audit edge case: analytics-only agents (sem entity_id no result).

Auditoria 2026-04-27 W3.3 v2 identificou que orchestrator audit
(main_orchestrator.py:1585-1605) e CONDITIONAL: so chama
AuditService.log_output quando result tem candidate_id/job_id/job_vacancy_id.

Agents analytics-only (analytics, company_settings) retornam AgentOutput
com apenas {message, actions, confidence, metadata} — sem entity_id.
Logo: NAO sao auditados pelo wrapper.

Decisao (W4.4): isso pode ser comportamento CORRETO para LGPD —
audit obrigatorio apenas para decisoes sobre individuos. Queries
analytics agregadas (ex: "5 candidatos no pipeline") nao tomam decisao
sobre individuo, nao precisam audit individual.

Estes testes documentam o edge case:
1. Confirma que orchestrator audit e conditional (nao gap)
2. Marca xfail os agents que poderiam precisar audit explicito mas
   nao tem (depende de decisao de produto / compliance officer)
"""
from __future__ import annotations
import inspect
import pytest


class TestOrchestratorAuditIsConditional:
    """Validate that orchestrator audit gate is documented and intentional."""

    def test_orchestrator_audit_is_conditional_on_entity_id(self):
        """main_orchestrator.py:1585 conditions audit on entity_id presence."""
        import app.orchestrator.execution.main_orchestrator as mod
        src = inspect.getsource(mod)
        assert "_should_audit = bool(" in src
        assert (
            'result.get("candidate_id") or result.get("job_id") or result.get("job_vacancy_id")'
            in src
        ), "Audit condition deve usar candidate_id/job_id/job_vacancy_id"

    @pytest.mark.xfail(
        reason=(
            "EDGE CASE W4.4: analytics_react_agent retorna AgentOutput sem "
            "entity_id no top-level. Orchestrator audit e CONDITIONAL — nao "
            "audita queries analytics agregadas. "
            "DECISAO PENDENTE (produto + compliance): "
            "  (a) Comportamento correto se queries sao agregadas (sem decisao individual)? "
            "  (b) Refatorar agent para incluir entity_id quando query envolve candidato/vaga especifico?"
        ),
        strict=False,
    )
    def test_analytics_agent_audits_when_query_involves_individual(self):
        """
        Cenario: analytics query envolve candidato especifico
        (ex: "qual o score do candidato X?") — deveria gerar audit.
        Hoje retorna AgentOutput sem candidate_id, audit nao dispara.
        """
        import app.domains.analytics.agents.analytics_react_agent as mod
        src = inspect.getsource(mod)
        # Looking for explicit audit_service.log_decision call OR
        # AgentOutput including candidate_id / job_id
        explicit_audit = "audit_service.log_decision" in src
        result_with_entity = (
            'AgentOutput(\n            message=' in src and
            ('candidate_id' in src or 'job_id' in src)
        )
        assert explicit_audit or result_with_entity, (
            "analytics agent must either audit explicitly OR include "
            "entity_id in AgentOutput when query involves individual"
        )


class TestAnalyticsAgentSafeByDefault:
    """Validate that analytics agents at least don't leak PII to logs."""

    def test_analytics_agent_inherits_pii_strip(self):
        """Auto-cobertura via LangGraphReActBase."""
        import inspect
        from app.domains.analytics.agents.analytics_react_agent import (
            AnalyticsReActAgent,
        )
        from lia_agents_core.langgraph_react_base import LangGraphReActBase
        assert issubclass(AnalyticsReActAgent, LangGraphReActBase)
        # PII strip vive em LangGraphReActBase:71-79 — heritage covers
        base_src = inspect.getsource(LangGraphReActBase)
        assert "strip_pii_for_llm_prompt" in base_src

    def test_analytics_agent_inherits_fairness_guard(self):
        """Auto-cobertura via EnhancedAgentMixin."""
        import inspect
        from app.domains.analytics.agents.analytics_react_agent import (
            AnalyticsReActAgent,
        )
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        assert issubclass(AnalyticsReActAgent, EnhancedAgentMixin)
