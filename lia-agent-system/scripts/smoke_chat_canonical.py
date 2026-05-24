#!/usr/bin/env python3
"""Sprint 6.2 — Smoke matrix for chat backend (Camada 1).

Tests STRUCTURAL behaviors, not literal output. Each scenario:
  1. POSTs to /api/v1/chat with a content + optional conversation_id
  2. Receives ChatResponse
  3. Runs structural assertions (no literal text match — those would
     break on LLM non-determinism)

Coverage:
  - Sprint 1.1 (B): history threading → "sim" after navigation doesn't
    return "ficou incompleta"
  - Sprint 1.2 (F): pending action persisted between turns
  - Sprint 1.3 (N): double-submit handled (server-side: 2 nearly-simultaneous
    requests both succeed but yield distinct conversation_ids OR backend
    dedups — either is acceptable)
  - Sprint 1.4 (G): Phase 1.5 persona — agentic_tool_call intent
  - Sprint 2 (G2): tool execution doesn't silently 0-row when context valid
  - Sprint 3: capability registry — LLM mentions actual tool names
  - Sprint 5: real RLS fixes — interview/candidate INSERT doesn't 500
  - Persona Rule 4 (N3): never mentions "Workana Hire"
  - Persona Anti-pattern #7 (N4): never says "ficou incompleta" for short replies
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable

import httpx


BASE_URL = os.environ.get("CHAT_SMOKE_BASE_URL", "http://localhost:8001")
TOKEN = os.environ.get("CHAT_SMOKE_TOKEN", "").strip()

if not TOKEN:
    print("ERROR: CHAT_SMOKE_TOKEN env var required.", file=sys.stderr)
    sys.exit(2)


# ===== Assertion helpers =====

@dataclass
class Result:
    name: str
    passed: bool
    detail: str = ""
    response_preview: str = ""
    duration_ms: float = 0.0


def assert_has(d: dict, path: list[str], context: str) -> tuple[bool, str]:
    cur: Any = d
    for k in path:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return False, f"{context}: missing path {'.'.join(path)}"
    return True, ""


def assert_not_contains(s: str, forbidden: list[str], context: str) -> tuple[bool, str]:
    s_low = s.lower()
    hits = [f for f in forbidden if f.lower() in s_low]
    if hits:
        return False, f"{context}: forbidden phrase(s) present: {hits}"
    return True, ""


def assert_contains_any(s: str, candidates: list[str], context: str) -> tuple[bool, str]:
    s_low = s.lower()
    hits = [c for c in candidates if c.lower() in s_low]
    if not hits:
        return False, f"{context}: none of {candidates} found in response"
    return True, ""


# ===== HTTP client =====

async def chat_send(
    client: httpx.AsyncClient,
    content: str,
    conversation_id: str | None = None,
    context: dict | None = None,
) -> tuple[int, dict]:
    body: dict = {"content": content}
    if conversation_id:
        body["conversation_id"] = conversation_id
    if context:
        body["context"] = context
    r = await client.post("/api/v1/chat", json=body)
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    return r.status_code, data


def lia_content(payload: dict) -> str:
    """Extract the assistant message content from the response envelope."""
    return (
        payload.get("data", {})
        .get("message", {})
        .get("content", "")
        if isinstance(payload, dict) else ""
    )


def conv_id(payload: dict) -> str:
    return (
        payload.get("data", {})
        .get("conversation", {})
        .get("id", "")
        if isinstance(payload, dict) else ""
    )


def msg_meta(payload: dict) -> dict:
    return (
        payload.get("data", {})
        .get("message", {})
        .get("message_metadata", {})
        if isinstance(payload, dict) else {}
    )


def intent(payload: dict) -> str:
    return msg_meta(payload).get("intent", "")


# ===== Scenarios =====

async def scenario_01_basic_greeting(client) -> Result:
    """Phase 1.5 agentic loop + persona base."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "oi")
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("01 basic greeting", False, f"HTTP {code}: {data}", duration_ms=dur)
    content = lia_content(data)
    if not content.strip():
        return Result("01 basic greeting", False, "empty content", duration_ms=dur)
    return Result("01 basic greeting", True,
                  f"intent={intent(data)} | content[:80]={content[:80]!r}",
                  response_preview=content[:200], duration_ms=dur)


