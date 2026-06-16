"""
LIA-I01: Shared Keyword Intent Matcher

Provides a unified, configurable intent matching system that domains can use
instead of hardcoded _KEYWORD_ACTION_MAP dicts.

Supports:
- Keyword matching (exact substring)
- Regex matching (compiled patterns)
- Confidence scoring (based on keyword length and specificity)
- INFO vs ACTION intent classification
- YAML configuration per domain

Usage:
    matcher = KeywordIntentMatcher.from_yaml("app/domains/analytics/config/capabilities.yaml")
    result = matcher.match("gerar relatório kpi")
    # IntentMatch(action="generate_kpi_report", confidence=0.85, intent_type="action")
"""
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    INFO = "info"           # User wants explanation/information
    ACTION = "action"       # User wants to execute something
    NAVIGATION = "navigation"  # User wants to go somewhere
    UNKNOWN = "unknown"


@dataclass
class IntentMatch:
    action: str
    confidence: float
    intent_type: IntentType = IntentType.ACTION
    domain_id: str = ""
    matched_keyword: str = ""


@dataclass
class IntentPattern:
    keywords: list[str]
    action: str
    intent_type: IntentType = IntentType.ACTION
    confidence_base: float = 0.8
    description: str = ""


# Global patterns that indicate INFO intent regardless of domain
_INFO_PATTERNS = [
    r"como\s+funciona",
    r"o\s+que\s+[eé]",
    r"me\s+explic[ae]",
    r"me\s+cont[ae]",
    r"quero\s+saber",
    r"quero\s+entender",
    r"como\s+faz",
    r"como\s+(?:eu\s+)?(?:posso|consigo|devo)",
    r"para\s+que\s+serve",
    r"qual\s+(?:a\s+)?diferen[cç]a",
    r"me\s+d[aá]\s+(?:uma\s+)?(?:vis[aã]o|ideia|resumo)",
    r"o\s+que\s+significa",
    r"como\s+usar",
    r"tutorial",
    r"ajuda\s+(?:com|sobre|para)",
]
_INFO_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INFO_PATTERNS]


class KeywordIntentMatcher:
    """Matches user queries to intents using keywords, regex, and info/action classification."""

    def __init__(self, patterns: list[IntentPattern] | None = None, domain_id: str = ""):
        self.patterns = patterns or []
        self.domain_id = domain_id

    @classmethod
    def from_yaml(cls, yaml_path: str) -> "KeywordIntentMatcher":
        """Load intent patterns from a YAML capabilities file."""
        try:
            with open(yaml_path, "r") as f:
                data = yaml.safe_load(f)

            domain_id = data.get("domain_id", "")
            patterns = []
            for intent in data.get("intents", []):
                patterns.append(IntentPattern(
                    keywords=intent.get("keywords", []),
                    action=intent.get("action", ""),
                    intent_type=IntentType(intent.get("type", "action")),
                    confidence_base=intent.get("confidence", 0.8),
                    description=intent.get("description", ""),
                ))

            return cls(patterns=patterns, domain_id=domain_id)
        except Exception as e:
            logger.warning("[LIA-I01] Failed to load YAML %s: %s", yaml_path, e)
            return cls(domain_id="")

    @classmethod
    def from_keyword_map(cls, keyword_map: dict[str, str], domain_id: str = "") -> "KeywordIntentMatcher":
        """Convert a legacy _KEYWORD_ACTION_MAP dict to a matcher.

        This enables gradual migration: domains can wrap their existing maps
        without changing behavior, then migrate to YAML later.
        """
        patterns = []
        for keyword, action in keyword_map.items():
            patterns.append(IntentPattern(
                keywords=[keyword],
                action=action,
                intent_type=IntentType.ACTION,
                confidence_base=0.8,
            ))
        return cls(patterns=patterns, domain_id=domain_id)

    def is_info_query(self, query: str) -> bool:
        """Detect if the query is asking for information/explanation, not action."""
        q_lower = query.lower().strip()
        return any(p.search(q_lower) for p in _INFO_COMPILED)

    def match(self, query: str, default_action: str = "general_help") -> IntentMatch:
        """Match a query to the best intent."""
        q_lower = query.lower().strip()

        # First check: is this an INFO query?
        is_info = self.is_info_query(query)

        best_match = IntentMatch(
            action=default_action,
            confidence=0.3,
            intent_type=IntentType.INFO if is_info else IntentType.UNKNOWN,
            domain_id=self.domain_id,
        )

        for pattern in self.patterns:
            for keyword in pattern.keywords:
                if keyword.lower() in q_lower:
                    # Calculate confidence based on keyword length
                    conf = min(0.95, pattern.confidence_base + len(keyword) * 0.01)

                    if conf > best_match.confidence:
                        best_match = IntentMatch(
                            action=pattern.action,
                            confidence=conf,
                            intent_type=IntentType.INFO if is_info else pattern.intent_type,
                            domain_id=self.domain_id,
                            matched_keyword=keyword,
                        )

        return best_match
