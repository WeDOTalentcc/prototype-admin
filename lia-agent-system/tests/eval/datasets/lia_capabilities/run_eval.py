"""
Runner standalone para suite lia_capabilities (Camada 2 — LLM-judge eval).

Para cada cenário em scenarios.yaml:
  1. Envia o prompt via /api/v1/chat (REST) contra o backend configurado
  2. Captura a resposta
  3. Passa ao LLM-judge (Claude Sonnet) com a rubrica de chat.yaml
  4. Agrega scores e gera relatório JSON

Uso:
    BACKEND_URL=http://localhost:8000 JWT_TOKEN=... \\
        python -m tests.eval.datasets.lia_capabilities.run_eval \\
        --output results/lia_cap_$(date +%Y%m%d_%H%M).json

Variáveis de ambiente:
    BACKEND_URL       — URL do FastAPI (default: http://localhost:8000)
    JWT_TOKEN         — token Bearer para autenticar
    ANTHROPIC_API_KEY — chave Claude para o judge
    EVAL_JUDGE_MODEL  — modelo (default: claude-sonnet-4-20250514)

Requer:
    pip install anthropic pyyaml httpx
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    import httpx
    from anthropic import Anthropic
except ImportError as e:
    print(f"Dependência faltando: {e}. Rode: pip install anthropic pyyaml httpx")
    sys.exit(1)


ROOT = Path(__file__).resolve().parents[3]  # lia-agent-system/
SCENARIOS_FILE = Path(__file__).resolve().parent / "scenarios.yaml"
RUBRIC_FILE = ROOT / "tests" / "eval" / "rubrics" / "chat.yaml"


def load_scenarios() -> list[dict[str, Any]]:
    with open(SCENARIOS_FILE) as f:
        data = yaml.safe_load(f)
    return data.get("scenarios", [])


def load_rubric() -> dict[str, Any]:
    with open(RUBRIC_FILE) as f:
        return yaml.safe_load(f)


async def call_chat(backend_url: str, jwt_token: str, message: str) -> dict[str, Any]:
    """Chama /api/v1/chat (REST) e retorna { content, metadata, status_code }"""
    url = f"{backend_url.rstrip('/')}/api/v1/chat"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}",
    }
    payload = {"message": message, "domain": "", "session_id": f"eval-{datetime.now().timestamp()}"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            r = await client.post(url, json=payload, headers=headers)
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            return {"status_code": r.status_code, "content": body.get("content", ""), "body": body}
        except Exception as e:
            return {"status_code": 0, "content": "", "body": {"error": str(e)}}


def judge_response(
    client: Anthropic,
    model: str,
    rubric: dict[str, Any],
    user_message: str,
    assistant_response: str,
) -> dict[str, Any]:
    """Pede ao Claude pra avaliar a resposta segundo a rubrica."""
    judge_prompt = rubric["judge_prompt"]

    dims_description = "\n".join(
        f"- **{name}** ({d['description']}). Escala:\n"
        + "\n".join(f"    {score}: {desc}" for score, desc in d["scale"].items())
        for name, d in rubric["dimensions"].items()
    )

    full_prompt = f"""{judge_prompt}

Dimensões:
{dims_description}

---
Pergunta do recrutador:
{user_message}

