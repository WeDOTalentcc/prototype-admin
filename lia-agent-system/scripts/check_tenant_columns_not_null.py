#!/usr/bin/env python3
"""WT-2022 sensor: detect models com company_id = Column(..., nullable=True).

Pattern canonical (CLAUDE.md REGRA 6 multi-tenancy + ADR-LGPD-001):
tabelas que armazenam dados per-tenant DEVEM ter company_id NOT NULL.
Nullable=True abre brecha de cross-tenant data leak via legacy rows e
bypassa o gate de repository (qualquer caller que faca SQL bruto
ou skip filter passa direto).

Sensor scaneia libs/models/lia_models/*.py (Python-owned models;
ignora rails_models/ -- governanca Anderson) e flags violations.

Marker de exempcao:

    # TENANT-EXEMPT: <razao curta>  (linha imediatamente antes do Column)
    company_id = Column(..., nullable=True)

Razoes legitimas que justificam EXEMPT:
- Tabela global (sem dimensao tenant): admin_user_roles, alert_rule_templates
- Tabela legacy em deprecation
- Migration intermediaria (dual-write phase)

Modo: warn-only inicialmente. Promove para blocking via flag
--blocking quando baseline atingir 0 violations.

Uso CI:

    python lia-agent-system/scripts/check_tenant_columns_not_null.py
    # warn-only, exit 0 mesmo com violations

    python lia-agent-system/scripts/check_tenant_columns_not_null.py --blocking
    # exit 1 quando violations > 0

Para LLM consumidor: mensagem de fix vem inline na output (REGRA harness:
otimizar mensagens de sensor pra consumo de LLM, nao so humano).
"""
from __future__ import annotations

import argparse
import ast
import pathlib
import sys
from typing import Iterator, NamedTuple


MODELS_DIR = pathlib.Path("lia-agent-system/libs/models/lia_models")
EXEMPT_MARKER = "TENANT-EXEMPT"


class Violation(NamedTuple):
    path: pathlib.Path
    line_no: int
    class_name: str
    table_name: str


def _is_nullable_true(call: ast.Call) -> bool:
    """Retorna True se Column(...) tem nullable=True explicito."""
    for kw in call.keywords:
        if kw.arg == "nullable":
            if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                return True
    return False


def _is_column_call(call: ast.Call) -> bool:
    """Retorna True se call eh Column(...) ou sa.Column(...)."""
    if isinstance(call.func, ast.Name) and call.func.id == "Column":
        return True
    if isinstance(call.func, ast.Attribute) and call.func.attr == "Column":
        return True
    return False


def _extract_tablename(class_node: ast.ClassDef) -> str | None:
    """Pega __tablename__ = "..." do corpo da classe."""
    for stmt in class_node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == "__tablename__":
                    if isinstance(stmt.value, ast.Constant) and isinstance(
                        stmt.value.value, str
                    ):
                        return stmt.value.value
    return None


def _has_exempt_marker(source_lines: list[str], line_no: int) -> bool:
    """Verifica se linha anterior ao assign tem # TENANT-EXEMPT: ...."""
    # line_no eh 1-based; checar lines[line_no - 2] (linha imediatamente antes)
    idx = line_no - 2
    while idx >= 0:
        stripped = source_lines[idx].strip()
        if not stripped:
            idx -= 1
            continue
        if stripped.startswith("#") and EXEMPT_MARKER in stripped:
            return True
        return False
    return False


def find_violations(models_dir: pathlib.Path) -> Iterator[Violation]:
    """Yields Violation pra cada company_id nullable=True sem marker exempt."""
    for py_file in sorted(models_dir.rglob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue
        source_lines = source.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            tablename = _extract_tablename(node)
            if tablename is None:
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                # so checar targets chamados company_id
                target_ok = any(
                    isinstance(t, ast.Name) and t.id == "company_id"
                    for t in stmt.targets
                )
                if not target_ok:
                    continue
                if not isinstance(stmt.value, ast.Call):
                    continue
                if not _is_column_call(stmt.value):
                    continue
                if not _is_nullable_true(stmt.value):
                    continue
                if _has_exempt_marker(source_lines, stmt.lineno):
                    continue
                yield Violation(
                    path=py_file,
                    line_no=stmt.lineno,
                    class_name=node.name,
                    table_name=tablename,
                )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="Exit 1 quando violations encontradas (default: warn-only).",
    )
    parser.add_argument(
        "--models-dir",
        default=str(MODELS_DIR),
        help=f"Path para diretorio de models (default: {MODELS_DIR}).",
    )
    args = parser.parse_args()

    models_dir = pathlib.Path(args.models_dir)
    if not models_dir.exists():
        print(
            f"ERRO: models_dir nao existe: {models_dir}",
            file=sys.stderr,
        )
        return 1

    violations = list(find_violations(models_dir))
    if not violations:
        print("OK: all models com company_id tem nullable=False (ou marker TENANT-EXEMPT).")
        return 0

    mode = "BLOCKING" if args.blocking else "WARN-ONLY"
    print(
        f"[WT-2022 P0.TENANT_LOCKDOWN] {len(violations)} violations "
        f"(modo={mode}):"
    )
    print("")
    for v in violations:
        rel = v.path
        print(f"  {rel}:{v.line_no}")
        print(f"    class {v.class_name} (table={v.table_name})")
        print(f"    -> Fix: mudar nullable=True para nullable=False.")
        print(
            f"       Se houver legacy rows orfas, criar migration alembic com "
            f"backfill via FK indireta + ALTER COLUMN NOT NULL (pattern: "
            f"alembic/versions/161_tasks_company_id_not_null.py)."
        )
        print(
            f"       Se a tabela for legitimamente global (sem dimensao tenant), "
            f"adicionar marker em linha anterior:"
        )
        print(f"       # TENANT-EXEMPT: <razao> (ex: tabela global de templates)")
        print("")

    if args.blocking:
        print(f"FALHA: {len(violations)} violations em modo blocking.")
        return 1
    print(f"AVISO: {len(violations)} violations em modo warn-only. Exit 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
