"""
Job Template Service for Fast Track creation.

Provides:
- Template CRUD operations
- Search and filtering
- AI enrichment for missing fields
- Learning from usage patterns
- Company-specific template creation
"""
import os
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.templates import (
    get_all_system_templates,
    get_template_categories,
)
from app.models.job_template import JobTemplate, TemplateUsageLog

WSI_QUALITY_GATES = {
    "min_technical_skills": 9,
    "min_behavioral_competencies": 5,
    "min_responsibilities": 5,
}


class WSIValidationError(Exception):
    """Raised when template doesn't meet WSI quality gates."""
    pass


def validate_wsi_quality(template_data: dict[str, Any], strict: bool = False) -> dict[str, Any]:
    """
    Validate template meets WSI quality gates.
    
    Args:
        template_data: Template data to validate
        strict: If True, raises exception; if False, returns warnings
        
    Returns:
        Dict with 'valid', 'warnings', and 'scores' keys
    """
    skills = template_data.get("default_skills", [])
    behavioral = template_data.get("default_behavioral", [])
    responsibilities = template_data.get("default_responsibilities", [])
    
    warnings = []
    scores = {
        "technical_skills": len(skills),
        "behavioral_competencies": len(behavioral),
        "responsibilities": len(responsibilities),
    }
    
    if len(skills) < WSI_QUALITY_GATES["min_technical_skills"]:
        warnings.append(
            f"Template needs at least {WSI_QUALITY_GATES['min_technical_skills']} technical skills "
            f"(has {len(skills)})"
        )
    
    if len(behavioral) < WSI_QUALITY_GATES["min_behavioral_competencies"]:
        warnings.append(
            f"Template needs at least {WSI_QUALITY_GATES['min_behavioral_competencies']} behavioral "
            f"competencies (has {len(behavioral)})"
        )
    
    if len(responsibilities) < WSI_QUALITY_GATES["min_responsibilities"]:
        warnings.append(
            f"Template needs at least {WSI_QUALITY_GATES['min_responsibilities']} responsibilities "
            f"(has {len(responsibilities)})"
        )
    
    valid = len(warnings) == 0
    
    if strict and not valid:
        raise WSIValidationError("; ".join(warnings))
    
    return {"valid": valid, "warnings": warnings, "scores": scores}


