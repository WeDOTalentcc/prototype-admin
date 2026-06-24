"""
Pipeline Monitor Service - Monitors recruitment pipeline per company and generates proactive events.

Scans all active companies for pipeline health issues including:
- Stagnant candidates exceeding SLA
- High WSI scores without recruiter action
- Approaching vacancy deadlines
- Interviews without feedback
- Rejected candidates without feedback
- Weak funnels with few advanced candidates
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.shared.policy_middleware import get_policy_for_company

logger = logging.getLogger(__name__)


class PipelineEventType(StrEnum):
    CANDIDATE_STAGNANT = "candidate_stagnant"
    HIGH_SCORE_NO_ACTION = "high_score_no_action"
    DEADLINE_APPROACHING = "deadline_approaching"
    INTERVIEW_NO_FEEDBACK = "interview_no_feedback"
    REJECTION_PENDING_FEEDBACK = "rejection_pending_feedback"
    FUNNEL_WEAK = "funnel_weak"


@dataclass
class PipelineEvent:
    event_type: PipelineEventType
    company_id: str
    title: str
    message: str
    severity: str
    data: dict[str, Any]
    suggested_action: str
    action_label: str
    candidate_id: str | None = None
    vacancy_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class PipelineMonitor:
    """
    Monitors the recruitment pipeline for each active company and generates
    proactive events when conditions require attention.
    """

    async def scan_all_companies(self) -> list[PipelineEvent]:
        all_events: list[PipelineEvent] = []

        try:
            async with async_session_factory() as db:
                result = await db.execute(
                    text("""
                        SELECT DISTINCT company_id
                        FROM job_vacancies
                        WHERE status IN ('Ativa', 'active', 'open')
                          AND company_id IS NOT NULL
                    """)
                )
                # asyncpg returns UUID Python objects from UUID columns; convert to
                # str so subsequent raw-text() params don't send UUID OID against
                # character varying columns (raises "operator does not exist: varchar = uuid").
                company_ids = [str(row[0]) for row in result.fetchall()]

                logger.info(f"🔍 [PipelineMonitor] Scanning {len(company_ids)} active companies")

                for company_id in company_ids:
                    try:
                        events = await self.scan_company(company_id, db)
                        all_events.extend(events)
                    except Exception as e:
                        logger.error(f"[PipelineMonitor] Error scanning company {company_id}: {e}")

        except Exception as e:
            logger.error(f"[PipelineMonitor] Error in scan_all_companies: {e}")

        logger.info(f"✅ [PipelineMonitor] Scan complete: {len(all_events)} events across {len(company_ids) if 'company_ids' in dir() else '?'} companies")
        return all_events

    async def scan_company(self, company_id: str, db: AsyncSession) -> list[PipelineEvent]:
        events: list[PipelineEvent] = []
        company_id = str(company_id)  # guard: asyncpg may return uuid.UUID from UUID columns

        try:
            policy = await get_policy_for_company(company_id, db)
            pipeline_rules = policy.get("pipeline_rules", {})
            max_days_in_stage = pipeline_rules.get("max_days_in_stage", None)

            events.extend(await self._detect_stagnant_candidates(company_id, db, max_days_in_stage))
            events.extend(await self._detect_high_score_no_action(company_id, db))
            events.extend(await self._detect_deadline_approaching(company_id, db))
            events.extend(await self._detect_interview_no_feedback(company_id, db))
            events.extend(await self._detect_rejection_pending_feedback(company_id, db, policy))
            events.extend(await self._detect_funnel_weak(company_id, db))

            logger.info(f"[PipelineMonitor] Company {company_id}: {len(events)} events detected")
        except Exception as e:
            logger.error(f"[PipelineMonitor] Error scanning company {company_id}: {e}")

        return events

    async def _detect_stagnant_candidates(
        self, company_id: str, db: AsyncSession, max_days_in_stage: int | None
    ) -> list[PipelineEvent]:
        events: list[PipelineEvent] = []
        try:
            sla = max_days_in_stage if max_days_in_stage else 10
            cutoff = datetime.utcnow() - timedelta(days=sla)

            result = await db.execute(
                text("""
                    SELECT vc.candidate_id, vc.vacancy_id, vc.stage, vc.updated_at,
                           c.name AS candidate_name, jv.title AS vacancy_title
                    FROM vacancy_candidates vc
                    JOIN candidates c ON c.id = vc.candidate_id
                    JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE jv.company_id = :company_id
                      AND jv.status IN ('Ativa', 'active', 'open')
                      AND vc.stage NOT IN ('hired', 'rejected', 'withdrawn', 'declined', 'offer_declined', 'contratado', 'reprovado')
                      AND vc.updated_at < :cutoff
                    ORDER BY vc.updated_at ASC
                    LIMIT 20
                """),
                {"company_id": company_id, "cutoff": cutoff}
            )
            rows = result.fetchall()

            for row in rows:
                days = (datetime.utcnow() - row.updated_at).days
                events.append(PipelineEvent(
                    event_type=PipelineEventType.CANDIDATE_STAGNANT,
                    company_id=company_id,
                    title="⏳ Candidato Estagnado",
                    message=f"{row.candidate_name} está há {days} dias em {row.stage} na vaga {row.vacancy_title}. O SLA é {sla} dias.",
                    severity="warning",
                    data={"days_stagnant": days, "stage": row.stage, "sla": sla},
                    suggested_action="advance_candidate",
                    action_label="Avançar Candidato",
                    candidate_id=str(row.candidate_id),
                    vacancy_id=str(row.vacancy_id),
                ))

        except Exception as e:
            logger.error(f"[PipelineMonitor] Error detecting stagnant candidates for {company_id}: {e}")

        return events

    async def _detect_high_score_no_action(
        self, company_id: str, db: AsyncSession
    ) -> list[PipelineEvent]:
        events: list[PipelineEvent] = []
        try:
            cutoff = datetime.utcnow() - timedelta(hours=48)

            result = await db.execute(
                text("""
                    SELECT ws.candidate_id, ws.score, ws.completed_at,
                           c.name AS candidate_name,
                           vc.vacancy_id, vc.stage, vc.updated_at AS vc_updated_at
                    FROM wsi_sessions ws
                    JOIN candidates c ON c.id = ws.candidate_id
                    JOIN vacancy_candidates vc ON vc.candidate_id = ws.candidate_id
                    JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE jv.company_id = :company_id
                      AND ws.status = 'completed'
                      AND ws.score > 80
                      AND vc.updated_at < :cutoff
                      AND vc.stage NOT IN ('hired', 'rejected', 'withdrawn', 'declined', 'interview', 'entrevista')
                      AND jv.status IN ('Ativa', 'active', 'open')
                    ORDER BY ws.score DESC
                    LIMIT 15
                """),
                {"company_id": company_id, "cutoff": cutoff}
            )
            rows = result.fetchall()

            for row in rows:
                hours = int((datetime.utcnow() - row.vc_updated_at).total_seconds() / 3600)
                events.append(PipelineEvent(
                    event_type=PipelineEventType.HIGH_SCORE_NO_ACTION,
                    company_id=company_id,
                    title="🌟 Score Alto Sem Ação",
                    message=f"{row.candidate_name} tem score WSI {row.score} e está parado há {hours}h. Sugerir entrevista?",
                    severity="warning",
                    data={"score": float(row.score), "hours_idle": hours},
                    suggested_action="schedule_interview",
                    action_label="Agendar Entrevista",
                    candidate_id=str(row.candidate_id),
                    vacancy_id=str(row.vacancy_id),
                ))

        except Exception as e:
            logger.error(f"[PipelineMonitor] Error detecting high score no action for {company_id}: {e}")

        return events

    async def _detect_deadline_approaching(
        self, company_id: str, db: AsyncSession
    ) -> list[PipelineEvent]:
        events: list[PipelineEvent] = []
        try:
            now = datetime.utcnow()
            deadline_limit = now + timedelta(days=5)

            result = await db.execute(
                text("""
                    SELECT jv.id AS vacancy_id, jv.title, jv.deadline,
                           COUNT(vc.id) FILTER (WHERE vc.stage IN ('interview', 'entrevista', 'offer', 'oferta', 'technical_test', 'teste_tecnico')) AS advanced_count
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND jv.status IN ('Ativa', 'active', 'open')
                      AND jv.deadline IS NOT NULL
                      AND jv.deadline >= :now
                      AND jv.deadline <= :deadline_limit
                    GROUP BY jv.id, jv.title, jv.deadline
                    ORDER BY jv.deadline ASC
                    LIMIT 10
                """),
                {"company_id": company_id, "now": now, "deadline_limit": deadline_limit}
            )
            rows = result.fetchall()

            for row in rows:
                days = (row.deadline - now).days
                events.append(PipelineEvent(
                    event_type=PipelineEventType.DEADLINE_APPROACHING,
                    company_id=company_id,
                    title="⏰ Prazo da Vaga se Aproxima",
                    message=f"Vaga '{row.title}' fecha em {days} dias. Apenas {row.advanced_count} candidatos em etapas avançadas.",
                    severity="urgent" if days <= 2 else "warning",
                    data={"days_remaining": days, "advanced_count": int(row.advanced_count)},
                    suggested_action="expand_sourcing",
                    action_label="Ampliar Sourcing",
                    vacancy_id=str(row.vacancy_id),
                ))

        except Exception as e:
            logger.error(f"[PipelineMonitor] Error detecting deadline approaching for {company_id}: {e}")

        return events

    async def _detect_interview_no_feedback(
        self, company_id: str, db: AsyncSession
    ) -> list[PipelineEvent]:
        events: list[PipelineEvent] = []
        try:
            cutoff = datetime.utcnow() - timedelta(hours=48)

            result = await db.execute(
                text("""
                    SELECT i.id AS interview_id, i.candidate_id, i.job_vacancy_id,
                           i.candidate_name, i.job_title, i.end_time
                    FROM interviews i
                    JOIN job_vacancies jv ON jv.id = i.job_vacancy_id
                    WHERE jv.company_id = :company_id
                      AND i.status = 'completed'
                      AND i.scorecard IS NULL
                      AND i.end_time < :cutoff
                    ORDER BY i.end_time ASC
                    LIMIT 15
                """),
                {"company_id": company_id, "cutoff": cutoff}
            )
            rows = result.fetchall()

            for row in rows:
                days = (datetime.utcnow() - row.end_time).days
                events.append(PipelineEvent(
                    event_type=PipelineEventType.INTERVIEW_NO_FEEDBACK,
                    company_id=company_id,
                    title="📝 Entrevista Sem Feedback",
                    message=f"Entrevista de {row.candidate_name} para {row.job_title} foi há {days} dias sem feedback.",
                    severity="urgent" if days >= 5 else "warning",
                    data={"days_without_feedback": days, "interview_id": str(row.interview_id)},
                    suggested_action="request_feedback",
                    action_label="Solicitar Feedback",
                    candidate_id=str(row.candidate_id),
                    vacancy_id=str(row.job_vacancy_id),
                ))

        except Exception as e:
            logger.error(f"[PipelineMonitor] Error detecting interview no feedback for {company_id}: {e}")

        return events

    async def _detect_rejection_pending_feedback(
        self, company_id: str, db: AsyncSession, policy: dict[str, Any]
    ) -> list[PipelineEvent]:
        events: list[PipelineEvent] = []
        try:
            communication_rules = policy.get("communication_rules", {})
            from app.shared.policy_helper import coerce_bool, coerce_int
            auto_rejection = coerce_bool(communication_rules.get("auto_rejection_feedback", True), True)

            if auto_rejection:
                return events

            deadline_hours = coerce_int(communication_rules.get("rejection_feedback_deadline_hours", 48), 48)
            cutoff = datetime.utcnow() - timedelta(hours=deadline_hours)

            result = await db.execute(
                text("""
                    SELECT COUNT(*) AS cnt
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    WHERE jv.company_id = :company_id
                      AND vc.stage IN ('rejected', 'reprovado')
                      AND vc.updated_at < :cutoff
                      AND jv.status IN ('Rascunho', 'Ativa', 'Pausada', 'Concluída', 'Cancelada', 'Arquivada')
                      AND NOT EXISTS (
                          SELECT 1 FROM communication_logs cl
                          WHERE cl.candidate_id = vc.candidate_id
                            AND cl.company_id = :company_id
                            AND cl.template_type = 'rejection'
                            AND cl.created_at > vc.updated_at
                      )
                    LIMIT 1
                """),
                {"company_id": company_id, "cutoff": cutoff}
            )
            row = result.fetchone()
            count = row.cnt if row else 0

            if count > 0:
                events.append(PipelineEvent(
                    event_type=PipelineEventType.REJECTION_PENDING_FEEDBACK,
                    company_id=company_id,
                    title="📨 Feedback de Reprovação Pendente",
                    message=f"{count} candidatos reprovados sem feedback há mais de {deadline_hours}h.",
                    severity="warning",
                    data={"count": int(count), "deadline_hours": deadline_hours},
                    suggested_action="send_batch_rejection",
                    action_label="Enviar Feedback em Lote",
                ))

        except Exception as e:
            logger.error(f"[PipelineMonitor] Error detecting rejection pending feedback for {company_id}: {e}")

        return events

    async def _detect_funnel_weak(
        self, company_id: str, db: AsyncSession
    ) -> list[PipelineEvent]:
        events: list[PipelineEvent] = []
        try:
            result = await db.execute(
                text("""
                    SELECT jv.id AS vacancy_id, jv.title,
                           COUNT(vc.id) FILTER (WHERE vc.stage IN ('interview', 'entrevista', 'technical_test', 'teste_tecnico', 'offer', 'oferta')) AS advanced_count
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                    WHERE jv.company_id = :company_id
                      AND jv.status IN ('Ativa', 'active', 'open')
                    GROUP BY jv.id, jv.title
                    HAVING COUNT(vc.id) FILTER (WHERE vc.stage IN ('interview', 'entrevista', 'technical_test', 'teste_tecnico', 'offer', 'oferta')) < 3
                    ORDER BY advanced_count ASC
                    LIMIT 10
                """),
                {"company_id": company_id}
            )
            rows = result.fetchall()

            for row in rows:
                events.append(PipelineEvent(
                    event_type=PipelineEventType.FUNNEL_WEAK,
                    company_id=company_id,
                    title="📉 Funil Fraco",
                    message=f"Funil fraco para '{row.title}': apenas {row.advanced_count} candidato(s) em etapas avançadas.",
                    severity="info" if row.advanced_count > 0 else "warning",
                    data={"advanced_count": int(row.advanced_count)},
                    suggested_action="expand_sourcing",
                    action_label="Ampliar Sourcing",
                    vacancy_id=str(row.vacancy_id),
                ))

        except Exception as e:
            logger.error(f"[PipelineMonitor] Error detecting weak funnel for {company_id}: {e}")

        return events
