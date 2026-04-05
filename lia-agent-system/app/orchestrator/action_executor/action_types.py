"""
ActionResult dataclass — single source of truth for action execution results.
No project dependencies — safe to import from anywhere.
"""
from typing import Dict, Any, Optional, List, Literal
from dataclasses import dataclass, field


@dataclass
class ActionResult:
    status: Literal["executed", "needs_params", "needs_confirmation", "not_actionable", "error"]
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    missing_params: Optional[List[str]] = None
    confirmation_summary: Optional[Dict[str, Any]] = None
    action_type: Optional[str] = None
    pending_action_id: Optional[str] = None
    error_detail: Optional[str] = None
