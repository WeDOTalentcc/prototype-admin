"""
Technical Tests models for managing assessment tests per client.

Provides models for:
- TechnicalTest: Global library of available tests
- ClientTestConfig: Client-specific test configurations
- TestResult: Candidate test results
- TestStats: Aggregated test statistics
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer, Float, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from typing import Dict, Any, Optional

from lia_config.database import Base


class TestCategory(str, enum.Enum):
    """Category of technical test."""
    CODING = "coding"
    LOGIC = "logic"
    DOMAIN_SPECIFIC = "domain_specific"
    PERSONALITY = "personality"


class TestSubcategory(str, enum.Enum):
    """Subcategory/technology of technical test."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    SQL = "sql"
    EXCEL = "excel"
    JAVA = "java"
    TYPESCRIPT = "typescript"
    REACT = "react"
    ANGULAR = "angular"
    DATA_ANALYSIS = "data_analysis"
    LOGICAL_REASONING = "logical_reasoning"
    NUMERICAL_REASONING = "numerical_reasoning"
    VERBAL_REASONING = "verbal_reasoning"
    DISC = "disc"
    BIG_FIVE = "big_five"
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"
    GENERAL = "general"


class TestDifficulty(str, enum.Enum):
    """Difficulty level of test."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


TEST_CATEGORY_OPTIONS = [
    {"value": TestCategory.CODING.value, "label": "Programação", "description": "Testes de código e programação"},
    {"value": TestCategory.LOGIC.value, "label": "Lógica", "description": "Testes de raciocínio lógico"},
    {"value": TestCategory.DOMAIN_SPECIFIC.value, "label": "Conhecimento Específico", "description": "Testes de domínio específico"},
    {"value": TestCategory.PERSONALITY.value, "label": "Personalidade", "description": "Avaliações comportamentais"},
]

TEST_DIFFICULTY_OPTIONS = [
    {"value": TestDifficulty.EASY.value, "label": "Fácil", "description": "Nível iniciante"},
    {"value": TestDifficulty.MEDIUM.value, "label": "Médio", "description": "Nível intermediário"},
    {"value": TestDifficulty.HARD.value, "label": "Difícil", "description": "Nível avançado"},
]


class TechnicalTest(Base):
    """
    TechnicalTest model.
    
    Represents a test template in the global library that can be
    configured and enabled for specific clients.
    """
    __tablename__ = "technical_tests"
    __table_args__ = {"extend_existing": True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    
    duration_minutes = Column(Integer, default=30)
    difficulty = Column(String(20), default=TestDifficulty.MEDIUM.value, index=True)
    passing_score = Column(Float, default=70.0)
    max_attempts = Column(Integer, default=3)
    
    instructions = Column(Text, nullable=True)
    questions_config = Column(JSON, nullable=True, default=dict)
    
    is_global = Column(Boolean, default=True, index=True)
    is_active = Column(Boolean, default=True, index=True)
    # TENANT-EXEMPT: TechnicalTest com is_global=True default => template publico do marketplace
    company_id = Column(String(255), nullable=True, index=True)
    
    created_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_technical_test_category', 'category'),
        Index('idx_technical_test_subcategory', 'subcategory'),
        Index('idx_technical_test_difficulty', 'difficulty'),
        Index('idx_technical_test_global', 'is_global'),
        Index('idx_technical_test_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<TechnicalTest {self.id} - {self.name}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "name": self.name,
            "category": self.category,
            "subcategory": self.subcategory,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "difficulty": self.difficulty,
            "passing_score": self.passing_score,
            "max_attempts": self.max_attempts,
            "instructions": self.instructions,
            "questions_config": self.questions_config or {},
            "is_global": self.is_global,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ClientTestConfig(Base):
    """
    ClientTestConfig model.
    
    Represents client-specific configuration for a test,
    including custom time limits, passing scores, and instructions.
    """
    __tablename__ = "client_test_configs"
    # Boy scout 2026-05-24: defense-in-depth contra Table already defined.
    # Sibling classes neste arquivo já tinham extend_existing.
    __table_args__ = {"extend_existing": True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey("technical_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    
    is_enabled = Column(Boolean, default=True)
    custom_time_limit = Column(Integer, nullable=True)
    custom_passing_score = Column(Float, nullable=True)
    custom_instructions = Column(Text, nullable=True)
    custom_max_attempts = Column(Integer, nullable=True)
    
    priority = Column(Integer, default=0)
    required_for_roles = Column(JSON, nullable=True, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_client_test_config_client', 'client_id'),
        Index('idx_client_test_config_test', 'test_id'),
        Index('idx_client_test_config_enabled', 'is_enabled'),
        Index('idx_client_test_config_unique', 'client_id', 'test_id', unique=True),
    )
    
    def __repr__(self):
        return f"<ClientTestConfig client={self.client_id} test={self.test_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "test_id": str(self.test_id),
            "is_enabled": self.is_enabled,
            "custom_time_limit": self.custom_time_limit,
            "custom_passing_score": self.custom_passing_score,
            "custom_instructions": self.custom_instructions,
            "custom_max_attempts": self.custom_max_attempts,
            "priority": self.priority,
            "required_for_roles": self.required_for_roles or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TestResult(Base):
    """
    TestResult model.
    
    Stores the result of a candidate taking a test.
    """
    __tablename__ = "test_results"
    # Boy scout 2026-05-24: defense-in-depth contra Table already defined.
    # Sibling classes neste arquivo já tinham extend_existing.
    __table_args__ = {"extend_existing": True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    test_id = Column(UUID(as_uuid=True), ForeignKey("technical_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    score = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    attempt_number = Column(Integer, default=1)
    
    answers = Column(JSON, nullable=True, default=dict)
    time_taken_seconds = Column(Integer, nullable=True)
    
    feedback = Column(Text, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_test_result_client', 'client_id'),
        Index('idx_test_result_test', 'test_id'),
        Index('idx_test_result_candidate', 'candidate_id'),
        Index('idx_test_result_passed', 'passed'),
        Index('idx_test_result_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<TestResult {self.id} - candidate={self.candidate_id} test={self.test_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "client_id": str(self.client_id),
            "test_id": str(self.test_id),
            "candidate_id": str(self.candidate_id),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "score": self.score,
            "passed": self.passed,
            "attempt_number": self.attempt_number,
            "answers": self.answers or {},
            "time_taken_seconds": self.time_taken_seconds,
            "feedback": self.feedback,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


DEFAULT_TESTS = [
    {
        "name": "Python Basics",
        "category": TestCategory.CODING.value,
        "subcategory": TestSubcategory.PYTHON.value,
        "description": "Avaliação de conhecimentos básicos de Python incluindo estruturas de dados, funções e orientação a objetos.",
        "duration_minutes": 45,
        "difficulty": TestDifficulty.EASY.value,
        "passing_score": 70.0,
        "max_attempts": 3,
        "instructions": "Complete os exercícios de programação Python. Você pode usar a documentação oficial como referência.",
        "is_global": True,
    },
    {
        "name": "JavaScript Fundamentals",
        "category": TestCategory.CODING.value,
        "subcategory": TestSubcategory.JAVASCRIPT.value,
        "description": "Teste de fundamentos JavaScript incluindo ES6+, manipulação de DOM e programação assíncrona.",
        "duration_minutes": 45,
        "difficulty": TestDifficulty.MEDIUM.value,
        "passing_score": 70.0,
        "max_attempts": 3,
        "instructions": "Resolva os problemas de JavaScript. Atenção especial para boas práticas e código limpo.",
        "is_global": True,
    },
    {
        "name": "SQL Queries",
        "category": TestCategory.CODING.value,
        "subcategory": TestSubcategory.SQL.value,
        "description": "Avaliação de SQL incluindo SELECT, JOINs, agregações e subqueries.",
        "duration_minutes": 40,
        "difficulty": TestDifficulty.MEDIUM.value,
        "passing_score": 65.0,
        "max_attempts": 3,
        "instructions": "Escreva consultas SQL para resolver os problemas apresentados. Use SQL padrão ANSI.",
        "is_global": True,
    },
    {
        "name": "Excel Skills",
        "category": TestCategory.DOMAIN_SPECIFIC.value,
        "subcategory": TestSubcategory.EXCEL.value,
        "description": "Teste de habilidades em Excel incluindo fórmulas, tabelas dinâmicas e análise de dados.",
        "duration_minutes": 35,
        "difficulty": TestDifficulty.EASY.value,
        "passing_score": 70.0,
        "max_attempts": 3,
        "instructions": "Demonstre suas habilidades em Excel resolvendo os problemas propostos.",
        "is_global": True,
    },
    {
        "name": "Logical Reasoning",
        "category": TestCategory.LOGIC.value,
        "subcategory": TestSubcategory.LOGICAL_REASONING.value,
        "description": "Avaliação de raciocínio lógico com problemas de padrões, sequências e dedução.",
        "duration_minutes": 30,
        "difficulty": TestDifficulty.MEDIUM.value,
        "passing_score": 60.0,
        "max_attempts": 2,
        "instructions": "Resolva os problemas de lógica. Gerencie bem seu tempo pois algumas questões podem ser mais complexas.",
        "is_global": True,
    },
    {
        "name": "DISC Assessment",
        "category": TestCategory.PERSONALITY.value,
        "subcategory": TestSubcategory.DISC.value,
        "description": "Avaliação comportamental DISC para identificar perfil de Dominância, Influência, Estabilidade e Conformidade.",
        "duration_minutes": 20,
        "difficulty": TestDifficulty.EASY.value,
        "passing_score": 0.0,
        "max_attempts": 1,
        "instructions": "Responda às perguntas com honestidade. Não há respostas certas ou erradas - o objetivo é entender seu perfil comportamental.",
        "is_global": True,
    },
]
