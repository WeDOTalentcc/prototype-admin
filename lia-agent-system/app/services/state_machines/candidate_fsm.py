"""
Candidate Stage FSM — finite-state machine for pipeline transitions.

Validates that a stage transition is semantically legal:
  • Blocks moves FROM terminal stages (rejected / hired / cancelled / not_selected)
    unless force=True is explicitly requested.
  • All other stage names (company-custom columns) may transition freely.

Usage
-----
    from app.services.state_machines.candidate_fsm import validate_stage_transition
    validate_stage_transition(from_stage, to_stage)  # raises LIAInvalidStateTransition

The caller is responsible for catching LIAInvalidStateTransition and returning
HTTP 409. The global LIAError handler in main.py handles it automatically when
the exception propagates out of a route function.
"""
from __future__ import annotations

from app.shared.errors import LIAInvalidStateTransition

# Terminal stages — once a candidate reaches these stages, no further
# transitions are allowed (unless force=True is used by agents).
# Source: app/api/v1/platform_event_handlers.py terminal_statuses + operational stages.
TERMINAL_STAGES: frozenset[str] = frozenset({
    "rejected",
    "hired",
    "cancelled",
    "not_selected",
})


def validate_stage_transition(
    from_stage: str | None,
    to_stage: str,
    force: bool = False,
) -> None:
    """Validate that a stage transition is allowed by the FSM.

    Args:
        from_stage: Current stage of the candidate. None means no previous stage
                    (initial placement) — always allowed.
        to_stage:   Target stage name.
        force:      When True, bypasses terminal-state check. Used by agents
                    with explicit override authority (e.g., admin corrections).

    Raises:
        LIAInvalidStateTransition: When transitioning from a terminal stage
            without force=True.
    """
    if force or from_stage is None:
        return

    if from_stage in TERMINAL_STAGES:
        raise LIAInvalidStateTransition(
            message=(
                f"Transição inválida: candidato está no estado terminal '{from_stage}' "
                f"e não pode ser movido para '{to_stage}'. "
                "Use force=True para forçar a transição em casos excepcionais."
            ),
            code="INVALID_STATE_TRANSITION",
            details={
                "from_stage": from_stage,
                "to_stage": to_stage,
                "terminal_stages": sorted(TERMINAL_STAGES),
            },
            recoverable=False,
        )
