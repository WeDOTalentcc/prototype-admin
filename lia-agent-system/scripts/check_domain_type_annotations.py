#!/usr/bin/env python3
"""ADR-031 §6.1 — verifica __domain_type__ em todos os domínios.

Sensor computacional AST-based.
Exit 0 = sem violations. Exit 1 = violations encontradas (modo blocking).
"""
import ast
import sys
from pathlib import Path

DOMAINS_ROOT = Path(__file__).parent.parent / "app" / "domains"
VALID_TYPES = {"agentic", "service"}

# Dirs que NAO sao dominios reais
_SKIP_DIRS = {"__pycache__", "_template"}


def check_domain(domain_dir: Path) -> list:
    init_file = domain_dir / "__init__.py"
    if not init_file.exists():
        return [
            "  [NO_INIT] {}/__init__.py ausente — ADR-031 §6.1 requer __init__.py com __domain_type__\n"
            "  -> Fix: criar {}/__init__.py com __domain_type__ = \"agentic\"  # ou \"service\"".format(
                domain_dir.name, domain_dir.name
            )
        ]

    source = init_file.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return ["  [SYNTAX_ERROR] {}/__init__.py: {}".format(domain_dir.name, e)]

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__domain_type__":
                    if isinstance(node.value, ast.Constant):
                        val = node.value.value
                        if val not in VALID_TYPES:
                            return [
                                "  [INVALID_TYPE] {}/__init__.py: __domain_type__ = {!r} invalido. "
                                "Valores validos: {}\n"
                                "  -> Fix: __domain_type__ = \"agentic\"  # ou \"service\"".format(
                                    domain_dir.name, val, VALID_TYPES
                                )
                            ]
                    return []  # annotation presente e valida

    return [
        "  [MISSING] {}/__init__.py: __domain_type__ ausente (ADR-031 §6.1).\n"
        "  -> Fix: adicionar __domain_type__ = \"agentic\"  # dominio com domain.py/agents/\n"
        "          ou    __domain_type__ = \"service\"   # dominio so com services/repos".format(
            domain_dir.name
        )
    ]


def main():
    warn_only = "--warn-only" in sys.argv

    if not DOMAINS_ROOT.exists():
        print("ERRO: {} nao encontrado.".format(DOMAINS_ROOT))
        return 1

    violations = []
    checked = 0
    for domain_dir in sorted(DOMAINS_ROOT.iterdir()):
        if not domain_dir.is_dir():
            continue
        if domain_dir.name in _SKIP_DIRS or domain_dir.name.startswith("_"):
            continue
        violations.extend(check_domain(domain_dir))
        checked += 1

    if violations:
        print(
            "ADR-031 §6.1 — __domain_type__ annotation ausente ou invalida: "
            "{} violation(s) em {} dominios".format(len(violations), checked)
        )
        for v in violations:
            print(v)
        if warn_only:
            print("\n[warn-only] Violations encontradas mas modo warn. Exit 0.")
            return 0
        return 1

    print("ADR-031 §6.1 OK — todos os {} dominios tem __domain_type__ valido.".format(checked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
