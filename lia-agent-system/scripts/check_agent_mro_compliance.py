#!/usr/bin/env python3
"""Sensor canônico (AST): todo agente que herda LangGraphReActBase DEVE herdar
TenantAwareAgentMixin.

Origem: Gap G (auditoria enterprise-readiness 2026-06-08). CustomAgentRuntime
(Agent Studio) herdava (LangGraphReActBase, EnhancedAgentMixin) SEM
TenantAwareAgentMixin — privando agentes do Studio do strict-mode gate de
tenant context (MissingTenantContextError) e do filtro de snippet degradado.
Não havia guard computacional que forçasse a cadeia de herança canônica.

Este sensor é puro AST (não-inferencial, sem LLM, sem DB): parseia cada arquivo
.py, encontra ClassDef cujos bases incluem `LangGraphReActBase`, e exige
`TenantAwareAgentMixin` nos bases. Docstrings/templates/strings são ignorados
naturalmente (não são ClassDef no AST).

Regra de ordem (recomendada, warn): TenantAwareAgentMixin deve vir ANTES de
LangGraphReActBase no MRO — o override async de `_process_langgraph` precisa
preceder o do base. Violação de ordem é WARN; ausência total é ERRO.

Uso:
    python3 scripts/check_agent_mro_compliance.py            # blocking (exit 1 se violação)
    python3 scripts/check_agent_mro_compliance.py --json     # saída JSON p/ CI tooling
    python3 scripts/check_agent_mro_compliance.py --warn-only # exit 0 sempre

Baseline 2026-06-08: 0 violações (18 agentes, todos com o mixin).
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

BASE_CLASS = "LangGraphReActBase"
REQUIRED_MIXIN = "TenantAwareAgentMixin"

# Diretórios varridos (código real de agentes vive aqui)
SCAN_DIRS = ["app"]
# Arquivos a ignorar (definição da própria base + scaffolding/templates)
IGNORE_SUFFIXES = (
    "langgraph_react_base.py",  # define a base, não a herda
    "agent_scaffold.py",        # template string (já ignorado pelo AST, mas defensivo)
)


def _base_names(node: ast.ClassDef) -> list[str]:
    """Extrai os nomes simples dos bases de uma ClassDef (Name ou Attribute)."""
    names: list[str] = []
    for b in node.bases:
        if isinstance(b, ast.Name):
            names.append(b.id)
        elif isinstance(b, ast.Attribute):
            names.append(b.attr)
    return names


def scan_file(path: Path) -> list[dict]:
    """Retorna lista de violações no arquivo (cada uma é um dict)."""
    violations: list[dict] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return violations

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = _base_names(node)
        if BASE_CLASS not in bases:
            continue
        # A própria definição da base nunca se herda; defensivo.
        if node.name == BASE_CLASS:
            continue
        if REQUIRED_MIXIN not in bases:
            violations.append({
                "file": str(path),
                "line": node.lineno,
                "klass": node.name,
                "severity": "error",
                "reason": (
                    f"'{node.name}' herda {BASE_CLASS} sem {REQUIRED_MIXIN} — "
                    f"agente escapa do strict-mode gate de tenant context (LGPD)."
                ),
                "fix": (
                    f"class {node.name}({REQUIRED_MIXIN}, {BASE_CLASS}, ...): "
                    f"adicione {REQUIRED_MIXIN} como PRIMEIRO base."
                ),
            })
            continue
        # Ordem: mixin deve preceder a base no MRO.
        if bases.index(REQUIRED_MIXIN) > bases.index(BASE_CLASS):
            violations.append({
                "file": str(path),
                "line": node.lineno,
                "klass": node.name,
                "severity": "warning",
                "reason": (
                    f"'{node.name}': {REQUIRED_MIXIN} vem DEPOIS de {BASE_CLASS} no MRO — "
                    f"o override de _process_langgraph do mixin não precederá o do base."
                ),
                "fix": (
                    f"reordene: class {node.name}({REQUIRED_MIXIN}, {BASE_CLASS}, ...)"
                ),
            })
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="saída JSON")
    parser.add_argument("--warn-only", action="store_true", help="exit 0 sempre")
    parser.add_argument("--max-violations", type=int, default=0)
    parser.add_argument("--root", default=".", help="raiz do projeto")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    all_violations: list[dict] = []
    for scan_dir in SCAN_DIRS:
        base = root / scan_dir
        if not base.exists():
            continue
        for py in base.rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            if str(py).endswith(IGNORE_SUFFIXES):
                continue
            all_violations.extend(scan_file(py))

    errors = [v for v in all_violations if v["severity"] == "error"]
    warnings = [v for v in all_violations if v["severity"] == "warning"]

    if args.json:
        print(json.dumps({
            "total": len(all_violations),
            "errors": len(errors),
            "warnings": len(warnings),
            "violations": all_violations,
        }, indent=2, ensure_ascii=False))
    else:
        for v in all_violations:
            mark = "❌" if v["severity"] == "error" else "⚠️"
            rel = v["file"].replace(str(root) + "/", "")
            print(f"{mark} [{rel}:{v['line']}] {v['reason']}")
            print(f"   → Fix: {v['fix']}")
        if not all_violations:
            print(f"✅ check_agent_mro_compliance: 0 violações "
                  f"(todos os agentes que herdam {BASE_CLASS} têm {REQUIRED_MIXIN}).")

    if args.warn_only:
        return 0
    if len(errors) > args.max_violations:
        print(f"\n❌ {len(errors)} erro(s) de MRO compliance (max permitido: "
              f"{args.max_violations}). Veja AI_LAYER_TREE.md §12.3 / Gap G.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
