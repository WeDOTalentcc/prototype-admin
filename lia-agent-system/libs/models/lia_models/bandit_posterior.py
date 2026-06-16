"""T-19 Fase 2: BanditPosterior canonical model (ADR-AB-001).

Persiste posteriors (alpha, beta) do Thompson sampler per (test_name, arm).
Resolve gap V4: ThompsonSampler in-memory perde state em restart/multi-instance.

Pattern canonical:
- 1 row per (test_name, arm) — composite UNIQUE
- alpha + beta floats (continuous priors)
- last_updated_at automatically refreshed
- company_id opcional (None = global test cross-tenant)

Refs:
- ADR-AB-001 (T-19 Thompson + FairnessGate canonical)
- ADR-LGPD-001 (aggregates from candidate data — N >= 10 threshold)
- Russo et al. (2018) A Tutorial on Thompson Sampling
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class BanditPosterior(Base):
    """Persisted Bayesian beta posterior canonical (T-19 ADR-AB-001).

    Pattern canonical:
    - test_name = experiment identifier (e.g., "wsi_question_v1_vs_v2")
    - arm = variant identifier (e.g., "control", "variant_b")
    - alpha = successes + 1 (Beta prior shape parameter)
    - beta = failures + 1 (Beta prior rate parameter)
    - n_observations = total samples (successes + failures, audit aid)
    - company_id NULL = global experiment cross-tenant
    """

    __tablename__ = "bandit_posteriors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_name = Column(String(255), nullable=False, index=True)
    arm = Column(String(100), nullable=False)

    alpha = Column(Float, nullable=False, default=1.0)
    beta = Column(Float, nullable=False, default=1.0)
    n_observations = Column(Integer, nullable=False, default=0)

    # Multi-tenancy: NULL = global experiment, UUID = per-company
    # WT-2022 P0.TENANT: TENANT-EXEMPT TENANT-NULLABLE-DELIBERATE - bandit_posteriors aggregated cross-tenant for thompson sampling efficacy (ADR-LGPD-001 anonymization, NULL=global experiment)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Versioning canonical (drift detection se prior schema mudar)
    version = Column(String(20), nullable=False, default="1.0")

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    last_updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        # Composite UNIQUE: 1 posterior per (test, arm, company    {"extend_existing": True},)
        UniqueConstraint(
            "test_name", "arm", "company_id",
            name="uq_bandit_posteriors_test_arm_company",
        ),
        Index(
            "idx_bandit_posteriors_test_lookup",
            "test_name", "company_id",
        ),
    {"extend_existing": True}, )

    def __repr__(self):
        return (
            f"<BanditPosterior {self.test_name}:{self.arm} "
            f"α={self.alpha:.1f} β={self.beta:.1f} n={self.n_observations}>"
        )

    @property
    def expected_value(self) -> float:
        """E[Beta(α, β)] = α / (α + β) — posterior mean (point estimate)."""
        total = self.alpha + self.beta
        return self.alpha / total if total > 0 else 0.5

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "test_name": self.test_name,
            "arm": self.arm,
            "alpha": self.alpha,
            "beta": self.beta,
            "n_observations": self.n_observations,
            "expected_value": self.expected_value,
            "company_id": str(self.company_id) if self.company_id else None,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None,
        }
