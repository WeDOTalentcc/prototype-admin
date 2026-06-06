"""
OpenAIEmbeddingProvider — Task #134.

Wraps OpenAI text-embedding-3-small via Replit AI Integrations.

Dimension compatibility:
  text-embedding-3-small supports output dimensions from 512 to 1536.
  The default here is 768 to match the existing job_embeddings.embedding
  column type (Vector(768)) and remain compatible with Gemini embeddings.
  Pass output_dimensions=1536 only when using a separate storage column.
"""
import logging
import os

from app.shared.providers.embedding_provider import EmbeddingProviderABC, EmbeddingResult

logger = logging.getLogger(__name__)

OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_EMBEDDING_DIMENSIONS_DEFAULT = 768
OPENAI_EMBEDDING_DIMENSIONS_FULL = 1536
OPENAI_MAX_TEXT_CHARS = 8000
OPENAI_BATCH_SIZE = 100


class OpenAIEmbeddingProvider(EmbeddingProviderABC):
    """Embedding provider using OpenAI text-embedding-3-small.

    Uses Replit AI Integration environment variables:
    - AI_INTEGRATIONS_OPENAI_API_KEY
    - AI_INTEGRATIONS_OPENAI_BASE_URL

    Dimension strategy:
        By default this provider requests 768-dimensional output (the same
        dimensionality as Gemini text-embedding-004) via the ``dimensions``
        parameter supported by text-embedding-3-small.  This ensures that
        both providers write compatible vectors into the shared
        job_embeddings.embedding Vector(768) column without any schema changes.

        Pass ``output_dimensions=1536`` if you want the full native output
        (requires a separate column or table — not compatible with the default
        job_embeddings schema).
    """

    _provider_name = "openai"

    def __init__(
        self,
        model: str | None = None,
        output_dimensions: int = OPENAI_EMBEDDING_DIMENSIONS_DEFAULT,
    ):
        self._model = model or OPENAI_EMBEDDING_MODEL
        self._output_dimensions = output_dimensions
        self._client = None

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return OPENAI_EMBEDDING_MODEL

    @property
    def dimensions(self) -> int:
        return self._output_dimensions

    @property
    def _openai_client(self):
        """Lazy-initialize OpenAI client."""
        if self._client is None:
            from openai import OpenAI

            # Embedding P2 (audit 2026-06-06): aceitar OPENAI_API_KEY como
            # fallback ao Replit AI Integration. O proxy gemini rejeita
            # batchEmbedContents (INVALID_ENDPOINT) -> o openai e o provider
            # funcional de fato, e a chave canonica OPENAI_API_KEY ja esta
            # provisionada no ambiente. Sem AI_INTEGRATIONS_OPENAI_BASE_URL o
            # SDK usa api.openai.com (direto). Alinha com o design "OpenAI
            # text-embedding-3-small primario" (vector_semantic_cache/rag).
            api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY") or os.environ.get(
                "OPENAI_API_KEY"
            )
            base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")

            if not api_key:
                raise ValueError(
                    "Nenhuma chave OpenAI configurada "
                    "(AI_INTEGRATIONS_OPENAI_API_KEY ou OPENAI_API_KEY)"
                )

            kwargs = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url

            self._client = OpenAI(**kwargs)
        return self._client

    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text using OpenAI."""
        if not text or not text.strip():
            return EmbeddingResult(
                vector=[0.0] * self._output_dimensions,
                provider=self.provider_name,
                model=self._model,
            )

        clean = text.strip()[:OPENAI_MAX_TEXT_CHARS]

        try:
            client = self._openai_client
            response = client.embeddings.create(
                model=self._model,
                input=clean,
                dimensions=self._output_dimensions,
            )

            if response and response.data:
                vector = response.data[0].embedding
                return EmbeddingResult(
                    vector=list(vector),
                    provider=self.provider_name,
                    model=self._model,
                )

            logger.error("[OpenAIEmbedding] Empty response from OpenAI API")
            return EmbeddingResult(
                vector=[0.0] * self._output_dimensions,
                provider=self.provider_name,
                model=self._model,
            )

        except Exception as exc:
            logger.error("[OpenAIEmbedding] embed_text failed: %s", exc)
            raise

    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for a list of texts using OpenAI batch API."""
        if not texts:
            return []

        results: list[EmbeddingResult] = []

        for i in range(0, len(texts), OPENAI_BATCH_SIZE):
            batch = texts[i : i + OPENAI_BATCH_SIZE]
            clean_batch = [
                t.strip()[:OPENAI_MAX_TEXT_CHARS] if t and t.strip() else "" for t in batch
            ]

            non_empty_indices = [idx for idx, t in enumerate(clean_batch) if t]
            non_empty_texts = [clean_batch[idx] for idx in non_empty_indices]

            batch_results: list[EmbeddingResult | None] = [None] * len(batch)

            for idx in range(len(batch)):
                if idx not in non_empty_indices:
                    batch_results[idx] = EmbeddingResult(
                        vector=[0.0] * self._output_dimensions,
                        provider=self.provider_name,
                        model=self._model,
                    )

            if non_empty_texts:
                try:
                    client = self._openai_client
                    response = client.embeddings.create(
                        model=self._model,
                        input=non_empty_texts,
                        dimensions=self._output_dimensions,
                    )
                    for resp_item in response.data:
                        original_idx = non_empty_indices[resp_item.index]
                        batch_results[original_idx] = EmbeddingResult(
                            vector=list(resp_item.embedding),
                            provider=self.provider_name,
                            model=self._model,
                        )
                except Exception as exc:
                    logger.error(
                        "[OpenAIEmbedding] embed_batch chunk failed, returning zero vectors: %s",
                        exc,
                    )
                    for idx in non_empty_indices:
                        if batch_results[idx] is None:
                            batch_results[idx] = EmbeddingResult(
                                vector=[0.0] * self._output_dimensions,
                                provider=self.provider_name,
                                model=self._model,
                            )

            results.extend(batch_results)

        return results
