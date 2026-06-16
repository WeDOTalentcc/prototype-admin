"""Tests for OrchestratorIntentResult typed dataclass."""
import pytest
from app.orchestrator.context.intent_types import OrchestratorIntentResult


def test_basic_creation():
    r = OrchestratorIntentResult(intent_id="SEARCH_CANDIDATES", confidence=0.9)
    assert r.intent_id == "SEARCH_CANDIDATES"
    assert r.confidence == 0.9
    assert r.source == "keyword"


def test_to_dict():
    r = OrchestratorIntentResult(
        intent_id="SEARCH_CANDIDATES",
        confidence=0.9,
        source="llm",
        extracted_entities={"job_id": "123"},
        ab_variant="v2",
    )
    d = r.to_dict()
    assert d["intent_id"] == "SEARCH_CANDIDATES"
    assert d["confidence"] == 0.9
    assert d["ab_variant"] == "v2"
    assert d["extracted_entities"]["job_id"] == "123"


def test_from_dict_legacy():
    """Backward compat: reconstruct from legacy raw dict."""
    legacy = {"intent_id": "SEARCH_CANDIDATES", "confidence": 0.8, "source": "keyword"}
    r = OrchestratorIntentResult.from_dict(legacy)
    assert r.intent_id == "SEARCH_CANDIDATES"
    assert r.confidence == 0.8


def test_from_dict_missing_fields():
    """Handles dicts with missing fields gracefully."""
    r = OrchestratorIntentResult.from_dict({})
    assert r.intent_id == "unknown"
    assert r.confidence == 0.5
