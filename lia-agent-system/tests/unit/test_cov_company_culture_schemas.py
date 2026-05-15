"""Coverage tests for app/schemas/company_culture.py — Pydantic models."""
import pytest
from uuid import UUID
from app.schemas.company_culture import (
    CompanyCultureProfileBase,
    CompanyCultureProfileCreate,
    CompanyCultureProfileUpdate,
    CompanyCultureProfileResponse,
    CultureAnalysisRequest,
    CultureAnalysisDirectRequest,
    CultureAnalysisJobResponse,
    CultureAnalysisJobStatus,
    BigFiveOrgProfile,
    CultureAnalysisResult,
    ScrapedPageContent,
)


class TestCompanyCultureProfileBase:
    def test_minimal(self):
        m = CompanyCultureProfileBase(website_url="https://wedotalent.cc")
        assert m.website_url == "https://wedotalent.cc"
        assert m.values == []
        assert m.evp_bullets == []
        assert m.openness_score == 50  # default
        assert m.conscientiousness_score == 50  # default

    def test_with_scores(self):
        m = CompanyCultureProfileBase(
            website_url="https://example.com",
            openness_score=70,
            conscientiousness_score=80,
            extraversion_score=60,
            mission="Build the future",
            vision="A world where hiring is fair",
            values=["innovation", "integrity", "diversity"],
        )
        assert m.openness_score == 70
        assert m.conscientiousness_score == 80
        assert "innovation" in m.values

    def test_optional_fields(self):
        m = CompanyCultureProfileBase(website_url="https://co.com")
        assert m.mission is None
        assert m.vision is None
        assert m.linkedin_url is None
        assert m.culture_description is None


_UUID1 = UUID("550e8400-e29b-41d4-a716-446655440000")
_UUID2 = UUID("550e8400-e29b-41d4-a716-446655440001")
_UUID3 = UUID("550e8400-e29b-41d4-a716-446655440002")
_UUID4 = UUID("550e8400-e29b-41d4-a716-446655440003")


