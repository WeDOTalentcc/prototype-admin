"""
End-to-end tests for domain consolidation.
Validates auto-discovery, routing normalization, and full pipeline execution.
"""
import pytest
import asyncio
from typing import Dict, List


# === SECTION 1: Auto-Discovery Tests ===

_CANONICAL_DOMAINS = {
    "sourcing", "job_management", "cv_screening",
    "communication", "analytics", "interview_scheduling",
    "ats_integration", "automation", "recruiter_assistant",
    "hiring_policy",
    # pipeline_transition is registered lazily when tests import PipelineTransitionAgent
    "pipeline_transition",
}


class TestDomainAutoDiscovery:
    """Verify canonical domains are auto-registered when app.domains is imported."""

    def test_all_domains_registered(self):
        """DomainRegistry should have at least 10 canonical domains after import."""
        from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        domains = set(registry.list_domains())
        assert len(domains) >= 10, f"Expected at least 10 domains, got {len(domains)}: {sorted(domains)}"

    def test_expected_domain_ids(self):
        """All canonical domain IDs should be a subset of registered domains."""
        from app.domains.registry import DomainRegistry
        # Force pipeline_transition to register (same as running full suite)
        import app.domains.pipeline.domain  # noqa: F401
        registry = DomainRegistry()
        domains = set(registry.list_domains())
        missing = _CANONICAL_DOMAINS - domains
        assert not missing, f"Missing canonical domains: {missing}"

    def test_domain_instantiation(self):
        """All registered domains should instantiate successfully."""
        from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        for domain_id in registry.list_domains():
            instance = registry.get_instance(domain_id)
            assert instance is not None, f"Failed to instantiate {domain_id}"
            assert instance.domain_id == domain_id

    def test_total_actions_count(self):
        """Total actions across all registered domains should be at least 208."""
        from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        all_actions = registry.get_all_actions()
        total = sum(len(actions) for actions in all_actions.values())
        assert total >= 208, f"Expected at least 208 total actions, got {total}"

    def test_actions_per_domain(self):
        """Each domain should have its expected action count."""
        from app.domains.registry import DomainRegistry
        registry = DomainRegistry()
        expected_counts = {
            "sourcing": 30,
            "job_management": 29,
            "cv_screening": 25,
            "communication": 20,
            "analytics": 18,
            "interview_scheduling": 20,
            "ats_integration": 18,
            "automation": 20,
            "recruiter_assistant": 20,
            "hiring_policy": 8,
            "pipeline_transition": 5,
        }
        all_actions = registry.get_all_actions()
        for domain_id, expected in expected_counts.items():
            actual = len(all_actions.get(domain_id, []))
            assert actual == expected, f"{domain_id}: expected {expected} actions, got {actual}"


# === SECTION 2: FastRouter Normalization Tests ===

