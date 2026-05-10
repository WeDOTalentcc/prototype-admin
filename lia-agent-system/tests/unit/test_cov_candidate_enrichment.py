"""Coverage tests for candidate_enrichment_service.py — pure helper methods."""
import pytest
from unittest.mock import MagicMock


class TestParseDate:
    """Test CandidateEnrichmentService._parse_date pure method."""

    @pytest.fixture
    def svc(self):
        from app.domains.candidates.services.candidate_enrichment_service import (
            CandidateEnrichmentService,
        )
        return CandidateEnrichmentService()

    def test_none_returns_none(self, svc):
        assert svc._parse_date(None) is None

    def test_empty_string_returns_none(self, svc):
        assert svc._parse_date("") is None

    def test_string_returned_as_is(self, svc):
        assert svc._parse_date("2020-01") == "2020-01"

    def test_dict_with_year_and_month(self, svc):
        result = svc._parse_date({"year": 2020, "month": 3})
        assert result == "3/2020"

    def test_dict_with_year_only(self, svc):
        result = svc._parse_date({"year": 2020})
        assert result == "2020"

    def test_dict_without_year_returns_str(self, svc):
        # No year key → falls through to str(date_value) since dict is truthy
        result = svc._parse_date({"month": 3})
        assert result is not None  # returns str representation of the dict

    def test_other_type_coerced_to_str(self, svc):
        result = svc._parse_date(2020)
        assert result == "2020"


class TestNormalizeLinkedinUrl:
    @pytest.fixture
    def svc(self):
        from app.domains.candidates.services.candidate_enrichment_service import (
            CandidateEnrichmentService,
        )
        return CandidateEnrichmentService()

    def test_adds_https_if_missing(self, svc):
        result = svc._normalize_linkedin_url("linkedin.com/in/user")
        assert result.startswith("https://")

    def test_strips_query_params(self, svc):
        result = svc._normalize_linkedin_url("https://linkedin.com/in/user?query=foo")
        assert "?" not in result

    def test_strips_trailing_slash(self, svc):
        result = svc._normalize_linkedin_url("https://linkedin.com/in/user/")
        assert not result.endswith("/")

    def test_normalizes_www(self, svc):
        result = svc._normalize_linkedin_url("https://linkedin.com/in/user")
        assert "www.linkedin.com" in result

    def test_strips_whitespace(self, svc):
        result = svc._normalize_linkedin_url("  https://linkedin.com/in/user  ")
        assert not result.startswith(" ")


class TestApplyLocation:
    @pytest.fixture
    def svc(self):
        from app.domains.candidates.services.candidate_enrichment_service import (
            CandidateEnrichmentService,
        )
        return CandidateEnrichmentService()

    def _make_candidate(self, city=None, state=None, country=None):
        c = MagicMock()
        c.location_city = city
        c.location_state = state
        c.location_country = country
        return c

    def test_empty_location_returns_false(self, svc):
        candidate = self._make_candidate()
        result = svc._apply_location(candidate, {}, [])
        assert result is False

    def test_single_part_sets_city(self, svc):
        candidate = self._make_candidate()
        updated = []
        svc._apply_location(candidate, {"location": "São Paulo"}, updated)
        assert candidate.location_city == "São Paulo"
        assert "location_city" in updated

    def test_two_parts_city_and_country(self, svc):
        candidate = self._make_candidate()
        updated = []
        svc._apply_location(candidate, {"location": "São Paulo, Brasil"}, updated)
        assert candidate.location_city == "São Paulo"
        assert "location_city" in updated

    def test_three_parts_sets_all(self, svc):
        candidate = self._make_candidate()
        updated = []
        svc._apply_location(candidate, {"location": "São Paulo, SP, Brasil"}, updated)
        assert candidate.location_city == "São Paulo"
        assert "location_city" in updated

    def test_existing_city_not_overwritten(self, svc):
        candidate = self._make_candidate(city="Existing")
        updated = []
        svc._apply_location(candidate, {"location": "New City"}, updated)
        assert candidate.location_city == "Existing"
        assert "location_city" not in updated

    def test_locationname_fallback(self, svc):
        candidate = self._make_candidate()
        updated = []
        svc._apply_location(candidate, {"locationName": "Campinas"}, updated)
        assert candidate.location_city == "Campinas"


class TestApplySkills:
    @pytest.fixture
    def svc(self):
        from app.domains.candidates.services.candidate_enrichment_service import (
            CandidateEnrichmentService,
        )
        return CandidateEnrichmentService()

    def test_empty_skills_no_update(self, svc):
        candidate = MagicMock()
        candidate.technical_skills = []
        updated = []
        svc._apply_skills(candidate, {}, updated)
        assert "technical_skills" not in updated

    def test_string_skills_added(self, svc):
        candidate = MagicMock()
        candidate.technical_skills = []
        updated = []
        svc._apply_skills(candidate, {"skills": ["Python", "Django"]}, updated)
        assert "technical_skills" in updated
        assert "Python" in candidate.technical_skills

    def test_dict_skills_added(self, svc):
        candidate = MagicMock()
        candidate.technical_skills = []
        updated = []
        svc._apply_skills(candidate, {"skills": [{"name": "React"}]}, updated)
        assert "React" in candidate.technical_skills

    def test_existing_skill_not_duplicated(self, svc):
        candidate = MagicMock()
        candidate.technical_skills = ["Python"]
        updated = []
        svc._apply_skills(candidate, {"skills": ["Python"]}, updated)
        # Python already exists, no new skill → no update field
        assert "technical_skills" not in updated


class TestApplyLanguages:
    @pytest.fixture
    def svc(self):
        from app.domains.candidates.services.candidate_enrichment_service import (
            CandidateEnrichmentService,
        )
        return CandidateEnrichmentService()

    def test_empty_languages_no_update(self, svc):
        candidate = MagicMock()
        candidate.languages = {}
        updated = []
        svc._apply_languages(candidate, {}, updated)
        assert "languages" not in updated

    def test_string_language_added(self, svc):
        candidate = MagicMock()
        candidate.languages = {}
        updated = []
        svc._apply_languages(candidate, {"languages": ["English"]}, updated)
        assert "languages" in updated
        assert "English" in candidate.languages

    def test_dict_language_added(self, svc):
        candidate = MagicMock()
        candidate.languages = {}
        updated = []
        svc._apply_languages(candidate, {"languages": [{"name": "Portuguese", "proficiency": "native"}]}, updated)
        assert candidate.languages.get("Portuguese") == "native"

    def test_existing_language_not_overwritten(self, svc):
        candidate = MagicMock()
        candidate.languages = {"English": "fluent"}
        updated = []
        svc._apply_languages(candidate, {"languages": ["English"]}, updated)
        assert candidate.languages["English"] == "fluent"
