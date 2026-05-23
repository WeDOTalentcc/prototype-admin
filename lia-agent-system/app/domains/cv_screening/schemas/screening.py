"""
Pydantic schemas for WSI-based Screening Questions endpoints.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


# Sprint F.3 #25 canonical-fix: BigFiveProfile moved to schemas/screening.py
from app.schemas.screening import BigFiveProfile  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: ScreeningQuestionRequest moved to schemas/screening.py
from app.schemas.screening import ScreeningQuestionRequest  # noqa: F401  (re-export for backward compat)


# DUPLICATE_OF_INTENT: app/schemas/screening.py — re-export pattern (Sprint F.3 #25), fields verified identical
class ScreeningQuestion(BaseModel):
    id: str = Field(..., description="Unique question identifier")
    text: str = Field(..., description="The question text in Portuguese")
    category: Literal["behavioral", "technical", "cultural"] = Field(..., description="Question category")
    trait: str | None = Field(None, description="Big Five trait if behavioral question")
    skill: str | None = Field(None, description="Technical skill if technical question")
    bloom_level: int = Field(default=3, ge=1, le=6, description="Bloom's Taxonomy level (1-6)")
    bloom_label: str = Field(default="Aplicar", description="Bloom level label")
    dreyfus_stage: int = Field(default=3, ge=1, le=5, description="Dreyfus model stage (1-5)")
    dreyfus_label: str = Field(default="Competente", description="Dreyfus stage label")
    framework: Literal["CBI", "Bloom", "Dreyfus", "BigFive"] = Field(
        default="CBI", description="Framework used to generate question"
    )
    weight: float = Field(default=1.0, ge=0, le=1, description="Question weight for scoring")
    expected_signals: list[str] = Field(default=[], description="Expected positive signals in answer")
    scoring_criteria: dict[str, Any] = Field(default={}, description="Scoring criteria by level")
    is_selected: bool = Field(default=True, description="Whether question is selected for use")
    order: int = Field(default=0, description="Display order")


# DUPLICATE_OF_INTENT: app/schemas/screening.py — re-export pattern (Sprint F.3 #25), fields verified identical
class ScreeningQuestionResponse(BaseModel):
    questions: list[ScreeningQuestion] = Field(default=[], description="Generated screening questions")
    behavioral_questions: list[ScreeningQuestion] = Field(default=[], description="Behavioral questions grouped")
    technical_questions: list[ScreeningQuestion] = Field(default=[], description="Technical questions grouped")
    cultural_questions: list[ScreeningQuestion] = Field(default=[], description="Cultural questions grouped")
    total_count: int = Field(default=0, description="Total number of questions")
    metadata: dict[str, Any] = Field(default={}, description="Generation metadata")


# DUPLICATE_OF_INTENT: app/schemas/screening.py — re-export pattern (Sprint F.3 #25), fields verified identical
class RegenerateQuestionsRequest(WeDoBaseModel):
    context: ScreeningQuestionRequest = Field(..., description="Original job context")
    category: Literal["behavioral", "technical", "cultural"] | None = Field(
        None, description="Category to regenerate, or all if None"
    )
    exclude_ids: list[str] = Field(default=[], description="Question IDs to exclude from regeneration")


# Sprint F.3 #25 canonical-fix: UnifiedScreeningQuestion moved to schemas/screening.py
from app.schemas.screening import UnifiedScreeningQuestion  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: WSIScreeningPipelineRequest moved to schemas/screening.py
from app.schemas.screening import WSIScreeningPipelineRequest  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: WSIBlockSummary moved to schemas/screening.py
from app.schemas.screening import WSIBlockSummary  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: WSIScreeningPipelineResponse moved to schemas/screening.py
from app.schemas.screening import WSIScreeningPipelineResponse  # noqa: F401  (re-export for backward compat)
