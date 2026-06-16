"""Shim: re-exports policy_setup_agent from canonical location.

I3c cleanup (2026-05-xx): module moved to
``app.domains.policy.agents.agent``.  This shim preserves backwards-
compatibility for legacy ``from app.agents.policy_setup_agent import ...``
imports and test assertions.  Emits DeprecationWarning on import.
"""
import warnings

warnings.warn(
    "app.agents.policy_setup_agent is deprecated — "
    "import from app.domains.policy.agents.agent instead. "
    "This shim will be removed in a future sprint.",
    DeprecationWarning,
    stacklevel=2,
)

from app.domains.policy.agents.agent import (  # noqa: F401, E402
    PolicySetupAgent,
    policy_setup_agent,
)

__all__ = ["PolicySetupAgent", "policy_setup_agent"]
