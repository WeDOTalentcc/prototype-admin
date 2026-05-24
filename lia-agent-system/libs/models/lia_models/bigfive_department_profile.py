"""BigFiveDepartmentProfile - Department-level Big Five running averages per company.

Stores aggregated trait scores learned from confirmed hires grouped by
(company_id, department, seniority_level). Used as Layer 4 in the hybrid
BigFive blend formula when sample_count >= 10 and toggle is ON.

Stability semantics: alto = bom (consistente com CompanyCultureProfile.stability_score).
Multi-tenancy: company_id NOT NULL, indexed, never trusted from payload.
LGPD: no PII stored - only aggregated scores (no individual candidate data).
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class BigFiveDepartmentProfile(Base):
    """Running average Big Five scores per (company, department, seniority).

    Stability semantics: 0.0-1.0, alto = estavel/bom. Alinhado com
    CompanyCultureProfile.stability_score (que usa 0-100 mas significa o mesmo).

    Updated incrementally via record_hire() with temporal decay for
    entries older than 18 months (lambda=0.05).

    Minimum 10 samples required before this profile activates as Layer 4.
    """
    __tablename__ = "bigfive_department_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy - NOT NULL, validated from JWT context (never payload)
    company_id = Column(String(255), nullable=False, index=True)

    department = Column(String(100), nullable=False)
    seniority_level = Column(String(50), nullable=False)

    # Running average sample count - minimum 10 to activate Layer 4
    sample_count = Column(Integer, default=0, nullable=False)

    # Big Five trait averages (0.0-1.0, alto = melhor pra todas)
    openness_score = Column(Float, nullable=True)
    conscientiousness_score = Column(Float, nullable=True)
    extraversion_score = Column(Float, nullable=True)
    agreeableness_score = Column(Float, nullable=True)
    # Stability (em vez de Neuroticism) para consistencia com CompanyCultureProfile.
    # Alto = estavel/bom. Inverso de neuroticism (alto = neurotico/ruim).
    stability_score = Column(Float, nullable=True)

    last_updated_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index(
            "ix_bigfive_dept_company_dept_seniority",
            "company_id",
            "department",
            "seniority_level",
            unique=True,
        ),
    {"extend_existing": True}, )

    def __repr__(self):
        return (
            f"<BigFiveDepartmentProfile company={self.company_id} "
            f"dept={self.department} seniority={self.seniority_level} "
            f"n={self.sample_count}>"
        )
