#!/usr/bin/env python3
"""
Sensor schema-sync RRP ResponseBlock TS<->Python (2026-06-05).

Verifica que o catalogo de blocos do Rich Response Protocol fica sincronizado
entre o Pydantic (lia-agent-system/app/shared/rrp_blocks.py) e o mirror TS
(plataforma-lia/src/types/rrp-blocks.ts).

Divergencia = killer silencioso: backend emite um `kind` que o renderer nao
conhece (cai no fallback AD6, nunca renderiza o bloco rico) ou o FE declara um
kind que o backend nunca emite. Cobre tambem os enums compartilhados
(BlockRole, BlockLayout, BlockState).

Modo warn-only por default; --blocking para exit 1. Baseline esperado: 0.
Padrao espelhado de scripts/check_trigger_modes_ts_sync.py.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path("/home/runner/workspace")
PY_FILE = ROOT / "lia-agent-system/app/shared/rrp_blocks.py"
TS_FILE = ROOT / "plataforma-lia/src/types/rrp-blocks.ts"
PY_DISPLAY = "lia-agent-system/app/shared/rrp_blocks.py"
TS_DISPLAY = "plataforma-lia/src/types/rrp-blocks.ts"


def _strings(blob: str) -> set[str]:
    return set(re.findall(r'"([^"]+)"', blob))


def py_kinds(content: str) -> set[str]:
    return set(re.findall(r'kind:\s*Literal\[\s*"([^"]+)"\s*\]', content))


def ts_kinds(content: str) -> set[str]:
    return set(re.findall(r'kind:\s*"([^"]+)"', content))


def py_enum(content: str, name: str) -> set[str]:
    m = re.search(name + r"\s*=\s*Literal\[([^\]]+)\]", content)
    return _strings(m.group(1)) if m else set()


def ts_enum(content: str, name: str) -> set[str]:
    m = re.search(r"export type " + name + r"\s*=\s*([^;]+);", content)
    return _strings(m.group(1)) if m else set()


def main() -> int:
    blocking = "--blocking" in sys.argv
    if not PY_FILE.exists():
        print("[ERROR] Python file not found: " + PY_DISPLAY)
        return 0
    if not TS_FILE.exists():
        print("[ERROR] TS file not found: " + TS_DISPLAY)
        return 0

    py = PY_FILE.read_text(encoding="utf-8")
    ts = TS_FILE.read_text(encoding="utf-8")
    violations: list[dict[str, str]] = []

    def compare(label, py_set, ts_set, py_hint, ts_hint):
        for v in sorted(py_set - ts_set):
            violations.append({
                "issue": label + "_PY_ONLY",
                "message": label + " '" + v + "' em Python mas NAO em TS",
                "fix": "Adicionar '" + v + "' em " + ts_hint + " (" + TS_DISPLAY + ")",
            })
        for v in sorted(ts_set - py_set):
            violations.append({
                "issue": label + "_TS_ONLY",
                "message": label + " '" + v + "' em TS mas NAO em Python",
                "fix": "Adicionar '" + v + "' em " + py_hint + " (" + PY_DISPLAY + ")",
            })

    pk, tk = py_kinds(py), ts_kinds(ts)
    print("Schema sync sensor -- RRP ResponseBlock TS<->Python")
    print("  PY kinds (" + str(len(pk)) + "): " + PY_DISPLAY)
    print("  TS kinds (" + str(len(tk)) + "): " + TS_DISPLAY)
    compare("KIND", pk, tk, "classe *Block com kind: Literal[...]", "union ResponseBlock + interface *Block")
    for enum in ("BlockRole", "BlockLayout", "BlockState"):
        compare(enum, py_enum(py, enum), ts_enum(ts, enum), enum + " Literal", "type " + enum)

    if violations:
        mode_label = "BLOCKING" if blocking else "warn-only"
        marker = "[ERROR]" if blocking else "[WARN]"
        print("\n" + marker + " " + str(len(violations)) + " violation(s) (" + mode_label + "):")
        for v in violations:
            print("  [" + v["issue"] + "] " + v["message"])
            print("           -> Fix: " + v["fix"])
        if blocking:
            print("\nSaindo com exit 1 (--blocking ativo).")
            return 1
        print("\nSaindo com exit 0 (warn-only). Use --blocking para erro.")
    else:
        print("\n[OK] 0 violations -- RRP blocks TS <-> Python em sincronia (" + str(len(pk)) + " kinds).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