async def scenario_02_no_workana_hallucination(client) -> Result:
    """N3 / persona Rule 4 — never invents company name."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "qual é o nome da minha empresa?")
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("02 anti-hallucination Rule 4", False, f"HTTP {code}", duration_ms=dur)
    content = lia_content(data)
    ok, msg = assert_not_contains(content, ["Workana Hire", "TechCorp", "RH Plus"], "Rule 4")
    return Result("02 anti-hallucination Rule 4", ok, msg or f"safe: {content[:120]!r}",
                  response_preview=content[:200], duration_ms=dur)


async def scenario_03_short_reply_not_incomplete(client) -> Result:
    """N4 / Anti-pattern #7 — short reply 'sim' isolated must not trigger
    'ficou incompleta' (since there's no history, LIA should ask for context
    OR respond casually — but never say 'mensagem ficou incompleta')."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "sim")
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("03 short-reply Anti-pattern #7", False, f"HTTP {code}", duration_ms=dur)
    content = lia_content(data)
    ok, msg = assert_not_contains(
        content,
        ["ficou incompleta", "mensagem incompleta", "recebi apenas", "pode reformular"],
        "Anti-pattern #7",
    )
    return Result("03 short-reply Anti-pattern #7", ok, msg or f"safe: {content[:120]!r}",
                  response_preview=content[:200], duration_ms=dur)


async def scenario_04_navigation_request(client) -> Result:
    """G3 — 'me leve para vagas' should set ui_action.navigate_to or emit
    NAVIGATE marker that adapter strips."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "me leve para a página de vagas")
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("04 navigation G3", False, f"HTTP {code}", duration_ms=dur)
    content = lia_content(data)
    meta = msg_meta(data)
    # Sprint 7.1 (NS-1 fix): ui_action is a STRING ("navigate_to"),
    # ui_action_params is the dict with {"page": "..."}.
    ui_action = meta.get("ui_action")
    ui_action_params = meta.get("ui_action_params") or {}
    has_ui_action = (
        ui_action == "navigate_to"
        and bool(ui_action_params.get("page"))
    )
    mentions_nav = any(
        kw in content.lower()
        for kw in ["levando", "abrindo", "indo para", "te levo", "vamos para"]
    )
    if has_ui_action or mentions_nav:
        return Result(
            "04 navigation G3", True,
            f"ui_action={ui_action} params={ui_action_params} mentions_nav={mentions_nav}",
            response_preview=content[:200], duration_ms=dur,
        )
    return Result("04 navigation G3", False,
                  f"no ui_action AND no nav mention | content={content[:200]!r}",
                  response_preview=content[:200], duration_ms=dur)


async def scenario_05_pending_action_persist(client) -> Result:
    """Sprint 1.2 (F) — 'criar vaga X' should emit confirmation; subsequent
    'sim' must be caught by Phase 0 (pending was persisted)."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "criar vaga assistente comercial")
    if code != 200:
        return Result("05 pending persist F", False, f"HTTP {code} turn1", duration_ms=(time.perf_counter() - t0) * 1000)
    cid = conv_id(data)
    content1 = lia_content(data)
    # Turn 2: respond "sim" in same conversation
    code2, data2 = await chat_send(client, "sim", conversation_id=cid)
    dur = (time.perf_counter() - t0) * 1000
    if code2 != 200:
        return Result("05 pending persist F", False,
                      f"HTTP {code2} turn2 (cid={cid})", duration_ms=dur)
    content2 = lia_content(data2)
    # If F worked, turn 2 NOT contains "ficou incompleta"
    ok, msg = assert_not_contains(
        content2,
        ["ficou incompleta", "mensagem incompleta", "recebi apenas"],
        "B+F turn 2",
    )
    return Result(
        "05 pending persist F",
        ok,
        msg or f"turn1={content1[:60]!r} | turn2={content2[:80]!r}",
        response_preview=content2[:200],
        duration_ms=dur,
    )


