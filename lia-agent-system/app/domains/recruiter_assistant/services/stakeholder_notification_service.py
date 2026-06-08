# ADR-001-EXEMPT: 3-table aging JOIN with EXTRACT/INTERVAL in detect_pending_decisions, CandidatePipelineRepository extension deferred.
"""
Stakeholder Notification Service — Escalation loop for hiring managers.

Detects pending decisions from hiring managers and sends escalated notifications:
1. Gentle reminder (after N days of inactivity)
2. Follow-up (after 2N days)
3. Escalation to recruiter/admin (after 3N days)

Stakeholder types: hiring_manager, recruiter, admin
"""
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class EscalationLevel(StrEnum):
    GENTLE_REMINDER = "gentle_reminder"
    FOLLOW_UP = "follow_up"
    ESCALATION = "escalation"


class PendingDecisionType(StrEnum):
    INTERVIEW_FEEDBACK = "interview_feedback"
    CANDIDATE_APPROVAL = "candidate_approval"
    OFFER_APPROVAL = "offer_approval"
    JOB_APPROVAL = "job_approval"
    SCREENING_REVIEW = "screening_review"


ESCALATION_INTERVALS_DAYS = {
    EscalationLevel.GENTLE_REMINDER: 2,
    EscalationLevel.FOLLOW_UP: 5,
    EscalationLevel.ESCALATION: 8,
}


@dataclass
class PendingDecision:
    decision_id: str
    decision_type: PendingDecisionType
    company_id: str
    stakeholder_id: str
    stakeholder_name: str
    stakeholder_role: str
    description: str
    created_at: datetime
    job_id: str | None = None
    candidate_id: str | None = None
    candidate_name: str | None = None
    job_title: str | None = None
    days_pending: int = 0
    escalation_level: EscalationLevel = EscalationLevel.GENTLE_REMINDER
    last_notified_at: datetime | None = None
    notification_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_type": self.decision_type.value,
            "company_id": self.company_id,
            "stakeholder_id": self.stakeholder_id,
            "stakeholder_name": self.stakeholder_name,
            "stakeholder_role": self.stakeholder_role,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "job_id": self.job_id,
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "job_title": self.job_title,
            "days_pending": self.days_pending,
            "escalation_level": self.escalation_level.value,
            "notification_count": self.notification_count,
        }


ESCALATION_TEMPLATES = {
    EscalationLevel.GENTLE_REMINDER: {
        "title": "Lembrete: {decision_type_label} pendente",
        "message": (
            "Olá {stakeholder_name}, a LIA identificou que há uma decisão pendente "
            "sobre {description}. Quando puder, por favor avalie para que possamos "
            "dar continuidade ao processo."
        ),
    },
    EscalationLevel.FOLLOW_UP: {
        "title": "Follow-up: {decision_type_label} aguardando há {days_pending} dias",
        "message": (
            "{stakeholder_name}, esta é uma segunda notificação sobre {description}. "
            "A decisão está pendente há {days_pending} dias. "
            "Candidatos podem perder interesse se o processo demorar muito."
        ),
    },
    EscalationLevel.ESCALATION: {
        "title": "Escalação: {decision_type_label} pendente há {days_pending} dias",
        "message": (
            "Atenção: a decisão sobre {description} está pendente há {days_pending} dias "
            "e {stakeholder_name} ainda não respondeu. "
            "Recomenda-se contato direto para evitar perda do candidato."
        ),
    },
}

DECISION_TYPE_LABELS = {
    PendingDecisionType.INTERVIEW_FEEDBACK: "Feedback de entrevista",
    PendingDecisionType.CANDIDATE_APPROVAL: "Aprovação de candidato",
    PendingDecisionType.OFFER_APPROVAL: "Aprovação de oferta",
    PendingDecisionType.JOB_APPROVAL: "Aprovação de vaga",
    PendingDecisionType.SCREENING_REVIEW: "Revisão de triagem",
}


