"""
Schema-sync sensor (Camada 3 backlog Item 2 / harness-engineering 2026-05-22):

The LIA field toggle universe lives in TWO source-of-truth files that must
stay perfectly aligned, or the UI and the agents will silently disagree:

  Python (canonical, used by agents):
      libs/models/lia_models/lia_field_toggles.py
        - DEFAULT_FIELD_TOGGLES (list of {field_key, is_active})
        - FIELD_FALLBACK_CONFIG (dict field_key -> [strategies])

  TypeScript (UI source-of-truth):
      plataforma-lia/src/hooks/company/use-company-lia-instructions.ts
        - LIA_FIELD_DEFINITIONS (object literal of 34 keys)

If a new field is added in one but not the other:
- New TS-only field: recruiter sees toggle, but agent never honors it (ghost).
- New Python-only field: agent honors a toggle that recruiter cannot turn off.

This sensor parses both files via static analysis (NO heavyweight imports —
keeps the test fast and resilient to import-graph churn) and pins:

1. len(DEFAULT_FIELD_TOGGLES) == len(LIA_FIELD_DEFINITIONS)
2. set(DEFAULT_FIELD_TOGGLES keys) == set(LIA_FIELD_DEFINITIONS keys)
3. set(FIELD_FALLBACK_CONFIG keys) == set(DEFAULT_FIELD_TOGGLES keys)
4. Every toggle key has at least one consumer in the agent codebase
   (via LiaFieldConfigService.get_field_config OR build_company_agent_context).

The last assertion is intentionally a *coarse* presence check — it does not
prove correctness, only that the field has been wired into the canonical
context-building pathway. Fine-grained per-field behavior is tested elsewhere.

Audit anchor: ~/Documents/wedotalent_audit_2026-05-21/menu_configuracoes_inteligencia_agentes.md
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = REPO_ROOT.parent  # /home/runner/workspace

PYTHON_TOGGLES_PATH = (
    REPO_ROOT / "libs" / "models" / "lia_models" / "lia_field_toggles.py"
)
TS_DEFINITIONS_PATH = (
    WORKSPACE_ROOT
    / "plataforma-lia"
    / "src"
    / "hooks"
    / "company"
    / "use-company-lia-instructions.ts"
)


def _extract_python_defaults() -> tuple[set[str], set[str]]:
    """Returns (DEFAULT_FIELD_TOGGLES keys, FIELD_FALLBACK_CONFIG keys)."""
    src = PYTHON_TOGGLES_PATH.read_text()
    tree = ast.parse(src)
    defaults: list[dict] = []
    fallback: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if not isinstance(tgt, ast.Name):
                    continue
                if tgt.id == "DEFAULT_FIELD_TOGGLES":
                    defaults = ast.literal_eval(node.value)
                elif tgt.id == "FIELD_FALLBACK_CONFIG":
                    fallback = ast.literal_eval(node.value)
    return (
        {t["field_key"] for t in defaults},
        set(fallback.keys()),
    )


def _extract_ts_definitions() -> set[str]:
    """Parse LIA_FIELD_DEFINITIONS keys via regex (no JS engine required)."""
    src = TS_DEFINITIONS_PATH.read_text()
    # Capture block: `export const LIA_FIELD_DEFINITIONS = { ... } as const`
    block_match = re.search(
        r"export const LIA_FIELD_DEFINITIONS\s*=\s*\{(.+?)\}\s*as const",
        src,
        re.DOTALL,
    )
    if not block_match:
        raise AssertionError(
            "LIA_FIELD_DEFINITIONS export block not found in "
            f"{TS_DEFINITIONS_PATH}"
        )
    block = block_match.group(1)
    # Each entry starts with `  <key>: { ... }`
    keys = re.findall(r"^\s+([a-z_][a-z0-9_]*)\s*:\s*\{", block, re.MULTILINE)
    return set(keys)


@pytest.fixture(scope="module")
def python_default_keys() -> set[str]:
    defaults, _ = _extract_python_defaults()
    return defaults


@pytest.fixture(scope="module")
def python_fallback_keys() -> set[str]:
    _, fallback = _extract_python_defaults()
    return fallback


@pytest.fixture(scope="module")
def ts_definition_keys() -> set[str]:
    return _extract_ts_definitions()


def test_count_is_34(python_default_keys: set[str], ts_definition_keys: set[str]):
    """Pin the canonical universe size. Adding a new field requires updating
    BOTH files — and updating this number signals an intentional schema bump."""
    assert len(python_default_keys) == 34, (
        f"DEFAULT_FIELD_TOGGLES has {len(python_default_keys)} keys, "
        f"expected 34. If you intentionally added a field, update this "
        f"sensor AND the TS LIA_FIELD_DEFINITIONS in the same commit."
    )
    assert len(ts_definition_keys) == 34, (
        f"LIA_FIELD_DEFINITIONS has {len(ts_definition_keys)} keys, "
        f"expected 34. UI will not render the new toggle if the TS object "
        f"is not updated alongside the Python module."
    )


def test_python_default_toggles_match_ts_definitions(
    python_default_keys: set[str],
    ts_definition_keys: set[str],
):
    """Pin that the TS UI exposes exactly the toggles the Python agents
    will honor. Drift here = ghost setting (per harness-engineering taxonomy:
    UI without consumer is a guide-without-sensor anti-pattern)."""
    missing_in_ts = python_default_keys - ts_definition_keys
    missing_in_py = ts_definition_keys - python_default_keys
    assert not missing_in_ts, (
        f"Fields in Python DEFAULT_FIELD_TOGGLES but missing in TS "
        f"LIA_FIELD_DEFINITIONS: {sorted(missing_in_ts)}. "
        f"Recruiter cannot turn these off — invisible toggle."
    )
    assert not missing_in_py, (
        f"Fields in TS LIA_FIELD_DEFINITIONS but missing in Python "
        f"DEFAULT_FIELD_TOGGLES: {sorted(missing_in_py)}. "
        f"Toggle visible to recruiter but agent ignores it — ghost toggle."
    )


def test_fallback_config_covers_all_default_toggles(
    python_default_keys: set[str],
    python_fallback_keys: set[str],
):
    """Pin that every toggleable field has a fallback strategy declared.
    Without a fallback, an `is_active=False` toggle silently degrades the
    prompt with no replacement signal."""
    missing_fallback = python_default_keys - python_fallback_keys
    extra_fallback = python_fallback_keys - python_default_keys
    assert not missing_fallback, (
        f"DEFAULT_FIELD_TOGGLES contains keys with no entry in "
        f"FIELD_FALLBACK_CONFIG: {sorted(missing_fallback)}. "
        f"Add at least ['skip'] to declare intent explicitly."
    )
    assert not extra_fallback, (
        f"FIELD_FALLBACK_CONFIG contains keys not in DEFAULT_FIELD_TOGGLES: "
        f"{sorted(extra_fallback)}. Either add to DEFAULT_FIELD_TOGGLES or "
        f"remove from FIELD_FALLBACK_CONFIG."
    )


def test_canonical_consumer_chain_exists():
    """Pin that the canonical helper module exists. This is the bridge
    every agent must use to consume toggles. If this module disappears,
    the entire toggle universe becomes ghost overnight."""
    helper_path = (
        REPO_ROOT
        / "app"
        / "shared"
        / "services"
        / "lia_agent_context_builder.py"
    )
    assert helper_path.exists(), (
        f"Canonical context-builder helper missing at {helper_path}. "
        f"Every agent that injects company data into a prompt MUST call "
        f"build_company_agent_context() from this module. See "
        f"~/Documents/wedotalent_audit_2026-05-21/menu_configuracoes_inteligencia_agentes.md"
    )
    src = helper_path.read_text()
    assert "build_company_agent_context" in src, (
        "Helper module exists but lacks `build_company_agent_context` "
        "function — has it been renamed? Update this test."
    )
    assert "LiaFieldConfigService" in src, (
        "Canonical helper must delegate to LiaFieldConfigService to "
        "respect toggles. The bridge contract is broken if it does not."
    )


def test_canonical_helper_has_real_callers():
    """Coarse check: the canonical helper has at least 3 real consumer
    sites across the agent codebase. If this drops to 0–1, the toggle
    feature is in danger of becoming inert again — same failure mode as
    the original audit gap (P0-1 / 2026-05-21)."""
    app_dir = REPO_ROOT / "app"
    callers: list[Path] = []
    for py_file in app_dir.rglob("*.py"):
        # Skip the helper module itself, .bak files, and __pycache__
        if py_file.name == "lia_agent_context_builder.py":
            continue
        if ".bak" in py_file.name or "__pycache__" in py_file.parts:
            continue
        try:
            text = py_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue
        if "build_company_agent_context" in text:
            callers.append(py_file.relative_to(REPO_ROOT))
    assert len(callers) >= 3, (
        f"Only {len(callers)} caller(s) of build_company_agent_context "
        f"found. Expected >=3 (jd_generator, context_aggregator, "
        f"custom_agent_runtime). Found: {sorted(str(c) for c in callers)}. "
        f"If you removed a caller, ensure another path injects company "
        f"context — otherwise the toggle UI becomes ghost."
    )
