"""
Canonical FairnessGuard wrapper for all sourcing tool registries.

P-SSOT: every sourcing tool that invokes FairnessGuard MUST use
 from this module — never catch the guard inline.

P-GUARD contract:
  - If the guard raises -> the result is NEVER served as if it were verified.
  - Decision: fail-LOUD + FLAGGED (not fail-closed) because sourcing is a
    *suggestion* surface, not an autonomous gate. The recruiter sees the result
    but ALSO sees the explicit fairness-not-verified flag and logger.error.
    Fail-closed would break sourcing entirely on any transient guard hiccup.
  - Exception: if a caller passes fail_closed=True (e.g., automated pipeline
    that skips human review), the result is blocked entirely.

Circuit-breaker (P-FAILLOUD):
  - After CIRCUIT_OPEN_THRESHOLD consecutive guard failures, the circuit opens:
    all subsequent calls immediately return flagged (without even trying the guard).
  - Resets on first successful guard call after CIRCUIT_RESET_AFTER_SECONDS.
  - logger.error on open + every call while open.
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# --- Circuit-breaker state (module-level, per-process) ---
CIRCUIT_OPEN_THRESHOLD: int = 5         # N consecutive failures -> open
CIRCUIT_RESET_AFTER_SECONDS: int = 120  # auto-reset attempt after 2 min

_cb_consecutive_failures: int = 0
_cb_open_since: float | None = None     # epoch when circuit opened

# --- Failure counter (for metrics / observability) ---
_total_guard_failures: int = 0          # monotonic; read via get_failure_stats()


def _circuit_is_open() -> bool:
    global _cb_open_since
    if _cb_open_since is None:
        return False
    if time.monotonic() - _cb_open_since > CIRCUIT_RESET_AFTER_SECONDS:
        # Half-open: allow one attempt to reset
        return False
    return True


def _record_failure() -> None:
    global _cb_consecutive_failures, _cb_open_since, _total_guard_failures
    _total_guard_failures += 1
    _cb_consecutive_failures += 1
    if _cb_consecutive_failures >= CIRCUIT_OPEN_THRESHOLD and _cb_open_since is None:
        _cb_open_since = time.monotonic()
        logger.error(
            "[FairnessGuard] circuit OPEN after %d consecutive failures -- "
            "all sourcing results will be flagged as fairness-not-verified "
            "until circuit resets in %ds",
            _cb_consecutive_failures, CIRCUIT_RESET_AFTER_SECONDS,
        )


def _record_success() -> None:
    global _cb_consecutive_failures, _cb_open_since
    _cb_consecutive_failures = 0
    _cb_open_since = None


def get_failure_stats() -> dict[str, Any]:
    """Return current circuit-breaker and failure stats (for health checks / tests)."""
    return {
        "consecutive_failures": _cb_consecutive_failures,
        "circuit_open": _circuit_is_open(),
        "total_failures": _total_guard_failures,
        "circuit_open_since": _cb_open_since,
    }


def reset_for_testing() -> None:
    """Reset all state -- use ONLY in tests."""
    global _cb_consecutive_failures, _cb_open_since, _total_guard_failures
    _cb_consecutive_failures = 0
    _cb_open_since = None
    _total_guard_failures = 0


def run_sourcing_fairness_check(
    guard_callable,
    *args,
    fail_closed: bool = False,
    registry_name: str = "unknown",
    **kwargs,
) -> tuple[bool, str | None]:
    """
    Invoke FairnessGuard.check() and return (is_blocked, block_message).

    Pattern for simple tool registries:

        from app.domains.sourcing.fairness import run_sourcing_fairness_check
        from app.shared.compliance.fairness_guard import FairnessGuard

        _fg = FairnessGuard()
        _fg_blocked, _fg_block_msg = run_sourcing_fairness_check(
            _fg.check, query_str, registry_name="github_tool_registry"
        )
        if _fg_blocked:
            return {
                "success": False,
                "data": {},
                "message": _fg_block_msg or "Busca bloqueada por criterio discriminatorio.",
                "fairness_blocked": True,
            }

    Args:
        guard_callable: The FairnessGuard.check (or similar) method to invoke.
        *args / **kwargs: Forwarded to guard_callable.
        fail_closed: If True, raises FairnessGuardUnavailableError when guard
                     fails unexpectedly. Use for automated pipelines only.
        registry_name: Name of the calling registry (for log context).

    Returns:
        is_blocked (bool): True if guard explicitly blocked the query.
        block_message (str | None): Educational message when blocked; None otherwise.

    Raises:
        FairnessGuardUnavailableError: if fail_closed=True and guard raised unexpectedly.

    Contract:
        - Guard raises unexpectedly -> (False, None) + logger.error (NOT debug).
          Caller must NOT treat this as "clean" -- the guard simply was not run.
          Add fairness_not_verified=True to the response for observability.
        - Circuit-breaker: after CIRCUIT_OPEN_THRESHOLD failures, all calls
          immediately return (False, None) and log error.
    """
    # --- Circuit-breaker check ---
    if _circuit_is_open():
        logger.error(
            "[FairnessGuard:%s] circuit is OPEN -- skipping guard, "
            "result is NOT fairness-verified",
            registry_name,
        )
        if fail_closed:
            raise FairnessGuardUnavailableError(
                f"FairnessGuard circuit open for {registry_name} -- fail_closed=True"
            )
        return False, None

    # --- Invoke guard ---
    try:
        result = guard_callable(*args, **kwargs)
        # Guard ran successfully
        _record_success()
        # Normalise: result is a FairnessCheckResult dataclass
        if hasattr(result, "is_blocked"):
            if result.is_blocked:
                return True, getattr(result, "educational_message", None)
            return False, None
        # Fallback if callable returned something unexpected
        return False, None

    except Exception as exc:
        # Guard failed unexpectedly (service down, input error, bug)
        _record_failure()
        logger.error(
            "[FairnessGuard:%s] guard raised %s: %s -- "
            "consecutive_failures=%d circuit_open=%s -- "
            "result will be served WITHOUT fairness verification",
            registry_name, type(exc).__name__, exc,
            _cb_consecutive_failures, _circuit_is_open(),
            exc_info=True,
        )
        if fail_closed:
            raise FairnessGuardUnavailableError(
                f"FairnessGuard unavailable for {registry_name}: {exc}"
            ) from exc
        return False, None


# --- Exception types ---

class FairnessGuardUnavailableError(RuntimeError):
    """Raised when fail_closed=True and the guard is unavailable/circuit-open."""
