"""
Config Completeness Service for Job Creation Wizard.

Manages field completeness checking, hybrid suggestions, and
publication readiness validation.
"""
import logging
from dataclasses import dataclass
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FieldCategory(StrEnum):
    """Field categorization for completeness checking."""
    CRITICAL = "critical"
    IMPORTANT = "important"
    OPTIONAL = "optional"


class SuggestionSource(StrEnum):
    """Sources for field value suggestions."""
    COMPANY_HISTORY = "company_history"
    COMPANY_DEFAULTS = "company_defaults"
    MARKET_BENCHMARK = "market_benchmark"


@dataclass
class FieldSuggestion:
    """A suggestion for a field value."""
    value: Any
    source: SuggestionSource
    confidence: float
    explanation: str


@dataclass
class CompletenessResult:
    """Result of completeness check."""
    filled_fields: list[str]
    missing_critical: list[str]
    missing_important: list[str]
    toggled_off: list[str]
    can_publish: bool
    completeness_score: int
    field_details: dict[str, dict[str, Any]]


class ConfigCompletenessService:
    """
    Service for checking job configuration completeness and providing
    hybrid suggestions for missing fields.
    """
    
    TOGGLE_TO_COMPLETENESS_MAP: dict[str, str] = {
        "seniority_levels": "seniority",
        "salary_ranges": "salary_range",
        "employment_types": "employment_type",
        "locations": "location",
        "departments": "department",
        "behavioral_competencies": "behavioral_competencies",
        "tech_stack": "tech_stack",
        "benefits": "benefits",
        "work_model": "work_model",
        "default_languages": "languages",
    }
    
    COMPLETENESS_TO_TOGGLE_MAP: dict[str, str] = {v: k for k, v in TOGGLE_TO_COMPLETENESS_MAP.items()}
    
    FIELD_DEFINITIONS: dict[str, dict[str, Any]] = {
        "critical": {
            "job_title": {"label": "Título da Vaga", "db_field": "title", "toggle_key": None},
            "seniority": {"label": "Senioridade", "db_field": "seniority_level", "toggle_key": "seniority_levels"},
            "department": {"label": "Departamento", "db_field": "department", "toggle_key": "departments"},
        },
        "important": {
            "salary_range": {"label": "Faixa Salarial", "db_field": "salary_range", "toggle_key": "salary_ranges"},
            "benefits": {"label": "Benefícios", "db_field": "benefits", "toggle_key": "benefits"},
            "tech_stack": {"label": "Tech Stack", "db_field": "technical_requirements", "toggle_key": "tech_stack"},
            "behavioral_competencies": {"label": "Competências Comportamentais", "db_field": "behavioral_competencies", "toggle_key": "behavioral_competencies"},
            "description": {"label": "Descrição da Vaga", "db_field": "description", "toggle_key": None},
            "requirements": {"label": "Requisitos", "db_field": "requirements", "toggle_key": None},
        },
        "optional": {
            "work_model": {"label": "Modelo de Trabalho", "db_field": "work_model", "toggle_key": "work_model"},
            "location": {"label": "Localização", "db_field": "location", "toggle_key": "locations"},
            "employment_type": {"label": "Tipo de Contratação", "db_field": "employment_type", "toggle_key": "employment_types"},
            "languages": {"label": "Idiomas", "db_field": "languages", "toggle_key": "default_languages"},
            "manager": {"label": "Gestor", "db_field": "manager", "toggle_key": None},
            "deadline": {"label": "Prazo", "db_field": "deadline", "toggle_key": None},
        }
    }
    
    MARKET_BENCHMARKS: dict[str, dict[str, Any]] = {
        "salary_range": {
            "Júnior": {"min": 3000, "max": 5000, "currency": "BRL"},
            "Pleno": {"min": 6000, "max": 10000, "currency": "BRL"},
            "Sênior": {"min": 12000, "max": 18000, "currency": "BRL"},
            "Especialista": {"min": 15000, "max": 25000, "currency": "BRL"},
            "Coordenador": {"min": 15000, "max": 22000, "currency": "BRL"},
            "Gerente": {"min": 20000, "max": 35000, "currency": "BRL"},
            "Diretor": {"min": 35000, "max": 60000, "currency": "BRL"},
        },
        "benefits": [
            "Vale Refeição",
            "Vale Alimentação", 
            "Plano de Saúde",
            "Plano Odontológico",
            "Seguro de Vida",
            "Vale Transporte",
            "Gympass/Wellhub",
        ],
        "behavioral_competencies": [
            {"competency": "Comunicação", "weight": "Importante"},
            {"competency": "Trabalho em Equipe", "weight": "Importante"},
            {"competency": "Resolução de Problemas", "weight": "Essencial"},
            {"competency": "Adaptabilidade", "weight": "Importante"},
            {"competency": "Proatividade", "weight": "Importante"},
        ],
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def check_completeness(
        self,
        job_data: dict[str, Any],
        company_config: dict[str, Any] | None = None,
        toggles: dict[str, bool] | None = None
    ) -> CompletenessResult:
        """
        Check completeness of job data.
        
        Args:
            job_data: Job vacancy data dict
            company_config: Company configuration (optional)
            toggles: Field toggles dict (field_key -> is_active)
        
        Returns:
            CompletenessResult with filled/missing fields and can_publish status
        """
        toggles = toggles or {}
        company_config = company_config or {}
        
        filled_fields: list[str] = []
        missing_critical: list[str] = []
        missing_important: list[str] = []
        toggled_off: list[str] = []
        field_details: dict[str, dict[str, Any]] = {}
        
        def is_field_filled(field_key: str, db_field: str) -> bool:
            value = job_data.get(db_field)
            if value is None:
                return False
            if isinstance(value, str) and not value.strip():
                return False
            if isinstance(value, (list, dict)) and len(value) == 0:
                return False
            return True
        
        for category, fields in self.FIELD_DEFINITIONS.items():
            for field_key, field_info in fields.items():
                db_field = field_info["db_field"]
                label = field_info["label"]
                toggle_key = field_info.get("toggle_key")
                
                if toggle_key and toggles.get(toggle_key) is False:
                    toggled_off.append(field_key)
                    field_details[field_key] = {
                        "category": category,
                        "label": label,
                        "status": "toggled_off",
                        "value": None,
                    }
                    continue
                
                if is_field_filled(field_key, db_field):
                    filled_fields.append(field_key)
                    field_details[field_key] = {
                        "category": category,
                        "label": label,
                        "status": "filled",
                        "value": job_data.get(db_field),
                    }
                else:
                    if category == "critical":
                        missing_critical.append(field_key)
                    elif category == "important":
                        missing_important.append(field_key)
                    
                    field_details[field_key] = {
                        "category": category,
                        "label": label,
                        "status": "missing",
                        "value": None,
                    }
        
        total_fields = len(filled_fields) + len(missing_critical) + len(missing_important)
        
        if total_fields > 0:
            completeness_score = int((len(filled_fields) / total_fields) * 100)
        else:
            completeness_score = 100
        
        can_publish = len(missing_critical) == 0
        
        return CompletenessResult(
            filled_fields=filled_fields,
            missing_critical=missing_critical,
            missing_important=missing_important,
            toggled_off=toggled_off,
            can_publish=can_publish,
            completeness_score=completeness_score,
            field_details=field_details,
        )
    
    def get_field_suggestion(
        self,
        field_key: str,
        job_data: dict[str, Any],
        company_config: dict[str, Any] | None = None,
        previous_jobs: list[dict[str, Any]] | None = None
    ) -> FieldSuggestion | None:
        """
        Get hybrid suggestion for a field.
        
        Priority order:
        1. Company history (previous similar jobs)
        2. Company defaults
        3. Market benchmark
        
        Args:
            field_key: Field identifier
            job_data: Current job data for context
            company_config: Company configuration
            previous_jobs: List of previous job vacancies from company
        
        Returns:
            FieldSuggestion or None if no suggestion available
        """
        company_config = company_config or {}
        previous_jobs = previous_jobs or []
        
        suggestion = self._try_company_history(field_key, job_data, previous_jobs)
        if suggestion:
            return suggestion
        
        suggestion = self._try_company_defaults(field_key, company_config)
        if suggestion:
            return suggestion
        
        suggestion = self._try_market_benchmark(field_key, job_data)
        if suggestion:
            return suggestion
        
        return None
    
    def get_all_suggestions(
        self,
        missing_fields: list[str],
        job_data: dict[str, Any],
        company_config: dict[str, Any] | None = None,
        previous_jobs: list[dict[str, Any]] | None = None
    ) -> dict[str, FieldSuggestion]:
        """
        Get suggestions for all missing fields.
        
        Args:
            missing_fields: List of missing field keys
            job_data: Current job data
            company_config: Company configuration
            previous_jobs: Previous job vacancies
        
        Returns:
            Dict mapping field_key to FieldSuggestion
        """
        suggestions = {}
        for field_key in missing_fields:
            suggestion = self.get_field_suggestion(
                field_key, job_data, company_config, previous_jobs
            )
            if suggestion:
                suggestions[field_key] = suggestion
        return suggestions
    
    def _try_company_history(
        self,
        field_key: str,
        job_data: dict[str, Any],
        previous_jobs: list[dict[str, Any]]
    ) -> FieldSuggestion | None:
        """Try to get suggestion from company's previous jobs."""
        if not previous_jobs:
            return None
        
        field_mapping = {
            "salary_range": "salary_range",
            "benefits": "benefits",
            "behavioral_competencies": "behavioral_competencies",
            "tech_stack": "technical_requirements",
            "work_model": "work_model",
            "employment_type": "employment_type",
            "description": "description",
        }
        
        db_field = field_mapping.get(field_key)
        if not db_field:
            return None
        
        current_seniority = job_data.get("seniority_level", "").lower()
        current_department = job_data.get("department", "").lower()
        
        relevant_jobs = []
        for job in previous_jobs:
            job_seniority = (job.get("seniority_level") or "").lower()
            job_department = (job.get("department") or "").lower()
            
            if current_seniority and job_seniority == current_seniority:
                relevant_jobs.append((job, 0.9))
            elif current_department and job_department == current_department:
                relevant_jobs.append((job, 0.8))
            else:
                relevant_jobs.append((job, 0.6))
        
        if not relevant_jobs:
            return None
        
        relevant_jobs.sort(key=lambda x: x[1], reverse=True)
        best_match = relevant_jobs[0]
        
        value = best_match[0].get(db_field)
        if not value:
            return None
        
        num_matches = len(relevant_jobs)
        confidence = min(0.85, 0.6 + (num_matches * 0.05))
        
        return FieldSuggestion(
            value=value,
            source=SuggestionSource.COMPANY_HISTORY,
            confidence=confidence,
            explanation=f"Baseado em {num_matches} vaga(s) anterior(es) similares da empresa"
        )
    
    def _try_company_defaults(
        self,
        field_key: str,
        company_config: dict[str, Any]
    ) -> FieldSuggestion | None:
        """Try to get suggestion from company defaults."""
        config_mapping = {
            "work_model": "work_model",
            "employment_type": "employment_types",
            "benefits": "benefits",
            "behavioral_competencies": "default_behavioral_competencies",
            "tech_stack": "tech_stack",
            "seniority": "seniority_levels",
        }
        
        config_key = config_mapping.get(field_key)
        if not config_key:
            return None
        
        value = company_config.get(config_key)
        if not value:
            return None
        
        if isinstance(value, list) and len(value) > 0:
            if field_key == "employment_type":
                value = value[0] if value else None
            elif field_key == "seniority":
                value = value[0] if value else None
        
        if not value:
            return None
        
        return FieldSuggestion(
            value=value,
            source=SuggestionSource.COMPANY_DEFAULTS,
            confidence=0.80,
            explanation="Valor padrão configurado pela empresa"
        )
    
    def _try_market_benchmark(
        self,
        field_key: str,
        job_data: dict[str, Any]
    ) -> FieldSuggestion | None:
        """Try to get suggestion from market benchmarks."""
        if field_key == "salary_range":
            seniority = job_data.get("seniority_level", "Pleno")
            salary_benchmarks = self.MARKET_BENCHMARKS.get("salary_range", {})
            value = salary_benchmarks.get(seniority)
            if value:
                return FieldSuggestion(
                    value=value,
                    source=SuggestionSource.MARKET_BENCHMARK,
                    confidence=0.60,
                    explanation=f"Média de mercado para nível {seniority}"
                )
        
        elif field_key == "benefits":
            value = self.MARKET_BENCHMARKS.get("benefits")
            if value:
                return FieldSuggestion(
                    value=value,
                    source=SuggestionSource.MARKET_BENCHMARK,
                    confidence=0.55,
                    explanation="Benefícios comuns de mercado"
                )
        
        elif field_key == "behavioral_competencies":
            value = self.MARKET_BENCHMARKS.get("behavioral_competencies")
            if value:
                return FieldSuggestion(
                    value=value,
                    source=SuggestionSource.MARKET_BENCHMARK,
                    confidence=0.50,
                    explanation="Competências comuns de mercado"
                )
        
        return None
    
    def get_field_label(self, field_key: str) -> str:
        """Get the human-readable label for a field."""
        for category, fields in self.FIELD_DEFINITIONS.items():
            if field_key in fields:
                return fields[field_key].get("label", field_key)
        return field_key
    
    def get_field_category(self, field_key: str) -> str | None:
        """Get the category for a field."""
        for category, fields in self.FIELD_DEFINITIONS.items():
            if field_key in fields:
                return category
        return None
    
    async def get_suggestions(
        self,
        db: AsyncSession,
        company_id: str,
        missing_fields: list[str],
        context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """
        Get suggestions for missing fields based on company history and benchmarks.
        
        Args:
            db: Database session
            company_id: Company ID
            missing_fields: List of missing field keys
            context: Job context for matching suggestions
        
        Returns:
            Dict with suggestions for each missing field
        """
        from lia_models.company import Department
        
        suggestions = {}
        context = context or {}
        
        try:
            for field in missing_fields:
                if field == 'department':
                    # Try to get departments from company
                    try:
                        # ADR-001-EXEMPT: cross-domain Department lookup; no admin/companies repo
                        # exposes it yet. Sprint 6 follow-up: extract to DepartmentRepository.
                        dept_query = select(Department).where(
                            Department.company_id == company_id
                        ).limit(10)
                        dept_result = await db.execute(dept_query)
                        departments = [d.name for d in dept_result.scalars().all()]
                        
                        if departments:
                            suggestions[field] = {
                                'source': 'company_history',
                                'options': departments[:5],
                                'confidence': 0.75
                            }
                        else:
                            suggestions[field] = {
                                'source': 'company_defaults',
                                'options': ['Tecnologia', 'Produto', 'Marketing', 'Vendas', 'RH'],
                                'confidence': 0.60
                            }
                    except Exception as e:
                        logger.warning(f"Failed to fetch departments: {e}")
                        suggestions[field] = {
                            'source': 'company_defaults',
                            'options': ['Tecnologia', 'Produto', 'Marketing', 'Vendas', 'RH'],
                            'confidence': 0.60
                        }
                
                elif field == 'work_model':
                    suggestions[field] = {
                        'source': 'company_defaults',
                        'options': ['Híbrido', 'Remoto', 'Presencial'],
                        'confidence': 0.70
                    }
                
                elif field == 'location':
                    suggestions[field] = {
                        'source': 'company_defaults',
                        'value': 'São Paulo, SP',
                        'confidence': 0.65
                    }
                
                elif field == 'employment_type':
                    suggestions[field] = {
                        'source': 'company_defaults',
                        'options': ['CLT', 'PJ', 'Temporário'],
                        'confidence': 0.70
                    }
                
                elif field == 'technical_skills':
                    suggestions[field] = {
                        'source': 'market_benchmark',
                        'message': 'Baseado no cargo e nível, sugerimos skills técnicas relevantes',
                        'confidence': 0.50
                    }
                
                elif field == 'behavioral_skills':
                    suggestions[field] = {
                        'source': 'company_defaults',
                        'value': ['Comunicação', 'Trabalho em Equipe', 'Resolução de Problemas'],
                        'confidence': 0.60
                    }
                
                elif field == 'salary_min' or field == 'salary_max':
                    seniority = context.get('seniority', 'Pleno')
                    salary_benchmarks = self.MARKET_BENCHMARKS.get('salary_range', {})
                    salary_data = salary_benchmarks.get(seniority, {})
                    
                    if field == 'salary_min':
                        suggestions[field] = {
                            'source': 'market_benchmark',
                            'value': salary_data.get('min', 6000),
                            'confidence': 0.60
                        }
                    else:
                        suggestions[field] = {
                            'source': 'market_benchmark',
                            'value': salary_data.get('max', 10000),
                            'confidence': 0.60
                        }
        
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
        
        return suggestions


config_completeness_service = ConfigCompletenessService()


def get_config_completeness_service() -> "ConfigCompletenessService":
    return config_completeness_service
