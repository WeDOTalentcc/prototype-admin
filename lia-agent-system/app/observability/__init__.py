"""Observability module — Sentry, LangSmith tracing, OpenTelemetry."""
from __future__ import annotations
import logging
import os

logger = logging.getLogger(__name__)


def init_langsmith() -> bool:
    """Initialize LangSmith tracing if env vars are set.

    UC-P1-06: wraps LangSmith init so all LLM calls via generate_with_fallback
    are traced when LANGSMITH_API_KEY is configured.

    Returns True if LangSmith is active, False otherwise (graceful degradation).
    """
    # Delegate to the canonical langsmith config module
    try:
        from app.config.langsmith import configure_langsmith
        return configure_langsmith()
    except ImportError:
        pass

    # Fallback: minimal inline init
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        logger.info("[LangSmith] LANGSMITH_API_KEY not set — LLM tracing disabled")
        return False
    try:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault(
            "LANGCHAIN_PROJECT",
            os.getenv("LANGSMITH_PROJECT", "lia-agent-system"),
        )
        # Validate the package is installed
        from langsmith import Client  # noqa: F401
        logger.info(
            "[LangSmith] Tracing initialized — project: %s",
            os.getenv("LANGCHAIN_PROJECT"),
        )
        return True
    except ImportError:
        logger.warning("[LangSmith] langsmith package not installed — pip install langsmith")
        return False
    except Exception as exc:
        logger.warning("[LangSmith] Init failed: %s", exc)
        return False


# Called at module import (app startup)
_langsmith_active = init_langsmith()
