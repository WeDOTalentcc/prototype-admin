#!/usr/bin/env python3
"""Sensor canonical R2-only BLOCKING (T-06 ADR-029).

R2 = request body schemas com `company_id` field (multi-tenancy LGPD violation).
Audit V4 baseline: 4 violations remaining em 2026-05-21 (down de 274 → 139 → 4).
T-06 R2 fix completo fechou 4 últimas em 2026-05-21.

Este sensor opera SOMENTE em R2 (não R1/R3/R4 que têm sensores próprios:
  - check_pydantic_R1_ratchet.py (ratchet baseline)
  - check_pydantic_R4_only.py (T-03 BLOCKING)
).

Pattern canonical:
  R2 violation = class BaseModel com field `company_id` em path /lia-agent-system/app/
  EXCETO em SKIP_R2 set (event/result/internal schemas allow-listed).

Uso (pre-commit, CI):
    python scripts/check_pydantic_R2_only.py
    # Exit 0 se R2 = 0
    # Exit 1 se R2 > 0
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

    # Procurar "R2 — N violação" no output canonical
    r2_count = 0
    for line in output.splitlines():
        if line.startswith("R2 ") and "violação" in line:
            # Format: "R2 — 4 violação(ões)"
            try:
                r2_count = int(line.split("—")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
            break

    # Se sensor canonical reportou "Pydantic conventions OK" sem detalhes
    if "Pydantic conventions OK" in output and r2_count == 0:
        print("[T-06 R2 BLOCKING] OK — 0 violations company_id em request body")
        return 0

    if r2_count == 0:
        print("[T-06 R2 BLOCKING] OK — R2 = 0 violations")
        return 0

    print(f"[T-06 R2 BLOCKING] FAIL — R2 = {r2_count} violations")
    print()
    print("CORRECAO canonical (CLAUDE.md REGRA 1 + ADR-029):")
    print("  ❌ class Foo(BaseModel):")
    print("         company_id: str")
    print()
    print("  ✅ class Foo(BaseModel):")
    print("         # company_id removed — multi-tenancy via JWT")
    print("         ...other fields...")
    print()
    print("  No handler:")
    print("    async def handler(")
    print("        payload: Foo,")
    print("        company_id: str = Depends(require_company_id),  # from JWT")
    print("    ): ...")
    print()
    print("Por quê: payload company_id permite cross-tenant manipulation (LGPD violation).")
    print("Rodar `python scripts/check_pydantic_conventions.py app/` para detalhes.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
