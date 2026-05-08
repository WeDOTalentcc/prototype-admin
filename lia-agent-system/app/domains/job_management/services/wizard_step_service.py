"""
Wizard Step Service — extracted from lia_assistant.py (Fase 5 decomposition).

Contains the full logic of the /job-wizard/step endpoint, previously an inline
2000-line handler. The router now delegates to wizard_step_service.process().
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.wizard_step_repository import WizardStepRepository
import logging

from app.models.job_draft import JobDraft, DraftFieldHistory, JobDraftStatus, ChangeType
from app.models.candidate import Candidate
from app.models import JobVacancy
from app.shared.services.intent_classifier import intent_classifier_service, IntentType
from app.shared.services.enhanced_intent_classifier import (
    enhanced_intent_classifier, EnhancedIntentType,
)
from app.shared.services.context_aggregator_service import context_aggregator
from app.shared.services.knowledge_base_service import knowledge_base
from app.shared.services.learning_hub_service import learning_hub_service
from app.shared.services.organization_catalog_service import OrganizationCatalogService
from app.shared.services.confidence_policy_service import ConfidencePolicyService
from app.shared.services.config_completeness_service import ConfigCompletenessService
from app.shared.services.skills_catalog_service import skills_catalog_service
from app.shared.services.responsibilities_catalog_service import responsibilities_catalog_service
from app.domains.job_management.services.jd_generator_service import jd_generator_service
from app.shared.services.feedback_learning_service import FeedbackLearningService
from app.domains.ai.services.llm import llm_service

USE_ENHANCED_CLASSIFIER = True

logger = logging.getLogger(__name__)


# Mapping from Portuguese entity keys to English draft field names
_ENTITY_FIELD_MAP: Dict[str, str] = {
    "cargo": "job_title",
    "area": "department",
    "senioridade": "seniority",
    "salario_min": "salary_min",
    "salario_max": "salary_max",
    "modelo_trabalho": "work_model",
    "localizacao": "location",
    "skills_tecnicas": "detected_skills",
    "beneficios": "benefits",
    "idiomas": "languages",
    "is_afirmativa": "is_affirmative",
    "criterio_afirmativo_primario": "affirmative_criteria_primary",
    "criterio_afirmativo_secundario": "affirmative_criteria_secondary",
    "gestor": "manager",
    "gestor_email": "manager_email",
}

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

def _track_field_confidence(
    confidence_service: "ConfidencePolicyService",
    field_origins: Dict[str, Any],
    field: str,
    value: Any,
    source: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Calculate field confidence and record it in field_origins."""
    source_entry = {"type": source, "value": value}
    result = confidence_service.calculate_field_confidence(
        field=field,
        value=value,
        sources=[source_entry],
    )
    origin = {
        "source": "detected" if source == "text_extraction" else source,
        "confidence": result.confidence,
        "action": result.action.value,
    }
    if extra:
        origin.update(extra)
    field_origins[field] = origin



