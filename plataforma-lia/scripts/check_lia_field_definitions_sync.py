#!/usr/bin/env python3
"""
Sensor: check_lia_field_definitions_sync.py
Verifica que LIA_FIELD_DEFINITIONS (TypeScript) e DEFAULT_FIELD_TOGGLES (Python) estao sincronizados.

Qualquer campo definido em um lado mas ausente no outro e uma violacao -- significa que o toggle
exposto na UI nao tem correspondente no backend (ghost setting) ou vice-versa.

Modo warn-only por default. Use --blocking para exit 1 em violations.

Uso:
  python3 scripts/check_lia_field_definitions_sync.py
  python3 scripts/check_lia_field_definitions_sync.py --blocking

Arquivos monitorados:
  TS:  plataforma-lia/src/hooks/company/use-company-lia-instructions.ts
  PY:  lia-agent-system/libs/models/lia_models/lia_field_toggles.py
"""
import re
import sys
from pathlib import Path

TS_FILE = Path("/home/runner/workspace/plataforma-lia/src/hooks/company/use-company-lia-instructions.ts")
PY_FILE = Path("/home/runner/workspace/lia-agent-system/libs/models/lia_models/lia_field_toggles.py")

TS_DISPLAY = "plataforma-lia/src/hooks/company/use-company-lia-instructions.ts"
PY_DISPLAY = "lia-agent-system/libs/models/lia_models/lia_field_toggles.py"


def extract_ts_field_keys(path):
    content = path.read_text(encoding="utf-8")
    m = re.search(r"export const LIA_FIELD_DEFINITIONS\s*=\s*\{(.+?)\}\s*as const", content, re.DOTALL)
    if not m:
        print("  [WARN] LIA_FIELD_DEFINITIONS block not found in " + TS_DISPLAY)
        return set()
    block = m.group(1)
    keys = set(re.findall(r"^\s{2}([a-zA-Z_][a-zA-Z0-9_]*)\s*:", block, re.MULTILINE))
    return keys


def extract_py_field_keys(path):
    content = path.read_text(encoding="utf-8")
    m = re.search(r"DEFAULT_FIELD_TOGGLES\s*=\s*\[(.+?)\]", content, re.DOTALL)
    if not m:
        print("  [WARN] DEFAULT_FIELD_TOGGLES block not found in " + PY_DISPLAY)
        return set()
    block = m.group(1)
    keys = set(re.findall(r'"field_key"\s*:\s*"([^"]+)"', block))
    return keys


def main():
    blocking = "--blocking" in sys.argv

    if not TS_FILE.exists():
        print("[ERROR] TS file not found: " + TS_DISPLAY)
        return 0

    if not PY_FILE.exists():
        print("[ERROR] Python file not found: " + PY_DISPLAY)
        return 0

    ts_keys = extract_ts_field_keys(TS_FILE)
    py_keys = extract_py_field_keys(PY_FILE)

    ts_only = ts_keys - py_keys
    py_only = py_keys - ts_keys

    print("Schema sync sensor -- LIA_FIELD_DEFINITIONS TS<->Python")
    print("  TS  fields (" + str(len(ts_keys)) + "): " + TS_DISPLAY)
    print("  PY  fields (" + str(len(py_keys)) + "): " + PY_DISPLAY)

    violations = []

    for key in sorted(ts_only):
        violations.append({
            "key": key,
            "issue": "TS_ONLY",
            "message": "Campo '" + key + "' esta em LIA_FIELD_DEFINITIONS (TS) mas NAO em DEFAULT_FIELD_TOGGLES (Python)",
            "fix": 'Adicionar {"field_key": "' + key + '", "is_active": True} em DEFAULT_FIELD_TOGGLES em ' + PY_DISPLAY,
        })

    for key in sorted(py_only):
        violations.append({
            "key": key,
            "issue": "PY_ONLY",
            "message": "Campo '" + key + "' esta em DEFAULT_FIELD_TOGGLES (Python) mas NAO em LIA_FIELD_DEFINITIONS (TS)",
            "fix": "Adicionar entry '" + key + ": { label: ..., category: ..., location: ... }' em LIA_FIELD_DEFINITIONS em " + TS_DISPLAY,
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
        else:
            print("Saindo com exit 0 (modo warn-only). Use --blocking para tratar como erro.")
    else:
        print("\n[OK] 0 violations -- TS <-> Python field definitions estao em sincronia.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
