#!/usr/bin/env python3
"""
Sensor anti-regressão · W1-002 (2026-05-22)

Bloqueia novos imports de `from app.agents.base_agent import ...` em
qualquer arquivo .py de app/, libs/ ou tests/, EXCETO o próprio shim
em `app/agents/base_agent.py`.

Canonical pós-W1-002: símbolos vivem em `app/shared/agents/agent_types.py`.
Legacy `app/agents/base_agent.py` é shim de retrocompat com DeprecationWarning.

Mensagem em PT-BR + fix sugerido em sintaxe exata (harness pattern CLAUDE.md
— output otimizado pra consumo do LLM consumidor do erro).

Modo: BLOCKING por default. Use `--warn-only` durante migração.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_ROOTS = ("app", "libs", "tests")
SELF_SHIM = "app/agents/base_agent.py"  # único arquivo permitido


def find_legacy_imports() -> list[tuple[Path, int, str]]:
    """Retorna lista (file_rel, lineno, símbolos_importados) com imports legacy."""
    offenders: list[tuple[Path, int, str]] = []

    for root_name in SCAN_ROOTS:
        root = REPO_ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            rel = path.relative_to(REPO_ROOT)
            if str(rel) == SELF_SHIM:
                continue
            if "__pycache__" in path.parts:
                continue

            try:
                src = path.read_text(encoding="utf-8")
                tree = ast.parse(src)
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    if mod == "app.agents.base_agent" or mod.endswith(
                        ".agents.base_agent"
                    ):
                        names = ", ".join(alias.name for alias in node.names)
                        offenders.append((rel, node.lineno, names))

    return offenders


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Reporta violações mas retorna exit 0 (uso durante migração).",
    )
    args = parser.parse_args()

    offenders = find_legacy_imports()

    if not offenders:
        print("✅ Nenhum import legacy de `app.agents.base_agent` (W1-002 limpo)")
        return 0

    print(
        f"❌ {len(offenders)} import(s) legacy de `app.agents.base_agent` encontrado(s):",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    for rel, lineno, names in offenders:
        print(f"  {rel}:{lineno}  →  importa: {names}", file=sys.stderr)

    print(file=sys.stderr)
    print(
        "FIX: substituir por canonical `app.shared.agents.agent_types`.\n"
        "    Símbolos canonical (W1-002 2026-05-22):\n"
        "      AgentType, TaskPriority, TaskStatus, AgentAction, AgentTask\n"
        "    Exemplo:\n"
        "      # ANTES\n"
        "      from app.agents.base_agent import AgentType\n"
        "      # DEPOIS\n"
        "      from app.shared.agents.agent_types import AgentType\n"
        "    Referência: sprint_logs/sprint_1.2/W1-002_AUDIT.md",
        file=sys.stderr,
    )

    if args.warn_only:
        print(
            "⚠️  WARN-ONLY mode: 0 exit despite violations (migração em curso)",
            file=sys.stderr,
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
