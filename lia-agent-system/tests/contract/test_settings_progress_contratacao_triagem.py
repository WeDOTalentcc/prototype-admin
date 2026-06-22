"""Contract sensor: settings_progress MUST include contratacao + screening-defaults.

Phase A — Configurações de Contratação (offer_rules) and Configurações de Triagem
(screening_config_defaults) were invisible to the progress system. These tests
pin the contract: both sections MUST appear in the response and factor into
`overall` and `minha-empresa` scores.

TDD RED → GREEN. Computational sensor (no LLM).
"""
from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path
from textwrap import dedent


# ---------------------------------------------------------------------------
# Helpers — read the source of settings_progress.py to validate contract
# ---------------------------------------------------------------------------

_SETTINGS_PROGRESS = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "api"
    / "v1"
    / "settings_progress.py"
)


def _read_source() -> str:
    return _SETTINGS_PROGRESS.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1. Sections dict MUST contain the canonical keys
# ---------------------------------------------------------------------------

def test_sections_dict_contains_contratacao_key() -> None:
    """settings_progress response['sections'] must include 'contratacao'."""
    src = _read_source()
    assert '"contratacao"' in src, (
        "settings_progress.py does not include 'contratacao' in the sections dict. "
        "→ Fix: add '\"contratacao\": contratacao_score' to the sections dict in "
        "the happy-path return and the error fallback."
    )


def test_sections_dict_contains_screening_defaults_key() -> None:
    """settings_progress response['sections'] must include 'screening-defaults'."""
    src = _read_source()
    assert '"screening-defaults"' in src, (
        "settings_progress.py does not include 'screening-defaults' in the sections "
        "dict. → Fix: add '\"screening-defaults\": screening_defaults_score' to the "
        "sections dict in the happy-path return and the error fallback."
    )


# ---------------------------------------------------------------------------
# 2. Scores MUST appear in details.scores
# ---------------------------------------------------------------------------

def test_details_scores_contains_contratacao() -> None:
    """details.scores must include contratacao score."""
    src = _read_source()
    assert '"contratacao"' in src and "contratacao_score" in src, (
        "settings_progress.py does not expose contratacao_score in details.scores. "
        "→ Fix: add '\"contratacao\": contratacao_score' to the details.scores dict."
    )


def test_details_scores_contains_screening_defaults() -> None:
    """details.scores must include screening_defaults score."""
    src = _read_source()
    assert '"screening_defaults"' in src and "screening_defaults_score" in src, (
        "settings_progress.py does not expose screening_defaults_score in "
        "details.scores. → Fix: add '\"screening_defaults\": "
        "screening_defaults_score' to the details.scores dict."
    )


# ---------------------------------------------------------------------------
# 3. Overall formula MUST reference both new scores
# ---------------------------------------------------------------------------

def test_overall_formula_includes_contratacao() -> None:
    """The overall calculation must factor in contratacao_score."""
    src = _read_source()
    # Look for contratacao_score multiplied by a weight in the overall calc
    overall_block = _extract_overall_block(src)
    assert "contratacao_score" in overall_block, (
        "The overall progress formula does not include contratacao_score. "
        "→ Fix: add contratacao_score with a weight to the overall calculation."
    )


def test_overall_formula_includes_screening_defaults() -> None:
    """The overall calculation must factor in screening_defaults_score."""
    src = _read_source()
    overall_block = _extract_overall_block(src)
    assert "screening_defaults_score" in overall_block, (
        "The overall progress formula does not include screening_defaults_score. "
        "→ Fix: add screening_defaults_score with a weight to the overall "
        "calculation."
    )


def _extract_overall_block(src: str) -> str:
    """Extract the lines around the 'overall = int(' calculation."""
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if "overall" in line and "int(" in line:
            # Grab surrounding context (up to 15 lines after)
            return "\n".join(lines[i : i + 15])
    return ""


# ---------------------------------------------------------------------------
# 4. minha-empresa score MUST include contratacao + screening_defaults
# ---------------------------------------------------------------------------

