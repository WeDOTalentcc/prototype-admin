"""
Sensor: normalize_search_query produces tokenizer-friendly output.

Post-mortem 2026-04-29 wizard UAT — Bug 5. Guards against regression
of the query-normalization behavior so queries like "candidatos?"
keep returning hits instead of zero results.

Skill canônica: harness-engineering [sensor computacional].
"""
import pytest

from app.shared.search_utils import normalize_search_query


class TestNormalizeSearchQuery:
    """Behavior contract for normalize_search_query."""

    def test_strips_trailing_question_mark(self):
        """The original Bug 5 case."""
        assert normalize_search_query("candidatos?") == "candidatos"

    def test_strips_trailing_punctuation_chain(self):
        assert normalize_search_query("Python!?.") == "Python"

    def test_strips_leading_punctuation(self):
        assert normalize_search_query("? candidatos") == "candidatos"

    def test_collapses_whitespace(self):
        assert (
            normalize_search_query("   Python   sênior   ")
            == "Python sênior"
        )

    def test_preserves_internal_hyphen(self):
        """Hyphenated technical terms must survive."""
        assert (
            normalize_search_query("back-end developer")
            == "back-end developer"
        )

    def test_preserves_accents(self):
        """Portuguese accents are meaningful tokens, never strip."""
        assert (
            normalize_search_query("desenvolvedor sênior")
            == "desenvolvedor sênior"
        )

    def test_preserves_case(self):
        """Backend handles case-folding; we do not lowercase."""
        assert (
            normalize_search_query("Python Sênior")
            == "Python Sênior"
        )

    def test_handles_none(self):
        assert normalize_search_query(None) == ""

    def test_handles_empty(self):
        assert normalize_search_query("") == ""

    def test_handles_whitespace_only(self):
        assert normalize_search_query("   ") == ""

    def test_handles_punctuation_only(self):
        """All punctuation -> empty string."""
        assert normalize_search_query("???") == ""

    def test_idempotent(self):
        """Normalizing twice yields the same result."""
        original = "Python sênior?"
        once = normalize_search_query(original)
        twice = normalize_search_query(once)
        assert once == twice
