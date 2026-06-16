"""
Autonomous Actions Engine — Executes low-risk actions automatically.

Classifies actions by risk level (low/medium/high) and:
- LOW risk  → executes automatically with audit log (e.g., send reminders, flag stale candidates)
- MEDIUM risk → notifies recruiter before executing (e.g., suggest rescheduling)
- HIGH risk → asks for explicit confirmation (e.g., reject candidate, send offer)

Respects ConfidencePolicyService thresholds:
- APPLY_SILENT  (≥0.85): auto-execute
- APPLY_NOTIFY  (≥0.70): execute + notify
- ASK_USER      (<0.70): require confirmation
"""
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ActionRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionStatus(StrEnum):
    PENDING = "pending"
    EXECUTED = "executed"
    NOTIFIED = "notified"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    FAILED = "failed"


class AutonomousActionType(StrEnum):
    SEND_REMINDER = "send_reminder"
    FLAG_STALE_CANDIDATE = "flag_stale_candidate"
    SUGGEST_RESCHEDULE = "suggest_reschedule"
    SEND_FOLLOW_UP = "send_follow_up"
    UPDATE_CANDIDATE_NOTES = "update_candidate_notes"
    NOTIFY_HIRING_MANAGER = "notify_hiring_manager"
    REJECT_CANDIDATE = "reject_candidate"
    ADVANCE_CANDIDATE = "advance_candidate"
    SEND_OFFER = "send_offer"
    CLOSE_VACANCY = "close_vacancy"


ACTION_RISK_CLASSIFICATION: dict[AutonomousActionType, ActionRiskLevel] = {
    AutonomousActionType.SEND_REMINDER: ActionRiskLevel.LOW,
    AutonomousActionType.FLAG_STALE_CANDIDATE: ActionRiskLevel.LOW,
    AutonomousActionType.UPDATE_CANDIDATE_NOTES: ActionRiskLevel.LOW,
    AutonomousActionType.SEND_FOLLOW_UP: ActionRiskLevel.LOW,
    AutonomousActionType.SUGGEST_RESCHEDULE: ActionRiskLevel.MEDIUM,
    AutonomousActionType.NOTIFY_HIRING_MANAGER: ActionRiskLevel.MEDIUM,
    AutonomousActionType.ADVANCE_CANDIDATE: ActionRiskLevel.MEDIUM,
    AutonomousActionType.REJECT_CANDIDATE: ActionRiskLevel.HIGH,
    AutonomousActionType.SEND_OFFER: ActionRiskLevel.HIGH,
    AutonomousActionType.CLOSE_VACANCY: ActionRiskLevel.HIGH,
}


@dataclass
class AutonomousAction:
    action_id: str
    action_type: AutonomousActionType
    risk_level: ActionRiskLevel
    status: ActionStatus
    company_id: str
    description: str
    confidence: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: datetime | None = None
    target_id: str | None = None
    job_id: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    audit_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "risk_level": self.risk_level.value,
            "status": self.status.value,
            "company_id": self.company_id,
            "description": self.description,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "target_id": self.target_id,
            "job_id": self.job_id,
            "params": self.params,
            "result": self.result,
            "audit_reason": self.audit_reason,
        }


CONFIDENCE_SILENT = 0.85
CONFIDENCE_NOTIFY = 0.70


