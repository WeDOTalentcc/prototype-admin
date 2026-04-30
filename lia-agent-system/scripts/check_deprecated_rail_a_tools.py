#!/usr/bin/env python3
"""
CI guard — Rail A × @deprecated tools (harness-engineering sensor computacional).

Detecta quando uma tool marcada com @deprecated (decorator Python, não comentário)
ainda está mapeada como intent_hint ativo no capability_map.yaml do Rail A.

Regra: nenhum intent em capability_map.yaml pode apontar para uma tool com
@deprecated decorator — evita que cards do Rail A prometam features quebradas.

Execução: python scripts/check_deprecated_rail_a_tools.py
Exit 0 = ok. Exit 1 = violations encontradas.

Note: comentários # @deprecated since=... são ignorados (não são decorators).
"""
from __future__ import annotations
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def find_deprecated_tools() -> set[str]:
    """Retorna nomes de functions/methods com @deprecated decorator Python (não comentário)."""
    deprecated: list[str] = []
    for py_file in (ROOT / "app").rglob("*.py"):
        try:
            src = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Only parse files with actual @deprecated decorator (not just comments)
        if "@deprecated" not in src:
            continue
        # Skip if only comment-style deprecated
        if not re.search(r"^\s*@deprecated", src, re.MULTILINE):
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                name = ""
                if isinstance(dec, ast.Name):
                    name = dec.id
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    name = dec.func.id
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    name = dec.func.attr
                if name == "deprecated":
                    deprecated.append(node.name)
    return set(deprecated)


def load_capability_intents() -> list[str]:
    """Carrega intents do capability_map.yaml."""
    try:
        import yaml
        data = yaml.safe_load((ROOT / "app/config/capability_map.yaml").read_text())
        return list(data.get("capabilities", {}).keys())
    except Exception:
        return []


def find_intent_handlers(intents: list[str]) -> dict[str, str]:
    """Para cada intent, tenta localizar o handler declarado."""
    handlers: dict[str, str] = {}
    for py_file in (ROOT / "app").rglob("*.py"):
        try:
            src = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for intent in intents:
            if re.search(rf"def {re.escape(intent)}\b", src):
                handlers[intent] = py_file.name
    return handlers


def main() -> int:
    deprecated = find_deprecated_tools()
    intents = load_capability_intents()
    handlers = find_intent_handlers(intents)

    violations: list[str] = []
    for intent in intents:
        handler_name = handlers.get(intent, "")
        if handler_name and handler_name.replace(".py", "") in deprecated:
            violations.append(
                f"  VIOLATION: Rail A intent {intent!r} is wired to "
                f"@deprecated tool {handler_name!r} — remove from capability_map or undeprecate."
            )

    if violations:
        print("✗ check_deprecated_rail_a_tools: VIOLATIONS FOUND\n")
        for v in violations:
            print(v)
        print(
            "\nFix: either remove the intent from capability_map.yaml OR undeprecate the tool.\n"
            "Ref: harness-engineering sensor — docs/harness/RAIL_A_GUARDS.md"
        )
        return 1

    print(f"✓ check_deprecated_rail_a_tools: {len(intents)} intents, {len(deprecated)} @deprecated functions — no conflicts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
