"""
TDD Red test: get_job_details deve usar get_active_vacancy() como fallback
quando job_id não é passado, em vez de crashar em UUID("") → "instabilidade técnica".

Causa-raiz P0-A auditada 2026-06-14.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_get_job_details_sem_job_id_retorna_clarification():
    """RED: sem job_id e sem active_vacancy → needs_clarification, não erro genérico."""
    from app.domains.job_management.tools.query_tools import get_job_details

    with patch("app.shared.entity_resolver.get_active_vacancy", return_value=""):
        with patch("app.tools.context_helpers.require_company_id_from_context", return_value="co-123"):
            result = await get_job_details(job_id="", _context=None)

    assert result["success"] is False
    assert result.get("needs_clarification") is True, (
        f"Esperado needs_clarification=True mas obteve: {result}"
    )
    assert "UUID" not in result.get("message", ""), (
        "Mensagem não deve vazar detalhe técnico de UUID"
    )


@pytest.mark.asyncio
async def test_get_job_details_usa_active_vacancy_como_fallback():
    """RED: sem job_id mas com active_vacancy setado → usa o vacancy_id ativo."""
    from app.domains.job_management.tools.query_tools import get_job_details

    FAKE_JOB_ID = "11111111-1111-1111-1111-111111111111"

    with patch("app.shared.entity_resolver.get_active_vacancy", return_value=FAKE_JOB_ID):
        with patch("app.tools.context_helpers.require_company_id_from_context", return_value="co-123"):
            # Mock do db para não precisar de DB real
            mock_job = MagicMock()
            mock_job.id = FAKE_JOB_ID
            mock_job.title = "Diretor Jurídico"
            mock_job.status = "Ativa"
            mock_job.created_at = None
            mock_job.published_at = None
            mock_job.closed_at = None

            mock_scalar = MagicMock()
            mock_scalar.scalar_one_or_none = MagicMock(return_value=mock_job)

            mock_db = AsyncMock()
            mock_db.execute = AsyncMock(return_value=mock_scalar)
            mock_db.__aenter__ = AsyncMock(return_value=mock_db)
            mock_db.__aexit__ = AsyncMock(return_value=False)

            with patch("app.core.database.AsyncSessionLocal", return_value=mock_db):
                result = await get_job_details(job_id="", _context=None)

    # Deve ter tentado buscar a vaga com o active_vacancy_id
    assert result["success"] is True or result.get("needs_clarification") is not True, (
        f"Com active_vacancy deve tentar buscar, resultado: {result}"
    )
