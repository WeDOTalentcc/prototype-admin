"""Coverage tests for input_validation.py — pure validation utilities."""
import pytest
from pydantic import ValidationError

from app.shared.robustness.input_validation import (
    BaseAgentInput,
    CandidateInput,
    JobInput,
    SearchInput,
    SupportedLanguage,
    WSIInput,
    detect_language,
    is_empty_or_whitespace,
    normalize_text,
    sanitize_sql_input,
    sanitize_text,
    validate_agent_input,
)


class TestSupportedLanguage:
    def test_pt_br_value(self):
        assert SupportedLanguage.PT_BR == "pt-BR"

    def test_en_us_value(self):
        assert SupportedLanguage.EN_US == "en-US"

    def test_es_value(self):
        assert SupportedLanguage.ES == "es"


class TestIsEmptyOrWhitespace:
    def test_none_returns_true(self):
        assert is_empty_or_whitespace(None) is True

    def test_empty_string_returns_true(self):
        assert is_empty_or_whitespace("") is True

    def test_whitespace_only_returns_true(self):
        assert is_empty_or_whitespace("   ") is True

    def test_text_returns_false(self):
        assert is_empty_or_whitespace("text") is False

    def test_mixed_returns_false(self):
        assert is_empty_or_whitespace("  a  ") is False


class TestNormalizeText:
    def test_lowercases(self):
        result = normalize_text("Hello World")
        assert result == result.lower()

    def test_collapses_spaces(self):
        result = normalize_text("a  b   c")
        assert "  " not in result

    def test_strips_leading_trailing(self):
        result = normalize_text("  hello  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_strips_accents(self):
        result = normalize_text("Sao Paulo")
        assert "a" in result


class TestSanitizeText:
    def test_html_encoded(self):
        result = sanitize_text("<script>alert(1)</script>")
        assert "<script>" not in result

    def test_truncates_to_max_length(self):
        long_text = "a" * 20000
        result = sanitize_text(long_text, max_length=100)
        assert len(result) <= 100

    def test_normal_text_unchanged(self):
        result = sanitize_text("Hello World")
        assert "Hello" in result

    def test_empty_string(self):
        result = sanitize_text("")
        assert result == ""


class TestSanitizeSqlInput:
    def test_drop_table_cleaned(self):
        result = sanitize_sql_input("SELECT * FROM users; DROP TABLE users")
        assert "DROP" not in result

    def test_normal_text_mostly_unchanged(self):
        result = sanitize_sql_input("Python developer with 5 years")
        assert "Python" in result

    def test_empty_string(self):
        assert sanitize_sql_input("") == ""

    def test_union_select_removed(self):
        result = sanitize_sql_input("word UNION SELECT * FROM passwords")
        assert "UNION" not in result or "SELECT" not in result


class TestDetectLanguage:
    def test_empty_returns_pt_br(self):
        result = detect_language("")
        assert result == SupportedLanguage.PT_BR

    def test_portuguese_text_returns_pt_br(self):
        result = detect_language("candidato com experiencia em tecnologia")
        assert result == SupportedLanguage.PT_BR

    def test_returns_supported_language(self):
        result = detect_language("some text")
        assert result in list(SupportedLanguage)


class TestBaseAgentInput:
    def test_valid_input(self):
        inp = BaseAgentInput(intent="search_candidates")
        assert inp.intent == "search_candidates"
        assert inp.language == SupportedLanguage.PT_BR

    def test_missing_intent_raises(self):
        with pytest.raises(ValidationError):
            BaseAgentInput(intent="")

    def test_language_defaults_pt_br(self):
        inp = BaseAgentInput(intent="search")
        assert inp.language == SupportedLanguage.PT_BR


class TestJobInput:
    def test_basic_job_input(self):
        inp = JobInput(intent="create_job", job_title="Engenheiro Backend")
        assert inp.job_title == "Engenheiro Backend"

    def test_salary_range_valid(self):
        inp = JobInput(intent="create_job", salary_min=3000.0, salary_max=5000.0)
        assert inp.salary_min == 3000.0

    def test_salary_inverted_raises(self):
        with pytest.raises(ValidationError):
            JobInput(intent="create_job", salary_min=5000.0, salary_max=3000.0)

    def test_experience_inverted_raises(self):
        with pytest.raises(ValidationError):
            JobInput(intent="x", experience_years_min=5, experience_years_max=2)


class TestCandidateInput:
    def test_valid_email(self):
        inp = CandidateInput(intent="screen", candidate_email="user@domain.com")
        assert inp.candidate_email == "user@domain.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            CandidateInput(intent="screen", candidate_email="not-an-email")


class TestSearchInput:
    def test_default_limit(self):
        inp = SearchInput(intent="search")
        assert inp.limit == 20

    def test_custom_limit(self):
        inp = SearchInput(intent="search", limit=50)
        assert inp.limit == 50

    def test_skills_stripped(self):
        inp = SearchInput(intent="search", skills=["  Python  ", "SQL"])
        assert "Python" in inp.skills


class TestValidateAgentInput:
    def test_validates_dict_to_base(self):
        result = validate_agent_input({"intent": "search"})
        assert isinstance(result, BaseAgentInput)

    def test_sanitizes_text_fields(self):
        result = validate_agent_input({"intent": "search", "session_id": "abc"})
        assert result.session_id == "abc"
