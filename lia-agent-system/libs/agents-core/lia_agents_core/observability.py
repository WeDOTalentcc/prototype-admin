import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from datetime import datetime, timezone
from lia_config.config import settings

logger = logging.getLogger("lia.agents.observability")


@dataclass
class IterationLog:
    iteration: int
    timestamp: str
    phase: str
    duration_ms: float
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    tool_success: Optional[bool] = None
    reasoning: Optional[str] = None
    observation: Optional[str] = None
    decision: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AgentExecutionLog:
    session_id: str
    domain: str
    agent_class: str
    start_time: str
    company_id: Optional[str] = None
    user_id: Optional[str] = None
    end_time: Optional[str] = None
    total_duration_ms: float = 0
    total_iterations: int = 0
    tools_called: list = field(default_factory=list)
    tools_succeeded: int = 0
    tools_failed: int = 0
    final_confidence: float = 0
    stage_before: Optional[str] = None
    stage_after: Optional[str] = None
    stage_transitioned: bool = False
    user_message_length: int = 0
    response_length: int = 0
    model_provider: str = "claude"
    iterations: list = field(default_factory=list)
    error: Optional[str] = None


class ReActObserver:
    """Observes and logs ReAct loop execution for telemetry and debugging."""

    def __init__(
        self,
        session_id: str,
        domain: str,
        agent_class: str,
        company_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        self.log = AgentExecutionLog(
            session_id=session_id,
            domain=domain,
            agent_class=agent_class,
            start_time=datetime.now(timezone.utc).isoformat(),
            company_id=company_id,
            user_id=user_id,
        )
        self.company_id = company_id
        self.user_id = user_id
        self._iteration_start: Optional[float] = None
        self._start_time = time.time()

    def start_iteration(self, iteration: int):
        self._iteration_start = time.time()
        self.log.total_iterations = iteration

    def log_reasoning(self, iteration: int, reasoning: str):
        elapsed = (time.time() - self._iteration_start) * 1000 if self._iteration_start else 0
        entry = IterationLog(
            iteration=iteration,
            timestamp=datetime.now(timezone.utc).isoformat(),
            phase="reason",
            duration_ms=round(elapsed, 2),
            reasoning=reasoning if reasoning else None,
        )
        self.log.iterations.append(asdict(entry))
        logger.debug(
            "ReAct reasoning phase",
            extra={"iteration": iteration, "duration_ms": round(elapsed, 2)},
        )

    def log_tool_call(
        self,
        iteration: int,
        tool_name: str,
        tool_args: dict,
        success: bool,
        duration_ms: float,
    ):
        self.log.tools_called.append(tool_name)
        if success:
            self.log.tools_succeeded += 1
        else:
            self.log.tools_failed += 1

        entry = IterationLog(
            iteration=iteration,
            timestamp=datetime.now(timezone.utc).isoformat(),
            phase="act",
            duration_ms=round(duration_ms, 2),
            tool_name=tool_name,
            tool_args=tool_args,
            tool_success=success,
        )
        self.log.iterations.append(asdict(entry))
        logger.debug(
            "ReAct tool call",
            extra={
                "iteration": iteration,
                "tool_name": tool_name,
                "success": success,
                "duration_ms": round(duration_ms, 2),
            },
        )

    def log_decision(self, iteration: int, decision: str):
        elapsed = (time.time() - self._iteration_start) * 1000 if self._iteration_start else 0
        entry = IterationLog(
            iteration=iteration,
            timestamp=datetime.now(timezone.utc).isoformat(),
            phase="decide",
            duration_ms=round(elapsed, 2),
            decision=decision,
        )
        self.log.iterations.append(asdict(entry))
        logger.debug(
            "ReAct decision",
            extra={"iteration": iteration, "decision": decision},
        )

    def finalize(
        self,
        confidence: float,
        response_length: int,
        stage_after: Optional[str] = None,
        error: Optional[str] = None,
    ) -> dict:
        self.log.end_time = datetime.now(timezone.utc).isoformat()
        self.log.total_duration_ms = round((time.time() - self._start_time) * 1000, 2)
        self.log.final_confidence = confidence
        self.log.response_length = response_length
        self.log.stage_after = stage_after
        self.log.error = error
        if stage_after and stage_after != self.log.stage_before:
            self.log.stage_transitioned = True

        result = asdict(self.log)
        logger.info(
            "ReAct execution complete",
            extra={"agent_telemetry": result},
        )
        return result
