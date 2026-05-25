"""
Coverage Boost — Serviços sem cobertura.

Targets:
- app/services/sector_benchmark_service.py  (303 linhas)
- app/services/agent_quality_evaluator.py   (232 linhas)
- app/services/candidate_channel_selector.py (158 linhas)
- app/services/consent_checker_service.py   (267 linhas)

Total: ~960 linhas. Cobertura estimada: ~70% = +672 linhas.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


# =============================================================================
# sector_benchmark_service.py
# =============================================================================

class TestSectorBenchmarkServiceImport:
    """Apenas importar o módulo cobre 80%+ das linhas (constantes/dataclasses)."""

    def test_import_succeeds(self):
        from app.domains.analytics.services.sector_benchmark_service import sector_benchmark_service, SectorBenchmarkService
        assert sector_benchmark_service is not None
        assert isinstance(sector_benchmark_service, SectorBenchmarkService)

    def test_benchmark_profile_dataclass_exists(self):
        from app.domains.analytics.services.sector_benchmark_service import BenchmarkProfile
        assert BenchmarkProfile is not None

    def test_benchmarks_dict_has_entries(self):
        from app.domains.analytics.services.sector_benchmark_service import _BENCHMARKS
        assert len(_BENCHMARKS) >= 12  # at least 4 areas × 3 levels

    def test_area_aliases_populated(self):
        from app.domains.analytics.services.sector_benchmark_service import _AREA_ALIASES
        assert "software" in _AREA_ALIASES
        assert _AREA_ALIASES["software"] == "software_engineering"
        assert "dev" in _AREA_ALIASES
        assert "data" in _AREA_ALIASES

    def test_seniority_aliases_populated(self):
        from app.domains.analytics.services.sector_benchmark_service import _SENIORITY_ALIASES
        assert "jr" in _SENIORITY_ALIASES
        assert _SENIORITY_ALIASES["jr"] == "junior"
        assert "sr" in _SENIORITY_ALIASES
        assert "mid" in _SENIORITY_ALIASES


class TestNormalizeArea:
    def test_empty_string_returns_none(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        assert _normalize_area("") is None

    def test_none_like_returns_none(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        assert _normalize_area("") is None

    def test_alias_software_resolves(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        assert _normalize_area("software") == "software_engineering"

    def test_alias_dev_resolves(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        assert _normalize_area("dev") == "software_engineering"

    def test_alias_data_resolves(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        assert _normalize_area("data") == "data_science"

    def test_alias_produto_resolves(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        assert _normalize_area("produto") == "product_management"

    def test_canonical_software_engineering(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        assert _normalize_area("software_engineering") == "software_engineering"

    def test_unknown_area_returns_none(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        assert _normalize_area("unknown_area_xyz") is None

    def test_case_insensitive(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        assert _normalize_area("SOFTWARE") == "software_engineering"

    def test_spaces_normalized(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_area
        result = _normalize_area("software engineering")
        assert result == "software_engineering"


class TestNormalizeSeniority:
    def test_empty_returns_none(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("") is None

    def test_jr_alias(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("jr") == "junior"

    def test_sr_alias(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("sr") == "senior"

    def test_mid_alias(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("mid") == "pleno"

    def test_canonical_junior(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("junior") == "junior"

    def test_canonical_pleno(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("pleno") == "pleno"

    def test_canonical_senior(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("senior") == "senior"

    def test_canonical_staff(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("staff") == "staff"

    def test_unknown_returns_none(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("unknown_level") is None

    def test_trainee_alias(self):
        from app.domains.analytics.services.sector_benchmark_service import _normalize_seniority
        assert _normalize_seniority("trainee") == "junior"


class TestSectorBenchmarkServiceGetContext:
    def setup_method(self):
        from app.domains.analytics.services.sector_benchmark_service import SectorBenchmarkService
        self.svc = SectorBenchmarkService()

    def test_returns_string(self):
        ctx = self.svc.get_benchmark_context("software_engineering", "senior")
        assert isinstance(ctx, str)

    def test_returns_non_empty_for_known_area_seniority(self):
        ctx = self.svc.get_benchmark_context("software_engineering", "senior")
        assert len(ctx) > 0

    def test_contains_p50_line(self):
        ctx = self.svc.get_benchmark_context("software_engineering", "pleno")
        assert "P50" in ctx or "mediano" in ctx

    def test_contains_calibration_note(self):
        ctx = self.svc.get_benchmark_context("software_engineering", "junior")
        assert "CALIBRAÇÃO" in ctx or "calibr" in ctx.lower()

    def test_empty_for_unknown_area(self):
        ctx = self.svc.get_benchmark_context("unknown_area", "senior")
        assert ctx == ""

    def test_empty_for_unknown_seniority(self):
        ctx = self.svc.get_benchmark_context("software_engineering", "unknown_level")
        assert ctx == ""

    def test_empty_for_empty_inputs(self):
        ctx = self.svc.get_benchmark_context("", "")
        assert ctx == ""

    def test_alias_resolves_software(self):
        ctx = self.svc.get_benchmark_context("software", "senior")
        assert len(ctx) > 0

    def test_alias_resolves_jr(self):
        ctx = self.svc.get_benchmark_context("data_science", "jr")
        assert len(ctx) > 0

    def test_data_science_pleno_has_mlops_signal(self):
        ctx = self.svc.get_benchmark_context("data_science", "senior")
        assert "MLOps" in ctx or "ML" in ctx or "dados" in ctx.lower()

    def test_list_supported_returns_list(self):
        supported = self.svc.list_supported()
        assert isinstance(supported, list)
        assert len(supported) >= 12

    def test_get_profile_known(self):
        profile = self.svc.get_profile("software_engineering", "senior")
        assert profile is not None
        assert profile.seniority == "senior"
        assert profile.score_p50 > 0

    def test_get_profile_unknown_returns_none(self):
        profile = self.svc.get_profile("unknown_area", "unknown_level")
        assert profile is None

    def test_get_profile_resolves_alias(self):
        profile = self.svc.get_profile("software", "sr")
        assert profile is not None

    def test_benchmark_profile_frozen(self):
        from app.domains.analytics.services.sector_benchmark_service import BenchmarkProfile
        # frozen=True means no assignment
        profile = BenchmarkProfile(
            area="test", seniority="junior",
            score_p50=40.0, score_p75=55.0, min_expected=30.0,
            approval_rate=0.35, key_signals=("sig1",),
            calibration_note="note"
        )
        with pytest.raises((AttributeError, TypeError)):
            profile.area = "changed"  # type: ignore


# =============================================================================
# agent_quality_evaluator.py
# =============================================================================

class TestAgentQualityEvaluatorImport:
    def test_import_module(self):
        from app.domains.ai.services.agent_quality_evaluator import agent_quality_evaluator, AgentQualityEvaluator
        assert agent_quality_evaluator is not None

    def test_sampling_rate_constant(self):
        from app.domains.ai.services.agent_quality_evaluator import QUALITY_EVAL_SAMPLING_RATE
        assert 0.0 <= QUALITY_EVAL_SAMPLING_RATE <= 1.0

    def test_eval_metrics_have_5_entries(self):
        from app.domains.ai.services.agent_quality_evaluator import EVAL_METRICS
        assert len(EVAL_METRICS) == 5
        assert "task_completion" in EVAL_METRICS
        assert "fairness" in EVAL_METRICS

    def test_evaluation_result_dataclass(self):
        from app.domains.ai.services.agent_quality_evaluator import EvaluationResult
        from datetime import datetime
        result = EvaluationResult(
            agent_id="wizard",
            company_id="company-123",
            session_id="sess-1",
            scores={"task_completion": 0.9},
            overall_score=0.9,
        )
        assert result.agent_id == "wizard"
        assert isinstance(result.evaluated_at, datetime)


class TestAgentQualityEvaluatorSampling:
    @pytest.mark.asyncio
    async def test_evaluate_if_sampled_returns_none_when_not_sampled(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator
        evaluator = AgentQualityEvaluator()
        # patch random.random to return 0.99 (above any sampling rate)
        with patch("app.services.agent_quality_evaluator.random.random", return_value=0.99):
            result = await evaluator.evaluate_if_sampled(
                agent_id="wizard",
                user_message="hello",
                agent_response="world",
                context={},
                company_id="company-1",
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_evaluate_if_sampled_catches_exception_returns_none(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator
        evaluator = AgentQualityEvaluator()
        # Sample (random returns 0.0) but evaluate_response raises
        with patch("app.services.agent_quality_evaluator.random.random", return_value=0.0):
            with patch.object(evaluator, "evaluate_response", side_effect=RuntimeError("boom")):
                result = await evaluator.evaluate_if_sampled(
                    agent_id="wizard",
                    user_message="hello",
                    agent_response="world",
                    context={},
                    company_id="company-1",
                )
        assert result is None

    @pytest.mark.asyncio
    async def test_evaluate_if_sampled_returns_result_when_sampled(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator, EvaluationResult
        evaluator = AgentQualityEvaluator()
        mock_result = EvaluationResult(
            agent_id="wizard", company_id="c-1", session_id=None,
            scores={"task_completion": 0.8}, overall_score=0.8
        )
        with patch("app.services.agent_quality_evaluator.random.random", return_value=0.0):
            with patch.object(evaluator, "evaluate_response", return_value=mock_result):
                result = await evaluator.evaluate_if_sampled(
                    agent_id="wizard",
                    user_message="hello",
                    agent_response="world",
                    context={},
                    company_id="c-1",
                )
        assert result is mock_result


class TestAgentQualityEvaluatorJudge:
    @pytest.mark.asyncio
    async def test_judge_returns_05_on_anthropic_exception(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator
        evaluator = AgentQualityEvaluator()
        # anthropic is imported inside the function; patch it in anthropic namespace
        with patch("anthropic.AsyncAnthropic", side_effect=RuntimeError("no api")):
            score = await evaluator._judge("question?", "user msg", "agent resp")
        assert score == 0.5

    @pytest.mark.asyncio
    async def test_judge_returns_05_on_runtime_error(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator
        evaluator = AgentQualityEvaluator()
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(side_effect=RuntimeError("api error"))
        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            score = await evaluator._judge("question?", "user msg", "agent resp")
        assert score == 0.5

    @pytest.mark.asyncio
    async def test_judge_clamps_score_above_1(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator
        evaluator = AgentQualityEvaluator()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="1.5")]
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            score = await evaluator._judge("q", "u", "a")
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_judge_clamps_score_below_0(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator
        evaluator = AgentQualityEvaluator()
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="-0.5")]
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(return_value=mock_message)
        with patch("anthropic.AsyncAnthropic", return_value=mock_client):
            score = await evaluator._judge("q", "u", "a")
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_send_to_langsmith_silent_without_api_key(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator, EvaluationResult
        evaluator = AgentQualityEvaluator()
        result = EvaluationResult(
            agent_id="test", company_id="c-1", session_id=None,
            scores={}, overall_score=0.8
        )
        # No LANGSMITH_API_KEY set — should return without error
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("LANGSMITH_API_KEY", None)
            await evaluator._send_to_langsmith(result, "user msg", "agent resp")
        # No exception = pass

    @pytest.mark.asyncio
    async def test_evaluate_response_computes_overall_correctly(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator, EVAL_METRICS
        evaluator = AgentQualityEvaluator()
        # All judges return 0.8
        with patch.object(evaluator, "_judge", return_value=0.8):
            with patch.object(evaluator, "_send_to_langsmith", return_value=None):
                result = await evaluator.evaluate_response(
                    agent_id="wizard",
                    user_message="hello",
                    agent_response="world",
                    context={},
                    company_id="c-1",
                )
        assert abs(result.overall_score - 0.8) < 0.001
        assert len(result.scores) == len(EVAL_METRICS)

    @pytest.mark.asyncio
    async def test_evaluate_response_persists_when_db_provided(self):
        from app.domains.ai.services.agent_quality_evaluator import AgentQualityEvaluator
        evaluator = AgentQualityEvaluator()
        mock_db = MagicMock()
        with patch.object(evaluator, "_judge", return_value=0.7):
            with patch.object(evaluator, "_send_to_langsmith", return_value=None):
                with patch.object(evaluator, "_persist", return_value=None) as mock_persist:
                    await evaluator.evaluate_response(
                        agent_id="wizard",
                        user_message="hello",
                        agent_response="world",
                        context={},
                        company_id="c-1",
                        db=mock_db,
                    )
        mock_persist.assert_called_once()


# =============================================================================
# candidate_channel_selector.py
# =============================================================================

class TestChannelSelectorConstants:
    def test_channel_consent_map_populated(self):
        from app.domains.candidates.services.candidate_channel_selector import CHANNEL_CONSENT_MAP
        assert "email" in CHANNEL_CONSENT_MAP
        assert "whatsapp" in CHANNEL_CONSENT_MAP

    def test_transactional_channels_contains_email(self):
        from app.domains.candidates.services.candidate_channel_selector import TRANSACTIONAL_CHANNELS
        assert "email" in TRANSACTIONAL_CHANNELS

    def test_fallback_channel_is_email(self):
        from app.domains.candidates.services.candidate_channel_selector import FALLBACK_CHANNEL
        assert FALLBACK_CHANNEL == ["email"]


class TestCandidateChannelSelectorLogic:
    @pytest.mark.asyncio
    async def test_empty_requested_channels_returns_fallback(self):
        from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector
        mock_db = MagicMock()
        selector = CandidateChannelSelector(db=mock_db)
        result = await selector.select_channels(
            candidate_id="cand-1",
            company_id="comp-1",
            requested_channels=[],
        )
        assert result == ["email"]

    @pytest.mark.asyncio
    async def test_channel_in_opt_out_excluded(self):
        from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector
        mock_db = MagicMock()
        selector = CandidateChannelSelector(db=mock_db)

        mock_candidate = MagicMock()
        mock_candidate.preferred_channels = ["email", "whatsapp"]
        mock_candidate.channel_opt_out = ["whatsapp"]

        with patch.object(selector, "_get_candidate", return_value=mock_candidate):
            with patch.object(selector, "_get_consented_channels", return_value=set()):
                result = await selector.select_channels(
                    candidate_id="cand-1",
                    company_id="comp-1",
                    requested_channels=["email", "whatsapp"],
                    message_type="transactional",
                )
        assert "whatsapp" not in result
        assert "email" in result

    @pytest.mark.asyncio
    async def test_marketing_requires_consent(self):
        from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector
        mock_db = MagicMock()
        selector = CandidateChannelSelector(db=mock_db)

        mock_candidate = MagicMock()
        mock_candidate.preferred_channels = ["email", "whatsapp"]
        mock_candidate.channel_opt_out = []

        # No whatsapp consent → excluded for marketing
        with patch.object(selector, "_get_candidate", return_value=mock_candidate):
            with patch.object(selector, "_get_consented_channels", return_value={"email"}):
                result = await selector.select_channels(
                    candidate_id="cand-1",
                    company_id="comp-1",
                    requested_channels=["email", "whatsapp"],
                    message_type="marketing",
                )
        assert "whatsapp" not in result

    @pytest.mark.asyncio
    async def test_marketing_with_whatsapp_consent_included(self):
        from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector
        mock_db = MagicMock()
        selector = CandidateChannelSelector(db=mock_db)

        mock_candidate = MagicMock()
        mock_candidate.preferred_channels = ["whatsapp", "email"]
        mock_candidate.channel_opt_out = []

        with patch.object(selector, "_get_candidate", return_value=mock_candidate):
            with patch.object(selector, "_get_consented_channels", return_value={"email", "whatsapp"}):
                result = await selector.select_channels(
                    candidate_id="cand-1",
                    company_id="comp-1",
                    requested_channels=["email", "whatsapp"],
                    message_type="marketing",
                )
        assert "whatsapp" in result

    @pytest.mark.asyncio
    async def test_fallback_when_all_channels_filtered(self):
        from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector
        mock_db = MagicMock()
        selector = CandidateChannelSelector(db=mock_db)

        mock_candidate = MagicMock()
        mock_candidate.preferred_channels = ["whatsapp"]
        mock_candidate.channel_opt_out = ["whatsapp"]

        with patch.object(selector, "_get_candidate", return_value=mock_candidate):
            with patch.object(selector, "_get_consented_channels", return_value=set()):
                result = await selector.select_channels(
                    candidate_id="cand-1",
                    company_id="comp-1",
                    requested_channels=["whatsapp"],
                    message_type="transactional",
                )
        assert result == ["email"]

    @pytest.mark.asyncio
    async def test_no_candidate_found_uses_defaults(self):
        from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector
        mock_db = MagicMock()
        selector = CandidateChannelSelector(db=mock_db)

        with patch.object(selector, "_get_candidate", return_value=None):
            with patch.object(selector, "_get_consented_channels", return_value=set()):
                result = await selector.select_channels(
                    candidate_id="cand-1",
                    company_id="comp-1",
                    requested_channels=["email"],
                    message_type="transactional",
                )
        assert result == ["email"]

    @pytest.mark.asyncio
    async def test_channel_not_in_requested_excluded(self):
        from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector
        mock_db = MagicMock()
        selector = CandidateChannelSelector(db=mock_db)

        mock_candidate = MagicMock()
        mock_candidate.preferred_channels = ["email", "whatsapp", "sms"]
        mock_candidate.channel_opt_out = []

        with patch.object(selector, "_get_candidate", return_value=mock_candidate):
            with patch.object(selector, "_get_consented_channels", return_value={"email", "whatsapp", "sms"}):
                result = await selector.select_channels(
                    candidate_id="cand-1",
                    company_id="comp-1",
                    requested_channels=["email"],  # only email requested
                    message_type="transactional",
                )
        assert result == ["email"]
        assert "sms" not in result

    @pytest.mark.asyncio
    async def test_get_consented_channels_error_returns_empty_set(self):
        from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector
        mock_db = MagicMock()
        mock_db.execute = AsyncMock(side_effect=RuntimeError("db error"))
        selector = CandidateChannelSelector(db=mock_db)
        result = await selector._get_consented_channels("cand-1", "comp-1")
        assert result == set()

    @pytest.mark.asyncio
    async def test_get_candidate_error_returns_none(self):
        from app.domains.candidates.services.candidate_channel_selector import CandidateChannelSelector
        mock_db = MagicMock()
        mock_db.execute = AsyncMock(side_effect=RuntimeError("db error"))
        selector = CandidateChannelSelector(db=mock_db)
        result = await selector._get_candidate("invalid-uuid-format")
        assert result is None


# =============================================================================
# consent_checker_service.py
# =============================================================================

class TestConsentCheckerServiceImport:
    def test_import_module(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService, ConsentCheckResult
        assert ConsentCheckerService is not None

    def test_consent_check_result_defaults(self):
        from app.shared.services.consent_checker_service import ConsentCheckResult
        result = ConsentCheckResult(allowed=True)
        assert result.allowed is True
        assert result.soft_warning is False
        assert result.reason is None
        assert result.consent_type is None

    def test_ai_purposes_list(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService
        assert "ai_screening" in ConsentCheckerService.AI_PURPOSES
        assert "ai_scoring" in ConsentCheckerService.AI_PURPOSES

    def test_purpose_to_consent_type_mapping(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService
        assert ConsentCheckerService.PURPOSE_TO_CONSENT_TYPE["ai_screening"] == "SCREENING"
        assert ConsentCheckerService.PURPOSE_TO_CONSENT_TYPE["ai_scoring"] == "SCREENING"


class TestConsentCheckerServiceRevokedConsent:
    @pytest.mark.asyncio
    async def test_revoked_consent_returns_blocked(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService
        from datetime import datetime

        mock_db = MagicMock()
        mock_consent = MagicMock()
        mock_consent.consent_given = False
        mock_consent.revoked_at = datetime(2026, 1, 1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_consent)
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = ConsentCheckerService(db=mock_db)
        result = await svc.check_candidate_consent(
            candidate_id="cand-1",
            company_id="comp-1",
            purpose="ai_screening",
        )

        assert result.allowed is False
        assert result.reason == "revoked"
        assert result.consent_type == "SCREENING"


class TestConsentCheckerServiceAbsentConsent:
    @pytest.mark.asyncio
    async def test_absent_consent_hard_block_blocks(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = ConsentCheckerService(db=mock_db)

        with patch("app.services.consent_checker_service.ConsentCheckerService._record_audit_log",
                   new_callable=AsyncMock):
            with patch("app.services.consent_checker_service.settings",
                       create=True) as mock_settings:
                mock_settings.LGPD_CONSENT_ABSENT_HARD_BLOCK = True

                # patch the import inside the function
                with patch("builtins.__import__", side_effect=ImportError):
                    pass  # use config patch instead

        # Direct approach: patch at module level
        with patch("app.services.consent_checker_service.ConsentCheckerService._record_audit_log",
                   new_callable=AsyncMock):
            # Simulate hard_block=True by patching the settings import
            original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

            import sys
            # Create a mock settings module
            mock_module = MagicMock()
            mock_module.settings = MagicMock()
            mock_module.settings.LGPD_CONSENT_ABSENT_HARD_BLOCK = True
            sys.modules["lia_config.config"] = mock_module

            try:
                result = await svc.check_candidate_consent(
                    candidate_id="cand-1",
                    company_id="comp-1",
                    purpose="ai_screening",
                )
                # With hard_block=True: should be blocked
                assert result.allowed is False
                assert result.reason == "absent"
            finally:
                sys.modules.pop("lia_config.config", None)

    @pytest.mark.asyncio
    async def test_absent_consent_soft_warning_continues(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = ConsentCheckerService(db=mock_db)

        import sys
        mock_module = MagicMock()
        mock_module.settings = MagicMock()
        mock_module.settings.LGPD_CONSENT_ABSENT_HARD_BLOCK = False
        sys.modules["lia_config.config"] = mock_module

        with patch.object(svc, "_record_audit_log", new_callable=AsyncMock):
            try:
                result = await svc.check_candidate_consent(
                    candidate_id="cand-1",
                    company_id="comp-1",
                    purpose="ai_scoring",
                )
                assert result.allowed is True
                assert result.soft_warning is True
                assert result.reason == "absent"
            finally:
                sys.modules.pop("lia_config.config", None)

    @pytest.mark.asyncio
    async def test_absent_consent_with_config_hard_block_true(self):
        """Quando LGPD_CONSENT_ABSENT_HARD_BLOCK=True, ausência bloqueia."""
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = ConsentCheckerService(db=mock_db)

        import sys
        mock_module = MagicMock()
        mock_module.settings = MagicMock()
        mock_module.settings.LGPD_CONSENT_ABSENT_HARD_BLOCK = True
        _orig_lia_config = sys.modules.get("lia_config")
        sys.modules["lia_config.config"] = mock_module
        sys.modules["lia_config"] = MagicMock()

        with patch.object(svc, "_record_audit_log", new_callable=AsyncMock):
            try:
                result = await svc.check_candidate_consent(
                    candidate_id="cand-1",
                    company_id="comp-1",
                    purpose="ai_screening",
                )
                assert result.allowed is False
                assert result.reason == "absent"
            finally:
                sys.modules.pop("lia_config.config", None)
                if _orig_lia_config is None:
                    sys.modules.pop("lia_config", None)
                else:
                    sys.modules["lia_config"] = _orig_lia_config


class TestConsentCheckerServicePresentConsent:
    @pytest.mark.asyncio
    async def test_present_valid_consent_allows(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = MagicMock()
        mock_consent = MagicMock()
        mock_consent.consent_given = True
        mock_consent.revoked_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_consent)
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = ConsentCheckerService(db=mock_db)
        result = await svc.check_candidate_consent(
            candidate_id="cand-1",
            company_id="comp-1",
            purpose="ai_screening",
        )

        assert result.allowed is True
        assert result.soft_warning is False
        assert result.consent_type == "SCREENING"

    @pytest.mark.asyncio
    async def test_db_exception_returns_soft_warning(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(side_effect=RuntimeError("db error"))

        svc = ConsentCheckerService(db=mock_db)
        result = await svc.check_candidate_consent(
            candidate_id="cand-1",
            company_id="comp-1",
            purpose="ai_screening",
        )

        assert result.allowed is True
        assert result.soft_warning is True
        assert result.reason == "check_error"


class TestConsentCheckerServiceRegister:
    @pytest.mark.asyncio
    async def test_register_consent_creates_new(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = MagicMock()
        mock_result = MagicMock()
        # No existing consent → create new
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()

        svc = ConsentCheckerService(db=mock_db)
        # LGPDConsent is already imported, so we call register_consent normally.
        # The add() call confirms a new record was created.
        await svc.register_consent(
            candidate_id="cand-1",
            company_id="comp-1",
            consent_type="SCREENING",
            consent_given=True,
        )
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_consent_updates_existing(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = MagicMock()
        mock_existing = MagicMock()
        mock_existing.consent_given = False

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_existing)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        svc = ConsentCheckerService(db=mock_db)
        result = await svc.register_consent(
            candidate_id="cand-1",
            company_id="comp-1",
            consent_type="SCREENING",
            consent_given=True,
        )
        assert mock_existing.consent_given is True

    @pytest.mark.asyncio
    async def test_register_consent_revoke_sets_revoked_at(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_db = MagicMock()
        mock_existing = MagicMock()
        mock_existing.consent_given = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_existing)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.flush = AsyncMock()

        svc = ConsentCheckerService(db=mock_db)
        await svc.register_consent(
            candidate_id="cand-1",
            company_id="comp-1",
            consent_type="SCREENING",
            consent_given=False,  # revoking
        )
        # revoked_by should be set
        assert mock_existing.revoked_by == "candidate"

    @pytest.mark.asyncio
    async def test_get_candidate_consents_returns_list(self):
        from app.shared.services.consent_checker_service import ConsentCheckerService

        mock_consent = MagicMock()
        mock_consent.to_dict = MagicMock(return_value={"consent_type": "SCREENING"})

        mock_scalars = MagicMock()
        mock_scalars.all = MagicMock(return_value=[mock_consent])

        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=mock_scalars)

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        svc = ConsentCheckerService(db=mock_db)
        consents = await svc.get_candidate_consents("cand-1", "comp-1")
        assert len(consents) == 1
        assert consents[0]["consent_type"] == "SCREENING"


# =============================================================================
# Briefing service — pure function only
# =============================================================================

class TestBriefingServiceGreeting:
    def test_morning_greeting(self):
        from app.shared.services.briefing_service import BriefingService
        from datetime import datetime
        svc = BriefingService()
        assert svc._get_greeting(datetime(2026, 3, 14, 9, 0)) == "Bom dia"

    def test_afternoon_greeting(self):
        from app.shared.services.briefing_service import BriefingService
        from datetime import datetime
        svc = BriefingService()
        assert svc._get_greeting(datetime(2026, 3, 14, 14, 0)) == "Boa tarde"

    def test_evening_greeting(self):
        from app.shared.services.briefing_service import BriefingService
        from datetime import datetime
        svc = BriefingService()
        assert svc._get_greeting(datetime(2026, 3, 14, 20, 0)) == "Boa noite"

    def test_boundary_noon(self):
        from app.shared.services.briefing_service import BriefingService
        from datetime import datetime
        svc = BriefingService()
        assert svc._get_greeting(datetime(2026, 3, 14, 12, 0)) == "Boa tarde"

    def test_boundary_6pm(self):
        from app.shared.services.briefing_service import BriefingService
        from datetime import datetime
        svc = BriefingService()
        assert svc._get_greeting(datetime(2026, 3, 14, 18, 0)) == "Boa noite"
