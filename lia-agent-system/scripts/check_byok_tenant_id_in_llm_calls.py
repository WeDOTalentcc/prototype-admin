#!/usr/bin/env python3
"""Sensor (warn-only baseline): BYOK tenant_id threading into create_tracked_llm.

Fase 2.5 Onda C2.4 — BYOK invariant (plano §2).

Every agent execution must propagate the tenant's ``tenant_id`` into
``create_tracked_llm(...)`` so the per-tenant ProviderContainer (and the tenant's
own API key when configured) is loaded. A call that omits ``tenant_id`` or passes
``tenant_id=None`` silently falls back to the platform default provider — wrong
billing + wrong key for BYOK tenants.

Scope: files in the agent/runtime/dispatch hot path
(``*agent*``, ``*runtime*``, ``*dispatch*`` in the filename). AST-based (not
regex) per the harness-engineering lesson that regex sensors produce >50% false
positives on scoped bindings.

A call is a VIOLATION when it:
  - calls ``create_tracked_llm(...)``, AND
  - has no ``tenant_id=`` keyword, OR passes ``tenant_id=None`` (literal None).

Calls passing ``tenant_id=<anything-else>`` (a variable, attribute, etc.) pass.

Mode: warn-only by default (baseline may be > 0 until Onda C1 closes the engine).
``--blocking`` exits 1 when violations > ``--max-violations`` (default 0).

Exit codes:
  0 — warn-only (always), or blocking with violations <= max.
  1 — blocking with violations > max.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = [ROOT / "app", ROOT / "libs"]
NAME_HINTS = ("agent", "runtime", "dispatch")
TARGET_FUNC = "create_tracked_llm"


def _is_target_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == TARGET_FUNC
    if isinstance(func, ast.Attribute):
        return func.attr == TARGET_FUNC
    return False


def _violation_reason(node: ast.Call) -> str | None:
    """Return a reason string if this create_tracked_llm call violates BYOK."""
    tenant_kw = next(
        (kw for kw in node.keywords if kw.arg == "tenant_id"), None
    )
    if tenant_kw is None:
        return "missing tenant_id= keyword (defaults to None -> platform provider)"
    if isinstance(tenant_kw.value, ast.Constant) and tenant_kw.value.value is None:
        return "tenant_id=None (hardcoded -> platform provider, BYOK ignored)"
    return None


def _scan_file(path: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return []
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_target_call(node):
            reason = _violation_reason(node)
            if reason:
                out.append((node.lineno, reason))
    return out


def _in_scope(path: Path) -> bool:
    name = path.name.lower()
    if "__pycache__" in path.parts or path.name.endswith("_test.py"):
        return False
    if "/tests/" in str(path).replace("\\", "/"):
        return False
    return any(h in name for h in NAME_HINTS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true")
    parser.add_argument("--max-violations", type=int, default=0)
    args = parser.parse_args(argv)

    violations: list[tuple[Path, int, str]] = []
    scanned = 0
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if not _in_scope(path):
                continue
            scanned += 1
            for lineno, reason in _scan_file(path):
                violations.append((path, lineno, reason))

    print(
        f"[byok-tenant sensor] scanned {scanned} agent/runtime/dispatch files; "
        f"{len(violations)} create_tracked_llm call(s) without resolved tenant_id."
    )
    for path, lineno, reason in violations:
        rel = path.relative_to(ROOT.parent) if ROOT.parent in path.parents else path
        print(
            f"[byok-tenant sensor] {rel}:{lineno} {TARGET_FUNC}() -> {reason}\n"
            f"  Fix: pass tenant_id=<company_id resolved from the deployment/agent "
            f"context> so the per-tenant ProviderContainer (BYOK key) is loaded.",
            file=sys.stderr,
        )

    if not violations:
        print("[byok-tenant sensor] OK — all agent-path LLM calls thread tenant_id.")

    if args.blocking and len(violations) > args.max_violations:
        print(
            f"\n[byok-tenant sensor] BLOCKING: {len(violations)} > "
            f"max {args.max_violations}.",
            file=sys.stderr,
        )
        return 1
    if not args.blocking and violations:
        print(
            "[byok-tenant sensor] WARN-ONLY — not blocking. Pass --blocking "
            "once Onda C1 closes the engine and baseline reaches 0.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
