"""
Email Template models for managing email communications with candidates.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class EmailTemplate(Base):
    """
    Represents an email/WhatsApp template for candidate communications.
    Templates support variable substitution for personalization.
    """
    __tablename__ = "email_templates"
    __table_args__ = (
        Index('ix_email_templates_company_channel', 'company_id', 'channel'),
    {"extend_existing": True}, )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=True)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    channel = Column(String(20), nullable=False, default="email", index=True)
    situation = Column(String(50), nullable=True, index=True)
    trigger_type = Column(String(20), nullable=True, default="manual")
    used_in = Column(JSONB, default=list)
    priority = Column(String(10), nullable=True, default="medium")
    variables = Column(JSONB, default=list)
    cc_emails = Column(JSONB, nullable=True, default=None)
    is_active = Column(Boolean, default=True, index=True)
    # WT-2022 P0.TENANT: TENANT-EXEMPT - templates podem ser global default (company_id NULL = template padrao WeDOTalent compartilhado entre tenants)
    company_id = Column(String(255), nullable=True, index=True)
    is_system_template = Column(Boolean, default=False, index=True)
    visibility = Column(String(20), nullable=False, default="recruiter", index=True)  # recruiter, admin, all
    origin_template_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    version = Column(Integer, default=1)
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    email_logs = relationship("EmailLog", back_populates="template", lazy="dynamic")
    
    def __repr__(self):
        return f"<EmailTemplate {self.id} - {self.name}>"


class EmailLog(Base):
    """
    Tracks all emails sent through the system.
    Used for auditing and debugging email delivery.
    """
    __tablename__ = "email_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(UUID(as_uuid=True), ForeignKey("email_templates.id"), nullable=True, index=True)
    candidate_id = Column(String(255), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="pending", index=True)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    variables_used = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(255), nullable=True, index=True)
    
    template = relationship("EmailTemplate", back_populates="email_logs")
    
    def __repr__(self):
        return f"<EmailLog {self.id} - {self.recipient_email} ({self.status})>"
