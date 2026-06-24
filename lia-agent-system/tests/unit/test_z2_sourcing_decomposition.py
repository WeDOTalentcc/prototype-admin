"""
Tests para Z2-02: SourcingReActAgent Decomposition — 4 subagentes especializados.

Cobre:
- _subagent_for_sourcing() — classificação correta por keyword
- FastRouter — patterns sourcing_planner/search/enrich/engagement
- AGENT_TYPE_TO_DOMAIN — 4 entradas sourcing adicionadas
- agent_model_config — modelos corretos por subagente
"""
import pytest


# ─── _subagent_for_sourcing ─────────────────────────────────────────────────

class TestSubagentForSourcing:
    def _fn(self, msg):
        from app.api.v1.chat_shared import _subagent_for_sourcing
        return _subagent_for_sourcing(msg)

    def test_engagement_abordagem(self):
        assert self._fn("enviar abordagem para candidato") == "sourcing_engagement"

    def test_engagement_outreach(self):
        assert self._fn("gerar outreach personalizado") == "sourcing_engagement"

    def test_engagement_mensagem_contato(self):
        assert self._fn("gerar mensagem de contato para o candidato") == "sourcing_engagement"

    def test_enrich_analisar_perfil(self):
        assert self._fn("analisar perfil do candidato João") == "sourcing_enrich"

    def test_enrich_shortlist(self):
        assert self._fn("adicionar shortlist top candidatos") == "sourcing_enrich"

    def test_enrich_comparar(self):
        assert self._fn("comparar candidatos para a vaga") == "sourcing_enrich"

    def test_search_talent_pool(self):
        assert self._fn("busca de talentos em Python") == "sourcing_search"

    def test_search_boolean(self):
        assert self._fn("boolean search para engenheiros") == "sourcing_search"

    def test_planner_criterios(self):
        assert self._fn("critérios de busca para vaga de dev") == "sourcing_planner"

    def test_planner_sugerir_skills(self):
        assert self._fn("sugerir skills para a vaga de marketing") == "sourcing_planner"

    def test_default_search_fallback(self):
        """Mensagens genéricas de sourcing → search (mais seguro)."""
        assert self._fn("preciso de candidatos para minha vaga") == "sourcing_search"

    def test_case_insensitive(self):
        assert self._fn("ABORDAGEM DO CANDIDATO") == "sourcing_engagement"


# ─── FastRouter patterns ─────────────────────────────────────────────────────

class TestFastRouterSourcingPatterns:
    def _router(self):
        from app.orchestrator.routing.fast_router import FastRouter
        return FastRouter()

    def test_sourcing_planner_criterios(self):
        r = self._router()
        result = r.match("critérios de busca para engenheiros")
        assert result is not None
        assert result.domain_id == "sourcing_planner"

    def test_sourcing_planner_sugerir_skills(self):
        r = self._router()
        result = r.match("sugerir skills para vaga de dados")
        assert result is not None
        assert result.domain_id == "sourcing_planner"

    def test_sourcing_search_talent_search(self):
        r = self._router()
        result = r.match("talent search para desenvolvedores")
        assert result is not None
        assert result.domain_id == "sourcing_search"

    def test_sourcing_enrich_shortlist(self):
        r = self._router()
        result = r.match("adicionar candidato ao shortlist")
        assert result is not None
        assert result.domain_id == "sourcing_enrich"

    def test_sourcing_engagement_outreach(self):
        r = self._router()
        result = r.match("enviar outreach para candidato")
        assert result is not None
        assert result.domain_id == "sourcing_engagement"


# ─── AGENT_TYPE_TO_DOMAIN ────────────────────────────────────────────────────

class TestCascadedRouterSourcingDomains:
    def test_all_sourcing_subagents_in_map(self):
        from app.orchestrator.routing.cascaded_router import AGENT_TYPE_TO_DOMAIN
        for domain in ("sourcing_planner", "sourcing_search", "sourcing_enrich", "sourcing_engagement"):
            assert domain in AGENT_TYPE_TO_DOMAIN, f"{domain} not in AGENT_TYPE_TO_DOMAIN"
            assert AGENT_TYPE_TO_DOMAIN[domain] == "sourcing"

    def test_original_sourcing_still_present(self):
        from app.orchestrator.routing.cascaded_router import AGENT_TYPE_TO_DOMAIN
        assert "sourcing" in AGENT_TYPE_TO_DOMAIN
        assert AGENT_TYPE_TO_DOMAIN["sourcing"] == "sourcing"


# ─── agent_model_config ──────────────────────────────────────────────────────

class TestAgentModelConfigSourcing:
    def test_sourcing_planner_uses_haiku(self):
        from app.core.agent_model_config import get_model_for_agent
        model = get_model_for_agent("sourcing_planner")
        assert "haiku" in model.lower()

    def test_sourcing_search_uses_haiku(self):
        from app.core.agent_model_config import get_model_for_agent
        model = get_model_for_agent("sourcing_search")
        assert "haiku" in model.lower()

    def test_sourcing_enrich_uses_sonnet(self):
        from app.core.agent_model_config import get_model_for_agent
        model = get_model_for_agent("sourcing_enrich")
        assert "sonnet" in model.lower()

    def test_sourcing_engagement_uses_sonnet(self):
        from app.core.agent_model_config import get_model_for_agent
        model = get_model_for_agent("sourcing_engagement")
        assert "sonnet" in model.lower()


# ─── LLM Cascade routing prompt ─────────────────────────────────────────────

class TestLLMCascadeRoutingPrompt:
    def test_sourcing_subdomains_in_prompt(self):
        from app.orchestrator.routing.llm_cascade import _ROUTING_PROMPT
        for subdomain in ("sourcing_planner", "sourcing_search", "sourcing_enrich", "sourcing_engagement"):
            assert subdomain in _ROUTING_PROMPT, f"{subdomain} not in _ROUTING_PROMPT"
