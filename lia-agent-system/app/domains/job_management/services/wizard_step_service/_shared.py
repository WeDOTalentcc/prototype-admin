"""
Shared imports, constants, and helper functions for wizard_step_service package.
"""
import json
import logging
import re
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.services.jd_generator_service import jd_generator_service
from lia_models.job_draft import ChangeType, JobDraft, JobDraftStatus
from app.shared.services.confidence_policy_service import ConfidencePolicyService
from app.shared.services.config_completeness_service import ConfigCompletenessService
from app.shared.services.context_aggregator_service import context_aggregator
from app.shared.services.enhanced_intent_classifier import (
    EnhancedIntentType,
    enhanced_intent_classifier,
)
from app.shared.services.intent_classifier import IntentType, intent_classifier_service
from app.shared.services.knowledge_base_service import knowledge_base
from app.shared.services.learning_hub_service import learning_hub_service
from app.shared.services.organization_catalog_service import OrganizationCatalogService
from app.shared.services.responsibilities_catalog_service import responsibilities_catalog_service
from app.shared.services.skills_catalog_service import skills_catalog_service

# Re-export helpers from the shared API layer
from app.api.v1.lia_assistant._shared import (
    QuestionType,
    detect_question_type,
    record_field_history,
    handle_salary_question,
    handle_skills_question,
    handle_time_to_fill_question,
    handle_process_question,
    analyze_competency_gaps,
    get_stage_benchmarks,
    handle_correction,
)
from app.domains.ai.services.llm import LLMService
from app.domains.job_management.services.vacancy_search_service import vacancy_search_service
from app.domains.analytics.services.feedback_learning_service import feedback_learning_service

USE_ENHANCED_CLASSIFIER = True

WIZARD_STAGES = [
    {"stage": 1, "name": "description", "panel": "Descrição da Vaga"},
    {"stage": 2, "name": "basic-info", "panel": "Informações Básicas"},
    {"stage": 3, "name": "competencies", "panel": "Competências"},
    {"stage": 4, "name": "salary", "panel": "Salário e Benefícios"},
    {"stage": 5, "name": "wsi-questions", "panel": "Perguntas de Triagem WSI"},
    {"stage": 6, "name": "review", "panel": "Revisão"},
    {"stage": 7, "name": "pre-publish", "panel": "Plataformas de Publicação"},
    {"stage": 8, "name": "candidate-search", "panel": "Busca de Candidatos"},
    {"stage": 9, "name": "calibration", "panel": "Calibração"},
    {"stage": 10, "name": "active-search", "panel": "Busca Ativa"},
]

logger = logging.getLogger(__name__)


async def get_historical_job_patterns(db_session: AsyncSession, company_id: str) -> dict[str, Any]:
    """
    Get most frequent work_model, employment_type and location patterns from historical jobs.
    Returns suggestions with confidence based on frequency.
    Filters by company_id for multi-tenant data isolation.
    """
    patterns = {}

    work_model_query = text("""
        SELECT work_model, COUNT(*) as count
        FROM job_vacancies
        WHERE work_model IS NOT NULL
        AND company_id = :company_id
        GROUP BY work_model
        ORDER BY count DESC
        LIMIT 1
    """)
    result = await db_session.execute(work_model_query, {'company_id': company_id})
    row = result.first()
    if row and row.count >= 3:
        total_query = text("SELECT COUNT(*) FROM job_vacancies WHERE work_model IS NOT NULL AND company_id = :company_id")
        total_result = await db_session.execute(total_query, {'company_id': company_id})
        total = total_result.scalar() or 1
        patterns['work_model'] = {
            'value': row.work_model,
            'count': row.count,
            'percentage': round((row.count / total) * 100),
            'source': 'historical_pattern',
        }

    emp_type_query = text("""
        SELECT employment_type, COUNT(*) as count
        FROM job_vacancies
        WHERE employment_type IS NOT NULL
        AND company_id = :company_id
        GROUP BY employment_type
        ORDER BY count DESC
        LIMIT 1
    """)
    result = await db_session.execute(emp_type_query, {'company_id': company_id})
    row = result.first()
    if row and row.count >= 3:
        total_query = text("SELECT COUNT(*) FROM job_vacancies WHERE employment_type IS NOT NULL AND company_id = :company_id")
        total_result = await db_session.execute(total_query, {'company_id': company_id})
        total = total_result.scalar() or 1
        patterns['employment_type'] = {
            'value': row.employment_type,
            'count': row.count,
            'percentage': round((row.count / total) * 100),
            'source': 'historical_pattern',
        }

    location_query = text("""
        SELECT location, COUNT(*) as count
        FROM job_vacancies
        WHERE location IS NOT NULL AND location != ''
        AND company_id = :company_id
        GROUP BY location
        ORDER BY count DESC
        LIMIT 1
    """)
    result = await db_session.execute(location_query, {'company_id': company_id})
    row = result.first()
    if row and row.count >= 3:
        total_query = text("SELECT COUNT(*) FROM job_vacancies WHERE location IS NOT NULL AND location != '' AND company_id = :company_id")
        total_result = await db_session.execute(total_query, {'company_id': company_id})
        total = total_result.scalar() or 1
        patterns['location'] = {
            'value': row.location,
            'count': row.count,
            'percentage': round((row.count / total) * 100),
            'source': 'historical_pattern',
        }

    return patterns


async def get_historical_salary_patterns(
    db_session: AsyncSession, company_id: str, job_title: str, seniority: str
) -> dict[str, Any]:
    """
    Get salary patterns from historical jobs for similar roles.
    Returns average salary range based on similar positions.
    Filters by company_id for multi-tenant data isolation.
    """
    try:
        query = text("""
            SELECT
                AVG(salary_min) as avg_min,
                AVG(salary_max) as avg_max,
                COUNT(*) as sample_size
            FROM job_vacancies
            WHERE salary_min IS NOT NULL
            AND salary_max IS NOT NULL
            AND salary_min > 0
            AND salary_max > 0
            AND company_id = :company_id
            AND (
                LOWER(title) LIKE :job_pattern
                OR LOWER(title) LIKE :seniority_pattern
            )
        """)
        result = await db_session.execute(query, {
            'company_id': company_id,
            'job_pattern': f'%{job_title.lower()[:10]}%' if job_title else '%',
            'seniority_pattern': f'%{seniority.lower()}%' if seniority else '%',
        })
        row = result.first()
        if row and row.sample_size >= 2:
            return {
                'avg_min': int(row.avg_min) if row.avg_min else None,
                'avg_max': int(row.avg_max) if row.avg_max else None,
                'sample_size': row.sample_size,
                'has_data': True,
            }
    except Exception as e:
        logger.warning(f"Could not fetch salary patterns: {e}")
    return {'has_data': False}
