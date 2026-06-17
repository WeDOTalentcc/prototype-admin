#!/usr/bin/env python3
"""Sensor canonical R1-only ZERO BLOCKING (T-07 final).

R1 = schemas Pydantic sem `extra='forbid'` em request body.
T-07 batches 1-4 fecharam todos 44 -> 0 violations em 2026-05-21.

Este sensor é COMPLEMENTAR ao check_pydantic_R1_ratchet.py:
- ratchet: garante que count NUNCA AUMENTA (mais flexível para migração gradual)
- R1_zero (ESTE): garante count = 0 (BLOCKING absoluto pós-T-07 final)

Use em CI/pre-commit para impedir nova violation R1 em qualquer schema novo.

Uso:
    python scripts/check_pydantic_R1_zero.py
    # Exit 0 se R1 = 0
    # Exit 1 se R1 > 0
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    full_sensor = repo_root / "scripts" / "check_pydantic_conventions.py"

    if not full_sensor.exists():
        print(f"[ERROR] Sensor canonical não encontrado: {full_sensor}", file=sys.stderr)
        return 1

    result = subprocess.run(
        ["python", str(full_sensor), "app/"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    # Procurar "R1 — N violação" no output
    r1_count = 0
    for line in output.splitlines():
        if line.startswith("R1 ") and "violação" in line:
            try:
                r1_count = int(line.split("—")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
            break

    # Se sensor canonical reportou "Pydantic conventions OK" sem detalhes
    if "Pydantic conventions OK" in output and r1_count == 0:
        print("[T-07 R1 ZERO BLOCKING] OK — 0 violations extra='forbid' em request schemas")
        return 0

    if r1_count == 0:
        print("[T-07 R1 ZERO BLOCKING] OK — R1 = 0 violations")
        return 0

    print(f"[T-07 R1 ZERO BLOCKING] FAIL — R1 = {r1_count} violations")
    print()
    print("CORRECAO canonical (ADR-029-v3):")
    print("  Adicionar em todo class:")
    print("    from pydantic import BaseModel, ConfigDict")
    print("    class FooSchema(BaseModel):")
    print("        model_config = ConfigDict(extra='forbid')")
    print("        ...fields...")
    print()
    print("  OU herdar de WeDoBaseModel canonical:")
    print("    from app.shared.types import WeDoBaseModel")
    print("    class FooSchema(WeDoBaseModel):  # extra='forbid' automatic")
    print("        ...fields...")
    print()
    print("Por quê: payload sem extra='forbid' aceita silenciosamente fields fantasma")
    print("(audit F1.O2). Use HTTP 422 explícito como contrato rígido.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
