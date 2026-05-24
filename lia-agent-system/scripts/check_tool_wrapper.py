#!/usr/bin/env python3
"""
Bug 3 sensor canonical: detecta tools registradas via tool_registry.register
ou em get_*_tools() registries cujo handler= aponta DIRETO para uma função
que exige _context (chama context_or_raise / require_company_id_from_context)
sem passar por um wrapper canonical _wrap_X que reconstrói SimpleNamespace.

Causa raiz Bug 3: ToolExecutor global não injeta _context em kwargs.
Handler que chama context_or_raise sem _context levanta
ToolContextMissingError em runtime.

Run:
    python3 lia-agent-system/scripts/check_tool_wrapper_canonical.py
    python3 lia-agent-system/scripts/check_tool_wrapper_canonical.py --blocking

Output: [file:line] description → Fix sugestão

Skill canonical: harness-engineering [sensor computacional].
"""
import argparse
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAINS_DIR = ROOT / "app" / "domains"


class Visitor(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.violations: list[tuple[int, str, str]] = []
        # Map of function name → AST FunctionDef
        self.functions: dict[str, ast.AsyncFunctionDef | ast.FunctionDef] = {}
        self.registrations: list[tuple[int, str]] = []

    def visit_AsyncFunctionDef(self, node):
        self.functions[node.name] = node
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.functions[node.name] = node
        self.generic_visit(node)

    def visit_Call(self, node):
        # Look for ToolDefinition(name=..., handler=X, ...) or function=X
        if isinstance(node.func, ast.Name) and node.func.id == "ToolDefinition":
            for kw in node.keywords:
                if kw.arg in ("handler", "function") and isinstance(kw.value, ast.Name):
                    self.registrations.append((kw.value.lineno, kw.value.id))
        self.generic_visit(node)


def function_uses_context_or_raise(func_node: ast.AST) -> bool:
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            fname = ""
            if isinstance(node.func, ast.Name):
                fname = node.func.id
            elif isinstance(node.func, ast.Attribute):
                fname = node.func.attr
            if fname in ("context_or_raise", "require_company_id_from_context"):
                return True
    return False


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []
    v = Visitor(path)
    v.visit(tree)
    violations: list[tuple[int, str, str]] = []
    for lineno, handler_name in v.registrations:
        # If handler name starts with _wrap_, OK (wrapper canonical pattern)
        if handler_name.startswith("_wrap_"):
            continue
        # Get the function body
        func = v.functions.get(handler_name)
        if func is None:
            continue  # External import — can't verify, skip
        if function_uses_context_or_raise(func):
            violations.append((
                lineno,
                f"Tool registrada com handler={handler_name} que requer _context (chama context_or_raise) sem wrapper canonical",
                f"Criar `async def _wrap_{handler_name}(**kwargs)` que faz "
                f"`ctx = SimpleNamespace(company_id=kwargs.get('company_id'), user_id=kwargs.get('user_id'))` "
                f"e chama `await {handler_name}(_context=ctx, ...)`. Apontar handler= pro wrapper. "
                f"Mirror pattern de _wrap_save_hiring_policy (Bug 3 fix 2026-05-24).",
            ))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocking", action="store_true")
    args = parser.parse_args()

    all_violations: list[tuple[Path, int, str, str]] = []
    for py in DOMAINS_DIR.rglob("*.py"):
        if "__pycache__" in py.parts or "tests" in py.parts:
            continue
        for lineno, desc, fix in scan_file(py):
            all_violations.append((py, lineno, desc, fix))

    if not all_violations:
        print("✅ check_tool_wrapper_canonical: 0 violations")
        return 0

    print(f"⚠️  check_tool_wrapper_canonical: {len(all_violations)} violation(s)")
    for path, lineno, desc, fix in all_violations:
        rel = path.relative_to(ROOT)
        print(f"  [{rel}:{lineno}] {desc}")
        print(f"  → Fix: {fix}\n")

    if args.blocking:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
