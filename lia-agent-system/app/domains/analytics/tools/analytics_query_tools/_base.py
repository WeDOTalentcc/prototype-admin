"""Shared utilities for analytics query tools."""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from app.tools.executor import ToolExecutionContext

logger = logging.getLogger(__name__)


def extract_context(kwargs: dict[str, Any]) -> Optional["ToolExecutionContext"]:
    """Extract and remove _context from kwargs if present."""
    return kwargs.pop("_context", None)


def success_response(message: str, data: Any, **extra) -> dict[str, Any]:
    """Build a standard success response."""
    return {"success": True, "message": message, "data": data, **extra}


def error_response(message: str, error: Exception) -> dict[str, Any]:
    """Build a standard error response."""
    return {"success": False, "message": message, "error": str(error)}


@asynccontextmanager
async def analytics_db():
    """Context manager for analytics DB sessions."""
    from app.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        yield db
