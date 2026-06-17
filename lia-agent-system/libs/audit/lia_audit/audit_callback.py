"""
AuditCallback — LangGraph/LangChain BaseCallbackHandler para auditoria automática.

Captura automaticamente toda execução de agente:
- Chamadas LLM (prompt preview, resposta, tokens, latência)
- Chamadas de tools (input, output, latência, sucesso/erro)
- Transições entre nós de StateGraph

Nenhum agente precisa saber que está sendo auditado.
O callback é injetado via config["callbacks"] no momento da execução.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from lia_audit.audit_models import ExecutionAuditRecord, RequestCostRecord

logger = logging.getLogger(__name__)

_MODEL_PRICING_PER_1K: Dict[str, Dict[str, float]] = {
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}

_DEFAULT_PRICING = {"input": 0.003, "output": 0.015}


def _estimate_cost(model: Optional[str], tokens_input: int, tokens_output: int) -> float:
    pricing = _DEFAULT_PRICING
    if model:
        model_lower = model.lower()
        for key, price in _MODEL_PRICING_PER_1K.items():
            if key in model_lower:
                pricing = price
                break
    return (tokens_input / 1000.0) * pricing["input"] + (tokens_output / 1000.0) * pricing["output"]


try:
    from langchain_core.callbacks import BaseCallbackHandler
    _HAS_LANGCHAIN = True
except ImportError:
    _HAS_LANGCHAIN = False

    class BaseCallbackHandler:  # type: ignore[no-redef]
        def on_chain_start(self, *a, **kw): pass
        def on_chain_end(self, *a, **kw): pass
        def on_llm_start(self, *a, **kw): pass
        def on_llm_end(self, *a, **kw): pass
        def on_tool_start(self, *a, **kw): pass
        def on_tool_end(self, *a, **kw): pass
        def on_tool_error(self, *a, **kw): pass


class AuditCallback(BaseCallbackHandler):
    """
    Callback handler que grava automaticamente toda execução de agente.

    Compatível com:
    - LangGraph StateGraph (callbacks injetados via config)
    - LangChain chains e agents
    - ReAct loop custom (métodos manuais on_*_manual)
    """

    def __init__(
        self,
        user_id: str,
        company_id: str,
        session_id: str,
        domain: str = "unknown",
        agent_type: str = "react",
        request_id: Optional[str] = None,
    ):
        if _HAS_LANGCHAIN:
            super().__init__()
        self.execution_id = str(uuid4())
        self.request_id = request_id or str(uuid4())
        self.user_id = user_id
        self.company_id = company_id
        self.session_id = session_id
        self.domain = domain
        self.agent_type = agent_type
        self.entries: List[Dict[str, Any]] = []
        self._start_time: Optional[datetime] = None
        self._current_llm_start: Optional[datetime] = None
        self._current_tool_start: Optional[datetime] = None
        self._current_tool_name: Optional[str] = None
        self._nodes_visited: List[str] = []
        self._final_confidence: float = 0.0
        # Sprint C #37 fix: capture the main event loop at construction time
        # so persistence can be scheduled even when LangChain calls the
        # callback from a ThreadPoolExecutor worker thread.
        try:
            self._main_loop: Optional[asyncio.AbstractEventLoop] = asyncio.get_running_loop()
        except RuntimeError:
            self._main_loop = None

    def on_chain_start(self, serialized: Dict, inputs: Any, **kwargs: Any) -> None:
        if self._start_time is None:
            self._start_time = datetime.now(timezone.utc)
        node_name = (serialized or {}).get("name") or (serialized or {}).get("id", [None])[-1]
        if node_name and node_name not in ("RunnableSequence", "RunnableLambda"):
            self._nodes_visited.append(str(node_name))

    def on_llm_start(self, serialized: Dict, prompts: List[str], **kwargs: Any) -> None:
        self._current_llm_start = datetime.now(timezone.utc)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        latency = self._elapsed_ms(self._current_llm_start)
        try:
            llm_output = getattr(response, "llm_output", None) or {}
            token_usage = llm_output.get("token_usage", {}) if llm_output else {}
            first_gen = ""
            if response.generations:
                first_gen = (response.generations[0][0].text or "")[:500]
            prompts = kwargs.get("prompts") or []
            prompt_preview = str(prompts[0])[:500] if prompts else ""
            self.entries.append({
                "type": "llm_call",
                "timestamp": (self._current_llm_start or datetime.now(timezone.utc)).isoformat(),
                "model": llm_output.get("model_name") if llm_output else None,
                "prompt_preview": prompt_preview,
                "response_preview": first_gen,
                "tokens_input": token_usage.get("prompt_tokens"),
                "tokens_output": token_usage.get("completion_tokens"),
                "tokens_total": token_usage.get("total_tokens"),
                "latency_ms": latency,
            })
        except Exception as exc:
            logger.debug("[AuditCallback] on_llm_end parse error: %s", exc)

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        latency = self._elapsed_ms(self._current_llm_start)
        self.entries.append({
            "type": "llm_call",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(error),
            "latency_ms": latency,
            "success": False,
        })

    def on_tool_start(self, serialized: Dict, input_str: str, **kwargs: Any) -> None:
        self._current_tool_start = datetime.now(timezone.utc)
        self._current_tool_name = (serialized or {}).get("name", "unknown")

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        latency = self._elapsed_ms(self._current_tool_start)
        self.entries.append({
            "type": "tool_call",
            "timestamp": (self._current_tool_start or datetime.now(timezone.utc)).isoformat(),
            "tool": self._current_tool_name or "unknown",
            "input_preview": str(kwargs.get("input_str", ""))[:500],
            "output_preview": str(output)[:500],
            "latency_ms": latency,
            "success": True,
        })

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        latency = self._elapsed_ms(self._current_tool_start)
        self.entries.append({
            "type": "tool_call",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": self._current_tool_name or "unknown",
            "error": str(error),
            "latency_ms": latency,
            "success": False,
        })

    def on_chain_end(self, outputs: Any, **kwargs: Any) -> None:
        self._schedule_persist(success=True)

    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        self._schedule_persist(success=False, error=str(error))

    # ------------------------------------------------------------------
    # API manual — para react_loop.py custom
    # ------------------------------------------------------------------

    def on_chain_start_manual(self) -> None:
        self._start_time = datetime.now(timezone.utc)

    def on_llm_call(
        self,
        prompt_preview: str,
        response_preview: str,
        latency_ms: float,
        model: Optional[str] = None,
        tokens_total: Optional[int] = None,
        prompt_full: Optional[str] = None,
        reasoning_full: Optional[str] = None,
    ) -> None:
        entry: dict = {
            "type": "llm_call",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "prompt_preview": prompt_preview[:500],
            "response_preview": response_preview[:500],
            "tokens_total": tokens_total,
            "latency_ms": latency_ms,
        }
        if prompt_full is not None:
            entry["prompt_full"] = prompt_full
        if reasoning_full is not None:
            entry["reasoning_full"] = reasoning_full
        self.entries.append(entry)

    def on_tool_call(
        self,
        tool_name: str,
        input_preview: str,
        output_preview: str,
        latency_ms: float,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        self.entries.append({
            "type": "tool_call",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tool": tool_name,
            "input_preview": input_preview[:500],
            "output_preview": output_preview[:500],
            "latency_ms": latency_ms,
            "success": success,
            "error": error,
        })

    async def on_chain_end_manual(
        self,
        confidence: float = 0.0,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        self._final_confidence = confidence
        await self._persist(success=success, error=error)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _elapsed_ms(self, start: Optional[datetime]) -> float:
        if start is None:
            return 0.0
        return (datetime.now(timezone.utc) - start).total_seconds() * 1000

    def _build_record(self, success: bool, error: Optional[str] = None) -> ExecutionAuditRecord:
        now = datetime.now(timezone.utc)
        start = self._start_time or now
        duration_ms = (now - start).total_seconds() * 1000
        tools_used = list({e["tool"] for e in self.entries if e.get("type") == "tool_call" and e.get("success")})

        llm_entries = [e for e in self.entries if e.get("type") == "llm_call"]
        tool_entries = [e for e in self.entries if e.get("type") == "tool_call"]
        tokens_input = sum(e.get("tokens_input") or 0 for e in llm_entries)
        tokens_output = sum(e.get("tokens_output") or 0 for e in llm_entries)
        tokens_total = sum(e.get("tokens_total") or 0 for e in llm_entries)
        model = llm_entries[-1].get("model") if llm_entries else None

        estimated_cost = _estimate_cost(model, tokens_input, tokens_output)

        request_cost = RequestCostRecord(
            request_id=self.request_id,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
            estimated_cost_usd=estimated_cost,
            model=model,
            llm_calls=len(llm_entries),
            tool_calls=len(tool_entries),
        )

        return ExecutionAuditRecord(
            execution_id=self.execution_id,
            session_id=self.session_id,
            user_id=self.user_id,
            company_id=self.company_id,
            domain=self.domain,
            agent_type=self.agent_type,
            start_time=start.isoformat(),
            end_time=now.isoformat(),
            total_duration_ms=duration_ms,
            success=success,
            confidence=self._final_confidence,
            tools_used=tools_used,
            nodes_visited=list(dict.fromkeys(self._nodes_visited)),
            error=error,
            request_id=self.request_id,
            request_cost=request_cost,
            entries=self.entries,
        )

    def _schedule_persist(self, success: bool, error: Optional[str] = None) -> None:
        # Sprint C #37 fix: schedule persistence robustly across threads.
        # LangChain may invoke callbacks from ThreadPoolExecutor workers
        # (e.g. tool nodes). Those threads don't have a running event loop,
        # so we must use run_coroutine_threadsafe against the main loop
        # captured in __init__.
        coro = self._persist(success=success, error=error)
        try:
            running = asyncio.get_running_loop()
            running.create_task(coro)
            return
        except RuntimeError:
            pass
        main = self._main_loop
        if main is not None and main.is_running():
            try:
                asyncio.run_coroutine_threadsafe(coro, main)
                return
            except Exception as exc:  # pragma: no cover — defensive
                logger.warning(
                    "[AuditCallback] run_coroutine_threadsafe falhou (exec=%s): %s",
                    self.execution_id, exc,
                )
        # No loop available — drop with a warning, don't crash the agent turn.
        logger.warning(
            "[AuditCallback] persistência ignorada — nenhum event loop disponível (exec=%s)",
            self.execution_id,
        )
        # Best-effort: close the coroutine so we don't leak warnings.
        try:
            coro.close()
        except Exception:
            pass

    async def _persist(self, success: bool, error: Optional[str] = None) -> None:
        try:
            from lia_audit.audit_writer import get_audit_writer
            record = self._build_record(success=success, error=error)
            await get_audit_writer().persist(record)
            logger.debug(
                "[AuditCallback] Execução persistida: exec=%s domain=%s duration=%.0fms",
                self.execution_id, self.domain, record.total_duration_ms,
            )
        except Exception as exc:
            logger.error("[AuditCallback] Falha na persistência (exec=%s): %s", self.execution_id, exc)
