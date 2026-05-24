#!/usr/bin/env python3
"""Sensor 5 (v3) — bloqueia iteração sobre tabelas legacy never-existed.

REGRESSÃO 2026-05-24 (commit acd2f7174 follow-up): `lgpd_cleanup_service.py`
tinha `for table in ("messages", "conversation_messages", "chat_messages"):`
onde as 2 últimas tabelas NUNCA existiram no schema canonical. Primeira falha
da iteração cascateava InFailedSQLTransactionError em TODAS as TTLs seguintes.

Escopo do sensor: detecta `for ... in (..., "conversation_messages", ...)` ou
`for ... in (..., "chat_messages", ...)` — apenas em iteração, NÃO em strings
soltas (que podem ser dict keys ou allowlist de defense-in-depth).

Honra `# LGPD-LEGACY-TABLE-OK: <reason>` acima do for-statement.

Pattern: BLOCKING (baseline 0 após fix 2026-05-24).
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

LEGACY_NEVER_EXISTED = frozenset({"conversation_messages", "chat_messages"})
EXEMPT_MARKER = "LGPD-LEGACY-TABLE-OK:"

TARGETS = [
    "app/domains/lgpd/services/lgpd_cleanup_service.py",
    "app/jobs/tasks/voice_retention.py",
    "app/jobs/wsi_abandoned_service.py",
    "app/jobs/followup_service.py",
    "app/jobs/tasks/_utils.py",
]


def _extract_strings_from_tuple_or_list(node: ast.AST) -> list[str]:
    """Return string literals if node is a tuple/list of constants."""
    if not isinstance(node, (ast.Tuple, ast.List)):
        return []
    out: list[str] = []
    for elt in node.elts:
        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
            out.append(elt.value)
    return out


def _scan_file(path: Path) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    src_lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    violations: list[dict] = []

    # Also handle ttl_config: list[tuple[str, int]] = [("table", days), ...]
    # by walking each `for ... in <list-literal-of-tuples>`
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue

        # Exempt marker on line above
        if node.lineno >= 2 and EXEMPT_MARKER in src_lines[node.lineno - 2]:
            continue

        iter_node = node.iter
        legacy_found: list[str] = []

        # Case A: for table in ("messages", "conversation_messages", ...)
        strings = _extract_strings_from_tuple_or_list(iter_node)
        legacy_found.extend(s for s in strings if s in LEGACY_NEVER_EXISTED)

        # Case B: for table_name, days in [("messages", 90), ("conversation_messages", 90), ...]
        if isinstance(iter_node, (ast.Tuple, ast.List)):
            for sub in iter_node.elts:
                if isinstance(sub, ast.Tuple) and sub.elts:
                    first = sub.elts[0]
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        if first.value in LEGACY_NEVER_EXISTED:
                            legacy_found.append(first.value)

        # Case C: for x in some_var where some_var is a list literal nearby
        # (deferred — TTL_CONFIG inlined is the canonical pattern)

        if legacy_found:
            violations.append({
                "file": str(path.relative_to(REPO_ROOT)),
                "line": node.lineno,
                "legacy_iterated": sorted(set(legacy_found)),
            })

    return violations


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--blocking", action="store_true")
    args = parser.parse_args(argv)

    violations = []
    for rel in TARGETS:
        violations.extend(_scan_file(REPO_ROOT / rel))

    if args.json:
        print(json.dumps({"violations": violations}, indent=2))
    else:
        if violations:
            print(f"❌ {len(violations)} for-loop(s) iterating legacy LGPD tables:\n")
            for v in violations:
                print(f"  {v['file']}:{v['line']}")
                print(f"    Legacy tables iterated: {v['legacy_iterated']}")
                print(f"    → Essas tabelas nunca existiram no schema canonical. "
                      f"UndefinedTableError aborta a transação e cascateia "
                      f"InFailedSQLTransactionError em TTLs subsequentes. "
                      f"Remova do iterable ou adicione `# {EXEMPT_MARKER} <reason>` acima.\n")
        else:
            print("✅ No for-loop iterates legacy LGPD tables.")

    if args.blocking and violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
