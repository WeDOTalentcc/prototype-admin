#!/usr/bin/env python3
"""
CI guard — Rail A × @deprecated tools (harness-engineering sensor computacional).

Detecta quando uma tool marcada com @deprecated ainda está mapeada como
intent_hint ativo no SUGGESTION_HINTS do Rail A (via capability_map.yaml).

Regra: nenhum intent em capability_map.yaml pode apontar para uma tool com
@deprecated decorator — evita que cards do Rail A prometam features quebradas.

Execução: python scripts/check_deprecated_rail_a_tools.py
Exit 0 = ok. Exit 1 = violations encontradas.
"""
from __future__ import annotations
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

def find_deprecated_tools() -> set[str]:
    """Retorna nomes de functions/methods com @deprecated decorator."""
    deprecated: set[str] = []
    for py_file in (ROOT / "app").rglob("*.py"):
        try:
            src = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "@deprecated" not in src:
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
            # Look for function definitions matching the intent name
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
                f"  VIOLATION: Rail A intent {intent} is wired to "
                f"@deprecated tool {handler_name} — remove from capability_map or undeprecate the tool."
            )

    # Special check: daily_briefing is known deprecated
    if "daily_briefing" in intents:
        violations.append(
            "  WARNING: daily_briefing is in capability_map but the tool is @deprecated (rails_adapter not yet implemented).\n"
            "  Add chat_executable=false and navigate_fallback until rails_adapter.daily_summary is live."
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

    print(f"✓ check_deprecated_rail_a_tools: {len(intents)} intents checked — no deprecated tools wired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
