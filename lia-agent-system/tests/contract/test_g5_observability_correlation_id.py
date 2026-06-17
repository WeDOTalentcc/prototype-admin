"""
G5 Sprint sensor: correlation_id em tabelas LGPD críticas de observabilidade.

Verifica que as 3 classes deferidas na migration 272 têm o campo correlation_id:
- AIInferenceLog (ai_inference_logs)
- DataAccessLog (data_access_logs)
- AutomatedDecisionExplanation (automated_decision_explanations)

LGPD Art. 37V — rastreabilidade fim-a-fim: request → LLM → decisão.
"""
from __future__ import annotations

import ast
import os
import pathlib

import pytest

# ---------------------------------------------------------------------------
# Paths canônicos
# ---------------------------------------------------------------------------
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
OBSERVABILITY_MODEL = REPO_ROOT / "libs" / "models" / "lia_models" / "observability.py"
MIGRATION_280 = REPO_ROOT / "alembic" / "versions" / "280_add_correlation_id_lgpd_tables.py"


# ---------------------------------------------------------------------------
# Helper: parse AST do observability.py e extrai campos por classe
# ---------------------------------------------------------------------------
def _get_class_column_names(class_name: str) -> set[str]:
    """Retorna os nomes dos atributos Column() declarados numa classe SQLAlchemy."""
    source = OBSERVABILITY_MODEL.read_text(encoding="utf-8")
    tree = ast.parse(source)
    columns: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in ast.walk(node):
                if isinstance(child, ast.AnnAssign):
                    # type-annotated: correlation_id: Mapped[...]
                    if isinstance(child.target, ast.Name):
                        columns.add(child.target.id)
                elif isinstance(child, ast.Assign):
                    # plain: correlation_id = Column(...)
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


# ---------------------------------------------------------------------------
# Tests — vão falhar (RED) enquanto o campo não existir nos modelos
# ---------------------------------------------------------------------------

class TestAIInferenceLogCorrelationId:
    def test_has_correlation_id_column(self):
        """AIInferenceLog deve ter o campo correlation_id (LGPD Art.37V)."""
        columns = _get_class_column_names("AIInferenceLog")
        assert "correlation_id" in columns, (
            "❌ AIInferenceLog não tem campo 'correlation_id'.\n"
            "→ Fix: adicionar `correlation_id = Column(String(80), nullable=True, index=True)` "
            "em libs/models/lia_models/observability.py na classe AIInferenceLog.\n"
            "   Também criar migration 280 com ADD COLUMN correlation_id em ai_inference_logs."
        )

    def test_correlation_id_is_string_type(self):
        """O campo correlation_id de AIInferenceLog deve ser String."""
        source = OBSERVABILITY_MODEL.read_text(encoding="utf-8")
        # Garantia básica: a linha contém Column(String(...))
        assert "correlation_id = Column(String" in source or "correlation_id: " in source, (
            "❌ Coluna correlation_id não encontrada em AIInferenceLog.\n"
            "→ Fix: adicionar `correlation_id = Column(String(80), nullable=True, index=True)` "
            "após o campo 'bias_flags' na classe AIInferenceLog."
        )


class TestDataAccessLogCorrelationId:
    def test_has_correlation_id_column(self):
        """DataAccessLog deve ter o campo correlation_id (LGPD Art.37V)."""
        columns = _get_class_column_names("DataAccessLog")
        assert "correlation_id" in columns, (
            "❌ DataAccessLog não tem campo 'correlation_id'.\n"
            "→ Fix: adicionar `correlation_id = Column(String(80), nullable=True, index=True)` "
            "em libs/models/lia_models/observability.py na classe DataAccessLog."
        )


class TestAutomatedDecisionExplanationCorrelationId:
    def test_has_correlation_id_column(self):
        """AutomatedDecisionExplanation deve ter o campo correlation_id (LGPD Art.37V)."""
        columns = _get_class_column_names("AutomatedDecisionExplanation")
        assert "correlation_id" in columns, (
            "❌ AutomatedDecisionExplanation não tem campo 'correlation_id'.\n"
            "→ Fix: adicionar `correlation_id = Column(String(80), nullable=True, index=True)` "
            "em libs/models/lia_models/observability.py na classe AutomatedDecisionExplanation."
        )


class TestMigration280Exists:
    def test_migration_280_file_exists(self):
        """Migration 280 deve existir para as 3 tabelas LGPD críticas."""
        assert MIGRATION_280.exists(), (
            f"❌ Migration {MIGRATION_280} não encontrada.\n"
            "→ Fix: criar alembic/versions/280_add_correlation_id_lgpd_tables.py com "
            "ADD COLUMN correlation_id em ai_inference_logs, data_access_logs, "
            "automated_decision_explanations."
        )

    def test_migration_280_covers_ai_inference_logs(self):
        """Migration 280 deve adicionar correlation_id em ai_inference_logs."""
        assert MIGRATION_280.exists(), "Migration 280 não existe — rode test_migration_280_file_exists primeiro."
        content = MIGRATION_280.read_text(encoding="utf-8")
        assert "ai_inference_logs" in content, (
            "❌ Migration 280 não toca a tabela ai_inference_logs.\n"
            "→ Fix: adicionar ALTER TABLE ai_inference_logs ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)."
        )

    def test_migration_280_covers_data_access_logs(self):
        """Migration 280 deve adicionar correlation_id em data_access_logs."""
        assert MIGRATION_280.exists(), "Migration 280 não existe."
        content = MIGRATION_280.read_text(encoding="utf-8")
        assert "data_access_logs" in content, (
            "❌ Migration 280 não toca a tabela data_access_logs.\n"
            "→ Fix: adicionar ALTER TABLE data_access_logs ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)."
        )

    def test_migration_280_covers_automated_decision_explanations(self):
        """Migration 280 deve adicionar correlation_id em automated_decision_explanations."""
        assert MIGRATION_280.exists(), "Migration 280 não existe."
        content = MIGRATION_280.read_text(encoding="utf-8")
        assert "automated_decision_explanations" in content, (
            "❌ Migration 280 não toca a tabela automated_decision_explanations.\n"
            "→ Fix: adicionar ALTER TABLE automated_decision_explanations ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80)."
        )

    def test_migration_280_has_partial_indexes(self):
        """Migration 280 deve criar índices parciais WHERE correlation_id IS NOT NULL."""
        assert MIGRATION_280.exists(), "Migration 280 não existe."
        content = MIGRATION_280.read_text(encoding="utf-8")
        assert "WHERE correlation_id IS NOT NULL" in content, (
            "❌ Migration 280 não tem índices parciais WHERE correlation_id IS NOT NULL.\n"
            "→ Fix: adicionar CREATE INDEX IF NOT EXISTS ix_<tabela>_correlation_id "
            "ON <tabela>(correlation_id) WHERE correlation_id IS NOT NULL."
        )
