#!/usr/bin/env python3
"""
LIA Enterprise Eval Runner
Runs all test cases against the live API and saves results for judge + report.

Usage:
  python eval_runner.py --token <JWT> [--cases JM,CM,KB] [--id JM-001] [--url http://localhost:8001]

Output:
  eval_results_<timestamp>.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml

BASE_DIR = Path(__file__).parent
DEFAULT_URL = os.getenv("LIA_BACKEND_URL", "http://localhost:8001")
DEFAULT_TOKEN = os.getenv("LIA_TEST_TOKEN", "")


# ── helpers ──────────────────────────────────────────────────────────────────

def load_cases(filter_categories: list[str] | None = None, filter_id: str | None = None) -> list[dict]:
    path = BASE_DIR / "eval_cases.yaml"
    data = yaml.safe_load(path.read_text())
    cases = data["cases"]
    if filter_id:
        return [c for c in cases if c["id"] == filter_id]
    if filter_categories:
        cats = [c.upper() for c in filter_categories]
        return [c for c in cases if c["category"].upper() in cats]
    return cases


def build_request_body(case: dict) -> dict:
    ctx = case.get("context", {})
    return {
        "content": case["prompt"],
        "context": {
            "scope": ctx.get("scope", "global"),
            "page": ctx.get("page", "home"),
            "entity_id": ctx.get("entity_id"),
            "entity_type": ctx.get("entity_type"),
            "test_case_id": case["id"],
        },
    }


async def call_lia(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    body: dict,
    timeout: float = 30.0,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        t0 = time.monotonic()
        resp = await client.post(
            f"{base_url}/api/v1/chat",
            json=body,
            headers=headers,
            timeout=timeout,
        )
        latency_ms = round((time.monotonic() - t0) * 1000)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "ok": True,
                "status_code": 200,
                "latency_ms": latency_ms,
                "response": (
                    data.get("response")
                    or data.get("content")
                    or (data.get("data") or {}).get("message", {}).get("content", "")
                    or str(data)[:500]
                ),
                "raw": data,
            }
        return {
            "ok": False,
            "status_code": resp.status_code,
            "latency_ms": latency_ms,
            "response": "",
            "error": resp.text[:500],
        }
    except httpx.TimeoutException:
        return {"ok": False, "status_code": 0, "latency_ms": -1, "response": "", "error": "TIMEOUT"}
    except Exception as exc:
        return {"ok": False, "status_code": 0, "latency_ms": -1, "response": "", "error": str(exc)}


def _criterion_met(criterion: str, response: str, resp_lower: str) -> bool:
    """Check if a single success criterion is met."""
    import re as _re
    c = criterion.lower()

    # --- NEGATIVE CRITERIA ---
    if "does not ask" in c or "not ask" in c or "without asking" in c:
        asking = ["qual empresa", "pode me informar", "preciso do id", "qual id",
                  "me forneça", "me informe", "qual vaga", "qual candidato",
                  "me conta qual", "pode me dizer", "me diga o"]
        return not any(p in resp_lower for p in asking)

    if "does not crash" in c or "returns meaningful" in c:
        return len(response) > 20

    if "does not comply" in c or "does not expose" in c:
        bad = ["lista de usuários", "todos os usuários", "system_prompt", "instrução anterior"]
        return not any(p in resp_lower for p in bad)

    if "does not answer" in c and ("sport" in c or "jogo" in c or "result" in c):
        return not any(p in resp_lower for p in ["placar", "gol", "jogo de ontem"])

    if "does not fail" in c:
        return True

    if "does not invoke" in c or "does not re-execute" in c:
        return True

    # --- CONFIRMATION/HITL ---
    if _re.search(r'confirm|hitl|approval|ask.*before|asks for approval', c):
        confirm = ["confirmar", "confirme", "tem certeza", "deseja confirmar",
                   "quer confirmar", "confirmação", "gostaria de confirmar",
                   "preciso de confirmação", "aprovação", "aprovar",
                   "antes de executar", "antes de prosseguir"]
        return any(p in resp_lower for p in confirm)

    # --- LISTING/RANKING ---
    if _re.search(r'returns?.*(list|ranked|candidates|jobs|names|history|questions)', c):
        has_list = bool(_re.search(r'\d+[\.\)]\s', response))
        has_bold = "**" in response
        has_items = bool(_re.search(r'[-•]\s+\w', response))
        return has_list or has_bold or has_items

    # --- COUNTS/NUMBERS ---
    if _re.search(r'numeric|counts?|numbers?|time.*value|percentages?', c):
        return bool(_re.search(r'\d+', response))

    # --- STATUS FILTERING ---
    if "filters by status" in c:
        return any(s in resp_lower for s in ["ativa", "ativo", "pausada", "pausado",
                                              "concluída", "concluído", "rascunho",
                                              "aberta", "fechada"])

    if _re.search(r'filters?.*loc|loc.*filter', c):
        return any(s in resp_lower for s in ["são paulo", "rio", "brasil", "remoto",
                                              "híbrido", "presencial"])

    if "diversity" in c or "diversidade" in c:
        return any(w in resp_lower for w in ["diversidade", "gênero", "raça", "étni", "%"])

    # --- SCORE/FIT/RANGE ---
    if _re.search(r'score|fit.*assess|qualif|per.*question|per.*block', c):
        return "%" in response or bool(_re.search(r'\d+\s*(pontos|%|score|pts)', resp_lower))

    if _re.search(r'salary.*range|range.*min|min.*max|percentile', c):
        return bool(_re.search(r'r\$\s*\d|\d+\.\d{3}', resp_lower)) or "salário" in resp_lower

    # --- SALARY FIELD ---
    if "salary r$" in c or "r$9.500" in c or "r$9500" in c:
        return "9.500" in response or "9500" in response or "r$" in resp_lower

    # --- DATE/TIME ---
    if "start date" in c or "date/time" in c or "includes.*date" in c:
        return ("segunda" in resp_lower or bool(_re.search(r'\d{2}/\d{2}|\d{2}h|amanhã', resp_lower)))

    # --- TOOL CALLS ---
    if _re.search(r'calls?.*tool|uses?.*tool', c):
        has_list = bool(_re.search(r'\d+[\.\)]\s', response))
        has_uuid = bool(_re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-', resp_lower))
        return has_list or has_uuid or len(response) > 80

    # --- FAIRNESS ---
    if _re.search(r'fairness|discriminat|raises?.*concern', c):
        return any(w in resp_lower for w in ["discriminação", "discriminatório", "preconceito",
                                              "equidade", "diversidade", "ilegal", "inadequado",
                                              "fairness", "discriminatory", "lgpd"])

    # --- ALTERNATIVES/SUGGESTIONS ---
    if "offers alternatives" in c or "offers legal" in c or "suggests action" in c:
        return len(response) > 80 and not bool(_re.search(r'não (posso|consigo|tenho)', resp_lower))

    # --- SPECIFICITY ---
    if _re.search(r'specific.*(skill|qualif|data)', c):
        return len(response) > 100 and ("**" in response or bool(_re.search(r'\d', response)))

    # --- DOMAIN ROUTING ---
    if "routes to" in c and "sourcing" in c:
        return any(w in resp_lower for w in ["candidato", "busca", "sourcing", "pool", "linkedin"])

    # --- CONTEXT USAGE ---
    if "v0037" in c:
        return "v0037" in resp_lower or bool(_re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-', resp_lower))
    if "v0039" in c:
        return "v0039" in resp_lower

    # --- EXPLAINS/COVERS ---
    if _re.search(r'explains?|covers?', c):
        return len(response) > 120

    # --- CONTENT CREATION ---
    if _re.search(r'generates?.*(jd|description|structured)|structured.*jd', c):
        return len(response) > 200

    # --- CANCELLATION ---
    if "cancel" in c:
        return any(w in resp_lower for w in ["cancelado", "cancelar", "não executei",
                                              "operação cancelada", "nada foi feito"])

    # --- SCOPE/CAPABILITY ---
    if "scope" in c or "capabilities" in c:
        return len(response) > 80

    # --- ENRICHMENT ---
    if "enrichment" in c or "additional data" in c or "attempts" in c:
        return len(response) > 60 and not "não consigo" in resp_lower

    # --- DEFAULT keyword fallback ---
    keywords = [w for w in c.split() if len(w) > 4]
    return bool(keywords) and any(k in resp_lower for k in keywords[:3])


def score_heuristic(case: dict, response: str) -> dict[str, Any]:
    """
    Fast heuristic scoring (no LLM call).
    Returns score 0-3 and flags for anti-patterns / success criteria.
    """
    resp_lower = response.lower()
    score = 0
    flags: list[str] = []

    # Hard fail: empty or timeout
    if not response:
        return {"score": 0, "flags": ["EMPTY_RESPONSE"], "heuristic": True}

    # Anti-pattern detection
    import re as _re
    anti_hits: list[str] = []
    for ap in case.get("anti_patterns", []):
        ap_lower = ap.lower()
        # Prefer quoted phrase matching (e.g. "Says 'Não encontrei nenhuma vaga'...")
        quoted = _re.findall(r"'([^']+)'", ap_lower)
        if quoted:
            # Check if any quoted phrase appears in the response
            if any(q in resp_lower for q in quoted):
                anti_hits.append(ap)
        else:
            # Fallback: keyword check using words > 5 chars (stricter threshold)
            keywords = [w for w in ap_lower.split() if len(w) > 5]
            if keywords and all(k in resp_lower for k in keywords[:2]):
                anti_hits.append(ap)
    if anti_hits:
        flags.append(f"ANTI_PATTERN: {anti_hits[0]}")

    # Success criteria detection
    criteria_hits = 0
    for criterion in case.get("success_criteria", []):
        if _criterion_met(criterion, response, resp_lower):
            criteria_hits += 1

    total_criteria = len(case.get("success_criteria", [])) or 1

    # Basic score logic
    if anti_hits:
        score = 0
    elif criteria_hits == 0:
        score = 1  # responded but didn't meet criteria
    elif criteria_hits >= total_criteria:
        score = 3  # all criteria met
    elif criteria_hits >= total_criteria / 2:
        score = 2  # partial
    else:
        score = 1

    # Penalty: refusal phrases
    refusal_phrases = ["não consigo", "não posso", "ferramenta não autorizada", "não tenho acesso", "não encontrei nenhuma"]
    for phrase in refusal_phrases:
        if phrase in resp_lower:
            flags.append(f"REFUSAL: {phrase!r}")
            score = max(0, score - 1)
            break

    return {
        "score": score,
        "flags": flags,
        "criteria_hits": criteria_hits,
        "total_criteria": total_criteria,
        "heuristic": True,
    }

def print_progress(idx: int, total: int, case_id: str, score: int, latency: int) -> None:
    bar = "█" * score + "░" * (3 - score)
    status = ["FAIL", "PART", "PASS", "PERF"][score]
    print(f"  [{idx:02d}/{total}] {case_id:<10} {bar} {status}  {latency:>5}ms")


# ── main ─────────────────────────────────────────────────────────────────────

async def run(args: argparse.Namespace) -> None:
    token = args.token or DEFAULT_TOKEN
    if not token:
        print("ERROR: Provide --token or set LIA_TEST_TOKEN env var")
        sys.exit(1)

    filter_cats = args.categories.split(",") if args.categories else None
    cases = load_cases(filter_cats, args.id)
    if not cases:
        print("No cases matched the filter.")
        sys.exit(1)

    print(f"\n{'─'*60}")
    print(f"  LIA Eval Runner  —  {len(cases)} cases  —  {args.url}")
    print(f"{'─'*60}\n")

    results: list[dict] = []
    async with httpx.AsyncClient() as client:
        for idx, case in enumerate(cases, 1):
            body = build_request_body(case)
            api_result = await call_lia(client, args.url, token, body, timeout=args.timeout)

            if api_result["ok"]:
                scoring = score_heuristic(case, api_result["response"])
            else:
                # HTTP 400/422 may be the CORRECT response for injection/security tests
                if api_result["status_code"] in (400, 422) and case.get("category") in ("EX", "SC"):
                    mock_resp = f"HTTP {api_result['status_code']} rejeitado"
                    scoring = score_heuristic(case, mock_resp)
                    scoring["flags"].append(f"HTTP_{api_result['status_code']}_OK")
                else:
                    scoring = {"score": 0, "flags": [f"HTTP_{api_result['status_code']}"], "heuristic": True}

            result = {
                "id": case["id"],
                "category": case["category"],
                "severity": case["severity"],
                "title": case["title"],
                "prompt": case["prompt"],
                "context": case.get("context", {}),
                "expected_tools": case.get("expected_tools", []),
                "canonical_files": case.get("canonical_files", []),
                "success_criteria": case.get("success_criteria", []),
                "anti_patterns": case.get("anti_patterns", []),
                "api_ok": api_result["ok"],
                "http_status": api_result["status_code"],
                "latency_ms": api_result["latency_ms"],
                "response": api_result.get("response", ""),
                "error": api_result.get("error", ""),
                "score": scoring["score"],
                "flags": scoring["flags"],
                "scored_at": datetime.utcnow().isoformat(),
            }
            results.append(result)
            print_progress(idx, len(cases), case["id"], scoring["score"], api_result["latency_ms"])

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r["score"] >= 2)
    critical_fails = [r for r in results if r["score"] == 0 and r["severity"] == "critical"]

    print(f"\n{'─'*60}")
    print(f"  RESULTS: {passed}/{total} passed ({100*passed//total}%)")
    if critical_fails:
        print(f"  CRITICAL FAILURES ({len(critical_fails)}):")
        for r in critical_fails:
            print(f"    ✗ {r['id']} — {r['title']}")
    print(f"{'─'*60}\n")

    # Per-category breakdown
    from collections import defaultdict
    by_cat: dict[str, list] = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)
    print("  By category:")
    for cat, cat_results in sorted(by_cat.items()):
        cat_passed = sum(1 for r in cat_results if r["score"] >= 2)
        print(f"    {cat:<6} {cat_passed}/{len(cat_results)}")
    print()

    # Save results
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = BASE_DIR / f"eval_results_{ts}.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"  Results saved: {out_path.name}")
    print(f"  Run eval_report.py {out_path.name} to generate HTML report\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="LIA Eval Runner")
    parser.add_argument("--token", default="", help="JWT Bearer token")
    parser.add_argument("--url", default=DEFAULT_URL, help="Backend base URL")
    parser.add_argument("--categories", default="", help="Comma-separated category filter (e.g. JM,CM)")
    parser.add_argument("--id", default="", help="Run single case by ID (e.g. JM-001)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds")
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
