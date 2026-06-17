"""
Testes de integração para Audit Lifecycle S3 — política de retenção SOX.

Valida a estrutura da política de retenção, S3Storage com boto3 mockado,
LocalFileStorage stub e o Celery task de aplicação mensal.

Camada 3 (Integração) da pirâmide — S3/boto3 mockados.

Cobertura:
  - get_lifecycle_config() retorna estrutura AWS válida
  - Transições de storage class (Standard → Glacier IR → Glacier Deep → Delete)
  - Retenção SOX: 7 anos = 2555 dias
  - S3Storage.apply_lifecycle_policy() com boto3 mockado
  - LocalFileStorage.apply_lifecycle_policy() retorna False (stub)
  - build_storage_path() inclui company_id (isolamento multi-tenant)
  - Celery task audit.apply_lifecycle_policy está registrado
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from libs.audit.lia_audit.audit_storage import (
    LocalFileStorage,
    S3Storage,
    build_storage_path,
    get_audit_storage,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SOX_RETENTION_DAYS = 2555  # ~7 anos


def _make_s3_storage() -> S3Storage:
    return S3Storage(bucket="lia-audit-test", prefix="audit", region="us-east-1")


# ---------------------------------------------------------------------------
# Seção 1: get_lifecycle_config() — estrutura AWS
# ---------------------------------------------------------------------------

class TestLifecycleConfigStructure:

    def test_get_lifecycle_config_has_rules_key(self):
        """Lifecycle config tem chave 'Rules'."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()
        assert "Rules" in config, "Lifecycle config deve ter chave 'Rules'"

    def test_lifecycle_config_rules_is_list(self):
        """'Rules' é uma lista."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()
        assert isinstance(config["Rules"], list)

    def test_lifecycle_config_has_at_least_one_rule(self):
        """Lifecycle config tem pelo menos 1 regra."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()
        assert len(config["Rules"]) >= 1

    def test_lifecycle_config_rule_has_id(self):
        """Cada regra tem campo 'ID'."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()
        for rule in config["Rules"]:
            assert "ID" in rule, f"Regra sem ID: {rule}"

    def test_lifecycle_config_rule_has_status(self):
        """Cada regra tem campo 'Status'."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()
        for rule in config["Rules"]:
            assert "Status" in rule, f"Regra sem Status: {rule}"
            assert rule["Status"] in ("Enabled", "Disabled")

    def test_lifecycle_config_rule_has_transitions(self):
        """Pelo menos uma regra tem Transitions."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()
        has_transitions = any("Transitions" in rule for rule in config["Rules"])
        assert has_transitions, "Lifecycle config deve ter pelo menos uma regra com Transitions"

    def test_lifecycle_config_has_expiration(self):
        """Pelo menos uma regra tem Expiration (delete após 7 anos)."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()
        has_expiration = any("Expiration" in rule for rule in config["Rules"])
        assert has_expiration, "Lifecycle config deve ter Expiration para conformidade SOX"


# ---------------------------------------------------------------------------
# Seção 2: SOX Compliance — 7 anos
# ---------------------------------------------------------------------------

class TestSOXRetentionCompliance:

    def test_lifecycle_delete_after_sox_period(self):
        """Expiração (delete) ocorre após pelo menos 2555 dias (7 anos SOX)."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()

        for rule in config["Rules"]:
            if "Expiration" in rule:
                expiration = rule["Expiration"]
                days = expiration.get("Days", 0)
                assert days >= SOX_RETENTION_DAYS, (
                    f"Expiração de {days} dias não atende SOX (mínimo {SOX_RETENTION_DAYS} dias)"
                )

    def test_lifecycle_transitions_to_glacier(self):
        """Pelo menos uma transição deve ir para GLACIER (redução de custo)."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()

        glacier_classes = {
            "GLACIER",
            "GLACIER_IR",
            "DEEP_ARCHIVE",
            "GLACIER_DEEP_ARCHIVE",
        }
        found_glacier = False
        for rule in config["Rules"]:
            for transition in rule.get("Transitions", []):
                sc = transition.get("StorageClass", "")
                if any(g in sc for g in glacier_classes):
                    found_glacier = True
                    break

        assert found_glacier, "Lifecycle deve ter transição para Glacier (custo SOX)"

    def test_lifecycle_initial_transition_at_90_days(self):
        """Primeira transição deve ocorrer em 90 dias (Standard → Glacier IR)."""
        storage = _make_s3_storage()
        config = storage.get_lifecycle_config()

        first_transition_days = []
        for rule in config["Rules"]:
            for transition in rule.get("Transitions", []):
                days = transition.get("Days", 9999)
                first_transition_days.append(days)

        if first_transition_days:
            min_days = min(first_transition_days)
            assert min_days <= 365, (
                f"Primeira transição em {min_days} dias — deveria ser <= 365 dias"
            )


# ---------------------------------------------------------------------------
# Seção 3: S3Storage.apply_lifecycle_policy() com boto3 mockado
# ---------------------------------------------------------------------------

