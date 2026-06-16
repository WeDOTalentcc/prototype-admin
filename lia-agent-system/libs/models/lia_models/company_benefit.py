"""
Company Benefits model for multi-tenant benefits management.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float, ARRAY, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from lia_config.database import Base


class CompanyBenefit(Base):
    """
    Company-specific benefits for job postings.
    Multi-tenant model with company_id scoping.
    """
    __tablename__ = "company_benefits"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)

    value = Column(Float, nullable=True)
    percentage_value = Column(Float, nullable=True)
    value_type = Column(String(50), default="informative")
    value_details = Column(Text, nullable=True)

    # Eligibility scoping (Rails canonical)
    # NOTE: DB columns are TEXT[] (Postgres native arrays). Using ARRAY(String)
    # ensures SQLAlchemy serializes lists correctly — avoids Python repr "[all]" bug.
    applicable_to = Column(ARRAY(String), nullable=True, default=list)
    seniority_levels = Column(ARRAY(String), nullable=True, default=list)
    contract_types = Column(ARRAY(String), nullable=True, default=list)
    # DB column was migrated to JSONB (seeders write dicts/lists). Mismatch with
    # the previous Text mapping made INSERT crash with DatatypeMismatchError
    # ('column "departments" is of type jsonb but expression is of type character varying').
    # Response normalization in app/api/v1/company_benefits.py::_to_response keeps
    # backwards-compat for the str|None response schema.
    departments = Column(JSONB, nullable=True, default=list)

    # Provider info
    provider = Column(String(255), nullable=True)
    provider_contact = Column(String(255), nullable=True)
    provider_cnpj = Column(String(20), nullable=True)  # migration 191

    # Filiais aplicáveis: [{"name": "Filial SP", "cnpj": "12345678000190"}, ...]
    # migration 191
    subsidiaries = Column(JSONB, nullable=True, default=list)

    # Validade do contrato com fornecedor — migration 191
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    review_frequency_months = Column(Integer, nullable=True)
    next_review_date = Column(Date, nullable=True)

    # Scheduling
    waiting_period_days = Column(Integer, nullable=True)

    # Flags
    is_mandatory = Column(Boolean, default=False)
    is_discount = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_highlighted = Column(Boolean, default=False)
    order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CompanyBenefit {self.id} - {self.name}>"


class CompanyBenefitHistory(Base):
    """Histórico de alterações em benefícios. Append-only.

    Toda operação de criação, atualização e desativação de CompanyBenefit
    grava uma entrada aqui. Multi-tenant via company_id (mirrored do benefit).
    """
    __tablename__ = "company_benefit_history"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    benefit_id = Column(
        UUID(as_uuid=True),
        ForeignKey("company_benefits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id = Column(String(255), nullable=False, index=True)
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by = Column(String(255), nullable=True)
    # created / updated / deactivated / reactivated
    change_type = Column(String(50), nullable=False)
    previous_snapshot = Column(JSONB, nullable=True)
    change_notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<CompanyBenefitHistory {self.id} - {self.change_type}@{self.changed_at}>"


DEFAULT_BRAZILIAN_BENEFITS = [
    {"name": "Vale Refeição", "category": "food", "description": "Cartão ou voucher para refeições prontas", "icon": "🍽️", "is_highlighted": True, "order": 1},
    {"name": "Vale Alimentação", "category": "food", "description": "Cartão para compra de alimentos em supermercados", "icon": "🛒", "is_highlighted": True, "order": 2},
    {"name": "Vale Transporte", "category": "transport", "description": "Auxílio para transporte público", "icon": "🚌", "is_highlighted": True, "order": 3},
    {"name": "Plano de Saúde", "category": "health", "description": "Cobertura de consultas, exames e internações", "icon": "🏥", "is_highlighted": True, "order": 4},
    {"name": "Plano Odontológico", "category": "health", "description": "Cobertura de procedimentos odontológicos", "icon": "🦷", "is_highlighted": True, "order": 5},
    {"name": "Seguro de Vida", "category": "health", "description": "Proteção financeira para a família", "icon": "🛡️", "is_highlighted": True, "order": 6},
    {"name": "Previdência Privada", "category": "financial", "description": "Complemento ao INSS para aposentadoria", "icon": "💰", "is_highlighted": True, "order": 7},
    {"name": "Gympass/TotalPass", "category": "wellness", "description": "Acesso a academias e atividades físicas", "icon": "💪", "is_highlighted": True, "order": 8},
    {"name": "Day Off Aniversário", "category": "wellness", "description": "Folga no dia do aniversário", "icon": "🎂", "is_highlighted": True, "order": 9},
    {"name": "Home Office", "category": "flexibility", "description": "Possibilidade de trabalhar remotamente", "icon": "🏠", "is_highlighted": True, "order": 10},
    {"name": "Horário Flexível", "category": "flexibility", "description": "Flexibilidade para ajustar horário de trabalho", "icon": "⏰", "is_highlighted": True, "order": 11},
    {"name": "Auxílio Home Office", "category": "flexibility", "description": "Subsídio para estrutura de trabalho em casa", "icon": "💻", "is_highlighted": False, "order": 12},
    {"name": "Participação nos Lucros (PLR)", "category": "financial", "description": "Bônus baseado em resultados", "icon": "📈", "is_highlighted": False, "order": 13},
    {"name": "Bônus de Desempenho", "category": "financial", "description": "Recompensa por atingimento de metas", "icon": "🎯", "is_highlighted": False, "order": 14},
    {"name": "Auxílio-Creche", "category": "family", "description": "Subsídio para creche ou babá", "icon": "👶", "is_highlighted": False, "order": 15},
    {"name": "Licença-Maternidade Estendida", "category": "family", "description": "Período maior que o obrigatório", "icon": "🤱", "is_highlighted": False, "order": 16},
    {"name": "Licença-Paternidade Estendida", "category": "family", "description": "Período maior que o obrigatório", "icon": "👨‍👧", "is_highlighted": False, "order": 17},
    {"name": "Auxílio-Educação", "category": "education", "description": "Subsídio para educação formal", "icon": "📚", "is_highlighted": False, "order": 18},
    {"name": "Cursos e Certificações", "category": "education", "description": "Custeio de cursos e certificações profissionais", "icon": "🎓", "is_highlighted": False, "order": 19},
    {"name": "Aulas de Idiomas", "category": "education", "description": "Custeio de aulas de línguas estrangeiras", "icon": "🌎", "is_highlighted": False, "order": 20},
    {"name": "Vale-Combustível", "category": "transport", "description": "Subsídio para combustível de veículo próprio", "icon": "⛽", "is_highlighted": False, "order": 21},
    {"name": "Estacionamento", "category": "transport", "description": "Custeio de estacionamento", "icon": "🅿️", "is_highlighted": False, "order": 22},
    {"name": "Apoio Psicológico", "category": "wellness", "description": "Sessões com profissionais de saúde mental", "icon": "🧠", "is_highlighted": False, "order": 23},
    {"name": "Check-up Anual", "category": "health", "description": "Exame de saúde periódico", "icon": "🩺", "is_highlighted": False, "order": 24},
    {"name": "Short Friday", "category": "flexibility", "description": "Expediente reduzido às sextas-feiras", "icon": "🌴", "is_highlighted": False, "order": 25},
]
