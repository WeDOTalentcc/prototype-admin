"""
orchestrator/legacy/ — módulos legados em processo de desativação ou substituição.

- orchestrator.py: Orchestrator legado (usado por orchestrator_routes.py)
- tasting_engine.py: TastingEngine de insights proativos (importado lazy por main_orchestrator)

Re-exports de compatibilidade mantidos via __init__.py do pacote pai.
"""
from app.orchestrator.legacy.orchestrator import Orchestrator
from app.orchestrator.legacy.tasting_engine import TastingEngine, tasting_engine, format_tasting_block

__all__ = [
    "Orchestrator",
    "TastingEngine",
    "tasting_engine",
    "format_tasting_block",
]
