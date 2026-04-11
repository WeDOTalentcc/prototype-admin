"""Base classes and types for chunking strategies."""

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class DocumentType(str, enum.Enum):
    CV = "cv"
    JOB_DESCRIPTION = "job_description"
    POLICY = "policy"
    GENERIC = "generic"


@dataclass
class Chunk:
    text: str
    index: int
    metadata: dict = field(default_factory=dict)


class ChunkingStrategy(ABC):
    """Abstract base for all chunking strategies."""

    @abstractmethod
    def chunk(self, text: str, **kwargs) -> list[Chunk]:
        ...

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        ...
