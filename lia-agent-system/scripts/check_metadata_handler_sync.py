#!/usr/bin/env python3
"""Sensor G5: metadata YAML → handler sync (harness-engineering, Fase 1D).

Garante que toda tool declarada em tool_registry_metadata.yaml tem um handler
Python real em app/ (ToolDefinition com name="<tool>").

Ghost direction relevante: missing_in_registry = declarada no YAML mas SEM
handler Python. O LLM poderia ver a descrição de uma tool que nunca executa.

NÃO bloqueia em missing_in_yaml (tools registradas em Python mas não no YAML)
— essa direção é expected (maioria das 819 tools reais não estão no yaml,
e não queremos forçar a adição de todas).

Default warn-only (exit 0); --blocking exit 1 quando missing_in_registry > 0.

Uso:
    python3 scripts/check_metadata_handler_sync.py            # warn-only
    python3 scripts/check_metadata_handler_sync.py --blocking # CI gate G5

Modelo: scripts/check_capability_catalog_sync.py (padrão canonical do projeto).
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover
    _YAML_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parent.parent
METADATA_YAML = REPO_ROOT / "app" / "tools" / "tool_registry_metadata.yaml"


def extract_declared_names(source: str) -> set[str]:
    """Nomes de tool declarados como name="literal" em chamadas de função (ToolDefinition)."""
    names: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if (
                    kw.arg == "name"
                    and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, str)
                ):
                    names.add(kw.value.value)
    return names


def scan_declared_in_tree(app_dir: Path) -> set[str]:
    """Varre recursivamente app/ e coleta todos os nomes declarados."""
    names: set[str] = set()
    for py in app_dir.rglob("*.py"):
        if "__pycache__" in str(py):
            continue
        try:
            names |= extract_declared_names(py.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, UnicodeDecodeError):
            continue
    return names


def load_yaml_tool_names(path: Path) -> list[str]:
    """Carrega nomes de tools do tool_registry_metadata.yaml."""
    if not _YAML_AVAILABLE:
        print("ERRO: PyYAML não instalado — instale com: pip install pyyaml", file=sys.stderr)
        sys.exit(2)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    tools = data.get("tools") or []
    return [t["name"] for t in tools if isinstance(t, dict) and "name" in t]


def format_report(missing: list[str]) -> str:
    if not missing:
        return (
            "OK - 0 phantoms. Toda tool em tool_registry_metadata.yaml tem handler em app/."
        )
    lines = [
        f"ERRO: {len(missing)} phantom(s) em tool_registry_metadata.yaml sem handler Python:\n"
    ]
    for name in missing:
        lines.append(f"  - {name}")
        lines.append(
            f"    -> Fix: remova '{name}' de app/tools/tool_registry_metadata.yaml "
            f"(tool descontinuada sem handler), "
            f"OU adicione o handler ToolDefinition(name='{name}', ...) em app/."
        )
    lines.append(
        "\nNOTA: missing_in_yaml (tools com handler mas sem entrada no YAML) "
        "NÃO é verificada por este sensor — é a direção esperada (a maioria "
        "das tools reais não precisa de entrada no YAML de metadados)."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sensor G5: metadata YAML -> handler sync"
    )
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="exit 1 se missing_in_registry > 0",
    )
    args = parser.parse_args(argv)

    if not METADATA_YAML.exists():
        print(
            f"ERRO: {METADATA_YAML} não encontrado — sensor não pode rodar",
            file=sys.stderr,
        )
        return 2

    yaml_names = load_yaml_tool_names(METADATA_YAML)
    declared = scan_declared_in_tree(REPO_ROOT / "app")

    yaml_name_set = set(yaml_names)
    missing_in_registry = sorted(yaml_name_set - declared)

    print(format_report(missing_in_registry))
    print(
        f"\n[resumo] {len(missing_in_registry)} phantom(s) · "
        f"{len(yaml_names)} tools no YAML · "
        f"{len(declared)} nomes declarados em app/"
    )

    if args.blocking and missing_in_registry:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
