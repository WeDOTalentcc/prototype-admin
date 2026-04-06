"""
Handlers para eventos inter-API da plataforma.

Registra handlers para eventos publicados pelas outras APIs de domínio.
Chamado no startup da aplicação via register_all_handlers().

Padrão de implementação dos handlers:
  - Recebem PlatformEvent com company_id e payload
  - São assíncronos (async def)
  - Falhas são capturadas pelo dispatcher (não propagam)
  - Lógica real fica nos services de domínio
"""
import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.shared.messaging.platform_events import PlatformEvent, register_event_handler

logger = logging.getLogger(__name__)


async def _get_db() -> AsyncSession:
    return AsyncSessionLocal()


async def handle_job_published(event: PlatformEvent) -> None:
    """
    Quando uma vaga é publicada (api-vagas), preparar estrutura de pipeline (api-funil).

    Responsabilidades:
    - Inicializar os estágios do pipeline para a nova vaga (via company stages)
    - Registrar atividade no log de auditoria
    """
    job_id = event.payload.get("job_id")
    company_id = event.company_id
    job_title = event.payload.get("title", "")
    logger.info(
        "[EventHandler] job.published job_id=%s company=%s",
        job_id,
        company_id,
    )

    db = await _get_db()
    try:
        from app.domains.recruiter_assistant.services.pipeline_stage_service import (
            PipelineStageService,
        )

        svc = PipelineStageService()
        await svc.initialize_company_stages(company_id, db=db)
        logger.info(
            "[EventHandler] Pipeline stages ensured for company=%s job_id=%s",
            company_id,
            job_id,
        )

        try:
            from app.services.activity_service import ActivityService

            activity_svc = ActivityService()
            await activity_svc.create_activity(
                activity_type="job_published",
                title="Vaga Publicada",
                description=f"Vaga '{job_title}' publicada e pipeline inicializado.",
                actor_id="system",
                actor_name="LIA Platform Events",
                actor_type="system",
                target_id=job_id or "",
                target_type="job",
                extra_data={
                    "company_id": company_id,
                    "job_title": job_title,
                    "event_id": event.event_id,
                },
                category="automation",
            )
        except Exception as exc:
            logger.warning("[EventHandler] Failed to create activity for job_published: %s", exc)
    except Exception as exc:
        logger.error("[EventHandler] handle_job_published error: %s", exc)
    finally:
        await db.close()


async def handle_job_closed(event: PlatformEvent) -> None:
    """
    Quando uma vaga é encerrada (api-vagas), arquivar candidatos em aberto.

    Responsabilidades:
    - Marcar candidatos pendentes como 'withdrawn' (vaga encerrada)
    - Enviar feedback humanizado aos candidatos afetados
    - Registrar atividade
    """
    job_id = event.payload.get("job_id")
    company_id = event.company_id
    reason = event.payload.get("reason", "Vaga encerrada pela empresa")
    logger.info(
        "[EventHandler] job.closed job_id=%s company=%s",
        job_id,
        company_id,
    )

    db = await _get_db()
    try:
        from app.models.candidate import Candidate, VacancyCandidate
        from app.models.job_vacancy import JobVacancy

        vacancy_result = await db.execute(
            select(JobVacancy).where(
                JobVacancy.id == job_id,
                JobVacancy.company_id == company_id,
            )
        )
        vacancy = vacancy_result.scalar_one_or_none()
        if not vacancy:
            logger.warning("[EventHandler] Vacancy %s not found for company %s", job_id, company_id)
            return

        active_statuses = ("rejected", "hired", "withdrawn")
        open_candidates_result = await db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == vacancy.id,
                VacancyCandidate.status.notin_(active_statuses),
            )
        )
        open_candidates = open_candidates_result.scalars().all()

        archived_count = 0
        feedback_sent = 0
        candidates_to_notify: list[tuple[str, str, str | None]] = []

        for vc in open_candidates:
            vc.status = "withdrawn"
            vc.updated_at = datetime.now(UTC)
            archived_count += 1

            try:
                candidate_result = await db.execute(
                    select(Candidate).where(Candidate.id == vc.candidate_id)
                )
                candidate = candidate_result.scalar_one_or_none()
                if candidate and candidate.email:
                    candidates_to_notify.append(
                        (candidate.name, candidate.email, getattr(candidate, "phone", None))
                    )
            except Exception as exc:
                logger.warning(
                    "[EventHandler] Failed to load candidate %s for notification: %s",
                    vc.candidate_id,
                    exc,
                )

        await db.commit()

        for cand_name, cand_email, cand_phone in candidates_to_notify:
            try:
                from app.domains.communication.services.communication_dispatcher import (
                    CommunicationDispatcher,
                )

                dispatcher = CommunicationDispatcher()
                await dispatcher.dispatch_message(
                    company_id=company_id,
                    recipient_email=cand_email,
                    recipient_phone=cand_phone,
                    subject=f"Atualização sobre sua candidatura - {vacancy.title}",
                    message=(
                        f"Olá {cand_name}, informamos que a posição "
                        f"'{vacancy.title}' foi encerrada. {reason}. "
                        f"Seu perfil permanece em nosso banco de talentos."
                    ),
                    candidate_name=cand_name,
                )
                feedback_sent += 1
            except Exception as exc:
                logger.warning(
                    "[EventHandler] Failed to send closure feedback to %s: %s",
                    cand_email,
                    exc,
                )

        logger.info(
            "[EventHandler] job.closed archived=%d feedback_sent=%d job_id=%s",
            archived_count,
            feedback_sent,
            job_id,
        )

        try:
            from app.services.activity_service import ActivityService

            activity_svc = ActivityService()
            await activity_svc.create_activity(
                activity_type="job_closed",
                title="Vaga Encerrada",
                description=(
                    f"Vaga '{vacancy.title}' encerrada. "
                    f"{archived_count} candidatos arquivados, "
                    f"{feedback_sent} notificados."
                ),
                actor_id="system",
                actor_name="LIA Platform Events",
                actor_type="system",
                target_id=job_id or "",
                target_type="job",
                extra_data={
                    "company_id": company_id,
                    "archived_count": archived_count,
                    "feedback_sent": feedback_sent,
                    "reason": reason,
                    "event_id": event.event_id,
                },
                category="automation",
            )
        except Exception as exc:
            logger.warning("[EventHandler] Failed to create activity for job_closed: %s", exc)
    except Exception as exc:
        logger.error("[EventHandler] handle_job_closed error: %s", exc)
        try:
            await db.rollback()
        except Exception:
            pass
    finally:
        await db.close()


