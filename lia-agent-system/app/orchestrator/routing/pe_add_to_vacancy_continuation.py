"""
Post-score "add approved to vacancy" continuation (Task #1227).

The Plan & Execute pattern ``buscar_pontuar_e_adicionar`` runs two steps —
search + score — and then STOPS. Actually adding the approved candidates to the
vacancy is a state-changing action, so it is gated behind a natural PT-BR
confirmation from the recruiter (chat-as-primary-interface preference): LIA
posts the ranking and OFFERS to add the approved ones; only a "sim/pode/vamos"
reply dispatches ``cv_screening.add_approved_to_vacancy``.

This mirrors ``post_wizard_continuation``: it reuses the canonical
conversation-keyed ``pending_action_store`` with a dedicated ``intent`` so the
two flows never collide. Phase 0's ``_handle_pending_action`` skips this intent,
and a dedicated orchestrator handler runs BEFORE Phase 0.

Deliberately thin / side-effect-light (only touches the injected store handle)
so the decision logic stays unit-testable.

INVIOLÁVEL (#1211): this never creates a job — it only adds already-existing
candidates to an already-existing vacancy.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from app.orchestrator.execution.pending_action import (
    PendingActionState,
    pending_action_store,
)

__all__ = [
    "ADD_CONTINUATION_INTENT",
    "ADD_CONTINUATION_TTL_MINUTES",
    "is_add_continuation",
    "store_add_offer",
    "get_add_continuation",
    "clear_add_continuation",
    "build_add_offer_message",
]

ADD_CONTINUATION_INTENT = "pe_add_to_vacancy"
ADD_CONTINUATION_TTL_MINUTES = 30


def is_add_continuation(state: PendingActionState | None) -> bool:
    return bool(state and state.intent == ADD_CONTINUATION_INTENT)


def store_add_offer(
    conversation_id: str,
    company_id: str | None,
    job_id: str | None,
    approved_candidate_ids: list[str] | None,
    *,
    store=pending_action_store,
) -> PendingActionState | None:
    """Park the "add approved to vacancy" offer after scoring.

    Returns the stored state, or ``None`` when there is nothing to offer (no
    vacancy or no approved candidates) — honest, never a fake pending.
    """
    ids = [str(c) for c in (approved_candidate_ids or []) if c]
    if not job_id or not ids:
        return None

    state = PendingActionState(
        pending_id=str(uuid.uuid4()),
        intent=ADD_CONTINUATION_INTENT,
        action_id="add_approved_to_vacancy",
        domain_id="cv_screening",
        collected_params={
            "job_id": str(job_id),
            "approved_candidate_ids": ids,
        },
        missing_params=[],
        conversation_id=conversation_id,
        company_id=company_id,
        awaiting_confirmation=True,
        expires_at=datetime.utcnow() + timedelta(minutes=ADD_CONTINUATION_TTL_MINUTES),
    )
    store.save(conversation_id, state)
    return state


def get_add_continuation(
    conversation_id: str, *, store=pending_action_store
) -> PendingActionState | None:
    state = store.get(conversation_id)
    return state if is_add_continuation(state) else None


def clear_add_continuation(conversation_id: str, *, store=pending_action_store) -> None:
    store.remove(conversation_id)


def build_add_offer_message(approved_count: int) -> str:
    """Proactive LIA chat message offering to add the approved candidates.

    Conversational, no buttons — the recruiter just replies naturally.
    """
    if approved_count == 1:
        return (
            "\n\nQuer que eu adicione o candidato aprovado à vaga (etapa Triagem)? "
            "É só dizer *sim* ou *agora não*."
        )
    return (
        f"\n\nQuer que eu adicione os {approved_count} candidatos aprovados à vaga "
        "(etapa Triagem)? É só dizer *sim* ou *agora não*."
    )
