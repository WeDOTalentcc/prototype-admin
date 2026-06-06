"""
LIA Field Config Service - Central service for field toggle management.

This service provides a unified interface for AI agents to:
1. Query field toggles and comments
2. Determine which data sources to use (company config vs fallback)
3. Build context prompts respecting toggle states
4. Track data source origin for transparency

CRITICAL: Toggles control AI DATA CONSUMPTION only, not UI visibility.
- Fields with is_active=False still appear in wizard UI
- When is_active=False, agents use fallback strategies (job history, benchmarks)
"""
import logging
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID

from app.domains.cv_screening.repositories.lia_field_config_repository import LiaFieldConfigRepository
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company import CompanyProfile
from lia_models.job_vacancy import JobVacancy
from lia_models.lia_field_toggles import (
    DEFAULT_FIELD_TOGGLES,
    FIELD_FALLBACK_CONFIG,
    LiaFieldToggle,
)

logger = logging.getLogger(__name__)


class DataSource(StrEnum):
    """Source of data used by AI agents."""
    COMPANY_CONFIG = "company_config"
    DEPARTMENT_CONFIG = "department_config"
    JOB_HISTORY = "job_history"
    MARKET_BENCHMARK = "market_benchmark"
    ROLE_INFERENCE = "role_inference"
    NOT_AVAILABLE = "not_available"


@dataclass
class FieldConfig:
    """Configuration for a single field."""
    field_key: str
    is_active: bool
    comment: str | None = None
    fallback_strategies: list[str] = field(default_factory=list)
    company_value: Any = None
    fallback_value: Any = None
    data_source: DataSource = DataSource.NOT_AVAILABLE
    confidence: float = 0.0


@dataclass
class FieldContext:
    """Complete context for a field including resolved value and source."""
    field_key: str
    value: Any
    source: DataSource
    source_explanation: str
    confidence: float
    is_toggle_active: bool
    recruiter_comment: str | None = None


@dataclass
class LiaFieldConfigResult:
    """Result of field config lookup with all toggles, comments, and resolved values."""
    company_id: str
    active_fields: dict[str, FieldConfig]
    inactive_fields: dict[str, FieldConfig]
    all_fields: dict[str, FieldConfig]
    field_contexts: dict[str, FieldContext]
    context_prompt: str
    data_quality_score: float


MARKET_BENCHMARKS = {
    "work_model": {
        "tech": "hybrid",
        "finance": "hybrid",
        "retail": "onsite",
        "default": "hybrid"
    },
    "hybrid_days_onsite": {
        "default": 3
    },
    "employment_types": {
        "brazil": ["CLT"],
        "default": ["CLT"]
    },
    "salary_ranges": {
        "Estagiário": {"min": 1500, "max": 2500, "currency": "BRL"},
        "Júnior": {"min": 3000, "max": 5000, "currency": "BRL"},
        "Pleno": {"min": 5000, "max": 9000, "currency": "BRL"},
        "Sênior": {"min": 9000, "max": 15000, "currency": "BRL"},
        "Especialista": {"min": 12000, "max": 20000, "currency": "BRL"},
        "Coordenador": {"min": 12000, "max": 18000, "currency": "BRL"},
        "Gerente": {"min": 18000, "max": 30000, "currency": "BRL"},
        "Diretor": {"min": 30000, "max": 50000, "currency": "BRL"},
    },
    "seniority_levels": {
        "default": ["Estágio", "Júnior", "Pleno", "Sênior", "Especialista", "Coordenador", "Gerente", "Diretor"]
    },
    "benefits": {
        "tech": ["Vale Refeição", "Vale Transporte", "Plano de Saúde", "PLR", "Gympass"],
        "default": ["Vale Refeição", "Vale Transporte", "Plano de Saúde"]
    },
    "behavioral_competencies": {
        "tech": [
            {"competency": "Comunicação", "weight": "Importante"},
            {"competency": "Trabalho em Equipe", "weight": "Essencial"},
            {"competency": "Resolução de Problemas", "weight": "Essencial"},
            {"competency": "Adaptabilidade", "weight": "Importante"}
        ],
        "default": [
            {"competency": "Comunicação", "weight": "Importante"},
            {"competency": "Trabalho em Equipe", "weight": "Essencial"}
        ]
    }
}

