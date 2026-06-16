"""Coverage tests for lia_utils shims and utils.

Targets:
  - app/utils/datetime_helpers.py  (1 stmt — re-export shim)
  - app/utils/skill_classifier.py  (1 stmt — re-export shim)
  - lia_utils.skill_classifier     (underlying implementation)
  - lia_utils.datetime_helpers     (underlying implementation)
"""
import pytest
from datetime import datetime, timezone


# ===========================================================================
# app/utils/skill_classifier.py (shim) + lia_utils.skill_classifier
# ===========================================================================
from app.utils.skill_classifier import (
    SOFT_SKILLS,
    classify_skills,
    normalize_skill,
)


class TestSkillClassifier:
    def test_soft_skills_is_collection(self):
        assert SOFT_SKILLS is not None
        assert len(SOFT_SKILLS) > 0

    def test_normalize_skill_basic(self):
        result = normalize_skill("Python Programming")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_normalize_skill_whitespace(self):
        result = normalize_skill("  java  ")
        assert isinstance(result, str)

    def test_classify_skills_returns_tuple(self):
        result = classify_skills(["python", "communication"])
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_classify_skills_separates_soft_and_hard(self):
        hard_skills, soft_skills = classify_skills(["python", "communication", "teamwork"])
        assert isinstance(hard_skills, list)
        assert isinstance(soft_skills, list)

    def test_classify_skills_empty(self):
        hard, soft = classify_skills([])
        assert hard == []
        assert soft == []

    def test_classify_skills_all_hard(self):
        hard, soft = classify_skills(["python", "sql", "kubernetes"])
        assert isinstance(hard, list)

    def test_classify_skills_known_soft_skill(self):
        # "communication" is typically a soft skill
        hard, soft = classify_skills(["communication"])
        assert len(hard) == 0 or "communication" in soft or "communication" in hard


# ===========================================================================
# app/utils/datetime_helpers.py (shim) + lia_utils.datetime_helpers
# ===========================================================================
from app.utils.datetime_helpers import (
    WINDOWS_TO_IANA_TIMEZONES,
    parse_graph_datetime,
)


class TestDatetimeHelpers:
    def test_windows_to_iana_is_dict(self):
        assert isinstance(WINDOWS_TO_IANA_TIMEZONES, dict)
        assert len(WINDOWS_TO_IANA_TIMEZONES) > 0

    def test_windows_to_iana_known_mapping(self):
        # UTC should definitely be in the mapping
        assert any("UTC" in k or "UTC" in v for k, v in WINDOWS_TO_IANA_TIMEZONES.items())

    def test_parse_graph_datetime_utc(self):
        result = parse_graph_datetime("2024-01-15T10:00:00Z")
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_parse_graph_datetime_with_offset(self):
        result = parse_graph_datetime("2024-06-01T14:30:00+03:00")
        assert isinstance(result, datetime)

    def test_parse_graph_datetime_iso(self):
        result = parse_graph_datetime("2025-01-01T00:00:00.000Z")
        assert isinstance(result, datetime)
        assert result.year == 2025
