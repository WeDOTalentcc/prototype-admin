"""Onda 3.3 Init VII (2026-04-21) — Error recovery policy engine.

Loads app/orchestrator/error_policies.yaml + provides lookup helpers so
orchestrator exception handlers can emit a grounded PT response instead of
improvising.

Usage at callsite:
    from app.orchestrator.error_policies import resolve_policy
    try:
        result = await tool.execute(...)
    except TimeoutError:
        policy = resolve_policy("timeout")
        return policy.render()

Canonical-fix: YAML is the single producer for error recovery semantics.
Python module is thin loader + matcher. Drift guarded by CI test.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_ERROR_POLICIES_ENABLED = os.environ.get(
    "LIA_ERROR_POLICIES_ENABLED", "true"
).lower() == "true"


@dataclass
class ErrorPolicy:
    id: str
    triggers: list[str]
    response_template: str
    retry_hint: bool = False
    severity: str = "info"
    anti_patterns: list[str] = field(default_factory=list)

    def render(self, **context: Any) -> str:
        """Render template with context substitution. Missing keys stay as
        literal placeholders (safe for partial context)."""
        out = self.response_template
        for key, val in context.items():
            out = out.replace("{" + key + "}", str(val))
        return out.strip()


@lru_cache(maxsize=1)
def _load_policies() -> list[ErrorPolicy]:
    """Load error_policies.yaml. Cached — restart required to reload."""
    yaml_path = Path(__file__).parent / "error_policies.yaml"
    if not yaml_path.exists():
        logger.warning("Init VII: error_policies.yaml not found at %s", yaml_path)
        return []

    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        policies = []
        for entry in data.get("policies", []):
            policies.append(ErrorPolicy(
                id=entry["id"],
                triggers=entry.get("triggers", []),
                response_template=entry.get("response_template", ""),
                retry_hint=entry.get("retry_hint", False),
                severity=entry.get("severity", "info"),
                anti_patterns=entry.get("anti_patterns", []),
            ))
        return policies
    except Exception as exc:
        logger.error("Init VII: failed to load error_policies.yaml: %s", exc)
        return []


def list_policy_ids() -> list[str]:
    """Return all policy IDs registered in catalog."""
    return [p.id for p in _load_policies()]


def resolve_policy(signal: str | Exception) -> ErrorPolicy | None:
    """Find the first policy whose triggers match the given signal.

    Args:
        signal: Error string OR exception instance. Exception class name
            + message will both be tested against trigger patterns.

    Returns:
        Matching ErrorPolicy or None.
    """
    if not _ERROR_POLICIES_ENABLED:
        return None

    policies = _load_policies()
    if not policies:
        return None

    # Build search corpus from signal
    corpus: list[str] = []
    if isinstance(signal, Exception):
        corpus.append(type(signal).__name__)
        corpus.append(str(signal))
    else:
        corpus.append(str(signal))

    haystack = " ".join(corpus).lower()

    for policy in policies:
        for trigger in policy.triggers:
            if trigger.lower() in haystack:
                return policy
    return None


def apply_policy(
    signal: str | Exception,
    *,
    context: dict[str, Any] | None = None,
    fallback: str = "Ocorreu um erro inesperado. Reporte se persistir.",
) -> dict[str, Any]:
    """Resolve + render a policy. Returns dict with response/severity/retry_hint
    suitable for orchestrator to surface in ChatResponse.

    Always returns a dict (never raises). Falls back to generic message when
    no policy matches.
    """
    policy = resolve_policy(signal)
    if policy is None:
        return {
            "response": fallback,
            "severity": "error",
            "retry_hint": False,
            "policy_id": None,
        }

    rendered = policy.render(**(context or {}))
    logger.info(
        "[LIA-ERRPOL] applied policy=%s severity=%s signal=%s",
        policy.id, policy.severity,
        type(signal).__name__ if isinstance(signal, Exception) else str(signal)[:80],
    )
    return {
        "response": rendered,
        "severity": policy.severity,
        "retry_hint": policy.retry_hint,
        "policy_id": policy.id,
    }