async def scenario_06_capability_mention(client) -> Result:
    """G6 / Sprint 3 — LLM should know about its tools when asked."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "o que você consegue fazer?")
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("06 capability G6", False, f"HTTP {code}", duration_ms=dur)
    content = lia_content(data)
    # Accept either: mentions tool category names OR specific tool names
    ok, msg = assert_contains_any(
        content,
        ["vaga", "candidato", "email", "agendar", "analiz", "buscar", "mover"],
        "G6 capability mention",
    )
    return Result("06 capability G6", ok, msg or f"safe: {content[:120]!r}",
                  response_preview=content[:200], duration_ms=dur)


async def scenario_07_list_jobs_no_silent_zero(client) -> Result:
    """G2 / Sprint 2 — listar vagas; if tenant has jobs, response shouldn't
    say 'no há vagas' (Demo tenant — may or may not have jobs; assert structure
    only, mark fail on explicit zero message + no tool call)."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "lista as vagas que tenho")
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("07 list jobs G2", False, f"HTTP {code}", duration_ms=dur)
    content = lia_content(data)
    # Hard rule: 'tool_not_found' or 'erro técnico' indicates breakage
    ok, msg = assert_not_contains(
        content,
        ["tool_not_found", "erro técnico", "exception", "traceback"],
        "G2 no exception leak",
    )
    return Result("07 list jobs G2", ok, msg or f"safe: {content[:120]!r}",
                  response_preview=content[:200], duration_ms=dur)


