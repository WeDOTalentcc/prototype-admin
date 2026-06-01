"""SalaryBand model — faixa salarial canonica GRANULAR.

FONTE UNICA da faixa salarial (R$) por nivel + escopo organizacional, definida em
Configuracoes. Mesmo cadastro granular de CompanyBenefit/CompensationComponent: alem
do nivel (level), escopo por contrato, departamento, AREA e filial/CNPJ + vigencia +
moeda. Varias faixas por nivel sao permitidas (ex.: Senior-Vendas-SP != Senior-Eng-RJ);
a UI agrupa por nivel. A verba (%) deriva R$ da faixa que CASA o escopo (motor
compensation_resolution_service). Substitui as bandas que viviam presas no PRV.

Multi-tenant via company_id. SEM unique(company,level) — multiplas faixas por nivel.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Date, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB

from lia_config.database import Base


class SalaryBand(Base):
    """Faixa salarial canonica (min/mid/max) por nivel + escopo organizacional."""
    __tablename__ = "salary_bands"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)

    # Identidade de senioridade (ver app/shared/seniority_levels.py)
    level = Column(String(50), nullable=False)
    label = Column(String(100), nullable=True)

    # Faixa salarial mensal (R$). mid = referencia de mercado (opcional).
    min = Column(Float, nullable=True)
    mid = Column(Float, nullable=True)
    max = Column(Float, nullable=True)
    currency = Column(String(10), default="BRL")

    # Escopo organizacional granular (paridade com CompensationComponent + area)
    contract_types = Column(ARRAY(String), nullable=True, default=list)
    departments = Column(JSONB, nullable=True, default=dict)        # {nome_dept: bool} | {"all": true}
    area = Column(ARRAY(String), nullable=True, default=list)       # areas de negocio (tokens livres)
    subsidiaries = Column(JSONB, nullable=True, default=list)       # [{"name","cnpj"}, ...]

    # Vigencia
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    # legado (Fase 0, nao usado pela UI nova)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)

    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SalaryBand {self.company_id}:{self.level} {self.min}-{self.max}>"
