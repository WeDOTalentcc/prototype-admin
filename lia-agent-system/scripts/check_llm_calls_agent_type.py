#!/usr/bin/env python3
"""
Sensor canonical (F11, 2026-05-24): detecta chamadas LLM sem `agent_type`
parameter, que default ao 2K token ceiling.

Contexto: `container.generate_with_fallback(...)` aplica token budget guard via
`DEFAULT_REQUEST_LIMIT=2000` quando `plan_code=None` E `agent_type=None`. Prompts
acima de 2K (system + context + expected output) são bloqueados com HTTP 500
"Request excede ceiling: X estimados > 2,000 permitidos".

Para evitar bloqueio silencioso, endpoints DEVEM passar `agent_type="<Name>Agent"`
correspondente a uma entry em `AGENT_TYPE_REQUEST_OVERRIDES` (em
`app/domains/credits/services/token_budget_service.py`).

Modes:
  default (warn-only): exit 0
  --blocking: exit 1
"""
import argparse
import ast
import sys
from pathlib import Path


ROOT = Path("/home/runner/workspace/lia-agent-system/app")


def find_unsafe_calls(root: Path) -> list[tuple[str, int, str]]:
    """Return [(file, lineno, snippet)] for generate_with_fallback calls
    that don't pass agent_type kwarg."""
    violations = []
    for f in root.rglob("*.py"):
        if "__pycache__" in f.parts or "tests" in f.parts:
            continue
        try:
            source = f.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            # Match `.generate_with_fallback(...)` or `.llm_call_with_fallback(...)`
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in {"generate_with_fallback", "llm_call_with_fallback"}:
                continue
            # Check if agent_type kwarg present
            has_agent_type = any(kw.arg == "agent_type" for kw in node.keywords)
            if has_agent_type:
                continue
            line = source.splitlines()[node.lineno - 1].strip()
            violations.append((str(f), node.lineno, line))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true")
    args = parser.parse_args()

    print("check_llm_calls_agent_type.py\n")
    violations = find_unsafe_calls(ROOT)

    if not violations:
        print("✅ 0 violations — todos LLM calls passam agent_type explicitamente.")
        return 0

    for fp, ln, line in violations:
        rel = fp.replace("/home/runner/workspace/lia-agent-system/", "")
        print(f"  ⚠️  {rel}:{ln}")
        print(f"     {line[:120]}")
        print(f"     → Fix: add agent_type=\"<Name>Agent\" kwarg")
        print(f"            Register override in AGENT_TYPE_REQUEST_OVERRIDES")
        print(f"            (token_budget_service.py) if cap >2000 needed")
        print()

    print(f"Total: {len(violations)} LLM call(s) without agent_type.")
    return 1 if args.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
