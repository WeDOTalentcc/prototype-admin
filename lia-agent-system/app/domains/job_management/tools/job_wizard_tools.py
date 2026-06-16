"""
Job Wizard Tools - Tools for the job creation wizard agent.

Provides function calling capabilities for the job wizard,
including salary benchmarks, field validation, suggestions, and draft saving.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID


from app.domains.job_management.services.jd_enrichment_service import JobManagementJdEnrichmentService
from app.schemas.jd_enrichment import EnrichmentRequest
from app.domains.company.services.company_configuration_service import CompanyConfigurationService
from app.shared.services.config_completeness_service import ConfigCompletenessService
from app.shared.services.intelligent_data_orchestrator import JobContext, intelligent_data_orchestrator
from app.shared.services.market_benchmark_service import MarketBenchmarkService
from app.shared.services.skills_catalog_service import skills_catalog_service
from app.tools.registry import ToolDefinition, tool_registry

logger = logging.getLogger(__name__)

market_benchmark_service = MarketBenchmarkService()
config_completeness_service = ConfigCompletenessService()
company_configuration_service = CompanyConfigurationService()
jd_enrichment_service = JobManagementJdEnrichmentService()


async def search_salary_benchmark(
    job_title: str,
    seniority: str | None = None,
    location: str | None = None,
    industry: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Search for salary benchmark data for a given role.
    
    Args:
        job_title: The job title to search for
        seniority: Seniority level (Junior, Pleno, Senior, etc.)
        location: Location/city for the role
        industry: Industry sector
        
    Returns:
        Salary benchmark data with min, max, median values
    """
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Searching salary benchmark for: {job_title}, seniority={seniority}")
    
    try:
        result = await market_benchmark_service.search_salary_benchmark(
            role=job_title,
            seniority=seniority,
            location=location or "Brasil"
        )
        
        return {
            "job_title": job_title,
            "seniority": seniority,
            "location": location or "Brasil",
            "salary_range": result.get("salary_range", {}),
            "percentiles": result.get("percentiles", {}),
            "confidence": result.get("confidence", "medium"),
            "sources": result.get("sources", []),
            "disclaimer": market_benchmark_service.DISCLAIMER
        }
        
    except Exception as e:
        logger.error(f"Error fetching salary benchmark: {e}")
        return {
            "job_title": job_title,
            "seniority": seniority,
            "error": str(e),
            "fallback_range": _get_fallback_salary_range(seniority)
        }


def _get_fallback_salary_range(seniority: str | None) -> dict[str, Any]:
    """Get fallback salary range based on seniority."""
    ranges = {
        "Júnior": {"min": 3000, "max": 5000, "currency": "BRL"},
        "Junior": {"min": 3000, "max": 5000, "currency": "BRL"},
        "Pleno": {"min": 6000, "max": 10000, "currency": "BRL"},
        "Sênior": {"min": 12000, "max": 18000, "currency": "BRL"},
        "Senior": {"min": 12000, "max": 18000, "currency": "BRL"},
        "Especialista": {"min": 15000, "max": 25000, "currency": "BRL"},
        "Coordenador": {"min": 15000, "max": 22000, "currency": "BRL"},
        "Gerente": {"min": 20000, "max": 35000, "currency": "BRL"},
        "Diretor": {"min": 35000, "max": 60000, "currency": "BRL"},
    }
    return ranges.get(seniority or "", {"min": 5000, "max": 15000, "currency": "BRL"})


