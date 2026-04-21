"""FIX 22 (2026-04-21) — close_job.reason enum normalizer PT→EN.

Closes chat gap: user said "orçamento" as close_reason and LIA asked
"qual orçamento? qual período?" — treating the PT enum value as a generic
budget query. Root cause: close_job.reason accepts enum
["filled", "cancelled", "budget", "on_hold", "other"] (English) with no
translation layer. LLM often has the PT word from recruiter speech.

Canonical-fix (producer-side): `_normalize_close_reason(raw)` maps common
PT synonyms to canonical enum values before close_job validates.

Non-goals: LLM-driven slot coercion via prompt (that's FIX 25 / Initiative II,
separate scope). FIX 22 is the deterministic fallback.
"""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "raw,expected",
    [
        # canonical enum values passthrough
        ("filled", "filled"),
        ("cancelled", "cancelled"),
        ("budget", "budget"),
        ("on_hold", "on_hold"),
        ("other", "other"),
        # PT synonyms
        ("orçamento", "budget"),
        ("orcamento", "budget"),  # accent-less
        ("restrição orçamentária", "budget"),
        ("preenchida", "filled"),
        ("preenchido", "filled"),
        ("contratado", "filled"),
        ("contratada", "filled"),
        ("cancelada", "cancelled"),
        ("cancelado", "cancelled"),
        ("congelada", "on_hold"),
        ("congelado", "on_hold"),
        ("em espera", "on_hold"),
        ("em_espera", "on_hold"),
        ("outro", "other"),
        ("outra", "other"),
        # Case-insensitive
        ("ORÇAMENTO", "budget"),
        ("Cancelada", "cancelled"),
        # Extra whitespace
        ("  preenchida  ", "filled"),
    ],
)
def test_normalize_close_reason_known_values(raw: str, expected: str) -> None:
    """FIX 22: PT synonyms + canonical values must map correctly."""
    from app.domains.job_management.tools.job_tools import _normalize_close_reason

    assert _normalize_close_reason(raw) == expected, (
        f"FIX 22: {raw!r} should normalize to {expected!r}"
    )


@pytest.mark.parametrize("raw", ["xyz", "", "alguma coisa", "delete all"])
def test_normalize_close_reason_unknown_returns_none(raw: str) -> None:
    """FIX 22: unknown values must return None so caller rejects cleanly."""
    from app.domains.job_management.tools.job_tools import _normalize_close_reason

    result = _normalize_close_reason(raw)
    assert result is None, (
        f"FIX 22: {raw!r} is unknown; must return None so close_job rejects "
        f"with clear enum-error message, not silently default"
    )


def test_close_job_schema_description_mentions_pt_synonyms() -> None:
    """FIX 22: close_job schema description must hint that PT synonyms are accepted.

    Without the hint, LLM may still reject 'orçamento' thinking only English works.
    """
    from app.domains.job_management.tools.job_tools import CLOSE_JOB_SCHEMA

    reason_prop = CLOSE_JOB_SCHEMA["properties"]["reason"]
    desc = reason_prop.get("description", "").lower()
    assert "fix 22" in desc or "orçamento" in desc or "sinônimo" in desc or "pt" in desc, (
        "FIX 22: close_job.reason description should mention PT synonyms "
        "accepted (e.g. 'orçamento', 'preenchida') so LLM doesn't restrict to English"
    )


def test_module_has_fix22_marker() -> None:
    """FIX 22 audit marker."""
    from pathlib import Path

    import app.domains.job_management.tools.job_tools as jt

    source = Path(jt.__file__).read_text(encoding="utf-8")
    assert "FIX 22" in source, (
        "FIX 22: job_tools.py must contain `FIX 22` marker"
    )
    assert "_normalize_close_reason" in source, (
        "FIX 22: job_tools.py must define _normalize_close_reason helper"
    )
