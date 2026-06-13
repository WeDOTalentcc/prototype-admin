#!/usr/bin/env python3
"""Sensor canonical: detecta eventos criticos publicados sem outbox.

Regra Sprint E (2026-06-13):
  Eventos criticos DEVEM usar publish_via_outbox() - nao publish_platform_event() direto.

Modo: WARN-ONLY por default. Use --block para bloquear CI.
"""
from __future__ import annotations
import ast, sys
from pathlib import Path

CRITICAL_EVENT_CLASSES = {
    "StageChangedEvent", "ScreeningCompletedEvent", "OfferSentEvent", "CandidateAppliedEvent"
}


def check(block=False):
    repo_root = Path(__file__).resolve().parent.parent
    violations = []

    for py_file in (repo_root / "app").rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        if "publish_platform_event" not in source:
            continue
        if not any(cls in source for cls in CRITICAL_EVENT_CLASSES):
            continue
        if "publish_via_outbox" in source:
            continue

        try:
            tree = ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func_name = ""
            if isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                func_name = node.func.id
            if func_name != "publish_platform_event":
                continue

            call_src = ast.unparse(node)
            if any(cls in call_src for cls in CRITICAL_EVENT_CLASSES):
                rel = str(py_file.relative_to(repo_root))
                violations.append((rel, node.lineno, call_src[:80]))

    if violations:
        print(f"[EVENTS-OUTBOX] {len(violations)} eventos criticos sem outbox:")
        for f, line, code in violations[:15]:
            print(f"  {f}:{line} -- {code}")
        print()
        print("CORRECAO: usar EventsOutboxService.publish_via_outbox(event, db)")
        print("  from app.shared.messaging.events_outbox_service import get_events_outbox_service")
        mode = "BLOCKING" if block else "WARN-ONLY"
        print(f"Mode: {mode}")
        return 1 if block else 0

    print("[EVENTS-OUTBOX] OK -- 0 eventos criticos sem outbox")
    return 0


if __name__ == "__main__":
    sys.exit(check(block="--block" in sys.argv))