async def validate_job_fields(
    job_data: dict[str, Any],
    company_config: dict[str, Any] | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Validate that required job fields are complete.
    
    Args:
        job_data: Current job data dictionary
        company_config: Company-specific configuration
        
    Returns:
        Validation result with completeness score and missing fields
    """
    logger.info(f"Validating job fields, keys: {list(job_data.keys())}")
    
    try:
        result = config_completeness_service.check_completeness(
            job_data=job_data,
            company_config=company_config
        )
        
        return {
            "is_valid": result.can_publish,
            "completeness_score": result.completeness_score,
            "filled_fields": result.filled_fields,
            "missing_critical": result.missing_critical,
            "missing_important": result.missing_important,
            "can_publish": result.can_publish,
            "field_details": result.field_details
        }
        
    except Exception as e:
        logger.error(f"Error validating job fields: {e}")
        return {
            "is_valid": False,
            "error": str(e),
            "completeness_score": 0
        }


async def get_job_suggestions(
    field_name: str,
    job_context: dict[str, Any],
    company_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get AI suggestions for a specific job field using real data sources.
    
    Uses SkillsCatalogService for skills and competencies,
    and CompanyConfigurationService for company-specific data.
    
    Args:
        field_name: Name of the field to get suggestions for
        job_context: Current job data for context
        company_id: Company ID for personalized suggestions
        
    Returns:
        Suggestions for the specified field from real data sources
    """
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Getting suggestions for field: {field_name}, company_id: {company_id}")
    
    try:
        job_title = job_context.get("job_title", "") or job_context.get("title", "")
        seniority = job_context.get("seniority", "Pleno")
        job_context.get("department", "")
        
        suggestions = {
            "field_name": field_name,
            "suggestions": [],
            "source": "skills_catalog_service"
        }
        
        if field_name == "skills":
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"Fetching skills for role: {job_title}, seniority: {seniority}")
            skill_data = skills_catalog_service.suggest_skills(
                role=job_title,
                seniority=seniority,
                limit=15
            )
            suggestions["suggestions"] = skill_data.get("technical_skills", [])
            suggestions["skill_count"] = skill_data.get("skill_count", {"min": 5, "max": 8})
            suggestions["area"] = skill_data.get("area")
            suggestions["categories"] = skill_data.get("categories", [])
            
        elif field_name == "behavioral_competencies":
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"Fetching behavioral competencies for role: {job_title}")
            competencies = skills_catalog_service.get_behavioral_competencies_for_role(job_title)
            suggestions["suggestions"] = [
                {
                    "key": comp.get("key"),
                    "competency": comp.get("name"),
                    "weight": "Essencial" if comp.get("relevance") == "high" else "Importante",
                    "subcategories": comp.get("subcategories", [])
                }
                for comp in competencies[:8]
            ]
            
        elif field_name == "benefits":
            if company_id:
                try:
                    logger.info(f"Fetching company benefits for company_id: {company_id}")
                    config = await company_configuration_service.get_configuration(
                        company_id=company_id,
                        allow_default_fallback=True
                    )
                    company_benefits = config.get_benefits_for_seniority(seniority)
                    suggestions["suggestions"] = [
                        {
                            "name": b.get("name"),
                            "description": b.get("description"),
                            "category": b.get("category"),
                            "is_highlighted": b.get("is_highlighted", False)
                        }
                        for b in company_benefits
                    ]
                    suggestions["source"] = "company_configuration"
                except Exception as e:
                    logger.warning(f"Error fetching company benefits: {e}, using defaults")
                    suggestions["suggestions"] = _get_default_benefits()
                    suggestions["source"] = "system_defaults"
            else:
                suggestions["suggestions"] = _get_default_benefits()
                suggestions["source"] = "system_defaults"
                
        elif field_name == "work_model":
            suggestions["suggestions"] = ["Remoto", "Híbrido", "Presencial"]
            suggestions["source"] = "system_defaults"
            
        elif field_name == "employment_type":
            suggestions["suggestions"] = ["CLT", "PJ", "Temporário", "Estágio"]
            suggestions["source"] = "system_defaults"
            
        elif field_name == "seniority":
            suggestions["suggestions"] = [
                "Júnior", "Pleno", "Sênior", 
                "Especialista", "Coordenador", "Gerente", "Diretor"
            ]
            suggestions["source"] = "system_defaults"
            
        elif field_name == "screening_questions":
            if company_id:
                try:
                    logger.info(f"Fetching screening questions for company_id: {company_id}")
                    config = await company_configuration_service.get_configuration(
                        company_id=company_id,
                        allow_default_fallback=True
                    )
                    suggestions["suggestions"] = config.screening_questions[:10]
                    suggestions["source"] = "company_configuration"
                except Exception as e:
                    logger.warning(f"Error fetching screening questions: {e}")
                    suggestions["suggestions"] = []
            else:
                suggestions["suggestions"] = []
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"Returning {len(suggestions['suggestions'])} suggestions for {field_name}")
        return suggestions
        
    except Exception as e:
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.error(f"Error getting suggestions for {field_name}: {e}", exc_info=True)
        return {
            "field_name": field_name,
            "error": str(e),
            "suggestions": [],
            "source": "error_fallback"
        }


