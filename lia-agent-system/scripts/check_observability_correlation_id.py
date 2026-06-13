#!/usr/bin/env python3
"""
Sensor G5 — verifica que as tabelas LGPD críticas de observabilidade têm
correlation_id nos modelos SQLAlchemy e que audit_service chama get_correlation_id().

LGPD Art.37V: rastreabilidade fim-a-fim request → LLM → decisão.

Uso:
    python3 scripts/check_observability_correlation_id.py          # warn-only (default)
    python3 scripts/check_observability_correlation_id.py --block  # exit 1 se violations

Output otimizado para consumo de LLM: cada violation inclui instrução de correção.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OBSERVABILITY_MODEL = REPO_ROOT / "libs" / "models" / "lia_models" / "observability.py"
AUDIT_SERVICE = REPO_ROOT / "app" / "shared" / "compliance" / "audit_service.py"
MIGRATION_280 = REPO_ROOT / "alembic" / "versions" / "280_add_correlation_id_lgpd_tables.py"

REQUIRED_CLASSES = [
    "AIInferenceLog",
    "DataAccessLog",
    "AutomatedDecisionExplanation",
]


def _get_class_column_names(source: str, class_name: str) -> set[str]:
    """Extrai atributos Column() declarados numa classe SQLAlchemy via AST."""
    tree = ast.parse(source)
    columns: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for t in child.targets:
                        if isinstance(t, ast.Name):
                            val = child.value
                            if isinstance(val, ast.Call):
                                func_name = ""
                                if isinstance(val.func, ast.Name):
                                    func_name = val.func.id
                                elif isinstance(val.func, ast.Attribute):
                                    func_name = val.func.attr
                                if func_name == "Column":
                                    columns.add(t.id)
    return columns


def check_model_fields() -> list[str]:
    """Verifica que as 3 classes têm correlation_id no modelo."""
    violations: list[str] = []
    if not OBSERVABILITY_MODEL.exists():
        violations.append(
            f"[observability.py:0] MODELO NÃO ENCONTRADO: {OBSERVABILITY_MODEL}\n"
            "→ Fix: verificar caminho libs/models/lia_models/observability.py"
        )
        return violations

    source = OBSERVABILITY_MODEL.read_text(encoding="utf-8")
    for cls_name in REQUIRED_CLASSES:
        cols = _get_class_column_names(source, cls_name)
        if "correlation_id" not in cols:
            violations.append(
                f"[observability.py] {cls_name} | campo correlation_id AUSENTE\n"
                f"→ Fix: adicionar `correlation_id = Column(String(80), nullable=True, index=True)` "
                f"em libs/models/lia_models/observability.py na classe {cls_name}.\n"
                f"   Também verificar migration 280 (ADD COLUMN em tabela correspondente)."
            )
    return violations


def check_audit_service_uses_correlation_id() -> list[str]:
    """Verifica que audit_service chama get_correlation_id() antes de gravar."""
    violations: list[str] = []
    if not AUDIT_SERVICE.exists():
        violations.append(
            f"[audit_service.py:0] ARQUIVO NÃO ENCONTRADO: {AUDIT_SERVICE}\n"
            "→ Fix: verificar caminho app/shared/compliance/audit_service.py"
        )
        return violations

    source = AUDIT_SERVICE.read_text(encoding="utf-8")
    if "get_correlation_id" not in source:
        violations.append(
            "[audit_service.py] get_correlation_id() NÃO encontrada\n"
            "→ Fix: importar e chamar get_correlation_id() de app.middleware.request_id "
            "antes de gravar em ai_inference_logs / data_access_logs / automated_decision_explanations.\n"
            "   Pattern canônico:\n"
            "     from app.middleware.request_id import get_correlation_id\n"
            "     _correlation_id = get_correlation_id() or None"
        )
    return violations


def check_migration_280() -> list[str]:
    """Verifica que a migration 280 existe e cobre as 3 tabelas."""
    violations: list[str] = []
    if not MIGRATION_280.exists():
        violations.append(
            f"[alembic/versions] 280_add_correlation_id_lgpd_tables.py AUSENTE\n"
            "→ Fix: criar alembic/versions/280_add_correlation_id_lgpd_tables.py com "
            "ADD COLUMN correlation_id VARCHAR(80) + índice parcial WHERE correlation_id IS NOT NULL "
            "em ai_inference_logs, data_access_logs, automated_decision_explanations.\n"
            "   down_revision = '279_add_stakeholders_to_job_vacancies'"
        )
        return violations

    content = MIGRATION_280.read_text(encoding="utf-8")
    expected_tables = [
        "ai_inference_logs",
        "data_access_logs",
        "automated_decision_explanations",
    ]
    for table in expected_tables:
        if table not in content:
            violations.append(
                f"[280_migration] Tabela '{table}' NÃO coberta pela migration 280\n"
                f"→ Fix: adicionar ALTER TABLE {table} ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80) "
                f"+ CREATE INDEX IF NOT EXISTS ix_{table[:30]}_correlation_id ON {table}(correlation_id) "
                f"WHERE correlation_id IS NOT NULL."
            )

    if "WHERE correlation_id IS NOT NULL" not in content:
        violations.append(
            "[280_migration] Índices parciais WHERE correlation_id IS NOT NULL AUSENTES\n"
            "→ Fix: adicionar CREATE INDEX ... WHERE correlation_id IS NOT NULL para cada tabela. "
            "Índices parciais evitam overhead em rows NULL (a maioria em logs históricos)."
        )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Sensor G5: correlation_id em tabelas LGPD críticas")
    parser.add_argument("--block", action="store_true", help="Exit 1 se houver violations (modo blocking)")
    args = parser.parse_args()

    all_violations: list[str] = []
    all_violations.extend(check_model_fields())
    all_violations.extend(check_audit_service_uses_correlation_id())
    all_violations.extend(check_migration_280())

    if not all_violations:
        print("✅ Sensor G5 — OK: correlation_id presente nas 3 tabelas LGPD críticas.")
        print("   ai_inference_logs ✓  data_access_logs ✓  automated_decision_explanations ✓")
        print("   audit_service usa get_correlation_id() ✓")
        print("   Migration 280 presente e completa ✓")
        return 0

    print(f"⚠️  Sensor G5 — {len(all_violations)} violation(s) encontrada(s):\n")
    for i, v in enumerate(all_violations, 1):
        print(f"  [{i}] {v}\n")

    if args.block:
        print(f"❌ Modo --block: {len(all_violations)} violation(s). Corrija antes de continuar.")
        return 1

    print("ℹ️  Modo warn-only. Use --block para falhar em CI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
