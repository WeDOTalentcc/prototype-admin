#!/usr/bin/env python3
"""
check_chat_path_parity.py — GAP-00-001

Verifica que os 3 paths de chat têm paridade de gates de segurança:
  - FairnessGuard (bloqueio de discriminação CLT Art.373-A)
  - Daily token budget gate
  - LGPD consent gate

Paths verificados:
  1. app/api/v1/chat.py            (path legacy WS/SSE)
  2. app/api/v1/agent_chat_sse.py  (path SSE canônico)
  3. app/orchestrator/execution/main_orchestrator.py  (supervisor)

Output otimizado para consumo de LLM: indica exatamente o que adicionar em PT-BR.
"""
import sys
from pathlib import Path
import argparse

REPO_ROOT = Path(__file__).resolve().parents[1]

PATHS = {
    "chat_legacy": REPO_ROOT / "app/api/v1/chat.py",
    "chat_sse": REPO_ROOT / "app/api/v1/agent_chat_sse.py",
    "main_orch": REPO_ROOT / "app/orchestrator/execution/main_orchestrator.py",
}

# Gate signatures — each is a list of alternatives (any one counts as "present")
GATES = {
    "fairness_guard": {
        "description": "FairnessGuard — bloqueio de discriminação CLT Art.373-A",
        "required_in": ["chat_legacy", "chat_sse", "main_orch"],
        "signatures": ["FairnessGuard", "fairness_guard"],
    },
    "fairness_log_check": {
        "description": "FairnessGuard.log_check() — audit trail de bloqueios",
        "required_in": ["chat_legacy", "chat_sse", "main_orch"],
        "signatures": ["log_check"],
    },
    "daily_budget": {
        "description": "Daily token budget check (Redis) — gasto diário de IA",
        "required_in": ["chat_legacy", "chat_sse", "main_orch"],
        "signatures": [
            "check_budget",
            "budget_exhausted",
            "token_budget",
            "token_budget_gate",
            "LIA-BUDGET",
        ],
    },
    "lgpd_consent": {
        "description": "LGPD consent gate — Art. 7 / Art. 18 revogação",
        "required_in": ["chat_legacy", "chat_sse", "main_orch"],
        "signatures": [
            "consent_revoked",
            "ConsentCheckerService",
            "check_candidate_consent",
            "LIA-CONSENT",
            "consent_blocked",
        ],
    },
}

FIX_HINTS = {
    ("chat_legacy", "fairness_guard"): (
        "Adicionar FairnessGuard em app/api/v1/chat.py /stream antes de retornar StreamingResponse."
    ),
    ("chat_legacy", "fairness_log_check"): (
        "Adicionar log_check() ao bloco FairnessGuard em chat.py /stream "
        "(ver pattern em agent_chat_sse.py:359)."
    ),
    ("chat_legacy", "daily_budget"): (
        "Adicionar check_budget() em chat.py antes de _disable_unified (ver GAP-00-001)."
    ),
    ("chat_legacy", "lgpd_consent"): (
        "Adicionar consent gate em chat.py /stream usando view_context.candidate_id (ver GAP-00-001)."
    ),
    ("chat_sse", "fairness_guard"): (
        "Adicionar FairnessGuard em agent_chat_sse.py (ver LIA-P03 block)."
    ),
    ("chat_sse", "fairness_log_check"): (
        "Adicionar log_check() ao bloco FairnessGuard em agent_chat_sse.py."
    ),
    ("chat_sse", "daily_budget"): (
        "Adicionar check_budget() em agent_chat_sse.py (ver _check_budget_async)."
    ),
    ("chat_sse", "lgpd_consent"): (
        "Adicionar consent gate em agent_chat_sse.py (ver GAP-07-004 block)."
    ),
    ("main_orch", "fairness_guard"): (
        "Adicionar FairnessGuard em main_orchestrator.process() (ver lines 465-515)."
    ),
    ("main_orch", "fairness_log_check"): (
        "Adicionar log_check() ao FairnessGuard block em main_orchestrator.py."
    ),
    ("main_orch", "daily_budget"): (
        "Adicionar check_budget() em main_orchestrator.process() antes de PolicyGate (ver GAP-00-001)."
    ),
    ("main_orch", "lgpd_consent"): (
        "Adicionar consent gate em main_orchestrator usando get_active_candidate() ContextVar "
        "(lê candidato resolvido upstream pelo entity resolver)."
    ),
}


def check_gate(content: str, signatures: list[str]) -> bool:
    return any(sig in content for sig in signatures)


def run_parity_check() -> dict:
    violations = []
    results = {}

    for path_key, file_path in PATHS.items():
        if not file_path.exists():
            violations.append({
                "path": path_key,
                "gate": "FILE_EXISTS",
                "file": str(file_path),
                "message": f"Arquivo não encontrado: {file_path}",
            })
            results[path_key] = {}
            continue

        content = file_path.read_text(encoding="utf-8")
        results[path_key] = {}

        for gate_key, gate_cfg in GATES.items():
            if path_key not in gate_cfg["required_in"]:
                continue
            present = check_gate(content, gate_cfg["signatures"])
            results[path_key][gate_key] = present
            if not present:
                hint = FIX_HINTS.get((path_key, gate_key), "Ver pattern em agent_chat_sse.py.")
                violations.append({
                    "path": path_key,
                    "gate": gate_key,
                    "file": str(file_path.relative_to(REPO_ROOT)),
                    "description": gate_cfg["description"],
                    "fix": hint,
                })

    return {"ok": len(violations) == 0, "violations": violations, "results": results}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chat path parity sensor (GAP-00-001)")
    parser.add_argument("--blocking", action="store_true", help="Exit 1 when violations exist")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--max-violations", type=int, default=0)
    args = parser.parse_args(argv)

    result = run_parity_check()

    if args.json:
        import json
        print(json.dumps(result, indent=2))
        return 0

    violations = result["violations"]
    if not violations:
        print("✅ Chat path parity OK — FairnessGuard, budget, consent wired em todos os 3 paths")
        print(f"\n[resumo] 0 violações · {len(PATHS)} paths verificados · {len(GATES)} gates")
        return 0

    print(f"❌ {len(violations)} violação(ões) de paridade nos paths de chat:\n")
    for v in violations:
        print(f"❌ [{v['path']}] {v['gate']}: {v.get('description', '')}")
        print(f"   Arquivo: {v['file']}")
        print(f"   → Fix: {v['fix']}")
        print()

    count = len(violations)
    print(f"📊 Resumo: {count} violação(ões) total")

    if args.blocking and count > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
