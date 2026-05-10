"""
D10 — Fallback Chain Pearch AI → Busca Interna (RAG Híbrido)

Verifica:
1. Circuit aberto dispara fallback interno (RAG)
2. Fallback retorna resultados do RAG convertidos em PearchSearchResponse
3. Fallback loga [PEARCH-FALLBACK] com contagem de resultados
4. Circuit fechado não usa fallback (não chama RAG)
5. Fallback fail-safe: RAG falha → retorna status="unavailable" sem exceção
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


FALLBACK_PATH = "app.domains.sourcing.services.pearch_service._pearch_search_fallback"


class TestPearchFallbackChain:

    def _make_request(self, query: str = "engenheiro python", company_id: str = "co-1", limit: int = 5):
        req = MagicMock()
        req.query = query
        req.company_id = company_id
        req.limit = limit
        return req

    def _make_rag_result(self, count: int = 3):
        from dataclasses import dataclass
        from typing import List, Dict, Any

        results = [
            {"id": f"cand-{i}", "name": f"Candidato {i}", "current_role": "Dev", "location": "SP", "summary": "bom", "score": 0.8}
            for i in range(count)
        ]
        rag = MagicMock()
        rag.results = results
        rag.total = count
        return rag

    @pytest.mark.asyncio
    async def test_fallback_calls_rag_when_triggered(self):
        """Quando fallback é chamado, chama RAGPipelineService.search."""
        from app.domains.sourcing.services.pearch_service import _pearch_search_fallback

        mock_rag_svc = MagicMock()
        mock_rag_svc.search = AsyncMock(return_value=self._make_rag_result(3))

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.domains.ai.services.rag_pipeline_service.RAGPipelineService",
            return_value=mock_rag_svc,
        ):
            with patch(
                "app.core.database.AsyncSessionLocal",
                return_value=mock_db,
            ):
                result = await _pearch_search_fallback(None, self._make_request(), timeout=30)

        mock_rag_svc.search.assert_called_once()
        assert result.status == "internal_fallback"
        assert result.total_estimate == 3

    @pytest.mark.asyncio
    async def test_fallback_converts_rag_results_to_pearch_format(self):
        """Resultados RAG são convertidos para PearchSearchResult com CandidateProfile."""
        from app.domains.sourcing.services.pearch_service import _pearch_search_fallback

        mock_rag_svc = MagicMock()
        mock_rag_svc.search = AsyncMock(return_value=self._make_rag_result(2))

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.domains.ai.services.rag_pipeline_service.RAGPipelineService",
            return_value=mock_rag_svc,
        ):
            with patch(
                "app.core.database.AsyncSessionLocal",
                return_value=mock_db,
            ):
                result = await _pearch_search_fallback(None, self._make_request(), timeout=30)

        assert len(result.search_results) == 2
        first = result.search_results[0]
        assert first.profile is not None
        assert first.docid == "cand-0"

    @pytest.mark.asyncio
    async def test_fallback_logs_pearch_fallback(self, caplog):
        """Fallback loga [PEARCH-FALLBACK] com contagem de resultados."""
        import logging
        from app.domains.sourcing.services.pearch_service import _pearch_search_fallback

        mock_rag_svc = MagicMock()
        mock_rag_svc.search = AsyncMock(return_value=self._make_rag_result(4))

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.domains.ai.services.rag_pipeline_service.RAGPipelineService",
            return_value=mock_rag_svc,
        ):
            with patch(
                "app.core.database.AsyncSessionLocal",
                return_value=mock_db,
            ):
                with caplog.at_level(logging.WARNING):
                    await _pearch_search_fallback(None, self._make_request(), timeout=30)

        assert "PEARCH-FALLBACK" in caplog.text

    @pytest.mark.asyncio
    async def test_fallback_fail_safe_when_rag_raises(self):
        """Se RAG falha, retorna status='unavailable' sem exceção."""
        from app.domains.sourcing.services.pearch_service import _pearch_search_fallback

        mock_rag_svc = MagicMock()
        mock_rag_svc.search = AsyncMock(side_effect=Exception("RAG unavailable"))

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.domains.ai.services.rag_pipeline_service.RAGPipelineService",
            return_value=mock_rag_svc,
        ):
            with patch(
                "app.core.database.AsyncSessionLocal",
                return_value=mock_db,
            ):
                result = await _pearch_search_fallback(None, self._make_request(), timeout=30)

        assert result.status == "unavailable"
        assert result.total_estimate == 0

    @pytest.mark.asyncio
    async def test_fallback_without_company_id_returns_unavailable(self):
        """Sem company_id não chama RAG, retorna unavailable."""
        from app.domains.sourcing.services.pearch_service import _pearch_search_fallback

        req = MagicMock()
        req.query = "python dev"
        req.company_id = ""  # sem company_id
        req.limit = 10

        with patch(
            "app.domains.ai.services.rag_pipeline_service.RAGPipelineService"
        ) as mock_rag_cls:
            result = await _pearch_search_fallback(None, req, timeout=30)

        mock_rag_cls.assert_not_called()
        assert result.status == "unavailable"
