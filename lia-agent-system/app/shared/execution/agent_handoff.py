"""
Honest Plan & Execute → Agent handoff contract (Task #1222).

Plan & Execute (P&E) only runs DISCRETE, one-shot actions. Some steps that a
recruiter might phrase as part of a composite request are actually CONTINUOUS,
monetizable agents (triagem/WSI screening, continuous sourcing, onboarding) that
live in the Agent Studio and are NOT available yet.

The inviolable contract: when a P&E flow reaches such a step, it must hand off
HONESTLY — return an explicit signal that this is a continuous agent that is not
yet available — and it must NEVER fake success (no silent fallback, no
"done" message for something that did not run).

This module is intentionally *pure* (no DB, no LLM, no app singletons) so it is
reusable identically by every P&E flow and trivially unit-testable. It mirrors
the "never fake success" pattern already established in
``app/orchestrator/routing/post_wizard_continuation.py``.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.domains.base import DomainResponse

__all__ = [
    "DeferredAgent",
    "AgentHandoff",
    "DEFERRED_AGENTS",
    "deferred_agent_for",
    "build_handoff_message",
    "build_handoff",
    "build_handoff_response",
    "HANDOFF_METADATA_KEY",
]

# Metadata flag set on the DomainResponse so downstream consumers can tell a
# deferred-agent handoff apart from a genuine execution failure.
HANDOFF_METADATA_KEY = "agent_handoff"


@dataclass(frozen=True)
class DeferredAgent:
    """A continuous, monetizable agent that P&E hands off to (not yet available)."""

    kind: str
    label: str  # recruiter-facing PT-BR description of what the agent does


# Canonical registry of continuous agents that P&E must NOT execute itself.
# Single source of truth — downstream flow tasks reference these kinds rather
# than re-declaring them.
DEFERRED_AGENTS: dict[str, DeferredAgent] = {
    "triagem_wsi": DeferredAgent(
        kind="triagem_wsi",
        label="a triagem WSI dos candidatos",
    ),
    "sourcing_continuo": DeferredAgent(
        kind="sourcing_continuo",
        label="a busca contínua de candidatos (sourcing)",
    ),
    "onboarding": DeferredAgent(
        kind="onboarding",
        label="o onboarding do candidato contratado",
    ),
}


# Maps a P&E pipeline step ``(domain_id, action_id)`` to the deferred agent it
# actually belongs to. Only genuinely-continuous steps are listed here; discrete
# steps (move stage, send a single notification, enrich a JD, parse a CV) are NOT
# deferred and execute normally.
#
# NOTE (Task #1222): the onboarding mappings are kept as a *reserved* canonical
# entry for the future onboarding agent even though no current PLAN_PATTERN
# produces them (the "onboarding_pipeline" pattern/template were removed). This
# is harmless — ``deferred_agent_for`` simply returns ``None`` for steps never
# reached — and documents intent so a re-added onboarding flow hands off honestly
# by construction instead of silently faking success.
_ACTION_TO_DEFERRED_AGENT: dict[tuple[str, str], str] = {
    ("cv_screening", "screen_candidates"): "triagem_wsi",
    ("cv_screening", "run_wsi_screening"): "triagem_wsi",
    ("cv_screening", "send_wsi_batch"): "triagem_wsi",
    ("cv_screening", "list_pending_screening"): "triagem_wsi",
    ("sourcing", "start_sourcing"): "sourcing_continuo",
    ("communication", "request_onboarding_documents"): "onboarding",
    ("interview_scheduling", "schedule_day_one"): "onboarding",
    ("communication", "notify_team_new_hire"): "onboarding",
}


@dataclass(frozen=True)
class AgentHandoff:
    """An honest, never-faked handoff result for a deferred-agent step."""

    kind: str
    label: str
    message: str
    executed: bool = False  # ALWAYS False — the continuous agent did not run


def deferred_agent_for(domain_id: str, action_id: str) -> DeferredAgent | None:
    """Return the :class:`DeferredAgent` a P&E step belongs to, else ``None``.

    ``None`` means the step is a normal discrete action and P&E may run it.
    """
    kind = _ACTION_TO_DEFERRED_AGENT.get((domain_id, action_id))
    return DEFERRED_AGENTS.get(kind) if kind else None


def build_handoff_message(agent: DeferredAgent) -> str:
    """Recruiter-facing PT-BR message: explicit, conversational, never fake.

    No buttons — the chat is the primary interface. We tell the recruiter the
    discrete part is done and that the continuous part will be an agent that is
    not available yet (instead of pretending it executed).
    """
    return (
        f"Sobre {agent.label}: isso é uma etapa contínua que vai virar um agente "
        f"dedicado e ainda não está disponível para execução automática — então "
        f"não executei essa parte. Por enquanto você pode tocá-la manualmente. "
        f"Quer seguir com o resto?"
    )


def build_handoff(domain_id: str, action_id: str) -> AgentHandoff | None:
    """Build an :class:`AgentHandoff` for a deferred step, else ``None``."""
    agent = deferred_agent_for(domain_id, action_id)
    if agent is None:
        return None
    return AgentHandoff(
        kind=agent.kind,
        label=agent.label,
        message=build_handoff_message(agent),
    )


def build_handoff_response(domain_id: str, action_id: str) -> DomainResponse | None:
    """Build a :class:`DomainResponse` for a deferred step, else ``None``.

    ``success=False`` (it did not run) but tagged via ``metadata`` so callers can
    distinguish an honest handoff from a real error and surface the explicit
    message instead of a generic failure. Never fakes success.
    """
    handoff = build_handoff(domain_id, action_id)
    if handoff is None:
        return None
    return DomainResponse(
        success=False,
        message=handoff.message,
        metadata={
            HANDOFF_METADATA_KEY: {
                "kind": handoff.kind,
                "label": handoff.label,
                "executed": handoff.executed,
            }
        },
    )
