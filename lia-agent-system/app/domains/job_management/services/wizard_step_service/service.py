"""
WizardStepService facade — delegates to stage-specific handlers.
"""

# CANONICAL-EXEMPT: legacy HITL resume — wizard de criacao de vaga canonical
# vive em app/domains/job_creation/ (WizardSessionService + JobCreationGraph).
# Este arquivo permanece DEPRECATED apenas para suportar HITL resume em
# agent_chat_ws.py:558-561 durante a Fase 1 da migracao planejada em
# .planning/adrs/ADR-CANONICAL-001-wizard-domain.md.

import logging
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.wizard_step_repository import WizardStepRepository

from lia_models.job_draft import ChangeType, JobDraft, JobDraftStatus
from app.shared.services.confidence_policy_service import ConfidencePolicyService
from app.shared.services.config_completeness_service import ConfigCompletenessService
from app.shared.services.context_aggregator_service import context_aggregator
from app.shared.services.enhanced_intent_classifier import EnhancedIntentType, enhanced_intent_classifier
from app.shared.services.intent_classifier import IntentType, intent_classifier_service
from app.shared.services.knowledge_base_service import knowledge_base
from app.shared.services.learning_hub_service import learning_hub_service
from app.shared.services.organization_catalog_service import OrganizationCatalogService

from ._shared import (
    WIZARD_STAGES,
    USE_ENHANCED_CLASSIFIER,
    LLMService,
    vacancy_search_service,
    feedback_learning_service,
    record_field_history,
    QuestionType,
    detect_question_type,
    handle_salary_question,
    handle_skills_question,
    handle_time_to_fill_question,
    handle_process_question,
    handle_correction,
    get_stage_benchmarks,
    get_historical_job_patterns,
)
from .stage_description import handle_description
from .stage_basic_info import handle_basic_info
from .stage_competencies import handle_competencies
from .stage_salary import handle_salary
from .stage_wsi import handle_wsi_questions
from .stage_review import handle_review
from .stage_publication import (
    handle_pre_publish,
    handle_candidate_search,
    handle_calibration,
    handle_active_search,
)

