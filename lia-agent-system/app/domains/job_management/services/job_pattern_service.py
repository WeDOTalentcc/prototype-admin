"""
Job Pattern Service - Learns from historical job creation data.

Enables the 10th job to be 80% faster than the 1st by:
- Recognizing patterns from similar jobs
- Learning salary ranges per role/location
- Suggesting skills based on successful hires
- Predicting time-to-fill
"""
import logging
import re
from datetime import datetime
from statistics import mean, median
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.job_pattern_repository import JobPatternRepository

from app.core.database import AsyncSessionLocal
from lia_models.feedback_learning import JobOutcome
from lia_models.job_pattern import JobPattern, SalaryBenchmark

logger = logging.getLogger(__name__)


class JobPatternService:
    """
    Service for learning and applying job creation patterns.
    
    Features:
    - Pattern recognition from job titles/departments
    - Salary learning and recommendations
    - Skills recommendation engine
    - Time-to-fill predictions
    - Success profile generation
    """
    
    MIN_SAMPLES_FOR_RECOMMENDATION = 3
    HIGH_CONFIDENCE_SAMPLES = 10
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def normalize_job_title(self, title: str) -> str:
        """Normalize job title for pattern matching."""
        if not title:
            return ""
        
        normalized = title.lower().strip()
        normalized = re.sub(r'\s+', ' ', normalized)
        
        replacements = {
            'sr.': 'senior',
            'sr': 'senior',
            'jr.': 'junior',
            'jr': 'junior',
            'pl.': 'pleno',
            'pl': 'pleno',
            'dev': 'desenvolvedor',
            'eng': 'engenheiro',
            'analista de ti': 'analista de tecnologia',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def generate_pattern_key(
        self,
        job_title: str,
        department: str | None = None,
        seniority: str | None = None
    ) -> str:
        """Generate a unique pattern key from job attributes."""
        parts = []
        
        normalized_title = self.normalize_job_title(job_title)
        if normalized_title:
            parts.append(normalized_title)
        
        if department:
            parts.append(department.lower().strip())
        
        if seniority:
            parts.append(seniority.lower().strip())
        
        return "_".join(parts) if parts else "general"
    
    async def find_similar_patterns(
        self,
        company_id: str,
        job_title: str,
        department: str | None = None,
        seniority: str | None = None,
        location: str | None = None,
        limit: int = 5,
        db: AsyncSession | None = None
    ) -> list[JobPattern]:
        """
        Find similar job patterns for suggestions.
        
        Returns patterns ordered by relevance and confidence.
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            company_uuid = UUID(company_id)
            normalized_title = self.normalize_job_title(job_title)
            
            conditions = [
                JobPattern.company_id == company_uuid,
                JobPattern.is_active,
                JobPattern.sample_count >= self.MIN_SAMPLES_FOR_RECOMMENDATION
            ]
            
            if normalized_title:
                conditions.append(
                    or_(
                        JobPattern.job_title_normalized == normalized_title,
                        JobPattern.job_title_normalized.ilike(f"%{normalized_title}%"),
                        JobPattern.pattern_key.ilike(f"%{normalized_title}%")
                    )
                )
            
            if department:
                conditions.append(
                    or_(
                        JobPattern.department is None,
                        JobPattern.department == department.lower().strip()
                    )
                )
            
            patterns = await JobPatternRepository(db).find_patterns_with_conditions(
                conditions, limit
            )
            
            self.logger.info(
                f"Found {len(patterns)} similar patterns for '{job_title}' "
                f"(company={company_id})"
            )
            
            return list(patterns)
            
        except Exception as e:
            self.logger.error(f"Error finding similar patterns: {e}")
            return []
        finally:
            if should_close and db:
                await db.close()
    
    async def get_salary_suggestion(
        self,
        company_id: str,
        job_title: str,
        seniority: str | None = None,
        location: str | None = None,
        department: str | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get salary suggestion based on historical data.
        
        Returns:
            Dictionary with salary range, confidence, and basis
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            company_uuid = UUID(company_id)
            normalized_title = self.normalize_job_title(job_title)
            
            conditions = [
                SalaryBenchmark.company_id == company_uuid,
                SalaryBenchmark.job_title_normalized == normalized_title
            ]
            
            if seniority:
                conditions.append(SalaryBenchmark.seniority == seniority.lower())
            
            benchmark = await JobPatternRepository(db).find_salary_benchmark(conditions)
            
            if benchmark and benchmark.sample_count >= self.MIN_SAMPLES_FOR_RECOMMENDATION:
                confidence = min(0.95, 0.5 + (benchmark.sample_count / 20))
                
                return {
                    "has_suggestion": True,
                    "min_salary": benchmark.percentile_25 or benchmark.min_salary,
                    "max_salary": benchmark.percentile_75 or benchmark.max_salary,
                    "median_salary": benchmark.median_salary,
                    "avg_salary": benchmark.avg_salary,
                    "sample_count": benchmark.sample_count,
                    "confidence": round(confidence, 2),
                    "basis": f"Baseado em {benchmark.sample_count} vagas similares",
                    "percentiles": {
                        "p10": benchmark.percentile_10,
                        "p25": benchmark.percentile_25,
                        "p50": benchmark.percentile_50,
                        "p75": benchmark.percentile_75,
                        "p90": benchmark.percentile_90,
                    }
                }
            
            patterns = await self.find_similar_patterns(
                company_id=company_id,
                job_title=job_title,
                department=department,
                seniority=seniority,
                db=db
            )
            
            if patterns:
                pattern = patterns[0]
                if pattern.avg_salary_min and pattern.avg_salary_max:
                    return {
                        "has_suggestion": True,
                        "min_salary": pattern.salary_percentile_25 or pattern.avg_salary_min,
                        "max_salary": pattern.salary_percentile_75 or pattern.avg_salary_max,
                        "sample_count": pattern.sample_count,
                        "confidence": round(pattern.confidence * 0.8, 2),
                        "basis": f"Baseado em padrão similar ({pattern.sample_count} amostras)",
                    }
            
            return {
                "has_suggestion": False,
                "message": "Dados insuficientes para sugestão de salário",
            }
            
        except Exception as e:
            self.logger.error(f"Error getting salary suggestion: {e}")
            return {"has_suggestion": False, "error": str(e)}
        finally:
            if should_close and db:
                await db.close()
    
    async def get_skills_recommendation(
        self,
        company_id: str,
        job_title: str,
        existing_skills: list[str] | None = None,
        department: str | None = None,
        seniority: str | None = None,
        limit: int = 10,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get skill recommendations based on similar jobs.
        
        Returns:
            Dictionary with recommended skills, confidence, and missing skills
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            existing_skills = existing_skills or []
            existing_lower = {s.lower() for s in existing_skills}
            
            patterns = await self.find_similar_patterns(
                company_id=company_id,
                job_title=job_title,
                department=department,
                seniority=seniority,
                db=db
            )
            
            if not patterns:
                return {
                    "has_recommendations": False,
                    "message": "Dados insuficientes para recomendações de skills",
                }
            
            skill_scores: dict[str, float] = {}
            total_weight = 0
            
            for pattern in patterns:
                weight = pattern.confidence * pattern.sample_count
                total_weight += weight
                
                skill_freq = pattern.skill_frequency or {}
                for skill, freq in skill_freq.items():
                    if skill.lower() not in existing_lower:
                        if skill not in skill_scores:
                            skill_scores[skill] = 0
                        skill_scores[skill] += freq * weight
            
            if total_weight > 0:
                for skill in skill_scores:
                    skill_scores[skill] /= total_weight
            
            recommended = sorted(
                skill_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            common_skills = set()
            for pattern in patterns[:3]:
                if pattern.common_skills:
                    common_skills.update(pattern.common_skills)
            
            missing_critical = [
                s for s in common_skills
                if s.lower() not in existing_lower
            ]
            
            return {
                "has_recommendations": True,
                "recommended_skills": [
                    {"name": skill, "score": round(score, 2)}
                    for skill, score in recommended
                ],
                "missing_critical": missing_critical[:5],
                "patterns_used": len(patterns),
                "total_samples": sum(p.sample_count for p in patterns),
                "confidence": round(patterns[0].confidence, 2) if patterns else 0,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting skills recommendation: {e}")
            return {"has_recommendations": False, "error": str(e)}
        finally:
            if should_close and db:
                await db.close()
    
    async def get_behavioral_recommendation(
        self,
        company_id: str,
        job_title: str,
        existing_behavioral: list[str] | None = None,
        department: str | None = None,
        seniority: str | None = None,
        limit: int = 5,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """Get behavioral competency recommendations."""
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            existing_behavioral = existing_behavioral or []
            existing_lower = {b.lower() for b in existing_behavioral}
            
            patterns = await self.find_similar_patterns(
                company_id=company_id,
                job_title=job_title,
                department=department,
                seniority=seniority,
                db=db
            )
            
            if not patterns:
                return {
                    "has_recommendations": False,
                    "message": "Dados insuficientes para recomendações comportamentais",
                }
            
            behavioral_scores: dict[str, float] = {}
            
            for pattern in patterns:
                weight = pattern.confidence * pattern.sample_count
                
                behavioral_freq = pattern.behavioral_frequency or {}
                for comp, freq in behavioral_freq.items():
                    if comp.lower() not in existing_lower:
                        if comp not in behavioral_scores:
                            behavioral_scores[comp] = 0
                        behavioral_scores[comp] += freq * weight
            
            recommended = sorted(
                behavioral_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return {
                "has_recommendations": True,
                "recommended_behavioral": [
                    {"name": comp, "score": round(score, 2)}
                    for comp, score in recommended
                ],
                "patterns_used": len(patterns),
            }
            
        except Exception as e:
            self.logger.error(f"Error getting behavioral recommendation: {e}")
            return {"has_recommendations": False, "error": str(e)}
        finally:
            if should_close and db:
                await db.close()
    
    async def predict_time_to_fill(
        self,
        company_id: str,
        job_title: str,
        seniority: str | None = None,
        location: str | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Predict time-to-fill based on similar jobs.
        
        Returns:
            Dictionary with estimated days, confidence, and factors
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            UUID(company_id)
            
            patterns = await self.find_similar_patterns(
                company_id=company_id,
                job_title=job_title,
                seniority=seniority,
                location=location,
                db=db
            )
            
            if not patterns:
                return {
                    "has_prediction": False,
                    "message": "Dados insuficientes para previsão",
                }
            
            times = []
            weights = []
            
            for pattern in patterns:
                if pattern.avg_time_to_fill:
                    times.append(pattern.avg_time_to_fill)
                    weights.append(pattern.sample_count)
            
            if not times:
                return {
                    "has_prediction": False,
                    "message": "Sem dados de tempo de preenchimento",
                }
            
            weighted_avg = sum(t * w for t, w in zip(times, weights)) / sum(weights)
            
            factors = []
            adjustment = 1.0
            
            if seniority and seniority.lower() in ['senior', 'sênior', 'lead', 'principal']:
                adjustment *= 1.2
                factors.append("Senioridade alta (+20%)")
            
            if salary_min and salary_max:
                avg_salary = (salary_min + salary_max) / 2
                pattern_salary = patterns[0].avg_salary_max if patterns[0].avg_salary_max else None
                if pattern_salary and avg_salary < pattern_salary * 0.85:
                    adjustment *= 1.3
                    factors.append("Salário abaixo da média (+30%)")
            
            estimated_days = int(weighted_avg * adjustment)
            
            confidence = min(0.9, patterns[0].confidence if patterns else 0.5)
            
            return {
                "has_prediction": True,
                "estimated_days": estimated_days,
                "range_min": max(7, int(estimated_days * 0.7)),
                "range_max": int(estimated_days * 1.5),
                "median_days": int(median(times)) if times else None,
                "sample_count": sum(weights),
                "confidence": round(confidence, 2),
                "factors": factors,
                "basis": f"Baseado em {len(patterns)} padrões similares",
            }
            
        except Exception as e:
            self.logger.error(f"Error predicting time-to-fill: {e}")
            return {"has_prediction": False, "error": str(e)}
        finally:
            if should_close and db:
                await db.close()
    
    async def get_success_profile(
        self,
        company_id: str,
        job_title: str,
        department: str | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get success profile based on successful hires.
        
        Returns:
            Dictionary with ideal candidate profile
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            company_uuid = UUID(company_id)
            
            successful_outcomes = await JobPatternRepository(db).list_successful_outcomes(
                company_id=company_uuid,
                job_title_normalized=self.normalize_job_title(job_title),
                min_quality=4.0,
                limit=10,
            )
            
            if len(successful_outcomes) < 2:
                return {
                    "has_profile": False,
                    "message": "Poucos casos de sucesso para gerar perfil",
                }
            
            all_skills: dict[str, int] = {}
            all_behavioral: dict[str, int] = {}
            salaries = []
            ttf_days = []
            
            for outcome in successful_outcomes:
                for skill in (outcome.skills or []):
                    all_skills[skill] = all_skills.get(skill, 0) + 1
                
                for comp in (outcome.behavioral_competencies or []):
                    all_behavioral[comp] = all_behavioral.get(comp, 0) + 1
                
                if outcome.final_salary:
                    salaries.append(outcome.final_salary)
                
                if outcome.time_to_fill_days:
                    ttf_days.append(outcome.time_to_fill_days)
            
            n = len(successful_outcomes)
            top_skills = [
                {"name": k, "frequency": round(v / n, 2)}
                for k, v in sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            top_behavioral = [
                {"name": k, "frequency": round(v / n, 2)}
                for k, v in sorted(all_behavioral.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
            
            return {
                "has_profile": True,
                "sample_count": n,
                "ideal_skills": top_skills,
                "ideal_behavioral": top_behavioral,
                "salary_range": {
                    "min": min(salaries) if salaries else None,
                    "max": max(salaries) if salaries else None,
                    "avg": mean(salaries) if salaries else None,
                },
                "avg_time_to_fill": int(mean(ttf_days)) if ttf_days else None,
                "confidence": min(0.9, 0.5 + (n / 20)),
            }
            
        except Exception as e:
            self.logger.error(f"Error getting success profile: {e}")
            return {"has_profile": False, "error": str(e)}
        finally:
            if should_close and db:
                await db.close()
    
    async def record_job_outcome(
        self,
        company_id: str,
        job_id: str,
        outcome_data: dict[str, Any],
        db: AsyncSession | None = None
    ) -> JobOutcome:
        """
        Record a job outcome for learning purposes.
        
        Called when a job is filled, closed, or cancelled.
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            company_uuid = UUID(company_id)
            job_uuid = UUID(job_id)
            
            outcome = JobOutcome(
                id=uuid4(),
                company_id=company_uuid,
                job_id=job_uuid,
                draft_id=UUID(outcome_data.get("draft_id")) if outcome_data.get("draft_id") else None,
                job_title=outcome_data.get("job_title"),
                job_title_normalized=self.normalize_job_title(outcome_data.get("job_title", "")),
                department=outcome_data.get("department"),
                seniority=outcome_data.get("seniority"),
                location=outcome_data.get("location"),
                work_model=outcome_data.get("work_model"),
                salary_min=outcome_data.get("salary_min"),
                salary_max=outcome_data.get("salary_max"),
                final_salary=outcome_data.get("final_salary"),
                skills=outcome_data.get("skills", []),
                behavioral_competencies=outcome_data.get("behavioral_competencies", []),
                outcome_status=outcome_data.get("outcome_status", "unknown"),
                published_at=outcome_data.get("published_at"),
                filled_at=outcome_data.get("filled_at"),
                closed_at=outcome_data.get("closed_at"),
                time_to_fill_days=outcome_data.get("time_to_fill_days"),
                candidates_total=outcome_data.get("candidates_total"),
                candidates_screened=outcome_data.get("candidates_screened"),
                candidates_interviewed=outcome_data.get("candidates_interviewed"),
                candidates_offered=outcome_data.get("candidates_offered"),
                hire_quality_score=outcome_data.get("hire_quality_score"),
                wizard_time_seconds=outcome_data.get("wizard_time_seconds"),
                fields_auto_filled=outcome_data.get("fields_auto_filled"),
                fields_edited=outcome_data.get("fields_edited"),
                extra_data=outcome_data.get("extra_data", {}),
            )
            
            db.add(outcome)
            await db.commit()
            await db.refresh(outcome)
            
            self.logger.info(
                f"Recorded job outcome: job={job_id}, status={outcome.outcome_status}"
            )
            
            await self._update_patterns_from_outcome(outcome, db)
            
            return outcome
            
        except Exception as e:
            if db:
                await db.rollback()
            self.logger.error(f"Error recording job outcome: {e}")
            raise
        finally:
            if should_close and db:
                await db.close()
    
    async def _update_patterns_from_outcome(
        self,
        outcome: JobOutcome,
        db: AsyncSession
    ) -> None:
        """Update patterns based on a new outcome."""
        try:
            if not outcome.job_title_normalized:
                return
            
            pattern_key = self.generate_pattern_key(
                job_title=outcome.job_title or "",
                department=outcome.department,
                seniority=outcome.seniority
            )
            
            pattern = await JobPatternRepository(db).get_active_pattern_by_key(
                company_id=outcome.company_id, pattern_key=pattern_key
            )
            
            is_success = outcome.is_successful
            
            if pattern:
                pattern.sample_count += 1
                if is_success:
                    pattern.success_count += 1
                
                if outcome.salary_min and outcome.salary_max:
                    (outcome.salary_min + outcome.salary_max) / 2
                    if pattern.avg_salary_min:
                        pattern.avg_salary_min = (pattern.avg_salary_min * (pattern.sample_count - 1) + outcome.salary_min) / pattern.sample_count
                        pattern.avg_salary_max = (pattern.avg_salary_max * (pattern.sample_count - 1) + outcome.salary_max) / pattern.sample_count
                    else:
                        pattern.avg_salary_min = outcome.salary_min
                        pattern.avg_salary_max = outcome.salary_max
                
                if outcome.skills:
                    skill_freq = dict(pattern.skill_frequency or {})
                    for skill in outcome.skills:
                        skill_freq[skill] = skill_freq.get(skill, 0) + 1
                    pattern.skill_frequency = skill_freq
                    
                    common = [k for k, v in sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)[:10]]
                    pattern.common_skills = common
                
                if outcome.behavioral_competencies:
                    behav_freq = dict(pattern.behavioral_frequency or {})
                    for comp in outcome.behavioral_competencies:
                        behav_freq[comp] = behav_freq.get(comp, 0) + 1
                    pattern.behavioral_frequency = behav_freq
                    
                    common = [k for k, v in sorted(behav_freq.items(), key=lambda x: x[1], reverse=True)[:5]]
                    pattern.common_behavioral = common
                
                if outcome.time_to_fill_days:
                    samples = list(pattern.time_to_fill_samples or [])
                    samples.append(outcome.time_to_fill_days)
                    samples = samples[-50:]
                    pattern.time_to_fill_samples = samples
                    pattern.avg_time_to_fill = int(mean(samples))
                    pattern.median_time_to_fill = int(median(samples))
                
                pattern.calculate_success_rate()
                pattern.update_confidence()
                pattern.last_sample_at = datetime.utcnow()
                pattern.updated_at = datetime.utcnow()
                
            else:
                pattern = JobPattern(
                    id=uuid4(),
                    company_id=outcome.company_id,
                    pattern_type="job_title",
                    pattern_key=pattern_key,
                    job_title_normalized=outcome.job_title_normalized,
                    department=outcome.department,
                    seniority=outcome.seniority,
                    location=outcome.location,
                    work_model=outcome.work_model,
                    sample_count=1,
                    success_count=1 if is_success else 0,
                    avg_salary_min=outcome.salary_min,
                    avg_salary_max=outcome.salary_max,
                    common_skills=outcome.skills or [],
                    skill_frequency={s: 1 for s in (outcome.skills or [])},
                    common_behavioral=outcome.behavioral_competencies or [],
                    behavioral_frequency={c: 1 for c in (outcome.behavioral_competencies or [])},
                    time_to_fill_samples=[outcome.time_to_fill_days] if outcome.time_to_fill_days else [],
                    avg_time_to_fill=outcome.time_to_fill_days,
                    last_sample_at=datetime.utcnow(),
                )
                pattern.calculate_success_rate()
                pattern.update_confidence()
                db.add(pattern)
            
            await self._update_salary_benchmark(outcome, db)
            
            outcome.processed_for_patterns = True
            
            await db.commit()
            
            self.logger.info(f"Updated patterns from outcome: {outcome.id}")
            
        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            self.logger.error(f"Error updating patterns from outcome: {e}")
    
    async def _update_salary_benchmark(
        self,
        outcome: JobOutcome,
        db: AsyncSession
    ) -> None:
        """Update salary benchmarks from outcome."""
        try:
            if not outcome.job_title_normalized:
                return
            if not outcome.salary_min and not outcome.salary_max:
                return
            
            benchmark = await JobPatternRepository(db).get_salary_benchmark_for_outcome(
                company_id=outcome.company_id,
                job_title_normalized=outcome.job_title_normalized,
                seniority=outcome.seniority.lower() if outcome.seniority else None,
            )
            
            salary = outcome.final_salary or ((outcome.salary_min or 0) + (outcome.salary_max or 0)) / 2
            
            if benchmark:
                samples = list(benchmark.salary_samples or [])
                samples.append(salary)
                samples = samples[-100:]
                
                benchmark.salary_samples = samples
                benchmark.sample_count = len(samples)
                
                sorted_samples = sorted(samples)
                n = len(sorted_samples)
                
                benchmark.min_salary = min(sorted_samples)
                benchmark.max_salary = max(sorted_samples)
                benchmark.avg_salary = mean(sorted_samples)
                benchmark.median_salary = median(sorted_samples)
                
                benchmark.percentile_10 = sorted_samples[int(n * 0.1)] if n > 0 else None
                benchmark.percentile_25 = sorted_samples[int(n * 0.25)] if n > 0 else None
                benchmark.percentile_50 = sorted_samples[int(n * 0.5)] if n > 0 else None
                benchmark.percentile_75 = sorted_samples[int(n * 0.75)] if n > 0 else None
                benchmark.percentile_90 = sorted_samples[int(n * 0.9)] if n > 0 else None
                
            else:
                benchmark = SalaryBenchmark(
                    id=uuid4(),
                    company_id=outcome.company_id,
                    job_title_normalized=outcome.job_title_normalized,
                    department=outcome.department,
                    seniority=outcome.seniority.lower() if outcome.seniority else None,
                    location=outcome.location,
                    work_model=outcome.work_model,
                    sample_count=1,
                    min_salary=salary,
                    max_salary=salary,
                    avg_salary=salary,
                    median_salary=salary,
                    salary_samples=[salary],
                )
                db.add(benchmark)
            
        except Exception as e:
            self.logger.error(f"Error updating salary benchmark: {e}")
    
    async def get_wizard_suggestions(
        self,
        company_id: str,
        job_title: str,
        department: str | None = None,
        seniority: str | None = None,
        location: str | None = None,
        existing_skills: list[str] | None = None,
        existing_behavioral: list[str] | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get all suggestions for the wizard in a single call.
        
        Combines salary, skills, behavioral, and TTF predictions.
        """
        should_close = db is None
        if db is None:
            db = AsyncSessionLocal()
        
        try:
            salary_suggestion = await self.get_salary_suggestion(
                company_id=company_id,
                job_title=job_title,
                seniority=seniority,
                location=location,
                department=department,
                db=db
            )
            
            skills_recommendation = await self.get_skills_recommendation(
                company_id=company_id,
                job_title=job_title,
                existing_skills=existing_skills,
                department=department,
                seniority=seniority,
                db=db
            )
            
            behavioral_recommendation = await self.get_behavioral_recommendation(
                company_id=company_id,
                job_title=job_title,
                existing_behavioral=existing_behavioral,
                department=department,
                seniority=seniority,
                db=db
            )
            
            ttf_prediction = await self.predict_time_to_fill(
                company_id=company_id,
                job_title=job_title,
                seniority=seniority,
                location=location,
                salary_min=salary_suggestion.get("min_salary"),
                salary_max=salary_suggestion.get("max_salary"),
                db=db
            )
            
            patterns = await self.find_similar_patterns(
                company_id=company_id,
                job_title=job_title,
                department=department,
                seniority=seniority,
                db=db
            )
            
            return {
                "has_suggestions": any([
                    salary_suggestion.get("has_suggestion"),
                    skills_recommendation.get("has_recommendations"),
                    behavioral_recommendation.get("has_recommendations"),
                    ttf_prediction.get("has_prediction"),
                ]),
                "salary": salary_suggestion,
                "skills": skills_recommendation,
                "behavioral": behavioral_recommendation,
                "time_to_fill": ttf_prediction,
                "patterns_found": len(patterns),
                "total_samples": sum(p.sample_count for p in patterns) if patterns else 0,
                "generated_at": datetime.utcnow().isoformat(),
            }
            
        except Exception as e:
            self.logger.error(f"Error getting wizard suggestions: {e}")
            return {"has_suggestions": False, "error": str(e)}
        finally:
            if should_close and db:
                await db.close()


job_pattern_service = JobPatternService()


def record_outcome_fire_and_forget(
    company_id: str,
    job_id: str,
    outcome_data: dict,
) -> None:
    """Fire-and-forget wrapper for sync callers (e.g., LangGraph publish_node).

    Spawns a daemon thread with its own asyncio event loop and calls
    record_job_outcome() on the singleton job_pattern_service.
    NEVER raises — failures are logged but never bubble up to the caller.

    Multi-tenancy: company_id required.
    Use case: publish_node (sync) fires async pattern learning after successful
    job creation, without blocking the wizard response to the recruiter.
    """
    import logging as _logging
    _log = _logging.getLogger(__name__)

    if not company_id or not job_id:
        _log.debug(
            "[JobPattern.fire_and_forget] missing required fields (company=%s job=%s)",
            bool(company_id), bool(job_id),
        )
        return

    import threading

    def _runner() -> None:
        import asyncio

        async def _run() -> None:
            try:
                await job_pattern_service.record_job_outcome(
                    company_id=company_id,
                    job_id=job_id,
                    outcome_data=outcome_data,
                )
            except Exception as exc:
                _log.warning(
                    "[JobPattern.fire_and_forget] record failed (job_id=%s): %s",
                    job_id, str(exc)[:200],
                )

        try:
            asyncio.run(_run())
        except Exception as exc:
            _log.warning(
                "[JobPattern.fire_and_forget] event loop error (job_id=%s): %s",
                job_id, str(exc)[:200],
            )

    t = threading.Thread(target=_runner, daemon=True, name=f"job-pattern-{job_id[:8]}")
    t.start()
