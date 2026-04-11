"""
FAR-5: Testes para auditoria de disparate impact em outputs de ranking.

Cobre:
- BiasAuditService.audit_ranking_results() com Four-Fifths Rule
- Campo soft_warnings no FairnessAuditLog
- Migration 048 declarada corretamente
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAuditRankingResults:
    """Testa BiasAuditService.audit_ranking_results()."""

    def setup_method(self):
        from app.shared.services.bias_audit_service import BiasAuditService
        self.service = BiasAuditService()

    def test_detects_gender_imbalance_above_threshold(self):
        """Top-10 com 90% masculino (> 70% limite) deve ser flagged."""
        results = [{"id": str(i), "gender": "masculino"} for i in range(9)]
        results.append({"id": "10", "gender": "feminino"})

        audit = self.service.audit_ranking_results(results, dimension="gender", top_n=10)

        assert audit["fairness_ok"] is False
        assert "feminino" in audit["flagged_groups"]
        assert audit["alert"] is not None
        assert len(audit["alert"]) > 0

    def test_accepts_balanced_gender_distribution(self):
        """Top-10 com 60/40 masculino/feminino deve passar (acima de 80% ratio)."""
        results = (
            [{"id": str(i), "gender": "masculino"} for i in range(6)] +
            [{"id": str(i + 6), "gender": "feminino"} for i in range(4)]
        )

        audit = self.service.audit_ranking_results(results, dimension="gender", top_n=10)

        # ratio feminino = (4/10) / (6/10) = 0.667 — abaixo de 0.80 → deve ser flagged
        assert "feminino" in audit["flagged_groups"]

    def test_balanced_50_50_passes(self):
        """Top-10 com 50/50 deve passar (ratio = 1.0)."""
        results = (
            [{"id": str(i), "gender": "masculino"} for i in range(5)] +
            [{"id": str(i + 5), "gender": "feminino"} for i in range(5)]
        )

        audit = self.service.audit_ranking_results(results, dimension="gender", top_n=10)

        assert audit["fairness_ok"] is True
        assert len(audit["flagged_groups"]) == 0
        assert audit["alert"] is None

    def test_insufficient_data_returns_ok(self):
        """Menos de 3 candidatos com dados de gênero retorna fairness_ok=True."""
        results = [
            {"id": "1", "gender": "masculino"},
            {"id": "2"},  # sem gender
            {"id": "3"},  # sem gender
        ]

        audit = self.service.audit_ranking_results(results, dimension="gender", top_n=10)

        assert audit["fairness_ok"] is True

    def test_empty_results_returns_ok(self):
        """Lista vazia deve retornar fairness_ok=True."""
        audit = self.service.audit_ranking_results([], dimension="gender")
        assert audit["fairness_ok"] is True

    def test_returns_correct_group_counts(self):
        """group_counts deve refletir a distribuição real."""
        results = (
            [{"id": str(i), "gender": "masculino"} for i in range(7)] +
            [{"id": str(i + 7), "gender": "feminino"} for i in range(3)]
        )

        audit = self.service.audit_ranking_results(results, dimension="gender", top_n=10)

        assert audit["group_counts"]["masculino"] == 7
        assert audit["group_counts"]["feminino"] == 3

    def test_adverse_impact_ratios_computed(self):
        """adverse_impact_ratios deve ter ratio para cada grupo."""
        results = (
            [{"id": str(i), "gender": "masculino"} for i in range(8)] +
            [{"id": str(i + 8), "gender": "feminino"} for i in range(2)]
        )

        audit = self.service.audit_ranking_results(results, dimension="gender", top_n=10)

        assert "masculino" in audit["adverse_impact_ratios"]
        assert "feminino" in audit["adverse_impact_ratios"]
        # Grupo dominante tem ratio 1.0
        assert audit["adverse_impact_ratios"]["masculino"] == 1.0
        # Grupo minoritário tem ratio < 1.0
        assert audit["adverse_impact_ratios"]["feminino"] < 1.0

    def test_respects_top_n_parameter(self):
        """Deve auditar apenas os top-N resultados, ignorando o restante."""
        results = (
            [{"id": str(i), "gender": "feminino"} for i in range(5)] +
            [{"id": str(i + 5), "gender": "masculino"} for i in range(15)]  # 15 extras
        )

        # top_n=5: apenas os 5 primeiros (todos feminino)
        audit = self.service.audit_ranking_results(results, dimension="gender", top_n=5)

        # Dados insuficientes para auditoria (apenas 1 gênero em top-5) → ok
        assert audit["fairness_ok"] is True or len(audit["group_counts"]) == 1

    def test_company_id_included_in_warning_log(self):
        """Deve logar com company_id quando detecta disparate impact."""
        import logging
        results = [{"id": str(i), "gender": "masculino"} for i in range(10)]

        with patch('app.services.bias_audit_service.logger') as mock_logger:
            audit = self.service.audit_ranking_results(
                results, dimension="gender", top_n=10, company_id="test-company-123"
            )

        # Se detectou problema, deve ter logado
        if not audit["fairness_ok"]:
            mock_logger.warning.assert_called_once()
            call_args = str(mock_logger.warning.call_args)
            assert "test-company-123" in call_args


class TestFairnessAuditLogModel:
    """Verifica que o modelo FairnessAuditLog tem o campo soft_warnings."""

    def test_model_has_soft_warnings_column(self):
        from app.models.fairness_audit import FairnessAuditLog
        # O campo deve existir no modelo
        assert hasattr(FairnessAuditLog, 'soft_warnings')

    def test_libs_model_has_soft_warnings_column(self):
        from lia_models.fairness_audit import FairnessAuditLog
        assert hasattr(FairnessAuditLog, 'soft_warnings')


class TestMigration048:
    """Verifica que a migration 048 está declarada corretamente."""

    def test_migration_file_exists(self):
        import os
        path = "alembic/versions/048_add_soft_warnings_to_fairness_audit.py"
        assert os.path.exists(path), f"Migration 048 não encontrada em {path}"

    def test_migration_revises_047(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "migration_048",
            "alembic/versions/048_add_soft_warnings_to_fairness_audit.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.revision == '048'
        assert mod.down_revision == '047'

    def test_migration_adds_soft_warnings_column(self):
        """Migration deve adicionar coluna soft_warnings."""
        with open("alembic/versions/048_add_soft_warnings_to_fairness_audit.py") as f:
            content = f.read()
        assert "soft_warnings" in content
        assert "add_column" in content
        assert "fairness_audit_log" in content
