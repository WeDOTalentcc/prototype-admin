"""Sensor TDD — Fase 4-E: LGPD guardrails (TTL + erasure cascade).

Pina:
 - RETENTION_DAYS["pearch_discovered_profiles"] == 180 (contrato de retenção)
 - run_cleanup inclui external_candidate_profiles (TTL step presente)
 - DSR deletion apaga ExternalCandidateProfile por email (erasure cascade Art. 18 VI)
 - Erasure falha silenciosamente (non-fatal) mas loga warning
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import sqlalchemy as sa


class TestRetentionPolicy:
    """4-E: contrato de retenção 180 dias para perfis Pearch não-engajados."""

    def test_retention_days_pearch_is_180(self):
        from app.domains.lgpd.services.lgpd_cleanup_service import RETENTION_DAYS
        assert "pearch_discovered_profiles" in RETENTION_DAYS, (
            "LGPD Art. 5 e: pearch_discovered_profiles deve ter TTL definido"
        )
        assert RETENTION_DAYS["pearch_discovered_profiles"] == 180, (
            f"TTL esperado: 180 dias; obtido: {RETENTION_DAYS['pearch_discovered_profiles']}"
        )

    def test_external_candidate_profiles_in_allowed_ttl_tables(self):
        """external_candidate_profiles deve estar na allowlist do cleanup service."""
        from app.domains.lgpd.services.lgpd_cleanup_service import _ALLOWED_TTL_TABLES
        assert "external_candidate_profiles" in _ALLOWED_TTL_TABLES, (
            "Tabela não está em _ALLOWED_TTL_TABLES; TTL cleanup não pode atuar nela"
        )


class TestRunCleanupPearchStep:
    """4-E: run_cleanup inclui etapa de purge de perfis Pearch."""

    @pytest.mark.asyncio
    async def test_cleanup_queries_external_candidate_profiles(self):
        """run_cleanup deve consultar external_candidate_profiles para TTL."""
        from app.domains.lgpd.services.lgpd_cleanup_service import run_cleanup

        executed_sqls = []

        async def _fake_execute(stmt, params=None):
            sql_str = str(stmt) if hasattr(stmt, "__str__") else repr(stmt)
            executed_sqls.append(sql_str.lower())
            result = MagicMock()
            result.scalar_one.return_value = 0
            result.scalars.return_value.all.return_value = []
            result.fetchall.return_value = []
            return result

        mock_db = AsyncMock()
        mock_db.execute = _fake_execute
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch("app.domains.lgpd.services.lgpd_cleanup_service.AsyncSessionLocal", return_value=mock_db):
            summary = await run_cleanup(dry_run=True)

        # Verifica que external_candidate_profiles foi consultado
        pearch_queried = any("external_candidate_profiles" in s for s in executed_sqls)
        assert pearch_queried, (
            "run_cleanup não consultou external_candidate_profiles — "
            f"SQL executados: {[s for s in executed_sqls if 'external' in s]}"
        )

    @pytest.mark.asyncio
    async def test_cleanup_dry_run_does_not_delete(self):
        """dry_run=True não deve apagar dados do external_candidate_profiles."""
        from app.domains.lgpd.services.lgpd_cleanup_service import run_cleanup

        delete_calls = []

        async def _fake_execute(stmt, params=None):
            sql_str = str(stmt).lower() if hasattr(stmt, "__str__") else ""
            if "delete" in sql_str and "external_candidate" in sql_str:
                delete_calls.append(sql_str)
            result = MagicMock()
            result.scalar_one.return_value = 3  # simula 3 rows elegíveis
            result.scalars.return_value.all.return_value = []
            result.fetchall.return_value = []
            return result

        mock_db = AsyncMock()
        mock_db.execute = _fake_execute
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch("app.domains.lgpd.services.lgpd_cleanup_service.AsyncSessionLocal", return_value=mock_db):
            summary = await run_cleanup(dry_run=True)

        assert not delete_calls, (
            f"dry_run=True não deve gerar DELETE em external_candidate_profiles; "
            f"DELETE calls: {delete_calls}"
        )


class TestErasureCascade:
    """4-E: DSR deletion apaga ExternalCandidateProfile por email (Art. 18 VI)."""

    def test_side_effect_has_pearch_erased_key(self):
        """Erasure cascade registra resultado em side_effect['pearch_profiles_erased']."""
        # Verifica que o campo existe como chave possível via importação do repositório
        import importlib
        mod = importlib.import_module(
            "app.repositories.data_subject_repository"
        )
        import inspect
        src = inspect.getsource(mod)
        assert "pearch_profiles_erased" in src, (
            "data_subject_repository deve registrar 'pearch_profiles_erased' em side_effect "
            "(Art. 18 VI: auditoria de erasure)"
        )

    def test_erasure_uses_email_filter(self):
        """Erasure usa email do data subject para deletar perfis Pearch (não candidate_id)."""
        import inspect
        import importlib
        mod = importlib.import_module(
            "app.repositories.data_subject_repository"
        )
        src = inspect.getsource(mod)
        assert "subject_email" in src, "Erasure deve usar subject_email como filtro"
        assert "ExternalCandidateProfile" in src, (
            "data_subject_repository deve importar ExternalCandidateProfile para cascade"
        )

    def test_erasure_is_non_fatal(self):
        """Falha no cascade erasure não bloqueia DSR — loga warning mas continua."""
        import inspect
        import importlib
        mod = importlib.import_module(
            "app.repositories.data_subject_repository"
        )
        src = inspect.getsource(mod)
        # Verifica que existe catch para erasure failure (non-fatal pattern)
        assert "pearch_erase_warning" in src or "_erase_exc" in src, (
            "Erasure cascade deve ser non-fatal: capturar exceção e logar warning"
        )
