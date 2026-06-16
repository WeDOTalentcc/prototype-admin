"""Coverage tests for app/schemas/job_description.py — enums and Pydantic models."""
import pytest
from app.schemas.job_description import (
    SuggestionSource,
    RequirementLevel,
    WorkModel,
    ContractType,
    SuggestedItem,
    Competency,
    Responsibility,
)


class TestSuggestionSource:
    def test_detected(self):
        assert SuggestionSource.DETECTED == "detected"

    def test_lia_catalog(self):
        assert SuggestionSource.LIA_CATALOG == "lia_catalog"

    def test_lia_market(self):
        assert SuggestionSource.LIA_MARKET == "lia_market"

    def test_company_default(self):
        assert SuggestionSource.COMPANY_DEFAULT == "company_default"

    def test_recruiter(self):
        assert SuggestionSource.RECRUITER == "recruiter"


class TestRequirementLevel:
    def test_required(self):
        assert RequirementLevel.REQUIRED == "required"

    def test_nice_to_have(self):
        assert RequirementLevel.NICE_TO_HAVE == "nice_to_have"


class TestWorkModel:
    def test_remote(self):
        assert WorkModel.REMOTE == "remoto"

    def test_hybrid(self):
        assert WorkModel.HYBRID == "hibrido"

    def test_onsite(self):
        assert WorkModel.ONSITE == "presencial"


class TestContractType:
    def test_clt(self):
        assert ContractType.CLT == "CLT"

    def test_pj(self):
        assert ContractType.PJ == "PJ"

    def test_estagio(self):
        assert ContractType.ESTAGIO == "Estágio"

    def test_temporario(self):
        assert ContractType.TEMPORARIO == "Temporário"

    def test_freelancer(self):
        assert ContractType.FREELANCER == "Freelancer"


class TestSuggestedItem:
    def test_basic(self):
        m = SuggestedItem(value="Python")
        assert m.value == "Python"

    def test_with_source(self):
        m = SuggestedItem(
            value="Docker",
            source=SuggestionSource.LIA_CATALOG,
            confidence=0.9,
        )
        assert m.source == "lia_catalog"
        assert m.confidence == pytest.approx(0.9)

    def test_is_new(self):
        m = SuggestedItem(
            value="Kubernetes",
            source=SuggestionSource.LIA_MARKET,
            is_new=True,
        )
        assert m.is_new is True

    def test_defaults(self):
        m = SuggestedItem(value="React")
        assert m.source is not None  # has default
        assert m.confidence is None
        assert m.is_new is False  # default False

    def test_recruiter_added(self):
        m = SuggestedItem(
            value="Team leadership",
            source=SuggestionSource.RECRUITER,
        )
        assert m.source == "recruiter"

    def test_detected(self):
        m = SuggestedItem(
            value="Bachelor's degree in Computer Science",
            source=SuggestionSource.DETECTED,
            confidence=1.0,
        )
        assert m.source == "detected"


class TestCompetency:
    def test_basic(self):
        m = Competency(name="Leadership")
        assert m.name == "Leadership"

    def test_with_level(self):
        from app.schemas.job_description import RequirementLevel
        m = Competency(
            name="Problem Solving",
            level=RequirementLevel.NICE_TO_HAVE,
        )
        assert m.level == RequirementLevel.NICE_TO_HAVE

    def test_technical_competency(self):
        m = Competency(
            name="Software Architecture",
            source=SuggestionSource.LIA_CATALOG,
            years_experience=5,
            proficiency="expert",
        )
        assert m.name == "Software Architecture"
        assert m.source == "lia_catalog"
        assert m.years_experience == 5
        assert m.proficiency == "expert"

    def test_defaults(self):
        m = Competency(name="Communication")
        assert m.level is not None  # has default "required"
        assert m.source is not None  # has default
        assert m.years_experience is None
        assert m.proficiency is None

    def test_soft_skill(self):
        m = Competency(
            name="Emotional Intelligence",
            is_new=True,
        )
        assert m.name == "Emotional Intelligence"
        assert m.is_new is True


class TestResponsibility:
    def test_basic(self):
        m = Responsibility(description="Develop backend APIs using FastAPI")
        assert m.description == "Develop backend APIs using FastAPI"

    def test_with_source(self):
        m = Responsibility(
            description="Lead technical architecture decisions",
            source=SuggestionSource.DETECTED,
        )
        assert m.source == "detected"

    def test_is_new(self):
        m = Responsibility(
            description="Manage team of 3-5 engineers",
            is_new=True,
        )
        assert m.is_new is True

    def test_defaults(self):
        m = Responsibility(description="Write unit tests for all new features")
        assert m.source is not None  # has default
        assert m.is_new is False  # default False

    def test_multiple_responsibilities(self):
        items = [
            Responsibility(description="Design database schema"),
            Responsibility(description="Implement REST APIs"),
            Responsibility(description="Write technical documentation"),
        ]
        assert len(items) == 3
        assert items[0].description == "Design database schema"
        assert items[2].description == "Write technical documentation"
