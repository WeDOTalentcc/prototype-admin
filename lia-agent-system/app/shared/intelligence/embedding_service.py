"""
Embedding service for generating text embeddings — Task #134.

Refactored to use EmbeddingProviderFactory instead of calling Gemini directly.
Supports multi-provider operation, fallback, and per-embedding provider metadata.
"""
from typing import List
import logging

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 100

EMBEDDING_DIMENSION = 768


class EmbeddingService:
    """Service for generating text embeddings using pluggable providers.

    Delegates to EmbeddingProviderFactory which supports Gemini, OpenAI,
    and any future provider registered at startup.

    Backward-compatible: existing callers that rely on ``generate_embedding()``
    and ``generate_batch_embeddings()`` continue to work without changes.
    """

    async def generate_embedding(
        self,
        text: str,
        provider: str | None = None,
    ) -> list[float]:
        """Generate embedding for text.

        Args:
            text: The text to embed. Empty strings return a zero vector.
            provider: Override the default provider. ``None`` uses the factory
                      default (EMBEDDING_DEFAULT_PROVIDER env var or 'gemini').

        Returns:
            List of floats representing the embedding vector.
        """
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory

        if not text or not text.strip():
            default_prov = EmbeddingProviderFactory.get_default()
            return [0.0] * default_prov.dimensions

        try:
            vector, _provider_name, _model = await EmbeddingProviderFactory.embed_with_fallback(
                text=text,
                preferred_provider=provider,
            )
            return vector
        except Exception as exc:
            logger.error("[EmbeddingService] generate_embedding failed: %s", exc)
            raise

    async def generate_embedding_with_metadata(
        self,
        text: str,
        provider: str | None = None,
    ) -> tuple[list[float], str, str]:
        """Generate embedding and return (vector, provider_name, model_name).

        Use this variant when callers need to record which provider/model
        generated the vector (e.g., for the job_embeddings table).
        """
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory

        if not text or not text.strip():
            default_prov = EmbeddingProviderFactory.get_default()
            return (
                [0.0] * default_prov.dimensions,
                default_prov.provider_name,
                default_prov.default_model,
            )

        return await EmbeddingProviderFactory.embed_with_fallback(
            text=text,
            preferred_provider=provider,
        )

    async def generate_batch_embeddings(
        self,
        texts: list[str],
        provider: str | None = None,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.
            provider: Override the default provider.

        Returns:
            List of embedding vectors, one per input text.
        """
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory

        if not texts:
            return []

        try:
            vectors, _provider_name, _model = (
                await EmbeddingProviderFactory.embed_batch_with_fallback(
                    texts=texts,
                    preferred_provider=provider,
                )
            )
            return vectors
        except Exception as exc:
            logger.error("[EmbeddingService] generate_batch_embeddings failed: %s", exc)
            raise

    async def generate_batch_embeddings_with_metadata(
        self,
        texts: list[str],
        provider: str | None = None,
    ) -> tuple[list[list[float]], str, str]:
        """Generate batch embeddings and return (vectors, provider_name, model_name)."""
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory

        if not texts:
            default_prov = EmbeddingProviderFactory.get_default()
            return [], default_prov.provider_name, default_prov.default_model

        return await EmbeddingProviderFactory.embed_batch_with_fallback(
            texts=texts,
            preferred_provider=provider,
        )

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 100,
    ) -> list[str]:
        """Split text into overlapping chunks for embedding.

        Args:
            text: The text to chunk.
            chunk_size: Maximum characters per chunk.
            overlap: Number of characters to overlap between chunks.

        Returns:
            List of text chunks.
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            if end < len(text):
                last_period = text.rfind(".", start, end)
                last_newline = text.rfind("\n", start, end)
                break_point = max(last_period, last_newline)

                if break_point > start + chunk_size // 2:
                    end = break_point + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks


embedding_service = EmbeddingService()