async def handle_candidate_moved(event: PlatformEvent) -> None:
    """
    Quando um candidato muda de estágio (api-funil), atualizar analytics e disparar automações.

    Responsabilidades:
    - Disparar automações configuradas para o estágio destino
    - Registrar atividade de transição
    """
    candidate_id = event.payload.get("candidate_id")
    vacancy_id = event.payload.get("vacancy_id")
    from_stage = event.payload.get("from_stage")
    to_stage = event.payload.get("to_stage")
    company_id = event.company_id
    logger.info(
        "[EventHandler] candidate.moved candidate_id=%s %s→%s company=%s",
        candidate_id,
        from_stage,
        to_stage,
        company_id,
    )

    if not candidate_id or not to_stage:
        logger.warning("[EventHandler] candidate.moved missing candidate_id or to_stage")
        return

    db = await _get_db()
    try:
        from app.domains.automation.services.stage_automation_engine import (
            AutomationEvent,
            TriggerType,
        )

        automation_event = AutomationEvent(
            trigger_type=TriggerType.STAGE_CHANGED,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id or "",
            company_id=company_id,
            payload={
                "from_stage": from_stage,
                "to_stage": to_stage,
                "event_id": event.event_id,
            },
        )

        try:
            from app.domains.automation.services.stage_automation_engine import (
                stage_automation_engine,
            )

            await stage_automation_engine.process_event(automation_event, db=db)
            logger.info(
                "[EventHandler] Stage automation processed for candidate %s → %s",
                candidate_id,
                to_stage,
            )
        except ImportError:
            logger.debug("[EventHandler] stage_automation_engine singleton not available")
        except Exception as exc:
            logger.warning("[EventHandler] Stage automation error: %s", exc)

        try:
            from app.services.activity_service import ActivityService

            activity_svc = ActivityService()
            await activity_svc.create_activity(
                activity_type="candidate_moved",
                title="Candidato Movido no Pipeline",
                description=f"Candidato movido de '{from_stage}' para '{to_stage}'.",
                actor_id="system",
                actor_name="LIA Platform Events",
                actor_type="system",
                target_id=candidate_id,
                target_type="candidate",
                extra_data={
                    "company_id": company_id,
                    "vacancy_id": vacancy_id,
                    "from_stage": from_stage,
                    "to_stage": to_stage,
                    "event_id": event.event_id,
                },
                category="pipeline",
            )
        except Exception as exc:
            logger.warning("[EventHandler] Failed to create activity for candidate_moved: %s", exc)
    except Exception as exc:
        logger.error("[EventHandler] handle_candidate_moved error: %s", exc)
    finally:
        await db.close()


