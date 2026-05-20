#!/usr/bin/env python3
"""
SENSOR (harness-engineering): canonical endpoints accept-or-reject-cleanly.

Production rule: every endpoint in the canonical list MUST respond with
either:
  - 2xx (happy path),
  - or 4xx with a structured JSON error body (auth, validation, etc),
but NEVER:
  - HTTP 500 (server crashed; means a bug we did not predict),
  - HTTP 200 with body containing the literal token "internal_error" (means
    the handler caught an exception silently and pretended success).

Same shape we hit in 2026-05-20: `/api/v1/chat` returned 500 due to
FIELD_ENCRYPTION_KEY; `domain="wizard"` in /chat/message returned 200 but
with `error: "internal_error"` (silent failure pretending success).

Usage:
  python3 scripts/check_endpoint_smoke.py
  python3 scripts/check_endpoint_smoke.py --base http://localhost:8001

Exit codes:
  0 — all endpoints in the canonical bag responded acceptably
  1 — at least one endpoint returned HTTP 500 or silent internal_error
  2 — could not generate auth token / could not reach base URL
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


REAL_USER_ID = "13cf82fb-f1f6-4205-9377-758e59040148"
REAL_COMPANY = "00000000-0000-4000-a000-000000000001"


@dataclass(frozen=True)
class Probe:
    """One endpoint to smoke-test."""
    method: str
    path: str
    body: dict[str, Any] | None
    description: str
    expect_codes: tuple[int, ...] = (200, 201, 400, 401, 403, 404, 422)


CANONICAL_PROBES: tuple[Probe, ...] = (
    Probe("GET", "/api/v1/health/live", None, "Liveness probe", (200, 401)),
    Probe(
        "POST", "/api/v1/wizard/smart-orchestrate",
        {
            "message": "smoke test ping",
            "current_stage": "input-evaluation",
            "collected_data": {},
            "conversation_history": [],
            "conversation_id": "smoke-canonical",
        },
        "Wizard canonical entry point (R-009)",
    ),
    Probe(
        "POST", "/api/v1/wizard/smart-orchestrate",
        {
            "message": "x",
            "approval_decision": "approved",
            "conversation_id": "smoke-hitl-422",
        },
        "Wizard HITL validator (R-009): expects 422",
        (422,),
    ),
    Probe(
        "POST", "/chat/message",
        {"message": "ping", "domain": "auto", "session_id": "smoke"},
        "Legacy chat fallback",
    ),
    Probe(
        "POST", "/api/v1/calibration/start",
        {},
        "Calibration full session (expects 422 missing fields)",
        (422,),
    ),
    Probe(
        "GET", "/api/v1/calibration/dashboard", None,
        "Calibration dashboard",
    ),
    Probe(
        "GET", "/api/v1/calibration/weights", None,
        "Calibration weights (touches calibration_weights.company_id)",
    ),
    Probe(
        "POST", "/api/v1/search/calibration/start",
        {"vacancy_id": "smoke", "sample_size": 3},
        "Candidate search calibration",
    ),
)


def _make_token() -> str:
    sys.path.insert(0, ".")
    from datetime import timedelta
    from app.auth.security import create_access_token
    return create_access_token(
        subject=REAL_USER_ID,
        role="recruiter",
        company_id=REAL_COMPANY,
        expires_delta=timedelta(hours=1),
    )


def _http_call(base: str, probe: Probe, token: str) -> tuple[int, str]:
    url = f"{base.rstrip('/')}{probe.path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = json.dumps(probe.body).encode("utf-8") if probe.body is not None else None
    req = urllib.request.Request(url, data=data, method=probe.method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, body_text
    except Exception as exc:
        return 0, f"<connection error: {type(exc).__name__}: {exc}>"


def _is_silent_internal_error(status: int, body: str) -> bool:
    """HTTP 200 + body claims internal_error → silent failure anti-pattern."""
    if status != 200:
        return False
    try:
        d = json.loads(body)
        data = d.get("data", d) if isinstance(d, dict) else {}
        err = (data.get("error") or "").lower() if isinstance(data, dict) else ""
        return "internal_error" in err
    except Exception:
        return False


def render_report(results: list[tuple[Probe, int, str, str]]) -> tuple[str, int]:
    failures = []
    passes = []
    for probe, status, body, verdict in results:
        if verdict == "pass":
            passes.append((probe, status))
        else:
            failures.append((probe, status, body, verdict))

    lines: list[str] = [f"=== {len(results)} probes — {len(passes)} pass, {len(failures)} fail ==="]
    for probe, status, body, verdict in failures:
        lines.append("")
        lines.append(f"❌ [{verdict}] {probe.method} {probe.path}")
        lines.append(f"   description: {probe.description}")
        lines.append(f"   got HTTP {status}, expected one of {list(probe.expect_codes)}")
        lines.append(f"   body (truncated): {body[:300]}")
        if status == 500:
            lines.append(
                "   HOW TO FIX: tail /tmp/lia-backend-stdout.log around the request_id"
                " above to find the unhandled exception. Wrap with structured error"
                " handler (R-003) or fix root cause."
            )
        elif verdict == "silent_internal_error":
            lines.append(
                "   HOW TO FIX: anti-pattern. The handler caught an exception and"
                " returned 200 with `error: internal_error` instead of surfacing it."
                " See R-003 (Exception handling discipline)."
            )
    if not failures:
        lines.append("✅ All canonical endpoints respond acceptably (no 500, no silent internal_error).")
    return "\n".join(lines), 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test canonical endpoints — no 500, no silent internal_error.",
    )
    parser.add_argument(
        "--base",
        default=os.environ.get("LIA_BASE_URL", "http://localhost:8001"),
        help="Backend base URL (default: http://localhost:8001)",
    )
    args = parser.parse_args()

    try:
        token = _make_token()
    except Exception as exc:
        print(f"❌ Could not generate auth token: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    results: list[tuple[Probe, int, str, str]] = []
    for probe in CANONICAL_PROBES:
        status, body = _http_call(args.base, probe, token)
        if status == 500:
            verdict = "http_500"
        elif _is_silent_internal_error(status, body):
            verdict = "silent_internal_error"
        elif status not in probe.expect_codes:
            verdict = f"unexpected_status_{status}"
        else:
            verdict = "pass"
        results.append((probe, status, body, verdict))

    report, exit_code = render_report(results)
    print(report)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
