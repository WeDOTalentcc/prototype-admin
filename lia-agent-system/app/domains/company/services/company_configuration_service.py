"""
Company Configuration Service - Unified configuration provider for AI agents.

This service consolidates all company-specific configurations needed by agents:
- Company profile and culture
- Benefits packages
- Pipeline templates
- Default screening questions
- Communication settings

Features:
- In-memory cache with configurable TTL
- Async database operations
- Formatted output for AI prompts
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID as UUID_type

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.communication.repositories.communication_settings_repository import (
    CommunicationSettingsRepository,
)
from app.domains.company.repositories.benefit_repository import BenefitRepository
from app.domains.company.services.benefits_service import (
    BENEFIT_CATEGORIES,
    BENEFIT_CATEGORY_ICONS,
    resolve_benefit_category,
)
from app.domains.company.repositories.company_profile_repository import (
    CompanyProfileRepository,
)
from app.domains.pipeline.repositories.pipeline_template_repository import (
    PipelineTemplateRepository,
)
from app.domains.recruitment.repositories.company_screening_question_repository import (
    CompanyScreeningQuestionRepository,
)
from lia_models.communication_settings import CommunicationSettings
from lia_models.company import Benefit, CompanyProfile
from lia_models.pipeline_template import PipelineTemplate
from lia_models.screening_question import CompanyScreeningQuestion

logger = logging.getLogger(__name__)


def _to_uuid(company_id: str) -> UUID_type | None:
    """Convert string to UUID, returns None if invalid."""
    try:
        return UUID_type(company_id)
    except (ValueError, TypeError):
        return None


@dataclass
class CompanyConfiguration:
    """Complete company configuration for AI agents."""
    company_id: str
    company_name: str
    industry: str | None = None
    company_size: str | None = None
    description: str | None = None
    culture_values: list[dict[str, Any]] = field(default_factory=list)
    benefits: list[dict[str, Any]] = field(default_factory=list)
    pipeline_templates: list[dict[str, Any]] = field(default_factory=list)
    default_pipeline: dict[str, Any] | None = None
    screening_questions: list[dict[str, Any]] = field(default_factory=list)
    communication_settings: dict[str, Any] | None = None
    loaded_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_ai_context(self) -> str:
        """Format configuration as context for AI prompts."""
        lines = [
            f"## Contexto da Empresa: {self.company_name}",
            f"- Indústria: {self.industry or 'Não especificada'}",
            f"- Porte: {self.company_size or 'Não especificado'}",
        ]
        
        if self.description:
            lines.append(f"- Descrição: {self.description[:200]}...")
        
        if self.culture_values:
            lines.append("\n### Valores Culturais:")
            for value in self.culture_values[:5]:
                lines.append(f"  - {value.get('name', 'N/A')}: {value.get('description', '')[:100]}")
        
        if self.benefits:
            lines.append(f"\n### Benefícios Disponíveis ({len(self.benefits)}):")
            highlighted = [b for b in self.benefits if b.get('is_highlighted')]
            for benefit in highlighted[:5]:
                lines.append(f"  - ⭐ {benefit.get('name', 'N/A')}: {benefit.get('description', '')[:80]}")
            if len(self.benefits) > 5:
                lines.append(f"  - ... e mais {len(self.benefits) - 5} benefícios")
        
        if self.default_pipeline:
            lines.append(f"\n### Pipeline Padrão: {self.default_pipeline.get('name', 'N/A')}")
            stages = self.default_pipeline.get('stages', [])
            for stage in stages[:6]:
                lines.append(f"  {stage.get('order', '?')}. {stage.get('name', 'N/A')} ({stage.get('sla_days', '?')} dias)")
        
        if self.screening_questions:
            lines.append(f"\n### Perguntas de Triagem Padrão ({len(self.screening_questions)}):")
            for q in self.screening_questions[:5]:
                eliminatory = "⚠️ Eliminatória" if q.get('is_eliminatory') else ""
                lines.append(f"  - {q.get('question_text', 'N/A')[:60]}... {eliminatory}")
        
        if self.communication_settings:
            lines.append("\n### Configurações de Comunicação:")
            lines.append(f"  - Horário de envio: {self.communication_settings.get('sending_hours_start', 8)}h - {self.communication_settings.get('sending_hours_end', 20)}h")
            lines.append(f"  - LGPD: {'Ativo' if self.communication_settings.get('lgpd_compliant') else 'Inativo'}")
        
        return "\n".join(lines)
    
    def get_benefits_for_seniority(self, seniority: str | None = None) -> list[dict[str, Any]]:
        """Get benefits filtered by seniority level."""
        if not seniority:
            return self.benefits
        
        filtered = []
        for benefit in self.benefits:
            applicable = benefit.get('applicable_seniorities', [])
            if not applicable or seniority.lower() in [s.lower() for s in applicable]:
                filtered.append(benefit)
        return filtered
    
    def get_eliminatory_questions(self) -> list[dict[str, Any]]:
        """Get only eliminatory screening questions."""
        return [q for q in self.screening_questions if q.get('is_eliminatory')]


class CacheEntry:
    """Cache entry with TTL tracking."""
    
    def __init__(self, data: Any, ttl_seconds: int = 600):
        self.data = data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return (time.time() - self.created_at) > self.ttl_seconds


class ConfigurationCache:
    """In-memory cache for company configurations."""
    
    def __init__(self, default_ttl: int = 600):
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
    
    def get(self, company_id: str) -> CompanyConfiguration | None:
        """Get cached configuration if not expired."""
        if company_id in self._cache:
            entry = self._cache[company_id]
            if not entry.is_expired():
                logger.debug(f"Cache hit for company {company_id}")
                return entry.data
            else:
                del self._cache[company_id]
                logger.debug(f"Cache expired for company {company_id}")
        return None
    
    def set(self, company_id: str, config: CompanyConfiguration, ttl: int | None = None) -> None:
        """Set cache entry with TTL."""
        ttl = ttl or self.default_ttl
        self._cache[company_id] = CacheEntry(config, ttl)
        logger.debug(f"Cache set for company {company_id} (TTL: {ttl}s)")
    
    def invalidate(self, company_id: str) -> None:
        """Invalidate cache for a specific company."""
        if company_id in self._cache:
            del self._cache[company_id]
            logger.info(f"Cache invalidated for company {company_id}")
    
    def invalidate_all(self) -> None:
        """Invalidate all cached configurations."""
        self._cache.clear()
        logger.info("All configuration cache invalidated")


_cache = ConfigurationCache(default_ttl=600)


class CompanyConfigurationService:
    """
    Service for loading and providing company configurations to AI agents.
    
    Usage:
        config = await company_config_service.get_configuration("company-123")
        ai_context = config.to_ai_context()
    """
    
    def __init__(self):
        self.cache = _cache
    
    async def get_configuration(
        self,
        company_id: str,
        db: AsyncSession | None = None,
        force_refresh: bool = False,
        allow_default_fallback: bool = True
    ) -> CompanyConfiguration:
        """
        Get complete company configuration.
        
        Args:
            company_id: Company identifier
            db: Optional database session (creates one if not provided)
            force_refresh: Force reload from database ignoring cache
            allow_default_fallback: If True, falls back to default profile when tenant not found.
                                    If False, raises ValueError when tenant lookup fails.
            
        Returns:
            CompanyConfiguration object with all settings
            
        Raises:
            ValueError: If allow_default_fallback=False and tenant config not found
        """
        if not force_refresh:
            cached = self.cache.get(company_id)
            if cached:
                return cached
        
        if db:
            config = await self._load_configuration(db, company_id, allow_default_fallback)
        else:
            async with AsyncSessionLocal() as session:
                config = await self._load_configuration(session, company_id, allow_default_fallback)
        
        self.cache.set(company_id, config)
        return config
    
    async def _load_configuration(
        self,
        db: AsyncSession,
        company_id: str,
        allow_default_fallback: bool = True
    ) -> CompanyConfiguration:
        """Load all configuration from database."""
        logger.info(f"Loading configuration for company {company_id}")
        
        profile = await self._load_company_profile(db, company_id, allow_default_fallback)
        benefits = await self._load_benefits(db, company_id)
        pipelines = await self._load_pipeline_templates(db, company_id)
        questions = await self._load_screening_questions(db, company_id)
        comm_settings = await self._load_communication_settings(db, company_id)
        
        default_pipeline = None
        for p in pipelines:
            if p.get('is_default'):
                default_pipeline = p
                break
        
        if not default_pipeline and pipelines:
            default_pipeline = pipelines[0]
        
        return CompanyConfiguration(
            company_id=company_id,
            company_name=profile.get('name', 'Empresa'),
            industry=profile.get('industry'),
            company_size=profile.get('company_size'),
            description=profile.get('description'),
            culture_values=profile.get('culture_values', []),
            benefits=benefits,
            pipeline_templates=pipelines,
            default_pipeline=default_pipeline,
            screening_questions=questions,
            communication_settings=comm_settings
        )
    
    async def _load_company_profile(
        self,
        db: AsyncSession,
        company_id: str,
        allow_default_fallback: bool = True
    ) -> dict[str, Any]:
        """Load company profile."""
        try:
            company_uuid = _to_uuid(company_id)
            profile = None
            
            cp_repo = CompanyProfileRepository(db)
            if company_uuid:
                profile = await cp_repo.get_by_id_with_culture_values(company_uuid)

            if not profile:
                if not allow_default_fallback:
                    raise ValueError(f"Company profile not found for {company_id} and fallback disabled")
                logger.warning(f"Company profile not found for {company_id}, using default (multi-tenant risk)")
                profile = await cp_repo.get_default_with_culture_values()
            
            if profile:
                culture_values = []
                if hasattr(profile, 'culture_values') and profile.culture_values:
                    for cv in profile.culture_values:
                        culture_values.append({
                            'name': str(getattr(cv, 'name', '')),
                            'description': str(getattr(cv, 'description', '')),
                            'importance': getattr(cv, 'importance', 'medium')
                        })
                
                return {
                    'id': str(profile.id),
                    'name': str(getattr(profile, 'name', '') or 'Empresa'),
                    'industry': str(getattr(profile, 'industry', '')) if getattr(profile, 'industry', None) else None,
                    'company_size': str(getattr(profile, 'company_size', '')) if getattr(profile, 'company_size', None) else None,
                    'description': str(getattr(profile, 'description', '')) if getattr(profile, 'description', None) else None,
                    'culture_values': culture_values
                }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error loading company profile: {e}")
            if not allow_default_fallback:
                raise ValueError(f"Failed to load company profile for {company_id}: {e}")
        
        logger.warning(f"Returning default profile for {company_id} (multi-tenant risk)")
        return {
            'id': company_id,
            'name': 'Empresa Demo',
            'industry': None,
            'company_size': None,
            'description': None,
            'culture_values': []
        }
    
    async def _load_benefits(
        self,
        db: AsyncSession,
        company_id: str
    ) -> list[dict[str, Any]]:
        """Load company benefits."""
        try:
            company_uuid = _to_uuid(company_id)
            if not company_uuid:
                logger.warning(f"Invalid company_id format for benefits: {company_id}")
                return []
            
            benefits_list = await BenefitRepository(db).list_active_ordered(
                company_uuid
            )
            
            return [
                {
                    'id': str(b.id),
                    'name': str(getattr(b, 'name', '')),
                    'description': str(getattr(b, 'description', '')),
                    'category': str(getattr(b, 'category', 'other')),
                    'value_type': str(getattr(b, 'value_type', 'informative')),
                    'value': getattr(b, 'value', None),
                    'is_highlighted': bool(getattr(b, 'is_highlighted', False)),
                    'applicable_seniorities': list(getattr(b, 'applicable_seniorities', []) or [])
                }
                for b in benefits_list
            ]
        except Exception as e:
            logger.warning(f"Error loading benefits: {e}")
            return []
    
    async def _load_pipeline_templates(
        self,
        db: AsyncSession,
        company_id: str
    ) -> list[dict[str, Any]]:
        """Load pipeline templates."""
        try:
            templates, _total = await PipelineTemplateRepository(db).list_for_company(
                company_id, is_active=True, page=1, size=1000
            )
            
            return [
                {
                    'id': str(t.id),
                    'name': str(getattr(t, 'name', '')),
                    'description': str(getattr(t, 'description', '')),
                    'stages': list(getattr(t, 'stages', []) or []),
                    'is_default': bool(getattr(t, 'is_default', False)),
                    'usage_count': int(getattr(t, 'usage_count', 0))
                }
                for t in templates
            ]
        except Exception as e:
            logger.warning(f"Error loading pipeline templates: {e}")
            return []
    
    async def _load_screening_questions(
        self,
        db: AsyncSession,
        company_id: str
    ) -> list[dict[str, Any]]:
        """Load default screening questions."""
        try:
            questions = await CompanyScreeningQuestionRepository(
                db
            ).list_for_company(company_id, is_active=True)
            
            return [
                {
                    'id': str(q.id),
                    'question_text': str(getattr(q, 'question_text', '')),
                    'question_type': str(getattr(q, 'question_type', 'text')),
                    'options': list(getattr(q, 'options', []) or []),
                    'is_required': bool(getattr(q, 'is_required', True)),
                    'is_eliminatory': bool(getattr(q, 'is_eliminatory', False)),
                    'expected_answer': getattr(q, 'expected_answer', None),
                    'category': str(getattr(q, 'category', 'general'))
                }
                for q in questions
            ]
        except Exception as e:
            logger.warning(f"Error loading screening questions: {e}")
            return []
    
    async def _load_communication_settings(
        self,
        db: AsyncSession,
        company_id: str
    ) -> dict[str, Any] | None:
        """Load communication settings."""
        try:
            settings = await CommunicationSettingsRepository(
                db
            ).get_by_company_id(company_id)
            
            if settings:
                return settings.to_dict()
        except Exception as e:
            logger.warning(f"Error loading communication settings: {e}")
        
        return {
            'sending_hours_start': 8,
            'sending_hours_end': 20,
            'respect_holidays': True,
            'respect_weekends': True,
            'timezone': 'America/Sao_Paulo',
            'max_messages_per_day': 3,
            'lgpd_compliant': True
        }
    
    def invalidate_cache(self, company_id: str) -> None:
        """Invalidate cached configuration for a company."""
        self.cache.invalidate(company_id)
    
    def invalidate_all_cache(self) -> None:
        """Invalidate all cached configurations."""
        self.cache.invalidate_all()
    
    async def get_benefits_formatted(
        self,
        company_id: str,
        seniority: str | None = None,
        db: AsyncSession | None = None
    ) -> str:
        """
        Get formatted benefits for AI prompts.
        
        Args:
            company_id: Company identifier
            seniority: Optional seniority filter (junior, pleno, senior, etc)
            db: Optional database session
            
        Returns:
            Formatted string of benefits for AI context
        """
        config = await self.get_configuration(company_id, db)
        benefits = config.get_benefits_for_seniority(seniority)
        
        if not benefits:
            return "Nenhum benefício configurado para esta empresa."
        
        lines = [f"## Benefícios Disponíveis ({len(benefits)}):\n"]
        
        categories: dict[str, list[dict]] = {}
        for b in benefits:
            cat = b.get('category', 'outros')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(b)
        
        # Canonical labels from benefits_service SSOT (v2, 14 categories)
        
        for cat, cat_benefits in categories.items():
            _canonical = resolve_benefit_category(cat)
            _icon = BENEFIT_CATEGORY_ICONS.get(_canonical, '📦')
            _label = BENEFIT_CATEGORIES.get(_canonical, cat.capitalize())
            cat_name = f'{_icon} {_label}'
            lines.append(f"\n### {cat_name}")
            for b in cat_benefits:
                star = "⭐ " if b.get('is_highlighted') else ""
                value_info = ""
                if b.get('value_type') == 'monetary' and b.get('value'):
                    value_info = f" (R$ {b['value']:,.2f})"
                elif b.get('value_type') == 'percentage' and b.get('value'):
                    value_info = f" ({b['value']}%)"
                lines.append(f"  - {star}{b['name']}{value_info}: {b['description']}")
        
        return "\n".join(lines)
    
    async def get_pipeline_for_job_type(
        self,
        company_id: str,
        job_type: str | None = None,
        db: AsyncSession | None = None
    ) -> dict[str, Any] | None:
        """
        Get recommended pipeline template based on job type.
        
        Args:
            company_id: Company identifier
            job_type: Type of job (tech, sales, operations, etc)
            db: Optional database session
            
        Returns:
            Pipeline template dict or None
        """
        config = await self.get_configuration(company_id, db)
        
        if not config.pipeline_templates:
            return config.default_pipeline
        
        if job_type:
            job_type_lower = job_type.lower()
            for template in config.pipeline_templates:
                name_lower = template.get('name', '').lower()
                desc_lower = template.get('description', '').lower()
                if job_type_lower in name_lower or job_type_lower in desc_lower:
                    return template
        
        return config.default_pipeline

    async def get_catalog_status(
        self,
        company_id: str,
        db: AsyncSession | None = None
    ) -> dict[str, Any]:
        """
        Get the maturity status of company's catalog data.
        
        Returns information about what data is available for smart wizard:
        - Salary policies by role/seniority
        - Skills catalog (technical and behavioral)
        - Benefits packages
        - Departments and managers
        
        Args:
            company_id: Company identifier
            db: Optional database session
            
        Returns:
            Dictionary with catalog status and counts
        """
        from lia_models.company import Department, DepartmentMember
        from lia_models.company_learning import CompanySkill
        from app.shared.services.skills_catalog_service import skills_catalog_service
        
        config = await self.get_configuration(company_id, db)
        
        # Count benefits
        benefits_count = len(config.benefits)
        highlighted_benefits = len([b for b in config.benefits if b.get('is_highlighted')])
        
        # Count departments and managers
        departments_count = 0
        managers_count = 0
        
        if db:
            try:
                from uuid import UUID

                from sqlalchemy import func, select
                
                try:
                    company_uuid = UUID(company_id)
                    dept_result = await db.execute(
                        select(func.count(Department.id)).where(Department.company_id == company_uuid)
                    )
                    departments_count = dept_result.scalar() or 0
                    
                    mgr_result = await db.execute(
                        select(func.count(DepartmentMember.id))
                        .join(Department)
                        .where(Department.company_id == company_uuid)
                        .where(DepartmentMember.role == 'manager')
                    )
                    managers_count = mgr_result.scalar() or 0
                except (ValueError, TypeError):
                    pass
            except Exception as e:
                logger.warning(f"Error counting departments: {e}")
        
        # Count company skills from database
        company_skills_count = 0
        if db:
            try:
                from uuid import UUID

                from sqlalchemy import func, select
                try:
                    company_uuid = UUID(company_id)
                    skills_result = await db.execute(
                        select(func.count(CompanySkill.id)).where(CompanySkill.company_id == company_uuid)
                    )
                    company_skills_count = skills_result.scalar() or 0
                except (ValueError, TypeError):
                    pass
            except Exception as e:
                logger.warning(f"Error counting company skills: {e}")
        
        # Get catalog skills count (behavioral competencies from static catalog)
        behavioral_skills_count = len(skills_catalog_service.get_all_behavioral_competencies())
        
        # Total skills = company-specific + standard behavioral
        company_skills_count + behavioral_skills_count
        
        # Calculate maturity score (0-100) based on available data
        # Weights: benefits=30, departments=30, skills=25, screening=15
        maturity_score = 0
        maturity_factors = []
        
        # Benefits (30 points max)
        if benefits_count >= 5:
            maturity_score += 30
            maturity_factors.append("benefits_complete")
        elif benefits_count >= 3:
            maturity_score += 20
            maturity_factors.append("benefits_partial")
        elif benefits_count > 0:
            maturity_score += 10
            maturity_factors.append("benefits_minimal")
        
        # Departments (30 points max)
        if departments_count >= 3 and managers_count >= 2:
            maturity_score += 30
            maturity_factors.append("departments_complete")
        elif departments_count >= 2:
            maturity_score += 20
            maturity_factors.append("departments_partial")
        elif departments_count > 0:
            maturity_score += 10
            maturity_factors.append("departments_minimal")
        
        # Company-specific skills (25 points max)
        if company_skills_count >= 20:
            maturity_score += 25
            maturity_factors.append("skills_complete")
        elif company_skills_count >= 10:
            maturity_score += 15
            maturity_factors.append("skills_partial")
        elif company_skills_count > 0:
            maturity_score += 8
            maturity_factors.append("skills_minimal")
        
        # Screening questions (15 points max)
        screening_count = len(config.screening_questions or [])
        if screening_count >= 5:
            maturity_score += 15
            maturity_factors.append("screening_complete")
        elif screening_count >= 3:
            maturity_score += 10
            maturity_factors.append("screening_partial")
        elif screening_count > 0:
            maturity_score += 5
            maturity_factors.append("screening_minimal")
        
        # Determine maturity level and required fields
        if maturity_score >= 75:
            maturity_level = "complete"
            smart_start_enabled = True
            required_fields = ["cargo", "departamento"]
        elif maturity_score >= 40:
            maturity_level = "partial"
            smart_start_enabled = True
            required_fields = ["cargo", "departamento", "senioridade"]
        else:
            maturity_level = "minimal"
            smart_start_enabled = False
            required_fields = ["cargo", "senioridade", "departamento", "salario", "competencias"]
        
        # Build availability summary
        available_data = []
        if company_skills_count > 0:
            available_data.append(f"{company_skills_count} competências específicas da empresa")
        if behavioral_skills_count > 0:
            available_data.append(f"{behavioral_skills_count} competências comportamentais padrão")
        if benefits_count > 0:
            available_data.append(f"Pacote de benefícios configurado ({benefits_count} itens)")
        if highlighted_benefits > 0:
            available_data.append(f"{highlighted_benefits} benefícios destacados")
        if departments_count > 0:
            available_data.append(f"{departments_count} departamentos com gestores")
        
        return {
            "company_id": company_id,
            "maturity_score": maturity_score,
            "maturity_level": maturity_level,
            "maturity_factors": maturity_factors,
            "smart_start_enabled": smart_start_enabled,
            "required_fields_for_wizard": required_fields,
            "available_data_summary": available_data,
            "counts": {
                "benefits": benefits_count,
                "highlighted_benefits": highlighted_benefits,
                "departments": departments_count,
                "managers": managers_count,
                "company_skills": company_skills_count,
                "catalog_behavioral_skills": behavioral_skills_count,
                "screening_questions": screening_count
            },
            "recommendations": self._get_catalog_recommendations(
                maturity_score=maturity_score,
                maturity_factors=maturity_factors,
                benefits=benefits_count,
                departments=departments_count,
                managers=managers_count,
                skills=company_skills_count,
                screening=screening_count
            )
        }
    
    def _get_catalog_recommendations(
        self,
        maturity_score: int,
        maturity_factors: list[str],
        benefits: int,
        departments: int,
        managers: int,
        skills: int,
        screening: int
    ) -> list[str]:
        """Generate recommendations for improving catalog completeness."""
        if maturity_score >= 75:
            return ["Catálogo completo! O Smart Start está habilitado para suas vagas."]
        
        recommendations = []
        
        if "benefits_complete" not in maturity_factors:
            if benefits == 0:
                recommendations.append(
                    "Configure o pacote de benefícios padrão da empresa (mínimo 5 itens recomendado)"
                )
            else:
                recommendations.append(
                    f"Complete o pacote de benefícios (atual: {benefits}, recomendado: 5+)"
                )
        
        if "departments_complete" not in maturity_factors:
            if departments == 0:
                recommendations.append(
                    "Cadastre os departamentos e seus gestores para facilitar atribuição de vagas"
                )
            else:
                recommendations.append(
                    f"Adicione mais departamentos e gestores (atual: {departments} dept, {managers} gestores)"
                )
        
        if "skills_complete" not in maturity_factors:
            if skills == 0:
                recommendations.append(
                    "Adicione competências técnicas específicas da sua empresa ao catálogo"
                )
            else:
                recommendations.append(
                    f"Expanda o catálogo de competências (atual: {skills}, recomendado: 20+)"
                )
        
        if "screening_complete" not in maturity_factors:
            if screening == 0:
                recommendations.append(
                    "Configure perguntas de triagem padrão para acelerar a seleção"
                )
            else:
                recommendations.append(
                    f"Adicione mais perguntas de triagem (atual: {screening}, recomendado: 5+)"
                )
        
        return recommendations[:4]  # Return max 4 recommendations


company_config_service = CompanyConfigurationService()