class WizardStepService:
    """Service encapsulating /job-wizard/step business logic."""

    async def process(
        self,
        request: Any,
        db: AsyncSession,
        company_id: str,
        recruiter_id: str,
    ) -> Any:
        """Process one wizard step and return a WizardStepResponse."""
        # Import response model here to avoid circular imports at module load time
        from app.api.v1.lia_assistant import WizardStepRequest, WizardStepResponse

        from app.models.company_benefit import CompanyBenefit
        from app.models.company import CompanyProfile, Department

        

        conversation_id = request.conversation_id or str(uuid4())
        current_stage = request.stage
        stage_info = WIZARD_STAGES[current_stage - 1] if current_stage <= len(WIZARD_STAGES) else WIZARD_STAGES[-1]

        # Try to find existing draft in database
        try:
            conv_uuid = UUID(conversation_id)
        except (ValueError, TypeError):
            conv_uuid = uuid4()
            conversation_id = str(conv_uuid)

        job_draft_model = await WizardStepRepository(db).get_draft_by_conversation(conv_uuid)

        if not job_draft_model:
            # Create new draft in database
            job_draft_model = JobDraft(
                conversation_id=conv_uuid,
                company_id=company_id,
                recruiter_id=recruiter_id,
                status=JobDraftStatus.DRAFT,
                current_step=stage_info["name"],
                raw_input=request.user_input,
                inferred_fields={},
                confirmed_fields={},
                company_defaults_used={},
                confidence_map={},
                skills=[],
                benefits=[],
                languages=[]
            )
            db.add(job_draft_model)
            await db.flush()
            logger.info(f"Created new JobDraft with conversation_id={conversation_id}, recruiter_id={recruiter_id}")

        # Create a dict for backward compatibility with existing code
        job_draft = {
            "job_id": str(job_draft_model.id),
            "created_at": job_draft_model.created_at.isoformat() if job_draft_model.created_at else datetime.utcnow().isoformat(),
            "company_id": company_id,
            "job_title": job_draft_model.job_title,
            "department": job_draft_model.department,
            "seniority": job_draft_model.seniority,
            "location": job_draft_model.location,
            "work_model": job_draft_model.work_model,
            "salary_min": job_draft_model.salary_min,
            "salary_max": job_draft_model.salary_max,
            "detected_skills": job_draft_model.skills or [],
            "benefits": job_draft_model.benefits or [],
            "is_affirmative": job_draft_model.is_affirmative,
            "affirmative_criteria_primary": job_draft_model.affirmative_criteria_primary,
            "affirmative_criteria_secondary": job_draft_model.affirmative_criteria_secondary,
            "manager": job_draft_model.manager,
            "manager_email": job_draft_model.manager_email,
        }

        # Merge any extra data from inferred_fields that acts as extra storage
        if job_draft_model.inferred_fields:
            extra_data = job_draft_model.inferred_fields.get("_extra_data", {})
            job_draft.update(extra_data)

        if request.context:
            for key, value in request.context.items():
                if value is not None:
                    job_draft[key] = value

        try:
            stage_context = stage_info["name"]

            enhanced_classification = None
            aggregated_context = None
            kb_response = None

            if USE_ENHANCED_CLASSIFIER:
                try:
                    aggregated_context = await context_aggregator.get_full_context(
                        company_id=company_id,
                        session_id=conversation_id,
                        db=db,
                        stage=current_stage,
                        filled_fields=job_draft
                    )

                    enhanced_classification = await enhanced_intent_classifier.classify(
                        user_input=request.user_input,
                        stage=current_stage,
                        filled_fields=job_draft,
                        context={"company": aggregated_context.company.name if aggregated_context else None}
                    )

                    entities_dict = enhanced_classification.entities.to_dict()
                    for key, value in entities_dict.items():
                        if value is not None and key not in ["raw_entities", "filtro_busca"]:
                            mapped_key = _ENTITY_FIELD_MAP.get(key, key)
                            job_draft[mapped_key] = value

                    if enhanced_classification.intent_type == EnhancedIntentType.QUESTION:
                        kb_response = knowledge_base.search(request.user_input)

                    logger.info(f"Enhanced classification: {enhanced_classification.intent_type} (confidence: {enhanced_classification.confidence})")

                except Exception as e:
                    logger.warning(f"Enhanced classifier failed, falling back: {e}")
                    enhanced_classification = None

            classification = await intent_classifier_service.classify(
                user_input=request.user_input,
                stage_context=stage_context,
                use_llm=True
            )

            if not enhanced_classification:
                for key, value in classification.extracted_entities.items():
                    if value is not None:
                        job_draft[key] = value

            logger.info(f"Intent classified: {classification.intent_type} (confidence: {classification.confidence})")

            # Initialize services for catalog validation
            org_catalog = OrganizationCatalogService()
            confidence_service = ConfidencePolicyService()

            # Track field origins
            field_origins = {}

            # Validate and enrich detected criteria using catalog
            if classification.extracted_entities:
                entities = classification.extracted_entities

                # Validate job title against catalog
                if entities.get('job_title'):
                    matched_role = org_catalog.get_role_by_name(entities['job_title'])
                    if matched_role:
                        # With catalog match, we have two sources agreeing
                        job_title_result = confidence_service.calculate_field_confidence(
                            field="job_title",
                            value=entities['job_title'],
                            sources=[
                                {"type": "text_extraction", "value": entities['job_title']},
                                {"type": "similar_jobs", "value": matched_role.get('nome')}
                            ]
                        )
                        field_origins['job_title'] = {
                            'source': 'detected',
                            'confidence': job_title_result.confidence,
                            'action': job_title_result.action.value,
                            'catalog_match': matched_role.get('nome')
                        }
                        # Get suggested skills for this role
                        role_skills = org_catalog.suggest_skills_for_role(entities['job_title'])
                        if role_skills and (role_skills.get('technical') or role_skills.get('behavioral')):
                            job_draft['suggested_skills'] = role_skills
                    else:
                        job_title_result = confidence_service.calculate_field_confidence(
                            field="job_title",
                            value=entities['job_title'],
                            sources=[{"type": "text_extraction", "value": entities['job_title']}]
                        )
                        field_origins['job_title'] = {
                            'source': 'detected',
                            'confidence': job_title_result.confidence,
                            'action': job_title_result.action.value,
                            'catalog_match': None
                        }

                # Validate technical skills against catalog
                if entities.get('technical_skills'):
                    validated_skills = []
                    for skill in entities['technical_skills']:
                        # Search for the skill using the search_skills method
                        search_results = org_catalog.search_skills(skill)
                        catalog_skill = None
                        if search_results.get('technical'):
                            catalog_skill = search_results['technical'][0]

                        if catalog_skill:
                            validated_skills.append({
                                'name': catalog_skill.get('nome', skill),
                                'category': catalog_skill.get('categoria'),
                                'validated': True
                            })
                            # Skill validated against catalog - two sources agreeing
                            skill_result = confidence_service.calculate_field_confidence(
                                field=f'skill_{skill}',
                                value=skill,
                                sources=[
                                    {"type": "text_extraction", "value": skill},
                                    {"type": "similar_jobs", "value": catalog_skill.get('nome', skill)}
                                ]
                            )
                            field_origins[f'skill_{skill}'] = {
                                'source': 'detected',
                                'confidence': skill_result.confidence,
                                'action': skill_result.action.value
                            }
                        else:
                            validated_skills.append({
                                'name': skill,
                                'validated': False
                            })
                            # Skill not in catalog - only text extraction
                            skill_result = confidence_service.calculate_field_confidence(
                                field=f'skill_{skill}',
                                value=skill,
                                sources=[{"type": "text_extraction", "value": skill}]
                            )
                            field_origins[f'skill_{skill}'] = {
                                'source': 'detected',
                                'confidence': skill_result.confidence,
                                'action': skill_result.action.value
                            }
                    job_draft['validated_technical_skills'] = validated_skills

                # Track other field origins using confidence service
                for field in ['seniority', 'department', 'location', 'work_model', 'salary_min', 'salary_max']:
                    if entities.get(field):
                        _track_field_confidence(confidence_service, field_origins, field, entities[field], "text_extraction")

            company_benefits = []
            company_departments = []
            company_profile = None

            try:
                _benefits = await WizardStepRepository(db).list_active_company_benefits(company_id)
                company_benefits = [
                    {"name": b.name, "category": b.category, "description": b.description}
                    for b in _benefits
                ]
            except Exception as e:
                logger.warning(f"Could not fetch company benefits: {e}")

            try:
                _repo = WizardStepRepository(db)
                company_profile = await _repo.get_active_company_profile()

                if company_profile:
                    _depts = await _repo.list_departments_for_profile(company_profile.id)
                    company_departments = [
                        {"name": d.name, "manager": d.manager_name, "location": d.location}
                        for d in _depts
                    ]
            except Exception as e:
                logger.warning(f"Could not fetch company profile/departments: {e}")

            # Helper function to get historical job patterns for fallback suggestions
            async def get_historical_job_patterns(db_session: AsyncSession, company_id: str) -> Dict[str, Any]:
                """
                Get most frequent work_model, employment_type and location patterns from historical jobs.
                Returns suggestions with confidence based on frequency.
                Filters by company_id for multi-tenant data isolation.
                """
                patterns = {}
                import re as _re
                _SAFE_PATTERN_COLS = frozenset(["work_model", "employment_type", "location"])
                _SAFE_COL_RE = _re.compile(r"^[a-z][a-z0-9_]{0,62}$")
                _pattern_fields = [
                    ("work_model", "work_model IS NOT NULL"),
                    ("employment_type", "employment_type IS NOT NULL"),
                    ("location", "location IS NOT NULL AND location != ''"),
                ]
                for col, where_clause in _pattern_fields:
                    if col not in _SAFE_PATTERN_COLS or not _SAFE_COL_RE.match(col):
                        continue
                    query = text(f"""
                        SELECT {col}, COUNT(*) as count
                        FROM job_vacancies
                        WHERE {where_clause}
                        AND company_id = :company_id
                        GROUP BY {col}
                        ORDER BY count DESC
                        LIMIT 1
                    """)
                    result = await db_session.execute(query, {'company_id': company_id})
                    row = result.first()
                    if row and row.count >= 3:
                        total_query = text(f"SELECT COUNT(*) FROM job_vacancies WHERE {where_clause} AND company_id = :company_id")
                        total_result = await db_session.execute(total_query, {'company_id': company_id})
                        total = total_result.scalar() or 1
                        patterns[col] = {
                            'value': getattr(row, col),
                            'count': row.count,
                            'percentage': round((row.count / total) * 100),
                            'source': 'historical_pattern',
                        }

                return patterns

            # Helper function to get salary patterns from historical jobs
            async def get_historical_salary_patterns(db_session: AsyncSession, company_id: str, job_title: str, seniority: str) -> Dict[str, Any]:
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
                        'seniority_pattern': f'%{seniority.lower()}%' if seniority else '%'
                    })
                    row = result.first()
                    if row and row.sample_size >= 2:
                        return {
                            'avg_min': int(row.avg_min) if row.avg_min else None,
                            'avg_max': int(row.avg_max) if row.avg_max else None,
                            'sample_size': row.sample_size,
                            'has_data': True
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch salary patterns: {e}")
                return {'has_data': False}

            # Apply company defaults for fields not detected from text extraction
            # Track fields that were filled by company defaults for history
            company_default_fields = {}

            if company_profile and company_profile.additional_data:
                additional_data = company_profile.additional_data

                # Apply company defaults for unfilled fields
                _default_candidates = [
                    ("work_model", "modeloTrabalho", additional_data.get("work_model")),
                    ("location", "localizacao", company_profile.headquarters_city),
                ]
                for field, alt_key, default_value in _default_candidates:
                    if not job_draft.get(field) and not job_draft.get(alt_key) and default_value:
                        job_draft[field] = default_value
                        _track_field_confidence(
                            confidence_service, field_origins, field, default_value, "company_default"
                        )
                        company_default_fields[field] = {
                            "value": default_value,
                            "confidence": field_origins[field]["confidence"],
                        }

            # FALLBACK: If company defaults not available, use historical patterns
            historical_patterns = {}
            _historical_fallback_fields = [
                ("work_model", "modeloTrabalho"),
                ("employment_type", "tipoContrato"),
                ("location", "localizacao"),
            ]
            for _hf_field, _hf_alt in _historical_fallback_fields:
                if not job_draft.get(_hf_field) and not job_draft.get(_hf_alt):
                    try:
                        if not historical_patterns:
                            historical_patterns = await get_historical_job_patterns(db, company_id)
                        if _hf_field in historical_patterns:
                            pattern = historical_patterns[_hf_field]
                            job_draft[_hf_field] = pattern['value']
                            job_draft[f'{_hf_field}_suggested'] = True
                            job_draft[f'{_hf_field}_suggestion_context'] = f"Baseado em {pattern['percentage']}% das suas vagas anteriores"
                            field_origins[_hf_field] = {
                                'source': 'historical_pattern',
                                'confidence': min(0.85, 0.5 + (pattern['percentage'] / 200)),
                                'action': 'suggest',
                                'context': pattern,
                            }
                    except Exception as e:
                        logger.warning(f"Could not fetch {_hf_field} pattern: {e}")

            llm_service = LLMService()

            high_confidence_fields = []
            low_confidence_fields = []

            for field, origin in field_origins.items():
                conf = origin.get('confidence', 0.5)
                if conf >= 0.70:
                    high_confidence_fields.append(field)
                else:
                    low_confidence_fields.append(field)

            response_style = "assertive" if len(low_confidence_fields) == 0 else "questioning"

            company_context = ""
            if company_profile:
                additional_data = company_profile.additional_data or {}

                tech_stack_lines = ""
                if additional_data.get('tech_stack'):
                    tech_stack_items = []
                    for cat, techs in list((additional_data.get('tech_stack', {}) or {}).items())[:5]:
                        if isinstance(techs, list):
                            tech_stack_items.append(f"- {cat}: {', '.join(techs)}")
                    tech_stack_lines = chr(10).join(tech_stack_items) if tech_stack_items else "- Não informadas"
                else:
                    tech_stack_lines = "- Não informadas"

                competencies_lines = ""
                if additional_data.get('default_behavioral_competencies'):
                    comp_items = []
                    for c in (additional_data.get('default_behavioral_competencies', []) or [])[:5]:
                        if isinstance(c, dict):
                            comp_items.append(f"- {c.get('competency', '')} ({c.get('weight', '')})")
                    competencies_lines = chr(10).join(comp_items) if comp_items else "- Não definidas"
                else:
                    competencies_lines = "- Não definidas"

                values_str = ', '.join(additional_data.get('values', [])) if additional_data.get('values') else 'Não definidos'
                employment_types_str = ', '.join(additional_data.get('employment_types', ['CLT']))

                company_context = f"""
    CONTEXTO DA EMPRESA:
    - Nome: {company_profile.name}
    - Nome Fantasia: {company_profile.trading_name or company_profile.name}
    - Setor: {company_profile.industry or 'Não informado'}
    - Sede: {company_profile.headquarters_city or 'Não informada'}, {company_profile.headquarters_state or ''}
    - Tamanho: {company_profile.company_size or 'Não informado'} ({company_profile.employee_count or '?'} funcionários)
    - Ano de Fundação: {company_profile.founded_year or 'Não informado'}
    - Website: {company_profile.website or 'Não informado'}

    CULTURA E VALORES:
    - Missão: {additional_data.get('mission', 'Não definida')}
    - Visão: {additional_data.get('vision', 'Não definida')}
    - Valores: {values_str}

    MODELO DE TRABALHO PADRÃO:
    - Modelo: {additional_data.get('work_model', 'Não definido')}
    - Dias presenciais (híbrido): {additional_data.get('hybrid_days_onsite', 3)}
    - Tipos de contrato aceitos: {employment_types_str}

    TECNOLOGIAS:
    {tech_stack_lines}

    COMPETÊNCIAS COMPORTAMENTAIS VALORIZADAS:
    {competencies_lines}
    """

            if company_departments:
                dept_info = [f"- {d['name']}" + (f" (Gestor: {d['manager']})" if d.get('manager') else "") for d in company_departments[:10]]
                company_context += "\nDEPARTAMENTOS:\n" + "\n".join(dept_info) + "\n"

            if company_benefits:
                benefit_info = [f"- {b['name']} ({b['category']})" for b in company_benefits[:10]]
                company_context += "\nBENEFÍCIOS:\n" + "\n".join(benefit_info) + "\n"

            detected_criteria = None
            lia_message = ""
            next_stage = current_stage + 1 if current_stage < 10 else None
            is_complete = current_stage >= 10
            created_job = None
            benchmarks = {}
            suggestions_data = {}

            if classification.intent_type == IntentType.QUESTION:
                question_type = detect_question_type(request.user_input)

                if question_type == QuestionType.SALARY:
                    lia_message = await handle_salary_question(db, company_id, job_draft, request.user_input)
                elif question_type == QuestionType.SKILLS:
                    lia_message = await handle_skills_question(db, company_id, job_draft, request.user_input)
                elif question_type == QuestionType.TIME_TO_FILL:
                    lia_message = await handle_time_to_fill_question(db, company_id, job_draft, request.user_input)
                elif question_type == QuestionType.PROCESS:
                    lia_message = await handle_process_question(request.user_input, llm_service)
                else:
                    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
                    _persona = SystemPromptBuilder.build(agent_type="job_planner", extra_instructions="Responda brevemente à pergunta do recrutador sobre a vaga.")
                    prompt = f"""{_persona}

Responda brevemente à pergunta:

    Pergunta: {request.user_input}
    Contexto da vaga: {json.dumps(job_draft, default=str)}

    Responda de forma útil e concisa."""
                    lia_message = await llm_service.generate(prompt, provider="gemini")

                lia_message += "\n\n---\nPosso ajudar com mais alguma dúvida ou prefere continuar com a criação da vaga?"
                next_stage = current_stage

            elif classification.intent_type == IntentType.CORRECTION:
                correction_response, updated_fields = await handle_correction(
                    db, company_id, job_draft, classification, request.user_input, conversation_id
                )
                lia_message = correction_response
                lia_message += "\n\nDeseja fazer mais algum ajuste ou podemos continuar?"
                detected_criteria = updated_fields
                next_stage = current_stage

            elif classification.intent_type == IntentType.DEVIATION:
                text_lower = request.user_input.lower()
                if any(kw in text_lower for kw in ["próximo", "pula", "skip", "next", "avançar"]):
                    next_stage = current_stage + 1 if current_stage < 10 else None
                    lia_message = f"Ok, avançando para a próxima etapa: **{WIZARD_STAGES[current_stage]['panel'] if current_stage < 10 else 'Finalização'}**"
                elif any(kw in text_lower for kw in ["voltar", "anterior", "back"]):
                    next_stage = current_stage - 1 if current_stage > 1 else 1
                    lia_message = f"Voltando para a etapa anterior: **{WIZARD_STAGES[next_stage - 1]['panel']}**"
                else:
                    lia_message = "Entendi que você quer mudar de assunto. Posso ajudar com:\n"
                    lia_message += "• Avançar para a próxima etapa\n"
                    lia_message += "• Voltar para a etapa anterior\n"
                    lia_message += "• Responder dúvidas sobre salário, skills, ou processo\n"
                    lia_message += "\nO que prefere?"
                    next_stage = current_stage

            elif classification.intent_type == IntentType.REUSE_VACANCY:
                # User wants to search or reuse previous vacancies
                criteria = await vacancy_search_service.extract_search_criteria(request.user_input)
                has_minimum = vacancy_search_service.validate_minimum_criteria(criteria)

                # Check if user just wants to list/see vacancies (no specific criteria)
                text_lower = request.user_input.lower()
                is_list_query = any(kw in text_lower for kw in ["ultimas", "últimas", "recentes", "listar", "mostrar", "ver", "quais"])

                if is_list_query and not has_minimum:
                    # List recent vacancies without specific criteria
                    vacancies = await vacancy_search_service.search_vacancies(
                        criteria={},  # Empty criteria = list recent
                        company_id=company_id,
                        db=db,
                        limit=10
                    )

                    if vacancies:
                        lia_message = f"📋 Encontrei **{len(vacancies)}** vaga(s) recentes da empresa:\n\n"
                        for i, v in enumerate(vacancies[:8], 1):
                            status_emoji = "✅" if v.status == "contratado" else "❌" if v.status == "cancelado" else "🔄"
                            date_str = v.date_closed.strftime("%d/%m/%Y") if v.date_closed else "Em aberto"
                            lia_message += f"{i}. **{v.title}** {status_emoji}\n"
                            if v.department:
                                lia_message += f"   📁 Área: {v.department}\n"
                            if v.seniority_level:
                                lia_message += f"   🎯 Nível: {v.seniority_level}\n"
                            if v.manager:
                                lia_message += f"   👤 Gestor: {v.manager}\n"
                            lia_message += f"   📅 {date_str}\n\n"

                        lia_message += "---\n"
                        lia_message += "🔍 Quer filtrar por algum critério específico (cargo, área, gestor, ano)?\n"
                        lia_message += "📋 Ou clique em **Usar anterior** para selecionar uma vaga como base."

                        suggestions_data['vacancy_search_results'] = [v.model_dump(mode='json') for v in vacancies]
                    else:
                        lia_message = "Ainda não encontrei vagas anteriores registradas no sistema.\n\n"
                        lia_message += "Vamos criar uma nova vaga? Me diga o cargo e os requisitos principais!"
                elif has_minimum:
                    # Search with specific criteria
                    vacancies = await vacancy_search_service.search_vacancies(
                        criteria=criteria,
                        company_id=company_id,
                        db=db,
                        limit=10
                    )

                    if vacancies:
                        criteria_desc = []
                        if criteria.get('cargo'):
                            criteria_desc.append(f"cargo: {criteria['cargo']}")
                        if criteria.get('area'):
                            criteria_desc.append(f"área: {criteria['area']}")
                        if criteria.get('gestor'):
                            criteria_desc.append(f"gestor: {criteria['gestor']}")
                        criteria_text = ", ".join(criteria_desc) if criteria_desc else "seus critérios"

                        lia_message = f"🎯 Encontrei **{len(vacancies)}** vaga(s) para {criteria_text}:\n\n"
                        for i, v in enumerate(vacancies[:5], 1):
                            status_emoji = "✅" if v.status == "contratado" else "❌" if v.status == "cancelado" else "🔄"
                            lia_message += f"{i}. **{v.title}** - {v.department or 'Sem área'} {status_emoji}\n"
                            if v.manager:
                                lia_message += f"   👤 Gestor: {v.manager}\n"
                            if v.hired_candidate:
                                lia_message += f"   ✅ Contratado: {v.hired_candidate}\n"

                        lia_message += "\n---\n"
                        lia_message += "Qual vaga você gostaria de usar como base? Digite o número ou clique para selecionar."

                        suggestions_data['vacancy_search_results'] = [v.model_dump(mode='json') for v in vacancies]
                    else:
                        lia_message = "Não encontrei vagas anteriores com esses critérios.\n\n"
                        lia_message += "💡 Tente outros termos de busca ou podemos criar uma nova vaga do zero.\n"
                        lia_message += "O que você prefere?"
                else:
                    lia_message = "Entendi que você quer buscar vagas anteriores! 🔍\n\n"
                    lia_message += "Para encontrar a vaga certa, me diga mais detalhes:\n"
                    lia_message += "• Qual era o cargo ou título?\n"
                    lia_message += "• Em qual área/departamento?\n"
                    lia_message += "• De qual período (ex: ano passado, 2024)?\n\n"
                    lia_message += "Ou digite **listar vagas** para ver todas as vagas recentes."

                next_stage = current_stage  # Stay on current stage

            else:
                benchmarks = await get_stage_benchmarks(db, company_id, job_draft, current_stage)

                if current_stage == 1:
                    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
                    _persona = SystemPromptBuilder.build(agent_type="job_planner", extra_instructions="Analise a descrição e extraia informações estruturadas.")
                    prompt = f"""{_persona}

Analise esta descrição de vaga e extraia TODAS as informações possíveis.

    ## Descrição fornecida pelo recrutador:
    {request.user_input}

    {company_context}

    ## INSTRUÇÕES CRÍTICAS:
    1. Extraia TODAS as tecnologias, linguagens, frameworks, ferramentas e skills técnicas mencionadas
    2. Se mencionar "desenvolvedor Python", inclua "Python" em detected_skills
    3. Se mencionar frameworks como "FastAPI", "Django", "React", inclua cada um em detected_skills
    4. Se mencionar bancos de dados como "PostgreSQL", "MongoDB", inclua em detected_skills
    5. Se mencionar ferramentas como "Docker", "Kubernetes", "AWS", inclua em detected_skills
    6. Competências comportamentais vão em behavioral_skills (liderança, comunicação, etc.)

    ## Extraia e retorne um JSON com:
    {{
      "job_title": "título da vaga (ex: Desenvolvedor Python, Analista de Dados)",
      "department": "departamento/área ou null se não mencionado",
      "seniority": "junior/pleno/senior/lead/staff",
      "work_model": "presencial/híbrido/remoto",
      "location": "cidade/região ou null se não mencionado",
      "detected_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
      "behavioral_skills": ["Comunicação", "Trabalho em equipe"],
      "experience_years": "X-Y anos ou null",
      "education": "formação mínima ou null"
    }}

    ## IMPORTANTE:
    - detected_skills DEVE conter TODAS as tecnologias técnicas mencionadas, uma por item
    - Não agrupe skills - liste cada uma separadamente
    - Responda APENAS em JSON válido, sem texto adicional."""

                    logger.info(f"[WIZARD-STAGE1] Prompt enviado para LLM: {prompt[:500]}...")
                    response = await llm_service.generate(prompt, provider="gemini")
                    logger.info(f"[WIZARD-STAGE1] Resposta do LLM: {response[:500]}...")

                    try:
                        json_match = re.search(r'\{[\s\S]*\}', response)
                        if json_match:
                            raw_criteria = json.loads(json_match.group())
                            logger.info(f"[WIZARD-STAGE1] Critérios brutos extraídos: {raw_criteria}")

                            detected_criteria = {
                                "cargo": raw_criteria.get("job_title"),
                                "gestorArea": raw_criteria.get("manager") or raw_criteria.get("department"),
                                "department": raw_criteria.get("department"),
                                "manager": raw_criteria.get("manager"),
                                "competenciasTecnicas": raw_criteria.get("detected_skills", []),
                                "competenciasComportamentais": raw_criteria.get("behavioral_skills", []),
                                "senioridadeIdiomas": raw_criteria.get("seniority"),
                                "modeloTrabalho": raw_criteria.get("work_model"),
                                "localizacao": raw_criteria.get("location"),
                                "tipoContrato": None,
                                "salario": None,
                                "experiencia": raw_criteria.get("experience_years"),
                                "formacao": raw_criteria.get("education")
                            }

                            for key, value in detected_criteria.items():
                                if value is not None:
                                    job_draft[key] = value

                            if detected_criteria.get('cargo'):
                                try:
                                    skill_suggestions = skills_catalog_service.suggest_skills(
                                        role=detected_criteria['cargo'],
                                        seniority=detected_criteria.get('senioridadeIdiomas', 'pleno'),
                                        limit=10
                                    )
                                    job_draft['skill_suggestions'] = skill_suggestions

                                    detected_skills = detected_criteria.get('competenciasTecnicas', [])
                                    if isinstance(detected_skills, str):
                                        detected_skills = [detected_skills]

                                    skill_quality_feedback = skills_catalog_service.validate_skills_quality(
                                        detected_skills=detected_skills,
                                        seniority=detected_criteria.get('senioridadeIdiomas', 'pleno')
                                    )
                                    job_draft['skill_quality_feedback'] = skill_quality_feedback

                                    logger.info(f"[WIZARD-STAGE1] Skill suggestions for role '{detected_criteria['cargo']}': {len(skill_suggestions.get('technical_skills', []))} tech skills")
                                    logger.info(f"[WIZARD-STAGE1] Skill quality feedback: {skill_quality_feedback.get('status')} - {skill_quality_feedback.get('message')}")
                                except Exception as skill_err:
                                    logger.warning(f"[WIZARD-STAGE1] Failed to get skill suggestions: {skill_err}")

                                try:
                                    detected_responsibilities = raw_criteria.get('responsibilities', [])
                                    if isinstance(detected_responsibilities, str):
                                        detected_responsibilities = [detected_responsibilities]

                                    responsibilities_analysis = responsibilities_catalog_service.get_expected_responsibilities(
                                        role=detected_criteria['cargo'],
                                        seniority=detected_criteria.get('senioridadeIdiomas', 'pleno'),
                                        detected_responsibilities=detected_responsibilities
                                    )
                                    job_draft['responsibilities_analysis'] = responsibilities_analysis
                                    job_draft['detected_responsibilities'] = detected_responsibilities
                                    job_draft['suggested_responsibilities'] = responsibilities_analysis.get('missing_responsibilities', [])

                                    logger.info(f"[WIZARD-STAGE1] Responsibilities analysis for role '{detected_criteria['cargo']}': completeness={responsibilities_analysis.get('completeness_score')}%")
                                    logger.info(f"[WIZARD-STAGE1] Responsibilities validation: {responsibilities_analysis.get('validation', {}).get('status')} - {responsibilities_analysis.get('validation', {}).get('message')}")
                                except Exception as resp_err:
                                    logger.warning(f"[WIZARD-STAGE1] Failed to get responsibilities analysis: {resp_err}")

                            # Calculate confidence for stage 1 detected fields using the service
                            for field in ['cargo', 'senioridadeIdiomas', 'modeloTrabalho', 'localizacao']:
                                if detected_criteria.get(field):
                                    _track_field_confidence(confidence_service, field_origins, field, detected_criteria[field], "text_extraction")

                            detected_high_conf = []
                            detected_low_conf = []
                            for field, origin in field_origins.items():
                                if origin.get('confidence', 0.5) >= 0.70:
                                    detected_high_conf.append(field)
                                else:
                                    detected_low_conf.append(field)

                            stage1_response_style = "assertive" if len(detected_low_conf) == 0 else "questioning"

                            # Enhanced consultive response with sources and confidence
                            confidence_pct = int(len(detected_high_conf) / max(len(detected_high_conf) + len(detected_low_conf), 1) * 100)

                            if stage1_response_style == "assertive":
                                lia_intro = f"Excelente! Analisei sua descrição e identifiquei os critérios com **{confidence_pct}% de confiança**.\n\n"
                                lia_intro += "📊 **Fontes consultadas:** descrição fornecida + histórico da empresa + benchmarks de mercado\n\n"
                            else:
                                lia_intro = f"Entendi sua descrição! Detectei alguns critérios (confiança: {confidence_pct}%), mas preciso confirmar alguns pontos:\n\n"
                                lia_intro += "📊 **Fontes consultadas:** descrição fornecida + histórico da empresa\n\n"

                            criteria_lines = []
                            if detected_criteria.get('cargo'):
                                criteria_lines.append(f"• **Cargo**: {detected_criteria['cargo']}")
                            if detected_criteria.get('senioridadeIdiomas'):
                                criteria_lines.append(f"• **Senioridade**: {detected_criteria['senioridadeIdiomas']}")
                            if detected_criteria.get('gestorArea'):
                                criteria_lines.append(f"• **Área**: {detected_criteria['gestorArea']}")
                            if detected_criteria.get('modeloTrabalho'):
                                criteria_lines.append(f"• **Modelo de trabalho**: {detected_criteria['modeloTrabalho']}")
                            if detected_criteria.get('localizacao'):
                                criteria_lines.append(f"• **Localização**: {detected_criteria['localizacao']}")

                            skills = detected_criteria.get('competenciasTecnicas', [])
                            if skills:
                                skills_list = skills if isinstance(skills, list) else [skills]
                                criteria_lines.append(f"• **Skills técnicas**: {', '.join(skills_list[:5])}")

                            behavioral = detected_criteria.get('competenciasComportamentais', [])
                            if behavioral:
                                behavioral_list = behavioral if isinstance(behavioral, list) else [behavioral]
                                criteria_lines.append(f"• **Competências comportamentais**: {', '.join(behavioral_list[:5])}")

                            # Add salary information with market alignment
                            salary_info = detected_criteria.get('salario', {})
                            suggested_salary = job_draft.get('suggested_salary', {})

                            if salary_info or suggested_salary:
                                salary_lines = []

                                # Helper to safely parse salary values
                                def parse_salary(val):
                                    if val is None:
                                        return None
                                    try:
                                        if isinstance(val, (int, float)):
                                            return float(val)
                                        # Handle string values (remove formatting)
                                        cleaned = str(val).replace('.', '').replace(',', '.').replace('R$', '').strip()
                                        return float(cleaned) if cleaned else None
                                    except (ValueError, TypeError):
                                        return None

                                # User-provided salary (if any)
                                user_min = parse_salary(salary_info.get('min') if isinstance(salary_info, dict) else None)
                                user_max = parse_salary(salary_info.get('max') if isinstance(salary_info, dict) else None)

                                # Suggested salary from market data
                                suggested_min = parse_salary(suggested_salary.get('min') or job_draft.get('salary_min_suggested'))
                                suggested_max = parse_salary(suggested_salary.get('max') or job_draft.get('salary_max_suggested'))
                                market_source = suggested_salary.get('source', 'benchmark de mercado')

                                if user_min and user_max and user_min > 0 and user_max > 0:
                                    salary_lines.append(f"• **Salário informado**: R$ {user_min:,.0f} - R$ {user_max:,.0f}")
                                    if suggested_min and suggested_max and suggested_min > 0 and suggested_max > 0:
                                        # Check market alignment
                                        user_avg = (user_min + user_max) / 2
                                        market_avg = (suggested_min + suggested_max) / 2
                                        diff_pct = ((user_avg - market_avg) / market_avg) * 100 if market_avg > 0 else 0

                                        if abs(diff_pct) <= 10:
                                            alignment = "✅ Alinhado com o mercado"
                                        elif diff_pct > 10:
                                            alignment = f"📈 {diff_pct:.0f}% acima do mercado"
                                        else:
                                            alignment = f"⚠️ {abs(diff_pct):.0f}% abaixo do mercado"

                                        salary_lines.append(f"• **Sugestão de mercado**: R$ {suggested_min:,.0f} - R$ {suggested_max:,.0f} ({alignment})")
                                elif suggested_min and suggested_max and suggested_min > 0 and suggested_max > 0:
                                    salary_lines.append(f"• **Salário sugerido**: R$ {suggested_min:,.0f} - R$ {suggested_max:,.0f} ({market_source})")

                                if salary_lines:
                                    criteria_lines.extend(salary_lines)

                            lia_message = lia_intro + "\n".join(criteria_lines)

                            if detected_low_conf:
                                lia_message += "\n\n**Preciso confirmar:**\n"
                                question_map = {
                                    'cargo': "Qual o título exato do cargo?",
                                    'senioridadeIdiomas': "Qual o nível de senioridade esperado?",
                                    'gestorArea': "Para qual área/departamento é a vaga?",
                                    'localizacao': "Qual a localidade da vaga?",
                                    'modeloTrabalho': "Qual o modelo de trabalho (presencial/híbrido/remoto)?"
                                }
                                questions_added = 0
                                for field in detected_low_conf:
                                    base_field = field.replace('skill_', '')
                                    if base_field in question_map and questions_added < 3:
                                        lia_message += f"• {question_map[base_field]}\n"
                                        questions_added += 1

                            if company_departments:
                                dept_names = ', '.join([d['name'] for d in company_departments[:5]])
                                lia_message += f"\n\n📋 **Departamentos disponíveis:** {dept_names}"

                            skill_quality_fb = job_draft.get('skill_quality_feedback', {})
                            if skill_quality_fb.get('status') == 'too_few':
                                lia_message += f"\n\n⚠️ **Atenção sobre skills:** {skill_quality_fb.get('message', '')}"
                                suggested = job_draft.get('skill_suggestions', {}).get('technical_skills', [])
                                if suggested:
                                    lia_message += f"\n💡 **Sugestões do catálogo:** {', '.join(suggested[:5])}"
                            elif skill_quality_fb.get('status') == 'too_many':
                                lia_message += f"\n\n⚠️ **Atenção sobre skills:** {skill_quality_fb.get('message', '')}"

                            responsibilities_analysis = job_draft.get('responsibilities_analysis', {})
                            detected_resp = job_draft.get('detected_responsibilities', [])
                            if detected_resp:
                                resp_completeness = responsibilities_analysis.get('completeness_score', 0)
                                lia_message += f"\n\n📋 **Responsabilidades** (completude: {resp_completeness}%)"
                                lia_message += f"\n✅ **Detectadas:** {', '.join(detected_resp[:3])}"

                            resp_validation = responsibilities_analysis.get('validation', {})
                            if resp_validation.get('status') == 'warning':
                                lia_message += f"\n\n⚠️ **Atenção sobre responsabilidades:** {resp_validation.get('message', '')}"
                                suggested_resp = job_draft.get('suggested_responsibilities', [])
                                if suggested_resp:
                                    lia_message += "\n💡 **Sugestões do catálogo:**"
                                    for resp in suggested_resp[:4]:
                                        lia_message += f"\n  • {resp}"

                            # Add historical suggestions context to response
                            if job_draft.get('work_model_suggested') or job_draft.get('employment_type_suggested') or job_draft.get('location_suggested'):
                                suggestion_parts = []
                                if job_draft.get('work_model_suggested'):
                                    ctx = job_draft.get('work_model_suggestion_context', '')
                                    suggestion_parts.append(f"**Modelo de trabalho**: {job_draft.get('work_model')} ({ctx})")
                                if job_draft.get('employment_type_suggested'):
                                    ctx = job_draft.get('employment_type_suggestion_context', '')
                                    suggestion_parts.append(f"**Tipo de contrato**: {job_draft.get('employment_type')} ({ctx})")
                                if job_draft.get('location_suggested'):
                                    ctx = job_draft.get('location_suggestion_context', '')
                                    suggestion_parts.append(f"**Localização**: {job_draft.get('location')} ({ctx})")

                                if suggestion_parts:
                                    lia_message += "\n\n📊 **Sugestões baseadas no seu histórico**:\n"
                                    lia_message += "\n".join(['• ' + p for p in suggestion_parts])
                                    lia_message += "\n\n*Esses valores foram sugeridos com base nas suas vagas anteriores. Deseja manter ou alterar?*"

                            if stage1_response_style == "assertive":
                                lia_message += "\n\n---\n\n**Próximo passo:** Revise as informações acima. Você pode:"
                                lia_message += "\n• ✅ **Aceitar** as sugestões de competências e responsabilidades"
                                lia_message += "\n• ✏️ **Ajustar** - me informe aqui no chat o que deseja alterar e eu ajusto para você"
                                lia_message += "\n\nQuando estiver satisfeito, clique em **Confirmar Critérios**."
                            else:
                                lia_message += "\n\n---\n\nMe informe aqui no chat o que deseja ajustar e eu faço as alterações para você."
                                lia_message += "\n\nQuando estiver satisfeito, clique em **Confirmar Critérios**."

                            suggestions_data['skill_suggestions'] = job_draft.get('skill_suggestions', {})
                            suggestions_data['skill_quality_feedback'] = job_draft.get('skill_quality_feedback', {})
                            suggestions_data['responsibilities_analysis'] = job_draft.get('responsibilities_analysis', {})
                            suggestions_data['detected_responsibilities'] = job_draft.get('detected_responsibilities', [])
                            suggestions_data['suggested_responsibilities'] = job_draft.get('suggested_responsibilities', [])
                        else:
                            lia_message = "Entendi a descrição! Por favor, me informe se deseja ajustar algo ou adicione mais detalhes."
                            detected_criteria = {}
                    except Exception:
                        lia_message = "Consegui processar a descrição. Verifique os critérios detectados no painel lateral."
                        detected_criteria = {}

                elif current_stage == 2:
                    dept_list = ""
                    if company_departments:
                        dept_list = f"\n\n📋 **Departamentos cadastrados:** {', '.join([d['name'] for d in company_departments[:8]])}"

                    # Competency gap analysis before advancing to Stage 3
                    job_title_for_gap = job_draft.get('cargo') or job_draft.get('job_title') or ''
                    seniority_for_gap = job_draft.get('senioridade') or job_draft.get('seniority') or 'Pleno'
                    detected_tech = job_draft.get('competenciasTecnicas') or job_draft.get('detected_skills') or []
                    detected_behav = job_draft.get('competenciasComportamentais') or job_draft.get('behavioral_skills') or []

                    if isinstance(detected_tech, str):
                        detected_tech = [detected_tech]
                    if isinstance(detected_behav, str):
                        detected_behav = [detected_behav]

                    competency_gap_message = ""
                    try:
                        if job_title_for_gap:
                            gap_analysis = await analyze_competency_gaps(
                                job_title=job_title_for_gap,
                                seniority=seniority_for_gap,
                                detected_technical=detected_tech,
                                detected_behavioral=detected_behav
                            )

                            job_draft['competency_gap_analysis'] = gap_analysis
                            suggestions_data['competency_gap_analysis'] = gap_analysis

                            if gap_analysis.get('missing_technical') or gap_analysis.get('missing_behavioral'):
                                gap_feedback_parts = []

                                gap_feedback_parts.append(f"\n\n📊 **Análise de Competências** (completude: {gap_analysis['completeness_score']}%)")
                                gap_feedback_parts.append(gap_analysis['analysis_summary'])

                                if gap_analysis.get('missing_technical'):
                                    tech_names = [s.get('name', str(s)) for s in gap_analysis['missing_technical'][:5]]
                                    gap_feedback_parts.append(f"\n🔧 **Competências técnicas sugeridas** (baseado no cargo {job_title_for_gap}):")
                                    gap_feedback_parts.extend([f"  • {name}" for name in tech_names])

                                if gap_analysis.get('missing_behavioral'):
                                    behav_names = [s.get('name', str(s)) for s in gap_analysis['missing_behavioral'][:3]]
                                    gap_feedback_parts.append("\n🎯 **Competências comportamentais sugeridas**:")
                                    gap_feedback_parts.extend([f"  • {name}" for name in behav_names])

                                gap_feedback_parts.append("\n*Gostaria de adicionar alguma dessas competências à vaga?*")

                                competency_gap_message = "\n".join(gap_feedback_parts)
                                job_draft['competency_gap_feedback'] = competency_gap_message
                    except Exception as e:
                        logger.warning(f"Competency gap analysis failed: {e}")

                    lia_message = f"""Ótimo progresso! Vamos às **Informações Básicas**. 📋
    {dept_list}

    **O que precisamos confirmar:**
    • Quantas posições você precisa preencher?
    • Qual o departamento responsável?
    • Quem será o gestor da vaga?
    • Prazo para preenchimento
    • Tipo de contratação (CLT, PJ, Temporário)

    💡 *Se algum campo já estiver preenchido no painel, é só confirmar ou ajustar.*
    {competency_gap_message}

    ---

    ✅ **Próximo passo:** Após confirmar, vamos para as **competências** onde sugerirei skills baseadas no cargo.

    *Campos com ícone 📊 foram sugeridos com base no seu histórico.*"""

                    suggestions_data = {
                        "departments": [d["name"] for d in company_departments] if company_departments else [],
                        "contract_types": ["CLT", "PJ", "Temporário", "Estágio", "Terceirizado"]
                    }

                    if job_draft.get('competency_gap_analysis'):
                        suggestions_data['competency_gap_analysis'] = job_draft['competency_gap_analysis']

                elif current_stage == 3:
                    skills_benchmark = benchmarks.get("suggested_skills", {})
                    skills_list = skills_benchmark.get("skills", [])

                    skills_suggestion = ""
                    if skills_list:
                        tech_skills = [s["skill"] for s in skills_list if s.get("category") == "Técnico"][:6]
                        if tech_skills:
                            skills_suggestion = f"\n\n🎯 **Skills sugeridas** (baseado em vagas similares):\n• {chr(10).join(['• ' + s for s in tech_skills])}"

                    lia_message = f"""Excelente! Agora vamos às **Competências**. 🎯
    {skills_suggestion}

    📊 **Fontes da minha análise:**
    • Histórico de vagas similares na sua empresa
    • Benchmark de mercado por área/senioridade
    • Skills identificadas na descrição original

    **Competências Técnicas:**
    Sugiro as skills abaixo. Me diga quais ajustes deseja e eu aplico. Para cada skill, defina:
    • **Nível** (Básico → Expert)
    • **Peso** (1-5★) - impacto na Nota LIA
    • **Obrigatório/Desejável**

    **Competências Comportamentais:**
    Aspectos sugeridos para este perfil:
    • Comunicação • Trabalho em equipe
    • Resolução de problemas • Proatividade

    💡 *Recomendação: 5-8 competências técnicas e 3-5 comportamentais para triagem equilibrada.*

    ---

    ✅ **Próximo passo:** Após confirmar, vamos gerar as **perguntas de triagem WSI** baseadas nas competências selecionadas.

    ❓ *Quer que eu sugira competências específicas para este perfil? Pergunte!*"""

                    suggestions_data["suggested_skills"] = skills_list

                elif current_stage == 4:
                    benefits_list = ""
                    if company_benefits:
                        benefits_list = "\n\n✅ **Benefícios cadastrados da empresa:**\n" + "\n".join([f"• {b['name']}" for b in company_benefits[:10]])
                    else:
                        benefits_list = "\n\n⚠️ *Nenhum benefício cadastrado. Você pode adicionar benefícios em Configurações → Benefícios.*"

                    salary_info = ""
                    learning_info = ""
                    historical_salary_info = ""
                    internal_salary = benchmarks.get("internal_salary", {})
                    market_salary = benchmarks.get("market_salary", {})
                    combined = benchmarks.get("combined_recommendation", {})
                    learning_adjustments = benchmarks.get("learning_adjustments", {})

                    # Get historical salary patterns from similar jobs
                    job_title_for_salary = job_draft.get('cargo') or job_draft.get('job_title') or ''
                    seniority_for_salary = job_draft.get('senioridade') or job_draft.get('seniority') or 'Pleno'

                    try:
                        salary_patterns = await get_historical_salary_patterns(
                            db,
                            company_id,
                            job_title_for_salary,
                            seniority_for_salary
                        )
                        if salary_patterns.get('has_data'):
                            avg_min = salary_patterns['avg_min']
                            avg_max = salary_patterns['avg_max']
                            sample = salary_patterns['sample_size']
                            historical_salary_info = f"\n\n💰 **Referência histórica** ({sample} vagas similares): R$ {avg_min:,.0f} - R$ {avg_max:,.0f}"
                            job_draft['salary_suggestion'] = historical_salary_info

                            # Track field origin for historical salary suggestion
                            field_origins['salary_historical'] = {
                                'source': 'historical_pattern',
                                'confidence': min(0.85, 0.5 + (sample * 0.05)),
                                'avg_min': avg_min,
                                'avg_max': avg_max,
                                'sample_size': sample
                            }

                            # Pre-fill salary if not already set
                            if not job_draft.get('salary_min') and not job_draft.get('salario'):
                                job_draft['salary_min'] = avg_min
                                job_draft['salary_max'] = avg_max
                                job_draft['salary_suggested'] = True
                                logger.info(f"Pre-filled salary from historical patterns: R$ {avg_min:,.0f} - R$ {avg_max:,.0f}")
                    except Exception as e:
                        logger.warning(f"Could not get historical salary patterns: {e}")

                    if internal_salary.get("sample_size", 0) > 0 or market_salary.get("min"):
                        salary_info = "\n\n💰 **Sugestão de faixa salarial:**"

                        if combined.get("recommended_min"):
                            salary_info += f"\n• Recomendado: R$ {combined.get('recommended_min', 0):,.0f} - R$ {combined.get('recommended_max', 0):,.0f}"
                        elif internal_salary.get("median"):
                            salary_info += f"\n• Mediana interna: R$ {internal_salary['median']:,.0f}"
                        elif market_salary.get("median"):
                            salary_info += f"\n• Mediana de mercado: R$ {market_salary['median']:,.0f}"

                        if internal_salary.get("trend") == "increasing":
                            salary_info += "\n• 📈 Tendência de alta nos últimos meses"
                        elif internal_salary.get("trend") == "decreasing":
                            salary_info += "\n• 📉 Tendência de queda nos últimos meses"

                    # Registrar ajustes de aprendizado (já aplicados nos benchmarks) e gerar mensagem
                    # NOTA: O ajuste já foi aplicado em get_stage_benchmarks() - aqui apenas registramos e informamos
                    if "salary_range" in learning_adjustments:
                        salary_adj = learning_adjustments["salary_range"]
                        adjustment_pct = salary_adj.get("adjustment_pct", 0)

                        if adjustment_pct and abs(adjustment_pct) > 5:
                            # Aplicar recomendação ajustada ao draft se não tiver salário definido
                            # Os valores de combined já estão ajustados pelo learning
                            if combined.get("recommended_min") and not job_draft.get("salary_min"):
                                job_draft["salary_min"] = combined.get("recommended_min")
                                job_draft["salary_max"] = combined.get("recommended_max", combined.get("recommended_min"))

                            # Registrar no field_origins que usou learning
                            field_origins["salary_range"] = {
                                "source": "learning_adjusted",
                                "original_min": combined.get("original_recommended_min"),
                                "original_max": combined.get("original_recommended_max"),
                                "adjusted_min": combined.get("recommended_min"),
                                "adjusted_max": combined.get("recommended_max"),
                                "adjustment_pct": adjustment_pct,
                                "confidence": salary_adj.get("confidence", "low"),
                                "sample_size": salary_adj.get("sample_size", 0)
                            }

                            # Gerar mensagem sobre o ajuste
                            direction_text = "para cima" if adjustment_pct > 0 else "para baixo"
                            confidence_emoji = "🟢" if salary_adj.get("confidence") == "high" else "🟡" if salary_adj.get("confidence") == "medium" else "🔴"
                            learning_info = f"\n\n🧠 **Ajuste baseado em aprendizado:** Com base no histórico de correções da sua empresa, ajustei a faixa salarial em **{adjustment_pct:+.0f}%** {direction_text}. {confidence_emoji} Confiança: {salary_adj.get('confidence', 'low')}"

                            logger.info(f"Learning adjustment applied in benchmarks: {adjustment_pct:+.1f}% for role {job_draft.get('cargo') or job_draft.get('job_title')}")

                    lia_message = f"""Perfeito! Vamos definir a **Remuneração**. 💰

    📊 **Minha análise de mercado:**
    {historical_salary_info}{salary_info}{learning_info}
    {benefits_list}

    **O que precisamos definir:**
    • Faixa salarial (mínimo - máximo)
    • Bônus ou PLR (se aplicável)
    • Benefícios oferecidos nesta vaga

    💡 *Os benefícios da empresa já estão pré-selecionados no painel. Ajuste conforme necessário.*

    ---

    ✅ **Próximo passo:** Após confirmar a remuneração, vamos definir as **competências** técnicas e comportamentais.

    ❓ *Quer saber mais sobre salários de mercado para este cargo? Pergunte!*"""

                    suggestions_data = {
                        "benefits": [{"name": b["name"], "selected": True} for b in company_benefits] if company_benefits else [],
                        "salary_benchmark": combined,
                        "learning_adjustments": learning_adjustments,
                        "historical_salary": salary_patterns if 'salary_patterns' in dir() and salary_patterns.get('has_data') else None
                    }

                elif current_stage == 5:
                    # Get detected competencies for WSI question generation
                    detected_tech = job_draft.get('competenciasTecnicas') or job_draft.get('detected_skills') or []
                    detected_behav = job_draft.get('competenciasComportamentais') or job_draft.get('behavioral_skills') or []
                    job_title_for_wsi = job_draft.get('cargo') or job_draft.get('job_title') or ''
                    seniority_for_wsi = job_draft.get('senioridade') or job_draft.get('seniority') or 'Pleno'

                    if isinstance(detected_tech, str):
                        detected_tech = [detected_tech]
                    if isinstance(detected_behav, str):
                        detected_behav = [detected_behav]

                    # Build competencies summary for WSI suggestions
                    wsi_competency_summary = ""
                    wsi_question_suggestions = []

                    if detected_tech or detected_behav:
                        wsi_competency_summary = "\n\n📋 **Competências identificadas para triagem:**"

                        if detected_tech:
                            tech_names = detected_tech[:5] if isinstance(detected_tech[0], str) else [c.get('name', str(c)) for c in detected_tech[:5]]
                            wsi_competency_summary += f"\n**Técnicas:** {', '.join(tech_names)}"

                            # Generate suggested questions for technical competencies
                            for tech in tech_names[:3]:
                                wsi_question_suggestions.append({
                                    "competency": tech,
                                    "type": "technical",
                                    "suggested_question": f"Descreva um projeto em que você utilizou {tech} para resolver um problema complexo.",
                                    "framework": "CBI"
                                })

                        if detected_behav:
                            behav_names = detected_behav[:3] if isinstance(detected_behav[0], str) else [c.get('name', c.get('competency', str(c))) for c in detected_behav[:3]]
                            wsi_competency_summary += f"\n**Comportamentais:** {', '.join(behav_names)}"

                            # Generate suggested questions for behavioral competencies
                            behavioral_questions_map = {
                                "comunicação": "Conte sobre uma situação em que você precisou comunicar uma ideia complexa de forma simples.",
                                "trabalho em equipe": "Descreva um momento em que você colaborou com uma equipe para atingir um objetivo desafiador.",
                                "liderança": "Relate uma experiência em que você liderou uma equipe ou iniciativa.",
                                "resolução de problemas": "Dê um exemplo de um problema difícil que você resolveu e como chegou à solução.",
                                "proatividade": "Conte sobre uma situação em que você identificou uma oportunidade de melhoria e tomou iniciativa."
                            }

                            for behav in behav_names[:2]:
                                behav_lower = behav.lower()
                                question = behavioral_questions_map.get(behav_lower, 
                                    f"Descreva uma situação em que você demonstrou {behav} no ambiente de trabalho.")
                                wsi_question_suggestions.append({
                                    "competency": behav,
                                    "type": "behavioral",
                                    "suggested_question": question,
                                    "framework": "BigFive"
                                })

                        wsi_competency_summary += f"\n\n🎯 **{len(wsi_question_suggestions)} perguntas sugeridas** baseadas nas competências detectadas."

                    suggestions_data['wsi_question_suggestions'] = wsi_question_suggestions
                    suggestions_data['detected_competencies'] = {
                        'technical': detected_tech,
                        'behavioral': detected_behav
                    }

                    lia_message = f"""Perfeito! Agora vou gerar as **Perguntas de Triagem WSI**. 📝
    {wsi_competency_summary}

    🎯 **Metodologia WSI aplicada:**
    As perguntas seguem a metodologia WeDoTalent Skill Index com 7 blocos:
    1. Autodeclaração de contexto
    2. Micro-cases técnicos
    3. Situacional comportamental
    4. Fit cultural
    5. Autodeclaração de habilidades
    6. Perguntas técnicas específicas
    7. Perguntas de elegibilidade

    💡 *Recomendação: Selecione 4-6 perguntas para um formulário objetivo (3-5 min de resposta).*

    ---

    🔄 Gerando perguntas personalizadas baseadas nas competências selecionadas...

    ✅ **Próximo passo:** Após confirmar as perguntas, vamos para a **revisão final** onde você verá tudo consolidado.

    ❓ *Quer saber mais sobre a metodologia WSI? Pergunte!*"""

                elif current_stage == 6:
                    job_context = request.context or {}

                    job_data_for_completeness = {
                        "title": job_draft.get("cargo") or job_draft.get("job_title"),
                        "seniority_level": job_draft.get("senioridadeIdiomas") or job_draft.get("seniority"),
                        "department": job_draft.get("gestorArea") or job_draft.get("department"),
                        "salary_range": job_draft.get("salario") or job_draft.get("salary_range"),
                        "benefits": job_draft.get("beneficios") or job_draft.get("benefits"),
                        "technical_requirements": job_draft.get("competenciasTecnicas") or job_draft.get("detected_skills") or job_draft.get("tech_stack"),
                        "behavioral_competencies": job_draft.get("competenciasComportamentais") or job_draft.get("behavioral_skills"),
                        "description": job_draft.get("descricao") or job_draft.get("description"),
                        "requirements": job_draft.get("requisitos") or job_draft.get("requirements"),
                        "work_model": job_draft.get("modeloTrabalho") or job_draft.get("work_model"),
                        "location": job_draft.get("localizacao") or job_draft.get("location"),
                        "employment_type": job_draft.get("tipoContrato") or job_draft.get("employment_type"),
                        "languages": job_draft.get("idiomas") or job_draft.get("languages"),
                        "manager": job_draft.get("gestor") or job_draft.get("manager"),
                        "deadline": job_draft.get("prazo") or job_draft.get("deadline"),
                    }

                    completeness_result = completeness_service.check_completeness(job_data_for_completeness)

                    suggestions_data['completeness'] = {
                        'score': completeness_result.completeness_score,
                        'can_publish': completeness_result.can_publish,
                        'missing_critical': completeness_result.missing_critical,
                        'missing_important': completeness_result.missing_important,
                        'filled_fields': completeness_result.filled_fields,
                        'toggled_off': completeness_result.toggled_off,
                        'field_details': completeness_result.field_details,
                    }

                    generated_description = jd_generator_service.generate_description(
                        job_data=job_draft,
                        company_context={
                            'about': company_profile.about if company_profile and hasattr(company_profile, 'about') else None,
                            'benefits': company_benefits
                        }
                    )
                    job_draft['generated_description'] = generated_description
                    suggestions_data['generated_description'] = generated_description

                    completeness_warnings = []
                    if completeness_result.missing_critical:
                        critical_labels = [completeness_service.get_field_label(f) for f in completeness_result.missing_critical]
                        completeness_warnings.append(f"⚠️ **Campos obrigatórios faltando:** {', '.join(critical_labels)}")

                    if completeness_result.missing_important:
                        important_labels = [completeness_service.get_field_label(f) for f in completeness_result.missing_important[:3]]
                        completeness_warnings.append(f"💡 **Recomendamos preencher:** {', '.join(important_labels)}")

                    warnings_text = "\n".join(completeness_warnings) if completeness_warnings else ""

                    if completeness_result.can_publish:
                        status_message = f"✅ **Completude: {completeness_result.completeness_score}%** - Vaga pronta para publicação!"
                    else:
                        status_message = f"⚠️ **Completude: {completeness_result.completeness_score}%** - Preencha os campos obrigatórios para publicar."

                    job_title = job_data_for_completeness.get("title") or "Vaga"
                    seniority = job_data_for_completeness.get("seniority_level") or ""
                    department = job_data_for_completeness.get("department") or "Não informado"
                    work_model = job_data_for_completeness.get("work_model") or "Não informado"
                    location = job_data_for_completeness.get("location") or "Não informado"
                    employment_type = job_data_for_completeness.get("employment_type") or "CLT"

                    salary_info = job_data_for_completeness.get("salary_range")
                    if isinstance(salary_info, dict):
                        salary_text = f"R$ {salary_info.get('min', 0):,.0f} - R$ {salary_info.get('max', 0):,.0f}"
                    elif salary_info:
                        salary_text = str(salary_info)
                    else:
                        salary_text = "A combinar"

                    tech_skills = job_data_for_completeness.get("technical_requirements") or []
                    if isinstance(tech_skills, list):
                        tech_skills_text = ", ".join([str(s) for s in tech_skills[:8]]) if tech_skills else "Não definidas"
                    else:
                        tech_skills_text = str(tech_skills) if tech_skills else "Não definidas"

                    behavioral_skills = job_data_for_completeness.get("behavioral_competencies") or []
                    if isinstance(behavioral_skills, list):
                        if behavioral_skills and isinstance(behavioral_skills[0], dict):
                            def get_competency_name(c):
                                return c.get('competency') or c.get('name') or c.get('skill') or str(c)
                            behavioral_text = ", ".join([get_competency_name(c) for c in behavioral_skills[:5]])
                        else:
                            behavioral_text = ", ".join([str(s) for s in behavioral_skills[:5]]) if behavioral_skills else "Não definidas"
                    else:
                        behavioral_text = str(behavioral_skills) if behavioral_skills else "Não definidas"

                    benefits_list = job_data_for_completeness.get("benefits") or []
                    if isinstance(benefits_list, list):
                        benefits_text = ", ".join(benefits_list[:6]) if benefits_list else "Não definidos"
                    else:
                        benefits_text = str(benefits_list)

                    languages = job_data_for_completeness.get("languages") or []
                    if isinstance(languages, list):
                        languages_text = ", ".join(languages) if languages else "Português"
                    else:
                        languages_text = str(languages) if languages else "Português"

                    one_page_summary = f"""**{job_title}** {f'- {seniority}' if seniority else ''}

    **Departamento:** {department}
    **Modelo:** {work_model} | **Local:** {location}
    **Contratação:** {employment_type}
    **Faixa Salarial:** {salary_text}

    **Competências Técnicas:** {tech_skills_text}
    **Competências Comportamentais:** {behavioral_text}
    **Benefícios:** {benefits_text}
    **Idiomas:** {languages_text}"""

                    jd_text = str(generated_description) if generated_description else "Descrição será gerada automaticamente."
                    jd_preview = jd_text[:500] + "..." if len(jd_text) > 500 else jd_text

                    # Build field origin summary for transparency
                    field_summary_lines = []
                    auto_filled_count = 0

                    # Define field label mappings
                    field_labels = {
                        'job_title': 'Cargo',
                        'seniority': 'Senioridade',
                        'department': 'Departamento',
                        'location': 'Localização',
                        'work_model': 'Modelo de Trabalho',
                        'employment_type': 'Tipo de Contratação',
                        'salary_range': 'Faixa Salarial',
                        'salary_historical': 'Referência Salarial',
                        'detected_skills': 'Competências Técnicas',
                        'behavioral_skills': 'Competências Comportamentais'
                    }

                    for field, origin in field_origins.items():
                        # Skip internal skill tracking fields
                        if field.startswith('skill_'):
                            continue

                        source = origin.get('source', 'manual')
                        confidence = origin.get('confidence', 0)

                        if source != 'manual' and source:
                            auto_filled_count += 1
                            # Choose emoji based on source type
                            if source == 'company_default':
                                emoji = '🏢'
                                source_label = 'Padrão da empresa'
                            elif source == 'historical_pattern':
                                emoji = '📊'
                                source_label = 'Histórico de vagas'
                            elif source == 'learning_adjusted':
                                emoji = '🧠'
                                source_label = 'Aprendizado de correções'
                            elif source == 'detected':
                                emoji = '🤖'
                                source_label = 'Detecção automática'
                            else:
                                emoji = '✨'
                                source_label = source

                            field_label = field_labels.get(field, field.replace('_', ' ').title())
                            confidence_pct = int(confidence * 100) if isinstance(confidence, float) else confidence
                            field_summary_lines.append(f"  • {field_label}: {emoji} {source_label} ({confidence_pct}% confiança)")

                    field_origin_summary = ""
                    if field_summary_lines:
                        field_origin_summary = f"""
    🔍 **Origem dos campos preenchidos automaticamente** ({auto_filled_count} campos):
    {chr(10).join(field_summary_lines)}

    """
                        job_draft['field_origin_summary'] = field_origin_summary
                        suggestions_data['field_origins'] = field_origins
                        suggestions_data['auto_filled_count'] = auto_filled_count

                    lia_message = f"""Excelente! Chegamos à **Revisão Final**! 🎉

    {status_message}
    {field_origin_summary}
    ---

    📋 **RESUMO DA VAGA**

    {one_page_summary}

    ---

    📝 **DESCRIÇÃO GERADA (Preview)**

    {jd_preview}

    ---

    {warnings_text}

    **✅ Checklist de Qualidade:**
    ✓ Informações básicas conferidas
    ✓ Competências e pesos verificados
    ✓ Perguntas de triagem WSI definidas
    ✓ Descrição gerada automaticamente

    ---

    {"🚀 **Próximo passo:** Clique em **Publicar Vaga** para escolher as plataformas e ativar o recrutamento!" if completeness_result.can_publish else "⚠️ **Complete os campos obrigatórios** listados acima antes de publicar."}

    💡 *Após publicar, vou começar a buscar candidatos compatíveis automaticamente!*"""

                elif current_stage == 7:
                    lia_message = """**Plataformas de Publicação**

    Escolha onde publicar sua vaga:

    🔗 **LinkedIn** - Maior rede profissional
    📋 **Indeed** - Alto volume de candidatos
    🌐 **Página de Carreiras** - Candidatos qualificados
    📱 **WhatsApp** - Divulgação rápida

    Selecione as plataformas desejadas e clique em "Publicar Vaga"."""

                elif current_stage == 8:
                    lia_message = """**Busca de Candidatos**

    Agora que a vaga está ativa, vou buscar candidatos compatíveis.

    🔍 Buscando na base de talentos...
    🔍 Analisando perfis do LinkedIn...
    🔍 Verificando candidatos similares...

    Em breve você verá os primeiros candidatos sugeridos."""

                elif current_stage == 9:
                    lia_message = """**Calibração de Candidatos**

    Vou apresentar alguns candidatos para você avaliar.
    Sua avaliação ajuda a LIA a entender melhor o perfil ideal.

    Para cada candidato:
    • ✅ Aprovar - Perfil adequado
    • ❌ Reprovar - Não adequado
    • 💬 Comentar - Adicionar observações

    Vamos começar?"""

                elif current_stage == 10:
                    lia_message = """**Busca Ativa**

    Com base na calibração, vou intensificar a busca por candidatos ideais.

    🎯 Critérios refinados aplicados
    📧 Outreach automatizado ativo
    📊 Monitorando respostas

    Você será notificado quando houver novos candidatos compatíveis."""
                    is_complete = True

                else:
                    lia_message = f"Continuando com a etapa: {stage_info['panel']}"

            # Sync job_draft dict back to database model with history tracking
            job_draft_model.current_step = stage_info["name"]

            # Define field mappings: (draft_key_options, model_attr)
            field_mappings = [
                (["cargo", "job_title"], "job_title"),
                (["gestorArea", "department"], "department"),
                (["senioridadeIdiomas", "seniority"], "seniority"),
                (["localizacao", "location"], "location"),
                (["modeloTrabalho", "work_model"], "work_model"),
                (["is_affirmative"], "is_affirmative"),
                (["affirmative_criteria_primary"], "affirmative_criteria_primary"),
                (["affirmative_criteria_secondary"], "affirmative_criteria_secondary"),
                (["manager"], "manager"),
                (["manager_email"], "manager_email"),
            ]

            # Track changes and update model with history
            for draft_keys, model_attr in field_mappings:
                new_value = None
                for key in draft_keys:
                    if job_draft.get(key):
                        new_value = job_draft.get(key)
                        break

                if new_value:
                    old_value = getattr(job_draft_model, model_attr, None)
                    if old_value != new_value:
                        # Record history for the change
                        field_origin = field_origins.get(model_attr, {})
                        confidence = field_origin.get('confidence', 0.5)
                        source = field_origin.get('source', 'detected')

                        await record_field_history(
                            db=db,
                            job_draft_model=job_draft_model,
                            field_name=model_attr,
                            old_value=old_value,
                            new_value=new_value,
                            change_type=ChangeType.INFERRED,
                            recruiter_id=recruiter_id,
                            confidence=confidence,
                            source=source
                        )

                        # Update the model
                        setattr(job_draft_model, model_attr, new_value)

            # Handle skills with history tracking
            detected_skills = job_draft.get("competenciasTecnicas") or job_draft.get("detected_skills") or []
            if detected_skills:
                old_skills = job_draft_model.skills or []
                if old_skills != detected_skills:
                    await record_field_history(
                        db=db,
                        job_draft_model=job_draft_model,
                        field_name="skills",
                        old_value=old_skills,
                        new_value=detected_skills,
                        change_type=ChangeType.INFERRED,
                        recruiter_id=recruiter_id,
                        source="detected"
                    )
                    job_draft_model.skills = detected_skills

            # Handle salary with history tracking
            if job_draft.get("salary_min"):
                old_salary_min = job_draft_model.salary_min
                new_salary_min = job_draft.get("salary_min")
                if old_salary_min != new_salary_min:
                    await record_field_history(
                        db=db,
                        job_draft_model=job_draft_model,
                        field_name="salary_min",
                        old_value=old_salary_min,
                        new_value=new_salary_min,
                        change_type=ChangeType.INFERRED,
                        recruiter_id=recruiter_id,
                        source="detected"
                    )
                    job_draft_model.salary_min = new_salary_min

            if job_draft.get("salary_max"):
                old_salary_max = job_draft_model.salary_max
                new_salary_max = job_draft.get("salary_max")
                if old_salary_max != new_salary_max:
                    await record_field_history(
                        db=db,
                        job_draft_model=job_draft_model,
                        field_name="salary_max",
                        old_value=old_salary_max,
                        new_value=new_salary_max,
                        change_type=ChangeType.INFERRED,
                        recruiter_id=recruiter_id,
                        source="detected"
                    )
                    job_draft_model.salary_max = new_salary_max

            # Record history for company defaults applied
            for field, default_info in company_default_fields.items():
                await record_field_history(
                    db=db,
                    job_draft_model=job_draft_model,
                    field_name=field,
                    old_value=None,
                    new_value=default_info['value'],
                    change_type=ChangeType.INFERRED,
                    recruiter_id=recruiter_id,
                    confidence=default_info.get('confidence', 0.5),
                    source="company_default",
                    reason="Applied from company profile defaults"
                )

            # Update confidence map with simplified field -> confidence mapping
            current_confidence_map = dict(job_draft_model.confidence_map) if job_draft_model.confidence_map else {}
            # Generate simplified confidence_map from field_origins
            confidence_map = {field: origin.get('confidence', 0.5) for field, origin in field_origins.items()}
            current_confidence_map.update(confidence_map)
            job_draft_model.confidence_map = current_confidence_map

            # Track inferred fields and their sources
            current_inferred = dict(job_draft_model.inferred_fields) if job_draft_model.inferred_fields else {}
            current_defaults = dict(job_draft_model.company_defaults_used) if job_draft_model.company_defaults_used else {}
            current_confirmed = dict(job_draft_model.confirmed_fields) if job_draft_model.confirmed_fields else {}

            for field, origin in field_origins.items():
                source = origin.get('source', '')
                if source == 'detected':
                    current_inferred[field] = {
                        "source": source,
                        "confidence": origin.get('confidence', 0.5),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                elif source == 'company_default':
                    current_defaults[field] = {
                        "source": source,
                        "applied_at": datetime.utcnow().isoformat()
                    }

            job_draft_model.inferred_fields = current_inferred
            job_draft_model.company_defaults_used = current_defaults

            # Handle confirmed_fields from user context
            if request.context:
                confirmed_fields_from_context = request.context.get('confirmed_fields', [])
                for field in confirmed_fields_from_context:
                    if field not in current_confirmed:
                        current_confirmed[field] = {
                            "confirmed_at": datetime.utcnow().isoformat(),
                            "confirmed_by": recruiter_id
                        }
                        # Remove from inferred_fields when confirmed
                        if field in current_inferred:
                            del current_inferred[field]

                        # Record confirmation in history
                        field_value = getattr(job_draft_model, field, None) if hasattr(job_draft_model, field) else job_draft.get(field)
                        await record_field_history(
                            db=db,
                            job_draft_model=job_draft_model,
                            field_name=field,
                            old_value=field_value,
                            new_value=field_value,
                            change_type=ChangeType.CONFIRMED,
                            recruiter_id=recruiter_id,
                            source="user_confirmation"
                        )

                job_draft_model.confirmed_fields = current_confirmed
                job_draft_model.inferred_fields = current_inferred

            # Store extra data that doesn't map to columns
            known_keys = {"job_id", "created_at", "company_id", "job_title", "department", "seniority", 
                          "location", "work_model", "salary_min", "salary_max", "detected_skills", "benefits",
                          "cargo", "gestorArea", "senioridadeIdiomas", "localizacao", "modeloTrabalho",
                          "competenciasTecnicas", "competenciasComportamentais"}
            extra_data = {k: v for k, v in job_draft.items() if k not in known_keys and v is not None}

            if extra_data:
                inferred_with_extra = dict(job_draft_model.inferred_fields) if job_draft_model.inferred_fields else {}
                inferred_with_extra["_extra_data"] = extra_data
                job_draft_model.inferred_fields = inferred_with_extra

            # Commit all changes
            await db.commit()
            logger.info(f"Saved JobDraft to database: id={job_draft_model.id}, conversation_id={conversation_id}")

            # Track feedback for learning
            if request.context:
                # Check if user accepted/rejected any suggestions
                accepted_fields = request.context.get('accepted_suggestions', [])
                rejected_fields = request.context.get('rejected_suggestions', [])
                edited_fields = request.context.get('edited_fields', {})

                for field in accepted_fields:
                    try:
                        await feedback_learning_service.record_feedback(
                            db=db,
                            company_id=company_id,
                            field_name=field,
                            suggested_value=job_draft.get(field),
                            accepted=True,
                            context={
                                'job_title': job_draft.get('job_title'),
                                'department': job_draft.get('department'),
                                'seniority': job_draft.get('seniority')
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to record positive feedback for {field}: {e}")

                for field in rejected_fields:
                    try:
                        await feedback_learning_service.record_feedback(
                            db=db,
                            company_id=company_id,
                            field_name=field,
                            suggested_value=job_draft.get(field),
                            accepted=False,
                            context={
                                'job_title': job_draft.get('job_title'),
                                'department': job_draft.get('department'),
                                'seniority': job_draft.get('seniority')
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to record negative feedback for {field}: {e}")

                # Track manual edits as implicit rejection of original suggestion
                for field, new_value in edited_fields.items():
                    original_value = field_origins.get(field, {}).get('original_text')
                    if original_value and original_value != new_value:
                        try:
                            await feedback_learning_service.record_feedback(
                                db=db,
                                company_id=company_id,
                                field_name=field,
                                suggested_value=original_value,
                                accepted=False,
                                actual_value=new_value,
                                context={
                                    'job_title': job_draft.get('job_title'),
                                    'department': job_draft.get('department'),
                                    'seniority': job_draft.get('seniority')
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Failed to record edit feedback for {field}: {e}")

            # Check field completeness for the current stage
            completeness_service = ConfigCompletenessService()

            # Define required fields by stage
            stage_fields = {
                1: ['job_title'],
                2: ['job_title', 'department', 'location', 'work_model', 'employment_type'],
                3: ['technical_skills', 'behavioral_skills'],
                4: ['salary_min', 'salary_max'],
                5: [],
                6: ['job_title', 'department', 'technical_skills'],
                7: [],
                8: [],
                9: [],
                10: []
            }

            required_fields = stage_fields.get(current_stage, [])
            missing_critical = []
            missing_important = []

            # Check which required fields are missing
            critical_fields = ['job_title', 'department', 'technical_skills']

            for field in required_fields:
                # Check both normalized and detected field names
                field_value = job_draft.get(field)
                # Special handling for job_title - also check 'cargo' (Portuguese field name)
                if field == 'job_title' and not field_value:
                    field_value = job_draft.get('cargo') or detected_criteria.get('cargo') if detected_criteria else None
                # Special handling for department - also check 'gestorArea'
                if field == 'department' and not field_value:
                    field_value = job_draft.get('gestorArea') or (detected_criteria.get('gestorArea') if detected_criteria else None)

                if not field_value:
                    if field in critical_fields:
                        missing_critical.append(field)
                    else:
                        missing_important.append(field)

            # Generate completeness suggestions
            completeness_suggestions = {}
            if missing_critical or missing_important:
                try:
                    suggestions_result = await completeness_service.get_suggestions(
                        db=db,
                        company_id=company_id,
                        missing_fields=missing_critical + missing_important,
                        context={
                            'job_title': job_draft.get('job_title'),
                            'department': job_draft.get('department'),
                            'seniority': job_draft.get('seniority')
                        }
                    )
                    completeness_suggestions = suggestions_result
                except Exception as e:
                    logger.warning(f"Failed to get completeness suggestions: {e}")

            # Add completeness info to response
            suggestions_data['completeness'] = {
                'missing_critical': missing_critical,
                'missing_important': missing_important,
                'suggestions': completeness_suggestions,
                'can_advance': len(missing_critical) == 0
            }

            # Append warning to LIA message if critical fields missing
            if missing_critical:
                field_labels = {
                    'job_title': 'Cargo',
                    'department': 'Departamento',
                    'location': 'Localização',
                    'work_model': 'Modelo de Trabalho',
                    'employment_type': 'Tipo de Contratação',
                    'technical_skills': 'Skills Técnicas',
                    'behavioral_skills': 'Competências Comportamentais',
                    'salary_min': 'Salário Mínimo',
                    'salary_max': 'Salário Máximo'
                }
                missing_labels = [field_labels.get(f, f) for f in missing_critical]
                lia_message += f"\n\n⚠️ **Campos obrigatórios faltando:** {', '.join(missing_labels)}"
                lia_message += "\nPreencha esses campos para poder avançar."

                # Block advancement if critical fields are missing
                if next_stage and next_stage > current_stage:
                    next_stage = current_stage

            stage_skipped = None
            skip_reason = None
            auto_filled_data = None
            stages_to_skip = []

            # Ensure affirmative action fields are included in detected_criteria
            if detected_criteria:
                detected_criteria["is_affirmative"] = job_draft.get("is_affirmative")
                detected_criteria["affirmative_criteria_primary"] = job_draft.get("affirmative_criteria_primary")
                detected_criteria["affirmative_criteria_secondary"] = job_draft.get("affirmative_criteria_secondary")
                detected_criteria["job_title"] = job_draft.get("job_title") or detected_criteria.get("cargo")
                detected_criteria["seniority"] = job_draft.get("seniority") or detected_criteria.get("senioridadeIdiomas")
                detected_criteria["work_model"] = job_draft.get("work_model") or detected_criteria.get("modeloTrabalho")
                detected_criteria["location"] = job_draft.get("location") or detected_criteria.get("localizacao")
                detected_criteria["salary_min"] = job_draft.get("salary_min") or detected_criteria.get("salary_min") or detected_criteria.get("salario", {}).get("min") if isinstance(detected_criteria.get("salario"), dict) else job_draft.get("salary_min")
                detected_criteria["salary_max"] = job_draft.get("salary_max") or detected_criteria.get("salary_max") or detected_criteria.get("salario", {}).get("max") if isinstance(detected_criteria.get("salario"), dict) else job_draft.get("salary_max")
                detected_criteria["department"] = job_draft.get("department") or detected_criteria.get("gestorArea")
                detected_criteria["manager"] = job_draft.get("manager")
                detected_criteria["manager_email"] = job_draft.get("manager_email")

            if next_stage and next_stage > current_stage:
                from app.domains.job_management.services.job_stage_config import get_stage_config

                cargo_data = (detected_criteria or {}).get("cargo")
                role = job_draft.get("job_title") or (cargo_data.get("value") if isinstance(cargo_data, dict) else cargo_data)
                seniority_data = (detected_criteria or {}).get("senioridade")
                seniority = job_draft.get("seniority") or (seniority_data.get("value") if isinstance(seniority_data, dict) else seniority_data)

                try:
                    should_skip, skip_msg, auto_data = await learning_hub_service.should_skip_stage_with_learning(
                        db=db,
                        company_id=company_id,
                        stage_number=next_stage,
                        detected_criteria=detected_criteria or job_draft,
                        role=role,
                        seniority=seniority
                    )

                    if should_skip:
                        stage_skipped = True
                        skip_reason = skip_msg
                        auto_filled_data = auto_data
                        stages_to_skip.append(next_stage)

                        stage_config = get_stage_config(next_stage)
                        if stage_config.get("use_skills_deduplication"):
                            already_selected = []
                            skills_data = (detected_criteria or {}).get("competencias_tecnicas", {})
                            if isinstance(skills_data, dict) and skills_data.get("value"):
                                already_selected = skills_data["value"]
                            elif isinstance(skills_data, list):
                                already_selected = skills_data

                            deduplicated_skills = await learning_hub_service.get_skills_without_duplicates(
                                db=db,
                                company_id=company_id,
                                role=role,
                                exclude_already_selected=already_selected
                            )
                            suggestions_data["deduplicated_skills"] = deduplicated_skills

                        lia_message += f"\n\n✅ **{skip_msg}**"

                        next_after_skip = next_stage + 1 if next_stage < 10 else None
                        if next_after_skip:
                            should_skip_next, _, _ = await learning_hub_service.should_skip_stage_with_learning(
                                db=db,
                                company_id=company_id,
                                stage_number=next_after_skip,
                                detected_criteria=detected_criteria or job_draft,
                                role=role,
                                seniority=seniority
                            )
                            if should_skip_next:
                                stages_to_skip.append(next_after_skip)
                                next_stage = next_after_skip + 1 if next_after_skip < 10 else None
                            else:
                                next_stage = next_after_skip

                except Exception as e:
                    logger.warning(f"Error evaluating stage skip: {e}")

            return WizardStepResponse(
                conversation_id=conversation_id,
                current_stage=current_stage,
                next_stage=next_stage,
                stage_name=stage_info["name"],
                lia_message=lia_message,
                detected_criteria=detected_criteria or job_draft,
                is_complete=is_complete,
                created_job=created_job,
                intent_detected=classification.intent_type.value,
                benchmarks=benchmarks if benchmarks else None,
                suggestions=suggestions_data if suggestions_data else None,
                field_origins=field_origins if field_origins else None,
                stage_skipped=stage_skipped,
                skip_reason=skip_reason,
                auto_filled_data=auto_filled_data,
                stages_to_skip=stages_to_skip if stages_to_skip else None
            )

        except Exception as e:
            logger.error(f"Error in wizard step: {e}", exc_info=True)
            return WizardStepResponse(
                conversation_id=conversation_id,
                current_stage=current_stage,
                next_stage=None,
                stage_name=stage_info["name"],
                lia_message=f"Desculpe, ocorreu um erro. Detalhes: {str(e)}",
                detected_criteria=None,
                is_complete=False,
                created_job=None,
                intent_detected="ERROR",
                field_origins=None
            )

wizard_step_service = WizardStepService()