class TestFastRouterNormalization:
    """Verify FastRouter outputs canonical domain IDs."""

    def setup_method(self):
        from app.orchestrator.routing.fast_router import FastRouter
        self.router = FastRouter()

    def test_job_management_routing(self):
        result = self.router.match("criar nova vaga de desenvolvedor")
        assert result is not None
        assert result.domain_id == "job_management"

    def test_sourcing_routing(self):
        result = self.router.match("buscar candidatos com python")
        assert result is not None
        assert result.domain_id == "sourcing"

    def test_cv_screening_routing(self):
        result = self.router.match("analisar cv do candidato")
        assert result is not None
        assert result.domain_id == "cv_screening"

    def test_wsi_normalizes_to_cv_screening(self):
        """wsi_assessment patterns should resolve to cv_screening."""
        result = self.router.match("avaliar score wsi do candidato")
        assert result is not None
        assert result.domain_id == "cv_screening", f"Expected cv_screening, got {result.domain_id}"

    def test_interviewing_normalizes_to_interview_scheduling(self):
        """interviewing patterns should resolve to interview_scheduling."""
        result = self.router.match("entrevistar candidato para a vaga")
        assert result is not None
        assert result.domain_id == "interview_scheduling", f"Expected interview_scheduling, got {result.domain_id}"

    def test_scheduling_normalizes_to_interview_scheduling(self):
        """scheduling patterns should resolve to interview_scheduling."""
        result = self.router.match("agendar entrevista para amanhã")
        assert result is not None
        assert result.domain_id == "interview_scheduling", f"Expected interview_scheduling, got {result.domain_id}"

    def test_pipeline_normalizes_to_analytics(self):
        """pipeline_management patterns should resolve to analytics."""
        result = self.router.match("relatório do pipeline de candidatos")
        assert result is not None
        assert result.domain_id == "analytics", f"Expected analytics, got {result.domain_id}"

    def test_task_normalizes_to_automation(self):
        """task_planning patterns should resolve to automation."""
        result = self.router.match("criar tarefa para o recrutador")
        assert result is not None
        assert result.domain_id == "automation", f"Expected automation, got {result.domain_id}"

    def test_communication_routing(self):
        result = self.router.match("enviar email para candidato")
        assert result is not None
        assert result.domain_id == "communication"

    def test_ats_integration_routing(self):
        result = self.router.match("sincronizar candidatos do gupy")
        assert result is not None
        assert result.domain_id == "ats_integration"

    def test_recruiter_assistant_routing(self):
        result = self.router.match("meu briefing do dia")
        assert result is not None
        assert result.domain_id == "recruiter_assistant"

    def test_all_normalized_ids_are_canonical(self):
        """Every possible FastRouter result should use a canonical domain ID."""
        from app.orchestrator.routing.fast_router import DOMAIN_PATTERNS, normalize_domain_id
        canonical_ids = {
            "sourcing", "job_management", "cv_screening",
            "communication", "analytics", "interview_scheduling",
            "ats_integration", "automation", "recruiter_assistant"
        }
        for pattern_id in DOMAIN_PATTERNS:
            normalized = normalize_domain_id(pattern_id)
            assert normalized in canonical_ids, f"Pattern ID '{pattern_id}' normalizes to '{normalized}' which is not canonical"


# === SECTION 3: CascadedRouter Tests ===

class TestCascadedRouterMapping:
    """Verify CascadedRouter maps agent types to canonical domain IDs."""

    def test_agent_type_to_domain_canonical(self):
        """All AGENT_TYPE_TO_DOMAIN values should be canonical domain IDs."""
        from app.orchestrator.routing.cascaded_router import AGENT_TYPE_TO_DOMAIN
        canonical_ids = {
            "sourcing", "job_management", "cv_screening",
            "communication", "analytics", "interview_scheduling",
            "ats_integration", "automation", "recruiter_assistant"
        }
        for agent_type, domain_id in AGENT_TYPE_TO_DOMAIN.items():
            assert domain_id in canonical_ids, f"Agent type '{agent_type}' maps to non-canonical '{domain_id}'"

    def test_wsi_evaluator_maps_to_cv_screening(self):
        from app.orchestrator.routing.cascaded_router import AGENT_TYPE_TO_DOMAIN
        assert AGENT_TYPE_TO_DOMAIN["wsi_evaluator"] == "cv_screening"

    def test_interviewer_maps_to_interview_scheduling(self):
        from app.orchestrator.routing.cascaded_router import AGENT_TYPE_TO_DOMAIN
        assert AGENT_TYPE_TO_DOMAIN["interviewer"] == "interview_scheduling"

    def test_task_planner_maps_to_automation(self):
        from app.orchestrator.routing.cascaded_router import AGENT_TYPE_TO_DOMAIN
        assert AGENT_TYPE_TO_DOMAIN["task_planner"] == "automation"

    def test_analytics_maps_to_analytics(self):
        from app.orchestrator.routing.cascaded_router import AGENT_TYPE_TO_DOMAIN
        assert AGENT_TYPE_TO_DOMAIN["analytics"] == "analytics"
        assert AGENT_TYPE_TO_DOMAIN["analyst_feedback"] == "analytics"


