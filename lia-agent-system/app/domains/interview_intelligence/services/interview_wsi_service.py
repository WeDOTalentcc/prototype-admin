"""
Interview WSI Service — Applies WSI methodology to interview transcripts.

Wraps the existing InterviewTranscriptAnalysisService (deterministic scorer)
and adds interview-specific context: job requirements, competency extraction,
and enriched scoring with Bloom/Dreyfus/CBI/Big Five frameworks.
"""
import logging
from typing import Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.interview_scheduling.services.interview_transcript_analysis_service import (
    interview_transcript_analysis_service,
)
from app.models.interview import Interview

logger = logging.getLogger(__name__)


class InterviewWSIService:

    def __init__(self) -> None:
        self._analyzer = interview_transcript_analysis_service

    async def analyze(
        self,
        interview_id: str,
        db: AsyncSession,
        company_id: Optional[str] = None,
        job_requirements: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        filters = [Interview.id == interview_id]
        if company_id:
            filters.append(Interview.company_id == company_id)

        result = await db.execute(select(Interview).where(and_(*filters)))
        interview = result.scalar_one_or_none()
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


interview_wsi_service = InterviewWSIService()