class StakeholderNotificationService:
    _instance: "StakeholderNotificationService | None" = None

    @classmethod
    def get_instance(cls) -> "StakeholderNotificationService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._notification_history: dict[str, list[dict[str, Any]]] = {}

    async def detect_pending_decisions(self, company_id: str) -> list[PendingDecision]:
        from lia_config.database import AsyncSessionLocal
        from sqlalchemy import text

        decisions: list[PendingDecision] = []

        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT vc.candidate_id, vc.vacancy_id, vc.stage, vc.updated_at,
                           c.name AS candidate_name,
                           jv.title AS job_title,
                           jv.hiring_manager_id,
                           EXTRACT(DAY FROM NOW() - vc.updated_at) AS days_pending
                    FROM vacancy_candidates vc
                    LEFT JOIN candidates c ON c.id = vc.candidate_id
                    LEFT JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE vc.company_id = :company_id
                      AND vc.stage IN ('Entrevista Gestor', 'Proposta', 'Aprovação')
                      AND vc.updated_at < NOW() - INTERVAL '2 days'
                      AND jv.status = 'Ativa'
                    ORDER BY vc.updated_at ASC
                    LIMIT 30
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as exc:
                logger.warning("Failed to detect pending decisions: %s", exc)
                return decisions

        for row in rows:
            days_pending = int(row[7] or 0)

            if days_pending >= ESCALATION_INTERVALS_DAYS[EscalationLevel.ESCALATION]:
                level = EscalationLevel.ESCALATION
            elif days_pending >= ESCALATION_INTERVALS_DAYS[EscalationLevel.FOLLOW_UP]:
                level = EscalationLevel.FOLLOW_UP
            else:
                level = EscalationLevel.GENTLE_REMINDER

            stage = row[2] or "Aprovação"
            if stage == "Entrevista Gestor":
                decision_type = PendingDecisionType.INTERVIEW_FEEDBACK
            elif stage == "Proposta":
                decision_type = PendingDecisionType.OFFER_APPROVAL
            else:
                decision_type = PendingDecisionType.CANDIDATE_APPROVAL

            decisions.append(PendingDecision(
                decision_id=str(uuid.uuid4()),
                decision_type=decision_type,
                company_id=company_id,
                stakeholder_id=str(row[6]) if row[6] else f"hm:{company_id}",
                stakeholder_name="Gestor da Vaga",
                stakeholder_role="hiring_manager",
                description=f"{row[4] or 'Candidato'} na vaga '{row[5] or row[1]}'",
                created_at=row[3] if row[3] else datetime.now(timezone.utc),
                job_id=str(row[1]),
                candidate_id=str(row[0]),
                candidate_name=row[4],
                job_title=row[5],
                days_pending=days_pending,
                escalation_level=level,
            ))
        return decisions

    async def send_escalation_notifications(
        self,
        company_id: str,
        decisions: list[PendingDecision] | None = None,
    ) -> dict[str, Any]:
        if decisions is None:
            decisions = await self.detect_pending_decisions(company_id)

        sent = 0
        skipped = 0
        errors = 0

        for decision in decisions:
            try:
                already_sent = self._was_recently_notified(decision)
                if already_sent:
                    skipped += 1
                    continue

                await self._send_notification(decision)
                self._record_notification(decision)
                sent += 1
            except Exception as exc:
                logger.error("Failed to send escalation for %s: %s", decision.decision_id, exc)
                errors += 1

        summary = {
            "company_id": company_id,
            "total_pending": len(decisions),
            "notifications_sent": sent,
            "skipped_recent": skipped,
            "errors": errors,
            "by_level": {},
        }
        for d in decisions:
            lvl = d.escalation_level.value
            summary["by_level"][lvl] = summary["by_level"].get(lvl, 0) + 1

        logger.info(
            "Stakeholder notifications for %s: %d sent, %d skipped, %d errors",
            company_id, sent, skipped, errors,
        )
        return summary

    def _was_recently_notified(self, decision: PendingDecision) -> bool:
        key = f"{decision.stakeholder_id}:{decision.candidate_id}:{decision.job_id}"
        history = self._notification_history.get(key, [])
        if not history:
            return False

        last = history[-1]
        last_at = last.get("sent_at")
        if isinstance(last_at, datetime):
            hours_since = (datetime.now(timezone.utc) - last_at).total_seconds() / 3600
            if hours_since < 24:
                return True

        last_level = last.get("level")
        if last_level == decision.escalation_level.value:
            return True
        return False

    def _record_notification(self, decision: PendingDecision) -> None:
        key = f"{decision.stakeholder_id}:{decision.candidate_id}:{decision.job_id}"
        if key not in self._notification_history:
            self._notification_history[key] = []
        self._notification_history[key].append({
            "level": decision.escalation_level.value,
            "sent_at": datetime.now(timezone.utc),
            "decision_type": decision.decision_type.value,
        })

    async def _send_notification(self, decision: PendingDecision) -> None:
        template = ESCALATION_TEMPLATES[decision.escalation_level]
        decision_type_label = DECISION_TYPE_LABELS.get(
            decision.decision_type, decision.decision_type.value
        )

        fmt_vars = {
            "stakeholder_name": decision.stakeholder_name,
            "description": decision.description,
            "days_pending": str(decision.days_pending),
            "decision_type_label": decision_type_label,
        }
        title = template["title"].format(**fmt_vars)
        message = template["message"].format(**fmt_vars)

        try:
            from lia_messaging.notification_service import NotificationService, NotificationType

            ntype_map = {
                EscalationLevel.GENTLE_REMINDER: NotificationType.INFO,
                EscalationLevel.FOLLOW_UP: NotificationType.ACTION_REQUIRED,
                EscalationLevel.ESCALATION: NotificationType.URGENT,
            }
            ntype = ntype_map.get(decision.escalation_level, NotificationType.INFO)

            channels = ["bell", "chat"]
            if decision.escalation_level == EscalationLevel.ESCALATION:
                channels.append("teams")
                channels.append("email")
            elif decision.escalation_level == EscalationLevel.FOLLOW_UP:
                channels.append("teams")

            recipients = [decision.stakeholder_id]
            if decision.escalation_level == EscalationLevel.ESCALATION:
                recruiter_id = await self._get_recruiter_for_job(decision.company_id, decision.job_id)
                if recruiter_id and recruiter_id != decision.stakeholder_id:
                    recipients.append(recruiter_id)

            svc = NotificationService()
            for recipient_id in recipients:
                await svc.create_notification(
                    user_id=recipient_id,
                    title=title,
                    message=message,
                    notification_type=ntype,
                    category="stakeholder_escalation",
                    source_agent="stakeholder_notification_service",
                    source_trigger=decision.escalation_level.value,
                    related_job_id=decision.job_id,
                    related_candidate_id=decision.candidate_id,
                    channels=channels,
                    metadata={
                        "decision_type": decision.decision_type.value,
                        "escalation_level": decision.escalation_level.value,
                        "days_pending": decision.days_pending,
                        "escalated_to": recipients,
                    },
                    expires_in_hours=48,
                )

            if decision.escalation_level in (EscalationLevel.FOLLOW_UP, EscalationLevel.ESCALATION):
                try:
                    from lia_messaging.teams import send_teams_message
                    await send_teams_message(
                        title=title,
                        text=message,
                        company_id=decision.company_id,
                        facts=[
                            {"name": "Candidato", "value": decision.candidate_name or "N/A"},
                            {"name": "Vaga", "value": decision.job_title or "N/A"},
                            {"name": "Dias pendente", "value": str(decision.days_pending)},
                            {"name": "Nível", "value": decision.escalation_level.value},
                        ],
                    )
                except Exception as teams_exc:
                    logger.debug("Teams notification skipped: %s", teams_exc)

        except Exception as exc:
            logger.warning("Failed to send stakeholder notification: %s", exc)
            raise

    async def _get_recruiter_for_job(self, company_id: str, job_id: str | None) -> str | None:
        # ADR-001 W1-004-C: migrated from raw SQL (session+text) to JobVacancyCrudRepository
        if not job_id:
            return None
        from lia_config.database import AsyncSessionLocal
        from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCrudRepository

        async with AsyncSessionLocal() as session:
            try:
                repo = JobVacancyCrudRepository(session)
                return await repo.get_recruiter_id(job_id=job_id, company_id=company_id)
            except Exception:
                return None

    def get_notification_summary(self, company_id: str) -> dict[str, Any]:
        total = 0
        by_level: dict[str, int] = {}
        for key, history in self._notification_history.items():
            if company_id in key:
                total += len(history)
                for entry in history:
                    lvl = entry.get("level", "unknown")
                    by_level[lvl] = by_level.get(lvl, 0) + 1
        return {"total_notifications": total, "by_level": by_level}


stakeholder_service = StakeholderNotificationService.get_instance()