# === SECTION 4: Full Pipeline Tests ===

class TestFullPipelineE2E:
    """End-to-end: FastRouter → DomainRegistry → Domain.process_intent → IntentResult."""

    @pytest.fixture
    def setup_pipeline(self):
        from app.orchestrator.routing.fast_router import FastRouter
        from app.domains.registry import DomainRegistry
        from app.domains.base import DomainContext
        return FastRouter(), DomainRegistry(), DomainContext

    @pytest.mark.asyncio
    async def test_job_management_e2e(self, setup_pipeline):
        router, registry, DomainContext = setup_pipeline
        result = router.match("criar vaga de analista")
        assert result is not None
        domain = registry.get_instance(result.domain_id)
        assert domain is not None
        ctx = DomainContext(domain_id=result.domain_id, tenant_id="test", user_id="u1", session_id="s1")
        intent = await domain.process_intent("criar vaga de analista", ctx)
        assert intent is not None
        assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_cv_screening_e2e(self, setup_pipeline):
        router, registry, DomainContext = setup_pipeline
        result = router.match("analisar cv do candidato")
        assert result is not None
        assert result.domain_id == "cv_screening"
        domain = registry.get_instance(result.domain_id)
        assert domain is not None
        ctx = DomainContext(domain_id=result.domain_id, tenant_id="test", user_id="u1", session_id="s1")
        intent = await domain.process_intent("analisar cv do candidato", ctx)
        assert intent is not None

    @pytest.mark.asyncio
    async def test_interview_scheduling_e2e(self, setup_pipeline):
        router, registry, DomainContext = setup_pipeline
        result = router.match("agendar entrevista para segunda")
        assert result is not None
        assert result.domain_id == "interview_scheduling"
        domain = registry.get_instance(result.domain_id)
        assert domain is not None
        ctx = DomainContext(domain_id=result.domain_id, tenant_id="test", user_id="u1", session_id="s1")
        intent = await domain.process_intent("agendar entrevista para segunda", ctx)
        assert intent is not None

    @pytest.mark.asyncio
    async def test_analytics_e2e(self, setup_pipeline):
        router, registry, DomainContext = setup_pipeline
        result = router.match("análise do funil de candidatos")
        assert result is not None
        assert result.domain_id == "analytics"
        domain = registry.get_instance(result.domain_id)
        assert domain is not None
        ctx = DomainContext(domain_id=result.domain_id, tenant_id="test", user_id="u1", session_id="s1")
        intent = await domain.process_intent("análise do funil de candidatos", ctx)
        assert intent is not None

    @pytest.mark.asyncio
    async def test_automation_e2e(self, setup_pipeline):
        router, registry, DomainContext = setup_pipeline
        result = router.match("criar tarefa urgente")
        assert result is not None
        assert result.domain_id == "automation"
        domain = registry.get_instance(result.domain_id)
        assert domain is not None
        ctx = DomainContext(domain_id=result.domain_id, tenant_id="test", user_id="u1", session_id="s1")
        intent = await domain.process_intent("criar tarefa urgente", ctx)
        assert intent is not None

    @pytest.mark.asyncio
    async def test_recruiter_assistant_e2e(self, setup_pipeline):
        router, registry, DomainContext = setup_pipeline
        result = router.match("briefing do dia")
        assert result is not None
        assert result.domain_id == "recruiter_assistant"
        domain = registry.get_instance(result.domain_id)
        assert domain is not None
        ctx = DomainContext(domain_id=result.domain_id, tenant_id="test", user_id="u1", session_id="s1")
        intent = await domain.process_intent("briefing diário", ctx)
        assert intent is not None
        assert intent.action_id == "daily_briefing"

    @pytest.mark.asyncio
    async def test_all_domains_reachable_via_router(self, setup_pipeline):
        """Every canonical domain should be reachable via at least one FastRouter pattern."""
        router, registry, DomainContext = setup_pipeline
        test_queries = {
            "sourcing": "buscar candidatos para a vaga",
            "job_management": "criar vaga de emprego",
            "cv_screening": "triagem de currículos",
            "communication": "enviar email para candidato",
            "analytics": "relatório de pipeline",
            "interview_scheduling": "agendar entrevista",
            "ats_integration": "sync ats gupy",
            "automation": "criar tarefa",
            "recruiter_assistant": "briefing do dia",
        }
        for expected_domain, query in test_queries.items():
            result = router.match(query)
            assert result is not None, f"No FastRouter match for '{query}' (expected {expected_domain})"
            assert result.domain_id == expected_domain, f"'{query}' routed to {result.domain_id}, expected {expected_domain}"
            domain = registry.get_instance(result.domain_id)
            assert domain is not None, f"Domain {result.domain_id} not in registry"


