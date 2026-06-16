"""
Integration tests — Multi-tenant boundary fix in Teams (P0-1).

Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P0-1) identificou que
`teams_orchestrator_bridge._resolve_company_id` lê `TeamsConversation.company_id`
que NÃO existia no modelo. `getattr(row, "company_id", None)` mascarava o erro
silently — toda mensagem do Teams chegava no orchestrator com `company_id=None`,
quebrando isolamento multi-tenant downstream (RAG, fairness, audit, drift).

Esta suite de testes valida que:
1. Schema: TeamsConversation tem coluna `company_id` (String, indexed).
2. Bridge: `_resolve_company_id` retorna company_id via lookup correto, sem getattr.
3. Write path: `_store_conversation_reference` popula company_id no DB.
4. E2E: orchestrator recebe company_id no context.

Pattern TDD: este arquivo é parte da fase RED — testes devem falhar antes da
implementação. Após Migration 097 + edits, todos os 7 testes passam (GREEN).
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any


# ============================================================================
# 1. Schema tests — introspecção pura do modelo (sem DB)
# ============================================================================


class TestTeamsConversationSchema:
    """Valida que TeamsConversation tem company_id no schema."""

    def test_teams_conversation_model_has_company_id_column(self):
        """company_id deve existir como Column no modelo TeamsConversation."""
        from lia_models.teams import TeamsConversation

        cols = [c.key for c in TeamsConversation.__table__.columns]
        assert "company_id" in cols, (
            f"TeamsConversation deve ter company_id. Colunas atuais: {cols}"
        )

    def test_teams_conversation_company_id_is_string_255(self):
        """company_id deve ser String(255) — pattern de User.company_id."""
        from lia_models.teams import TeamsConversation

        col = TeamsConversation.__table__.columns["company_id"]
        # SQLAlchemy String type — verifica length
        assert hasattr(col.type, "length"), (
            f"company_id type deve ser String(...) com length. Got: {col.type}"
        )
        assert col.type.length == 255, (
            f"company_id deve ser String(255). Got length={col.type.length}"
        )

    def test_teams_conversation_company_id_is_indexed(self):
        """company_id deve ter index para performance em queries multi-tenant."""
        from lia_models.teams import TeamsConversation

        col = TeamsConversation.__table__.columns["company_id"]
        assert col.index is True, (
            "company_id deve ter index=True (perf multi-tenant lookup)"
        )

    def test_teams_conversation_company_id_is_nullable(self):
        """company_id deve ser nullable — backfill pode deixar legados como NULL."""
        from lia_models.teams import TeamsConversation

        col = TeamsConversation.__table__.columns["company_id"]
        assert col.nullable is True, (
            "company_id deve ser nullable=True para suportar registros pre-backfill"
        )


# ============================================================================
# 2. Bridge resolve_company_id — sem getattr fallback
# ============================================================================


class TestResolveCompanyIdBridge:
    """Valida que TeamsOrchestratorBridge._resolve_company_id usa coluna real."""

    @pytest.mark.asyncio
    async def test_resolve_company_id_returns_value_from_conversation_row(self):
        """Quando TeamsConversation tem company_id, bridge retorna direto."""
        from app.domains.communication.services.teams_orchestrator_bridge import (
            TeamsOrchestratorBridge,
        )

        # Mock DB session que retorna conversation com company_id
        mock_conv = MagicMock()
        mock_conv.company_id = "comp_abc_123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_conv

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        bridge = TeamsOrchestratorBridge()
        company_id = await bridge._resolve_company_id(
            teams_user_id="teams_user_42",
            tenant_id="tenant_xyz",
            db=mock_db,
        )

        assert company_id == "comp_abc_123"

    @pytest.mark.asyncio
    async def test_resolve_company_id_returns_none_when_no_conversation(self):
        """Quando não há conversation row, bridge retorna None explicito."""
        from app.domains.communication.services.teams_orchestrator_bridge import (
            TeamsOrchestratorBridge,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        bridge = TeamsOrchestratorBridge()
        company_id = await bridge._resolve_company_id(
            teams_user_id="unknown_user",
            tenant_id="tenant_xyz",
            db=mock_db,
        )

        assert company_id is None

    @pytest.mark.asyncio
    async def test_resolve_company_id_does_not_use_getattr_fallback(self):
        """
        Bridge não pode usar getattr(row, 'company_id', None) como fallback.

        Esse pattern mascarava silently bugs de schema (P0-1). Após o fix,
        o acesso deve ser direto: row.company_id (com AttributeError se faltar
        a coluna — falha rápida em vez de None silencioso).
        """
        import inspect
        from app.domains.communication.services.teams_orchestrator_bridge import (
            TeamsOrchestratorBridge,
        )

        src = inspect.getsource(TeamsOrchestratorBridge._resolve_company_id)
        assert "getattr(row, \"company_id\"" not in src, (
            "_resolve_company_id NÃO deve usar getattr para company_id "
            "(mascara bugs de schema — fix P0-1)"
        )
        assert "getattr(row, 'company_id'" not in src, (
            "_resolve_company_id NÃO deve usar getattr para company_id "
            "(mascara bugs de schema — fix P0-1)"
        )


# ============================================================================
# 3. Write path — _store_conversation_reference popula company_id
# ============================================================================


class TestStoreConversationReferenceWritePath:
    """Valida que _store_conversation_reference popula company_id no DB."""

    @pytest.mark.asyncio
    async def test_store_conversation_reference_passes_company_id_to_repo(self):
        """
        _store_conversation_reference deve fazer lookup
        aad_object_id → User.company_id e passar ao repo.upsert_conversation.
        """
        from app.api.v1.teams import _store_conversation_reference

        activity = {
            "conversation": {"id": "19:abc@thread.v2", "tenantId": "tenant_xyz"},
            "from": {
                "id": "29:1abc",
                "name": "Maria Recruiter",
                "aadObjectId": "aad_obj_123",
            },
            "channelId": "msteams",
            "serviceUrl": "https://smba.trafficmanager.net/br/",
            "timestamp": "2026-04-26T10:00:00Z",
        }

        mock_user = MagicMock()
        mock_user.company_id = "comp_target_456"

        mock_repo_instance = MagicMock()
        mock_repo_instance.get_user_by_aad_object_id = AsyncMock(return_value=mock_user)
        mock_repo_instance.upsert_conversation = AsyncMock()

        mock_db = AsyncMock()

        with patch(
            "app.api.v1.teams.TeamsRepository", return_value=mock_repo_instance
        ):
            await _store_conversation_reference(activity, mock_db)

        # Validar que upsert_conversation foi chamado com company_id derivado
        mock_repo_instance.upsert_conversation.assert_called_once()
        kwargs = mock_repo_instance.upsert_conversation.call_args.kwargs
        assert "company_id" in kwargs, (
            "upsert_conversation deve receber kwarg company_id"
        )
        assert kwargs["company_id"] == "comp_target_456", (
            f"company_id deve vir de User.company_id (lookup via aadObjectId). "
            f"Got: {kwargs.get('company_id')}"
        )

    @pytest.mark.asyncio
    async def test_store_conversation_reference_sets_none_when_user_not_found(self):
        """
        Quando aadObjectId não bate com nenhum User, company_id deve ficar None
        (em vez de explodir ou inventar valor).
        """
        from app.api.v1.teams import _store_conversation_reference

        activity = {
            "conversation": {"id": "19:nouser@thread.v2"},
            "from": {"id": "29:zzz", "aadObjectId": "aad_unknown"},
            "channelId": "msteams",
            "serviceUrl": "https://example.com/",
        }

        mock_repo_instance = MagicMock()
        mock_repo_instance.get_user_by_aad_object_id = AsyncMock(return_value=None)
        mock_repo_instance.upsert_conversation = AsyncMock()

        mock_db = AsyncMock()

        with patch(
            "app.api.v1.teams.TeamsRepository", return_value=mock_repo_instance
        ):
            await _store_conversation_reference(activity, mock_db)

        kwargs = mock_repo_instance.upsert_conversation.call_args.kwargs
        assert kwargs.get("company_id") is None, (
            "Quando User não encontrado por aadObjectId, company_id deve ser None"
        )


# ============================================================================
# 4. Repository — upsert_conversation aceita company_id
# ============================================================================


class TestRepositoryUpsertConversationSignature:
    """Valida que TeamsRepository.upsert_conversation aceita company_id."""

    def test_upsert_conversation_accepts_company_id_kwarg(self):
        """Signature de upsert_conversation deve incluir company_id."""
        import inspect
        from app.domains.communication.repositories.teams_repository import (
            TeamsRepository,
        )

        sig = inspect.signature(TeamsRepository.upsert_conversation)
        assert "company_id" in sig.parameters, (
            f"upsert_conversation deve aceitar kwarg company_id. "
            f"Params atuais: {list(sig.parameters.keys())}"
        )
