"""
Company Benefits model for multi-tenant benefits management.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
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
    
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    icon = Column(String(100), nullable=True)
    
    value = Column(Float, nullable=True)
    value_type = Column(String(50), default="informative")
    
    is_active = Column(Boolean, default=True)
    is_highlighted = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CompanyBenefit {self.id} - {self.name}>"


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
