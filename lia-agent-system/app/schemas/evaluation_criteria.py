from uuid import UUID

from pydantic import BaseModel


class EvaluationCriteriaResponse(BaseModel):
    id: UUID
    name: str
    category: str
    subcategory: str | None = None
    positive_evidences: list[str]
    negative_evidences: list[str]
    evaluation_guidelines: str | None = None
    effectiveness_score: float
    usage_count: int
    source: str

    class Config:
        from_attributes = True


class CriteriaMatchResult(BaseModel):
    requirement: str
    matched_criteria: list[EvaluationCriteriaResponse]
    match_score: float
