"""
Template Learning Service.

Learns from job creation patterns to:
- Create company-specific templates
- Improve template suggestions
- Track template effectiveness
- Enable the 80% faster 10th job creation goal
"""
import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_template import JobTemplate

logger = logging.getLogger(__name__)


class TemplateLearningService:
    """Service for learning from job creation patterns."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def learn_from_job_creation(
        self,
        company_id: UUID,
        job_data: dict[str, Any],
        template_used: UUID | None = None
    ) -> JobTemplate | None:
        """
        Learn from a completed job creation and potentially create a new template.
        
        Args:
            company_id: Company that created the job
            job_data: The job vacancy data used
            template_used: ID of template used (if any)
            
        Returns:
            New template if created, None otherwise
        """
        title = job_data.get("title", "")
        normalized_title = JobTemplate.normalize_title(title)
        
        similar_jobs = await self._find_similar_jobs(company_id, normalized_title)
        
        if len(similar_jobs) >= 3:
            existing_template = await self._check_existing_template(company_id, normalized_title)
            if not existing_template:
                return await self._create_learned_template(
                    company_id,
                    job_data,
                    similar_jobs
                )
        
        if template_used:
            await self._record_template_usage(template_used, company_id, job_data)
        
        return None
    
    async def _find_similar_jobs(
        self,
        company_id: UUID,
        normalized_title: str,
        days: int = 365
    ) -> list[dict]:
        """Find similar jobs created by the company."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            text("""
                SELECT 
                    id, title, department, seniority,
                    description, responsibilities, requirements,
                    tech_skills, behavioral_skills,
                    salary_min, salary_max, work_model
                FROM job_vacancies
                WHERE company_id = :company_id
                  AND created_at >= :cutoff
                  AND (
                    LOWER(title) LIKE :pattern
                    OR LOWER(COALESCE(title, '')) LIKE :pattern
                  )
                ORDER BY created_at DESC
                LIMIT 10
            """),
            {
                "company_id": str(company_id),
                "cutoff": cutoff,
                "pattern": f"%{normalized_title[:20]}%"
            }
        )
        
        jobs = []
        for row in result:
            jobs.append({
                "id": row[0],
                "title": row[1],
                "department": row[2],
                "seniority": row[3],
                "description": row[4],
                "responsibilities": row[5],
                "requirements": row[6],
                "tech_skills": row[7],
                "behavioral_skills": row[8],
                "salary_min": row[9],
                "salary_max": row[10],
                "work_model": row[11]
            })
        
        return jobs
    
    async def _check_existing_template(
        self,
        company_id: UUID,
        normalized_title: str
    ) -> JobTemplate | None:
        """Check if a template already exists for this pattern."""
        result = await self.db.execute(
            text("""
                SELECT id FROM job_templates
                WHERE company_id = :company_id
                  AND title_normalized LIKE :pattern
                  AND is_active = true
                LIMIT 1
            """),
            {
                "company_id": str(company_id),
                "pattern": f"%{normalized_title[:20]}%"
            }
        )
        return result.fetchone() is not None
    
    async def _create_learned_template(
        self,
        company_id: UUID,
        job_data: dict[str, Any],
        similar_jobs: list[dict]
    ) -> JobTemplate:
        """Create a new template learned from similar jobs."""
        merged_skills = self._merge_skills(similar_jobs)
        merged_behavioral = self._merge_behavioral(similar_jobs)
        merged_responsibilities = self._merge_responsibilities(similar_jobs)
        
        avg_salary_min = self._average_value(similar_jobs, "salary_min")
        avg_salary_max = self._average_value(similar_jobs, "salary_max")
        
        most_common_seniority = self._most_common(similar_jobs, "seniority") or "pleno"
        most_common_work_model = self._most_common(similar_jobs, "work_model") or "hybrid"
        
        category = self._infer_category(job_data.get("department", ""))
        
        title = job_data.get("title", "Learned Template")
        template = JobTemplate(
            id=uuid4(),
            company_id=company_id,
            category=category,
            subcategory="aprendido",
            title=title,
            title_normalized=JobTemplate.normalize_title(title),
            title_alternatives=[],
            seniority=most_common_seniority,
            default_description=job_data.get("description", ""),
            default_responsibilities=merged_responsibilities[:8],
            default_requirements=job_data.get("requirements", ""),
            default_skills=merged_skills[:10],
            default_behavioral=merged_behavioral[:5],
            salary_range_min=int(avg_salary_min) if avg_salary_min else None,
            salary_range_max=int(avg_salary_max) if avg_salary_max else None,
            work_model=most_common_work_model,
            is_system=False,
            is_active=True,
            template_metadata={
                "source": "learning",
                "learned_from_count": len(similar_jobs),
                "created_at": datetime.utcnow().isoformat()
            }
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        
        logger.info(f"Created learned template: {title} for company {company_id}")
        return template
    
    def _merge_skills(self, jobs: list[dict]) -> list[dict]:
        """Merge skills from similar jobs, keeping most common."""
        skill_counts = Counter()
        skill_details = {}
        
        for job in jobs:
            skills = job.get("tech_skills") or []
            if isinstance(skills, list):
                for skill in skills:
                    if isinstance(skill, dict):
                        name = skill.get("name", "")
                        if name:
                            skill_counts[name] += 1
                            skill_details[name] = skill
                    elif isinstance(skill, str):
                        skill_counts[skill] += 1
                        skill_details[skill] = {
                            "name": skill,
                            "category": "technical",
                            "level": "intermediate",
                            "weight": 1.0,
                            "required": True
                        }
        
        merged = []
        for name, count in skill_counts.most_common(10):
            detail = skill_details.get(name, {"name": name})
            detail["frequency"] = count / len(jobs)
            merged.append(detail)
        
        return merged
    
    def _merge_behavioral(self, jobs: list[dict]) -> list[dict]:
        """Merge behavioral competencies from similar jobs."""
        behavior_counts = Counter()
        behavior_details = {}
        
        for job in jobs:
            behaviors = job.get("behavioral_skills") or []
            if isinstance(behaviors, list):
                for behavior in behaviors:
                    if isinstance(behavior, dict):
                        name = behavior.get("name", "")
                        if name:
                            behavior_counts[name] += 1
                            behavior_details[name] = behavior
                    elif isinstance(behavior, str):
                        behavior_counts[behavior] += 1
                        behavior_details[behavior] = {
                            "name": behavior,
                            "weight": 1.0,
                            "justification": "Learned from historical jobs"
                        }
        
        merged = []
        for name, count in behavior_counts.most_common(5):
            detail = behavior_details.get(name, {"name": name})
            detail["frequency"] = count / len(jobs)
            merged.append(detail)
        
        return merged
    
    def _merge_responsibilities(self, jobs: list[dict]) -> list[str]:
        """Merge responsibilities from similar jobs."""
        resp_counts = Counter()
        
        for job in jobs:
            responsibilities = job.get("responsibilities") or []
            if isinstance(responsibilities, list):
                for resp in responsibilities:
                    if isinstance(resp, str) and len(resp) > 10:
                        resp.strip().lower()[:100]
                        resp_counts[resp] += 1
        
        return [resp for resp, _ in resp_counts.most_common(8)]
    
    def _average_value(self, jobs: list[dict], key: str) -> float | None:
        """Calculate average of a numeric field."""
        values = [j.get(key) for j in jobs if j.get(key)]
        if values:
            return sum(values) / len(values)
        return None
    
    def _most_common(self, jobs: list[dict], key: str) -> str | None:
        """Find most common value for a field."""
        values = [j.get(key) for j in jobs if j.get(key)]
        if values:
            counter = Counter(values)
            return counter.most_common(1)[0][0]
        return None
    
    def _infer_category(self, department: str) -> str:
        """Infer category from department name."""
        department_lower = department.lower() if department else ""
        
        mappings = {
            "tecnologia": ["ti", "tech", "desenvolvimento", "engineering", "data"],
            "financas": ["financeiro", "finance", "contabil", "fiscal"],
            "recursos_humanos": ["rh", "hr", "gente", "pessoas"],
            "vendas": ["vendas", "sales", "comercial"],
            "marketing": ["marketing", "comunicação", "digital"],
            "operacoes": ["operações", "operations", "logística"],
        }
        
        for category, keywords in mappings.items():
            if any(kw in department_lower for kw in keywords):
                return category
        
        return "geral"
    
    async def _record_template_usage(
        self,
        template_id: UUID,
        company_id: UUID,
        job_data: dict[str, Any]
    ) -> None:
        """Record template usage for analytics."""
        await self.db.execute(
            text("""
                UPDATE job_templates
                SET 
                    usage_count = usage_count + 1,
                    last_used_at = CURRENT_TIMESTAMP,
                    popularity_score = popularity_score + 0.1
                WHERE id = :template_id
            """),
            {"template_id": str(template_id)}
        )
        await self.db.commit()
    
    async def get_learning_stats(
        self,
        company_id: UUID
    ) -> dict[str, Any]:
        """Get learning statistics for a company."""
        result = await self.db.execute(
            text("""
                SELECT 
                    COUNT(*) as total_templates,
                    COUNT(*) FILTER (WHERE template_metadata->>'source' = 'learning') as learned_templates,
                    SUM(usage_count) as total_uses,
                    AVG(usage_count) as avg_uses
                FROM job_templates
                WHERE company_id = :company_id AND is_active = true
            """),
            {"company_id": str(company_id)}
        )
        
        row = result.fetchone()
        
        job_count = await self.db.execute(
            text("""
                SELECT COUNT(*) FROM job_vacancies
                WHERE company_id = :company_id
            """),
            {"company_id": str(company_id)}
        )
        total_jobs = job_count.fetchone()[0]
        
        return {
            "total_templates": row[0] or 0,
            "learned_templates": row[1] or 0,
            "total_template_uses": row[2] or 0,
            "avg_template_uses": float(row[3]) if row[3] else 0.0,
            "total_jobs_created": total_jobs,
            "learning_ratio": (row[1] or 0) / max(total_jobs, 1)
        }
    
    async def suggest_templates_for_improvement(
        self,
        company_id: UUID,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """Suggest job patterns that could benefit from templates."""
        result = await self.db.execute(
            text("""
                WITH job_patterns AS (
                    SELECT 
                        LOWER(SUBSTRING(title FROM 1 FOR 30)) as pattern,
                        COUNT(*) as count,
                        AVG(EXTRACT(EPOCH FROM (updated_at - created_at))/60) as avg_creation_time_min
                    FROM job_vacancies
                    WHERE company_id = :company_id
                      AND created_at >= CURRENT_DATE - INTERVAL '365 days'
                    GROUP BY LOWER(SUBSTRING(title FROM 1 FOR 30))
                    HAVING COUNT(*) >= 2
                )
                SELECT pattern, count, avg_creation_time_min
                FROM job_patterns
                WHERE pattern NOT IN (
                    SELECT LOWER(SUBSTRING(title_normalized FROM 1 FOR 30))
                    FROM job_templates
                    WHERE (company_id = :company_id OR is_system = true) AND is_active = true
                )
                ORDER BY count DESC, avg_creation_time_min DESC
                LIMIT :limit
            """),
            {"company_id": str(company_id), "limit": limit}
        )
        
        suggestions = []
        for row in result:
            suggestions.append({
                "pattern": row[0],
                "job_count": row[1],
                "avg_creation_time_minutes": round(row[2], 1) if row[2] else None,
                "potential_time_savings": f"{round((row[2] or 15) * 0.8, 1)} min per job"
            })
        
        return suggestions
