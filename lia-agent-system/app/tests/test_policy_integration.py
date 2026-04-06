"""
Phase 2 Integration Tests — Policy integrations with services.

Tests:
- PolicyMiddleware resolution
- PolicySyncService (SLA sync + feature flags sync)
- Scheduling policy integration
- Communication policy integration
- Screening policy integration
- Pipeline transition validation
- Pipeline templates resolution
- Default fallback behavior (no policy)
"""
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.models.company_hiring_policy import (
    AUTOMATION_RULES_DEFAULTS,
    COMMUNICATION_RULES_DEFAULTS,
    PIPELINE_RULES_DEFAULTS,
    SCHEDULING_RULES_DEFAULTS,
    SCREENING_RULES_DEFAULTS,
)
from app.shared.policy_helper import (
    _get_defaults_dict,
    get_policy_rule,
)
from app.shared.policy_middleware import (
    get_policy_for_company,
    resolve_policy_value,
)
from app.shared.policy_sync_service import (
    AUTOMATION_FLAG_MAP,
    AUTONOMY_LEVEL_PRESETS,
    sync_policy_to_models,
)


class TestPolicyMiddleware:
    """Tests for PolicyMiddleware dependency injection."""
    
    def test_resolve_policy_value_with_override(self):
        policy = {"scheduling_rules": {"default_duration_minutes": 45}}
        result = resolve_policy_value(
            policy, "scheduling_rules", "default_duration_minutes",
            override=30, default=60,
        )
        assert result == 30
    
    def test_resolve_policy_value_from_policy(self):
        policy = {"scheduling_rules": {"default_duration_minutes": 45}}
        result = resolve_policy_value(
            policy, "scheduling_rules", "default_duration_minutes",
            override=None, default=60,
        )
        assert result == 45
    
    def test_resolve_policy_value_fallback_to_default(self):
        policy = {"scheduling_rules": {}}
        result = resolve_policy_value(
            policy, "scheduling_rules", "default_duration_minutes",
            override=None, default=60,
        )
        assert result == 60
    
    def test_resolve_policy_value_missing_block(self):
        policy = {}
        result = resolve_policy_value(
            policy, "scheduling_rules", "default_duration_minutes",
            override=None, default=60,
        )
        assert result == 60
    
    @pytest.mark.asyncio
    async def test_get_policy_for_company_no_company_id(self):
        mock_db = AsyncMock()
        result = await get_policy_for_company("", mock_db)
        assert result["scheduling_rules"] == SCHEDULING_RULES_DEFAULTS
    
    @pytest.mark.asyncio
    async def test_get_policy_for_company_with_valid_id(self):
        mock_db = AsyncMock()
        mock_policy_dict = {
            "id": "test-id",
            "company_id": "company-123",
            "scheduling_rules": {"default_duration_minutes": 45},
            "communication_rules": COMMUNICATION_RULES_DEFAULTS,
            "pipeline_rules": PIPELINE_RULES_DEFAULTS,
            "screening_rules": SCREENING_RULES_DEFAULTS,
            "automation_rules": AUTOMATION_RULES_DEFAULTS,
        }
        with patch('app.shared.policy_middleware.get_company_policy', return_value=mock_policy_dict):
            result = await get_policy_for_company("company-123", mock_db)
            assert result["scheduling_rules"]["default_duration_minutes"] == 45