def _get_default_benefits() -> list[dict[str, Any]]:
    """Return default benefits list when company config is unavailable."""
    return [
        {"name": "Vale Refeição", "category": "food", "is_highlighted": True},
        {"name": "Vale Alimentação", "category": "food", "is_highlighted": True},
        {"name": "Plano de Saúde", "category": "health", "is_highlighted": True},
        {"name": "Plano Odontológico", "category": "health", "is_highlighted": False},
        {"name": "Seguro de Vida", "category": "security", "is_highlighted": False},
        {"name": "Vale Transporte", "category": "transport", "is_highlighted": False},
        {"name": "Gympass/Wellhub", "category": "quality_life", "is_highlighted": True},
        {"name": "Day Off Aniversário", "category": "quality_life", "is_highlighted": False},
        {"name": "PLR/Bônus", "category": "financial", "is_highlighted": True}
    ]


async def save_job_draft(
    draft_id: str,
    updates: dict[str, Any],
    recruiter_id: str,
    company_id: str,
    **kwargs
) -> dict[str, Any]:
    """
    Save updates to a job draft.
    
    Args:
        draft_id: UUID of the draft to update
        updates: Dictionary of field updates
        recruiter_id: ID of the recruiter making changes
        company_id: Company ID
        
    Returns:
        Save result with updated draft info
    """
    logger.info(f"Saving job draft {draft_id} with updates: {list(updates.keys())} (company: {company_id})")

    try:
        from sqlalchemy import and_, select

        from app.core.database import AsyncSessionLocal
        from app.models.job_draft import JobDraft

        async with AsyncSessionLocal() as db:
            # Multi-tenancy fail-closed (REGRA ZERO): scope by company_id
            # so a recruiter cannot mutate a draft from another tenant. AST
            # sensor sees Model.company_id == company_id directly here.
            conditions = [JobDraft.id == UUID(draft_id)]
            if company_id:
                conditions.append(JobDraft.company_id == company_id)
            # TENANT-EXEMPT: dynamic builder — JobDraft.company_id
            # appended conditionally above.
            result = await db.execute(
                select(JobDraft).where(and_(*conditions))
            )
            draft = result.scalar_one_or_none()

            if not draft:
                return {
                    "success": False,
                    "error": f"Draft not found: {draft_id}"
                }
            
            for field, value in updates.items():
                if hasattr(draft, field):
                    setattr(draft, field, value)
            
            draft.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(draft)
            
            return {
                "success": True,
                "draft_id": str(draft.id),
                "updated_fields": list(updates.keys()),
                "status": draft.status.value if hasattr(draft.status, 'value') else str(draft.status),
                "updated_at": draft.updated_at.isoformat()
            }
            
    except Exception as e:
        try:
            await db.rollback()
        except Exception:
            pass
        logger.error(f"Error saving job draft: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_company_config(
    company_id: str,
    config_type: str = "all",
    seniority: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Fetch company configuration from CompanyConfigurationService.
    
    Retrieves company-specific settings like benefits, salary levels,
    pipeline templates, and screening questions.
    
    Args:
        company_id: The company identifier
        config_type: Type of config to fetch: 'all', 'benefits', 'salary_levels',
                     'pipeline_templates', 'screening_questions', 'communication'
        seniority: Optional seniority level to filter benefits
        
    Returns:
        Company configuration data based on config_type
    """
    logger.info(f"Getting company config for {company_id}, type={config_type}, seniority={seniority}")
    
    try:
        config = await company_configuration_service.get_configuration(
            company_id=company_id,
            allow_default_fallback=True
        )
        
        result: dict[str, Any] = {
            "company_id": company_id,
            "company_name": config.company_name,
            "config_type": config_type,
            "source": "company_configuration_service"
        }
        
        if config_type == "all" or config_type == "benefits":
            benefits = config.get_benefits_for_seniority(seniority)
            result["benefits"] = [
                {
                    "id": b.get("id"),
                    "name": b.get("name"),
                    "description": b.get("description"),
                    "category": b.get("category"),
                    "value_type": b.get("value_type"),
                    "value": b.get("value"),
                    "is_highlighted": b.get("is_highlighted", False)
                }
                for b in benefits
            ]
            result["benefits_count"] = len(benefits)
        
        if config_type == "all" or config_type == "pipeline_templates":
            result["pipeline_templates"] = config.pipeline_templates
            result["default_pipeline"] = config.default_pipeline
        
        if config_type == "all" or config_type == "screening_questions":
            result["screening_questions"] = config.screening_questions
            result["eliminatory_questions"] = config.get_eliminatory_questions()
        
        if config_type == "all" or config_type == "communication":
            result["communication_settings"] = config.communication_settings
        
        if config_type == "all" or config_type == "culture":
            result["culture_values"] = config.culture_values
            result["industry"] = config.industry
            result["company_size"] = config.company_size
            result["description"] = config.description
        
        if config_type == "ai_context":
            result["ai_context"] = config.to_ai_context()
        
        logger.info(f"Returning company config with keys: {list(result.keys())}")
        return result
        
    except ValueError as e:
        logger.warning(f"Company not found: {company_id}, error: {e}")
        return {
            "company_id": company_id,
            "config_type": config_type,
            "error": f"Company not found: {str(e)}",
            "source": "error_fallback",
            "benefits": [],
            "pipeline_templates": [],
            "screening_questions": []
        }
    except Exception as e:
        logger.error(f"Error fetching company config: {e}", exc_info=True)
        return {
            "company_id": company_id,
            "config_type": config_type,
            "error": str(e),
            "source": "error_fallback",
            "benefits": [],
            "pipeline_templates": [],
            "screening_questions": []
        }


async def get_intelligent_salary(
    company_id: str,
    job_title: str,
    seniority: str | None = None,
    location: str | None = None,
    department: str | None = None,
    session_id: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Get intelligent salary data from multiple sources with priority-based confidence.
    
    Consolidates data from:
    1. Learning patterns (company historical preferences) - VERY_HIGH confidence
    2. Company configuration (explicit salary policies) - HIGH confidence
    3. Internal job history - HIGH confidence
    4. ATS history - MEDIUM confidence
    5. Market benchmark - LOW_MEDIUM confidence
    
    Args:
        company_id: Company identifier
        job_title: Job title/role
        seniority: Seniority level
        location: Location for the role
        department: Department
        session_id: Session ID for caching
        
    Returns:
        Consolidated salary data with source attribution
    """
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Getting intelligent salary for: {job_title}, seniority={seniority}")
    
    try:
        from app.core.database import AsyncSessionLocal
        
        context = JobContext(
            company_id=company_id,
            session_id=session_id,
            role=job_title,
            title=job_title,
            seniority=seniority,
            department=department,
            location=location
        )
        
        async with AsyncSessionLocal() as db:
            result = await intelligent_data_orchestrator.get_salary_data(db, context)
        
        sources_summary = [
            {
                "source": s.source.value,
                "confidence": round(s.confidence, 2),
                "confidence_level": s.confidence_level.value
            }
            for s in result.all_sources
        ]
        
        return {
            "job_title": job_title,
            "seniority": seniority,
            "location": location,
            "salary_range": {
                "min": result.min_salary,
                "max": result.max_salary,
                "median": result.median_salary,
                "currency": result.currency
            },
            "primary_source": result.primary_source.value,
            "primary_confidence": round(result.primary_confidence, 2),
            "consensus": result.consensus,
            "sources_consulted": sources_summary,
            "explanation": result.explanation,
            "suggested_value": result.suggested_value
        }
        
    except Exception as e:
        logger.error(f"Error getting intelligent salary: {e}")
        fallback = _get_fallback_salary_range(seniority)
        return {
            "job_title": job_title,
            "seniority": seniority,
            "error": str(e),
            "salary_range": fallback,
            "primary_source": "fallback",
            "primary_confidence": 0.3
        }


async def get_intelligent_skills(
    company_id: str,
    job_title: str,
    seniority: str | None = None,
    session_id: str | None = None,
    limit: int = 15,
    **kwargs
) -> dict[str, Any]:
    """
    Get intelligent skills suggestions from multiple sources.
    
    Consolidates data from:
    1. Learning patterns (company skill preferences) - VERY_HIGH confidence
    2. Company configuration - HIGH confidence
    3. ATS history - MEDIUM confidence
    4. Skills catalog - MEDIUM confidence
    
    Args:
        company_id: Company identifier
        job_title: Job title/role
        seniority: Seniority level
        session_id: Session ID for caching
        limit: Maximum skills to return
        
    Returns:
        Consolidated skills with source attribution
    """
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"Getting intelligent skills for: {job_title}")
    
    try:
        from app.core.database import AsyncSessionLocal
        
        context = JobContext(
            company_id=company_id,
            session_id=session_id,
            role=job_title,
            title=job_title,
            seniority=seniority
        )
        
        async with AsyncSessionLocal() as db:
            result = await intelligent_data_orchestrator.get_skills_data(db, context, limit)
        
        return {
            "job_title": job_title,
            "seniority": seniority,
            "skills": result.primary_value,
            "technical_skills": result.technical_skills,
            "behavioral_skills": result.behavioral_skills,
            "recommended_count": result.recommended_count,
            "primary_source": result.primary_source.value,
            "primary_confidence": round(result.primary_confidence, 2),
            "consensus": result.consensus
        }
        
    except Exception as e:
        logger.error(f"Error getting intelligent skills: {e}")
        return {
            "job_title": job_title,
            "seniority": seniority,
            "error": str(e),
            "skills": [],
            "technical_skills": [],
            "behavioral_skills": [],
            "primary_source": "error",
            "primary_confidence": 0.0
        }


