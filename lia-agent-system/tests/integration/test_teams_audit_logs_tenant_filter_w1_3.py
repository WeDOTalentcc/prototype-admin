"""
Integration tests — W1.3: P0-3 tenant filter em /webhook/audit-logs.

Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P0-3) identificou
que GET /api/v1/teams/webhook/audit-logs:
  1. Não tinha Depends(get_current_user) — endpoint público para autenticados
  2. Repository.list_audit_logs / count_audit_logs não aceitavam company_id
Resultado: qualquer caller autenticado lista logs de TODAS as empresas.
Vazamento cross-tenant — viola CLAUDE.md global multi-tenant non-negotiable.

Esta suite valida:
1. Repository: list_audit_logs / count_audit_logs aceitam kwarg company_id.
2. Repository: queries WHERE company_id quando filter passado.
3. Endpoint: declara Depends(get_current_user) e passa company_id à query.

Pattern TDD: testes falham antes da implementação. Pattern canônico replicado
de app/api/v1/agent_approvals.py:list_pending_approvals.
"""
from __future__ import annotations

import inspect
import pytest
from unittest.mock import AsyncMock, MagicMock


# ============================================================================
# 1. Repository — signatures aceitam company_id
# ============================================================================


class TestRepositoryAuditLogsSignature:
    """list_audit_logs / count_audit_logs aceitam company_id kwarg."""

    def test_list_audit_logs_accepts_company_id_kwarg(self):
        from app.domains.communication.repositories.teams_repository import (
            TeamsRepository,
        )
        sig = inspect.signature(TeamsRepository.list_audit_logs)
        assert "company_id" in sig.parameters, (
            f"list_audit_logs deve aceitar kwarg company_id. "
            f"Params: {list(sig.parameters.keys())}"
        )

    def test_count_audit_logs_accepts_company_id_kwarg(self):
        from app.domains.communication.repositories.teams_repository import (
            TeamsRepository,
        )
        sig = inspect.signature(TeamsRepository.count_audit_logs)
        assert "company_id" in sig.parameters, (
            f"count_audit_logs deve aceitar kwarg company_id. "
            f"Params: {list(sig.parameters.keys())}"
        )


# ============================================================================
# 2. Repository — query aplica WHERE company_id quando filter passado
# ============================================================================


class TestRepositoryAuditLogsFilters:
    """Quando company_id passado, query inclui filtro WHERE."""

    @pytest.mark.asyncio
    async def test_list_audit_logs_filters_by_company_id_in_query(self):
        """Quando company_id passado, query SQL deve incluir WHERE company_id."""
        from app.domains.communication.repositories.teams_repository import (
            TeamsRepository,
        )

        captured_query = {}

        async def _capture_execute(stmt):
            # SQLAlchemy stmt -> str (mostra o SQL com placeholders)
            captured_query["sql"] = str(stmt)
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        mock_db = AsyncMock()
        mock_db.execute = _capture_execute

        repo = TeamsRepository(mock_db)
        await repo.list_audit_logs(company_id="comp_target_42")

        sql_str = captured_query.get("sql", "")
        assert "company_id" in sql_str, (
            f"SQL deve filtrar por company_id quando passado. SQL: {sql_str[:300]}"
        )

    @pytest.mark.asyncio
    async def test_list_audit_logs_no_filter_when_company_id_none(self):
        """Quando company_id=None, query NÃO inclui filter (compatibilidade dev/admin)."""
        from app.domains.communication.repositories.teams_repository import (
            TeamsRepository,
        )

        captured = {}

        async def _capture(stmt):
            captured["sql"] = str(stmt)
            mr = MagicMock()
            mr.scalars.return_value.all.return_value = []
            return mr

        mock_db = AsyncMock()
        mock_db.execute = _capture
        repo = TeamsRepository(mock_db)
        await repo.list_audit_logs(company_id=None)

        sql = captured.get("sql", "")
        # Quando None, não devemos forçar WHERE company_id IS NULL
        # (caller decide se quer all-tenant view ou single-tenant)
        # Apenas valida que não crash e SQL é coerente
        assert "FROM teams_action_audit_logs" in sql or "teams_action_audit_logs" in sql


# ============================================================================
# 3. Endpoint — Depends(get_current_user) + passa company_id
# ============================================================================


class TestEndpointTenantFilter:
    """GET /webhook/audit-logs requires auth and filters by tenant."""

    def test_endpoint_declares_get_current_user_dependency(self):
        """Endpoint deve usar Depends(get_current_user) — pattern canônico."""
        import app.api.v1.teams as teams_mod

        src = inspect.getsource(teams_mod.get_teams_audit_logs)
        # Aceita get_current_user, get_current_user_strict, ou require_role
        assert any(d in src for d in ("get_current_user", "require_role")), (
            "GET /webhook/audit-logs deve declarar Depends(get_current_user) ou "
            "Depends(require_role(...)) — pattern de app/api/v1/agent_approvals.py"
        )

    def test_endpoint_passes_current_user_company_id_to_repo(self):
        """Endpoint deve passar company_id=current_user.company_id ao repo."""
        import app.api.v1.teams as teams_mod

        src = inspect.getsource(teams_mod.get_teams_audit_logs)
        assert "current_user.company_id" in src, (
            "Endpoint deve repassar current_user.company_id à query do repository "
            "(P0-3 fix — sem isso, lista cross-tenant)"
        )
