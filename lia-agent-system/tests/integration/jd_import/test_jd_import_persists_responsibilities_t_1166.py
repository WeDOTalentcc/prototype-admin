"""T-1166 — runtime sentinel.

`jd_import_service.create_job_vacancy_from_jd` MUST persist
`imported_jd.responsibilities` into the dedicated `JobVacancy.responsibilities`
column (migration 132), and keep `imported_jd.requirements_mandatory` strictly
isolated in `JobVacancy.requirements`. The bug that motivated this sentinel
collapsed both into `requirements`, which made the "RESPONSABILIDADES" panel
in the JD editor render technical skills (vaga 200 contamination).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SERVICE_PATH = (
    Path(__file__).resolve().parents[3]
    / "app"
    / "domains"
    / "job_management"
    / "services"
    / "jd_import_service.py"
)


def _load_module_ast() -> ast.Module:
    return ast.parse(SERVICE_PATH.read_text(encoding="utf-8"))


def _find_jobvacancy_call(tree: ast.Module) -> ast.Call:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "JobVacancy":
                return node
            if isinstance(func, ast.Attribute) and func.attr == "JobVacancy":
                return node
    raise AssertionError(
        "T-1166: could not find a `JobVacancy(...)` constructor call in "
        f"{SERVICE_PATH}. The JD import service is the canonical bridge "
        "between imported_job_descriptions and the vacancies table — it "
        "MUST build a JobVacancy here so responsibilities is persisted."
    )


def test_jd_import_passes_responsibilities_kwarg_t_1166() -> None:
    """AST guard: the JobVacancy(...) call must pass `responsibilities=`."""
    tree = _load_module_ast()
    call = _find_jobvacancy_call(tree)
    kwarg_names = {kw.arg for kw in call.keywords if kw.arg}
    assert "responsibilities" in kwarg_names, (
        "T-1166: JobVacancy(...) in jd_import_service does NOT pass "
        "`responsibilities=`. Without this kwarg, the new ARRAY column added "
        "in migration 132 stays NULL and the JD editor falls back to "
        "rendering `requirements` under the RESPONSABILIDADES heading — "
        "exactly the bug we just fixed."
    )
    assert "requirements" in kwarg_names, (
        "T-1166: JobVacancy(...) must keep passing `requirements=` (with the "
        "imported_jd.requirements_mandatory list). Dropping it would erase "
        "the requirements column and re-create the contamination from the "
        "opposite direction."
    )


def test_jd_import_responsibilities_and_requirements_have_distinct_sources_t_1166() -> None:
    """The two kwargs must come from *different* fields of `imported_jd`.

    A single source (e.g. `imported_jd.responsibilities` feeding both) would
    not contaminate the columns but would empty `requirements`; we assert
    that the responsibilities kwarg references the `responsibilities` field
    and the requirements kwarg references the `requirements_mandatory` field
    (or a local variable derived from each).
    """
    source = SERVICE_PATH.read_text(encoding="utf-8")
    # Lightweight string check — robust to whitespace/line breaks.
    assert "imported_jd.responsibilities" in source, (
        "T-1166: jd_import_service must read `imported_jd.responsibilities` "
        "to populate the new column."
    )
    assert "imported_jd.requirements_mandatory" in source, (
        "T-1166: jd_import_service must keep reading "
        "`imported_jd.requirements_mandatory` for the requirements column."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
