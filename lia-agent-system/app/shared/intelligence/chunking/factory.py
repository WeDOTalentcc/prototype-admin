"""Factory for selecting chunking strategy based on document type and feature flags."""

import os
import logging

from app.shared.intelligence.chunking.base import ChunkingStrategy, DocumentType
from app.shared.intelligence.chunking.sliding_window import SlidingWindowChunker
from app.shared.intelligence.chunking.section_aware import SectionAwareChunker
from app.shared.intelligence.chunking.semantic_chunker import SemanticChunker
from app.shared.intelligence.chunking.recursive import RecursiveTextSplitter

logger = logging.getLogger(__name__)

_STRATEGY_MAP = {
    "sliding_window": "sliding_window",
    "section_aware": "section_aware",
    "semantic": "semantic",
    "recursive": "recursive",
}

_DEFAULT_DOC_TYPE_STRATEGY: dict[str, str] = {
    DocumentType.CV: "recursive",
    DocumentType.JOB_DESCRIPTION: "recursive",
    DocumentType.POLICY: "recursive",
    DocumentType.GENERIC: "recursive",
}


def _get_doc_type_config(document_type: DocumentType) -> tuple[int, int]:
    """Return (chunk_size, overlap) for a document type from settings."""
    try:
        from app.core.config import settings as _s
        if document_type == DocumentType.CV:
            return _s.CHUNKING_CV_CHUNK_SIZE, _s.CHUNKING_CV_OVERLAP
        elif document_type == DocumentType.JOB_DESCRIPTION:
            return _s.CHUNKING_JD_CHUNK_SIZE, _s.CHUNKING_JD_OVERLAP
        elif document_type == DocumentType.POLICY:
            return _s.CHUNKING_POLICY_CHUNK_SIZE, _s.CHUNKING_POLICY_OVERLAP
        else:
            return _s.CHUNKING_GENERIC_CHUNK_SIZE, _s.CHUNKING_GENERIC_OVERLAP
    except Exception:
        return 1000, 100


class ChunkingStrategyFactory:
    """Selects the appropriate chunking strategy.

    Resolution order:
    1. Explicit ``override`` parameter (per-call control)
    2. CHUNKING_STRATEGY env var (feature flag for global rollback)
    3. Document-type default mapping (all types → recursive by default)

    Chunk size and overlap are configurable per document type via settings
    (CHUNKING_CV_CHUNK_SIZE, CHUNKING_JD_CHUNK_SIZE, etc.) or explicit kwargs.
    """

    @staticmethod
    def get_strategy(
        document_type: DocumentType | str = DocumentType.GENERIC,
        override: str | None = None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> ChunkingStrategy:
        if isinstance(document_type, str):
            try:
                document_type = DocumentType(document_type)
            except ValueError:
                document_type = DocumentType.GENERIC

        env_override = os.environ.get("CHUNKING_STRATEGY", "").strip().lower()

        strategy_name = override or env_override or _DEFAULT_DOC_TYPE_STRATEGY.get(
            document_type, "sliding_window"
        )

        if strategy_name not in _STRATEGY_MAP:
            logger.warning(
                "[ChunkingStrategyFactory] Unknown strategy %r, falling back to sliding_window",
                strategy_name,
            )
            strategy_name = "sliding_window"

        default_size, default_overlap = _get_doc_type_config(document_type)
        size = chunk_size or default_size
        overlap = chunk_overlap or default_overlap

        logger.debug(
            "[ChunkingStrategyFactory] doc_type=%s strategy=%s size=%d overlap=%d (override=%s env=%s)",
            document_type.value,
            strategy_name,
            size,
            overlap,
            override,
            env_override or "unset",
        )

        if strategy_name == "section_aware":
            doc_label = "job_description" if document_type == DocumentType.JOB_DESCRIPTION else "cv"
            return SectionAwareChunker(document_type=doc_label, max_chunk_size=size, overlap=overlap)
        elif strategy_name == "semantic":
            return SemanticChunker(max_chunk_size=size)
        elif strategy_name == "recursive":
            return RecursiveTextSplitter(chunk_size=size, chunk_overlap=overlap)
        else:
            return SlidingWindowChunker(chunk_size=size, overlap=overlap)

    @staticmethod
    def get_strategy_name(document_type: DocumentType | str = DocumentType.GENERIC) -> str:
        strategy = ChunkingStrategyFactory.get_strategy(document_type)
        return strategy.strategy_name
