from datetime import datetime
import uuid

from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class PromptVariant(Base):
    __tablename__ = "prompt_variants"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_name = Column(String(255), nullable=False, index=True)
    variant_name = Column(String(100), nullable=False)
    prompt_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    traffic_percentage = Column(Float, default=50.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ABTestResult(Base):
    __tablename__ = "ab_test_results"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_name = Column(String(255), nullable=False, index=True)
    variant_name = Column(String(100), nullable=False)
    session_id = Column(String(255), nullable=False)
    company_id = Column(String(255), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    context = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
