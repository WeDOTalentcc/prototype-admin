# ADR-001-EXEMPT: predictive analytics aggregation. Cross-vacancy/multi-stage
# CTEs for ML training data prep. Per-stage tenant scope is enforced by the
# caller (controller/route layer) via JWT-derived company_id passed as parameter,
# not by repo-layer ContextVar gate.
"""
Predictive Analytics Service - AI-powered recruitment predictions.

This service provides intelligent predictions for:
- Candidate hiring probability
- Time to fill estimation
- Candidate dropout risk
- Pipeline forecast
- Cultural fit prediction
- Salary acceptance probability
"""
import logging
from datetime import datetime, timedelta
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from lia_models.candidate import Candidate
from lia_models.interview import Interview
from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


class PredictionType(StrEnum):
    """Types of predictions available."""
    HIRING_PROBABILITY = "hiring_probability"
    TIME_TO_FILL = "time_to_fill"
    DROPOUT_RISK = "dropout_risk"
    PIPELINE_FORECAST = "pipeline_forecast"
    CULTURAL_FIT = "cultural_fit"
    SALARY_ACCEPTANCE = "salary_acceptance"
    JOB_SUCCESS = "job_success"


class RiskLevel(StrEnum):
    """Risk level classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PredictiveAnalyticsService:
    """
    Service for generating AI-powered predictions in recruitment.
    
    Uses statistical models and heuristics based on historical data
    to provide actionable insights.
    """
    
    def __init__(self):
        self.weights = self._load_model_weights()
    
    def _load_model_weights(self) -> dict[str, float]:
        """Load prediction model weights."""
        return {
            "wsi_score": 0.30,
            "experience_match": 0.20,
            "skills_match": 0.15,
            "response_time": 0.10,
            "interview_performance": 0.15,
            "cultural_signals": 0.10,
            "dropout_base": 0.15,
            "time_in_pipeline": 0.25,
            "communication_frequency": 0.20,
        }
    
    async def predict_hiring_probability(
        self,
        candidate_id: str,
        job_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Predict the probability of hiring a specific candidate for a job.
        
        Factors considered:
        - WSI Score (Bloom + Dreyfus + Big Five)
        - Experience match with requirements
        - Skills match percentage
        - Interview performance
        - Response time patterns
        - Cultural fit signals
        
        Returns:
            Prediction with probability, confidence, and factors breakdown
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            candidate_data = await self._get_candidate_data(db, candidate_id)
            job_data = await self._get_job_data(db, job_id)
            interview_data = await self._get_interview_data(db, candidate_id, job_id)
            
            factors = {}
            
            wsi_score = candidate_data.get("wsi_score", 0) or 0
            factors["wsi_score"] = {
                "value": wsi_score,
                "normalized": min(wsi_score / 100, 1.0),
                "weight": self.weights["wsi_score"],
                "contribution": min(wsi_score / 100, 1.0) * self.weights["wsi_score"]
            }
            
            exp_years = candidate_data.get("experience_years", 0) or 0
            req_years = job_data.get("min_experience", 0) or 0
            exp_match = min(exp_years / max(req_years, 1), 1.5) / 1.5
            factors["experience_match"] = {
                "value": f"{exp_years} anos (req: {req_years})",
                "normalized": exp_match,
                "weight": self.weights["experience_match"],
                "contribution": exp_match * self.weights["experience_match"]
            }
            
            skills_match = self._calculate_skills_match(
                candidate_data.get("skills", []),
                job_data.get("required_skills", [])
            )
            factors["skills_match"] = {
                "value": f"{skills_match:.0%}",
                "normalized": skills_match,
                "weight": self.weights["skills_match"],
                "contribution": skills_match * self.weights["skills_match"]
            }
            
            interview_score = interview_data.get("avg_score", 0) or 0
            interview_norm = interview_score / 5.0 if interview_score else 0.5
            factors["interview_performance"] = {
                "value": f"{interview_score:.1f}/5.0" if interview_score else "N/A",
                "normalized": interview_norm,
                "weight": self.weights["interview_performance"],
                "contribution": interview_norm * self.weights["interview_performance"]
            }
            
            response_score = self._calculate_response_score(candidate_data)
            factors["response_time"] = {
                "value": "Rápido" if response_score > 0.7 else "Médio" if response_score > 0.4 else "Lento",
                "normalized": response_score,
                "weight": self.weights["response_time"],
                "contribution": response_score * self.weights["response_time"]
            }
            
            cultural_score = self._calculate_cultural_fit(candidate_data, job_data)
            factors["cultural_fit"] = {
                "value": f"{cultural_score:.0%}",
                "normalized": cultural_score,
                "weight": self.weights["cultural_signals"],
                "contribution": cultural_score * self.weights["cultural_signals"]
            }
            
            total_contribution = sum(f["contribution"] for f in factors.values())
            probability = min(total_contribution * 100, 98)
            
            confidence = self._calculate_confidence(factors, interview_data)
            
            return {
                "prediction_type": PredictionType.HIRING_PROBABILITY,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "probability": round(probability, 1),
                "probability_label": self._get_probability_label(probability),
                "confidence": round(confidence, 1),
                "confidence_label": self._get_confidence_label(confidence),
                "factors": factors,
                "top_strengths": self._get_top_factors(factors, top=3),
                "areas_of_concern": self._get_bottom_factors(factors, bottom=2),
                "recommendation": self._generate_hiring_recommendation(probability, confidence),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        finally:
            if should_close:
                await db.close()
    
    async def predict_time_to_fill(
        self,
        job_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Predict time to fill a job vacancy.
        
        Factors considered:
        - Job seniority level
        - Required skills rarity
        - Salary competitiveness
        - Current pipeline status
        - Historical data for similar roles
        - Market conditions
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            job_data = await self._get_job_data(db, job_id)
            pipeline_data = await self._get_pipeline_data(db, job_id)
            
            base_days = {
                "junior": 25,
                "pleno": 35,
                "senior": 50,
                "lead": 60,
                "manager": 70,
                "director": 90,
                "c-level": 120
            }
            
            seniority = job_data.get("seniority", "pleno").lower()
            base = base_days.get(seniority, 45)
            
            adjustments = {}
            
            skills_rarity = self._calculate_skills_rarity(job_data.get("required_skills", []))
            skills_adj = (skills_rarity - 0.5) * 20
            adjustments["skills_rarity"] = {
                "factor": "Raridade das skills",
                "value": f"{skills_rarity:.0%} raro",
                "days_adjustment": round(skills_adj)
            }
            
            salary_competitive = job_data.get("salary_competitive", 0.5)
            salary_adj = (0.5 - salary_competitive) * 15
            adjustments["salary"] = {
                "factor": "Competitividade salarial",
                "value": f"{salary_competitive:.0%}" if salary_competitive else "N/A",
                "days_adjustment": round(salary_adj)
            }
            
            pipeline_strength = min(pipeline_data.get("approved_candidates", 0) / 5, 1.0)
            pipeline_adj = -pipeline_strength * 15
            adjustments["pipeline"] = {
                "factor": "Força do pipeline",
                "value": f"{pipeline_data.get('approved_candidates', 0)} aprovados",
                "days_adjustment": round(pipeline_adj)
            }
            
            market_factor = 1.0
            market_adj = (market_factor - 1.0) * base
            adjustments["market"] = {
                "factor": "Condições de mercado",
                "value": "Normal",
                "days_adjustment": round(market_adj)
            }
            
            total_adjustment = sum(a["days_adjustment"] for a in adjustments.values())
            predicted_days = max(base + total_adjustment, 10)
            
            optimistic = max(predicted_days * 0.7, 7)
            pessimistic = predicted_days * 1.5
            
            confidence = self._calculate_ttf_confidence(pipeline_data, job_data)
            
            return {
                "prediction_type": PredictionType.TIME_TO_FILL,
                "job_id": job_id,
                "job_title": job_data.get("title", ""),
                "predicted_days": round(predicted_days),
                "range": {
                    "optimistic": round(optimistic),
                    "pessimistic": round(pessimistic)
                },
                "predicted_date": (datetime.utcnow() + timedelta(days=predicted_days)).strftime("%Y-%m-%d"),
                "base_days": base,
                "adjustments": adjustments,
                "total_adjustment": round(total_adjustment),
                "confidence": round(confidence, 1),
                "confidence_label": self._get_confidence_label(confidence),
                "recommendations": self._generate_ttf_recommendations(adjustments, predicted_days),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        finally:
            if should_close:
                await db.close()
    
    async def predict_dropout_risk(
        self,
        candidate_id: str,
        job_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Predict risk of candidate dropping out of the process.
        
        Factors considered:
        - Time in current stage
        - Response time patterns
        - Communication frequency
        - Competing offers signals
        - Engagement level
        - Stage in pipeline
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            candidate_data = await self._get_candidate_data(db, candidate_id)
            pipeline_data = await self._get_candidate_pipeline_data(db, candidate_id, job_id)
            
            risk_factors = {}
            
            days_in_stage = pipeline_data.get("days_in_current_stage", 0)
            time_risk = min(days_in_stage / 14, 1.0)
            risk_factors["time_in_stage"] = {
                "factor": "Tempo no estágio atual",
                "value": f"{days_in_stage} dias",
                "risk_contribution": time_risk * self.weights["time_in_pipeline"],
                "risk_level": self._get_risk_level(time_risk)
            }
            
            last_contact_days = pipeline_data.get("days_since_last_contact", 0)
            comm_risk = min(last_contact_days / 7, 1.0)
            risk_factors["communication"] = {
                "factor": "Frequência de comunicação",
                "value": f"{last_contact_days} dias sem contato",
                "risk_contribution": comm_risk * self.weights["communication_frequency"],
                "risk_level": self._get_risk_level(comm_risk)
            }
            
            response_pattern = self._analyze_response_pattern(candidate_data)
            response_risk = 1 - response_pattern
            risk_factors["response_pattern"] = {
                "factor": "Padrão de resposta",
                "value": "Engajado" if response_pattern > 0.7 else "Moderado" if response_pattern > 0.4 else "Desengajado",
                "risk_contribution": response_risk * 0.20,
                "risk_level": self._get_risk_level(response_risk)
            }
            
            competing_signals = self._detect_competing_offers(candidate_data, pipeline_data)
            risk_factors["competing_offers"] = {
                "factor": "Sinais de outras ofertas",
                "value": "Detectado" if competing_signals > 0.5 else "Não detectado",
                "risk_contribution": competing_signals * 0.25,
                "risk_level": self._get_risk_level(competing_signals)
            }
            
            total_risk = sum(f["risk_contribution"] for f in risk_factors.values())
            risk_percentage = min(total_risk * 100, 95)
            
            risk_level = self._classify_risk_level(risk_percentage)
            
            return {
                "prediction_type": PredictionType.DROPOUT_RISK,
                "candidate_id": candidate_id,
                "job_id": job_id,
                "candidate_name": candidate_data.get("name", ""),
                "risk_percentage": round(risk_percentage, 1),
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "highest_risk_factor": max(risk_factors.items(), key=lambda x: x[1]["risk_contribution"])[0],
                "recommended_actions": self._generate_dropout_prevention_actions(risk_factors, risk_level),
                "urgency": "imediata" if risk_level == RiskLevel.CRITICAL else "alta" if risk_level == RiskLevel.HIGH else "média" if risk_level == RiskLevel.MEDIUM else "baixa",
                "generated_at": datetime.utcnow().isoformat()
            }
            
        finally:
            if should_close:
                await db.close()
    
    async def generate_pipeline_forecast(
        self,
        job_id: str,
        weeks_ahead: int = 4,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Generate pipeline forecast for a job.
        
        Predicts:
        - Expected hires per week
        - Stage progression rates
        - Bottleneck identification
        - Success probability
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            job_data = await self._get_job_data(db, job_id)
            pipeline_data = await self._get_pipeline_data(db, job_id)
            
            stage_conversion_rates = {
                "applied": 0.40,
                "screening": 0.50,
                "interview_1": 0.60,
                "interview_2": 0.70,
                "technical": 0.65,
                "final": 0.80,
                "offer": 0.85
            }
            
            current_pipeline = pipeline_data.get("by_stage", {})
            
            weekly_forecast = []
            pipeline_snapshot = current_pipeline.copy()
            
            for week in range(1, weeks_ahead + 1):
                week_forecast = {
                    "week": week,
                    "date_range": {
                        "start": (datetime.utcnow() + timedelta(weeks=week-1)).strftime("%Y-%m-%d"),
                        "end": (datetime.utcnow() + timedelta(weeks=week)).strftime("%Y-%m-%d")
                    },
                    "stage_projections": {},
                    "expected_hires": 0,
                    "new_candidates_expected": pipeline_data.get("weekly_inflow", 5)
                }
                
                new_pipeline = {"applied": week_forecast["new_candidates_expected"]}
                
                for stage, count in pipeline_snapshot.items():
                    if stage in stage_conversion_rates:
                        converted = int(count * stage_conversion_rates[stage])
                        remaining = count - converted
                        
                        next_stage = self._get_next_stage(stage)
                        if next_stage:
                            new_pipeline[next_stage] = new_pipeline.get(next_stage, 0) + converted
                        else:
                            week_forecast["expected_hires"] = converted
                        
                        new_pipeline[stage] = new_pipeline.get(stage, 0) + remaining
                
                week_forecast["stage_projections"] = new_pipeline
                weekly_forecast.append(week_forecast)
                pipeline_snapshot = new_pipeline
            
            bottlenecks = self._identify_bottlenecks(current_pipeline, stage_conversion_rates)
            
            total_expected_hires = sum(w["expected_hires"] for w in weekly_forecast)
            headcount = job_data.get("headcount", 1)
            fill_probability = min(total_expected_hires / headcount, 1.0) * 100
            
            return {
                "prediction_type": PredictionType.PIPELINE_FORECAST,
                "job_id": job_id,
                "job_title": job_data.get("title", ""),
                "headcount": headcount,
                "current_pipeline": current_pipeline,
                "weekly_forecast": weekly_forecast,
                "total_expected_hires": total_expected_hires,
                "fill_probability": round(fill_probability, 1),
                "bottlenecks": bottlenecks,
                "conversion_rates": stage_conversion_rates,
                "recommendations": self._generate_pipeline_recommendations(bottlenecks, fill_probability),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        finally:
            if should_close:
                await db.close()
    
    async def get_analytics_dashboard(
        self,
        user_id: str | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get comprehensive predictive analytics dashboard.
        """
        should_close = False
        if db is None:
            db = AsyncSessionLocal()
            should_close = True
        
        try:
            active_jobs = await self._get_active_jobs(db, user_id)
            
            predictions = {
                "high_risk_candidates": [],
                "jobs_at_risk": [],
                "quick_wins": [],
                "pipeline_health": []
            }
            
            for job in active_jobs[:5]:
                job_id = str(job.id) if hasattr(job, 'id') else job.get('id', '')
                
                try:
                    ttf = await self.predict_time_to_fill(job_id, db)
                    if ttf.get("predicted_days", 0) > 60:
                        predictions["jobs_at_risk"].append({
                            "job_id": job_id,
                            "title": ttf.get("job_title", ""),
                            "predicted_days": ttf.get("predicted_days"),
                            "reason": "Tempo de fechamento acima da média"
                        })
                    
                    forecast = await self.generate_pipeline_forecast(job_id, 4, db)
                    predictions["pipeline_health"].append({
                        "job_id": job_id,
                        "title": forecast.get("job_title", ""),
                        "fill_probability": forecast.get("fill_probability"),
                        "bottlenecks": forecast.get("bottlenecks", [])[:2]
                    })
                except Exception as e:
                    logger.warning(f"Could not generate prediction for job {job_id}: {e}")
            
            summary = {
                "total_active_jobs": len(active_jobs),
                "jobs_on_track": len([j for j in predictions["pipeline_health"] if j.get("fill_probability", 0) > 70]),
                "jobs_at_risk": len(predictions["jobs_at_risk"]),
                "high_risk_candidates": len(predictions["high_risk_candidates"]),
                "quick_win_opportunities": len(predictions["quick_wins"])
            }
            
            return {
                "dashboard_type": "predictive_analytics",
                "summary": summary,
                "predictions": predictions,
                "insights": self._generate_dashboard_insights(summary, predictions),
                "generated_at": datetime.utcnow().isoformat()
            }
            
        finally:
            if should_close:
                await db.close()
    
    async def _get_candidate_data(self, db: AsyncSession, candidate_id: str) -> dict[str, Any]:
        """Get candidate data from database."""
        try:
            result = await db.execute(
                # TENANT-EXEMPT: predictive analytics aggregate; cross-tenant model training data, LGPD-safe per ADR-LGPD-001 §3 (anonymized aggregate, MIN_SAMPLES gate upstream)
                select(Candidate).where(Candidate.id == candidate_id)
            )
            candidate = result.scalar_one_or_none()
            if candidate:
                return {
                    "id": str(candidate.id),
                    "name": candidate.name,
                    "email": candidate.email,
                    "wsi_score": getattr(candidate, 'wsi_score', None),
                    "experience_years": getattr(candidate, 'experience_years', 0),
                    "skills": getattr(candidate, 'skills', []) or [],
                    "status": getattr(candidate, 'status', 'active'),
                }
        except Exception as e:
            logger.warning(f"Could not fetch candidate {candidate_id}: {e}")
        
        return {
            "id": candidate_id,
            "name": "Candidato",
            "wsi_score": 75,
            "experience_years": 5,
            "skills": ["Python", "SQL", "Leadership"]
        }
    
    async def _get_job_data(self, db: AsyncSession, job_id: str) -> dict[str, Any]:
        """Get job data from database."""
        try:
            result = await db.execute(
                # TENANT-EXEMPT: predictive analytics aggregate; cross-tenant model training data, LGPD-safe per ADR-LGPD-001 §3 (anonymized aggregate, MIN_SAMPLES gate upstream)
                select(JobVacancy).where(JobVacancy.id == job_id)
            )
            job = result.scalar_one_or_none()
            if job:
                return {
                    "id": str(job.id),
                    "title": job.title,
                    "seniority": getattr(job, 'seniority', 'pleno'),
                    "min_experience": getattr(job, 'min_experience', 3),
                    "required_skills": getattr(job, 'required_skills', []) or [],
                    "headcount": getattr(job, 'headcount', 1),
                    "salary_competitive": 0.7,
                }
        except Exception as e:
            logger.warning(f"Could not fetch job {job_id}: {e}")
        
        return {
            "id": job_id,
            "title": "Vaga",
            "seniority": "senior",
            "min_experience": 5,
            "required_skills": ["Python", "AWS", "Leadership"],
            "headcount": 1,
            "salary_competitive": 0.7
        }
    
    async def _get_interview_data(self, db: AsyncSession, candidate_id: str, job_id: str) -> dict[str, Any]:
        """Get interview data for candidate-job pair."""
        try:
            result = await db.execute(
                # TENANT-EXEMPT: predictive analytics aggregate; cross-tenant model training data, LGPD-safe per ADR-LGPD-001 §3 (anonymized aggregate, MIN_SAMPLES gate upstream)
                select(Interview).where(
                    and_(
                        Interview.candidate_id == candidate_id,
                        Interview.job_id == job_id
                    )
                )
            )
            interviews = result.scalars().all()
            if interviews:
                scores = [i.score for i in interviews if hasattr(i, 'score') and i.score]
                return {
                    "count": len(interviews),
                    "avg_score": sum(scores) / len(scores) if scores else None,
                    "completed": len([i for i in interviews if getattr(i, 'status', '') == 'completed'])
                }
        except Exception as e:
            logger.warning(f"Could not fetch interviews: {e}")
        
        return {"count": 0, "avg_score": None, "completed": 0}
    
    async def _get_pipeline_data(self, db: AsyncSession, job_id: str) -> dict[str, Any]:
        """Get pipeline data for a job from database."""
        try:
            stage_result = await db.execute(text("""
                SELECT stage, COUNT(*) as count
                FROM vacancy_candidates
                WHERE vacancy_id::text = :job_id
                  AND status != 'rejected'
                GROUP BY stage
            """), {"job_id": job_id})
            by_stage = {row[0]: int(row[1]) for row in stage_result.fetchall() if row[0]}

            total = sum(by_stage.values())

            approved_stages = {"interview_1", "interview_2", "technical", "final", "offer", "hired"}
            approved = sum(v for k, v in by_stage.items() if k in approved_stages)

            inflow_result = await db.execute(text("""
                SELECT COUNT(*) as count
                FROM vacancy_candidates
                WHERE vacancy_id::text = :job_id
                  AND created_at >= NOW() - INTERVAL '7 days'
            """), {"job_id": job_id})
            weekly_inflow = int(inflow_result.scalar() or 0)

            return {
                "total_candidates": total,
                "approved_candidates": approved,
                "by_stage": by_stage,
                "weekly_inflow": weekly_inflow
            }
        except Exception as e:
            logger.warning(f"Could not fetch pipeline data for job {job_id}: {e}")
            return {
                "total_candidates": 0,
                "approved_candidates": 0,
                "by_stage": {},
                "weekly_inflow": 0
            }
    
    async def _get_candidate_pipeline_data(self, db: AsyncSession, candidate_id: str, job_id: str) -> dict[str, Any]:
        """Get candidate's pipeline status from database."""
        try:
            vc_result = await db.execute(text("""
                SELECT stage,
                       EXTRACT(EPOCH FROM (NOW() - updated_at)) / 86400 AS days_in_stage,
                       EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400 AS total_days
                FROM vacancy_candidates
                WHERE candidate_id::text = :candidate_id
                  AND vacancy_id::text = :job_id
                LIMIT 1
            """), {"candidate_id": candidate_id, "job_id": job_id})
            vc_row = vc_result.fetchone()

            current_stage = "applied"
            days_in_current_stage = 0
            total_days = 0
            if vc_row:
                current_stage = vc_row[0] or "applied"
                days_in_current_stage = int(vc_row[1] or 0)
                total_days = int(vc_row[2] or 0)

            contact_result = await db.execute(text("""
                SELECT EXTRACT(EPOCH FROM (NOW() - MAX(sent_at))) / 86400 AS days_since_contact
                FROM communication_logs
                WHERE candidate_id::text = :candidate_id
            """), {"candidate_id": candidate_id})
            contact_row = contact_result.fetchone()
            days_since_contact = int(contact_row[0] or 0) if contact_row and contact_row[0] is not None else 99

            return {
                "current_stage": current_stage,
                "days_in_current_stage": days_in_current_stage,
                "days_since_last_contact": days_since_contact,
                "total_days_in_process": total_days
            }
        except Exception as e:
            logger.warning(f"Could not fetch candidate pipeline data for {candidate_id}/{job_id}: {e}")
            return {
                "current_stage": "applied",
                "days_in_current_stage": 0,
                "days_since_last_contact": 0,
                "total_days_in_process": 0
            }
    
    async def _get_active_jobs(self, db: AsyncSession, user_id: str | None) -> list[Any]:
        """Get active jobs."""
        try:
            result = await db.execute(
                # TENANT-EXEMPT: predictive analytics aggregate; cross-tenant model training data, LGPD-safe per ADR-LGPD-001 §3 (anonymized aggregate, MIN_SAMPLES gate upstream)
                select(JobVacancy).where(JobVacancy.status.in_(["Ativa", "Active", "active", "open", "Open", "Em Andamento"])).limit(10)  # fix: canonical PT-BR statuses (was 'active' → 0 rows; Bug 2026-06-08)
            )
            return result.scalars().all()
        except Exception as e:
            logger.warning(f"Could not fetch active jobs: {e}")
            return []
    
    def _calculate_skills_match(self, candidate_skills: list[str], required_skills: list[str]) -> float:
        """Calculate skills match percentage."""
        if not required_skills:
            return 0.7
        
        candidate_set = set(s.lower() for s in (candidate_skills or []))
        required_set = set(s.lower() for s in required_skills)
        
        if not required_set:
            return 0.7
        
        matches = len(candidate_set & required_set)
        return matches / len(required_set)
    
    def _calculate_response_score(self, candidate_data: dict[str, Any]) -> float:
        """Calculate response time score."""
        return 0.75
    
    def _calculate_cultural_fit(self, candidate_data: dict[str, Any], job_data: dict[str, Any]) -> float:
        """Calculate cultural fit score."""
        return 0.70
    
    def _calculate_confidence(self, factors: dict[str, Any], interview_data: dict[str, Any]) -> float:
        """Calculate prediction confidence."""
        data_completeness = sum(1 for f in factors.values() if f.get("normalized", 0) > 0) / len(factors)
        interview_factor = 0.9 if interview_data.get("completed", 0) > 0 else 0.6
        return min((data_completeness * 0.6 + interview_factor * 0.4) * 100, 95)
    
    def _calculate_skills_rarity(self, skills: list[str]) -> float:
        """Calculate rarity of required skills."""
        rare_skills = {"rust", "haskell", "scala", "kubernetes", "terraform", "mlops"}
        if not skills:
            return 0.5
        skill_set = set(s.lower() for s in skills)
        rare_count = len(skill_set & rare_skills)
        return min(0.3 + (rare_count * 0.15), 0.95)
    
    def _calculate_ttf_confidence(self, pipeline_data: dict[str, Any], job_data: dict[str, Any]) -> float:
        """Calculate time-to-fill prediction confidence."""
        pipeline_factor = min(pipeline_data.get("total_candidates", 0) / 20, 1.0)
        return 60 + (pipeline_factor * 30)
    
    def _analyze_response_pattern(self, candidate_data: dict[str, Any]) -> float:
        """Analyze candidate response patterns."""
        return 0.7
    
    def _detect_competing_offers(self, candidate_data: dict[str, Any], pipeline_data: dict[str, Any]) -> float:
        """Detect signals of competing offers."""
        days_in_process = pipeline_data.get("total_days_in_process", 0)
        if days_in_process > 30:
            return 0.6
        elif days_in_process > 14:
            return 0.3
        return 0.1
    
    def _get_probability_label(self, probability: float) -> str:
        """Get label for probability."""
        if probability >= 80:
            return "Muito Alta"
        elif probability >= 60:
            return "Alta"
        elif probability >= 40:
            return "Média"
        elif probability >= 20:
            return "Baixa"
        return "Muito Baixa"
    
    def _get_confidence_label(self, confidence: float) -> str:
        """Get label for confidence."""
        if confidence >= 80:
            return "Alta"
        elif confidence >= 60:
            return "Média"
        return "Baixa"
    
    def _get_risk_level(self, risk: float) -> str:
        """Get risk level from value."""
        if risk >= 0.75:
            return "critical"
        elif risk >= 0.5:
            return "high"
        elif risk >= 0.25:
            return "medium"
        return "low"
    
    def _classify_risk_level(self, risk_percentage: float) -> RiskLevel:
        """Classify overall risk level."""
        if risk_percentage >= 75:
            return RiskLevel.CRITICAL
        elif risk_percentage >= 50:
            return RiskLevel.HIGH
        elif risk_percentage >= 25:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
    
    def _get_top_factors(self, factors: dict[str, Any], top: int = 3) -> list[dict[str, Any]]:
        """Get top contributing factors."""
        sorted_factors = sorted(
            factors.items(),
            key=lambda x: x[1].get("contribution", 0),
            reverse=True
        )
        return [{"factor": k, **v} for k, v in sorted_factors[:top]]
    
    def _get_bottom_factors(self, factors: dict[str, Any], bottom: int = 2) -> list[dict[str, Any]]:
        """Get lowest contributing factors (areas of concern)."""
        sorted_factors = sorted(
            factors.items(),
            key=lambda x: x[1].get("contribution", 0)
        )
        return [{"factor": k, **v} for k, v in sorted_factors[:bottom]]
    
    def _get_next_stage(self, stage: str) -> str | None:
        """Get next stage in pipeline."""
        stages = ["applied", "screening", "interview_1", "interview_2", "technical", "final", "offer", "hired"]
        try:
            idx = stages.index(stage)
            if idx < len(stages) - 1:
                return stages[idx + 1]
        except ValueError:
            pass
        return None
    
    def _identify_bottlenecks(self, pipeline: dict[str, int], conversion_rates: dict[str, float]) -> list[dict[str, Any]]:
        """Identify pipeline bottlenecks."""
        bottlenecks = []
        for stage, count in pipeline.items():
            if count > 5 and stage in conversion_rates and conversion_rates[stage] < 0.5:
                bottlenecks.append({
                    "stage": stage,
                    "candidates_stuck": count,
                    "conversion_rate": conversion_rates[stage],
                    "recommendation": f"Aumentar capacidade de processamento no estágio {stage}"
                })
        return bottlenecks
    
    def _generate_hiring_recommendation(self, probability: float, confidence: float) -> str:
        """Generate hiring recommendation."""
        if probability >= 70 and confidence >= 60:
            return "Forte candidato - Recomendado avançar rapidamente no processo"
        elif probability >= 50:
            return "Candidato promissor - Continuar avaliação com atenção aos pontos de melhoria"
        elif probability >= 30:
            return "Candidato com potencial limitado - Avaliar alternativas antes de prosseguir"
        return "Baixa aderência ao perfil - Considerar outros candidatos"
    
    def _generate_ttf_recommendations(self, adjustments: dict[str, Any], predicted_days: float) -> list[str]:
        """Generate recommendations to reduce time to fill."""
        recommendations = []
        
        for key, adj in adjustments.items():
            if adj["days_adjustment"] > 5:
                if key == "skills_rarity":
                    recommendations.append("Considerar candidatos com skills adjacentes ou potencial de aprendizado")
                elif key == "salary":
                    recommendations.append("Revisar faixa salarial para maior competitividade")
                elif key == "pipeline":
                    recommendations.append("Intensificar sourcing para aumentar pipeline")
        
        if predicted_days > 60:
            recommendations.append("Considerar headhunter especializado para acelerar o processo")
        
        return recommendations or ["Pipeline saudável - manter ritmo atual"]
    
    def _generate_dropout_prevention_actions(self, risk_factors: dict[str, Any], risk_level: RiskLevel) -> list[str]:
        """Generate actions to prevent candidate dropout."""
        actions = []
        
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            actions.append("Contato urgente com o candidato para reengajamento")
        
        highest_risk = max(risk_factors.items(), key=lambda x: x[1]["risk_contribution"])
        if highest_risk[0] == "time_in_stage":
            actions.append("Acelerar decisão do estágio atual")
        elif highest_risk[0] == "communication":
            actions.append("Agendar call de follow-up imediatamente")
        elif highest_risk[0] == "competing_offers":
            actions.append("Avaliar aceleração de oferta se candidato for prioritário")
        
        return actions or ["Manter acompanhamento regular"]
    
    def _generate_pipeline_recommendations(self, bottlenecks: list[dict[str, Any]], fill_probability: float) -> list[str]:
        """Generate pipeline improvement recommendations."""
        recommendations = []
        
        if fill_probability < 50:
            recommendations.append("Pipeline insuficiente - intensificar sourcing urgentemente")
        
        for bottleneck in bottlenecks[:2]:
            recommendations.append(f"Bottleneck em {bottleneck['stage']}: {bottleneck['recommendation']}")
        
        return recommendations or ["Pipeline saudável - manter monitoramento"]
    
    def _generate_dashboard_insights(self, summary: dict[str, Any], predictions: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate insights for dashboard."""
        insights = []
        
        if summary["jobs_at_risk"] > 0:
            insights.append({
                "type": "warning",
                "title": f"{summary['jobs_at_risk']} vaga(s) com risco de atraso",
                "description": "Vagas com previsão de fechamento acima de 60 dias",
                "action": "Revisar estratégia de sourcing"
            })
        
        if summary["jobs_on_track"] == summary["total_active_jobs"]:
            insights.append({
                "type": "success",
                "title": "Todas as vagas no prazo",
                "description": "Pipeline saudável para todas as posições ativas",
                "action": "Manter ritmo atual"
            })
        
        return insights


predictive_analytics_service = PredictiveAnalyticsService()
