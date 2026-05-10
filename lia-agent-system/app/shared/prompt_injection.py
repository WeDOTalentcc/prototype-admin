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


# Maps low-level security pattern names → canonical injection categories.
# PromptInjectionGuard exposes simplified category names for backward compat.
_PATTERN_TO_CATEGORY: dict[str, str] = {
    # System prompt override (ignore/disregard/forget instructions)
    "jailbreak_ignore_instructions_en": "system_prompt_override",
    "jailbreak_ignore_instructions_pt": "system_prompt_override",
    # Jailbreak attempts (DAN, developer mode, act-as, etc.)
    "jailbreak_dan_developer_mode": "jailbreak_attempt",
    "jailbreak_act_as_override": "role_manipulation",
    "jailbreak_previous_prompt": "jailbreak_attempt",
    "jailbreak_keyword_persona": "jailbreak_attempt",
    # Role manipulation
    "role_manipulation_pretend": "role_manipulation",
    # System prompt extraction
    "system_override_extract_prompt": "system_prompt_extraction",
    # Delimiter injection
    "system_override_delimiter": "delimiter_injection",
    "delimiter_injection_markdown": "delimiter_injection",
}

# Public catalogue of injection pattern names — used by tests and external audit tools.
INJECTION_PATTERNS: list[str] = list(_PATTERN_TO_CATEGORY.keys())


def _normalize_risk(risk: str) -> str:
    """Normalize security_patterns risk levels to PromptInjectionGuard scale.

    security_patterns uses CRITICAL (highest) but PromptInjectionGuard
    tests expect 'high' as the maximum level.
    """
    if str(risk) == "critical":
        return "high"
    return str(risk)


def _to_injection_result(sec: SecurityCheckResult, sanitized: str = "") -> InjectionCheckResult:
    """Convert canonical SecurityCheckResult to legacy InjectionCheckResult.

    Adds canonical category names to matched_patterns (in addition to raw
    pattern names) so callers that check for 'system_prompt_override' etc.
    keep working.
    """
    # Build enriched pattern list: raw names + canonical categories (deduped)
    raw_names = list(sec.matched_pattern_names)
    categories: list[str] = []
    for name in raw_names:
        cat = _PATTERN_TO_CATEGORY.get(name)
        if cat and cat not in raw_names and cat not in categories:
            categories.append(cat)
    enriched_patterns = raw_names + categories

    return InjectionCheckResult(
        is_suspicious=sec.is_blocked,
        risk_level=_normalize_risk(sec.risk_level),
        matched_patterns=enriched_patterns,
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
