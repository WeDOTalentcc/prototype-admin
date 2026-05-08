"""
Interview WSI Service — Applies WSI 7-block methodology to interview transcripts.

Wraps the existing InterviewTranscriptAnalysisService (deterministic scorer)
and maps results to the 7-block WSI rubric:
  1. Hard Skills (técnico)
  2. Soft Skills (comportamental)
  3. Experiência (Dreyfus stage)
  4. Liderança
  5. Comunicação
  6. Fit Cultural
  7. Potencial (Bloom cognitive level)

Enforces tenant isolation via mandatory company_id.
"""
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_intelligence.repositories.interview_repository import (
    InterviewRepository,
)

from app.domains.interview_scheduling.services.interview_transcript_analysis_service import (
    interview_transcript_analysis_service,
)
from app.models.interview import Interview

logger = logging.getLogger(__name__)

LEADERSHIP_KEYWORDS = [
    "liderar", "liderança", "equipe", "gerenciar", "coordenar",
    "delegar", "mentoria", "gestão de pessoas", "people management",
]
COMMUNICATION_KEYWORDS = [
    "comunicar", "comunicação", "apresentar", "explicar", "articular",
    "negociar", "oratória", "feedback", "escuta ativa",
]


class InterviewWSIService:

    def __init__(self) -> None:
        self._analyzer = interview_transcript_analysis_service

    async def analyze(
        self,
        interview_id: str,
        db: AsyncSession,
        company_id: str,
        job_requirements: list[str] | None = None,
    ) -> dict[str, Any]:
        if not company_id:
            return {"success": False, "error": "company_id is required for tenant isolation"}

        _ii_repo = InterviewRepository(db)
        interview = await _ii_repo.get_for_company(
            interview_id=interview_id, company_id=company_id
        )
        if not interview:
            return {"success": False, "error": "Interview not found"}

        transcript = interview.transcript
        if not transcript or len(transcript.strip()) < 50:
            return {
                "success": False,
                "error": "Transcript too short or missing (min 50 chars)",
            }

        job_competencies: list[dict] | None = None
        if job_requirements:
            job_competencies = [
                {"name": r, "type": "technical"} for r in job_requirements
            ]

        analysis = self._analyzer.analyze_transcript(
            transcript_text=transcript,
            interview_id=interview_id,
            candidate_id=str(interview.candidate_id) if interview.candidate_id else "",
            job_vacancy_id=str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
            job_competencies=job_competencies,
        )

        seven_blocks = self._map_to_seven_blocks(analysis, transcript)

        return {
            "success": True,
            "interview_id": interview_id,
            "candidate_id": str(interview.candidate_id) if interview.candidate_id else None,
            "job_vacancy_id": str(interview.job_vacancy_id) if interview.job_vacancy_id else None,
            "interview_type": interview.interview_type,
            "wsi_score": analysis.overall_wsi_score,
            "technical_score": analysis.technical_score,
            "behavioral_score": analysis.behavioral_score,
            "cultural_score": analysis.cultural_score,
            "bloom_level": analysis.bloom_average,
            "dreyfus_stage": analysis.dreyfus_average,
            "cbi_completeness": analysis.cbi_completeness,
            "big_five": analysis.big_five_profile,
            "seven_blocks": seven_blocks,
            "evidences": [
                {
                    "competency": e.competency_name,
                    "category": e.category,
                    "excerpt": e.evidence_text[:200],
                    "bloom_level": e.bloom_level,
                }
                for e in analysis.evidences[:15]
            ],
            "strengths": analysis.strengths[:5],
            "concerns": analysis.concerns[:5],
            "red_flags": analysis.red_flags[:5],
            "recommendation": analysis.recommendation,
            "summary": analysis.summary,
        }

    def _map_to_seven_blocks(self, analysis: Any, transcript: str) -> dict[str, Any]:
        text_lower = transcript.lower()

        leadership_hits = sum(1 for kw in LEADERSHIP_KEYWORDS if kw in text_lower)
        leadership_score = min(5.0, 2.0 + leadership_hits * 0.5)

        comm_hits = sum(1 for kw in COMMUNICATION_KEYWORDS if kw in text_lower)
        communication_score = min(5.0, 2.0 + comm_hits * 0.5)

        big_five = analysis.big_five_profile or {}
        extraversion = big_five.get("extraversion", 0)
        agreeableness = big_five.get("agreeableness", 0)
        if extraversion > 0.3 or agreeableness > 0.3:
            communication_score = min(5.0, communication_score + 0.5)

        potential_score = min(5.0, analysis.bloom_average)

        return {
            "hard_skills": {
                "score": round(analysis.technical_score, 2),
                "label": "Hard Skills / Técnico",
                "description": "Competências técnicas demonstradas na entrevista",
            },
            "soft_skills": {
                "score": round(analysis.behavioral_score, 2),
                "label": "Soft Skills / Comportamental",
                "description": "Competências comportamentais e interpessoais",
            },
            "experience": {
                "score": round(analysis.dreyfus_average, 2),
                "label": "Experiência (Dreyfus)",
                "description": f"Estágio de expertise: {self._dreyfus_label(analysis.dreyfus_average)}",
            },
            "leadership": {
                "score": round(leadership_score, 2),
                "label": "Liderança",
                "description": f"{leadership_hits} indicadores de liderança identificados",
            },
            "communication": {
                "score": round(communication_score, 2),
                "label": "Comunicação",
                "description": f"{comm_hits} indicadores de comunicação identificados",
            },
            "cultural_fit": {
                "score": round(analysis.cultural_score, 2),
                "label": "Fit Cultural",
                "description": "Compatibilidade cultural baseada em Big Five e evidências",
            },
            "potential": {
                "score": round(potential_score, 2),
                "label": "Potencial (Bloom)",
                "description": f"Nível cognitivo: {self._bloom_label(analysis.bloom_average)}",
            },
        }

    @staticmethod
    def _dreyfus_label(score: float) -> str:
        if score >= 4.5:
            return "Expert"
        if score >= 3.5:
            return "Proficient"
        if score >= 2.5:
            return "Competent"
        if score >= 1.5:
            return "Advanced Beginner"
        return "Novice"

    @staticmethod
    def _bloom_label(score: float) -> str:
        if score >= 4.5:
            return "Create"
        if score >= 3.5:
            return "Evaluate"
        if score >= 2.5:
            return "Analyze"
        if score >= 1.5:
            return "Apply"
        if score >= 0.5:
            return "Understand"
        return "Remember"


interview_wsi_service = InterviewWSIService()