class JobTemplateService:
    """Service for managing job templates."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def validate_template(self, template_data: dict[str, Any], strict: bool = False) -> dict[str, Any]:
        """Validate template meets WSI quality gates."""
        return validate_wsi_quality(template_data, strict)
    
    async def get_template_by_id(self, template_id: UUID) -> JobTemplate | None:
        """Get a template by ID."""
        result = await self.db.execute(
            select(JobTemplate).where(JobTemplate.id == template_id)
        )
        return result.scalar_one_or_none()
    
    async def get_templates(
        self,
        company_id: UUID | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        seniority: str | None = None,
        include_system: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobTemplate]:
        """
        Get templates with filtering.
        
        Args:
            company_id: Filter by company (also includes system templates if include_system=True)
            category: Filter by category
            subcategory: Filter by subcategory
            seniority: Filter by seniority level
            include_system: Include system templates
            limit: Maximum results
            offset: Pagination offset
            
        Returns:
            List of JobTemplate objects
        """
        query = select(JobTemplate).where(JobTemplate.is_active == True)
        
        if company_id and include_system:
            query = query.where(
                or_(
                    JobTemplate.company_id == company_id,
                    JobTemplate.is_system == True
                )
            )
        elif company_id:
            query = query.where(JobTemplate.company_id == company_id)
        elif include_system:
            query = query.where(JobTemplate.is_system == True)
        
        if category:
            query = query.where(JobTemplate.category == category)
        if subcategory:
            query = query.where(JobTemplate.subcategory == subcategory)
        if seniority:
            query = query.where(JobTemplate.seniority == seniority)
        
        query = query.order_by(JobTemplate.popularity_score.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def search_templates(
        self,
        query: str,
        company_id: UUID | None = None,
        limit: int = 20,
    ) -> list[JobTemplate]:
        """
        Search templates by title or alternative titles.
        
        Args:
            query: Search query
            company_id: Optional company filter
            limit: Maximum results
            
        Returns:
            List of matching templates
        """
        query_lower = f"%{query.lower()}%"
        
        sql_query = (
            select(JobTemplate)
            .where(JobTemplate.is_active == True)
            .where(
                or_(
                    func.lower(JobTemplate.title).like(query_lower),
                    func.lower(JobTemplate.title_normalized).like(query_lower),
                    func.lower(func.array_to_string(JobTemplate.title_alternatives, ' ')).like(query_lower),
                )
            )
        )
        
        if company_id:
            sql_query = sql_query.where(
                or_(
                    JobTemplate.company_id == company_id,
                    JobTemplate.is_system == True
                )
            )
        else:
            sql_query = sql_query.where(JobTemplate.is_system == True)
        
        sql_query = sql_query.order_by(JobTemplate.popularity_score.desc())
        sql_query = sql_query.limit(limit)
        
        result = await self.db.execute(sql_query)
        return list(result.scalars().all())
    
    async def get_popular_templates(
        self,
        company_id: UUID | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[JobTemplate]:
        """Get most popular templates."""
        query = (
            select(JobTemplate)
            .where(JobTemplate.is_active == True)
            .order_by(JobTemplate.usage_count.desc())
            .limit(limit)
        )
        
        if category:
            query = query.where(JobTemplate.category == category)
        
        if company_id:
            query = query.where(
                or_(
                    JobTemplate.company_id == company_id,
                    JobTemplate.is_system == True
                )
            )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_template(self, template_data: dict[str, Any]) -> JobTemplate:
        """Create a new template."""
        template = JobTemplate(
            id=uuid4(),
            company_id=template_data.get("company_id"),
            parent_template_id=template_data.get("parent_template_id"),
            category=template_data["category"],
            subcategory=template_data["subcategory"],
            title=template_data["title"],
            title_normalized=JobTemplate.normalize_title(template_data["title"]),
            title_alternatives=template_data.get("title_alternatives", []),
            seniority=template_data["seniority"],
            default_description=template_data.get("default_description"),
            default_responsibilities=template_data.get("default_responsibilities", []),
            default_requirements=template_data.get("default_requirements"),
            default_nice_to_have=template_data.get("default_nice_to_have"),
            default_education=template_data.get("default_education", []),
            default_certifications=template_data.get("default_certifications", []),
            default_languages=template_data.get("default_languages", []),
            default_skills=template_data.get("default_skills", []),
            default_behavioral=template_data.get("default_behavioral", []),
            salary_range_min=template_data.get("salary_range_min"),
            salary_range_max=template_data.get("salary_range_max"),
            salary_currency=template_data.get("salary_currency", "BRL"),
            work_model=template_data.get("work_model", "hybrid"),
            employment_type=template_data.get("employment_type", "clt"),
            experience_years_min=template_data.get("experience_years_min"),
            experience_years_max=template_data.get("experience_years_max"),
            is_system=template_data.get("is_system", False),
            is_active=True,
            created_by=template_data.get("created_by"),
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        
        return template
    
    async def clone_template_for_company(
        self,
        template_id: UUID,
        company_id: UUID,
        modifications: dict[str, Any] | None = None,
    ) -> JobTemplate:
        """
        Clone a system template for a company with optional modifications.
        
        Args:
            template_id: Original template ID
            company_id: Company to clone for
            modifications: Optional field modifications
            
        Returns:
            New company-specific template
        """
        original = await self.get_template_by_id(template_id)
        if not original:
            raise ValueError(f"Template {template_id} not found")
        
        template_data = {
            "company_id": company_id,
            "parent_template_id": original.id,
            "category": original.category,
            "subcategory": original.subcategory,
            "title": original.title,
            "title_alternatives": original.title_alternatives or [],
            "seniority": original.seniority,
            "default_description": original.default_description,
            "default_responsibilities": original.default_responsibilities or [],
            "default_requirements": original.default_requirements,
            "default_nice_to_have": original.default_nice_to_have,
            "default_education": original.default_education or [],
            "default_certifications": original.default_certifications or [],
            "default_languages": original.default_languages or [],
            "default_skills": original.default_skills or [],
            "default_behavioral": original.default_behavioral or [],
            "salary_range_min": original.salary_range_min,
            "salary_range_max": original.salary_range_max,
            "work_model": original.work_model,
            "employment_type": original.employment_type,
            "experience_years_min": original.experience_years_min,
            "experience_years_max": original.experience_years_max,
            "is_system": False,
        }
        
        if modifications:
            template_data.update(modifications)
        
        return await self.create_template(template_data)
    
    async def use_template(
        self,
        template_id: UUID,
        company_id: UUID,
        user_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Use a template for job creation (Fast Track).
        
        Returns wizard-compatible data and logs usage.
        
        Args:
            template_id: Template to use
            company_id: Company using the template
            user_id: User using the template
            
        Returns:
            Wizard-compatible data dictionary
        """
        template = await self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        template.increment_usage()
        await self.db.commit()
        
        usage_log = TemplateUsageLog(
            id=uuid4(),
            template_id=template_id,
            company_id=company_id,
            user_id=user_id,
            action="fast_track_use",
        )
        self.db.add(usage_log)
        await self.db.commit()
        
        return template.to_wizard_data()
    
    async def log_template_feedback(
        self,
        template_id: UUID,
        company_id: UUID,
        job_id: UUID | None = None,
        fields_modified: list[str] | None = None,
        time_to_complete: int | None = None,
        feedback_rating: int | None = None,
    ) -> None:
        """Log template usage feedback for learning."""
        usage_log = TemplateUsageLog(
            id=uuid4(),
            template_id=template_id,
            company_id=company_id,
            job_id=job_id,
            action="completion_feedback",
            fields_modified=fields_modified or [],
            modifications_count=len(fields_modified) if fields_modified else 0,
            time_to_complete_seconds=time_to_complete,
            feedback_rating=feedback_rating,
        )
        self.db.add(usage_log)
        await self.db.commit()
    
    async def seed_system_templates(self) -> int:
        """
        Seed database with system templates.
        
        Returns:
            Number of templates created
        """
        templates_data = get_all_system_templates()
        count = 0
        
        for data in templates_data:
            existing = await self.db.execute(
                select(JobTemplate).where(
                    JobTemplate.is_system == True,
                    JobTemplate.title == data["title"],
                    JobTemplate.seniority == data["seniority"],
                )
            )
            if existing.scalar_one_or_none():
                continue
            
            await self.create_template(data)
            count += 1
        
        return count
    
    def get_categories(self) -> dict[str, Any]:
        """Get all template categories with metadata."""
        return get_template_categories()
    
    async def get_category_stats(self) -> dict[str, int]:
        """Get template count by category."""
        result = await self.db.execute(
            select(
                JobTemplate.category,
                func.count(JobTemplate.id).label("count")
            )
            .where(JobTemplate.is_active == True)
            .where(JobTemplate.is_system == True)
            .group_by(JobTemplate.category)
        )
        
        return {row.category: row.count for row in result}


