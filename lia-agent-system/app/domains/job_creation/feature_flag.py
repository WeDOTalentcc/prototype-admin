"""
Feature flag for the Unified Wizard (B.6 migration switch).

Controls whether the new conversational wizard is enabled per workspace.
When disabled, the legacy 96-file wizard continues to function.

Usage:
    from app.domains.job_creation.feature_flag import is_wizard_enabled

    if is_wizard_enabled(workspace_id):
        # Route to job_creation domain (new wizard)
    else:
        # Route to legacy wizard
"""

import logging
import os
from typing import Optional, Set

logger = logging.getLogger(__name__)

# Environment variable override (global on/off)
_ENV_FLAG = os.environ.get("ENABLE_UNIFIED_WIZARD", "").lower()

# Per-workspace overrides (loaded from DB or config)
_workspace_overrides: dict[int, bool] = {}

# Rollout percentage (0-100) for gradual migration
_rollout_percentage: int = 0


def is_wizard_enabled(workspace_id: Optional[int] = None) -> bool:
    """Check if the unified wizard is enabled for a workspace.

    Priority:
    1. ENV override (ENABLE_UNIFIED_WIZARD=true/false) — global
    2. Per-workspace override (set via admin)
    3. Rollout percentage (gradual migration)
    4. Default: False (legacy wizard)
    """
    # 1. Global env override
    if _ENV_FLAG == "true":
        return True
    if _ENV_FLAG == "false":
        return False

    # 2. Per-workspace override
    if workspace_id and workspace_id in _workspace_overrides:
        return _workspace_overrides[workspace_id]

    # 3. Rollout percentage
    if workspace_id and _rollout_percentage > 0:
        # Deterministic: same workspace always gets same result
        return (workspace_id % 100) < _rollout_percentage

    # 4. Default: disabled
    return False


def enable_for_workspace(workspace_id: int) -> None:
    """Enable unified wizard for a specific workspace."""
    _workspace_overrides[workspace_id] = True
    logger.info("[FeatureFlag] Unified wizard ENABLED for workspace %d", workspace_id)


def disable_for_workspace(workspace_id: int) -> None:
    """Disable unified wizard for a specific workspace."""
    _workspace_overrides[workspace_id] = False
    logger.info("[FeatureFlag] Unified wizard DISABLED for workspace %d", workspace_id)


def set_rollout_percentage(pct: int) -> None:
    """Set rollout percentage (0-100) for gradual migration."""
    global _rollout_percentage
    _rollout_percentage = max(0, min(100, pct))
    logger.info("[FeatureFlag] Rollout percentage set to %d%%", _rollout_percentage)


def get_status() -> dict:
    """Get current feature flag status for monitoring."""
    return {
        "env_override": _ENV_FLAG or "not_set",
        "workspace_overrides": len(_workspace_overrides),
        "rollout_percentage": _rollout_percentage,
        "enabled_workspaces": [ws for ws, v in _workspace_overrides.items() if v],
    }
