"""
Prompt Injection Protection - Guards against adversarial inputs.

Detects and blocks common prompt injection patterns in user messages
before they reach LLM processing. Provides sanitization and detection.

CONSOLIDATED: This module now delegates to the canonical security engine
in app.shared.robustness.security_patterns. The PromptInjectionGuard class
and InjectionCheckResult dataclass are preserved for backward compatibility.

Usage:
    from app.shared.prompt_injection import PromptInjectionGuard
    
    guard = PromptInjectionGuard()
    result = guard.check(user_message)
    if result.is_suspicious:
        # Handle injection attempt
        ...
    
    sanitized = guard.sanitize(user_message)
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.shared.robustness.security_patterns import (
    check_input_security,
    SecurityCheckResult,
)

logger = logging.getLogger(__name__)


@dataclass
class InjectionCheckResult:
    """Backward-compatible result wrapper over SecurityCheckResult."""
    is_suspicious: bool
    risk_level: str = "none"
    matched_patterns: list[str] = field(default_factory=list)
    original_input: str = ""
    sanitized_input: str = ""
    confidence: float = 0.0

    @property
    def is_blocked(self) -> bool:
        """Alias for is_suspicious - backward compat with compliance_base."""
        return self.is_suspicious


def _to_injection_result(sec: SecurityCheckResult, sanitized: str = "") -> InjectionCheckResult:
    """Convert canonical SecurityCheckResult to legacy InjectionCheckResult."""
    return InjectionCheckResult(
        is_suspicious=sec.is_blocked,
        risk_level=sec.risk_level,
        matched_patterns=sec.matched_pattern_names,
        original_input=sec.original_input,
        sanitized_input=sanitized or sec.original_input,
        confidence=sec.confidence,
    )


class PromptInjectionGuard:
    """
    Prompt injection guard — delegates to security_patterns.check_input_security().

    Preserves the original class API (check, sanitize, get_stats) so all existing
    callers (agent_chat_ws.py, wsi_interview_graph.py, compliance_base.py) keep working.
    """

    def __init__(self) -> None:
        self._total_checks = 0
        self._total_blocks = 0

    def check(self, user_input: str) -> InjectionCheckResult:
        self._total_checks += 1

        if not user_input or not user_input.strip():
            return InjectionCheckResult(
                is_suspicious=False,
                original_input=user_input or "",
                sanitized_input=user_input or "",
            )

        sec_result = check_input_security(user_input)

        if sec_result.is_blocked:
            self._total_blocks += 1
            sanitized = self.sanitize(user_input)
        else:
            sanitized = user_input

        return _to_injection_result(sec_result, sanitized)

    def sanitize(self, user_input: str) -> str:
        sanitized = user_input
        sanitized = re.sub(r'<\|?[^>]*\|?>', '', sanitized)
        sanitized = re.sub(r'```\w*\n', '', sanitized)
        sanitized = re.sub(r'###\s*SYSTEM[^\n]*', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\[SYSTEM\][^\]]*', '', sanitized, flags=re.IGNORECASE)
        return sanitized.strip()

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_checks": self._total_checks,
            "total_blocks": self._total_blocks,
            "block_rate": (
                round(self._total_blocks / self._total_checks, 4)
                if self._total_checks > 0
                else 0.0
            ),
        }
