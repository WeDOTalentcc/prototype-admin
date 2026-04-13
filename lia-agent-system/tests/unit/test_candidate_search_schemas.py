"""
Unit tests for candidate_search.py DTOs and helper functions — Sprint I4 (coverage gate 40%).

Cobre modelos Pydantic e helpers puros sem dependência de DB ou API externa:
  - SearchRequestDTO: defaults, validação de campos
  - ExperienceDTO: campos opcionais
  - ImportCandidateExperienceDTO: campos
  - ImportCandidateDTO: campos e defaults
  - ImportCandidatesRequest: validação
  - ImportCandidatesResponse: contagem e mapeamento
  - IdMapping: round-trip
  - EducationDTO / LanguageDTO: campos
  - _normalize_priority(): enum, string, None, PyEnum ORM
"""
import pytest

pytestmark = pytest.mark.easy

from enum import Enum as PyEnum
from app.api.v1.candidate_search import (
    SearchRequestDTO,
    ExperienceDTO,
    ImportCandidateExperienceDTO,
    ImportCandidateDTO,
    ImportCandidatesRequest,
    ImportCandidatesResponse,
    IdMapping,
    EducationDTO,
    LanguageDTO,
    _normalize_priority,
)
from app.schemas.rubric import RequirementPriorityEnum


# ── SearchRequestDTO ───────────────────────────────────────────────────────────

class TestSearchRequestDTO:
    def test_required_query(self):
        dto = SearchRequestDTO(query="engenheiro Python")
        assert dto.query == "engenheiro Python"

    def test_defaults_search_local_true(self):
        dto = SearchRequestDTO(query="test")
        assert dto.search_local is True

    def test_defaults_search_pearch_true(self):
        dto = SearchRequestDTO(query="test")
        assert dto.search_pearch is True

    def test_defaults_pearch_type_fast(self):
        dto = SearchRequestDTO(query="test")
        assert dto.pearch_type == "fast"

    def test_defaults_local_limit(self):
        dto = SearchRequestDTO(query="test")
        assert dto.local_limit == 20

    def test_defaults_pearch_limit(self):
        dto = SearchRequestDTO(query="test")
        assert dto.pearch_limit == 15

    def test_defaults_show_emails_false(self):
        dto = SearchRequestDTO(query="test")
        assert dto.show_emails is False

    def test_defaults_show_phones_false(self):
        dto = SearchRequestDTO(query="test")
        assert dto.show_phone_numbers is False

    def test_defaults_high_freshness_false(self):
        dto = SearchRequestDTO(query="test")
        assert dto.high_freshness is False

    def test_defaults_include_discovered_true(self):
        dto = SearchRequestDTO(query="test")
        assert dto.include_discovered is True

    def test_defaults_exclude_candidate_ids_empty(self):
        dto = SearchRequestDTO(query="test")
        assert dto.exclude_candidate_ids == []

    def test_thread_id_optional(self):
        dto = SearchRequestDTO(query="test", thread_id="abc-123")
        assert dto.thread_id == "abc-123"

    def test_job_id_optional(self):
        dto = SearchRequestDTO(query="test", job_id="job-uuid")
        assert dto.job_id == "job-uuid"

    def test_custom_limits(self):
        dto = SearchRequestDTO(query="test", local_limit=50, pearch_limit=30)
        assert dto.local_limit == 50
        assert dto.pearch_limit == 30

    def test_pearch_type_defaults_to_fast(self):
        dto = SearchRequestDTO(query="test")
        assert dto.pearch_type == "fast"

    def test_search_spec_optional(self):
        dto = SearchRequestDTO(query="test", search_spec={"location": "SP"})
        assert dto.search_spec == {"location": "SP"}


# ── ExperienceDTO ──────────────────────────────────────────────────────────────

class TestExperienceDTO:
    def test_all_optional_fields(self):
        dto = ExperienceDTO()
        assert dto.title is None
        assert dto.company is None
        assert dto.current is False

    def test_industries_default_empty(self):
        dto = ExperienceDTO()
        assert dto.industries == []

    def test_technologies_default_empty(self):
        dto = ExperienceDTO()
        assert dto.technologies == []

    def test_with_values(self):
        dto = ExperienceDTO(
            title="Engenheiro de Software",
            company="ACME",
            current=True,
            duration_years=2.5,
        )
        assert dto.title == "Engenheiro de Software"
        assert dto.company == "ACME"
        assert dto.current is True
        assert dto.duration_years == 2.5


# ── ImportCandidateExperienceDTO ───────────────────────────────────────────────

class TestImportCandidateExperienceDTO:
    def test_required_company_name(self):
        dto = ImportCandidateExperienceDTO(company_name="ACME Corp")
        assert dto.company_name == "ACME Corp"

    def test_optional_fields_default_none(self):
        dto = ImportCandidateExperienceDTO(company_name="ACME")
        assert dto.title is None
        assert dto.is_current is False
        assert dto.industries == []

    def test_is_startup_field(self):
        dto = ImportCandidateExperienceDTO(company_name="Startup X", is_startup=True)
        assert dto.is_startup is True


# ── ImportCandidateDTO ─────────────────────────────────────────────────────────

