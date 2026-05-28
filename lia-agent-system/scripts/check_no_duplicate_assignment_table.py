#!/usr/bin/env python3
"""
Sensor canonical-fix: detecta criação de tabela paralela a AgentDeployment.

Princípio canonical (Onda 3 — Fase 2 Agent Studio, registrado 2026-05-27):
  AgentDeployment é a tabela canonical pra acoplar agentes a targets
  (jobs, pools, pipeline_stages, candidate_lists). NÃO criar tabela
  separada `job_agent_assignments`, `pipeline_agent_assignments`, ou
  similar — quebra o canonical-fix #1 (1 fonte de verdade) e
  desincroniza counters (execution_count, candidates_processed).

Esse sensor falha quando encontrar:
  1. Migration alembic criando tabela com nome banido.
  2. Model SQLAlchemy declarando __tablename__ banido.

Honra marker `# DUPLICATE-TABLE-EXEMPT: <reason>` quando, em casos raros,
uma migration legacy é mantida pra rollback histórico (sem caller real).

Exit codes:
  0 = ok ou warn-only mode
  1 = blocking mode + violations encontradas

Uso:
  python3 scripts/check_no_duplicate_assignment_table.py            # blocking (default)
  python3 scripts/check_no_duplicate_assignment_table.py --warn-only
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Tabelas banidas — paralelas ao AgentDeployment canonical.
BANNED_TABLE_NAMES = {
    "job_agent_assignments",
    "pipeline_agent_assignments",
    "pipeline_stage_agent_assignments",
    "candidate_list_agent_assignments",
    "talent_pool_agent_assignments",  # tabela legacy do Sprint 7C deve-se manter, NÃO neste set
    "job_agent_bindings",
    "stage_agent_bindings",
    "vacancy_agent_assignments",
}

# Allowlist — tabelas legitimamente existentes (não banidas) para evitar
# falso positivo quando o sensor encontra um match de substring.
# (Hoje 2026-05-27 não há nenhum nome bem-formado no allowlist; deixar
# expansível pra futuras coincidências.)
ALLOWLIST_TABLE_NAMES: set[str] = set()

EXEMPT_MARKER = "DUPLICATE-TABLE-EXEMPT"

# Diretórios escaneados.
SCAN_DIRS = [
    REPO_ROOT / "alembic" / "versions",
    REPO_ROOT / "libs" / "models",
    REPO_ROOT / "app" / "models",
    REPO_ROOT / "app" / "domains",
]

# Skip canonical agent_deployment files (they reference legitimate model).
SKIP_FILES = {
    REPO_ROOT / "libs" / "models" / "lia_models" / "agent_deployment.py",
    REPO_ROOT / "app" / "models" / "agent_deployment.py",
    REPO_ROOT / "scripts" / "check_no_duplicate_assignment_table.py",
}


def has_exempt_marker(source_lines: list[str], lineno: int) -> bool:
    """Procura `# DUPLICATE-TABLE-EXEMPT: <reason>` ±2 linhas."""
    for delta in (-2, -1, 0, 1):
        idx = lineno - 1 + delta
        if 0 <= idx < len(source_lines):
            if EXEMPT_MARKER in source_lines[idx]:
                return True
    return False


def _extract_string_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _relative_or_absolute(file_path: Path) -> str:
    """Retorna path relativo ao REPO_ROOT quando possível, absoluto senão (para testes)."""
    try:
        return str(file_path.relative_to(REPO_ROOT))
    except ValueError:
        return str(file_path)


def find_violations(file_path: Path) -> list[dict]:
    """Retorna list of {file, line, kind, name, fix}."""
    if file_path.resolve() in {p.resolve() for p in SKIP_FILES}:
        return []

    try:
        source = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    source_lines = source.split("\n")
    violations: list[dict] = []

    for node in ast.walk(tree):
        # Pattern 1: __tablename__ = "banned"
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__tablename__":
                    val = _extract_string_value(node.value)
                    if val in BANNED_TABLE_NAMES and val not in ALLOWLIST_TABLE_NAMES:
                        if has_exempt_marker(source_lines, node.lineno):
                            continue
                        violations.append({
                            "file": _relative_or_absolute(file_path),
                            "line": node.lineno,
                            "kind": "model_tablename",
                            "name": val,
                            "fix": (
                                f"NÃO criar model com __tablename__='{val}'. "
                                "Use AgentDeployment (target_type='job'|'pipeline_stage'|"
                                "'talent_pool'|'candidate_list') em libs/models/lia_models/"
                                "agent_deployment.py. Se for migration legacy, marque com "
                                "`# DUPLICATE-TABLE-EXEMPT: <razão>`."
                            ),
                        })

        # Pattern 2: op.create_table("banned", ...) em alembic.
        if isinstance(node, ast.Call):
            func = node.func
            qualified = ""
            if isinstance(func, ast.Attribute):
                qualified = func.attr
            elif isinstance(func, ast.Name):
                qualified = func.id

            if qualified == "create_table" and node.args:
                first_arg = node.args[0]
                val = _extract_string_value(first_arg)
                if val in BANNED_TABLE_NAMES and val not in ALLOWLIST_TABLE_NAMES:
                    if has_exempt_marker(source_lines, node.lineno):
                        continue
                    violations.append({
                        "file": _relative_or_absolute(file_path),
                        "line": node.lineno,
                        "kind": "alembic_create_table",
                        "name": val,
                        "fix": (
                            f"NÃO crie tabela '{val}' via alembic. AgentDeployment já "
                            "cobre acoplar agente a target (job, pool, stage, list). "
                            "Se rollback histórico exigir manter, marque com "
                            "`# DUPLICATE-TABLE-EXEMPT: <razão>`."
                        ),
                    })

    return violations


def iter_python_files() -> list[Path]:
    out: list[Path] = []
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        out.extend(d.rglob("*.py"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="exit 0 mesmo com violations (default: blocking).",
    )
    args = parser.parse_args()

    all_violations: list[dict] = []
    for f in iter_python_files():
        all_violations.extend(find_violations(f))

    if not all_violations:
        print("OK — 0 violations. AgentDeployment é canonical sem drift.")
        return 0

    print(f"FALHA — {len(all_violations)} violation(s) de tabela paralela:")
    for v in all_violations:
        print(f"  [{v['file']}:{v['line']}] {v['kind']} '{v['name']}'")
        print(f"    Fix: {v['fix']}")

    if args.warn_only:
        print("\n(warn-only — exit 0)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
