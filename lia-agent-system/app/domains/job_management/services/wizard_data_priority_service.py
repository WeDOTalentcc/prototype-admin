"""
Wizard Data Priority Service - Orchestrates data sources for intelligent suggestions.

Implements the Learning Loop priority system:
1. Company Settings (Menu Configurações) - 100% precision
2. LIA Platform History - 95% precision
3. Imported JDs from ATS - 85% precision
4. Workforce Planning / HRIS - 80% precision
5. Full ETL + Datalakes - 75% precision
6. Curated Templates (662) - 70% precision (fallback)

This service queries each source in priority order and returns the best
suggestion for each field in the job wizard.
"""
import logging
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.wizard_data_priority_repository import WizardDataPriorityRepository

from lia_models.company import Benefit, Department
from lia_models.company_learning import CompanyResponsibility, CompanySkill
from lia_models.imported_job_description import ClientSkillCatalog, ImportedJobDescription
from lia_models.job_pattern import JobPattern

logger = logging.getLogger(__name__)


class DataSource(StrEnum):
    """Available data sources in priority order."""
    COMPANY_SETTINGS = "company_settings"
    LIA_HISTORY = "lia_history"
    IMPORTED_ATS = "imported_ats"
    WORKFORCE_PLANNING = "workforce_planning"
    ETL_DATALAKES = "etl_datalakes"
    CURATED_TEMPLATES = "curated_templates"
    LLM_FALLBACK = "llm_fallback"


@dataclass
class Suggestion:
    """A suggestion from a data source."""
    value: Any
    source: DataSource
    confidence: float
    explanation: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "source": self.source.value,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


@dataclass
class JobContext:
    """Context for querying suggestions."""
    company_id: UUID
    job_title: str | None = None
    department: str | None = None
    seniority: str | None = None
    location: str | None = None
    work_model: str | None = None
    employment_type: str | None = None
    recruiter_id: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": str(self.company_id),
            "job_title": self.job_title,
            "department": self.department,
            "seniority": self.seniority,
            "location": self.location,
            "work_model": self.work_model,
            "employment_type": self.employment_type,
        }


