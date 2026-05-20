"""
Job Insights Service - Provides intelligent suggestions based on historical job data.

This service queries the JobVacancy table to provide:
- Salary benchmarks based on similar past jobs
- Common skills for roles
- Similar job listings
- Time to fill metrics
- Success metrics from closed positions
"""
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCRUDRepository

from lia_models.job_vacancy import JobVacancy

logger = logging.getLogger(__name__)


@dataclass
class SalaryBenchmark:
    min: float
    max: float
    median: float
    average: float
    sample_size: int
    confidence: str
    based_on: str
    trend: str
    data_freshness_days: int


@dataclass
class SkillFrequency:
    skill: str
    category: str
    frequency: int
    percentage: float
    is_required: bool


@dataclass
class TimeToFillMetrics:
    average_days: float
    median_days: float
    min_days: int
    max_days: int
    sample_size: int
    confidence: str
    based_on: str


@dataclass
class SimilarJob:
    id: str
    title: str
    department: str | None
    seniority: str | None
    location: str | None
    work_model: str | None
    status: str
    created_at: datetime
    closed_at: datetime | None
    similarity_score: float


def _coerce_str_param(value, field_name: str, logger_obj=None):
    """Defensive: callers sometimes pass dict (e.g. structured location/salary).

    Extract canonical string or return None. Logs unexpected types so we can fix upstream.
    Root cause hardening for bug 2026-05-20 "dict object has no attribute lower".
    """
    if value is None or value == "":
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for k in ("name", "title", "label", "value", "city", "text"):
            v = value.get(k)
            if isinstance(v, str) and v:
                if logger_obj:
                    logger_obj.warning(
                        "job_insights_service received dict for %s, extracted from key %s",
                        field_name, k,
                        extra={"input_type": type(value).__name__, "field": field_name, "extracted_key": k},
                    )
                return v
        if logger_obj:
            logger_obj.warning(
                "job_insights_service received dict for %s with no usable string key; treating as None",
                field_name,
                extra={"input_type": type(value).__name__, "field": field_name, "keys": list(value.keys())},
            )
        return None
    if logger_obj:
        logger_obj.warning(
            "job_insights_service received unexpected type for %s, coercing via str()",
            field_name,
            extra={"input_type": type(value).__name__, "field": field_name},
        )
    return str(value)



