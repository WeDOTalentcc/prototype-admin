"""Sliding window chunking strategy — the original approach."""

from app.shared.intelligence.chunking.base import Chunk, ChunkingStrategy


class SlidingWindowChunker(ChunkingStrategy):
    """Fixed-size overlapping chunks with sentence-boundary snapping."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 100):
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if overlap < 0:
            raise ValueError(f"overlap must be non-negative, got {overlap}")
        if overlap >= chunk_size:
            raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")
        self._chunk_size = chunk_size
        self._overlap = overlap

    @property
    def strategy_name(self) -> str:
        return "sliding_window"

    def chunk(self, text: str, **kwargs) -> list[Chunk]:
        if not text or len(text) <= self._chunk_size:
            return [Chunk(text=text, index=0)] if text else []

        chunks: list[Chunk] = []
        start = 0
        idx = 0

        while start < len(text):
            end = start + self._chunk_size

            if end < len(text):
                last_period = text.rfind(".", start, end)
                last_newline = text.rfind("\n", start, end)
                break_point = max(last_period, last_newline)

                if break_point > start + self._chunk_size // 2:
                    end = break_point + 1

            fragment = text[start:end].strip()
            if fragment:
                chunks.append(Chunk(text=fragment, index=idx, metadata={"strategy": "sliding_window"}))
                idx += 1

            start = end - self._overlap

        return chunks
