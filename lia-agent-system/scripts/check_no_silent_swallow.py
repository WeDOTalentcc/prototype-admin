#!/usr/bin/env python3
"""
Sensor canonical: detecta  seguido imediatamente de
pass/return/continue SEM logger.* na linha imediata.

Exclui: ImportError (optional deps), CancelledError, ValueError-em-loop-com-continue.

Uso: python scripts/check_no_silent_swallow.py [--paths app/orchestrator,...]
Sai exit=1 se violations não-aceitáveis encontradas.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PATHS = [
    "app/orchestrator",
    "app/shared/llm",
    "app/shared/compliance",
    "app/shared/providers",
    "app/middleware",
    "app/shared/services",
    "app/domains",
]

# Tipos excluídos (silenciar é aceitável)
EXCLUDED_TYPES = {"ImportError", "asyncio.CancelledError", "CancelledError"}

EXCEPT_RE = re.compile(r"^\s*except\s+([A-Za-z_][\w\.]*)(\s+as\s+\w+)?\s*:\s*$")
SILENT_RE = re.compile(r"^\s*(pass|return\s|continue\s*$)")
LOGGER_RE = re.compile(r"\blogger\.")


def scan_file(path: Path):
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return violations
    for i, line in enumerate(lines):
        m = EXCEPT_RE.match(line)
        if not m:
            continue
        exc_type = m.group(1)
        if exc_type in EXCLUDED_TYPES:
            continue
        # Próximas 1-2 linhas não-vazias
        next_lines = []
        for j in range(i + 1, min(i + 4, len(lines))):
            stripped = lines[j].strip()
            if stripped:
                next_lines.append(lines[j])
                if len(next_lines) >= 2:
                    break
        if not next_lines:
            continue
        first_next = next_lines[0]
        # É silent?
        if SILENT_RE.match(first_next):
            # Tem logger nas próximas 2 linhas?
            ctx = "\n".join(next_lines)
            if not LOGGER_RE.search(ctx):
                violations.append((path, i + 1, line.rstrip(), first_next.strip()))
    return violations



EXC_INFO_WARN_RE = re.compile(r"logger\.(warning|error)\(")


def scan_file_exc_info(path: Path):
    """Detecta except Exception com logger.warning/error mas sem exc_info=True."""
    violations = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return violations
    for i, line in enumerate(lines):
        m = EXCEPT_RE.match(line)
        if not m:
            continue
        exc_type = m.group(1)
        if exc_type in EXCLUDED_TYPES:
            continue
        # Collect next 4 non-empty lines
        block_lines = []
        for j in range(i + 1, min(i + 8, len(lines))):
            stripped = lines[j].strip()
            if stripped:
                block_lines.append(lines[j])
                if len(block_lines) >= 4:
                    break
        block = "\n".join(block_lines)
        # Has logger.warning/error call but no exc_info=True?
        if EXC_INFO_WARN_RE.search(block) and "exc_info=True" not in block:
            violations.append((path, i + 1, line.rstrip()))
    return violations

def main(argv):
    paths = DEFAULT_PATHS
    if len(argv) > 1 and argv[1].startswith("--paths"):
        if "=" in argv[1]:
            paths = argv[1].split("=", 1)[1].split(",")

    all_violations = []
    exc_info_violations = []
    for path_str in paths:
        base = ROOT / path_str
        if not base.exists():
            continue
        for f in base.rglob("*.py"):
            if "__pycache__" in f.parts or f.name.startswith("test_"):
                continue
            all_violations.extend(scan_file(f))
            exc_info_violations.extend(scan_file_exc_info(f))

    if all_violations:
        print("WARN Silent exception swallows (sem logger nas proximas 2 linhas):", file=sys.stderr)
        for p, line_no, except_line, next_line in all_violations:
            rel = p.relative_to(ROOT)
            print(f"  {rel}:{line_no}: {except_line.strip()} -> {next_line[:60]}", file=sys.stderr)
        print(f"\nTotal: {len(all_violations)} silent swallows.", file=sys.stderr)
        print("Substitua por: logger.debug(..., exc_info=True) ou logger.warning para compliance.", file=sys.stderr)

    if exc_info_violations:
        print("\nWARN logger.warning/error sem exc_info=True (traceback perdido):", file=sys.stderr)
        for p, line_no, except_line in exc_info_violations:
            rel = p.relative_to(ROOT)
            print(f"  {rel}:{line_no}: {except_line.strip()}", file=sys.stderr)
            print(f"    -> Fix: adicionar exc_info=True ao logger call na linha seguinte", file=sys.stderr)
        print(f"\nTotal: {len(exc_info_violations)} sem exc_info.", file=sys.stderr)

    if not all_violations and not exc_info_violations:
        print("OK Sem silent swallows nem logger sem exc_info em paths criticos")
    # Modo warn-only inicial - exit 0
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
