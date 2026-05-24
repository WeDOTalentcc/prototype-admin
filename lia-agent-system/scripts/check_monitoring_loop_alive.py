#!/usr/bin/env python3
"""Sprint 4.3 (M) — sensor: monitoring loop liveness check.

Imports MonitoringLoop and reads get_loop_health(). Designed to be run on
the running backend process (Replit cron or external poller) — NOT a static
code scan. Exits non-zero if the loop is stale or never started.

Usage:
    # static (will always show "never started" since loop only lives in
    # the long-running uvicorn process):
    python scripts/check_monitoring_loop_alive.py

    # Connect to running backend via HTTP healthz endpoint (preferred):
    python scripts/check_monitoring_loop_alive.py --http http://localhost:8001/api/v1/admin/monitoring/healthz

Exit codes:
    0 — loop is healthy (running + recent iteration)
    1 — loop is stale or never ran
    2 — loop is failing (consecutive_failures > threshold)
    3 — internal error / cannot read state
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _fetch_via_import() -> dict:
    """Read health by importing the in-process loop singleton.
    Only meaningful when run INSIDE the uvicorn process (e.g. from a backend
    admin endpoint handler). Outside, will report 'never ran' which is correct
    for a fresh process but not for ops monitoring.
    """
    sys.path.insert(0, str(REPO_ROOT))
    os.environ.setdefault("DATABASE_URL", "postgresql://stub/stub")
    from app.domains.recruiter_assistant.services.monitoring_loop import monitoring_loop
    return monitoring_loop.get_loop_health()


def _fetch_via_http(url: str) -> dict:
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"FAIL: HTTP fetch error: {e}", file=sys.stderr)
        sys.exit(3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--http", help="HTTP URL of monitoring healthz endpoint")
    parser.add_argument("--max-consecutive-failures", type=int, default=3,
                        help="exit 2 if consecutive_failures > N (default 3)")
    parser.add_argument("--allow-not-started", action="store_true",
                        help="exit 0 if iteration_count == 0 (initial boot)")
    parser.add_argument("--json", action="store_true",
                        help="emit raw JSON")
    args = parser.parse_args()

    try:
        health = _fetch_via_http(args.http) if args.http else _fetch_via_import()
    except Exception as e:
        print(f"FAIL: cannot read loop state: {e}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(health, indent=2, default=str))

    iteration_count = health.get("iteration_count", 0)
    is_stale = health.get("is_stale", True)
    running = health.get("running", False)
    consecutive_failures = health.get("consecutive_failures", 0)

    # Decision tree
    if not running:
        if iteration_count == 0 and args.allow_not_started:
            if not args.json:
                print("INFO: loop not started yet (fresh boot, --allow-not-started ok)")
            return 0
        if not args.json:
            print(f"FAIL: loop is not running (iteration_count={iteration_count})")
        return 1

    if iteration_count == 0:
        if not args.json:
            print("FAIL: loop running but iteration_count=0 (never completed an iteration)")
        return 1

    if consecutive_failures > args.max_consecutive_failures:
        if not args.json:
            print(
                f"FAIL: loop is failing — consecutive_failures={consecutive_failures} "
                f"(threshold {args.max_consecutive_failures}). Last error: "
                f"{health.get('last_error')}"
            )
        return 2

    if is_stale:
        if not args.json:
            print(
                f"FAIL: loop is stale — last iteration {health.get('last_iteration_at')} "
                f"older than 2x interval ({2 * health.get('check_interval_seconds', 0)}s)"
            )
        return 1

    if not args.json:
        print(
            f"OK monitoring loop alive: iter={iteration_count} "
            f"last={health.get('last_iteration_at')} "
            f"consec_fail={consecutive_failures} interval={health.get('check_interval_seconds')}s"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
