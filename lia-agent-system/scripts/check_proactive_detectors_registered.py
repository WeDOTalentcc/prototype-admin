#!/usr/bin/env python3
"""WT-2022 Camada IA Proativa: AST sensor anti-regressao.

Garante que TODA classe `XxxDetector(BaseDetector)` declarada em
`app/shared/services/proactive_detector_service.py` aparece dentro da
inicializacao de `ProactiveDetectorService.detectors`.

Padrao de erro classico:
- Dev adiciona NewFooDetector(BaseDetector), esquece de incluir em
  `self.detectors = [...]`. Service nunca chama o detector novo.
  Bug silencioso, descoberto so semanas depois.

Esse sensor roda como pre-commit + CI step (warn-only no inicio, blocking
quando baseline = 0).

Exemplo de uso:
    python scripts/check_proactive_detectors_registered.py
    python scripts/check_proactive_detectors_registered.py --warn-only

Exit codes:
- 0: tudo registrado
- 1: detector declarado mas nao registrado (a menos que --warn-only)
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

CANONICAL_FILE = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "shared"
    / "services"
    / "proactive_detector_service.py"
)

ABSTRACT_BASE = "BaseDetector"
ORCHESTRATOR = "ProactiveDetectorService"


def _find_detector_classes(tree: ast.AST) -> list[str]:
    """Retorna nomes de classes que herdam de BaseDetector (excluindo o proprio)."""
    detectors: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name == ABSTRACT_BASE:
            continue
        for base in node.bases:
            base_name = ""
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name == ABSTRACT_BASE:
                detectors.append(node.name)
                break
    return detectors


def _find_registered_detectors(tree: ast.AST) -> set[str]:
    """Procura dentro de ProactiveDetectorService.__init__ o self.detectors = [...].
    Retorna set de nomes de classe registrados.
    """
    registered: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        if node.name != ORCHESTRATOR:
            continue
        for item in node.body:
            if not isinstance(item, ast.FunctionDef):
                continue
            if item.name != "__init__":
                continue
            for stmt in ast.walk(item):
                # self.detectors = [Cls(), ...]  (ast.Assign)
                target: ast.AST | None = None
                value: ast.AST | None = None
                if (
                    isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Attribute)
                ):
                    target = stmt.targets[0]
                    value = stmt.value
                # self.detectors: list[BaseDetector] = [Cls(), ...]  (ast.AnnAssign)
                elif (
                    isinstance(stmt, ast.AnnAssign)
                    and isinstance(stmt.target, ast.Attribute)
                ):
                    target = stmt.target
                    value = stmt.value

                if (
                    target is not None
                    and isinstance(target, ast.Attribute)
                    and target.attr == "detectors"
                    and isinstance(value, ast.List)
                ):
                    for elt in value.elts:
                        if isinstance(elt, ast.Call) and isinstance(
                            elt.func, ast.Name
                        ):
                            registered.add(elt.func.id)
    return registered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print warnings but exit 0 (ratchet mode)",
    )
    args = parser.parse_args()

    if not CANONICAL_FILE.exists():
        print(
            f"ERRO: arquivo canonical nao encontrado: {CANONICAL_FILE}",
            file=sys.stderr,
        )
        return 1

    source = CANONICAL_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    declared = _find_detector_classes(tree)
    registered = _find_registered_detectors(tree)

    missing = [name for name in declared if name not in registered]

    if not missing:
        print(
            f"OK: {len(declared)} detectors declarados, todos registrados em "
            f"{ORCHESTRATOR}.detectors"
        )
        return 0

    print(
        "ERRO: detectors declarados mas NAO registrados em "
        f"{ORCHESTRATOR}.detectors:",
        file=sys.stderr,
    )
    for name in missing:
        print(f"  - {name}", file=sys.stderr)
    print(
        "\nFix sugerido: adicionar no `__init__` do ProactiveDetectorService:\n"
        "    self.detectors: list[BaseDetector] = [\n"
        "        ...existing...,\n"
        + "\n".join(f"        {name}()," for name in missing)
        + "\n    ]",
        file=sys.stderr,
    )

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
