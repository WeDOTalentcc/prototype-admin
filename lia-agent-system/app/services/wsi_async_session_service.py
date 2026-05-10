"""Shim: re-exports WSIAsyncSessionService from cv_screening domain.

Tests patch: app.services.wsi_async_session_service.WSIAsyncSessionService.*
The canonical implementation lives in:
  app.domains.cv_screening.services.wsi_async_session_service
"""
from app.domains.cv_screening.services.wsi_async_session_service import (  # noqa: F401
    WSIAsyncSessionService,
    get_wsi_async_session_service,
)

__all__ = ["WSIAsyncSessionService", "get_wsi_async_session_service"]
