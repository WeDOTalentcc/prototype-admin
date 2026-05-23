"""Learning Loop for continuous AI improvement (UC-P3-05).

This module provides the UC-P3-05 stub: captures explicit user corrections
and uncertain-response flags as training signals, and decides when the AI
should ask for clarification before responding.

Relationship to existing services
----------------------------------
- learning_loop_service.py   → pattern mining from implicit acceptance/rejection
- template_learning_service.py → JD template learning from edits
- THIS MODULE                → explicit correction capture + clarification gating

Active learning loop (full implementation roadmap):
1. Uncertainty sampling: surface low-confidence responses for human review
2. Correction capture: structured form when user corrects AI
3. Few-shot evolution: feed corrections into FewShotEvolutionService
4. Model feedback: batch corrections → fine-tuning dataset

TODO(ml-team, ISSUE-P3-05, 2026-10-01): Persist LearningSignal via
  LearningSignalRepository and route to FewShotEvolutionService when
  correction_count > threshold for an intent.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class LearningSignal:
    """A single training signal from user feedback.

    Multi-tenancy: company_id is mandatory — signals are always scoped to a tenant.
    """

    company_id: str
    user_id: str
    conversation_id: str
    original_response: str
    corrected_response: str
    # "correction" | "thumbs_down" | "explicit_correction"
    feedback_type: str
    confidence_at_generation: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class CorrectionCaptureService:
    """Captures learning signals and gates clarification requests.

    Designed to be instantiated once per app lifetime (singleton via DI).
    """

    async def record_correction(self, signal: LearningSignal) -> None:
        """Record a user correction as a learning signal.

        W3-021 (2026-05-23): Persiste via LearningSignalRepository (canonical
        infra criada por migration 184). FewShotEvolutionService consome via
        `list_unconsumed_by_domain()` no daily job.

        Fail-open: erros de persist são logged mas NÃO raise (fire-and-forget).
        Caller (Onda UI/chat handler) não deve quebrar por falha de logging.
        """
        # W3-021: persistência canonical
        try:
            from app.core.database import AsyncSessionLocal
            from app.domains.analytics.repositories.learning_signal_repository import (
                LearningSignalRepository,
            )

            async with AsyncSessionLocal() as session:
                repo = LearningSignalRepository(session)
                await repo.insert(
                    company_id=signal.company_id,
                    user_id=signal.user_id,
                    conversation_id=signal.conversation_id,
                    domain=signal.metadata.get("domain") if signal.metadata else None,
                    original_response=signal.original_response,
                    corrected_response=signal.corrected_response,
                    feedback_type=signal.feedback_type,
                    confidence_at_generation=signal.confidence_at_generation,
                    metadata=signal.metadata or {},
                )
        except Exception as e:
            # Fail-open: log mas não raise
            logger.error(
                "[LearningLoop] Failed to persist correction (signal logged but not stored): %s",
                e,
                exc_info=True,
            )

        logger.info(
            "[LearningLoop] Correction recorded: company=%s user=%s type=%s confidence=%.2f",
            signal.company_id,
            signal.user_id,
            signal.feedback_type,
            signal.confidence_at_generation,
        )

    async def should_ask_for_clarification(
        self,
        confidence: float,
        message: str,
        threshold: float = 0.6,
    ) -> bool:
        """Return True if the AI should ask for clarification before responding.

        Two independent triggers:
        1. Low generation confidence (below threshold).
        2. Ambiguous short message with no named entities.

        Args:
            confidence: The LLM's self-reported confidence (0.0–1.0).
            message: The user's original message.
            threshold: Below this confidence, always ask for clarification.

        Returns:
            True → the caller should request clarification from the user.
        """
        if confidence < threshold:
            return True

        # Ambiguity heuristic: very short message with no proper nouns
        words = message.split()
        if len(words) < 5 and not any(w[0].isupper() for w in words if w):
            return True

        return False
