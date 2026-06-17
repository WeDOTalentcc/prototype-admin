"""
Company Calendar Credentials model.

Armazena credenciais OAuth/Service Account de calendário por empresa.
Suporta Google Calendar e Microsoft Graph.
Credenciais armazenadas criptografadas via Fernet (app/shared/encryption.py).

Criado em Sprint 5 — Google Calendar Integration.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from lia_config.database import Base


class CompanyCalendarCredentials(Base):
    """
    Per-company calendar integration credentials.

    One record per (company_id, provider) pair — unique constraint.
    Providers: 'google' or 'microsoft'.
    """
    __tablename__ = "company_calendar_credentials"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    provider = Column(
        String(20),
        nullable=False,
        comment="Calendar provider: 'google' or 'microsoft'",
    )
    encrypted_credentials = Column(
        Text,
        nullable=False,
        comment="Fernet-encrypted JSON with OAuth tokens or service account key",
    )

    is_active = Column(Boolean, default=True, nullable=False)
    timezone = Column(String(100), default="America/Sao_Paulo", nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<CompanyCalendarCredentials company={self.company_id} provider={self.provider}>"
