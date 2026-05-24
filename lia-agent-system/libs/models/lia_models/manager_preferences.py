"""
ManagerPreferences model — learning loop for job creation.

Stores per-manager preferences learned from previous job creation sessions.
Key: (company_id, manager_email) — best-effort identity without FK.

LGPD note: Only professional data stored (corporate email + work preferences).
No sensitive personal data (no race, gender, health, religion).
"""
from __future__ import annotations

from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from lia_config.database import Base


class ManagerPreferences(Base):
    """Learned preferences for a hiring manager within a company."""

    __tablename__ = "manager_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Tenant isolation — always validated from JWT, never from payload
    company_id = Column(String(255), nullable=False, index=True)

    # Best-effort identity: corporate email (may change — workaround without FK)
    manager_email = Column(String(255), nullable=False, index=True)
    manager_name = Column(String(255), nullable=True)

    # ── Learned preferences ───────────────────────────────────────────────────
    preferred_seniorities = Column(ARRAY(String), default=list)
    preferred_departments = Column(ARRAY(String), default=list)
    preferred_work_models = Column(ARRAY(String), default=list)
    # Salary percentile preference: 25 | 50 | 75 | 90
    salary_percentile_preference = Column(Integer, nullable=True)
    # "quick" | "standard" | "detailed"
    screening_style = Column(String(50), default="standard", nullable=False)
    approve_before_publish = Column(Boolean, default=False, nullable=False)

    # ── Learning loop ─────────────────────────────────────────────────────────
    jobs_created_count = Column(Integer, default=0, nullable=False)
    last_job_created_at = Column(DateTime, nullable=True)

    # Audit trail of corrections: {field: {from: x, to: y, count: N}}
    # EU AI Act: kept for explainability, not for candidate ranking
    corrections_log = Column(JSONB, default=dict, nullable=False)

    # ── Idempotency ───────────────────────────────────────────────────────────
    # Prevents double-counting if handoff_node is re-executed by LangGraph
    last_idempotency_key = Column(String(255), nullable=True)

    # ── Audit timestamps ──────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("company_id", "manager_email", name="uq_manager_prefs_company_email"),
    {"extend_existing": True}, )

    def __repr__(self) -> str:
        return (
            f"<ManagerPreferences company={self.company_id!r} "
            f"email={self.manager_email!r} jobs={self.jobs_created_count}>"
        )