class WizardDataPriorityService:
    """
    Service for querying data sources in priority order.
    
    Implements the Learning Loop by:
    1. Querying each source in priority order
    2. Returning first match with confidence > threshold
    3. Aggregating suggestions when multiple sources agree
    4. Providing explanations for each suggestion
    """
    
    PRIORITY_ORDER = [
        DataSource.COMPANY_SETTINGS,
        DataSource.LIA_HISTORY,
        DataSource.IMPORTED_ATS,
        DataSource.WORKFORCE_PLANNING,
        DataSource.ETL_DATALAKES,
        DataSource.CURATED_TEMPLATES,
    ]
    
    SOURCE_CONFIDENCE = {
        DataSource.COMPANY_SETTINGS: 1.0,
        DataSource.LIA_HISTORY: 0.95,
        DataSource.IMPORTED_ATS: 0.85,
        DataSource.WORKFORCE_PLANNING: 0.80,
        DataSource.ETL_DATALAKES: 0.75,
        DataSource.CURATED_TEMPLATES: 0.70,
        DataSource.LLM_FALLBACK: 0.60,
    }
    
    MINIMUM_CONFIDENCE = 0.7

    async def get_suggestion(
        self,
        db: AsyncSession,
        field: str,
        context: JobContext,
        include_all_sources: bool = False
    ) -> Suggestion | None:
        """
        Get the best suggestion for a field based on context.
        
        Args:
            db: Database session
            field: Field name (e.g., 'salary_range', 'skills', 'responsibilities')
            context: Job context with known values
            include_all_sources: If True, returns all suggestions (for comparison UI)
        
        Returns:
            Best suggestion or None if no match found
        """
        for source in self.PRIORITY_ORDER:
            suggestion = await self._query_source(db, source, field, context)
            if suggestion and suggestion.confidence >= self.MINIMUM_CONFIDENCE:
                return suggestion
        
        return None

    async def get_all_suggestions(
        self,
        db: AsyncSession,
        field: str,
        context: JobContext
    ) -> list[Suggestion]:
        """
        Get suggestions from all sources for comparison.
        
        Useful for showing the recruiter where each suggestion comes from.
        """
        suggestions = []
        
        for source in self.PRIORITY_ORDER:
            suggestion = await self._query_source(db, source, field, context)
            if suggestion:
                suggestions.append(suggestion)
        
        return suggestions

    async def get_field_suggestions(
        self,
        db: AsyncSession,
        context: JobContext,
        fields: list[str] | None = None
    ) -> dict[str, Suggestion]:
        """
        Get suggestions for multiple fields at once.
        
        More efficient than calling get_suggestion multiple times.
        """
        if fields is None:
            fields = [
                "job_title", "department", "seniority", "salary_range",
                "technical_skills", "behavioral_competencies", 
                "responsibilities", "benefits"
            ]
        
        results = {}
        for field in fields:
            suggestion = await self.get_suggestion(db, field, context)
            if suggestion:
                results[field] = suggestion
        
        return results

    async def _query_source(
        self,
        db: AsyncSession,
        source: DataSource,
        field: str,
        context: JobContext
    ) -> Suggestion | None:
        """Query a specific data source for a field suggestion."""
        
        query_methods = {
            DataSource.COMPANY_SETTINGS: self._query_company_settings,
            DataSource.LIA_HISTORY: self._query_lia_history,
            DataSource.IMPORTED_ATS: self._query_imported_ats,
            DataSource.WORKFORCE_PLANNING: self._query_workforce_planning,
            DataSource.CURATED_TEMPLATES: self._query_curated_templates,
        }
        
        query_method = query_methods.get(source)
        if query_method:
            return await query_method(db, field, context)
        
        return None

    async def _query_company_settings(
        self,
        db: AsyncSession,
        field: str,
        context: JobContext
    ) -> Suggestion | None:
        """Query company settings (Menu Configurações)."""
        
        if field == "department":
            departments = await WizardDataPriorityRepository(db).list_departments(
                str(context.company_id)
            )
            if departments:
                return Suggestion(
                    value=[d.name for d in departments],
                    source=DataSource.COMPANY_SETTINGS,
                    confidence=1.0,
                    explanation="Departamentos cadastrados nas configurações da empresa"
                )
        
        elif field == "benefits":
            benefits = await WizardDataPriorityRepository(db).list_benefits(
                str(context.company_id)
            )
            if benefits:
                return Suggestion(
                    value=[b.name for b in benefits],
                    source=DataSource.COMPANY_SETTINGS,
                    confidence=1.0,
                    explanation="Benefícios padrão cadastrados nas configurações"
                )
        
        return None

    async def _query_lia_history(
        self,
        db: AsyncSession,
        field: str,
        context: JobContext
    ) -> Suggestion | None:
        """Query LIA platform history (vagas criadas anteriormente)."""
        
        if field == "technical_skills":
            skills = await WizardDataPriorityRepository(db).list_promoted_technical_skills(
                str(context.company_id), limit=20
            )
            if skills:
                return Suggestion(
                    value=[{"name": s.skill_name, "category": s.category} for s in skills],
                    source=DataSource.LIA_HISTORY,
                    confidence=0.95,
                    explanation=f"Skills mais usadas em vagas anteriores ({len(skills)} skills)"
                )
        
        elif field == "responsibilities":
            responsibilities = await WizardDataPriorityRepository(db).list_promoted_responsibilities(
                str(context.company_id), limit=10
            )
            if responsibilities:
                return Suggestion(
                    value=[r.description for r in responsibilities],
                    source=DataSource.LIA_HISTORY,
                    confidence=0.95,
                    explanation="Responsabilidades frequentes em vagas anteriores"
                )
        
        elif field == "salary_range":
            if not context.job_title:
                return None
            
            pattern = await WizardDataPriorityRepository(db).find_top_job_pattern_by_title(
                company_id=context.company_id,
                job_title=context.job_title,
                min_samples=2,
            )
            if pattern and pattern.avg_salary_min:
                return Suggestion(
                    value={
                        "min": pattern.avg_salary_min,
                        "max": pattern.avg_salary_max,
                    },
                    source=DataSource.LIA_HISTORY,
                    confidence=0.95,
                    explanation=f"Baseado em {pattern.sample_count} vagas similares anteriores"
                )
        
        return None

    async def _query_imported_ats(
        self,
        db: AsyncSession,
        field: str,
        context: JobContext
    ) -> Suggestion | None:
        """Query imported JDs from ATS."""
        
        filters = [
            ImportedJobDescription.company_id == context.company_id,
            ImportedJobDescription.is_used_for_learning,
        ]
        
        if context.job_title:
            filters.append(
                or_(
                    ImportedJobDescription.job_title_normalized.ilike(f"%{context.job_title}%"),
                    ImportedJobDescription.job_title_original.ilike(f"%{context.job_title}%")
                )
            )
        
        if context.department:
            filters.append(ImportedJobDescription.department == context.department)
        
        if context.seniority:
            filters.append(ImportedJobDescription.seniority == context.seniority)
        
        jds = await WizardDataPriorityRepository(db).list_imported_jds(filters, limit=10)
        
        if not jds:
            return None
        
        if field == "technical_skills":
            all_skills = []
            for jd in jds:
                all_skills.extend(jd.technical_skills or [])
            
            skill_count = {}
            for skill in all_skills:
                name = skill.get("name", "") if isinstance(skill, dict) else skill
                skill_count[name] = skill_count.get(name, 0) + 1
            
            top_skills = sorted(skill_count.items(), key=lambda x: x[1], reverse=True)[:15]
            
            if top_skills:
                return Suggestion(
                    value=[{"name": s[0], "frequency": s[1]} for s in top_skills],
                    source=DataSource.IMPORTED_ATS,
                    confidence=0.85,
                    explanation=f"Skills mais frequentes em {len(jds)} JDs importados do ATS"
                )
        
        elif field == "responsibilities":
            all_responsibilities = []
            for jd in jds:
                all_responsibilities.extend(jd.responsibilities or [])
            
            unique = list(set(all_responsibilities))[:10]
            if unique:
                return Suggestion(
                    value=unique,
                    source=DataSource.IMPORTED_ATS,
                    confidence=0.85,
                    explanation=f"Responsabilidades extraídas de {len(jds)} JDs importados"
                )
        
        elif field == "salary_range":
            salaries = [(jd.salary_min, jd.salary_max) for jd in jds if jd.salary_min]
            if salaries:
                avg_min = sum(s[0] for s in salaries) / len(salaries)
                avg_max = sum(s[1] for s in salaries if s[1]) / len([s for s in salaries if s[1]]) if any(s[1] for s in salaries) else avg_min * 1.3
                
                return Suggestion(
                    value={"min": avg_min, "max": avg_max},
                    source=DataSource.IMPORTED_ATS,
                    confidence=0.85,
                    explanation=f"Média salarial de {len(salaries)} vagas similares importadas"
                )
        
        elif field == "benefits":
            all_benefits = []
            for jd in jds:
                all_benefits.extend(jd.benefits or [])
            
            benefit_count = {}
            for b in all_benefits:
                benefit_count[b] = benefit_count.get(b, 0) + 1
            
            top_benefits = sorted(benefit_count.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if top_benefits:
                return Suggestion(
                    value=[b[0] for b in top_benefits],
                    source=DataSource.IMPORTED_ATS,
                    confidence=0.85,
                    explanation="Benefícios mais oferecidos em vagas similares"
                )
        
        elif field == "behavioral_competencies":
            all_competencies = []
            for jd in jds:
                all_competencies.extend(jd.behavioral_competencies or [])
            
            comp_count = {}
            for c in all_competencies:
                name = c.get("name", "") if isinstance(c, dict) else c
                comp_count[name] = comp_count.get(name, 0) + 1
            
            top_comps = sorted(comp_count.items(), key=lambda x: x[1], reverse=True)[:5]
            
            if top_comps:
                return Suggestion(
                    value=[{"name": c[0], "frequency": c[1]} for c in top_comps],
                    source=DataSource.IMPORTED_ATS,
                    confidence=0.85,
                    explanation="Competências comportamentais frequentes em vagas similares"
                )
        
        return None

    async def _query_workforce_planning(
        self,
        db: AsyncSession,
        field: str,
        context: JobContext
    ) -> Suggestion | None:
        """Query workforce planning data (future implementation)."""
        return None

    async def _query_curated_templates(
        self,
        db: AsyncSession,
        field: str,
        context: JobContext
    ) -> Suggestion | None:
        """Query curated templates (662 templates)."""
        return None

    async def get_similar_jobs(
        self,
        db: AsyncSession,
        context: JobContext,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Find similar jobs from all sources.
        
        Returns jobs sorted by relevance for Fast Track mode.
        """
        similar = []
        
        filters = [ImportedJobDescription.company_id == context.company_id]
        
        if context.job_title:
            filters.append(
                or_(
                    ImportedJobDescription.job_title_normalized.ilike(f"%{context.job_title}%"),
                    ImportedJobDescription.job_title_original.ilike(f"%{context.job_title}%")
                )
            )
        
        jds = await WizardDataPriorityRepository(db).list_imported_jds(filters, limit=limit)
        
        for jd in jds:
            similar.append({
                "id": str(jd.id),
                "source": "imported_ats",
                "title": jd.job_title_original,
                "department": jd.department,
                "seniority": jd.seniority,
                "was_successful": jd.was_filled,
                "time_to_fill": jd.time_to_fill_days,
                "created_at": jd.created_at.isoformat() if jd.created_at else None,
                "can_use_as_template": True,
            })
        
        return similar

    async def get_data_coverage(
        self,
        db: AsyncSession,
        company_id: UUID
    ) -> dict[str, Any]:
        """
        Get data coverage statistics for a company.
        
        Shows which sources have data and coverage percentage.
        """
        counts = await WizardDataPriorityRepository(db).coverage_counts(company_id)
        imported = counts["imported"]
        skills = counts["skills"]
        patterns = counts["patterns"]
        
        coverage = {
            "imported_jds": imported,
            "skills_catalog": skills,
            "job_patterns": patterns,
            "coverage_score": min(100, (imported * 2 + skills + patterns) * 2),
            "recommendations": [],
        }
        
        if imported < 10:
            coverage["recommendations"].append(
                "Importe mais JDs do seu ATS para melhorar as sugestões"
            )
        if skills < 20:
            coverage["recommendations"].append(
                "O catálogo de skills ainda está pequeno - continue criando vagas"
            )
        
        return coverage


wizard_data_priority_service = WizardDataPriorityService()


def get_wizard_data_priority_service() -> "WizardDataPriorityService":
    return wizard_data_priority_service
