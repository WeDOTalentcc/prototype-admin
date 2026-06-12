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
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

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
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transitioning candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


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
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transition/execute", response_model=TransitionExecuteResponse)
async def execute_transition(
    request: TransitionExecuteRequest,
    current_user: User = Depends(get_current_active_user),
    stage_repo: RecruitmentStageRepository = Depends(get_stage_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Execute a candidate stage transition with optional auto-dispatch."""
    import asyncio as _asyncio
    try:
        from sqlalchemy import update as sa_update

        from app.models.candidate import VacancyCandidate

        values = {"stage": request.to_stage}
        if request.sub_status:
            values["status"] = request.sub_status
        # AUD-4 / LGPD Art. 20: registrar o humano autenticado que decidiu a transicao.
        _reviewer_id = str(getattr(current_user, "id", "") or "") or None
        if _reviewer_id:
            values["human_reviewer_id"] = _reviewer_id
        if request.from_stage:
            values["previous_status"] = request.from_stage

        predicted_sub_status = None
        prediction = None
        if not request.sub_status and settings.ENABLE_LLM_SUBSTATUS_PREDICTION:
            try:
                from app.domains.automation.services.candidate_context_aggregator import CandidateContextAggregator
                from app.domains.automation.services.stage_transition_automation import SubStatusPredictor

                aggregator = CandidateContextAggregator(stage_repo.db)
                candidate_context = await aggregator.aggregate(request.vacancy_candidate_id)

                prediction = SubStatusPredictor.predict(
                    candidate_context=candidate_context,
                    from_stage=request.from_stage or "",
                    to_stage=request.to_stage,
                )

                if prediction and prediction.get("confidence", 0) >= 0.6:
                    predicted_sub_status = prediction.get("predicted_substatus") or ""  # type: ignore[arg-type]
                    values["status"] = predicted_sub_status
                    logger.info(
                        f"[PIPELINE] Predicted sub-status: {predicted_sub_status} "
                        f"(confidence: {prediction.get('confidence')}, "
                        f"reasoning: {prediction.get('reasoning')})"
                    )
            except Exception as pred_err:
                logger.warning(f"[PIPELINE] SubStatus prediction failed (fallback to no sub-status): {pred_err}")

        stmt = (
            sa_update(VacancyCandidate)
            # Onda 4.2b-P0-3 (2026-05-23): filtro company_id obrigatorio — cross-
            # tenant write em candidato = LGPD critical.
            .where(
                VacancyCandidate.id == request.vacancy_candidate_id,
                VacancyCandidate.company_id == company_id,
            )
            .values(**values)
        )
        result = await stage_repo.db.execute(stmt)
        await stage_repo.db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Candidate not found in this tenant",
            )

        try:
            from app.domains.automation.services.stage_automation_engine import (
                AutomationEvent,
                StageAutomationEngine,
                TriggerType,
            )

            automation_payload = {
                    "from_stage": request.from_stage or "",
                    "to_stage": request.to_stage,
                    "action_behavior": request.action_behavior or "",
                    "sub_status": request.sub_status or "",
                    "prompt": request.prompt or "",
                    "action": request.action or "",
                    "triggered_by": str(getattr(current_user, 'id', 'system')),
                }
            if request.extracted_preferences:
                automation_payload["extracted_preferences"] = request.extracted_preferences

            event = AutomationEvent(
                trigger_type=TriggerType.STAGE_CHANGED,
                candidate_id=request.vacancy_candidate_id,
                vacancy_id=request.vacancy_id or "",
                # Onda 4.2b-P0-4 (2026-05-23): removido 'admin_company' fallback.
                # JWT e fonte autoritativa unica (REGRA 6).
                company_id=company_id,
                payload=automation_payload,
            )
            engine = StageAutomationEngine()
            _asyncio.create_task(engine.process_event(event, stage_repo.db))
            logger.info(f"[PIPELINE] Emitted STAGE_CHANGED event for {request.vacancy_candidate_id}")
        except Exception as event_err:
            logger.warning(f"[PIPELINE] Failed to emit STAGE_CHANGED event: {event_err}")

        dispatch_results = []

        resolved_action_behavior = request.action_behavior
        if request.action == "lia_auto" and not resolved_action_behavior:
            try:
                from sqlalchemy import select as sa_select

                from app.models.recruitment_stages import RecruitmentStage as _RS
                # Onda 4.2b-P0-5 (2026-05-23): stage lookup com company_id filter.
                # Antes resolvia stage de qualquer empresa que tivesse nome igual.
                stage_result = await stage_repo.db.execute(
                    sa_select(_RS).where(
                        _RS.name == request.to_stage,
                        _RS.company_id == company_id,
                    )
                )
                dest_stage = stage_result.scalar_one_or_none()
                if dest_stage:
                    resolved_action_behavior = dest_stage.action_behavior
                    logger.info(f"Resolved action_behavior '{resolved_action_behavior}' from stage '{request.to_stage}'")
            except Exception as stage_err:
                logger.warning(f"Could not resolve action_behavior from stage: {stage_err}")

        from app.shared.hitl.hitl_approval_context import rest_hitl_blocks
        _hitl_held = rest_hitl_blocks(action=request.action or "", approved=bool(getattr(request, "hitl_approved", False)))
        if _hitl_held:
            logger.info("[PIPELINE] HITL gate: feedback de %s retido ate confirmacao", request.vacancy_candidate_id)
        if request.action == "lia_auto" and resolved_action_behavior and not _hitl_held:  # type: ignore[truthy-bool]
            try:
                from app.domains.communication.services.transition_dispatch_service import TransitionDispatchService
                dispatch_service = TransitionDispatchService(stage_repo.db)

                # Onda 4.2b-P0-4 (2026-05-23): removido fallback 'admin_company'.
                # company_id ja vem do Depends(require_company_id) — usar direto.
                triggered_by = getattr(current_user, 'id', None) or 'system'

                personalized_content = None
                if request.prompt and settings.ENABLE_LLM_DISPATCH_PERSONALIZATION:
                    try:
                        from app.domains.automation.services.candidate_context_aggregator import (
                            CandidateContextAggregator,
                        )
                        from app.domains.automation.services.stage_transition_automation import MessageGenerator

                        aggregator = CandidateContextAggregator(stage_repo.db)
                        candidate_context = await aggregator.aggregate(request.vacancy_candidate_id)
                        job_context = candidate_context.get("job", {})

                        # Assinatura do feedback = nome do CLIENTE (tenant), nunca "WeDoTalent".
                        # Falha-soft: sem nome resolvido, o gerador usa "Equipe de Recrutamento".
                        try:
                            from sqlalchemy import select as _sa_select_co
                            from app.models.company import Company as _Company
                            _co_res = await stage_repo.db.execute(
                                _sa_select_co(_Company.display_name, _Company.name).where(_Company.id == company_id)
                            )
                            _co_row = _co_res.first()
                            if _co_row:
                                job_context["company_name"] = _co_row[0] or _co_row[1] or ""
                        except Exception as _co_err:
                            logger.warning(f"[PIPELINE] could not resolve company display name: {_co_err}")

                        msg_type = "feedback_construtivo" if request.to_stage == "rejected" else "aprovacao"

                        msg_result = await MessageGenerator.generate(
                            candidate_context=candidate_context,
                            to_stage=request.to_stage,
                            substatus=request.sub_status or predicted_sub_status or "",
                            job_context=job_context,
                            message_type=msg_type,
                            channel=request.channel or "email",
                        )

                        if msg_result and msg_result.get("body"):
                            personalized_content = msg_result["body"]
                            logger.info("[PIPELINE] AI-generated personalized message for dispatch")
                    except Exception as msg_err:
                        logger.warning(f"[PIPELINE] AI message generation failed, using template: {msg_err}")

                extra_vars: dict[str, Any] = {}
                if request.prompt:
                    extra_vars["prompt"] = request.prompt
                if request.extracted_preferences and request.action in ("lia_auto", None):
                    prefs = {k: str(v) for k, v in request.extracted_preferences.items() if v is not None and str(v).strip()}
                    extra_vars.update(prefs)
                    pref_map = {
                        "date": "interview_date",
                        "time": "interview_time",
                        "interviewer": "interviewer_name",
                        "location": "interview_location",
                        "format": "interview_format",
                        "duration": "interview_duration",
                    }
                    for src_key, dest_key in pref_map.items():
                        if src_key in prefs:
                            extra_vars[dest_key] = prefs[src_key]

                result = await dispatch_service.dispatch_for_transition(
                    vacancy_candidate_id=request.vacancy_candidate_id,
                    to_stage=request.to_stage,
                    action_behavior=str(resolved_action_behavior),  # type: ignore[arg-type]
                    channel=request.channel or "email",
                    company_id=str(company_id),
                    triggered_by=str(triggered_by),
                    extra_variables=extra_vars if extra_vars else None,
                    personalized_content=personalized_content,
                )
                dispatch_results.append(DispatchResult(**result))
            except Exception as dispatch_error:
                logger.error(f"Dispatch error during transition: {dispatch_error}", exc_info=True)
                dispatch_results.append(DispatchResult(
                    success=False,
                    channel=request.channel or "email",
                    error=str(dispatch_error)
                ))

        # AUD-4: trilha de auditoria da decisao de transicao (humano autenticado).
        try:
            from app.models.audit_log import DecisionType
            from app.shared.compliance.audit_service import get_audit_service
            _dtype = DecisionType.REJECT_CANDIDATE.value if request.to_stage == "rejected" else DecisionType.MOVE_STAGE.value
            await get_audit_service().log_decision(
                company_id=str(company_id),
                agent_name="pipeline_transition",
                decision_type=_dtype,
                action="execute_transition",
                decision=str(values.get("status") or request.to_stage),
                reasoning=[
                    f"Transicao {request.from_stage or '?'} -> {request.to_stage}",
                    f"Motivo: {values.get('status') or 'n/d'}",
                    f"Acao: {request.action or 'n/d'}",
                    ("Feedback retido p/ confirmacao HITL" if _hitl_held else ("Feedback disparado" if request.action == "lia_auto" else "Sem feedback")),
                ],
                criteria_used=["human_initiated_transition"],
                candidate_id=request.vacancy_candidate_id,
                job_vacancy_id=request.vacancy_id or None,
                human_review_required=_hitl_held,
                actor_user_id=_reviewer_id,
            )
        except Exception as audit_err:
            logger.warning(f"[PIPELINE] audit log_decision failed: {audit_err}")

        return TransitionExecuteResponse(
            success=True,
            message=("Candidato movido; feedback aguarda confirmacao." if _hitl_held else f"Candidato movido para {request.to_stage}"),
            candidate_id=request.vacancy_candidate_id,
            new_stage=request.to_stage,
            new_sub_status=request.sub_status or predicted_sub_status,
            dispatch_results=dispatch_results if dispatch_results else None,
            predicted_sub_status=predicted_sub_status,
            prediction_confidence=prediction.get("confidence") if predicted_sub_status and prediction else None,
            requires_approval=_hitl_held,
        )
    except HTTPException:
        raise  # deixar FastAPI tratar (retorna 4xx/5xx)
    except ValueError as e:
        # Erro de validação de negócio — 422 explícito
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # Crash inesperado — logar e retornar 500 (não swallow como HTTP 200)
        logger.error(
            "[transition/execute] unhandled error: %s",
            str(e),
            exc_info=True,
            extra={"vacancy_candidate_id": getattr(request, "vacancy_candidate_id", None)},
        )
        raise HTTPException(status_code=500, detail="Erro interno ao processar transição")



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
