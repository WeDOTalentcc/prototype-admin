"""
BaseStateMachine — Abstract base class for all LangGraph-style state machines.

Provides a common interface for:
  - Stage/transition management
  - State initialisation and validation
  - Progress tracking

Concrete state machines (JobWizardGraph, interview flows, etc.) should inherit
from this class and implement the abstract methods.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar

StateT = TypeVar("StateT")
StageT = TypeVar("StageT")


class BaseStateMachine(ABC, Generic[StateT, StageT]):
    """Abstract base for ReAct / LangGraph state machines in LIA."""

    # ------------------------------------------------------------------ #
    # Required overrides                                                   #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def get_initial_state(self, **kwargs: Any) -> StateT:
        """Return an initialised state object for a new session."""

    @abstractmethod
    def get_stage_order(self) -> List[StageT]:
        """Return the ordered list of stages for this state machine."""

    @abstractmethod
    def get_next_stage(self, current: StageT) -> Optional[StageT]:
        """Return the stage that follows *current*, or None if at end."""

    @abstractmethod
    def can_transition(self, state: StateT, target: StageT) -> bool:
        """Return True if the state machine can move to *target* from current state."""

    @abstractmethod
    def apply_transition(self, state: StateT, target: StageT) -> StateT:
        """Mutate (or return a new) state that reflects the transition to *target*."""

    # ------------------------------------------------------------------ #
    # Optional helpers with default implementations                        #
    # ------------------------------------------------------------------ #

    def get_progress(self, state: StateT) -> Dict[str, Any]:
        """
        Return a serialisable dict describing current stage progress.

        Default implementation returns an empty dict; override to enrich.
        """
        return {}

    def is_terminal(self, state: StateT) -> bool:
        """
        Return True when the state machine has reached a terminal (final) stage.

        Default: False. Override to provide real logic.
        """
        return False

    def validate_state(self, state: StateT) -> List[str]:
        """
        Return a list of validation errors for *state*.

        Empty list means valid. Default: no validation.
        """
        return []
