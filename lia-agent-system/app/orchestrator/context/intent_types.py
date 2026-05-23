"""
Typed intent result for the orchestrator pipeline.

Separate from app/domains/base.IntentResult (domain-level) -- this
covers the orchestrator's own cascaded routing output which includes
A/B variant, routing source, and entity extraction metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OrchestratorIntentResult:
    """
    Typed output of the cascaded router intent detection pipeline.

    Replaces ad-hoc dict[str, Any] in RouteResult.intent_details.
    Keeps backward compat via to_dict() for callers expecting raw dict.
    """

    intent_id: str
    """Canonical intent identifier, e.g. 'SEARCH_CANDIDATES'."""

    confidence: float
    """Confidence score 0.0-1.0."""

    source: str = "keyword"
    """Detection source: 'keyword' | 'llm' | 'vector' | 'semantic'."""

    extracted_entities: dict[str, Any] = field(default_factory=dict)
    """Entity dict extracted from the message (candidate_id, job_id, etc.)."""

    ab_variant: str | None = None
    """A/B test variant identifier, if active."""

    ab_prompt_hash: str | None = None
    """Hash of the prompt template used in LLM tier."""

    raw_intent: str | None = None
    """Raw string returned by the LLM before normalization."""

    routing_metadata: dict[str, Any] = field(default_factory=dict)
    """Extra metadata from routing tiers (tier name, latency, etc.)."""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for backward-compatible consumers expecting raw dict."""
        return {
            "intent_id": self.intent_id,
            "confidence": self.confidence,
            "source": self.source,
            "extracted_entities": self.extracted_entities,
            "ab_variant": self.ab_variant,
            "ab_prompt_hash": self.ab_prompt_hash,
            "raw_intent": self.raw_intent,
            "routing_metadata": self.routing_metadata,
        }

    def __str__(self) -> str:
        """Backward compat: OrchestratorIntentResult used as str returns intent_id.

        This allows gradual migration — consumers that do `intent in ACTIONABLE_INTENTS`
        or `str(intent)` keep working without changes.
        """
        return self.intent_id

    def __hash__(self) -> int:
        return hash(self.intent_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, OrchestratorIntentResult):
            return self.intent_id == other.intent_id
        if isinstance(other, str):
            return self.intent_id == other
        return NotImplemented

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "OrchestratorIntentResult":
        """Reconstruct from legacy dict for migration paths."""
        return cls(
            intent_id=d.get("intent_id", d.get("raw_intent", "unknown")),
            confidence=float(d.get("confidence", 0.5)),
            source=d.get("source", "keyword"),
            extracted_entities=d.get("extracted_entities", d.get("entities", {})),
            ab_variant=d.get("ab_variant"),
            ab_prompt_hash=d.get("ab_prompt_hash"),
            raw_intent=d.get("raw_intent"),
            routing_metadata=d.get("routing_metadata", {}),
        )
