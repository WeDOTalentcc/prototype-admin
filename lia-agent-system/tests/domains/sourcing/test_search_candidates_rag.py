"""
TDD RED: Tests for search_candidates natural-language (RAG) path.
These tests MUST FAIL until the RAG path is implemented.

Sensor computacional: Verifica que search_candidates(query=...) chama
rag_pipeline_service.search() e não a query SQL.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest


@pytest.mark.asyncio
async def test_search_candidates_uses_rag_when_query_provided():
    """RAG path: quando query= é fornecida, deve chamar rag_pipeline_service.search."""
    from app.domains.sourcing.tools.query_tools import search_candidates
    from app.domains.ai.services.rag_pipeline_service import RAGSearchResult

    mock_rag_result = RAGSearchResult(
        results=[
            {
                "id": "cand-001",
                "name": "João Silva",
                "email": "joao@example.com",
                "seniority_level": "Sênior",
                "lia_score": 82.5,
                "skills": ["Python", "FastAPI"],
                "rag_score": 0.91,
            }
        ],
        query="desenvolvedor Python sênior",
        total=1,
        source="hybrid",
        fairness_ok=True,
        search_time_ms=45.2,
    )

    mock_context = MagicMock()
    mock_context.company_id = "company-abc"

    with patch(
        "app.domains.ai.services.rag_pipeline_service.rag_pipeline_service"
    ) as mock_rag_svc, patch(
        "app.core.database.AsyncSessionLocal"
    ) as mock_db_factory:
        mock_rag_svc.search = AsyncMock(return_value=mock_rag_result)

        # Simulate AsyncSessionLocal as async context manager
        mock_session = AsyncMock()
        mock_db_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await search_candidates(
            query="desenvolvedor Python sênior",
            _context=mock_context,
        )

    assert result["success"] is True, f"Expected success, got: {result}"
    assert result["search_mode"] == "rag_hybrid", f"Expected rag_hybrid mode, got: {result.get('search_mode')}"
    assert result["fairness_ok"] is True
    assert result["data"]["total"] == 1
    assert result["data"]["candidates"][0]["id"] == "cand-001"
    mock_rag_svc.search.assert_called_once()
    call_kwargs = mock_rag_svc.search.call_args
    assert call_kwargs.kwargs.get("query") == "desenvolvedor Python sênior" or call_kwargs.args[0] == "desenvolvedor Python sênior"
    assert call_kwargs.kwargs.get("company_id") == "company-abc"


@pytest.mark.asyncio
async def test_search_candidates_sql_path_unchanged_without_query():
    """SQL path: sem query=, o comportamento existente deve ser mantido."""
    from app.domains.sourcing.tools.query_tools import search_candidates

    mock_context = MagicMock()
    mock_context.company_id = "company-xyz"

    # With SQL path: we mock AsyncSessionLocal to return empty results
    from unittest.mock import MagicMock as MM
    mock_candidates = []

    with patch("app.core.database.AsyncSessionLocal") as mock_db_factory:
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_candidates
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        # No query= param → SQL path
        result = await search_candidates(
            skills=["Python"],
            seniority="Pleno",
            _context=mock_context,
        )

    assert result["success"] is True
    # SQL path should NOT have search_mode=rag_hybrid
    assert result.get("search_mode") != "rag_hybrid"


@pytest.mark.asyncio
async def test_search_candidates_rag_fallback_to_sql_on_error():
    """Fallback: se RAG falhar, deve cair no SQL path sem erro para o caller."""
    from app.domains.sourcing.tools.query_tools import search_candidates

    mock_context = MagicMock()
    mock_context.company_id = "company-fallback"

    mock_candidates = []

    with patch(
        "app.domains.ai.services.rag_pipeline_service.rag_pipeline_service"
    ) as mock_rag_svc, patch(
        "app.core.database.AsyncSessionLocal"
    ) as mock_db_factory:
        # RAG raises an exception
        mock_rag_svc.search = AsyncMock(side_effect=Exception("pgvector unavailable"))

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_candidates
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_db_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_factory.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await search_candidates(
            query="Python developer",
            _context=mock_context,
        )

    # Must not crash — must return success (even if empty via SQL fallback)
    assert result["success"] is True, f"Fallback must succeed, got: {result}"
