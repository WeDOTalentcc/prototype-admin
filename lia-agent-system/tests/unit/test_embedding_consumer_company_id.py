"""Tests for A4: consumer services pass company_id to EmbeddingService.

Verifies that the consumer services wire company_id through to embedding calls,
enabling BYOK routing for tenant-specific embedding providers.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestJobEmbeddingServiceCompanyIdWiring:
    """Consumer 3: job_embedding_service passes company_id to EmbeddingService."""

    @pytest.mark.asyncio
    async def test_generate_job_embedding_passes_company_id(self):
        """generate_job_embedding now accepts and forwards company_id."""
        from app.domains.job_management.services.job_embedding_service import JobEmbeddingService

        svc = JobEmbeddingService()
        mock_vec = [0.1] * 768
        svc._embedding_service = MagicMock()
        svc._embedding_service.generate_embedding = AsyncMock(return_value=mock_vec)

        result = await svc.generate_job_embedding(
            job_title="Engenheiro de Software",
            company_id="test-company-abc-123",
        )

        assert result == mock_vec
        call_kwargs = svc._embedding_service.generate_embedding.call_args
        # company_id should be passed as keyword arg
        assert call_kwargs.kwargs.get("company_id") == "test-company-abc-123", (
            f"Expected company_id=test-company-abc-123 in embedding call, got: {call_kwargs}"
        )

    @pytest.mark.asyncio
    async def test_generate_job_embedding_with_metadata_passes_company_id(self):
        """generate_job_embedding_with_metadata forwards company_id."""
        from app.domains.job_management.services.job_embedding_service import JobEmbeddingService

        svc = JobEmbeddingService()
        mock_result = ([0.1] * 768, "openai", "text-embedding-3-small")
        svc._embedding_service = MagicMock()
        svc._embedding_service.generate_embedding_with_metadata = AsyncMock(return_value=mock_result)

        result = await svc.generate_job_embedding_with_metadata(
            job_title="Desenvolvedor Python",
            company_id="test-company-xyz-456",
        )

        assert result == mock_result
        call_kwargs = svc._embedding_service.generate_embedding_with_metadata.call_args
        assert call_kwargs.kwargs.get("company_id") == "test-company-xyz-456"


class TestDomainEmbeddingServiceCompanyIdWiring:
    """Consumer 5: domain_embedding_service passes company_id to EmbeddingService."""

    @pytest.mark.asyncio
    async def test_embed_document_passes_company_id(self):
        """embed_document passes company_id to generate_embedding."""
        from app.domains.ai.services.domain_embedding_service import DomainEmbeddingService

        svc = DomainEmbeddingService()
        mock_vec = [0.2] * 768
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch(
            "app.shared.intelligence.embedding_service.EmbeddingService"
        ) as MockEmbSvc:
            mock_instance = MagicMock()
            mock_instance.generate_embedding = AsyncMock(return_value=mock_vec)
            MockEmbSvc.return_value = mock_instance

            result = await svc.embed_document(
                content="Python developer with 5 years experience",
                source_type="cv",
                source_id="cand-001",
                company_id="company-byok-test",
                db=mock_db,
            )

        mock_instance.generate_embedding.assert_called_once()
        call_args = mock_instance.generate_embedding.call_args
        # company_id should be passed as kwarg
        assert call_args.kwargs.get("company_id") == "company-byok-test", (
            f"Expected company_id=company-byok-test, got: {call_args}"
        )


class TestJdSimilarServiceCompanyIdWiring:
    """Consumer 4 (A1+A4): jd_similar_service passes company_id to EmbeddingService."""

    def test_jd_similar_service_has_company_id_in_embedding_calls(self):
        """Verify source code contains company_id= in generate_embedding calls."""
        import ast
        import pathlib

        src = pathlib.Path(
            "/home/runner/workspace/lia-agent-system/app/domains/job_creation/services/jd_similar_service.py"
        ).read_text()
        # Both embedding call sites should pass company_id
        assert "company_id=company_id" in src, (
            "jd_similar_service.py must pass company_id to generate_embedding calls"
        )
        # Count occurrences — expect at least 2 (find_similar_jds + record_jd)
        count = src.count("company_id=company_id")
        assert count >= 2, (
            f"Expected at least 2 company_id= passes in jd_similar_service.py, found {count}"
        )
