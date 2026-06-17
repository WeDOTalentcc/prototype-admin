#!/usr/bin/env python3
"""Sensor de sincronização YAML ↔ domain registries (GAP-00-004).

Garante que todo tool declarado em `tool_registry_metadata.yaml` tem
um HANDLER real em algum domain registry (_CANONICAL_SOURCES em tool_catalog.py).

Ghost YAML = tool no YAML sem handler → pode ser enviado ao LLM via
descrição do catálogo, mas falha na execução (sem handler).

Undocumented = tool em domain registry sem entrada no YAML → sem metadata
central de scope/versão/allowed_agents.

Baseline 2026-06-15:
  - ghost_in_yaml: 37 (YAML tools without domain handler)
  - undocumented:  164 (domain tools without YAML entry)

Default: warn-only (exit 0). --blocking exit 1 quando ghost_in_yaml > --max-violations.

Uso:
    python3 scripts/check_tool_registry_sync.py              # warn-only
    python3 scripts/check_tool_registry_sync.py --blocking   # CI blocking
    python3 scripts/check_tool_registry_sync.py --json       # output JSON
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add repo root to path so imports from app/ work.
_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))


def _load_yaml_tool_names() -> set[str]:
    """Nomes de tools declarados em tool_registry_metadata.yaml."""
    from app.tools.tool_registry_loader import load_tool_metadata
    return set(load_tool_metadata().keys())


def _load_catalog_tool_names() -> set[str]:
    """Nomes de tools com handler real em domain registries (_CANONICAL_SOURCES)."""
    from app.shared.tool_catalog import build_tool_catalog
    return set(build_tool_catalog().keys())


def run_sync_check(
    yaml_names: set[str] | None = None,
    catalog_names: set[str] | None = None,
) -> dict:
    """Compara YAML vs domain registries e retorna relatório estruturado.

    Args:
        yaml_names: override para testes (None = carrega do YAML).
        catalog_names: override para testes (None = carrega do catalog).
    """
    if yaml_names is None:
        yaml_names = _load_yaml_tool_names()
    if catalog_names is None:
        catalog_names = _load_catalog_tool_names()

    ghost_in_yaml = sorted(yaml_names - catalog_names)  # em YAML, sem handler
    undocumented = sorted(catalog_names - yaml_names)   # handler, sem YAML
    common = sorted(yaml_names & catalog_names)

    return {
        "ok": len(ghost_in_yaml) == 0,
        "yaml_count": len(yaml_names),
        "catalog_count": len(catalog_names),
        "common_count": len(common),
        "ghost_in_yaml": ghost_in_yaml,        # crítico: YAML sem handler
        "undocumented": undocumented,           # aviso: handler sem YAML
    }


def format_report(report: dict) -> str:
    """Formata relatório em texto legível para humano + LLM."""
    lines: list[str] = []
    yaml_c = report["yaml_count"]
    cat_c = report["catalog_count"]
    common_c = report["common_count"]
    ghosts = report["ghost_in_yaml"]
    undoc = report["undocumented"]

    lines.append(
        f"[tool_registry_sync] YAML={yaml_c} · catalog={cat_c} · "
        f"common={common_c} · ghost_in_yaml={len(ghosts)} · undocumented={len(undoc)}"
    )

    if not ghosts and not undoc:
        lines.append("OK — YAML e domain registries estão sincronizados.")
        return "\n".join(lines)

    if ghosts:
        lines.append(
            f"\n🔴 GHOST_IN_YAML ({len(ghosts)}) — declarados no YAML mas SEM handler em domain registries:"
        )
        for name in ghosts:
            lines.append(f"  - {name}")
            lines.append(
                f"    → Fix: implemente o handler em um domain registry "
                f"(_CANONICAL_SOURCES em app/shared/tool_catalog.py), "
                f"OU remova '{name}' de app/tools/tool_registry_metadata.yaml "
                f"se a tool foi descontinuada."
            )

    if undoc:
        lines.append(
            f"\n⚠️  UNDOCUMENTED ({len(undoc)}) — handlers sem entrada no YAML (warn-only):"
        )
        for name in undoc[:20]:
            lines.append(f"  - {name}")
        if len(undoc) > 20:
            lines.append(f"  ... e mais {len(undoc) - 20} tools")
        lines.append(
            "    → Fix: adicione uma entrada em app/tools/tool_registry_metadata.yaml "
            "com description + scope + allowed_agents + version."
        )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sensor YAML ↔ domain registries sync")
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="Exit 1 quando ghost_in_yaml > max-violations (CI mode)",
    )
    parser.add_argument(
        "--max-violations",
        type=int,
        default=0,
        metavar="N",
        help="Threshold para exit 1 em blocking mode (default 0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output JSON em vez de texto",
    )
    args = parser.parse_args(argv)

    report = run_sync_check()

    if args.json_output:
        print(json.dumps(report, indent=2))
    else:
        print(format_report(report))

    if args.blocking and len(report["ghost_in_yaml"]) > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
