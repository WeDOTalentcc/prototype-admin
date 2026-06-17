import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Integer, Index

from lia_config.database import Base


class TaskRecord(Base):
    __tablename__ = "task_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    domain_id = Column(String(100), nullable=False, index=True)
    action_id = Column(String(100), nullable=False, index=True)
    params = Column(JSON, default=dict)
    priority = Column(Integer, default=1)
    state = Column(String(20), nullable=False, default="queued", index=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=2)
    user_id = Column(String(255), default="")
    tenant_id = Column(String(255), nullable=True, index=True)
    callback = Column(String(500), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)

    __table_args__ = (
        Index("idx_task_records_domain_state", "domain_id", "state"),
        Index("idx_task_records_tenant_state", "tenant_id", "state"),
        Index("idx_task_records_scheduled", "state", "scheduled_at"),
    {"extend_existing": True}, )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "domain_id": self.domain_id,
            "action_id": self.action_id,
            "params": self.params or {},
            "priority": self.priority,
            "state": self.state,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "callback": self.callback,
            "metadata": self.metadata_ or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
        }


class TaskSchedule(Base):
    __tablename__ = "task_schedules"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True)
    domain_id = Column(String(100), nullable=False)
    action_id = Column(String(100), nullable=False)
    params = Column(JSON, default=dict)
    cron_expression = Column(String(100), nullable=False)
    priority = Column(Integer, default=1)
    tenant_id = Column(String(255), nullable=True)
    user_id = Column(String(255), default="system")
    is_active = Column(Boolean, default=True, index=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    run_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=2)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "domain_id": self.domain_id,
            "action_id": self.action_id,
            "params": self.params or {},
            "cron_expression": self.cron_expression,
            "priority": self.priority,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "is_active": self.is_active,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "run_count": self.run_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata_ or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DeadLetterRecord(Base):
    __tablename__ = "dead_letter_queue"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_task_id = Column(String(255), nullable=False, index=True)
    domain_id = Column(String(100), nullable=False)
    action_id = Column(String(100), nullable=False)
    params = Column(JSON, default=dict)
    error = Column(Text, nullable=False)
    retry_count = Column(Integer, default=0)
    original_created_at = Column(DateTime, nullable=True)
    moved_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    tenant_id = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "original_task_id": self.original_task_id,
            "domain_id": self.domain_id,
            "action_id": self.action_id,
            "params": self.params or {},
            "error": self.error,
            "retry_count": self.retry_count,
            "original_created_at": self.original_created_at.isoformat() if self.original_created_at else None,
            "moved_at": self.moved_at.isoformat() if self.moved_at else None,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "tenant_id": self.tenant_id,
            "metadata": self.metadata_ or {},
        }
