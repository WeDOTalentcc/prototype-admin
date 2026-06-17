#!/usr/bin/env python3
"""Cross-stack sensor: backend WS event serializers ↔ frontend StreamingEventType.

Guards the WS event contract (registered 2026-06-03): every event type emitted by
the backend via ``serialize_event("<type>", ...)`` in
``app/shared/chat_event_serializer.py`` MUST have a counterpart in the frontend
union ``StreamingEventType`` (``plataforma-lia/src/hooks/ai/use-agent-streaming.ts``)
— or be listed in ``IGNORED`` with a reason. Prevents the recurring class of bug
where the backend emits a frame the frontend silently drops (or renames).

Scope (deliberately narrow to stay low-false-positive — see harness-engineering
"MEDIR o sensor antes de medir o código"): only events produced through the
canonical ``serialize_*`` helpers are checked. Events emitted as inline
``{"type": ...}`` dicts in handlers (plan_progress, wizard_stage, clarification,
ping/pong, approval_*) are out of scope for v1 and tracked separately.

Direction: BACKEND → FRONTEND only. Extra entries in the FE union (e.g.
plan_progress, approval_required) are fine and not flagged.

Usage:
  python3 scripts/check_ws_event_contract.py            # warn-only (exit 0)
  python3 scripts/check_ws_event_contract.py --blocking  # exit 1 on violations
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# lia-agent-system/scripts/ -> repo root is two parents up; plataforma-lia is a
# sibling of lia-agent-system under the workspace root.
_THIS = Path(__file__).resolve()
_LIA = _THIS.parents[1]  # lia-agent-system/
_WORKSPACE = _LIA.parent  # /home/runner/workspace
_SERIALIZER = _LIA / "app" / "shared" / "chat_event_serializer.py"
_FE_UNION = (
    _WORKSPACE / "plataforma-lia" / "src" / "hooks" / "ai" / "use-agent-streaming.ts"
)

# Backend serialized events that intentionally have no FE union entry.
IGNORED: dict[str, str] = {
    "connected": "handshake WS — não é renderizado, consumido implicitamente",
}


def backend_events() -> set[str]:
    src = _SERIALIZER.read_text(encoding="utf-8")
    return set(re.findall(r"""serialize_event\(\s*["']([a-z_]+)["']""", src))


def frontend_union() -> set[str]:
    src = _FE_UNION.read_text(encoding="utf-8")
    m = re.search(r"StreamingEventType\s*=\s*(.+?)\n\n", src, re.DOTALL)
    block = m.group(1) if m else src
    return set(re.findall(r"""[|=]\s*['"]([a-z_]+)['"]""", block))


def main() -> int:
    blocking = "--blocking" in sys.argv
    be = backend_events()
    fe = frontend_union()
    if not be:
        print("[check_ws_event_contract] ⚠ nenhum serialize_event encontrado — "
              f"o serializer mudou de forma? ({_SERIALIZER})")
        return 1 if blocking else 0
    if not fe:
        print("[check_ws_event_contract] ⚠ union StreamingEventType não parseado — "
              f"o arquivo FE mudou de forma? ({_FE_UNION})")
        return 1 if blocking else 0

    violations = sorted(be - fe - set(IGNORED))
    if not violations:
        print(f"✓ check_ws_event_contract: 0 violations "
              f"({len(be)} eventos backend ↔ {len(fe)} no union FE)")
        return 0

    for ev in violations:
        print(
            f"[check_ws_event_contract] '{ev}' é emitido por "
            f"serialize_event('{ev}', ...) em chat_event_serializer.py mas NÃO existe "
            f"no union StreamingEventType (use-agent-streaming.ts).\n"
            f"  → Fix: adicionar | '{ev}' ao union StreamingEventType E tratar o evento "
            f"em useChatSocket.ts (ou registrar em IGNORED do sensor com motivo)."
        )
    print(f"\n{len(violations)} violation(s).")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
