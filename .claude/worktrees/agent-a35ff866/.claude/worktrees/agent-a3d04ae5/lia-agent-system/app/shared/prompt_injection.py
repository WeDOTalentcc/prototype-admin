"""
Prompt Injection Protection - Guards against adversarial inputs.

Detects and blocks common prompt injection patterns in user messages
before they reach LLM processing. Provides sanitization and detection.

Usage:
    from app.shared.prompt_injection import PromptInjectionGuard
    
    guard = PromptInjectionGuard()
    result = guard.check(user_message)
    if result.is_suspicious:
        # Handle injection attempt
        ...
    
    sanitized = guard.sanitize(user_message)
"""
import re
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class InjectionCheckResult:
    is_suspicious: bool
    risk_level: str = "none"
    matched_patterns: List[str] = field(default_factory=list)
    original_input: str = ""
    sanitized_input: str = ""
    confidence: float = 0.0


INJECTION_PATTERNS = [
    {
        "name": "system_prompt_override",
        "patterns": [
            re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
            re.compile(r"ignore\s+(all\s+)?above\s+instructions", re.IGNORECASE),
            re.compile(r"disregard\s+(all\s+)?previous", re.IGNORECASE),
            re.compile(r"forget\s+(all\s+)?previous", re.IGNORECASE),
            re.compile(r"ignore\s+tudo\s+anterior", re.IGNORECASE),
            re.compile(r"desconsidere?\s+(todas?\s+)?instru[çc][õo]es", re.IGNORECASE),
        ],
        "risk": "high",
        "confidence": 0.9,
    },
    {
        "name": "role_manipulation",
        "patterns": [
            re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
            re.compile(r"act\s+as\s+(a|an)\s+", re.IGNORECASE),
            re.compile(r"pretend\s+(to\s+be|you\s+are)", re.IGNORECASE),
            re.compile(r"voc[êe]\s+agora\s+[ée]\s+(um|uma)", re.IGNORECASE),
            re.compile(r"finja\s+(ser|que)", re.IGNORECASE),
            re.compile(r"assuma\s+o\s+papel", re.IGNORECASE),
        ],
        "risk": "high",
        "confidence": 0.85,
    },
    {
        "name": "system_prompt_extraction",
        "patterns": [
            re.compile(r"(show|reveal|print|display)\s+(me\s+)?(your|the)\s+system\s+prompt", re.IGNORECASE),
            re.compile(r"what\s+(is|are)\s+your\s+(system\s+)?instructions", re.IGNORECASE),
            re.compile(r"(mostre|revele|exiba)\s+(seu\s+)?prompt\s+d[eo]\s+sistema", re.IGNORECASE),
            re.compile(r"quais?\s+s[ãa]o\s+suas?\s+instru[çc][õo]es", re.IGNORECASE),
        ],
        "risk": "medium",
        "confidence": 0.8,
    },
    {
        "name": "delimiter_injection",
        "patterns": [
            re.compile(r"```system", re.IGNORECASE),
            re.compile(r"\[SYSTEM\]", re.IGNORECASE),
            re.compile(r"<\|?system\|?>", re.IGNORECASE),
            re.compile(r"###\s*SYSTEM", re.IGNORECASE),
            re.compile(r"<\|?im_start\|?>", re.IGNORECASE),
        ],
        "risk": "high",
        "confidence": 0.95,
    },
    {
        "name": "data_exfiltration",
        "patterns": [
            re.compile(r"(send|post|fetch|curl)\s+.*(http|url|api|endpoint)", re.IGNORECASE),
            re.compile(r"(envie|mande|poste)\s+.*(http|url|api|endpoint)", re.IGNORECASE),
            re.compile(r"(base64|encode|decrypt|hexadecimal)", re.IGNORECASE),
        ],
        "risk": "medium",
        "confidence": 0.7,
    },
    {
        "name": "jailbreak_attempt",
        "patterns": [
            re.compile(r"(DAN|do\s+anything\s+now)", re.IGNORECASE),
            re.compile(r"developer\s+mode", re.IGNORECASE),
            re.compile(r"(bypass|circumvent|override)\s+.*(filter|guard|safety|restriction)", re.IGNORECASE),
        ],
        "risk": "high",
        "confidence": 0.9,
    },
]


class PromptInjectionGuard:
    def __init__(self):
        self._total_checks = 0
        self._total_blocks = 0

    def check(self, user_input: str) -> InjectionCheckResult:
        self._total_checks += 1

        if not user_input or not user_input.strip():
            return InjectionCheckResult(
                is_suspicious=False,
                original_input=user_input,
                sanitized_input=user_input,
            )

        matched_patterns = []
        max_confidence = 0.0
        max_risk = "none"

        risk_priority = {"none": 0, "low": 1, "medium": 2, "high": 3}

        for category in INJECTION_PATTERNS:
            for pattern in category["patterns"]:
                if pattern.search(user_input):
                    matched_patterns.append(category["name"])
                    max_confidence = max(max_confidence, category["confidence"])
                    if risk_priority.get(category["risk"], 0) > risk_priority.get(max_risk, 0):
                        max_risk = category["risk"]
                    break

        is_suspicious = len(matched_patterns) > 0

        if is_suspicious:
            self._total_blocks += 1
            logger.warning(
                f"[PROMPT-INJECTION] Suspicious input detected: "
                f"patterns={matched_patterns}, risk={max_risk}, "
                f"confidence={max_confidence:.2f}, "
                f"input_preview='{user_input[:80]}...'"
            )

        return InjectionCheckResult(
            is_suspicious=is_suspicious,
            risk_level=max_risk,
            matched_patterns=matched_patterns,
            original_input=user_input,
            sanitized_input=self.sanitize(user_input) if is_suspicious else user_input,
            confidence=max_confidence,
        )

    def sanitize(self, user_input: str) -> str:
        sanitized = user_input
        sanitized = re.sub(r'<\|?[^>]*\|?>', '', sanitized)
        sanitized = re.sub(r'```\w*\n', '', sanitized)
        sanitized = re.sub(r'###\s*SYSTEM[^\n]*', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\[SYSTEM\][^\]]*', '', sanitized, flags=re.IGNORECASE)
        return sanitized.strip()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_checks": self._total_checks,
            "total_blocks": self._total_blocks,
            "block_rate": (
                round(self._total_blocks / self._total_checks, 4)
                if self._total_checks > 0
                else 0.0
            ),
        }
