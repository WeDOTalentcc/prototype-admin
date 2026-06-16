#!/usr/bin/env python3
"""
Task #977 — Tenant-context no-regression eval suite.

Roda prompts realistas pelo /api/v1/chat e marca como FALHA qualquer resposta
que contenha frases-sintoma do bug "LIA esquece a empresa". Asserção é puramente
NEGATIVA — a LIA pode legitimamente perguntar outras coisas, o que NUNCA pode é
pedir/citar a empresa, porque o snippet de tenant chega injetado pelo backend.

Usage:
  python tenant_context_no_regression_eval.py [--token <JWT>] [--url http://localhost:8001]
                                               [--id TCNR-WZ-001] [--verbose]

Exit codes:
  0  todos os cenários PASS
  1  um ou mais cenários FAIL (frase-sintoma detectada ou erro de transporte)
  2  erro de configuração / cases YAML inválido

Output:
  tenant_context_no_regression_<timestamp>.json — resultado por cenário
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

BASE_DIR = Path(__file__).parent
CASES_PATH = BASE_DIR / "tenant_context_no_regression_cases.yaml"
DEFAULT_URL = os.getenv("LIA_BACKEND_URL", "http://localhost:8001")


def _make_eval_token() -> str:
    """Reusa o helper canônico do eval_runner principal (mesmo SECRET_KEY)."""
    env_token = os.getenv("LIA_TEST_TOKEN")
    if env_token:
        return env_token
    sys.path.insert(0, str(BASE_DIR.parent))
    try:
        import jwt as _jwt  # type: ignore
        from app.core.config import settings as _settings  # type: ignore
        payload = {
            "sub": "13cf82fb-f1f6-4205-9377-758e59040148",
            "email": "demo@wedotalent.cc",
            "company_id": "00000000-0000-4000-a000-000000000001",
            "type": "access",
            "exp": 1798675200,
        }
        return _jwt.encode(payload, _settings.SECRET_KEY, algorithm="HS256")
    except Exception as exc:  # pragma: no cover
        print(f"[warn] falha ao auto-gerar JWT ({exc}); use --token", file=sys.stderr)
        return ""


def load_cases(filter_id: str | None = None, filter_agent: str | None = None) -> tuple[dict, list[dict]]:
    if not CASES_PATH.exists():
        raise FileNotFoundError(f"cases yaml ausente: {CASES_PATH}")
    data = yaml.safe_load(CASES_PATH.read_text())
    cases = data.get("cases", [])
    if filter_id:
        cases = [c for c in cases if c["id"] == filter_id]
    if filter_agent:
        cases = [c for c in cases if c.get("agent") == filter_agent]
    return data.get("meta", {}), cases


def build_request_body(case: dict) -> dict:
    ctx = case.get("context", {})
    return {
        "content": case["prompt"],
        "context": {
            "scope": ctx.get("scope", "global"),
            "page": ctx.get("page", "home"),
            "test_case_id": case["id"],
            "expected_agent": case.get("agent"),
        },
    }


async def call_lia(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    body: dict,
    timeout: float = 45.0,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    t0 = time.monotonic()
    try:
        resp = await client.post(
            f"{base_url}/api/v1/chat", json=body, headers=headers, timeout=timeout
        )
        latency_ms = round((time.monotonic() - t0) * 1000)
    except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as exc:
        return {"ok": False, "status_code": 0, "latency_ms": -1, "response": "", "error": str(exc)}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "status_code": 0, "latency_ms": -1, "response": "", "error": str(exc)}

    if resp.status_code != 200:
        return {
            "ok": False,
            "status_code": resp.status_code,
            "latency_ms": latency_ms,
            "response": "",
            "error": resp.text[:500],
        }
    data = resp.json()
    response_text = (
        data.get("response")
        or data.get("content")
        or (data.get("message") or {}).get("content", "")
        or ((data.get("data") or {}).get("message") or {}).get("content", "")
        or ""
    )
    return {
        "ok": True,
        "status_code": 200,
        "latency_ms": latency_ms,
        "response": response_text,
    }


def detect_forbidden_phrases(response: str, forbidden: list[str]) -> list[str]:
    """Match case-insensitive de frase-sintoma. Retorna lista de hits."""
    if not response:
        return []
    norm = response.lower()
    hits: list[str] = []
    for phrase in forbidden:
        # normaliza espaços compactos para tolerar quebras de linha
        if re.search(re.escape(phrase.lower()), norm):
            hits.append(phrase)
    return hits


async def run_case(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    case: dict,
    forbidden: list[str],
) -> dict[str, Any]:
    body = build_request_body(case)
    api = await call_lia(client, base_url, token, body)
    result: dict[str, Any] = {
        "id": case["id"],
        "agent": case.get("agent"),
        "severity": case.get("severity", "medium"),
        "prompt": case["prompt"],
        "latency_ms": api.get("latency_ms"),
        "status_code": api.get("status_code"),
    }
    if not api["ok"]:
        result.update(
            {
                "verdict": "FAIL",
                "reason": "transport_error",
                "error": api.get("error"),
                "response": "",
                "forbidden_hits": [],
            }
        )
        return result

    response = api["response"] or ""
    hits = detect_forbidden_phrases(response, forbidden)
    if hits:
        result.update(
            {
                "verdict": "FAIL",
                "reason": "forbidden_phrase_detected",
                "forbidden_hits": hits,
                "response": response[:600],
            }
        )
    elif not response.strip():
        result.update(
            {
                "verdict": "FAIL",
                "reason": "empty_response",
                "forbidden_hits": [],
                "response": "",
            }
        )
    else:
        result.update(
            {
                "verdict": "PASS",
                "reason": "no_forbidden_phrase",
                "forbidden_hits": [],
                "response": response[:300],
            }
        )
    return result


async def main_async(args: argparse.Namespace) -> int:
    try:
        meta, cases = load_cases(filter_id=args.id, filter_agent=args.agent)
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    if not cases:
        print("[error] nenhum cenário selecionado", file=sys.stderr)
        return 2

    forbidden = [p for p in (meta.get("forbidden_phrases") or []) if isinstance(p, str)]
    if not forbidden:
        print("[error] meta.forbidden_phrases ausente no YAML", file=sys.stderr)
        return 2

    token = args.token or _make_eval_token()
    if not token:
        print("[error] sem JWT — passe --token ou defina LIA_TEST_TOKEN", file=sys.stderr)
        return 2

    print(f"→ Rodando {len(cases)} cenários contra {args.url}")
    results: list[dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        for case in cases:
            print(f"  · {case['id']:14s} ({case.get('agent','?'):24s})", end=" ", flush=True)
            res = await run_case(client, args.url, token, case, forbidden)
            verdict = res["verdict"]
            tag = "✓ PASS" if verdict == "PASS" else "✗ FAIL"
            extra = ""
            if verdict == "FAIL":
                if res["reason"] == "forbidden_phrase_detected":
                    extra = f" [{', '.join(res['forbidden_hits'])}]"
                else:
                    extra = f" [{res['reason']}]"
            print(f"{tag}{extra}  {res['latency_ms']}ms")
            if args.verbose and verdict == "FAIL":
                print(f"      response: {res.get('response','')[:240]!r}")
            results.append(res)

    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    fail_count = len(results) - pass_count

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = BASE_DIR / f"tenant_context_no_regression_{timestamp}.json"
    out_path.write_text(
        json.dumps(
            {
                "task": "#977",
                "url": args.url,
                "total": len(results),
                "pass": pass_count,
                "fail": fail_count,
                "forbidden_phrases": forbidden,
                "timestamp": datetime.utcnow().isoformat(),
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print(f"== Total: {len(results)} | PASS: {pass_count} | FAIL: {fail_count}")
    print(f"== Resultado: {out_path.relative_to(BASE_DIR.parent)}")
    return 0 if fail_count == 0 else 1


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Task #977 tenant-context no-regression eval")
    p.add_argument("--token", default="", help="JWT (default: auto-gera com SECRET_KEY do server)")
    p.add_argument("--url", default=DEFAULT_URL, help=f"Backend URL (default: {DEFAULT_URL})")
    p.add_argument("--id", default=None, help="Roda apenas o ID indicado (ex: TCNR-WZ-001)")
    p.add_argument("--agent", default=None, help="Filtra por agente (ex: wizard)")
    p.add_argument("--verbose", action="store_true", help="Mostra trecho da resposta em FAIL")
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(asyncio.run(main_async(parse_args())))
