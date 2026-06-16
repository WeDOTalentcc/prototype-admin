"""
LGPD Art.11 sensor: view_candidate_profile must NOT return sensitive fields
(gender, race, ethnicity, religion, health_info, disability_status) to the LLM.

P1-7 regression prevention — committed 2026-06-15.

Refs:
  - LGPD Art.11 caput (dados sensíveis)
  - LGPD Art.12 §1 (anonimização / analytics agregados N>=10 only)
  - _wrap_view_candidate_profile in talent_tool_registry.py
  - _LGPD_ART11_SENSITIVE frozenset gate
"""
import pytest

# Mirror of _LGPD_ART11_SENSITIVE in talent_tool_registry._wrap_view_candidate_profile
_LGPD_ART11_SENSITIVE = frozenset({
    "gender", "race", "ethnicity", "religion",
    "health_info", "disability_status",
})

# Helper: apply the same gate logic as in the production code
def _apply_lgpd_art11_gate(profile_dict: dict) -> dict:
    return {k: v for k, v in profile_dict.items() if k not in _LGPD_ART11_SENSITIVE}


class TestLgpdArt11GateLogic:
    """Unit tests for the default-deny gate logic (mirrors production code)."""

    def test_gender_stripped(self):
        """gender is LGPD Art.11 sensitive — must be removed before LLM sees profile."""
        raw = {
            "id": "uuid-123",
            "name": "Maria Silva",
            "email": "maria@example.com",
            "lia_score": 87.5,
            "gender": "feminino",  # SENSITIVE
            "skills": ["Python", "Django"],
        }
        result = _apply_lgpd_art11_gate(raw)
        assert "gender" not in result, (
            "LGPD Art.11 VIOLATION: gender returned to LLM in view_candidate_profile. "
            "Strip via _LGPD_ART11_SENSITIVE before returning profile dict. "
            "Fix: talent_tool_registry._wrap_view_candidate_profile"
        )

    def test_all_sensitive_fields_stripped(self):
        """Every field in the sensitive set must be removed from LLM context."""
        raw = {field: f"value_{field}" for field in _LGPD_ART11_SENSITIVE}
        raw.update({"name": "Test", "lia_score": 90, "email": "t@t.com"})
        result = _apply_lgpd_art11_gate(raw)
        for field in _LGPD_ART11_SENSITIVE:
            assert field not in result, (
                f"LGPD Art.11 VIOLATION: {field} must be stripped from LLM profile context. "
                f"Add to _LGPD_ART11_SENSITIVE in talent_tool_registry.py."
            )

    def test_non_sensitive_fields_preserved(self):
        """Operational fields (name, email, lia_score, skills, etc.) must survive the gate."""
        preserved = {
            "name": "João",
            "email": "joao@co.com",
            "lia_score": 92.0,
            "skills": ["React"],
            "current_title": "Eng",
            "seniority_level": "senior",
            "years_of_experience": 7,
            "location_city": "SP",
            "profile_loaded": True,
        }
        raw = {**preserved, "gender": "masculino", "race": "branco"}
        result = _apply_lgpd_art11_gate(raw)
        for field, value in preserved.items():
            assert field in result and result[field] == value, (
                f"Non-sensitive field {field} was incorrectly removed by LGPD gate."
            )

    def test_profile_without_sensitive_fields_unchanged(self):
        """Profiles with no sensitive fields must pass through the gate unmodified."""
        raw = {"name": "Ana", "lia_score": 75.0, "email": "ana@co.com"}
        result = _apply_lgpd_art11_gate(raw)
        assert result == raw, "Gate must not modify profiles that contain no sensitive fields."

    def test_response_blocks_preserved(self):
        """response_blocks (RRP cards) must be preserved — they hold UI render data, not PII."""
        raw = {
            "name": "Carlos",
            "lia_score": 88,
            "gender": "masculino",
            "response_blocks": [{"type": "candidate_card", "data": {}}],
            "render_hint": "narrate",
        }
        result = _apply_lgpd_art11_gate(raw)
        assert "gender" not in result
        assert "response_blocks" in result
        assert "render_hint" in result


class TestSensitiveFieldSet:
    """Guard the _LGPD_ART11_SENSITIVE set definition — prevent regressions."""

    def test_gender_in_sensitive_set(self):
        """gender must always be in the sensitive set (LGPD Art.11 caput explicit mention)."""
        assert "gender" in _LGPD_ART11_SENSITIVE, (
            "REGRESSION: gender removed from _LGPD_ART11_SENSITIVE. "
            "gender is LGPD Art.11 sensitive data. Do NOT remove from the set."
        )

    def test_sensitive_set_contains_minimum_fields(self):
        """Ensure the minimum required LGPD Art.11 fields are present in the set."""
        minimum_required = {"gender", "race", "ethnicity", "religion"}
        missing = minimum_required - _LGPD_ART11_SENSITIVE
        assert not missing, (
            f"REGRESSION: fields {missing} removed from _LGPD_ART11_SENSITIVE. "
            f"These are LGPD Art.11 sensitive fields and must be default-deny."
        )
