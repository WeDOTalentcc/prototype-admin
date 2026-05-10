"""Coverage tests for app/schemas/trust_center.py — enums and Pydantic models."""
import pytest
from app.schemas.trust_center import (
    SubprocessorCategoryEnum,
    ResourceCategoryEnum,
    UpdateCategoryEnum,
    TrustCenterSettingsBase,
    TrustCenterSettingsCreate,
    TrustCenterSettingsUpdate,
    TrustCenterSettingsResponse,
    SubprocessorBase,
    SubprocessorCreate,
    SubprocessorResponse,
    SubprocessorListResponse,
    TrustCenterResourceBase,
    TrustCenterResourceCreate,
    TrustCenterResourceResponse,
    TrustCenterResourceListResponse,
    TrustCenterUpdateBase,
    TrustCenterUpdateCreate,
    TrustCenterUpdateResponse,
    TrustCenterUpdateListResponse,
    CertificationInfo,
)


class TestSubprocessorCategoryEnum:
    def test_has_values(self):
        values = list(SubprocessorCategoryEnum)
        assert len(values) > 0

    def test_other_exists(self):
        assert SubprocessorCategoryEnum.OTHER is not None


class TestResourceCategoryEnum:
    def test_has_values(self):
        values = list(ResourceCategoryEnum)
        assert len(values) > 0

    def test_other_exists(self):
        assert ResourceCategoryEnum.OTHER is not None


class TestUpdateCategoryEnum:
    def test_has_values(self):
        values = list(UpdateCategoryEnum)
        assert len(values) > 0


class TestTrustCenterSettingsBase:
    def test_basic(self):
        m = TrustCenterSettingsBase(
            company_slug="wedotalent",
            company_name="WeDOTalent",
        )
        assert m.company_slug == "wedotalent"
        assert m.company_name == "WeDOTalent"
        assert m.is_public is False  # default
        assert m.show_certifications is True  # default

    def test_with_all_fields(self):
        m = TrustCenterSettingsBase(
            company_slug="acme-corp",
            company_name="ACME Corporation",
            company_description="We build amazing things",
            logo_url="https://acme.com/logo.png",
            primary_color="#FF5733",
            is_public=True,
            contact_email="trust@acme.com",
        )
        assert m.is_public is True
        assert m.primary_color == "#FF5733"
        assert m.contact_email == "trust@acme.com"

    def test_defaults(self):
        m = TrustCenterSettingsBase(
            company_slug="test-co",
            company_name="Test Co",
        )
        assert m.show_controls is True
        assert m.show_bias_audits is True
        assert m.show_subprocessors is True


class TestTrustCenterSettingsCreate:
    def test_inherits_base(self):
        m = TrustCenterSettingsCreate(
            company_slug="my-company",
            company_name="My Company",
        )
        assert m.company_slug == "my-company"

    def test_with_public(self):
        m = TrustCenterSettingsCreate(
            company_slug="open-co",
            company_name="Open Co",
            is_public=True,
        )
        assert m.is_public is True


class TestTrustCenterSettingsUpdate:
    def test_all_optional(self):
        m = TrustCenterSettingsUpdate()
        assert m.company_name is None
        assert m.is_public is None

    def test_update_public(self):
        m = TrustCenterSettingsUpdate(is_public=True, primary_color="#333333")
        assert m.is_public is True
        assert m.primary_color == "#333333"


class TestSubprocessorBase:
    def test_basic(self):
        m = SubprocessorBase(name="AWS")
        assert m.name == "AWS"
        assert m.is_public is True  # default
        assert m.category == SubprocessorCategoryEnum.OTHER  # default

    def test_with_category(self):
        first_cat = list(SubprocessorCategoryEnum)[0]
        m = SubprocessorBase(
            name="OpenAI",
            category=first_cat,
            description="LLM provider",
            country="US",
            data_processed="Job descriptions, candidate summaries",
        )
        assert m.description == "LLM provider"
        assert m.country == "US"


class TestSubprocessorCreate:
    def test_basic(self):
        m = SubprocessorCreate(name="Google Cloud")
        assert m.name == "Google Cloud"


class TestSubprocessorListResponse:
    def test_empty(self):
        m = SubprocessorListResponse(subprocessors=[], total=0)
        assert m.subprocessors == []
        assert m.total == 0

    def test_with_more(self):
        m = SubprocessorListResponse(
            subprocessors=[],
            total=50,
        )
        assert m.total == 50


class TestTrustCenterResourceBase:
    def test_basic(self):
        m = TrustCenterResourceBase(
            title="Privacy Policy",
            file_url="https://cdn.example.com/privacy.pdf",
        )
        assert m.title == "Privacy Policy"
        assert m.file_url == "https://cdn.example.com/privacy.pdf"
        assert m.is_public is True  # default
        assert m.requires_nda is False  # default

    def test_nda_required(self):
        m = TrustCenterResourceBase(
            title="Security Audit Report",
            file_url="https://cdn.example.com/audit.pdf",
            is_public=False,
            requires_nda=True,
            description="Annual penetration test results",
        )
        assert m.requires_nda is True
        assert m.is_public is False


class TestTrustCenterResourceCreate:
    def test_basic(self):
        m = TrustCenterResourceCreate(
            title="SOC 2 Report",
            file_url="https://cdn.example.com/soc2.pdf",
        )
        assert m.title == "SOC 2 Report"


class TestTrustCenterResourceListResponse:
    def test_empty(self):
        m = TrustCenterResourceListResponse(resources=[], total=0)
        assert m.total == 0


class TestTrustCenterUpdateBase:
    def test_basic(self):
        m = TrustCenterUpdateBase(
            title="Q1 2024 Security Update",
            content="We've improved our data encryption.",
        )
        assert m.title == "Q1 2024 Security Update"
        assert "encryption" in m.content

    def test_optional_fields(self):
        m = TrustCenterUpdateBase(
            title="Service Update",
            content="Scheduled maintenance completed.",
        )
        assert m.category is not None  # has default


class TestTrustCenterUpdateCreate:
    def test_basic(self):
        m = TrustCenterUpdateCreate(
            title="New Feature",
            content="We added two-factor authentication.",
        )
        assert m.title == "New Feature"


class TestTrustCenterUpdateListResponse:
    def test_empty(self):
        m = TrustCenterUpdateListResponse(updates=[], total=0)
        assert m.updates == []
        assert m.total == 0


class TestCertificationInfo:
    def test_basic(self):
        m = CertificationInfo(
            name="ISO 27001",
            status="certified",
        )
        assert m.name == "ISO 27001"
        assert m.status == "certified"

    def test_with_expiry(self):
        m = CertificationInfo(
            name="SOC 2 Type II",
            status="certified",
            issued_date="2024-01-15",
            expires_date="2025-01-15",
            badge_url="https://example.com/badge.png",
        )
        assert m.badge_url == "https://example.com/badge.png"
        assert m.issued_date is not None
