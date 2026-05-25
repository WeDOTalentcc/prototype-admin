#!/usr/bin/env python3
"""Harness sensor #8 (Sprint 7A): bane imports legacy de SourcingAgent model em codigo novo.

Apos migration 203, qualquer novo uso DEVE ler de CustomAgent (filter category='sourcing').

Honra `# SOURCING-LEGACY-EXEMPT: <reason>` marker para arquivos transitorios
(ex: app/api/v1/sourcing_agents.py legado ate Sprint 7B deletar, admin_external.py
ate migrar pra count via CustomAgent.category).

Plan: ~/Documents/wedotalent_audit_2026-05-25/AGENT_STUDIO_SPRINT7_PLAN.md §2.7
"""
from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN_DIRS = ["app", "libs"]
BANNED_NAMES = {"SourcingAgent", "SourcingAgentSignal"}
BANNED_MODULES = {
    "lia_models.sourcing_agent",
    "libs.models.lia_models.sourcing_agent",
    "app.models.sourcing_agent",  # shim path 2026-05-25 7B-3a
}
EXEMPT_MARKER = "SOURCING-LEGACY-EXEMPT"


def scan_file(path: pathlib.Path) -> list[str]:
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    if EXEMPT_MARKER in src:
        return []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module in BANNED_MODULES:
                for alias in node.names:
                    if alias.name in BANNED_NAMES:
                        violations.append(
                            f"{path}:{node.lineno} import {alias.name} from {node.module}\n"
                            f"  -> Fix: usar `from lia_models.custom_agent import CustomAgent` "
                            f"+ filter category='sourcing'"
                        )
    return violations


def main(blocking: bool = False) -> int:
    total: list[str] = []
    for sd in SCAN_DIRS:
        base = ROOT / sd
        if not base.exists():
            continue
        for py in base.rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            if "alembic/versions" in str(py):
                continue
            total.extend(scan_file(py))
    if total:
        print("\n".join(total))
        print(f"\nTotal violations: {len(total)}")
        return 1 if blocking else 0
    print("Sensor #8 baseline: 0 violations")
    return 0


if __name__ == "__main__":
    sys.exit(main(blocking="--blocking" in sys.argv))
