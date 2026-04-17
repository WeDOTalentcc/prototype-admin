"""
LangSmith Configuration - Observability for LLM/Agent traces

Configures LangSmith tracing for:
- Orchestrator operations
- Agent executions
- LLM calls (Claude, OpenAI, Gemini)
- Task planning
- Intent routing
"""

import logging
import os

logger = logging.getLogger(__name__)


def configure_langsmith() -> bool:
    """
    Configure LangSmith environment variables for tracing.

    Accepts the API key from either LANGSMITH_API_KEY or LANGCHAIN_API_KEY
    (LANGSMITH_API_KEY takes precedence for backward compatibility).

    Returns:
        bool: True if LangSmith is configured and enabled
    """
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")

    if not langsmith_api_key:
        logger.warning("LangSmith NOT configured (LANGSMITH_API_KEY / LANGCHAIN_API_KEY missing)")
        logger.warning("   LLM/Agent tracing will not be available")
        logger.warning("   Add LANGSMITH_API_KEY (or LANGCHAIN_API_KEY) to Replit Secrets to enable tracing")
        return False

    workspace_id = os.getenv("LANGSMITH_WORKSPACE_ID")

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = os.getenv(
        "LANGSMITH_PROJECT",
        os.getenv("LANGCHAIN_PROJECT", "lia-agent-system"),
    )

    if workspace_id:
        os.environ["LANGSMITH_WORKSPACE_ID"] = workspace_id
        logger.info("LangSmith tracing enabled")
        logger.info("   Project: %s", os.environ["LANGCHAIN_PROJECT"])
        logger.info("   Workspace ID: %s", workspace_id)
        logger.info("   Endpoint: %s", os.environ["LANGCHAIN_ENDPOINT"])
        logger.info("   View traces at: https://smith.langchain.com")
    else:
        logger.info("LangSmith tracing enabled (without workspace_id)")
        logger.info("   Project: %s", os.environ["LANGCHAIN_PROJECT"])
        logger.info("   Endpoint: %s", os.environ["LANGCHAIN_ENDPOINT"])

    return True


def get_langsmith_project() -> str | None:
    """Get current LangSmith project name."""
    return os.getenv("LANGCHAIN_PROJECT")


def is_langsmith_enabled() -> bool:
    """Check if LangSmith tracing is enabled."""
    return os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