def test_minha_empresa_includes_contratacao() -> None:
    """minha_empresa_score must factor in contratacao_score."""
    src = _read_source()
    minha_block = _extract_minha_empresa_block(src)
    assert "contratacao_score" in minha_block, (
        "minha_empresa_score does not include contratacao_score. "
        "→ Fix: add contratacao_score to the minha_empresa_score average."
    )


def test_minha_empresa_includes_screening_defaults() -> None:
    """minha_empresa_score must factor in screening_defaults_score."""
    src = _read_source()
    minha_block = _extract_minha_empresa_block(src)
    assert "screening_defaults_score" in minha_block, (
        "minha_empresa_score does not include screening_defaults_score. "
        "→ Fix: add screening_defaults_score to the minha_empresa_score average."
    )


def _extract_minha_empresa_block(src: str) -> str:
    """Extract the minha_empresa_score calculation line(s)."""
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if "minha_empresa_score" in line and "=" in line and "int(" in line:
            return "\n".join(lines[i : i + 5])
    return ""


# ---------------------------------------------------------------------------
# 5. Scoring functions MUST exist for both data sources
# ---------------------------------------------------------------------------

def test_offer_rules_scoring_logic_exists() -> None:
    """A scoring function/block for offer_rules must exist."""
    src = _read_source()
    # Either a function or inline calculation referencing offer_rules fields
    assert "offer_rules" in src and "contratacao_score" in src, (
        "settings_progress.py has no scoring logic for offer_rules → "
        "contratacao_score. → Fix: add calculation that reads "
        "CompanyHiringPolicy.offer_rules and scores based on filled fields."
    )


def test_screening_config_defaults_scoring_logic_exists() -> None:
    """A scoring function/block for screening_config_defaults must exist."""
    src = _read_source()
    assert "screening_config_defaults" in src and "screening_defaults_score" in src, (
        "settings_progress.py has no scoring logic for screening_config_defaults → "
        "screening_defaults_score. → Fix: add calculation that reads "
        "CompanyHiringPolicy.screening_config_defaults and scores based on "
        "filled fields."
    )


# ---------------------------------------------------------------------------
# 6. Repository MUST have method to fetch hiring policy
# ---------------------------------------------------------------------------

def test_repository_has_hiring_policy_method() -> None:
    """SettingsProgressRepository must have a method to get hiring policy."""
    from app.domains.company.repositories.settings_progress_repository import (
        SettingsProgressRepository,
    )
    methods = [m for m in dir(SettingsProgressRepository) if "hiring_policy" in m or "policy" in m]
    assert methods, (
        "SettingsProgressRepository has no method to fetch the hiring policy. "
        "→ Fix: add get_hiring_policy(company_id) method to "
        "SettingsProgressRepository."
    )


# ---------------------------------------------------------------------------
# 7. Error fallback MUST also include the new keys
# ---------------------------------------------------------------------------

def test_error_fallback_contains_contratacao() -> None:
    """The error fallback sections dict must include 'contratacao'."""
    src = _read_source()
    # Find the except block's return
    in_except = False
    for line in src.splitlines():
        if "except Exception" in line:
            in_except = True
        if in_except and '"contratacao"' in line:
            return  # Found it
    raise AssertionError(
        "Error fallback in settings_progress.py does not include 'contratacao'. "
        "→ Fix: add '\"contratacao\": 0' to the error fallback sections dict."
    )


def test_error_fallback_contains_screening_defaults() -> None:
    """The error fallback sections dict must include 'screening-defaults'."""
    src = _read_source()
    in_except = False
    for line in src.splitlines():
        if "except Exception" in line:
            in_except = True
        if in_except and '"screening-defaults"' in line:
            return  # Found it
    raise AssertionError(
        "Error fallback in settings_progress.py does not include "
        "'screening-defaults'. → Fix: add '\"screening-defaults\": 0' to the "
        "error fallback sections dict."
    )
