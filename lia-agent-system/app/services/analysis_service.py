"""Shim: re-exports from canonical app.shared.services.analysis_service."""
from app.shared.services.analysis_service import *  # noqa: F401, F403
try:
    from app.shared.services.analysis_service import AnalysisService, analysis_service
except ImportError:
    pass