async def enrich_template_with_ai(
    template_data: dict[str, Any],
    fields_to_enrich: list[str] | None = None,
) -> dict[str, Any]:
    """
    Enrich template with AI-generated content.
    
    Uses LLM to generate missing fields like:
    - Description
    - Responsibilities
    - Requirements
    - Skills suggestions
    
    Args:
        template_data: Existing template data
        fields_to_enrich: Specific fields to enrich (or all if None)
        
    Returns:
        Enriched template data
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        return template_data
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return template_data
    
    client = Anthropic(api_key=api_key)
    
    title = template_data.get("title", "")
    seniority = template_data.get("seniority", "pleno")
    category = template_data.get("category", "")
    
    fields_needing_enrichment = []
    if not fields_to_enrich:
        if not template_data.get("default_description"):
            fields_needing_enrichment.append("description")
        if not template_data.get("default_responsibilities"):
            fields_needing_enrichment.append("responsibilities")
        if not template_data.get("default_skills"):
            fields_needing_enrichment.append("skills")
    else:
        fields_needing_enrichment = fields_to_enrich
    
    if not fields_needing_enrichment:
        return template_data
    
    prompt = f"""Você é um especialista em descrição de vagas no Brasil.
    
Para a vaga de "{title}" (senioridade: {seniority}, área: {category}), gere:

{chr(10).join([f"- {field}" for field in fields_needing_enrichment])}

Responda em formato JSON com as chaves solicitadas.
Para skills, use formato: [{{"name": "...", "level": "basic/intermediate/advanced", "required": true/false}}]
Para responsibilities, use uma lista de strings com 5-7 itens.
Para description, escreva 2-3 parágrafos descrevendo a vaga.
"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        content = response.content[0].text
        
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end > start:
            enriched = json.loads(content[start:end])
            
            if "description" in enriched:
                template_data["default_description"] = enriched["description"]
            if "responsibilities" in enriched:
                template_data["default_responsibilities"] = enriched["responsibilities"]
            if "skills" in enriched:
                template_data["default_skills"] = enriched["skills"]
    except Exception:
        pass
    
    return template_data
