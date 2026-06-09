"""
DataCollectionVoicePlugin — Fase 2 (acende voice_collection_script).

Canonical VoiceCorePlugin that drives a DataRequest field-collection flow over
an outbound LIA voice call. Sibling of ``WSIVoicePlugin`` (scripted screening)
and ``StudioVoicePlugin`` (open conversation): this plugin asks the candidate
for the PENDING DataRequest fields, one prompt per voice-collectable field, and
extracts/normalizes the spoken answers at finalize time.

This plugin "lights up" the previously-dead ``voice_collection_script.py`` pure
functions (audit 2026-06-06): ``build_collection_script`` turns the pending
fields into an ordered list of ``VoiceFieldPrompt``; ``portal_only_fields``
separates file/photo uploads (NOT voice-collectable → portal fallback);
``normalize_field_value`` validates each spoken answer by ``field_type``.

plugin_name == "data_collection"
────────────────────────────────
Crucially NOT "wsi_screening" — the Fase 0.5 gate in the orchestrator only runs
the WSI finalize/analysis block when a registered plugin reports
``plugin_name == 'wsi_screening'``. "data_collection" therefore correctly does
NOT trigger the WSI scoring path.

Hooks
─────
- on_session_initiated:
    Build the ordered voice-collectable prompt list from ``build_collection_script``
    and store it on the plugin (and mirror onto ``session.metadata`` for
    telemetry). Portal-only fields are separated out (returned to the producer
    at finalize for portal fallback).
- get_next_question:
    Return the next voice-collectable field prompt text (sequential cursor),
    then ``None`` when all collectable fields have been asked (core wraps up).
- on_session_finalized:
    Extract the candidate's answer per asked field from the transcript,
    normalize each via ``normalize_field_value``, and return a structured dict:
        {
          "strategy": "data_collection",
          "collected": {field_name: {"value", "valid", "raw", "error"}},
          "needs_followup": [field_name, ...],   # asked but no answer / invalid
          "portal_fallback_fields": [field_name, ...],
        }
    Fase 4 wires persistence of ``collected`` into the DataRequest. Fase 2 does
    NOT persist and — per CLAUDE.md REGRA 4 (anti-silent-fallback) — NEVER fakes
    a value for a field it could not extract: such fields are listed explicitly
    under ``needs_followup``.

Multi-tenancy / best-effort
───────────────────────────
Mirrors the sibling plugins: every hook catches Exception broadly and logs via
``logger.warning`` — plugin failure MUST NOT break the voice call. The plugin
NEVER trusts external input for tenant identity (``session.company_id`` is
authoritative).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from app.domains.voice.protocols.voice_core_plugin import VoiceCorePlugin

if TYPE_CHECKING:
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceCoreOrchestrator,
        VoiceScreeningSession,
    )

logger = logging.getLogger(__name__)


class DataCollectionVoicePlugin(VoiceCorePlugin):
    """VoiceCorePlugin that collects DataRequest fields over a voice call."""

    def __init__(
        self,
        fields: list[dict[str, Any]] | None = None,
        *,
        completed_names: list[str] | None = None,
        data_request_id: Any | None = None,
        orchestrator: "VoiceCoreOrchestrator | None" = None,
    ) -> None:
        """
        Args:
            fields: pending DataRequest fields — list of dicts with
                {name, label, field_type|type, is_required|required}. Same shape
                ``DataRequest.fields_requested`` persists.
            completed_names: field names already collected (skipped by the
                script builder).
            data_request_id: the DataRequest UUID this call collects for. Fase 4
                uses it to persist collected answers back into the canonical
                DataRequest at finalize. When absent, finalize returns the
                extracted dict WITHOUT persisting (no row to write to).
            orchestrator: optional bound VoiceCoreOrchestrator reference (mirrors
                WSIVoicePlugin). Unused by Fase 2 but kept for parity/future
                shared-helper reuse.
        """
        self._fields: list[dict[str, Any]] = list(fields or [])
        self._completed_names: list[str] = list(completed_names or [])
        self._data_request_id = data_request_id
        self._orchestrator = orchestrator

        # Per-field collection state, populated in on_session_initiated.
        # Ordered list of voice-collectable VoiceFieldPrompt objects.
        self._voice_prompts: list[Any] = []
        # Field names that cannot be collected by voice (file/photo → portal).
        self._portal_only_names: list[str] = []
        # Sequential cursor for get_next_question.
        self._cursor: int = 0
        # Fase 3 (LGPD): the FIRST thing said on the call MUST be a recording /
        # data-collection notice (LGPD Art. 9 — informação ao titular). Flipped
        # to True once the notice has been emitted by get_next_question.
        self._recording_notice_emitted: bool = False

    @property
    def plugin_name(self) -> str:
        return "data_collection"

    # Fase 3 (LGPD Art. 9): mandatory recording / data-collection notice spoken
    # as the FIRST utterance of the call, before any field is requested.
    RECORDING_NOTICE: str = (
        "Olá! Esta ligação será gravada para fins de coleta de dados do seu "
        "processo seletivo. As informações que você fornecer serão usadas "
        "exclusivamente para esse fim, conforme a Lei Geral de Proteção de "
        "Dados. Se você não concordar, pode encerrar a ligação a qualquer "
        "momento. Vamos começar."
    )

    # ── VoiceCorePlugin protocol implementations ───────────────────────────

    async def on_session_initiated(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> None:
        """
        Build the ordered voice-collectable prompt list from the pending fields.

        Stores the collectable prompts (asked in order) on the plugin and
        separates portal-only fields (file/photo → portal fallback). Mirrors the
        result onto ``session.metadata`` for telemetry. Best-effort: never raises.
        """
        try:
            from app.domains.communication.services.voice_collection_script import (
                build_collection_script,
                portal_only_fields,
            )

            script = build_collection_script(self._fields, self._completed_names)
            self._voice_prompts = [p for p in script if p.voice_collectable]
            self._portal_only_names = [p.name for p in portal_only_fields(script)]
            self._cursor = 0

            # Telemetry: annotate session metadata defensively (never break ser.).
            try:
                current_metadata = getattr(session, "metadata", None)
                if not isinstance(current_metadata, dict):
                    current_metadata = {}
                current_metadata["plugin_name"] = self.plugin_name
                current_metadata["data_collection_voice_fields"] = [
                    p.name for p in self._voice_prompts
                ]
                current_metadata["data_collection_portal_fields"] = list(
                    self._portal_only_names
                )
                session.metadata = current_metadata  # type: ignore[attr-defined]
            except Exception:
                pass  # dataclass may be frozen in some test paths

            logger.info(
                "[DataCollectionVoicePlugin] session=%s prepared %d voice field(s), "
                "%d portal-only field(s)",
                getattr(session, "session_id", "<unknown>"),
                len(self._voice_prompts),
                len(self._portal_only_names),
            )
        except Exception as e:
            logger.warning(
                "[DataCollectionVoicePlugin] on_session_initiated failed "
                "(non-blocking) session=%s: %s",
                getattr(session, "session_id", "<unknown>"),
                e,
            )

    async def get_next_question(
        self,
        session: "VoiceScreeningSession",
        db: Any,
    ) -> str | None:
        """
        Return the next voice-collectable field prompt, or None when done.

        Sequential cursor over the collectable prompts built in
        ``on_session_initiated``. Returns ``None`` once every collectable field
        has been asked, letting the core wrap up the call. Best-effort.

        Fase 3 (LGPD): the FIRST call returns the mandatory recording /
        data-collection notice, BEFORE the first field is asked — independent
        of whether any field is collectable.
        """
        try:
            # LGPD recording notice is the very first thing said on the call.
            if not self._recording_notice_emitted:
                self._recording_notice_emitted = True
                return self.RECORDING_NOTICE
            if self._cursor >= len(self._voice_prompts):
                return None
            prompt = self._voice_prompts[self._cursor]
            self._cursor += 1
            return self._format_prompt(prompt)
        except Exception as e:
            logger.warning(
                "[DataCollectionVoicePlugin] get_next_question failed "
                "(non-blocking) session=%s: %s",
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
        """
        Extract + normalize the candidate's answers per asked field.

        Walks the (PII-redacted) transcript pairing each asked field prompt with
        the candidate's following utterance, normalizes via
        ``normalize_field_value``, and returns a structured dict for the
        DataRequest producer (Fase 4 persists; Fase 2 returns only).

        Anti-silent-fallback (CLAUDE.md REGRA 4): a field with no extractable /
        invalid answer is NEVER faked — it is listed under ``needs_followup``.

        Returns ``{}`` on unexpected failure (non-blocking finalize).
        """
        try:
            from app.domains.communication.services.voice_collection_script import (
                normalize_field_value,
            )

            collected: dict[str, dict[str, Any]] = {}
            needs_followup: list[str] = []

            # Candidate utterances in order (role in {candidate, user, human}).
            answers = self._candidate_answers(transcript)

            for idx, prompt in enumerate(self._voice_prompts):
                raw = answers[idx] if idx < len(answers) else None
                if not raw or not str(raw).strip():
                    # No answer captured → explicit follow-up, NOT a faked value.
                    needs_followup.append(prompt.name)
                    continue
                normalized = normalize_field_value(prompt.field_type, str(raw))
                if not normalized.valid:
                    # Invalid spoken answer → follow-up, do not persist a guess.
                    needs_followup.append(prompt.name)
                    collected[prompt.name] = {
                        "value": None,
                        "valid": False,
                        "raw": str(raw),
                        "error": normalized.error,
                        "field_type": prompt.field_type,
                        "sensitive": prompt.sensitive,
                    }
                    continue
                collected[prompt.name] = {
                    "value": normalized.value,
                    "valid": True,
                    "raw": str(raw),
                    "error": None,
                    "field_type": prompt.field_type,
                    "sensitive": prompt.sensitive,
                }

            logger.info(
                "[DataCollectionVoicePlugin] session=%s finalized: %d collected, "
                "%d need follow-up, %d portal-only",
                getattr(session, "session_id", "<unknown>"),
                sum(1 for v in collected.values() if v.get("valid")),
                len(needs_followup),
                len(self._portal_only_names),
            )

            # Fase 4 — persist via the CANONICAL DataRequest producer pattern
            # (mirrors DataRequestWhatsAppService.process_document_response):
            # one DataRequestResponse row per VALID field + append to the
            # DataRequest.fields_completed list. needs_followup fields are NEVER
            # persisted as answered (CLAUDE.md REGRA 4). No new write path.
            persisted = await self._persist_collected_fields(session, db, collected)

            return {
                "strategy": "data_collection",
                "collected": collected,
                "needs_followup": needs_followup,
                "portal_fallback_fields": list(self._portal_only_names),
                "persisted_fields": persisted,
            }
        except Exception as e:
            logger.warning(
                "[DataCollectionVoicePlugin] on_session_finalized failed "
                "(non-blocking) session=%s: %s",
                getattr(session, "session_id", "<unknown>"),
                e,
            )
            return {}

    # ── Internal helpers ───────────────────────────────────────────────────

    @staticmethod
    def _format_prompt(prompt: Any) -> str:
        """
        Build the spoken question for a field prompt.

        Sensitive fields get an explicit read-back hint (the orchestrator/LLM
        performs the actual confirmation turn). Falls back to the field name
        when no label is present.
        """
        label = getattr(prompt, "label", None) or getattr(prompt, "name", "")
        if getattr(prompt, "sensitive", False):
            return (
                f"Preciso confirmar um dado sensível: poderia me informar {label}? "
                "Vou repetir para você confirmar."
            )
        return f"Poderia me informar {label}?"

    @staticmethod
    def _candidate_answers(transcript: list[dict[str, Any]] | None) -> list[str]:
        """
        Extract the candidate's utterances (in order) from the transcript.

        Roles treated as the candidate: candidate / user / human. Assistant/LIA
        turns are ignored. Pairs positionally with the asked prompts.
        """
        candidate_roles = {"candidate", "user", "human"}
        out: list[str] = []
        for turn in transcript or []:
            if not isinstance(turn, dict):
                continue
            role = str(turn.get("role", "")).lower()
            if role in candidate_roles:
                text = turn.get("text") or turn.get("content") or ""
                out.append(str(text))
        return out

    async def _persist_collected_fields(
        self,
        session: "VoiceScreeningSession",
        db: Any,
        collected: dict[str, dict[str, Any]],
    ) -> list[str]:
        """
        Persist VALID collected answers via the CANONICAL DataRequest producer.

        Mirrors ``DataRequestWhatsAppService.process_document_response`` exactly:
        one ``DataRequestResponse`` row per valid field + append to the
        ``DataRequest.fields_completed`` list. NO new write path is created —
        this is the same model + same shape WhatsApp uses.

        Provenance (CLAUDE.md honest-provenance): the ``DataRequestResponse``
        model has no dedicated ``source`` column, so provenance is recorded on
        the ``fields_completed`` entry as ``"source": "voice_collection"`` and
        on ``DataRequest.collection_method = "voice"``.

        Best-effort + anti-silent-fallback: only fields with ``valid=True`` are
        persisted; invalid / missing fields were already routed to
        ``needs_followup`` by the caller and are NEVER written as answered.
        Returns the list of field names actually persisted.
        """
        persisted: list[str] = []
        if db is None or not self._data_request_id:
            return persisted
        try:
            from datetime import datetime as _dt

            from lia_models.data_request import DataFieldType, DataRequest
            from lia_models.data_request import (
                DataRequestResponse as _DataRequestResponseModel,
            )

            data_request = await db.get(DataRequest, self._data_request_id)
            if data_request is None:
                logger.warning(
                    "[DataCollectionVoicePlugin] persist skipped: data request %s "
                    "not found (session=%s)",
                    self._data_request_id,
                    getattr(session, "session_id", "<unknown>"),
                )
                return persisted

            completed_fields = list(data_request.fields_completed or [])
            completed_names = {f.get("name") for f in completed_fields if f.get("name")}

            for field_name, info in collected.items():
                if not info.get("valid"):
                    continue  # needs_followup — never persist a guess (REGRA 4)
                if field_name in completed_names:
                    continue  # already recorded — idempotent
                ft_raw = info.get("field_type") or "text"
                try:
                    field_type = (
                        DataFieldType(str(ft_raw).lower())
                        if not isinstance(ft_raw, DataFieldType)
                        else ft_raw
                    )
                except Exception:
                    field_type = DataFieldType.TEXT

                response_record = _DataRequestResponseModel(
                    data_request_id=self._data_request_id,
                    field_name=field_name,
                    field_type=field_type,
                    value=info.get("value"),
                    is_valid=True,
                    submitted_at=_dt.utcnow(),
                )
                db.add(response_record)

                completed_fields.append(
                    {
                        "name": field_name,
                        "completed_at": _dt.utcnow().isoformat(),
                        "source": "voice_collection",
                    }
                )
                completed_names.add(field_name)
                persisted.append(field_name)

            if persisted:
                data_request.fields_completed = completed_fields
                data_request.collection_method = "voice"
                await db.commit()

            logger.info(
                "[DataCollectionVoicePlugin] session=%s persisted %d field(s) via "
                "canonical DataRequest producer: %s",
                getattr(session, "session_id", "<unknown>"),
                len(persisted),
                persisted,
            )
        except Exception as e:
            logger.warning(
                "[DataCollectionVoicePlugin] _persist_collected_fields failed "
                "(non-blocking) session=%s: %s",
                getattr(session, "session_id", "<unknown>"),
                e,
            )
        return persisted
