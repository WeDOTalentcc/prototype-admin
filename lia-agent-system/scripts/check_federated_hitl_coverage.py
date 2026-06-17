#!/usr/bin/env python3
"""Sensor canônico (AST): toda tool de ESCRITA exposta pelo agente federado
(recruiter_copilot) DEVE estar coberta pelo gate HITL (`_HITL_ACTION_TYPES`).

Origem: preparação do "copiloto onipotente" (consolidação do chat, 2026-06-09).
Decisão de produto: o federado vai cobrir TODOS os domínios (vagas, candidatos,
pipeline, e futuramente config/políticas/automação). O HITL hoje é FRAGMENTADO
por caller (federado tem `_HITL_ACTION_TYPES`; supervisor tem `intents_config`;
`tool_handler` tem `requires_confirmation`) — não há chokepoint único. Risco: ao
adicionar uma tool de ESCRITA ao `_FEDERATION_SPEC` (ex: `update_hiring_policy`),
esquecer de gateá-la = ação sensível sem confirmação humana (LGPD/SOX).

Este sensor fecha esse furo no caminho federado: cruza `_FEDERATION_SPEC` (tools
que o federado expõe) com `_HITL_ACTION_TYPES` (o gate). Toda tool cujo nome
bate um padrão de mutação DEVE estar no gate — salvo allowlist documentada de
ações que NÃO persistem (ex: `start_creation_from_source` inicia o wizard
seeded mas não grava; `open_ui` é navegação).

Uso:
    python3 scripts/check_federated_hitl_coverage.py            # blocking
    python3 scripts/check_federated_hitl_coverage.py --json
    python3 scripts/check_federated_hitl_coverage.py --warn-only

Baseline 2026-06-09: 0 violações (3 escritas gated; 2 na allowlist).
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

_AGENTS = "app/domains/recruiter_assistant/agents"
SPEC_FILE = f"{_AGENTS}/recruiter_copilot_tool_registry.py"
AGENT_FILE = f"{_AGENTS}/recruiter_copilot_react_agent.py"

# Padrões de nome que indicam MUTAÇÃO (ação de escrita).
WRITE_PATTERNS = (
    "move", "pause", "reopen", "publish", "unpublish", "update", "delete",
    "create", "bulk", "archive", "activate", "deactivate", "send", "reject",
    "approve", "close", "remove", "add_", "assign", "set_", "toggle", "start_",
)

# Allowlist: tools cujo nome bate WRITE_PATTERNS mas que NÃO persistem mutação.
# Cada entrada exige justificativa (auditável).
WRITE_ALLOWLIST: dict[str, str] = {
    "start_creation_from_source": "inicia o wizard seeded (diretiva de UI) — não persiste vaga; usuário preenche+confirma no wizard",
    "open_ui": "navegação/abertura de modal — não muta dados (camada de navegação)",
}


def _extract_federation_tools(root: Path) -> list[str]:
    """Lê _FEDERATION_SPEC (lista de tuplas (registry, tool_name))."""
    src = (root / SPEC_FILE).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "_FEDERATION_SPEC":
                    try:
                        spec = ast.literal_eval(node.value)
                        return [pair[1] for pair in spec]
                    except (ValueError, IndexError, TypeError):
                        return []
    return []


def _extract_hitl_action_types(root: Path) -> set[str]:
    """Lê _HITL_ACTION_TYPES (frozenset({...}) dentro da classe do agente)."""
    src = (root / AGENT_FILE).read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "_HITL_ACTION_TYPES":
                    v = node.value
                    # frozenset({...}) -> Call com 1 arg Set; ou set literal direto
                    if isinstance(v, ast.Call) and v.args:
                        try:
                            return set(ast.literal_eval(v.args[0]))
                        except (ValueError, TypeError):
                            return set()
                    try:
                        return set(ast.literal_eval(v))
                    except (ValueError, TypeError):
                        return set()
    return set()


def scan(root: Path) -> list[dict]:
    tools = _extract_federation_tools(root)
    hitl = _extract_hitl_action_types(root)
    violations: list[dict] = []
    for name in tools:
        is_write = any(p in name for p in WRITE_PATTERNS)
        if not is_write:
            continue
        if name in WRITE_ALLOWLIST:
            continue
        if name not in hitl:
            violations.append({
                "tool": name,
                "reason": (
                    f"tool federada '{name}' parece ser de ESCRITA (bate padrão de "
                    f"mutação) mas NÃO está em _HITL_ACTION_TYPES — ação sensível "
                    f"sem confirmação humana no caminho federado."
                ),
                "fix": (
                    f"adicione '{name}' a _HITL_ACTION_TYPES em recruiter_copilot_react_agent.py "
                    f"(ou, se não persiste mutação, a WRITE_ALLOWLIST deste sensor com justificativa)."
                ),
            })
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--warn-only", action="store_true")
    parser.add_argument("--max-violations", type=int, default=0)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    violations = scan(root)

    if args.json:
        print(json.dumps({"total": len(violations), "violations": violations},
                         indent=2, ensure_ascii=False))
    else:
        for v in violations:
            print(f"❌ [{v['tool']}] {v['reason']}")
            print(f"   → Fix: {v['fix']}")
        if not violations:
            print("✅ check_federated_hitl_coverage: 0 violações "
                  "(toda tool federada de escrita está no gate HITL).")

    if args.warn_only:
        return 0
    if len(violations) > args.max_violations:
        print(f"\n❌ {len(violations)} ação(ões) de escrita federada sem gate HITL "
              f"(max: {args.max_violations}).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
