#!/usr/bin/env python3
"""Wave E Sensor 6 — Detecta prompt builders sem referência a compliance_block.

Pattern canonical (Wave D1.2, 2026-05-27): todo system prompt builder DEVE
injetar compliance blocks via PromptComposer.compliance_blocks_for().
Sem isso, agentes operam sem guardrails LGPD/fairness — risco compliance P0.

Verifica em *prompt_builder*.py:
- Método build() referencia 'compliance_block' ou 'compliance_blocks_for'
  OU importa PromptComposer com esse propósito

O arquivo canônico system_prompt_builder.py JÁ está em conformidade.
Sensor detecta novos builders que esquecem de incluir.

Honra marker: # COMPLIANCE-EXEMPT: <reason>

Exit 0 = OK. Exit 1 = violations (BLOCKING).
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_ROOT = REPO_ROOT / "app"

# Patterns que indicam compliance injection presente
COMPLIANCE_PATTERNS = re.compile(
    r'compliance_block|compliance_blocks_for|PromptComposer\.compliance|'
    r'COMPLIANCE_BLOCK|LGPD_BLOCK|fairness_block|'
    r'compliance_blocks',
)

EXEMPT_MARKER = "COMPLIANCE-EXEMPT"


def check_builder_file(path: Path) -> list[tuple[int, str]]:
    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    # Checar marker de isenção no arquivo
    if EXEMPT_MARKER in content:
        return []

    # Verificar se arquivo tem método build()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    has_build_method = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "build"
        for node in ast.walk(tree)
    )

    if not has_build_method:
        return []

    # Verificar se tem referência a compliance injection
    if COMPLIANCE_PATTERNS.search(content):
        return []

    # Encontrar linha do método build para reportar
    build_lineno = 0
    for i, line in enumerate(lines, 1):
        if re.match(r'\s+(?:async\s+)?def\s+build\s*\(', line):
            build_lineno = i
            break

    return [(
        build_lineno or 1,
        f"Arquivo *prompt_builder* com método build() sem referência a compliance_block",
    )]


def main() -> int:
    blocking = "--warn-only" not in sys.argv
    all_violations: list[tuple[Path, int, str]] = []

    # Buscar todos *prompt_builder*.py
    builder_files = list(APP_ROOT.rglob("*prompt_builder*.py"))

    if not builder_files:
        print(f"[check_compliance_block_injection] ✅ Nenhum *prompt_builder*.py encontrado — OK.")
        return 0

    for path in sorted(builder_files):
        if "__pycache__" in str(path):
            continue
        for lineno, msg in check_builder_file(path):
            rel = path.relative_to(REPO_ROOT)
            all_violations.append((rel, lineno, msg))

    if not all_violations:
        print(f"[check_compliance_block_injection] ✅ 0 violations — todos builders com compliance injection.")
        return 0

    print(f"[check_compliance_block_injection] {'❌' if blocking else '⚠️'} {len(all_violations)} violation(s):\n")
    for rel_path, lineno, msg in all_violations:
        print(f"  [{rel_path}:{lineno}] {msg}")
        print(f"    → Fix: adicionar compliance injection no método build():")
        print(f"      from app.shared.prompts.prompt_composer import PromptComposer")
        print(f"      compliance_block = PromptComposer.compliance_blocks_for(agent_type)")
        print(f"      if compliance_block:")
        print(f"          sections.append(f'\\n## Compliance e Guardrails\\n{{compliance_block}}')")
        print(f"      Se builder não é para agentes IA, adicionar # COMPLIANCE-EXEMPT: <razão>")
        print()

    if blocking:
        print(f"[check_compliance_block_injection] BLOCKING — corrija antes de commitar.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