# === SECTION 5: Backward Compatibility Tests ===

class TestBackwardCompatibility:
    """Verify original files still importable (no broken backward compat)."""

    def test_react_agents_importable(self):
        """ReAct agents should import correctly (replaced legacy RecruiterAssistantAgent)."""
        from app.domains.recruiter_assistant.agents.talent_react_agent import TalentReActAgent
        from app.domains.recruiter_assistant.agents.jobs_mgmt_react_agent import JobsManagementReActAgent
        assert TalentReActAgent is not None
        assert JobsManagementReActAgent is not None

    def test_original_services_importable(self):
        """Original service files should still import correctly."""
        from app.domains.recruiter_assistant.services.conversation_manager import ConversationManager
        assert ConversationManager is not None

    def test_existing_tests_not_broken(self):
        """Existing test suite should pass (checked separately, this is a marker test)."""
        pass


# === SECTION 6: CascadedRouter E2E ===

class TestCascadedRouterE2E:
    """Test CascadedRouter full pipeline."""

    @pytest.mark.asyncio
    async def test_cascaded_fast_routing(self):
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()
        result = await router.route("criar vaga de desenvolvedor senior")
        assert result.domain_id == "job_management"
        assert result.source == "fast_router"
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_cascaded_default_fallback(self):
        from unittest.mock import AsyncMock, patch as mock_patch
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()
        # Mock LLM cascade to return None so clarification_needed path is exercised
        # Fase 2: o fallback agora emite clarification em vez de retornar silenciosamente
        with mock_patch.object(router, "_route_via_llm_cascade", new=AsyncMock(return_value=None)):
            result = await router.route("xyzzy nonsense query 12345")
        assert result.domain_id == "recruiter_assistant"
        assert result.source == "clarification_needed"
        assert result.needs_clarification is True
        assert result.clarification_question is not None
        assert isinstance(result.clarification_options, list)

    @pytest.mark.asyncio
    async def test_cascaded_memory_cache(self):
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        router = CascadedRouter()
        result1 = await router.route("analisar cv do candidato")
        result2 = await router.route("analisar cv do candidato")
        assert result2.cached == True
        assert result2.domain_id == result1.domain_id
        stats = router.get_stats()
        assert stats["memory_hits"] >= 1

    @pytest.mark.asyncio
    async def test_cascaded_normalized_ids(self):
        """CascadedRouter should return canonical domain IDs."""
        from app.orchestrator.routing.cascaded_router import CascadedRouter
        canonical_ids = {
            "sourcing", "job_management", "cv_screening",
            "communication", "analytics", "interview_scheduling",
            "ats_integration", "automation", "recruiter_assistant"
        }
        router = CascadedRouter()
        queries = [
            "buscar candidatos",
            "criar vaga",
            "analisar cv",
            "enviar email candidato",
            "relatório pipeline",
            "agendar entrevista",
            "sync ats gupy",
            "criar tarefa",
            "briefing",
        ]
        for query in queries:
            result = await router.route(query)
            assert result.domain_id in canonical_ids, f"'{query}' returned non-canonical '{result.domain_id}'"
