"""
COMPAT STUB — W4-035 Fase 1.
Módulo movido para app/orchestrator/legacy/tasting_engine.py.
Este stub mantém compatibilidade de imports existentes.
"""
from app.orchestrator.legacy.tasting_engine import (  # noqa: F401
    TastingEngine,
    tasting_engine,
    format_tasting_block,
)

__all__ = ["TastingEngine", "tasting_engine", "format_tasting_block"]
