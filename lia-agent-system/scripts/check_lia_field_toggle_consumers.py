#!/usr/bin/env python3
"""
check_lia_field_toggle_consumers.py -- Sensor P2-5

Validates that every field_key in DEFAULT_FIELD_TOGGLES has a real consumer:
  - DIRECT: field_key is a column in CompanyProfile or CompanyCultureProfile
  - EXPLICIT: field_key is referenced as a string literal in lia_field_config_service.py
              (explicit fetch/mapping beyond the generic DEFAULT_FIELD_TOGGLES loop)
  - ORPHAN: field_key not found in any consumer -> ghost toggle

Usage:
  python3 scripts/check_lia_field_toggle_consumers.py           # warn-only (exit 0)
  python3 scripts/check_lia_field_toggle_consumers.py --blocking # exit 1 if orphans found
  python3 scripts/check_lia_field_toggle_consumers.py --json     # machine-readable output

Sensor type: COMPUTATIONAL (AST-based, no DB required)
Sprint: P2-5 Settings Coherence Audit 2026-05-27
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent  # lia-agent-system/

TOGGLES_FILE = ROOT / "libs/models/lia_models/lia_field_toggles.py"
MODEL_FILES = [
    ROOT / "libs/models/lia_models/company.py",
    ROOT / "libs/models/lia_models/company_culture.py",
    ROOT / "libs/models/lia_models/company_hiring_policy.py",
]
SERVICE_FILE = ROOT / "app/domains/cv_screening/services/lia_field_config_service.py"


def _collect_field_keys_from_toggles(path: Path) -> list[str]:
    """Parse DEFAULT_FIELD_TOGGLES from lia_field_toggles.py using AST."""
    tree = ast.parse(path.read_text())
    field_keys: list[str] = []

    for node in ast.walk(tree):
        # Looking for: DEFAULT_FIELD_TOGGLES = [{"field_key": "...", ...}, ...]
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "DEFAULT_FIELD_TOGGLES"
        ):
            if isinstance(node.value, ast.List):
                for elt in node.value.elts:
                    if isinstance(elt, ast.Dict):
                        for k, v in zip(elt.keys, elt.values):
                            if (
                                isinstance(k, ast.Constant)
                                and k.value == "field_key"
                                and isinstance(v, ast.Constant)
                            ):
                                field_keys.append(v.value)
    return field_keys


def _collect_model_columns(model_paths: list[Path]) -> set[str]:
    """
    Extract attribute names from SQLAlchemy model classes.
    Covers:
    - mapped_column assignments
    - Column assignments
    - Annotated attribute assignments
    """
    columns: set[str] = set()

    for path in model_paths:
        if not path.exists():
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    # Case 1: field = mapped_column(...) or field = Column(...)
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                                columns.add(target.id)
                    # Case 2: field: Type = mapped_column(...) or field: Type
                    elif isinstance(item, ast.AnnAssign):
                        if isinstance(item.target, ast.Name) and not item.target.id.startswith("_"):
                            columns.add(item.target.id)

    return columns


def _collect_explicit_service_references(service_path: Path, all_toggles: list[str]) -> set[str]:
    """
    Find field_keys that appear as explicit string literals in the service,
    outside of generic DEFAULT_FIELD_TOGGLES loop iteration.

    Returns field_keys that are referenced by name (not just iterated generically).
    """
    toggle_set = set(all_toggles)
    found: set[str] = set()

    tree = ast.parse(service_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in toggle_set:
                found.add(node.value)

    return found


def classify(
    field_keys: list[str],
    model_columns: set[str],
    explicit_refs: set[str],
) -> dict[str, str]:
    """Classify each field_key as DIRECT | EXPLICIT | ORPHAN."""
    result: dict[str, str] = {}
    for fk in field_keys:
        if fk in model_columns:
            result[fk] = "DIRECT"
        elif fk in explicit_refs:
            result[fk] = "EXPLICIT"
        else:
            result[fk] = "ORPHAN"
    return result


def main() -> int:
    blocking = "--blocking" in sys.argv
    as_json = "--json" in sys.argv

    if not TOGGLES_FILE.exists():
        print(f"ERROR: Toggles file not found: {TOGGLES_FILE}")
        return 1

    field_keys = _collect_field_keys_from_toggles(TOGGLES_FILE)
    model_columns = _collect_model_columns(MODEL_FILES)
    explicit_refs = _collect_explicit_service_references(SERVICE_FILE, field_keys)
    classification = classify(field_keys, model_columns, explicit_refs)

    orphans = [fk for fk, status in classification.items() if status == "ORPHAN"]
    explicit_only = [fk for fk, status in classification.items() if status == "EXPLICIT"]
    direct = [fk for fk, status in classification.items() if status == "DIRECT"]

    if as_json:
        print(json.dumps({
            "total": len(field_keys),
            "direct": direct,
            "explicit_service": explicit_only,
            "orphans": orphans,
            "violations": len(orphans),
        }, indent=2))
        return 1 if (blocking and orphans) else 0

    # ── Human-readable output ──────────────────────────────────────────────────
    print(f"check_lia_field_toggle_consumers.py -- {TOGGLES_FILE.name}")
    print(f"  Total field_keys: {len(field_keys)}")
    print(f"  DIRECT  (model column)      : {len(direct)}")
    print(f"  EXPLICIT (service string)   : {len(explicit_only)}")
    print(f"  ORPHAN  (ghost toggle)      : {len(orphans)}")
    print()

    if explicit_only:
        print("EXPLICIT -- verify these have a real data fetch in lia_field_config_service.py:")
        for fk in sorted(explicit_only):
            print(f"   * {fk}")
            print(f"     -> Grep: grep -n '{fk}' {SERVICE_FILE.relative_to(ROOT)}")
        print()

    if orphans:
        print("ORPHAN -- these appear in DEFAULT_FIELD_TOGGLES but have NO:")
        print("   * model column in CompanyProfile / CompanyCultureProfile / CompanyHiringPolicy")
        print("   * explicit string reference in lia_field_config_service.py")
        print()
        for fk in sorted(orphans):
            print(f"   [ORPHAN] {fk}")
            print(f"   -> Fix: Add column to profile model OR add explicit fetch in lia_field_config_service.py")
            print(f"   -> OR: Add to ORPHAN_ALLOWLIST with justification if data comes from another source")
            print()
        if blocking:
            print(f"BLOCKING: {len(orphans)} orphaned toggle(s) found. Fix before committing.")
            return 1
        else:
            print(f"WARN: {len(orphans)} orphaned toggle(s). Run with --blocking to enforce.")
    else:
        print("All field_keys have confirmed consumers.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
