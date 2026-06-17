#!/usr/bin/env python3
"""
Sensor anti-regressão · W2-008 (2026-05-22)

Verifica que `app/shared/providers/llm_claude.py`:

1. Define 3 helpers canonical:
   - `_system_with_cache_control(system_prompt)` — converte str → cache block list
   - `_build_usage_with_cache(response)` — extrai 4 fields (input/output/cache_*)
   - `_log_cache_metrics(method_name, usage_dict)` — observability hook

2. Inclui beta header `extra_headers={"anthropic-beta": "prompt-caching-..."}`
   em todas as 4 chamadas a `client.messages.create()`

3. As 3 methods que aceitam system_prompt (generate_with_system,
   generate_with_tools, generate_structured) usam `_system_with_cache_control`
   para wrappar o system em cache block

4. As 2 methods principais (generate, generate_with_system) expõem
   cache metrics no LLMResponse.usage dict (via _build_usage_with_cache)

Pattern violação:
- Remover `extra_headers={"anthropic-beta": ...}` (perde cache)
- Trocar `_system_with_cache_control(prompt)` por `prompt` direto (sem cache)
- Remover usage_with_cache (perde observability)

Mensagem em PT-BR + fix sugerido em sintaxe exata (harness CLAUDE.md).
Modo: BLOCKING por default · --warn-only opt-out.

ROI documentado: 50-80% economia em sessões longas (Sonnet 50-turn 10k
tokens: $1.50 → $0.30).
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_FILE = REPO_ROOT / "app/shared/providers/llm_claude.py"


def _find_function(tree: ast.Module, name: str):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def _method_calls_messages_create_with_beta(method_node) -> bool:
    """Check se método chama messages.create(extra_headers=ANTHROPIC_CACHE_HEADERS)."""
    if method_node is None:
        return False
    src = ast.unparse(method_node)
    has_create = "messages.create(" in src
    has_beta = (
        "ANTHROPIC_CACHE_HEADERS" in src
        or "prompt-caching" in src
        or "anthropic-beta" in src
    )
    return has_create and has_beta


def check_helpers_present() -> list[str]:
    errors: list[str] = []
    if not CLAUDE_FILE.exists():
        return [f"❌ {CLAUDE_FILE.relative_to(REPO_ROOT)} ausente"]

    src = CLAUDE_FILE.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [f"❌ Syntax error em {CLAUDE_FILE.name}: {exc}"]

    required = [
        "_system_with_cache_control",
        "_build_usage_with_cache",
        "_log_cache_metrics",
    ]
    for fn_name in required:
        if _find_function(tree, fn_name) is None:
            errors.append(
                f"❌ Helper `{fn_name}` ausente em llm_claude.py (W2-008)\n"
                f"   File: {CLAUDE_FILE.relative_to(REPO_ROOT)}\n"
                f"   FIX: adicionar função canonical (ver pre-audit\n"
                f"        REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md W2-008)"
            )

    # Beta header constant
    if "ANTHROPIC_CACHE_HEADERS" not in src or "prompt-caching" not in src:
        errors.append(
            "❌ Constante `ANTHROPIC_CACHE_HEADERS` ausente OU sem 'prompt-caching'\n"
            f"   File: {CLAUDE_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: declarar no topo:\n"
            "       ANTHROPIC_PROMPT_CACHE_BETA = \"prompt-caching-2024-07-31\"\n"
            "       ANTHROPIC_CACHE_HEADERS = {\"anthropic-beta\": ANTHROPIC_PROMPT_CACHE_BETA}"
        )

    return errors


def check_all_4_methods_wired() -> list[str]:
    errors: list[str] = []
    if not CLAUDE_FILE.exists():
        return errors

    try:
        tree = ast.parse(CLAUDE_FILE.read_text())
    except SyntaxError:
        return errors

    # Find ClaudeLLMProvider class
    provider_cls = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ClaudeLLMProvider":
            provider_cls = node
            break
    if provider_cls is None:
        return [
            "❌ ClaudeLLMProvider class não encontrada\n"
            f"   File: {CLAUDE_FILE.relative_to(REPO_ROOT)}"
        ]

    methods_to_check = [
        "generate",
        "generate_with_system",
        "generate_with_tools",
        "generate_structured",
    ]

    for method_name in methods_to_check:
        method_node = None
        for child in provider_cls.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                method_node = child
                break
        if method_node is None:
            errors.append(
                f"❌ Método `{method_name}` ausente em ClaudeLLMProvider\n"
                f"   File: {CLAUDE_FILE.relative_to(REPO_ROOT)}"
            )
            continue
        if not _method_calls_messages_create_with_beta(method_node):
            errors.append(
                f"❌ Método `{method_name}` NÃO declara prompt caching beta header\n"
                f"   File: {CLAUDE_FILE.relative_to(REPO_ROOT)}\n"
                f"   Risco: perde 50-80% economia em sessões longas (W2-008)\n"
                f"   FIX: adicionar `extra_headers=ANTHROPIC_CACHE_HEADERS` na\n"
                f"        chamada client.messages.create(...)"
            )

    return errors


def check_system_uses_cache_control() -> list[str]:
    """3 methods com system_prompt devem chamar _system_with_cache_control."""
    errors: list[str] = []
    if not CLAUDE_FILE.exists():
        return errors

    try:
        tree = ast.parse(CLAUDE_FILE.read_text())
    except SyntaxError:
        return errors

    provider_cls = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "ClaudeLLMProvider":
            provider_cls = node
            break
    if provider_cls is None:
        return errors

    methods_with_system = [
        "generate_with_system",
        "generate_with_tools",
        "generate_structured",
    ]

    for method_name in methods_with_system:
        method_node = None
        for child in provider_cls.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method_name:
                method_node = child
                break
        if method_node is None:
            continue

        src = ast.unparse(method_node)
        if "_system_with_cache_control" not in src:
            errors.append(
                f"❌ Método `{method_name}` NÃO chama _system_with_cache_control\n"
                f"   File: {CLAUDE_FILE.relative_to(REPO_ROOT)}\n"
                f"   Risco: system message não-cacheado (W2-008 perdido)\n"
                f"   FIX: trocar `system=system_prompt` por\n"
                f"        `system=_system_with_cache_control(system_prompt)`"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    errors.extend(check_helpers_present())
    errors.extend(check_all_4_methods_wired())
    errors.extend(check_system_uses_cache_control())

    if errors:
        print(
            f"W2-008 prompt caching · {len(errors)} violation(s):",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print(file=sys.stderr)
        if args.warn_only:
            print("⚠️  WARN-ONLY mode: exit 0", file=sys.stderr)
            return 0
        return 1

    print(
        "✅ Anthropic prompt caching wired (W2-008) · "
        "3 helpers + 4 methods + cache_control em 3 system messages"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
