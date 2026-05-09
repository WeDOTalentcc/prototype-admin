"""
LangChain callbacks for PII stripping and audit logging.

Used by llm_service.get_audited_model() to wrap ChatAnthropic/ChatOpenAI
with PII protection and structured audit logging on every LLM call.

# R-054: canonical callbacks — app/shared/observability/callbacks.py is an
# identical duplicate with no callers. That file should be deleted.
"""
import logging
import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult

from app.shared.pii_masking import strip_pii_for_llm_prompt

logger = logging.getLogger(__name__)


class PIIStripCallback(AsyncCallbackHandler):
    """Strip PII from messages before they reach the LLM."""

    async def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        """Strip PII from all message contents before sending to LLM."""
        for message_batch in messages:
            for msg in message_batch:
                if isinstance(msg.content, str) and msg.content:
                    msg.content = strip_pii_for_llm_prompt(msg.content)
                elif isinstance(msg.content, list):
                    for i, block in enumerate(msg.content):
                        if isinstance(block, dict) and block.get("type") == "text":
                            block["text"] = strip_pii_for_llm_prompt(block.get("text", ""))


class AuditLogCallback(AsyncCallbackHandler):
    """Log all LLM calls with provider, model, latency, and tenant info."""

    def __init__(self, tenant_id: str = "", caller: str = ""):
        super().__init__()
        self.tenant_id = tenant_id
        self.caller = caller
        self._start_times: dict[UUID, float] = {}

    async def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[BaseMessage]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._start_times[run_id] = time.monotonic()

    async def on_llm_end(
        self, response: LLMResult, *, run_id: UUID, **kwargs: Any
    ) -> None:
        elapsed = time.monotonic() - self._start_times.pop(run_id, time.monotonic())
        latency_ms = round(elapsed * 1000)
        model = response.llm_output.get("model_name", "") if response.llm_output else ""
        logger.info(
            "[LLM-AUDIT] provider=langchain-chain model=%s latency_ms=%d tenant=%s caller=%s",
            model, latency_ms, self.tenant_id or "default", self.caller,
        )

    async def on_llm_error(
        self, error: BaseException, *, run_id: UUID, **kwargs: Any
    ) -> None:
        elapsed = time.monotonic() - self._start_times.pop(run_id, time.monotonic())
        latency_ms = round(elapsed * 1000)
        logger.warning(
            "[LLM-AUDIT] provider=langchain-chain ERROR=%s latency_ms=%d tenant=%s caller=%s",
            type(error).__name__, latency_ms, self.tenant_id or "default", self.caller,
        )
