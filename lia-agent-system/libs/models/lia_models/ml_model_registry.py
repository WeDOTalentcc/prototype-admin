"""
MLModelRegistryRecord — Persistência de modelos ML no PostgreSQL.

Tabela: ml_model_registry
Migration: alembic/versions/077_ml_model_registry.py
Item: PX08-075 (Sprint 11, item 11.5)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Index, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MLModelRegistryRecord(Base):
    __tablename__ = "ml_model_registry"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    model_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active, inactive, training
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # JSON fields
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    features: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Performance tracking
    predictions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    correct_predictions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_error: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_evaluated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Training metadata
    training_samples: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Tenant isolation
    company_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        Index("ix_mlreg_name_version_company", "name", "version", "company_id", unique=True),
        Index("ix_mlreg_name_default", "name", "is_default"),
        Index("ix_mlreg_company", "company_id"),
        Index("ix_mlreg_status", "status"),
    {"extend_existing": True}, )
