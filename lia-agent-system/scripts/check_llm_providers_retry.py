#!/usr/bin/env python3
"""Sensor (AST): todo metodo de provider LLM com @circuit_breaker_decorator DEVE
ter tambem @llm_transient_retry (retry transitorio 429/5xx) e o modulo DEVE
importar llm_transient_retry. Computacional, exit 1 em violacao.
Registrado 2026-06-05 (auditoria degradacao chat: retry middleware nao-aplicado).
"""
import ast
import sys
from pathlib import Path

PROVIDERS = [
    "app/shared/providers/llm_claude.py",
    "app/shared/providers/llm_gemini.py",
    "app/shared/providers/llm_openai.py",
    "app/shared/providers/llm_deepseek.py",
]


def _dec_name(d):
    t = d.func if isinstance(d, ast.Call) else d
    if isinstance(t, ast.Attribute):
        return t.attr
    if isinstance(t, ast.Name):
        return t.id
    return ""


def main():
    root = Path(__file__).resolve().parent.parent
    violations = []
    for rel in PROVIDERS:
        p = root / rel
        if not p.exists():
            continue
        tree = ast.parse(p.read_text(), filename=str(p))
        imports_retry = any(
            isinstance(n, ast.ImportFrom)
            and any(a.name == "llm_transient_retry" for a in n.names)
            for n in ast.walk(tree)
        )
        has_circuit = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                names = {_dec_name(d) for d in node.decorator_list}
                if "circuit_breaker_decorator" in names:
                    has_circuit = True
                    if "llm_transient_retry" not in names:
                        violations.append(
                            rel + ":" + str(node.lineno) + " " + node.name
                            + "() tem @circuit_breaker_decorator mas NAO @llm_transient_retry"
                        )
        if has_circuit and not imports_retry:
            violations.append(
                rel + " usa @circuit_breaker_decorator mas NAO importa llm_transient_retry"
            )
    if violations:
        print("FALHA: provider(s) LLM sem retry transitorio aplicado:")
        for v in violations:
            print("  - " + v)
        print("")
        print("-> Fix: '    @llm_transient_retry' LOGO ABAIXO de cada '@circuit_breaker_decorator(...)'")
        print("   (retry interno, circuit externo) + import de app.shared.providers.llm_retry.")
        sys.exit(1)
    print("OK: " + str(len(PROVIDERS)) + " providers com @llm_transient_retry em todos os metodos circuit-breaked.")
    sys.exit(0)


if __name__ == "__main__":
    main()
