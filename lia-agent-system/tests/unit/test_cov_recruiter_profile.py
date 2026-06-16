"""Coverage tests for app/schemas/recruiter_profile.py — Pydantic models."""
import pytest
from datetime import datetime
from uuid import UUID
from app.schemas.recruiter_profile import (
    WizardFlowConfig,
    PersonalizedDefaults,
    PersonalizationSettingsBase,
    PersonalizationSettingsCreate,
    PersonalizationSettingsUpdate,
    PersonalizationSettingsResponse,
    PersonalizationEventCreate,
    PersonalizationEventResponse,
    RecruiterFieldPreferenceBase,
    RecruiterFieldPreferenceResponse,
    RecruiterProfileBase,
    RecruiterProfileCreate,
    RecruiterProfileUpdate,
    RecruiterProfileResponse,
    RecruiterPersonalizationContext,
)

_DT = datetime(2024, 3, 15, 10, 0)
_UUID1 = UUID("550e8400-e29b-41d4-a716-446655440001")
_UUID2 = UUID("550e8400-e29b-41d4-a716-446655440002")


class TestWizardFlowConfig:
    def test_empty(self):
        m = WizardFlowConfig()
        assert m is not None

    def test_with_values(self):
        m = WizardFlowConfig(
            show_detailed_explanations=True,
            skip_optional_confirmations=False,
            auto_expand_sections=True,
            suggest_jd_import=True,
        )
        assert m.show_detailed_explanations is True
        assert m.skip_optional_confirmations is False

    def test_with_thresholds(self):
        m = WizardFlowConfig(
            confidence_thresholds={"salary": 0.8, "seniority": 0.7},
        )
        assert m.confidence_thresholds["salary"] == pytest.approx(0.8)


class TestPersonalizedDefaults:
    def test_empty(self):
        m = PersonalizedDefaults()
        assert m is not None

    def test_with_values(self):
        m = PersonalizedDefaults(
            seniority="senior",
            department="Engineering",
            work_model="hybrid",
            salary_percentile_hint=60.0,
        )
        assert m.seniority == "senior"
        assert m.work_model == "hybrid"

    def test_with_skills(self):
        m = PersonalizedDefaults(
            suggested_skills=["Python", "Docker", "FastAPI"],
        )
        assert len(m.suggested_skills) == 3


class TestPersonalizationSettingsBase:
    def test_empty(self):
        m = PersonalizationSettingsBase()
        assert m is not None

    def test_with_flags(self):
        m = PersonalizationSettingsBase(
            enable_personalization=True,
            enable_learning=True,
            learn_from_corrections=True,
            show_personalization_indicators=False,
        )
        assert m.enable_personalization is True
        assert m.show_personalization_indicators is False


class TestPersonalizationSettingsCreate:
    def test_basic(self):
        m = PersonalizationSettingsCreate(recruiter_id="rec-001")
        assert m.recruiter_id == "rec-001"

    def test_with_consent(self):
        m = PersonalizationSettingsCreate(
            recruiter_id="rec-002",
            consent_version="v1.2",
            enable_learning=True,
        )
        assert m.consent_version == "v1.2"
        assert m.enable_learning is True


class TestPersonalizationSettingsUpdate:
    def test_empty(self):
        m = PersonalizationSettingsUpdate()
        assert m is not None

    def test_disable_learning(self):
        m = PersonalizationSettingsUpdate(enable_learning=False)
        assert m.enable_learning is False


