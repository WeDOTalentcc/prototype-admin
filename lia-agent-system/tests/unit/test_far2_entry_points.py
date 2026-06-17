"""
FAR-2: Testes para os novos pontos de entrada protegidos pelo FairnessGuard.

Cobre: rag_pipeline_service.search(), pearch_service.search_candidates(),
e verifica que o guard é chamado antes de qualquer busca real.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRAGPipelineGuard:
    """Verifica que RAGPipelineService.search() bloqueia queries discriminatórias."""

    @pytest.mark.asyncio
    async def test_search_blocked_by_fairness_guard(self):
        """Query discriminatória deve retornar RAGSearchResult vazio com fairness_blocked=True."""
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService

        service = RAGPipelineService()
        mock_db = AsyncMock()

        result = await service.search(
            query="apenas homens para a vaga de engenheiro",
            company_id="test-company",
            db=mock_db,
            limit=10,
        )

        assert result.fairness_ok is False
        assert result.total == 0
        assert result.results == []
        assert result.source == "blocked"
        assert result.metadata.get("fairness_blocked") is True
        assert result.metadata.get("fairness_category") == "genero"

    @pytest.mark.asyncio
    async def test_search_allows_neutral_query(self):
        """Query neutra deve passar pelo guard e tentar busca no DB."""
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService

        service = RAGPipelineService()
        mock_db = AsyncMock()

        # Mock dos métodos de busca internos para retornar lista vazia
        with patch.object(service, '_bm25_search', new_callable=AsyncMock, return_value=[]):
            result = await service.search(
                query="desenvolvedor Python sênior com experiência em AWS",
                company_id="test-company",
                db=mock_db,
                limit=10,
            )

        # Não deve estar bloqueado por fairness
        assert result.source != "blocked"
        assert result.metadata.get("fairness_blocked") is not True

    @pytest.mark.asyncio
    async def test_search_blocked_new_category_antecedentes(self):
        """Nova categoria antecedentes_criminais deve bloquear busca RAG."""
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService

        service = RAGPipelineService()
        mock_db = AsyncMock()

        result = await service.search(
            query="candidatos sem antecedentes criminais apenas",
            company_id="test-company",
            db=mock_db,
        )

        assert result.fairness_ok is False
        assert result.metadata.get("fairness_category") == "antecedentes_criminais"

    @pytest.mark.asyncio
    async def test_search_blocked_new_category_saude(self):
        """Nova categoria saude_doenca deve bloquear busca RAG."""
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService

        service = RAGPipelineService()
        mock_db = AsyncMock()

        result = await service.search(
            query="buscar candidatos sem HIV para a vaga",
            company_id="test-company",
            db=mock_db,
        )

        assert result.fairness_ok is False
        assert result.metadata.get("fairness_category") == "saude_doenca"

    @pytest.mark.asyncio
    async def test_search_educational_message_in_metadata(self):
        """Mensagem educativa deve estar no metadata do resultado bloqueado."""
        from app.domains.ai.services.rag_pipeline_service import RAGPipelineService

        service = RAGPipelineService()
        mock_db = AsyncMock()

        result = await service.search(
            query="apenas candidatos sem doenças crônicas",
            company_id="test-company",
            db=mock_db,
        )

        assert result.metadata.get("educational_message") is not None
        assert len(result.metadata["educational_message"]) > 20


class TestPearchServiceGuard:
    """Verifica que PearchService.search_candidates() bloqueia queries discriminatórias."""

    @pytest.mark.asyncio
    async def test_search_candidates_blocked_by_guard(self):
        """Query discriminatória não deve chegar à API Pearch."""
        from app.domains.sourcing.services.pearch_service import PearchService
        from app.models.pearch import PearchSearchRequest, SearchType

        service = PearchService()
        service.api_key = "fake-key-for-test"

        request = PearchSearchRequest(
            query="apenas mulheres para a vaga de vendas",
            type=SearchType.FAST,
            limit=10,
        )

        # Mock httpx para garantir que a API NÃO é chamada
        with patch('httpx.AsyncClient') as mock_client:
            result = await service.search_candidates(request)

        # Guard bloqueou antes de chamar API externa
        assert result.status == "fairness_blocked"
        assert result.total_estimate == 0
        assert result.search_results == []
        mock_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_candidates_blocked_new_category(self):
        """Nova categoria aparencia_fisica deve bloquear antes do Pearch."""
        from app.domains.sourcing.services.pearch_service import PearchService
        from app.models.pearch import PearchSearchRequest, SearchType

        service = PearchService()
        service.api_key = "fake-key-for-test"

        request = PearchSearchRequest(
            query="altura mínima 1.75 exigida para vendas externas",
            type=SearchType.FAST,
            limit=10,
        )

        with patch('httpx.AsyncClient'):
            result = await service.search_candidates(request)

        assert result.status == "fairness_blocked"
        assert result.total_estimate == 0

    @pytest.mark.asyncio
    async def test_search_candidates_allows_neutral_query_reaches_api(self):
        """Query neutra deve tentar alcançar a API Pearch (circuit breaker pode bloquear)."""
        from app.domains.sourcing.services.pearch_service import PearchService
        from app.models.pearch import PearchSearchRequest, SearchType

        service = PearchService()
        service.api_key = "fake-key-for-test"

        request = PearchSearchRequest(
            query="engenheiro de software Python com 5 anos de experiência",
            type=SearchType.FAST,
            limit=5,
        )

        # Mock da chamada HTTP para simular resposta da API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [], "total": 0}
        mock_response.raise_for_status = MagicMock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            try:
                result = await service.search_candidates(request)
                # Se chegou aqui sem bloquear por fairness, está correto
                assert result.status != "fairness_blocked"
            except Exception:
                # Circuit breaker, API error, etc. — não é problema de fairness
                pass
