"""
LangSmith Configuration - Observability for LLM/Agent traces

Configures LangSmith tracing for:
- Orchestrator operations
- Agent executions
- LLM calls (Claude, OpenAI)
- Task planning
- Intent routing
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def configure_langsmith() -> bool:
    """
    Configure LangSmith environment variables for tracing.
    
    Returns:
        bool: True if LangSmith is configured and enabled
    """
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    
    if not langsmith_api_key:
        logger.warning("⚠️  LangSmith NOT configured (LANGSMITH_API_KEY missing)")
        logger.warning("   LLM/Agent tracing will not be available")
        logger.warning("   Add LANGSMITH_API_KEY to Replit Secrets to enable tracing")
        return False
    
    # For org-scoped API keys, workspace_id is REQUIRED
    workspace_id = os.getenv("LANGSMITH_WORKSPACE_ID")
    
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "lia-agent-system")
    
    if workspace_id:
        os.environ["LANGSMITH_WORKSPACE_ID"] = workspace_id
        logger.info("✅ LangSmith tracing enabled")
        logger.info(f"   Project: {os.environ['LANGCHAIN_PROJECT']}")
        logger.info(f"   Workspace ID: {workspace_id}")
        logger.info(f"   Endpoint: {os.environ['LANGCHAIN_ENDPOINT']}")
        logger.info("   View traces at: https://smith.langchain.com")
    else:
        # Workspace ID not provided - tracing may fail for org-scoped keys
        logger.warning("⚠️  LangSmith configured WITHOUT workspace_id")
        logger.warning("   If using org-scoped API key, tracing will fail at runtime")
        logger.warning("   Add LANGSMITH_WORKSPACE_ID to Replit Secrets to fix")
        logger.info("✅ LangSmith tracing enabled (without workspace_id)")
        logger.info(f"   Project: {os.environ['LANGCHAIN_PROJECT']}")
        logger.info(f"   Endpoint: {os.environ['LANGCHAIN_ENDPOINT']}")
    
    return True


def get_langsmith_project() -> Optional[str]:
    """Get current LangSmith project name."""
    return os.getenv("LANGCHAIN_PROJECT")


def is_langsmith_enabled() -> bool:
    """Check if LangSmith tracing is enabled."""
    return os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