class TestCompanyCultureProfileLegacyNullCoercion:
    """Task #1098 — guarantee legacy DB rows with NULL columns don't 500.

    The SQLAlchemy model uses Python-side ``default=[]`` / ``default=50`` and
    no ``server_default`` / ``NOT NULL`` for the array and score columns, so
    rows written before those defaults existed (or via raw SQL) carry NULL.
    The response schema now coerces those NULLs to the documented defaults so
    the wizard's culture-profile step doesn't fail with ``ResponseValidationError``.
    """

    def _legacy_row(self) -> dict:
        return {
            "website_url": "https://legacy.example.com",
            "values": None,
            "evp_bullets": None,
            "core_competencies": None,
            "analyzed_pages": None,
            "locations": None,
            "tech_stack": None,
            "default_languages": None,
            "openness_score": None,
            "conscientiousness_score": None,
            "extraversion_score": None,
            "agreeableness_score": None,
            "stability_score": None,
        }

    def test_base_coerces_null_arrays_and_scores(self):
        m = CompanyCultureProfileBase(**self._legacy_row())
        assert m.values == []
        assert m.evp_bullets == []
        assert m.core_competencies == []
        assert m.analyzed_pages == []
        assert m.locations == []
        assert m.tech_stack == []
        assert m.default_languages == []
        assert m.openness_score == 50
        assert m.conscientiousness_score == 50
        assert m.extraversion_score == 50
        assert m.agreeableness_score == 50
        assert m.stability_score == 50

    def test_response_validates_full_legacy_row(self):
        from datetime import datetime as _dt

        payload = {
            **self._legacy_row(),
            "id": _UUID1,
            "company_id": _UUID2,
            "source": "auto",
            "confidence_score": 0.5,
            "last_analysis_at": _dt(2024, 1, 1, 12, 0, 0),
            "created_at": _dt(2024, 1, 1, 12, 0, 0),
            "updated_at": _dt(2024, 1, 1, 12, 0, 0),
        }
        m = CompanyCultureProfileResponse(**payload)
        assert m.values == []
        assert m.openness_score == 50
        assert m.website_url == "https://legacy.example.com"

    def test_populated_values_pass_through_unchanged(self):
        row = self._legacy_row()
        row["values"] = ["transparency"]
        row["openness_score"] = 73
        m = CompanyCultureProfileBase(**row)
        assert m.values == ["transparency"]
        assert m.openness_score == 73
        assert m.evp_bullets == []  # still coerced

    def test_response_from_attributes_orm_path(self):
        """Production path: FastAPI calls ``model_validate(orm_row)`` with
        ``from_attributes=True``. The validator must coerce NULLs read off
        the ORM object's attributes, not just dict keys."""
        from datetime import datetime as _dt

        class _OrmRow:
            pass

        # simulate a SQLAlchemy ``CompanyCultureProfile`` row whose
        # array/score columns were never populated (legacy NULLs)
        row = _OrmRow()
        row.id = _UUID1
        row.company_id = _UUID2
        row.website_url = "https://legacy.example.com"
        row.linkedin_url = None
        row.mission = None
        row.vision = None
        row.culture_description = None
        row.values = None
        row.evp_bullets = None
        row.core_competencies = None
        row.analyzed_pages = None
        row.locations = None
        row.tech_stack = None
        row.default_languages = None
        row.openness_score = None
        row.conscientiousness_score = None
        row.extraversion_score = None
        row.agreeableness_score = None
        row.stability_score = None
        row.industry = None
        row.employee_count = None
        row.company_size = None
        row.headquarters = None
        row.founded_year = None
        row.work_model = None
        row.growth_opportunities = None
        row.team_dynamics = None
        row.leadership_style = None
        row.dei_initiatives = None
        row.sustainability = None
        row.social_impact = None
        row.engineering_culture = None
        row.source = "auto"
        row.confidence_score = 0.5
        row.last_analysis_at = _dt(2024, 1, 1, 12, 0, 0)
        row.created_at = _dt(2024, 1, 1, 12, 0, 0)
        row.updated_at = _dt(2024, 1, 1, 12, 0, 0)

        m = CompanyCultureProfileResponse.model_validate(row, from_attributes=True)
        assert m.values == []
        assert m.evp_bullets == []
        assert m.tech_stack == []
        assert m.default_languages == []
        assert m.openness_score == 50
        assert m.stability_score == 50
        assert m.website_url == "https://legacy.example.com"


class TestCompanyCultureProfileCreate:
    def test_basic(self):
        m = CompanyCultureProfileCreate(
            website_url="https://company.com",
            company_id=_UUID1,
        )
        assert m.website_url == "https://company.com"
        assert m.company_id == _UUID1

    def test_with_url(self):
        m = CompanyCultureProfileCreate(
            website_url="https://tech.company.io",
            company_id=_UUID2,
            linkedin_url="https://linkedin.com/company/tech",
            analyzed_pages=["about", "careers", "culture"],
        )
        assert m.linkedin_url == "https://linkedin.com/company/tech"
        assert len(m.analyzed_pages) == 3


class TestCompanyCultureProfileUpdate:
    def test_all_optional(self):
        m = CompanyCultureProfileUpdate()
        assert m.mission is None
        assert m.values is None
        assert m.openness_score is None

    def test_update_mission(self):
        m = CompanyCultureProfileUpdate(
            mission="Empowering talent globally",
            openness_score=75,
        )
        assert m.mission == "Empowering talent globally"
        assert m.openness_score == 75


class TestCultureAnalysisRequest:
    def test_basic(self):
        company_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        m = CultureAnalysisRequest(
            website_url="https://company.com",
            company_id=company_uuid,
        )
        assert m.website_url == "https://company.com"
        assert m.company_id == company_uuid
        assert m.force_refresh is False  # default

    def test_force_refresh(self):
        company_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
        m = CultureAnalysisRequest(
            website_url="https://updated.com",
            company_id=company_uuid,
            force_refresh=True,
        )
        assert m.force_refresh is True