class TestPolicySyncService:
    """Tests for PolicySyncService — SLA and feature flag sync."""
    
    @pytest.mark.asyncio
    async def test_sync_feature_flags_low_autonomy(self):
        mock_db = AsyncMock()
        policy = {
            "pipeline_rules": {},
            "automation_rules": {"autonomy_level": "low"},
        }
        
        with patch('app.shared.governance.feature_flag_service.feature_flag_service') as mock_ff:
            mock_ff.set_flag = AsyncMock(return_value={"success": True})
            result = await sync_policy_to_models("company-1", policy, mock_db)
            assert result["flags_synced"] is True
            for call in mock_ff.set_flag.call_args_list:
                assert call.kwargs["is_enabled"] is False
    
    @pytest.mark.asyncio
    async def test_sync_feature_flags_high_autonomy(self):
        mock_db = AsyncMock()
        policy = {
            "pipeline_rules": {},
            "automation_rules": {"autonomy_level": "high"},
        }
        
        with patch('app.shared.governance.feature_flag_service.feature_flag_service') as mock_ff:
            mock_ff.set_flag = AsyncMock(return_value={"success": True})
            result = await sync_policy_to_models("company-1", policy, mock_db)
            assert result["flags_synced"] is True
            for call in mock_ff.set_flag.call_args_list:
                assert call.kwargs["is_enabled"] is True
    
    @pytest.mark.asyncio
    async def test_sync_feature_flags_medium_autonomy(self):
        mock_db = AsyncMock()
        policy = {
            "pipeline_rules": {},
            "automation_rules": {"autonomy_level": "medium"},
        }
        
        with patch('app.shared.governance.feature_flag_service.feature_flag_service') as mock_ff:
            mock_ff.set_flag = AsyncMock(return_value={"success": True})
            result = await sync_policy_to_models("company-1", policy, mock_db)
            assert result["flags_synced"] is True
            calls = {c.kwargs["flag_key"]: c.kwargs["is_enabled"] for c in mock_ff.set_flag.call_args_list}
            screening_key = [k for k in calls if "SCREENING" in k][0]
            assert calls[screening_key] is True
    
    @pytest.mark.asyncio
    async def test_sync_explicit_override_wins_over_autonomy(self):
        mock_db = AsyncMock()
        policy = {
            "pipeline_rules": {},
            "automation_rules": {
                "autonomy_level": "low",
                "auto_screening": True,
            },
        }
        
        with patch('app.shared.governance.feature_flag_service.feature_flag_service') as mock_ff:
            mock_ff.set_flag = AsyncMock(return_value={"success": True})
            await sync_policy_to_models("company-1", policy, mock_db)
            calls = {c.kwargs["flag_key"]: c.kwargs["is_enabled"] for c in mock_ff.set_flag.call_args_list}
            screening_key = [k for k in calls if "SCREENING" in k][0]
            assert calls[screening_key] is True
    
    @pytest.mark.asyncio
    async def test_sync_no_automation_rules(self):
        mock_db = AsyncMock()
        policy = {"pipeline_rules": {}, "automation_rules": {}}
        
        result = await sync_policy_to_models("company-1", policy, mock_db)
        assert result["flags_synced"] is False
    
    def test_autonomy_presets_coverage(self):
        assert "low" in AUTONOMY_LEVEL_PRESETS
        assert "medium" in AUTONOMY_LEVEL_PRESETS
        assert "high" in AUTONOMY_LEVEL_PRESETS
        
        for level, preset in AUTONOMY_LEVEL_PRESETS.items():
            for key in AUTOMATION_FLAG_MAP:
                assert key in preset


class TestSchedulingPolicyIntegration:
    """Tests for scheduling service policy integration."""
    
    def test_resolve_allowed_days_from_policy(self):
        policy = {"scheduling_rules": {"allowed_days": ["mon", "wed", "fri"]}}
        days = resolve_policy_value(
            policy, "scheduling_rules", "allowed_days",
            override=None, default=["mon", "tue", "wed", "thu", "fri"],
        )
        assert days == ["mon", "wed", "fri"]
    
    def test_resolve_allowed_hours_from_policy(self):
        policy = {"scheduling_rules": {"allowed_hours": {"start": "10:00", "end": "16:00"}}}
        hours = resolve_policy_value(
            policy, "scheduling_rules", "allowed_hours",
            override=None, default={"start": "09:00", "end": "18:00"},
        )
        assert hours == {"start": "10:00", "end": "16:00"}
    
    def test_resolve_duration_with_explicit_override(self):
        policy = {"scheduling_rules": {"default_duration_minutes": 45}}
        duration = resolve_policy_value(
            policy, "scheduling_rules", "default_duration_minutes",
            override=30, default=60,
        )
        assert duration == 30
    
    def test_resolve_self_scheduling(self):
        policy = {"scheduling_rules": {"self_scheduling_enabled": True}}
        enabled = resolve_policy_value(
            policy, "scheduling_rules", "self_scheduling_enabled",
            override=None, default=False,
        )
        assert enabled is True
    
    def test_defaults_when_no_policy(self):
        policy = _get_defaults_dict()
        assert resolve_policy_value(policy, "scheduling_rules", "allowed_days", default=["mon"]) == ["mon", "tue", "wed", "thu", "fri"]
        assert resolve_policy_value(policy, "scheduling_rules", "default_duration_minutes", default=60) == 60


