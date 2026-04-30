"""
WizardSessionService — Sprint A.1 — Bug 6 (state persistence across WS turns).

harness-engineering guide computacional:
Encapsulates JobCreationGraph session lifecycle so conversation_messages
accumulate across WebSocket turns instead of being reset on every message.
Mirrors the `rail_a_hint_override.py` single-responsibility pattern.

Multi-tenant: workspace_id (= company_id as int) validated in every call.
LGPD: no PII stored beyond what JobCreationState already carries.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Keys carried forward from context into wizard state
_CONTEXT_CARRY_KEYS = ("right_panel_form", "attached_file_text")

# Stage-aware default responses (avoids empty string responses)
_STAGE_DEFAULTS: dict[str, str] = {
    "intake": "Captei a vaga. Vou seguir para o próximo passo.",
    "jd_enrichment": "Descrição da vaga enriquecida — preciso da sua aprovação.",
    "wsi_questions": "Perguntas de triagem WSI sugeridas — preciso da sua aprovação.",
    "completed": "Vaga criada com sucesso.",
}


class WizardSessionService:
    """Manages JobCreationGraph invocation with per-session state accumulation.

    Fixes Bug 6: conversation_messages are now accumulated across WS turns.
    On Turn N the service pulls the checkpointed state from LangGraph,
    appends the new user message, and re-invokes — so the graph always has
    the full conversation history.

    Responsibilities
    ────────────────
    - derive_thread_id(): stable session → thread_id mapping
    - _get_prior_state(): non-raising checkpointer read
    - _build_state(): merge or fresh-start state builder
    - process_message(): main entry point for agent_chat_ws.py

    NOT responsible for: HITL approval routing (stays in agent_chat_ws.py),
    token streaming setup (caller provides on_token callback).
    """

    # ── Public helpers ────────────────────────────────────────────────────

    @staticmethod
    def derive_thread_id(msg: dict, session_id: str) -> str:
        """Return stable thread_id for this wizard session.

        Priority:
          1. Client-supplied ``msg["thread_id"]`` — wizard panel sends this
             so the checkpointer key matches the frontend's HITL approval key.
          2. ``f"wiz-{session_id}"`` — stable session-scoped fallback.

        NOTE: thread_id must be consistent across ALL turns of the same
        wizard session (including approval_response messages). The frontend
        panel should send the same thread_id it received on the first turn.
        """
        return (msg.get("thread_id") or f"wiz-{session_id}").strip() or f"wiz-{session_id}"

    @staticmethod
    async def _get_prior_state(thread_id: str) -> dict:
        """Read checkpointed wizard state without raising.

        Returns empty dict on any error so callers always get a valid dict.
        Fail-open: a checkpointer miss means start fresh, never crash.

        Harness: computational sensor — reads LangGraph checkpoint directly.
        """
        try:
            from app.domains.job_creation.graph import job_creation_graph as wiz_g
            config = {"configurable": {"thread_id": thread_id}}
            snapshot = await asyncio.to_thread(wiz_g._graph.get_state, config)
            if snapshot is not None and snapshot.values:
                state = dict(snapshot.values)
                logger.debug(
                    "[WizardSession] Prior state loaded thread=%s stage=%s conv_len=%d",
                    thread_id,
                    state.get("current_stage") or "?",
                    len(state.get("conversation_messages") or []),
                )
                return state
        except Exception as exc:
            logger.debug("[WizardSession] Checkpointer read skipped: %s", exc)
        return {}

    @staticmethod
    def _build_state(
        *,
        thread_id: str,
        user_message: str,
        user_id: str | None,
        company_id: str | None,
        session_id: str,
        context: dict | None,
        prior_state: dict,
    ) -> dict:
        """Build the state dict for the next JobCreationGraph invocation.

        Bug 6 fix: when prior_state is non-empty (continuing session),
        appends the new message to conversation_messages and preserves
        all accumulated fields. Avoids the previous behaviour of
        overwriting the full history with a single-element list.

        Multi-tenancy: workspace_id always derived from company_id param,
        never trusted from prior_state (prevents tenant escalation via
        stale checkpoint data).
        """
        # Always compute workspace_id from the authoritative company_id param.
        safe_workspace_id = (
            int(company_id)
            if (company_id and str(company_id).isdigit())
            else (prior_state.get("workspace_id") or 0)
        )

        ctx = context or {}

        if prior_state:
            # ── Continuing session ──────────────────────────────────────
            conv = list(prior_state.get("conversation_messages") or [])
            conv.append({"role": "user", "content": user_message})
            state: dict = {
                **prior_state,
                # Override tenant fields with authoritative values
                "workspace_id": safe_workspace_id,
                "company_id": str(company_id) if company_id else "",
                "user_id": str(user_id) if user_id else prior_state.get("user_id", ""),
                # Update query fields with new message
                "user_query": user_message,
                "raw_input": user_message,
                "conversation_messages": conv,
                # Reset approval flags — this is NOT an approval resume
                "hitl_approved": False,
            }
            # Carry any fresh context overrides
            for k in _CONTEXT_CARRY_KEYS:
                if ctx.get(k):
                    state[k] = ctx[k]
            logger.info(
                "[WizardSession] Continuing session thread=%s stage=%s conv_turns=%d",
                thread_id,
                state.get("current_stage") or "?",
                len(conv),
            )
            return state

        # ── Fresh session ─────────────────────────────────────────────────
        logger.info("[WizardSession] New session thread=%s source=wizard_new", thread_id)
        state = {
            "session_id": session_id,
            "user_id": str(user_id) if user_id else "",
            "workspace_id": safe_workspace_id,
            "company_id": str(company_id) if company_id else "",
            "auth_token": "",
            "language": "pt-BR",
            "current_stage": None,
            "stage_history": [],
            "user_query": user_message,
            "raw_input": user_message,
            "conversation_messages": [
                {"role": "user", "content": user_message},
            ],
        }
        for k in _CONTEXT_CARRY_KEYS:
            if ctx.get(k):
                state[k] = ctx[k]
        return state

    @classmethod
    async def process_message(
        cls,
        *,
        thread_id: str,
        user_message: str,
        user_id: str | None,
        company_id: str | None,
        session_id: str,
        context: dict | None,
        on_token: Any | None = None,
    ) -> tuple[str, dict, int]:
        """Invoke JobCreationGraph for a wizard message (new or continuing).

        Entry point for agent_chat_ws.py wizard path. Replaces the inline
        _invoke_wizard_canonical_streaming logic with the session-aware variant.

        Args:
            thread_id:    Stable session thread_id (from derive_thread_id()).
            user_message: Recruiter's current message.
            user_id:      From JWT (never from payload — multi-tenancy).
            company_id:   From JWT (never from payload — multi-tenancy).
            session_id:   WS session id (used as fallback thread_id key).
            context:      Raw WS context dict (right_panel_form, metadata, …).
            on_token:     Optional async callback ``(chunk: str) → None``.

        Returns:
            ``(recruiter_message, ws_stage_payload, tokens_emitted)``
        """
        from app.domains.job_creation.graph import job_creation_graph as wiz_g

        prior_state = await cls._get_prior_state(thread_id)
        state = cls._build_state(
            thread_id=thread_id,
            user_message=user_message,
            user_id=user_id,
            company_id=company_id,
            session_id=session_id,
            context=context,
            prior_state=prior_state,
        )

        # ── Manager preferences injection (GUIDE — fail-open) ──────────
        # Only on the first message of a session (when manager_email is known)
        # to avoid overwriting state already set by the user in later turns.
        manager_email = state.get("manager_email") or (context or {}).get("manager_email")
        if manager_email and company_id and not state.get("manager_preferences_loaded"):
            try:
                from app.core.database import AsyncSessionLocal
                from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService
                async with AsyncSessionLocal() as _mp_db:
                    prefs = await ManagerPreferencesService.apply_to_state(
                        _mp_db, str(company_id), manager_email, state
                    )
                    if prefs:
                        state.update(prefs)
                        state["company_defaults_applied"] = list(state.get("company_defaults_applied") or []) + ["manager_preferences"]
                        state["manager_preferences_loaded"] = True
                        logger.info("[WizardSession] manager_preferences applied: %s", list(prefs.keys()))
            except Exception as mp_exc:
                logger.warning("[WizardSession] manager_preferences injection failed (fail-open): %s", mp_exc)

        tokens_emitted = 0
        if hasattr(wiz_g, "stream_invoke"):
            result, tokens_emitted = await wiz_g.stream_invoke(
                state, thread_id, on_token=on_token,
            )
        else:  # pragma: no cover — defensive: older deploy without stream_invoke
            result = await asyncio.to_thread(wiz_g.invoke, state, thread_id)

        if not isinstance(result, dict):
            return ("Vaga em criação — vamos seguir.", {}, tokens_emitted)

        # ── Learning loop: record manager preferences on handoff ──────
        # Called here (async context) instead of inside handoff_node (sync).
        # Idempotency key: prevents double-counting on WS reconnect.
        if (
            result.get("current_stage") == "handoff"
            and result.get("manager_email")
            and company_id
        ):
            import hashlib, datetime as _dt
            _ikey = hashlib.md5(
                f"{company_id}:{result['manager_email']}:{result.get('job_id') or thread_id}:{_dt.date.today().isoformat()}".encode()
            ).hexdigest()
            try:
                from app.core.database import AsyncSessionLocal
                from app.domains.job_creation.services.manager_preferences_service import ManagerPreferencesService
                async with AsyncSessionLocal() as _rl_db:
                    await ManagerPreferencesService.record_job_completion(
                        _rl_db,
                        company_id=str(company_id),
                        manager_email=result["manager_email"],
                        final_state=result,
                        initial_state=prior_state or None,
                        idempotency_key=_ikey,
                    )
                    logger.info("[WizardSession] manager_preferences recorded for %s", result["manager_email"])
            except Exception as _rl_exc:
                logger.warning("[WizardSession] record_job_completion failed (fail-open): %s", _rl_exc)


        stage_payload = result.get("ws_stage_payload") or {}
        stage_data = stage_payload.get("data") or {}
        current_stage = result.get("current_stage", "") or ""
        message = (
            stage_data.get("message")
            or stage_data.get("response_text")
            or _STAGE_DEFAULTS.get(current_stage, f"Etapa atual: {current_stage or 'wizard'}.")
        )
        return (message, stage_payload, tokens_emitted)
