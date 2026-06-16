"""WsiQuestionEffectiveness model - Sprint B Phase 3.

Aprende discrimination_score por (company, skill_probed, dept, seniority).
Welford incremental: mantem mean + M2 (sum of squared deltas) sem ter que
reler historico.

Multi-tenancy: company_id NOT NULL, indexed.
LGPD: armazena apenas medias agregadas + counts (zero PII).
ADR-002: model em lia_models.
"""
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class WsiQuestionEffectiveness(Base):
    """Effectiveness por skill (hierarquia 2 niveis: filho + parent rollup).

    Welford running stats:
      mean_score_hired = mean atual dos scores de candidatos contratados
      m2_score_hired = sum((x - mean)^2) - usado pra std calc
      std_hired = sqrt(m2_hired / (times_hired - 1))

    discrimination_score = (mean_hired - mean_rejected) / std_total
      - Alto absoluto -> skill discrimina
      - Sinal positivo -> contratados pontuam mais
      - Threshold pratico: |disc| >= 0.5 = skill util
    """
    __tablename__ = "wsi_question_effectiveness"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy + chave hierarquica
    company_id = Column(String(255), nullable=False, index=True)
    skill_probed = Column(String(100), nullable=False)
    parent_id = Column(String(100), nullable=False, index=True)  # denormalizado

    department = Column(String(100), nullable=False, default="")
    seniority_level = Column(String(50), nullable=False, default="")

    # Counts
    times_used = Column(Integer, nullable=False, default=0)
    times_hired = Column(Integer, nullable=False, default=0)
    times_rejected = Column(Integer, nullable=False, default=0)

    # Welford running stats - hired
    mean_score_hired = Column(Float, nullable=False, default=0.0)
    m2_score_hired = Column(Float, nullable=False, default=0.0)

    # Welford running stats - rejected
    mean_score_rejected = Column(Float, nullable=False, default=0.0)
    m2_score_rejected = Column(Float, nullable=False, default=0.0)

    # Computed (cached - recomputed on each outcome)
    discrimination_score = Column(Float, nullable=False, default=0.0)

    # Fairness audit (Phase 2.5 - populado por batch externo)
    adverse_impact_score = Column(Float, nullable=False, default=0.0)
    fairness_blocked = Column(Integer, nullable=False, default=0)  # 0/1 boolean

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_outcome_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index(
            "ix_wsi_eff_unique",
            "company_id", "skill_probed", "department", "seniority_level",
            unique=True,
        ),
        Index("ix_wsi_eff_parent_lookup", "company_id", "parent_id"),
    {"extend_existing": True}, )

    def __repr__(self):
        return (
            f"<WsiEffectiveness company={self.company_id} "
            f"skill={self.skill_probed} n={self.times_used} "
            f"disc={self.discrimination_score:.3f}>"
        )
