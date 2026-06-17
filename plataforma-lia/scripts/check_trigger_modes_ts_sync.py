#!/usr/bin/env python3
"""
Onda 4 Agent E (2026-05-29) — Sensor schema-sync VALID_TRIGGER_MODES_BY_TARGET.

Verifica que a tabela canonical em TypeScript
(plataforma-lia/src/lib/agents/trigger-modes.ts) e a matriz Python
(lia-agent-system/app/shared/trigger_mode_validation.py) ficam sincronizadas.

Qualquer divergencia (target_type so em um lado, trigger_mode missing em um
target_type) e violacao -- significa que UI pode oferecer combo que backend
rejeita (HTTP 422) ou vice-versa.

Modo warn-only por default. Promover a --blocking quando baseline = 0
(esperado: 0 ja na primeira run pos-criacao).

Padrao espelhado de scripts/check_lia_field_definitions_sync.py.

Uso:
  python3 scripts/check_trigger_modes_ts_sync.py
  python3 scripts/check_trigger_modes_ts_sync.py --blocking
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/home/runner/workspace")
TS_FILE = ROOT / "plataforma-lia/src/lib/agents/trigger-modes.ts"
PY_FILE = ROOT / "lia-agent-system/app/shared/trigger_mode_validation.py"

TS_DISPLAY = "plataforma-lia/src/lib/agents/trigger-modes.ts"
PY_DISPLAY = "lia-agent-system/app/shared/trigger_mode_validation.py"


def extract_ts_matrix(path: Path) -> dict[str, set[str]]:
    """Parse VALID_TRIGGER_MODES_BY_TARGET literal em .ts.

    Esperado:
      export const VALID_TRIGGER_MODES_BY_TARGET = {
        talent_pool: ["on_create", "on_schedule", "manual"],
        ...
      } as const ...
    """
    content = path.read_text(encoding="utf-8")
    m = re.search(
        r"export const VALID_TRIGGER_MODES_BY_TARGET\s*=\s*\{(.+?)\}\s*as const",
        content,
        re.DOTALL,
    )
    if not m:
        print("  [WARN] VALID_TRIGGER_MODES_BY_TARGET block not found in " + TS_DISPLAY)
        return {}
    block = m.group(1)

    matrix: dict[str, set[str]] = {}
    # Pattern: target_type: ["mode1", "mode2", ...]
    entry_re = re.compile(
        r"(\w+)\s*:\s*\[([^\]]+)\]",
        re.DOTALL,
    )
    for entry_match in entry_re.finditer(block):
        target = entry_match.group(1)
        modes_block = entry_match.group(2)
        modes = set(re.findall(r'"([^"]+)"', modes_block))
        matrix[target] = modes
    return matrix


def extract_py_matrix(path: Path) -> dict[str, set[str]]:
    """Parse VALID_TRIGGER_MODES_BY_TARGET dict em .py.

    Esperado:
      VALID_TRIGGER_MODES_BY_TARGET: dict[str, frozenset[str]] = {
          "talent_pool": frozenset({"on_create", "on_schedule", "manual"}),
          ...
      }
    """
    content = path.read_text(encoding="utf-8")
    m = re.search(
        r"VALID_TRIGGER_MODES_BY_TARGET[^=]*=\s*\{(.+?)\n\}",
        content,
        re.DOTALL,
    )
    if not m:
        print("  [WARN] VALID_TRIGGER_MODES_BY_TARGET block not found in " + PY_DISPLAY)
        return {}
    block = m.group(1)

    matrix: dict[str, set[str]] = {}
    # Pattern: "target_type": frozenset({"mode1", "mode2", ...})
    entry_re = re.compile(
        r'"(\w+)"\s*:\s*frozenset\s*\(\s*\{([^}]+)\}\s*\)',
        re.DOTALL,
    )
    for entry_match in entry_re.finditer(block):
        target = entry_match.group(1)
        modes_block = entry_match.group(2)
        modes = set(re.findall(r'"([^"]+)"', modes_block))
        matrix[target] = modes
    return matrix


def main() -> int:
    blocking = "--blocking" in sys.argv

    if not TS_FILE.exists():
        print("[ERROR] TS file not found: " + TS_DISPLAY)
        return 0
    if not PY_FILE.exists():
        print("[ERROR] Python file not found: " + PY_DISPLAY)
        return 0

    ts_matrix = extract_ts_matrix(TS_FILE)
    py_matrix = extract_py_matrix(PY_FILE)

    print("Schema sync sensor -- VALID_TRIGGER_MODES_BY_TARGET TS<->Python")
    print("  TS targets (" + str(len(ts_matrix)) + "): " + TS_DISPLAY)
    print("  PY targets (" + str(len(py_matrix)) + "): " + PY_DISPLAY)

    violations: list[dict[str, str]] = []

    ts_targets = set(ts_matrix.keys())
    py_targets = set(py_matrix.keys())

    for target in sorted(ts_targets - py_targets):
        violations.append({
            "issue": "TARGET_TS_ONLY",
            "message": "target_type '" + target + "' em TS mas NAO em Python",
            "fix": "Adicionar '" + target + "' em VALID_TRIGGER_MODES_BY_TARGET em " + PY_DISPLAY,
        })

    for target in sorted(py_targets - ts_targets):
        violations.append({
            "issue": "TARGET_PY_ONLY",
            "message": "target_type '" + target + "' em Python mas NAO em TS",
            "fix": "Adicionar '" + target + ": [...]' em VALID_TRIGGER_MODES_BY_TARGET em " + TS_DISPLAY,
        })

    for target in sorted(ts_targets & py_targets):
        ts_modes = ts_matrix[target]
        py_modes = py_matrix[target]
        for mode in sorted(ts_modes - py_modes):
            violations.append({
                "issue": "MODE_TS_ONLY",
                "message": "trigger_mode '" + mode + "' em TS[" + target + "] mas NAO em Python[" + target + "]",
                "fix": "Adicionar '" + mode + "' em VALID_TRIGGER_MODES_BY_TARGET['" + target + "'] em " + PY_DISPLAY,
            })
        for mode in sorted(py_modes - ts_modes):
            violations.append({
                "issue": "MODE_PY_ONLY",
                "message": "trigger_mode '" + mode + "' em Python[" + target + "] mas NAO em TS[" + target + "]",
                "fix": "Adicionar '" + mode + "' em VALID_TRIGGER_MODES_BY_TARGET." + target + " em " + TS_DISPLAY,
            })

    if violations:
        mode_label = "BLOCKING" if blocking else "warn-only"
        marker = "[ERROR]" if blocking else "[WARN]"
        print("\n" + marker + " " + str(len(violations)) + " violation(s) encontrada(s) (" + mode_label + "):")
        for v in violations:
            print("  [" + v["issue"] + "] " + v["message"])
            print("           -> Fix: " + v["fix"])
        print("")
        if blocking:
            print("Saindo com exit 1 (--blocking ativo).")
            return 1
        print("Saindo com exit 0 (modo warn-only). Use --blocking para tratar como erro.")
    else:
        print("\n[OK] 0 violations -- TS <-> Python trigger_mode matrix em sincronia.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
