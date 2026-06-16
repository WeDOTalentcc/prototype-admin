"""
StudioVoicePlugin — Sprint 3.6 W4-1 V2 (audit 2026-05-22).

Canonical plugin allowing custom agents from the Agent Studio to operate on
the voice channel. Mirrors the agent's chat behavior (system_prompt +
allowed_tools + persona) for voice sessions.

Differs from `WSIVoicePlugin` (scripted WSI questions) by allowing open-ended
conversation: `get_next_question` returns ``initial_greeting`` only on the
first turn; subsequent turns defer to the core orchestrator's LLM path (which
in turn reads ``session.job_context``/persona injection upstream).

Hooks
─────
- on_session_initiated:
    1. Mark `session.metadata["studio_agent_id"]` for downstream telemetry.
    2. Emit canonical AuditService.log_decision row tagged with this plugin.
- get_next_question:
    1. First turn → return ``agent_config["initial_greeting"]`` if configured.
       Falls back to a generic greeting derived from agent description.
    2. Subsequent turns → ``None`` (core LLM owns the conversation).
- on_session_finalized:
    1. Generate post-call summary via canonical ``llm_service`` (best-effort).
    2. Record billing/execution via canonical
       ``AgentMarketplaceService.record_execution`` + ``compute_voice_credits``.
    3. Emit canonical AuditService completion row.
    4. Return a result dict with ``strategy="studio_custom_agent"`` so the
       core can include it in the orchestrator output.

Multi-tenancy
─────────────
``company_id`` is captured at plugin construction (mirrors the
CustomAgentRuntime cached company). Plugin NEVER trusts external input for
tenant identity. All audit / billing calls pass canonical ``company_id``.

Best-effort guarantees
──────────────────────
Every hook catches Exception broadly and logs via ``logger.warning`` —
plugin failure MUST NOT break the voice call. Audit + billing failures are
non-blocking by design (voice is fire-and-forget critical path).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from app.domains.voice.protocols.voice_core_plugin import VoiceCorePlugin

if TYPE_CHECKING:
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningSession,
    )

logger = logging.getLogger(__name__)


class StudioVoicePlugin(VoiceCorePlugin):
    """Canonical voice plugin for Agent Studio custom agents (Sprint 3.6)."""

    def __init__(
        self,
        *,
        agent_id: str | UUID,
        agent_config: dict[str, Any] | None,
        company_id: str,
    ) -> None:
        """
        Args:
            agent_id: UUID (or str) of the Agent Studio custom agent.
            agent_config: dict with optional keys:
                - system_prompt: str — canonical agent persona (already used
                  by chat path; voice path reuses the same string).
                - allowed_tools: list[str] — whitelist of tool names.
                - initial_greeting: str | None — first-turn greeting override.
                - persona: dict | None — per-tenant persona overrides
                  (forwarded for telemetry; injection is core-owned).
                - description: str | None — short agent description for
                  greeting fallback.
                - pricing_tier: str — billing tier override (default "pro").
            company_id: tenant identifier (REQUIRED for audit + billing).
        """
        self.agent_id = str(agent_id)
        self.config: dict[str, Any] = dict(agent_config or {})
        self.company_id = company_id

    @property
    def plugin_name(self) -> str:
        return "studio_custom_agent"

    # ── VoiceCorePlugin protocol implementations ───────────────────────────

    async def on_session_initiated(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> None:
        """Tag session with the agent_id + emit canonical audit row."""
        # 1) Annotate session for telemetry/observability. VoiceScreeningSession
        #    is a dataclass without `metadata` field by default — attach
        #    defensively via setattr so we never break existing serialization.
        try:
            current_metadata = getattr(session, "metadata", None)
            if not isinstance(current_metadata, dict):
                current_metadata = {}
            current_metadata["studio_agent_id"] = self.agent_id
            current_metadata["plugin_name"] = self.plugin_name
            try:
                session.metadata = current_metadata  # type: ignore[attr-defined]
            except Exception:
                pass  # dataclass may be frozen in some test paths
        except Exception as e:
            logger.warning(
                "[StudioVoicePlugin] failed to annotate session metadata: %s", e
            )

        # 2) Canonical audit (best-effort; never block voice call).
        try:
            from app.shared.compliance.audit_service import AuditService

            allowed_tools = self.config.get("allowed_tools") or []
            await AuditService().log_decision(
                company_id=self.company_id,
                agent_name=f"studio_voice_plugin:{self.agent_id}",
                decision_type="voice_session_initiated",
                action="voice_session_initiated",
                decision="started",
                reasoning=[
                    f"agent_id={self.agent_id}",
                    f"session_id={session.session_id}",
                    f"allowed_tools_count={len(allowed_tools)}",
                    f"voice_provider={getattr(session, 'voice_provider', 'unknown')}",
                ],
                criteria_used=[
                    "agent_config_loaded",
                    "tenant_isolation",
                    "plugin=studio_custom_agent",
                ],
                criteria_ignored=[],
                candidate_id=getattr(session, "candidate_id", None),
                job_vacancy_id=getattr(session, "job_id", None),
                human_review_required=False,
            )
        except Exception as e:
            logger.warning(
                "[StudioVoicePlugin] audit log on_session_initiated failed "
                "(non-blocking) session=%s: %s",
                getattr(session, "session_id", "<unknown>"),
                e,
            )

    async def get_next_question(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> str | None:
        """First turn → initial_greeting; otherwise None (core LLM decides)."""
        try:
            transcript = getattr(session, "transcript_segments", None) or []
            if transcript:
                # Subsequent turns: defer to core LLM path. The agent's
                # system_prompt is injected at the orchestrator level via
                # SystemPromptBuilder (Sprint 3.5+); plugin contributes nothing.
                return None

            greeting = self.config.get("initial_greeting")
            if isinstance(greeting, str) and greeting.strip():
                return greeting.strip()

            description = self.config.get("description") or "esta vaga"
            return (
                f"Olá! Sou a LIA e vou te ajudar com {description}. "
                "Pode se apresentar?"
            )
        except Exception as e:
            logger.warning(
                "[StudioVoicePlugin] get_next_question failed (non-blocking) "
                "session=%s: %s",
                getattr(session, "session_id", "<unknown>"),
                e,
            )
            return None

    async def on_session_finalized(
        self,
        session: "VoiceScreeningSession",
        db: Any,
        transcript: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate summary + record canonical billing + audit completion."""
        summary = await self._generate_summary(session, transcript)

        # Compute canonical credits from session duration.
        duration_seconds = self._duration_seconds(session)
        credits_consumed = 0
        try:
            from app.services.agent_pricing import compute_voice_credits

            credits_consumed = compute_voice_credits(
                total_audio_seconds=duration_seconds,
                # P1 ticket #1 (2026-05-23): canonical Gemini LLM tokens.
                # Antes hardcoded default 0 — agora le do session canonical.
                tokens_input=int(getattr(session, "llm_tokens_input", 0) or 0),
                tokens_output=int(getattr(session, "llm_tokens_output", 0) or 0),
                tier=self.config.get("pricing_tier", "pro"),
            )
        except Exception as e:
            logger.warning(
                "[StudioVoicePlugin] compute_voice_credits failed "
                "(non-blocking) session=%s: %s",
                getattr(session, "session_id", "<unknown>"),
                e,
            )

        # Record execution via canonical marketplace service.
        try:
            from app.services.agent_marketplace_service import (
                agent_marketplace_service,
            )

            if db is not None:
                await agent_marketplace_service.record_execution(
                    db=db,
                    agent_id=self.agent_id,
                    company_id=self.company_id,
                    credits_consumed=credits_consumed,
                    pricing_tier=self.config.get("pricing_tier", "pro"),
                )
        except Exception as e:
            logger.warning(
                "[StudioVoicePlugin] record_execution failed (non-blocking) "
                "session=%s: %s",
                getattr(session, "session_id", "<unknown>"),
                e,
            )

        # Canonical audit row for completion.
        try:
            from app.shared.compliance.audit_service import AuditService

            await AuditService().log_decision(
                company_id=self.company_id,
                agent_name=f"studio_voice_plugin:{self.agent_id}",
                decision_type="voice_session_finalized",
                action="voice_session_finalized",
                decision="completed",
                reasoning=[
                    f"agent_id={self.agent_id}",
                    f"session_id={session.session_id}",
                    f"transcript_turns={len(transcript)}",
                    f"summary_len={len(summary)}",
                    f"credits_consumed={credits_consumed}",
                    f"duration_seconds={duration_seconds}",
                ],
                criteria_used=[
                    "agent_canonical_completion",
                    "plugin=studio_custom_agent",
                ],
                criteria_ignored=[],
                candidate_id=getattr(session, "candidate_id", None),
                job_vacancy_id=getattr(session, "job_id", None),
                human_review_required=False,
            )
        except Exception as e:
            logger.warning(
                "[StudioVoicePlugin] audit log on_session_finalized failed "
                "(non-blocking) session=%s: %s",
                getattr(session, "session_id", "<unknown>"),
                e,
            )

        return {
            "strategy": "studio_custom_agent",
            "agent_id": self.agent_id,
            "summary": summary,
            "transcript_turns": len(transcript),
            "duration_seconds": duration_seconds,
            "credits_consumed": credits_consumed,
        }

    # ── Internal helpers ───────────────────────────────────────────────────

    async def _generate_summary(
        self,
        session: "VoiceScreeningSession",
        transcript: list[dict[str, Any]],
    ) -> str:
        """
        Best-effort post-call summary via canonical ``llm_service``.

        Returns empty string on failure — finalization MUST NOT block on the
        summary path (audit + billing run regardless).
        """
        if not transcript:
            return ""
        try:
            from app.domains.ai.services.llm import llm_service

            transcript_text = "\n".join(
                f"{turn.get('role', 'unknown')}: {turn.get('text', '')}"
                for turn in transcript
                if isinstance(turn, dict)
            )
            agent_description = self.config.get("description") or "entrevista"
            prompt = (
                "Resuma esta entrevista por voz em ate 5 bullets concisos "
                "(PT-BR). Foque em: experiencia relevante, motivacoes, red "
                "flags se houver, recomendacao final.\n\n"
                f"Contexto do agente: {agent_description}\n\n"
                f"Transcript:\n{transcript_text[:5000]}\n\n"
                "Resumo (5 bullets):"
            )
            text = await llm_service.generate_with_gemini(prompt)
            return (text or "").strip()[:2000]
        except Exception as e:
            logger.warning(
                "[StudioVoicePlugin] summary generation failed (non-blocking) "
                "session=%s: %s",
                getattr(session, "session_id", "<unknown>"),
                e,
            )
            return ""

    @staticmethod
    def _duration_seconds(session: "VoiceScreeningSession") -> int:
        """Compute duration in seconds from started_at/ended_at, or 0."""
        try:
            started = getattr(session, "started_at", None)
            ended = getattr(session, "ended_at", None)
            if started and ended:
                delta = (ended - started).total_seconds()
                return max(0, int(delta))
        except Exception:
            pass
        return 0