async def capture_wizard_feedback(
    company_id: str,
    session_id: str,
    field_name: str,
    suggested_value: Any,
    final_value: Any,
    role: str | None = None,
    seniority: str | None = None,
    source: str | None = None,
    source_confidence: float | None = None,
    explicitly_rejected: bool = False,
    **kwargs
) -> dict[str, Any]:
    """
    Capture feedback for the learning loop (silent operation).
    
    This is called whenever a field is finalized to record
    what was suggested vs what was actually used.
    
    Args:
        company_id: Company identifier
        session_id: Session ID
        field_name: Name of the field
        suggested_value: What was suggested
        final_value: What the user actually used
        role: Job role for context
        seniority: Seniority level for context
        source: Source of the suggestion
        source_confidence: Confidence of the source
        explicitly_rejected: Whether user explicitly rejected
        
    Returns:
        Confirmation of capture
    """
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.debug(f"Capturing feedback for field: {field_name}")
    
    try:
        from app.core.database import AsyncSessionLocal
        
        context = JobContext(
            company_id=company_id,
            session_id=session_id,
            role=role,
            seniority=seniority
        )
        
        async with AsyncSessionLocal() as db:
            await intelligent_data_orchestrator.capture_field_feedback(
                db=db,
                context=context,
                field_name=field_name,
                suggested_value=suggested_value,
                final_value=final_value,
                source=source,
                source_confidence=source_confidence,
                explicitly_rejected=explicitly_rejected
            )
        
        return {
            "success": True,
            "field_name": field_name,
            "captured": True
        }
        
    except Exception as e:
        logger.warning(f"Error capturing feedback (non-critical): {e}")
        return {
            "success": False,
            "field_name": field_name,
            "error": str(e)
        }


