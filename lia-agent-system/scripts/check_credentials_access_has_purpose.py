#!/usr/bin/env python3
"""AST sensor — every call to get_decrypted_credentials MUST pass access_purpose=.

LGPD Art. 37 (Wave 3 Camada 3 — 2026-05-22): credentials decryption is a
sensitive operation that requires audit trail. The repository method
``IntegrationsHubRepository.get_decrypted_credentials`` was redesigned
to write an entry to ``credentials_access_logs`` on every call, and
requires the caller to pass ``access_purpose=<string>`` (keyword-only,
required) documenting *why* the secret material is being read.

This sensor walks every Python file under app/, libs/, scripts/, tests/
and detects any call to ``.get_decrypted_credentials(...)`` whose
keyword arguments do NOT include ``access_purpose``. Such a call would
raise TypeError at runtime, but we want to catch it pre-merge.

Exit code:
  0 — all calls guarded
  1 — one or more calls missing access_purpose= (printed to stderr)

Usage in CI:
  python lia-agent-system/scripts/check_credentials_access_has_purpose.py

LLM-consumable error message (REGRA harness):
  Each violation prints exact file:line plus the fix snippet.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = ("app", "libs", "scripts", "tests")
TARGET_METHOD = "get_decrypted_credentials"


def iter_python_files() -> Iterator[Path]:
    for top in SCAN_DIRS:
        base = ROOT / top
        if not base.exists():
            continue
        for p in base.rglob("*.py"):
            # Skip caches and venvs
            if "__pycache__" in p.parts or ".venv" in p.parts:
                continue
            yield p


def call_is_target(node: ast.Call) -> bool:
    """True iff node is a call to ``.get_decrypted_credentials(...)``."""
    target = node.func
    return isinstance(target, ast.Attribute) and target.attr == TARGET_METHOD


def call_has_access_purpose(node: ast.Call) -> bool:
    """True iff call has ``access_purpose=...`` keyword arg."""
    for kw in node.keywords:
        if kw.arg == "access_purpose":
            return True
        # Tolerate ``**kwargs`` splat (cannot statically prove absence) —
        # treat as guarded to avoid blocking dynamic dispatch patterns.
        if kw.arg is None:
            return True
    return False


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Return list of (lineno, snippet) for offending calls."""
    try:
        src = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []

    offenders: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not call_is_target(node):
            continue
        # Skip the definition site itself (it's an AsyncFunctionDef, not a Call)
        if call_has_access_purpose(node):
            continue
        snippet = (
            src.splitlines()[node.lineno - 1].strip()
            if node.lineno - 1 < len(src.splitlines())
            else "<unavailable>"
        )
        offenders.append((node.lineno, snippet))
    return offenders


def main() -> int:
    violations: list[tuple[Path, int, str]] = []
    for p in iter_python_files():
        for lineno, snippet in scan_file(p):
            violations.append((p, lineno, snippet))

    if not violations:
        print("[OK] check_credentials_access_has_purpose: 0 violations")
        return 0

    rel_root = ROOT
    print(
        "[FAIL] LGPD Art. 37 violation — get_decrypted_credentials called "
        "without access_purpose= keyword:\n",
        file=sys.stderr,
    )
    for p, lineno, snippet in violations:
        try:
            relp = p.relative_to(rel_root)
        except ValueError:
            relp = p
        print(f"  {relp}:{lineno}  {snippet}", file=sys.stderr)
    print(
        "\nFIX (per offending call) — add a keyword arg describing why:\n"
        "  await repo.get_decrypted_credentials(\n"
        "      conn_id, company_id,\n"
        "      access_purpose='webhook_dispatch',  # <-- REQUIRED (LGPD Art. 37)\n"
        "      accessor_user_id=current_user.id,    # when human in loop\n"
        "      accessor_type='human_user',           # or 'system'|'agent'|'celery_task'\n"
        "      request_id=getattr(request.state, 'request_id', None),\n"
        "  )",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
