"""
Embedding service for generating text embeddings — Task #134.

Refactored to use EmbeddingProviderFactory instead of calling Gemini directly.
Supports multi-provider operation, fallback, and per-embedding provider metadata.

Chunking strategies (Task #126):
- sliding_window: Original fixed-size overlapping chunks
- section_aware: Header/section-based chunking for CVs and JDs
- semantic: Embedding similarity-based sentence grouping
"""
import hashlib
import logging
import os
import time
from collections import OrderedDict

from app.shared.tracing import get_tracer, trace_span

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 100

EMBEDDING_DIMENSION = 768

_EMBEDDING_CACHE_SIZE = int(os.getenv("EMBEDDING_CACHE_SIZE", "512"))


class EmbeddingService:
    """Service for generating text embeddings using pluggable providers.

    Delegates to EmbeddingProviderFactory which supports Gemini, OpenAI,
    and any future provider registered at startup.

    Backward-compatible: existing callers that rely on ``generate_embedding()``
    and ``generate_batch_embeddings()`` continue to work without changes.
    """

    def __init__(self) -> None:
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._cache_max = _EMBEDDING_CACHE_SIZE

    @staticmethod
    def _cache_key(text: str, provider: str | None) -> str:
        h = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:24]
        return f"{provider or 'default'}:{h}"

    def _cache_get(self, key: str) -> list[float] | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def _cache_put(self, key: str, vector: list[float]) -> None:
        self._cache[key] = vector
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_max:
            self._cache.popitem(last=False)

    @trace_span("embedding.generate", attributes={"service": "embedding_service", "tier_name": "embedding_generate"})
    async def generate_embedding(
        self,
        text: str,
        provider: str | None = None,
        *,
        mask_names: bool = False,
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

        tracer = get_tracer()

        if not text or not text.strip():
            async with tracer.start_span("embedding.shortcircuit_empty", attributes={
                "service": "embedding_service", "tier_name": "embedding_shortcircuit",
                "result": "zero_vector", "reason": "empty_text",
            }):
                pass
            default_prov = EmbeddingProviderFactory.get_default()
            return [0.0] * default_prov.dimensions

        # LGPD (audit 2026-06-06): redige PII ANTES de cache/API no
        # chokepoint -- nenhum caller pode esquecer. Estruturada sempre
        # (CPF/email/tel/etc); nomes (Presidio NER) quando mask_names=True
        # (superficies de candidato/conversa). Default False = base segura.
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        text = strip_pii_for_llm_prompt(text, mask_names=mask_names)

        ck = self._cache_key(text, provider)
        cached = self._cache_get(ck)
        if cached is not None:
            async with tracer.start_span("embedding.cache_hit", attributes={
                "service": "embedding_service", "tier_name": "embedding_cache",
                "cache_result": "hit", "vector_dim": str(len(cached)),
            }):
                pass
            return cached

        async with tracer.start_span("embedding.cache_miss", attributes={
            "service": "embedding_service", "tier_name": "embedding_cache",
            "cache_result": "miss", "text_length": str(len(text)),
        }):
            pass

        try:
            async with tracer.start_span("embedding.api_call", attributes={
                "service": "embedding_service", "tier_name": "embedding_api_call",
                "provider_hint": provider or "default",
            }) as api_span:
                _t0 = time.perf_counter()
                vector, _provider_name, _model = await EmbeddingProviderFactory.embed_with_fallback(
                    text=text,
                    preferred_provider=provider,
                )
                _elapsed = (time.perf_counter() - _t0) * 1000
                api_span.set_attribute("latency_ms", f"{_elapsed:.2f}")
                api_span.set_attribute("provider_used", _provider_name)
                api_span.set_attribute("model_used", _model)
                api_span.set_attribute("vector_dim", str(len(vector)))
            self._cache_put(ck, vector)
            return vector
        except Exception as exc:
            logger.error("[EmbeddingService] generate_embedding failed: %s", exc)
            raise

    @trace_span("embedding.generate_with_metadata", attributes={"service": "embedding_service", "tier_name": "embedding_generate_metadata"})
    async def generate_embedding_with_metadata(
        self,
        text: str,
        provider: str | None = None,
        *,
        mask_names: bool = False,
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

        # LGPD (audit 2026-06-06): redige PII ANTES de cache/API no
        # chokepoint -- nenhum caller pode esquecer. Estruturada sempre
        # (CPF/email/tel/etc); nomes (Presidio NER) quando mask_names=True
        # (superficies de candidato/conversa). Default False = base segura.
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        text = strip_pii_for_llm_prompt(text, mask_names=mask_names)

        tracer = get_tracer()
        async with tracer.start_span("embedding.api_call", attributes={
            "service": "embedding_service", "tier_name": "embedding_api_call",
            "provider_hint": provider or "default",
        }) as api_span:
            _t0 = time.perf_counter()
            result = await EmbeddingProviderFactory.embed_with_fallback(
                text=text,
                preferred_provider=provider,
            )
            _elapsed = (time.perf_counter() - _t0) * 1000
            api_span.set_attribute("latency_ms", f"{_elapsed:.2f}")
            api_span.set_attribute("provider_used", result[1])
            api_span.set_attribute("model_used", result[2])
        return result

    @trace_span("embedding.batch_generate", attributes={"service": "embedding_service", "tier_name": "embedding_batch"})
    async def generate_batch_embeddings(
        self,
        texts: list[str],
        provider: str | None = None,
        *,
        mask_names: bool = False,
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

        # LGPD (audit 2026-06-06): redige PII ANTES de cache/API no
        # chokepoint -- nenhum caller pode esquecer. Estruturada sempre
        # (CPF/email/tel/etc); nomes (Presidio NER) quando mask_names=True
        # (superficies de candidato/conversa). Default False = base segura.
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        texts = [strip_pii_for_llm_prompt(t, mask_names=mask_names) for t in texts]

        tracer = get_tracer()
        try:
            async with tracer.start_span("embedding.api_call", attributes={
                "service": "embedding_service", "tier_name": "embedding_api_call",
                "provider_hint": provider or "default",
                "batch_size": str(len(texts)),
            }) as api_span:
                _t0 = time.perf_counter()
                vectors, _provider_name, _model = (
                    await EmbeddingProviderFactory.embed_batch_with_fallback(
                        texts=texts,
                        preferred_provider=provider,
                    )
                )
                _elapsed = (time.perf_counter() - _t0) * 1000
                api_span.set_attribute("latency_ms", f"{_elapsed:.2f}")
                api_span.set_attribute("provider_used", _provider_name)
                api_span.set_attribute("model_used", _model)
                api_span.set_attribute("vectors_returned", str(len(vectors)))
            return vectors
        except Exception as exc:
            logger.error("[EmbeddingService] generate_batch_embeddings failed: %s", exc)
            raise

    @trace_span("embedding.batch_generate_with_metadata", attributes={"service": "embedding_service", "tier_name": "embedding_batch_metadata"})
    async def generate_batch_embeddings_with_metadata(
        self,
        texts: list[str],
        provider: str | None = None,
        *,
        mask_names: bool = False,
    ) -> tuple[list[list[float]], str, str]:
        """Generate batch embeddings and return (vectors, provider_name, model_name)."""
        from app.shared.providers.embedding_factory import EmbeddingProviderFactory

        if not texts:
            default_prov = EmbeddingProviderFactory.get_default()
            return [], default_prov.provider_name, default_prov.default_model

        # LGPD (audit 2026-06-06): redige PII ANTES de cache/API no
        # chokepoint -- nenhum caller pode esquecer. Estruturada sempre
        # (CPF/email/tel/etc); nomes (Presidio NER) quando mask_names=True
        # (superficies de candidato/conversa). Default False = base segura.
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        texts = [strip_pii_for_llm_prompt(t, mask_names=mask_names) for t in texts]

        tracer = get_tracer()
        async with tracer.start_span("embedding.api_call", attributes={
            "service": "embedding_service", "tier_name": "embedding_api_call",
            "provider_hint": provider or "default",
            "batch_size": str(len(texts)),
        }) as api_span:
            _t0 = time.perf_counter()
            result = await EmbeddingProviderFactory.embed_batch_with_fallback(
                texts=texts,
                preferred_provider=provider,
            )
            _elapsed = (time.perf_counter() - _t0) * 1000
            api_span.set_attribute("latency_ms", f"{_elapsed:.2f}")
            api_span.set_attribute("provider_used", result[1])
            api_span.set_attribute("model_used", result[2])
        return result

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 100,
        document_type: str = "generic",
        strategy_override: str | None = None,
    ) -> list[str]:
        """Split text into chunks for embedding.

        Uses the ChunkingStrategyFactory to select the best strategy based on
        document type and the CHUNKING_STRATEGY feature flag.

        Instrumented with sync span for chunk_generation phase.

        Args:
            text: The text to chunk.
            chunk_size: Maximum characters per chunk (used by sliding_window).
            overlap: Number of characters to overlap (used by sliding_window).
            document_type: One of "cv", "job_description", "generic".
            strategy_override: Force a specific strategy ("sliding_window",
                "section_aware", or "semantic").

        Returns:
            List of text chunks.
        """
        tracer = get_tracer()
        span = tracer.create_span("embedding.chunk_generation", attributes={
            "service": "embedding_service", "tier_name": "embedding_chunk",
            "chunk_size": str(chunk_size), "overlap": str(overlap),
            "text_length": str(len(text) if text else 0),
            "document_type": document_type,
            "strategy_override": strategy_override or "auto",
        }, _start_otel=True)

        try:
            from app.shared.intelligence.chunking.factory import ChunkingStrategyFactory

            strategy = ChunkingStrategyFactory.get_strategy(
                document_type=document_type,
                override=strategy_override,
            )

            if strategy.strategy_name == "sliding_window":
                from app.shared.intelligence.chunking.sliding_window import SlidingWindowChunker
                strategy = SlidingWindowChunker(chunk_size=chunk_size, overlap=overlap)

            span.set_attribute("strategy_resolved", strategy.strategy_name)

            chunk_objects = strategy.chunk(text)
            chunks = [c.text for c in chunk_objects]
            span.set_attribute("chunks_produced", str(len(chunks)))
            return chunks
        finally:
            from app.shared.tracing import finish_span
            finish_span(span, status="ok")


embedding_service = EmbeddingService()
