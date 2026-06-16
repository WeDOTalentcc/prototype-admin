"""
VoiceCorePlugin protocol — Sprint 3.2 refactor (audit 2026-05-22 W4-1 V2).

Defines the contract for extending VoiceCoreOrchestrator with domain-specific
behavior (WSI screening, generic conversation, custom agents) WITHOUT
polluting the core orchestrator with vertical-specific imports/logic.

Design intent
─────────────
The legacy `VoiceScreeningOrchestrator` (2.5k LoC) mixed four responsibilities:
1. Voice transport core (Twilio, Gemini Live, audio pipeline)
2. WSI-specific screening logic (question generation, scoring)
3. Session persistence (Redis + DB)
4. Audit / billing / compliance

Sprint 3.2 extracts (1)+(3)+(4) into `VoiceCoreOrchestrator` (generic) and pushes
(2) behind this protocol so multiple domain plugins can coexist:

    core = VoiceCoreOrchestrator(plugins=[WSIVoicePlugin()])     # backward-compat default
    core = VoiceCoreOrchestrator(plugins=[CustomAgentPlugin()])  # future: agent studio
    core = VoiceCoreOrchestrator(plugins=[])                     # bare voice (no domain)

Hooks
─────
- on_session_initiated(session, db): runs after initiate_call/voip succeed.
  Plugin can register domain state (e.g., WSI session row, BigFive profile).
- get_next_question(session, db): plugin-provided next question text. Return
  None to fall through to scripted core fallback (SCREENING_QUESTIONS_PT).
- on_session_finalized(session, db, transcript): runs in finalize_screening.
  Returns dict (e.g., WSI score, custom agent verdict) merged into result.

Multi-plugin semantics
──────────────────────
Plugins run in registration order. `get_next_question` returns FIRST non-None
result (priority by order). `on_session_initiated`/`on_session_finalized` run
all plugins (best-effort, errors logged but non-blocking — voice call MUST NOT
break because plugin failed).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domains.voice.services.voice_core_orchestrator import VoiceScreeningSession


class VoiceCorePlugin(ABC):
    """
    Abstract base class for VoiceCoreOrchestrator extensions.

    Subclasses provide domain-specific hooks invoked at canonical lifecycle
    points (post-initiate, mid-conversation, finalize).

    Implementations MUST be best-effort:
    - Never raise unhandled exceptions (catch + log, return None/empty dict).
    - Never block the voice call on plugin failure.
    - Multi-tenancy: respect session.company_id; never trust external input.
    """

    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Stable identifier for telemetry/audit (e.g., 'wsi_screening')."""
        ...

    @abstractmethod
    async def on_session_initiated(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> None:
        """
        Called after `initiate_call` / `initiate_voip_session` succeeds and the
        session has a `call_sid` (Twilio) or live session id (Gemini).

        Plugin can register domain-specific state (DB rows, cache entries,
        external API calls). Errors MUST be caught internally — never propagate.

        Args:
            session: Active VoiceScreeningSession with session_id, candidate_id,
                     job_id, company_id, call_sid populated.
            db: SQLAlchemy AsyncSession or None.
        """
        ...

    @abstractmethod
    async def get_next_question(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> str | None:
        """
        Return the next domain-specific question text, or None to defer to the
        next plugin (or the core's scripted fallback).

        Plugins SHOULD return None if they cannot provide a question (e.g., WSI
        questions table empty), allowing the core to fall back to
        SCREENING_QUESTIONS_PT.
        """
        ...

    @abstractmethod
    async def on_session_finalized(
        self,
        session: "VoiceScreeningSession",
        db: Any,
        transcript: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Called by `finalize_screening` after the call ends.

        Plugin runs its domain-specific completion logic (scoring, analysis)
        and returns a dict merged into the orchestrator result. Empty dict
        means "no domain output" (core proceeds with generic finalization).

        Args:
            session: Finalized VoiceScreeningSession (status=analyzing).
            db: SQLAlchemy AsyncSession or None.
            transcript: Masked transcript segments (already PII-redacted).

        Returns:
            Dict with domain-specific result (e.g., {"wsi_result": {...},
            "wsi_strategy": "primary"}). Errors return {} (non-blocking).
        """
        ...
