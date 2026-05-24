"""Sprint 14.2 sensor canonical — verifica TS↔Python parity em ui_action global types.

Mesma motivação que check_canonical_pages_sync.py: PR-D introduziu
GLOBAL_UI_ACTION_TYPES em duplicidade controlada (TS + Python). Sensor
previne drift entre ws_message_schemas.py e ui-action.ts.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
PYTHON_FILE = WORKSPACE / "app" / "shared" / "websocket" / "ws_message_schemas.py"
TS_FILE = WORKSPACE.parent / "plataforma-lia" / "src" / "types" / "ui-action.ts"


def extract_python_types(src: str) -> set[str]:
    m = re.search(r"GLOBAL_UI_ACTION_TYPES.*?=\s*\((.*?)\)", src, re.DOTALL)
    if not m:
        return set()
    return set(re.findall(r'"([a-z_]+)"', m.group(1)))


def extract_ts_types(src: str) -> set[str]:
    m = re.search(r"GLOBAL_UI_ACTION_TYPES.*?=\s*\[(.*?)\]", src, re.DOTALL)
    if not m:
        return set()
    return set(re.findall(r'"([a-z_]+)"', m.group(1)))


def main() -> int:
    if not PYTHON_FILE.exists():
        print(f"Python file not found: {PYTHON_FILE}", file=sys.stderr)
        return 1
    if not TS_FILE.exists():
        print(f"TS file not found: {TS_FILE}", file=sys.stderr)
        return 1

    py_types = extract_python_types(PYTHON_FILE.read_text())
    ts_types = extract_ts_types(TS_FILE.read_text())

    only_py = py_types - ts_types
    only_ts = ts_types - py_types

    if not only_py and not only_ts:
        print(f"OK ui_action GLOBAL parity ({len(py_types)} types)")
        return 0

    print("DRIFT detectado em ui_action GLOBAL_UI_ACTION_TYPES:")
    if only_py:
        print(f"\n  Only Python: {sorted(only_py)}")
        print(f"  Fix: adicionar em {TS_FILE.relative_to(WORKSPACE.parent)}")
    if only_ts:
        print(f"\n  Only TS: {sorted(only_ts)}")
        print(f"  Fix: adicionar em {PYTHON_FILE.relative_to(WORKSPACE)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
