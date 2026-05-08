#!/usr/bin/env python3
"""
Sensor canonical: arquivos com mesmo basename em
app/shared/observability/ e app/shared/services/ é dup proibida.

Uso: python scripts/check_no_observability_services_dup.py
Sai com código 1 se duplicação detectada.

# WARN-ONLY até R-005.2 zerar dups irmãs (drift_alert, model_drift,
# token_budget, token_tracking + 1). Quando todas consolidadas em
# observability/, promover para CI gate bloqueante.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OBS_DIR = ROOT / "app" / "shared" / "observability"
SVC_DIR = ROOT / "app" / "shared" / "services"

EXCLUDED = {"__init__.py", "__pycache__"}


def main() -> int:
    if not OBS_DIR.exists() or not SVC_DIR.exists():
        print(f"WARN: dirs ausentes {OBS_DIR} ou {SVC_DIR}", file=sys.stderr)
        return 0

    obs_files = {f.name for f in OBS_DIR.iterdir() if f.is_file() and f.name not in EXCLUDED}
    svc_files = {f.name for f in SVC_DIR.iterdir() if f.is_file() and f.name not in EXCLUDED}
    dups = sorted(obs_files & svc_files)

    if dups:
        print("❌ Dups proibidas em shared/observability/ ↔ shared/services/:", file=sys.stderr)
        for d in dups:
            print(f"  - {d}", file=sys.stderr)
        print(
            "\nConvenção (CLAUDE.md):\n"
            "  shared/observability/ = telemetria, alertas, métricas, drift, budget tracking\n"
            "  shared/services/      = regra de negócio compartilhada cross-domain\n"
            "Mesmo basename em ambos = duplicação. Consolidar em uma só localização.",
            file=sys.stderr,
        )
        return 1

    print(f"✓ shared/observability/ ({len(obs_files)}) e shared/services/ ({len(svc_files)}) sem dups")
    return 0


if __name__ == "__main__":
    sys.exit(main())
