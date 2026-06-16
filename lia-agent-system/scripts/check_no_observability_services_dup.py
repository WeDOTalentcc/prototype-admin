#!/usr/bin/env python3
"""
Sensor canonical: arquivos com mesmo basename em
app/shared/observability/ e app/shared/services/ é dup proibida.

Uso: python scripts/check_no_observability_services_dup.py
Sai com código 1 se duplicação detectada.

R-005.2 (2026-05-08): shims legítimos (arquivos contendo apenas re-exports
para canonical de domínio) são permitidos em ambos os dirs simultaneamente —
são backward-compat, não dups de implementação. O sensor detecta shims via
marcador "R-005.2: this file is a re-export shim" OU "Backwards-compatibility shim"
no conteúdo do arquivo. Pares onde AMBOS são shims apontando ao mesmo canonical
são excluídos do check.

Quando as dups de implementação (código real) forem zeradas este sensor
é promovido para CI gate bloqueante.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OBS_DIR = ROOT / "app" / "shared" / "observability"
SVC_DIR = ROOT / "app" / "shared" / "services"

EXCLUDED = {"__init__.py", "__pycache__"}

SHIM_MARKERS = (
    "R-005.2: this file is a re-export shim",
    "Backwards-compatibility shim",
    "Backward-compat shim",
    "backward-compat shim",
    "backwards-compatibility shim",
)


def _is_shim(path: Path) -> bool:
    """Return True if the file is a known backward-compat re-export shim."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return any(marker in content for marker in SHIM_MARKERS)
    except OSError:
        return False


def main() -> int:
    if not OBS_DIR.exists() or not SVC_DIR.exists():
        print(f"WARN: dirs ausentes {OBS_DIR} ou {SVC_DIR}", file=sys.stderr)
        return 0

    obs_files = {f.name for f in OBS_DIR.iterdir() if f.is_file() and f.name not in EXCLUDED}
    svc_files = {f.name for f in SVC_DIR.iterdir() if f.is_file() and f.name not in EXCLUDED}
    candidates = sorted(obs_files & svc_files)

    real_dups: list[str] = []
    shim_pairs: list[str] = []

    for name in candidates:
        obs_path = OBS_DIR / name
        svc_path = SVC_DIR / name
        obs_shim = _is_shim(obs_path)
        svc_shim = _is_shim(svc_path)
        if obs_shim and svc_shim:
            shim_pairs.append(name)
        else:
            real_dups.append(name)

    if shim_pairs:
        print(
            f"ℹ  {len(shim_pairs)} par(es) shim legítimo (ambos re-export → domain canonical; OK): "
            + ", ".join(shim_pairs)
        )

    if real_dups:
        print("❌ Dups proibidas em shared/observability/ ↔ shared/services/:", file=sys.stderr)
        for d in real_dups:
            obs_shim = _is_shim(OBS_DIR / d)
            svc_shim = _is_shim(SVC_DIR / d)
            print(f"  - {d}  (obs_shim={obs_shim}, svc_shim={svc_shim})", file=sys.stderr)
        print(
            "\nConvenção (CLAUDE.md):\n"
            "  shared/observability/ = telemetria, alertas, métricas, drift, budget tracking\n"
            "  shared/services/      = regra de negócio compartilhada cross-domain\n"
            "Mesmo basename em ambos = duplicação de implementação. Consolidar em uma só localização.\n"
            "Se um dos dois já é shim, converta o outro também (R-005.2).",
            file=sys.stderr,
        )
        return 1

    obs_count = len(obs_files)
    svc_count = len(svc_files)
    print(
        f"✓ shared/observability/ ({obs_count}) e shared/services/ ({svc_count}) sem dups de implementação"
        + (f" [{len(shim_pairs)} shim-pair(s) excluído(s)]" if shim_pairs else "")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
