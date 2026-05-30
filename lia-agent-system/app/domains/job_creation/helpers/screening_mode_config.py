"""SCREENING_MODE_CONFIG — single source of truth for screening mode constants.

Consumed by intake_gate_node (time estimates), competency_gate_node (confirmation),
and any future consumer (wsi_questions, competency_node).
"""
from __future__ import annotations
from typing import TypedDict


class ScreeningModeInfo(TypedDict):
    total_questions: int
    estimated_minutes: int


SCREENING_MODE_CONFIG: dict[str, ScreeningModeInfo] = {
    "compact": {"total_questions": 7, "estimated_minutes": 15},
    "full": {"total_questions": 12, "estimated_minutes": 25},
}
