"""Shim: re-exports from app.shared.services.rag_pipeline_service (canonical location).

Tests patch via app.services.rag_pipeline_service — this shim ensures importability.
"""
from app.shared.services.rag_pipeline_service import *  # noqa: F401, F403
try:
    from app.shared.services.rag_pipeline_service import *  # noqa: F401, F403
except ImportError:
    pass
