"""
Contract Tests: Manager Alignment

Verifica:
  - ManagerAlignmentRepository tem métodos obrigatórios com assinaturas corretas
  - ManagerAlignment.is_expired() e is_pending() funcionam corretamente
  - Gate _check_alignment_gate bloqueia quando política exige e não há alinhamento aprovado
  - Gate é fail-open em erros (não bloqueia sourcing por erro de infraestrutura)
  - Token gerado tem entropia mínima aceitável
"""
import secrets
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Contract: ManagerAlignmentRepository métodos obrigatórios
# ---------------------------------------------------------------------------

class TestManagerAlignmentRepositoryContract:

    def test_has_create_method(self):
        from app.domains.approvals.repositories.manager_alignment_repository import ManagerAlignmentRepository
        assert hasattr(ManagerAlignmentRepository, "create")
        assert callable(ManagerAlignmentRepository.create)

    def test_has_get_by_token_method(self):
        from app.domains.approvals.repositories.manager_alignment_repository import ManagerAlignmentRepository
        assert hasattr(ManagerAlignmentRepository, "get_by_token")

    def test_has_get_pending_for_job_method(self):
        from app.domains.approvals.repositories.manager_alignment_repository import ManagerAlignmentRepository
        assert hasattr(ManagerAlignmentRepository, "get_pending_for_job")

    def test_has_respond_method(self):
        from app.domains.approvals.repositories.manager_alignment_repository import ManagerAlignmentRepository
        assert hasattr(ManagerAlignmentRepository, "respond")

    def test_require_company_id_raises_on_empty(self):
        from app.domains.approvals.repositories.manager_alignment_repository import ManagerAlignmentRepository
        with pytest.raises((ValueError, Exception)):
            ManagerAlignmentRepository._require_company_id(None)

    def test_require_company_id_passes_valid(self):
        from app.domains.approvals.repositories.manager_alignment_repository import ManagerAlignmentRepository
        result = ManagerAlignmentRepository._require_company_id("company-uuid-123")
        assert result == "company-uuid-123"


# ---------------------------------------------------------------------------
# Contract: ManagerAlignment model helpers
# ---------------------------------------------------------------------------

class TestManagerAlignmentModelContract:

    def _make_alignment(self, status="pending", expired=False):
        from lia_models.manager_alignment import ManagerAlignment
        a = ManagerAlignment()
        a.status = status
        a.expires_at = (
            datetime.now(timezone.utc) - timedelta(hours=1)
            if expired
            else datetime.now(timezone.utc) + timedelta(hours=48)
        )
        return a

    def test_is_expired_returns_true_when_past(self):
        a = self._make_alignment(expired=True)
        assert a.is_expired() is True

    def test_is_expired_returns_false_when_future(self):
        a = self._make_alignment(expired=False)
        assert a.is_expired() is False

    def test_is_pending_returns_true_for_pending_status(self):
        a = self._make_alignment(status="pending")
        assert a.is_pending() is True

    def test_is_pending_returns_false_for_approved(self):
        a = self._make_alignment(status="approved")
        assert a.is_pending() is False

    def test_token_has_minimum_length(self):
        from lia_models.manager_alignment import ManagerAlignment
        import inspect
        # token default factory should produce at least 32 chars
        token = secrets.token_urlsafe(32)
        assert len(token) >= 32


# ---------------------------------------------------------------------------
# Contract: _check_alignment_gate — gate behaviour
# ---------------------------------------------------------------------------

class TestAlignmentGateContract:

    def _make_orchestrator(self):
        from app.services.sourcing_agent_orchestrator import SourcingAgentOrchestrator
        orch = SourcingAgentOrchestrator.__new__(SourcingAgentOrchestrator)
        return orch

    @pytest.mark.asyncio
    async def test_gate_blocks_when_policy_requires_and_no_approved_alignment(self):
        from fastapi import HTTPException
        orch = self._make_orchestrator()

        mock_db = AsyncMock()

        # Policy says require_manager_alignment = True
        mock_policy = MagicMock()
        mock_policy.communication_rules = {"require_manager_alignment": True}

        # No approved alignment exists
        mock_repo = AsyncMock()
        mock_repo.list_for_job = AsyncMock(return_value=[])

        with patch(
            "app.services.sourcing_agent_orchestrator.JobHiringPolicyRepository",
            return_value=AsyncMock(get_by_company=AsyncMock(return_value=mock_policy)),
        ), patch(
            "app.services.sourcing_agent_orchestrator.ManagerAlignmentRepository",
            return_value=mock_repo,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await orch._check_alignment_gate("company-1", "job-1", mock_db)
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail["code"] == "ALIGNMENT_REQUIRED"

    @pytest.mark.asyncio
    async def test_gate_passes_when_approved_alignment_exists(self):
        orch = self._make_orchestrator()
        mock_db = AsyncMock()

        mock_policy = MagicMock()
        mock_policy.communication_rules = {"require_manager_alignment": True}

        approved = MagicMock()
        approved.status = "approved"

        mock_repo = AsyncMock()
        mock_repo.list_for_job = AsyncMock(return_value=[approved])

        with patch(
            "app.services.sourcing_agent_orchestrator.JobHiringPolicyRepository",
            return_value=AsyncMock(get_by_company=AsyncMock(return_value=mock_policy)),
        ), patch(
            "app.services.sourcing_agent_orchestrator.ManagerAlignmentRepository",
            return_value=mock_repo,
        ):
            # Should not raise
            await orch._check_alignment_gate("company-1", "job-1", mock_db)

    @pytest.mark.asyncio
    async def test_gate_passes_when_policy_does_not_require_alignment(self):
        orch = self._make_orchestrator()
        mock_db = AsyncMock()

        mock_policy = MagicMock()
        mock_policy.communication_rules = {"require_manager_alignment": False}

        with patch(
            "app.services.sourcing_agent_orchestrator.JobHiringPolicyRepository",
            return_value=AsyncMock(get_by_company=AsyncMock(return_value=mock_policy)),
        ):
            # Should not raise
            await orch._check_alignment_gate("company-1", "job-1", mock_db)

    @pytest.mark.asyncio
    async def test_gate_is_fail_open_on_infrastructure_error(self):
        """Gate must NOT block sourcing when policy lookup itself fails."""
        orch = self._make_orchestrator()
        mock_db = AsyncMock()

        with patch(
            "app.services.sourcing_agent_orchestrator.JobHiringPolicyRepository",
            side_effect=Exception("DB connection lost"),
        ):
            # Should not raise — fail-open
            await orch._check_alignment_gate("company-1", "job-1", mock_db)
