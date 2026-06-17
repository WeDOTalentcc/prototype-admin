"""
Communication Settings Model - Company-level communication configurations.

Stores settings for email signatures, LGPD sending hours, message limits,
and candidate consent tracking.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid

from lia_config.database import Base


class CommunicationSettings(Base):
    """
    Company communication settings.
    
    Stores:
    - Email signature configuration
    - LGPD-compliant sending hours
    - Message rate limits
    - Default channel preferences
    """
    __tablename__ = "communication_settings"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, unique=True, index=True)
    
    signature = Column(Text, nullable=True)
    signature_html = Column(Text, nullable=True)
    
    sending_hours_start = Column(Integer, default=8)
    sending_hours_end = Column(Integer, default=20)
    respect_holidays = Column(Boolean, default=True)
    respect_weekends = Column(Boolean, default=True)
    timezone = Column(String(50), default="America/Sao_Paulo")
    
    max_messages_per_day = Column(Integer, default=3)
    max_messages_per_candidate = Column(Integer, default=5)
    cooldown_hours_between_messages = Column(Integer, default=24)
    
    lgpd_compliant = Column(Boolean, default=True)
    require_consent_before_contact = Column(Boolean, default=True)
    auto_unsubscribe_after_days = Column(Integer, default=90)
    
    default_email_from_name = Column(String(255), nullable=True)
    default_reply_to = Column(String(255), nullable=True)
    
    mailgun_enabled = Column("mailgun_enabled", Boolean, default=True)
    twilio_enabled = Column(Boolean, default=False)
    # P0-W1-06: Ghost-setting fix — tenant opt-out toggle for job alert generation.
    # Default True (alerts enabled). When False, check_all_alerts() is a no-op for this tenant.
    alerts_enabled = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CommunicationSettings {self.id} - company: {self.company_id}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "signature": self.signature,
            "signature_html": self.signature_html,
            "sending_hours_start": self.sending_hours_start,
            "sending_hours_end": self.sending_hours_end,
            "respect_holidays": self.respect_holidays,
            "respect_weekends": self.respect_weekends,
            "timezone": self.timezone,
            "max_messages_per_day": self.max_messages_per_day,
            "max_messages_per_candidate": self.max_messages_per_candidate,
            "cooldown_hours_between_messages": self.cooldown_hours_between_messages,
            "lgpd_compliant": self.lgpd_compliant,
            "require_consent_before_contact": self.require_consent_before_contact,
            "auto_unsubscribe_after_days": self.auto_unsubscribe_after_days,
            "default_email_from_name": self.default_email_from_name,
            "default_reply_to": self.default_reply_to,
            "mailgun_enabled": self.mailgun_enabled,
            "twilio_enabled": self.twilio_enabled,
            "alerts_enabled": self.alerts_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LGPDConsent(Base):
    """
    LGPD Consent tracking for candidates.
    
    Records consent given/revoked for different communication types.
    Required for LGPD compliance in Brazil.
    """
    __tablename__ = "lgpd_consents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    candidate_id = Column(String(255), nullable=False, index=True)
    candidate_email = Column(String(255), nullable=True)
    candidate_phone = Column(String(50), nullable=True)
    
    consent_type = Column(String(50), nullable=False, index=True)
    
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime, nullable=True)
    consent_source = Column(String(100), nullable=True)
    consent_text = Column(Text, nullable=True)
    
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(255), nullable=True)
    revoke_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_lgpd_company_candidate', 'company_id', 'candidate_id'),
        Index('idx_lgpd_consent_type', 'company_id', 'consent_type'),
        Index('idx_lgpd_consent_given', 'company_id', 'consent_given'),
        UniqueConstraint('company_id', 'candidate_id', 'consent_type', name='uq_lgpd_consent_unique'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<LGPDConsent {self.id} - {self.consent_type} - given: {self.consent_given}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "candidate_email": self.candidate_email,
            "candidate_phone": self.candidate_phone,
            "consent_type": self.consent_type,
            "consent_given": self.consent_given,
            "consent_date": self.consent_date.isoformat() if self.consent_date else None,
            "consent_source": self.consent_source,
            "consent_text": self.consent_text,
            "ip_address": self.ip_address,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revoked_by": self.revoked_by,
            "revoke_reason": self.revoke_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ConsentType:
    """Enum-like class for consent types."""
    EMAIL_MARKETING = "email_marketing"
    EMAIL_TRANSACTIONAL = "email_transactional"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    SCREENING = "screening"
    DATA_STORAGE = "data_storage"
    DATA_SHARING = "data_sharing"
    PROCESS_PARTICIPATION = "process_participation"
    # F7 — LGPD: consentimentos específicos para provedores de comunicação e IA
    DATA_SHARING_EMAIL_PROVIDERS = "data_sharing_email_providers"   # Mailgun, Resend
    DATA_SHARING_SMS_PROVIDERS = "data_sharing_sms_providers"       # Twilio
    AI_GENERATED_COMMUNICATIONS = "ai_generated_communications"     # LIA gera mensagens


DEFAULT_COMMUNICATION_SETTINGS = {
    "signature": """{{recrutador_nome}} | {{cargo}}
{{empresa_nome}}
📧 {{email}} | 📱 {{telefone}}
🌐 {{website}}""",
    "signature_html": None,
    "sending_hours_start": 8,
    "sending_hours_end": 20,
    "respect_holidays": True,
    "respect_weekends": True,
    "timezone": "America/Sao_Paulo",
    "max_messages_per_day": 3,
    "max_messages_per_candidate": 5,
    "cooldown_hours_between_messages": 24,
    "lgpd_compliant": True,
    "require_consent_before_contact": True,
    "auto_unsubscribe_after_days": 90,
    "default_email_from_name": None,
    "default_reply_to": None,
    "mailgun_enabled": True,
    "twilio_enabled": False,
}
