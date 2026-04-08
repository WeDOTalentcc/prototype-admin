"""
WSI (WeDoTalent Skill Index) Service Package.

Re-exports the public API to maintain backward compatibility with all
existing imports of the form:
    from app.domains.cv_screening.services.wsi_service import WSIService
    from app.domains.cv_screening.services.wsi_service import wsi_service
    from app.domains.cv_screening.services.wsi_service import get_wsi_service
"""
from .models import (
    CandidateFeedback,
    Competency,
    CompetencySuggestion,
    OceanTraitScore,
    ResponseAnalysis,
    SENIORITY_BIGFIVE_TOP_N,
    StructuredReport,
    WSIQuestion,
    WSIResult,
    normalize_weights,
    safe_json_parse,
)
from .question_generator import WSIQuestionGenerator
from .response_analyzer import WSIResponseAnalyzer
from .score_calculator import WSIScoreCalculator
from .report_generator import WSIReportGenerator
from .service import WSIService, wsi_service, get_wsi_service, generate_wsi_questions_tool

__all__ = [
    "WSIService",
    "wsi_service",
    "get_wsi_service",
    "generate_wsi_questions_tool",
    "Competency",
    "CompetencySuggestion",
    "WSIQuestion",
    "ResponseAnalysis",
    "WSIResult",
    "StructuredReport",
    "CandidateFeedback",
    "OceanTraitScore",
    "SENIORITY_BIGFIVE_TOP_N",
    "normalize_weights",
    "safe_json_parse",
    "WSIQuestionGenerator",
    "WSIResponseAnalyzer",
    "WSIScoreCalculator",
    "WSIReportGenerator",
]
