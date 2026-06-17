"""
RED tests — G-Fairness: rejection notes devem ser passados ao BE + FairnessGuard aplicado.

Cenários:
1. BulkUpdateStatusRequest aceita rejection_notes (campo existe no schema)
2. Quando rejection_notes contém conteúdo discriminatório → 400 fairness_blocked
3. Quando rejection_notes é válido → 200 OK (sem bloqueio)
4. Quando rejection_notes é None → 200 OK (sem bloqueio mesmo em rejeição)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError


class TestBulkUpdateStatusRequestSchema:
    """G-Fairness: schema aceita rejection_notes"""

    def test_rejection_notes_field_exists(self):
        """BulkUpdateStatusRequest deve ter campo rejection_notes opcional."""
        from app.api.v1.bulk_actions import BulkUpdateStatusRequest
        req = BulkUpdateStatusRequest(
            candidate_ids=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
            new_status="rejected",
            rejection_notes="Perfil não atendeu requisitos técnicos de Java",
        )
        assert req.rejection_notes == "Perfil não atendeu requisitos técnicos de Java"

    def test_rejection_notes_optional_none(self):
        """rejection_notes deve ser opcional (None por padrão)."""
        from app.api.v1.bulk_actions import BulkUpdateStatusRequest
        req = BulkUpdateStatusRequest(
            candidate_ids=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
            new_status="rejected",
        )
        assert req.rejection_notes is None

    def test_rejection_notes_on_non_reject_status(self):
        """Campo presente mesmo em status não-rejected (BE ignora silenciosamente)."""
        from app.api.v1.bulk_actions import BulkUpdateStatusRequest
        req = BulkUpdateStatusRequest(
            candidate_ids=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
            new_status="screening",
            rejection_notes="deveria ser ignorado",
        )
        assert req.rejection_notes == "deveria ser ignorado"


class TestBulkRejectFairnessGuard:
    """G-Fairness: FairnessGuard aplicado nos rejection_notes antes de processar."""

    @pytest.mark.asyncio
    async def test_fairness_blocked_returns_400(self, mock_bulk_repo, mock_current_user):
        """
        POST /candidates/bulk/update-status com rejection_notes discriminatório
        deve retornar HTTP 400 com fairness_blocked=True.
        """
        from fastapi import HTTPException
        from app.api.v1.bulk_actions import bulk_update_candidate_status, BulkUpdateStatusRequest

        req = BulkUpdateStatusRequest(
            candidate_ids=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
            new_status="rejected",
            rejection_notes="candidata está grávida",  # discriminatório
        )

        with pytest.raises(HTTPException) as exc_info:
            await bulk_update_candidate_status(
                request=req,
                current_user=mock_current_user,
                repo=mock_bulk_repo,
                company_id="company-uuid-123",
            )

        assert exc_info.value.status_code == 400
        detail = exc_info.value.detail
        assert detail.get("error") == "fairness_blocked"
        assert detail.get("fairness_blocked") is True

    @pytest.mark.asyncio
    async def test_valid_rejection_notes_allowed(self, mock_bulk_repo, mock_current_user, mock_candidate):
        """
        POST /candidates/bulk/update-status com rejection_notes neutro
        deve processar normalmente (200 OK).
        """
        from app.api.v1.bulk_actions import bulk_update_candidate_status, BulkUpdateStatusRequest

        candidate_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        mock_candidate.status = "screening"
        mock_bulk_repo.get_candidate_by_id = AsyncMock(return_value=mock_candidate)
        mock_bulk_repo.commit = AsyncMock()

        req = BulkUpdateStatusRequest(
            candidate_ids=[candidate_id],
            new_status="rejected",
            rejection_notes="Perfil técnico não atende nível sênior exigido",
        )

        result = await bulk_update_candidate_status(
            request=req,
            current_user=mock_current_user,
            repo=mock_bulk_repo,
            company_id="company-uuid-123",
        )

        assert result.successful == 1
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_no_fairness_guard_when_notes_none(self, mock_bulk_repo, mock_current_user, mock_candidate):
        """
        POST sem rejection_notes não deve invocar FairnessGuard.
        """
        from app.api.v1.bulk_actions import bulk_update_candidate_status, BulkUpdateStatusRequest

        candidate_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        mock_candidate.status = "screening"
        mock_bulk_repo.get_candidate_by_id = AsyncMock(return_value=mock_candidate)
        mock_bulk_repo.commit = AsyncMock()

        req = BulkUpdateStatusRequest(
            candidate_ids=[candidate_id],
            new_status="rejected",
            rejection_notes=None,
        )

        with patch("app.shared.compliance.fairness_guard.FairnessGuard.check") as mock_fg:
            result = await bulk_update_candidate_status(
                request=req,
                current_user=mock_current_user,
                repo=mock_bulk_repo,
                company_id="company-uuid-123",
            )
            mock_fg.assert_not_called()

        assert result.successful == 1


@pytest.fixture
def mock_current_user():
    user = MagicMock()
    user.id = "user-uuid-000"
    return user


@pytest.fixture
def mock_bulk_repo():
    repo = MagicMock()
    repo.get_candidate_by_id = AsyncMock(return_value=None)
    repo.commit = AsyncMock()
    repo.rollback = AsyncMock()
    return repo


@pytest.fixture
def mock_candidate():
    candidate = MagicMock()
    candidate.id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    candidate.status = "screening"
    candidate.is_active = True
    candidate.rejection_reason = None
    return candidate
