"""
UserAgentPreference — Model SQLAlchemy para preferências de auto_confirm por usuário.

Tabela: user_agent_preferences
Migration: alembic/versions/035_add_user_agent_preferences.py
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserAgentPreference(Base):
    __tablename__ = "user_agent_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    company_id: Mapped[str] = mapped_column(String(36), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    auto_confirm: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "company_id", "domain", "action_type",
                         name="uq_user_agent_pref"),
        Index("ix_uap_user_company", "user_id", "company_id"),
    {"extend_existing": True}, )
