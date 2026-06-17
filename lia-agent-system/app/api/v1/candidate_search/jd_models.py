"""Job description search models (route lives in jd_search.py)."""
from typing import Any
from pydantic import BaseModel, Field

from ._shared import CandidateSearchResultDTO
from app.shared.types import WeDoBaseModel

class JobDescriptionSearchRequest(WeDoBaseModel):
    """Request para busca por job description."""
    job_description: str = Field(..., min_length=50, description="Descrição completa da vaga")
    location: str | None = Field(None, description="Localização preferida")
    limit: int = Field(20, ge=1, le=50)
    search_pearch: bool = Field(True, description="Buscar também na Pearch AI")
    pearch_type: str = Field("fast", description="Tipo de busca (sempre fast)")


class ExtractedCriteria(BaseModel):
    """Critérios extraídos da job description."""
    job_title: str | None = None
    seniority: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_years: int | None = None
    location: str | None = None
    languages: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


class JobDescriptionSearchResponse(BaseModel):
    """Response da busca por job description."""
    extracted_criteria: ExtractedCriteria
    query_generated: str
    candidates: list[CandidateSearchResultDTO] = Field(default_factory=list)
    local_count: int = 0
    pearch_count: int = 0
    total_count: int = 0
    credits_remaining: int | None = None
    search_time_seconds: float | None = None