class JobInsightsService:
    """
    Service for querying historical job data to provide intelligent suggestions.
    
    Features:
    - Salary benchmarking based on role/seniority/location
    - Common skills analysis
    - Similar job matching
    - Time to fill predictions
    - Success metrics from closed positions
    """
    
    MONTHS_FOR_ANALYSIS = 12
    HIGH_CONFIDENCE_THRESHOLD = 20
    MEDIUM_CONFIDENCE_THRESHOLD = 10
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _calculate_confidence(self, sample_size: int) -> str:
        """Calculate confidence level based on sample size."""
        if sample_size >= self.HIGH_CONFIDENCE_THRESHOLD:
            return "high"
        elif sample_size >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            return "medium"
        elif sample_size > 0:
            return "low"
        return "none"
    
    def _calculate_trend(self, values_by_date: list[tuple]) -> str:
        """
        Calculate salary trend based on historical data.
        Returns: 'increasing', 'decreasing', 'stable'
        """
        if len(values_by_date) < 4:
            return "stable"
        
        sorted_values = sorted(values_by_date, key=lambda x: x[0])
        
        first_half = sorted_values[:len(sorted_values)//2]
        second_half = sorted_values[len(sorted_values)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        avg_first = statistics.mean([v[1] for v in first_half])
        avg_second = statistics.mean([v[1] for v in second_half])
        
        change_pct = ((avg_second - avg_first) / avg_first) * 100 if avg_first > 0 else 0
        
        if change_pct > 5:
            return "increasing"
        elif change_pct < -5:
            return "decreasing"
        return "stable"
    
    def _normalize_role_for_search(self, role: str) -> list[str]:
        """Generate variations of role for fuzzy matching."""
        variations = [role.lower()]
        
        role_mappings = {
            "desenvolvedor": ["developer", "dev", "engenheiro de software", "software engineer"],
            "analista": ["analyst", "especialista"],
            "gerente": ["manager", "gestor", "head", "líder", "lider"],
            "coordenador": ["coordinator", "supervisor"],
            "diretor": ["director", "vp", "head"],
            "product manager": ["pm", "gerente de produto", "product owner"],
            "tech lead": ["líder técnico", "lead developer", "arquiteto"],
            "data scientist": ["cientista de dados", "ml engineer", "machine learning"],
            "devops": ["sre", "platform engineer", "infrastructure"],
            "ux designer": ["ui designer", "product designer", "designer de produto"],
        }
        
        role_lower = role.lower()
        for key, synonyms in role_mappings.items():
            if key in role_lower or any(syn in role_lower for syn in synonyms):
                variations.extend(synonyms)
                variations.append(key)
        
        return list(set(variations))
    
    async def get_salary_benchmark(
        self,
        db: AsyncSession,
        company_id: str,
        role: str,
        seniority: str | None = None,
        location: str | None = None,
        work_model: str | None = None,
        months_back: int = 12
    ) -> dict[str, Any]:
        """
        Get salary benchmark based on similar past jobs.
        
        Args:
            db: Database session
            company_id: Company ID for scoping
            role: Job role/title
            seniority: Seniority level (Júnior, Pleno, Sênior, Especialista)
            location: Location filter
            work_model: Work model (remoto, híbrido, presencial)
            months_back: How many months back to analyze
        
        Returns:
            Dictionary with salary statistics and confidence
        """
        try:
            # Defensive coercion: upstream callers may pass dict (e.g. structured location)
            # Root cause hardening for bug 2026-05-20 "dict object has no attribute lower".
            role = _coerce_str_param(role, "role", self.logger) or ""
            seniority = _coerce_str_param(seniority, "seniority", self.logger)
            location = _coerce_str_param(location, "location", self.logger)
            work_model = _coerce_str_param(work_model, "work_model", self.logger)

            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            
            role_variations = self._normalize_role_for_search(role)
            role_conditions = or_(*[
                func.lower(JobVacancy.title).contains(var)
                for var in role_variations
            ])
            
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.created_at >= cutoff_date,
                JobVacancy.salary_range.isnot(None),
                role_conditions
            ]
            
            if seniority:
                conditions.append(func.lower(JobVacancy.seniority_level) == seniority.lower())
            
            if location:
                conditions.append(
                    or_(
                        func.lower(JobVacancy.location).contains(location.lower()),
                        JobVacancy.location.is_(None)
                    )
                )
            
            if work_model:
                conditions.append(
                    or_(
                        func.lower(JobVacancy.work_model) == work_model.lower(),
                        JobVacancy.work_model.is_(None)
                    )
                )
            
            query = select(
                JobVacancy.salary_range,
                JobVacancy.created_at
            ).where(and_(*conditions))
            
            result = await db.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return self._empty_salary_response(role, seniority)
            
            min_salaries = []
            max_salaries = []
            values_by_date = []
            
            for row in rows:
                salary_range = row.salary_range
                if isinstance(salary_range, dict):
                    min_val = salary_range.get("min")
                    max_val = salary_range.get("max")
                    if min_val is not None:
                        min_salaries.append(float(min_val))
                    if max_val is not None:
                        max_salaries.append(float(max_val))
                    if min_val and max_val:
                        avg_salary = (float(min_val) + float(max_val)) / 2
                        values_by_date.append((row.created_at, avg_salary))
            
            if not min_salaries or not max_salaries:
                return self._empty_salary_response(role, seniority)
            
            sample_size = len(min_salaries)
            oldest_date = min(row.created_at for row in rows)
            data_freshness_days = (datetime.utcnow() - oldest_date).days
            
            confidence = self._calculate_confidence(sample_size)
            trend = self._calculate_trend(values_by_date)
            
            all_midpoints = [(min_s + max_s) / 2 for min_s, max_s in zip(min_salaries, max_salaries)]
            
            description_parts = [f"{sample_size} vagas similares"]
            if seniority:
                description_parts.append(f"nível {seniority}")
            if location:
                description_parts.append(f"em {location}")
            description_parts.append(f"nos últimos {months_back} meses")
            
            return {
                "min": round(statistics.mean(min_salaries), 2),
                "max": round(statistics.mean(max_salaries), 2),
                "median": round(statistics.median(all_midpoints), 2),
                "average": round(statistics.mean(all_midpoints), 2),
                "percentile_25": round(sorted(all_midpoints)[int(len(all_midpoints) * 0.25)] if len(all_midpoints) >= 4 else min(all_midpoints), 2),
                "percentile_75": round(sorted(all_midpoints)[int(len(all_midpoints) * 0.75)] if len(all_midpoints) >= 4 else max(all_midpoints), 2),
                "sample_size": sample_size,
                "confidence": confidence,
                "based_on": " ".join(description_parts),
                "trend": trend,
                "data_freshness_days": data_freshness_days,
                "currency": "BRL"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting salary benchmark: {e}")
            return self._empty_salary_response(role, seniority, error=str(e))
    
    def _empty_salary_response(
        self,
        role: str,
        seniority: str | None = None,
        error: str | None = None
    ) -> dict[str, Any]:
        """Return empty salary response when no data is available."""
        return {
            "min": None,
            "max": None,
            "median": None,
            "average": None,
            "sample_size": 0,
            "confidence": "none",
            "based_on": f"Nenhuma vaga similar encontrada para {role}" + (f" nível {seniority}" if seniority else ""),
            "trend": "unknown",
            "data_freshness_days": None,
            "currency": "BRL",
            "error": error
        }
    
    async def get_common_skills(
        self,
        db: AsyncSession,
        company_id: str,
        department: str | None = None,
        role: str | None = None,
        months_back: int = 12,
        limit: int = 20
    ) -> dict[str, Any]:
        """
        Get most frequently used skills for similar roles.
        
        Args:
            db: Database session
            company_id: Company ID for scoping
            department: Department filter
            role: Role/title filter
            months_back: How many months back to analyze
            limit: Maximum skills to return
        
        Returns:
            Dictionary with skill frequencies and categories
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.created_at >= cutoff_date,
                JobVacancy.technical_requirements.isnot(None)
            ]
            
            if department:
                conditions.append(func.lower(JobVacancy.department) == department.lower())
            
            if role:
                role_variations = self._normalize_role_for_search(role)
                role_conditions = or_(*[
                    func.lower(JobVacancy.title).contains(var)
                    for var in role_variations
                ])
                conditions.append(role_conditions)
            
            query = select(
                JobVacancy.technical_requirements,
                JobVacancy.behavioral_competencies
            ).where(and_(*conditions))
            
            result = await db.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return self._empty_skills_response(department, role)
            
            skill_counts: dict[str, dict[str, Any]] = {}
            total_jobs = len(rows)
            
            for row in rows:
                tech_reqs = row.technical_requirements or []
                for req in tech_reqs:
                    if isinstance(req, dict):
                        skill = req.get("technology", req.get("skill", ""))
                        category = req.get("category", "Técnico")
                        is_required = req.get("required", False)
                        
                        if skill:
                            key = f"{skill}|{category}"
                            if key not in skill_counts:
                                skill_counts[key] = {
                                    "skill": skill,
                                    "category": category,
                                    "count": 0,
                                    "required_count": 0
                                }
                            skill_counts[key]["count"] += 1
                            if is_required:
                                skill_counts[key]["required_count"] += 1
                
                behavioral = row.behavioral_competencies or []
                for comp in behavioral:
                    if isinstance(comp, dict):
                        skill = comp.get("competency", comp.get("name", ""))
                        weight = comp.get("weight", "Desejável")
                        is_required = weight in ["Essencial", "Obrigatório"]
                        
                        if skill:
                            key = f"{skill}|Comportamental"
                            if key not in skill_counts:
                                skill_counts[key] = {
                                    "skill": skill,
                                    "category": "Comportamental",
                                    "count": 0,
                                    "required_count": 0
                                }
                            skill_counts[key]["count"] += 1
                            if is_required:
                                skill_counts[key]["required_count"] += 1
            
            skills_list = []
            for data in skill_counts.values():
                skills_list.append({
                    "skill": data["skill"],
                    "category": data["category"],
                    "frequency": data["count"],
                    "percentage": round((data["count"] / total_jobs) * 100, 1),
                    "is_commonly_required": data["required_count"] > data["count"] / 2
                })
            
            skills_list.sort(key=lambda x: x["frequency"], reverse=True)
            skills_list = skills_list[:limit]
            
            categories_summary = {}
            for skill in skills_list:
                cat = skill["category"]
                if cat not in categories_summary:
                    categories_summary[cat] = {"count": 0, "top_skills": []}
                categories_summary[cat]["count"] += 1
                if len(categories_summary[cat]["top_skills"]) < 5:
                    categories_summary[cat]["top_skills"].append(skill["skill"])
            
            confidence = self._calculate_confidence(total_jobs)
            
            return {
                "skills": skills_list,
                "categories_summary": categories_summary,
                "total_jobs_analyzed": total_jobs,
                "confidence": confidence,
                "based_on": f"Análise de {total_jobs} vagas" + 
                           (f" em {department}" if department else "") +
                           (f" para {role}" if role else "") +
                           f" nos últimos {months_back} meses"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting common skills: {e}")
            return self._empty_skills_response(department, role, error=str(e))
    
    def _empty_skills_response(
        self,
        department: str | None = None,
        role: str | None = None,
        error: str | None = None
    ) -> dict[str, Any]:
        """Return empty skills response when no data is available."""
        return {
            "skills": [],
            "categories_summary": {},
            "total_jobs_analyzed": 0,
            "confidence": "none",
            "based_on": "Nenhuma vaga encontrada" + 
                       (f" em {department}" if department else "") +
                       (f" para {role}" if role else ""),
            "error": error
        }
    
    async def get_similar_jobs(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        department: str | None = None,
        seniority: str | None = None,
        location: str | None = None,
        work_model: str | None = None,
        exclude_job_id: str | None = None,
        limit: int = 10
    ) -> dict[str, Any]:
        """
        Find similar jobs based on criteria.
        
        Args:
            db: Database session
            company_id: Company ID for scoping
            role: Role/title to match
            department: Department filter
            seniority: Seniority level
            location: Location filter
            work_model: Work model filter
            exclude_job_id: Job ID to exclude from results
            limit: Maximum jobs to return
        
        Returns:
            Dictionary with list of similar jobs and match details
        """
        try:
            conditions = [JobVacancy.company_id == company_id]
            
            if exclude_job_id:
                conditions.append(JobVacancy.id != exclude_job_id)
            
            query = select(
                JobVacancy.id,
                JobVacancy.title,
                JobVacancy.department,
                JobVacancy.seniority_level,
                JobVacancy.location,
                JobVacancy.work_model,
                JobVacancy.status,
                JobVacancy.created_at,
                JobVacancy.closed_at,
                JobVacancy.salary_range,
                JobVacancy.technical_requirements
            ).where(and_(*conditions)).order_by(JobVacancy.created_at.desc())
            
            result = await db.execute(query)
            rows = result.fetchall()
            
            similar_jobs = []
            
            for row in rows:
                score = self._calculate_similarity_score(
                    row=row,
                    target_role=role,
                    target_department=department,
                    target_seniority=seniority,
                    target_location=location,
                    target_work_model=work_model
                )
                
                if score > 0:
                    similar_jobs.append({
                        "id": str(row.id),
                        "title": row.title,
                        "department": row.department,
                        "seniority": row.seniority_level,
                        "location": row.location,
                        "work_model": row.work_model,
                        "status": row.status,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "closed_at": row.closed_at.isoformat() if row.closed_at else None,
                        "similarity_score": score,
                        "has_salary": row.salary_range is not None
                    })
            
            similar_jobs.sort(key=lambda x: x["similarity_score"], reverse=True)
            similar_jobs = similar_jobs[:limit]
            
            return {
                "similar_jobs": similar_jobs,
                "total_matches": len(similar_jobs),
                "search_criteria": {
                    "role": role,
                    "department": department,
                    "seniority": seniority,
                    "location": location,
                    "work_model": work_model
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error finding similar jobs: {e}")
            return {
                "similar_jobs": [],
                "total_matches": 0,
                "search_criteria": {
                    "role": role,
                    "department": department,
                    "seniority": seniority,
                    "location": location,
                    "work_model": work_model
                },
                "error": str(e)
            }
    
    def _calculate_similarity_score(
        self,
        row,
        target_role: str | None = None,
        target_department: str | None = None,
        target_seniority: str | None = None,
        target_location: str | None = None,
        target_work_model: str | None = None
    ) -> float:
        """Calculate similarity score between a job and target criteria."""
        score = 0.0
        max_score = 0.0
        
        if target_role:
            max_score += 40
            role_variations = self._normalize_role_for_search(target_role)
            if row.title:
                title_lower = row.title.lower()
                if any(var in title_lower for var in role_variations):
                    score += 40
                elif any(word in title_lower for word in target_role.lower().split()):
                    score += 20
        
        if target_department:
            max_score += 20
            if row.department and row.department.lower() == target_department.lower():
                score += 20
        
        if target_seniority:
            max_score += 20
            if row.seniority_level and row.seniority_level.lower() == target_seniority.lower():
                score += 20
            elif row.seniority_level:
                seniority_map = {
                    "júnior": 1, "junior": 1,
                    "pleno": 2,
                    "sênior": 3, "senior": 3,
                    "especialista": 4, "staff": 4
                }
                target_level = seniority_map.get(target_seniority.lower(), 0)
                actual_level = seniority_map.get(row.seniority_level.lower(), 0)
                if abs(target_level - actual_level) == 1:
                    score += 10
        
        if target_location:
            max_score += 10
            if row.location and target_location.lower() in row.location.lower():
                score += 10
        
        if target_work_model:
            max_score += 10
            if row.work_model and row.work_model.lower() == target_work_model.lower():
                score += 10
        
        if max_score == 0:
            return 0.5
        
        return round(score / max_score, 2)
    
    async def get_time_to_fill(
        self,
        db: AsyncSession,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
        department: str | None = None,
        months_back: int = 24
    ) -> dict[str, Any]:
        """
        Get average time to fill similar positions.
        
        Args:
            db: Database session
            company_id: Company ID for scoping
            role: Role/title filter
            seniority: Seniority level filter
            department: Department filter
            months_back: How many months back to analyze
        
        Returns:
            Dictionary with time to fill metrics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.created_at >= cutoff_date,
                JobVacancy.closed_at.isnot(None),
                JobVacancy.status.in_(["Concluída", "Fechada", "Preenchida", "closed", "filled"])
            ]
            
            if role:
                role_variations = self._normalize_role_for_search(role)
                role_conditions = or_(*[
                    func.lower(JobVacancy.title).contains(var)
                    for var in role_variations
                ])
                conditions.append(role_conditions)
            
            if seniority:
                conditions.append(func.lower(JobVacancy.seniority_level) == seniority.lower())
            
            if department:
                conditions.append(func.lower(JobVacancy.department) == department.lower())
            
            query = select(
                JobVacancy.created_at,
                JobVacancy.closed_at,
                JobVacancy.open_date
            ).where(and_(*conditions))
            
            result = await db.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return self._empty_time_to_fill_response(role, seniority)
            
            days_to_fill = []
            for row in rows:
                start_date = row.open_date or row.created_at
                if start_date and row.closed_at:
                    diff = (row.closed_at - start_date).days
                    if diff >= 0:
                        days_to_fill.append(diff)
            
            if not days_to_fill:
                return self._empty_time_to_fill_response(role, seniority)
            
            sample_size = len(days_to_fill)
            confidence = self._calculate_confidence(sample_size)
            
            description_parts = [f"{sample_size} vagas fechadas"]
            if role:
                description_parts.append(f"para {role}")
            if seniority:
                description_parts.append(f"nível {seniority}")
            description_parts.append(f"nos últimos {months_back} meses")
            
            return {
                "average_days": round(statistics.mean(days_to_fill), 1),
                "median_days": round(statistics.median(days_to_fill), 1),
                "min_days": min(days_to_fill),
                "max_days": max(days_to_fill),
                "percentile_25": sorted(days_to_fill)[int(len(days_to_fill) * 0.25)] if len(days_to_fill) >= 4 else min(days_to_fill),
                "percentile_75": sorted(days_to_fill)[int(len(days_to_fill) * 0.75)] if len(days_to_fill) >= 4 else max(days_to_fill),
                "sample_size": sample_size,
                "confidence": confidence,
                "based_on": " ".join(description_parts)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting time to fill: {e}")
            return self._empty_time_to_fill_response(role, seniority, error=str(e))
    
    def _empty_time_to_fill_response(
        self,
        role: str | None = None,
        seniority: str | None = None,
        error: str | None = None
    ) -> dict[str, Any]:
        """Return empty time to fill response when no data is available."""
        return {
            "average_days": None,
            "median_days": None,
            "min_days": None,
            "max_days": None,
            "sample_size": 0,
            "confidence": "none",
            "based_on": "Nenhuma vaga fechada encontrada" + 
                       (f" para {role}" if role else "") +
                       (f" nível {seniority}" if seniority else ""),
            "error": error
        }
    
    async def get_success_metrics(
        self,
        db: AsyncSession,
        company_id: str,
        job_id: str | None = None,
        role: str | None = None,
        seniority: str | None = None,
        department: str | None = None
    ) -> dict[str, Any]:
        """
        Get metrics from successfully filled similar jobs.
        
        If job_id is provided, finds similar jobs to that job.
        Otherwise uses role/seniority/department filters.
        
        Args:
            db: Database session
            company_id: Company ID for scoping
            job_id: Optional specific job ID to find similar filled jobs
            role: Role/title filter
            seniority: Seniority level filter
            department: Department filter
        
        Returns:
            Dictionary with success metrics
        """
        try:
            if job_id:
                job = await JobVacancyCRUDRepository(db).get_by_id_strict_company(
                    job_id, company_id
                )
                
                if job:
                    role = str(job.title) if job.title is not None else None
                    seniority = str(job.seniority_level) if job.seniority_level is not None else None
                    department = str(job.department) if job.department is not None else None
            
            conditions = [
                JobVacancy.company_id == company_id,
                JobVacancy.closed_at.isnot(None),
                JobVacancy.status.in_(["Concluída", "Fechada", "Preenchida", "closed", "filled"])
            ]
            
            if role:
                role_variations = self._normalize_role_for_search(role)
                role_conditions = or_(*[
                    func.lower(JobVacancy.title).contains(var)
                    for var in role_variations
                ])
                conditions.append(role_conditions)
            
            if seniority:
                conditions.append(func.lower(JobVacancy.seniority_level) == seniority.lower())
            
            if department:
                conditions.append(func.lower(JobVacancy.department) == department.lower())
            
            query = select(
                JobVacancy.id,
                JobVacancy.title,
                JobVacancy.created_at,
                JobVacancy.closed_at,
                JobVacancy.open_date,
                JobVacancy.funnel_data,
                JobVacancy.lia_metrics,
                JobVacancy.nps,
                JobVacancy.salary_range
            ).where(and_(*conditions)).order_by(JobVacancy.closed_at.desc())
            
            result = await db.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return self._empty_success_metrics_response(role, seniority, department)
            
            total_jobs = len(rows)
            
            days_to_fill = []
            nps_scores = []
            candidates_screened = []
            interviews_conducted = []
            
            for row in rows:
                start_date = row.open_date or row.created_at
                if start_date and row.closed_at:
                    diff = (row.closed_at - start_date).days
                    if diff >= 0:
                        days_to_fill.append(diff)
                
                if row.nps is not None:
                    nps_scores.append(row.nps)
                
                if row.funnel_data and isinstance(row.funnel_data, dict):
                    if "screening" in row.funnel_data:
                        candidates_screened.append(row.funnel_data["screening"])
                    if "interview" in row.funnel_data:
                        interviews_conducted.append(row.funnel_data["interview"])
            
            confidence = self._calculate_confidence(total_jobs)
            
            return {
                "total_filled_jobs": total_jobs,
                "time_to_fill": {
                    "average_days": round(statistics.mean(days_to_fill), 1) if days_to_fill else None,
                    "median_days": round(statistics.median(days_to_fill), 1) if days_to_fill else None,
                    "fastest_days": min(days_to_fill) if days_to_fill else None,
                    "slowest_days": max(days_to_fill) if days_to_fill else None
                },
                "candidate_satisfaction": {
                    "average_nps": round(statistics.mean(nps_scores), 1) if nps_scores else None,
                    "nps_count": len(nps_scores)
                },
                "funnel_metrics": {
                    "avg_candidates_screened": round(statistics.mean(candidates_screened), 1) if candidates_screened else None,
                    "avg_interviews_conducted": round(statistics.mean(interviews_conducted), 1) if interviews_conducted else None
                },
                "confidence": confidence,
                "based_on": f"{total_jobs} vagas preenchidas com sucesso" +
                           (f" para {role}" if role else "") +
                           (f" nível {seniority}" if seniority else "") +
                           (f" em {department}" if department else "")
            }
            
        except Exception as e:
            self.logger.error(f"Error getting success metrics: {e}")
            return self._empty_success_metrics_response(role, seniority, department, error=str(e))
    
    def _empty_success_metrics_response(
        self,
        role: str | None = None,
        seniority: str | None = None,
        department: str | None = None,
        error: str | None = None
    ) -> dict[str, Any]:
        """Return empty success metrics response when no data is available."""
        return {
            "total_filled_jobs": 0,
            "time_to_fill": {
                "average_days": None,
                "median_days": None,
                "fastest_days": None,
                "slowest_days": None
            },
            "candidate_satisfaction": {
                "average_nps": None,
                "nps_count": 0
            },
            "funnel_metrics": {
                "avg_candidates_screened": None,
                "avg_interviews_conducted": None
            },
            "confidence": "none",
            "based_on": "Nenhuma vaga preenchida encontrada" +
                       (f" para {role}" if role else "") +
                       (f" nível {seniority}" if seniority else "") +
                       (f" em {department}" if department else ""),
            "error": error
        }
    
    async def get_all_insights(
        self,
        db: AsyncSession,
        company_id: str,
        role: str,
        seniority: str | None = None,
        department: str | None = None,
        location: str | None = None,
        work_model: str | None = None
    ) -> dict[str, Any]:
        """
        Get all insights for a job creation flow.
        
        Combines salary benchmark, common skills, similar jobs, time to fill,
        and success metrics into a single response.
        
        Args:
            db: Database session
            company_id: Company ID for scoping
            role: Job role/title
            seniority: Seniority level
            department: Department
            location: Location
            work_model: Work model
        
        Returns:
            Dictionary with all insights
        """
        salary = await self.get_salary_benchmark(
            db=db,
            company_id=company_id,
            role=role,
            seniority=seniority,
            location=location,
            work_model=work_model
        )
        
        skills = await self.get_common_skills(
            db=db,
            company_id=company_id,
            department=department,
            role=role
        )
        
        similar = await self.get_similar_jobs(
            db=db,
            company_id=company_id,
            role=role,
            department=department,
            seniority=seniority,
            location=location,
            work_model=work_model,
            limit=5
        )
        
        time_to_fill = await self.get_time_to_fill(
            db=db,
            company_id=company_id,
            role=role,
            seniority=seniority,
            department=department
        )
        
        success = await self.get_success_metrics(
            db=db,
            company_id=company_id,
            role=role,
            seniority=seniority,
            department=department
        )
        
        return {
            "salary_benchmark": salary,
            "common_skills": skills,
            "similar_jobs": similar,
            "time_to_fill": time_to_fill,
            "success_metrics": success,
            "generated_at": datetime.utcnow().isoformat()
        }


job_insights_service = JobInsightsService()


def get_job_insights_service() -> "JobInsightsService":
    return job_insights_service
