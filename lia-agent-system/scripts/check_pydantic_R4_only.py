#!/usr/bin/env python3
"""Sensor canonical R4-only BLOCKING (T-03 ADR-029-v2).

R4 = endpoints com `x_company_id` via Header (multi-tenancy LGPD violation).
Audit SMOKE-#2 LGPD: 28 sites cross-tenant data manipulation pre-fix.
T-03 batches 1-3 fecharam todos sites em 2026-05-20.

Este sensor opera SOMENTE em R4 (nao R1/R2/R3 que ainda tem violations pendentes
em T-06/T-07). Promove R4 isolado para BLOCKING enquanto outros ratchet.

Uso (pre-commit, CI):
    python scripts/check_pydantic_R4_only.py
    # Exit 0 se R4 = 0
    # Exit 1 se R4 > 0
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    full_sensor = repo_root / "scripts" / "check_pydantic_conventions.py"

    if not full_sensor.exists():
        print(f"[ERROR] Sensor canonical nao encontrado: {full_sensor}", file=sys.stderr)
        return 1

    result = subprocess.run(
        ["python", str(full_sensor), "app/"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    # Procurar "R4 — N violacao" no output
    r4_count = 0
    for line in output.splitlines():
        if line.startswith("R4 ") and "violação" in line:
            # Format: "R4 — 31 violação(ões)"
            try:
                r4_count = int(line.split("—")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
            break

    # Se sensor canonical reportou "Pydantic conventions OK" sem detalhes
    if "Pydantic conventions OK" in output and r4_count == 0:
        print("[T-03 R4 BLOCKING] OK — 0 violations cross-tenant via Header")
        return 0

    if r4_count == 0:
        print("[T-03 R4 BLOCKING] OK — R4 = 0 violations")
        return 0

    print(f"[T-03 R4 BLOCKING] FAIL — R4 = {r4_count} violations")
    print()
    print("CORRECAO canonical (CLAUDE.md REGRA 6 + ADR-029):")
    print("  ❌ x_company_id: str = Header(..., alias='X-Company-ID')")
    print("  ✅ company_id: str = Depends(require_company_id)  # from JWT")
    print()
    print("Ou para defense-in-depth (header validado vs JWT):")
    print("  ✅ company_id: str = Depends(get_verified_company_id)")
    print()
    print("Rodar `python scripts/check_pydantic_conventions.py app/` para detalhes.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
