"""Chunking strategies for RAG document processing.

Supports four strategies:
- sliding_window: Original fixed-size overlapping chunks
- section_aware: Header/section-based chunking for CVs and JDs
- semantic: Embedding similarity-based sentence grouping
- recursive: Hierarchical splitting by semantic boundaries (paragraphs, sentences, words)
"""

from app.shared.intelligence.chunking.base import ChunkingStrategy, DocumentType
from app.shared.intelligence.chunking.sliding_window import SlidingWindowChunker
from app.shared.intelligence.chunking.section_aware import SectionAwareChunker
from app.shared.intelligence.chunking.semantic_chunker import SemanticChunker
from app.shared.intelligence.chunking.recursive import RecursiveTextSplitter
from app.shared.intelligence.chunking.factory import ChunkingStrategyFactory

__all__ = [
    "ChunkingStrategy",
    "DocumentType",
    "SlidingWindowChunker",
    "SectionAwareChunker",
    "SemanticChunker",
    "RecursiveTextSplitter",
    "ChunkingStrategyFactory",
]
