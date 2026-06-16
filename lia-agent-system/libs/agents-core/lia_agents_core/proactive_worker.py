import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from lia_config.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


async def ensure_proactive_actions_columns():
    async with engine.begin() as conn:
        columns_to_add = [
            ("severity", "VARCHAR(20) DEFAULT 'info'"),
            ("message", "TEXT"),
            ("data", "JSONB DEFAULT '{}'::jsonb"),
            ("is_read", "BOOLEAN DEFAULT FALSE"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("target_user_id", "VARCHAR(255)"),
        ]
        for column_name, column_type in columns_to_add:
            try:
                await conn.execute(
                    text(f"ALTER TABLE proactive_actions ADD COLUMN IF NOT EXISTS {column_name} {column_type}")
                )
            except Exception as e:
                logger.warning(f"Could not add proactive_actions column {column_name}: {e}")

        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_proactive_actions_company ON proactive_actions(company_id)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_proactive_actions_status ON proactive_actions(status)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_proactive_actions_is_read ON proactive_actions(is_read)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_proactive_actions_created ON proactive_actions(created_at)"
            ))
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_proactive_actions_target_user ON proactive_actions(target_user_id)"
            ))
        except Exception as e:
            logger.warning(f"Could not create proactive_actions indexes: {e}")

    logger.info("Proactive actions columns verified/added successfully")


