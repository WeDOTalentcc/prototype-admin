"""
Embedding Provider Abstraction Layer — Task #134.

Defines the contract for embedding provider implementations.
Allows swapping between Gemini, OpenAI, and future providers
without changing business logic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EmbeddingResult:
    """Standardized result from any embedding provider."""
    vector: list[float]
    provider: str
    model: str
    dimensions: int = field(init=False)

    def __post_init__(self):
        self.dimensions = len(self.vector)


class EmbeddingProviderABC(ABC):
    """Abstract base class for embedding providers.

    Implement this interface to add new embedding providers.
    The EmbeddingProviderFactory will manage provider instances.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'gemini', 'openai')."""
        ...

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default embedding model for this provider."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Output vector dimensions for the default model."""
        ...

    @abstractmethod
    async def embed_text(self, text: str) -> EmbeddingResult:
        """Generate an embedding for a single text string.

        Args:
            text: The text to embed. Empty strings should return a zero vector.

        Returns:
            EmbeddingResult with vector, provider, and model metadata.
        """
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of EmbeddingResult, one per input text, in the same order.
        """
        ...

    def get_dimensions(self) -> int:
        """Return the vector dimensions produced by this provider."""
        return self.dimensions
