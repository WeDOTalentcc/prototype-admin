#!/usr/bin/env python3
"""Sensor — `ComplianceContext(...)` must include all 6 required arguments.

REGRESSÃO 2026-05-24: `agentic_loop.py:220` chamava ComplianceContext com
apenas 4 args (company_id, user_id, domain, agent_id) — faltavam
`session_id` e `original_message`. Resultado: TODO post_compliance no
agentic_loop falhava silenciosamente. FactChecker + audit log de output
da LIA DESLIGADOS em produção sem ninguém saber (só warning no log).

Detection: AST scan de ``ComplianceContext(...)`` em todos os arquivos Python
do projeto, verificando que all keyword args required estão presentes:
- company_id (string)
- user_id (string)
- session_id (string)
- domain (string)
- agent_id (string)
- original_message (string)

Pattern: BLOCKING após baseline 0.

Usage:
    python scripts/check_compliance_context_complete.py
    python scripts/check_compliance_context_complete.py --json
    python scripts/check_compliance_context_complete.py --blocking
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_GLOBS = ["app/**/*.py"]
REQUIRED_ARGS = frozenset({
    "company_id", "user_id", "session_id", "domain", "agent_id", "original_message",
})
EXEMPT_MARKER = "COMPLIANCE-CONTEXT-OK:"


@dataclass
class Violation:
    file: str
    line: int
    missing: list[str]

    def as_dict(self) -> dict:
        return asdict(self)


def _scan_file(path: Path) -> list[Violation]:
    violations: list[Violation] = []
    try:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
    except (SyntaxError, UnicodeDecodeError):
        return violations

    src_lines = text.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        is_target = (
            (isinstance(f, ast.Name) and f.id == "ComplianceContext")
            or (isinstance(f, ast.Attribute) and f.attr == "ComplianceContext")
        )
        if not is_target:
            continue

        # Skip aliased local names (e.g., _C3bCtx) — they're already in scope
        # but we detect the actual class binding via import. To keep AST scan
        # simple, also detect calls to _C3bCtx / C3bCtx that look like the same.
        # Already handled by attribute match above.

        # Exempt marker (line above call)
        if node.lineno >= 2 and EXEMPT_MARKER in src_lines[node.lineno - 2]:
            continue

        kw_names = {kw.arg for kw in node.keywords if kw.arg is not None}
        missing = sorted(REQUIRED_ARGS - kw_names)
        if missing:
            violations.append(
                Violation(
                    file=str(path.relative_to(REPO_ROOT)),
                    line=node.lineno,
                    missing=missing,
                )
            )

    # Also catch `_C3bCtx(...)` aliased call sites
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name) and f.id in ("_C3bCtx", "C3bCtx"):
            if node.lineno >= 2 and EXEMPT_MARKER in src_lines[node.lineno - 2]:
                continue
            kw_names = {kw.arg for kw in node.keywords if kw.arg is not None}
            missing = sorted(REQUIRED_ARGS - kw_names)
            if missing:
                violations.append(
                    Violation(
                        file=str(path.relative_to(REPO_ROOT)),
                        line=node.lineno,
                        missing=missing,
                    )
                )

    return violations


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--blocking", action="store_true")
    args = parser.parse_args(argv)

    all_files: list[Path] = []
    for glob in TARGET_GLOBS:
        all_files.extend(REPO_ROOT.glob(glob))

    violations: list[Violation] = []
    for path in sorted(set(all_files)):
        if path.is_file() and path.suffix == ".py":
            violations.extend(_scan_file(path))

    if args.json:
        print(json.dumps({"violations": [v.as_dict() for v in violations]}, indent=2))
    else:
        if violations:
            print(f"❌ {len(violations)} ComplianceContext call(s) missing required args:\n")
            for v in violations:
                print(f"  {v.file}:{v.line}")
                print(f"    Missing kwargs: {', '.join(v.missing)}")
                print(f"    → Fix: add missing kwargs. session_id usually = conversation_id; "
                      f"original_message = user input pre-PII-strip. See "
                      f"app/api/v1/chat.py:323 and app/api/v1/agent_chat_ws.py:1269 "
                      f"for canonical examples. Bypass with `# {EXEMPT_MARKER} <reason>` "
                      f"comment above the call if legitimately partial (rare).\n")
        else:
            print("✅ All ComplianceContext calls have required args.")

    if args.blocking and violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