class TestCommunicationPolicyIntegration:
    """Tests for communication dispatcher policy integration."""
    
    def test_resolve_preferred_channel(self):
        policy = {"communication_rules": {"preferred_channel": "email"}}
        channel = resolve_policy_value(
            policy, "communication_rules", "preferred_channel",
            override=None, default="whatsapp",
        )
        assert channel == "email"
    
    def test_explicit_channel_overrides_policy(self):
        policy = {"communication_rules": {"preferred_channel": "email"}}
        channel = resolve_policy_value(
            policy, "communication_rules", "preferred_channel",
            override="whatsapp", default="email",
        )
        assert channel == "whatsapp"
    
    def test_resolve_lia_tone(self):
        policy = {"communication_rules": {"lia_tone": "friendly"}}
        tone = resolve_policy_value(
            policy, "communication_rules", "lia_tone",
            override=None, default="professional",
        )
        assert tone == "friendly"
    
    def test_resolve_auto_rejection_feedback(self):
        policy = {"communication_rules": {"auto_rejection_feedback": True}}
        auto = resolve_policy_value(
            policy, "communication_rules", "auto_rejection_feedback",
            override=None, default=False,
        )
        assert auto is True
    
    def test_tone_application(self):
        from app.domains.communication.services.communication_dispatcher import communication_dispatcher
        
        result_professional = communication_dispatcher._apply_tone(
            "Sua entrevista foi agendada.", "professional", "João Silva"
        )
        assert "João Silva" in result_professional
        
        result_friendly = communication_dispatcher._apply_tone(
            "Sua entrevista foi agendada.", "friendly", "João Silva"
        )
        assert "João" in result_friendly
        assert "Oi" in result_friendly
        
        result_formal = communication_dispatcher._apply_tone(
            "Sua entrevista foi agendada.", "formal", "João Silva"
        )
        assert "Sr(a)." in result_formal


class TestScreeningPolicyIntegration:
    """Tests for screening policy integration."""
    
    def test_default_screening_questions_from_policy(self):
        policy = {"screening_rules": {"default_screening_questions": ["Qual sua disponibilidade?", "Pretensão salarial?"]}}
        questions = get_policy_rule(policy, "screening_rules", "default_screening_questions", [])
        assert len(questions) == 2
        assert "Qual sua disponibilidade?" in questions
    
    def test_experience_policy_per_job(self):
        policy = {"screening_rules": {"experience_policy": "per_job"}}
        exp = get_policy_rule(policy, "screening_rules", "experience_policy", "per_job")
        assert exp == "per_job"
    
    def test_experience_policy_global(self):
        policy = {"screening_rules": {"experience_policy": "global"}}
        exp = get_policy_rule(policy, "screening_rules", "experience_policy", "per_job")
        assert exp == "global"


class TestPipelineValidation:
    """Tests for pipeline transition validation."""
    
    def test_min_interviews_check(self):
        policy = {"pipeline_rules": {"min_interviews_before_offer": 3}}
        min_interviews = get_policy_rule(policy, "pipeline_rules", "min_interviews_before_offer", 2)
        assert min_interviews == 3
        interview_count = 1
        assert interview_count < min_interviews
    
    def test_manager_approval_required(self):
        policy = {"pipeline_rules": {"manager_approval_for_offer": True}}
        approval = get_policy_rule(policy, "pipeline_rules", "manager_approval_for_offer", True)
        assert approval is True
    
    def test_max_days_in_stage_dict(self):
        policy = {"pipeline_rules": {"max_days_in_stage": {"screening": 3, "interview": 7}}}
        max_days = get_policy_rule(policy, "pipeline_rules", "max_days_in_stage", {})
        assert max_days["screening"] == 3
        assert max_days["interview"] == 7
    
    def test_max_days_in_stage_global(self):
        policy = {"pipeline_rules": {"max_days_in_stage": 5}}
        max_days = get_policy_rule(policy, "pipeline_rules", "max_days_in_stage", {})
        assert max_days == 5
    
    def test_default_pipeline_rules(self):
        policy = _get_defaults_dict()
        min_interviews = get_policy_rule(policy, "pipeline_rules", "min_interviews_before_offer", 2)
        assert min_interviews == 2


class TestPipelineTemplates:
    """Tests for pipeline template resolution."""
    
    def test_templates_from_policy(self):
        policy = {
            "pipeline_templates": [
                {"id": "custom", "name": "Processo Custom", "stages": [{"name": "Triagem", "order": 1}]}
            ]
        }
        templates = policy.get("pipeline_templates", [])
        assert len(templates) == 1
        assert templates[0]["name"] == "Processo Custom"
    
    def test_no_templates_returns_empty(self):
        policy = _get_defaults_dict()
        templates = policy.get("pipeline_templates", [])
        assert templates == []


