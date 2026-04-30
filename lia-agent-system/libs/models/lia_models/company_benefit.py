"""
Company Benefits model for multi-tenant benefits management.

Schema-alvo: alinhado ao contrato Rails canonico
(ats-api-copia/db/migrate/20250715000005_create_benefits.rb, 22 colunas) + `icon`
extra do FastAPI (harmless). Total 23 colunas.

Multi-tenant: scoping por company_id em toda query.

Mudancas Fase 1 (2026-04-30):
  - Adicionadas 11 colunas: percentage_value, value_details, applicable_to[],
    seniority_levels[], contract_types[], departments (jsonb),
    waiting_period_days, is_mandatory, is_discount, provider, provider_contact.
  - Sem PII em logs: provider_contact deve ser mascarado pela camada de logging
    (// TODO(LGPD:001) — filtro em jd_template_service para JD publicada).
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
import uuid

from lia_config.database import Base


class CompanyBenefit(Base):
    """
    Company-specific benefits for job postings.
    Multi-tenant model with company_id scoping.
    """
    __tablename__ = "company_benefits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)

    # --- Identificacao basica ---
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)  # extra FastAPI; nao existe no Rails (harmless)

    # --- Valor (3 modos: monetary | percentage | informative) ---
    value = Column(Float, nullable=True)
    percentage_value = Column(Float, nullable=True)
    value_type = Column(String(50), default="informative")
    value_details = Column(Text, nullable=True)

    # --- Elegibilidade (Postgres arrays + jsonb para departments) ---
    applicable_to = Column(ARRAY(String), nullable=True, server_default="{}")
    seniority_levels = Column(ARRAY(String), nullable=True, server_default="{}")
    contract_types = Column(ARRAY(String), nullable=True, server_default="{}")
    departments = Column(JSONB, nullable=True, server_default="{}")

    # --- Regras operacionais ---
    waiting_period_days = Column(Integer, nullable=True)
    is_mandatory = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_highlighted = Column(Boolean, default=False)
    is_discount = Column(Boolean, default=False)

    # --- Apresentacao ---
    order = Column(Integer, default=0)

    # --- Provider (PII: provider_contact deve ser mascarado em logs) ---
    provider = Column(String(255), nullable=True)
    provider_contact = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<CompanyBenefit {self.id} - {self.name}>"


# ---------------------------------------------------------------------------
# Lista mestre 1: SEED CURADO de empresa nova
# ---------------------------------------------------------------------------
# DEFAULT_BRAZILIAN_BENEFITS e a lista *curada* (25 itens) usada pelo
# CompanyBenefitRepository.seed_defaults() ao popular uma empresa nova.
# Tem identidade visual (icon emoji), is_highlighted, e nomes BR-friendly.
#
# Existe uma SEGUNDA lista, BENEFIT_TEMPLATES_DATA em
# `app/api/v1/benefits.py` (60+ itens), que e o *catalogo de templates*
# globais usado pelo endpoint `GET /api/v1/benefits/` para autocomplete e
# import bulk. As duas se sobrepoem em ~20 itens com pequenas variacoes
# de nomenclatura ("Vale Refeicao" vs "Vale-Refeicao") e categoria
# (flexibility vs quality_life).
#
# // TODO(SYNC:001) — consolidacao futura (Fase 2 ou pos-PRV):
#   1. Eleger DEFAULT_BRAZILIAN_BENEFITS como subset curado.
#   2. Refatorar BENEFIT_TEMPLATES_DATA para incluir todos os 25 (com icon)
#      + 35 itens extras nao curados (sem icon, is_popular flag).
#   3. seed_defaults filtra TEMPLATES por flag `is_seed_curated=True`.
#   4. Alinhar nomenclatura (com hifen ou sem) e categorias (flexibility
#      como categoria distinta de quality_life).
# Por enquanto, a duplicacao e intencional e sem impacto funcional —
# usuario nao ve, ambas sao consistentes em relacao ao Schema (24 cols).
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
