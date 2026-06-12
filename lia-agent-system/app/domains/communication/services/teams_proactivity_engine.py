"""
Teams Proactivity Engine.
LIA proactively reaches out to recruiters via Teams based on platform events.
"""
import logging
from datetime import datetime, timedelta
from typing import Any


logger = logging.getLogger(__name__)


class TeamsProactivityEngine:
    """
    Monitors recruitment platform events and proactively notifies recruiters via Teams.

    Three intelligence levels:
    1. Event-driven: new candidate, screening complete, etc.
    2. Contextual: pipeline stalled, deadlines approaching
    3. Intelligent: pattern-based suggestions before recruiter notices
    """

    async def on_candidate_applied(
        self,
        candidate_id: str,
        candidate_name: str,
        vacancy_id: str,
        vacancy_title: str,
        company_id: str,
        estimated_score: float | None = None,
    ) -> bool:
        """Triggered when a new candidate applies to a vacancy."""
        from app.domains.communication.services.teams_card_renderer import teams_card_renderer

        card = teams_card_renderer.render_new_candidate_card(
            candidate_name=candidate_name,
            job_title=vacancy_title,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            estimated_score=estimated_score,
        )

        refs = await self._get_recruiter_refs_for_vacancy(vacancy_id, company_id)
        return await self._broadcast_card(card, refs)

    async def on_screening_complete(
        self,
        candidate_id: str,
        candidate_name: str,
        vacancy_id: str,
        job_title: str,
        match_score: float,
        recommendation: str,
        company_id: str,
        recruiter_teams_id: str | None = None,
    ) -> bool:
        """Triggered when WSI/BARS screening completes."""
        from app.domains.communication.services.teams_card_renderer import teams_card_renderer

        card = teams_card_renderer.render_screening_complete_card(
            candidate_name=candidate_name,
            job_title=job_title,
            match_score=match_score,
            recommendation=recommendation,
            candidate_id=candidate_id,
        )

        if recruiter_teams_id:
            ref = await self._get_conversation_ref(teams_user_id=recruiter_teams_id)
            if ref:
                return await self._send_card_to_ref(card, ref)

        refs = await self._get_recruiter_refs_for_vacancy(vacancy_id, company_id)
        return await self._broadcast_card(card, refs)

    async def check_stalled_pipelines(self, company_id: str | None = None) -> int:
        """
        Periodic check: find pipelines stalled for 5+ days and notify recruiter.
        Returns number of notifications sent.
        """
        from app.domains.communication.services.teams_card_renderer import teams_card_renderer

        try:
            stalled = await self._find_stalled_pipelines(company_id, stalled_days=5)
            sent = 0
            for item in stalled:
                card = teams_card_renderer.render_stalled_pipeline_card(
                    vacancy_title=item["vacancy_title"],
                    candidates_count=item["candidates_count"],
                    days_stalled=item["days_stalled"],
                    vacancy_id=item["vacancy_id"],
                )
                refs = await self._get_recruiter_refs_for_vacancy(item["vacancy_id"], item["company_id"])
                if await self._broadcast_card(card, refs):
                    sent += 1
            return sent
        except Exception as e:
            logger.error(f"[ProactivityEngine] check_stalled_pipelines error: {e}", exc_info=True)
            return 0

    async def check_approaching_deadlines(self, company_id: str | None = None) -> int:
        """
        Periodic check: find vacancies with deadlines in <=7 days.
        Returns number of notifications sent.
        """
        from app.domains.communication.services.teams_card_renderer import teams_card_renderer

        try:
            deadlines = await self._find_approaching_deadlines(company_id, days_ahead=7)
            sent = 0
            for item in deadlines:
                card = teams_card_renderer.render_deadline_card(
                    vacancy_title=item["vacancy_title"],
                    days_remaining=item["days_remaining"],
                    candidates_in_pipeline=item["candidates_in_pipeline"],
                    vacancy_id=item["vacancy_id"],
                )
                refs = await self._get_recruiter_refs_for_vacancy(item["vacancy_id"], item["company_id"])
                if await self._broadcast_card(card, refs):
                    sent += 1
            return sent
        except Exception as e:
            logger.error(f"[ProactivityEngine] check_approaching_deadlines error: {e}", exc_info=True)
            return 0

    # --- DB queries ----------------------------------------------------------

    async def _find_stalled_pipelines(
        self, company_id: str | None, stalled_days: int = 5
    ) -> list[dict[str, Any]]:
        """Query DB for vacancies with candidates stuck for stalled_days."""
        try:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal

            cutoff = datetime.utcnow() - timedelta(days=stalled_days)

            async with AsyncSessionLocal() as db:
                q = text("""
                    SELECT
                        jv.id as vacancy_id,
                        jv.title as vacancy_title,
                        jv.company_id,
                        COUNT(vc.id) as candidates_count,
                        EXTRACT(DAY FROM NOW() - MAX(vc.updated_at)) as days_stalled
                    FROM job_vacancies jv
                    JOIN vacancy_candidates vc ON vc.vacancy_id = jv.id
                    WHERE jv.status = 'active'
                        AND vc.stage NOT IN ('hired', 'rejected', 'withdrawn')
                        AND vc.updated_at < :cutoff
                        AND (:company_id IS NULL OR jv.company_id = :company_id)
                    GROUP BY jv.id, jv.title, jv.company_id
                    HAVING COUNT(vc.id) > 0
                    LIMIT 20
                """)
                result = await db.execute(q, {"cutoff": cutoff, "company_id": company_id})
                rows = result.fetchall()
                return [
                    {
                        "vacancy_id": str(r.vacancy_id),
                        "vacancy_title": r.vacancy_title,
                        "company_id": str(r.company_id),
                        "candidates_count": r.candidates_count,
                        "days_stalled": int(r.days_stalled or stalled_days),
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.warning(f"[ProactivityEngine] _find_stalled_pipelines: {e}")
            return []

    async def _find_approaching_deadlines(
        self, company_id: str | None, days_ahead: int = 7
    ) -> list[dict[str, Any]]:
        """Query DB for vacancies with deadlines in the next days_ahead days."""
        try:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal

            now = datetime.utcnow()
            deadline_cutoff = now + timedelta(days=days_ahead)

            async with AsyncSessionLocal() as db:
                q = text("""
                    SELECT
                        jv.id as vacancy_id,
                        jv.title as vacancy_title,
                        jv.company_id,
                        jv.deadline,
                        EXTRACT(DAY FROM jv.deadline - NOW()) as days_remaining,
                        COUNT(vc.id) as candidates_in_pipeline
                    FROM job_vacancies jv
                    LEFT JOIN vacancy_candidates vc
                        ON vc.vacancy_id = jv.id
                        AND vc.stage NOT IN ('hired', 'rejected', 'withdrawn')
                    WHERE jv.status = 'active'
                        AND jv.deadline IS NOT NULL
                        AND jv.deadline > :now
                        AND jv.deadline <= :cutoff
                        AND (:company_id IS NULL OR jv.company_id = :company_id)
                    GROUP BY jv.id, jv.title, jv.company_id, jv.deadline
                    LIMIT 20
                """)
                result = await db.execute(q, {"now": now, "cutoff": deadline_cutoff, "company_id": company_id})
                rows = result.fetchall()
                return [
                    {
                        "vacancy_id": str(r.vacancy_id),
                        "vacancy_title": r.vacancy_title,
                        "company_id": str(r.company_id),
                        "days_remaining": max(0, int(r.days_remaining or 0)),
                        "candidates_in_pipeline": r.candidates_in_pipeline or 0,
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.warning(f"[ProactivityEngine] _find_approaching_deadlines: {e}")
            return []

    async def _get_recruiter_refs_for_vacancy(
        self, vacancy_id: str, company_id: str
    ) -> list[dict[str, Any]]:
        """Get stored Teams conversation refs for recruiters responsible for a vacancy."""
        try:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                q = text("""
                    SELECT DISTINCT tc.service_url, tc.conversation_id, tc.user_id
                    FROM teams_conversations tc
                    WHERE tc.company_id = :company_id
                    ORDER BY tc.created_at DESC
                    LIMIT 5
                """)
                result = await db.execute(q, {"company_id": company_id})
                rows = result.fetchall()
                refs = []
                for r in rows:
                    refs.append({
                        "service_url": r.service_url,
                        "conversation_id": r.conversation_id,
                        "user_id": r.user_id,
                    })
                return refs
        except Exception as e:
            logger.warning(f"[ProactivityEngine] _get_recruiter_refs: {e}")
            return []

    async def _get_conversation_ref(self, teams_user_id: str) -> dict[str, Any] | None:
        """Get the most recent conversation reference for a specific Teams user."""
        try:
            from sqlalchemy import text

            from app.core.database import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                q = text("""
                    SELECT service_url, conversation_id
                    FROM teams_conversations
                    WHERE user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """)
                result = await db.execute(q, {"user_id": teams_user_id})
                row = result.fetchone()
                if row:
                    return {"service_url": row.service_url, "conversation_id": row.conversation_id}
        except Exception as e:
            logger.warning(f"[ProactivityEngine] _get_conversation_ref: {e}")
        return None

    # --- Sending helpers -----------------------------------------------------

    async def _broadcast_card(self, card: dict[str, Any], refs: list[dict[str, Any]]) -> bool:
        """Send card to all refs. Returns True if at least one succeeded."""
        from app.domains.communication.services.teams_simple import simple_teams_bot

        if not refs:
            logger.info("[ProactivityEngine] No Teams conversation references found, skipping.")
            return False

        success = False
        for ref in refs:
            try:
                ok = await simple_teams_bot.send_adaptive_card(
                    service_url=ref["service_url"],
                    conversation_id=ref["conversation_id"],
                    card_payload=card,
                )
                if ok:
                    success = True
            except Exception as e:
                logger.warning(f"[ProactivityEngine] Failed to send to {ref}: {e}")
        return success

    async def _send_card_to_ref(self, card: dict[str, Any], ref: dict[str, Any]) -> bool:
        from app.domains.communication.services.teams_simple import simple_teams_bot
        try:
            return await simple_teams_bot.send_adaptive_card(
                service_url=ref["service_url"],
                conversation_id=ref["conversation_id"],
                card_payload=card,
            )
        except Exception as e:
            logger.warning(f"[ProactivityEngine] _send_card_to_ref error: {e}")
            return False


    async def send_daily_digest(self, company_id: str | None = None) -> int:
        """
        Send the daily morning digest to all recruiters via Teams.
        Shows: active jobs, pending candidates, critical alerts, suggested actions.
        Called by cron at 08:00 every weekday.
        """
        from datetime import datetime, timedelta

        from sqlalchemy import and_, func, select

        from app.domains.communication.services.teams_card_renderer import teams_card_renderer
        from app.models import Candidate, JobVacancy

        sent = 0
        try:
            async for db in self._get_db():
                # Pull live metrics
                today = datetime.utcnow()
                week_ago = today - timedelta(days=7)
                week_ahead = today + timedelta(days=7)

                # Active jobs
                jobs_q = select(func.count(JobVacancy.id)).where(
                    JobVacancy.status.in_(["open", "active", "Open", "Active", "Em Andamento"])
                )
                if company_id:
                    jobs_q = jobs_q.where(JobVacancy.company_id == company_id)
                active_jobs = (await db.execute(jobs_q)).scalar() or 0

                # Expiring soon
                expiring_q = select(func.count(JobVacancy.id)).where(
                    and_(
                        JobVacancy.status.in_(["open", "active", "Open", "Active"]),
                        JobVacancy.deadline is not None,
                        JobVacancy.deadline <= week_ahead,
                    )
                )
                if company_id:
                    expiring_q = expiring_q.where(JobVacancy.company_id == company_id)
                expiring_jobs = (await db.execute(expiring_q)).scalar() or 0

                # New candidates (last 7 days)
                cands_q = select(func.count(Candidate.id)).where(
                    Candidate.created_at >= week_ago
                )
                if company_id:
                    cands_q = cands_q.where(Candidate.company_id == company_id)
                new_candidates = (await db.execute(cands_q)).scalar() or 0

                # Stalled pipelines (reuse existing check)
                stalled = await self._find_stalled_pipelines(db, company_id)

                # Build digest card
                from datetime import datetime as _dt
                weekday_names = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                weekday = weekday_names[_dt.now().weekday()]

                body_lines = [
                    f"**{weekday}, {_dt.now().strftime('%d/%m/%Y')}** — Bom dia! ☀️",
                    "",
                    f"📋 **{active_jobs}** vagas ativas",
                    f"👥 **{new_candidates}** novos candidatos esta semana",
                ]
                if expiring_jobs:
                    body_lines.append(f"⏰ **{expiring_jobs}** vaga(s) com prazo nos próximos 7 dias")
                if stalled:
                    body_lines.append(f"⚠️ **{len(stalled)}** pipeline(s) parado(s) há 5+ dias")

                body_text = "\n".join(body_lines)

                actions = [
                    {"type": "Action.Submit", "title": "📊 Ver pipeline", "data": {"message": "Como está a saúde geral do pipeline?"}},
                    {"type": "Action.Submit", "title": "👥 Candidatos aguardando", "data": {"message": "Quais candidatos estão aguardando triagem ou retorno?"}},
                    {"type": "Action.Submit", "title": "⚠️ Vagas críticas", "data": {"message": "Quais vagas estão em estado crítico?"}},
                    {"type": "Action.OpenUrl", "title": "🔗 Abrir plataforma", "url": "https://app.wedotalent.com"},
                ]

                card = teams_card_renderer.render_notification_card(
                    title="📅 Resumo Diário — LIA",
                    body_text=body_text,
                    actions=actions,
                    color="#6366F1",
                    emoji="📅",
                )

                # Get all recruiters refs for this company
                refs = await self._get_recruiter_refs_for_vacancy(
                    vacancy_id=None, company_id=company_id or ""
                )
                if not refs and company_id:
                    # Broader query — all refs for company
                    try:
                        async for db2 in self._get_db():
                            result = await db2.execute(
                                "SELECT DISTINCT service_url, conversation_id FROM teams_conversations WHERE company_id = :cid LIMIT 50",
                                {"cid": company_id}
                            )
                            refs = [{"service_url": r.service_url, "conversation_id": r.conversation_id} for r in result]
                            break
                    except Exception:
                        pass

                if refs:
                    sent_ok = await self._broadcast_card(card, refs)
                    sent = len(refs) if sent_ok else 0
                break  # Only one DB iteration needed

        except Exception as e:
            logger.error(f"[ProactivityEngine] send_daily_digest error: {e}", exc_info=True)
        return sent

    async def _get_db(self):
        """Yield a DB session for internal use."""
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            yield session


teams_proactivity_engine = TeamsProactivityEngine()


async def _safe_teams_hook(coro_func, **kwargs):
    # Dispara hook Teams sem propagar excecoes (fire-and-forget).
    # Uso: asyncio.create_task(_safe_teams_hook(engine.on_candidate_applied, ...))
    try:
        await coro_func(**kwargs)
    except Exception as _exc:
        import logging as _log
        _log.getLogger(__name__).warning(
            "Teams hook falhou (ignorado): %s", _exc, exc_info=False
        )
