"""

# ADR-001-EXEMPT: Cross-domain read-only aggregator for AI prediction services.
# Aggregates VacancyCandidate + Candidate + JobVacancy + InterviewNote by ID
# from a trusted parent context (e.g., SubStatusPredictor). Tenant scope is
# established by the caller passing pre-validated vacancy_candidate_id.
# TODO Sprint 6: refactor to use existing VacancyCandidateRepository,  # R-048: needs owner + ticket
# CandidateRepository, JobVacancyCRUDRepository explicitly.

CandidateContextAggregator - Aggregates candidate data for AI predictions.
Collects WSI scores, interview notes, stage history, and feedback into a standardized format.
"""
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CandidateContextAggregator:
    """Aggregates candidate context for SubStatusPredictor and other AI services."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def aggregate(
        self,
        vacancy_candidate_id: str,
        include_wsi: bool = True,
        include_interview_notes: bool = True,
        include_job_context: bool = True,
    ) -> dict[str, Any]:
        """
        Aggregate all available context for a candidate in a pipeline.
        Returns standardized dict compatible with SubStatusPredictor.
        """
        context: dict[str, Any] = {
            "vacancy_candidate_id": vacancy_candidate_id,
            "name": "",
            "current_title": "",
            "wsi_score": {},
            "interview_notes": [],
            "lia_parecer": {},
            "job": {},
            "stage_history": [],
        }
        
        try:
            from lia_models.candidate import Candidate, VacancyCandidate
            from lia_models.job_vacancy import JobVacancy
            
            # TENANT-EXEMPT: cross-domain read-only aggregator (ADR-001-EXEMPT at module
            # level); tenant scope established by caller via pre-validated
            # vacancy_candidate_id (see header comment)
            vc_result = await self.db.execute(
                select(VacancyCandidate).where(VacancyCandidate.id == vacancy_candidate_id)
            )
            vc = vc_result.scalars().first()
            if not vc:
                logger.warning(f"[CONTEXT] VacancyCandidate not found: {vacancy_candidate_id}")
                return context

            # TENANT-EXEMPT: candidate fetched by id linked from validated vc.candidate_id
            # (ADR-001-EXEMPT at module level); tenant scope established by caller upstream.
            candidate_result = await self.db.execute(
                select(Candidate).where(Candidate.id == vc.candidate_id)
            )
            candidate = candidate_result.scalars().first()
            if candidate:
                context["name"] = candidate.name or ""
                context["current_title"] = candidate.current_title or ""
                context["email"] = getattr(candidate, 'email', '')
            
            if include_wsi:
                context["wsi_score"] = self._extract_wsi_score(vc)
            
            if include_interview_notes:
                db_notes = await self._extract_interview_notes_from_db(vacancy_candidate_id)
                if db_notes:
                    context["interview_notes"] = db_notes
                else:
                    context["interview_notes"] = self._extract_interview_notes(vc)
            
            context["lia_parecer"] = self._extract_lia_parecer(vc)
            context["stage_history"] = self._extract_stage_history(vc)
            
            if include_job_context:
                try:
                    # TENANT-EXEMPT: cross-domain read-only aggregator (ADR-001-EXEMPT
                    # at module level); tenant scope established by caller via
                    # pre-validated vacancy_candidate_id (see header comment)
                    job_result = await self.db.execute(
                        select(JobVacancy).where(JobVacancy.id == vc.vacancy_id)
                    )
                    job = job_result.scalars().first()
                    if job:
                        context["job"] = {
                            "title": job.title or "",
                            "company_id": str(job.company_id) if job.company_id else "",
                            "has_hired_candidate": getattr(job, 'has_hired_candidate', False),
                            "seniority": getattr(job, 'seniority', None),
                            "department": getattr(job, 'department', None),
                        }
                except Exception as je:
                    logger.warning(f"[CONTEXT] Could not load job data: {je}")
            
        except Exception as e:
            logger.error(f"[CONTEXT] Error aggregating context: {e}", exc_info=True)
        
        return context
    
    def _extract_wsi_score(self, vc) -> dict[str, Any]:
        """Extract WSI scores from VacancyCandidate metadata."""
        try:
            metadata = getattr(vc, 'metadata', None) or {}
            if isinstance(metadata, dict):
                wsi = metadata.get('wsi_score', {})
                if wsi:
                    return wsi
            
            screening_data = getattr(vc, 'screening_data', None) or {}
            if isinstance(screening_data, dict):
                wsi = screening_data.get('wsi_score', {})
                if wsi:
                    return wsi
            
            score = getattr(vc, 'wsi_score', None)
            if score is not None:
                return {"overall": score}
        except Exception as e:
            logger.debug(f"[CONTEXT] Could not extract WSI score: {e}")
        
        return {}
    
    def _extract_interview_notes(self, vc) -> list:
        """Extract interview notes from VacancyCandidate."""
        try:
            metadata = getattr(vc, 'metadata', None) or {}
            if isinstance(metadata, dict):
                notes = metadata.get('interview_notes', [])
                if notes:
                    return notes
        except Exception as e:
            logger.debug(f"[CONTEXT] Could not extract interview notes: {e}")
        return []
    
    def _extract_lia_parecer(self, vc) -> dict[str, Any]:
        """Extract LIA parecer/assessment from VacancyCandidate."""
        try:
            metadata = getattr(vc, 'metadata', None) or {}
            if isinstance(metadata, dict):
                parecer = metadata.get('lia_parecer', {})
                if parecer:
                    return parecer
        except Exception as e:
            logger.debug(f"[CONTEXT] Could not extract LIA parecer: {e}")
        return {}
    
    def _extract_stage_history(self, vc) -> list:
        """Extract stage history from VacancyCandidate metadata or stage_transitions."""
        try:
            metadata = getattr(vc, 'metadata', None) or {}
            if isinstance(metadata, dict):
                history = metadata.get('stage_history', [])
                if history:
                    return [
                        {
                            "stage": h.get('stage', ''),
                            "timestamp": h.get('timestamp', ''),
                            "sub_status": h.get('sub_status', ''),
                        }
                        for h in history
                    ]
            transitions = getattr(vc, 'stage_transitions', [])
            if transitions:
                return [
                    {
                        "stage": getattr(t, 'stage', '') if not isinstance(t, dict) else t.get('stage', ''),
                        "timestamp": getattr(t, 'timestamp', '') if not isinstance(t, dict) else t.get('timestamp', ''),
                        "sub_status": getattr(t, 'sub_status', '') if not isinstance(t, dict) else t.get('sub_status', ''),
                    }
                    for t in transitions
                ]
        except Exception as e:
            logger.debug(f"[CONTEXT] Could not extract stage history: {e}")
        return []
    
    async def _extract_interview_notes_from_db(self, vacancy_candidate_id: str) -> list:
        """Extract interview notes from InterviewNote table if available."""
        try:
            from lia_models.interview import InterviewNote
            # TENANT-EXEMPT: InterviewNote fetched by vacancy_candidate_id which
            # was validated upstream by caller (ADR-001-EXEMPT module-level).
            result = await self.db.execute(
                select(InterviewNote).where(InterviewNote.vacancy_candidate_id == vacancy_candidate_id)
            )
            notes = result.scalars().all()
            return [
                {
                    "stage": getattr(n, 'stage', ''),
                    "interviewer": getattr(n, 'interviewer_name', None),
                    "rating": getattr(n, 'rating', None),
                    "strengths": getattr(n, 'strengths', []) or [],
                    "gaps": getattr(n, 'gaps', []) or [],
                    "recommendation": getattr(n, 'recommendation', None),
                    "notes": getattr(n, 'notes_text', None),
                }
                for n in notes
            ]
        except Exception as e:
            logger.debug(f"[CONTEXT] InterviewNote table not available: {e}")
            return []
    
    async def aggregate_bulk(
        self,
        vacancy_candidate_ids: list[str],
        include_wsi: bool = True,
        include_interview_notes: bool = True,
        include_job_context: bool = True,
    ) -> dict[str, dict[str, Any]]:
        """Aggregate context for multiple candidates. Returns {vc_id: context}."""
        results = {}
        for vc_id in vacancy_candidate_ids:
            results[vc_id] = await self.aggregate(
                vc_id,
                include_wsi=include_wsi,
                include_interview_notes=include_interview_notes,
                include_job_context=include_job_context,
            )
        return results