class TestDefaultFallback:
    """Tests ensuring everything works correctly without any policy."""
    
    def test_defaults_dict_has_all_blocks(self):
        defaults = _get_defaults_dict()
        assert "pipeline_rules" in defaults
        assert "scheduling_rules" in defaults
        assert "communication_rules" in defaults
        assert "screening_rules" in defaults
        assert "automation_rules" in defaults
        assert "pipeline_templates" in defaults
    
    def test_default_scheduling_values(self):
        defaults = _get_defaults_dict()
        sched = defaults["scheduling_rules"]
        assert sched["allowed_days"] == ["mon", "tue", "wed", "thu", "fri"]
        assert sched["allowed_hours"] == {"start": "09:00", "end": "18:00"}
        assert sched["default_duration_minutes"] == 60
        assert sched["self_scheduling_enabled"] is False
    
    def test_default_communication_values(self):
        defaults = _get_defaults_dict()
        comm = defaults["communication_rules"]
        assert comm["preferred_channel"] == "whatsapp"
        assert comm["lia_tone"] == "professional"
        assert comm["auto_rejection_feedback"] is False
    
    def test_default_screening_values(self):
        defaults = _get_defaults_dict()
        screen = defaults["screening_rules"]
        assert screen["experience_policy"] == "per_job"
        assert screen["default_screening_questions"] == []
    
    def test_default_automation_values(self):
        defaults = _get_defaults_dict()
        auto = defaults["automation_rules"]
        assert auto["auto_screening"] is False
        assert auto["auto_scheduling"] is False
        assert auto["auto_stage_advance"] is False
        assert auto["autonomy_level"] == "low"
    
    def test_default_pipeline_values(self):
        defaults = _get_defaults_dict()
        pipe = defaults["pipeline_rules"]
        assert pipe["min_interviews_before_offer"] == 2
        assert pipe["manager_approval_for_offer"] is True


class TestFeatureFlagMapping:
    """Tests for automation_rules to feature flag mapping."""
    
    def test_flag_map_covers_all_automation_keys(self):
        expected_keys = {"auto_screening", "auto_scheduling", "auto_stage_advance"}
        assert set(AUTOMATION_FLAG_MAP.keys()) == expected_keys
    
    def test_flag_key_template_format(self):
        for key, config in AUTOMATION_FLAG_MAP.items():
            template = config["flag_key_template"]
            assert "{company_id}" in template
            formatted = template.format(company_id="test-company")
            assert "test-company" in formatted
    
    def test_all_presets_cover_all_flags(self):
        for level, preset in AUTONOMY_LEVEL_PRESETS.items():
            for flag_key in AUTOMATION_FLAG_MAP:
                assert flag_key in preset, f"Preset '{level}' missing key '{flag_key}'"


class TestCalendarServicePolicyIntegration:
    """Tests for CalendarService policy integration."""

    @pytest.mark.asyncio
    async def test_calendar_uses_default_hours_without_policy(self):
        from app.domains.interview_scheduling.services.calendar_service import CalendarService

        svc = CalendarService()
        svc.graph = AsyncMock()
        svc.graph.get_user_calendar_view = AsyncMock(return_value=[])

        await svc.check_interviewer_availability(
            interviewer_email="test@example.com",
            date=datetime(2026, 3, 2, 12, 0, 0),
        )
        call_args = svc.graph.get_user_calendar_view.call_args
        start_time = call_args.kwargs["start_time"]
        end_time = call_args.kwargs["end_time"]
        assert start_time.hour == 9
        assert end_time.hour == 18

    @pytest.mark.asyncio
    async def test_calendar_uses_policy_hours(self):
        from app.domains.interview_scheduling.services.calendar_service import CalendarService

        svc = CalendarService()
        svc.graph = AsyncMock()
        svc.graph.get_user_calendar_view = AsyncMock(return_value=[])

        mock_policy = {
            "scheduling_rules": {
                "allowed_hours": {"start": "10:00", "end": "17:00"},
                "default_duration_minutes": 60,
            }
        }
        mock_db = AsyncMock()

        with patch(
            "app.domains.interview_scheduling.services.calendar_service.get_policy_for_company",
            return_value=mock_policy,
        ):
            await svc.check_interviewer_availability(
                interviewer_email="test@example.com",
                date=datetime(2026, 3, 2, 12, 0, 0),
                company_id="company-1",
                db=mock_db,
            )

        call_args = svc.graph.get_user_calendar_view.call_args
        start_time = call_args.kwargs["start_time"]
        end_time = call_args.kwargs["end_time"]
        assert start_time.hour == 10
        assert end_time.hour == 17

    @pytest.mark.asyncio
    async def test_calendar_uses_policy_duration(self):
        from app.domains.interview_scheduling.services.calendar_service import CalendarService

        svc = CalendarService()
        svc.graph = AsyncMock()
        svc.graph.get_user_calendar_view = AsyncMock(return_value=[])

        mock_policy = {
            "scheduling_rules": {
                "allowed_hours": {"start": "09:00", "end": "18:00"},
                "default_duration_minutes": 45,
            }
        }
        mock_db = AsyncMock()

        with patch(
            "app.domains.interview_scheduling.services.calendar_service.get_policy_for_company",
            return_value=mock_policy,
        ):
            slots = await svc.check_interviewer_availability(
                interviewer_email="test@example.com",
                date=datetime(2026, 3, 2, 12, 0, 0),
                company_id="company-1",
                db=mock_db,
            )

        if slots:
            assert slots[0]["duration_minutes"] == 45

    @pytest.mark.asyncio
    async def test_calendar_explicit_duration_overrides_policy(self):
        from app.domains.interview_scheduling.services.calendar_service import CalendarService

        svc = CalendarService()
        svc.graph = AsyncMock()
        svc.graph.create_calendar_event = AsyncMock(return_value={"id": "evt-1"})

        mock_policy = {
            "scheduling_rules": {
                "default_duration_minutes": 45,
            }
        }
        mock_db = AsyncMock()

        with patch(
            "app.domains.interview_scheduling.services.calendar_service.get_policy_for_company",
            return_value=mock_policy,
        ):
            await svc.schedule_interview(
                organizer_email="hr@example.com",
                candidate_name="Test",
                candidate_email="cand@example.com",
                interviewer_emails=["int@example.com"],
                position="Dev",
                start_time=datetime(2026, 3, 2, 10, 0, 0),
                duration_minutes=30,
                company_id="company-1",
                db=mock_db,
            )

        call_args = svc.graph.create_calendar_event.call_args
        start = call_args.kwargs["start_time"]
        end = call_args.kwargs["end_time"]
        assert (end - start).total_seconds() == 30 * 60


