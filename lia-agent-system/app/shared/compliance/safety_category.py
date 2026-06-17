"""Safety categories for tool governance (UC-P2-09).

Replaces GUARDRAIL_TOOLS list[str] with a typed enum so Python
catches invalid tool names at import time rather than silently
allowing them through guardrail checks.
"""
from __future__ import annotations
from enum import StrEnum


class SafetyCategory(StrEnum):
    """Risk category for tools that require HITL or extra audit."""
    DESTRUCTIVE_WRITE = "destructive_write"   # irreversible data mutation
    BULK_ACTION = "bulk_action"               # affects many records at once
    PII_EXPORT = "pii_export"                 # exports personal data
    OUTREACH = "outreach"                     # sends external communications
    PIPELINE_MOVE = "pipeline_move"           # moves candidate stage
    OFFER = "offer"                           # sends/creates an offer


# Maps tool names to their safety category.
# Import and use in each tool registry instead of a raw list[str].
TOOL_SAFETY_MAP: dict[str, SafetyCategory] = {}
