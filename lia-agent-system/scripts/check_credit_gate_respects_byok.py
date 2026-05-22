#!/usr/bin/env python3
"""Sensor canonical: check_credit_gate_respects_byok.

ADR-WT-2027 BYOK Strategy (Opcao C, 2026-05-22) -- guards Bug B3 regression.

Background
----------
Before this sensor, ``ai_credit_gate.check_credit_budget`` was the canonical
budget enforcement point but did NOT detect BYOK -- it always blocked when
``current_usage >= monthly_limit``, even for tenants paying the provider
directly. UI advertised unmetered, backend silently blocked.

Fix (2026-05-22): canonical helper ``app.shared.services.byok_detector.is_byok_active``
+ a new ``byok_active`` kwarg on ``check_credit_budget`` that, when True, switches
the gate to track-only mode. This sensor pins the canonical contract so a future
refactor cannot regress.

Checks
------
1. ``app/shared/services/ai_credit_gate.py`` MUST import ``is_byok_active``
   (lazy import inside function body counts).
2. ``check_credit_budget`` MUST accept a ``byok_active`` keyword parameter.
3. ``check_credit_budget`` MUST have a code path that returns ``{"byok": True, ...}``
   without raising ``AICreditExhausted`` (presence of ``"byok": True`` literal
   in the function body is sufficient evidence).
4. ``check_credit_budget`` MUST call ``_emit_track_only_metric`` (or the
   underlying ``byok_track_only_total`` counter) somewhere in its body to
   ensure Grafana visibility.

Exit codes
----------
- 0: all checks pass
- 1: at least one check failed (sensor BLOCKING)

Usage
-----
    python3 scripts/check_credit_gate_respects_byok.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_FILE = REPO_ROOT / "app" / "shared" / "services" / "ai_credit_gate.py"


def _fail(msg: str) -> None:
    print(f"\033[31m[BLOCKING] {msg}\033[0m", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if not GATE_FILE.exists():
        _fail(f"canonical gate file missing: {GATE_FILE}")

    source = GATE_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(GATE_FILE))

    # Check 1: byok_detector import exists somewhere (top-level or lazy)
    if "is_byok_active" not in source:
        _fail(
            "ai_credit_gate.py does NOT reference byok_detector.is_byok_active. "
            "ADR-WT-2027 requires BYOK detection in check_credit_budget. "
            "Fix: add `from app.shared.services.byok_detector import is_byok_active` "
            "and call it inside check_credit_budget."
        )

    # Find check_credit_budget function
    fn_node = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "check_credit_budget":
            fn_node = node
            break

    if fn_node is None:
        _fail("check_credit_budget function not found in ai_credit_gate.py")

    # Check 2: byok_active kwarg in signature
    arg_names: set[str] = set()
    for arg in fn_node.args.args:
        arg_names.add(arg.arg)
    for arg in fn_node.args.kwonlyargs:
        arg_names.add(arg.arg)
    if "byok_active" not in arg_names:
        _fail(
            "check_credit_budget signature missing `byok_active` parameter. "
            "ADR-WT-2027 requires explicit override for testing + track-only mode. "
            f"Found args: {sorted(arg_names)}"
        )

    fn_source = ast.get_source_segment(source, fn_node) or ""

    # Check 3: track-only branch returns byok=True
    if '"byok": True' not in fn_source and "'byok': True" not in fn_source:
        _fail(
            "check_credit_budget has no code path returning `{\"byok\": True, ...}`. "
            "Track-only mode must surface in return dict so callers can branch on it."
        )

    # Check 4: emits track-only metric
    if (
        "_emit_track_only_metric" not in fn_source
        and "byok_track_only_total" not in fn_source
    ):
        _fail(
            "check_credit_budget body does not emit byok_track_only_total counter. "
            "Grafana visibility regression risk. Fix: call _emit_track_only_metric() "
            "inside the BYOK branch."
        )

    print("\033[32m[OK] ai_credit_gate.check_credit_budget respects BYOK (4/4 checks).\033[0m")
    sys.exit(0)


if __name__ == "__main__":
    main()
