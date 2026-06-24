"""
Recruitment stages — candidate transitions API.

- GET  /candidate/{id}/info
- GET  /candidate/{id}/history
- POST /transition/interpret-context
- POST /transition/execute
"""
import uuid
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from ._shared import (
    ACTION_BEHAVIOR_LABELS,
    TransitionRequest,
    InterpretContextRequest,
    InterpretContextResponse,
    TransitionExecuteRequest,
    TransitionExecuteResponse,
    PreviewFeedbackRequest,
    PreviewFeedbackResponse,
    DispatchResult,
    TaskItem,
    LearnedSuggestion,
    _get_default_sub_status,
    _determine_suggested_action,
    _determine_urgency,
    get_current_active_user,
    get_current_user_or_demo,
    get_user_company_id,
    get_stage_repo,
    RecruitmentStageRepository,
    TransitionError,
    pipeline_stage_service,
    settings,
    User,
)
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAInvalidStateTransition
from app.shared.errors import LIAError
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from app.services.cache.context_cache import get_context_cache as _get_ctx_cache
from app.api.v1.candidates._shared import REJECTION_STAGES  # P-GUARD SEV1-C3-01
from app.shared.compliance.fairness_guard_middleware import (  # P-GUARD SEV1-C3-01
    check_rejection_reason,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Recruitment Stages - Transition"])


@router.post("/transition", response_model=None)
async def transition_candidate(
    request: TransitionRequest,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    """
    Transition a candidate to a new stage/sub-status.

    This is the main endpoint for moving candidates through the pipeline.
    Validates transition, records history, and triggers ATS sync.
    Uses the authenticated user's company for validation.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        result = await pipeline_stage_service.transition_candidate(
            vacancy_candidate_id=request.vacancy_candidate_id,
            to_stage=request.to_stage,
            to_sub_status=request.to_sub_status,
            triggered_by=request.triggered_by,
            triggered_by_user_id=request.triggered_by_user_id or str(current_user.id),
            source_agent=request.source_agent,
            reason=request.reason,
            notes=request.notes,
            context={"company_id": effective_company_id},
            force=request.force,
            db=stage_repo.db
        )
        return result
    except TransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LIAInvalidStateTransition as e:
        raise HTTPException(status_code=409, detail=e.message)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transitioning candidate: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/candidate/{vacancy_candidate_id}/info", response_model=None)
async def get_candidate_stage_info(
    vacancy_candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    """
    Get current stage/sub-status info for a candidate.
    Uses the authenticated user's company for access control.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        info = await pipeline_stage_service.get_candidate_stage_info(
            vacancy_candidate_id=vacancy_candidate_id,
            company_id=effective_company_id,
            db=stage_repo.db
        )
        if not info:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate info: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/candidate/{vacancy_candidate_id}/history", response_model=None)
async def get_candidate_history(
    vacancy_candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    """
    Get stage transition history for a candidate.
    Uses the authenticated user's company for access control.
    """
    try:
        effective_company_id = get_user_company_id(current_user)

        history = await pipeline_stage_service.get_candidate_history(
            vacancy_candidate_id=vacancy_candidate_id,
            company_id=effective_company_id,
            limit=limit,
            db=stage_repo.db
        )
        return {
            "history": history,
            "total": len(history)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting candidate history: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/transition/interpret-context", response_model=InterpretContextResponse)
async def interpret_transition_context(
    request: InterpretContextRequest,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)):
    """
    Interpret a candidate stage transition context.
    Layer 3: PipelineTransitionAgent (ReAct loop with tools) — primary.
    Layer 2: Uses LLM single-shot when Layer 3 fails.
    Layer 1: Rule-based logic as final fallback.
    """
    import uuid as _uuid
    try:
        if request.prompt and request.prompt.strip():
            # --- Layer 3: ReAct Agent ---
            try:
                from lia_agents_core.agent_interface import AgentInput

                from app.domains.pipeline.agents.pipeline_transition_agent import get_pipeline_transition_agent

                conversation_history = []
                if request.message_history:
                    conversation_history = [
                        {"role": m.role, "content": m.content}
                        for m in request.message_history
                    ]

                # R2 canonical: company_id from JWT via Depends(require_company_id) — handler scope
                user_id = str(getattr(current_user, "id", "")) or ""

                conv_id = request.conversation_id or str(_uuid.uuid4())

                agent_input = AgentInput(
                    message=request.prompt,
                    context={
                        "action_behavior": request.action_behavior,
                        "candidate_id": request.candidate_id,
                        "candidate_name": request.candidate_name or "",
                        "job_id": request.job_id or "",
                        "job_title": request.job_title or "",
                        "from_stage": request.from_stage,
                        "to_stage": request.to_stage,
                        "company_id": company_id,
                    },
                    session_id=conv_id,
                    company_id=company_id,
                    user_id=user_id,
                    conversation_history=conversation_history,
                )

                agent = get_pipeline_transition_agent()
                agent_output = await agent.process(agent_input)

                if agent_output and agent_output.message and not agent_output.error:
                    state = agent_output.state_updates or {}

                    suggested_sub = state.get("suggested_sub_status")
                    if not suggested_sub:
                        suggested_sub = _get_default_sub_status(request.to_stage)

                    tasks_raw = state.get("tasks") or []
                    tasks = [TaskItem(**t) for t in tasks_raw] if tasks_raw else None

                    learned_raw = state.get("learned_suggestions") or []
                    learned = [LearnedSuggestion(**s) for s in learned_raw] if learned_raw else None

                    return InterpretContextResponse(
                        suggested_sub_status=suggested_sub,
                        suggested_action=state.get("suggested_action", "lia_auto"),
                        action_label=ACTION_BEHAVIOR_LABELS.get(request.action_behavior, "Mover Candidato"),
                        urgency=_determine_urgency(request.action_behavior),
                        lia_message=agent_output.message,
                        extracted_preferences=state.get("extracted_preferences") or None,
                        ai_powered=True,
                        confidence=agent_output.confidence,
                        tasks=tasks,
                        out_of_scope=state.get("out_of_scope", False),
                        candidate_info=state.get("candidate_info"),
                        learned_suggestions=learned,
                        fairness_result=state.get("fairness_result"),
                        layer=3,
                        conversation_id=conv_id,
                    )

                logger.warning("[INTERPRET] Layer 3 returned empty/error response")
                return InterpretContextResponse(
                    suggested_sub_status=_get_default_sub_status(request.to_stage),
                    suggested_action="lia_auto",
                    action_label=ACTION_BEHAVIOR_LABELS.get(request.action_behavior, "Mover Candidato"),
                    urgency=_determine_urgency(request.action_behavior),
                    lia_message="Não consegui processar sua mensagem agora. Por favor, tente novamente.",
                    ai_powered=False,
                    layer=1,
                    conversation_id=conv_id,
                )

            except Exception as agent_err:
                logger.warning(f"[INTERPRET] ReAct agent failed: {agent_err}")
                return InterpretContextResponse(
                    suggested_sub_status=_get_default_sub_status(request.to_stage),
                    suggested_action=_determine_suggested_action(request.action_behavior, request.prompt),
                    action_label=ACTION_BEHAVIOR_LABELS.get(request.action_behavior, "Mover Candidato"),
                    urgency=_determine_urgency(request.action_behavior),
                    lia_message="Estou com dificuldade em processar agora. Você pode prosseguir com a movimentação manualmente.",
                    ai_powered=False,
                    layer=1,
                    conversation_id=conv_id if 'conv_id' in locals() else None,
                )

        # No prompt — rule-based defaults only (UI didn't open chat)
        return InterpretContextResponse(
            suggested_sub_status=_get_default_sub_status(request.to_stage),
            suggested_action=_determine_suggested_action(request.action_behavior, request.prompt),
            action_label=ACTION_BEHAVIOR_LABELS.get(request.action_behavior, "Mover Candidato"),
            urgency=_determine_urgency(request.action_behavior),
            ai_powered=False,
            layer=1,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error interpreting transition context: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/transition/preview-feedback", response_model=PreviewFeedbackResponse)
async def preview_feedback(
    request: PreviewFeedbackRequest,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
    company_id: str = Depends(require_company_id),
):
    """Gera o texto do feedback para REVISAO (item 3 / 1-exemplo do bulk).

    READ-ONLY: NAO move o candidato e NAO envia nada. Reusa o MESMO produtor
    (MessageGenerator) + a mesma camada de fairness/LGPD e a regra de canal (W1)
    do envio real, para o recrutador ver exatamente o que sairia.
    """
    from app.domains.automation.services.candidate_context_aggregator import (
        CandidateContextAggregator,
    )
    from app.domains.automation.services.stage_transition_automation import (
        MessageGenerator,
        is_high_risk_rejection,
    )
    from app.domains.communication.services.transition_dispatch_service import (
        ai_personalization_allowed_for_channel,
        is_feedback_fairness_blocked,
    )

    channel = request.channel or "email"
    aggregator = CandidateContextAggregator(stage_repo.db)
    candidate_context = await aggregator.aggregate(request.vacancy_candidate_id)
    job_context = candidate_context.get("job", {}) or {}

    try:
        from sqlalchemy import select as _sa_sel
        from app.models.company import Company as _Company
        _r = await stage_repo.db.execute(
            _sa_sel(_Company.display_name, _Company.name).where(_Company.id == company_id)
        )
        _row = _r.first()
        if _row:
            job_context["company_name"] = _row[0] or _row[1] or ""
    except Exception as _ce:
        logger.warning(f"[PREVIEW] could not resolve company name: {_ce}")

    msg_type = "feedback_construtivo" if request.to_stage == "rejected" else "aprovacao"
    result = await MessageGenerator.generate(
        candidate_context=candidate_context,
        to_stage=request.to_stage,
        substatus=request.sub_status or "",
        job_context=job_context,
        message_type=msg_type,
        channel=channel,
    )
    body = result.get("body", "") or ""
    generated_by = (result.get("metadata") or {}).get("generated_by", "unknown")
    high_risk = request.to_stage == "rejected" and is_high_risk_rejection(request.sub_status or "")
    uses_template_only = not ai_personalization_allowed_for_channel(channel)
    fairness_blocked = (not uses_template_only) and is_feedback_fairness_blocked(body, str(company_id))
    ai_personalized = (generated_by == "lia_claude") and not uses_template_only and not fairness_blocked

    return PreviewFeedbackResponse(
        body=body,
        subject=result.get("subject"),
        generated_by=generated_by,
        ai_personalized=ai_personalized,
        fairness_blocked=fairness_blocked,
        high_risk=high_risk,
        uses_template_only=uses_template_only,
        channel=channel,
    )