---
Resposta do agente:
{assistant_response}
"""

    try:
        msg = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": full_prompt}],
        )
        raw_text = "".join(b.text for b in msg.content if hasattr(b, "text"))

        # Extrai JSON
        import re
        match = re.search(r"\{[^{}]*\}", raw_text, re.DOTALL)
        if not match:
            return {"error": "no_json", "raw": raw_text[:500]}
        return json.loads(match.group(0))
    except Exception as e:
        return {"error": str(e)[:300]}


def compute_score(judge_result: dict[str, Any], rubric: dict[str, Any]) -> float:
    """Calcula score ponderado (0-3) a partir das dimensões avaliadas."""
    if "error" in judge_result:
        return 0.0
    weights = {name: d["weight"] for name, d in rubric["dimensions"].items()}
    total = 0.0
    for name, weight in weights.items():
        score = judge_result.get(name, 0)
        if isinstance(score, (int, float)):
            total += weight * float(score)
    return round(total, 2)


def check_must_include(content: str, required: list[str]) -> list[str]:
    """Retorna palavras ausentes (ok se lista vazia)."""
    lc = content.lower()
    return [w for w in required if w.lower() not in lc]


def check_must_not_include(content: str, forbidden: list[str]) -> list[str]:
    """Retorna palavras presentes que NÃO deveriam estar."""
    lc = content.lower()
    return [w for w in forbidden if w.lower() in lc]


async def run_scenario(
    scenario: dict[str, Any],
    backend_url: str,
    jwt_token: str,
    anthropic_client: Anthropic,
    judge_model: str,
    rubric: dict[str, Any],
) -> dict[str, Any]:
    """Executa 1 cenário: chama LIA → judge → agrega."""
    user_message = scenario["input"]["user_message"]
    scenario_id = scenario["id"]

    print(f"\n[{scenario_id}] {user_message[:80]}")

    chat = await call_chat(backend_url, jwt_token, user_message)
    content = chat.get("content", "") or ""
    status = chat.get("status_code", 0)

    # Expectativas estruturais
    expected = scenario.get("expected", {})
    missing = check_must_include(content, expected.get("must_include", []))
    forbidden = check_must_not_include(content, expected.get("must_not_include", []))

    # Judge LLM
    if status == 200 and content:
        judge = judge_response(anthropic_client, judge_model, rubric, user_message, content)
    else:
        judge = {"error": f"chat_failed_status_{status}"}

    score = compute_score(judge, rubric)
    threshold = scenario.get("threshold", 2.0)

    # Pass = score acima do threshold E sem must_include faltando E sem forbidden presente
    passed = score >= threshold and not missing and not forbidden

    result = {
        "id": scenario_id,
        "name": scenario.get("name", ""),
        "category": scenario.get("category", ""),
        "severity": scenario.get("severity", "medium"),
        "input": user_message,
        "http_status": status,
        "content_preview": content[:200],
        "content_length": len(content),
        "must_include_missing": missing,
        "must_not_include_found": forbidden,
        "judge": judge,
        "score": score,
        "threshold": threshold,
        "passed": passed,
    }

    status_emoji = "✅" if passed else "❌"
    print(f"  {status_emoji} score={score:.2f} threshold={threshold} status={status}")
    if missing:
        print(f"     ⚠️  must_include ausente: {missing}")
    if forbidden:
        print(f"     🚨 must_not_include presente: {forbidden}")

    return result


async def main(args):
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    jwt_token = os.getenv("JWT_TOKEN", "")
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not jwt_token:
        print("⚠️  JWT_TOKEN não configurado — cenários vão receber 401/403.")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY não configurado — judge vai falhar.")
        return 1

    anthropic_client = Anthropic(api_key=api_key)
    judge_model = os.getenv("EVAL_JUDGE_MODEL", "claude-sonnet-4-20250514")

    rubric = load_rubric()
    scenarios = load_scenarios()

    if args.filter:
        scenarios = [s for s in scenarios if args.filter in s["id"] or args.filter == s.get("severity")]

    print(f"📊 Rodando {len(scenarios)} cenários contra {backend_url}")
    print(f"    Judge: {judge_model}")

    results = []
    for s in scenarios:
        try:
            r = await run_scenario(
                s, backend_url, jwt_token, anthropic_client, judge_model, rubric
            )
            results.append(r)
        except Exception as exc:
            print(f"  ❌ Erro fatal: {exc}")
            results.append({"id": s["id"], "passed": False, "error": str(exc)})

    # Agregação
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    by_severity = {}
    for r in results:
        sev = r.get("severity", "medium")
        by_severity.setdefault(sev, {"total": 0, "passed": 0})
        by_severity[sev]["total"] += 1
        if r.get("passed"):
            by_severity[sev]["passed"] += 1

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "backend_url": backend_url,
        "judge_model": judge_model,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 3) if total else 0.0,
        "by_severity": by_severity,
        "results": results,
    }

    output_path = Path(args.output) if args.output else Path("results/lia_capabilities.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print(f"\n{'=' * 60}")
    print(f"📊 Summary: {passed}/{total} PASS ({summary['pass_rate']*100:.1f}%)")
    for sev, stats in sorted(by_severity.items()):
        print(f"   {sev:10s}: {stats['passed']}/{stats['total']}")
    print(f"\n💾 Relatório: {output_path}")

    return 0 if summary["pass_rate"] >= 0.7 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Caminho do JSON de saída")
    parser.add_argument("--filter", help="Filtrar por id substring ou severidade")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args)))
