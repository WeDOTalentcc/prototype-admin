"""Phase C.4 — pin the consolidated VALID_JOB_STATUSES whitelist.

Background. Pre-Phase-C, two whitelists existed for job vacancy status:
  - app/api/v1/job_vacancies/_shared.py:66  (canonical, included Cancelada)
  - app/api/v1/job_vacancies/crud.py:902    (drift, MISSING Cancelada)

The bulk endpoint (lifecycle.py:942) used the canonical constant. The
single-vacancy PATCH (crud.py:893) used the drifted one, so a recruiter
trying to cancel one vacancy got a 400 error while bulk-cancelling worked.

Phase C.1 imported VALID_JOB_STATUSES into crud.py and replaced the local
list. This test asserts:

  1. There is only ONE source of truth (the constant from _shared).
  2. crud.py imports it (no local list reappears).
  3. Cancelada is in the whitelist.

Why a test (vs a lint rule). The drift type — "two lists that should be one"
— is hard to lint generically. A regression test that asserts the canonical
constant contains the expected statuses + grep-style assertion that the
drifted local list is gone is simple and aligns with our harness discipline
(every defect class needs a sensor; this is the sensor for THIS class).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.api.v1.job_vacancies._shared import VALID_JOB_STATUSES


def test_canonical_whitelist_includes_cancelada():
    """The shared constant must include 'Cancelada' (Phase C.1)."""
    assert "Cancelada" in VALID_JOB_STATUSES, (
        f"VALID_JOB_STATUSES missing 'Cancelada'. Current: {VALID_JOB_STATUSES}"
    )


def test_canonical_whitelist_has_expected_statuses():
    """Document the expected set so accidental changes fail loudly."""
    expected = {"Rascunho", "Ativa", "Pausada", "Concluída", "Cancelada", "Arquivada"}
    actual = set(VALID_JOB_STATUSES)
    assert actual == expected, (
        f"VALID_JOB_STATUSES drift detected.\n"
        f"  Expected: {sorted(expected)}\n"
        f"  Actual:   {sorted(actual)}\n"
        f"If the drift is intentional, update this test in the same PR."
    )


def test_crud_module_uses_canonical_constant():
    """Phase C.1 — crud.py must import VALID_JOB_STATUSES, not redefine it.

    A drifted local list `valid_statuses = [...]` would re-introduce the bug
    we just fixed. Sensor against that regression.
    """
    crud_path = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "job_vacancies" / "crud.py"
    assert crud_path.exists(), f"crud.py not found at {crud_path}"
    src = crud_path.read_text()

    # Must import the canonical constant.
    assert "VALID_JOB_STATUSES" in src, "crud.py must reference VALID_JOB_STATUSES"

    # Must NOT redefine a local list of statuses (the drift pattern).
    drift_pattern = re.compile(
        r"valid_statuses\s*=\s*\[[^\]]*\"Rascunho\"",
        re.IGNORECASE,
    )
    assert not drift_pattern.search(src), (
        "Drifted local `valid_statuses = [...]` re-introduced in crud.py. "
        "Use VALID_JOB_STATUSES from app.api.v1.job_vacancies._shared."
    )


def test_lifecycle_module_uses_canonical_constant():
    """lifecycle.py:942 has used the constant since pre-Phase-C; pin it."""
    lifecycle_path = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "job_vacancies" / "lifecycle.py"
    assert lifecycle_path.exists()
    src = lifecycle_path.read_text()
    assert "VALID_JOB_STATUSES" in src, "lifecycle.py must reference VALID_JOB_STATUSES"


def test_only_one_status_whitelist_in_codebase():
    """Whole-repo sweep: no lurking duplicate of the status list."""
    # Allow occurrences inside the canonical _shared.py and lifecycle/crud's
    # legitimate references. Reject anywhere else.
    expected_files_with_definition = {"_shared.py"}

    # Walk app/api/v1/job_vacancies/ only — that's the surface we care about.
    base = Path(__file__).resolve().parents[2] / "app" / "api" / "v1" / "job_vacancies"
    drift_pattern = re.compile(
        r'\[\s*"Rascunho"\s*,\s*"Ativa"\s*,\s*"Pausada"',
        re.IGNORECASE,
    )

    offenders: list[str] = []
    for py in base.rglob("*.py"):
        # The shared module is allowed to define the list.
        if py.name in expected_files_with_definition:
            continue
        if drift_pattern.search(py.read_text()):
            offenders.append(str(py.relative_to(base.parent.parent.parent.parent)))

    assert not offenders, (
        "Status whitelist drift detected in:\n  " + "\n  ".join(offenders) +
        "\nUse VALID_JOB_STATUSES from app.api.v1.job_vacancies._shared."
    )
