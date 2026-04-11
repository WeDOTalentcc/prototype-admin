"""Recursive text splitter — splits by semantic boundaries (paragraphs, sentences, words)."""

import re

from app.shared.intelligence.chunking.base import Chunk, ChunkingStrategy

_SEPARATORS = [
    "\n\n",
    "\n",
    ". ",
    "? ",
    "! ",
    "; ",
    ", ",
    " ",
    "",
]


class RecursiveTextSplitter(ChunkingStrategy):
    """Recursively splits text using a hierarchy of separators.

    Tries the largest semantic boundary first (double newline / paragraph),
    then falls back to smaller boundaries (sentence, clause, word, char)
    until each chunk fits within ``chunk_size``.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        separators: list[str] | None = None,
    ):
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be non-negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(f"chunk_overlap ({chunk_overlap}) must be < chunk_size ({chunk_size})")

        self._chunk_size = chunk_size
        self._overlap = chunk_overlap
        self._separators = separators or list(_SEPARATORS)

    @property
    def strategy_name(self) -> str:
        return "recursive"

    def chunk(self, text: str, **kwargs) -> list[Chunk]:
        if not text:
            return []
        raw = self._split_text(text, self._separators)
        chunks: list[Chunk] = []
        for idx, piece in enumerate(raw):
            chunks.append(Chunk(
                text=piece,
                index=idx,
                metadata={"strategy": "recursive"},
            ))
        return chunks

    def _split_text(self, text: str, separators: list[str]) -> list[str]:
        if len(text) <= self._chunk_size:
            return [text] if text.strip() else []

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:] if len(separators) > 1 else []

        if sep == "":
            splits = list(text)
        else:
            splits = text.split(sep)

        good_splits: list[str] = []
        current: list[str] = []
        current_len = 0

        for piece in splits:
            piece_len = len(piece) + (len(sep) if current else 0)

            if current_len + piece_len > self._chunk_size and current:
                merged = self._join(current, sep)
                if len(merged) > self._chunk_size and remaining_seps:
                    good_splits.extend(self._split_text(merged, remaining_seps))
                elif merged.strip():
                    good_splits.append(merged)

                overlap_pieces = self._compute_overlap(current, sep)
                current = overlap_pieces
                current_len = sum(len(p) for p in current) + len(sep) * max(len(current) - 1, 0)

                current.append(piece)
                current_len += piece_len
            else:
                current.append(piece)
                current_len += piece_len

        if current:
            merged = self._join(current, sep)
            if len(merged) > self._chunk_size and remaining_seps:
                good_splits.extend(self._split_text(merged, remaining_seps))
            elif merged.strip():
                good_splits.append(merged)

        return good_splits

    def _join(self, pieces: list[str], sep: str) -> str:
        return sep.join(pieces)

    def _compute_overlap(self, pieces: list[str], sep: str) -> list[str]:
        if self._overlap <= 0:
            return []
        overlap_parts: list[str] = []
        total = 0
        for piece in reversed(pieces):
            total += len(piece) + len(sep)
            if total > self._overlap:
                break
            overlap_parts.insert(0, piece)
        return overlap_parts