class ProactiveAgentWorker:
    def __init__(self, check_interval_minutes: int = 30):
        self.check_interval_minutes = check_interval_minutes
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self._running:
            logger.warning("ProactiveAgentWorker is already running")
            return

        await ensure_proactive_actions_columns()
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info(
            f"ProactiveAgentWorker started with interval={self.check_interval_minutes}m"
        )

    async def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("ProactiveAgentWorker stopped")

    async def _get_active_company_ids(self) -> List[str]:
        """Return all active company IDs from the database."""
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text(
                    "SELECT DISTINCT id::text FROM companies WHERE is_active = true"
                ))
                rows = result.fetchall()
                return [r[0] for r in rows] if rows else []
            except Exception as e:
                logger.warning(f"Could not fetch company IDs: {e}")
                return []

    async def _loop(self):
        while self._running:
            try:
                company_ids = await self._get_active_company_ids()
                if not company_ids:
                    logger.warning("ProactiveAgentWorker: no active companies found, skipping cycle")
                else:
                    total_alerts = 0
                    for company_id in company_ids:
                        try:
                            alerts = await self.run_all_checks(company_id)
                            total_alerts += len(alerts)
                        except Exception as e:
                            logger.error(f"ProactiveAgentWorker error for company {company_id}: {e}", exc_info=True)
                    if total_alerts:
                        logger.info(f"ProactiveAgentWorker generated {total_alerts} alert(s) across {len(company_ids)} companies")
            except Exception as e:
                logger.error(f"ProactiveAgentWorker check cycle error: {e}", exc_info=True)

            try:
                await asyncio.sleep(self.check_interval_minutes * 60)
            except asyncio.CancelledError:
                break

    async def run_all_checks(self, company_id: str) -> List[Dict]:
        all_alerts: List[Dict] = []

        checks = [
            self.check_velocity_bottleneck,
            self.check_recruiter_backlog,
            self.check_early_warning,
            self.check_journey_intelligence,
            self.check_pipeline_prediction,
            self.check_stale_pipeline,
            self.check_low_pipeline,
            self.check_high_scorers,
            self.check_deadlines,
            self.check_silver_medalists,
        ]

        for check_fn in checks:
            try:
                alerts = await check_fn(company_id)
                if alerts:
                    all_alerts.extend(alerts)
            except Exception as e:
                logger.error(f"Proactive check {check_fn.__name__} failed: {e}", exc_info=True)

        if all_alerts:
            await self._store_alerts(all_alerts)

        return all_alerts

    async def check_velocity_bottleneck(self, company_id: str) -> List[Dict]:
        """Alert when candidates exceed stage-specific time thresholds (uses stage_entered_at)."""
        from app.shared.services.pipeline_velocity_service import pipeline_velocity_service

        alerts: List[Dict] = []
        try:
            bottlenecked = await pipeline_velocity_service.get_bottlenecked_candidates(company_id)
        except Exception as e:
            logger.warning(f"check_velocity_bottleneck failed: {e}")
            return alerts

        for item in bottlenecked:
            overdue = item["overdue_days"]
            severity = "critical" if overdue > item["threshold_days"] else "warning"
            alerts.append({
                "type": "velocity_bottleneck",
                "severity": severity,
                "title": f"Candidato travado na etapa '{item['stage']}': {item['candidate_name']}",
                "message": (
                    f"{item['candidate_name']} está na etapa '{item['stage']}' da vaga "
                    f"'{item['vacancy_title']}' há {item['days_in_stage']:.0f} dias "
                    f"(limite recomendado: {item['threshold_days']} dias, "
                    f"{overdue:.0f} dias acima do esperado)."
                ),
                "data": {
                    "vacancy_candidate_id": item["vacancy_candidate_id"],
                    "candidate_id": item["candidate_id"],
                    "candidate_name": item["candidate_name"],
                    "vacancy_id": item["vacancy_id"],
                    "vacancy_title": item["vacancy_title"],
                    "stage": item["stage"],
                    "days_in_stage": item["days_in_stage"],
                    "threshold_days": item["threshold_days"],
                    "overdue_days": overdue,
                },
                "company_id": company_id,
                "created_at": datetime.now(timezone.utc),
                "is_read": False,
                "suggested_action": (
                    f"Tomar decisão sobre {item['candidate_name']} na etapa '{item['stage']}': "
                    f"avançar, rejeitar ou registrar motivo de bloqueio."
                ),
                "related_candidate_id": item["candidate_id"],
                "related_job_id": item["vacancy_id"],
            })

        return alerts

    async def check_recruiter_backlog(self, company_id: str) -> List[Dict]:
        """
        Alerta recrutadores quando têm candidatos além do threshold de tempo por etapa.
        - Uma query por empresa (sem N+1)
        - Alerta direcionado por recrutador (target_user_id)
        - Push Bell + Teams para severity=critical; Bell para warning
        """
        from app.shared.services.recruiter_metrics_service import recruiter_metrics_service
        from app.services.notification_service import notification_service, NotificationType, NotificationChannel

        alerts: List[Dict] = []
        try:
            recruiters = await recruiter_metrics_service.get_company_recruiters_backlog(company_id)
        except Exception as e:
            logger.warning(f"check_recruiter_backlog failed: {e}")
            return alerts

        for rec in recruiters:
            critical_stages = rec.get("critical_stages", [])
            if not critical_stages:
                continue

            recruiter_id = rec["recruiter_id"]
            has_offer_stuck = any(
                s["stage"].lower() in ("offer", "proposta") for s in critical_stages
            )
            severity = "critical" if has_offer_stuck else "warning"
            total_waiting = sum(s["candidate_count"] for s in critical_stages)

            stage_summary = ", ".join(
                f"'{s['stage']}' ({s['candidate_count']} cand., máx {s['max_days']}d)"
                for s in critical_stages[:3]
            )
            title = f"Backlog acumulado: {total_waiting} candidato(s) aguardando sua ação"
            message = (
                f"Candidatos além do prazo recomendado: {stage_summary}. "
                f"Pergunte à LIA: 'Quais candidatos estão me esperando?' para ver a lista priorizada."
            )

            # Alerta direcionado ao recrutador específico (Item 1)
            alerts.append({
                "type": "recruiter_backlog",
                "severity": severity,
                "title": title,
                "message": message,
                "data": {
                    "recruiter_id": recruiter_id,
                    "company_id": company_id,
                    "critical_stages": critical_stages,
                    "total_active": rec["total_active"],
                    "max_days_in_any_stage": rec["max_days_in_any_stage"],
                },
                "company_id": company_id,
                "target_user_id": recruiter_id,  # Item 1 — alerta só para este recrutador
                "created_at": datetime.now(timezone.utc),
                "is_read": False,
                "suggested_action": (
                    "Abra o chat com LIA e pergunte: 'Quais candidatos estão me esperando?' "
                    "para ver a lista priorizada e tomar ação."
                ),
            })

            # Item 3 — Push Bell + Teams direto no recrutador
            try:
                channels = [NotificationChannel.IN_APP.value]
                if severity == "critical":
                    channels.append(NotificationChannel.TEAMS.value)

                notification_type = (
                    NotificationType.URGENT if severity == "critical"
                    else NotificationType.WARNING
                )

                await notification_service.create_notification(
                    user_id=recruiter_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    category="recruiter_backlog",
                    source_agent="ProactiveAgentWorker",
                    source_trigger="check_recruiter_backlog",
                    channels=channels,
                    metadata={
                        "critical_stages": critical_stages,
                        "total_waiting": total_waiting,
                    },
                    expires_in_hours=24,
                )
            except Exception as e:
                logger.warning(f"check_recruiter_backlog notification failed for {recruiter_id}: {e}")

        return alerts

    async def check_early_warning(self, company_id: str) -> List[Dict]:
        """
        Alerta sobre candidatos em risco de ghosting usando EWS score por etapa.
        - Alerta individual por candidato, direcionado ao recrutador (target_user_id)
        - Bell + Teams para severity=critical; Bell para warning/high
        """
        from app.shared.services.early_warning_service import early_warning_service
        from app.services.notification_service import notification_service, NotificationType, NotificationChannel

        alerts: List[Dict] = []
        try:
            at_risk = await early_warning_service.get_at_risk_candidates(
                company_id=company_id,
                min_risk_level="high",  # só high e critical no ProactiveWorker
            )
        except Exception as e:
            logger.warning(f"check_early_warning failed: {e}")
            return alerts

        for candidate in at_risk[:20]:  # cap para evitar flood de alertas
            risk_level = candidate["risk_level"]
            severity = "critical" if risk_level == "critical" else "warning"
            days = candidate["days_since_contact"]
            ews = candidate["ews_score"]
            recruiter_id = candidate.get("recruiter_id")

            title = (
                f"Risco de ghosting [{risk_level.upper()}]: {candidate['candidate_name']}"
            )
            message = (
                f"{candidate['candidate_name']} está na etapa '{candidate['stage']}' "
                f"da vaga '{candidate['vacancy_title']}' sem contato há {days:.0f} dia(s) "
                f"(EWS score: {ews:.2f}, limite crítico: {candidate['critical_threshold']}d). "
                f"Envie uma mensagem para evitar perder este candidato."
            )

            alert: Dict = {
                "type": "early_warning",
                "severity": severity,
                "title": title,
                "message": message,
                "data": {
                    "vacancy_candidate_id": candidate["vacancy_candidate_id"],
                    "candidate_id": candidate["candidate_id"],
                    "candidate_name": candidate["candidate_name"],
                    "vacancy_id": candidate["vacancy_id"],
                    "vacancy_title": candidate["vacancy_title"],
                    "stage": candidate["stage"],
                    "lia_score": candidate["lia_score"],
                    "ews_score": ews,
                    "risk_level": risk_level,
                    "days_since_contact": days,
                    "warning_threshold": candidate["warning_threshold"],
                    "critical_threshold": candidate["critical_threshold"],
                    "last_contact_at": candidate.get("last_contact_at"),
                },
                "company_id": company_id,
                "target_user_id": recruiter_id,
                "created_at": datetime.now(timezone.utc),
                "is_read": False,
                "suggested_action": (
                    f"Enviar mensagem de acompanhamento para {candidate['candidate_name']} "
                    f"sobre a vaga '{candidate['vacancy_title']}' agora."
                ),
                "related_candidate_id": candidate["candidate_id"],
                "related_job_id": candidate["vacancy_id"],
            }
            alerts.append(alert)

            if recruiter_id:
                try:
                    channels = [NotificationChannel.IN_APP.value]
                    if severity == "critical":
                        channels.append(NotificationChannel.TEAMS.value)

                    notification_type = (
                        NotificationType.URGENT if severity == "critical"
                        else NotificationType.WARNING
                    )

                    await notification_service.create_notification(
                        user_id=recruiter_id,
                        title=title,
                        message=message,
                        notification_type=notification_type,
                        category="early_warning",
                        source_agent="ProactiveAgentWorker",
                        source_trigger="check_early_warning",
                        channels=channels,
                        metadata={
                            "candidate_id": candidate["candidate_id"],
                            "vacancy_id": candidate["vacancy_id"],
                            "ews_score": ews,
                            "risk_level": risk_level,
                        },
                        expires_in_hours=12,
                    )
                except Exception as e:
                    logger.warning(f"check_early_warning notification failed for {recruiter_id}: {e}")

        return alerts

    async def check_journey_intelligence(self, company_id: str) -> List[Dict]:
        """
        Detecta vagas com pipeline em risco usando Journey Intelligence (health score).
        - Bell para todos os alertas (por recrutador via target_user_id)
        - Teams para health_label=critical
        - Email semanal: enviado apenas às sextas (digest por recrutador)
        """
        from app.shared.services.journey_intelligence_service import journey_intelligence_service
        from app.services.notification_service import notification_service, NotificationType, NotificationChannel
        import datetime
        from datetime import timezone

        alerts: List[Dict] = []
        try:
            at_risk_recruiters = await journey_intelligence_service.get_company_recruiters_journey(
                company_id=company_id
            )
        except Exception as e:
            logger.warning(f"check_journey_intelligence failed: {e}")
            return alerts

        is_friday = datetime.datetime.now(timezone.utc).weekday() == 4  # sexta = 4

        for rec in at_risk_recruiters:
            recruiter_id = rec["recruiter_id"]
            at_risk_vacancies = rec["at_risk_vacancies"]
            critical_count = rec["critical_count"]
            warning_count = rec["warning_count"]

            if not at_risk_vacancies:
                continue

            # Um alerta consolidado por recrutador (não um por vaga — evita flood)
            severity = "critical" if critical_count > 0 else "warning"

            worst = at_risk_vacancies[0]  # já ordenado por health_score ASC
            title = (
                f"Pipeline em risco: {critical_count} vaga(s) crítica(s), "
                f"{warning_count} em alerta"
                if critical_count > 0
                else f"Pipeline em alerta: {warning_count} vaga(s) precisam de atenção"
            )

            vac_summary = ", ".join(
                f"'{v['vacancy_title']}' ({v['health_score']}/100)"
                for v in at_risk_vacancies[:3]
            )
            message = (
                f"Vagas com pipeline comprometido: {vac_summary}. "
                f"Pior score: {worst['vacancy_title']} ({worst['health_score']}/100 — "
                f"{worst['health_label']}). "
                f"Pergunte à LIA: 'Como está o funil da vaga X?' para análise detalhada."
            )

            alert: Dict = {
                "type": "journey_intelligence",
                "severity": severity,
                "title": title,
                "message": message,
                "data": {
                    "recruiter_id": recruiter_id,
                    "company_id": company_id,
                    "critical_count": critical_count,
                    "warning_count": warning_count,
                    "at_risk_vacancies": at_risk_vacancies[:5],
                },
                "company_id": company_id,
                "target_user_id": recruiter_id,
                "created_at": datetime.datetime.now(timezone.utc),
                "is_read": False,
                "suggested_action": (
                    f"Abra o chat com LIA e pergunte: 'Como está o funil da vaga "
                    f"{worst['vacancy_title']}?' para análise e ações recomendadas."
                ),
                "related_job_id": worst["vacancy_id"],
            }
            alerts.append(alert)

            # Push Bell (sempre) + Teams (critical) + Email (sextas)
            if recruiter_id and recruiter_id != "unknown":
                try:
                    channels = [NotificationChannel.IN_APP.value]
                    if severity == "critical":
                        channels.append(NotificationChannel.TEAMS.value)
                    if is_friday:
                        channels.append(NotificationChannel.EMAIL.value)

                    notification_type = (
                        NotificationType.URGENT if severity == "critical"
                        else NotificationType.WARNING
                    )

                    await notification_service.create_notification(
                        user_id=recruiter_id,
                        title=title,
                        message=message,
                        notification_type=notification_type,
                        category="journey_intelligence",
                        source_agent="ProactiveAgentWorker",
                        source_trigger="check_journey_intelligence",
                        channels=channels,
                        metadata={
                            "critical_count": critical_count,
                            "warning_count": warning_count,
                            "worst_vacancy": worst["vacancy_title"],
                            "worst_score": worst["health_score"],
                        },
                        expires_in_hours=24,
                    )
                except Exception as e:
                    logger.warning(
                        f"check_journey_intelligence notification failed for {recruiter_id}: {e}"
                    )

        return alerts

    async def check_pipeline_prediction(self, company_id: str) -> List[Dict]:
        """
        Alerta para vagas com baixa probabilidade de fechamento (<30%)
        e positivo (>=80%) para vagas prestes a fechar (Bell 1x).

        - Bell sempre
        - Teams se severity == critical (prob < 30% E health crítico)
        - Email apenas às sextas
        - Bell positivo (prob >= 80%) dispara 1x por vaga (flag em memória)
        """
        from app.shared.services.pipeline_prediction_service import pipeline_prediction_service
        from app.services.notification_service import notification_service, NotificationType, NotificationChannel
        import datetime
        from datetime import timezone

        alerts: List[Dict] = []
        try:
            overview = await pipeline_prediction_service.get_company_overview(
                company_id=company_id
            )
        except Exception as e:
            logger.warning(f"check_pipeline_prediction failed: {e}")
            return alerts

        vacancies = overview.get("vacancies", [])
        is_friday = datetime.datetime.now(timezone.utc).weekday() == 4

        for vac in vacancies:
            prob = vac.get("closure_probability", 50)
            vac_id = vac.get("vacancy_id", "")
            title = vac.get("vacancy_title", "Vaga")
            confidence = vac.get("confidence_level", "medium")
            risks = vac.get("risk_factors", [])

            # --- Alerta negativo: probabilidade baixa ---
            if prob < 30:
                severity = "critical" if prob < 15 else "warning"
                alert_title = (
                    f"Pipeline crítico: '{title}' com {prob}% de chance de fechar"
                    if prob < 15
                    else f"Pipeline em risco: '{title}' com {prob}% de chance de fechar"
                )
                risk_summary = ", ".join(risks[:3]) if risks else "pipeline comprometido"
                message = (
                    f"A vaga '{title}' tem apenas {prob}% de probabilidade de fechamento. "
                    f"Fatores: {risk_summary}. "
                    f"Confiança da previsão: {confidence}. "
                    f"Pergunte à LIA: 'O que está impedindo o fechamento da vaga {title}?'"
                )

                alert: Dict = {
                    "type": "pipeline_prediction_risk",
                    "severity": severity,
                    "title": alert_title,
                    "message": message,
                    "data": {
                        "vacancy_id": vac_id,
                        "vacancy_title": title,
                        "closure_probability": prob,
                        "confidence_level": confidence,
                        "risk_factors": risks,
                        "company_id": company_id,
                    },
                    "company_id": company_id,
                    "target_user_id": None,  # broadcast para a empresa
                    "created_at": datetime.datetime.now(timezone.utc),
                    "is_read": False,
                    "suggested_action": (
                        f"Abra o chat com LIA e pergunte: "
                        f"'O que posso fazer para acelerar o fechamento da vaga {title}?'"
                    ),
                    "related_job_id": vac_id,
                }
                alerts.append(alert)

                try:
                    channels = [NotificationChannel.IN_APP.value]
                    if severity == "critical":
                        channels.append(NotificationChannel.TEAMS.value)
                    if is_friday:
                        channels.append(NotificationChannel.EMAIL.value)

                    notification_type = (
                        NotificationType.URGENT if severity == "critical"
                        else NotificationType.WARNING
                    )

                    await notification_service.create_notification(
                        user_id=None,
                        title=alert_title,
                        message=message,
                        notification_type=notification_type,
                        category="pipeline_prediction",
                        source_agent="ProactiveAgentWorker",
                        source_trigger="check_pipeline_prediction",
                        channels=channels,
                        metadata={
                            "vacancy_id": vac_id,
                            "closure_probability": prob,
                            "confidence_level": confidence,
                        },
                        expires_in_hours=24,
                        company_id=company_id,
                    )
                except Exception as e:
                    logger.warning(f"check_pipeline_prediction notification failed for {vac_id}: {e}")

            # --- Alerta positivo: vaga prestes a fechar (>=80%), 1x por vaga ---
            elif prob >= 80:
                flag_key = f"_notified_closing_{vac_id}"
                if getattr(self, flag_key, False):
                    continue  # já notificado nesta instância do worker

                setattr(self, flag_key, True)

                close_title = f"Vaga prestes a fechar: '{title}' com {prob}% de probabilidade"
                est_days = vac.get("estimated_days_to_close")
                days_str = f" em ~{est_days} dias" if est_days else ""
                close_message = (
                    f"A vaga '{title}' está a {prob}% de ser fechada{days_str}. "
                    f"Prepare a proposta e alinhe com o gestor para garantir o fechamento."
                )

                alert_closing: Dict = {
                    "type": "pipeline_prediction_closing",
                    "severity": "info",
                    "title": close_title,
                    "message": close_message,
                    "data": {
                        "vacancy_id": vac_id,
                        "vacancy_title": title,
                        "closure_probability": prob,
                        "estimated_days_to_close": est_days,
                        "company_id": company_id,
                    },
                    "company_id": company_id,
                    "target_user_id": None,
                    "created_at": datetime.datetime.now(timezone.utc),
                    "is_read": False,
                    "suggested_action": (
                        f"Prepare a proposta para '{title}' e confirme disponibilidade do gestor."
                    ),
                    "related_job_id": vac_id,
                }
                alerts.append(alert_closing)

                try:
                    await notification_service.create_notification(
                        user_id=None,
                        title=close_title,
                        message=close_message,
                        notification_type=NotificationType.INFO,
                        category="pipeline_prediction",
                        source_agent="ProactiveAgentWorker",
                        source_trigger="check_pipeline_prediction",
                        channels=[NotificationChannel.IN_APP.value],
                        metadata={
                            "vacancy_id": vac_id,
                            "closure_probability": prob,
                            "estimated_days_to_close": est_days,
                        },
                        expires_in_hours=48,
                        company_id=company_id,
                    )
                except Exception as e:
                    logger.warning(f"check_pipeline_prediction closing notification failed for {vac_id}: {e}")

        return alerts

    async def check_stale_pipeline(self, company_id: str) -> List[Dict]:
        alerts: List[Dict] = []
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT vc.id, vc.candidate_id, c.name, vc.stage, vc.vacancy_id,
                           jv.title, vc.updated_at
                    FROM vacancy_candidates vc
                    JOIN candidates c ON vc.candidate_id = c.id
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE vc.status = 'active'
                      AND vc.updated_at < NOW() - INTERVAL '7 days'
                      AND jv.company_id::text = :company_id
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as e:
                logger.warning(f"check_stale_pipeline query failed: {e}")
                return alerts

        for row in rows:
            days_stuck = (datetime.now(timezone.utc) - row.updated_at.replace(tzinfo=timezone.utc)).days if row.updated_at else 7
            severity = "critical" if days_stuck > 14 else "warning"
            alerts.append({
                "type": "stale_pipeline",
                "severity": severity,
                "title": f"Candidato parado há {days_stuck} dias",
                "message": (
                    f"{row.name} está na etapa '{row.stage}' da vaga "
                    f"'{row.title}' há {days_stuck} dias sem movimentação."
                ),
                "data": {
                    "vacancy_candidate_id": str(row.id),
                    "candidate_id": str(row.candidate_id),
                    "candidate_name": row.name,
                    "stage": row.stage,
                    "vacancy_id": str(row.vacancy_id),
                    "vacancy_title": row.title,
                    "days_stuck": days_stuck,
                },
                "company_id": company_id,
                "created_at": datetime.now(timezone.utc),
                "is_read": False,
                "suggested_action": (
                    f"Revisar o candidato {row.name} e avançar para a próxima etapa "
                    f"ou registrar feedback sobre a decisão."
                ),
                "related_candidate_id": str(row.candidate_id),
                "related_job_id": str(row.vacancy_id),
            })

        return alerts

    async def check_low_pipeline(self, company_id: str) -> List[Dict]:
        alerts: List[Dict] = []
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT jv.id, jv.title, jv.department,
                           COUNT(vc.id) as candidate_count
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc
                        ON jv.id = vc.vacancy_id AND vc.status = 'active'
                    WHERE jv.status = 'open'
                      AND jv.company_id::text = :company_id
                    GROUP BY jv.id, jv.title, jv.department
                    HAVING COUNT(vc.id) < 3
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as e:
                logger.warning(f"check_low_pipeline query failed: {e}")
                return alerts

        for row in rows:
            severity = "critical" if row.candidate_count == 0 else "warning"
            alerts.append({
                "type": "low_pipeline",
                "severity": severity,
                "title": f"Pipeline com poucos candidatos: {row.title}",
                "message": (
                    f"A vaga '{row.title}' ({row.department or 'sem departamento'}) "
                    f"possui apenas {row.candidate_count} candidato(s) ativo(s). "
                    f"Considere ampliar a divulgação ou buscar candidatos ativamente."
                ),
                "data": {
                    "vacancy_id": str(row.id),
                    "vacancy_title": row.title,
                    "department": row.department,
                    "candidate_count": row.candidate_count,
                },
                "company_id": company_id,
                "created_at": datetime.now(timezone.utc),
                "is_read": False,
                "suggested_action": (
                    f"Iniciar sourcing ativo para a vaga '{row.title}' ou "
                    f"revisar os requisitos para ampliar o pool de candidatos."
                ),
                "related_job_id": str(row.id),
            })

        return alerts

    async def check_high_scorers(self, company_id: str) -> List[Dict]:
        alerts: List[Dict] = []
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT vc.id, c.name, vc.lia_score, vc.stage, jv.title,
                           vc.candidate_id, vc.vacancy_id
                    FROM vacancy_candidates vc
                    JOIN candidates c ON vc.candidate_id = c.id
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    WHERE vc.lia_score > 0.8
                      AND vc.stage IN ('Novo', 'Triagem')
                      AND vc.status = 'active'
                      AND jv.company_id::text = :company_id
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as e:
                logger.warning(f"check_high_scorers query failed: {e}")
                return alerts

        for row in rows:
            score_pct = int((row.lia_score or 0) * 100)
            alerts.append({
                "type": "high_scorer_waiting",
                "severity": "warning",
                "title": f"Candidato de alto score aguardando: {row.name}",
                "message": (
                    f"{row.name} tem score LIA de {score_pct}% para a vaga "
                    f"'{row.title}', mas ainda está na etapa '{row.stage}'. "
                    f"Avance este candidato para evitar perder um talento qualificado."
                ),
                "data": {
                    "vacancy_candidate_id": str(row.id),
                    "candidate_id": str(row.candidate_id),
                    "candidate_name": row.name,
                    "lia_score": float(row.lia_score),
                    "stage": row.stage,
                    "vacancy_id": str(row.vacancy_id),
                    "vacancy_title": row.title,
                },
                "company_id": company_id,
                "created_at": datetime.now(timezone.utc),
                "is_read": False,
                "suggested_action": (
                    f"Avançar {row.name} (score {score_pct}%) para a próxima etapa "
                    f"do processo seletivo da vaga '{row.title}'."
                ),
                "related_candidate_id": str(row.candidate_id),
                "related_job_id": str(row.vacancy_id),
            })

        return alerts

    async def check_deadlines(self, company_id: str) -> List[Dict]:
        alerts: List[Dict] = []
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT id, title, deadline, department
                    FROM job_vacancies
                    WHERE status = 'open'
                      AND deadline IS NOT NULL
                      AND deadline BETWEEN NOW() AND NOW() + INTERVAL '7 days'
                      AND company_id::text = :company_id
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as e:
                logger.warning(f"check_deadlines query failed: {e}")
                return alerts

        for row in rows:
            days_left = (row.deadline.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days if row.deadline else 0
            severity = "critical" if days_left <= 2 else "warning"
            alerts.append({
                "type": "deadline_warning",
                "severity": severity,
                "title": f"Prazo se aproximando: {row.title}",
                "message": (
                    f"A vaga '{row.title}' ({row.department or 'sem departamento'}) "
                    f"tem prazo em {days_left} dia(s) "
                    f"({row.deadline.strftime('%d/%m/%Y') if row.deadline else 'N/A'}). "
                    f"Verifique o progresso do pipeline."
                ),
                "data": {
                    "vacancy_id": str(row.id),
                    "vacancy_title": row.title,
                    "deadline": row.deadline.isoformat() if row.deadline else None,
                    "department": row.department,
                    "days_left": days_left,
                },
                "company_id": company_id,
                "created_at": datetime.now(timezone.utc),
                "is_read": False,
                "suggested_action": (
                    f"Revisar o status da vaga '{row.title}' e garantir que as "
                    f"etapas do processo sejam concluídas antes do prazo."
                ),
                "related_job_id": str(row.id),
            })

        return alerts

    async def check_engagement_gaps(self, company_id: str) -> List[Dict]:
        alerts: List[Dict] = []
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(text("""
                    SELECT vc.candidate_id, c.name, vc.vacancy_id, jv.title,
                           vc.stage, MAX(cl.sent_at) as last_contact
                    FROM vacancy_candidates vc
                    JOIN candidates c ON vc.candidate_id = c.id
                    JOIN job_vacancies jv ON vc.vacancy_id = jv.id
                    LEFT JOIN communication_logs cl
                        ON CAST(vc.candidate_id AS VARCHAR) = cl.candidate_id
                    WHERE vc.status = 'active'
                      AND jv.status = 'open'
                      AND jv.company_id::text = :company_id
                    GROUP BY vc.candidate_id, c.name, vc.vacancy_id, jv.title, vc.stage
                    HAVING MAX(cl.sent_at) IS NULL
                       OR MAX(cl.sent_at) < NOW() - INTERVAL '10 days'
                """), {"company_id": company_id})
                rows = result.fetchall()
            except Exception as e:
                logger.warning(f"check_engagement_gaps query failed: {e}")
                return alerts

        for row in rows:
            if row.last_contact:
                days_since = (datetime.now(timezone.utc) - row.last_contact.replace(tzinfo=timezone.utc)).days
                msg = (
                    f"O último contato com {row.name} na vaga '{row.title}' "
                    f"foi há {days_since} dias. Envie uma atualização para manter o engajamento."
                )
            else:
                days_since = None
                msg = (
                    f"Nenhuma comunicação registrada com {row.name} "
                    f"na vaga '{row.title}'. Inicie o contato para alinhar expectativas."
                )

            alerts.append({
                "type": "engagement_gap",
                "severity": "info",
                "title": f"Sem contato recente: {row.name}",
                "message": msg,
                "data": {
                    "candidate_id": str(row.candidate_id),
                    "candidate_name": row.name,
                    "vacancy_id": str(row.vacancy_id),
                    "vacancy_title": row.title,
                    "stage": row.stage,
                    "days_since_contact": days_since,
                    "last_contact": row.last_contact.isoformat() if row.last_contact else None,
                },
                "company_id": company_id,
                "created_at": datetime.now(timezone.utc),
                "is_read": False,
                "suggested_action": (
                    f"Enviar uma mensagem de acompanhamento para {row.name} "
                    f"sobre o andamento do processo na vaga '{row.title}'."
                ),
                "related_candidate_id": str(row.candidate_id),
                "related_job_id": str(row.vacancy_id),
            })

        return alerts

    async def check_silver_medalists(self, company_id: str) -> List[Dict]:
        """Alert when there are warm candidates from past processes available for active vacancies."""
        from app.shared.services.silver_medalist_service import silver_medalist_service

        alerts: List[Dict] = []
        try:
            medalists = await silver_medalist_service.find_for_company(
                company_id=company_id, limit=10, max_days_lookback=90
            )
        except Exception as e:
            logger.warning(f"check_silver_medalists failed: {e}")
            return alerts

        if not medalists:
            return alerts

        # Emit a single summary alert listing the top medalists
        names = ", ".join(m["candidate_name"] for m in medalists[:3])
        extra = len(medalists) - 3
        suffix = f" e mais {extra}" if extra > 0 else ""
        alerts.append({
            "type": "silver_medalists_available",
            "severity": "info",
            "title": f"{len(medalists)} candidato(s) 'prata' disponíveis para reaproveitamento",
            "message": (
                f"Candidatos que chegaram à etapa de entrevista em processos recentes "
                f"mas não foram contratados: {names}{suffix}. "
                f"Considere convidá-los para vagas abertas similares."
            ),
            "data": {
                "total_medalists": len(medalists),
                "medalists": medalists[:5],
            },
            "company_id": company_id,
            "created_at": datetime.now(timezone.utc),
            "is_read": False,
            "suggested_action": (
                "Revisar candidatos prata e convidá-los para vagas abertas compatíveis "
                "com seu perfil e etapa atingida anteriormente."
            ),
            "related_candidate_id": medalists[0]["candidate_id"] if medalists else None,
            "related_job_id": medalists[0]["past_vacancy_id"] if medalists else None,
        })
        return alerts

    async def _store_alerts(self, alerts: List[Dict]) -> int:
        stored = 0
        async with AsyncSessionLocal() as session:
            for alert in alerts:
                try:
                    alert_id = str(uuid.uuid4())
                    now = datetime.now(timezone.utc)
                    await session.execute(text("""
                        INSERT INTO proactive_actions (
                            id, company_id, action_type, severity, title,
                            description, message, data, suggested_action,
                            status, is_read, priority, auto_executable,
                            trigger_reason, related_job_id, related_candidate_id,
                            target_user_id, created_at, updated_at
                        ) VALUES (
                            CAST(:id AS UUID),
                            CAST(:company_id AS UUID),
                            :action_type, :severity, :title,
                            :description, :message,
                            CAST(:data AS JSONB),
                            CAST(:suggested_action AS JSON),
                            :status, :is_read, :priority, :auto_executable,
                            :trigger_reason,
                            CAST(:related_job_id AS UUID),
                            CAST(:related_candidate_id AS UUID),
                            :target_user_id, :created_at, :updated_at
                        )
                    """), {
                        "id": alert_id,
                        "company_id": alert.get("company_id"),
                        "action_type": alert["type"],
                        "severity": alert.get("severity", "info"),
                        "title": alert["title"],
                        "description": alert["message"],
                        "message": alert["message"],
                        "data": json.dumps(alert.get("data", {}), default=str),
                        "suggested_action": json.dumps({"text": alert.get("suggested_action", "")}),
                        "status": "pending",
                        "is_read": False,
                        "priority": alert.get("severity", "info"),
                        "auto_executable": False,
                        "trigger_reason": alert["message"],
                        "related_job_id": alert.get("related_job_id"),
                        "related_candidate_id": alert.get("related_candidate_id"),
                        "target_user_id": alert.get("target_user_id"),
                        "created_at": now,
                        "updated_at": now,
                    })
                    stored += 1
                except Exception as e:
                    logger.error(f"Failed to store alert '{alert.get('title')}': {e}")

            try:
                await session.commit()
            except Exception as e:
                logger.error(f"Failed to commit alerts: {e}")
                await session.rollback()

        logger.info(f"Stored {stored}/{len(alerts)} proactive alerts")
        return stored


async def get_pending_alerts(
    company_id: str,
    include_read: bool = False,
    limit: int = 50,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as session:
        read_filter = "" if include_read else "AND (is_read = FALSE OR is_read IS NULL)"
        # Show alerts that are either targeted to this user OR not targeted to anyone
        user_filter = ""
        if user_id:
            user_filter = "AND (target_user_id IS NULL OR target_user_id = :user_id)"
        try:
            result = await session.execute(text(f"""
                SELECT id, company_id, action_type, severity, title,
                       description, message, data, suggested_action,
                       status, is_read, priority, related_job_id,
                       related_candidate_id, target_user_id, created_at, updated_at
                FROM proactive_actions
                WHERE CAST(company_id AS VARCHAR) = :company_id
                  AND (status = 'pending' OR status IS NULL)
                  {read_filter}
                  {user_filter}
                ORDER BY created_at DESC
                LIMIT :limit
            """), {"company_id": company_id, "limit": limit, "user_id": user_id or ""})
            rows = result.fetchall()
        except Exception as e:
            logger.error(f"Failed to fetch pending alerts: {e}")
            return []

    alerts = []
    for row in rows:
        alerts.append({
            "id": str(row.id),
            "company_id": str(row.company_id),
            "type": row.action_type,
            "severity": row.severity or row.priority or "info",
            "title": row.title,
            "message": row.message or row.description,
            "data": row.data if isinstance(row.data, dict) else {},
            "suggested_action": row.suggested_action,
            "status": row.status,
            "is_read": row.is_read or False,
            "related_job_id": str(row.related_job_id) if row.related_job_id else None,
            "related_candidate_id": str(row.related_candidate_id) if row.related_candidate_id else None,
            "target_user_id": row.target_user_id if row.target_user_id else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        })

    return alerts


async def mark_alert_read(alert_id: str) -> bool:
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("""
                UPDATE proactive_actions
                SET is_read = TRUE, updated_at = NOW()
                WHERE CAST(id AS VARCHAR) = :alert_id
            """), {"alert_id": alert_id})
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to mark alert {alert_id} as read: {e}")
            await session.rollback()
            return False


async def dismiss_alert(alert_id: str) -> bool:
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("""
                UPDATE proactive_actions
                SET status = 'dismissed', is_read = TRUE, updated_at = NOW()
                WHERE CAST(id AS VARCHAR) = :alert_id
            """), {"alert_id": alert_id})
            await session.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to dismiss alert {alert_id}: {e}")
            await session.rollback()
            return False
