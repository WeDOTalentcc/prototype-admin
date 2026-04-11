"""
Tests for SourcingReActAgent (nova arquitetura DDD).

Cobre:
- Happy path: busca de candidatos por perfil
- Company/user ID propagação para observabilidade
- Configurações via settings
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSourcingReActAgentImport:
    """Importações e instanciação."""

    def test_agent_importable(self):
        """SourcingReActAgent importável de app.domains.sourcing."""
        from app.domains.sourcing.agents.sourcing_react_agent import SourcingReActAgent
        agent = SourcingReActAgent()
        assert agent is not None


class TestSourcingAgentObservability:
    """Observabilidade: company_id e user_id propagados."""

    def test_react_observer_accepts_company_user_id(self):
        """ReActObserver deve aceitar company_id e user_id."""
        from lia_agents_core.observability import ReActObserver
        observer = ReActObserver(
            session_id="session-sourcing-test",
            domain="sourcing",
            agent_class="SourcingReActAgent",
            company_id="company-001",
            user_id="user-001",
        )
        assert observer.company_id == "company-001"
        assert observer.user_id == "user-001"

    def test_agent_execution_log_has_company_user(self):
        """AgentExecutionLog deve ter campos company_id e user_id."""
        from lia_agents_core.observability import AgentExecutionLog
        log = AgentExecutionLog(
            session_id="session-test-001",
            domain="sourcing",
            agent_class="SourcingReActAgent",
            start_time="2026-01-01T00:00:00+00:00",
            company_id="company-001",
            user_id="user-001",
        )
        assert log.company_id == "company-001"
        assert log.user_id == "user-001"


class TestSourcingSettings:
    """Configurações do sistema (magic numbers externalizados)."""

    def test_no_hardcoded_model_names_in_config(self):
        """Modelos LLM devem estar em settings, não hardcoded."""
        from app.core.config import settings
        assert hasattr(settings, "LLM_PRIMARY_MODEL")
        assert "claude" in settings.LLM_PRIMARY_MODEL.lower()
        assert hasattr(settings, "LLM_FAST_MODEL")
        assert hasattr(settings, "LLM_POWERFUL_MODEL")

    def test_cascade_thresholds_in_settings(self):
        """Thresholds de cascata LLM devem estar em settings."""
        from app.core.config import settings
        assert 0 < settings.LLM_CASCADE_FAST_THRESHOLD <= 1.0
        assert 0 < settings.LLM_CASCADE_MID_THRESHOLD <= 1.0
        assert 0 < settings.LLM_CASCADE_FALLBACK_THRESHOLD <= 1.0
        # Fast threshold deve ser mais restritivo
        assert settings.LLM_CASCADE_FAST_THRESHOLD > settings.LLM_CASCADE_MID_THRESHOLD


class TestSourcingToolRegistry:
    """Tool registry and system prompt."""

    def test_sourcing_tool_registry_importable(self):
        from app.domains.sourcing.agents.sourcing_tool_registry import get_sourcing_tools
        tools = get_sourcing_tools()
        assert isinstance(tools, list) and len(tools) > 0

    def test_sourcing_system_prompt_importable(self):
        from app.domains.sourcing.agents.sourcing_system_prompt import (
            SOURCING_SYSTEM_PROMPT,
        )
        assert isinstance(SOURCING_SYSTEM_PROMPT, str)
        assert len(SOURCING_SYSTEM_PROMPT) > 50

    def test_sourcing_stage_context_importable(self):
        from app.domains.sourcing.agents.sourcing_stage_context import (
            get_stage_context,
        )
        assert callable(get_stage_context)

    def test_sourcing_system_prompt_no_hardcoded_demo_company(self):
        from app.domains.sourcing.agents.sourcing_system_prompt import (
            SOURCING_SYSTEM_PROMPT,
        )
        assert "demo_company" not in SOURCING_SYSTEM_PROMPT


class TestSourcingCandidateGoalService:
    """CandidateGoalService pure-logic tests."""

    @pytest.mark.asyncio
    async def test_check_vacancy_goal_below_target(self):
        from app.domains.candidates.services.candidate_goal_service import candidate_goal_service
        result = await candidate_goal_service.check_vacancy_candidate_goal(
            vacancy_id="v1", current_count=10, target_min=50, target_max=70
        )
        assert result["status"] == "below_target"
        assert result["deficit"] == 40

    @pytest.mark.asyncio
    async def test_check_vacancy_goal_on_target(self):
        from app.domains.candidates.services.candidate_goal_service import candidate_goal_service
        result = await candidate_goal_service.check_vacancy_candidate_goal(
            vacancy_id="v1", current_count=55, target_min=50, target_max=70
        )
        assert result["status"] == "on_target"

    @pytest.mark.asyncio
    async def test_check_vacancy_goal_above_target(self):
        from app.domains.candidates.services.candidate_goal_service import candidate_goal_service
        result = await candidate_goal_service.check_vacancy_candidate_goal(
            vacancy_id="v1", current_count=80, target_min=50, target_max=70
        )
        assert result["status"] == "above_target"
        assert result["surplus"] == 10
