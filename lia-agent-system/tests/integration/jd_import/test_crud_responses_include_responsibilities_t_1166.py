"""T-1166 — AST sentinel: every `JobVacancyResponse(...)` constructor call in
`app/api/v1/job_vacancies/crud.py` MUST pass `responsibilities=` so the new
column is round-tripped to the frontend on POST/PUT/finalize.

Backstop for the bug found by code review: the POST handler initially
persisted `responsibilities` but did not return it, which would cause the JD
editor to render an empty RESPONSABILIDADES panel right after a fresh create.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

CRUD_PATH = (
    Path(__file__).resolve().parents[3]
    / "app"
    / "api"
    / "v1"
    / "job_vacancies"
    / "crud.py"
)


def _find_response_calls(tree: ast.Module) -> list[ast.Call]:
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Name) and func.id == "JobVacancyResponse") or (
                isinstance(func, ast.Attribute) and func.attr == "JobVacancyResponse"
            ):
                calls.append(node)
    return calls


def test_every_jobvacancyresponse_call_passes_responsibilities_t_1166() -> None:
    tree = ast.parse(CRUD_PATH.read_text(encoding="utf-8"))
    calls = _find_response_calls(tree)
    assert calls, (
        "T-1166: no `JobVacancyResponse(...)` constructor found in crud.py. "
        "If this file moved, update CRUD_PATH in this sentinel."
    )

    missing: list[int] = []
    for call in calls:
        kwargs = {kw.arg for kw in call.keywords if kw.arg}
        if "responsibilities" not in kwargs:
            missing.append(call.lineno)

    assert not missing, (
        "T-1166: `JobVacancyResponse(...)` at line(s) "
        f"{missing} in {CRUD_PATH} does NOT pass `responsibilities=`. "
        "The frontend reads `job.responsibilities` (SCMSectionContent.tsx); "
        "an absent kwarg defaults to [] in the Pydantic schema and erases "
        "the panel right after POST/PUT until the next page refresh."
    )


def test_every_response_dict_in_crud_includes_responsibilities_t_1166() -> None:
    """GET handlers in crud.py return raw dicts (not the Pydantic model).

    Each such dict MUST also include a `"responsibilities"` key, otherwise the
    frontend gets `undefined` and the JD editor falls back to empty state
    silently (no crash, just a wrong UI).
    """
    source = CRUD_PATH.read_text(encoding="utf-8")
    # crud.py has 2 dict-returning paths (GET detail + GET list items). A
    # simple substring count keeps the guard resilient to minor formatting
    # without coupling to AST internals of dict literals.
    count = source.count('"responsibilities"')
    assert count >= 2, (
        f"T-1166: crud.py mentions `\"responsibilities\"` only {count} times. "
        "Expected at least 2 (GET detail response + GET list item builder). "
        "If you reduced the number of GET handlers, update this threshold."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
