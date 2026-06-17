"""
BiasAuditSnapshot — G.4

Persiste snapshots históricos de auditoria de viés para rastreabilidade SOX/ISO 27001.
Cada chamada ao endpoint /bias-audit/job/{job_id} gera um snapshot.

Referências:
- dei-fairness §4 (Four-Fifths Rule)
- SOX: trilha de auditoria histórica obrigatória
- LGPD: apenas dados agregados (sem PII)
"""
import json
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class BiasAuditSnapshot(Base):
    """
    Snapshot histórico de auditoria de viés para uma vaga.

    Armazena dados agregados das 4 dimensões (gender, age_group, disability, region)
    no momento em que a auditoria foi executada.
    Não contém IDs individuais de candidatos (LGPD-safe).
    """
    __tablename__ = "bias_audit_snapshots"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_id = Column(String(36), nullable=False, index=True)
    evaluated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_candidates = Column(Integer, nullable=False, default=0)
    has_alerts = Column(Boolean, nullable=False, default=False)
    dimensions_json = Column(Text, nullable=False)  # JSON das 4 dimensões
    disparate_impact_data = Column(JSON, nullable=True)  # D3: chi-square por dimensão
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        """Serializa snapshot para resposta de API."""
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "job_id": self.job_id,
            "evaluated_at": self.evaluated_at.isoformat() if self.evaluated_at else None,
            "total_candidates": self.total_candidates,
            "has_alerts": self.has_alerts,
            "dimensions": json.loads(self.dimensions_json) if self.dimensions_json else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
