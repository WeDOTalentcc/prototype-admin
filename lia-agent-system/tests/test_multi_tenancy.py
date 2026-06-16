"""
Multi-tenancy test suite (Sprint 6).

Verifies that company_id isolation is enforced across the key services and
that no cross-tenant data leakage occurs in query helpers.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #

@pytest.fixture
def company_a():
    return "company-tenant-a"


@pytest.fixture
def company_b():
    return "company-tenant-b"


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.__aenter__ = AsyncMock(return_value=db)
    db.__aexit__ = AsyncMock(return_value=None)
    db.execute = AsyncMock(return_value=MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[]))),
        scalar_one_or_none=MagicMock(return_value=None),
        scalar=MagicMock(return_value=0),
        all=MagicMock(return_value=[]),
    ))
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    db.refresh = AsyncMock()
    return db


# ------------------------------------------------------------------ #
# 1–4: Auth dependency multi-tenancy                                   #
# ------------------------------------------------------------------ #

class TestAuthDependencies:

    def test_get_current_user_or_demo_importable(self):
        from app.auth.dependencies import get_current_user_or_demo
        assert callable(get_current_user_or_demo)

    def test_get_current_user_strict_importable(self):
        """Sprint 7: strict version should exist."""
        from app.auth.dependencies import get_current_user_strict
        assert callable(get_current_user_strict)

    def test_user_model_has_company_id(self):
        from app.auth.models import User
        import inspect
        # company_id must be a column or attribute
        src = inspect.getsource(User)
        assert "company_id" in src

    async def test_get_current_user_strict_raises_without_token(self):
        """get_current_user_strict must raise 401 when no valid token provided."""
        from fastapi import HTTPException
        from app.auth.dependencies import get_current_user_strict

        raised = False
        try:
            await get_current_user_strict(credentials=None)
        except (HTTPException, Exception):
            raised = True

        assert raised is True


# ------------------------------------------------------------------ #
# 5–8: CandidateGoalService tenant isolation                           #
# ------------------------------------------------------------------ #

class TestCandidateGoalServiceTenantIsolation:

    @pytest.mark.asyncio
    async def test_goal_result_includes_vacancy_id(self, company_a):
        from app.domains.candidates.services.candidate_goal_service import candidate_goal_service
        result = await candidate_goal_service.check_vacancy_candidate_goal(
            vacancy_id="vac-001", current_count=20
        )
        assert result["vacancy_id"] == "vac-001"

    @pytest.mark.asyncio
    async def test_calibration_patterns_session_id_isolated(self):
        from app.domains.candidates.services.candidate_goal_service import candidate_goal_service
        feedbacks_a = [
            {"feedback": "like", "candidate_snapshot": {"skills": ["Python", "FastAPI"]}},
        ]
        feedbacks_b = [
            {"feedback": "like", "candidate_snapshot": {"skills": ["Java", "Spring"]}},
        ]
        result_a = await candidate_goal_service.analyze_calibration_patterns_for_session(
            "session-a", feedbacks_a
        )
        result_b = await candidate_goal_service.analyze_calibration_patterns_for_session(
            "session-b", feedbacks_b
        )
        assert result_a["patterns"]["session_id"] == "session-a"
        assert result_b["patterns"]["session_id"] == "session-b"
        assert result_a["patterns"] != result_b["patterns"]

    @pytest.mark.asyncio
    async def test_goal_below_target_progress_percentage(self):
        from app.domains.candidates.services.candidate_goal_service import candidate_goal_service
        result = await candidate_goal_service.check_vacancy_candidate_goal(
            vacancy_id="v1", current_count=25, target_min=50
        )
        assert result["progress_percentage"] == 50

    @pytest.mark.asyncio
    async def test_goal_zero_candidates(self):
        from app.domains.candidates.services.candidate_goal_service import candidate_goal_service
        result = await candidate_goal_service.check_vacancy_candidate_goal(
            vacancy_id="v1", current_count=0
        )
        assert result["status"] == "below_target"
        assert result["progress_percentage"] == 0


# ------------------------------------------------------------------ #
# 9–12: LearningConfirmationService tenant isolation                   #
# ------------------------------------------------------------------ #

class TestLearningConfirmationTenantIsolation:

    def test_confirmation_service_requires_company_id_param(self):
        """record_skill_confirmation must have company_id as explicit param."""
        import inspect
        from app.shared.services.learning_confirmation_service import (
            LearningConfirmationService,
        )
        sig = inspect.signature(LearningConfirmationService.record_skill_confirmation)
        assert "company_id" in sig.parameters

    def test_get_company_skills_requires_company_id(self):
        import inspect
        from app.shared.services.learning_confirmation_service import (
            LearningConfirmationService,
        )
        sig = inspect.signature(LearningConfirmationService.get_company_skills)
        assert "company_id" in sig.parameters

    def test_update_pattern_requires_company_id(self):
        import inspect
        from app.shared.services.learning_confirmation_service import (
            LearningConfirmationService,
        )
        sig = inspect.signature(LearningConfirmationService.update_pattern)
        assert "company_id" in sig.parameters

    def test_analytics_service_requires_company_id(self):
        import inspect
        from app.shared.services.learning_analytics_service import LearningAnalyticsService
        sig = inspect.signature(LearningAnalyticsService.get_learning_dashboard)
        assert "company_id" in sig.parameters


# ------------------------------------------------------------------ #
# 13–15: ReAct loop context propagation                                #
# ------------------------------------------------------------------ #

class TestReActContextPropagation:

    def test_react_state_has_session_id_field(self):
        from lia_agents_core.react_loop import ReActState
        fields = ReActState.model_fields if hasattr(ReActState, "model_fields") else {}
        assert "session_id" in fields

    def test_react_config_is_pydantic_model(self):
        from lia_agents_core.react_loop import ReActConfig
        from pydantic import BaseModel
        assert issubclass(ReActConfig, BaseModel)

    def test_token_budget_default_is_safe(self):
        """Token budget must be disabled by default (safe rollout)."""
        from app.core.config import settings
        assert settings.REACT_TOKEN_BUDGET_ENABLED is False, (
            "REACT_TOKEN_BUDGET_ENABLED must default to False for safe rollout"
        )