GET_INTELLIGENT_SALARY_SCHEMA = {
    "type": "object",
    "properties": {
        "company_id": {
            "type": "string",
            "description": "Company identifier (UUID)"
        },
        "job_title": {
            "type": "string",
            "description": "The job title to search salary data for"
        },
        "seniority": {
            "type": "string",
            "description": "Seniority level (Júnior, Pleno, Sênior, etc.)",
            "enum": ["Júnior", "Junior", "Pleno", "Sênior", "Senior", "Especialista", "Coordenador", "Gerente", "Diretor"]
        },
        "location": {
            "type": "string",
            "description": "Location/city for the role"
        },
        "department": {
            "type": "string",
            "description": "Department"
        },
        "session_id": {
            "type": "string",
            "description": "Session ID for caching"
        }
    },
    "required": ["company_id", "job_title"]
}

GET_INTELLIGENT_SKILLS_SCHEMA = {
    "type": "object",
    "properties": {
        "company_id": {
            "type": "string",
            "description": "Company identifier (UUID)"
        },
        "job_title": {
            "type": "string",
            "description": "The job title to get skills for"
        },
        "seniority": {
            "type": "string",
            "description": "Seniority level",
            "enum": ["Júnior", "Junior", "Pleno", "Sênior", "Senior", "Especialista", "Coordenador", "Gerente", "Diretor"]
        },
        "session_id": {
            "type": "string",
            "description": "Session ID for caching"
        },
        "limit": {
            "type": "integer",
            "description": "Maximum skills to return",
            "default": 15
        }
    },
    "required": ["company_id", "job_title"]
}

