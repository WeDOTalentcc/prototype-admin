"""
ActionResult dataclass — single source of truth for action execution results.
No project dependencies — safe to import from anywhere.
"""
from dataclasses import dataclass
from typing import Any, Literal



@dataclass
class ActionResult:
    status: Literal["executed", "needs_params", "needs_confirmation", "not_actionable", "error"]
    message: str = ""
    data: dict[str, Any] | None = None
    missing_params: list[str] | None = None
    confirmation_summary: dict[str, Any] | None = None
    action_type: str | None = None
    pending_action_id: str | None = None
    error_detail: str | None = None
