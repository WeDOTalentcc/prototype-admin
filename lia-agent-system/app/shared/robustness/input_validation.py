"""
Input Validation - Pydantic schemas and sanitization for agent inputs.

This module provides:
- Base input schemas with validation
- Text sanitization
- Language detection
- Edge case handling
"""
import html
import logging
import re
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)


class SupportedLanguage(StrEnum):
    """Supported languages for the platform."""
    PT_BR = "pt-BR"
    EN_US = "en-US"
    ES = "es"


class BaseAgentInput(WeDoBaseModel):
    """Base input schema for all agent operations."""
    intent: str = Field(..., min_length=1, max_length=100)
    user_id: str | None = None
    session_id: str | None = None
    language: SupportedLanguage = SupportedLanguage.PT_BR
    
    class Config:
        extra = "allow"


class JobInput(BaseAgentInput):
    """Input schema for job-related operations."""
    job_id: str | None = None
    job_title: str | None = Field(None, max_length=200)
    job_description: str | None = Field(None, max_length=50000)
    skills: list[str] | None = None
    location: str | None = Field(None, max_length=200)
    salary_min: float | None = Field(None, ge=0)
    salary_max: float | None = Field(None, ge=0)
    experience_years_min: int | None = Field(None, ge=0, le=50)
    experience_years_max: int | None = Field(None, ge=0, le=50)
    
    @model_validator(mode='after')
    def validate_salary_range(self):
        if self.salary_min and self.salary_max:
            if self.salary_min > self.salary_max:
                raise ValueError("salary_min cannot be greater than salary_max")
        return self
    
    @model_validator(mode='after')
    def validate_experience_range(self):
        if self.experience_years_min and self.experience_years_max:
            if self.experience_years_min > self.experience_years_max:
                raise ValueError("experience_years_min cannot be greater than experience_years_max")
        return self


class CandidateInput(BaseAgentInput):
    """Input schema for candidate-related operations."""
    candidate_id: str | None = None
    candidate_name: str | None = Field(None, max_length=200)
    candidate_email: str | None = Field(None, max_length=200)
    cv_text: str | None = Field(None, max_length=100000)
    
    @field_validator('candidate_email')
    @classmethod
    def validate_email(cls, v):
        if v and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError("Invalid email format")
        return v


class SearchInput(BaseAgentInput):
    """Input schema for search operations."""
    query: str | None = Field(None, max_length=1000)
    skills: list[str] | None = None
    location: str | None = Field(None, max_length=200)
    experience_min: int | None = Field(None, ge=0, le=50)
    experience_max: int | None = Field(None, ge=0, le=50)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    
    @field_validator('skills')
    @classmethod
    def validate_skills(cls, v):
        if v:
            return [s.strip()[:100] for s in v if s and s.strip()]
        return v


class InterviewInput(BaseAgentInput):
    """Input schema for interview operations."""
    interview_id: str | None = None
    candidate_id: str | None = None
    job_id: str | None = None
    scheduled_at: str | None = None
    duration_minutes: int | None = Field(None, ge=15, le=180)
    interview_type: str | None = Field(None, max_length=50)


class WSIInput(BaseAgentInput):
    """Input schema for WSI evaluation operations."""
    candidate_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)
    responses: dict[str, Any] | None = None
    autodeclaracao_override: float | None = Field(None, ge=1.0, le=5.0)
    contexto_override: float | None = Field(None, ge=1.0, le=5.0)
    years_experience: int | None = Field(None, ge=0, le=50)


class MessageInput(BaseAgentInput):
    """Input schema for messaging operations."""
    recipient_id: str | None = None
    recipient_email: str | None = None
    subject: str | None = Field(None, max_length=500)
    message: str | None = Field(None, max_length=50000)
    template_id: str | None = None
    channel: str | None = Field(None, pattern=r'^(email|whatsapp|sms|bell)$')


DANGEROUS_PATTERNS = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'on\w+\s*=',
    r'<\s*iframe',
    r'<\s*object',
    r'<\s*embed',
    r'<\s*link',
    r'<\s*meta',
    r'expression\s*\(',
    r'url\s*\(',
    r'@import',
]

SQL_INJECTION_PATTERNS = [
    r"'\s*(OR|AND)\s+\d+\s*=\s*\d+",
    r';\s*(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE)',
    r'UNION\s+(ALL\s+)?SELECT',
    r'--\s*$',
    r'/\*.*\*/',
]


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """
    Sanitize text input to prevent XSS, SQL injection, and other attacks.
    
    Args:
        text: Raw text input
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    text = text[:max_length]
    text = html.escape(text)
    
    for pattern in DANGEROUS_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    return text.strip()


def sanitize_sql_input(text: str) -> str:
    """
    Additional sanitization for values that might be used in SQL.
    
    Args:
        text: Text that might be used in SQL queries
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    text = sanitize_text(text)
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"Potential SQL injection detected: {text[:100]}")
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    text = text.replace("'", "''")
    
    return text


PT_INDICATORS = [
    'você', 'voce', 'candidato', 'vaga', 'entrevista', 'empresa',
    'trabalho', 'experiência', 'experiencia', 'currículo', 'curriculo',
    'salário', 'salario', 'contrato', 'período', 'periodo', 'está',
    'como', 'para', 'quero', 'preciso', 'buscar', 'encontrar'
]

EN_INDICATORS = [
    'you', 'candidate', 'job', 'interview', 'company', 'work',
    'experience', 'resume', 'salary', 'contract', 'period',
    'want', 'need', 'search', 'find', 'looking', 'please'
]

ES_INDICATORS = [
    'usted', 'candidato', 'trabajo', 'entrevista', 'empresa',
    'experiencia', 'curriculum', 'salario', 'contrato', 'período',
    'quiero', 'necesito', 'buscar', 'encontrar', 'por favor'
]


def detect_language(text: str) -> SupportedLanguage:
    """
    Detect the language of the input text.
    
    Args:
        text: Input text
        
    Returns:
        Detected language (defaults to Portuguese)
    """
    if not text:
        return SupportedLanguage.PT_BR
    
    text_lower = text.lower()
    
    pt_score = sum(1 for indicator in PT_INDICATORS if indicator in text_lower)
    en_score = sum(1 for indicator in EN_INDICATORS if indicator in text_lower)
    es_score = sum(1 for indicator in ES_INDICATORS if indicator in text_lower)
    
    if en_score > pt_score and en_score > es_score:
        return SupportedLanguage.EN_US
    elif es_score > pt_score and es_score > en_score:
        return SupportedLanguage.ES
    
    return SupportedLanguage.PT_BR


def validate_agent_input(
    input_data: dict[str, Any],
    schema_class: type = BaseAgentInput
) -> BaseAgentInput:
    """
    Validate and sanitize agent input.
    
    Args:
        input_data: Raw input dictionary
        schema_class: Pydantic model class for validation
        
    Returns:
        Validated input model
        
    Raises:
        ValueError: If validation fails
    """
    for key, value in input_data.items():
        if isinstance(value, str):
            input_data[key] = sanitize_text(value)
        elif isinstance(value, list):
            input_data[key] = [
                sanitize_text(v) if isinstance(v, str) else v 
                for v in value
            ]
    
    return schema_class(**input_data)


def is_empty_or_whitespace(text: str | None) -> bool:
    """Check if text is empty or only whitespace."""
    return not text or not text.strip()


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, no accents, no extra spaces)."""
    import unicodedata
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = ' '.join(text.lower().split())
    return text
