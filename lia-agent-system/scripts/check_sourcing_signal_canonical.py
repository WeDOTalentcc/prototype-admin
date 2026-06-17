#!/usr/bin/env python3
"""Sprint 7B-3a Part 1.5 v2 sensor (2026-05-26): detect legacy SourcingAgentSignal writes.

Canonical pattern (Decisão Paulo 2026-05-26 #2): signals NOVOS DEVEM ser escritos com
`custom_agent_id=<uuid>` (NOT NULL fail-closed). Pattern legacy `agent_id=` standalone
sem `custom_agent_id=` indica orchestrator não migrado para canonical.

Baseline 2026-05-26: 0 violations (orchestrator atual usa agent_id, mas mudança vem em
Part 2 full — sensor warn-only inicial, promote BLOCKING após Part 2 land).

Detects:
- `SourcingAgentSignal(agent_id=..., signal_type=..., ...)` sem keyword custom_agent_id
- `SourcingAgentSignal(**dict)` é ignorado (não inspecionável estaticamente)

Honra `# SOURCING-SIGNAL-LEGACY-EXEMPT: <reason>` marker em linha imediatamente acima
da chamada (para signals históricos / scripts de seed).

Plan: AGENT_STUDIO_GAP_ANALYSIS_2026-05-26.md decisão #2
"""
from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCAN_DIRS = ["app", "libs"]
TARGET_CLASS = "SourcingAgentSignal"
EXEMPT_MARKER = "SOURCING-SIGNAL-LEGACY-EXEMPT"


def get_call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def scan_file(path: pathlib.Path) -> list[str]:
    try:
        src = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []

    if TARGET_CLASS not in src:
        return []

    src_lines = src.splitlines()

    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []

    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if get_call_name(node) != TARGET_CLASS:
            continue

        # Exempt marker check (line immediately above)
        lineno = node.lineno
        if lineno >= 2:
            prev = src_lines[lineno - 2]
            if EXEMPT_MARKER in prev:
                continue

        kw_names = {kw.arg for kw in node.keywords if kw.arg}
        # If only **kwargs passed (no named kw at all), skip — not statically inspectable
        if not kw_names:
            continue

        if "custom_agent_id" not in kw_names:
            violations.append(
                f"{path.relative_to(ROOT)}:{lineno} → "
                f"SourcingAgentSignal(...) sem custom_agent_id (canonical fail-closed). "
                f"Fix: adicionar custom_agent_id=<uuid> ou marker '# {EXEMPT_MARKER}: <reason>'."
            )
    return violations


def main() -> int:
    all_violations: list[str] = []
    for sd in SCAN_DIRS:
        base = ROOT / sd
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            all_violations.extend(scan_file(path))

    if not all_violations:
        print("✓ check_sourcing_signal_canonical: 0 violations (baseline canonical)")
        return 0

    print(f"⚠ check_sourcing_signal_canonical: {len(all_violations)} violation(s)")
    for v in all_violations:
        print(f"  {v}")

    blocking = "--blocking" in sys.argv
    if blocking:
        return 1
    print("(warn-only — passe --blocking pra falhar em CI)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
