"""
Company Screening Questions model for company-level default screening questions.
"""
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class CompanyScreeningQuestion(Base):
    """
    Represents a company-level default screening question.
    These questions can be imported into job vacancies.
    """
    __tablename__ = "company_screening_questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="text")  # text, single_choice, multiple_choice, yes_no, scale
    options = Column(JSON, nullable=True)  # For choice questions: ["Sim", "Não"] or ["Opção 1", "Opção 2"]
    is_required = Column(Boolean, default=True)
    is_eliminatory = Column(Boolean, default=False)
    expected_answer = Column(String(255), nullable=True)  # For eliminatory questions
    category = Column(String(100), nullable=True)  # availability, salary, experience, legal, logistics, etc.
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CompanyScreeningQuestion {self.id} - {self.question_text[:50]}>"


DEFAULT_SCREENING_QUESTIONS = [
    {
        "question_text": "Disponibilidade para início imediato?",
        "question_type": "yes_no",
        "options": ["Sim", "Não"],
        "is_required": True,
        "is_eliminatory": False,
        "expected_answer": None,
        "category": "availability",
        "order": 1
    },
    {
        "question_text": "Qual sua pretensão salarial (CLT)?",
        "question_type": "text",
        "options": None,
        "is_required": True,
        "is_eliminatory": False,
        "expected_answer": None,
        "category": "salary",
        "order": 2
    },
    {
        "question_text": "Disponibilidade para trabalho presencial/híbrido/remoto?",
        "question_type": "single_choice",
        "options": ["Presencial", "Híbrido", "Remoto", "Qualquer modalidade"],
        "is_required": True,
        "is_eliminatory": False,
        "expected_answer": None,
        "category": "work_model",
        "order": 3
    },
    {
        "question_text": "Possui disponibilidade para viagens?",
        "question_type": "yes_no",
        "options": ["Sim", "Não"],
        "is_required": False,
        "is_eliminatory": False,
        "expected_answer": None,
        "category": "logistics",
        "order": 4
    },
    {
        "question_text": "Possui CNH categoria B?",
        "question_type": "yes_no",
        "options": ["Sim", "Não"],
        "is_required": False,
        "is_eliminatory": False,
        "expected_answer": None,
        "category": "legal",
        "order": 5
    },
    {
        "question_text": "Possui disponibilidade para mudança de cidade?",
        "question_type": "yes_no",
        "options": ["Sim", "Não"],
        "is_required": False,
        "is_eliminatory": False,
        "expected_answer": None,
        "category": "logistics",
        "order": 6
    },
    {
        "question_text": "Quantos anos de experiência você possui na área?",
        "question_type": "single_choice",
        "options": ["Menos de 1 ano", "1-2 anos", "3-5 anos", "5-10 anos", "Mais de 10 anos"],
        "is_required": True,
        "is_eliminatory": False,
        "expected_answer": None,
        "category": "experience",
        "order": 7
    },
    {
        "question_text": "Nível de inglês?",
        "question_type": "single_choice",
        "options": ["Básico", "Intermediário", "Avançado", "Fluente", "Nativo"],
        "is_required": False,
        "is_eliminatory": False,
        "expected_answer": None,
        "category": "language",
        "order": 8
    }
]


QUESTION_CATEGORIES = {
    "availability": "Disponibilidade",
    "salary": "Pretensão Salarial",
    "work_model": "Modelo de Trabalho",
    "logistics": "Logística",
    "legal": "Documentação/Legal",
    "experience": "Experiência",
    "language": "Idiomas",
    "custom": "Personalizada"
}


QUESTION_TYPES = {
    "text": "Texto livre",
    "yes_no": "Sim/Não",
    "single_choice": "Escolha única",
    "multiple_choice": "Múltipla escolha",
    "scale": "Escala (1-10)"
}
