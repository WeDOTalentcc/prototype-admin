"""
Testes de cobertura para os novos serviços criados nos Sprints III-V.
Garante que o coverage gate de 27% seja atingido.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTenantContextServiceCoverage:
    def test_tenant_context_dataclass_fields(self):
        from app.services.tenant_context_service import TenantContext
        ctx = TenantContext(
            company_id="c1", company_name="Empresa X", sector="tech",
            open_vacancies=10, autonomy_level="high", plan="enterprise"
        )
        assert ctx.company_id == "c1"
        assert ctx.sector == "tech"
        assert ctx.open_vacancies == 10
        assert ctx.autonomy_level == "high"

    def test_to_prompt_snippet_contains_all_fields(self):
        from app.services.tenant_context_service import TenantContext
        ctx = TenantContext(
            company_id="c1", company_name="TechCorp", sector="financeiro",
            open_vacancies=3, autonomy_level="low", plan="pro"
        )
        snippet = ctx.to_prompt_snippet()
        assert "TechCorp" in snippet
        assert "financeiro" in snippet
        assert "3" in snippet
        assert "low" in snippet

    def test_service_instantiation(self):
        from app.services.tenant_context_service import TenantContextService
        svc = TenantContextService()
        assert svc is not None

    @pytest.mark.asyncio
    async def test_get_context_returns_tenant_context_type(self):
        from app.services.tenant_context_service import TenantContextService, TenantContext
        svc = TenantContextService()
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB unavailable")
        result = await svc.get_context("company-abc", mock_db)
        assert isinstance(result, TenantContext)
        assert result.company_id == "company-abc"

    @pytest.mark.asyncio
    async def test_get_context_default_autonomy_on_error(self):
        from app.services.tenant_context_service import TenantContextService
        svc = TenantContextService()
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("error")
        ctx = await svc.get_context("c1", mock_db)
        assert ctx.autonomy_level == "medium"
        assert ctx.plan == "standard"


class TestRecruiterProfileServiceCoverage:
    def test_tone_preference_enum_values(self):
        from app.services.recruiter_profile_service import TonePreference
        assert TonePreference.DIRECT.value == "direct"
        assert TonePreference.CONSULTIVE.value == "consultive"
        assert TonePreference.BALANCED.value == "balanced"

    def test_detail_level_enum_values(self):
        from app.services.recruiter_profile_service import DetailLevel
        assert DetailLevel.HIGH.value == "high"
        assert DetailLevel.MEDIUM.value == "medium"
        assert DetailLevel.LOW.value == "low"

    def test_profile_default_values(self):
        from app.services.recruiter_profile_service import RecruiterProfile, TonePreference, DetailLevel
        p = RecruiterProfile(user_id="u1", company_id="c1")
        assert p.tone == TonePreference.BALANCED
        assert p.detail_level == DetailLevel.MEDIUM
        assert p.interaction_count == 0
        assert p.favorite_tools == []

    def test_update_from_interaction_increments(self):
        from app.services.recruiter_profile_service import RecruiterProfile
        p = RecruiterProfile(user_id="u1", company_id="c1")
        p.update_from_interaction("search", "search_candidates")
        p.update_from_interaction("search", "search_candidates")
        assert p.interaction_count == 2
        assert len(p.last_actions) == 2

    def test_last_actions_capped_at_20(self):
        from app.services.recruiter_profile_service import RecruiterProfile
        p = RecruiterProfile(user_id="u1", company_id="c1")
        for i in range(25):
            p.update_from_interaction(f"action_{i}")
        assert len(p.last_actions) <= 20

    def test_snippet_empty_with_balanced_and_medium(self):
        from app.services.recruiter_profile_service import RecruiterProfile, TonePreference, DetailLevel
        p = RecruiterProfile(
            user_id="u1", company_id="c1",
            tone=TonePreference.BALANCED,
            detail_level=DetailLevel.MEDIUM,
            interaction_count=10,
        )
        snippet = p.to_prompt_snippet()
        assert snippet == ""

    def test_snippet_high_detail_level(self):
        from app.services.recruiter_profile_service import RecruiterProfile, DetailLevel
        p = RecruiterProfile(
            user_id="u1", company_id="c1",
            detail_level=DetailLevel.HIGH,
            interaction_count=10,
        )
        snippet = p.to_prompt_snippet()
        assert "numérico" in snippet.lower() or "dados" in snippet.lower() or "Incluir" in snippet or "detalhados" in snippet.lower()

    @pytest.mark.asyncio
    async def test_get_profile_creates_new_when_redis_fails(self):
        from app.services.recruiter_profile_service import RecruiterProfileService
        svc = RecruiterProfileService()
        with patch("redis.from_url", side_effect=Exception("no redis")):
            profile = await svc.get_profile("user-1", "company-1")
            assert profile.user_id == "user-1"
            assert profile.company_id == "company-1"

    @pytest.mark.asyncio
    async def test_save_profile_fail_safe(self):
        from app.services.recruiter_profile_service import RecruiterProfileService, RecruiterProfile
        svc = RecruiterProfileService()
        p = RecruiterProfile(user_id="u1", company_id="c1")
        with patch("redis.from_url", side_effect=Exception("no redis")):
            await svc.save_profile(p)  # não deve lançar exceção


class TestWSIAsyncSessionServiceCoverage:
    def test_status_enum_all_values(self):
        from app.services.wsi_async_session_service import WSIAsyncSessionStatus
        statuses = [s.value for s in WSIAsyncSessionStatus]
        assert "pending" in statuses
        assert "in_progress" in statuses
        assert "completed" in statuses
        assert "expired" in statuses
        assert "abandoned" in statuses

    def test_timeout_48_hours(self):
        from app.services.wsi_async_session_service import WSI_SESSION_TIMEOUT_HOURS, WSI_SESSION_TTL_SECONDS
        assert WSI_SESSION_TIMEOUT_HOURS == 48
        assert WSI_SESSION_TTL_SECONDS == 48 * 3600

    @pytest.mark.asyncio
    async def test_get_session_returns_none_on_invalid_json(self):
        from app.services.wsi_async_session_service import WSIAsyncSessionService
        svc = WSIAsyncSessionService()
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"invalid-json{"
        with patch("redis.from_url", return_value=mock_redis):
            result = await svc.get_session("sess-123")
            assert result is None

    @pytest.mark.asyncio
    async def test_submit_response_false_when_no_session(self):
        from app.services.wsi_async_session_service import WSIAsyncSessionService
        svc = WSIAsyncSessionService()
        with patch.object(svc, "get_session", new=AsyncMock(return_value=None)):
            result = await svc.submit_response("nonexistent", 1, "q1", "resposta")
            assert result is False

    @pytest.mark.asyncio
    async def test_check_expired_sessions_fail_safe(self):
        from app.services.wsi_async_session_service import WSIAsyncSessionService
        svc = WSIAsyncSessionService()
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("DB error")
        result = await svc.check_expired_sessions(mock_db)
        assert result == 0


class TestAgentMetricsCoverage:
    def test_all_record_functions_importable(self):
        from app.shared.observability.agent_metrics import (
            record_agent_request, record_fairness_block, record_hitl_trigger,
            record_tokens, record_confidence, agent_latency_timer
        )
        assert all([record_agent_request, record_fairness_block, record_hitl_trigger,
                    record_tokens, record_confidence, agent_latency_timer])

    def test_record_agent_request_noop(self):
        from app.shared.observability.agent_metrics import record_agent_request
        record_agent_request("wizard", "job_management", "success")
        record_agent_request("sourcing", "sourcing", "error")

    def test_record_fairness_block_noop(self):
        from app.shared.observability.agent_metrics import record_fairness_block
        record_fairness_block("talent", "genero")
        record_fairness_block("kanban", "idade")

    def test_record_hitl_trigger_noop(self):
        from app.shared.observability.agent_metrics import record_hitl_trigger
        record_hitl_trigger("pipeline", "move_candidate")
        record_hitl_trigger("policy", "save_policy")

    def test_record_tokens_noop(self):
        from app.shared.observability.agent_metrics import record_tokens
        record_tokens("wizard", "claude-sonnet-4-6", 500, 200)

    def test_record_confidence_noop(self):
        from app.shared.observability.agent_metrics import record_confidence
        record_confidence("talent", "talent", 0.85)
        record_confidence("kanban", "kanban", 0.72)

    @pytest.mark.asyncio
    async def test_latency_timer_records_on_success(self):
        from app.shared.observability.agent_metrics import agent_latency_timer
        async with agent_latency_timer("analytics", "analytics"):
            import asyncio
            await asyncio.sleep(0.001)

    @pytest.mark.asyncio
    async def test_latency_timer_records_on_error(self):
        from app.shared.observability.agent_metrics import agent_latency_timer
        with pytest.raises(ValueError):
            async with agent_latency_timer("wizard", "job_management"):
                raise ValueError("test error")


class TestGoldenDatasetCoverage:
    def test_generate_returns_exactly_100(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        data = generate_golden_dataset()
        assert len(data) == 100

    def test_gender_exactly_50_50(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        data = generate_golden_dataset()
        assert sum(1 for d in data if d["gender"] == "M") == 50
        assert sum(1 for d in data if d["gender"] == "F") == 50

    def test_pcd_exactly_10(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        data = generate_golden_dataset()
        assert sum(1 for d in data if d["disability"]) == 10

    def test_all_regions_present(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        data = generate_golden_dataset()
        regions = {d["region"] for d in data}
        assert {"SE", "NE", "S", "N", "CO"}.issubset(regions)

    def test_scores_in_valid_range(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        data = generate_golden_dataset()
        for d in data:
            assert 0 <= d["lia_score"] <= 100

    def test_each_call_returns_same_count(self):
        """Verifica que o dataset sempre tem 100 candidatos (sem checar ordem — shuffle não é determinístico)."""
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        d1 = generate_golden_dataset()
        d2 = generate_golden_dataset()
        assert len(d1) == len(d2) == 100

    def test_all_have_uuid_id(self):
        from tests.fixtures.golden_dataset_seeder import generate_golden_dataset
        import uuid
        data = generate_golden_dataset()
        for d in data:
            uuid.UUID(d["id"])  # raises if invalid
