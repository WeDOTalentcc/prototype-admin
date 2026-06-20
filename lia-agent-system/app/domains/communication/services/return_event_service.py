"""
Return Event Service - Processes candidate return events for pipeline transitions.
Phase 5: Automatic Candidate Return.
"""
import enum
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.activity_feed import ActivityFeed
from lia_models.candidate import Candidate, VacancyCandidate
from app.services.notification_service import notification_service
from app.domains.recruiter_assistant.services.pipeline_stage_service import pipeline_stage_service

logger = logging.getLogger(__name__)


class ReturnEventType(enum.StrEnum):
    SCREENING_COMPLETE = "screening_complete"
    SCREENING_EXPIRED = "screening_expired"
    INTERVIEW_CONFIRMED = "interview_confirmed"
    INTERVIEW_DECLINED = "interview_declined"
    INTERVIEW_COMPLETED = "interview_completed"
    INTERVIEW_NO_SHOW = "interview_no_show"
    TEST_SUBMITTED = "test_submitted"
    TEST_EXPIRED = "test_expired"
    DOCUMENTS_RECEIVED = "documents_received"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"


RETURN_EVENT_CONFIG: dict[str, dict[str, Any]] = {
    "screening_complete": {
        "sub_status": "triagem_completa",
        "stage": None,
        "priority": "normal",
        "notification_type": "success",
        "title_template": "{candidate_name} completou a triagem WSI",
        "description_template": "O candidato {candidate_name} finalizou todas as etapas da triagem WSI e está pronto para avaliação.",
        "category": "screening",
        "action_label": "Ver Resultado da Triagem",
    },
    "screening_expired": {
        "sub_status": "triagem_expirada",
        "stage": None,
        "priority": "normal",
        "notification_type": "warning",
        "title_template": "{candidate_name} — triagem WSI expirou",
        "description_template": "O prazo da triagem WSI para {candidate_name} expirou sem conclusão.",
        "category": "screening",
        "action_label": "Reenviar Triagem",
    },
    "interview_confirmed": {
        "sub_status": "confirmada",
        "stage": None,
        "priority": "normal",
        "notification_type": "success",
        "title_template": "{candidate_name} confirmou a entrevista",
        "description_template": "O candidato {candidate_name} confirmou presença na entrevista agendada.",
        "category": "interview",
        "action_label": "Ver Detalhes da Entrevista",
    },
    "interview_declined": {
        "sub_status": "candidato_recusou",
        "stage": None,
        "priority": "normal",
        "notification_type": "warning",
        "title_template": "{candidate_name} recusou a entrevista",
        "description_template": "O candidato {candidate_name} recusou o convite para entrevista.",
        "category": "interview",
        "action_label": "Ver Candidato",
    },
    "interview_completed": {
        "sub_status": "realizada",
        "stage": None,
        "priority": "normal",
        "notification_type": "info",
        "title_template": "{candidate_name} — entrevista realizada",
        "description_template": "A entrevista com {candidate_name} foi concluída com sucesso.",
        "category": "interview",
        "action_label": "Registrar Feedback",
    },
    "interview_no_show": {
        "sub_status": "no_show",
        "stage": None,
        "priority": "normal",
        "notification_type": "warning",
        "title_template": "{candidate_name} não compareceu à entrevista",
        "description_template": "O candidato {candidate_name} não compareceu à entrevista agendada.",
        "category": "interview",
        "action_label": "Ver Candidato",
    },
    "test_submitted": {
        "sub_status": "concluido",
        "stage": None,
        "priority": "normal",
        "notification_type": "success",
        "title_template": "{candidate_name} enviou o teste técnico",
        "description_template": "O candidato {candidate_name} concluiu e enviou o teste técnico para avaliação.",
        "category": "evaluation",
        "action_label": "Avaliar Teste",
    },
    "test_expired": {
        "sub_status": "expirado",
        "stage": None,
        "priority": "normal",
        "notification_type": "warning",
        "title_template": "{candidate_name} — prazo do teste expirou",
        "description_template": "O prazo para envio do teste técnico de {candidate_name} expirou.",
        "category": "evaluation",
        "action_label": "Ver Candidato",
    },
    "documents_received": {
        "sub_status": "documentos_recebidos",
        "stage": None,
        "priority": "normal",
        "notification_type": "success",
        "title_template": "{candidate_name} enviou os documentos solicitados",
        "description_template": "O candidato {candidate_name} enviou os documentos solicitados para verificação.",
        "category": "verification",
        "action_label": "Verificar Documentos",
    },
    "offer_accepted": {
        "sub_status": "aceita",
        "stage": "hired",
        "priority": "urgent",
        "notification_type": "success",
        "title_template": "{candidate_name} aceitou a proposta!",
        "description_template": "O candidato {candidate_name} aceitou a proposta de emprego. Movido automaticamente para a etapa de contratação.",
        "category": "offer",
        "action_label": "Iniciar Onboarding",
    },
    "offer_declined": {
        "sub_status": "recusada",
        "stage": "offer_declined",
        "priority": "normal",
        "notification_type": "warning",
        "title_template": "{candidate_name} recusou a proposta",
        "description_template": "O candidato {candidate_name} recusou a proposta de emprego.",
        "category": "offer",
        "action_label": "Ver Candidato",
    },
}


class ReturnEventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_event(
        self,
        vacancy_candidate_id: str,
        event_type: str,
        metadata: dict[str, Any] | None = None,
        triggered_by: str | None = None,
    ) -> dict[str, Any]:
        """
        Process a candidate return event.

        Returns:
            {
                "success": bool,
                "event_type": str,
                "new_sub_status": str,
                "new_stage": str | None,
                "activity_id": str,
                "notification_sent": bool,
                "error": str | None,
            }
        """
        try:
            if event_type not in RETURN_EVENT_CONFIG:
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.warning(f"Unknown return event type: {event_type}")
                return {
                    "success": False,
                    "event_type": event_type,
                    "new_sub_status": None,
                    "new_stage": None,
                    "activity_id": None,
                    "notification_sent": False,
                    "error": f"Unknown event type: {event_type}",
                }

            event_config = RETURN_EVENT_CONFIG[event_type]

            candidate_data = await self._load_candidate_data(vacancy_candidate_id)
            if not candidate_data:
                logger.error(
                    f"Could not load candidate data for vacancy_candidate_id={vacancy_candidate_id}"
                )
                return {
                    "success": False,
                    "event_type": event_type,
                    "new_sub_status": None,
                    "new_stage": None,
                    "activity_id": None,
                    "notification_sent": False,
                    "error": f"VacancyCandidate not found: {vacancy_candidate_id}",
                }

            sub_status = event_config["sub_status"]
            new_stage = event_config.get("stage")

            updated = await self._update_candidate_status(
                vacancy_candidate_id, sub_status, new_stage,
                triggered_by=triggered_by,
            )
            if not updated:
                logger.error(
                    f"Failed to update status for vacancy_candidate_id={vacancy_candidate_id}"
                )
                return {
                    "success": False,
                    "event_type": event_type,
                    "new_sub_status": sub_status,
                    "new_stage": new_stage,
                    "activity_id": None,
                    "notification_sent": False,
                    "error": "Failed to update candidate status in database",
                }

            logger.info(
                f"Return event '{event_type}' processed: "
                f"vacancy_candidate={vacancy_candidate_id}, "
                f"sub_status={sub_status}, stage={new_stage}"
            )

            activity_id = await self._create_activity(
                event_config, candidate_data, vacancy_candidate_id, event_type, metadata, triggered_by
            )

            notification_sent = await self._notify_recruiter(
                event_config, candidate_data, vacancy_candidate_id, event_type, metadata
            )

            return {
                "success": True,
                "event_type": event_type,
                "new_sub_status": sub_status,
                "new_stage": new_stage,
                "activity_id": activity_id,
                "notification_sent": notification_sent,
                "error": None,
            }

        except Exception as e:
            logger.error(
                f"Unexpected error processing return event '{event_type}' "
                f"for vacancy_candidate_id={vacancy_candidate_id}: {e}",
                exc_info=True,
            )
            return {
                "success": False,
                "event_type": event_type,
                "new_sub_status": None,
                "new_stage": None,
                "activity_id": None,
                "notification_sent": False,
                "error": str(e),
            }

    async def _load_candidate_data(
        self, vacancy_candidate_id: str
    ) -> dict[str, Any] | None:
        """Load VacancyCandidate and associated Candidate data."""
        try:
            # ADR-001-EXEMPT: cross-domain VacancyCandidate/Candidate single-PK reads.
            # ScreeningRepository.get_vacancy_candidate requires (vacancy_id,candidate_id) tuple
            # while this flow only has vacancy_candidate_id PK. Sprint 6 follow-up: extend
            # screening repo with get_vacancy_candidate_by_id(vc_id) + reuse get_candidate_by_id.
            vc_result = await self.db.execute(
                select(VacancyCandidate).where(
                    VacancyCandidate.id == vacancy_candidate_id
                )
            )
            vc = vc_result.scalars().first()
            if not vc:
                logger.warning(f"VacancyCandidate not found: {vacancy_candidate_id}")
                return None

            # Multi-tenancy fail-closed: scope candidate lookup to vc.company_id
            # (defense-in-depth on top of Postgres RLS — Task #1143).
            candidate_result = await self.db.execute(
                select(Candidate).where(
                    Candidate.id == vc.candidate_id,
                    Candidate.company_id == vc.company_id,
                )
            )
            candidate = candidate_result.scalars().first()
            if not candidate:
                logger.warning(f"Candidate not found: {vc.candidate_id}")
                return None

            return {
                "vacancy_candidate_id": str(vc.id),
                "vacancy_id": str(vc.vacancy_id),
                "candidate_id": str(candidate.id),
                "candidate_name": candidate.name or "",  # type: ignore[truthy-bool]
                "candidate_email": candidate.email or "",  # type: ignore[truthy-bool]
                "stage": vc.stage or "",  # type: ignore[truthy-bool]
                "status": vc.status or "",  # type: ignore[truthy-bool]
                "company_id": vc.company_id or None,  # type: ignore[truthy-bool]
                "added_by": vc.added_by or "",  # type: ignore[truthy-bool]
            }

        except Exception as e:
            logger.error(f"Error loading candidate data: {e}", exc_info=True)
            return None

    async def _update_candidate_status(
        self,
        vacancy_candidate_id: str,
        sub_status: str,
        stage: str | None = None,
        triggered_by: str | None = None,
    ) -> bool:
        """Update VacancyCandidate status and optionally stage.

        Item11 SEV1 FIX (P-GUARD): when the event moves the candidate to a
        new stage, route through pipeline_stage_service.transition_candidate()
        instead of raw sa_update(VacancyCandidate). This ensures:
          - Fairness gate fires for rejection stages
          - STAGE_CHANGED event is published
          - AuditService.log_decision is written
          - Candidate history entry is created
        For events with stage=None (sub_status only), sa_update is still used
        because no stage transition occurs.
        """
        try:
            if stage is not None:
                # P-GUARD: route through canonical transition service.
                # transition_candidate resolves company_id from the VacancyCandidate
                # record (no cross-tenant risk) and enforces FSM + fairness gate.
                transition_result = await pipeline_stage_service.transition_candidate(
                    vacancy_candidate_id=vacancy_candidate_id,
                    to_stage=stage,
                    to_sub_status=sub_status,
                    triggered_by=triggered_by or "return_event_service",
                    source_agent="return_event_service",
                    db=self.db,
                )
                success = transition_result.get("success", False)
                if not success:
                    logger.warning(
                        "[ReturnEventService] transition_candidate failure: vc=%s stage=%s result=%s",
                        vacancy_candidate_id, stage, transition_result,
                    )
                    return False
                logger.info(
                    "[ReturnEventService] transition_candidate succeeded: vc=%s stage=%s sub=%s",
                    vacancy_candidate_id, stage, sub_status,
                )
                return True

            # No stage change: sub_status update only (sa_update acceptable here).
            values: dict[str, Any] = {
                "status": sub_status,
                "updated_at": datetime.utcnow(),
            }
            stmt = (
                sa_update(VacancyCandidate)
                .where(VacancyCandidate.id == vacancy_candidate_id)
                .values(**values)
            )
            result = await self.db.execute(stmt)
            await self.db.commit()

            if getattr(result, 'rowcount', 0) == 0:  # type: ignore[union-attr]
                logger.warning(
                    "[ReturnEventService] No rows updated for vc=%s",
                    vacancy_candidate_id,
                )
                return False

            logger.info(
                "[ReturnEventService] Sub-status updated: vc=%s sub_status=%s",
                vacancy_candidate_id, sub_status,
            )
            return True

        except Exception as e:
            logger.error(
                "[ReturnEventService] Error updating candidate status: %s", e, exc_info=True
            )
            try:
                await self.db.rollback()
            except Exception:
                pass
            return False

    async def _create_activity(
        self,
        event_config: dict[str, Any],
        candidate_data: dict[str, Any],
        vacancy_candidate_id: str,
        event_type: str,
        metadata: dict[str, Any] | None = None,
        triggered_by: str | None = None,
    ) -> str | None:
        """Create ActivityFeed entry and return its ID."""
        try:
            candidate_name = candidate_data.get("candidate_name", "")
            title = event_config["title_template"].format(
                candidate_name=candidate_name
            )
            description = event_config.get("description_template", "").format(
                candidate_name=candidate_name
            )

            activity_id = str(uuid.uuid4())

            extra_data = {
                "event_type": event_type,
                "sub_status": event_config["sub_status"],
                "vacancy_candidate_id": vacancy_candidate_id,
                "vacancy_id": candidate_data.get("vacancy_id"),
                "triggered_by": triggered_by or "system",
            }
            if event_config.get("stage"):
                extra_data["new_stage"] = event_config["stage"]
            if metadata:
                extra_data["metadata"] = metadata

            activity = ActivityFeed(
                id=activity_id,
                activity_type=f"return_event_{event_type}",
                actor_id=candidate_data.get("candidate_id"),
                actor_name=candidate_name,
                actor_type="candidate",
                target_id=vacancy_candidate_id,
                target_name=candidate_name,
                target_type="vacancy_candidate",
                title=title,
                description=description,
                summary=title,
                extra_data=extra_data,
                priority=event_config.get("priority", "normal"),
                category=event_config.get("category"),
                action_url=f"/funil-de-talentos/candidato/{candidate_data.get('candidate_id')}",
                action_label=event_config.get("action_label", "Ver Candidato"),
                is_visible=True,
                created_at=datetime.utcnow(),
                created_by="system",
            )

            self.db.add(activity)
            await self.db.commit()

            logger.info(
                f"ActivityFeed created: id={activity_id}, type=return_event_{event_type}"
            )
            return activity_id

        except Exception as e:
            logger.error(f"Error creating activity feed entry: {e}", exc_info=True)
            try:
                await self.db.rollback()
            except Exception:
                pass
            return None

    async def _notify_recruiter(
        self,
        event_config: dict[str, Any],
        candidate_data: dict[str, Any],
        vacancy_candidate_id: str,
        event_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Send notification to recruiter about the event."""
        try:
            candidate_name = candidate_data.get("candidate_name", "")
            title = event_config["title_template"].format(
                candidate_name=candidate_name
            )
            description = event_config.get("description_template", "").format(
                candidate_name=candidate_name
            )

            recruiter_id = candidate_data.get("added_by") or "default_user"

            await notification_service.create_notification(
                user_id=recruiter_id,
                title=title,
                message=description,
                notification_type=event_config.get("notification_type", "info"),
                category=event_config.get("category"),
                related_candidate_id=candidate_data.get("candidate_id"),
                related_job_id=candidate_data.get("vacancy_id"),
                action_url=f"/funil-de-talentos/candidato/{candidate_data.get('candidate_id')}",
                action_label=event_config.get("action_label", "Ver Candidato"),
            )

            logger.info(
                f"Notification sent to recruiter {recruiter_id} "
                f"for event '{event_type}' on candidate '{candidate_name}'"
            )
            return True

        except Exception as e:
            logger.error(
                f"Error sending notification for event '{event_type}': {e}",
                exc_info=True,
            )
            return False