class TestCultureAnalysisDirectRequest:
    def test_basic(self):
        m = CultureAnalysisDirectRequest(website_url="https://startup.io")
        assert m.website_url == "https://startup.io"
        assert m.linkedin_url is None
        assert m.company_id is None

    def test_with_linkedin(self):
        m = CultureAnalysisDirectRequest(
            website_url="https://bigcorp.com",
            linkedin_url="https://linkedin.com/company/bigcorp",
            company_id="co-uuid-001",
        )
        assert m.linkedin_url == "https://linkedin.com/company/bigcorp"
        assert m.company_id == "co-uuid-001"


class TestBigFiveOrgProfile:
    def test_defaults(self):
        m = BigFiveOrgProfile()
        assert m.openness == 50
        assert m.conscientiousness == 50
        assert m.extraversion == 50
        assert m.agreeableness == 50
        assert m.stability == 50

    def test_custom_scores(self):
        m = BigFiveOrgProfile(
            openness=85,
            conscientiousness=70,
            extraversion=60,
            agreeableness=75,
            stability=80,
        )
        assert m.openness == 85
        assert m.conscientiousness == 70
        assert m.agreeableness == 75

    def test_boundary_values(self):
        m = BigFiveOrgProfile(
            openness=0,
            conscientiousness=100,
            extraversion=0,
            agreeableness=100,
            stability=50,
        )
        assert m.openness == 0
        assert m.conscientiousness == 100


class TestCultureAnalysisResult:
    def test_with_big_five(self):
        bf = BigFiveOrgProfile()
        m = CultureAnalysisResult(big_five=bf)
        assert m.mission is None
        assert m.values == []
        assert m.big_five.openness == 50

    def test_with_data(self):
        bf = BigFiveOrgProfile(openness=80, conscientiousness=70, extraversion=60, agreeableness=75, stability=65)
        m = CultureAnalysisResult(
            mission="Build tools for better hiring",
            vision="Fair hiring for everyone",
            values=["transparency", "excellence"],
            evp_bullets=["Remote-first", "Great benefits"],
            big_five=bf,
        )
        assert m.mission == "Build tools for better hiring"
        assert "transparency" in m.values
        assert m.big_five.openness == 80


class TestScrapedPageContent:
    def test_basic(self):
        m = ScrapedPageContent(
            url="https://company.com/about",
            content="We are a company that builds amazing things.",
            page_type="about",
        )
        assert m.url == "https://company.com/about"
        assert m.page_type == "about"

    def test_careers_page(self):
        m = ScrapedPageContent(
            url="https://company.com/careers",
            content="Join our team! We offer great opportunities.",
            page_type="careers",
        )
        assert m.page_type == "careers"


class TestCultureAnalysisJobResponse:
    def test_pending(self):
        m = CultureAnalysisJobResponse(
            job_id=_UUID3,
            status="pending",
            progress=0,
            message="Queued for processing",
        )
        assert m.job_id == _UUID3
        assert m.status == "pending"
        assert m.progress == 0

    def test_completed(self):
        m = CultureAnalysisJobResponse(
            job_id=_UUID4,
            status="completed",
            progress=100,
            message="Analysis complete",
        )
        assert m.status == "completed"
        assert m.progress == 100


class TestCultureAnalysisJobStatus:
    def test_in_progress(self):
        m = CultureAnalysisJobStatus(
            job_id=_UUID3,
            status="in_progress",
            progress=50,
            created_at="2024-05-10T10:00:00Z",
        )
        assert m.status == "in_progress"
        assert m.progress == 50

    def test_completed(self):
        m = CultureAnalysisJobStatus(
            job_id=_UUID4,
            status="completed",
            progress=100,
            created_at="2024-05-10T09:00:00Z",
        )
        assert m.progress == 100
