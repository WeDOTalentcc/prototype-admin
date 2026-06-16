#!/usr/bin/env python3
"""Sensor canonical: check_no_plaintext_pii.

Detecta writes plaintext em colunas LGPD PII canonical:
- ``PaymentMethod.billing_document`` (CPF/CNPJ) — Wave 4 audit 2026-05-22.

Pattern derivado de ``check_no_plaintext_credentials.py`` (Wave 3 P0.D).

Falha (exit 1) se algum site fizer:
  - ``PaymentMethod(billing_document=<expr>)`` — kwarg em construtor
  - ``pm.billing_document = <expr>`` — attribute assignment

Permitido:
  - ``PaymentMethod(billing_document_encrypted=...)`` — canonical
  - ``pm.billing_document_encrypted = ...``
  - ``pm.billing_document_legacy = None`` — defense-in-depth clear
  - Linhas com marcador ``# PII-PLAINTEXT-OK: <reason>`` (audit + ticket)

Escopo: arquivos sob ``app/`` e ``libs/models/`` no lia-agent-system.

LGPD Art. 5 II + Art. 46 — CPF/CNPJ é "dado pessoal" e exige medidas
técnicas de segurança. Plaintext em DB = violação direta.

Usage:
    python scripts/check_no_plaintext_pii.py            # blocking
    python scripts/check_no_plaintext_pii.py --warn-only

Output otimizado para LLM: cada violação inclui path:linha + fix sugerido.
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
EXEMPT_MARKER = re.compile(r"#\s*PII-PLAINTEXT-OK\b")

# Files that legitimately reference the legacy column (model definition,
# the migration backfill itself if it lived here, sensor file).
ALLOWLIST_FILES = {
    "libs/models/lia_models/billing.py",  # column definition
    "scripts/check_no_plaintext_pii.py",
}

# Sentinel column names to ban from plaintext writes
PII_COLUMNS = {"billing_document"}
PII_MODELS = {"PaymentMethod"}


class PlaintextPIIVisitor(ast.NodeVisitor):
    def __init__(self, source_lines: list[str], rel_path: str):
        self.source_lines = source_lines
        self.rel_path = rel_path
        self.violations: list[tuple[int, str, str]] = []

    def _is_exempt(self, lineno: int) -> bool:
        if 0 < lineno <= len(self.source_lines):
            return bool(EXEMPT_MARKER.search(self.source_lines[lineno - 1]))
        return False

    def visit_Call(self, node: ast.Call) -> None:
        # Detect PaymentMethod(billing_document=...) — kwarg
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in PII_MODELS:
            for kw in node.keywords:
                if kw.arg in PII_COLUMNS and not self._is_exempt(kw.lineno):
                    self.violations.append((
                        kw.lineno,
                        f"{func_name}({kw.arg}=...) plaintext PII kwarg (LGPD Art. 46)",
                        f"use encrypt_pii(...) -> {kw.arg}_encrypted kwarg",
                    ))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # Detect obj.billing_document = <expr>
        for tgt in node.targets:
            if isinstance(tgt, ast.Attribute) and tgt.attr in PII_COLUMNS:
                if not self._is_exempt(node.lineno):
                    self.violations.append((
                        node.lineno,
                        f"obj.{tgt.attr} = ... plaintext PII assignment (LGPD Art. 46)",
                        f"use obj.{tgt.attr}_encrypted = encrypt_pii(...)",
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
    visitor = PlaintextPIIVisitor(source.splitlines(), rel)
    visitor.visit(tree)
    return [(rel, lineno, what, fix) for lineno, what, fix in visitor.violations]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print violations but exit 0 (ratchet mode).",
    )
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
        print("OK no plaintext PII writes detected")
        return 0

    print(f"VIOLATIONS: {len(all_violations)} plaintext PII write(s)")
    for rel, lineno, what, fix in all_violations:
        print(f"  {rel}:{lineno}")
        print(f"    issue: {what}")
        print(f"    fix:   {fix}")
        print(f"    escape hatch: '# PII-PLAINTEXT-OK: <ticket>:<reason>'")

    print()
    print("Canonical: scalar PII must be encrypted via")
    print("  from app.shared.services.pii_crypto import encrypt_pii")
    print("  enc = encrypt_pii(cpf_str)  # writes -> billing_document_encrypted")
    print("LGPD Art. 5 II + Art. 46. See migration 169_encrypt_billing_document.")

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
