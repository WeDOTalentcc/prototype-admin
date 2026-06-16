"""Semantic chunking strategy based on embedding similarity between sentences."""

import logging
import re
import math

from app.shared.intelligence.chunking.base import Chunk, ChunkingStrategy

logger = logging.getLogger(__name__)

_DEFAULT_SIMILARITY_THRESHOLD = 0.5
_DEFAULT_MAX_CHUNK_SIZE = 2000
_DEFAULT_MIN_CHUNK_SIZE = 100


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _split_sentences(text: str) -> list[str]:
    raw = re.split(r'(?<=[.!?;])\s+|\n{2,}', text)
    sentences = [s.strip() for s in raw if s.strip()]
    return sentences


class SemanticChunker(ChunkingStrategy):
    """Groups consecutive sentences by embedding similarity.

    Sentences with cosine similarity above the threshold are kept in
    the same chunk. When similarity drops below the threshold, a new
    chunk boundary is created.
    """

    def __init__(
        self,
        similarity_threshold: float = _DEFAULT_SIMILARITY_THRESHOLD,
        max_chunk_size: int = _DEFAULT_MAX_CHUNK_SIZE,
        min_chunk_size: int = _DEFAULT_MIN_CHUNK_SIZE,
    ):
        self._threshold = similarity_threshold
        self._max_chunk_size = max_chunk_size
        self._min_chunk_size = min_chunk_size

    @property
    def strategy_name(self) -> str:
        return "semantic"

    def chunk(self, text: str, embeddings: list[list[float]] | None = None, **kwargs) -> list[Chunk]:
        if not text:
            return []

        sentences = _split_sentences(text)
        if not sentences:
            return [Chunk(text=text, index=0, metadata={"strategy": "semantic"})] if text.strip() else []

        if len(sentences) == 1:
            return [Chunk(text=sentences[0], index=0, metadata={"strategy": "semantic"})]

        if embeddings and len(embeddings) == len(sentences):
            return self._chunk_with_embeddings(sentences, embeddings)

        logger.debug("[SemanticChunker] No pre-computed embeddings, falling back to sliding_window")
        from app.shared.intelligence.chunking.sliding_window import SlidingWindowChunker
        return SlidingWindowChunker().chunk(text)

    def _chunk_with_embeddings(
        self, sentences: list[str], embeddings: list[list[float]]
    ) -> list[Chunk]:
        groups: list[list[str]] = [[sentences[0]]]

        for i in range(1, len(sentences)):
            sim = _cosine_similarity(embeddings[i - 1], embeddings[i])

            current_group_text = " ".join(groups[-1])

            if sim >= self._threshold and len(current_group_text) + len(sentences[i]) <= self._max_chunk_size:
                groups[-1].append(sentences[i])
            else:
                groups.append([sentences[i]])

        merged_groups = self._merge_small_groups(groups)

        chunks: list[Chunk] = []
        for idx, group in enumerate(merged_groups):
            chunk_text = " ".join(group)
            chunks.append(Chunk(
                text=chunk_text,
                index=idx,
                metadata={"strategy": "semantic", "sentence_count": len(group)},
            ))

        return chunks

    def _merge_small_groups(self, groups: list[list[str]]) -> list[list[str]]:
        if not groups:
            return groups

        merged: list[list[str]] = [groups[0]]

        for group in groups[1:]:
            current_text = " ".join(merged[-1])
            group_text = " ".join(group)

            if len(group_text) < self._min_chunk_size and len(current_text) + len(group_text) <= self._max_chunk_size:
                merged[-1].extend(group)
            else:
                merged.append(group)

        return merged
