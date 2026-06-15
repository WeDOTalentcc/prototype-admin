"""
LIA Assistant — Fast Track wizard endpoint.

Extracted from lia_assistant.py (Phase 5 decomposition).
All routes share prefix="/lia" to preserve existing /api/v1/lia/fast-track/* URLs.
"""
import logging
import re
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.domains.job_management.services.vacancy_search_service import vacancy_search_service
from app.models import JobVacancy
from app.shared.services.intent_classifier import IntentType, intent_classifier_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lia", tags=["lia-fasttrack"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FastTrackState(StrEnum):
    PRE_WIZARD = "pre_wizard"
    SEARCHING = "searching"
    SELECTING = "selecting"
    REVIEWING = "reviewing"
    ADJUSTING = "adjusting"
    PUBLISHING = "publishing"


class FastTrackWizardRequest(WeDoBaseModel):
    conversation_id: str | None = None
    state: FastTrackState = FastTrackState.PRE_WIZARD
    user_input: str
    selected_vacancy_id: UUID | None = None
    context: dict[str, Any] | None = None


class FastTrackWizardResponse(BaseModel):
    conversation_id: str
    state: str
    next_state: str | None = None
    lia_message: str
    vacancies: list[dict[str, Any]] | None = None
    selected_vacancy: dict[str, Any] | None = None
    adjustments_applied: dict[str, Any] | None = None
    is_complete: bool = False
    created_job: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/fast-track/wizard", response_model=FastTrackWizardResponse)
# TODO(phase2): extract to repository — LIA fasttrack DB calls
async def fast_track_wizard_step(
    request: FastTrackWizardRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo), 
