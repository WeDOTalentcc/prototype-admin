"""
VacancySearchService - Service for Fast Track vacancy search and reuse.

Provides functionality to:
- Extract search criteria from natural language
- Search previous vacancies by criteria
- Apply adjustments to reused vacancies
"""
from app.shared.llm_models import CANONICAL_GEMINI_FLASH_MODEL
import json
import logging
import re
from datetime import datetime
from typing import Any

from app.schemas.job_management import SearchCriteriaResult  # R-026
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCRUDRepository

from lia_models.job_vacancy import JobVacancy
from app.domains.ai.services.llm import llm_service

logger = logging.getLogger(__name__)


# Sprint F.3 #25 canonical-fix: VacancySummary moved to domains/sourcing/services/vacancy_search.py
from app.domains.sourcing.services.vacancy_search import VacancySummary  # noqa: F401  (re-export for backward compat)


# Sprint F.3 #25 canonical-fix: VacancyFullDetails moved to domains/sourcing/services/vacancy_search.py
from app.domains.sourcing.services.vacancy_search import VacancyFullDetails  # noqa: F401  (re-export for backward compat)


class VacancySearchService:
    """
    Service for Fast Track vacancy search and reuse operations.
    Uses LLM for natural language criteria extraction and adjustments.
    """

    CRITERIA_EXTRACTION_PROMPT = """Analise a mensagem do usuário e extraia critérios de busca para encontrar vagas anteriores.

Mensagem: "{message}"

Extraia os seguintes critérios se mencionados:
- cargo: título ou função mencionada (ex: "desenvolvedor", "analista", "gerente de produto")
- gestor: nome do gestor/manager se mencionado
- candidato_contratado: nome do candidato contratado se mencionado
- ano: ano de referência (2024, 2023, "ano passado", etc)
- area: departamento/área (Tecnologia, RH, Financeiro, Marketing, etc)
- senioridade: nível de senioridade (júnior, pleno, sênior, etc)
- modelo_trabalho: remoto, híbrido, presencial
- localizacao: cidade ou região

Retorne APENAS um JSON válido no formato:
{{"cargo": "string ou null", "gestor": "string ou null", "candidato_contratado": "string ou null", "ano": "número ou null", "area": "string ou null", "senioridade": "string ou null", "modelo_trabalho": "string ou null", "localizacao": "string ou null"}}

Se nenhum critério for encontrado, retorne null para todos os campos."""

    ADJUSTMENTS_EXTRACTION_PROMPT = """Analise a mensagem do usuário e extraia ajustes que ele quer fazer em uma vaga.

Mensagem: "{message}"

Extraia APENAS os seguintes ajustes se mencionados (campos editáveis):
- salary_min: novo salário mínimo (converta "15k" para 15000)
- salary_max: novo salário máximo
- bonus_min: novo bônus mínimo
- bonus_max: novo bônus máximo
- benefits: lista de benefícios
- location: nova localização
- work_model: novo modelo de trabalho (remoto, híbrido, presencial)
- manager: novo gestor/manager

Retorne APENAS um JSON válido no formato:
{{"salary_min": número ou null, "salary_max": número ou null, "bonus_min": número ou null, "bonus_max": número ou null, "benefits": ["string"] ou null, "location": "string ou null", "work_model": "string ou null", "manager": "string ou null"}}

Se nenhum ajuste for mencionado, retorne null para todos os campos."""

    def __init__(self):
        self._llm_service = llm_service

    async def extract_search_criteria(self, message: str) -> SearchCriteriaResult:
        """
        Extract search criteria from a natural language message using LLM.
        
        Args:
            message: User's message in natural language
            
        Returns:
            Dictionary with extracted criteria
        """
        try:
            prompt = self.CRITERIA_EXTRACTION_PROMPT.format(message=message[:500])
            
            gemini = self._llm_service.gemini_native
            response = await gemini.aio.models.generate_content(
                model=CANONICAL_GEMINI_FLASH_MODEL,
                contents=prompt
            )
            
            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            criteria = json.loads(response_text)
            criteria = {k: v for k, v in criteria.items() if v is not None}
            
            logger.info(f"Extracted search criteria: {criteria}")
            return criteria
            
        except Exception as e:
            logger.error(f"Error extracting search criteria: {e}")
            return self._extract_criteria_fallback(message)

    def _extract_criteria_fallback(self, message: str) -> SearchCriteriaResult:
        """Fallback regex-based criteria extraction."""
        criteria = {}
        message_lower = message.lower()
        
        role_patterns = [
            r"vaga\s+de\s+([a-záéíóúâêô\s]+)",
            r"(desenvolvedor|analista|gerente|coordenador|diretor|engenheiro|designer|product\s*manager)[a-záéíóúâêô\s]*",
        ]
        for pattern in role_patterns:
            match = re.search(pattern, message_lower)
            if match:
                criteria["cargo"] = match.group(1).strip()
                break
        
        year_match = re.search(r"\b(202[0-5])\b", message)
        if year_match:
            criteria["ano"] = int(year_match.group(1))
        elif "ano passado" in message_lower:
            criteria["ano"] = datetime.now().year - 1
        
        departments = ["tecnologia", "ti", "rh", "recursos humanos", "financeiro", "marketing", "comercial", "vendas", "produto"]
        for dept in departments:
            if dept in message_lower:
                criteria["area"] = dept.title()
                break
        
        work_models = ["remoto", "híbrido", "hibrido", "presencial"]
        for model in work_models:
            if model in message_lower:
                criteria["modelo_trabalho"] = model.replace("hibrido", "híbrido")
                break
        
        seniorities = ["júnior", "junior", "pleno", "sênior", "senior", "lead", "staff"]
        for sen in seniorities:
            if sen in message_lower:
                criteria["senioridade"] = sen.replace("junior", "júnior").replace("senior", "sênior")
                break
        
        return criteria

    def validate_minimum_criteria(self, criteria: dict[str, Any]) -> bool:
        """
        Validate that at least 2 search criteria are provided.
        
        Args:
            criteria: Dictionary of search criteria
            
        Returns:
            True if at least 2 non-null criteria exist
        """
        non_null_count = sum(1 for v in criteria.values() if v is not None and v != "")
        return non_null_count >= 2

    async def search_vacancies(
        self,
        criteria: dict[str, Any],
        company_id: str,
        db: AsyncSession,
        limit: int = 10
    ) -> list[VacancySummary]:
        """
        Search previous vacancies based on criteria.
        
        Args:
            criteria: Search criteria dictionary
            company_id: Company ID for multi-tenancy
            db: Database session
            limit: Maximum number of results
            
        Returns:
            List of VacancySummary objects
        """
        try:
            effective_company_id = company_id
            conditions = [JobVacancy.company_id == effective_company_id]
            
            # Include all valid statuses (both Portuguese and English, various cases)
            valid_statuses = [
                "Concluída", "Cancelada", "Arquivada",
                "Ativa", "Active", "Open", "Em Andamento", "active", "ativa", "open"
            ]
            conditions.append(JobVacancy.status.in_(valid_statuses))
            
            if criteria.get("cargo"):
                cargo_term = f"%{criteria['cargo']}%"
                conditions.append(JobVacancy.title.ilike(cargo_term))
            
            if criteria.get("gestor"):
                gestor_term = f"%{criteria['gestor']}%"
                conditions.append(JobVacancy.manager.ilike(gestor_term))
            
            if criteria.get("area"):
                area_term = f"%{criteria['area']}%"
                conditions.append(JobVacancy.department.ilike(area_term))
            
            if criteria.get("senioridade"):
                sen_term = f"%{criteria['senioridade']}%"
                conditions.append(JobVacancy.seniority_level.ilike(sen_term))
            
            if criteria.get("modelo_trabalho"):
                model_term = f"%{criteria['modelo_trabalho']}%"
                conditions.append(JobVacancy.work_model.ilike(model_term))
            
            if criteria.get("localizacao"):
                loc_term = f"%{criteria['localizacao']}%"
                conditions.append(JobVacancy.location.ilike(loc_term))
            
            if criteria.get("ano"):
                year = int(criteria["ano"])
                year_start = datetime(year, 1, 1)
                year_end = datetime(year, 12, 31, 23, 59, 59)
                conditions.append(
                    or_(
                        and_(JobVacancy.closed_at >= year_start, JobVacancy.closed_at <= year_end),
                        and_(JobVacancy.created_at >= year_start, JobVacancy.created_at <= year_end)
                    )
                )
            
            vacancies = await JobVacancyCRUDRepository(db).search_by_conditions(
                conditions, limit=limit
            )
            
            summaries = []
            for v in vacancies:
                status_normalized = "contratado" if v.status in ["Concluída", "Cancelada", "Arquivada"] else (
                    "cancelado" if v.status in ["Cancelada", "Cancelled"] else "ativa"
                )
                
                summaries.append(VacancySummary(
                    id=v.id,
                    title=v.title,
                    department=v.department,
                    manager=v.manager,
                    hired_candidate=v.additional_data.get("hired_candidate") if v.additional_data else None,
                    date_closed=v.closed_at,
                    salary_range=v.salary_range,
                    work_model=v.work_model,
                    status=status_normalized,
                    seniority_level=v.seniority_level,
                    location=v.location
                ))
            
            logger.info(f"Found {len(summaries)} vacancies for criteria: {criteria}")
            return summaries
            
        except Exception as e:
            logger.error(f"Error searching vacancies: {e}")
            return []

    async def get_vacancy_full_details(
        self,
        vacancy_id: UUID,
        db: AsyncSession,
        company_id: str
    ) -> VacancyFullDetails | None:
        """
        Get full details of a vacancy for reuse.
        
        Args:
            vacancy_id: UUID of the vacancy
            db: Database session
            company_id: Company ID for tenant scoping/validation
            
        Returns:
            VacancyFullDetails or None if not found
        """
        try:
            vacancy = await JobVacancyCRUDRepository(db).get_by_id_strict_company(
                vacancy_id, company_id
            )
            
            if not vacancy:
                return None
            
            return VacancyFullDetails(
                id=vacancy.id,
                title=vacancy.title,
                department=vacancy.department,
                location=vacancy.location,
                work_model=vacancy.work_model,
                employment_type=vacancy.employment_type,
                seniority_level=vacancy.seniority_level,
                job_description=vacancy.description,
                salary_range=vacancy.salary_range,
                benefits=vacancy.benefits or [],
                technical_skills=vacancy.technical_requirements or [],
                behavioral_competencies=vacancy.behavioral_competencies or [],
                screening_questions=vacancy.screening_questions or [],
                languages=vacancy.languages or [],
                manager=vacancy.manager,
                manager_email=vacancy.manager_email,
                hired_candidate=vacancy.additional_data.get("hired_candidate") if vacancy.additional_data else None,
                status=vacancy.status,
                closed_at=vacancy.closed_at,
                interview_stages=vacancy.interview_stages or [],
                eligibility_questions=vacancy.eligibility_questions or []
            )
            
        except Exception as e:
            logger.error(f"Error getting vacancy details: {e}")
            return None

    async def extract_adjustments(self, message: str) -> dict[str, Any]:
        """
        Extract adjustments from a natural language message.
        
        Args:
            message: User's message with adjustments
            
        Returns:
            Dictionary with extracted adjustments
        """
        try:
            prompt = self.ADJUSTMENTS_EXTRACTION_PROMPT.format(message=message[:500])
            
            gemini = self._llm_service.gemini_native
            response = await gemini.aio.models.generate_content(
                model=CANONICAL_GEMINI_FLASH_MODEL,
                contents=prompt
            )
            
            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            adjustments = json.loads(response_text)
            adjustments = {k: v for k, v in adjustments.items() if v is not None}
            
            logger.info(f"Extracted adjustments: {adjustments}")
            return adjustments
            
        except Exception as e:
            logger.error(f"Error extracting adjustments: {e}")
            return self._extract_adjustments_fallback(message)

    def _extract_adjustments_fallback(self, message: str) -> dict[str, Any]:
        """Fallback regex-based adjustments extraction. Only extracts allowed fields."""
        adjustments = {}
        message_lower = message.lower()
        
        salary_patterns = [
            r"(\d+(?:\.\d+)?)\s*[kK]",
            r"R\$?\s*(\d+(?:\.\d{3})*(?:,\d{2})?)",
            r"(\d+)\s*(?:mil|reais)",
        ]
        for pattern in salary_patterns:
            match = re.search(pattern, message)
            if match:
                raw_value = match.group(1)
                clean_value = raw_value.replace(".", "").replace(",", ".")
                try:
                    value = float(clean_value)
                    if value < 1000:
                        value *= 1000
                    if "mínimo" in message_lower or "min" in message_lower:
                        adjustments["salary_min"] = int(value)
                    elif "máximo" in message_lower or "max" in message_lower:
                        adjustments["salary_max"] = int(value)
                    else:
                        adjustments["salary_min"] = int(value * 0.9)
                        adjustments["salary_max"] = int(value * 1.1)
                except ValueError:
                    pass
                break
        
        work_models = {"remoto": "Remoto", "híbrido": "Híbrido", "hibrido": "Híbrido", "presencial": "Presencial"}
        for model, normalized in work_models.items():
            if model in message_lower:
                adjustments["work_model"] = normalized
                break
        
        location_keywords = ["são paulo", "rj", "rio de janeiro", "belo horizonte", "sp", "rn", "ba", "minas gerais", "paraná"]
        for location in location_keywords:
            if location in message_lower:
                adjustments["location"] = location.title()
                break
        
        return adjustments

    def apply_adjustments(
        self,
        vacancy: VacancyFullDetails,
        adjustments: dict[str, Any]
    ) -> VacancyFullDetails:
        """
        Apply adjustments to a vacancy. Only applies allowed fields.
        
        Allowed editable fields:
        - salary_min, salary_max
        - bonus_min, bonus_max
        - benefits
        - location
        - work_model
        - manager
        
        Args:
            vacancy: Original vacancy details
            adjustments: Dictionary of adjustments to apply (disallowed fields are filtered out)
            
        Returns:
            Updated VacancyFullDetails
        """
        vacancy_dict = vacancy.model_dump()
        
        ALLOWED_ADJUSTMENT_FIELDS = {"salary_min", "salary_max", "bonus_min", "bonus_max", "benefits", "location", "work_model", "manager"}
        
        filtered_adjustments = {k: v for k, v in adjustments.items() if k in ALLOWED_ADJUSTMENT_FIELDS}
        
        if filtered_adjustments.get("location"):
            vacancy_dict["location"] = filtered_adjustments["location"]
        
        if filtered_adjustments.get("work_model"):
            vacancy_dict["work_model"] = filtered_adjustments["work_model"]
        
        if filtered_adjustments.get("manager"):
            vacancy_dict["manager"] = filtered_adjustments["manager"]
        
        if filtered_adjustments.get("bonus_min") is not None or filtered_adjustments.get("bonus_max") is not None:
            current_salary = vacancy_dict.get("salary_range") or {}
            if filtered_adjustments.get("bonus_min") is not None:
                current_salary["bonus_min"] = filtered_adjustments["bonus_min"]
            if filtered_adjustments.get("bonus_max") is not None:
                current_salary["bonus_max"] = filtered_adjustments["bonus_max"]
            vacancy_dict["salary_range"] = current_salary
        
        if filtered_adjustments.get("salary_min") is not None or filtered_adjustments.get("salary_max") is not None:
            current_salary = vacancy_dict.get("salary_range") or {}
            if filtered_adjustments.get("salary_min") is not None:
                current_salary["min"] = filtered_adjustments["salary_min"]
            if filtered_adjustments.get("salary_max") is not None:
                current_salary["max"] = filtered_adjustments["salary_max"]
            vacancy_dict["salary_range"] = current_salary
        
        if filtered_adjustments.get("benefits"):
            benefits = filtered_adjustments["benefits"]
            if isinstance(benefits, list):
                vacancy_dict["benefits"] = benefits
            else:
                existing_benefits = vacancy_dict.get("benefits") or []
                if isinstance(existing_benefits, list):
                    existing_benefits.append(benefits)
                    vacancy_dict["benefits"] = existing_benefits
        
        return VacancyFullDetails(**vacancy_dict)


vacancy_search_service = VacancySearchService()
