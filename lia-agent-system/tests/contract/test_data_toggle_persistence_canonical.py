"""Contract test: every UI ``data-toggle`` literal MUST be backed by
a persistence-layer field OR be explicitly whitelisted as UI-only.

Wave 4 audit follow-up 2026-05-22. Companion to the AST sensor
``scripts/check_data_toggle_matches_persisted_key.py`` — wraps it as a
contract test so pytest CI fails when a new ghost toggle is introduced
in the frontend, even if pre-commit was bypassed.

Why a separate test on top of the AST sensor
─────────────────────────────────────────────
The script-based sensor is already run by pre-commit and (optionally) by
the dedicated CI step. The contract test gives an *additional*
fail-loud signal inside the regular pytest suite — useful when devs
focus on backend changes and assume pre-commit covers everything. It
also makes the canonical rule discoverable from the test suite (TDD
canonical: "what does the system promise?").

How it works
────────────
1. Imports the sensor module directly (it lives in ``scripts/``).
2. Calls its public helpers (``collect_persistence_names``,
   ``collect_data_toggles``, ``load_whitelist``).
3. For each toggle not in the persistence name set and not in the
   whitelist, the test fails with a clear repro hint.

This duplicates the runtime check intentionally — every harness sensor
gets at least two consumers: pre-commit + pytest.

Canonical ref: CLAUDE.md "lia_field_toggles canonical pattern".
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]  # lia-agent-system/
SCRIPTS_DIR = REPO_ROOT / "scripts"
SENSOR_PATH = SCRIPTS_DIR / "check_data_toggle_matches_persisted_key.py"


def _load_sensor_module():
    """Import the sensor module by file path (it has no package)."""
    spec = importlib.util.spec_from_file_location(
        "data_toggle_sensor", SENSOR_PATH
    )
    assert spec is not None and spec.loader is not None, (
        f"Sensor module not loadable at {SENSOR_PATH}. Did the file move?"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["data_toggle_sensor"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def sensor():
    return _load_sensor_module()


def test_sensor_script_exists(sensor):
    """Sensor file is present (basic harness wiring check)."""
    assert SENSOR_PATH.exists(), (
        "Sensor missing — Wave 4 canonical guard is gone. "
        "Restore scripts/check_data_toggle_matches_persisted_key.py."
    )
    assert hasattr(sensor, "collect_data_toggles")
    assert hasattr(sensor, "collect_persistence_names")
    assert hasattr(sensor, "load_whitelist")


def test_whitelist_file_loads(sensor):
    """Whitelist file format is parsable (even when empty)."""
    entries = sensor.load_whitelist()
    # Every entry MUST be a (path, toggle) tuple of two non-empty strings.
    for entry in entries:
        assert isinstance(entry, tuple) and len(entry) == 2, (
            f"Malformed whitelist entry: {entry!r}"
        )
        path, toggle = entry
        assert path and toggle, (
            f"Whitelist entry missing path or toggle: {entry!r}"
        )


def test_every_data_toggle_is_persisted_or_whitelisted(sensor):
    """Canonical: zero ghost toggles in the frontend tree.

    For each ``data-toggle="X"`` literal in plataforma-lia/src/ either:
      (a) ``X`` matches a backend SQLAlchemy column / Pydantic field /
          Zod schema field, OR
      (b) the (path, X) pair appears in scripts/whitelists/
          data_toggle_exempt.txt (UI-only documented exemption).
    """
    names = sensor.collect_persistence_names()
    toggles = sensor.collect_data_toggles()
    whitelist = sensor.load_whitelist()
    workspace_root = sensor.WORKSPACE_ROOT

    if not toggles:
        pytest.skip(
            "No data-toggle literals found — plataforma-lia tree absent "
            "(running from clone without frontend sibling)."
        )

    violations: list[str] = []
    for path, lineno, toggle in toggles:
        if toggle in names:
            continue
        try:
            rel_str = str(path.relative_to(workspace_root))
        except ValueError:
            rel_str = str(path)
        if (rel_str, toggle) in whitelist:
            continue
        violations.append(f"{rel_str}:{lineno}: data-toggle=\"{toggle}\"")

    assert not violations, (
        "Ghost data-toggle(s) detected — UI exposes a switch the backend "
        "doesn't persist. Each is a customer-trust break.\n\n"
        + "\n".join(violations)
        + "\n\nFix options:\n"
        "  1. Rename data-toggle attr to match the actual persisted key.\n"
        "  2. Add the field to backend (SQLAlchemy/Pydantic/Zod).\n"
        "  3. If genuinely UI-only (derived state, ephemeral, etc.), add\n"
        "     <path>:<toggle>:<reason> to\n"
        "     lia-agent-system/scripts/whitelists/data_toggle_exempt.txt"
    )


def test_whitelist_entries_still_match_real_files(sensor):
    """Defense: whitelist must not rot (stale paths).

    If a whitelisted file no longer exists OR no longer contains a
    ``data-toggle="<name>"`` literal, the whitelist entry is dead weight
    and should be removed (or the toggle was renamed and re-emerged
    unwhitelisted somewhere else).
    """
    workspace_root = sensor.WORKSPACE_ROOT
    whitelist = sensor.load_whitelist()
    toggles = sensor.collect_data_toggles()

    if not toggles:
        pytest.skip("No frontend tree to validate against.")

    # Build (rel_path, toggle) set of toggles actually present in code.
    present: set[tuple[str, str]] = set()
    for path, _lineno, toggle in toggles:
        try:
            rel = str(path.relative_to(workspace_root))
        except ValueError:
            rel = str(path)
        present.add((rel, toggle))

    stale = [entry for entry in whitelist if entry not in present]
    assert not stale, (
        "Stale whitelist entries (the file no longer contains the "
        f"toggle, or the path changed):\n  "
        + "\n  ".join(f"{p}:{t}" for p, t in stale)
        + "\n\nRemove them from "
        "scripts/whitelists/data_toggle_exempt.txt."
    )