class TestPersonalizationSettingsResponse:
    def test_basic(self):
        m = PersonalizationSettingsResponse(
            recruiter_id="rec-001",
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.recruiter_id == "rec-001"
        assert m.created_at == _DT

    def test_with_consent(self):
        m = PersonalizationSettingsResponse(
            recruiter_id="rec-002",
            consent_version="v1.0",
            consent_given_at=_DT,
            enable_personalization=True,
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.consent_version == "v1.0"
        assert m.enable_personalization is True


class TestPersonalizationEventCreate:
    def test_basic(self):
        m = PersonalizationEventCreate(
            recruiter_id="rec-001",
            company_id="co-001",
            event_type="field_corrected",
        )
        assert m.recruiter_id == "rec-001"
        assert m.event_type == "field_corrected"

    def test_with_values(self):
        m = PersonalizationEventCreate(
            recruiter_id="rec-001",
            company_id="co-001",
            event_type="field_accepted",
            field_name="salary_range",
            suggested_value="10000-15000",
            final_value="12000-16000",
        )
        assert m.field_name == "salary_range"
        assert m.final_value == "12000-16000"

    def test_with_timing(self):
        m = PersonalizationEventCreate(
            recruiter_id="rec-001",
            company_id="co-001",
            event_type="field_corrected",
            time_to_decision_ms=1500,
        )
        assert m.time_to_decision_ms == 1500


class TestPersonalizationEventResponse:
    def test_basic(self):
        m = PersonalizationEventResponse(
            recruiter_id="rec-001",
            company_id="co-001",
            event_type="field_accepted",
            id=_UUID1,
            created_at=_DT,
        )
        assert m.id == _UUID1
        assert m.event_type == "field_accepted"

    def test_full(self):
        m = PersonalizationEventResponse(
            recruiter_id="rec-002",
            company_id="co-002",
            event_type="field_corrected",
            field_name="contract_type",
            suggested_value="PJ",
            final_value="CLT",
            id=_UUID2,
            created_at=_DT,
        )
        assert m.field_name == "contract_type"
        assert m.final_value == "CLT"


class TestRecruiterFieldPreferenceBase:
    def test_basic(self):
        m = RecruiterFieldPreferenceBase(
            recruiter_id="rec-001",
            field_name="contract_type",
        )
        assert m.recruiter_id == "rec-001"
        assert m.field_name == "contract_type"

    def test_with_stats(self):
        m = RecruiterFieldPreferenceBase(
            recruiter_id="rec-002",
            field_name="seniority",
            times_seen=20,
            times_corrected=5,
            times_accepted=15,
        )
        assert m.times_seen == 20
        assert m.times_corrected == 5


class TestRecruiterFieldPreferenceResponse:
    def test_basic(self):
        m = RecruiterFieldPreferenceResponse(
            recruiter_id="rec-001",
            field_name="currency",
            id=_UUID1,
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.id == _UUID1
        assert m.field_name == "currency"


class TestRecruiterProfileBase:
    def test_basic(self):
        m = RecruiterProfileBase(recruiter_id="rec-001", company_id="co-001")
        assert m.recruiter_id == "rec-001"
        assert m.company_id == "co-001"

    def test_with_stats(self):
        m = RecruiterProfileBase(
            recruiter_id="rec-002",
            company_id="co-002",
            total_jobs_created=15,
            prefers_quick_flow=True,
            uses_jd_import=False,
        )
        assert m.total_jobs_created == 15
        assert m.prefers_quick_flow is True

    def test_with_preferences(self):
        m = RecruiterProfileBase(
            recruiter_id="rec-003",
            company_id="co-003",
            preferred_seniorities=["senior", "pleno"],
            preferred_departments=["Engineering", "Product"],
            communication_style="concise",
        )
        assert len(m.preferred_seniorities) == 2
        assert m.communication_style == "concise"


class TestRecruiterProfileCreate:
    def test_basic(self):
        m = RecruiterProfileCreate(recruiter_id="rec-001", company_id="co-001")
        assert m.recruiter_id == "rec-001"


class TestRecruiterProfileUpdate:
    def test_empty(self):
        m = RecruiterProfileUpdate()
        assert m is not None

    def test_partial(self):
        m = RecruiterProfileUpdate(
            total_jobs_created=20,
            prefers_quick_flow=True,
        )
        assert m.total_jobs_created == 20


class TestRecruiterProfileResponse:
    def test_basic(self):
        m = RecruiterProfileResponse(
            recruiter_id="rec-001",
            company_id="co-001",
            id=_UUID1,
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.id == _UUID1
        assert m.recruiter_id == "rec-001"

    def test_with_stats(self):
        m = RecruiterProfileResponse(
            recruiter_id="rec-002",
            company_id="co-002",
            id=_UUID2,
            total_jobs_created=25,
            avg_correction_rate=0.15,
            is_active=True,
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.total_jobs_created == 25
        assert m.is_active is True


class TestRecruiterPersonalizationContext:
    def test_basic(self):
        m = RecruiterPersonalizationContext(recruiter_id="rec-001")
        assert m.recruiter_id == "rec-001"

    def test_with_context(self):
        m = RecruiterPersonalizationContext(
            recruiter_id="rec-002",
            is_new_user=True,
            personalization_level="low",
        )
        assert m.is_new_user is True
        assert m.personalization_level == "low"

    def test_with_defaults(self):
        defaults = PersonalizedDefaults(seniority="pleno", work_model="remote")
        m = RecruiterPersonalizationContext(
            recruiter_id="rec-003",
            personalized_defaults=defaults,
        )
        assert m.personalized_defaults.seniority == "pleno"
