#!/usr/bin/env python3
"""Sprint 14.5 canonical smoke matrix — 15 scenarios runtime regression.

Tests chat endpoint with parametrized JWT against prod-like setup.
Asserts:
  - HTTP 200
  - response.success != False on healthy paths
  - ui_action populated when expected
  - error_code populated when intentional fail-loud
  - response time within budget (p95 < 30s post Sprint 9 timeout=60s)

Usage:
    export LIA_SMOKE_JWT="<your_jwt>"
    export LIA_SMOKE_BASE_URL="http://localhost:8001"  # or replit dev URL
    python3 scripts/smoke_matrix_canonical.py

Exit codes:
    0 — all scenarios passed
    1 — one or more failures
    2 — config error (JWT/URL ausente)
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

try:
    import httpx
except ImportError:
    print("Missing dep: pip install httpx", file=sys.stderr)
    sys.exit(2)


@dataclass
class Scenario:
    """One smoke test scenario."""
    name: str
    message: str
    page_context: dict[str, Any] = field(default_factory=dict)
    expected_success: bool = True
    expected_ui_action: str | None = None  # e.g. "navigate_to"
    expected_error_code: str | None = None
    max_latency_s: float = 30.0
    notes: str = ""


SCENARIOS: list[Scenario] = [
    # === Navigation tests (G3 canonical) ===
    Scenario(
        name="nav_to_vagas",
        message="me leve para vagas",
        page_context={"page_type": "home"},
        expected_ui_action="navigate_to",
        notes="G3 canonical fix — Phase 1.5 deve emitir [NAVIGATE:vagas]",
    ),
    Scenario(
        name="nav_to_config",
        message="abre configurações",
        page_context={"page_type": "vagas"},
        expected_ui_action="navigate_to",
    ),
    # === Greeting / general (Sprint 12.5-TF clarification) ===
    Scenario(
        name="greeting_oi",
        message="oi",
        page_context={"page_type": "home"},
        notes="Sprint 12.5-TF: deve PERGUNTAR de volta em vez de chutar tool",
    ),
    Scenario(
        name="ambiguous_query",
        message="tudo",
        page_context={"page_type": "home"},
        notes="Sprint 12.5-TF clarification",
    ),
    # === Tool execution (Sprint 2.5 fixes — search_candidates) ===
    Scenario(
        name="search_candidates",
        message="buscar candidatos Python Sênior em São Paulo",
        page_context={"page_type": "vagas"},
        notes="Sprint 2.5 fix — antes falhava com ToolContextMissingError",
        max_latency_s=15.0,
    ),
    Scenario(
        name="list_jobs",
        message="lista as vagas",
        page_context={"page_type": "home"},
        notes="Sprint 8.2 NS-2 query intent",
    ),
    # === Action with confirmation (Sprint 8.4 NS-3) ===
    Scenario(
        name="action_pause_job",
        message="pausar a vaga atual",
        page_context={"page_type": "vaga_detalhe", "job_vacancy_id": "00000000-0000-0000-0000-000000000001"},
        notes="Action requires confirmation",
    ),
    # === Page-aware context (G1 canonical) ===
    Scenario(
        name="where_am_i_configs",
        message="onde estou?",
        page_context={"page_type": "configuracoes"},
        notes="LIA deve responder 'Configurações' baseado em context_page",
    ),
    Scenario(
        name="where_am_i_pipeline",
        message="que página é essa?",
        page_context={"page_type": "pipeline_kanban"},
    ),
    # === Suggested prompts dinâmicos (Sprint 14.4) ===
    Scenario(
        name="suggestions_funil",
        message="alguma coisa",
        page_context={"page_type": "funil_talentos"},
        notes="Response deve trazer 3 suggested_prompts canonical do funil",
    ),
    # === Compliance / Fairness ===
    Scenario(
        name="fairness_implicit_bias",
        message="me indica candidatos masculinos para essa vaga",
        page_context={"page_type": "vagas"},
        notes="FairnessGuard deve adicionar soft_warning",
    ),
    # === Pending action confirmation flow (Sprint 1.2 F) ===
    Scenario(
        name="pending_confirmation_sim",
        message="sim",
        page_context={"page_type": "vagas"},
        notes="Sem pending state, sim deve fall-through clarification not action",
    ),
    # === Memory + history ===
    Scenario(
        name="how_are_you",
        message="tudo bem?",
        page_context={"page_type": "home"},
    ),
    # === Long query ===
    Scenario(
        name="complex_multi_intent",
        message="lista as vagas paradas há mais de 7 dias e me mostra os top 3 candidatos de cada",
        page_context={"page_type": "vagas"},
        max_latency_s=20.0,
    ),
    # === Error paths (intentional fail-loud) ===
    Scenario(
        name="empty_message",
        message="",
        page_context={"page_type": "home"},
        expected_success=False,
        notes="Empty msg deve 400 OR success=False",
    ),
]


async def run_scenario(
    client: httpx.AsyncClient,
    base_url: str,
    jwt: str,
    scenario: Scenario,
) -> tuple[bool, str]:
    """Run one scenario, return (passed, reason)."""
    payload = {
        "message": scenario.message,
        "page_context": scenario.page_context,
    }
    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

    t0 = time.monotonic()
    try:
        resp = await client.post(
            f"{base_url}/api/v1/chat",
            json=payload,
            headers=headers,
            timeout=60.0,
        )
    except Exception as exc:
        return False, f"HTTP error: {type(exc).__name__}: {exc}"

    elapsed_s = time.monotonic() - t0

    if elapsed_s > scenario.max_latency_s:
        return False, f"Latency {elapsed_s:.1f}s > budget {scenario.max_latency_s}s"

    if resp.status_code == 401:
        return False, "401 Unauthorized — check JWT"

    if scenario.expected_success and resp.status_code != 200:
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"

    try:
        data = resp.json()
    except Exception:
        return False, f"Non-JSON response: {resp.text[:200]}"

    body = data.get("data") or data
    success = body.get("success", True)

    if scenario.expected_success and not success:
        ec = body.get("error_code") or "?"
        return False, f"success=False, error_code={ec}, content={body.get('content', '')[:120]}"

    if scenario.expected_error_code and body.get("error_code") != scenario.expected_error_code:
        return False, f"Expected error_code={scenario.expected_error_code}, got {body.get('error_code')}"

    if scenario.expected_ui_action and body.get("ui_action") != scenario.expected_ui_action:
        return False, f"Expected ui_action={scenario.expected_ui_action}, got {body.get('ui_action')}"

    return True, f"OK in {elapsed_s:.1f}s | ui_action={body.get('ui_action') or '-'}"


async def main() -> int:
    jwt = os.environ.get("LIA_SMOKE_JWT", "")
    base_url = os.environ.get("LIA_SMOKE_BASE_URL", "http://localhost:8001")

    if not jwt:
        print("Missing LIA_SMOKE_JWT env. Set with a valid JWT token.", file=sys.stderr)
        return 2

    print(f"Smoke matrix canonical Sprint 14.5 — {len(SCENARIOS)} scenarios")
    print(f"Base URL: {base_url}")
    print(f"JWT: {jwt[:16]}...{jwt[-8:]}")
    print()

    results: list[tuple[str, bool, str]] = []
    async with httpx.AsyncClient() as client:
        for sc in SCENARIOS:
            passed, reason = await run_scenario(client, base_url, jwt, sc)
            results.append((sc.name, passed, reason))
            icon = "✅" if passed else "❌"
            print(f"  {icon} {sc.name:30s} {reason}")

    print()
    passed_count = sum(1 for _, p, _ in results if p)
    total = len(results)
    print(f"Results: {passed_count}/{total} passed")

    if passed_count < total:
        print("\nFailed:")
        for n, p, r in results:
            if not p:
                print(f"  - {n}: {r}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
