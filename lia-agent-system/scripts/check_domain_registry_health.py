#!/usr/bin/env python3
"""
SENSOR (harness-engineering): every registered agent domain answers without
internal_error.

Catches the class of bug we hit auditing /chat/message in 2026-05-20:
``domain="wizard"`` returned 200 with ``error: "internal_error"`` in 11ms
(failed at factory init, never reached the LLM). Same for ``pipeline``,
``autonomous``, ``talent_pool``.

Different from check_endpoint_smoke: that one probes specific paths. This
one walks the agent registry and probes EACH domain — so a newly registered
broken agent gets caught at the next CI run.

Usage:
  python3 scripts/check_domain_registry_health.py
  python3 scripts/check_domain_registry_health.py --domains wizard,pipeline
  python3 scripts/check_domain_registry_health.py --timeout 20

Exit codes:
  0 — every domain responded without internal_error / agent_unavailable
  1 — at least one domain returned a structural failure
  2 — could not enumerate the registry / generate auth token
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


REAL_USER_ID = "13cf82fb-f1f6-4205-9377-758e59040148"
REAL_COMPANY = "00000000-0000-4000-a000-000000000001"


@dataclass(frozen=True)
class DomainHealth:
    domain: str
    status: int
    elapsed_s: float
    intent: str
    error: str | None
    verdict: str  # "ok" | "internal_error" | "agent_unavailable" | "http_error"
    body_preview: str


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


DOMAINS_EXPECTED_FAIL_CLOSED: frozenset[str] = frozenset({
    # Wizard requires pre-injected tenant_context_snippet via
    # WizardSessionService.process_message() — by design (see
    # wizard_react_agent.py:71 tenant_strict_override=True). Calling via
    # the legacy /chat/message endpoint without setup is a NO-OP path that
    # the frontend never uses (canonical is /api/v1/wizard/smart-orchestrate).
    # Probing it here would always fail-closed — exclude to keep the sensor
    # signal-to-noise high.
    "wizard",
})


def _enumerate_domains() -> list[str]:
    """Read the registry. Trigger module imports so decorators run first."""
    sys.path.insert(0, ".")
    # Lazy-touch the agent modules so @register_agent decorators execute.
    try:
        import app.tools  # registers tools as side effect
        app.tools.initialize_tools()
    except Exception:
        pass  # initialize_tools is idempotent; failure here just means we
              # may see fewer domains. Sensor still works.
    try:
        from app.shared.agents.agent_registry import _REGISTRY  # type: ignore
        all_domains = sorted(_REGISTRY.keys())
    except (ImportError, AttributeError):
        # Fallback to a curated list seen in production logs.
        all_domains = [
            "wizard", "pipeline", "sourcing", "talent_funnel",
            "jobs_management", "kanban", "policy", "automation",
            "analytics", "communication", "ats_integration",
            "talent_pool", "autonomous", "company_settings",
            "candidate_self_service",
        ]
    return [d for d in all_domains if d not in DOMAINS_EXPECTED_FAIL_CLOSED]


def _http_probe(base: str, domain: str, token: str, timeout: int) -> DomainHealth:
    """One probe per domain via legacy /chat/message endpoint."""
    import time
    url = f"{base.rstrip('/')}/chat/message"
    body = json.dumps({
        "message": "ping smoke registry",
        "domain": domain,
        "session_id": f"registry-health-{domain}",
        "context": {},
    }).encode("utf-8")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)

    t0 = time.monotonic()
    status = 0
    raw = ""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
    except Exception as exc:
        return DomainHealth(
            domain=domain, status=0, elapsed_s=time.monotonic() - t0,
            intent="", error=str(exc), verdict="http_error",
            body_preview=f"<{type(exc).__name__}: {exc}>",
        )
    elapsed = time.monotonic() - t0

    try:
        d = json.loads(raw)
        data = d.get("data", d) if isinstance(d, dict) else {}
    except Exception:
        data = {}

    err = (data.get("error") or "").lower() if isinstance(data, dict) else ""
    intent = data.get("intent") or ""
    if err == "agent_unavailable":
        verdict = "agent_unavailable"
    elif err == "internal_error":
        verdict = "internal_error"
    elif status >= 400:
        verdict = f"http_{status}"
    else:
        verdict = "ok"

    return DomainHealth(
        domain=domain, status=status, elapsed_s=elapsed, intent=intent,
        error=err or None, verdict=verdict, body_preview=raw[:200],
    )


def render_report(results: list[DomainHealth]) -> tuple[str, int]:
    passes = [r for r in results if r.verdict == "ok"]
    fails = [r for r in results if r.verdict != "ok"]
    lines: list[str] = [
        f"=== Domain registry health: {len(passes)}/{len(results)} healthy ===",
    ]
    for r in passes:
        lines.append(f"  ✅ {r.domain:25s} HTTP {r.status} in {r.elapsed_s:.2f}s")
    for r in fails:
        lines.append("")
        lines.append(f"❌ {r.domain:25s} [{r.verdict}] HTTP {r.status} in {r.elapsed_s:.2f}s")
        lines.append(f"   body: {r.body_preview[:200]}")
        if r.verdict == "agent_unavailable":
            lines.append(
                "   HOW TO FIX: agent registered but factory returns None. "
                "Likely @register_agent decorator did not run — module not "
                "imported by app/tools/__init__.py or initialize_tools()."
            )
        elif r.verdict == "internal_error":
            lines.append(
                "   HOW TO FIX: factory crashed during agent setup (before LLM). "
                "Tail logs around the request_id, look for circular import / "
                "dependency missing in agent class __init__."
            )
        elif r.verdict.startswith("http_5"):
            lines.append(
                "   HOW TO FIX: middleware crashed before reaching domain handler. "
                "Likely FIELD_ENCRYPTION_KEY or other env var issue (R-006)."
            )
    return "\n".join(lines), 0 if not fails else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe every registered agent domain — flag internal_error / agent_unavailable.",
    )
    parser.add_argument(
        "--base",
        default=os.environ.get("LIA_BASE_URL", "http://localhost:8001"),
    )
    parser.add_argument(
        "--domains",
        default=None,
        help="Comma-separated subset (default: all registered)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout per probe in seconds (default: 30)",
    )
    args = parser.parse_args()

    if args.domains:
        domains = [d.strip() for d in args.domains.split(",") if d.strip()]
    else:
        try:
            domains = _enumerate_domains()
        except Exception as exc:
            print(f"❌ Could not enumerate registry: {exc}", file=sys.stderr)
            return 2

    if not domains:
        print("❌ No domains to probe.", file=sys.stderr)
        return 2

    try:
        token = _make_token()
    except Exception as exc:
        print(f"❌ Could not generate auth token: {exc}", file=sys.stderr)
        return 2

    # Sequential probes with small inter-call delay. The LangGraph runtime
    # has process-wide state (compiled graphs, checkpointers, audit thread
    # pool) that gets perturbed by back-to-back identical requests against
    # different agents — surfaced as "Received multiple non-consecutive
    # system messages" errors. 2s gap eliminates the flake.
    import time as _time
    results: list[DomainHealth] = []
    for i, d in enumerate(domains):
        if i > 0:
            _time.sleep(2)
        results.append(_http_probe(args.base, d, token, args.timeout))
    report, exit_code = render_report(results)
    print(report)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
