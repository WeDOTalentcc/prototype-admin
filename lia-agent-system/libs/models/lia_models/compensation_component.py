"""
Compensation Component model — item-centric variable pay catalog.

Espelha CompanyBenefit (granularidade por senioridade/contrato/departamento/CNPJ),
mas para VERBAS VARIAVEIS: cada componente e um item tipado (`kind`) com faixa
inicial/final e campos especificos por tipo (`spec`). Substitui o conceito
policy-centric `compensation_policies.variable_compensation.items[]`; salary_bands
continuam no CompensationPolicy (remuneracao base e outra preocupacao).
"""
import uuid
from datetime import datetime, date  # noqa: F401
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float, ARRAY, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from lia_config.database import Base

# Discriminador / agrupador da lista (analogo a benefit.category)
COMPENSATION_KINDS = ("bonus", "plr", "ppr", "commission", "spot_bonus", "equity", "other")


class CompensationComponent(Base):
    """Verba variavel da empresa (bonus, PLR, comissao, stock options, etc.).
    Multi-tenant via company_id. Item-centric (paridade com CompanyBenefit)."""
    __tablename__ = "compensation_components"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)

    # Discriminador do tipo de verba (agrupa a lista por tipo)
    kind = Column(String(50), nullable=False, default="bonus")
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)

    # Alvo / faixa inicial-final (discriminado por tipo)
    value_type = Column(String(50), default="percent")  # percent | currency
    target_pct = Column(Float, nullable=True)
    min_pct = Column(Float, nullable=True)
    max_pct = Column(Float, nullable=True)
    min_amount = Column(Float, nullable=True)
    max_amount = Column(Float, nullable=True)
    currency = Column(String(10), default="BRL")
    frequency = Column(String(50), nullable=True)   # monthly|quarterly|annual|biannual|one_off|on_target
    trigger = Column(String(50), nullable=True)     # goal|kpi|discretionary

    # Campos especificos do kind: commission.tiers, equity.{equity_pct,units,vesting...}, plr.n_salaries...
    spec = Column(JSONB, nullable=True, default=dict)

    # Elegibilidade granular (paridade com CompanyBenefit — 4 dimensoes)
    seniority_levels = Column(ARRAY(String), nullable=True, default=list)
    contract_types = Column(ARRAY(String), nullable=True, default=list)
    departments = Column(JSONB, nullable=True, default=dict)        # {nome_dept: bool} ou {"all": true}
    subsidiaries = Column(JSONB, nullable=True, default=list)       # [{"name","cnpj"}, ...]

    # Vigencia
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)

    # Flags
    is_active = Column(Boolean, default=True)
    is_highlighted = Column(Boolean, default=False)
    order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CompensationComponent {self.id} - {self.kind}:{self.name}>"


class CompensationComponentHistory(Base):
    """Historico append-only de alteracoes em CompensationComponent (mirror CompanyBenefitHistory)."""
    __tablename__ = "compensation_component_history"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component_id = Column(
        UUID(as_uuid=True),
        ForeignKey("compensation_components.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id = Column(String(255), nullable=False, index=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by = Column(String(255), nullable=True)
    change_type = Column(String(50), nullable=False)  # created|updated|deactivated|reactivated
    previous_snapshot = Column(JSONB, nullable=True)
    change_notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<CompensationComponentHistory {self.id} - {self.change_type}@{self.changed_at}>"


# Defaults BR — seedados por empresa (paridade com DEFAULT_BRAZILIAN_BENEFITS)
DEFAULT_BR_COMPENSATION_COMPONENTS = [
    {"kind": "bonus", "name": "Bônus Anual", "description": "Bônus por desempenho pago anualmente",
     "icon": "🎯", "value_type": "percent", "target_pct": 10.0, "min_pct": 5.0, "max_pct": 20.0,
     "frequency": "annual", "trigger": "goal", "is_highlighted": True, "order": 1},
    {"kind": "plr", "name": "PLR", "description": "Participação nos Lucros e Resultados",
     "icon": "📈", "value_type": "currency", "frequency": "annual", "trigger": "goal",
     "spec": {"n_salaries_min": 1, "n_salaries_max": 2}, "is_highlighted": True, "order": 2},
    {"kind": "commission", "name": "Comissão", "description": "Comissão sobre vendas/metas",
     "icon": "💰", "value_type": "percent", "frequency": "monthly", "trigger": "kpi",
     "spec": {"base_pct": 5.0, "tiers": []}, "is_highlighted": False, "order": 3},
]
