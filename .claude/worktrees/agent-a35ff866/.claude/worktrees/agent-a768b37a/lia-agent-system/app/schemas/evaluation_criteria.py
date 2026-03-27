from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class EvaluationCriteriaResponse(BaseModel):
    id: UUID
    name: str
    category: str
    subcategory: Optional[str] = None
    positive_evidences: List[str]
    negative_evidences: List[str]
    evaluation_guidelines: Optional[str] = None
    effectiveness_score: float
    usage_count: int
    source: str

    class Config:
        from_attributes = True


class CriteriaMatchResult(BaseModel):
    requirement: str
    matched_criteria: List[EvaluationCriteriaResponse]
    match_score: float
