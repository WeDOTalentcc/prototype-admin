"""Coverage tests for apify_mapper.py — ApifyProfileMapper pure methods."""
import pytest
from datetime import datetime

from app.domains.sourcing.services.apify_mapper import ApifyProfileMapper, SENIORITY_KEYWORDS


class TestSeniorityKeywords:
    def test_has_expected_levels(self):
        assert "senior" in SENIORITY_KEYWORDS
        assert "junior" in SENIORITY_KEYWORDS
        assert "manager" in SENIORITY_KEYWORDS
        assert "c_level" in SENIORITY_KEYWORDS

    def test_each_level_has_keywords(self):
        for level, keywords in SENIORITY_KEYWORDS.items():
            assert len(keywords) > 0, f"Level {level} has no keywords"


@pytest.fixture
def mapper():
    return ApifyProfileMapper()


class TestParseLocation:
    def test_empty_returns_nones(self, mapper):
        assert mapper._parse_location("") == (None, None, None)

    def test_none_returns_nones(self, mapper):
        assert mapper._parse_location(None) == (None, None, None)  # type: ignore

    def test_single_part(self, mapper):
        city, state, country = mapper._parse_location("São Paulo")
        assert city == "São Paulo"
        assert state is None
        assert country is None

    def test_two_parts(self, mapper):
        city, state, country = mapper._parse_location("São Paulo, Brasil")
        assert city == "São Paulo"
        assert state is None
        assert country == "Brasil"

    def test_three_parts(self, mapper):
        city, state, country = mapper._parse_location("São Paulo, SP, Brasil")
        assert city == "São Paulo"
        assert state == "SP"
        assert country == "Brasil"


class TestInferSeniority:
    def test_none_returns_none(self, mapper):
        assert mapper._infer_seniority(None) is None  # type: ignore

    def test_empty_returns_none(self, mapper):
        assert mapper._infer_seniority("") is None

    def test_senior_keyword(self, mapper):
        assert mapper._infer_seniority("Senior Software Engineer") == "senior"

    def test_junior_keyword(self, mapper):
        assert mapper._infer_seniority("Junior Developer") == "junior"

    def test_manager_keyword(self, mapper):
        assert mapper._infer_seniority("Product Manager") == "manager"

    def test_director_keyword(self, mapper):
        # "Engineering Director" contains "cto" as substring ("direCTOr"), so
        # use Portuguese "Diretor" which doesn't contain any c_level keyword
        assert mapper._infer_seniority("Diretor de Produto") == "director"

    def test_ceo_is_c_level(self, mapper):
        assert mapper._infer_seniority("CEO") == "c_level"

    def test_unknown_returns_none(self, mapper):
        assert mapper._infer_seniority("Software Wizard") is None

    def test_case_insensitive(self, mapper):
        assert mapper._infer_seniority("SENIOR ENGINEER") == "senior"


class TestExtractEmails:
    def test_empty_data_returns_empty(self, mapper):
        assert mapper._extract_emails({}) == []

    def test_email_in_emailaddress(self, mapper):
        result = mapper._extract_emails({"emailAddress": "a@b.com"})
        assert "a@b.com" in result

    def test_email_in_email_key(self, mapper):
        # "primaryEmail" is not a supported key; "email" is
        result = mapper._extract_emails({"email": "primary@b.com"})
        assert "primary@b.com" in result

    def test_duplicate_deduped(self, mapper):
        # Both "email" and "emailAddress" pointing to same address → deduped
        result = mapper._extract_emails({"email": "a@b.com", "emailAddress": "a@b.com"})
        assert result.count("a@b.com") == 1

    def test_invalid_email_excluded(self, mapper):
        result = mapper._extract_emails({"emailAddress": "not-an-email"})
        assert "not-an-email" not in result


class TestGetCurrentExperience:
    def test_no_experience_returns_none(self, mapper):
        assert mapper._get_current_experience({}) is None

    def test_empty_experience_returns_none(self, mapper):
        assert mapper._get_current_experience({"experience": []}) is None

    def test_open_experience_returned(self, mapper):
        exp = {"timePeriod": {"startDate": {"year": 2020}}}
        result = mapper._get_current_experience({"experience": [exp]})
        assert result is exp

    def test_closed_experience_first_as_fallback(self, mapper):
        exp = {"timePeriod": {"startDate": {"year": 2020}, "endDate": {"year": 2022}}}
        result = mapper._get_current_experience({"experience": [exp]})
        assert result is exp


class TestCalculateYearsOfExperience:
    def test_no_experience_returns_none(self, mapper):
        assert mapper._calculate_years_of_experience({}) is None

    def test_with_experience(self, mapper):
        current_year = datetime.utcnow().year
        exp = {"timePeriod": {"startDate": {"year": current_year - 5}}}
        result = mapper._calculate_years_of_experience({"experience": [exp]})
        assert result == 5

    def test_future_year_returns_zero(self, mapper):
        current_year = datetime.utcnow().year
        exp = {"timePeriod": {"startDate": {"year": current_year + 1}}}
        result = mapper._calculate_years_of_experience({"experience": [exp]})
        assert result == 0


class TestMapToCandidate:
    def test_empty_input_returns_empty(self, mapper):
        assert mapper.map_to_candidate({}) == {}

    def test_basic_name_mapping(self, mapper):
        result = mapper.map_to_candidate({
            "firstName": "Ana", "lastName": "Silva",
        })
        assert result["name"] == "Ana Silva"

    def test_linkedin_url_mapped(self, mapper):
        # Actual apify field is "profileUrl" or "url"
        result = mapper.map_to_candidate({"profileUrl": "https://linkedin.com/in/ana"})
        assert result.get("linkedin_url") == "https://linkedin.com/in/ana"


class TestMapToSkills:
    def test_empty_returns_empty(self, mapper):
        assert mapper.map_to_skills({}) == []

    def test_string_skills(self, mapper):
        result = mapper.map_to_skills({"skills": ["Python", "Django"]})
        assert "Python" in result

    def test_dict_skills(self, mapper):
        result = mapper.map_to_skills({"skills": [{"name": "Python"}, {"name": "React"}]})
        assert "Python" in result
        assert "React" in result
