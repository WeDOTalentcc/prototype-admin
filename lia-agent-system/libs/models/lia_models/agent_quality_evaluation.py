"""
AgentQualityEvaluation — Model SQLAlchemy para avaliações de qualidade de agentes.

Tabela: agent_quality_evaluations
Migration: alembic/versions/034_add_agent_quality_evaluations.py
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AgentQualityEvaluation(Base):
    __tablename__ = "agent_quality_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False)
    company_id: Mapped[str] = mapped_column(String(36), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    scores: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_aqe_company_agent", "company_id", "agent_id"),
        Index("ix_aqe_evaluated_at", "evaluated_at"),
    {"extend_existing": True}, )