async def handle_company_configured(event: PlatformEvent) -> None:
    """
    Quando empresa completa onboarding (api-onboarding), inicializar pipeline padrão.

    Responsabilidades:
    - Criar pipeline padrão com estágios pré-configurados
    - Criar policy de hiring padrão
    - Registrar atividade
    """
    company_id = event.company_id
    company_name = event.payload.get("company_name", "")
    logger.info("[EventHandler] company.configured company=%s", company_id)

    db = await _get_db()
    try:
        from app.domains.recruiter_assistant.services.pipeline_stage_service import (
            PipelineStageService,
        )

        svc = PipelineStageService()
        created_stages = await svc.initialize_company_stages(company_id, db=db)
        stages_count = len(created_stages) if created_stages else 0
        logger.info(
            "[EventHandler] Initialized %d default stages for company %s",
            stages_count,
            company_id,
        )

        try:
            from app.models.company_hiring_policy import CompanyHiringPolicy

            existing = await db.execute(
                select(CompanyHiringPolicy).where(
                    CompanyHiringPolicy.company_id == company_id
                )
            )
            if not existing.scalar_one_or_none():
                policy = CompanyHiringPolicy(company_id=company_id)
                db.add(policy)
                await db.commit()
                logger.info("[EventHandler] Created default hiring policy for company %s", company_id)
        except ImportError:
            logger.debug("[EventHandler] CompanyHiringPolicy model not available")
        except Exception as exc:
            logger.warning("[EventHandler] Failed to create default hiring policy: %s", exc)
            try:
                await db.rollback()
            except Exception:
                pass

        try:
            from app.services.activity_service import ActivityService

            activity_svc = ActivityService()
            await activity_svc.create_activity(
                activity_type="company_configured",
                title="Empresa Configurada",
                description=(
                    f"Empresa '{company_name}' configurada com sucesso. "
                    f"{stages_count} estágios de pipeline criados."
                ),
                actor_id="system",
                actor_name="LIA Platform Events",
                actor_type="system",
                target_id=company_id,
                target_type="company",
                extra_data={
                    "company_id": company_id,
                    "company_name": company_name,
                    "stages_created": stages_count,
                    "event_id": event.event_id,
                },
                category="onboarding",
            )
        except Exception as exc:
            logger.warning("[EventHandler] Failed to create activity for company_configured: %s", exc)
    except Exception as exc:
        logger.error("[EventHandler] handle_company_configured error: %s", exc)
    finally:
        await db.close()


