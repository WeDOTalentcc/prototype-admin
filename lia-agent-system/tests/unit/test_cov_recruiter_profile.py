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

_UUID1 = UUID("550e8400-e29b-41d4-a716-446655440001")
_UUID2 = UUID("550e8400-e29b-41d4-a716-446655440002")
_DT = datetime(2024, 3, 15, 10, 0)


class TestWizardFlowConfig:
    def test_empty(self):
        m = WizardFlowConfig()
        assert m is not None

    def test_with_steps(self):
        m = WizardFlowConfig(
            skip_steps=["benefits", "compensation"],
            default_tab="requirements",
        )
        assert m.skip_steps == ["benefits", "compensation"]
        assert m.default_tab == "requirements"


class TestPersonalizedDefaults:
    def test_empty(self):
        m = PersonalizedDefaults()
        assert m is not None

    def test_with_values(self):
        m = PersonalizedDefaults(
            contract_type="CLT",
            seniority="senior",
            currency="BRL",
            work_model="hybrid",
        )
        assert m.contract_type == "CLT"
        assert m.work_model == "hybrid"


class TestPersonalizationSettingsBase:
    def test_empty(self):
        m = PersonalizationSettingsBase()
        assert m is not None

    def test_with_values(self):
        m = PersonalizationSettingsBase(
            theme="dark",
            language="pt-BR",
        )
        assert m.theme == "dark"


class TestPersonalizationSettingsCreate:
    def test_basic(self):
        m = PersonalizationSettingsCreate(recruiter_id="rec-001")
        assert m.recruiter_id == "rec-001"

    def test_with_extras(self):
        m = PersonalizationSettingsCreate(
            recruiter_id="rec-002",
            theme="light",
            language="en-US",
        )
        assert m.language == "en-US"


class TestPersonalizationSettingsUpdate:
    def test_empty(self):
        m = PersonalizationSettingsUpdate()
        assert m is not None

    def test_update_theme(self):
        m = PersonalizationSettingsUpdate(theme="dark")
        assert m.theme == "dark"


class TestPersonalizationSettingsResponse:
    def test_basic(self):
        m = PersonalizationSettingsResponse(
            recruiter_id="rec-001",
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.recruiter_id == "rec-001"
        assert m.created_at == _DT

    def test_with_settings(self):
        m = PersonalizationSettingsResponse(
            recruiter_id="rec-002",
            theme="dark",
            language="pt-BR",
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.theme == "dark"


class TestPersonalizationEventCreate:
    def test_basic(self):
        m = PersonalizationEventCreate(
            recruiter_id="rec-001",
            company_id="co-001",
            event_type="theme_changed",
        )
        assert m.recruiter_id == "rec-001"
        assert m.event_type == "theme_changed"

    def test_with_payload(self):
        m = PersonalizationEventCreate(
            recruiter_id="rec-001",
            company_id="co-001",
            event_type="default_updated",
            payload={"field": "contract_type", "value": "CLT"},
        )
        assert m.payload["field"] == "contract_type"


class TestPersonalizationEventResponse:
    def test_basic(self):
        m = PersonalizationEventResponse(
            recruiter_id="rec-001",
            company_id="co-001",
            event_type="login",
            id="event-001",
            created_at=_DT,
        )
        assert m.id == "event-001"
        assert m.event_type == "login"


class TestRecruiterFieldPreferenceBase:
    def test_basic(self):
        m = RecruiterFieldPreferenceBase(
            recruiter_id="rec-001",
            field_name="contract_type",
        )
        assert m.recruiter_id == "rec-001"
        assert m.field_name == "contract_type"

    def test_with_value(self):
        m = RecruiterFieldPreferenceBase(
            recruiter_id="rec-002",
            field_name="seniority",
            preferred_value="senior",
        )
        assert m.preferred_value == "senior"


class TestRecruiterFieldPreferenceResponse:
    def test_basic(self):
        m = RecruiterFieldPreferenceResponse(
            recruiter_id="rec-001",
            field_name="currency",
            id="pref-001",
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.id == "pref-001"
        assert m.field_name == "currency"


class TestRecruiterProfileBase:
    def test_basic(self):
        m = RecruiterProfileBase(recruiter_id="rec-001", company_id="co-001")
        assert m.recruiter_id == "rec-001"
        assert m.company_id == "co-001"

    def test_optional_fields(self):
        m = RecruiterProfileBase(
            recruiter_id="rec-002",
            company_id="co-002",
            display_name="Ana Recruiter",
            avatar_url="https://cdn.example.com/avatar.jpg",
        )
        assert m.display_name == "Ana Recruiter"


class TestRecruiterProfileCreate:
    def test_basic(self):
        m = RecruiterProfileCreate(recruiter_id="rec-001", company_id="co-001")
        assert m.recruiter_id == "rec-001"


class TestRecruiterProfileUpdate:
    def test_empty(self):
        m = RecruiterProfileUpdate()
        assert m is not None

    def test_partial(self):
        m = RecruiterProfileUpdate(display_name="New Name")
        assert m.display_name == "New Name"


class TestRecruiterProfileResponse:
    def test_basic(self):
        m = RecruiterProfileResponse(
            recruiter_id="rec-001",
            company_id="co-001",
            id="prof-001",
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.id == "prof-001"
        assert m.recruiter_id == "rec-001"

    def test_with_full_profile(self):
        m = RecruiterProfileResponse(
            recruiter_id="rec-002",
            company_id="co-002",
            id="prof-002",
            display_name="Ana Silva",
            created_at=_DT,
            updated_at=_DT,
        )
        assert m.display_name == "Ana Silva"


class TestRecruiterPersonalizationContext:
    def test_basic(self):
        m = RecruiterPersonalizationContext(recruiter_id="rec-001")
        assert m.recruiter_id == "rec-001"

    def test_with_company(self):
        m = RecruiterPersonalizationContext(
            recruiter_id="rec-002",
            company_id="co-001",
            context_data={"last_job_title": "Backend Dev"},
        )
        assert m.company_id == "co-001"
        assert m.context_data["last_job_title"] == "Backend Dev"
