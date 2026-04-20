"""
Pure-Python agentic eval runner — no browser required.

Connects to the LIA backend via WebSocket at:
  ws://127.0.0.1:5000/api/v1/ws/chat/{session_id}?token={JWT}

Uses the same UserSimulator as the Playwright runner and produces
output in the exact same JSON format so judge_agentic.py works
without changes.

Usage:
  python3 run_agentic_api.py               # all 66 scenarios
  python3 run_agentic_api.py --smoke       # 11 @smoke scenarios only
  python3 run_agentic_api.py --dim d1      # scenarios tagged d1
  python3 run_agentic_api.py --id AGT-D01-001  # single scenario
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jwt
import yaml
import websockets

# ── repo roots ────────────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent  # lia-agent-system/
sys.path.insert(0, str(_REPO))

from eval.agentic.user_simulator import UserSimulator  # noqa: E402

# ── configuration ─────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("LIA_SECRET_KEY", "change-this-in-production")
ALGORITHM = "HS256"
DEMO_COMPANY_ID = "00000000-0000-4000-a000-000000000001"
DEMO_USER_ID = "e2e-eval-user"

WS_BASE = os.environ.get("LIA_WS_BASE", "ws://127.0.0.1:5000")
SCENARIOS_DIR = _HERE.parent / "agentic_cases"
RUNS_DIR = _HERE / "runs"

PASS_K = int(os.environ.get("AGENTIC_PASS_K", "1"))
MAX_TURNS = 8
TURN_TIMEOUT_S = 90
CONNECT_TIMEOUT_S = 15

PRINT_BANNER = True


# ── auth ──────────────────────────────────────────────────────────────────────
def _make_jwt() -> str:
    return jwt.encode(
        {
            "sub": DEMO_USER_ID,
            "company_id": DEMO_COMPANY_ID,
            "role": "admin",
            "exp": int(time.time()) + 7200,
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ── scenario loading ──────────────────────────────────────────────────────────
def load_scenarios(
    filter_tags: list[str] | None = None,
    filter_id: str | None = None,
    smoke_only: bool = False,
) -> list[dict]:
    scenarios: list[dict] = []
    for yaml_file in sorted(SCENARIOS_DIR.glob("*.yaml")):
        doc = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        for sc in doc.get("scenarios", []):
            tags = sc.get("tags", [])
            if smoke_only and "smoke" not in tags:
                continue
            if filter_tags and not any(t in tags for t in filter_tags):
                continue
            if filter_id and sc.get("id") != filter_id:
                continue
            scenarios.append(sc)
    return scenarios


# ── tool call extraction ───────────────────────────────────────────────────────
def _extract_tools_from_msg(msg: dict) -> list[str]:
    """Extract tool names from a WebSocket message.

    The LIA backend sends tool calls in the 'actions' field:
      actions = [{'action_type': 'call_tool', 'params': {'tool': 'list_jobs'}, ...}]
    Panel updates may also signal tool usage via panel_type.
    """
    tools: list[str] = []
    # Primary: actions field
    for action in msg.get("actions") or []:
        if isinstance(action, dict):
            if action.get("action_type") == "call_tool":
                tool = action.get("params", {}).get("tool") or action.get("tool")
                if tool:
                    tools.append(tool)
            elif action.get("tool"):
                tools.append(action["tool"])
    # Secondary: panel_update → panel_type maps to some tools
    if msg.get("type") == "panel_update":
        panel = msg.get("panel_type", "")
        if panel:
            tools.append("panel:" + panel)
    return tools


# ── WebSocket session ─────────────────────────────────────────────────────────
async def run_scenario(scenario: dict, token: str, run_index: int) -> dict:
    sc_id = scenario["id"]
    page = scenario.get("page_context", {}).get("page", "chat")
    scope = scenario.get("page_context", {}).get("scope", "global")
    domain_map = {
        "chat": "recruiter_assistant",
        "pipeline": "kanban",
        "sourcing": "sourcing",
    }
    domain = domain_map.get(page, "recruiter_assistant")

    session_id = "eval-" + sc_id.lower().replace("-", "") + "-" + uuid.uuid4().hex[:8]
    url = (
        WS_BASE.rstrip("/")
        + "/api/v1/ws/chat/"
        + session_id
        + "?token=" + token
        + "&domain=" + domain
    )

    sim = UserSimulator(scenario)
    transcript: list[dict] = []
    all_tools: list[str] = []
    errored: str | None = None
    run_start = time.monotonic()

    try:
        async with websockets.connect(url, open_timeout=CONNECT_TIMEOUT_S) as ws:
            # Turn loop
            user_msg = sim.opening_turn()
            for turn_num in range(MAX_TURNS):
                if not user_msg or user_msg == "[END]":
                    break

                turn_start = time.monotonic()
                await ws.send(json.dumps({
                    "type": "message",
                    "content": user_msg,
                    "context": {"company_id": DEMO_COMPANY_ID},
                }))

                # Collect all messages until the 'message' type arrives
                lia_text = ""
                turn_tools: list[str] = []
                deadline = time.monotonic() + TURN_TIMEOUT_S
                while time.monotonic() < deadline:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 5))
                    except asyncio.TimeoutError:
                        continue
                    msg = json.loads(raw)
                    mtype = msg.get("type", "")
                    turn_tools.extend(_extract_tools_from_msg(msg))
                    if mtype == "message":
                        lia_text = msg.get("content", "")
                        break
                    if mtype == "error":
                        lia_text = "[ERROR] " + msg.get("message", "backend error")
                        break
                    if mtype == "clarification":
                        lia_text = msg.get("question", "") + " " + str(msg.get("options", ""))
                        break
                    # background_task_update may carry tool info
                    if mtype == "background_task_update":
                        task_type = msg.get("task_type", "")
                        if task_type:
                            turn_tools.append("bg:" + task_type)

                dur_ms = int((time.monotonic() - turn_start) * 1000)
                transcript.append({
                    "user": user_msg,
                    "lia": lia_text,
                    "durationMs": dur_ms,
                    "observedTools": [{"name": t, "ok": True, "status": 200} for t in turn_tools],
                })
                all_tools.extend(turn_tools)

                print(
                    f"  [{sc_id}#{run_index}] turn {turn_num+1}: "
                    f"{len(turn_tools)} tools, {dur_ms}ms",
                    flush=True,
                )

                # Get next user message from simulator
                user_msg = sim.respond_to(lia_text)

    except asyncio.TimeoutError:
        errored = "Connection timeout"
    except Exception as exc:
        errored = str(exc)

    total_ms = int((time.monotonic() - run_start) * 1000)
    status = "✘ " if errored else "✓ "
    print(
        f"  {status}{sc_id}#{run_index} "
        f"({len(transcript)} turns, {len(all_tools)} tool calls, {total_ms}ms)",
        flush=True,
    )

    return {
        "scenario_id": sc_id,
        "run_index": run_index,
        "page": page,
        "scope": scope,
        "goal": scenario.get("goal", ""),
        "setup_notes": scenario.get("setup_notes", ""),
        "severity": scenario.get("severity", "normal"),
        "tags": scenario.get("tags", []),
        "expected_tools": scenario.get("expected_tools", []),
        "expected_proactive_actions": scenario.get("expected_proactive_actions", []),
        "expected_state_after": scenario.get("expected_state_after", []),
        "transcript": transcript,
        "observed_tools": [{"name": t, "ok": True, "status": 200} for t in all_tools],
        "total_turns": len(transcript),
        "total_duration_ms": total_ms,
        **({"errored": errored} if errored else {}),
    }


# ── main ──────────────────────────────────────────────────────────────────────
async def main(args: argparse.Namespace) -> None:
    scenarios = load_scenarios(
        filter_tags=args.dim,
        filter_id=args.id,
        smoke_only=args.smoke,
    )
    if not scenarios:
        print("No scenarios matched. Check --smoke / --dim / --id flags.", flush=True)
        sys.exit(1)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    out_path = RUNS_DIR / ("agentic-" + ts + ".json")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    if PRINT_BANNER:
        print("", flush=True)
        print("=" * 40, flush=True)
        print(f"Agentic Eval (API mode) — {len(scenarios)} scenarios, pass^k={PASS_K}", flush=True)
        print(f"Run: {ts}", flush=True)
        print(f"Output: {out_path}", flush=True)
        print("=" * 40, flush=True)
        print("", flush=True)

    token = _make_jwt()
    results: list[dict] = []

    for i, scenario in enumerate(scenarios):
        for k in range(PASS_K):
            result = await run_scenario(scenario, token, k)
            results.append(result)

    output = {
        "meta": {
            "base_url": WS_BASE,
            "pass_k": PASS_K,
            "scenarios_run": len(scenarios),
            "scenarios_total": 66,
            "timestamp": ts,
            "runner": "api",
        },
        "results": results,
    }
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    n_ok = sum(1 for r in results if not r.get("errored") and r["total_turns"] > 0)
    n_err = sum(1 for r in results if r.get("errored"))
    print("", flush=True)
    print("=" * 40, flush=True)
    print(f"Captured {len(results)} runs ({n_ok} with turns, {n_err} errored)", flush=True)
    print(f"File: {out_path}", flush=True)
    print(f"Next: python3 {_HERE}/judge_agentic.py {out_path}", flush=True)
    print("=" * 40, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic eval runner (API mode)")
    parser.add_argument("--smoke", action="store_true", help="Run only @smoke scenarios")
    parser.add_argument("--dim", nargs="+", help="Filter by dimension tag (e.g. d1 d2)")
    parser.add_argument("--id", help="Run a single scenario by ID")
    args = parser.parse_args()
    asyncio.run(main(args))
