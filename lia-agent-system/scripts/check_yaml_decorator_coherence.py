#!/usr/bin/env python3
"""
Sensor canonical · W1-001 (2026-05-22)

Detecta drift entre `app/agents_registry.yaml` (declarativo) e os agents
decorados com `@register_agent` em `app/domains/**/agents/*.py` (canonical
runtime).

Regras:
- Todo agent listado no YAML (enabled=True) DEVE ter `@register_agent("<name>")`
  ou aparecer como alias de outro decorated agent.
- Todo decorated agent que NÃO está em INTERNAL_AGENTS DEVE estar no YAML
  (vice-versa) — sub-agents internos (kanban_action, pipeline_*, sourcing_*)
  são opt-in pra publicação YAML.

Pre-audit: sprint_logs/sprint_1.2/W1-001_AUDIT.md.
Skill: harness-engineering [computacional, BLOCKING].

Mensagem em PT-BR com fix sugerido em sintaxe exata.

Modo: BLOCKING por default. `--warn-only` durante migração gradual.

Exit codes:
    0 = OK (coerente) ou --warn-only
    1 = drift detectado (BLOCKING)
    2 = arquivo registry ausente
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_YAML = REPO_ROOT / "app" / "agents_registry.yaml"
DOMAINS_DIR = REPO_ROOT / "app" / "domains"
SHARED_AGENTS_DIR = REPO_ROOT / "app" / "shared" / "agents"

# Sub-agents internos · não precisam estar no YAML (acessíveis só via tool dispatch
# ou registry interna; não são consumidos via WebSocket chat path crítico).
# Atualizar quando promover algum desses pra "publishable agent" (canonical chat).
INTERNAL_AGENTS: frozenset[str] = frozenset({
    # Kanban sub-agents (chamados via tool dispatch, não direto)
    "kanban_action",
    "kanban_insight",
    "kanban_search",
    # Pipeline sub-agents
    "pipeline_action",
    "pipeline_context",
    "pipeline_decision",
    "pipeline_transition",
    # Sourcing sub-agents granulares
    "sourcing_engagement",
    "sourcing_enrich",
    "sourcing_planner",
    "sourcing_search",
    # Sourcing sub-agents especializados (W1-001 cleanup target)
    "sourcing_github",
    "sourcing_stackoverflow",
    "sourcing_diversity",
    "sourcing_passive_pipeline",
    "sourcing_referral",
    "sourcing_nurture_sequence",
    # Standalone domain agents que não fazem parte do roster YAML publicável
    "candidate_self_service",
    "company_settings",
    "talent_pool",
    # job_management (Frente 4 2026-05-29): canonical id do JobsManagementReActAgent
    # foi flipado de "jobs_management" -> "job_management" pra alinhar com o domain
    # id do roteamento (singular). jobs_management/jobs_mgmt viram aliases. O agente
    # roda GESTAO de vaga existente via routing, mas NÃO está no YAML por desenho
    # (consolidado; o entry wizard do YAML cobre criação). Allowlist segue o canonical.
    "job_management",
    # NOTA: autonomous é chamado por CascadedRouter Tier 6 (não via chat
    # direto), mas ESTÁ no YAML como hint pra observabilidade. Não está em
    # INTERNAL_AGENTS por desejo explícito (canonical chat-eligible fallback).
})


def parse_yaml_agents() -> list[dict]:
    """Carrega lista de agents enabled=True do YAML."""
    if not REGISTRY_YAML.exists():
        return []
    data = yaml.safe_load(REGISTRY_YAML.read_text(encoding="utf-8")) or {}
    agents = data.get("agents", []) if isinstance(data, dict) else []
    return [a for a in agents if a.get("enabled", True)]


def find_decorated_agents() -> tuple[
    dict[str, tuple[Path, int]],
    dict[str, str],
]:
    """
    Faz AST scan em app/domains/**/agents/*.py procurando @register_agent("name").

    Returns:
        canonical: dict {canonical_agent_id: (file_path, lineno)}
        aliases:   dict {alias: canonical_agent_id}
    """
    canonical: dict[str, tuple[Path, int]] = {}
    aliases: dict[str, str] = {}

    for py_file in DOMAINS_DIR.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        if "/agents/" not in str(py_file):
            continue

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for deco in node.decorator_list:
                    if not isinstance(deco, ast.Call):
                        continue
                    func = deco.func
                    if not (
                        (isinstance(func, ast.Name) and func.id == "register_agent")
                        or (isinstance(func, ast.Attribute) and func.attr == "register_agent")
                    ):
                        continue
                    # First positional arg = canonical agent_id
                    canonical_id: str | None = None
                    if deco.args and isinstance(deco.args[0], ast.Constant):
                        val = deco.args[0].value
                        if isinstance(val, str):
                            canonical_id = val
                            canonical[val] = (py_file, deco.lineno)
                    # Optional aliases= keyword → mapped to canonical_id
                    for kw in deco.keywords:
                        if kw.arg == "aliases" and isinstance(kw.value, ast.List) and canonical_id:
                            for elt in kw.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    aliases[elt.value] = canonical_id

    return canonical, aliases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Reporta drift mas retorna exit 0 (uso transitório).",
    )
    args = parser.parse_args()

    if not REGISTRY_YAML.exists():
        print(f"❌ Registry YAML não encontrado: {REGISTRY_YAML}", file=sys.stderr)
        return 2

    yaml_agents = parse_yaml_agents()
    yaml_names: set[str] = {a["name"] for a in yaml_agents if a.get("name")}

    canonical, aliases = find_decorated_agents()
    canonical_ids: set[str] = set(canonical.keys())
    alias_ids: set[str] = set(aliases.keys())

    errors: list[str] = []

    # Regra 1: todo YAML agent DEVE resolver para um canonical OU ser alias válido
    yaml_unresolved = yaml_names - canonical_ids - alias_ids
    if yaml_unresolved:
        errors.append(
            f"❌ {len(yaml_unresolved)} agent(s) em YAML sem canonical/alias decorator:"
        )
        for name in sorted(yaml_unresolved):
            errors.append(f"   - {name}")
        errors.append(
            "   FIX: adicionar `@register_agent(\"<name>\")` à class canonical do\n"
            "        agent (ver app/agents_registry.yaml.class_path).\n"
            "        OU registrar como alias=[\"<name>\"] de um canonical agent."
        )

    # Regra 2: todo canonical agent DEVE estar no YAML, OU seu alias DEVE estar
    #          no YAML, OU o canonical DEVE estar em INTERNAL_AGENTS.
    # Aliases NUNCA são "drift" — só canonical. Resolve YAML → canonical via aliases.
    yaml_canonical_resolved: set[str] = set()
    for name in yaml_names:
        if name in canonical_ids:
            yaml_canonical_resolved.add(name)
        elif name in aliases:
            yaml_canonical_resolved.add(aliases[name])

    canonical_missing_yaml = (canonical_ids - yaml_canonical_resolved) - INTERNAL_AGENTS
    if canonical_missing_yaml:
        errors.append("")
        errors.append(
            f"❌ {len(canonical_missing_yaml)} canonical agent(s) NÃO listado(s) em YAML:"
        )
        for name in sorted(canonical_missing_yaml):
            path, lineno = canonical[name]
            errors.append(f"   - {name} @ {path.relative_to(REPO_ROOT)}:{lineno}")
        errors.append(
            "   FIX: adicionar entry em app/agents_registry.yaml OU adicionar\n"
            "        a INTERNAL_AGENTS allowlist (sub-agent que não roda chat direto)\n"
            "        em scripts/check_yaml_decorator_coherence.py."
        )

    if errors:
        print(
            f"W1-001 drift detected · {len(yaml_names)} YAML × "
            f"{len(canonical_ids)} canonical decorated ({len(alias_ids)} aliases)",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
        print(file=sys.stderr)
        print("Pre-audit: sprint_logs/sprint_1.2/W1-001_AUDIT.md", file=sys.stderr)

        if args.warn_only:
            print("⚠️  WARN-ONLY mode: exit 0 despite drift", file=sys.stderr)
            return 0
        return 1

    print(
        f"✅ Coherence OK · {len(yaml_names)} YAML × {len(canonical_ids)} canonical "
        f"({len(alias_ids)} aliases · {len(INTERNAL_AGENTS)} internal)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
