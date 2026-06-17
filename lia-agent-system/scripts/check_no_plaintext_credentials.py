#!/usr/bin/env python3
"""Sensor canonical: check_no_plaintext_credentials.

Detecta writes plaintext em IntegrationConnection.credentials (legacy column).
Wave 3 audit 2026-05-21 - P0.D fix landed migration 168 + helper
``app.shared.services.credentials_crypto``.

Falha (exit 1) se algum site fizer:
  - ``IntegrationConnection(credentials=<expr>)`` - kwarg em construtor
  - ``connection.credentials = <expr>`` - attribute assignment

Permitido:
  - ``IntegrationConnection(credentials_encrypted=...)`` - canonical path
  - ``connection.credentials_encrypted = ...``
  - ``connection.credentials_legacy = None`` - defense-in-depth clear
  - Linhas com marcador ``# CREDENTIALS-PLAINTEXT-OK: <reason>`` (audit + ticket)

Escopo: arquivos sob ``app/`` e ``libs/models/`` no lia-agent-system.

Usage:
    python scripts/check_no_plaintext_credentials.py            # blocking
    python scripts/check_no_plaintext_credentials.py --warn-only

Output otimizado para consumo de LLM: cada violacao inclui path:linha +
sugestao de fix exata.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCAN_PATHS = [ROOT / "app", ROOT / "libs" / "models"]
SKIP_DIRS = {"__pycache__", ".pytest_cache", "alembic"}
EXEMPT_MARKER = re.compile(r"#\s*CREDENTIALS-PLAINTEXT-OK\b")

# Files that legitimately reference the legacy column (model, repo path
# that does the migration, sensor itself).
ALLOWLIST_FILES = {
    "libs/models/lia_models/integration_hub.py",  # column definition
    "app/domains/integrations_hub/repositories/integrations_hub_repository.py",
    "scripts/check_no_plaintext_credentials.py",
}


class PlaintextCredentialsVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: list[str], rel_path: str):
        self.source_lines = source_lines
        self.rel_path = rel_path
        self.violations: list[tuple[int, str, str]] = []

    def _is_exempt(self, lineno: int) -> bool:
        if 0 < lineno <= len(self.source_lines):
            return bool(EXEMPT_MARKER.search(self.source_lines[lineno - 1]))
        return False

    def visit_Call(self, node: ast.Call) -> None:
        # Detect IntegrationConnection(credentials=...) - kwarg
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name == "IntegrationConnection":
            for kw in node.keywords:
                if kw.arg == "credentials" and not self._is_exempt(kw.lineno):
                    self.violations.append((
                        kw.lineno,
                        "IntegrationConnection(credentials=...) plaintext kwarg",
                        "use encrypt_credentials(...) -> credentials_encrypted kwarg",
                    ))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # Detect obj.credentials = <expr>
        for tgt in node.targets:
            if isinstance(tgt, ast.Attribute) and tgt.attr == "credentials":
                if not self._is_exempt(node.lineno):
                    self.violations.append((
                        node.lineno,
                        "obj.credentials = ... plaintext assignment",
                        "use obj.credentials_encrypted = encrypt_credentials(...)",
                    ))
        self.generic_visit(node)


def scan_file(path: Path, root: Path) -> list[tuple[str, int, str, str]]:
    rel = str(path.relative_to(root))
    if rel in ALLOWLIST_FILES:
        return []
    try:
        source = path.read_text()
    except (UnicodeDecodeError, OSError):
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    visitor = PlaintextCredentialsVisitor(source.splitlines(), rel)
    visitor.visit(tree)
    return [(rel, lineno, what, fix) for lineno, what, fix in visitor.violations]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warn-only", action="store_true",
                        help="Print violations but exit 0 (ratchet mode).")
    args = parser.parse_args()

    all_violations: list[tuple[str, int, str, str]] = []
    for scan_root in SCAN_PATHS:
        if not scan_root.exists():
            continue
        for py in scan_root.rglob("*.py"):
            if any(p in SKIP_DIRS for p in py.parts):
                continue
            all_violations.extend(scan_file(py, ROOT))

    if not all_violations:
        print("OK no plaintext credentials writes detected")
        return 0

    print(f"VIOLATIONS: {len(all_violations)} plaintext credentials write(s)")
    for rel, lineno, what, fix in all_violations:
        print(f"  {rel}:{lineno}")
        print(f"    issue: {what}")
        print(f"    fix:   {fix}")
        print(f"    escape hatch: add comment '# CREDENTIALS-PLAINTEXT-OK: <ticket>:<reason>'")

    print()
    print("Canonical: credentials must be encrypted via")
    print("  from app.shared.services.credentials_crypto import encrypt_credentials")
    print("  enc = encrypt_credentials(creds_dict)  # writes -> credentials_encrypted (Text)")
    print("ADR-006 + LGPD Art. 46. See migration 168_encrypt_integration_credentials.")

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
