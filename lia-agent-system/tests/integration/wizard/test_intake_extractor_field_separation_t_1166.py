"""T-1166 — AST sentinel: IntakeExtractor (the LLM-fed payload that feeds the
wizard state) MUST declare `responsibilities` and `technical_skills` as
distinct fields on its Pydantic payload. Collapsing them — e.g. by using
`requirements` as an alias for both — is the upstream root cause of the
"RESPONSABILIDADES shows Python/TS/PostgreSQL" bug (vaga 200).

This guard is intentionally cheap: it walks the AST of the payload class
and checks that both attributes exist as separate Field declarations.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

CANDIDATES = [
    Path(__file__).resolve().parents[3]
    / "app"
    / "domains"
    / "job_creation"
    / "intake"
    / "intake_extractor.py",
    Path(__file__).resolve().parents[3]
    / "app"
    / "domains"
    / "job_creation"
    / "services"
    / "intake_extractor.py",
]


def _find_module() -> Path:
    for candidate in CANDIDATES:
        if candidate.exists():
            return candidate
    pytest.skip(
        "T-1166: IntakeExtractor module not found at the canonical paths. "
        "If the wizard intake moved, update CANDIDATES in this sentinel."
    )


def _find_payload_class(tree: ast.Module) -> ast.ClassDef | None:
    """Return the first class whose body mentions both target fields."""
    best: ast.ClassDef | None = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        names = {
            stmt.target.id
            for stmt in node.body
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
        }
        if {"responsibilities", "technical_skills"} <= names:
            return node
        if "responsibilities" in names and best is None:
            best = node
    return best


def test_intake_payload_separates_responsibilities_from_technical_skills_t_1166() -> None:
    module_path = _find_module()
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    payload_cls = _find_payload_class(tree)
    if payload_cls is None:
        # The extractor might emit a TypedDict / dataclass elsewhere; fall
        # back to a source-level grep so we still catch the most common
        # regression (a single field handling both concepts).
        source = module_path.read_text(encoding="utf-8")
        assert "responsibilities" in source and "technical_skills" in source, (
            "T-1166: IntakeExtractor source does not mention BOTH "
            "`responsibilities` and `technical_skills`. The two concepts "
            "must be kept distinct end-to-end (LLM prompt → payload → "
            "wizard state → JobVacancy column)."
        )
        return

    field_names = {
        stmt.target.id
        for stmt in payload_cls.body
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
    }
    assert "responsibilities" in field_names, (
        f"T-1166: payload class `{payload_cls.name}` in {module_path} is "
        "missing the `responsibilities` field. The LLM extracts duties but "
        "they will be silently lost if this field does not exist."
    )
    assert "technical_skills" in field_names, (
        f"T-1166: payload class `{payload_cls.name}` in {module_path} is "
        "missing the `technical_skills` field. Without separation, the "
        "extractor will be tempted to dump skills into `responsibilities` "
        "and re-create the contamination bug."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
