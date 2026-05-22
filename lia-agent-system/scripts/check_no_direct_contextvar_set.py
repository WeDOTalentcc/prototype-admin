#!/usr/bin/env python3
"""
Sensor G-CONTEXTVAR: bloqueia chamadas diretas a _current_company_id.set()
fora dos 2 helpers canonicos de R-008.

R-008 (Sprint 1) hardening do ContextVar de company_id: a ContextVar
SO PODE ser populada via _set_company_id_from_jwt() ou
_set_company_id_synthetic_dev_only(). Chamadas diretas indicam regressao
ou novo bypass de auth multi-tenant.

Exit: 0 = clean, 1 = violacao encontrada.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

AUTHORIZED_FILE = "app/middleware/auth_enforcement.py"
# Exclude scripts/ (sensor files mention the pattern in docs/prints)
EXCLUDED_DIRS = {"scripts", ".git", "__pycache__", ".venv", "venv"}
CANONICAL_HELPERS = ("_set_company_id_from_jwt", "_set_company_id_synthetic_dev_only")
DIRECT_SET_RE = re.compile(r"_current_company_id\.set\(", re.IGNORECASE)
# Allow ADR-029-EXEMPT marker in the same line or 10 lines above (docstring block).
EXEMPT_MARKER = "ADR-029-EXEMPT"


def _strip_strings_and_comments(source: str) -> list[tuple[int, str]]:
    """Return (lineno, line) pairs with string literals and comments blanked out."""
    result = []
    in_triple = False
    triple_char = None
    for lineno, line in enumerate(source.splitlines(), 1):
        stripped = ""
        i = 0
        while i < len(line):
            if in_triple:
                end = line.find(triple_char * 3, i)
                if end != -1:
                    i = end + 3
                    in_triple = False
                else:
                    i = len(line)
            else:
                ch = line[i]
                if ch == "#":
                    break  # rest of line is comment
                elif line[i:i+3] in ('"""', "'''"):
                    triple_char = line[i]
                    end = line.find(triple_char * 3, i + 3)
                    if end != -1:
                        i = end + 3  # single-line triple string
                    else:
                        in_triple = True
                        i = len(line)
                elif ch in ('"', "'"):
                    j = i + 1
                    while j < len(line) and line[j] != ch:
                        if line[j] == "\\":
                            j += 1
                        j += 1
                    i = j + 1
                else:
                    stripped += ch
                    i += 1
        result.append((lineno, stripped))
    return result


def main() -> int:
    violations = []

    for py_file in ROOT.rglob("*.py"):
        rel = py_file.relative_to(ROOT).as_posix()
        # Skip excluded directories
        parts = set(rel.split("/"))
        if parts & EXCLUDED_DIRS:
            continue
        if rel.startswith("tests/") or "/tests/" in rel:
            continue  # test files manipulate ContextVar for setup

        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        if not DIRECT_SET_RE.search(source):
            continue  # fast path

        lines = _strip_strings_and_comments(source)

        if rel == AUTHORIZED_FILE:
            # Only check lines OUTSIDE the canonical helper function bodies
            in_helper = False
            sets_outside = 0
            for _, stripped in lines:
                if re.match(r"def _set_company_id_", stripped):
                    in_helper = True
                elif re.match(r"^def |^class ", stripped) and in_helper:
                    in_helper = False
                if not in_helper and DIRECT_SET_RE.search(stripped):
                    sets_outside += 1
            if sets_outside > 0:
                violations.append(
                    f"  {rel}: {sets_outside} chamada(s) direta(s) fora dos helpers"
                )
        else:
            raw_lines = source.splitlines()
            for lineno, stripped in lines:
                if DIRECT_SET_RE.search(stripped):
                    # Check for ADR-029-EXEMPT marker in same line OR 6 lines above
                    # (allows docstring-style justification block).
                    window_start = max(0, lineno - 11)  # 10-line window above + same line
                    window = "\n".join(raw_lines[window_start:lineno])
                    if EXEMPT_MARKER in window:
                        continue  # exempted
                    raw_line = raw_lines[lineno - 1]
                    violations.append(f"  {rel}:{lineno}: {raw_line.strip()}")

    if violations:
        print("FAIL [G-CONTEXTVAR] _current_company_id.set() direto detectado fora dos helpers:")
        print("\n".join(violations))
        print()
        print("INSTRUCAO DE CORRECAO:")
        print("  Use _set_company_id_from_jwt(verified_payload) para auth real (JWT verificado).")
        print("  Use _set_company_id_synthetic_dev_only(id) para paths DEV_MODE gateados.")
        print("  Para runtime scope (ex: agent-to-agent), adicionar comment ADR-029-EXEMPT")
        print("  na mesma linha ou ate 6 linhas acima documentando justificativa + reset em finally.")
        print("  NUNCA setar diretamente de request.body/query/headers (R-008).")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
