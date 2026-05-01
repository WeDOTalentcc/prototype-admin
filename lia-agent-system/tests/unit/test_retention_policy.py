"""
Tests for CompanyRetentionPolicy — Etapa 4 hardening.

Cobre:
- CompanyRetentionPolicy model defaults (retention_months=24, auto_anonymize=False)
- RetentionPolicyRequest validação (6 ≤ months ≤ 120)
- _run_retention_cleanup_async() não processa empresas com auto_anonymize=False
- _run_retention_cleanup_async() retorna summary com campos corretos
- run_retention_cleanup task registrada com nome correto
- Celery beat schedule "data-retention-monthly" configurado
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCompanyRetentionPolicyModel:
    """Testa defaults e estrutura do model."""

    def test_model_exists(self):
        from libs.models.lia_models.retention_policy import CompanyRetentionPolicy
        assert CompanyRetentionPolicy is not None

    def test_model_retention_months_default(self):
        from libs.models.lia_models.retention_policy import CompanyRetentionPolicy
        # Verificar que o default está definido na coluna
        col = CompanyRetentionPolicy.__table__.columns.get("retention_months")
        assert col is not None
        assert col.default.arg == 24

    def test_model_auto_anonymize_default_false(self):
        from libs.models.lia_models.retention_policy import CompanyRetentionPolicy
        col = CompanyRetentionPolicy.__table__.columns.get("auto_anonymize")
        assert col is not None
        assert col.default.arg is False

    def test_model_tablename(self):
        from libs.models.lia_models.retention_policy import CompanyRetentionPolicy
        assert CompanyRetentionPolicy.__tablename__ == "company_retention_policies"

    def test_model_has_company_id_column(self):
        from libs.models.lia_models.retention_policy import CompanyRetentionPolicy
        assert hasattr(CompanyRetentionPolicy, "company_id")

    def test_model_has_activated_at_column(self):
        from libs.models.lia_models.retention_policy import CompanyRetentionPolicy
        assert hasattr(CompanyRetentionPolicy, "activated_at")

    def test_model_has_last_cleanup_at_column(self):
        from libs.models.lia_models.retention_policy import CompanyRetentionPolicy
        assert hasattr(CompanyRetentionPolicy, "last_cleanup_at")


class TestRetentionPolicyRequest:
    """Testa validação Pydantic da request."""

    def test_valid_request_24_months(self):
        from app.api.v1.company_retention import RetentionPolicyRequest
        req = RetentionPolicyRequest(retention_months=24, auto_anonymize=False)
        assert req.retention_months == 24
        assert req.auto_anonymize is False

    def test_valid_request_min_6_months(self):
        from app.api.v1.company_retention import RetentionPolicyRequest
        req = RetentionPolicyRequest(retention_months=6)
        assert req.retention_months == 6

    def test_valid_request_max_120_months(self):
        from app.api.v1.company_retention import RetentionPolicyRequest
        req = RetentionPolicyRequest(retention_months=120)
        assert req.retention_months == 120

    def test_invalid_request_below_6(self):
        from app.api.v1.company_retention import RetentionPolicyRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RetentionPolicyRequest(retention_months=5)

    def test_invalid_request_above_120(self):
        from app.api.v1.company_retention import RetentionPolicyRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RetentionPolicyRequest(retention_months=121)

    def test_auto_anonymize_defaults_false(self):
        from app.api.v1.company_retention import RetentionPolicyRequest
        req = RetentionPolicyRequest(retention_months=24)
        assert req.auto_anonymize is False


class TestRetentionCeleryTask:
    """Testa o Celery task de retenção."""

    def test_task_registered_with_correct_name(self):
        from app.jobs.celery_tasks import celery_app
        assert "data.retention.run" in celery_app.tasks

    def test_beat_schedule_has_data_retention_monthly(self):
        from app.jobs.celery_tasks import celery_app
        beat = celery_app.conf.beat_schedule
        assert "data-retention-monthly" in beat

    def test_beat_schedule_task_name_correct(self):
        from app.jobs.celery_tasks import celery_app
        beat = celery_app.conf.beat_schedule
        task_entry = beat.get("data-retention-monthly", {})
        assert task_entry.get("task") == "data.retention.run"


class TestRetentionCleanupAsync:
    """Testa a lógica assíncrona de limpeza."""

    @pytest.mark.asyncio
    async def test_returns_summary_with_required_fields(self):
        """_run_retention_cleanup_async deve retornar dict com os 4 campos."""
        import sys
        mock_candidate = MagicMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch.dict(sys.modules, {"libs.models.lia_models.candidate": mock_candidate}):
            with patch("lia_config.database.AsyncSessionLocal", return_value=mock_session):
                from app.jobs.celery_tasks import _run_retention_cleanup_async
                result = await _run_retention_cleanup_async()

        assert "companies_processed" in result
        assert "total_anonymized" in result
        assert "errors" in result
        assert "ran_at" in result

    @pytest.mark.asyncio
    async def test_no_companies_processed_when_no_auto_anonymize(self):
        """Se nenhuma empresa tem auto_anonymize=True, nenhuma é processada."""
        import sys
        mock_candidate = MagicMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()

        with patch.dict(sys.modules, {"libs.models.lia_models.candidate": mock_candidate}):
            with patch("lia_config.database.AsyncSessionLocal", return_value=mock_session):
                from app.jobs.celery_tasks import _run_retention_cleanup_async
                result = await _run_retention_cleanup_async()

        assert result["companies_processed"] == 0
        assert result["total_anonymized"] == 0
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_errors_list_is_populated_on_per_company_failure(self):
        """Erros por empresa devem ir para result["errors"] sem parar o job."""
        import sys
        mock_candidate = MagicMock()
        mock_policy = MagicMock()
        mock_policy.company_id = "company-bad"
        mock_policy.retention_months = 24

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.commit = AsyncMock()

        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = [mock_policy]
                return mock_result
            else:
                raise Exception("Simulated DB error for company")

        mock_session.execute = mock_execute

        with patch.dict(sys.modules, {"libs.models.lia_models.candidate": mock_candidate}):
            with patch("lia_config.database.AsyncSessionLocal", return_value=mock_session):
                from app.jobs.celery_tasks import _run_retention_cleanup_async
                result = await _run_retention_cleanup_async()

        assert len(result["errors"]) >= 1
        assert result["errors"][0]["company_id"] == "company-bad"
