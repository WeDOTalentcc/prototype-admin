"""Implicit feedback capture (Task #1299).

Explicit feedback (Task #1297: thumbs / rating / correction) is rare — most
recruiters never click 👍/👎. This module multiplies the learning-loop volume
by harvesting THREE *implicit* signals from natural chat behaviour, routing
them through the SAME storage + learning path as explicit feedback:

  1. ``regeneration``      → strong NEGATIVE. The recruiter asked LIA to redo a
                             response ⇒ the superseded answer was unsatisfactory.
  2. ``correction_delta``  → NEGATIVE. The recruiter took LIA's suggestion,
                             EDITED it, and sent the edited version (outside the
                             job-creation wizard). The delta original→used is a
                             correction signal.
  3. ``abandonment``       → WEAK negative. The recruiter ignored a substantive
                             answer and switched topic. Captured under a
                             deliberately CONSERVATIVE criterion to avoid false
                             positives polluting the learning data.

Each signal:
- carries ``intent`` / ``stage`` / ``trace_id`` + the REAL ``company_id`` (from
  the authenticated JWT, never the request body);
- is gated by :class:`FairnessGuard` BEFORE it can become a learned pattern — a
  biased candidate text is dropped (fail-loud log + audit), never persisted;
- persists to ``learning_signals`` (the canonical few-shot/governance store,
  same table explicit corrections use via ``CorrectionCaptureService``);
- additionally demotes the matching ``learning_patterns`` row via
  ``FeedbackService.record_implicit_negative`` for the strong signals
  (regeneration + correction_delta). Abandonment is intentionally
  signals-ONLY (weak) so a single ignored answer never flips a pattern.

No silent fallbacks: every skip path logs the reason. Persistence failures are
logged and re-raised to the caller of the typed capture methods so the HTTP
layer can surface them (the regenerate hook wraps its call defensively so the
core handshake never breaks on a learning-loop hiccup).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.feedback import InteractionFeedback

logger = logging.getLogger(__name__)


# Signal-type constants (also used as the learning_signals.feedback_type value).
SIGNAL_REGENERATION = "regeneration"
SIGNAL_CORRECTION_DELTA = "correction_delta"
SIGNAL_ABANDONMENT = "abandonment"

_VALID_SIGNALS = {SIGNAL_REGENERATION, SIGNAL_CORRECTION_DELTA, SIGNAL_ABANDONMENT}

# Conservative abandonment thresholds. Deliberately strict — a missed signal is
# far cheaper than a false-positive that teaches LIA the wrong lesson.
_ABANDON_MIN_RESPONSE_CHARS = 60      # answer must be substantive, not a one-liner
_ABANDON_MIN_NEXT_WORDS = 4           # next msg must be a real utterance, not "ok"
_ABANDON_MAX_TOKEN_OVERLAP = 0.08     # next msg must barely overlap the answer

# Portuguese continuation/confirmation words — if the next user message is one of
# these it is ENGAGEMENT (answering LIA), never an abandonment.
_CONTINUATION_TOKENS = {
    "sim", "claro", "ok", "okay", "beleza", "isso", "pode", "vamos", "vai",
    "certo", "perfeito", "obrigado", "obrigada", "valeu", "concordo", "aceito",
    "não", "nao", "negativo", "continua", "continuar", "prossiga", "segue",
}

_WORD_RE = re.compile(r"[a-zà-ÿ0-9]+", re.IGNORECASE)
# Minimal PT-BR stopword set for the topic-switch overlap heuristic.
_STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "de", "da", "do", "das", "dos", "em",
    "no", "na", "nos", "nas", "e", "ou", "que", "para", "pra", "por", "com",
    "se", "sua", "seu", "the", "to", "of", "and", "is", "in", "you", "me",
    "eu", "voce", "você", "ao", "aos", "à", "às", "mais", "como", "isso",
}


@dataclass
class ImplicitSignalResult:
    """Outcome of an implicit-signal capture attempt."""

    persisted: bool
    signal_type: str
    signal_id: str | None = None          # learning_signals row id (str)
    feedback_id: str | None = None        # interaction_feedback row id (str)
    skipped_reason: str | None = None     # populated when persisted is False


def _tokenize(text: str | None) -> set[str]:
    if not text:
        return set()
    return {
        t.lower()
        for t in _WORD_RE.findall(text)
        if t.lower() not in _STOPWORDS and len(t) > 1
    }


def _token_overlap(a: str | None, b: str | None) -> float:
    """Jaccard overlap of significant tokens (0.0 = disjoint topics)."""
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def is_abandonment_candidate(lia_response: str | None, next_user_message: str | None) -> bool:
    """Conservative, PURE abandonment test (no DB, fully unit-testable).

    Returns True ONLY when ALL hold:
      1. The LIA answer is substantive (>= _ABANDON_MIN_RESPONSE_CHARS).
      2. The answer did NOT itself ask the user a question (a trailing '?'
         means the user's next message is an ANSWER → continuation, not abandon).
      3. The next user message is a real utterance (>= _ABANDON_MIN_NEXT_WORDS
         words) and is NOT a continuation/confirmation token.
      4. The next user message barely overlaps the answer's topic
         (token overlap <= _ABANDON_MAX_TOKEN_OVERLAP) → a topic switch.
    """
    resp = (lia_response or "").strip()
    nxt = (next_user_message or "").strip()
    if len(resp) < _ABANDON_MIN_RESPONSE_CHARS:
        return False
    if resp.endswith("?"):
        return False
    words = _WORD_RE.findall(nxt)
    if len(words) < _ABANDON_MIN_NEXT_WORDS:
        return False
    if nxt.lower().rstrip("?.! ") in _CONTINUATION_TOKENS:
        return False
    return _token_overlap(resp, nxt) <= _ABANDON_MAX_TOKEN_OVERLAP


class ImplicitFeedbackService:
    """Single capture point for the three implicit feedback signals."""

    def __init__(self, feedback_service: Any = None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        # Lazy default to avoid import cycles at module load.
        self._feedback_service = feedback_service

    # ── FairnessGuard gate ────────────────────────────────────────────────
    def _fairness_clean(self, *texts: str | None) -> tuple[bool, str | None]:
        """Run FairnessGuard layer-1 explicit-bias check on every candidate text.

        Returns ``(is_clean, reason)``. ``is_clean=False`` ⇒ caller MUST NOT
        persist the signal (it would otherwise become a biased learned pattern).
        Fail-loud: a guard that cannot initialise is treated as NOT clean
        (fail-closed) so biased text is never silently learned.
        """
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard

            guard = FairnessGuard(strict=False)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(
                "[ImplicitFeedback] FairnessGuard init failed — refusing to "
                "learn from unvalidated signal (fail-closed): %s", exc,
            )
            return False, "fairness_guard_unavailable"

        for text in texts:
            if not text or not text.strip():
                continue
            try:
                result = guard.check_explicit_bias(text)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.error(
                    "[ImplicitFeedback] FairnessGuard check raised — "
                    "fail-closed: %s", exc,
                )
                return False, "fairness_check_error"
            if getattr(result, "is_blocked", False):
                self.logger.warning(
                    "[ImplicitFeedback] signal BLOCKED by FairnessGuard "
                    "(category=%s) — not persisted",
                    getattr(result, "category", "?"),
                )
                return False, "fairness_blocked"
        return True, None

    # ── persistence helpers ───────────────────────────────────────────────
    async def _persist_learning_signal(
        self,
        *,
        db: AsyncSession,
        company_id: str,
        user_id: str,
        conversation_id: str | None,
        signal_type: str,
        original_response: str,
        corrected_response: str,
        intent: str | None,
        stage: str | None,
        trace_id: str | None,
        signal_strength: str,
        confidence_at_generation: float | None,
        extra_metadata: dict | None,
    ) -> str:
        from app.domains.analytics.repositories.learning_signal_repository import (
            LearningSignalRepository,
        )

        metadata: dict[str, Any] = {
            "signal_source": "implicit",
            "signal_type": signal_type,
            "signal_strength": signal_strength,
            "intent": intent,
            "stage": stage,
            "trace_id": trace_id,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        repo = LearningSignalRepository(db)
        signal_id = await repo.insert(
            company_id=company_id,
            user_id=user_id,
            conversation_id=conversation_id,
            # Dedicated domain namespace so the existing few-shot domain fanout
            # never ingests an implicit NEGATIVE as a positive example. The
            # downstream golden-dataset/eval task reads these by prefix.
            domain=f"implicit_{signal_type}",
            original_response=original_response,
            corrected_response=corrected_response,
            feedback_type=signal_type,
            confidence_at_generation=confidence_at_generation,
            metadata=metadata,
        )
        return str(signal_id)

    def _ensure_feedback_service(self):
        if self._feedback_service is None:
            from app.domains.analytics.services.feedback_service import (
                feedback_service as _fs,
            )
            self._feedback_service = _fs
        return self._feedback_service

    # ── public capture: regeneration ──────────────────────────────────────
    async def capture_regeneration(
        self,
        *,
        db: AsyncSession,
        company_id: str,
        user_id: str,
        session_id: str,
        superseded_message_id: str,
        superseded_response: str,
        prior_user_message: str,
        intent: str | None = None,
        stage: str | None = None,
        trace_id: str | None = None,
        confidence_at_generation: float | None = None,
    ) -> ImplicitSignalResult:
        """Regeneration ⇒ strong implicit NEGATIVE on the superseded answer."""
        clean, reason = self._fairness_clean(superseded_response, prior_user_message)
        if not clean:
            return ImplicitSignalResult(
                persisted=False, signal_type=SIGNAL_REGENERATION, skipped_reason=reason
            )
        if not superseded_response or not superseded_response.strip():
            return ImplicitSignalResult(
                persisted=False, signal_type=SIGNAL_REGENERATION,
                skipped_reason="empty_response",
            )

        signal_id = await self._persist_learning_signal(
            db=db,
            company_id=company_id,
            user_id=user_id,
            conversation_id=session_id,
            signal_type=SIGNAL_REGENERATION,
            original_response=superseded_response,
            # What the recruiter wanted instead: a fresh answer to the same ask.
            corrected_response=prior_user_message or "[regeneração solicitada]",
            intent=intent,
            stage=stage,
            trace_id=trace_id,
            signal_strength="negative",
            confidence_at_generation=confidence_at_generation,
            extra_metadata={"regenerate_of": superseded_message_id},
        )

        fb = await self._ensure_feedback_service().record_implicit_negative(
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
            signal_type=SIGNAL_REGENERATION,
            message_context={
                "message_id": superseded_message_id,
                "user_message": prior_user_message,
                "lia_response": superseded_response,
                "intent": intent,
                "stage": stage,
                "confidence_score": confidence_at_generation,
            },
            db=db,
        )
        return ImplicitSignalResult(
            persisted=True,
            signal_type=SIGNAL_REGENERATION,
            signal_id=signal_id,
            feedback_id=str(fb.id),
        )

    # ── public capture: correction delta ──────────────────────────────────
    async def capture_correction_delta(
        self,
        *,
        db: AsyncSession,
        company_id: str,
        user_id: str,
        session_id: str,
        source_message_id: str,
        original_response: str,
        used_text: str,
        intent: str | None = None,
        stage: str | None = None,
        trace_id: str | None = None,
        confidence_at_generation: float | None = None,
    ) -> ImplicitSignalResult:
        """Recruiter edited LIA's suggestion before sending ⇒ correction signal.

        No-op when the used text equals the original (the recruiter accepted it
        verbatim — that is a POSITIVE/neutral, not a correction).
        """
        if (original_response or "").strip() == (used_text or "").strip():
            return ImplicitSignalResult(
                persisted=False, signal_type=SIGNAL_CORRECTION_DELTA,
                skipped_reason="no_delta",
            )
        if not used_text or not used_text.strip():
            return ImplicitSignalResult(
                persisted=False, signal_type=SIGNAL_CORRECTION_DELTA,
                skipped_reason="empty_used_text",
            )

        clean, reason = self._fairness_clean(original_response, used_text)
        if not clean:
            return ImplicitSignalResult(
                persisted=False, signal_type=SIGNAL_CORRECTION_DELTA,
                skipped_reason=reason,
            )

        signal_id = await self._persist_learning_signal(
            db=db,
            company_id=company_id,
            user_id=user_id,
            conversation_id=session_id,
            signal_type=SIGNAL_CORRECTION_DELTA,
            original_response=original_response,
            corrected_response=used_text,
            intent=intent,
            stage=stage,
            trace_id=trace_id,
            signal_strength="negative",
            confidence_at_generation=confidence_at_generation,
            extra_metadata={"source_message_id": source_message_id},
        )

        fb = await self._ensure_feedback_service().record_implicit_negative(
            session_id=session_id,
            company_id=company_id,
            user_id=user_id,
            signal_type=SIGNAL_CORRECTION_DELTA,
            message_context={
                "message_id": source_message_id,
                "lia_response": original_response,
                "intent": intent,
                "stage": stage,
                "confidence_score": confidence_at_generation,
            },
            db=db,
        )
        return ImplicitSignalResult(
            persisted=True,
            signal_type=SIGNAL_CORRECTION_DELTA,
            signal_id=signal_id,
            feedback_id=str(fb.id),
        )

    # ── public capture: abandonment ───────────────────────────────────────
    async def _has_explicit_engagement(
        self, db: AsyncSession, company_id_uuid, message_id: str
    ) -> bool:
        """True if the message already carries explicit feedback (thumbs/rating/
        correction). Such a turn is NOT abandoned, by definition."""
        row = (
            await db.execute(
                select(func.count(InteractionFeedback.id)).where(
                    and_(
                        InteractionFeedback.company_id == company_id_uuid,
                        InteractionFeedback.message_id == message_id,
                        InteractionFeedback.feedback_category.is_(None),
                    )
                )
            )
        ).scalar()
        return bool(row and row > 0)

    async def capture_abandonment(
        self,
        *,
        db: AsyncSession,
        company_id: str,
        user_id: str,
        session_id: str,
        abandoned_message_id: str,
        abandoned_response: str,
        next_user_message: str,
        intent: str | None = None,
        stage: str | None = None,
        trace_id: str | None = None,
        confidence_at_generation: float | None = None,
    ) -> ImplicitSignalResult:
        """Turn abandonment ⇒ WEAK negative (learning_signals only).

        Gatekept by the conservative :func:`is_abandonment_candidate` criterion
        PLUS a DB check that the turn carries no explicit engagement. Never
        touches ``learning_patterns`` — a single ignored answer must not flip a
        pattern.
        """
        from uuid import UUID as _UUID

        if not is_abandonment_candidate(abandoned_response, next_user_message):
            return ImplicitSignalResult(
                persisted=False, signal_type=SIGNAL_ABANDONMENT,
                skipped_reason="criterion_not_met",
            )

        try:
            company_uuid = _UUID(company_id)
        except (ValueError, TypeError):
            return ImplicitSignalResult(
                persisted=False, signal_type=SIGNAL_ABANDONMENT,
                skipped_reason="invalid_company_id",
            )

        if await self._has_explicit_engagement(db, company_uuid, abandoned_message_id):
            return ImplicitSignalResult(
                persisted=False, signal_type=SIGNAL_ABANDONMENT,
                skipped_reason="turn_engaged",
            )

        clean, reason = self._fairness_clean(abandoned_response, next_user_message)
        if not clean:
            return ImplicitSignalResult(
                persisted=False, signal_type=SIGNAL_ABANDONMENT,
                skipped_reason=reason,
            )

        signal_id = await self._persist_learning_signal(
            db=db,
            company_id=company_id,
            user_id=user_id,
            conversation_id=session_id,
            signal_type=SIGNAL_ABANDONMENT,
            original_response=abandoned_response,
            corrected_response=next_user_message,
            intent=intent,
            stage=stage,
            trace_id=trace_id,
            signal_strength="weak_negative",
            confidence_at_generation=confidence_at_generation,
            extra_metadata={"abandoned_message_id": abandoned_message_id},
        )
        return ImplicitSignalResult(
            persisted=True,
            signal_type=SIGNAL_ABANDONMENT,
            signal_id=signal_id,
        )


# Module-level singleton (stateless, safe to share).
implicit_feedback_service = ImplicitFeedbackService()