FIELD_LABELS = {
    "seniority_levels": "Níveis de Senioridade",
    "work_model": "Modelo de Trabalho",
    "hybrid_days_onsite": "Dias Presenciais",
    "employment_types": "Tipos de Contratação",
    "salary_ranges": "Faixas Salariais",
    "trade_name": "Nome Fantasia",
    "industry": "Setor/Indústria",
    "website": "Website",
    "linkedin_url": "LinkedIn",
    "company_size": "Tamanho da Empresa",
    "employee_count": "Número de Funcionários",
    "founded_year": "Ano de Fundação",
    "mission": "Missão",
    "vision": "Visão",
    "values": "Valores",
    "core_competencies": "Competências Essenciais",
    "engineering_culture": "Cultura de Engenharia",
    "default_languages": "Idiomas Padrão",
    "company_big_five": "Perfil Big Five",
    "departments": "Departamentos",
    "behavioral_competencies": "Competências Comportamentais",
    "growth_opportunities": "Oportunidades de Crescimento",
    "dei_initiatives": "Iniciativas DEI",
    "sustainability": "Sustentabilidade",
    "social_impact": "Impacto Social",
    "evp_bullets": "EVP",
    "tech_stack": "Tech Stack",
    "benefits": "Benefícios",
    "locations": "Localizações",
    "pipeline": "Pipeline",
    "eligibility_questions": "Perguntas de Elegibilidade",
    "headcount_planning": "Planejamento Headcount",
    "leadership_style": "Estilo de Liderança",
    "team_dynamics": "Dinâmica de Equipe",
}


