"""Tests for candidate portal /applications endpoint (replaces 503 stub)."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


def test_list_candidate_applications_repo_method_exists():
    """Repository must have list_candidate_applications method."""
    from app.domains.candidate_self_service.repositories.candidate_status_repository import (
        CandidateSelfServiceRepository,
    )
    assert hasattr(CandidateSelfServiceRepository, "list_candidate_applications")
    import inspect
    assert asyncio.iscoroutinefunction(
        CandidateSelfServiceRepository.list_candidate_applications
    ), "Must be async"


def test_portal_applications_endpoint_no_longer_raises_503():
    """Endpoint source must NOT contain the 503 Rails migration stub."""
    import inspect
    from app.api.v1 import candidate_portal
    src = inspect.getsource(candidate_portal)
    assert "migração Rails→FastAPI pendente" not in src, "503 stub still present"
    assert "list_candidate_applications" in src, "real implementation missing"


async def test_list_candidate_applications_repo_returns_list():
    """Repository method returns list (empty when no rows)."""
    from app.domains.candidate_self_service.repositories.candidate_status_repository import (
        CandidateSelfServiceRepository,
    )
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    repo = CandidateSelfServiceRepository(mock_session)
    result = await repo.list_candidate_applications(
        candidate_id="cand-123",
        company_id="company-abc",
    )
    assert isinstance(result, list)
    assert result == []
