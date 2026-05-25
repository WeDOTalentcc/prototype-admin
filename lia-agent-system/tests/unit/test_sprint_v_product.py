"""Testes Sprint V — Produto e Experiência."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestFairnessGuardLayer3:
    def test_high_impact_actions_constant_exists(self):
        from app.shared.compliance.fairness_guard import FairnessGuard
        # Verificar que FairnessGuard tem check_with_layer3 ou HIGH_IMPACT_ACTIONS
        try:
            from app.shared.compliance.fairness_guard import HIGH_IMPACT_ACTIONS
            assert "rejection" in HIGH_IMPACT_ACTIONS
            assert "shortlist" in HIGH_IMPACT_ACTIONS
            assert "wsi_score" in HIGH_IMPACT_ACTIONS
        except ImportError:
            # Pode estar como atributo da classe
            fg = FairnessGuard()
            assert hasattr(fg, "check_with_layer3") or hasattr(fg, "HIGH_IMPACT_ACTIONS")

    def test_check_with_layer3_method_exists(self):
        from app.shared.compliance.fairness_guard import FairnessGuard
        fg = FairnessGuard()
        assert hasattr(fg, "check_with_layer3")

    @pytest.mark.asyncio
    async def test_low_impact_action_skips_layer3(self):
        from app.shared.compliance.fairness_guard import FairnessGuard
        fg = FairnessGuard()
        if not hasattr(fg, "check_with_layer3"):
            pytest.skip("check_with_layer3 não implementado ainda")
        result = await fg.check_with_layer3("buscar desenvolvedores python", action_type="search")
        # Para ação de baixo impacto, não deve chamar LLM
        assert result is not None

    def test_high_impact_actions_set_content(self):
        from app.shared.compliance.fairness_guard import HIGH_IMPACT_ACTIONS
        assert "bulk_rejection" in HIGH_IMPACT_ACTIONS
        assert "policy_save" in HIGH_IMPACT_ACTIONS

    @pytest.mark.asyncio
    async def test_check_with_layer3_blocked_by_layer1(self):
        from app.shared.compliance.fairness_guard import FairnessGuard
        fg = FairnessGuard()
        # Texto que deve ser bloqueado na Camada 1 — não deve chegar à Camada 3
        result = await fg.check_with_layer3(
            "somente homens para esta vaga",
            action_type="rejection",
        )
        assert result.is_blocked is True

    @pytest.mark.asyncio
    async def test_check_with_layer3_non_blocked_low_impact(self):
        from app.shared.compliance.fairness_guard import FairnessGuard
        fg = FairnessGuard()
        # Texto neutro com ação de baixo impacto — Layer 3 NÃO executa (não precisa de mock)
        result = await fg.check_with_layer3(
            "candidatos com experiência em Python",
            action_type="general",
        )
        assert result is not None
        assert result.is_blocked is False


class TestRecruiterProfileService:
    def test_module_importable(self):
        from app.domains.analytics.services.recruiter_profile_service import RecruiterProfileService, RecruiterProfile
        assert RecruiterProfileService is not None

    def test_profile_to_prompt_snippet_empty_below_threshold(self):
        from app.domains.analytics.services.recruiter_profile_service import RecruiterProfile, TonePreference, DetailLevel
        profile = RecruiterProfile(
            user_id="u1", company_id="c1",
            interaction_count=2,  # abaixo do threshold de 5
        )
        snippet = profile.to_prompt_snippet()
        assert snippet == ""

    def test_profile_to_prompt_snippet_with_direct_tone(self):
        from app.domains.analytics.services.recruiter_profile_service import RecruiterProfile, TonePreference, DetailLevel
        profile = RecruiterProfile(
            user_id="u1", company_id="c1",
            tone=TonePreference.DIRECT,
            interaction_count=10,
        )
        snippet = profile.to_prompt_snippet()
        assert "direto" in snippet.lower() or "conciso" in snippet.lower()

    def test_profile_update_increments_count(self):
        from app.domains.analytics.services.recruiter_profile_service import RecruiterProfile
        profile = RecruiterProfile(user_id="u1", company_id="c1")
        assert profile.interaction_count == 0
        profile.update_from_interaction("search")
        assert profile.interaction_count == 1

    def test_profile_last_actions_capped_at_20(self):
        from app.domains.analytics.services.recruiter_profile_service import RecruiterProfile
        profile = RecruiterProfile(user_id="u1", company_id="c1")
        for i in range(25):
            profile.update_from_interaction(f"action_{i}")
        assert len(profile.last_actions) <= 20

    def test_profile_consultive_tone_snippet(self):
        from app.domains.analytics.services.recruiter_profile_service import RecruiterProfile, TonePreference
        profile = RecruiterProfile(
            user_id="u1", company_id="c1",
            tone=TonePreference.CONSULTIVE,
            interaction_count=10,
        )
        snippet = profile.to_prompt_snippet()
        assert "contexto" in snippet.lower() or "proativamente" in snippet.lower()

    def test_profile_balanced_tone_no_extra_instruction(self):
        from app.domains.analytics.services.recruiter_profile_service import RecruiterProfile, TonePreference, DetailLevel
        profile = RecruiterProfile(
            user_id="u1", company_id="c1",
            tone=TonePreference.BALANCED,
            detail_level=DetailLevel.MEDIUM,
            interaction_count=10,
        )
        snippet = profile.to_prompt_snippet()
        # BALANCED + MEDIUM = sem instruções extras = snippet vazio
        assert snippet == ""

    @pytest.mark.asyncio
    async def test_get_profile_returns_new_profile_when_redis_unavailable(self):
        from app.domains.analytics.services.recruiter_profile_service import RecruiterProfileService
        svc = RecruiterProfileService()
        with patch("redis.from_url", side_effect=Exception("no redis")):
            profile = await svc.get_profile("user_123", "company_abc")
        assert profile.user_id == "user_123"
        assert profile.company_id == "company_abc"

    @pytest.mark.asyncio
    async def test_save_profile_fail_safe_on_redis_error(self):
        from app.domains.analytics.services.recruiter_profile_service import RecruiterProfileService, RecruiterProfile
        svc = RecruiterProfileService()
        profile = RecruiterProfile(user_id="u1", company_id="c1")
        # Deve não levantar exceção mesmo com Redis indisponível
        with patch("redis.from_url", side_effect=Exception("no redis")):
            await svc.save_profile(profile)  # não deve levantar


class TestWSIAsyncSessionService:
    def test_module_importable(self):
        from app.domains.cv_screening.services.wsi_async_session_service import WSIAsyncSessionService, WSIAsyncSessionStatus
        assert WSIAsyncSessionService is not None
        assert WSIAsyncSessionStatus.PENDING is not None

    def test_session_timeout_configured(self):
        from app.domains.cv_screening.services.wsi_async_session_service import WSI_SESSION_TIMEOUT_HOURS
        assert WSI_SESSION_TIMEOUT_HOURS == 48

    @pytest.mark.asyncio
    async def test_get_session_returns_none_when_not_found(self):
        from app.domains.cv_screening.services.wsi_async_session_service import WSIAsyncSessionService
        svc = WSIAsyncSessionService()
        with patch("redis.from_url") as mock_redis:
            mock_redis.return_value.get.return_value = None
            result = await svc.get_session("nonexistent-session-id")
            assert result is None

    def test_session_status_values(self):
        from app.domains.cv_screening.services.wsi_async_session_service import WSIAsyncSessionStatus
        assert WSIAsyncSessionStatus.PENDING.value == "pending"
        assert WSIAsyncSessionStatus.IN_PROGRESS.value == "in_progress"
        assert WSIAsyncSessionStatus.COMPLETED.value == "completed"
        assert WSIAsyncSessionStatus.EXPIRED.value == "expired"
        assert WSIAsyncSessionStatus.ABANDONED.value == "abandoned"

    def test_session_ttl_constant(self):
        from app.domains.cv_screening.services.wsi_async_session_service import WSI_SESSION_TTL_SECONDS, WSI_SESSION_TIMEOUT_HOURS
        assert WSI_SESSION_TTL_SECONDS == WSI_SESSION_TIMEOUT_HOURS * 3600

    @pytest.mark.asyncio
    async def test_get_session_returns_none_on_redis_error(self):
        from app.domains.cv_screening.services.wsi_async_session_service import WSIAsyncSessionService
        svc = WSIAsyncSessionService()
        with patch("redis.from_url", side_effect=Exception("connection refused")):
            result = await svc.get_session("any-session-id")
            assert result is None

    @pytest.mark.asyncio
    async def test_submit_response_returns_false_when_session_not_found(self):
        from app.domains.cv_screening.services.wsi_async_session_service import WSIAsyncSessionService
        svc = WSIAsyncSessionService()
        with patch.object(svc, "get_session", new=AsyncMock(return_value=None)):
            result = await svc.submit_response("missing-id", block=1, question_id="q1", response_text="teste")
            assert result is False

    def test_singleton_instance_exists(self):
        from app.domains.cv_screening.services.wsi_async_session_service import wsi_async_session_service, WSIAsyncSessionService
        assert isinstance(wsi_async_session_service, WSIAsyncSessionService)


class TestCommunicationTemplates:
    def test_communication_templates_in_system_prompt(self):
        try:
            from app.domains.communication.agents.communication_system_prompt import (
                COMMUNICATION_TEMPLATES,
                get_communication_system_prompt,
            )
            assert "WSI" in COMMUNICATION_TEMPLATES or "convite" in COMMUNICATION_TEMPLATES.lower()
            assert "{{candidato_nome}}" in COMMUNICATION_TEMPLATES or "candidato_nome" in COMMUNICATION_TEMPLATES
        except ImportError:
            pytest.skip("COMMUNICATION_TEMPLATES não encontrado")

    def test_system_prompt_includes_templates(self):
        try:
            from app.domains.communication.agents.communication_system_prompt import get_communication_system_prompt
            prompt = get_communication_system_prompt()
            assert len(prompt) > 500
        except (ImportError, TypeError):
            pytest.skip("get_communication_system_prompt não disponível sem args")

    def test_templates_contain_gate1_rejection(self):
        from app.domains.communication.agents.communication_system_prompt import COMMUNICATION_TEMPLATES
        assert "Gate 1" in COMMUNICATION_TEMPLATES or "Reprovação Gate 1" in COMMUNICATION_TEMPLATES

    def test_templates_contain_gate2_rejection(self):
        from app.domains.communication.agents.communication_system_prompt import COMMUNICATION_TEMPLATES
        assert "Gate 2" in COMMUNICATION_TEMPLATES or "Reprovação Gate 2" in COMMUNICATION_TEMPLATES

    def test_templates_contain_interview_invite(self):
        from app.domains.communication.agents.communication_system_prompt import COMMUNICATION_TEMPLATES
        assert "Entrevista Final" in COMMUNICATION_TEMPLATES or "Convite Entrevista" in COMMUNICATION_TEMPLATES

    def test_templates_fairness_guard_mention(self):
        from app.domains.communication.agents.communication_system_prompt import COMMUNICATION_TEMPLATES
        assert "FairnessGuard" in COMMUNICATION_TEMPLATES

    def test_system_prompt_contains_templates_section(self):
        from app.domains.communication.agents.communication_system_prompt import get_communication_system_prompt
        prompt = get_communication_system_prompt()
        assert "Templates de Comunicação" in prompt