async def handle_screening_completed_event(event: PlatformEvent) -> None:
    """
    Quando triagem WSI é concluída, avaliar resultado e decidir próximo passo.

    Usa WSI_CUTOFFS para decisão automática:
      - wsi_final >= 3.75 → auto-advance (se auto_stage_advance habilitado)
      - 3.00 <= wsi_final < 3.75 → review (mantém para revisão humana)
      - wsi_final < 3.00 → auto-reject (se auto_screening habilitado)

    Sempre gera feedback humanizado via WSIFeedbackGenerator.
    """
    candidate_id = event.payload.get("candidate_id")
    vacancy_id = event.payload.get("vacancy_id")
    wsi_scores = event.payload.get("wsi_scores", {})
    company_id = event.company_id

    try:
        wsi_final = float(event.payload.get("wsi_final_score", 0.0))
    except (TypeError, ValueError):
        logger.warning("[EventHandler] screening.completed invalid wsi_final_score, defaulting to 0.0")
        wsi_final = 0.0

    logger.info(
        "[EventHandler] screening.completed candidate=%s wsi=%.2f company=%s",
        candidate_id,
        wsi_final,
        company_id,
    )

    if not candidate_id or not vacancy_id:
        logger.warning("[EventHandler] screening.completed missing candidate_id or vacancy_id")
        return

    db = await _get_db()
    try:
        from app.domains.automation.services.automation_handlers import (
            validate_multi_tenancy,
        )

        is_valid, error_msg = await validate_multi_tenancy(
            db=db,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            company_id=company_id,
        )
        if not is_valid:
            logger.warning(
                "[EventHandler] Tenant validation failed for screening.completed: %s",
                error_msg,
            )
            return

        from app.domains.cv_screening.services.wsi_deterministic_scorer import WSI_CUTOFFS

        approved_threshold = WSI_CUTOFFS["approved_auto"]
        review_threshold = WSI_CUTOFFS["review_min"]

        if wsi_final >= approved_threshold:
            decision = "approved"
        elif wsi_final >= review_threshold:
            decision = "review"
        else:
            decision = "rejected"

        auto_advance = False
        auto_reject = False

        try:
            from app.models.company_hiring_policy import CompanyHiringPolicy

            policy_result = await db.execute(
                select(CompanyHiringPolicy).where(
                    CompanyHiringPolicy.company_id == company_id
                )
            )
            policy = policy_result.scalar_one_or_none()

            if policy and policy.automation_rules:
                auto_advance = policy.automation_rules.get("auto_stage_advance", False)
                auto_reject = policy.automation_rules.get("auto_screening", False)
        except ImportError:
            logger.debug("[EventHandler] CompanyHiringPolicy model not available")
        except Exception as exc:
            logger.warning("[EventHandler] Failed to check automation rules: %s", exc)

        from app.domains.automation.services.automation_handlers import (
            handle_screening_completed,
        )

        if decision == "approved" and auto_advance:
            await handle_screening_completed(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                company_id=company_id,
                db=db,
                wsi_scores=wsi_scores,
                passed=True,
            )

            try:
                from app.domains.recruiter_assistant.services.pipeline_stage_service import (
                    PipelineStageService,
                )
                from app.models.candidate import VacancyCandidate

                vc_result = await db.execute(
                    select(VacancyCandidate).where(
                        VacancyCandidate.candidate_id == candidate_id,
                        VacancyCandidate.vacancy_id == vacancy_id,
                    )
                )
                vc = vc_result.scalar_one_or_none()

                if vc:
                    svc = PipelineStageService()
                    await svc.transition_candidate(
                        vacancy_candidate_id=str(vc.id),
                        to_stage="interview_hr",
                        triggered_by="automation",
                        reason=f"WSI auto-advance: score {wsi_final:.2f} >= {approved_threshold}",
                        context={"company_id": company_id},
                        db=db,
                    )
                    logger.info(
                        "[EventHandler] Auto-advanced candidate %s to interview_hr (WSI=%.2f)",
                        candidate_id,
                        wsi_final,
                    )
            except Exception as exc:
                logger.warning("[EventHandler] Auto-advance failed: %s", exc)

        elif decision == "rejected" and auto_reject:
            await handle_screening_completed(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                company_id=company_id,
                db=db,
                wsi_scores=wsi_scores,
                passed=False,
            )
            logger.info(
                "[EventHandler] Auto-rejected candidate %s (WSI=%.2f < %.2f)",
                candidate_id,
                wsi_final,
                review_threshold,
            )

        else:
            await handle_screening_completed(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                company_id=company_id,
                db=db,
                wsi_scores=wsi_scores,
                passed=(decision != "rejected"),
            )
            logger.info(
                "[EventHandler] Screening result=%s for candidate %s (WSI=%.2f, auto_advance=%s)",
                decision,
                candidate_id,
                wsi_final,
                auto_advance,
            )

        try:
            from app.services.activity_service import ActivityService

            activity_svc = ActivityService()
            await activity_svc.create_activity(
                activity_type="screening_completed",
                title="Triagem WSI Concluída",
                description=(
                    f"Triagem concluída com decisão '{decision}'. "
                    f"WSI Score: {wsi_final:.2f}."
                ),
                actor_id="system",
                actor_name="LIA Platform Events",
                actor_type="system",
                target_id=candidate_id,
                target_type="candidate",
                extra_data={
                    "company_id": company_id,
                    "vacancy_id": vacancy_id,
                    "wsi_final_score": wsi_final,
                    "decision": decision,
                    "auto_advance": auto_advance,
                    "auto_reject": auto_reject,
                    "event_id": event.event_id,
                },
                category="screening",
            )
        except Exception as exc:
            logger.warning("[EventHandler] Failed to create activity for screening: %s", exc)
    except Exception as exc:
        logger.error("[EventHandler] handle_screening_completed_event error: %s", exc)
    finally:
        await db.close()


def register_all_handlers() -> None:
    """
    Registra todos os event handlers para eventos inter-API.

    Chamado no startup da aplicação (app/main.py lifespan).
    Idempotente: se chamado múltiplas vezes, duplica os handlers —
    use apenas no startup.
    """
    register_event_handler("vagas.job.published", handle_job_published)
    register_event_handler("vagas.job.closed", handle_job_closed)
    register_event_handler("funil.candidate.moved", handle_candidate_moved)
    register_event_handler("onboarding.company.configured", handle_company_configured)
    register_event_handler("screening.wsi.completed", handle_screening_completed_event)
    logger.info(
        "[PlatformEvents] All event handlers registered: %s",
        [
            "vagas.job.published",
            "vagas.job.closed",
            "funil.candidate.moved",
            "onboarding.company.configured",
            "screening.wsi.completed",
        ],
    )
