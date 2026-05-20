"""
Pydantic schemas for Technical Tests API.
"""

from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class TestCategoryEnum(StrEnum):
    """Category of technical test."""
    CODING = "coding"
    LOGIC = "logic"
    DOMAIN_SPECIFIC = "domain_specific"
    PERSONALITY = "personality"


class TestSubcategoryEnum(StrEnum):
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


class TestDifficultyEnum(StrEnum):
    """Difficulty level of test."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TechnicalTestCreate(WeDoBaseModel):
    """Schema for creating a technical test."""
    name: str = Field(..., min_length=1, max_length=255, description="Test name")
    category: TestCategoryEnum = Field(..., description="Test category")
    subcategory: TestSubcategoryEnum | None = Field(None, description="Test subcategory/technology")
    description: str | None = Field(None, description="Test description")
    duration_minutes: int = Field(30, ge=5, le=180, description="Test duration in minutes")
    difficulty: TestDifficultyEnum = Field(TestDifficultyEnum.MEDIUM, description="Difficulty level")
    passing_score: float = Field(70.0, ge=0, le=100, description="Minimum passing score")
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum number of attempts")
    instructions: str | None = Field(None, description="Test instructions")
    questions_config: dict[str, Any] | None = Field(None, description="Questions configuration")
    is_global: bool = Field(True, description="Available to all clients")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python Advanced",
                "category": "coding",
                "subcategory": "python",
                "description": "Teste avançado de Python",
                "duration_minutes": 60,
                "difficulty": "hard",
                "passing_score": 75.0,
                "max_attempts": 2,
                "instructions": "Complete todos os exercícios.",
                "is_global": True
            }
        }


class TechnicalTestUpdate(WeDoBaseModel):
    """Schema for updating a technical test."""
    name: str | None = Field(None, min_length=1, max_length=255)
    category: TestCategoryEnum | None = None
    subcategory: TestSubcategoryEnum | None = None
    description: str | None = None
    duration_minutes: int | None = Field(None, ge=5, le=180)
    difficulty: TestDifficultyEnum | None = None
    passing_score: float | None = Field(None, ge=0, le=100)
    max_attempts: int | None = Field(None, ge=1, le=10)
    instructions: str | None = None
    questions_config: dict[str, Any] | None = None
    is_global: bool | None = None
    is_active: bool | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Python Advanced v2",
                "passing_score": 80.0,
                "is_active": True
            }
        }


class TechnicalTestResponse(BaseModel):
    """Schema for technical test response."""
    id: str
    name: str
    category: str
    subcategory: str | None = None
    description: str | None = None
    duration_minutes: int
    difficulty: str
    passing_score: float
    max_attempts: int
    instructions: str | None = None
    questions_config: dict[str, Any] | None = None
    is_global: bool
    is_active: bool
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TechnicalTestListResponse(BaseModel):
    """Schema for paginated test list response."""
    tests: list[TechnicalTestResponse]
    total: int
    limit: int
    offset: int


class ClientTestConfigCreate(WeDoBaseModel):
    """Schema for creating/updating client test configuration."""
    is_enabled: bool = Field(True, description="Whether test is enabled for this client")
    custom_time_limit: int | None = Field(None, ge=5, le=180, description="Custom time limit in minutes")
    custom_passing_score: float | None = Field(None, ge=0, le=100, description="Custom passing score")
    custom_instructions: str | None = Field(None, description="Custom instructions for this client")
    custom_max_attempts: int | None = Field(None, ge=1, le=10, description="Custom max attempts")
    priority: int = Field(0, description="Display priority (higher = more important)")
    required_for_roles: list[str] | None = Field(None, description="Roles that require this test")

    class Config:
        json_schema_extra = {
            "example": {
                "is_enabled": True,
                "custom_time_limit": 60,
                "custom_passing_score": 80.0,
                "custom_instructions": "Instruções específicas do cliente",
                "priority": 1,
                "required_for_roles": ["developer", "tech_lead"]
            }
        }


class ClientTestConfigResponse(BaseModel):
    """Schema for client test configuration response."""
    id: str
    client_id: str
    test_id: str
    is_enabled: bool
    custom_time_limit: int | None = None
    custom_passing_score: float | None = None
    custom_instructions: str | None = None
    custom_max_attempts: int | None = None
    priority: int = 0
    required_for_roles: list[str] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    test: TechnicalTestResponse | None = None

    class Config:
        from_attributes = True


class ClientTestConfigListResponse(BaseModel):
    """Schema for paginated client test config list response."""
    configs: list[ClientTestConfigResponse]
    total: int
    limit: int
    offset: int


class TestResultCreate(WeDoBaseModel):
    """Schema for creating a test result."""
    candidate_id: str = Field(..., description="Candidate ID")
    test_id: str = Field(..., description="Test ID")
    started_at: datetime | None = Field(None, description="When the test started")
    completed_at: datetime | None = Field(None, description="When the test completed")
    score: float | None = Field(None, ge=0, le=100, description="Test score")
    passed: bool | None = Field(None, description="Whether candidate passed")
    attempt_number: int = Field(1, ge=1, description="Attempt number")
    answers: dict[str, Any] | None = Field(None, description="Candidate answers")
    time_taken_seconds: int | None = Field(None, ge=0, description="Time taken in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "550e8400-e29b-41d4-a716-446655440001",
                "test_id": "550e8400-e29b-41d4-a716-446655440002",
                "score": 85.0,
                "passed": True,
                "attempt_number": 1,
                "time_taken_seconds": 1800
            }
        }


class TestResultUpdate(WeDoBaseModel):
    """Schema for updating a test result."""
    completed_at: datetime | None = None
    score: float | None = Field(None, ge=0, le=100)
    passed: bool | None = None
    answers: dict[str, Any] | None = None
    time_taken_seconds: int | None = Field(None, ge=0)
    feedback: str | None = None


class TestResultResponse(BaseModel):
    """Schema for test result response."""
    id: str
    client_id: str
    test_id: str
    candidate_id: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    score: float | None = None
    passed: bool | None = None
    attempt_number: int
    answers: dict[str, Any] | None = None
    time_taken_seconds: int | None = None
    feedback: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    test: TechnicalTestResponse | None = None

    class Config:
        from_attributes = True


class TestResultListResponse(BaseModel):
    """Schema for paginated test result list response."""
    results: list[TestResultResponse]
    total: int
    limit: int
    offset: int


class TestStatsResponse(BaseModel):
    """Schema for test statistics response."""
    test_id: str
    test_name: str
    total_taken: int = 0
    total_completed: int = 0
    avg_score: float = 0.0
    completion_rate: float = 0.0
    pass_rate: float = 0.0
    avg_time_seconds: float | None = None
    by_difficulty: dict[str, Any] | None = None
    by_category: dict[str, Any] | None = None


class ClientTestStatsResponse(BaseModel):
    """Schema for client test statistics response."""
    client_id: str
    total_tests_enabled: int = 0
    total_results: int = 0
    overall_pass_rate: float = 0.0
    overall_avg_score: float = 0.0
    stats_by_test: list[TestStatsResponse] = []
    stats_by_category: dict[str, Any] = {}


class TestOptionsResponse(BaseModel):
    """Schema for test options (categories, difficulties, etc.)."""
    categories: list[dict[str, Any]]
    subcategories: list[dict[str, Any]]
    difficulties: list[dict[str, Any]]
