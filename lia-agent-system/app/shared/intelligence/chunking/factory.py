"""Factory for selecting chunking strategy based on document type and feature flags."""

import os
import logging

from app.shared.intelligence.chunking.base import ChunkingStrategy, DocumentType
from app.shared.intelligence.chunking.sliding_window import SlidingWindowChunker
from app.shared.intelligence.chunking.section_aware import SectionAwareChunker
from app.shared.intelligence.chunking.semantic_chunker import SemanticChunker

logger = logging.getLogger(__name__)

_STRATEGY_MAP = {
    "sliding_window": "sliding_window",
    "section_aware": "section_aware",
    "semantic": "semantic",
}

_DEFAULT_DOC_TYPE_STRATEGY: dict[str, str] = {
    DocumentType.CV: "section_aware",
    DocumentType.JOB_DESCRIPTION: "section_aware",
    DocumentType.GENERIC: "sliding_window",
}


class ChunkingStrategyFactory:
    """Selects the appropriate chunking strategy.

    Resolution order:
    1. Explicit ``override`` parameter (per-call control)
    2. CHUNKING_STRATEGY env var (feature flag for global rollback)
    3. Document-type default mapping (CV/JD → section_aware, generic → sliding_window)
    """

    @staticmethod
    def get_strategy(
        document_type: DocumentType | str = DocumentType.GENERIC,
        override: str | None = None,
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

        logger.debug(
            "[ChunkingStrategyFactory] doc_type=%s strategy=%s (override=%s env=%s)",
            document_type.value,
            strategy_name,
            override,
            env_override or "unset",
        )

        if strategy_name == "section_aware":
            doc_label = "job_description" if document_type == DocumentType.JOB_DESCRIPTION else "cv"
            return SectionAwareChunker(document_type=doc_label)
        elif strategy_name == "semantic":
            return SemanticChunker()
        else:
            return SlidingWindowChunker()

    @staticmethod
    def get_strategy_name(document_type: DocumentType | str = DocumentType.GENERIC) -> str:
        strategy = ChunkingStrategyFactory.get_strategy(document_type)
        return strategy.strategy_name
