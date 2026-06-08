"""
CV Scoring Service - Deterministic scoring calculation for CV vs Job evaluation.

This service implements the Rubric Evaluation methodology defined in LIA_METHODOLOGY.md Section 4:
- Uses BARS (Behaviorally Anchored Rating Scales) for CV analysis
- Calculates deterministic scores based on evaluation levels and priorities
- Returns recommendations based on score thresholds

IMPORTANT: This is CV-only screening. Full WSI scoring requires the conversational
triagem (voice/chat) which is handled separately by the WSI Evaluator agent.
See LIA_METHODOLOGY.md Section 4.8 for the separation of evaluation dimensions.

Architecture:
- Agent (AI): Semantic analysis, evidence extraction, requirement matching
- System (Deterministic): Score formulas, recommendations, pipeline status
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domains.cv_screening.repositories.screening_repository import ScreeningRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.cv_screening.services.rubric_evaluation_service import rubric_evaluation_service
from lia_models.candidate import Candidate, VacancyCandidate
from lia_models.job_vacancy import JobVacancy
from lia_models.rubric import JobRequirement
from app.schemas.rubric import JobRequirementCreate, RequirementPriorityEnum
from app.domains.analytics.services.activity_service import activity_service

logger = logging.getLogger(__name__)
from app.shared.compliance import scoring_safeguards as _ss


class CVScoringService:
    """
    Service for calculating CV scores using the Rubric Evaluation methodology.
    
    Score Thresholds (from LIA_METHODOLOGY.md Section 4.7):
    - 85-100%: Altamente Recomendado (Highly Recommended) - Priorizar entrevista
    - 70-84%: Recomendado (Recommended) - Considerar para processo
    - 55-69%: Potencial (Potential) - Avaliar gaps específicos
    - 40-54%: Baixo Match (Low Match) - Arquivar para futuras vagas
    - 0-39%: Não Recomendado (Not Recommended) - Não prosseguir
    
    Note: Full WSI scoring requires conversational triagem (voice/chat).
    This service provides CV-only rubric evaluation.
    """
    
    SCORE_THRESHOLDS = {
        "highly_recommended": 85,
        "recommended": 70,
        "potential": 55,
        "low_match": 40,
        "not_recommended": 0
    }
    
    async def screen_candidate(
        self,
        candidate_id: str,
        vacancy_id: str,
        company_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Execute full CV screening for a candidate against a vacancy.
        
        This method:
        1. Fetches candidate data and job requirements
        2. Calls RubricEvaluationService for LLM-powered analysis
        3. Calculates deterministic scores using formulas
        4. Updates candidate with screening results
        5. Logs activity for audit trail
        
        Args:
            candidate_id: ID of the candidate to screen
            vacancy_id: ID of the job vacancy
            company_id: Company ID for multi-tenancy
            db: Optional database session
        
        Returns:
            Screening result with scores, recommendation, and details
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            logger.info(f"🔍 [CV_SCORING] Starting screening for candidate={candidate_id}, vacancy={vacancy_id}")
            
            candidate_data = await self._get_candidate_data(candidate_id, db)
            if not candidate_data:
                return {
                    "success": False,
                    "error": "candidate_not_found",
                    "message": f"Candidato {candidate_id} não encontrado"
                }

            # C1 — Fairness gate (LGPD Art.20 / CLAUDE.md #2/#3): check
            # resume_text before rubric evaluation. Never queries DB on block.
            fairness_block = await self._enforce_candidate_fairness_gate(
                candidate_data=candidate_data,
                company_id=company_id,
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
            )
            if fairness_block is not None:
                return fairness_block

            requirements = await self._get_job_requirements(vacancy_id, db)
            if not requirements:
                return {
                    "success": False,
                    "error": "no_requirements",
                    "message": f"Nenhum requisito encontrado para a vaga {vacancy_id}"
                }
            
            job_info = await self._get_job_info(vacancy_id, db)
            
            evaluation_result = await rubric_evaluation_service.evaluate_candidate(
                candidate_data=candidate_data,
                requirements=requirements
            )
            
            screening_result = self._build_screening_result(
                candidate_data=candidate_data,
                evaluation_result=evaluation_result,
                vacancy_id=vacancy_id,
                job_info=job_info,
                persisted=True,
            )
            rubric_score = evaluation_result.score
            cv_fit = screening_result["cv_fit"]
            recommendation = screening_result["recommendation"]
            sub_status = screening_result["sub_status"]
            
            await self._update_candidate_score(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                score=rubric_score,
                cv_fit_score=cv_fit["cv_fit_score"],
                sub_status=sub_status,
                db=db
            )
            
            await activity_service.create_activity(
                activity_type="cv_screening_completed",
                title="CV Screening Automático Concluído",
                description=f"Score: {rubric_score:.1f}% - {recommendation}",
                actor_id="cv_screening_agent",
                actor_name="CV Screening Agent",
                actor_type="agent",
                target_id=candidate_id,
                target_type="candidate",
                extra_data={
                    "vacancy_id": vacancy_id,
                    "company_id": company_id,
                    "rubric_score": rubric_score,
                    "cv_fit_score": cv_fit["cv_fit_score"],
                    "recommendation": recommendation,
                    "sub_status": sub_status
                },
                category="screening"
            )
            
            await db.commit()
            
            logger.info(
                f"✅ [CV_SCORING] Completed screening for candidate={candidate_id}: "
                f"score={rubric_score:.1f}%, recommendation={recommendation}"
            )
            
            return screening_result
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"❌ [CV_SCORING] Error screening candidate {candidate_id}: {e}", exc_info=True)
            return {
                "success": False,
                "error": "screening_failed",
                "message": str(e)
            }
        finally:
            if should_close:
                await db.close()

    async def score_candidate_standalone(
        self,
        *,
        candidate_data: dict[str, Any],
        vacancy_id: str,
        company_id: str,
        db: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Standalone / dry-run BARS scoring (Task #1224 primitive a).

        Scores already-loaded ``candidate_data`` against a vacancy's
        requirements WITHOUT requiring a persisted ``Candidate`` or
        ``VacancyCandidate`` row. Used to evaluate sourcing candidates
        BEFORE they enter the vacancy.

        Schema parity: returns the SAME payload as ``screen_candidate``
        (built by the shared ``_build_screening_result``), so the chat /
        CV-modal renders identical data. Marked ``persisted=False`` /
        ``standalone=True``.

        Keeps the existing gates: FairnessGuard C1 on candidate text,
        AuditService on block + decision, and tenant verification on the
        vacancy (never scores a vacancy from another company).
        """
        if not company_id:
            return {
                "success": False,
                "error": "missing_company_id",
                "message": "company_id é obrigatório para scoring standalone",
            }

        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True

        candidate_id = candidate_data.get("id") if candidate_data else None

        try:
            logger.info(
                f"🔍 [CV_SCORING] Standalone (dry-run) scoring candidate={candidate_id}, "
                f"vacancy={vacancy_id}"
            )

            # C1 — Fairness gate before any evaluation. Never queries DB on block.
            fairness_block = await self._enforce_candidate_fairness_gate(
                candidate_data=candidate_data,
                company_id=company_id,
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
            )
            if fairness_block is not None:
                return fairness_block

            # Tenant verification: the vacancy MUST belong to company_id.
            # Fail closed (no silent cross-tenant scoring) per ADR-001 §3.
            job_info = await self._get_job_info(vacancy_id, db)
            if not job_info:
                return {
                    "success": False,
                    "error": "job_not_found",
                    "message": f"Vaga {vacancy_id} não encontrada",
                }
            # Fail-closed: deny on mismatch AND on missing job company_id
            # (never score a vacancy whose tenant cannot be verified).
            job_company_id = job_info.get("company_id")
            if not job_company_id or str(job_company_id) != str(company_id):
                return {
                    "success": False,
                    "error": "cross_tenant_access_denied",
                    "message": "Acesso negado: vaga pertence a outra empresa",
                }

            requirements = await self._get_job_requirements(vacancy_id, db)
            if not requirements:
                return {
                    "success": False,
                    "error": "no_requirements",
                    "message": f"Nenhum requisito encontrado para a vaga {vacancy_id}",
                }

            evaluation_result = await rubric_evaluation_service.evaluate_candidate(
                candidate_data=candidate_data,
                requirements=requirements,
            )

            screening_result = self._build_screening_result(
                candidate_data=candidate_data,
                evaluation_result=evaluation_result,
                vacancy_id=vacancy_id,
                job_info=job_info,
                persisted=False,
            )

            # Best-effort audit of the automated scoring decision (LGPD Art.20).
            # Never persists VacancyCandidate / activity — this is a dry-run.
            await _ss.log_scoring_decision(
                company_id=company_id,
                agent_name="cv_scoring_service",
                decision_type="score_candidate",
                action="cv_screening.score_standalone",
                decision=screening_result["recommendation"],
                reasoning=[evaluation_result.reasoning or "standalone scoring"],
                criteria_used=["rubric_bars"],
                candidate_id=str(candidate_id) if candidate_id else None,
                job_vacancy_id=vacancy_id,
                score=evaluation_result.score,
                score_breakdown={"rubric_score": evaluation_result.score},
            )

            logger.info(
                f"✅ [CV_SCORING] Standalone scoring done candidate={candidate_id}: "
                f"score={evaluation_result.score:.1f}%"
            )
            return screening_result

        except Exception as e:
            logger.error(
                f"❌ [CV_SCORING] Standalone scoring failed candidate={candidate_id}: {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "error": "screening_failed",
                "message": str(e),
            }
        finally:
            if should_close:
                await db.close()

    async def _enforce_candidate_fairness_gate(
        self,
        *,
        candidate_data: dict[str, Any],
        company_id: str,
        candidate_id: str | None,
        vacancy_id: str | None,
    ) -> dict[str, Any] | None:
        """C1 FairnessGuard gate shared by screen_candidate + standalone.

        Runs FairnessGuard on the candidate-facing text (resume + summary).
        On block (or guard unavailable) emits the regulator-facing audit
        entry and returns a controlled error dict. Returns ``None`` when the
        input is clean and scoring may proceed.
        """
        _cv_text = (
            (candidate_data.get("resume_text") or "")
            + " " + (candidate_data.get("summary") or "")
        ).strip()
        _cv_fg, _cv_unavail = _ss.run_fairness_check(_cv_text)
        if _cv_unavail or (_cv_fg and _cv_fg.is_blocked):
            _cv_fg = _cv_fg or type(
                "FR", (), {"is_blocked": True, "category": "unavailable",
                           "educational_message": "fairness guard unavailable"}
            )()
            await _ss.log_scoring_decision(
                company_id=company_id,
                agent_name="cv_scoring_service",
                decision_type="fairness_block",
                action="cv_screening.fairness_block",
                decision="blocked",
                reasoning=[f"FairnessGuard: category={_cv_fg.category}",
                           _cv_fg.educational_message or ""],
                criteria_used=["fairness_guard"],
                candidate_id=candidate_id, job_vacancy_id=vacancy_id,
                human_review_required=True,
            )
            return {"success": False, "error": "fairness_block",
                    "message": _cv_fg.educational_message or "blocked"}
        return None

    def _build_screening_result(
        self,
        *,
        candidate_data: dict[str, Any],
        evaluation_result: Any,
        vacancy_id: str,
        job_info: dict[str, Any] | None,
        persisted: bool,
    ) -> dict[str, Any]:
        """Single source of truth for the screening payload schema.

        Both ``screen_candidate`` (persisted=True) and
        ``score_candidate_standalone`` (persisted=False) build their result
        here so the chat / CV-modal always receives an identical schema.
        """
        rubric_score = evaluation_result.score
        cv_fit = self._get_cv_fit_indicator(rubric_score)
        recommendation = self._get_recommendation(rubric_score)
        sub_status = self._get_sub_status(rubric_score)

        return {
            "success": True,
            "candidate_id": candidate_data.get("id"),
            "candidate_name": candidate_data.get("name", "Candidato"),
            "vacancy_id": vacancy_id,
            "job_title": job_info.get("title") if job_info else "Vaga",
            "rubric_score": round(rubric_score, 2),
            "cv_fit": cv_fit,
            "recommendation": recommendation,
            "recommendation_label": evaluation_result.recommendation,
            "sub_status": sub_status,
            "strengths": evaluation_result.strengths,
            "concerns": evaluation_result.concerns,
            "reasoning": evaluation_result.reasoning,
            "evaluations": [
                {
                    "requirement": e.requirement[:50],
                    "level": e.level.value if hasattr(e.level, 'value') else str(e.level),
                    "points": e.points,
                    "weighted_points": e.weighted_points,
                    "evidence": e.evidence[:200] if e.evidence else None
                }
                for e in evaluation_result.evaluations
            ],
            "evaluated_at": datetime.utcnow().isoformat(),
            "persisted": persisted,
            "standalone": not persisted,
            "methodology": {
                "name": "Rubricas Estruturadas (BARS) + André Methodology v1",
                "reference": "LIA_METHODOLOGY.md Section 4 + Phase 3 André's Criteria",
                "scoring_formula": "Score = min(99, round(Σ(points_i × evidence_weight_i × multiplier_i) / Σ(100 × multiplier_i) × 100))",
                "evidence_weights": {"explicit": 1.0, "implicit": 0.7, "inferred": 0.3},
                "cap": 99,
                "floor": "integer_rounding",
                "auto_exclusion": "essential + missing/non-explicit → score=0",
                "note": "CV-only screening. Full WSI requires conversational triagem."
            }
        }

    def _get_cv_fit_indicator(self, rubric_score: float) -> dict[str, Any]:
        """
        Calculate CV fit indicator (NOT full WSI).
        
        IMPORTANT: Full WSI scoring requires conversational triagem (voice/chat)
        with the WSI question model. This is only a CV-based fit indicator.
        
        The CV fit uses the same 0-5 scale as WSI for consistency but
        is clearly marked as preliminary and based only on CV analysis.
        
        Scale (consistent with WSI for UX):
        - 4.5-5.0: Excelente fit (CV highly matches requirements)
        - 4.0-4.4: Alto fit (CV strongly matches)
        - 3.0-3.9: Médio fit (CV partially matches)
        - 2.0-2.9: Regular fit (CV has significant gaps)
        - 0.0-1.9: Baixo fit (CV doesn't match)
        """
        cv_fit_score = rubric_score / 20
        
        if cv_fit_score >= 4.5:
            classification = "Excelente"
        elif cv_fit_score >= 4.0:
            classification = "Alto"
        elif cv_fit_score >= 3.0:
            classification = "Médio"
        elif cv_fit_score >= 2.0:
            classification = "Regular"
        else:
            classification = "Baixo"
        
        return {
            "cv_fit_score": round(cv_fit_score, 2),
            "rubric_percentage": round(rubric_score, 2),
            "classification": classification,
            "is_preliminary": True,
            "note": "Score baseado apenas em CV. WSI completo requer triagem conversacional."
        }
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on score thresholds."""
        if score >= self.SCORE_THRESHOLDS["highly_recommended"]:
            return "Altamente Recomendado"
        elif score >= self.SCORE_THRESHOLDS["recommended"]:
            return "Recomendado"
        elif score >= self.SCORE_THRESHOLDS["potential"]:
            return "Potencial"
        elif score >= self.SCORE_THRESHOLDS["low_match"]:
            return "Baixo Match"
        else:
            return "Não Recomendado"
    
    def _get_sub_status(self, score: float) -> str:
        """Map score to pipeline sub-status."""
        if score >= self.SCORE_THRESHOLDS["recommended"]:
            return "cv_approved"
        elif score >= self.SCORE_THRESHOLDS["potential"]:
            return "cv_analyzing"
        else:
            return "cv_rejected"
    
    async def _get_candidate_data(self, candidate_id: str, db: AsyncSession) -> dict[str, Any] | None:
        """Fetch candidate data from database."""
        try:
            candidate = await ScreeningRepository(db).get_candidate_by_uuid_string(candidate_id)
            
            if not candidate:
                return None
            
            return {
                "id": str(candidate.id),
                "name": candidate.name,
                "email": candidate.email,
                "current_title": candidate.current_title,
                "current_company": candidate.current_company,
                "years_of_experience": candidate.years_of_experience,
                "seniority_level": candidate.seniority_level,
                "technical_skills": candidate.technical_skills or [],
                "soft_skills": candidate.soft_skills or [],
                "certifications": candidate.certifications or [],
                "languages": candidate.languages or {},
                "location_city": candidate.location_city,
                "location_state": candidate.location_state,
                "location_country": candidate.location_country,
                "is_remote": getattr(candidate, 'is_remote', False),
                "work_history": getattr(candidate, 'work_history', []) or [],
                "education": getattr(candidate, 'education', []) or [],
                "resume_text": getattr(candidate, 'resume_text', None),
                "self_introduction": candidate.self_introduction,
            }
        except Exception as e:
            logger.error(f"Error fetching candidate data: {e}")
            return None
    
    async def _get_job_requirements(self, job_id: str, db: AsyncSession) -> list[JobRequirementCreate]:
        """Fetch job requirements from database."""
        try:
            db_requirements = await ScreeningRepository(db).list_requirements_by_vacancy_uuid_string(job_id)
            
            return [
                JobRequirementCreate(
                    requirement=req.requirement,
                    description=req.description,
                    priority=self._normalize_priority(req.priority),
                    category=req.category,
                )
                for req in db_requirements
            ]
        except Exception as e:
            logger.error(f"Error fetching job requirements: {e}")
            return []
    
    def _normalize_priority(self, priority_value) -> RequirementPriorityEnum:
        """Normalize priority value to RequirementPriorityEnum."""
        if priority_value is None:
            return RequirementPriorityEnum.IMPORTANT
        if isinstance(priority_value, RequirementPriorityEnum):
            return priority_value
        if hasattr(priority_value, 'value'):
            priority_value = priority_value.value
        if isinstance(priority_value, str):
            try:
                return RequirementPriorityEnum(priority_value.lower())
            except ValueError:
                return RequirementPriorityEnum.IMPORTANT
        return RequirementPriorityEnum.IMPORTANT
    
    async def _get_job_info(self, job_id: str, db: AsyncSession) -> dict[str, Any] | None:
        """Fetch job vacancy info from database."""
        try:
            job = await ScreeningRepository(db).get_job_vacancy_by_uuid_string(job_id)
            
            if not job:
                return None
            
            return {
                "id": str(job.id),
                "title": job.title,
                "code": getattr(job, 'code', None),
                "company_id": str(job.company_id) if job.company_id else None,
            }
        except Exception as e:
            logger.error(f"Error fetching job info: {e}")
            return None
    
    async def _update_candidate_score(
        self,
        candidate_id: str,
        vacancy_id: str,
        score: float,
        cv_fit_score: float,
        sub_status: str,
        db: AsyncSession
    ) -> None:
        """Update candidate with screening score."""
        try:
            result = await db.execute(
                select(VacancyCandidate).where(
                    VacancyCandidate.candidate_id == UUID(candidate_id),
                    VacancyCandidate.vacancy_id == UUID(vacancy_id)
                )
            )
            vc = result.scalar_one_or_none()
            
            if vc:
                if hasattr(vc, 'cv_score'):
                    vc.cv_score = score
                if hasattr(vc, 'cv_fit_score'):
                    vc.cv_fit_score = cv_fit_score
                if hasattr(vc, 'sub_status'):
                    vc.sub_status = sub_status
                if hasattr(vc, 'screening_completed_at'):
                    vc.screening_completed_at = datetime.utcnow()
                
                if hasattr(vc, 'ai_analysis'):
                    current_analysis = vc.ai_analysis or {}
                    current_analysis["cv_screening"] = {
                        "rubric_score": score,
                        "cv_fit_score": cv_fit_score,
                        "sub_status": sub_status,
                        "evaluated_at": datetime.utcnow().isoformat(),
                        "note": "WSI completo requer triagem conversacional"
                    }
                    vc.ai_analysis = current_analysis
                
                logger.info(f"📊 [CV_SCORING] Updated VacancyCandidate score: candidate={candidate_id}, rubric={score}%, cv_fit={cv_fit_score}")
        except Exception as e:
            logger.error(f"Error updating candidate score: {e}")


cv_scoring_service = CVScoringService()


def get_cv_scoring_service() -> "CVScoringService":
    return cv_scoring_service