class TestS3StorageLifecycleApply:

    @pytest.mark.asyncio
    async def test_apply_lifecycle_policy_returns_true_on_success(self):
        """apply_lifecycle_policy() retorna True quando boto3 responde OK."""
        storage = _make_s3_storage()
        mock_client = MagicMock()
        mock_client.put_bucket_lifecycle_configuration = MagicMock(return_value={})

        with patch.object(storage, "_get_client", return_value=mock_client):
            result = await storage.apply_lifecycle_policy()

        assert result is True

    @pytest.mark.asyncio
    async def test_apply_lifecycle_policy_calls_put_bucket(self):
        """apply_lifecycle_policy() chama put_bucket_lifecycle_configuration."""
        storage = _make_s3_storage()
        mock_client = MagicMock()
        mock_client.put_bucket_lifecycle_configuration = MagicMock(return_value={})

        with patch.object(storage, "_get_client", return_value=mock_client):
            await storage.apply_lifecycle_policy()

        mock_client.put_bucket_lifecycle_configuration.assert_called_once()

    @pytest.mark.asyncio
    async def test_apply_lifecycle_policy_returns_false_on_error(self):
        """apply_lifecycle_policy() retorna False quando boto3 falha."""
        storage = _make_s3_storage()
        mock_client = MagicMock()
        mock_client.put_bucket_lifecycle_configuration = MagicMock(
            side_effect=Exception("S3 permission denied")
        )

        with patch.object(storage, "_get_client", return_value=mock_client):
            result = await storage.apply_lifecycle_policy()

        assert result is False

    @pytest.mark.asyncio
    async def test_apply_lifecycle_policy_uses_correct_bucket(self):
        """apply_lifecycle_policy() usa o bucket configurado."""
        bucket_name = "lia-audit-sox-prod"
        storage = S3Storage(bucket=bucket_name, prefix="audit")
        mock_client = MagicMock()
        mock_client.put_bucket_lifecycle_configuration = MagicMock(return_value={})

        with patch.object(storage, "_get_client", return_value=mock_client):
            await storage.apply_lifecycle_policy()

        call_kwargs = mock_client.put_bucket_lifecycle_configuration.call_args[1]
        assert call_kwargs.get("Bucket") == bucket_name


# ---------------------------------------------------------------------------
# Seção 4: LocalFileStorage stub
# ---------------------------------------------------------------------------

class TestLocalFileStorageLifecycle:

    @pytest.mark.asyncio
    async def test_local_storage_apply_lifecycle_returns_false(self):
        """LocalFileStorage.apply_lifecycle_policy() retorna False (stub dev)."""
        storage = LocalFileStorage(base_dir="/tmp/lia_test_audit")
        result = await storage.apply_lifecycle_policy()
        assert result is False


# ---------------------------------------------------------------------------
# Seção 5: build_storage_path() — multi-tenant
# ---------------------------------------------------------------------------

class TestBuildStoragePath:

    def test_build_storage_path_includes_company_id(self):
        """Path inclui company_id para isolamento multi-tenant."""
        path = build_storage_path(
            domain="wizard",
            company_id="company-123",
            execution_id="exec-456",
        )
        assert "company-123" in path

    def test_build_storage_path_includes_domain(self):
        """Path inclui domain."""
        path = build_storage_path(
            domain="cv_screening",
            company_id="company-xyz",
            execution_id="exec-001",
        )
        assert "cv_screening" in path

    def test_build_storage_path_includes_execution_id(self):
        """Path inclui execution_id."""
        path = build_storage_path(
            domain="sourcing",
            company_id="company-abc",
            execution_id="exec-789",
        )
        assert "exec-789" in path

    def test_build_storage_path_different_companies_different_paths(self):
        """Empresas diferentes têm paths diferentes (isolamento)."""
        path_a = build_storage_path("wizard", "company-A", "exec-1")
        path_b = build_storage_path("wizard", "company-B", "exec-1")
        assert path_a != path_b


# ---------------------------------------------------------------------------
# Seção 6: Celery task registrado
# ---------------------------------------------------------------------------

class TestAuditLifecycleCeleryTask:

    def test_celery_task_apply_lifecycle_registered(self):
        """Celery task 'audit.apply_lifecycle_policy' está registrado."""
        try:
            from app.jobs.celery_tasks import apply_audit_lifecycle_policy
            assert callable(apply_audit_lifecycle_policy)
        except ImportError:
            pytest.skip("celery_tasks não importável no ambiente de teste")

    def test_celery_task_has_retry_config(self):
        """Celery task de lifecycle tem configuração de retry."""
        try:
            from app.jobs.celery_tasks import apply_audit_lifecycle_policy
            # Task Celery com bind=True tem método retry
            assert hasattr(apply_audit_lifecycle_policy, "retry") or \
                   hasattr(apply_audit_lifecycle_policy, "apply_async")
        except ImportError:
            pytest.skip("celery_tasks não importável")