logger = logging.getLogger(__name__)


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
        from app.domains.job_management.schemas.wizard_schemas import WizardStepResponse
        from lia_models.company import CompanyProfile, Department
        from lia_models.company_benefit import CompanyBenefit

        conversation_id = request.conversation_id or str(uuid4())
        current_stage = request.stage
        stage_info = (
            WIZARD_STAGES[current_stage - 1]
            if current_stage <= len(WIZARD_STAGES)
            else WIZARD_STAGES[-1]
        )

        try:
            conv_uuid = UUID(conversation_id)
        except (ValueError, TypeError):
            conv_uuid = uuid4()
            conversation_id = str(conv_uuid)

        job_draft_model = await WizardStepRepository(db).get_draft_by_conversation(conv_uuid)

        if not job_draft_model:
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
                languages=[],
            )
            db.add(job_draft_model)
            await db.flush()
            logger.info(
                f"Created new JobDraft with conversation_id={conversation_id}, recruiter_id={recruiter_id}"
            )

        job_draft = {
            "job_id": str(job_draft_model.id),
            "created_at": (
                job_draft_model.created_at.isoformat()
                if job_draft_model.created_at
                else datetime.utcnow().isoformat()
            ),
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

            if USE_ENHANCED_CLASSIFIER:
                try:
                    aggregated_context = await context_aggregator.get_full_context(
                        company_id=company_id,
                        session_id=conversation_id,
                        db=db,
                        stage=current_stage,
                        filled_fields=job_draft,
                    )

                    enhanced_classification = await enhanced_intent_classifier.classify(
                        user_input=request.user_input,
                        stage=current_stage,
                        filled_fields=job_draft,
                        context={
                            "company": aggregated_context.company.name if aggregated_context else None
                        },
                    )

                    entities_dict = enhanced_classification.entities.to_dict()
                    for key, value in entities_dict.items():
                        if value is not None and key not in ["raw_entities", "filtro_busca"]:
                            if key == "cargo":
                                job_draft["job_title"] = value
                            elif key == "area":
                                job_draft["department"] = value
                            elif key == "senioridade":
                                job_draft["seniority"] = value
                            elif key == "salario_min":
                                job_draft["salary_min"] = value
                            elif key == "salario_max":
                                job_draft["salary_max"] = value
                            elif key == "modelo_trabalho":
                                job_draft["work_model"] = value
                            elif key == "localizacao":
                                job_draft["location"] = value
                            elif key == "skills_tecnicas":
                                job_draft["detected_skills"] = value
                            elif key == "beneficios":
                                job_draft["benefits"] = value
                            elif key == "idiomas":
                                job_draft["languages"] = value
                            elif key == "is_afirmativa":
                                job_draft["is_affirmative"] = value
                            elif key == "criterio_afirmativo_primario":
                                job_draft["affirmative_criteria_primary"] = value
                            elif key == "criterio_afirmativo_secundario":
                                job_draft["affirmative_criteria_secondary"] = value
                            elif key == "gestor":
                                job_draft["manager"] = value
                            elif key == "gestor_email":
                                job_draft["manager_email"] = value
                            else:
                                job_draft[key] = value

                    if enhanced_classification.intent_type == EnhancedIntentType.QUESTION:
                        knowledge_base.search(request.user_input)

                    logger.info(
                        f"Enhanced classification: {enhanced_classification.intent_type} "
                        f"(confidence: {enhanced_classification.confidence})"
                    )

                except Exception as e:
                    logger.warning(f"Enhanced classifier failed, falling back: {e}")
                    enhanced_classification = None

            classification = await intent_classifier_service.classify(
                user_input=request.user_input,
                stage_context=stage_context,
                use_llm=True,
            )

            if not enhanced_classification:
                for key, value in classification.extracted_entities.items():
                    if value is not None:
                        job_draft[key] = value

            logger.info(
                f"Intent classified: {classification.intent_type} (confidence: {classification.confidence})"
            )

            org_catalog = OrganizationCatalogService()
            confidence_service = ConfidencePolicyService()
            field_origins = {}

            if classification.extracted_entities:
                entities = classification.extracted_entities

                if entities.get('job_title'):
                    matched_role = org_catalog.get_role_by_name(entities['job_title'])
                    if matched_role:
                        job_title_result = confidence_service.calculate_field_confidence(
                            field="job_title",
                            value=entities['job_title'],
                            sources=[
                                {"type": "text_extraction", "value": entities['job_title']},
                                {"type": "similar_jobs", "value": matched_role.get('nome')},
                            ],
                        )
                        field_origins['job_title'] = {
                            'source': 'detected',
                            'confidence': job_title_result.confidence,
                            'action': job_title_result.action.value,
                            'catalog_match': matched_role.get('nome'),
                        }
                        role_skills = org_catalog.suggest_skills_for_role(entities['job_title'])
                        if role_skills and (role_skills.get('technical') or role_skills.get('behavioral')):
                            job_draft['suggested_skills'] = role_skills
                    else:
                        job_title_result = confidence_service.calculate_field_confidence(
                            field="job_title",
                            value=entities['job_title'],
                            sources=[{"type": "text_extraction", "value": entities['job_title']}],
                        )
                        field_origins['job_title'] = {
                            'source': 'detected',
                            'confidence': job_title_result.confidence,
                            'action': job_title_result.action.value,
                            'catalog_match': None,
                        }

                if entities.get('technical_skills'):
                    validated_skills = []
                    for skill in entities['technical_skills']:
                        search_results = org_catalog.search_skills(skill)
                        catalog_skill = None
                        if search_results.get('technical'):
                            catalog_skill = search_results['technical'][0]

                        if catalog_skill:
                            validated_skills.append({
                                'name': catalog_skill.get('nome', skill),
                                'category': catalog_skill.get('categoria'),
                                'validated': True,
                            })
                            skill_result = confidence_service.calculate_field_confidence(
                                field=f'skill_{skill}',
                                value=skill,
                                sources=[
                                    {"type": "text_extraction", "value": skill},
                                    {"type": "similar_jobs", "value": catalog_skill.get('nome', skill)},
                                ],
                            )
                            field_origins[f'skill_{skill}'] = {
                                'source': 'detected',
                                'confidence': skill_result.confidence,
                                'action': skill_result.action.value,
                            }
                        else:
                            validated_skills.append({'name': skill, 'validated': False})
                            skill_result = confidence_service.calculate_field_confidence(
                                field=f'skill_{skill}',
                                value=skill,
                                sources=[{"type": "text_extraction", "value": skill}],
                            )
                            field_origins[f'skill_{skill}'] = {
                                'source': 'detected',
                                'confidence': skill_result.confidence,
                                'action': skill_result.action.value,
                            }
                    job_draft['validated_technical_skills'] = validated_skills

                for field in ['seniority', 'department', 'location', 'work_model', 'salary_min', 'salary_max']:
                    if entities.get(field):
                        field_result = confidence_service.calculate_field_confidence(
                            field=field,
                            value=entities.get(field),
                            sources=[{"type": "text_extraction", "value": entities.get(field)}],
                        )
                        field_origins[field] = {
                            'source': 'detected',
                            'confidence': field_result.confidence,
                            'action': field_result.action.value,
                        }

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

            company_default_fields = {}

            if company_profile and company_profile.additional_data:
                additional_data = company_profile.additional_data

                if not job_draft.get('work_model') and not job_draft.get('modeloTrabalho'):
                    default_work_model = additional_data.get('work_model')
                    if default_work_model:
                        job_draft['work_model'] = default_work_model
                        work_model_result = confidence_service.calculate_field_confidence(
                            field="work_model",
                            value=default_work_model,
                            sources=[{"type": "company_default", "value": default_work_model}],
                        )
                        field_origins['work_model'] = {
                            'source': 'company_default',
                            'confidence': work_model_result.confidence,
                            'action': work_model_result.action.value,
                        }
                        company_default_fields['work_model'] = {
                            'value': default_work_model,
                            'confidence': work_model_result.confidence,
                        }

                if not job_draft.get('location') and not job_draft.get('localizacao'):
                    default_location = company_profile.headquarters_city
                    if default_location:
                        job_draft['location'] = default_location
                        location_result = confidence_service.calculate_field_confidence(
                            field="location",
                            value=default_location,
                            sources=[{"type": "company_default", "value": default_location}],
                        )
                        field_origins['location'] = {
                            'source': 'company_default',
                            'confidence': location_result.confidence,
                            'action': location_result.action.value,
                        }
                        company_default_fields['location'] = {
                            'value': default_location,
                            'confidence': location_result.confidence,
                        }

            historical_patterns = {}
            if not job_draft.get('work_model') and not job_draft.get('modeloTrabalho'):
                try:
                    historical_patterns = await get_historical_job_patterns(db, company_id)
                    if 'work_model' in historical_patterns:
                        pattern = historical_patterns['work_model']
                        job_draft['work_model'] = pattern['value']
                        job_draft['work_model_suggested'] = True
                        job_draft['work_model_suggestion_context'] = (
                            f"Baseado em {pattern['percentage']}% das suas {pattern['count']} vagas anteriores"
                        )
                        field_origins['work_model'] = {
                            'source': 'historical_pattern',
                            'confidence': min(0.85, 0.5 + (pattern['percentage'] / 200)),
                            'action': 'suggest',
                            'context': pattern,
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch historical patterns: {e}")

            if not job_draft.get('employment_type') and not job_draft.get('tipoContrato'):
                try:
                    if not historical_patterns:
                        historical_patterns = await get_historical_job_patterns(db, company_id)
                    if 'employment_type' in historical_patterns:
                        pattern = historical_patterns['employment_type']
                        job_draft['employment_type'] = pattern['value']
                        job_draft['employment_type_suggested'] = True
                        job_draft['employment_type_suggestion_context'] = (
                            f"Baseado em {pattern['percentage']}% das suas vagas anteriores"
                        )
                        field_origins['employment_type'] = {
                            'source': 'historical_pattern',
                            'confidence': min(0.85, 0.5 + (pattern['percentage'] / 200)),
                            'action': 'suggest',
                            'context': pattern,
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch employment_type pattern: {e}")

            if not job_draft.get('location') and not job_draft.get('localizacao'):
                try:
                    if not historical_patterns:
                        historical_patterns = await get_historical_job_patterns(db, company_id)
                    if 'location' in historical_patterns:
                        pattern = historical_patterns['location']
                        job_draft['location'] = pattern['value']
                        job_draft['location_suggested'] = True
                        job_draft['location_suggestion_context'] = (
                            f"Baseado em {pattern['percentage']}% das suas vagas anteriores"
                        )
                        field_origins['location'] = {
                            'source': 'historical_pattern',
                            'confidence': min(0.85, 0.5 + (pattern['percentage'] / 200)),
                            'action': 'suggest',
                            'context': pattern,
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch location pattern: {e}")

            # Build company context string
            company_context = self._build_company_context(
                company_profile, company_departments, company_benefits
            )

            detected_criteria = None
            lia_message = ""
            next_stage = current_stage + 1 if current_stage < 10 else None
            is_complete = current_stage >= 10
            created_job = None
            benchmarks = {}
            suggestions_data = {}

            # --- Intent routing ---
            if classification.intent_type == IntentType.QUESTION:
                llm_service = LLMService()
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
                    import json as _json
                    prompt = (
                        f"Responda brevemente à pergunta do recrutador sobre a vaga:\n\n"
                        f"Pergunta: {request.user_input}\n"
                        f"Contexto da vaga: {_json.dumps(job_draft, default=str)}\n\n"
                        f"Responda de forma útil e concisa."
                    )
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
                    panel = (
                        WIZARD_STAGES[current_stage]['panel']
                        if current_stage < 10
                        else 'Finalização'
                    )
                    lia_message = f"Ok, avançando para a próxima etapa: **{panel}**"
                elif any(kw in text_lower for kw in ["voltar", "anterior", "back"]):
                    next_stage = current_stage - 1 if current_stage > 1 else 1
                    lia_message = f"Voltando para a etapa anterior: **{WIZARD_STAGES[next_stage - 1]['panel']}**"
                else:
                    lia_message = (
                        "Entendi que você quer mudar de assunto. Posso ajudar com:\n"
                        "• Avançar para a próxima etapa\n"
                        "• Voltar para a etapa anterior\n"
                        "• Responder dúvidas sobre salário, skills, ou processo\n\n"
                        "O que prefere?"
                    )
                    next_stage = current_stage

            elif classification.intent_type == IntentType.REUSE_VACANCY:
                lia_message, next_stage, suggestions_data = await self._handle_reuse_vacancy(
                    request, company_id, db, current_stage, suggestions_data
                )

            else:
                # Main stage processing
                benchmarks = await get_stage_benchmarks(db, company_id, job_draft, current_stage)

                if current_stage == 1:
                    lia_message, detected_criteria, suggestions_data = await handle_description(
                        request=request,
                        job_draft=job_draft,
                        company_context=company_context,
                        company_departments=company_departments,
                        field_origins=field_origins,
                        confidence_service=confidence_service,
                        suggestions_data=suggestions_data,
                    )

                elif current_stage == 2:
                    lia_message, suggestions_data = await handle_basic_info(
                        job_draft=job_draft,
                        company_departments=company_departments,
                        suggestions_data=suggestions_data,
                    )

                elif current_stage == 3:
                    lia_message, suggestions_data = await handle_competencies(
                        job_draft=job_draft,
                        benchmarks=benchmarks,
                        suggestions_data=suggestions_data,
                    )

                elif current_stage == 4:
                    lia_message, suggestions_data, field_origins = await handle_salary(
                        db=db,
                        company_id=company_id,
                        job_draft=job_draft,
                        company_benefits=company_benefits,
                        benchmarks=benchmarks,
                        field_origins=field_origins,
                        suggestions_data=suggestions_data,
                    )

                elif current_stage == 5:
                    lia_message, suggestions_data = await handle_wsi_questions(
                        job_draft=job_draft,
                        suggestions_data=suggestions_data,
                    )

                elif current_stage == 6:
                    completeness_service = ConfigCompletenessService()
                    lia_message, suggestions_data = await handle_review(
                        job_draft=job_draft,
                        company_profile=company_profile,
                        company_benefits=company_benefits,
                        field_origins=field_origins,
                        suggestions_data=suggestions_data,
                        completeness_service=completeness_service,
                    )

                elif current_stage == 7:
                    lia_message = handle_pre_publish()

                elif current_stage == 8:
                    lia_message = handle_candidate_search()

                elif current_stage == 9:
                    lia_message = handle_calibration()

                elif current_stage == 10:
                    lia_message = handle_active_search()
                    is_complete = True

                else:
                    lia_message = f"Continuando com a etapa: {stage_info['panel']}"

            # --- Persist draft to DB ---
            await self._persist_draft(
                db=db,
                job_draft_model=job_draft_model,
                job_draft=job_draft,
                stage_info=stage_info,
                field_origins=field_origins,
                company_default_fields=company_default_fields,
                recruiter_id=recruiter_id,
                request=request,
            )

            # --- Track feedback ---
            await self._track_feedback(
                db=db, company_id=company_id, job_draft=job_draft, field_origins=field_origins, request=request
            )

            # --- Completeness check ---
            lia_message, next_stage, suggestions_data = self._check_stage_completeness(
                job_draft=job_draft,
                detected_criteria=detected_criteria,
                current_stage=current_stage,
                next_stage=next_stage,
                lia_message=lia_message,
                suggestions_data=suggestions_data,
            )

            # --- Stage skip logic ---
            stage_skipped = None
            skip_reason = None
            auto_filled_data = None
            stages_to_skip = []

            if detected_criteria:
                detected_criteria["is_affirmative"] = job_draft.get("is_affirmative")
                detected_criteria["affirmative_criteria_primary"] = job_draft.get("affirmative_criteria_primary")
                detected_criteria["affirmative_criteria_secondary"] = job_draft.get("affirmative_criteria_secondary")
                detected_criteria["job_title"] = job_draft.get("job_title") or detected_criteria.get("cargo")
                detected_criteria["seniority"] = job_draft.get("seniority") or detected_criteria.get("senioridadeIdiomas")
                detected_criteria["work_model"] = job_draft.get("work_model") or detected_criteria.get("modeloTrabalho")
                detected_criteria["location"] = job_draft.get("location") or detected_criteria.get("localizacao")
                salario = detected_criteria.get("salario")
                detected_criteria["salary_min"] = (
                    job_draft.get("salary_min")
                    or detected_criteria.get("salary_min")
                    or (salario.get("min") if isinstance(salario, dict) else job_draft.get("salary_min"))
                )
                detected_criteria["salary_max"] = (
                    job_draft.get("salary_max")
                    or detected_criteria.get("salary_max")
                    or (salario.get("max") if isinstance(salario, dict) else job_draft.get("salary_max"))
                )
                detected_criteria["department"] = job_draft.get("department") or detected_criteria.get("gestorArea")
                detected_criteria["manager"] = job_draft.get("manager")
                detected_criteria["manager_email"] = job_draft.get("manager_email")

            if next_stage and next_stage > current_stage:
                from app.domains.job_management.services.job_stage_config import get_stage_config

                cargo_data = (detected_criteria or {}).get("cargo")
                role = job_draft.get("job_title") or (
                    cargo_data.get("value") if isinstance(cargo_data, dict) else cargo_data
                )
                seniority_data = (detected_criteria or {}).get("senioridade")
                seniority = job_draft.get("seniority") or (
                    seniority_data.get("value") if isinstance(seniority_data, dict) else seniority_data
                )

                try:
                    should_skip, skip_msg, auto_data = await learning_hub_service.should_skip_stage_with_learning(
                        db=db,
                        company_id=company_id,
                        stage_number=next_stage,
                        detected_criteria=detected_criteria or job_draft,
                        role=role,
                        seniority=seniority,
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
                                exclude_already_selected=already_selected,
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
                                seniority=seniority,
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
                stages_to_skip=stages_to_skip if stages_to_skip else None,
            )

        except Exception as e:
            try:
                await db.rollback()
            except Exception:
                pass
            logger.error(f"Error in wizard step: {e}", exc_info=True)
            from app.domains.job_management.schemas.wizard_schemas import WizardStepResponse
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
                field_origins=None,
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_company_context(self, company_profile, company_departments: list, company_benefits: list) -> str:
        """Build a formatted company context string for LLM prompts."""
        if not company_profile:
            return ""

        additional_data = company_profile.additional_data or {}

        tech_stack_lines = "- Não informadas"
        if additional_data.get('tech_stack'):
            tech_stack_items = []
            for cat, techs in list((additional_data.get('tech_stack', {}) or {}).items())[:5]:
                if isinstance(techs, list):
                    tech_stack_items.append(f"- {cat}: {', '.join(techs)}")
            tech_stack_lines = "\n".join(tech_stack_items) if tech_stack_items else "- Não informadas"

        competencies_lines = "- Não definidas"
        if additional_data.get('default_behavioral_competencies'):
            comp_items = []
            for c in (additional_data.get('default_behavioral_competencies', []) or [])[:5]:
                if isinstance(c, dict):
                    comp_items.append(f"- {c.get('competency', '')} ({c.get('weight', '')})")
            competencies_lines = "\n".join(comp_items) if comp_items else "- Não definidas"

        values_str = (
            ', '.join(additional_data.get('values', []))
            if additional_data.get('values')
            else 'Não definidos'
        )
        employment_types_str = ', '.join(additional_data.get('employment_types', ['CLT']))

        context = f"""
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
            dept_info = [
                f"- {d['name']}" + (f" (Gestor: {d['manager']})" if d.get('manager') else "")
                for d in company_departments[:10]
            ]
            context += "\nDEPARTAMENTOS:\n" + "\n".join(dept_info) + "\n"

        if company_benefits:
            benefit_info = [f"- {b['name']} ({b['category']})" for b in company_benefits[:10]]
            context += "\nBENEFÍCIOS:\n" + "\n".join(benefit_info) + "\n"

        return context

    async def _handle_reuse_vacancy(
        self,
        request,
        company_id: str,
        db: AsyncSession,
        current_stage: int,
        suggestions_data: dict,
    ) -> tuple[str, int, dict]:
        """Handle REUSE_VACANCY intent — search and list previous vacancies."""
        criteria = await vacancy_search_service.extract_search_criteria(request.user_input)
        has_minimum = vacancy_search_service.validate_minimum_criteria(criteria)
        text_lower = request.user_input.lower()
        is_list_query = any(
            kw in text_lower for kw in ["ultimas", "últimas", "recentes", "listar", "mostrar", "ver", "quais"]
        )

        if is_list_query and not has_minimum:
            vacancies = await vacancy_search_service.search_vacancies(
                criteria={}, company_id=company_id, db=db, limit=10
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
                lia_message += (
                    "---\n"
                    "🔍 Quer filtrar por algum critério específico (cargo, área, gestor, ano)?\n"
                    "📋 Ou clique em **Usar anterior** para selecionar uma vaga como base."
                )
                suggestions_data['vacancy_search_results'] = [v.model_dump(mode='json') for v in vacancies]
            else:
                lia_message = (
                    "Ainda não encontrei vagas anteriores registradas no sistema.\n\n"
                    "Vamos criar uma nova vaga? Me diga o cargo e os requisitos principais!"
                )

        elif has_minimum:
            vacancies = await vacancy_search_service.search_vacancies(
                criteria=criteria, company_id=company_id, db=db, limit=10
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
                lia_message += (
                    "\n---\n"
                    "Qual vaga você gostaria de usar como base? Digite o número ou clique para selecionar."
                )
                suggestions_data['vacancy_search_results'] = [v.model_dump(mode='json') for v in vacancies]
            else:
                lia_message = (
                    "Não encontrei vagas anteriores com esses critérios.\n\n"
                    "💡 Tente outros termos de busca ou podemos criar uma nova vaga do zero.\n"
                    "O que você prefere?"
                )
        else:
            lia_message = (
                "Entendi que você quer buscar vagas anteriores! 🔍\n\n"
                "Para encontrar a vaga certa, me diga mais detalhes:\n"
                "• Qual era o cargo ou título?\n"
                "• Em qual área/departamento?\n"
                "• De qual período (ex: ano passado, 2024)?\n\n"
                "Ou digite **listar vagas** para ver todas as vagas recentes."
            )

        return lia_message, current_stage, suggestions_data

    async def _persist_draft(
        self,
        db: AsyncSession,
        job_draft_model,
        job_draft: dict,
        stage_info: dict,
        field_origins: dict,
        company_default_fields: dict,
        recruiter_id: str,
        request,
    ) -> None:
        """Sync job_draft dict back to the database model with history tracking."""
        from datetime import datetime

        job_draft_model.current_step = stage_info["name"]

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

        for draft_keys, model_attr in field_mappings:
            new_value = None
            for key in draft_keys:
                if job_draft.get(key):
                    new_value = job_draft.get(key)
                    break

            if new_value:
                old_value = getattr(job_draft_model, model_attr, None)
                if old_value != new_value:
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
                        source=source,
                    )
                    setattr(job_draft_model, model_attr, new_value)

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
                    source="detected",
                )
                job_draft_model.skills = detected_skills

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
                    source="detected",
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
                    source="detected",
                )
                job_draft_model.salary_max = new_salary_max

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
                reason="Applied from company profile defaults",
            )

        current_confidence_map = (
            dict(job_draft_model.confidence_map) if job_draft_model.confidence_map else {}
        )
        confidence_map = {field: origin.get('confidence', 0.5) for field, origin in field_origins.items()}
        current_confidence_map.update(confidence_map)
        job_draft_model.confidence_map = current_confidence_map

        current_inferred = dict(job_draft_model.inferred_fields) if job_draft_model.inferred_fields else {}
        current_defaults = (
            dict(job_draft_model.company_defaults_used) if job_draft_model.company_defaults_used else {}
        )
        current_confirmed = (
            dict(job_draft_model.confirmed_fields) if job_draft_model.confirmed_fields else {}
        )

        for field, origin in field_origins.items():
            source = origin.get('source', '')
            if source == 'detected':
                current_inferred[field] = {
                    "source": source,
                    "confidence": origin.get('confidence', 0.5),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            elif source == 'company_default':
                current_defaults[field] = {
                    "source": source,
                    "applied_at": datetime.utcnow().isoformat(),
                }

        job_draft_model.inferred_fields = current_inferred
        job_draft_model.company_defaults_used = current_defaults

        if request.context:
            confirmed_fields_from_context = request.context.get('confirmed_fields', [])
            for field in confirmed_fields_from_context:
                if field not in current_confirmed:
                    current_confirmed[field] = {
                        "confirmed_at": datetime.utcnow().isoformat(),
                        "confirmed_by": recruiter_id,
                    }
                    if field in current_inferred:
                        del current_inferred[field]

                    field_value = (
                        getattr(job_draft_model, field, None)
                        if hasattr(job_draft_model, field)
                        else job_draft.get(field)
                    )
                    await record_field_history(
                        db=db,
                        job_draft_model=job_draft_model,
                        field_name=field,
                        old_value=field_value,
                        new_value=field_value,
                        change_type=ChangeType.CONFIRMED,
                        recruiter_id=recruiter_id,
                        source="user_confirmation",
                    )

            job_draft_model.confirmed_fields = current_confirmed
            job_draft_model.inferred_fields = current_inferred

        known_keys = {
            "job_id", "created_at", "company_id", "job_title", "department", "seniority",
            "location", "work_model", "salary_min", "salary_max", "detected_skills", "benefits",
            "cargo", "gestorArea", "senioridadeIdiomas", "localizacao", "modeloTrabalho",
            "competenciasTecnicas", "competenciasComportamentais",
        }
        extra_data = {k: v for k, v in job_draft.items() if k not in known_keys and v is not None}

        if extra_data:
            inferred_with_extra = (
                dict(job_draft_model.inferred_fields) if job_draft_model.inferred_fields else {}
            )
            inferred_with_extra["_extra_data"] = extra_data
            job_draft_model.inferred_fields = inferred_with_extra

        await db.commit()
        logger.info(
            f"Saved JobDraft to database: id={job_draft_model.id}, conversation_id={job_draft_model.conversation_id}"
        )

    async def _track_feedback(
        self,
        db: AsyncSession,
        company_id: str,
        job_draft: dict,
        field_origins: dict,
        request,
    ) -> None:
        """Record feedback signals from the current request context."""
        if not request.context:
            return

        accepted_fields = request.context.get('accepted_suggestions', [])
        rejected_fields = request.context.get('rejected_suggestions', [])
        edited_fields = request.context.get('edited_fields', {})
        context_meta = {
            'job_title': job_draft.get('job_title'),
            'department': job_draft.get('department'),
            'seniority': job_draft.get('seniority'),
        }

        for field in accepted_fields:
            try:
                await feedback_learning_service.record_feedback(
                    db=db,
                    company_id=company_id,
                    field_name=field,
                    suggested_value=job_draft.get(field),
                    accepted=True,
                    context=context_meta,
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
                    context=context_meta,
                )
            except Exception as e:
                logger.warning(f"Failed to record negative feedback for {field}: {e}")

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
                        context=context_meta,
                    )
                except Exception as e:
                    logger.warning(f"Failed to record edit feedback for {field}: {e}")

    def _check_stage_completeness(
        self,
        job_draft: dict,
        detected_criteria,
        current_stage: int,
        next_stage,
        lia_message: str,
        suggestions_data: dict,
    ) -> tuple[str, any, dict]:
        """Check required field completeness for the current stage and block if critical fields missing."""
        from app.shared.services.config_completeness_service import ConfigCompletenessService

        completeness_service = ConfigCompletenessService()

        stage_fields = {
            1: ['job_title'],
            2: ['job_title', 'department', 'location', 'work_model', 'employment_type'],
            3: ['technical_skills', 'behavioral_skills'],
            4: ['salary_min', 'salary_max'],
            5: [], 6: [], 7: [], 8: [], 9: [], 10: [],
        }

        required_fields = stage_fields.get(current_stage, [])
        critical_fields = ['job_title', 'department', 'technical_skills']
        missing_critical = []
        missing_important = []

        for field in required_fields:
            field_value = job_draft.get(field)
            if field == 'job_title' and not field_value:
                field_value = (
                    job_draft.get('cargo')
                    or (detected_criteria.get('cargo') if detected_criteria else None)
                )
            if field == 'department' and not field_value:
                field_value = (
                    job_draft.get('gestorArea')
                    or (detected_criteria.get('gestorArea') if detected_criteria else None)
                )

            if not field_value:
                if field in critical_fields:
                    missing_critical.append(field)
                else:
                    missing_important.append(field)

        suggestions_data['completeness'] = {
            'missing_critical': missing_critical,
            'missing_important': missing_important,
            'suggestions': {},
            'can_advance': len(missing_critical) == 0,
        }

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
                'salary_max': 'Salário Máximo',
            }
            missing_labels = [field_labels.get(f, f) for f in missing_critical]
            lia_message += f"\n\n⚠️ **Campos obrigatórios faltando:** {', '.join(missing_labels)}"
            lia_message += "\nPreencha esses campos para poder avançar."

            if next_stage and next_stage > current_stage:
                next_stage = current_stage

        return lia_message, next_stage, suggestions_data


wizard_step_service = WizardStepService()
