"""
GeminiEmbeddingProvider — Task #134.

Wraps Gemini text-embedding-004 via Replit AI Integrations.
Extracted from the original EmbeddingService.
"""
import logging
import os

from app.shared.providers.embedding_provider import EmbeddingProviderABC, EmbeddingResult

logger = logging.getLogger(__name__)

GEMINI_EMBEDDING_MODEL = "text-embedding-004"
GEMINI_EMBEDDING_DIMENSIONS = 768
GEMINI_MAX_TEXT_CHARS = 8000


class GeminiEmbeddingProvider(EmbeddingProviderABC):
    """Embedding provider using Google Gemini text-embedding-004.

    Uses Replit AI Integration environment variables:
    - AI_INTEGRATIONS_GEMINI_API_KEY
    - AI_INTEGRATIONS_GEMINI_BASE_URL
    """

    _provider_name = "gemini"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        self._model = model or GEMINI_EMBEDDING_MODEL
        self._client = None
        self._custom_api_key = api_key

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def default_model(self) -> str:
        return GEMINI_EMBEDDING_MODEL

    @property
    def dimensions(self) -> int:
        return GEMINI_EMBEDDING_DIMENSIONS

    @property
    def _gemini_client(self):
        """Lazy-initialize Gemini client (tenant-aware)."""
        if self._client is None:
            from google import genai

            if self._custom_api_key:
                # Tenant-specific key — direct Google API
                self._client = genai.Client(api_key=self._custom_api_key)
                logger.info("[GeminiEmbedding] Using tenant-specific API key")
            else:
                # Global Replit AI Integration
                api_key = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
                base_url = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")
                if not api_key or not base_url:
                    raise ValueError(
                        "AI_INTEGRATIONS_GEMINI_API_KEY or AI_INTEGRATIONS_GEMINI_BASE_URL not configured"
                    )
                self._client = genai.Client(
                    api_key=api_key,
                    http_options={"api_version": "", "base_url": base_url},
                )
        return self._client

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text using Gemini."""
        if not text or not text.strip():
            return EmbeddingResult(
                vector=[0.0] * GEMINI_EMBEDDING_DIMENSIONS,
                provider=self.provider_name,
                model=self._model,
            )

        clean = text.strip()[:GEMINI_MAX_TEXT_CHARS]

        try:
            client = self._gemini_client
            response = client.models.embed_content(
                model=self._model,
                contents=clean,
            )

            if response and response.embeddings:
                vector = list(response.embeddings[0].values)
                if len(vector) != GEMINI_EMBEDDING_DIMENSIONS:
                    logger.warning(
                        "[GeminiEmbedding] Unexpected dimension %d, expected %d",
                        len(vector),
                        GEMINI_EMBEDDING_DIMENSIONS,
                    )
                return EmbeddingResult(
                    vector=vector,
                    provider=self.provider_name,
                    model=self._model,
                )

            logger.error("[GeminiEmbedding] Empty response from Gemini API")
            return EmbeddingResult(
                vector=[0.0] * GEMINI_EMBEDDING_DIMENSIONS,
                provider=self.provider_name,
                model=self._model,
            )

        except Exception as exc:
            logger.error("[GeminiEmbedding] embed_text failed: %s", exc)
            raise

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for a list of texts using Gemini."""
        results: list[EmbeddingResult] = []

        for text in texts:
            try:
                result = await self.embed_text(text)
                results.append(result)
            except Exception as exc:
                logger.error(
                    "[GeminiEmbedding] embed_batch item failed, returning zero vector: %s", exc
                )
                results.append(
                    EmbeddingResult(
                        vector=[0.0] * GEMINI_EMBEDDING_DIMENSIONS,
                        provider=self.provider_name,
                        model=self._model,
                    )
                )

        return results
