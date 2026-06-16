#!/usr/bin/env python3
"""Sensor anti-ghost de catálogo de tools (harness-engineering, Fase 0).

Garante que todo nome de tool referenciado na camada de GOVERNANÇA
(tool_permissions.yaml: scopes + restricted_tools; tool_registry_metadata.yaml)
existe como tool REAL declarada (`name="..."`) em algum arquivo sob app/.

Ghost = nome referenciado na governança mas NÃO declarado em lugar nenhum.
Um restricted_tool ghost = gate HITL inerte (não dispara). Um scope ghost =
o gate de escopo filtra por um nome que não existe.

NOTA (ground-truth 2026-06-08): "declarado/real" = tem HANDLER Python (`name="..."`).
NÃO contamos `tool_registry_metadata.yaml` como fonte de declaração: esse arquivo
contém entradas SEM handler (os próprios ghosts estão lá), então tratá-lo como
"declarado" MASCARARIA os ghosts. Entradas no metadata yaml sem handler são um
problema SEPARADO (sensor futuro: metadata→handler).

Modelo: scripts/check_canonical_pages_sync.py + scripts/check_deprecated_rail_a_tools.py.
Default warn-only (exit 0); --blocking exit 1 quando ghosts > max-violations.

Uso:
    python3 scripts/check_capability_catalog_sync.py            # warn-only
    python3 scripts/check_capability_catalog_sync.py --blocking # CI
"""
from __future__ import annotations

import argparse
import ast
import sys
import yaml
from pathlib import Path


def extract_declared_names(source: str) -> set[str]:
    """Nomes de tool declarados como `name="literal"` em chamadas de função."""
    names: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    names.add(kw.value.value)
    return names


def extract_governance_refs(permissions_yaml_text: str) -> dict[str, list[str]]:
    """Mapeia cada nome de tool referenciado -> lista de origens (para o relatório).

    Cobre tool_permissions.yaml: global.scopes.<scope>.{query,action} + restricted_tools.
    """
    refs: dict[str, list[str]] = {}

    def add(name: str, origin: str) -> None:
        if isinstance(name, str) and name:
            refs.setdefault(name, []).append(origin)

    data = yaml.safe_load(permissions_yaml_text) or {}
    scopes = (data.get("global") or {}).get("scopes") or {}
    for scope_name, scope in scopes.items():
        for bucket in ("query", "action"):
            for tool in (scope or {}).get(bucket) or []:
                add(tool, f"scope:{scope_name}.{bucket}")
    for tool in data.get("restricted_tools") or []:
        add(tool, "restricted_tools")
    return refs


def compute_ghosts(
    refs: dict[str, list[str]],
    declared: set[str],
    exempt: set[str],
) -> list[dict]:
    """Ghost = referenciado na governança, não declarado em app/, não isento."""
    ghosts: list[dict] = []
    for name in sorted(refs):
        if name in declared or name in exempt:
            continue
        ghosts.append({"name": name, "origins": refs[name]})
    return ghosts


def format_report(ghosts: list[dict]) -> str:
    if not ghosts:
        return "OK - 0 ghosts. Toda tool referenciada na governança existe em app/."
    lines = [f"ERRO: {len(ghosts)} ghost(s) - nome referenciado na governança sem tool real:\n"]
    for g in ghosts:
        origins = ", ".join(g["origins"])
        lines.append(f"  - {g['name']}  (origem: {origins})")
        lines.append(
            f"    -> Fix: renomeie para o nome real da tool correspondente em app/, "
            f"OU remova de tool_permissions.yaml se a tool foi descontinuada, "
            f"OU adicione a EXEMPT_NAMES com motivo se for conceito só-DomainAction."
        )
    return "\n".join(lines)


EXEMPT_NAMES: set[str] = {
    # DomainActions legítimos (não são tools de LLM; o gate de escopo não os alcança
    # por design — são gated no Studio runtime). Decisão Paulo 2026-06-08.
    "create_sourcing_agent",     # DomainAction agent_studio/actions.py
    "calibrate_sourcing_agent",  # DomainAction agent_studio (calibrate_agent/recalibrate_agent)
    "advance_campaign_stage",    # DomainAction recruitment_campaign/actions.py
}
"""Nomes isentos (conceitos que vivem só como DomainAction, não como tool de LLM).
Preenchido na Task 6a com motivo inline por entrada. Formato: 'nome',  # motivo + ticket."""

REPO_ROOT = Path(__file__).resolve().parent.parent
PERMISSIONS_YAML = REPO_ROOT / "app" / "tools" / "tool_permissions.yaml"


def scan_declared_in_tree(app_dir: Path) -> set[str]:
    names: set[str] = set()
    for py in app_dir.rglob("*.py"):
        try:
            names |= extract_declared_names(py.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sensor anti-ghost de catálogo de tools")
    parser.add_argument("--blocking", action="store_true", help="exit 1 se ghosts > max-violations")
    parser.add_argument("--max-violations", type=int, default=0)
    args = parser.parse_args(argv)

    if not PERMISSIONS_YAML.exists():
        print(f"ERRO: {PERMISSIONS_YAML} não encontrado — sensor não pode rodar", file=sys.stderr)
        return 2

    declared = scan_declared_in_tree(REPO_ROOT / "app")
    refs = extract_governance_refs(PERMISSIONS_YAML.read_text(encoding="utf-8"))
    ghosts = compute_ghosts(refs, declared, EXEMPT_NAMES)
    print(format_report(ghosts))
    print(f"\n[resumo] {len(ghosts)} ghost(s) · {len(declared)} tools declaradas · {len(refs)} refs de governança")

    if args.blocking and len(ghosts) > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
