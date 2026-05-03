"""Real-time hallucination detection for LLM streaming responses (UC-P3-03).

Checks each streaming chunk as it arrives for potential hallucinations.
Lightweight enough to run inline (target < 5ms per chunk).

Complements the post-hoc FactChecker in:
  - app/shared/evaluation/fact_checker.py  (deep analysis, async)
  - app/shared/compliance/fact_checker.py  (compliance-focused validation)

This module handles the streaming / real-time path only.

TODO(ml-team, ISSUE-P3-03, 2026-09-01): Replace heuristics with
  lightweight ML model (logistic regression on token perplexity + NLI).
"""
from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Heuristic signal patterns
# ---------------------------------------------------------------------------
# Red flags that suggest potential hallucination in LLM output.
# Ordered by signal strength (strongest first).

_HALLUCINATION_SIGNALS: list[tuple[str, str]] = [
    # Absolute certainty language combined with factual claims
    (r"\b(?:certainly|definitely|always|never|100%)\b.*\b(?:is|are|was|were)\b", "absolute_certainty"),
    # Universal quantifiers about candidates
    (r"\b(?:all|every|none|no one|everyone)\b.*\bcandidate", "universal_quantifier_candidate"),
    # Explicit confidence assertions (often precede hallucinations)
    (r"\bwith (?:full |absolute )?confidence\b", "explicit_confidence_claim"),
    # First-person guarantees
    (r"\bI (?:know|guarantee|promise|assure|confirm)\b", "first_person_guarantee"),
    # Invented statistics without hedging
    (r"\b\d{1,3}(?:\.\d+)?%\b.{0,30}\b(?:candidates?|applications?|profiles?)\b", "unhedged_statistic"),
]

_COMPILED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(pattern, re.IGNORECASE), label)
    for pattern, label in _HALLUCINATION_SIGNALS
]


async def check_chunk_for_hallucination(chunk: str, context: str = "") -> dict:
    """Check a streaming chunk for hallucination signals.

    Designed to be awaitable (for consistent interface with future ML model).
    Currently synchronous under the hood — no I/O.

    Args:
        chunk: The streaming text chunk to evaluate.
        context: Optional upstream context (reserved for future NLI check).

    Returns:
        {
            "is_suspicious": bool,
            "signals": list[str],          # human-readable signal labels
            "confidence": float,            # 0.0–1.0
            "chunk_length": int,
        }
    """
    signals: list[str] = []
    for pattern, label in _COMPILED_PATTERNS:
        if pattern.search(chunk):
            signals.append(label)

    is_suspicious = len(signals) > 0
    confidence = min(len(signals) * 0.25, 1.0)

    if is_suspicious:
        logger.debug(
            "[RealtimeFactCheck] Suspicious chunk detected: signals=%s chunk_preview=%.60r",
            signals,
            chunk,
        )

    return {
        "is_suspicious": is_suspicious,
        "signals": signals,
        "confidence": confidence,
        "chunk_length": len(chunk),
    }
