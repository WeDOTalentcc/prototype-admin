"""SQLAlchemy model for PoolAgentRun — Sprint 7C Part 1.5a canonical.

Tabela `pool_agent_runs` criada na migration 210.
Cada row representa 1 execução de assignment (cron, on_demand, future event_driven).

Orchestrator real (Part 1.5b) escreve via PoolAgentRunRepository.create + update_status.
Endpoint GET .../runs lê via list_by_assignment.

Multi-tenancy invariant: company_id redundante com assignment.company_id.
Repository enforce em writes; FK CASCADE garante cleanup quando assignment deletado.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from lia_config.database import Base


class PoolAgentRun(Base):
    __tablename__ = "pool_agent_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # C1.4 (2026-05-29): a run is sourced from EITHER a legacy assignment OR an
    # agent_deployment (unified engine, Onda C1). Both nullable; the
    # chk_par_source_present CHECK guarantees at least one is set (fail-closed).
    assignment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pool_agent_assignments.id", ondelete="CASCADE"),
        nullable=True,
    )
    deployment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agent_deployments.id", ondelete="CASCADE"),
        nullable=True,
    )
    company_id = Column(String(64), nullable=False, index=True)

    trigger_source = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default="queued")

    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    dispatch_metadata = Column(JSONB, nullable=False, default=dict)
    results = Column(JSONB, nullable=False, default=dict)
    runtime_metrics = Column(JSONB, nullable=False, default=dict)
    # Onda 1 Fase 2 (2026-05-27): decision tree do agente (AgentReasoningStep[]).
    # Populado em real-time pelo TalentPoolReActAgent.process() via output.reasoning_trace.
    # Consumido pelo Studio Control Room (GET /agent-monitoring/executions/{id}/reasoning).
    reasoning_payload = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)

    # Sprint A (2026-06-13): rastreabilidade cross-domain
    correlation_id = Column(String(80), nullable=True, index=True)

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    assignment = relationship("PoolAgentAssignment", back_populates="runs")

    __table_args__ = (
        CheckConstraint(
            "trigger_source IN ('cron','on_demand','event_driven')",
            name="chk_par_trigger_source",
        ),
        CheckConstraint(
            "status IN ('queued','running','success','error','timeout','cancelled')",
            name="chk_par_status",
        ),
        CheckConstraint(
            "(assignment_id IS NOT NULL) OR (deployment_id IS NOT NULL)",
            name="chk_par_source_present",
        ),
        Index("idx_pool_agent_runs_assignment", "assignment_id", "created_at"),
        Index("idx_pool_agent_runs_deployment", "deployment_id", "created_at"),
        Index("idx_pool_agent_runs_company_status", "company_id", "status"),
        # C5.2 (2026-05-29): composite (company_id, started_at DESC) for the
        # active-summary / recent-executions sort. Migration 223.
        Index(
            "idx_pool_agent_runs_company_started",
            "company_id",
            started_at.desc(),
        ),
        # C5.1 (2026-05-29): GIN on results->'candidate_ids' so the
        # /candidate/{id}/touches endpoint can move from a Python-side O(N) scan
        # to an index-backed containment query (`results -> 'candidate_ids' @> :jsonb`)
        # when the endpoint is later optimized (endpoint owned by C4.2). Migration 223.
        Index(
            "idx_pool_agent_runs_results_candidate_ids",
            text("(results -> 'candidate_ids')"),
            postgresql_using="gin",
        ),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return (
            f"<PoolAgentRun id={self.id} assignment={self.assignment_id} "
            f"status={self.status} trigger={self.trigger_source}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "assignment_id": str(self.assignment_id) if self.assignment_id else None,
            "deployment_id": str(self.deployment_id) if self.deployment_id else None,
            "company_id": self.company_id,
            "trigger_source": self.trigger_source,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "dispatch_metadata": self.dispatch_metadata or {},
            "results": self.results or {},
            "runtime_metrics": self.runtime_metrics or {},
            "reasoning_payload": self.reasoning_payload,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
