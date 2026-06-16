"""
Persona Diagnostic — Runner

Authenticates as the demo recruiter (auto-generated JWT signed with the
backend's SECRET_KEY) and fires every probe at POST /api/v1/chat. The
backend's CascadedRouter is what actually picks the specialised agent;
we only set scope/page hints per the probe's `agent` target so routing
gets a useful nudge.

The captured response is returned untouched. All scoring happens later
in `judge.py` using the LLM-as-judge.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[3]  # lia-agent-system/
sys.path.insert(0, str(REPO_ROOT))

DEFAULT_URL = os.getenv("LIA_BACKEND_URL", "http://localhost:8001")
DEMO_USER_ID = "13cf82fb-f1f6-4205-9377-758e59040148"
DEMO_COMPANY_ID = "00000000-0000-4000-a000-000000000001"


def make_recruiter_token() -> str:
    """JWT signed with the running backend's SECRET_KEY."""
    env_token = os.getenv("LIA_TEST_TOKEN")
    if env_token:
        return env_token
    try:
        import jwt as _jwt
        from app.core.config import settings as _settings  # type: ignore

        payload = {
            "sub": DEMO_USER_ID,
            "email": "demo@wedotalent.cc",
            "company_id": DEMO_COMPANY_ID,
            "type": "access",
            "exp": 1798675200,
        }
        return _jwt.encode(payload, _settings.SECRET_KEY, algorithm="HS256")
    except Exception as exc:  # pragma: no cover - fail loud
        raise RuntimeError(
            f"Could not auto-generate test JWT (SECRET_KEY unreadable): {exc}. "
            "Set LIA_TEST_TOKEN explicitly."
        ) from exc


def _build_chat_body(probe: dict, conversation_id: str) -> dict:
    ctx = probe.get("context") or {}
    return {
        "content": probe["prompt"],
        "conversation_id": conversation_id,
        "context": {
            "scope": ctx.get("scope") or "global",
            "page": ctx.get("page") or "home",
            "entity_id": None,
            "entity_type": None,
            "test_case_id": probe["id"],
            "agent_target": probe["agent"],
        },
    }


def _extract_text(data: Any) -> str:
    if not isinstance(data, dict):
        return str(data)[:2000]
    candidates = [
        data.get("response"),
        data.get("content"),
        (data.get("message") or {}).get("content") if isinstance(data.get("message"), dict) else None,
        ((data.get("data") or {}).get("message") or {}).get("content")
        if isinstance(data.get("data"), dict) else None,
    ]
    for c in candidates:
        if c and isinstance(c, str):
            return c
    return ""


def _extract_agent(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None
    # Explicit routing keys only — `domain` is the page context, not the
    # answering agent, so we deliberately exclude it to avoid false matches.
    keys = ("agent", "agent_name", "routed_agent", "active_agent", "specialist")
    # Top-level, then a few common nested containers the chat API uses.
    candidates: list[Any] = [data]
    for nest in ("metadata", "routing", "data", "result"):
        nested = data.get(nest)
        if isinstance(nested, dict):
            candidates.append(nested)
            inner = nested.get("message") if isinstance(nested.get("message"), dict) else None
            if inner:
                candidates.append(inner)
    # `POST /api/v1/chat` returns ChatResponse{message: MessageResponse, ...}
    # and the routed specialist is echoed inside `message.message_metadata`
    # (Task #552). Descend into both so we don't miss it.
    msg = data.get("message") if isinstance(data.get("message"), dict) else None
    if msg:
        candidates.append(msg)
        meta = msg.get("message_metadata") if isinstance(msg.get("message_metadata"), dict) else None
        if meta:
            candidates.append(meta)
    # Iterate keys outermost so explicit `agent` always wins over weaker
    # signals like `specialist` even when they appear in different containers.
    for key in keys:
        for c in candidates:
            v = c.get(key)
            if isinstance(v, str) and v.strip():
                return v
    return None


async def _call_chat(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    body: dict,
    timeout: float,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    t0 = time.monotonic()
    try:
        resp = await client.post(
            f"{base_url}/api/v1/chat", json=body, headers=headers, timeout=timeout
        )
        latency_ms = round((time.monotonic() - t0) * 1000)
    except httpx.TimeoutException:
        return {"ok": False, "status_code": 0, "latency_ms": -1, "response": "", "error": "TIMEOUT"}
    except Exception as exc:
        return {"ok": False, "status_code": 0, "latency_ms": -1, "response": "", "error": str(exc)}

    if resp.status_code != 200:
        return {
            "ok": False,
            "status_code": resp.status_code,
            "latency_ms": latency_ms,
            "response": "",
            "error": resp.text[:500],
        }

    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    return {
        "ok": True,
        "status_code": 200,
        "latency_ms": latency_ms,
        "response": _extract_text(data),
        "agent_observed": _extract_agent(data),
        "raw": data,
    }


async def run_probes(
    probes: list[dict],
    base_url: str = DEFAULT_URL,
    token: str | None = None,
    timeout: float = 60.0,
    progress: bool = True,
    on_result: Any = None,
) -> list[dict]:
    """Execute every probe sequentially against /api/v1/chat.

    Each probe runs in its own conversation_id to avoid cross-contamination.
    """
    token = token or make_recruiter_token()
    results: list[dict] = []
    async with httpx.AsyncClient() as client:
        for i, probe in enumerate(probes, 1):
            conv_id = str(uuid.uuid4())
            body = _build_chat_body(probe, conv_id)
            outcome = await _call_chat(client, base_url, token, body, timeout)

            entry = {
                "id": probe["id"],
                "category": probe["category"],
                "agent": probe["agent"],
                "criticality": probe["criticality"],
                "criticality_num": probe.get("criticality_num", 1),
                "prompt": probe["prompt"],
                "expected": probe["expected"],
                "context": probe.get("context") or {},
                "response": outcome.get("response", ""),
                "agent_observed": outcome.get("agent_observed"),
                "latency_ms": outcome.get("latency_ms", -1),
                "ok": outcome.get("ok", False),
                "status_code": outcome.get("status_code"),
                "error": outcome.get("error"),
                "conversation_id": conv_id,
            }
            results.append(entry)
            if on_result:
                try:
                    on_result(entry, results)
                except Exception:
                    pass
            if progress:
                tag = "✓" if entry["ok"] and entry["response"] else ("⚠" if entry["ok"] else "✗")
                msg = entry["response"][:60].replace("\n", " ") if entry["response"] else (entry.get("error") or "")
                print(
                    f"  [{i:3d}/{len(probes)}] {tag} {entry['id']:<10} "
                    f"{entry['agent']:<3} {entry['latency_ms']:>5}ms  {msg[:60]}",
                    flush=True,
                )
    return results


def save_capture(results: list[dict], meta: dict, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            **meta,
            "probes_total": len(results),
            "probes_with_response": sum(1 for r in results if r.get("response")),
            "probes_with_errors": sum(1 for r in results if not r.get("ok")),
        },
        "results": results,
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