class LiaFieldConfigService:
    """
    Central service for managing field toggles and building AI context.
    
    This service:
    1. Loads field toggles + comments from database
    2. Resolves values using fallback strategies when toggles are inactive
    3. Builds context prompts for AI agents with source attribution
    4. Tracks data quality and confidence scores
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_field_config(
        self,
        company_id: str,
        job_context: dict[str, Any] | None = None
    ) -> LiaFieldConfigResult:
        """
        Get complete field configuration for a company.
        
        Args:
            company_id: The company UUID
            job_context: Optional context about the current job being created
                        (title, seniority, department) for better inference
        
        Returns:
            LiaFieldConfigResult with all field configs, contexts, and prompt
        """
        try:
            company_uuid = UUID(company_id)
        except ValueError:
            logger.error(f"Invalid company_id format: {company_id}")
            return self._create_empty_result(company_id)
        
        toggles = await self._load_toggles(company_uuid)
        company_profile = await self._load_company_profile(company_uuid)
        culture_profile = await self._load_culture_profile(company_uuid)
        department_profile = await self._load_department(company_uuid, job_context)
        job_history = await self._load_job_history(company_id)
        
        all_fields: dict[str, FieldConfig] = {}
        active_fields: dict[str, FieldConfig] = {}
        inactive_fields: dict[str, FieldConfig] = {}
        field_contexts: dict[str, FieldContext] = {}
        
        for toggle_def in DEFAULT_FIELD_TOGGLES:
            field_key = toggle_def["field_key"]
            default_active = toggle_def["is_active"]
            
            toggle = toggles.get(field_key)
            is_active = toggle.is_active if toggle else default_active
            # TENANT-FALLBACK-OK: sensor false-positive — `comment` is toggle metadata, not company_id
            comment = toggle.comment if toggle else None
            
            fallback_strategies = FIELD_FALLBACK_CONFIG.get(field_key, ["skip"])
            
            company_value = self._get_company_value(field_key, company_profile, culture_profile)
            # Cadeia de heranca: departamento.defaults vence o valor da empresa.
            dept_value = self._get_department_value(field_key, department_profile)
            value_from_dept = dept_value is not None
            if value_from_dept:
                company_value = dept_value
            
            fallback_value = None
            data_source = DataSource.NOT_AVAILABLE
            confidence = 0.0
            
            if is_active and company_value is not None:
                data_source = DataSource.DEPARTMENT_CONFIG if value_from_dept else DataSource.COMPANY_CONFIG
                confidence = 1.0
            elif not is_active:
                fallback_value, data_source, confidence = self._resolve_fallback(
                    field_key, 
                    fallback_strategies, 
                    job_history, 
                    job_context,
                    company_profile
                )
            
            field_config = FieldConfig(
                field_key=field_key,
                is_active=is_active,
                comment=comment,
                fallback_strategies=fallback_strategies,
                company_value=company_value,
                fallback_value=fallback_value,
                data_source=data_source,
                confidence=confidence
            )
            
            all_fields[field_key] = field_config
            
            if is_active:
                active_fields[field_key] = field_config
            else:
                inactive_fields[field_key] = field_config
            
            resolved_value = company_value if is_active else fallback_value
            source_explanation = self._get_source_explanation(data_source, field_key)
            
            field_contexts[field_key] = FieldContext(
                field_key=field_key,
                value=resolved_value,
                source=data_source,
                source_explanation=source_explanation,
                confidence=confidence,
                is_toggle_active=is_active,
                recruiter_comment=comment
            )
        
        context_prompt = self._build_context_prompt(field_contexts, job_context)
        data_quality_score = self._calculate_data_quality(field_contexts)
        
        return LiaFieldConfigResult(
            company_id=company_id,
            active_fields=active_fields,
            inactive_fields=inactive_fields,
            all_fields=all_fields,
            field_contexts=field_contexts,
            context_prompt=context_prompt,
            data_quality_score=data_quality_score
        )
    
    async def _load_toggles(self, company_uuid: UUID) -> dict[str, LiaFieldToggle]:
        """Load all field toggles for a company."""
        toggles = await LiaFieldConfigRepository(self.db).list_field_toggles(company_uuid)
        return {t.field_key: t for t in toggles}
    
    async def _load_company_profile(self, company_uuid: UUID) -> CompanyProfile | None:
        """Load company profile data."""
        return await LiaFieldConfigRepository(self.db).get_company_profile(company_uuid)

    async def _load_culture_profile(self, company_uuid: UUID):
        """Load CompanyCultureProfile — home of the narrative fields. FASE 0."""
        return await LiaFieldConfigRepository(self.db).get_culture_profile(company_uuid)

    async def _load_department(self, company_uuid: UUID, job_context: dict[str, Any] | None):
        """Carrega o Department (por nome exato) p/ defaults por-departamento.
        Cadeia de heranca: departamento > empresa. FASE 1 (audit 2026-06-06)."""
        dept_name = (job_context or {}).get("department") if job_context else None
        if not dept_name:
            return None
        return await LiaFieldConfigRepository(self.db).get_department_by_name(
            company_uuid, str(dept_name)
        )

    def _get_department_value(self, field_key: str, department: Any) -> Any:
        """Le um default por-departamento de Department.defaults (JSONB). Retorna
        None se ausente/vazio (entao o valor da empresa e usado). FASE 1."""
        if department is None:
            return None
        defaults = getattr(department, "defaults", None) or {}
        if not isinstance(defaults, dict):
            return None
        val = defaults.get(field_key)
        return val if val else None
    
    async def _load_job_history(self, company_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Load recent job history for pattern analysis."""
        jobs = await LiaFieldConfigRepository(self.db).list_recent_jobs_for_company(
            company_id=company_id, limit=limit
        )
        
        return [
            {
                "title": j.title,
                "seniority_level": j.seniority_level,
                "department": j.department,
                "work_model": j.work_model,
                "employment_type": j.employment_type,
                "salary_range": j.salary_range,
                "benefits": j.benefits,
                "technical_requirements": j.technical_requirements,
                "behavioral_competencies": j.behavioral_competencies,
                "location": j.location,
                "eligibility_questions": j.eligibility_questions or [],
            }
            for j in jobs
        ]
    
    def _get_company_value(self, field_key: str, profile: CompanyProfile | None, culture: Any = None) -> Any:
        """Extract company value for a field from profile (+ culture profile).

        Narrative fields (mission/vision/values/tech_stack/leadership_style/...)
        live on CompanyCultureProfile, which has NO relationship from
        CompanyProfile; they are read from ``culture`` here so the
        recruiter-configured values actually reach the prompt (FASE 0 ghost fix,
        audit 2026-06-06). CompanyProfile remains the primary source; culture is
        the secondary source for fields CompanyProfile lacks or leaves empty.
        """
        if profile is None and culture is None:
            return None
        
        if hasattr(profile, field_key):
            # Defense-in-depth (canonical-fix REGRA 4): never trigger an async
            # lazy-load from here. If field_key maps to an ORM relationship that
            # was NOT eager-loaded by the repository, getattr would emit IO
            # outside the greenlet -> MissingGreenlet, which the caller swallows
            # and silently empties the company context. Return None gracefully
            # so a future relationship that misses the selectinload degrades
            # honestly (skips that field) instead of nuking the whole context.
            try:
                unloaded = sa_inspect(profile).unloaded
            except Exception:
                unloaded = set()
            if field_key in unloaded:
                logger.warning(
                    "[lia_field_config] relationship %r is unloaded for company "
                    "profile; add selectinload(%s) to "
                    "LiaFieldConfigRepository.get_company_profile to surface it. "
                    "Skipping to avoid lazy-load MissingGreenlet.",
                    field_key, field_key,
                )
                return None
            return getattr(profile, field_key)
        
        if profile is not None and profile.additional_data and field_key in profile.additional_data:
            return profile.additional_data[field_key]
        
        field_mapping = {
            "trade_name": "trading_name",
            "industry": "industry",
            "website": "website",
            "linkedin_url": "linkedin_url",
            "company_size": "company_size",
            "employee_count": "employee_count",
            "mission": "mission",
            "vision": "vision",
            "values": "values",
        }
        
        if profile is not None and field_key in field_mapping:
            attr = field_mapping[field_key]
            if hasattr(profile, attr):
                val = getattr(profile, attr)
                if val:
                    return val

        # FASE 0 (audit 2026-06-06): narrative fields live on
        # CompanyCultureProfile (no relationship from CompanyProfile). Resolve
        # them here so the recruiter-configured values reach the prompt.
        culture_val = self._get_culture_value(field_key, culture)
        if culture_val is not None:
            return culture_val
        
        return None
    
    def _get_culture_value(self, field_key: str, culture: Any) -> Any:
        """Read a narrative field from CompanyCultureProfile. Returns None for
        absent/empty values so empty fields are never emitted. FASE 0."""
        if culture is None:
            return None
        culture_map = {
            "mission": "mission",
            "vision": "vision",
            "values": "values",
            "evp_bullets": "evp_bullets",
            "core_competencies": "core_competencies",
            # behavioral_competencies shares the same source column, whose own
            # model docstring reads "Behavioral competencies extracted from
            # website" (closes the last narrative ghost, audit 2026-06-06).
            "behavioral_competencies": "core_competencies",
            "locations": "locations",
            "work_model": "work_model",
            "growth_opportunities": "growth_opportunities",
            "team_dynamics": "team_dynamics",
            "leadership_style": "leadership_style",
            "dei_initiatives": "dei_initiatives",
            "sustainability": "sustainability",
            "social_impact": "social_impact",
            "tech_stack": "tech_stack",
            "engineering_culture": "engineering_culture",
            "default_languages": "default_languages",
        }
        if field_key in culture_map:
            val = getattr(culture, culture_map[field_key], None)
            return val if val else None
        if field_key == "company_big_five":
            # Only emit when the culture profile was actually approved — avoid
            # broadcasting the 50/50 placeholder default as if it were real.
            if not getattr(culture, "is_approved", False):
                return None
            o = getattr(culture, "openness_score", None)
            c = getattr(culture, "conscientiousness_score", None)
            e = getattr(culture, "extraversion_score", None)
            a = getattr(culture, "agreeableness_score", None)
            s = getattr(culture, "stability_score", None)
            if all(v is None for v in (o, c, e, a, s)):
                return None
            return (
                f"Abertura {o}, Conscienciosidade {c}, Extroversao {e}, "
                f"Amabilidade {a}, Estabilidade {s} (escala 0-100)"
            )
        return None

    def _resolve_fallback(
        self,
        field_key: str,
        strategies: list[str],
        job_history: list[dict[str, Any]],
        job_context: dict[str, Any] | None,
        company_profile: CompanyProfile | None
    ) -> tuple[Any, DataSource, float]:
        """
        Resolve fallback value using configured strategies.
        
        Returns: (value, source, confidence)
        """
        for strategy in strategies:
            if strategy == "skip":
                return None, DataSource.NOT_AVAILABLE, 0.0
            
            if strategy == "job_history":
                value, confidence = self._from_job_history(field_key, job_history)
                if value is not None:
                    return value, DataSource.JOB_HISTORY, confidence
            
            elif strategy == "market_benchmark":
                value = self._from_market_benchmark(field_key, job_context, company_profile)
                if value is not None:
                    return value, DataSource.MARKET_BENCHMARK, 0.6
            
            elif strategy == "role_inference":
                value = self._from_role_inference(field_key, job_context)
                if value is not None:
                    return value, DataSource.ROLE_INFERENCE, 0.5
        
        return None, DataSource.NOT_AVAILABLE, 0.0
    
    def _from_job_history(
        self, 
        field_key: str, 
        job_history: list[dict[str, Any]]
    ) -> tuple[Any | None, float]:
        """Extract pattern from job history."""
        if not job_history:
            return None, 0.0
        
        history_field_mapping = {
            "work_model": "work_model",
            "employment_types": "employment_type",
            "seniority_levels": "seniority_level",
            "salary_ranges": "salary_range",
            "benefits": "benefits",
            "tech_stack": "technical_requirements",
            "behavioral_competencies": "behavioral_competencies",
            "locations": "location",
            "departments": "department",
            "eligibility_questions": "eligibility_questions",
        }
        
        if field_key not in history_field_mapping:
            return None, 0.0
        
        history_key = history_field_mapping[field_key]
        values = [j.get(history_key) for j in job_history if j.get(history_key)]
        
        if not values:
            return None, 0.0
        
        if field_key in ["work_model", "employment_types"]:
            from collections import Counter
            counts = Counter(values)
            most_common = counts.most_common(1)[0]
            confidence = most_common[1] / len(values)
            return most_common[0], min(confidence + 0.2, 0.9)
        
        if field_key == "salary_ranges" and values:
            return values[0], 0.7
        
        if field_key in ["benefits", "tech_stack", "behavioral_competencies", "eligibility_questions"]:
            all_items = []
            for v in values:
                if isinstance(v, list):
                    all_items.extend(v)
            
            if all_items:
                from collections import Counter
                counts = Counter(item if isinstance(item, str) else str(item) for item in all_items)
                common_items = [item for item, count in counts.most_common(10) if count >= 2]
                if common_items:
                    return common_items, 0.7
        
        return values[0] if values else None, 0.6
    
    def _from_market_benchmark(
        self,
        field_key: str,
        job_context: dict[str, Any] | None,
        company_profile: CompanyProfile | None
    ) -> Any | None:
        """Get market benchmark value."""
        if field_key not in MARKET_BENCHMARKS:
            return None
        
        benchmark_data = MARKET_BENCHMARKS[field_key]
        
        industry = None
        if company_profile and hasattr(company_profile, 'industry'):
            industry = company_profile.industry
        
        seniority = None
        if job_context and "seniority" in job_context:
            seniority = job_context["seniority"]
        
        if field_key == "salary_ranges" and seniority:
            if seniority in benchmark_data:
                return benchmark_data[seniority]
            return benchmark_data.get("Pleno")
        
        if industry and industry.lower() in benchmark_data:
            return benchmark_data[industry.lower()]
        
        return benchmark_data.get("default")
    
    def _from_role_inference(
        self,
        field_key: str,
        job_context: dict[str, Any] | None
    ) -> Any | None:
        """Infer value from job role context."""
        if not job_context:
            return None
        
        title = job_context.get("title", "").lower()
        seniority = job_context.get("seniority", "")
        job_context.get("department", "")
        
        if field_key == "tech_stack":
            tech_keywords = {
                "python": ["python", "django", "flask", "fastapi", "data", "machine learning", "ml", "ai"],
                "javascript": ["frontend", "react", "vue", "angular", "node", "typescript", "full stack"],
                "java": ["java", "spring", "backend"],
                "devops": ["devops", "sre", "cloud", "aws", "azure", "kubernetes", "docker"],
            }
            
            inferred_stack = []
            for tech, keywords in tech_keywords.items():
                if any(kw in title for kw in keywords):
                    inferred_stack.append(tech.capitalize())
            
            return inferred_stack if inferred_stack else None
        
        if field_key == "behavioral_competencies":
            if "manager" in title or "gerente" in title or "líder" in title:
                return [
                    {"competency": "Liderança", "weight": "Essencial"},
                    {"competency": "Gestão de Pessoas", "weight": "Essencial"},
                    {"competency": "Comunicação", "weight": "Importante"},
                ]
            elif "sênior" in seniority.lower() or "senior" in title:
                return [
                    {"competency": "Mentoria", "weight": "Importante"},
                    {"competency": "Resolução de Problemas", "weight": "Essencial"},
                    {"competency": "Autonomia", "weight": "Essencial"},
                ]
        
        return None
    
    def _get_source_explanation(self, source: DataSource, field_key: str) -> str:
        """Generate human-readable explanation of data source."""
        explanations = {
            DataSource.COMPANY_CONFIG: "Configurado pela empresa nas Configurações",
            DataSource.DEPARTMENT_CONFIG: "Configurado para o departamento desta vaga",
            DataSource.JOB_HISTORY: "Baseado no histórico de vagas da empresa",
            DataSource.MARKET_BENCHMARK: "Benchmark de mercado para o setor/função",
            DataSource.ROLE_INFERENCE: "Inferido a partir do título e senioridade",
            DataSource.NOT_AVAILABLE: "Dado não disponível - campo desativado sem fallback",
        }
        return explanations.get(source, "Fonte desconhecida")
    
    def _build_context_prompt(
        self,
        field_contexts: dict[str, FieldContext],
        job_context: dict[str, Any] | None
    ) -> str:
        """
        Build context prompt for AI agents respecting toggle states.
        
        Includes:
        - Active fields with company values
        - Inactive fields with fallback values and source attribution
        - Recruiter comments as additional instructions
        """
        parts: list[str] = []
        
        parts.append("## Contexto de Configuração da Empresa para Criação de Vaga\n")
        
        active_parts = []
        for field_key, ctx in field_contexts.items():
            if ctx.is_toggle_active and ctx.value is not None:
                label = FIELD_LABELS.get(field_key, field_key)
                value_str = self._format_value(ctx.value)
                if value_str:
                    line = f"- **{label}**: {value_str}"
                    if ctx.recruiter_comment:
                        line += f"\n  _Instrução do recrutador: {ctx.recruiter_comment}_"
                    active_parts.append(line)
        
        if active_parts:
            parts.append("### Campos Configurados pela Empresa (fonte confiável):")
            parts.append("\n".join(active_parts))
        
        fallback_parts = []
        for field_key, ctx in field_contexts.items():
            if not ctx.is_toggle_active and ctx.value is not None:
                label = FIELD_LABELS.get(field_key, field_key)
                value_str = self._format_value(ctx.value)
                if value_str:
                    source_icon = {
                        DataSource.JOB_HISTORY: "📊",
                        DataSource.MARKET_BENCHMARK: "📈",
                        DataSource.ROLE_INFERENCE: "🔍",
                    }.get(ctx.source, "")
                    
                    line = f"- **{label}**: {value_str} {source_icon} _(confiança: {int(ctx.confidence * 100)}%)_"
                    line += f"\n  _Fonte: {ctx.source_explanation}_"
                    if ctx.recruiter_comment:
                        line += f"\n  _Instrução do recrutador: {ctx.recruiter_comment}_"
                    fallback_parts.append(line)
        
        if fallback_parts:
            parts.append("\n### Campos com Dados Alternativos (toggle desativado):")
            parts.append("_Estes campos não têm dados configurados pela empresa. Valores sugeridos com base em outras fontes:_")
            parts.append("\n".join(fallback_parts))
        
        unavailable_fields = [
            FIELD_LABELS.get(k, k) 
            for k, ctx in field_contexts.items() 
            if not ctx.is_toggle_active and ctx.value is None and ctx.source != DataSource.COMPANY_CONFIG
        ]
        if unavailable_fields:
            parts.append("\n### Campos Indisponíveis:")
            parts.append(f"_Os seguintes campos estão desativados e não possuem dados alternativos: {', '.join(unavailable_fields[:10])}_")
        
        comments = [
            f"- {FIELD_LABELS.get(k, k)}: {ctx.recruiter_comment}"
            for k, ctx in field_contexts.items()
            if ctx.recruiter_comment
        ]
        if comments:
            parts.append("\n### Instruções Específicas do Recrutador:")
            parts.append("\n".join(comments))
        
        return "\n\n".join(parts)
    
    def _format_value(self, value: Any) -> str:
        """Format a value for prompt display."""
        if value is None:
            return ""
        if isinstance(value, list):
            if not value:
                return ""
            if isinstance(value[0], dict):
                items = [str(v.get("competency", v.get("name", str(v)))) for v in value[:5]]
                return ", ".join(items) + ("..." if len(value) > 5 else "")
            # ORM rows (e.g. Department/Benefit relationships) expose a `name`
            # attribute; render that instead of the useless object repr that
            # would otherwise leak `<...Department object at 0x...>` into the
            # LLM prompt now that the relationships are eagerly loaded.
            if hasattr(value[0], "name"):
                items = [str(getattr(v, "name", str(v))) for v in value[:10]]
                return ", ".join(items) + ("..." if len(value) > 10 else "")
            return ", ".join(str(v) for v in value[:10]) + ("..." if len(value) > 10 else "")
        if isinstance(value, dict):
            if "min" in value and "max" in value:
                currency = value.get("currency", "BRL")
                return f"{currency} {value['min']:,.0f} - {value['max']:,.0f}"
            return str(value)
        return str(value)
    
    def _calculate_data_quality(self, field_contexts: dict[str, FieldContext]) -> float:
        """Calculate overall data quality score."""
        critical_fields = ["seniority_levels", "work_model", "employment_types", "salary_ranges", "benefits"]
        
        total_weight = 0
        weighted_score = 0
        
        for field_key, ctx in field_contexts.items():
            weight = 2.0 if field_key in critical_fields else 1.0
            total_weight += weight
            
            if ctx.value is not None:
                weighted_score += weight * ctx.confidence
        
        return (weighted_score / total_weight) if total_weight > 0 else 0.0
    
    def _create_empty_result(self, company_id: str) -> LiaFieldConfigResult:
        """Create empty result for invalid company."""
        return LiaFieldConfigResult(
            company_id=company_id,
            active_fields={},
            inactive_fields={},
            all_fields={},
            field_contexts={},
            context_prompt="Nenhuma configuração disponível para esta empresa.",
            data_quality_score=0.0
        )
    
    async def detect_empty_active_fields(
        self,
        company_id: str,
        user_id: str,
        job_context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Detect fields that have active toggles but empty company config values.
        
        These are fields where the recruiter WANTS the AI to use company data,
        but hasn't configured the data yet. Returns notifications for each.
        
        Args:
            company_id: The company UUID
            user_id: The recruiter's user ID
            job_context: Optional context about current job
            
        Returns:
            List of notification dicts with field info, impact, and actions
        """
        from datetime import datetime

        from lia_models.recruiter_profile import (
            DEFAULT_IMPACT_DESCRIPTION,
            FIELD_IMPACT_DESCRIPTIONS,
        )
        
        field_config = await self.get_field_config(company_id, job_context)
        
        recruiter_prefs = await self._load_recruiter_preferences(user_id, company_id)
        
        notifications = []
        
        for field_key, config in field_config.active_fields.items():
            if config.company_value is None or self._is_empty_value(config.company_value):
                pref = recruiter_prefs.get(field_key)
                
                if pref and not pref.remind_me_empty_field:
                    continue
                
                if pref and pref.snooze_until and pref.snooze_until > datetime.utcnow():
                    continue
                
                label = FIELD_LABELS.get(field_key, field_key)
                impact = FIELD_IMPACT_DESCRIPTIONS.get(field_key, DEFAULT_IMPACT_DESCRIPTION)
                
                fallback_strategies = FIELD_FALLBACK_CONFIG.get(field_key, ["skip"])
                has_fallback = fallback_strategies and fallback_strategies[0] != "skip"
                
                notifications.append({
                    "field_key": field_key,
                    "field_label": label,
                    "impact_description": impact,
                    "has_fallback": has_fallback,
                    "fallback_strategies": fallback_strategies,
                    "times_reminded": pref.times_reminded if pref else 0,
                    "actions": [
                        {
                            "action": "fill_now",
                            "label": "Preencher Agora",
                            "description": "LIA vai te ajudar a preencher este campo agora"
                        },
                        {
                            "action": "remind_later", 
                            "label": "Lembrar Depois",
                            "description": "Vou te lembrar na próxima vaga"
                        },
                        {
                            "action": "dont_remind",
                            "label": "Não Lembrar Mais",
                            "description": "Não vou mais avisar sobre este campo"
                        }
                    ]
                })
        
        return notifications
    
    async def _load_recruiter_preferences(
        self, 
        user_id: str, 
        company_id: str
    ) -> dict[str, "RecruiterFieldPreference"]:  # noqa: F821 (forward ref string)
        """Load recruiter field preferences from database."""
        from lia_models.recruiter_profile import RecruiterFieldPreference
        
        prefs = await LiaFieldConfigRepository(self.db).list_recruiter_preferences(
            recruiter_id=user_id, company_id=company_id
        )
        return {p.field_name: p for p in prefs}
    
    async def update_reminder_preference(
        self,
        company_id: str,
        user_id: str,
        field_key: str,
        action: str
    ) -> dict[str, Any]:
        """
        Update recruiter's preference for a field reminder.
        
        Args:
            company_id: The company UUID
            user_id: The recruiter's user ID
            field_key: The field key (e.g., "benefits")
            action: One of "fill_now", "remind_later", "dont_remind", "dismissed"
            
        Returns:
            Updated preference info
        """
        from datetime import datetime, timedelta

        from lia_models.recruiter_profile import RecruiterFieldPreference
        
        pref = await LiaFieldConfigRepository(self.db).get_recruiter_preference_for_field(
            recruiter_id=user_id, company_id=company_id, field_name=field_key
        )
        
        if not pref:
            pref = RecruiterFieldPreference(
                recruiter_id=user_id,
                company_id=company_id,
                field_name=field_key,
                remind_me_empty_field=True,
                times_reminded=0,
                times_filled_with_lia=0
            )
            self.db.add(pref)
        
        pref.last_reminded_at = datetime.utcnow()
        pref.times_reminded = (pref.times_reminded or 0) + 1
        pref.last_reminder_action = action
        
        if action == "dont_remind":
            pref.remind_me_empty_field = False
            pref.snooze_until = None
        elif action == "remind_later":
            pref.remind_me_empty_field = True
            pref.snooze_until = datetime.utcnow() + timedelta(days=7)
        elif action == "fill_now":
            pref.times_filled_with_lia = (pref.times_filled_with_lia or 0) + 1
            pref.remind_me_empty_field = True
            pref.snooze_until = None
        elif action == "dismissed":
            pref.snooze_until = datetime.utcnow() + timedelta(hours=24)
        
        await self.db.commit()
        
        return {
            "field_key": field_key,
            "action": action,
            "remind_me": pref.remind_me_empty_field,
            "snooze_until": pref.snooze_until.isoformat() if pref.snooze_until else None,
            "times_reminded": pref.times_reminded,
            "times_filled_with_lia": pref.times_filled_with_lia
        }
    
    async def suggest_field_value(
        self,
        company_id: str,
        field_key: str,
        job_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Generate AI suggestion for an empty field.
        
        Uses fallback strategies to suggest a value that the recruiter
        can use to fill the company config.
        
        Args:
            company_id: The company UUID
            field_key: The field to suggest value for
            job_context: Optional context about current job
            
        Returns:
            Suggestion with value, source, and confidence
        """
        try:
            company_uuid = UUID(company_id)
        except ValueError:
            return {"error": "Invalid company_id"}
        
        job_history = await self._load_job_history(company_id)
        company_profile = await self._load_company_profile(company_uuid)
        
        fallback_strategies = FIELD_FALLBACK_CONFIG.get(field_key, ["skip"])
        
        value, source, confidence = self._resolve_fallback(
            field_key,
            fallback_strategies,
            job_history,
            job_context,
            company_profile
        )
        
        if value is None:
            source = DataSource.MARKET_BENCHMARK
            confidence = 0.5
            # BUG-C4-B fix (2026-05-23): the canonical impl is _from_market_benchmark
            # (defined ~line 431 with matching 3-arg signature). The prior call to
            # self._get_market_benchmark(...) was a stale rename never propagated;
            # that name only exists in IntelligentDataOrchestrator with a totally
            # different signature (zero-arg lazy loader), so delegation would not
            # work. Use the canonical sibling method directly.
            value = self._from_market_benchmark(field_key, job_context, company_profile)
        
        label = FIELD_LABELS.get(field_key, field_key)
        source_explanation = self._get_source_explanation(source, field_key)
        
        source_icon = {
            DataSource.JOB_HISTORY: "📊",
            DataSource.MARKET_BENCHMARK: "📈",
            DataSource.ROLE_INFERENCE: "🔍",
            DataSource.COMPANY_CONFIG: "🏢",
        }.get(source, "")
        
        return {
            "field_key": field_key,
            "field_label": label,
            "suggested_value": value,
            "source": source.value,
            "source_icon": source_icon,
            "source_explanation": source_explanation,
            "confidence": confidence,
            "formatted_value": self._format_value(value)
        }
    
    def _is_empty_value(self, value: Any) -> bool:
        """Check if a value is considered empty."""
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False


async def get_lia_field_config_service(db: AsyncSession) -> LiaFieldConfigService:
    """Factory function to create LiaFieldConfigService."""
    return LiaFieldConfigService(db)
