"""SalaryBand model — faixa salarial canonica por nivel de senioridade.

FONTE UNICA da faixa salarial (R$) por nivel, definida UMA vez por empresa em
Configuracoes. Antes a faixa vivia presa em compensation_policies.salary_bands
(JSONB, policy-centric) e duplicada inline em job_vacancies.salary_range. Aqui
ela vira entidade de primeira classe que:
  - a verba variavel (CompensationComponent, % do salario) referencia por nivel p/
    derivar R$ = % x banda[nivel] (sem redigitar faixa em cada verba);
  - a vaga usa como default do salary_range do seu nivel;
  - o PRV (CompensationPolicy) le ao inves de ser dono de uma copia.

Multi-tenant via company_id. UNIQUE(company_id, level) — uma banda por nivel.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class SalaryBand(Base):
    """Faixa salarial canonica por nivel (min/mid/max) de uma empresa."""
    __tablename__ = "salary_bands"
    __table_args__ = (
        UniqueConstraint("company_id", "level", name="uq_salary_bands_company_level"),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)

    # Identificador canonico do nivel (ver app/shared/seniority_levels.py)
    level = Column(String(50), nullable=False)
    label = Column(String(100), nullable=True)  # snapshot do rotulo humano (opcional)

    # Faixa salarial mensal (R$). mid = referencia de mercado (opcional).
    min = Column(Float, nullable=True)
    mid = Column(Float, nullable=True)
    max = Column(Float, nullable=True)
    currency = Column(String(10), default="BRL")

    # Vigencia (informativa nesta fase)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)

    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SalaryBand {self.company_id}:{self.level} {self.min}-{self.max}>"
