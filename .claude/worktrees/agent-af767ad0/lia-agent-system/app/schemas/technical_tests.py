"""
Pydantic schemas for Technical Tests API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TestCategoryEnum(str, Enum):
    """Category of technical test."""
    CODING = "coding"
    LOGIC = "logic"
    DOMAIN_SPECIFIC = "domain_specific"
    PERSONALITY = "personality"


class TestSubcategoryEnum(str, Enum):
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


class TestDifficultyEnum(str, Enum):
    """Difficulty level of test."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TechnicalTestCreate(BaseModel):
    """Schema for creating a technical test."""
    name: str = Field(..., min_length=1, max_length=255, description="Test name")
    category: TestCategoryEnum = Field(..., description="Test category")
    subcategory: Optional[TestSubcategoryEnum] = Field(None, description="Test subcategory/technology")
    description: Optional[str] = Field(None, description="Test description")
    duration_minutes: int = Field(30, ge=5, le=180, description="Test duration in minutes")
    difficulty: TestDifficultyEnum = Field(TestDifficultyEnum.MEDIUM, description="Difficulty level")
    passing_score: float = Field(70.0, ge=0, le=100, description="Minimum passing score")
    max_attempts: int = Field(3, ge=1, le=10, description="Maximum number of attempts")
    instructions: Optional[str] = Field(None, description="Test instructions")
    questions_config: Optional[Dict[str, Any]] = Field(None, description="Questions configuration")
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


class TechnicalTestUpdate(BaseModel):
    """Schema for updating a technical test."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[TestCategoryEnum] = None
    subcategory: Optional[TestSubcategoryEnum] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=180)
    difficulty: Optional[TestDifficultyEnum] = None
    passing_score: Optional[float] = Field(None, ge=0, le=100)
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    instructions: Optional[str] = None
    questions_config: Optional[Dict[str, Any]] = None
    is_global: Optional[bool] = None
    is_active: Optional[bool] = None

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
    subcategory: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: int
    difficulty: str
    passing_score: float
    max_attempts: int
    instructions: Optional[str] = None
    questions_config: Optional[Dict[str, Any]] = None
    is_global: bool
    is_active: bool
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TechnicalTestListResponse(BaseModel):
    """Schema for paginated test list response."""
    tests: List[TechnicalTestResponse]
    total: int
    limit: int
    offset: int


class ClientTestConfigCreate(BaseModel):
    """Schema for creating/updating client test configuration."""
    is_enabled: bool = Field(True, description="Whether test is enabled for this client")
    custom_time_limit: Optional[int] = Field(None, ge=5, le=180, description="Custom time limit in minutes")
    custom_passing_score: Optional[float] = Field(None, ge=0, le=100, description="Custom passing score")
    custom_instructions: Optional[str] = Field(None, description="Custom instructions for this client")
    custom_max_attempts: Optional[int] = Field(None, ge=1, le=10, description="Custom max attempts")
    priority: int = Field(0, description="Display priority (higher = more important)")
    required_for_roles: Optional[List[str]] = Field(None, description="Roles that require this test")

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
    custom_time_limit: Optional[int] = None
    custom_passing_score: Optional[float] = None
    custom_instructions: Optional[str] = None
    custom_max_attempts: Optional[int] = None
    priority: int = 0
    required_for_roles: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    test: Optional[TechnicalTestResponse] = None

    class Config:
        from_attributes = True


class ClientTestConfigListResponse(BaseModel):
    """Schema for paginated client test config list response."""
    configs: List[ClientTestConfigResponse]
    total: int
    limit: int
    offset: int


class TestResultCreate(BaseModel):
    """Schema for creating a test result."""
    candidate_id: str = Field(..., description="Candidate ID")
    test_id: str = Field(..., description="Test ID")
    started_at: Optional[datetime] = Field(None, description="When the test started")
    completed_at: Optional[datetime] = Field(None, description="When the test completed")
    score: Optional[float] = Field(None, ge=0, le=100, description="Test score")
    passed: Optional[bool] = Field(None, description="Whether candidate passed")
    attempt_number: int = Field(1, ge=1, description="Attempt number")
    answers: Optional[Dict[str, Any]] = Field(None, description="Candidate answers")
    time_taken_seconds: Optional[int] = Field(None, ge=0, description="Time taken in seconds")

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


class TestResultUpdate(BaseModel):
    """Schema for updating a test result."""
    completed_at: Optional[datetime] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    passed: Optional[bool] = None
    answers: Optional[Dict[str, Any]] = None
    time_taken_seconds: Optional[int] = Field(None, ge=0)
    feedback: Optional[str] = None


class TestResultResponse(BaseModel):
    """Schema for test result response."""
    id: str
    client_id: str
    test_id: str
    candidate_id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    score: Optional[float] = None
    passed: Optional[bool] = None
    attempt_number: int
    answers: Optional[Dict[str, Any]] = None
    time_taken_seconds: Optional[int] = None
    feedback: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    test: Optional[TechnicalTestResponse] = None

    class Config:
        from_attributes = True


class TestResultListResponse(BaseModel):
    """Schema for paginated test result list response."""
    results: List[TestResultResponse]
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
    avg_time_seconds: Optional[float] = None
    by_difficulty: Optional[Dict[str, Any]] = None
    by_category: Optional[Dict[str, Any]] = None


class ClientTestStatsResponse(BaseModel):
    """Schema for client test statistics response."""
    client_id: str
    total_tests_enabled: int = 0
    total_results: int = 0
    overall_pass_rate: float = 0.0
    overall_avg_score: float = 0.0
    stats_by_test: List[TestStatsResponse] = []
    stats_by_category: Dict[str, Any] = {}


class TestOptionsResponse(BaseModel):
    """Schema for test options (categories, difficulties, etc.)."""
    categories: List[Dict[str, Any]]
    subcategories: List[Dict[str, Any]]
    difficulties: List[Dict[str, Any]]
