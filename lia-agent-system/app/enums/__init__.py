"""
Centralized enums and constants for the LIA Agent System.

Importing from here prevents magic strings scattered across the codebase.
"""
from app.enums.communication import ABTestName, TemplateSituation
from app.enums.orchestrator import CacheableIntent, OrchestratorScope

__all__ = [
    "CacheableIntent",
    "OrchestratorScope",
    "TemplateSituation",
    "ABTestName",
]
