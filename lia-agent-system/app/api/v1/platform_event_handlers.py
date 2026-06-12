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
from app.domains.analytics.services.activity_service import get_activity_service, ActivityService
from app.domains.recruiter_assistant.services.pipeline_stage_service import get_pipeline_stage_service, PipelineStageService

logger = logging.getLogger(__name__)


async def _get_db() -> AsyncSession:
    return AsyncSessionLocal()


async def _create_activity(
    activity_type: str,
    title: str,
    description: str,
    target_id: str,
    target_type: str,
    extra_data: dict,
    category: str,
    priority: str = "normal",
) -> None:
    try:
        svc = get_activity_service()
        await svc.create_activity(
            activity_type=activity_type,
            title=title,
            description=description,
            actor_id="system",
            actor_name="LIA Platform Events",
            actor_type="system",
            target_id=target_id,
            target_type=target_type,
            extra_data=extra_data,
            category=category,
            priority=priority,
        )
    except Exception as exc:
        logger.warning("[EventHandler] Failed to create activity '%s': %s", activity_type, exc)


async def _get_vacancy_candidate(
    db: AsyncSession,
    candidate_id: str,
    vacancy_id: str,
    company_id: str | None = None,
):
    """Get VacancyCandidate for (candidate, vacancy) pair.

    Multi-tenancy defense-in-depth via company_id filter quando passado
    (REGRA ZERO + harness B.1). Backwards-compat: callers legados em
    handlers podem omitir; Postgres RLS guarda.
    """
    from app.models.candidate import VacancyCandidate

    # TENANT-EXEMPT: dynamic builder — VacancyCandidate.company_id == company_id
    # é appended conditionally below quando company_id passado.
    query = select(VacancyCandidate).where(
        VacancyCandidate.candidate_id == candidate_id,
        VacancyCandidate.vacancy_id == vacancy_id,
    )
    if company_id:
        query = query.where(VacancyCandidate.company_id == company_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def _record_jd_if_enabled(
    db: AsyncSession,
    company_id: str,
    job_id: str,
    title: str,
    jd_enriched: dict | None,
    department: str | None,
    seniority_level: str | None,
) -> None:
    """Sprint B Phase 1 wiring (gap W2): thin adapter that delegates to
    JdSimilarService.record_jd_if_enabled.

    P1-1 refactor (post-audit): the toggle/policy lookup + service
    composition logic moved into JdSimilarService.record_jd_if_enabled
    so any caller (event handlers, graph nodes, future webhooks) gets
    the same behavior. This adapter only wires the FastAPI session into
    the service and swallows any escaping exception (fail-soft) so a
    missing JD record never breaks the publish pipeline.
    """
    try:
        from app.domains.job_creation.repositories.jd_similar_history_repository import (
            JdSimilarHistoryRepository,
        )
        from app.domains.job_creation.services.jd_similar_service import (
            JdSimilarService,
        )
        from app.shared.intelligence.embedding_service import EmbeddingService

        repo = JdSimilarHistoryRepository(db)
        svc = JdSimilarService(repository=repo, embedding_service=EmbeddingService())
        attempted = await svc.record_jd_if_enabled(
            company_id=company_id,
            job_id=job_id or "",
            title=title,
            jd_enriched=jd_enriched,
            seniority_level=seniority_level,
            department=department,
        )
        if attempted:
            logger.info(
                "[EventHandler] JD recorded in similarity history "
                "company=%s job_id=%s",
                company_id, job_id,
            )
    except Exception as exc:
        # Fail-soft: never break the publish handler over a learning-loop write
        logger.warning(
            "[EventHandler] record_jd failed (fail-soft) company=%s job_id=%s: %s",
            company_id, job_id, str(exc)[:200],
        )


async def handle_job_published(event: PlatformEvent) -> None:
    """
    Quando uma vaga é publicada (api-vagas), preparar estrutura de pipeline.

    Responsabilidades:
    - Garantir que a empresa tem os estágios do pipeline inicializados
    - Notificar recrutadores responsáveis (atividade de alta prioridade)
    - Registrar atividade no log de auditoria
    """
    job_id = event.payload.get("job_id")
    company_id = event.company_id
    job_title = event.payload.get("title", "")
    recruiter_ids = event.payload.get("recruiter_ids", [])
    logger.info(
        "[EventHandler] job.published job_id=%s company=%s",
        job_id,
        company_id,
    )

    db = await _get_db()
    try:
        svc = get_pipeline_stage_service()
        await svc.initialize_company_stages(company_id, db=db)
        logger.info(
            "[EventHandler] Pipeline stages ensured for company=%s job_id=%s",
            company_id,
            job_id,
        )

        await _create_activity(
            activity_type="job_published",
            title="Vaga Publicada",
            description=f"Vaga '{job_title}' publicada e pipeline inicializado.",
            target_id=job_id or "",
            target_type="job",
            extra_data={
                "company_id": company_id,
                "job_title": job_title,
                "recruiter_ids": recruiter_ids,
                "event_id": event.event_id,
            },
            category="automation",
            priority="high",
        )

        if recruiter_ids:
            for recruiter_id in recruiter_ids:
                await _create_activity(
                    activity_type="recruiter_notification",
                    title="Nova Vaga Atribuída",
                    description=(
                        f"Você foi designado como recrutador para a vaga '{job_title}'. "
                        f"O pipeline está pronto para receber candidatos."
                    ),
                    target_id=job_id or "",
                    target_type="job",
                    extra_data={
                        "company_id": company_id,
                        "job_title": job_title,
                        "recruiter_id": recruiter_id,
                    },
                    category="notification",
                    priority="high",
                )

        # Sprint B Phase 1 wiring (gap W2): persist JD in similarity history
        # so future jobs can suggest reuse. Internally fail-soft.
        await _record_jd_if_enabled(
            db=db,
            company_id=company_id,
            job_id=job_id or "",
            title=job_title,
            jd_enriched=event.payload.get("jd_enriched"),
            department=event.payload.get("department"),
            seniority_level=event.payload.get("seniority_level"),
        )
    except Exception as exc:
        logger.error("[EventHandler] handle_job_published error: %s", exc)
    finally:
        await db.close()


async def handle_job_closed(event: PlatformEvent) -> None:
    """
    Quando uma vaga é encerrada (api-vagas), arquivar candidatos em aberto.

    Responsabilidades:
    - Marcar candidatos pendentes como 'withdrawn' (vaga encerrada)
    - Persistir DB state ANTES de enviar comunicações externas
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

        terminal_statuses = ("rejected", "hired", "cancelled", "not_selected")
        # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
        open_candidates_result = await db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == vacancy.id,
                VacancyCandidate.status.notin_(terminal_statuses),
                VacancyCandidate.company_id == company_id,
            )
        )
        open_candidates = open_candidates_result.scalars().all()

        archived_count = 0
        candidates_to_notify: list[tuple[str, str, str | None]] = []

        for vc in open_candidates:
            vc.previous_status = vc.status
            vc.status = "cancelled"
            vc.notes = (vc.notes or "") + f"\n[{datetime.now(UTC).isoformat()}] Vaga encerrada: {reason}"
            vc.updated_at = datetime.now(UTC)
            archived_count += 1

            try:
                # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
                candidate_result = await db.execute(
                    select(Candidate).where(
                        Candidate.id == vc.candidate_id,
                        Candidate.company_id == company_id,
                    )
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
        logger.info(
            "[EventHandler] job.closed committed %d candidates as withdrawn for job_id=%s",
            archived_count,
            job_id,
        )

        feedback_sent = 0
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

        await _create_activity(
            activity_type="job_closed",
            title="Vaga Encerrada",
            description=(
                f"Vaga '{vacancy.title}' encerrada. "
                f"{archived_count} candidatos arquivados, "
                f"{feedback_sent} notificados."
            ),
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
        logger.error("[EventHandler] handle_job_closed error: %s", exc)
        try:
            await db.rollback()
        except Exception:
            pass
    finally:
        await db.close()


async def handle_candidate_moved(event: PlatformEvent) -> None:
    """
    Quando um candidato muda de estágio (api-funil), disparar automações e
    registrar métricas de velocidade.

    Responsabilidades:
    - Atualizar stage_entered_at via velocity tracking
    - Disparar automações configuradas para o estágio destino
    - Registrar atividade de transição
    """
    candidate_id = event.payload.get("candidate_id")
    vacancy_id = event.payload.get("vacancy_id")
    vacancy_candidate_id = event.payload.get("vacancy_candidate_id")
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
        if from_stage and from_stage != to_stage and vacancy_candidate_id:
            try:
                from app.models.candidate import VacancyCandidate

                vc = await db.get(VacancyCandidate, vacancy_candidate_id)
                if vc and vc.company_id == company_id:
                    if vc.stage_entered_at:
                        time_in_stage_hours = (
                            datetime.now(UTC) - vc.stage_entered_at.replace(tzinfo=UTC)
                        ).total_seconds() / 3600
                        logger.info(
                            "[EventHandler] Velocity: candidate %s spent %.1fh in stage '%s'",
                            candidate_id,
                            time_in_stage_hours,
                            from_stage,
                        )
                    else:
                        logger.info(
                            "[EventHandler] Velocity: no stage_entered_at for candidate %s stage '%s'",
                            candidate_id,
                            from_stage,
                        )
            except Exception as exc:
                logger.warning("[EventHandler] Velocity tracking error: %s", exc)

        try:
            from app.domains.automation.services.stage_automation_engine import (
                AutomationEvent,
                TriggerType,
                stage_automation_engine,
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

            await stage_automation_engine.process_event(automation_event, db=db)
            logger.info(
                "[EventHandler] Stage automation processed for candidate %s → %s",
                candidate_id,
                to_stage,
            )
        except ImportError:
            logger.debug("[EventHandler] stage_automation_engine not available")
        except Exception as exc:
            logger.warning("[EventHandler] Stage automation error: %s", exc)

        await _create_activity(
            activity_type="candidate_moved",
            title="Candidato Movido no Pipeline",
            description=f"Candidato movido de '{from_stage}' para '{to_stage}'.",
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
        logger.error("[EventHandler] handle_candidate_moved error: %s", exc)
    finally:
        await db.close()


async def handle_company_configured(event: PlatformEvent) -> None:
    """
    Quando empresa completa onboarding (api-onboarding), inicializar tudo.

    Responsabilidades:
    - Criar pipeline padrão com estágios pré-configurados
    - Criar policy de hiring padrão
    - Semear templates de comunicação padrão (email/whatsapp)
    - Registrar atividade
    """
    company_id = event.company_id
    company_name = event.payload.get("company_name", "")
    logger.info("[EventHandler] company.configured company=%s", company_id)

    db = await _get_db()
    try:
        svc = get_pipeline_stage_service()
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

        templates_seeded = 0
        try:
            from app.domains.job_management.services.template_seeder import (
                seed_default_templates,
            )

            seed_result = await seed_default_templates(db)
            templates_seeded = seed_result.get("created_count", 0)
            logger.info(
                "[EventHandler] Seeded %d system-wide communication templates",
                templates_seeded,
            )
        except ImportError:
            logger.debug("[EventHandler] template_seeder not available")
        except Exception as exc:
            logger.warning("[EventHandler] Failed to seed system templates: %s", exc)

        email_templates_seeded = 0
        try:
            from app.domains.job_management.services.recruitment_email_templates import (
                seed_default_templates as seed_email_templates,
            )

            email_result = await seed_email_templates(db, company_id=company_id)
            email_templates_seeded = len(email_result) if email_result else 0
            logger.info(
                "[EventHandler] Seeded %d recruitment email templates for company %s",
                email_templates_seeded,
                company_id,
            )
        except ImportError:
            logger.debug("[EventHandler] recruitment_email_templates not available")
        except Exception as exc:
            logger.warning("[EventHandler] Failed to seed email templates: %s", exc)

        await _create_activity(
            activity_type="company_configured",
            title="Empresa Configurada",
            description=(
                f"Empresa '{company_name}' configurada com sucesso. "
                f"{stages_count} estágios de pipeline criados, "
                f"{templates_seeded} templates de comunicação e "
                f"{email_templates_seeded} templates de email semeados."
            ),
            target_id=company_id,
            target_type="company",
            extra_data={
                "company_id": company_id,
                "company_name": company_name,
                "stages_created": stages_count,
                "templates_seeded": templates_seeded,
                "email_templates_seeded": email_templates_seeded,
                "event_id": event.event_id,
            },
            category="onboarding",
        )
    except Exception as exc:
        logger.error("[EventHandler] handle_company_configured error: %s", exc)
    finally:
        await db.close()


async def handle_screening_completed_event(event: PlatformEvent) -> None:
    """
    Quando triagem WSI é concluída, avaliar resultado e decidir próximo passo.

    Usa WSI_CUTOFFS para decisão automática:
      - wsi_final >= 3.75 → auto-advance to interview_hr (se auto_stage_advance)
      - 3.00 <= wsi_final < 3.75 → review (mantém + notifica recrutador)
      - wsi_final < 3.00 → auto-reject (se auto_screening) com feedback humanizado

    Sempre:
      - Valida tenant ownership antes de qualquer side-effect
      - Gera feedback via WSIFeedbackGenerator
      - Notifica recrutador responsável
    """
    candidate_id = event.payload.get("candidate_id")
    vacancy_id = event.payload.get("vacancy_id")
    wsi_scores = event.payload.get("wsi_scores", {})
    response_scores = event.payload.get("response_scores", [])
    job_title = event.payload.get("job_title", "")
    seniority_level = event.payload.get("seniority_level", "pleno")
    candidate_name = event.payload.get("candidate_name", "")
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

        try:
            from app.models.company_hiring_policy import CompanyHiringPolicy

            policy_result = await db.execute(
                select(CompanyHiringPolicy).where(
                    CompanyHiringPolicy.company_id == company_id
                )
            )
            policy = policy_result.scalar_one_or_none()

            if policy and policy.automation_rules:
                from app.shared.policy_helper import coerce_bool
                auto_advance = coerce_bool(policy.automation_rules.get("auto_stage_advance", False))
        except ImportError:
            logger.debug("[EventHandler] CompanyHiringPolicy model not available")
        except Exception as exc:
            logger.warning("[EventHandler] Failed to check automation rules: %s", exc)

        # W2-C: ler auto_approval_preset/limit/paused do screening_config por-vaga.
        # Sobrescreve auto_advance se a vaga atingiu cota ou está pausada.
        _auto_approvals_count = 0
        _auto_approval_limit = None  # None = sem cota por-vaga (só usa global)
        try:
            from app.models.job_vacancy import JobVacancy as _W2C_JV

            _w2c_vac = await db.get(_W2C_JV, vacancy_id)
            if _w2c_vac and _w2c_vac.screening_config:
                _sc_settings = {}
                _sc = _w2c_vac.screening_config
                if isinstance(_sc, dict):
                    _sc_settings = _sc.get("settings", {}) or {}

                # Pausado explicitamente → bloqueia auto-advance para esta vaga
                if _sc_settings.get("auto_approval_paused", False):
                    auto_advance = False
                    logger.info(
                        "[EventHandler] auto_advance BLOCKED: auto_approval_paused=True vaga=%s",
                        vacancy_id,
                    )
                else:
                    # Resolver limite: preset → número canônico (espelha approvalPresetToLimit FE)
                    _preset = _sc_settings.get("auto_approval_preset", "recommended")
                    _PRESET_LIMITS = {"conservative": 5, "recommended": 10, "autonomous": 25}
                    _auto_approval_limit = _sc_settings.get(
                        "auto_approval_limit",
                        _PRESET_LIMITS.get(_preset, 10),
                    )
                    _auto_approvals_count = int(_sc_settings.get("auto_approvals_count", 0) or 0)

                    if _auto_approvals_count >= _auto_approval_limit:
                        auto_advance = False
                        logger.info(
                            "[EventHandler] auto_advance BLOCKED: cota atingida count=%d limit=%d vaga=%s",
                            _auto_approvals_count,
                            _auto_approval_limit,
                            vacancy_id,
                        )
        except Exception as _w2c_exc:
            logger.warning("[EventHandler] W2-C screening_config read error (fail-open): %s", _w2c_exc)


        from app.domains.automation.services.automation_handlers import (
            handle_screening_completed,
        )

        feedback_text = ""
        try:
            from app.domains.cv_screening.services.wsi_feedback_generator import (
                WSIFeedbackGenerator,
            )

            generator = WSIFeedbackGenerator()
            feedback_result = generator.generate(
                response_scores=response_scores,
                job_title=job_title,
                seniority_level=seniority_level,
                candidate_name=candidate_name,
            )
            feedback_text = feedback_result.get("plain_text", "")
            logger.info(
                "[EventHandler] Generated WSI feedback for candidate %s (%d chars)",
                candidate_id,
                len(feedback_text),
            )
        except Exception as exc:
            logger.warning("[EventHandler] WSIFeedbackGenerator error: %s", exc)

        vc = await _get_vacancy_candidate(db, candidate_id, vacancy_id)

        decision_labels = {
            "approved": "Aprovado WSI",
            "review": "Revisão Necessária",
            "rejected": "Reprovado WSI",
        }
        if vc:
            existing_data = vc.additional_data or {}
            existing_data["screening_decision"] = decision
            existing_data["screening_label"] = decision_labels.get(decision, decision)
            existing_data["wsi_final_score"] = wsi_final
            existing_data["screening_completed_at"] = datetime.now(UTC).isoformat()
            vc.additional_data = existing_data
            try:
                await db.flush()
            except Exception as exc:
                logger.warning("[EventHandler] Failed to persist screening badge: %s", exc)

        if decision == "approved" and auto_advance:
            await handle_screening_completed(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                company_id=company_id,
                db=db,
                wsi_scores=wsi_scores,
                passed=True,
            )

            if vc:
                try:
                    svc = get_pipeline_stage_service()
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

                    # W2-C: incrementar auto_approvals_count no JSONB por-vaga (fail-soft).
                    if _auto_approval_limit is not None:
                        try:
                            from app.models.job_vacancy import JobVacancy as _W2C_JV2

                            _w2c_vac2 = await db.get(_W2C_JV2, vacancy_id)
                            if _w2c_vac2 and _w2c_vac2.screening_config:
                                _sc2 = dict(_w2c_vac2.screening_config)
                                _s2 = dict(_sc2.get("settings", {}) or {})
                                _s2["auto_approvals_count"] = _auto_approvals_count + 1
                                _sc2["settings"] = _s2
                                _w2c_vac2.screening_config = _sc2
                                await db.flush()
                                logger.info(
                                    "[EventHandler] auto_approvals_count incremented to %d/%d vaga=%s",
                                    _auto_approvals_count + 1,
                                    _auto_approval_limit,
                                    vacancy_id,
                                )
                        except Exception as _w2c_cnt_exc:
                            logger.warning("[EventHandler] W2-C count increment error (fail-soft): %s", _w2c_cnt_exc)


        elif decision == "rejected":
            await handle_screening_completed(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                company_id=company_id,
                db=db,
                wsi_scores=wsi_scores,
                passed=False,
            )

            if vc and auto_advance:
                try:
                    svc = get_pipeline_stage_service()
                    await svc.transition_candidate(
                        vacancy_candidate_id=str(vc.id),
                        to_stage="rejected",
                        triggered_by="automation",
                        reason=f"WSI auto-reject: score {wsi_final:.2f} < {review_threshold}",
                        context={"company_id": company_id},
                        force=True,
                        db=db,
                    )
                    logger.info(
                        "[EventHandler] Auto-rejected candidate %s (WSI=%.2f < %.2f)",
                        candidate_id,
                        wsi_final,
                        review_threshold,
                    )
                except Exception as exc:
                    logger.warning("[EventHandler] Auto-reject transition failed: %s", exc)

            if feedback_text:
                try:
                    from app.models.candidate import Candidate

                    # Multi-tenancy fail-closed: explicit company_id filter (REGRA ZERO + B.1).
                    cand_result = await db.execute(
                        select(Candidate).where(
                            Candidate.id == candidate_id,
                            Candidate.company_id == company_id,
                        )
                    )
                    candidate = cand_result.scalar_one_or_none()

                    if candidate and candidate.email:
                        from app.domains.communication.services.communication_dispatcher import (

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
# See: app/domains/integrations_hub/services/rails_adapter.py
                            CommunicationDispatcher,
                        )

                        dispatcher = CommunicationDispatcher()
                        await dispatcher.dispatch_message(
                            company_id=company_id,
                            recipient_email=candidate.email,
                            recipient_phone=getattr(candidate, "phone", None),
                            subject=f"Feedback sobre sua candidatura - {job_title}",
                            message=feedback_text,
                            candidate_name=candidate_name or candidate.name,
                        )
                        logger.info(
                            "[EventHandler] Sent WSI rejection feedback to candidate %s",
                            candidate_id,
                        )
                except Exception as exc:
                    logger.warning("[EventHandler] Failed to send rejection feedback: %s", exc)

        else:
            await handle_screening_completed(
                candidate_id=candidate_id,
                vacancy_id=vacancy_id,
                company_id=company_id,
                db=db,
                wsi_scores=wsi_scores,
                passed=True,
            )
            logger.info(
                "[EventHandler] Screening result=%s for candidate %s (WSI=%.2f, auto_advance=%s)",
                decision,
                candidate_id,
                wsi_final,
                auto_advance,
            )

        # W1-H (2026-06-12): dispatch custom feedback_template from screening_config.
        # Fail-soft: erros nao devem abortar processamento do evento principal.
        try:
            from app.models.job_vacancy import JobVacancy as _WH_JV

            _wh_vac = await db.get(_WH_JV, vacancy_id)
            _wh_templates = {}
            if _wh_vac and _wh_vac.screening_config:
                _sc = _wh_vac.screening_config
                if isinstance(_sc, dict):
                    _wh_templates = _sc.get("feedback_templates", {}) or {}

            if _wh_templates and decision != "review":
                _wh_tmpl = _wh_templates.get(decision, "")
                if _wh_tmpl:
                    # Resolve candidate email (multi-tenancy fail-closed)
                    from app.models.candidate import Candidate as _WH_Cand

                    _wh_cand_result = await db.execute(
                        select(_WH_Cand).where(
                            _WH_Cand.id == candidate_id,
                            _WH_Cand.company_id == company_id,
                        )
                    )
                    _wh_cand = _wh_cand_result.scalar_one_or_none()

                    if _wh_cand and _wh_cand.email:
                        from app.domains.communication.services.communication_dispatcher import (
                            CommunicationDispatcher as _WH_CD,
                        )

                        _wh_dispatcher = _WH_CD()
                        await _wh_dispatcher.dispatch_message(
                            company_id=company_id,
                            recipient_email=_wh_cand.email,
                            recipient_phone=getattr(_wh_cand, "phone", None),
                            subject=f"Atualização sobre sua candidatura - {job_title}",
                            message=_wh_tmpl,
                            candidate_name=candidate_name or _wh_cand.name,
                        )
                        logger.info(
                            "[EventHandler] Custom feedback_template dispatched candidate=%s decision=%s",
                            candidate_id,
                            decision,
                        )
        except Exception as _wh_exc:
            logger.warning("[EventHandler] Custom feedback_template dispatch skipped: %s", _wh_exc)

        # A2b (2026-06-10): notifica recrutador via Teams DM ao completar triagem.
        # Fail-soft: erro de entrega Teams nao deve abortar processamento do evento.
        try:
            from app.domains.communication.services.teams_proactivity_engine import (
                teams_proactivity_engine as _tpe,
            )

            await _tpe.on_screening_complete(
                candidate_id=candidate_id,
                candidate_name=candidate_name or "Candidato",
                vacancy_id=vacancy_id,
                job_title=job_title or "",
                match_score=wsi_final,
                recommendation=decision,
                company_id=company_id,
            )
        except Exception as _tpe_exc:
            logger.warning(
                "[EventHandler] teams on_screening_complete skipped: %s", _tpe_exc
            )

        # Fatia 4 — bell notification para o recrutador da vaga (melhor-esforco).
        try:
            from app.models.job_vacancy import JobVacancy as _JV
            _vac = await db.get(_JV, vacancy_id)
            _recruiter_uid = await _find_recruiter_user_id_by_email(
                db,
                getattr(_vac, "recruiter_email", None),
                company_id,
            ) if _vac else None
            if _recruiter_uid:
                from lia_messaging.notification_service import (
                    NotificationService as _NS,
                    NotificationType as _NT,
                )

                _score_str = f"{wsi_final:.1f}" if wsi_final else "–"
                _rec_labels = {
                    "approved": "Aprovado",
                    "review": "Revisão recomendada",
                    "rejected": "Não seguiu",
                }
                await _NS().create_notification(
                    user_id=_recruiter_uid,
                    title=f"Triagem concluída: {candidate_name or 'Candidato'}",
                    message=(
                        f"Vaga: {job_title or 'Vaga'} | "
                        f"Score WSI: {_score_str} | "
                        f"{_rec_labels.get(decision, decision)}"
                    ),
                    notification_type=(
                        _NT.SUCCESS if decision == "approved" else _NT.INFO
                    ),
                    category="screening_completed",
                    source_trigger="screening.wsi.completed",
                    related_job_id=vacancy_id,
                    related_candidate_id=candidate_id,
                    action_url=f"/pt/vagas/{vacancy_id}/candidatos/{candidate_id}",
                    action_label="Ver candidato",
                    channels=["bell"],
                    db=db,
                )
                logger.debug(
                    "[EventHandler] bell sent screening_complete user=%s rec=%s",
                    _recruiter_uid,
                    decision,
                )
        except Exception as _bell_exc:
            logger.debug("[EventHandler] bell screening_complete skipped: %s", _bell_exc)

        decision_labels = {
            "approved": "Aprovado na Triagem WSI",
            "review": "Triagem WSI - Revisão Necessária",
            "rejected": "Reprovado na Triagem WSI",
        }
        await _create_activity(
            activity_type="screening_completed",
            title=decision_labels.get(decision, "Triagem WSI Concluída"),
            description=(
                f"Triagem concluída com decisão '{decision}'. "
                f"WSI Score: {wsi_final:.2f}."
            ),
            target_id=candidate_id,
            target_type="candidate",
            extra_data={
                "company_id": company_id,
                "vacancy_id": vacancy_id,
                "wsi_final_score": wsi_final,
                "decision": decision,
                "auto_advance": auto_advance,
                "auto_stage_advance": auto_advance,
                "event_id": event.event_id,
            },
            category="screening",
            priority="high" if decision in ("approved", "rejected") else "normal",
        )

        await _create_activity(
            activity_type="recruiter_screening_notification",
            title=f"Resultado de Triagem: {decision.upper()}",
            description=(
                f"Candidato '{candidate_name}' recebeu decisão '{decision}' "
                f"na triagem WSI (score: {wsi_final:.2f}). "
                + (
                    "Ação automática executada."
                    if (decision == "approved" and auto_advance)
                    or (decision == "rejected" and auto_advance)
                    else "Requer revisão manual do recrutador."
                )
            ),
            target_id=vacancy_id,
            target_type="job",
            extra_data={
                "company_id": company_id,
                "candidate_id": candidate_id,
                "candidate_name": candidate_name,
                "wsi_final_score": wsi_final,
                "decision": decision,
                "requires_action": decision == "review" or not auto_advance,
            },
            category="notification",
            priority="high",
        )
    except Exception as exc:
        logger.error("[EventHandler] handle_screening_completed_event error: %s", exc)
    finally:
        await db.close()


async def _find_recruiter_user_id_by_email(
    db,
    recruiter_email: str | None,
    company_id: str,
) -> str | None:
    """Localiza o user_id do recrutador pelo email para envio de bell notification.

    Usa email_hash (SHA-256) para lookup seguro sem expor email plaintext.
    Multi-tenancy: filtra por company_id para garantir que o user pertence ao tenant.
    Fail-soft: retorna None em qualquer erro (bell é melhor-esforco).
    """
    if not recruiter_email:
        return None
    try:
        from sqlalchemy import select as _sa_select
        from app.auth.models import User as _User
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash

        email_hash = _sha256_hash(recruiter_email.strip().lower())
        result = await db.execute(
            _sa_select(_User.id).where(
                _User.email_hash == email_hash,
                _User.company_id == company_id,
            ).limit(1)
        )
        row = result.scalar_one_or_none()
        return str(row) if row else None
    except Exception as _exc:
        logger.debug("[EventHandler] _find_recruiter_user_id_by_email failed: %s", _exc)
        return None


async def handle_candidate_applied_teams(event: PlatformEvent) -> None:
    """A2b (2026-06-10): ao receber candidatura, notifica recrutador via Teams DM.

    CandidateAppliedEvent e lean (candidate_id + vacancy_id apenas). Fazemos
    lookup DB para obter name + title antes de chamar o engine.
    Multi-tenancy fail-closed: valida company_id do candidato E da vaga contra
    event.company_id (do JWT do request original) antes de qualquer fan-out.
    Fail-soft + LOUD: erro de entrega Teams e logado mas nao aborta o fluxo.
    """
    candidate_id = event.payload.get("candidate_id")
    vacancy_id = event.payload.get("vacancy_id")
    company_id = event.company_id

    if not candidate_id or not vacancy_id:
        logger.warning(
            "[EventHandler] handle_candidate_applied_teams: missing ids (cid=%s vid=%s), skipping",
            candidate_id,
            vacancy_id,
        )
        return

    db = await _get_db()
    try:
        from app.models.candidate import Candidate
        from app.models.job_vacancy import JobVacancy

        cand = await db.get(Candidate, candidate_id)
        vac = await db.get(JobVacancy, vacancy_id)

        # Multi-tenancy: ambos devem pertencer ao tenant do evento.
        if not cand or str(cand.company_id) != company_id:
            logger.warning(
                "[EventHandler] handle_candidate_applied_teams: candidate tenant mismatch"
                " (expected company=%s), skipping",
                company_id,
            )
            return
        if not vac or str(vac.company_id) != company_id:
            logger.warning(
                "[EventHandler] handle_candidate_applied_teams: vacancy tenant mismatch"
                " (expected company=%s), skipping",
                company_id,
            )
            return

        from app.domains.communication.services.teams_proactivity_engine import (
            teams_proactivity_engine,
        )

        await teams_proactivity_engine.on_candidate_applied(
            candidate_id=candidate_id,
            candidate_name=cand.name or "Candidato",
            vacancy_id=vacancy_id,
            vacancy_title=vac.title or "Vaga",
            company_id=company_id,
        )
        logger.info(
            "[EventHandler] handle_candidate_applied_teams OK candidate=%s vacancy=%s",
            candidate_id,
            vacancy_id,
        )
        # Fatia 4 — bell notification para o recrutador da vaga (melhor-esforco).
        try:
            _recruiter_uid = await _find_recruiter_user_id_by_email(
                db,
                getattr(vac, "recruiter_email", None),
                company_id,
            )
            if _recruiter_uid:
                from lia_messaging.notification_service import (
                    NotificationService as _NS,
                    NotificationType as _NT,
                )

                await _NS().create_notification(
                    user_id=_recruiter_uid,
                    title=f"Nova candidatura: {cand.name or 'Candidato'}",
                    message=f'Candidatura na vaga {vac.title or "Vaga"}',
                    notification_type=_NT.INFO,
                    category="new_application",
                    source_trigger="candidate_applied",
                    related_job_id=vacancy_id,
                    related_candidate_id=candidate_id,
                    action_url=f"/pt/vagas/{vacancy_id}/candidatos",
                    action_label="Ver candidatos",
                    channels=["bell"],
                    db=db,
                )
                logger.debug(
                    "[EventHandler] bell sent candidate_applied user=%s", _recruiter_uid
                )
        except Exception as _bell_exc:
            logger.debug("[EventHandler] bell candidate_applied skipped: %s", _bell_exc)
    except Exception as exc:
        logger.warning("[EventHandler] handle_candidate_applied_teams error: %s", exc)
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
    register_event_handler("candidate_applied", handle_candidate_applied_teams)  # A2b
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
