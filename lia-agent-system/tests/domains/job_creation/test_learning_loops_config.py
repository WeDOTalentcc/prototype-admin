"""Tests for learning_loops_config helpers — Sprint B Phase 1.

Cobre as funcoes puras (_extract_loops) sem dependencia de DB.
Endpoints async sao testaveis via FastAPI TestClient — fora deste escopo unitario.
"""
from __future__ import annotations

import pytest


def test_extract_loops_returns_defaults_when_none():
    """When automation_rules is None, extracts full defaults."""
    from app.api.v1.learning_loops_config import _DEFAULT_LOOPS, _extract_loops

    result = _extract_loops(None)
    assert result == _DEFAULT_LOOPS
    assert result["jd_similar_suggestion"] is True
    assert result["bigfive_department_history"] is False  # opt-in default


def test_extract_loops_returns_defaults_when_block_missing():
    """When learning_loops block is missing, returns defaults."""
    from app.api.v1.learning_loops_config import _DEFAULT_LOOPS, _extract_loops

    result = _extract_loops({"auto_screening": True, "auto_scheduling": False})
    assert result == _DEFAULT_LOOPS


def test_extract_loops_overlays_partial():
    """Stored partial values override defaults; missing keys use default."""
    from app.api.v1.learning_loops_config import _extract_loops

    rules = {
        "auto_screening": True,
        "learning_loops": {
            "jd_similar_suggestion": False,
            "wsi_question_effectiveness": True,
        },
    }
    result = _extract_loops(rules)
    assert result["jd_similar_suggestion"] is False  # overridden
    assert result["wsi_question_effectiveness"] is True  # overridden
    assert result["bigfive_company_culture"] is True  # default
    assert result["bigfive_department_history"] is False  # default


def test_extract_loops_coerces_truthy():
    """Truthy/falsy values get coerced to bool (defensive)."""
    from app.api.v1.learning_loops_config import _extract_loops

    rules = {"learning_loops": {"jd_similar_suggestion": 0, "enabled": 1}}
    result = _extract_loops(rules)
    assert result["jd_similar_suggestion"] is False
    assert result["enabled"] is True


def test_default_loops_match_automation_rules_defaults():
    """Constants stay in sync between model and endpoint."""
    from app.api.v1.learning_loops_config import _DEFAULT_LOOPS
    from lia_models.company_hiring_policy import AUTOMATION_RULES_DEFAULTS

    assert _DEFAULT_LOOPS == AUTOMATION_RULES_DEFAULTS["learning_loops"]
