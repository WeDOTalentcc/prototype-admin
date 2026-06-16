"""
Post-wizard continuity (Task #1211).

Optional, opt-in continuation of a COMPOSITE job-creation request such as
"criar a vaga e publicar no ATS". The inviolable rule stands: the wizard creates
the job ALONE. The "...e publicar" half is captured at wizard bootstrap, parked,
and — only after the wizard reaches "done" — proactively OFFERED by LIA in the
chat. It is executed ONLY on a natural PT-BR confirmation from the recruiter.

Storage reuses the canonical conversation-keyed ``pending_action_store`` (same
store Phase 0 uses) with a dedicated ``intent`` so the two flows never collide:
Phase 0's ``_handle_pending_action`` skips this intent, and the dedicated
orchestrator handler (``_handle_post_wizard_continuation``) runs BEFORE Phase 0.

This module is deliberately thin and side-effect-light (only touches the store
through the injected handle) so its decision logic is unit-testable.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from app.orchestrator.execution.pending_action import (
    PendingActionState,
    pending_action_store,
)
from app.orchestrator.routing.job_creation_disambiguator import JobCreationDetection

__all__ = [
    "CONTINUATION_INTENT",
    "CONTINUATION_TTL_MINUTES",
    "is_continuation",
    "store_continuation",
    "get_continuation",
    "mark_offered",
    "clear_continuation",
    "build_offer_message",
    "dispatch_for",
]

CONTINUATION_INTENT = "post_wizard_continuation"
CONTINUATION_TTL_MINUTES = 60  # wizard can take a while — longer than the 5-min default

# Connected continuation kinds → (domain_id, action_id, recruiter-facing label).
# Only kinds present here are executable today; everything else is offered with
# an explicit "ainda não conectado" message (never faked as done).
_CONTINUATION_DISPATCH: dict[str, tuple[str, str, str]] = {
    "publish_job": ("ats_integration", "sync_job", "publicar a vaga no ATS"),
    "sync_job": ("ats_integration", "sync_job", "sincronizar a vaga com o ATS"),
}


def dispatch_for(kind: str | None) -> tuple[str, str, str] | None:
    """Return ``(domain_id, action_id, label)`` for a connected kind, else None."""
    if not kind:
        return None
    return _CONTINUATION_DISPATCH.get(kind)


def is_continuation(state: PendingActionState | None) -> bool:
    return bool(state and state.intent == CONTINUATION_INTENT)


def store_continuation(
    conversation_id: str,
    company_id: str | None,
    detection: JobCreationDetection,
    original_query: str,
    *,
    store=pending_action_store,
) -> PendingActionState | None:
    """Park a composite continuation at wizard bootstrap.

    Returns the stored state, or ``None`` when there is nothing to continue
    (simple creation without a second clause).
    """
    if not detection.continuation_text:
        return None

    kind = detection.continuation_kind or ""
    dispatch = dispatch_for(detection.continuation_kind)
    domain_id = dispatch[0] if dispatch else ""
    action_id = dispatch[1] if dispatch else ""

    state = PendingActionState(
        pending_id=str(uuid.uuid4()),
        intent=CONTINUATION_INTENT,
        action_id=action_id,
        domain_id=domain_id,
        collected_params={
            "continuation_kind": kind,
            "continuation_text": detection.continuation_text,
            "continuation_connected": bool(detection.continuation_connected),
            "original_query": original_query,
            "job_id": None,
        },
        missing_params=[],
        conversation_id=conversation_id,
        company_id=company_id,
        awaiting_confirmation=False,  # not offered until the wizard is done
        expires_at=datetime.utcnow() + timedelta(minutes=CONTINUATION_TTL_MINUTES),
    )
    store.save(conversation_id, state)
    return state


def get_continuation(
    conversation_id: str, *, store=pending_action_store
) -> PendingActionState | None:
    state = store.get(conversation_id)
    return state if is_continuation(state) else None


def mark_offered(
    conversation_id: str,
    job_id: str | None,
    *,
    store=pending_action_store,
) -> PendingActionState | None:
    """Flip a parked continuation to ``awaiting_confirmation`` once the wizard is
    done, binding the freshly-created ``job_id``. Returns the updated state."""
    state = get_continuation(conversation_id, store=store)
    if state is None:
        return None
    if job_id:
        state.collected_params["job_id"] = str(job_id)
    state.awaiting_confirmation = True
    state.expires_at = datetime.utcnow() + timedelta(minutes=CONTINUATION_TTL_MINUTES)
    store.save(conversation_id, state)
    return state


def clear_continuation(conversation_id: str, *, store=pending_action_store) -> None:
    store.remove(conversation_id)


def build_offer_message(state: PendingActionState) -> str:
    """Proactive LIA chat message offering to run the continuation.

    Conversational, no buttons — the recruiter just replies naturally
    (aligns with the chat-as-primary-interface preference).
    """
    params = state.collected_params or {}
    connected = bool(params.get("continuation_connected"))
    dispatch = dispatch_for(params.get("continuation_kind"))
    raw_text = params.get("continuation_text") or "a etapa seguinte"

    if connected and dispatch:
        label = dispatch[2]
        return (
            f"\n\n✅ A vaga foi criada. Você também tinha pedido para **{raw_text}**. "
            f"Quer que eu {label} agora? (é só dizer *sim* ou *agora não*)"
        )
    # Not-yet-connected continuation: be explicit, never pretend it ran.
    return (
        f"\n\n✅ A vaga foi criada. Você também mencionou **{raw_text}**, mas essa "
        f"etapa ainda não está conectada para execução automática — você pode fazê-la "
        f"manualmente por enquanto. Posso ajudar em mais alguma coisa?"
    )
