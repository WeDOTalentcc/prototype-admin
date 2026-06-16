import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String, Text, select, func, desc
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import AsyncSessionLocal, Base

logger = logging.getLogger(__name__)


class AgentExecutionRecord(Base):
    __tablename__ = "agent_execution_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    domain = Column(String(100), nullable=False)
    agent_class = Column(String(255), nullable=False)
    user_message = Column(Text, nullable=True)
    agent_response = Column(Text, nullable=True)
    total_duration_ms = Column(Float, default=0)
    total_iterations = Column(Integer, default=0)
    tools_called = Column(JSON, default=list)
    tools_succeeded = Column(Integer, default=0)
    tools_failed = Column(Integer, default=0)
    final_confidence = Column(Float, default=0)
    reasoning_chain = Column(JSON, default=list)
    stage_before = Column(String(100), nullable=True)
    stage_after = Column(String(100), nullable=True)
    stage_transitioned = Column(Boolean, default=False)
    model_provider = Column(String(100), default="claude")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    metadata_ = Column("metadata", JSON, nullable=True)


class ExecutionLogStore:

    async def save(self, log_data: dict, company_id: str, user_id: str) -> AgentExecutionRecord:
        async with AsyncSessionLocal() as session:
            record = AgentExecutionRecord(
                session_id=log_data.get("session_id", str(uuid.uuid4())),
                company_id=company_id,
                user_id=user_id,
                domain=log_data.get("domain", "unknown"),
                agent_class=log_data.get("agent_class", "unknown"),
                user_message=log_data.get("user_message"),
                agent_response=log_data.get("agent_response"),
                total_duration_ms=log_data.get("total_duration_ms", 0),
                total_iterations=log_data.get("total_iterations", 0),
                tools_called=log_data.get("tools_called", []),
                tools_succeeded=log_data.get("tools_succeeded", 0),
                tools_failed=log_data.get("tools_failed", 0),
                final_confidence=log_data.get("final_confidence", 0),
                reasoning_chain=log_data.get("iterations", []),
                stage_before=log_data.get("stage_before"),
                stage_after=log_data.get("stage_after"),
                stage_transitioned=log_data.get("stage_transitioned", False),
                model_provider=log_data.get("model_provider", "claude"),
                metadata_=log_data.get("metadata"),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            logger.info(f"Saved execution record for session={record.session_id} domain={record.domain}")
            return record

    async def get_by_session(self, session_id: str, limit: int = 50) -> List[AgentExecutionRecord]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AgentExecutionRecord)
                .where(AgentExecutionRecord.session_id == session_id)
                .order_by(desc(AgentExecutionRecord.created_at))
                .limit(limit)
            )
            return list(result.scalars().all())

    async def get_by_company(self, company_id: str, domain: Optional[str] = None, limit: int = 100) -> List[AgentExecutionRecord]:
        async with AsyncSessionLocal() as session:
            query = select(AgentExecutionRecord).where(
                AgentExecutionRecord.company_id == company_id
            )
            if domain:
                query = query.where(AgentExecutionRecord.domain == domain)
            query = query.order_by(desc(AgentExecutionRecord.created_at)).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_timeline(self, session_id: str) -> List[dict]:
        records = await self.get_by_session(session_id)
        timeline = []
        for record in records:
            chain = record.reasoning_chain or []
            for step in chain:
                timeline.append({
                    "iteration": step.get("iteration", 0),
                    "phase": step.get("phase", "unknown"),
                    "reasoning_summary": (step.get("reasoning") or "")[:200] if step.get("reasoning") else None,
                    "tool_used": step.get("tool_name"),
                    "tool_result_summary": "success" if step.get("tool_success") else ("failed" if step.get("tool_success") is False else None),
                    "decision": step.get("decision"),
                    "duration_ms": step.get("duration_ms", 0),
                    "timestamp": step.get("timestamp"),
                })
        timeline.sort(key=lambda x: (x.get("timestamp") or "", x.get("iteration", 0)))
        return timeline

    async def get_domain_health(self, company_id: str, days: int = 30) -> list:
        """Retorna métricas de saúde por domínio para os últimos N dias."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    AgentExecutionRecord.domain,
                    func.count(AgentExecutionRecord.id).label("total_executions"),
                    func.avg(AgentExecutionRecord.total_duration_ms).label("avg_duration_ms"),
                    func.avg(AgentExecutionRecord.total_iterations).label("avg_iterations"),
                    func.avg(AgentExecutionRecord.final_confidence).label("avg_confidence"),
                    func.sum(AgentExecutionRecord.tools_succeeded).label("total_tools_succeeded"),
                    func.sum(AgentExecutionRecord.tools_failed).label("total_tools_failed"),
                    func.max(AgentExecutionRecord.created_at).label("last_execution"),
                )
                .where(
                    AgentExecutionRecord.company_id == company_id,
                    AgentExecutionRecord.created_at >= cutoff,
                )
                .group_by(AgentExecutionRecord.domain)
            )
            rows = result.all()

        health_data = []
        for row in rows:
            tools_total = (row.total_tools_succeeded or 0) + (row.total_tools_failed or 0)
            tool_failure_rate = (
                round((row.total_tools_failed or 0) / tools_total, 3) if tools_total > 0 else 0.0
            )
            avg_conf = float(row.avg_confidence or 0)
            last_exec = row.last_execution
            days_since = (datetime.now(timezone.utc) - last_exec).days if last_exec else None

            if days_since is None or days_since > 14:
                status = "stale"
            elif tool_failure_rate > 0.30 or avg_conf < 0.50:
                status = "degraded"
            elif tool_failure_rate > 0.10:
                status = "warning"
            else:
                status = "healthy"

            health_data.append({
                "domain": row.domain,
                "total_executions": int(row.total_executions or 0),
                "avg_duration_ms": round(float(row.avg_duration_ms or 0), 1),
                "avg_iterations": round(float(row.avg_iterations or 0), 1),
                "avg_confidence": round(avg_conf, 3),
                "tool_failure_rate": tool_failure_rate,
                "last_execution": last_exec.isoformat() if last_exec else None,
                "days_since_last_execution": days_since,
                "status": status,
            })

        return health_data

    async def get_stats(self, company_id: str) -> dict:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    func.avg(AgentExecutionRecord.final_confidence).label("avg_confidence"),
                    func.avg(AgentExecutionRecord.total_iterations).label("avg_iterations"),
                    func.avg(AgentExecutionRecord.total_duration_ms).label("avg_duration_ms"),
                    func.count(AgentExecutionRecord.id).label("total_executions"),
                    func.sum(AgentExecutionRecord.tools_succeeded).label("total_tools_succeeded"),
                    func.sum(AgentExecutionRecord.tools_failed).label("total_tools_failed"),
                ).where(AgentExecutionRecord.company_id == company_id)
            )
            row = result.one()

            tools_result = await session.execute(
                select(AgentExecutionRecord.tools_called)
                .where(AgentExecutionRecord.company_id == company_id)
                .order_by(desc(AgentExecutionRecord.created_at))
                .limit(500)
            )
            tool_counts: Dict[str, int] = {}
            for (tools,) in tools_result:
                if tools:
                    for tool in tools:
                        tool_counts[tool] = tool_counts.get(tool, 0) + 1

            most_used_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "avg_confidence": round(float(row.avg_confidence or 0), 3),
                "avg_iterations": round(float(row.avg_iterations or 0), 1),
                "avg_duration_ms": round(float(row.avg_duration_ms or 0), 1),
                "total_executions": int(row.total_executions or 0),
                "total_tools_succeeded": int(row.total_tools_succeeded or 0),
                "total_tools_failed": int(row.total_tools_failed or 0),
                "most_used_tools": [{"tool": t, "count": c} for t, c in most_used_tools],
            }
