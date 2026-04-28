"""
Wizard Suggestion Priority — canonical source selector for salary suggestions.

Defines WizardSuggestion dataclass and pick_canonical() function that chooses
the best salary suggestion from history vs. market benchmark sources.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class WizardSuggestion:
    """Represents a salary suggestion from a single data source."""

    source: str                       # e.g. "history" or "market"
    recommended_min: Optional[float]
    recommended_max: Optional[float]
    confidence: str = "low"           # "high" | "medium" | "low"
    sample_size: int = 0
    metadata: dict = field(default_factory=dict)

    @property
    def has_data(self) -> bool:
        return self.recommended_min is not None and self.recommended_min > 0


_CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


def pick_canonical(
    history: Optional[WizardSuggestion] = None,
    market: Optional[WizardSuggestion] = None,
) -> Optional[WizardSuggestion]:
    """
    Select the canonical salary suggestion from available sources.

    Priority rules:
      1. If only one source has data, use it.
      2. History wins over market when confidence is equal (company-specific > generic).
      3. Otherwise pick whichever has higher confidence.
      4. Tie-break: larger sample_size wins.

    Returns None if neither source has data.
    """
    candidates = [s for s in (history, market) if s is not None and s.has_data]

    if not candidates:
        logger.debug("pick_canonical: no candidates with data — returning None")
        return None

    if len(candidates) == 1:
        logger.debug(f"pick_canonical: single candidate from '{candidates[0].source}'")
        return candidates[0]

    hist, mkt = candidates[0], candidates[1]
    # Ensure correct assignment when both exist
    if history and history.has_data and market and market.has_data:
        hist, mkt = history, market

    hist_rank = _CONFIDENCE_RANK.get(hist.confidence, 0)
    mkt_rank = _CONFIDENCE_RANK.get(mkt.confidence, 0)

    if hist_rank >= mkt_rank:
        chosen = hist
    else:
        chosen = mkt

    # Tie-break by sample size
    if hist_rank == mkt_rank and mkt.sample_size > hist.sample_size:
        chosen = mkt

    logger.info(
        f"pick_canonical: chose '{chosen.source}' "
        f"(confidence={chosen.confidence}, sample_size={chosen.sample_size})"
    )
    return chosen
