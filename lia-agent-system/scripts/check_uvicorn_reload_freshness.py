#!/usr/bin/env python3
"""
Sensor canonical (F11, 2026-05-24): detecta uvicorn rodando com config velha de
`.replit` workflow (reload-dir antigo vs reload-include atual).

Contexto: durante F11 audit (2026-05-24), descobrimos que o uvicorn iniciado às
10:57 estava com `--reload-dir app` (config velha), mas `.replit` foi atualizado
pra `--reload-include='app/**/*.py'` (correção do restart-loop registrada em
memory `project_restart_loop_audit_2026-05-24`). Resultado: WatchFiles broken,
file changes não disparavam reload, agent dev cycle quietly broken por 3+ horas.

Detecção: compara cmdline do processo uvicorn vs args do .replit workflow.
Output otimizado para LLM (instruções de fix).

Modes:
  default (warn-only): print findings, exit 0
  --blocking: exit 1 if drift detected

Usage:
  python3 scripts/check_uvicorn_reload_freshness.py [--blocking]

Idempotente. Pode rodar em CI ou local. Não modifica nada (read-only).
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


REPLIT_FILE = Path("/home/runner/workspace/.replit")


def get_uvicorn_cmdline() -> str | None:
    """Find running uvicorn process and return its cmdline."""
    try:
        result = subprocess.run(
            ["pgrep", "-af", "uvicorn app.main"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    # pgrep returns lines like "PID cmdline..."
    for line in result.stdout.splitlines():
        if "uvicorn app.main" in line:
            return line
    return None


def get_replit_workflow_args() -> str | None:
    """Read .replit and find the lia-backend workflow args."""
    if not REPLIT_FILE.exists():
        return None
    text = REPLIT_FILE.read_text()
    # Find the workflow "lia-backend" args
    pattern = re.compile(
        r'name\s*=\s*"lia-backend".*?args\s*=\s*"([^"]+)"',
        re.DOTALL,
    )
    m = pattern.search(text)
    if m:
        return m.group(1)
    return None


def extract_reload_flags(cmdline: str) -> set[str]:
    """Extract --reload-* flags from a cmdline."""
    flags = set()
    for m in re.finditer(r"--reload[-\w]*(?:=\S+)?", cmdline):
        flags.add(m.group(0))
    return flags


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true",
                        help="Exit 1 if reload config drift detected.")
    args = parser.parse_args()

    print("check_uvicorn_reload_freshness.py\n")

    uvicorn_cmdline = get_uvicorn_cmdline()
    if not uvicorn_cmdline:
        print("ℹ️  Uvicorn process not running — nothing to check.")
        return 0

    replit_args = get_replit_workflow_args()
    if not replit_args:
        print("⚠️  Could not find .replit workflow args — skipping drift check.")
        return 0

    uvicorn_flags = extract_reload_flags(uvicorn_cmdline)
    replit_flags = extract_reload_flags(replit_args)

    # Drift detection: any flag in replit that's missing from running process
    missing_in_process = replit_flags - uvicorn_flags
    extra_in_process = uvicorn_flags - replit_flags

    if not missing_in_process and not extra_in_process:
        print("✅ Uvicorn cmdline matches .replit workflow args — reload config in sync.")
        return 0

    print("❌ DRIFT DETECTED: uvicorn process started with outdated config.")
    print()
    if missing_in_process:
        print("  Flags in .replit but MISSING from running process:")
        for f in sorted(missing_in_process):
            print(f"    + {f}")
    if extra_in_process:
        print("  Flags in running process but REMOVED from .replit:")
        for f in sorted(extra_in_process):
            print(f"    - {f}")
    print()
    print("→ Fix: restart workflow `lia-backend` in Replit IDE OR")
    print("       kill -TERM $(pgrep -f 'uvicorn app.main') && let workflow respawn.")
    print()
    print("→ Why this matters: reload watcher uses cmdline args set at startup;")
    print("  changes to .replit after boot are silently ignored. Code edits stop")
    print("  triggering reload → agent dev loop quietly broken.")
    print()
    print("→ Reference: memory `project_restart_loop_audit_2026-05-24` documents")
    print("  the canonical .replit args. F11 audit (2026-05-24) observed 3+ hours")
    print("  of stale runtime before detection.")

    return 1 if args.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
