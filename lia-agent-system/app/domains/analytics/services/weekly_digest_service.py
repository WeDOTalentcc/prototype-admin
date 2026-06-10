"""
Weekly Digest Service — Consolidated proactive insights for recruiters.

Aggregates data from:
- PredictiveAnalyticsService (pipeline health, at-risk vacancies)
- FairnessGuard (bias blocking stats for the week)
- ABTestingService (active tests + results)
- LearningLoopService (learned patterns)

Delivers via Teams (Adaptive Card), Chat (proactive message), and Bell notification.
"""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.pii_masking import get_masked_logger

logger = get_masked_logger(__name__)


class WeeklyDigestService:

    async def generate_digest(
        self,
        recruiter_id: str,
        recruiter_name: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        pipeline = await self._gather_pipeline_health(recruiter_id, db)
        at_risk = await self._gather_vagas_em_risco(recruiter_id, db)
        compliance = await self._gather_compliance_summary(recruiter_id, db)
        optimization = await self._gather_optimization_insights(db)
        patterns = await self._gather_patterns_learned(db)

        digest = {
            "recruiter_id": recruiter_id,
            "recruiter_name": recruiter_name,
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start": (datetime.utcnow() - timedelta(days=7)).strftime("%d/%m/%Y"),
                "end": datetime.utcnow().strftime("%d/%m/%Y"),
            },
            "pipeline_health": pipeline,
            "vagas_em_risco": at_risk,
            "compliance_summary": compliance,
            "optimization_insights": optimization,
            "patterns_learned": patterns,
        }

        logger.info(
            "[WeeklyDigest] Generated for recruiter=%s vagas_ativas=%d at_risk=%d",
            recruiter_id,
            pipeline.get("total_active_jobs", 0),
            len(at_risk.get("jobs", [])),
        )

        return digest

    async def _gather_pipeline_health(
        self, recruiter_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        """Pipeline health for the RESUMO SEMANAL card.

        Fix 2026-06-08: uses direct DB queries via SQLAlchemy instead of
        PredictiveAnalyticsService.get_analytics_dashboard(), which (a) had a
        status split-brain bug ('active' vs 'Ativa') and (b) never computed
        'total_candidates_analyzed' or 'interviews_scheduled' in its summary
        dict — so all three KPIs in the card were always 0.

        Sources:
          - total_active_jobs: JobVacancy.status canonical PT-BR list
          - candidates_screened_week: VacancyCandidate rows created in last 7d
          - interviews_scheduled: VacancyCandidate in interview-family stages
        """
        # Canonical active statuses (matches job_vacancy_crud_repository.py)
        _ACTIVE_STATUSES = ["Ativa", "Active", "active", "open", "Open", "Em Andamento"]
        # Interview-family stage names (both PT-BR and legacy EN)
        _INTERVIEW_STAGES = {
            "entrevista", "entrevista_tecnica", "entrevista_rh", "entrevista_gestor",
            "interview", "technical_interview", "hr_interview", "manager_interview",
        }
        try:
            from lia_models.job_vacancy import JobVacancy
            from app.models.candidate import VacancyCandidate

            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)

            # 1. total active jobs — company-wide (recruiter_id used as company pivot below)
            active_result = await db.execute(
                select(func.count(JobVacancy.id)).where(
                    JobVacancy.status.in_(_ACTIVE_STATUSES)
                )
            )
            total_active = active_result.scalar() or 0

            # 2. candidates screened this week (new VacancyCandidate rows)
            screened_result = await db.execute(
                select(func.count(VacancyCandidate.id)).where(
                    VacancyCandidate.created_at >= week_ago
                )
            )
            screened_week = screened_result.scalar() or 0

            # 3. candidates currently in interview stages
            interviews_result = await db.execute(
                select(func.count(VacancyCandidate.id)).where(
                    VacancyCandidate.stage_name.in_(_INTERVIEW_STAGES)
                )
            )
            interviews = interviews_result.scalar() or 0

            logger.debug(
                "[WeeklyDigest] pipeline health: active=%d screened_wk=%d interviews=%d",
                total_active, screened_week, interviews,
            )
            return {
                "total_active_jobs": total_active,
                "jobs_on_track": 0,  # not computed here; used for internal reporting
                "candidates_screened_week": screened_week,
                "interviews_scheduled": interviews,
                "conversion_rate": None,
                "conversion_change": None,
            }
        except Exception as exc:
            logger.warning("[WeeklyDigest] Pipeline health fallback: %s", exc, exc_info=True)
            return {
                "total_active_jobs": 0,
                "jobs_on_track": 0,
                "candidates_screened_week": 0,
                "interviews_scheduled": 0,
                "conversion_rate": None,
                "conversion_change": None,
                "fallback_used": True,
                "fallback_reason": str(exc),
            }

    async def _gather_vagas_em_risco(
        self, recruiter_id: str, db: AsyncSession
    ) -> dict[str, Any]:
        try:
            from app.domains.analytics.services.predictive_analytics_service import (
                PredictiveAnalyticsService,
            )
            from lia_models.job_vacancy import JobVacancy

            svc = PredictiveAnalyticsService()

            # ADR-001-EXEMPT: JobVacancy filtered by recruiter+status / User filtered by role; cross-domain reads better promoted alongside notifications domain refactor
            result = await db.execute(
                select(JobVacancy).where(
                    and_(
                        JobVacancy.created_by == recruiter_id,
                        JobVacancy.status.in_(["published", "active", "open"]),
                    )
                )
            )
            active_jobs = result.scalars().all()

            at_risk_jobs: list[dict[str, Any]] = []
            for job in active_jobs:
                try:
                    prediction = await svc.predict_time_to_fill(str(job.id), db)
                    days_open = (datetime.utcnow() - (job.created_at or datetime.utcnow())).days
                    predicted_days = prediction.get("predicted_days", 30)

                    if days_open > predicted_days * 0.8:
                        severity = "critical" if days_open > predicted_days else "attention"
                        at_risk_jobs.append({
                            "title": getattr(job, "title", "Vaga"),
                            "company": getattr(job, "company_name", ""),
                            "days_open": days_open,
                            "target_days": predicted_days,
                            "severity": severity,
                            "reason": prediction.get("risk_reason", f"Time-to-fill: {days_open} dias (meta: {predicted_days})"),
                        })
                except Exception:
                    continue

            return {"count": len(at_risk_jobs), "jobs": at_risk_jobs[:5]}
        except Exception as exc:
            logger.warning("[WeeklyDigest] At-risk vacancies fallback: %s", exc)
            return {"count": 0, "jobs": []}

    async def _gather_compliance_summary(self, recruiter_id: str, db: AsyncSession) -> dict[str, Any]:
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard

            guard = FairnessGuard()
            categories = guard.get_categories()

            try:
                from lia_messaging.notification_service import Notification
                week_ago = datetime.utcnow() - timedelta(days=7)
                result = await db.execute(
                    select(func.count()).select_from(Notification).where(
                        and_(
                            Notification.source_agent == "fairness_guard",
                            Notification.created_at >= week_ago,
                            Notification.user_id == recruiter_id,
                        )
                    )
                )
                blocks_this_week = result.scalar() or 0
            except Exception:
                blocks_this_week = 0

            return {
                "status": "ok" if blocks_this_week == 0 else "attention",
                "blocks_this_week": blocks_this_week,
                "active_categories": len(categories),
                "message": (
                    "FairnessGuard não bloqueou nenhuma triagem esta semana. Todas as avaliações dentro dos limites de equidade."
                    if blocks_this_week == 0
                    else f"FairnessGuard bloqueou {blocks_this_week} triagem(ns) esta semana. Verifique os detalhes no painel de compliance."
                ),
            }
        except Exception as exc:
            logger.warning("[WeeklyDigest] Compliance summary fallback: %s", exc)
            return {
                "status": "unknown",
                "blocks_this_week": 0,
                "active_categories": 0,
                "message": "Dados de compliance indisponíveis no momento.",
            }

    async def _gather_optimization_insights(self, db: AsyncSession) -> dict[str, Any]:
        try:
            from app.shared.learning.ab_testing_service import ABTestingService

            ab_svc = ABTestingService()
            active_tests = await ab_svc.list_active_tests(db)

            test_summaries: list[dict[str, Any]] = []
            for test in active_tests:
                test_name = test.get("test_name", "")
                try:
                    results = await ab_svc.get_test_results(test_name, db)
                    winner = results.get("winner")
                    total_obs = results.get("total_observations", 0)
                    test_summaries.append({
                        "test_name": test_name,
                        "has_winner": winner is not None,
                        "winner_variant": winner,
                        "total_observations": total_obs,
                        "status": "concluded" if winner else "in_progress",
                    })
                except Exception:
                    test_summaries.append({
                        "test_name": test_name,
                        "has_winner": False,
                        "status": "in_progress",
                    })

            return {
                "active_tests_count": len(active_tests),
                "tests": test_summaries[:3],
            }
        except Exception as exc:
            logger.warning("[WeeklyDigest] Optimization insights fallback: %s", exc)
            return {"active_tests_count": 0, "tests": []}

    async def _gather_patterns_learned(self, db: AsyncSession) -> dict[str, Any]:
        try:
            from app.shared.learning.learning_loop_service import LearningLoopService

            ll_svc = LearningLoopService()
            patterns = await ll_svc.get_patterns_for_context(
                company_id="global",
                field_name="general",
                db=db,
            )

            pattern_summaries = []
            for p in (patterns or [])[:3]:
                pattern_summaries.append({
                    "type": getattr(p, "pattern_type", "unknown"),
                    "confidence": getattr(p, "confidence_score", 0),
                    "sample_size": getattr(p, "sample_size", 0),
                })

            return {
                "total_patterns": len(patterns or []),
                "top_patterns": pattern_summaries,
            }
        except Exception as exc:
            logger.warning("[WeeklyDigest] Patterns learned fallback: %s", exc)
            return {"total_patterns": 0, "top_patterns": []}

    async def deliver_digest(
        self,
        digest: dict[str, Any],
        recruiter_id: str,
        recruiter_name: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        from app.domains.analytics.services.digest_formatter import (
            BellDigestFormatter,
            ChatDigestFormatter,
            TeamsDigestFormatter,
        )

        results = {"teams": None, "chat": None, "bell": None, "email": None}

        try:
            bell_fmt = BellDigestFormatter()
            bell_data = bell_fmt.format(digest)
            from lia_messaging.notification_service import (
                NotificationService,
            )
            from lia_messaging.notification_service import (
                NotificationType as NSNotificationType,
            )

            ns = NotificationService()
            bell_result = await ns.create_notification(
                user_id=recruiter_id,
                title=bell_data["title"],
                message=bell_data["message"],
                notification_type=NSNotificationType.INFO,
                category="weekly_digest",
                source_agent="weekly_digest_service",
                source_trigger="weekly_digest",
                action_url=bell_data.get("action_url", "/chat"),
                action_label="Ver no Chat",
                channels=["bell"],
                db=db,
            )
            results["bell"] = {"success": True, "id": bell_result.get("id") if isinstance(bell_result, dict) else str(bell_result)}
        except Exception as exc:
            logger.warning("[WeeklyDigest] Bell delivery failed: %s", exc)
            results["bell"] = {"success": False, "error": str(exc)}

        try:
            chat_fmt = ChatDigestFormatter()
            chat_data = chat_fmt.format(digest)
            from lia_messaging.notification_service import (
                NotificationChannel,
                NotificationService,
                ProactiveNotificationType,
            )

            ns = NotificationService()
            chat_result = await ns.send_multi_channel_notification(
                user_id=recruiter_id,
                title=chat_data["title"],
                message=chat_data["message"],
                channels=[NotificationChannel.CHAT],
                proactive_type=ProactiveNotificationType.MORNING_BRIEFING,
                priority="normal",
                data={"digest_type": "weekly", "generated_at": digest["generated_at"]},
                suggested_actions=["Detalhar vagas em risco", "Ver métricas completas"],
                db=db,
            )
            results["chat"] = {"success": True, "details": chat_result}
        except Exception as exc:
            logger.warning("[WeeklyDigest] Chat delivery failed: %s", exc)
            results["chat"] = {"success": False, "error": str(exc)}

        try:
            teams_fmt = TeamsDigestFormatter()
            teams_card = teams_fmt.format(digest)
            from app.domains.communication.services.teams_service import (
                TeamsService,
                resolve_tenant_teams_webhook_url,
            )

            _wh_url: str | None = None
            try:
                from sqlalchemy import select as _sel
                from app.auth.models import User as _User
                _ur = await db.execute(_sel(_User.company_id).where(_User.id == recruiter_id))
                _company_id = _ur.scalar_one_or_none()
                if _company_id:
                    _wh_url, _ = await resolve_tenant_teams_webhook_url(str(_company_id), db)
            except Exception as _url_exc:
                logger.debug("[WeeklyDigest] Could not resolve per-tenant Teams URL: %s", _url_exc)

            ts = TeamsService(webhook_url=_wh_url)
            teams_result = await ts.send_adaptive_card(teams_card, webhook_url=_wh_url)
            results["teams"] = {"success": True, "details": teams_result}
        except Exception as exc:
            logger.warning("[WeeklyDigest] Teams delivery failed: %s", exc)
            results["teams"] = {"success": False, "error": str(exc)}

        try:
            # E6 (2026-06-09): WeeklyDigest tambem por EMAIL (era so bell+chat+teams).
            from lia_messaging.notification_service import (
                NotificationChannel,
                NotificationService,
            )

            email_data = BellDigestFormatter().format(digest)
            ns = NotificationService()
            email_result = await ns.send_multi_channel_notification(
                user_id=recruiter_id,
                title=email_data["title"],
                message=email_data["message"],
                channels=[NotificationChannel.EMAIL],
                data={
                    "digest_type": "weekly",
                    "action_url": email_data.get("action_url", "/chat"),
                },
                db=db,
            )
            results["email"] = {"success": True, "details": email_result}
        except Exception as exc:
            logger.warning("[WeeklyDigest] Email delivery failed: %s", exc)
            results["email"] = {"success": False, "error": str(exc)}

        logger.info(
            "[WeeklyDigest] Delivered to recruiter=%s bell=%s chat=%s teams=%s",
            recruiter_id,
            results["bell"].get("success") if results["bell"] else False,
            results["chat"].get("success") if results["chat"] else False,
            results["teams"].get("success") if results["teams"] else False,
        )

        return results

    async def generate_and_deliver(
        self,
        recruiter_id: str,
        recruiter_name: str,
        db: AsyncSession,
    ) -> dict[str, Any]:
        digest = await self.generate_digest(recruiter_id, recruiter_name, db)
        delivery = await self.deliver_digest(digest, recruiter_id, recruiter_name, db)

        try:
            from app.shared.services.audit_service import AuditService
            await AuditService.log_decision(  # AUDIT-NO-DEMO: recruiter digest delivery (no candidate decision; LGPD Art.20 N/A)
                decision_type="weekly_digest_delivered",
                agent="WeeklyDigestService",
                input_data={"recruiter_id": recruiter_id, "period": digest.get("period", {})},
                output_data={"channels_delivered": list(delivery.keys()) if isinstance(delivery, dict) else []},
                rationale="Digest semanal consolidado entregue automaticamente",
                confidence=1.0,
                company_id=None,
                db=db,
            )
        except Exception as exc:
            logger.debug("[WeeklyDigest] Audit log failed (non-blocking): %s", exc)

        return {"digest": digest, "delivery": delivery}

    async def send_to_all_recruiters(self, db: AsyncSession) -> dict[str, Any]:
        try:
            from app.auth.models import User

            # ADR-001-EXEMPT: JobVacancy filtered by recruiter+status / User filtered by role; cross-domain reads better promoted alongside notifications domain refactor
            result = await db.execute(
                select(User).where(User.role.in_(["recruiter", "admin", "manager"]))
            )
            users = result.scalars().all()

            sent = 0
            skipped = 0
            errors = 0

            for user in users:
                prefs = getattr(user, "notification_preferences", None) or {}
                if isinstance(prefs, dict) and prefs.get("weekly_report_enabled") is False:
                    skipped += 1
                    continue

                try:
                    await self.generate_and_deliver(
                        recruiter_id=str(user.id),
                        recruiter_name=getattr(user, "name", getattr(user, "email", "Recrutador")),
                        db=db,
                    )
                    sent += 1
                except Exception as exc:
                    logger.error("[WeeklyDigest] Failed for user=%s: %s", user.id, exc)
                    errors += 1

            logger.info(
                "[WeeklyDigest] Batch complete: sent=%d skipped=%d errors=%d",
                sent, skipped, errors,
            )
            return {"sent": sent, "skipped": skipped, "errors": errors, "total": len(users)}
        except Exception as exc:
            logger.error("[WeeklyDigest] send_to_all_recruiters failed: %s", exc)
            return {"sent": 0, "skipped": 0, "errors": 1, "error": str(exc)}


weekly_digest_service = WeeklyDigestService()


def get_weekly_digest_service() -> "WeeklyDigestService":
    return weekly_digest_service