class TestImportCandidateDTO:
    def test_required_fields(self):
        dto = ImportCandidateDTO(pearch_id="pearch-123", name="João Silva")
        assert dto.pearch_id == "pearch-123"
        assert dto.name == "João Silva"

    def test_skills_default_empty(self):
        dto = ImportCandidateDTO(pearch_id="x", name="Test")
        assert dto.skills == []

    def test_emails_defaults_empty(self):
        dto = ImportCandidateDTO(pearch_id="x", name="Test")
        assert dto.personal_emails == []
        assert dto.business_emails == []

    def test_expertise_default_empty(self):
        dto = ImportCandidateDTO(pearch_id="x", name="Test")
        assert dto.expertise == []

    def test_optional_email(self):
        dto = ImportCandidateDTO(pearch_id="x", name="Test", email="test@example.com")
        assert dto.email == "test@example.com"

    def test_optional_linkedin_url(self):
        dto = ImportCandidateDTO(pearch_id="x", name="Test", linkedin_url="https://linkedin.com/in/test")
        assert "linkedin.com" in dto.linkedin_url


# ── ImportCandidatesRequest ────────────────────────────────────────────────────

class TestImportCandidatesRequest:
    def test_candidates_list(self):
        c = ImportCandidateDTO(pearch_id="x", name="Test")
        req = ImportCandidatesRequest(candidates=[c])
        assert len(req.candidates) == 1

    def test_empty_candidates(self):
        req = ImportCandidatesRequest(candidates=[])
        assert req.candidates == []

    def test_optional_source_query(self):
        c = ImportCandidateDTO(pearch_id="x", name="Test")
        req = ImportCandidatesRequest(candidates=[c], source_search_query="Python SR")
        assert req.source_search_query == "Python SR"

    def test_optional_vacancy_id(self):
        c = ImportCandidateDTO(pearch_id="x", name="Test")
        req = ImportCandidatesRequest(candidates=[c], add_to_vacancy_id="vaga-123")
        assert req.add_to_vacancy_id == "vaga-123"


# ── ImportCandidatesResponse ───────────────────────────────────────────────────

class TestImportCandidatesResponse:
    def test_basic_response(self):
        resp = ImportCandidatesResponse(
            imported_count=3,
            skipped_count=1,
            imported_ids=["a", "b", "c"],
            skipped_ids=["d"],
            mapping=[],
            message="OK",
        )
        assert resp.imported_count == 3
        assert resp.skipped_count == 1
        assert len(resp.imported_ids) == 3

    def test_updated_count_defaults_zero(self):
        resp = ImportCandidatesResponse(
            imported_count=0,
            skipped_count=0,
            imported_ids=[],
            skipped_ids=[],
            mapping=[],
            message="OK",
        )
        assert resp.updated_count == 0

    def test_mapping_field(self):
        mapping = [IdMapping(pearch_id="p1", local_id="l1")]
        resp = ImportCandidatesResponse(
            imported_count=1,
            skipped_count=0,
            imported_ids=["l1"],
            skipped_ids=[],
            mapping=mapping,
            message="OK",
        )
        assert resp.mapping[0].pearch_id == "p1"
        assert resp.mapping[0].local_id == "l1"


# ── IdMapping ──────────────────────────────────────────────────────────────────

class TestIdMapping:
    def test_fields(self):
        m = IdMapping(pearch_id="pearch-abc", local_id="local-xyz")
        assert m.pearch_id == "pearch-abc"
        assert m.local_id == "local-xyz"

    def test_round_trip_json(self):
        m = IdMapping(pearch_id="p1", local_id="l1")
        data = m.model_dump()
        m2 = IdMapping(**data)
        assert m2.pearch_id == m.pearch_id


# ── EducationDTO ───────────────────────────────────────────────────────────────

class TestEducationDTO:
    def test_all_optional(self):
        dto = EducationDTO()
        assert dto.school is None
        assert dto.degree is None

    def test_with_values(self):
        dto = EducationDTO(school="USP", degree="Bacharelado", field_of_study="Ciência da Computação")
        assert dto.school == "USP"
        assert dto.field_of_study == "Ciência da Computação"


# ── LanguageDTO ────────────────────────────────────────────────────────────────

class TestLanguageDTO:
    def test_all_optional(self):
        dto = LanguageDTO()
        assert dto.language is None
        assert dto.name is None

    def test_with_language(self):
        dto = LanguageDTO(language="Inglês", name="English")
        assert dto.language == "Inglês"


# ── _normalize_priority ────────────────────────────────────────────────────────

class TestNormalizePriority:
    def test_none_returns_important(self):
        result = _normalize_priority(None)
        assert result == RequirementPriorityEnum.IMPORTANT

    def test_already_enum_passthrough(self):
        result = _normalize_priority(RequirementPriorityEnum.IMPORTANT)
        assert result == RequirementPriorityEnum.IMPORTANT

    def test_string_essential(self):
        result = _normalize_priority("essential")
        assert result == RequirementPriorityEnum.ESSENTIAL

    def test_string_important(self):
        result = _normalize_priority("important")
        assert result == RequirementPriorityEnum.IMPORTANT

    def test_string_nice_to_have(self):
        result = _normalize_priority("nice_to_have")
        assert result == RequirementPriorityEnum.NICE_TO_HAVE

    def test_invalid_string_falls_back_to_important(self):
        result = _normalize_priority("invalid_value_xyz")
        assert result == RequirementPriorityEnum.IMPORTANT

    def test_pyenum_subclass_uses_value(self):
        class FakePriority(PyEnum):
            VALUE = "important"

        result = _normalize_priority(FakePriority.VALUE)
        assert result == RequirementPriorityEnum.IMPORTANT

    def test_integer_falls_back_to_important(self):
        result = _normalize_priority(42)
        assert result == RequirementPriorityEnum.IMPORTANT