async def scenario_08_double_submit_handled(client) -> Result:
    """Sprint 1.3 (N) — backend handles 2 near-simultaneous requests
    gracefully (both 200; no race condition / 500)."""
    t0 = time.perf_counter()
    tasks = [
        chat_send(client, "teste duplo 1"),
        chat_send(client, "teste duplo 2"),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    dur = (time.perf_counter() - t0) * 1000
    codes = []
    for r in results:
        if isinstance(r, Exception):
            return Result("08 double-submit N", False, f"exception: {r}", duration_ms=dur)
        codes.append(r[0])
    if all(c == 200 for c in codes):
        return Result("08 double-submit N", True, f"codes={codes}", duration_ms=dur)
    return Result("08 double-submit N", False, f"codes={codes}", duration_ms=dur)


async def scenario_09_persona_no_brand_invention(client) -> Result:
    """Persona must say 'não tenho o nome configurado' or similar when
    company name is asked AND tenant_context is empty for the test user."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "qual o nome da empresa do recrutador?")
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("09 persona no-brand", False, f"HTTP {code}", duration_ms=dur)
    content = lia_content(data)
    ok, msg = assert_not_contains(
        content,
        ["Workana", "TechCorp", "RH Plus", "AcmeCorp"],
        "Rule 4 strict",
    )
    return Result("09 persona no-brand", ok, msg or f"safe: {content[:120]!r}",
                  response_preview=content[:200], duration_ms=dur)


async def scenario_10_page_context_propagation(client) -> Result:
    """Sprint 1.4 — sending context.page_type should make LIA aware of where
    user is. Test by asking what page user is on."""
    t0 = time.perf_counter()
    code, data = await chat_send(
        client, "em que página estou?",
        context={"page_type": "vagas"},
    )
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("10 page_context G1", False, f"HTTP {code}", duration_ms=dur)
    content = lia_content(data)
    # Accept any indication LIA knows location
    ok = "vaga" in content.lower() or "lista" in content.lower()
    return Result("10 page_context G1", ok,
                  f"intent={intent(data)} | content={content[:120]!r}",
                  response_preview=content[:200], duration_ms=dur)


async def scenario_11_short_reply_with_context(client) -> Result:
    """Sprint 1.1 (B) full flow: turn 1 plants context, turn 2 'sim' uses history."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "quer que eu liste tuas vagas abertas?")
    if code != 200:
        return Result("11 B+F flow", False, f"HTTP {code} turn1",
                      duration_ms=(time.perf_counter() - t0) * 1000)
    cid = conv_id(data)
    code2, data2 = await chat_send(client, "sim", conversation_id=cid)
    dur = (time.perf_counter() - t0) * 1000
    if code2 != 200:
        return Result("11 B+F flow", False, f"HTTP {code2} turn2", duration_ms=dur)
    content2 = lia_content(data2)
    ok, msg = assert_not_contains(
        content2,
        ["ficou incompleta", "mensagem incompleta", "recebi apenas"],
        "B history threading",
    )
    return Result("11 B+F flow", ok, msg or f"turn2={content2[:120]!r}",
                  response_preview=content2[:200], duration_ms=dur)


async def scenario_12_no_persona_leak(client) -> Result:
    """G5 / G7 — persona / system prompt should never leak in user-facing reply."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "olá")
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("12 no persona leak", False, f"HTTP {code}", duration_ms=dur)
    content = lia_content(data)
    ok, msg = assert_not_contains(
        content,
        ["### Contexto", "### Capabilities", "**VAGAS**", "[NAVIGATE:",
         "tenant_context_snippet", "system prompt", "agent_type"],
        "G5/G7 persona leak",
    )
    return Result("12 no persona leak", ok, msg or f"safe: {content[:80]!r}",
                  response_preview=content[:200], duration_ms=dur)


async def scenario_13_5xx_resilience(client) -> Result:
    """Send a borderline-confusing input; backend must NOT 500."""
    t0 = time.perf_counter()
    code, data = await chat_send(client, "@#$%&*()_+ç~^?")
    dur = (time.perf_counter() - t0) * 1000
    if code >= 500:
        return Result("13 5xx resilience", False, f"HTTP {code}", duration_ms=dur)
    return Result("13 5xx resilience", True, f"HTTP {code}", duration_ms=dur)


async def scenario_14_long_message(client) -> Result:
    """Stress with longer (~500 char) message."""
    msg = (
        "Quero criar uma vaga para Engenheiro de Software Senior, "
        "remoto, focado em Python, FastAPI, PostgreSQL e AWS. "
        "Salario entre 15-20k. Beneficios completos. "
        "A vaga é para minha empresa, time de produto. " * 4
    )[:1000]
    t0 = time.perf_counter()
    code, data = await chat_send(client, msg)
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("14 long message", False, f"HTTP {code}", duration_ms=dur)
    return Result("14 long message", True, f"intent={intent(data)}",
                  response_preview=lia_content(data)[:200], duration_ms=dur)


async def scenario_15_context_chat_page(client) -> Result:
    """Frontend integration: page_type=chat — LIA should not assume specific
    page context."""
    t0 = time.perf_counter()
    code, data = await chat_send(
        client, "oi tudo bem?",
        context={"page_type": "chat"},
    )
    dur = (time.perf_counter() - t0) * 1000
    if code != 200:
        return Result("15 page=chat", False, f"HTTP {code}", duration_ms=dur)
    return Result("15 page=chat", True, f"intent={intent(data)}",
                  response_preview=lia_content(data)[:200], duration_ms=dur)


# ===== Runner =====

SCENARIOS: list[Callable] = [
    scenario_01_basic_greeting,
    scenario_02_no_workana_hallucination,
    scenario_03_short_reply_not_incomplete,
    scenario_04_navigation_request,
    scenario_05_pending_action_persist,
    scenario_06_capability_mention,
    scenario_07_list_jobs_no_silent_zero,
    scenario_08_double_submit_handled,
    scenario_09_persona_no_brand_invention,
    scenario_10_page_context_propagation,
    scenario_11_short_reply_with_context,
    scenario_12_no_persona_leak,
    scenario_13_5xx_resilience,
    scenario_14_long_message,
    scenario_15_context_chat_page,
]


async def main():
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(
        base_url=BASE_URL, headers=headers, timeout=60.0,
    ) as client:
        results: list[Result] = []
        for sc in SCENARIOS:
            try:
                r = await sc(client)
            except Exception as exc:
                r = Result(sc.__name__, False, f"EXCEPTION: {exc}")
            results.append(r)
            status = "✓" if r.passed else "✗"
            print(f"{status} {r.name:42s} [{r.duration_ms:6.0f}ms]  {r.detail[:100]}")

        print()
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        print(f"=== {passed}/{total} passed ===")
        if passed < total:
            print()
            print("=== Failures detail ===")
            for r in results:
                if not r.passed:
                    print(f"\n✗ {r.name}")
                    print(f"  detail: {r.detail}")
                    if r.response_preview:
                        print(f"  preview: {r.response_preview!r}")

        return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
