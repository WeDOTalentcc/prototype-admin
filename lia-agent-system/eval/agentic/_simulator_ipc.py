"""Tiny stdin/stdout IPC wrapper around UserSimulator.

The Playwright runner spawns this as a subprocess per scenario:

    > OPEN                    → first user turn (verbatim)
    > REPLY <json-encoded>    → next user turn, or "[END]"
    > QUIT                    → exit

Scenario JSON is passed via the AGENTIC_SCENARIO_JSON env var to keep
the stdio channel free of large payloads.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Make the user_simulator module importable whether we are launched as a
# script or as a module.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

from user_simulator import UserSimulator  # type: ignore  # noqa: E402


def main() -> None:
    raw = os.environ.get("AGENTIC_SCENARIO_JSON", "")
    if not raw:
        sys.stderr.write("AGENTIC_SCENARIO_JSON env var missing\n")
        sys.exit(2)
    try:
        scenario = json.loads(raw)
    except Exception as exc:
        sys.stderr.write(f"Invalid scenario JSON: {exc}\n")
        sys.exit(2)

    sim = UserSimulator(scenario)

    def emit(line: str) -> None:
        sys.stdout.write((line or "[END]").replace("\n", " ").strip() + "\n")
        sys.stdout.flush()

    for raw_line in sys.stdin:
        cmd = raw_line.strip()
        if cmd == "QUIT":
            return
        if cmd == "OPEN":
            emit(sim.opening_turn() or "[END]")
            continue
        if cmd.startswith("REPLY "):
            try:
                lia_text = json.loads(cmd[len("REPLY "):])
            except Exception:
                lia_text = cmd[len("REPLY "):]
            nxt = sim.respond_to(lia_text)
            emit(nxt if nxt is not None else "[END]")
            continue
        emit("[ERR] unknown command")


if __name__ == "__main__":
    main()