class TestScreeningQuestionSetPolicyIntegration:
    """Tests for ScreeningQuestionSetService policy integration."""

    @pytest.mark.asyncio
    async def test_inject_policy_defaults_adds_questions(self):
        from app.domains.cv_screening.services.screening_question_set_service import ScreeningQuestionSetService

        svc = ScreeningQuestionSetService()
        mock_db = AsyncMock()
        mock_policy = {
            "screening_rules": {
                "default_screening_questions": [
                    "Qual sua disponibilidade?",
                    "Pretensão salarial?",
                ],
            }
        }

        existing_questions = [{"id": "q1", "text": "Tell me about yourself"}]

        with patch(
            "app.domains.cv_screening.services.screening_question_set_service.get_policy_for_company",
            return_value=mock_policy,
        ):
            result = await svc.inject_policy_defaults(mock_db, "company-1", existing_questions)

        assert len(result) == 3
        injected_texts = [q["text"] for q in result if q.get("source") == "company_policy"]
        assert "Qual sua disponibilidade?" in injected_texts
        assert "Pretensão salarial?" in injected_texts

    @pytest.mark.asyncio
    async def test_inject_policy_defaults_deduplicates(self):
        from app.domains.cv_screening.services.screening_question_set_service import ScreeningQuestionSetService

        svc = ScreeningQuestionSetService()
        mock_db = AsyncMock()
        mock_policy = {
            "screening_rules": {
                "default_screening_questions": [
                    "Qual sua disponibilidade?",
                    "Pretensão salarial?",
                ],
            }
        }

        existing_questions = [
            {"id": "q1", "text": "qual sua disponibilidade?"},
        ]

        with patch(
            "app.domains.cv_screening.services.screening_question_set_service.get_policy_for_company",
            return_value=mock_policy,
        ):
            result = await svc.inject_policy_defaults(mock_db, "company-1", existing_questions)

        assert len(result) == 2
        texts = [q["text"] for q in result]
        assert texts.count("qual sua disponibilidade?") == 1

    @pytest.mark.asyncio
    async def test_inject_policy_defaults_no_policy(self):
        from app.domains.cv_screening.services.screening_question_set_service import ScreeningQuestionSetService

        svc = ScreeningQuestionSetService()
        mock_db = AsyncMock()

        existing_questions = [{"id": "q1", "text": "Tell me about yourself"}]

        with patch(
            "app.domains.cv_screening.services.screening_question_set_service.get_policy_for_company",
            return_value={"screening_rules": {}},
        ):
            result = await svc.inject_policy_defaults(mock_db, "company-1", existing_questions)

        assert len(result) == 1
        assert result[0]["text"] == "Tell me about yourself"


# TestScreeningAgentPolicyIntegration removida — ScreeningAgent migrado para PipelineReActAgent (Sprint 5).
