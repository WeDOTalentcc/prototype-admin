#!/usr/bin/env python3
"""Sensor C1.5.3 (anti-recidiva): proíbe NOVOS writes em pool_agent_assignments.

Princípio canonical (Fase 2.5 Onda C1.5 — Opção A):
  agent_deployments é a junction canonical agente<->surface. pool_agent_assignments
  é LEGADO em desativação (read-only durante a transição, ver C1.5.4). Código novo
  DEVE escrever em agent_deployments, NUNCA criar/inserir pool_agent_assignments.

Esse sensor falha (BLOCKING) quando encontra, em código de PRODUÇÃO (app/), um
write na tabela legada:
  1. Instanciação `PoolAgentAssignment(...)`.
  2. `.add(PoolAgentAssignment(...))` (mesma coisa, padrão SQLAlchemy session).
  3. `INSERT INTO pool_agent_assignments` em SQL textual (exec_driver_sql/text).

NÃO falha em:
  - tests/ e alembic/versions/ (a data migration C1.5.1 PRECISA ler/escrever a
    tabela legada; testes a semeiam de propósito).
  - O próprio arquivo do sensor.
  - Linhas com marker `# CANONICAL-EXEMPT: <razão>` (±2 linhas) — usado nos write
    sites legados conhecidos durante a janela de transição (repository legado +
    sourcing orchestrator). Cada marker tem que vir com razão + backlog.

Output em PT-BR, otimizado pra consumo do LLM (fix embutido).

Exit codes:
  0 = ok ou --warn-only
  1 = blocking (default) + violations

Uso:
  python3 scripts/check_no_new_pool_agent_assignments.py            # blocking
  python3 scripts/check_no_new_pool_agent_assignments.py --warn-only

Refs:
  - AGENT_STUDIO_FASE2.5_PLANO_CONSOLIDACAO.md §Onda C1.5
  - scripts/check_no_duplicate_assignment_table.py (sensor irmão — nível schema)
  - alembic/versions/221_migrate_pool_assignments_to_deployments.py
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

MODEL_CLASS = "PoolAgentAssignment"
BANNED_TABLE = "pool_agent_assignments"
EXEMPT_MARKER = "CANONICAL-EXEMPT"

# Só escaneia código de produção. Migration + tests são exempt por design (a
# migration de dados C1.5.1 lê/escreve a tabela legada; tests a semeiam).
SCAN_DIRS = [REPO_ROOT / "app"]

# Regex pra INSERT textual (SQL em string), case-insensitive.
_INSERT_RE = re.compile(
    r"insert\s+into\s+" + re.escape(BANNED_TABLE), re.IGNORECASE
)

SELF_PATH = Path(__file__).resolve()


def has_exempt_marker(source_lines: list[str], lineno: int) -> bool:
    """Procura `# CANONICAL-EXEMPT: <razão>` em ±2 linhas do site."""
    for delta in (-2, -1, 0, 1, 2):
        idx = lineno - 1 + delta
        if 0 <= idx < len(source_lines):
            if EXEMPT_MARKER in source_lines[idx]:
                return True
    return False


def _relative(file_path: Path) -> str:
    try:
        return str(file_path.relative_to(REPO_ROOT))
    except ValueError:
        return str(file_path)


def _call_targets_model(node: ast.Call) -> bool:
    """True se o Call instancia PoolAgentAssignment (Name ou Attribute)."""
    func = node.func
    if isinstance(func, ast.Name) and func.id == MODEL_CLASS:
        return True
    if isinstance(func, ast.Attribute) and func.attr == MODEL_CLASS:
        return True
    return False


def find_violations(file_path: Path) -> list[dict]:
    if file_path.resolve() == SELF_PATH:
        return []
    try:
        source = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    source_lines = source.split("\n")
    violations: list[dict] = []

    # --- AST: instanciação PoolAgentAssignment(...) ---
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        tree = None

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _call_targets_model(node):
                if has_exempt_marker(source_lines, node.lineno):
                    continue
                violations.append({
                    "file": _relative(file_path),
                    "line": node.lineno,
                    "kind": "model_instantiation",
                    "fix": (
                        f"NÃO instancie {MODEL_CLASS}(...) — tabela legada em "
                        "desativação. Use AgentDeployment(target_type='talent_pool', "
                        "target_id=<pool_id>, agent_id=..., trigger_mode=...) em "
                        "libs/models/lia_models/agent_deployment.py. Se for write "
                        "legado mantido durante a transição, marque com "
                        "`# CANONICAL-EXEMPT: <razão + backlog>`."
                    ),
                })

    # --- Regex: INSERT INTO pool_agent_assignments em SQL textual ---
    for i, line in enumerate(source_lines):
        if _INSERT_RE.search(line):
            if has_exempt_marker(source_lines, i + 1):
                continue
            violations.append({
                "file": _relative(file_path),
                "line": i + 1,
                "kind": "sql_insert",
                "fix": (
                    f"NÃO faça INSERT INTO {BANNED_TABLE} — tabela legada. "
                    "Escreva em agent_deployments. Se for migration de dados, "
                    "mova pra alembic/versions/ (exempt). Caso raro de write "
                    "legado, marque `# CANONICAL-EXEMPT: <razão + backlog>`."
                ),
            })

    return violations


def iter_python_files() -> list[Path]:
    out: list[Path] = []
    for d in SCAN_DIRS:
        if d.exists():
            out.extend(d.rglob("*.py"))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only", action="store_true",
        help="exit 0 mesmo com violations (default: blocking).",
    )
    args = parser.parse_args()

    all_violations: list[dict] = []
    for f in iter_python_files():
        all_violations.extend(find_violations(f))

    if not all_violations:
        print(
            "OK — 0 violations. Nenhum write novo em pool_agent_assignments "
            "(agent_deployments é canonical)."
        )
        return 0

    print(
        f"FALHA — {len(all_violations)} write(s) novo(s) em "
        f"{BANNED_TABLE} (tabela legada):"
    )
    for v in all_violations:
        print(f"  [{v['file']}:{v['line']}] {v['kind']}")
        print(f"    Fix: {v['fix']}")

    if args.warn_only:
        print("\n(warn-only — exit 0)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
