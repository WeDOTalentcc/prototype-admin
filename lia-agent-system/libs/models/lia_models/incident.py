"""
Incident model for LGPD Art.48 compliance.
Tracks data security incidents requiring internal admin notification.
"""
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from sqlalchemy import Column, String, Text, DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class IncidentSeverity(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, PyEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    REPORTED_ANPD = "reported_anpd"  # Manual ANPD notification done


class DataIncident(Base):
    """
    LGPD Art.48: Record of data security incidents.

    Notification flow:
    1. Incident registered here (automated or manual)
    2. Internal admin team alerted via structured CRITICAL log
    3. DPO reviews and decides if ANPD notification needed
    4. Manual ANPD notification done via admin page
    5. Status updated to REPORTED_ANPD
    """
    __tablename__ = "data_incidents"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)  # tenant
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.MEDIUM)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.OPEN)

    # What data was affected
    affected_data_categories = Column(Text, nullable=True)  # JSON list: ["name", "email", "cpf"]
    affected_users_count = Column(String(50), nullable=True)  # estimate: "~500", "unknown"

    # Timeline (LGPD Art.48: 72h window)
    incident_detected_at = Column(DateTime(timezone=True), nullable=False)
    admin_notified_at = Column(DateTime(timezone=True), nullable=True)  # when internal team was alerted
    anpd_reported_at = Column(DateTime(timezone=True), nullable=True)  # when ANPD was manually notified
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Audit
    reported_by = Column(String(255), nullable=True)  # user_id or "system"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