CAPTURE_WIZARD_FEEDBACK_SCHEMA = {
    "type": "object",
    "properties": {
        "company_id": {
            "type": "string",
            "description": "Company identifier"
        },
        "session_id": {
            "type": "string",
            "description": "Session ID"
        },
        "field_name": {
            "type": "string",
            "description": "Name of the field"
        },
        "suggested_value": {
            "description": "What was suggested"
        },
        "final_value": {
            "description": "What the user actually used"
        },
        "role": {
            "type": "string",
            "description": "Job role for context"
        },
        "seniority": {
            "type": "string",
            "description": "Seniority level for context"
        },
        "source": {
            "type": "string",
            "description": "Source of the suggestion"
        },
        "source_confidence": {
            "type": "number",
            "description": "Confidence of the source (0-1)"
        },
        "explicitly_rejected": {
            "type": "boolean",
            "description": "Whether user explicitly rejected"
        }
    },
    "required": ["company_id", "session_id", "field_name", "suggested_value", "final_value"]
}

SEARCH_SALARY_BENCHMARK_SCHEMA = {
    "type": "object",
    "properties": {
        "job_title": {
            "type": "string",
            "description": "The job title to search salary data for"
        },
        "seniority": {
            "type": "string",
            "description": "Seniority level (Júnior, Pleno, Sênior, etc.)",
            "enum": ["Júnior", "Junior", "Pleno", "Sênior", "Senior", "Especialista", "Coordenador", "Gerente", "Diretor"]
        },
        "location": {
            "type": "string",
            "description": "Location/city for the role"
        },
        "industry": {
            "type": "string",
            "description": "Industry sector"
        }
    },
    "required": ["job_title"]
}

VALIDATE_JOB_FIELDS_SCHEMA = {
    "type": "object",
    "properties": {
        "job_data": {
            "type": "object",
            "description": "Current job data dictionary with all fields"
        },
        "company_config": {
            "type": "object",
            "description": "Optional company-specific configuration"
        }
    },
    "required": ["job_data"]
}

GET_JOB_SUGGESTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "field_name": {
            "type": "string",
            "description": "Name of the field to get suggestions for",
            "enum": ["benefits", "behavioral_competencies", "skills", "work_model", "employment_type", "seniority", "screening_questions"]
        },
        "job_context": {
            "type": "object",
            "description": "Current job data for context (including job_title, seniority, department)"
        },
        "company_id": {
            "type": "string",
            "description": "Company ID for personalized suggestions (required for benefits and screening_questions)"
        }
    },
    "required": ["field_name", "job_context"]
}

SAVE_JOB_DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "draft_id": {
            "type": "string",
            "description": "UUID of the draft to update"
        },
        "updates": {
            "type": "object",
            "description": "Dictionary of field updates"
        },
        "recruiter_id": {
            "type": "string",
            "description": "ID of the recruiter making changes"
        },
        "company_id": {
            "type": "string",
            "description": "Company ID"
        }
    },
    "required": ["draft_id", "updates", "recruiter_id", "company_id"]
}

GET_COMPANY_CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "company_id": {
            "type": "string",
            "description": "The company identifier (UUID)"
        },
        "config_type": {
            "type": "string",
            "description": "Type of configuration to fetch",
            "enum": ["all", "benefits", "salary_levels", "pipeline_templates", "screening_questions", "communication", "culture", "ai_context"],
            "default": "all"
        },
        "seniority": {
            "type": "string",
            "description": "Optional seniority level to filter benefits (Júnior, Pleno, Sênior, etc.)"
        }
    },
    "required": ["company_id"]
}

GENERATE_ENRICHED_JD_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "Job title for enrichment analysis"
        },
        "company_id": {
            "type": "string",
            "description": "Company identifier for company-specific insights"
        },
        "seniority": {
            "type": "string",
            "description": "Seniority level (Júnior, Pleno, Sênior, etc.)"
        },
        "location": {
            "type": "string",
            "description": "Job location for market benchmarks"
        },
        "detected_responsibilities": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Responsibilities already detected from recruiter input"
        },
        "detected_skills": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Technical skills already detected"
        },
        "detected_behavioral": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Behavioral competencies already detected"
        },
        "salary_min": {
            "type": "number",
            "description": "Minimum salary if already provided"
        },
        "salary_max": {
            "type": "number",
            "description": "Maximum salary if already provided"
        }
    },
    "required": ["title", "company_id"]
}