company_id: str = Depends(require_company_id)) -> FastTrackWizardResponse:
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        conversation_id = request.conversation_id or str(uuid4())
        current_state = request.state
        user_input = request.user_input
        context = request.context or {}
        company_id = current_user.company_id

        lia_message = ""
        next_state = None
        vacancies_result = None
        selected_vacancy = None
        adjustments_applied = None
        is_complete = False
        created_job = None

        if current_state == FastTrackState.PRE_WIZARD:
            classification = await intent_classifier_service.classify(user_input)

            if classification.intent_type == IntentType.REUSE_VACANCY:
                criteria = await vacancy_search_service.extract_search_criteria(user_input)
                has_minimum = vacancy_search_service.validate_minimum_criteria(criteria)

                if has_minimum:
                    vacancies = await vacancy_search_service.search_vacancies(
                        criteria=criteria,
                        company_id=company_id,
                        db=db,
                        limit=10
                    )
                    if vacancies:
                        vacancies_result = [v.model_dump(mode='json') for v in vacancies]
                        lia_message = f"Perfeito! Encontrei {len(vacancies)} vaga(s) anteriores que correspondem aos seus critérios:\n\n"
                        for i, v in enumerate(vacancies[:5], 1):
                            status_emoji = "✅" if v.status == "contratado" else "❌" if v.status == "cancelado" else "🔄"
                            lia_message += f"{i}. **{v.title}** - {v.department or 'Sem área'} {status_emoji}\n"
                            if v.manager:
                                lia_message += f"   Gestor: {v.manager}\n"
                        lia_message += "\nQual vaga você gostaria de usar como base?"
                        next_state = FastTrackState.SELECTING.value
                    else:
                        lia_message = (
                            "Não encontrei vagas anteriores com esses critérios. Deseja:\n"
                            "1. Ajustar os critérios de busca\n"
                            "2. Criar uma vaga do zero\n\n"
                            "O que prefere?"
                        )
                        next_state = FastTrackState.SEARCHING.value
                else:
                    lia_message = (
                        "Entendi que você quer reaproveitar uma vaga anterior! 🎯\n\n"
                        "Para encontrar a vaga certa, me diga mais detalhes:\n"
                        "• Qual era o cargo?\n"
                        "• Em qual área/departamento?\n"
                        "• Quem era o gestor?\n"
                        "• De qual ano?\n"
                    )
                    next_state = FastTrackState.SEARCHING.value
            else:
                lia_message = (
                    "Entendi! Vou te ajudar a criar uma nova vaga. 🚀\n\n"
                    "Me conte sobre a posição que precisa:\n"
                    "• Qual o cargo?\n"
                    "• Para qual área?\n"
                    "• Modelo de trabalho (remoto/híbrido/presencial)?\n"
                )
                next_state = None

        elif current_state == FastTrackState.SEARCHING:
            criteria = await vacancy_search_service.extract_search_criteria(user_input)
            has_minimum = vacancy_search_service.validate_minimum_criteria(criteria)

            if has_minimum:
                vacancies = await vacancy_search_service.search_vacancies(
                    criteria=criteria,
                    company_id=company_id,
                    db=db,
                    limit=10
                )
                if vacancies:
                    vacancies_result = [v.model_dump(mode='json') for v in vacancies]
                    lia_message = f"Encontrei {len(vacancies)} vaga(s):\n\n"
                    for i, v in enumerate(vacancies[:5], 1):
                        status_emoji = "✅" if v.status == "contratado" else "❌" if v.status == "cancelado" else "🔄"
                        lia_message += f"{i}. **{v.title}** - {v.department or 'Sem área'} {status_emoji}\n"
                    lia_message += "\nQual vaga você gostaria de usar como base?"
                    next_state = FastTrackState.SELECTING.value
                else:
                    lia_message = "Ainda não encontrei vagas com esses critérios. Tente outros termos ou vamos criar do zero?"
                    next_state = FastTrackState.SEARCHING.value
            else:
                lia_message = (
                    "Preciso de mais informações para buscar. Por favor, me diga:\n"
                    "• O cargo ou título da vaga\n"
                    "• A área ou departamento\n"
                    "• O ano ou período\n"
                )
                next_state = FastTrackState.SEARCHING.value

        elif current_state == FastTrackState.SELECTING:
            if request.selected_vacancy_id:
                vacancy_details = await vacancy_search_service.get_vacancy_full_details(
                    vacancy_id=request.selected_vacancy_id,
                    db=db,
                    company_id=company_id
                )
                if vacancy_details:
                    selected_vacancy = vacancy_details.model_dump(mode='json')
                    lia_message = f"Ótima escolha! Aqui estão os detalhes da vaga **{vacancy_details.title}**:\n\n"
                    lia_message += f"📍 **Localização:** {vacancy_details.location or 'Não definida'}\n"
                    lia_message += f"🏢 **Modelo:** {vacancy_details.work_model or 'Não definido'}\n"
                    lia_message += f"👔 **Senioridade:** {vacancy_details.seniority_level or 'Não definida'}\n"
                    if vacancy_details.salary_range:
                        min_sal = vacancy_details.salary_range.get('min', 0)
                        max_sal = vacancy_details.salary_range.get('max', 0)
                        if min_sal and max_sal:
                            lia_message += f"💰 **Faixa salarial:** R$ {min_sal:,.0f} - R$ {max_sal:,.0f}\n"
                    if vacancy_details.technical_requirements:
                        skills = [r.get('technology', r.get('name', '')) for r in vacancy_details.technical_requirements[:5]]
                        lia_message += f"🛠️ **Skills:** {', '.join(skills)}\n"
                    lia_message += (
                        "\n**Deseja fazer algum ajuste ou publicar assim mesmo?**\n"
                        "• Diga o que quer alterar (ex: 'salário para 18k', 'modelo híbrido')\n"
                        "• Ou diga 'publicar' para criar a vaga"
                    )
                    next_state = FastTrackState.ADJUSTING.value
                else:
                    lia_message = "Não consegui carregar os detalhes dessa vaga. Por favor, selecione outra."
                    next_state = FastTrackState.SELECTING.value
            else:
                number_match = re.search(r'\b(\d+)\b', user_input)
                if number_match:
                    lia_message = "Por favor, me passe o ID da vaga selecionada para que eu possa carregar os detalhes."
                else:
                    lia_message = "Qual vaga você escolhe? Me diga o número ou o título."
                next_state = FastTrackState.SELECTING.value

        elif current_state == FastTrackState.ADJUSTING:
            if any(kw in user_input.lower() for kw in ["publicar", "criar", "confirmar", "ok", "pronto", "sim"]):
                selected_id = request.selected_vacancy_id or context.get("selected_vacancy_id")

                if selected_id:
                    vacancy_details = await vacancy_search_service.get_vacancy_full_details(
                        vacancy_id=selected_id,
                        db=db,
                        company_id=company_id
                    )
                    if vacancy_details:
                        stored_adjustments = context.get("adjustments", {})
                        if stored_adjustments:
                            vacancy_details = vacancy_search_service.apply_adjustments(vacancy_details, stored_adjustments)

                        new_job = JobVacancy(
                            company_id=company_id,
                            title=vacancy_details.title,
                            department=vacancy_details.department,
                            location=vacancy_details.location,
                            work_model=vacancy_details.work_model,
                            employment_type=vacancy_details.employment_type,
                            seniority_level=vacancy_details.seniority_level,
                            description=vacancy_details.description,
                            # T-1166 — propagate responsibilities defensively
                            # (fast-track clones an existing vacancy; legacy
                            # source rows may have it null/missing).
                            responsibilities=list(getattr(vacancy_details, "responsibilities", None) or []),
                            salary_range=vacancy_details.salary_range,
                            benefits=vacancy_details.benefits or [],
                            technical_requirements=vacancy_details.technical_requirements or [],
                            behavioral_competencies=vacancy_details.behavioral_competencies or [],
                            screening_questions=vacancy_details.screening_questions or [],
                            languages=vacancy_details.languages or [],
                            manager=vacancy_details.manager,
                            manager_email=vacancy_details.manager_email,
                            interview_stages=vacancy_details.interview_stages or [],
                            eligibility_questions=vacancy_details.eligibility_questions or [],
                            status="Rascunho",
                            stage="Planejamento",
                            additional_data={"source": "fast_track", "base_vacancy_id": str(selected_id)}
                        )
                        db.add(new_job)
                        await db.flush()
                        await db.refresh(new_job)

                        created_job = {
                            "id": str(new_job.id),
                            "title": new_job.title,
                            "status": new_job.status
                        }
                        lia_message = (
                            f"🎉 Pronto! A vaga **{new_job.title}** foi criada com sucesso!\n\n"
                            "A vaga está em rascunho. Você pode:\n"
                            "• Revisar os detalhes antes de publicar\n"
                            "• Publicar imediatamente\n"
                            "• Solicitar aprovação do gestor"
                        )
                        next_state = FastTrackState.PUBLISHING.value
                        is_complete = True
                else:
                    lia_message = "Não encontrei a vaga selecionada. Por favor, selecione novamente."
                    next_state = FastTrackState.SELECTING.value
            else:
                adjustments = await vacancy_search_service.extract_adjustments(user_input)
                if adjustments:
                    adjustments_applied = adjustments
                    adjustment_parts = []
                    if adjustments.get("salary_min") or adjustments.get("salary_max"):
                        adjustment_parts.append("faixa salarial")
                    if adjustments.get("work_model"):
                        adjustment_parts.append(f"modelo para {adjustments['work_model']}")
                    if adjustments.get("location"):
                        adjustment_parts.append(f"localização para {adjustments['location']}")
                    if adjustments.get("manager"):
                        adjustment_parts.append(f"gestor para {adjustments['manager']}")
                    if adjustments.get("title"):
                        adjustment_parts.append(f"título para {adjustments['title']}")
                    lia_message = (
                        f"✅ Registrei os ajustes: {', '.join(adjustment_parts)}.\n\n"
                        "Deseja fazer mais algum ajuste ou posso publicar a vaga?"
                    )
                else:
                    lia_message = (
                        "Não entendi qual ajuste você quer fazer. Exemplos:\n"
                        "• 'Salário para 15k'\n"
                        "• 'Modelo híbrido'\n"
                        "• 'Localização São Paulo'\n\n"
                        "Ou diga 'publicar' para criar a vaga como está."
                    )
                next_state = FastTrackState.ADJUSTING.value

        elif current_state == FastTrackState.PUBLISHING:
            lia_message = "A vaga já foi criada! Você pode acessá-la no painel de vagas."
            is_complete = True

        return FastTrackWizardResponse(
            conversation_id=conversation_id,
            state=current_state.value,
            next_state=next_state,
            lia_message=lia_message,
            vacancies=vacancies_result,
            selected_vacancy=selected_vacancy,
            adjustments_applied=adjustments_applied,
            is_complete=is_complete,
            created_job=created_job
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Fast Track wizard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
