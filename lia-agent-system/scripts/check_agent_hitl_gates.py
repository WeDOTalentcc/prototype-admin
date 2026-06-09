#!/usr/bin/env python3
"""W4-032 · Sensor canonical — HITL gate em todos os 9 agents canonical.

Walks os 9 + 4 (= 13) agents canonical do AGENT_COMPLIANCE_MATRIX e verifica:
1. Declara `_HITL_ACTION_TYPES = frozenset(...)` na classe.
2. Importa `maybe_request_hitl_approval` from `app.shared.hitl.agent_gate`.
3. `process` method tem early return pattern (`if _hitl_response is not None:`)
   ANTES do `_process_langgraph` call.

Saída em formato consumível por LLM (fix sugerido em PT-BR).
Modo --blocking exit 1 quando coverage < 100% (9/9 wired).

Default warn-only durante migration (P0 + P1 + P2 progressivo).
Promote para blocking quando baseline 9/9 atingido.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOMAINS_ROOT = REPO_ROOT / "app" / "domains"

# Os 9 agents canonical que requerem HITL gate (W4-032 P0+P1+P2)
# + 4 já wired pre-W4-032 (referência canonical)
CANONICAL_AGENTS: dict[str, dict[str, str]] = {
    # ----- 4 pre-existing (referência) -----
    "communication": {
        "path": "communication/agents/communication_react_agent.py",
        "constant": "_HITL_MESSAGE_TYPES",  # pre-existing naming
        "priority": "REF",
    },
    "candidate_self_service": {
        "path": "candidate_self_service/agents/candidate_react_agent.py",
        "priority": "REF",
    },
    "sourcing": {
        "path": "sourcing/agents/sourcing_react_agent.py",
        "priority": "REF",
    },
    # ----- 9 W4-032 P0+P1+P2 -----
    # P0
    "ats_integration": {
        "path": "ats_integration/agents/ats_integration_react_agent.py",
        "priority": "P0",
    },
    "kanban": {
        "path": "recruiter_assistant/agents/kanban_react_agent.py",
        "priority": "P0",
    },
    # P1
    "jobs_management": {
        "path": "recruiter_assistant/agents/jobs_mgmt_react_agent.py",
        "priority": "P1",
    },
    "pipeline": {
        "path": "cv_screening/agents/pipeline_react_agent.py",
        "priority": "P1",
    },
    "automation": {
        "path": "automation/agents/automation_react_agent.py",
        "priority": "P1",
    },
    # P2
    "talent_funnel": {
        "path": "recruiter_assistant/agents/talent_funnel_react_agent.py",
        "priority": "P2",
    },
    "analytics": {
        "path": "analytics/agents/analytics_react_agent.py",
        "priority": "P2",
    },
    "company_settings": {
        "path": "company_settings/agents/company_react_agent.py",
        "priority": "P2",
    },
}


def check_agent(agent_name: str, info: dict[str, str]) -> list[str]:
    """Return violations for this agent (empty list = OK)."""
    violations: list[str] = []
    path = DOMAINS_ROOT / info["path"]

    if not path.exists():
        # Agent file missing — possibly renamed or moved. Don't block, just warn.
        return [
            f"[W4-032/{info['priority']}] {agent_name}: file ausente em {info['path']}.\n"
            "  Fix: confirmar se agent foi renomeado/deletado em outro sprint."
        ]

    # REF agents (communication, policy, etc) usam pattern legacy pré-W4-032.
    # Não validar via este sensor — eles têm sua própria suite de testes.
    if info["priority"] == "REF":
        return violations

    src = path.read_text(encoding="utf-8")
    constant = info.get("constant", "_HITL_ACTION_TYPES")

    # 1. Declara _HITL_ACTION_TYPES
    if f"{constant} = frozenset" not in src:
        violations.append(
            f"[W4-032/{info['priority']}] {agent_name}: {constant} NÃO declarado.\n"
            f"  Fix: adicionar `{constant} = frozenset({{...}})` na class declaration.\n"
            f"  Pattern: app/shared/hitl/agent_gate.py docstring."
        )

    # 2. Importa helper canonical
    if "from app.shared.hitl.agent_gate import maybe_request_hitl_approval" not in src:
        violations.append(
            f"[W4-032/{info['priority']}] {agent_name}: NÃO importa "
            "maybe_request_hitl_approval.\n"
            "  Fix: adicionar import em process() method."
        )

    # 3. Early return pattern (depois do gate call)
    if "if _hitl_response is not None:" not in src and "if hitl_response is not None:" not in src:
        violations.append(
            f"[W4-032/{info['priority']}] {agent_name}: pattern early return missing.\n"
            "  Fix: adicionar `if _hitl_response is not None: return _hitl_response` "
            "ANTES de _process_langgraph."
        )

    return violations


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="W4-032 · HITL gate canonical sensor (9 agents)"
    )
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="Exit 1 if violations found (default warn-only).",
    )
    args = parser.parse_args()

    all_violations: list[str] = []
    wired_count = 0
    total_w4032 = sum(1 for info in CANONICAL_AGENTS.values() if info["priority"] != "REF")

    for agent_name, info in CANONICAL_AGENTS.items():
        v = check_agent(agent_name, info)
        if not v and info["priority"] != "REF":
            wired_count += 1
        all_violations.extend(v)

    if all_violations:
        for v in all_violations:
            print(v, file=sys.stderr)
            print("", file=sys.stderr)
        coverage_pct = (wired_count / total_w4032 * 100) if total_w4032 else 0
        print(
            f"\n⚠  check_agent_hitl_gates · {len(all_violations)} violation(s).\n"
            f"Coverage W4-032: {wired_count}/{total_w4032} agents ({coverage_pct:.0f}%).\n"
            "Helper canonical: app/shared/hitl/agent_gate.py",
            file=sys.stderr,
        )
        if args.blocking:
            return 1
        print("(warn-only mode — exit 0)", file=sys.stderr)
        return 0

    print(
        f"✅ check_agent_hitl_gates OK · {wired_count}/{total_w4032} W4-032 agents wired (100%)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