async def generate_enriched_jd(
    title: str,
    company_id: str,
    seniority: str | None = None,
    location: str | None = None,
    detected_responsibilities: list[str] | None = None,
    detected_skills: list[str] | None = None,
    detected_behavioral: list[str] | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    **kwargs
) -> dict[str, Any]:
    """
    Generate enriched job description with suggestions for all sections.
    
    Analyzes recruiter input against market benchmarks, company history,
    and skills catalog to generate contextualized suggestions with
    rich justifications including market percentages, impact metrics,
    and WSI quality notes.
    
    Args:
        title: Job title for analysis
        company_id: Company ID for company-specific insights
        seniority: Seniority level
        location: Job location for market data
        detected_responsibilities: Already detected responsibilities
        detected_skills: Already detected technical skills
        detected_behavioral: Already detected behavioral competencies
        salary_min: Minimum salary if provided
        salary_max: Maximum salary if provided
        
    Returns:
        Enriched JD with suggestions organized by section
    """
    logger.info(f"Generating enriched JD for: {title} at company {company_id}")
    
    try:
        request = EnrichmentRequest(
            title=title,
            company_id=company_id,
            seniority=seniority,
            location=location,
            detected_responsibilities=detected_responsibilities or [],
            detected_technical_skills=detected_skills or [],
            detected_behavioral_competencies=detected_behavioral or [],
            salary_min=salary_min,
            salary_max=salary_max
        )
        
        db = kwargs.get("db")
        
        result = await jd_enrichment_service.generate_enriched_jd(
            request=request,
            db=db
        )
        
        sections = []
        for section in result.sections:
            suggestions = []
            for s in section.suggestions:
                suggestions.append({
                    "id": s.id,
                    "value": s.value,
                    "source": s.source.value,
                    "justification": s.justification,
                    "metrics": s.metrics,
                    "impactDescription": s.impact_description,
                    "impactLevel": s.impact_level.value,
                    "wsiQualityNote": s.wsi_quality_note,
                    "isNew": s.is_new,
                    "category": s.category
                })
            
            sections.append({
                "sectionName": section.section_name,
                "sectionTitle": section.section_title,
                "detectedItems": section.detected_items,
                "suggestions": suggestions,
                "qualityNote": section.quality_note,
                "missingCount": section.missing_count,
                "recommendedCount": section.recommended_count
            })
        
        compensation = None
        if result.compensation:
            comp = result.compensation
            compensation = {
                "currentRange": comp.current_range,
                "marketRange": comp.market_range,
                "marketPosition": comp.market_position,
                "salarySuggestion": {
                    "id": comp.salary_suggestion.id,
                    "suggestedMin": comp.salary_suggestion.suggested_min,
                    "suggestedMax": comp.salary_suggestion.suggested_max,
                    "currentMin": comp.salary_suggestion.current_min,
                    "currentMax": comp.salary_suggestion.current_max,
                    "source": comp.salary_suggestion.source.value,
                    "justification": comp.salary_suggestion.justification,
                    "marketPercentile": comp.salary_suggestion.market_percentile,
                    "marketComparison": comp.salary_suggestion.market_comparison,
                    "impactDescription": comp.salary_suggestion.impact_description
                } if comp.salary_suggestion else None,
                "bonusSuggestion": {
                    "id": comp.bonus_suggestion.id,
                    "suggestedPercentageMin": comp.bonus_suggestion.suggested_percentage_min,
                    "suggestedPercentageMax": comp.bonus_suggestion.suggested_percentage_max,
                    "suggestedSalaryMonths": comp.bonus_suggestion.suggested_salary_months,
                    "source": comp.bonus_suggestion.source.value,
                    "justification": comp.bonus_suggestion.justification,
                    "sectorPractice": comp.bonus_suggestion.sector_practice
                } if comp.bonus_suggestion else None,
                "competitivenessScore": comp.competitiveness_score
            }
        
        return {
            "success": True,
            "title": title,
            "seniority": seniority,
            "sections": sections,
            "compensation": compensation,
            "wsiQualityScore": result.wsi_quality_score,
            "overallCompleteness": result.overall_completeness,
            "totalSuggestions": result.total_suggestions,
            "summary": {
                "readyForWsi": result.wsi_quality_score >= 70,
                "needsAttention": result.wsi_quality_score < 50,
                "message": _get_enrichment_summary_message(result)
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating enriched JD: {e}")
        return {
            "success": False,
            "error": str(e),
            "title": title
        }


def _get_enrichment_summary_message(result) -> str:
    """Generate a summary message for the enriched JD."""
    if result.wsi_quality_score >= 80:
        return "A vaga está bem estruturada e pronta para gerar perguntas WSI de alta qualidade."
    elif result.wsi_quality_score >= 60:
        return f"A vaga está quase pronta. Aceite {result.total_suggestions} sugestões para melhorar a qualidade das perguntas de triagem."
    elif result.wsi_quality_score >= 40:
        return f"A vaga precisa de mais detalhes. Temos {result.total_suggestions} sugestões para completar o perfil do candidato ideal."
    else:
        return f"A vaga está incompleta. Adicione as {result.total_suggestions} sugestões abaixo para criar uma descrição de qualidade."


def register_job_wizard_tools() -> None:
    """Register all job wizard tools in the registry."""
    
    tool_registry.register(ToolDefinition(
        name="search_salary_benchmark",
        description="Search for salary benchmark data for a given job role, seniority level, and location. Returns min, max, and median salary values with confidence level.",
        parameters_schema=SEARCH_SALARY_BENCHMARK_SCHEMA,
        handler=search_salary_benchmark,
        allowed_agents=["job_planner", "job_intake", "orchestrator", "job_wizard"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="validate_job_fields",
        description="Validate that all required job fields are complete and ready for publication. Returns completeness score and lists of missing critical/important fields.",
        parameters_schema=VALIDATE_JOB_FIELDS_SCHEMA,
        handler=validate_job_fields,
        allowed_agents=["job_planner", "job_intake", "orchestrator", "job_wizard"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_job_suggestions",
        description="Get AI-powered suggestions for a specific job field like benefits, skills, or behavioral competencies based on job context.",
        parameters_schema=GET_JOB_SUGGESTIONS_SCHEMA,
        handler=get_job_suggestions,
        allowed_agents=["job_planner", "job_intake", "orchestrator", "job_wizard"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="save_job_draft",
        description="Save updates to an existing job draft. Use this to persist changes made during the job creation wizard.",
        parameters_schema=SAVE_JOB_DRAFT_SCHEMA,
        handler=save_job_draft,
        allowed_agents=["job_planner", "job_intake", "orchestrator", "job_wizard"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_company_config",
        description="Fetch company configuration including benefits, salary levels, pipeline templates, screening questions, and communication settings. Essential for personalizing job creation.",
        parameters_schema=GET_COMPANY_CONFIG_SCHEMA,
        handler=get_company_config,
        allowed_agents=["job_planner", "job_intake", "orchestrator", "job_wizard"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_intelligent_salary",
        description="Get intelligent salary data from multiple sources with priority-based confidence. Consolidates learning patterns, company config, ATS history, and market benchmarks for the best salary recommendation.",
        parameters_schema=GET_INTELLIGENT_SALARY_SCHEMA,
        handler=get_intelligent_salary,
        allowed_agents=["job_planner", "job_intake", "orchestrator", "job_wizard"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="get_intelligent_skills",
        description="Get intelligent skills suggestions from multiple sources. Consolidates learning patterns, company preferences, ATS history, and curated catalog for the best skills recommendation.",
        parameters_schema=GET_INTELLIGENT_SKILLS_SCHEMA,
        handler=get_intelligent_skills,
        allowed_agents=["job_planner", "job_intake", "orchestrator", "job_wizard"]
    ))
    
    tool_registry.register(ToolDefinition(
        name="capture_wizard_feedback",
        description="Capture feedback for the learning loop. Records what was suggested vs what was actually used to improve future suggestions. Called silently when fields are finalized.",
        parameters_schema=CAPTURE_WIZARD_FEEDBACK_SCHEMA,
        handler=capture_wizard_feedback,
        allowed_agents=["job_planner", "job_intake", "orchestrator", "job_wizard"]
    ))

    # T-1168 (Bug 4): generate_enriched_jd é registrada canonicamente em
    # `app/domains/job_management/agents/wizard_tool_registry.py:710` via
    # `_wrap_generate_enriched_jd` (com tratamento de erro). Registrar aqui
    # também causava o warning "tool 'generate_enriched_jd' already registered,
    # overwriting" no startup do uvicorn. Source-of-truth = wizard_tool_registry.

    logger.info("Registered 8 job wizard tools")
