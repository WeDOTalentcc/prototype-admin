"""
COMPAT STUB — W4-035 Fase 1.
Módulo movido para app/orchestrator/legacy/orchestrator.py.

Este stub mantém compatibilidade total:
- Emite DeprecationWarning no import (preservando UC-P1-23)
- Re-exporta TODOS os símbolos do módulo original (incluindo para patch de testes)
"""
import warnings as _lia_warnings

# UC-P1-23: Module-level deprecation — fires on import, preservado do módulo original.
_lia_warnings.warn(
    "app.orchestrator.orchestrator (Orchestrator v1) is deprecated. "
    "Use app.orchestrator.main_orchestrator.MainOrchestrator via "
    "get_main_orchestrator() instead. Will be removed Q3 2026. [LIA-D06]",
    DeprecationWarning,
    stacklevel=2,
)

# Wildcard re-export: traz todos os atributos para este namespace,
# permitindo que patch("app.orchestrator.orchestrator.<attr>") continue funcionando.
from app.orchestrator.legacy.orchestrator import *  # noqa: F401, F403
from app.orchestrator.legacy.orchestrator import Orchestrator  # noqa: F401

__all__ = ["Orchestrator"]