class AutonomousActionsEngine:
    _instance: "AutonomousActionsEngine | None" = None

    @classmethod
    def get_instance(cls) -> "AutonomousActionsEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._action_log: list[AutonomousAction] = []
        self._pending_confirmations: dict[str, AutonomousAction] = {}

    def classify_risk(self, action_type: AutonomousActionType) -> ActionRiskLevel:
        return ACTION_RISK_CLASSIFICATION.get(action_type, ActionRiskLevel.HIGH)

    def determine_execution_policy(
        self, risk_level: ActionRiskLevel, confidence: float
    ) -> ActionStatus:
        if risk_level == ActionRiskLevel.LOW and confidence >= CONFIDENCE_SILENT:
            return ActionStatus.EXECUTED
        if risk_level == ActionRiskLevel.LOW and confidence >= CONFIDENCE_NOTIFY:
            return ActionStatus.NOTIFIED
        if risk_level == ActionRiskLevel.MEDIUM and confidence >= CONFIDENCE_SILENT:
            return ActionStatus.NOTIFIED
        return ActionStatus.AWAITING_CONFIRMATION

    async def propose_action(
        self,
        action_type: AutonomousActionType,
        company_id: str,
        description: str,
        confidence: float = 0.80,
        target_id: str | None = None,
        job_id: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> AutonomousAction:
        risk_level = self.classify_risk(action_type)
        policy = self.determine_execution_policy(risk_level, confidence)

        action = AutonomousAction(
            action_id=str(uuid.uuid4()),
            action_type=action_type,
            risk_level=risk_level,
            status=policy,
            company_id=company_id,
            description=description,
            confidence=confidence,
            target_id=target_id,
            job_id=job_id,
            params=params or {},
        )

        if policy == ActionStatus.EXECUTED:
            action = await self._execute_action(action)
        elif policy == ActionStatus.NOTIFIED:
            action = await self._execute_action(action)
            action.status = ActionStatus.NOTIFIED
            await self._send_notification_for_action(action)
        else:
            self._pending_confirmations[action.action_id] = action
            action.audit_reason = "Aguardando confirmação do recrutador"

        self._action_log.append(action)
        logger.info(
            "AutonomousAction proposed: type=%s risk=%s status=%s confidence=%.2f",
            action_type.value, risk_level.value, action.status.value, confidence,
        )
        return action

    async def confirm_action(self, action_id: str) -> AutonomousAction | None:
        action = self._pending_confirmations.pop(action_id, None)
        if not action:
            return None
        action.status = ActionStatus.CONFIRMED
        action = await self._execute_action(action)
        return action

    async def reject_action(self, action_id: str, reason: str = "") -> AutonomousAction | None:
        action = self._pending_confirmations.pop(action_id, None)
        if not action:
            return None
        action.status = ActionStatus.REJECTED
        action.audit_reason = reason or "Rejeitado pelo recrutador"
        return action

    def get_pending_confirmations(self, company_id: str | None = None) -> list[AutonomousAction]:
        actions = list(self._pending_confirmations.values())
        if company_id:
            actions = [a for a in actions if a.company_id == company_id]
        return actions

    def get_action_log(
        self,
        company_id: str | None = None,
        limit: int = 50,
    ) -> list[AutonomousAction]:
        log = self._action_log
        if company_id:
            log = [a for a in log if a.company_id == company_id]
        return log[-limit:]

    async def _execute_action(self, action: AutonomousAction) -> AutonomousAction:
        try:
            handler = self._get_handler(action.action_type)
            if handler:
                result = await handler(action)
                action.result = result
            action.status = ActionStatus.EXECUTED
            action.executed_at = datetime.now(timezone.utc)
            action.audit_reason = f"Executado automaticamente (confidence={action.confidence:.2f})"
            logger.info("AutonomousAction executed: %s (%s)", action.action_id, action.action_type.value)
        except Exception as exc:
            action.status = ActionStatus.FAILED
            action.audit_reason = f"Falha na execução: {exc}"
            logger.error("AutonomousAction failed: %s — %s", action.action_id, exc)
        return action

    def _get_handler(self, action_type: AutonomousActionType):
        handlers = {
            AutonomousActionType.FLAG_STALE_CANDIDATE: self._handle_flag_stale,
            AutonomousActionType.SEND_REMINDER: self._handle_send_reminder,
            AutonomousActionType.SEND_FOLLOW_UP: self._handle_send_follow_up,
            AutonomousActionType.UPDATE_CANDIDATE_NOTES: self._handle_update_notes,
            AutonomousActionType.NOTIFY_HIRING_MANAGER: self._handle_notify_hm,
        }
        return handlers.get(action_type)

    async def _handle_flag_stale(self, action: AutonomousAction) -> dict[str, Any]:
        # ADR-001 W1-004-C: migrated from raw SQL (session+text) to VacancyCandidateRepository
        from lia_config.database import AsyncSessionLocal
        from app.domains.candidates.repositories.vacancy_candidate_repository import VacancyCandidateRepository
        from datetime import datetime, timezone

        async with AsyncSessionLocal() as session:
            repo = VacancyCandidateRepository(session)
            flag_note = f"\n[LIA Auto] Candidato flaggado como parado em {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
            success = await repo.append_note(
                candidate_id=action.target_id,
                company_id=action.company_id,
                note=flag_note,
            )
            if not success:
                return {"flagged": False, "error": "candidate not found"}
        return {"flagged": True, "candidate_id": action.target_id}

    async def _handle_send_reminder(self, action: AutonomousAction) -> dict[str, Any]:
        try:
            from lia_messaging.notification_service import NotificationService, NotificationType

            svc = NotificationService()
            user_id = action.params.get("user_id", f"system:{action.company_id}")
            await svc.create_notification(
                user_id=user_id,
                title="Lembrete da LIA",
                message=action.description,
                notification_type=NotificationType.ACTION_REQUIRED,
                category="autonomous_reminder",
                source_agent="autonomous_engine",
                related_job_id=action.job_id,
                related_candidate_id=action.target_id,
                channels=["bell", "chat"],
            )
            return {"reminder_sent": True}
        except Exception as exc:
            logger.warning("Send reminder failed: %s", exc)
            return {"reminder_sent": False, "error": str(exc)}

    async def _handle_send_follow_up(self, action: AutonomousAction) -> dict[str, Any]:
        return await self._handle_send_reminder(action)

    async def _handle_update_notes(self, action: AutonomousAction) -> dict[str, Any]:
        # ADR-001 W1-004-C: migrated from raw SQL (session+text) to VacancyCandidateRepository
        note = action.params.get("note", action.description)
        from lia_config.database import AsyncSessionLocal
        from app.domains.candidates.repositories.vacancy_candidate_repository import VacancyCandidateRepository

        async with AsyncSessionLocal() as session:
            repo = VacancyCandidateRepository(session)
            success = await repo.append_note(
                candidate_id=action.target_id,
                company_id=action.company_id,
                note=f"\n[LIA] {note}",
            )
            if not success:
                return {"updated": False, "error": "candidate not found"}
        return {"updated": True}

    async def _handle_notify_hm(self, action: AutonomousAction) -> dict[str, Any]:
        return await self._handle_send_reminder(action)

    async def _send_notification_for_action(self, action: AutonomousAction) -> None:
        try:
            from lia_messaging.notification_service import NotificationService, NotificationType

            svc = NotificationService()
            await svc.create_notification(
                user_id=f"system:{action.company_id}",
                title=f"LIA executou: {action.action_type.value}",
                message=f"{action.description} (executado automaticamente, confidence={action.confidence:.2f})",
                notification_type=NotificationType.INFO,
                category="autonomous_action_notified",
                source_agent="autonomous_engine",
                related_job_id=action.job_id,
                related_candidate_id=action.target_id,
                channels=["bell", "chat"],
            )
        except Exception as exc:
            logger.warning("Failed to send action notification: %s", exc)

    async def process_monitoring_alerts(self, company_id: str, alerts: list) -> list[AutonomousAction]:
        from .monitoring_loop import AlertSeverity, ProactiveAlert

        actions: list[AutonomousAction] = []
        for alert in alerts:
            if not isinstance(alert, ProactiveAlert):
                continue

            if alert.category.value == "stale_candidate" and alert.severity in (
                AlertSeverity.MEDIUM, AlertSeverity.HIGH
            ):
                action = await self.propose_action(
                    action_type=AutonomousActionType.FLAG_STALE_CANDIDATE,
                    company_id=company_id,
                    description=alert.message,
                    confidence=0.90 if alert.severity == AlertSeverity.HIGH else 0.80,
                    target_id=alert.candidate_id,
                    job_id=alert.job_id,
                )
                actions.append(action)

            elif alert.category.value == "sla_breach":
                action = await self.propose_action(
                    action_type=AutonomousActionType.SEND_REMINDER,
                    company_id=company_id,
                    description=f"SLA expirado: {alert.message}",
                    confidence=0.90,
                    job_id=alert.job_id,
                )
                actions.append(action)

        return actions


autonomous_engine = AutonomousActionsEngine.get_instance()
