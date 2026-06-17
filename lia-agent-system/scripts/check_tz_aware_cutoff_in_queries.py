#!/usr/bin/env python3
"""Sensor 6 — DB queries com cutoff datetime aware contra colunas tz-naive.

REGRESSÃO 2026-05-24: `voice_retention.py`, `wsi_abandoned_service.py`,
`followup_service.py` passavam `datetime.now(timezone.utc)` (tz-aware) como
parâmetro para asyncpg em colunas `timestamp without time zone` (naive).
Resultado: `DataError: can't subtract offset-naive and offset-aware datetimes`.

Schema da WeDOTalent é tz-naive em 90%+ das colunas timestamp (legacy).
Quando colunas forem migradas para `timestamp with time zone`, este sensor
precisará update (ou EXEMPT marker).

Detection: para jobs/cron files, detectar:
- `datetime.now(timezone.utc)` ou `datetime.now(UTC)` sendo USADO como cutoff
  em parâmetros de query (db.execute(..., {"cutoff": <var>}))

Heurística: flagga se o arquivo está em app/jobs/ E usa `datetime.now(tz...)`
sem `.replace(tzinfo=None)` na mesma função.

Honra `# DB-TZ-AWARE-OK: <reason>` (e.g., quando a coluna É tz-aware).

Pattern: BLOCKING (baseline 0 após fix 2026-05-24).
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXEMPT_MARKER = "DB-TZ-AWARE-OK:"

TARGETS = [
    "app/jobs/tasks/voice_retention.py",
    "app/jobs/wsi_abandoned_service.py",
    "app/jobs/followup_service.py",
    "app/jobs/tasks/_utils.py",
    "app/jobs/wsi_abandoned_service.py",
]


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

    # Walk each function/method body
    for func in ast.walk(tree):
        if not isinstance(func, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue

        # Collect: does this function call `datetime.now(timezone.utc)` or
        # `datetime.now(UTC)` AND assign to a name that is later passed to
        # `db.execute(..., {"cutoff": <name>, ...})`?
        # Simplification: just detect "datetime.now(<arg>)" inside body where
        # arg is NOT None/missing.

        aware_assigns: dict[str, int] = {}  # var_name -> lineno
        naive_replacements: set[str] = set()  # var_name with replace(tzinfo=None)

        for node in ast.walk(func):
            # Find: name = datetime.now(timezone.utc) [or datetime.now(UTC)]
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if not isinstance(target, ast.Name):
                    continue
                if isinstance(node.value, ast.Call):
                    call = node.value
                    if (
                        isinstance(call.func, ast.Attribute)
                        and call.func.attr == "now"
                        and isinstance(call.func.value, ast.Name)
                        and call.func.value.id == "datetime"
                        and call.args  # has at least 1 arg (tz)
                    ):
                        aware_assigns[target.id] = node.lineno
            # Find: name = name.replace(tzinfo=None)
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                t = node.targets[0]
                if isinstance(t, ast.Name) and isinstance(node.value, ast.Call):
                    call = node.value
                    if (
                        isinstance(call.func, ast.Attribute)
                        and call.func.attr == "replace"
                        and any(
                            isinstance(k, ast.keyword)
                            and k.arg == "tzinfo"
                            and isinstance(k.value, ast.Constant)
                            and k.value.value is None
                            for k in call.keywords
                        )
                    ):
                        naive_replacements.add(t.id)

        # Find calls db.execute(..., {<dict with aware vars as values>})
        for node in ast.walk(func):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if not (
                isinstance(f, ast.Attribute)
                and f.attr == "execute"
                and isinstance(f.value, ast.Name)
                and f.value.id == "db"
            ):
                continue
            # 2nd positional arg or kw "parameters" is the params dict
            params_arg = None
            if len(node.args) >= 2:
                params_arg = node.args[1]
            for kw in node.keywords:
                if kw.arg == "parameters":
                    params_arg = kw.value
            if not isinstance(params_arg, ast.Dict):
                continue
            # Walk dict values for Names that are in aware_assigns and NOT in
            # naive_replacements
            for v in params_arg.values:
                # Allow direct Name or arithmetic on Name (e.g., now - timedelta)
                referenced = set()
                for sub in ast.walk(v):
                    if isinstance(sub, ast.Name):
                        referenced.add(sub.id)
                offending = referenced & set(aware_assigns) - naive_replacements
                if offending:
                    # Exempt marker check
                    if node.lineno >= 2 and EXEMPT_MARKER in src_lines[node.lineno - 2]:
                        continue
                    violations.append({
                        "file": str(path.relative_to(REPO_ROOT)),
                        "line": node.lineno,
                        "function": func.name,
                        "tz_aware_vars_in_query": sorted(offending),
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
            print(f"❌ {len(violations)} db.execute call(s) com cutoff tz-aware:\n")
            for v in violations:
                print(f"  {v['file']}:{v['line']}  fn={v['function']}")
                print(f"    Vars tz-aware passed: {v['tz_aware_vars_in_query']}")
                print(f"    → Schema WeDOTalent é majoritariamente `timestamp without "
                      f"time zone`. Use `datetime.utcnow()` ou `.replace(tzinfo=None)` "
                      f"antes do parâmetro. EXEMPT: `# {EXEMPT_MARKER} <reason>` se a "
                      f"coluna for tz-aware (`timestamp with time zone`).\n")
        else:
            print("✅ No tz-aware datetime passed to db.execute against naive columns.")

    if args.blocking and violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
