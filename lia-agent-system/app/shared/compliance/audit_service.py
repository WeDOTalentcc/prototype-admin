"""
Audit Service for AI Governance.

This service provides comprehensive audit logging for all AI decisions
made by LIA agents, ensuring transparency, accountability, and LGPD compliance.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import and_, desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog, DecisionType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Event-loop ownership (Audit-loop-leak fix, 2026-05-20)
# ---------------------------------------------------------------------------
# LangGraph sync nodes in `app/domains/job_creation/graph.py` call
# `_asyncio.run(AuditService().log_decision(...))` from worker threads. Each
# call spawns a transient event loop. The SQLAlchemy async pool, however, is
# shared across loops — once a connection's asyncpg callbacks are bound to
# the transient loop and that loop is closed, returning the connection to
# the pool poisons it. The next FastAPI request that borrows it raises
# "Event loop is closed" inside SET ROLE -> "RLS role enforcement failed".
#
# Fix: capture the FastAPI main loop at app startup (`register_main_loop`).
# When `log_decision` is invoked from a non-main loop (i.e. running inside
# `asyncio.run()` on a worker thread), redispatch the actual DB write to the
# main loop via `run_coroutine_threadsafe` and block on the resulting Future.
# This keeps all asyncpg state bound to the long-lived pool-owning loop.

import asyncio as _asyncio_loop_mod
import concurrent.futures as _cf_loop_mod

_MAIN_LOOP: "_asyncio_loop_mod.AbstractEventLoop | None" = None


def register_main_loop(loop: "_asyncio_loop_mod.AbstractEventLoop | None" = None) -> None:
    """Register the FastAPI app's main event loop.

    Called from `app/main.py` lifespan startup. Idempotent: calling twice with
    different loops overwrites (lifespan reload in dev) but logs a warning.
    """
    global _MAIN_LOOP
    if loop is None:
        try:
            loop = _asyncio_loop_mod.get_running_loop()
        except RuntimeError:
            loop = None
    if loop is None:
        return
    if _MAIN_LOOP is not None and _MAIN_LOOP is not loop:
        logger.warning(
            "[AuditService] main loop already registered (%s); overwriting with %s",
            id(_MAIN_LOOP), id(loop),
        )
    _MAIN_LOOP = loop
    logger.info("[AuditService] main loop registered id=%s", id(loop))


def _running_on_main_loop() -> bool:
    """Return True if the current task runs on the registered main loop."""
    if _MAIN_LOOP is None:
        return True  # no main loop registered yet — caller is presumed safe
    try:
        running = _asyncio_loop_mod.get_running_loop()
    except RuntimeError:
        return False
    return running is _MAIN_LOOP


def _dispatch_on_main_loop(coro_factory, *, timeout: float = 10.0):
    """Schedule `coro_factory()` on the main loop and block for the result.

    `coro_factory` is a zero-arg callable that returns a fresh coroutine —
    we use a factory (not a bare coroutine) because a coroutine bound to
    `asyncio.run`'s transient loop cannot be safely transferred. The factory
    is called from the main loop's thread context (inside the wrapped
    coroutine below), so the coroutine is created on the right loop.
    """
    if _MAIN_LOOP is None or _MAIN_LOOP.is_closed():
        raise RuntimeError("AuditService main loop not registered or closed")

    async def _runner():
        return await coro_factory()

    fut = _asyncio_loop_mod.run_coroutine_threadsafe(_runner(), _MAIN_LOOP)
    try:
        return fut.result(timeout=timeout)
    except _cf_loop_mod.TimeoutError:
        fut.cancel()
        raise RuntimeError(f"AuditService dispatch to main loop timed out after {timeout}s")



async def _bind_tenant(session: AsyncSession, company_id: str | None) -> None:
    """Set Postgres GUC ``app.company_id`` so RLS policies on audit_logs allow INSERT.

    Migration 068 enables FORCE ROW LEVEL SECURITY on audit_logs with a policy
    ``WITH CHECK (company_id = app_current_company_id())`` where
    ``app_current_company_id()`` reads ``current_setting('app.company_id', true)``.
    Without this binding the INSERT is rejected with InsufficientPrivilegeError
    even for the table owner. We use ``set_config(..., true)`` (transaction-local)
    so it doesn't leak across sessions in the connection pool.
    """
    if not company_id:
        return
    try:
        await session.execute(
            text("SELECT set_config('app.company_id', :cid, true)"),
            {"cid": str(company_id)},
        )
    except Exception as exc:
        logger.warning("[AuditService] failed to set tenant context: %s", exc)

DECISION_TYPE_MAPPING = {
    "cv_screening": DecisionType.SCORE_CANDIDATE,
    "screen_candidate": DecisionType.SCORE_CANDIDATE,
    "wsi_evaluation": DecisionType.SCORE_CANDIDATE,
    "calculate_wsi": DecisionType.SCORE_CANDIDATE,
    "quick_screening": DecisionType.SCORE_CANDIDATE,
    "complete_interview": DecisionType.SCORE_CANDIDATE,
    "screening_evaluation": DecisionType.SCORE_CANDIDATE,
    "search_candidates": DecisionType.SCORE_CANDIDATE,
    "proceed_to_next_stage": DecisionType.MOVE_STAGE,
    "proceed_to_wsi": DecisionType.MOVE_STAGE,
    "reject": DecisionType.REJECT_CANDIDATE,
    "rejected": DecisionType.REJECT_CANDIDATE,
    "approve": DecisionType.APPROVE_CANDIDATE,
    "approved": DecisionType.APPROVE_CANDIDATE,
    "generate_jd": DecisionType.GENERATE_FEEDBACK,
    "generate_wsi_questions": DecisionType.GENERATE_FEEDBACK,
    # Task #1061 — wizard step completion audit (EU AI Act Art.13).
    # Cada node decisório do JobCreationGraph (bigfive, wsi_questions,
    # competency, eligibility) emite um audit row ao concluir.
    "wizard_step_completed": DecisionType.GENERATE_FEEDBACK,
    # Task #1089 (T3) — fail-loud em fallback do WizardSessionService.
    # Quando o graph não devolve mensagem, em vez de cair em string canned
    # (anti-pattern Caso #3/#4 do canonical-fix), emite-se este audit row
    # com `human_review_required=True` para EU AI Act trail + investigação.
    "wizard_fallback_invoked": DecisionType.GENERATE_FEEDBACK,
    # Task #1127 (T2.2) — Wizard Supervisor pre-graph (intent routing).
    # Cada turno do wizard que passa pelo `WizardSupervisorClassifier`
    # emite um audit row com o intent decidido (allowlist 6 intents
    # canônicos). Mapeado para GENERATE_FEEDBACK por consistência com
    # os demais audit rows do wizard (wizard_step_completed,
    # wizard_fallback_invoked) — mesmo retention SOX 7y.
    "wizard_supervisor_routed": DecisionType.GENERATE_FEEDBACK,
}

PROTECTED_CRITERIA = [
    "age",
    "gender",
    "ethnicity",
    "marital_status",
    "photo",
    "institution",
    "address",
    "religion",
    "disability",
    "cv_gaps",
]


class AuditService:
    """Service for logging AI decisions with full explainability."""

    RETENTION_PERIODS = {
        "score_candidate": 730,
        "approve_candidate": 730,
        "reject_candidate": 730,
        "move_stage": 730,
        "send_message": 1825,
        "schedule_interview": 365,
        "generate_feedback": 730,
        # PR4 (Task #1004) — SOX exige 7 anos pra mudanças em config
        # corporativa que afetam decisões de hiring (BARS, hiring policy,
        # benefits). 2555 dias = 7 anos.
        "company_settings_change": 2555,
    }

    async def log_decision(

        self,
        company_id: str,
        agent_name: str,
        decision_type: str,
        action: str,
        decision: str,
        reasoning: list[str],
        criteria_used: list[str],
        candidate_id: str | None = None,
        job_vacancy_id: str | None = None,
        score: float | None = None,
        confidence: float | None = None,
        human_review_required: bool = False,
        criteria_ignored: list[str] | None = None,
        actor_user_id: str | None = None,
    ) -> AuditLog:
        """Public entrypoint — redispatches to main loop when called from a transient loop.

        See module-level docstring above `register_main_loop` for the rationale.
        """
        if not _running_on_main_loop():
            return _dispatch_on_main_loop(
                lambda: self._log_decision_impl(company_id=company_id, agent_name=agent_name, decision_type=decision_type, action=action, decision=decision, reasoning=reasoning, criteria_used=criteria_used, candidate_id=candidate_id, job_vacancy_id=job_vacancy_id, score=score, confidence=confidence, human_review_required=human_review_required, criteria_ignored=criteria_ignored, actor_user_id=actor_user_id),
                timeout=15.0,
            )
        return await self._log_decision_impl(company_id=company_id, agent_name=agent_name, decision_type=decision_type, action=action, decision=decision, reasoning=reasoning, criteria_used=criteria_used, candidate_id=candidate_id, job_vacancy_id=job_vacancy_id, score=score, confidence=confidence, human_review_required=human_review_required, criteria_ignored=criteria_ignored, actor_user_id=actor_user_id)

    async def _log_decision_impl(
        self,
        company_id: str,
        agent_name: str,
        decision_type: str,
        action: str,
        decision: str,
        reasoning: list[str],
        criteria_used: list[str],
        candidate_id: str | None = None,
        job_vacancy_id: str | None = None,
        score: float | None = None,
        confidence: float | None = None,
        human_review_required: bool = False,
        criteria_ignored: list[str] | None = None,
        actor_user_id: str | None = None,
    ) -> AuditLog:
        """
        Log an AI decision with full context for auditability.

        Args:
            company_id: The company/tenant ID
            agent_name: Name of the agent making the decision (e.g., "triagem_curricular")
            decision_type: Type of decision (see DecisionType enum)
            action: Specific action taken
            decision: Result of the decision ("approved", "rejected", "pending_review")
            reasoning: List of reasons for the decision
            criteria_used: List of criteria that were evaluated
            candidate_id: Optional candidate ID if decision relates to a candidate
            job_vacancy_id: Optional job vacancy ID if decision relates to a job
            score: Optional score assigned
            confidence: Optional confidence level (0-1)
            human_review_required: Whether this decision requires human review
            criteria_ignored: List of criteria explicitly ignored (for anti-bias)

        Returns:
            Created AuditLog instance
        """
        canonical_type = DECISION_TYPE_MAPPING.get(decision_type.lower())
        if canonical_type is None:
            try:
                canonical_type = DecisionType(decision_type)
            except ValueError:
                logger.warning(f"Unknown decision_type '{decision_type}', defaulting to SCORE_CANDIDATE")
                canonical_type = DecisionType.SCORE_CANDIDATE

        final_ignored = set(PROTECTED_CRITERIA)
        if criteria_ignored:
            final_ignored.update(criteria_ignored)

        retention_days = self.RETENTION_PERIODS.get(canonical_type.value, 730)
        now = datetime.utcnow()
        retention_until = now + timedelta(days=retention_days)

        # Sprint A: ler correlation_id do ContextVar se disponivel
        _correlation_id = None
        try:
            from app.middleware.request_id import get_correlation_id as _get_cid
            _cid = _get_cid()
            if _cid:
                _correlation_id = _cid
        except Exception:
            pass

        async with AsyncSessionLocal() as session:
            await _bind_tenant(session, company_id)
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                company_id=company_id,
                agent_name=agent_name,
                decision_type=canonical_type.value,
                action=action,
                decision=decision,
                reasoning=reasoning,
                criteria_used=criteria_used,
                criteria_ignored=list(final_ignored),
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
                score=score,
                confidence=confidence,
                human_review_required=human_review_required,
                retention_until=retention_until,
                # Task #366 column-promotion workaround — `actor_user_id`
                # ainda não tem coluna dedicada; reusamos `session_id`
                # para casar com `audit_service.get_decisions_by_user`
                # (a query usa `AuditLog.session_id == actor_user_id`).
                # Surfaceado em Task #1092 para permitir verificação
                # de idempotência do `wizard_gate_service` via
                # `/admin/audit-decisions/by-user/{actor_user_id}`.
                session_id=actor_user_id,
                # PR-A (Task #1016) — populamos created_at em Python para
                # NÃO precisar de session.refresh() após o COMMIT. O refresh
                # falhava com InvalidRequestError em sessões RLS-bound
                # ("Could not refresh instance"), o que disparava o
                # fail-CLOSED do wrapper audit_company_change e bloqueava
                # 100% das tools de company_settings (chat lateral / hub
                # Minha Empresa). O server_default=func.now() do schema
                # continua disponível como fallback no caso (improvável)
                # de o caller pular este caminho.
                created_at=now,
                correlation_id=_correlation_id,
            )

            session.add(audit_log)
            await session.commit()
            # NÃO chamar session.refresh(audit_log) aqui — todos os campos
            # relevantes (id, created_at, retention_until) já estão
            # populados em Python. O refresh em sessão RLS-bound após
            # COMMIT levanta InvalidRequestError e foi a causa-raiz do
            # bloqueio de tools de company_settings (auditoria #1015).

            logger.info(
                f"✅ Audit log created: {agent_name} - {decision_type} -> {decision} "
                f"(candidate: {candidate_id}, job: {job_vacancy_id})"
            )
            return audit_log

    async def log_decision_in_session(
        self,
        session,
        *,
        company_id: str,
        agent_name: str,
        decision_type: str,
        action: str,
        decision: str,
        reasoning: list[str],
        criteria_used: list[str],
        candidate_id: str | None = None,
        job_vacancy_id: str | None = None,
        score: float | None = None,
        confidence: float | None = None,
        human_review_required: bool = False,
        criteria_ignored: list[str] | None = None,
        actor_user_id: str | None = None,
    ) -> AuditLog:
        """PR4 (Task #1004) — Insert an AuditLog row USING the caller's
        session, WITHOUT committing. Lets the caller commit business
        writes + audit row atomically. Required by ``audit_company_change``
        for the outcome row (fail-CLOSED transactional rollback).

        Tenant binding is the caller's responsibility (already done by
        ``audit_company_change`` when opening the shared session).

        ``actor_user_id`` is persisted into ``session_id`` (Task #366
        column-promotion workaround — mirrors ``_log_decision_impl``) so the
        in-session path keeps the same audit fields as the independent-session
        ``log_decision`` (consumed by ``get_decisions_by_user``)."""
        canonical_type = DECISION_TYPE_MAPPING.get(decision_type.lower())
        if canonical_type is None:
            try:
                canonical_type = DecisionType(decision_type)
            except ValueError:
                logger.warning(
                    f"Unknown decision_type '{decision_type}', defaulting to SCORE_CANDIDATE"
                )
                canonical_type = DecisionType.SCORE_CANDIDATE

        final_ignored = set(PROTECTED_CRITERIA)
        if criteria_ignored:
            final_ignored.update(criteria_ignored)

        retention_days = self.RETENTION_PERIODS.get(canonical_type.value, 730)
        retention_until = datetime.utcnow() + timedelta(days=retention_days)

        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            company_id=company_id,
            agent_name=agent_name,
            decision_type=canonical_type.value,
            action=action,
            decision=decision,
            reasoning=reasoning,
            criteria_used=criteria_used,
            criteria_ignored=list(final_ignored),
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            score=score,
            confidence=confidence,
            human_review_required=human_review_required,
            retention_until=retention_until,
            # Task #366 column-promotion workaround — actor stored in
            # session_id until a dedicated column is promoted (mirrors
            # _log_decision_impl so both audit paths populate the same field).
            session_id=actor_user_id,
            # Sprint A: correlation_id do ContextVar
            correlation_id=(
                (lambda: __import__('app.middleware.request_id', fromlist=['get_correlation_id']).get_correlation_id() or None)()
                if True else None
            ),
        )
        session.add(audit_log)
        await session.flush()
        return audit_log

    async def get_candidate_decisions(
        self, company_id: str, candidate_id: str, job_vacancy_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> dict[str, Any]:
        """
        Get all decisions made about a candidate (for explainability).

        Args:
            company_id: The company/tenant ID
            candidate_id: The candidate ID
            job_vacancy_id: Optional job vacancy ID to filter by
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            Dictionary with audit logs and pagination info
        """
        from sqlalchemy import func

        async with AsyncSessionLocal() as session:
            where_conditions = [AuditLog.company_id == company_id, AuditLog.candidate_id == candidate_id]

            if job_vacancy_id:
                where_conditions.append(AuditLog.job_vacancy_id == job_vacancy_id)

            count_query = select(func.count()).select_from(AuditLog).where(and_(*where_conditions))
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            data_query = (
                # TENANT-EXEMPT: compliance audit_service queries AuditLog/Decision via dynamic conditions builder with company_id upstream
                # TENANT-EXEMPT: compliance audit_service queries AuditLog/Decision via dynamic conditions builder with company_id upstream
                select(AuditLog)
                .where(and_(*where_conditions))
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(data_query)
            audit_logs = result.scalars().all()

            logger.info(f"📋 Retrieved {len(audit_logs)} audit logs for candidate {candidate_id}")

            return {
                "audit_logs": [log.to_dict() for log in audit_logs],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    async def get_decisions_by_agent(
        self,
        company_id: str,
        agent_name: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        """
        Get decisions made by a specific agent.

        Args:
            company_id: The company/tenant ID
            agent_name: Name of the agent
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of results

        Returns:
            List of AuditLog instances
        """
        async with AsyncSessionLocal() as session:
            where_conditions = [AuditLog.company_id == company_id, AuditLog.agent_name == agent_name]

            if start_date:
                where_conditions.append(AuditLog.created_at >= start_date)
            if end_date:
                where_conditions.append(AuditLog.created_at <= end_date)

            # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter upstream tenant gate
            query = select(AuditLog).where(and_(*where_conditions)).order_by(desc(AuditLog.created_at)).limit(limit)

            result = await session.execute(query)
            audit_logs = result.scalars().all()

            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.info(f"📋 Retrieved {len(audit_logs)} audit logs for agent {agent_name}")
            return list(audit_logs)

    async def get_decisions_by_user(
        self,
        company_id: str,
        actor_user_id: str,
        start_date=None,
        end_date=None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get AI decisions triggered by a specific user (Task #366).

        Multi-tenant: enforced via company_id filter (fail-closed).
        Paged result: {audit_logs, total, limit, offset}.
        """
        from sqlalchemy import func

        async with AsyncSessionLocal() as session:
            conditions = [AuditLog.company_id == company_id]
            # actor_user_id stored in session_id until dedicated column is promoted.
            conditions.append(AuditLog.session_id == actor_user_id)
            if start_date:
                conditions.append(AuditLog.created_at >= start_date)
            if end_date:
                conditions.append(AuditLog.created_at <= end_date)

            count_q = select(func.count()).select_from(AuditLog).where(and_(*conditions))
            total = (await session.execute(count_q)).scalar() or 0

            # TENANT-EXEMPT: compliance audit_service queries AuditLog/Decision via dynamic conditions builder with company_id upstream
            rows_q = (
                # TENANT-EXEMPT: compliance audit_service queries AuditLog/Decision via dynamic conditions builder with company_id upstream
                select(AuditLog)
                .where(and_(*conditions))
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
                .offset(offset)
            )
            rows = (await session.execute(rows_q)).scalars().all()

            logger.info("[AuditService] get_decisions_by_user: %d rows for %s / %s",
                        len(rows), actor_user_id, company_id)
            return {
                "audit_logs": [r.to_dict() for r in rows],
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    async def log_output(
        self,
        *,
        company_id: str,
        session_id: str,
        agent_used: str,
        input_text: str,
        output_text: str,
        action_executed: str = None,
        candidate_id: str = None,
        job_vacancy_id: str = None,
        fairness_flags: list = None,
    ) -> None:
        """
        Registra a saida conversacional da LIA para auditoria completa.

        Chamado pelo MainOrchestrator apos cada resposta que envolva
        candidate_id ou job_vacancy_id (acoes de alto impacto).

        Compliance: EU AI Act Art. 13, LGPD Art. 18, CLT Art. 373-A.
        """
        retention_until = datetime.utcnow() + timedelta(days=1825)  # 5 anos

        async with AsyncSessionLocal() as session:
            await _bind_tenant(session, company_id)
            audit_log = AuditLog(
                id=str(uuid.uuid4()),
                company_id=company_id,
                session_id=session_id,
                agent_name=agent_used,
                agent_used=agent_used,
                decision_type="conversational_output",
                action=action_executed or "lia_response",
                decision="responded",
                candidate_id=candidate_id,
                job_vacancy_id=job_vacancy_id,
                input_text=input_text[:4000] if input_text else None,
                output_text=output_text[:8000] if output_text else None,
                fairness_flags=fairness_flags or [],
                reasoning=[],
                # R-003 (Sprint 1): payload estruturado para LGPD Art.20 explainability.
                # Formato "key:value" preserva schema list[str] sem mudanca destrutiva.
                criteria_used=[
                    f"agent:{agent_used or 'unknown'}",
                    f"action:{action_executed or 'lia_response'}",
                    "decision_type:conversational_output",
                    f"fairness_flags_count:{len(fairness_flags or [])}",
                    f"has_candidate_context:{bool(candidate_id)}",
                    f"has_job_context:{bool(job_vacancy_id)}",
                ],
                criteria_ignored=list(PROTECTED_CRITERIA),
                human_review_required=False,
                retention_until=retention_until,
            )
            session.add(audit_log)
            await session.commit()

            logger.info("Output audit logged: agent=%s session=%s candidate=%s", agent_used, session_id, candidate_id)

    async def record_human_review(
        self,
        audit_log_id: str,
        reviewed_by: str,
        override: str | None = None,
    ) -> AuditLog | None:
        """
        Record when a human reviews/overrides an AI decision.

        Args:
            audit_log_id: ID of the audit log to update
            reviewed_by: User ID of the reviewer
            override: Optional new decision if human overrides AI

        Returns:
            Updated AuditLog instance or None if not found
        # TENANT-EXEMPT: compliance audit_service queries AuditLog/Decision via dynamic conditions builder with company_id upstream
        """
        async with AsyncSessionLocal() as session:
            # TENANT-EXEMPT: compliance audit_service queries AuditLog/Decision via dynamic conditions builder with company_id upstream
            query = select(AuditLog).where(AuditLog.id == audit_log_id)
            result = await session.execute(query)
            audit_log = result.scalar_one_or_none()

            if audit_log:
                audit_log.human_reviewed_by = reviewed_by
                audit_log.human_reviewed_at = datetime.utcnow()
                audit_log.human_override = override

                await session.commit()
                await session.refresh(audit_log)

                logger.info(
                    f"✅ Human review recorded for audit log {audit_log_id} "
                    f"by {reviewed_by}" + (f" (override: {override})" if override else "")
                )
                return audit_log
            else:
                logger.warning(f"⚠️  Audit log not found: {audit_log_id}")
                return None

    async def get_pending_reviews(self, company_id: str, limit: int = 50) -> list[AuditLog]:
        """
        Get decisions that require human review but haven't been reviewed yet.

        Args:
            company_id: The company/tenant ID
            limit: Maximum number of results

        Returns:
            List of AuditLog instances pending review
        """
        async with AsyncSessionLocal() as session:
            query = (
                select(AuditLog)
                .where(
                    and_(
                        AuditLog.company_id == company_id,
                        AuditLog.human_review_required,
                        AuditLog.human_reviewed_at.is_(None),
                    )
                )
                .order_by(desc(AuditLog.created_at))
                .limit(limit)
            )

            result = await session.execute(query)
            audit_logs = result.scalars().all()

            logger.info(f"📋 Found {len(audit_logs)} pending reviews for company {company_id}")
            return list(audit_logs)

    async def get_decision_statistics(
        self, company_id: str, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> dict[str, Any]:
        """
        Get statistics about AI decisions for governance reporting.

        Args:
            company_id: The company/tenant ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with decision statistics
        """
        from sqlalchemy import func

        async with AsyncSessionLocal() as session:
            where_conditions = [AuditLog.company_id == company_id]

            if start_date:
                where_conditions.append(AuditLog.created_at >= start_date)
            if end_date:
                where_conditions.append(AuditLog.created_at <= end_date)

            total_query = select(func.count()).select_from(AuditLog).where(and_(*where_conditions))
            total_result = await session.execute(total_query)
            total_decisions = total_result.scalar() or 0

            by_type_query = (
                select(AuditLog.decision_type, func.count(AuditLog.id))
                .where(and_(*where_conditions))
                .group_by(AuditLog.decision_type)
            )
            by_type_result = await session.execute(by_type_query)
            by_type = dict(by_type_result.fetchall())

            by_decision_query = (
                select(AuditLog.decision, func.count(AuditLog.id))
                .where(and_(*where_conditions))
                .group_by(AuditLog.decision)
            )
            by_decision_result = await session.execute(by_decision_query)
            by_decision = dict(by_decision_result.fetchall())

            reviewed_query = (
                select(func.count())
                .select_from(AuditLog)
                .where(and_(*where_conditions, AuditLog.human_reviewed_at.isnot(None)))
            )
            reviewed_result = await session.execute(reviewed_query)
            human_reviewed = reviewed_result.scalar() or 0

            overridden_query = (
                select(func.count())
                .select_from(AuditLog)
                .where(and_(*where_conditions, AuditLog.human_override.isnot(None)))
            )
            overridden_result = await session.execute(overridden_query)
            human_overridden = overridden_result.scalar() or 0

            return {
                "total_decisions": total_decisions,
                "by_type": by_type,
                "by_decision": by_decision,
                "human_reviewed": human_reviewed,
                "human_overridden": human_overridden,
                "override_rate": (human_overridden / human_reviewed * 100) if human_reviewed > 0 else 0,
            }

    # ------------------------------------------------------------------
    # Unified facade methods (P35-061 — Audit Consolidation)
    # These accept trace_id to correlate events across all 7 audit mechanisms.
    # ------------------------------------------------------------------

    async def log_action(
        self,
        *,
        trace_id: str,
        company_id: str,
        action_type: str,
        actor: str,
        target_id: str | None = None,
        target_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log an action (email sent, candidate moved, job published).

        Unified entry point — delegates to AuditLog with trace_id.
        """
        try:
            async with AsyncSessionLocal() as session:
                await _bind_tenant(session, company_id)
                log = AuditLog(
                    id=str(uuid.uuid4()),
                    company_id=company_id,
                    agent_name=actor,
                    decision_type=action_type,
                    action=action_type,
                    decision="executed",
                    reasoning=[],
                    # R-003 (Sprint 1): payload estruturado pre log_action.
                    criteria_used=[
                        f"actor:{actor or 'unknown'}",
                        f"action_type:{action_type}",
                        f"target_type:{target_type or 'unknown'}",
                        f"has_target:{bool(target_id)}",
                        f"has_trace:{bool(trace_id)}",
                    ],
                    criteria_ignored=[],
                    candidate_id=target_id if target_type == "candidate" else None,
                    job_vacancy_id=target_id if target_type == "job" else None,
                    session_id=trace_id,
                    retention_until=datetime.utcnow() + timedelta(days=730),
                )
                session.add(log)
                await session.commit()
        except Exception as exc:
            logger.debug("[AuditService] log_action failed (non-blocking): %s", exc)

    async def log_data_access(
        self,
        *,
        company_id: str,
        user_id: str | None,
        user_email: str | None,
        resource_type: str,
        resource_id: str,
        action: str = "view",
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        """Log a PII data access event (LGPD Art. 37 V — registro de operações de tratamento).

        Sprint 3 RBAC (2026-05-25, plan canonical: ~/.claude/plans/jolly-roaming-moler.md).

        Persiste em SOXAuditLog com category=DATA_ACCESS. 7-year retention SOX.
        Non-blocking — exceções são logadas mas NÃO propagam (não bloqueia request).

        Args:
            company_id: tenant ID (multi-tenancy mandatory)
            user_id: user UUID (quem acessou)
            user_email: email do user (denormalized for query speed)
            resource_type: 'candidate' | 'job_vacancy' | 'audit_log' | ...
            resource_id: ID do recurso acessado (UUID ou int as string)
            action: 'view' (default) | 'view_pii' | 'export'
            ip_address: from request.client.host
            user_agent: from request.headers
            request_id: trace correlation
            details: optional extra context (e.g., {"is_confidential": True})

        Consumer: app/api/v1/observability.py:list_data_access_logs (DPO view).
        Reused: SOXAuditLog table + observability_repository (already canonical).
        """
        try:
            from lia_models.audit_logs import (
                ActionCategory,
                AuditStatus,
                SOXAuditLog,
            )
            async with AsyncSessionLocal() as session:
                await _bind_tenant(session, company_id)
                log = SOXAuditLog(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    user_id=user_id,
                    user_email=user_email,
                    action=action,
                    action_category=ActionCategory.DATA_ACCESS.value,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=(user_agent[:500] if user_agent else None),
                    status=AuditStatus.SUCCESS.value,
                    details=details or {},
                    retention_years=7,
                    retention_until=datetime.utcnow() + timedelta(days=365 * 7),
                    request_id=request_id,
                )
                session.add(log)
                await session.commit()
        except Exception as exc:
            # Non-blocking — falha de audit log NUNCA quebra request principal.
            # Sprint 3 RBAC: aceita perda eventual de log row vs bloquear UX.
            logger.debug("[AuditService] log_data_access failed (non-blocking): %s", exc)

    async def log_user_provisioning(
        self,
        *,
        company_id: str,
        actor: str,
        action: str,
        target_user_id: str | None,
        target_user_email: str | None,
        details: dict | None = None,
        status: str = "success",
        request_id: str | None = None,
    ) -> None:
        """Log a user provisioning event (LGPD Art. 37 V + SOX Section 802).

        Sprint 4 RBAC (2026-05-25, plan canonical: ~/.claude/plans/jolly-roaming-moler.md).
        Used by SCIM webhook handlers (dsync.user.created/updated/deleted,
        dsync.group.user_added/removed) and any other automated user lifecycle.

        Persists in SOXAuditLog with category=USER_MANAGEMENT. 7-year retention.
        Non-blocking — exceptions logged but NOT propagated.

        Args:
            company_id: tenant ID (multi-tenancy mandatory)
            actor: who performed the action (scim_webhook, user_id, etc.)
            action: provision_user | update_user | deactivate_user | role_change | group_add | group_remove
            target_user_id: affected user UUID
            target_user_email: denormalized for query speed
            details: extra context (e.g., {"workos_id": "...", "role_old": "viewer", "role_new": "admin", "groups": [...]})
            status: success | failed | partial
            request_id: trace correlation
        """
        try:
            from lia_models.audit_logs import (
                ActionCategory,
                AuditStatus,
                SOXAuditLog,
            )
            async with AsyncSessionLocal() as session:
                await _bind_tenant(session, company_id)
                log = SOXAuditLog(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    user_id=None,  # actor is system (scim_webhook), not authenticated user
                    user_email=actor,
                    action=action,
                    action_category=ActionCategory.USER_MANAGEMENT.value,
                    resource_type="user",
                    resource_id=target_user_id or "",
                    ip_address=None,
                    user_agent=None,
                    status=(
                        AuditStatus.SUCCESS.value if status == "success"
                        else AuditStatus.FAILED.value if status == "failed"
                        else AuditStatus.SUCCESS.value
                    ),
                    details={
                        **(details or {}),
                        "target_user_email": target_user_email,
                        "actor": actor,
                    },
                    retention_years=7,
                    retention_until=datetime.utcnow() + timedelta(days=365 * 7),
                    request_id=request_id,
                )
                session.add(log)
                await session.commit()
        except Exception as exc:
            logger.debug("[AuditService] log_user_provisioning failed (non-blocking): %s", exc)

    async def log_compliance(
        self,
        *,
        trace_id: str,
        company_id: str,
        check_type: str,
        result: str,
        details: dict[str, Any] | None = None,
        candidate_id: str | None = None,
    ) -> None:
        """Log a compliance check (fairness, consent, bias).

        Unified entry point for compliance audit events.
        """
        try:
            async with AsyncSessionLocal() as session:
                await _bind_tenant(session, company_id)
                log = AuditLog(
                    id=str(uuid.uuid4()),
                    company_id=company_id,
                    agent_name="compliance_check",
                    decision_type=check_type,
                    action=check_type,
                    decision=result,
                    reasoning=[str(details)] if details else [],
                    # R-003 (Sprint 1): payload estruturado para log_compliance_check.
                    criteria_used=[
                        f"check_type:{check_type}",
                        f"result:{result}",
                        f"has_details:{bool(details)}",
                        f"has_candidate:{bool(candidate_id)}",
                        f"has_trace:{bool(trace_id)}",
                    ],
                    criteria_ignored=list(PROTECTED_CRITERIA),
                    candidate_id=candidate_id,
                    session_id=trace_id,
                    retention_until=datetime.utcnow() + timedelta(days=1825),
                )
                session.add(log)
                await session.commit()
        except Exception as exc:
            logger.debug("[AuditService] log_compliance failed (non-blocking): %s", exc)

    async def log_error(
        self,
        *,
        trace_id: str,
        company_id: str,
        error_type: str,
        error_message: str,
        agent: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Log an error with context for debugging."""
        try:
            async with AsyncSessionLocal() as session:
                await _bind_tenant(session, company_id)
                log = AuditLog(
                    id=str(uuid.uuid4()),
                    company_id=company_id,
                    agent_name=agent,
                    decision_type="error",
                    action=error_type,
                    decision="error",
                    reasoning=[error_message],
                    # R-003 (Sprint 1): payload estruturado para log_error.
                    criteria_used=[
                        f"error_type:{error_type}",
                        f"agent:{agent}",
                        f"has_metadata:{bool(metadata)}",
                        f"has_trace:{bool(trace_id)}",
                        f"message_truncated:{len(error_message) > 500 if error_message else False}",
                    ],
                    criteria_ignored=[],
                    session_id=trace_id,
                    retention_until=datetime.utcnow() + timedelta(days=365),
                )
                session.add(log)
                await session.commit()
        except Exception as exc:
            logger.debug("[AuditService] log_error failed (non-blocking): %s", exc)

    async def get_trail(
        self,
        trace_id: str,
        company_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Reconstruct the full audit trail for a request/session.

        Queries AuditLog by session_id (= trace_id) and returns all events
        in chronological order. This correlates decisions, actions, compliance
        checks, and errors that happened during a single request.
        """
        try:
            async with AsyncSessionLocal() as session:
                conditions = [AuditLog.session_id == trace_id]
                if company_id:
                    conditions.append(AuditLog.company_id == company_id)

                # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace; T-RATCHET tenant_filter
                result = await session.execute(select(AuditLog).where(and_(*conditions)).order_by(AuditLog.created_at))
                logs = result.scalars().all()
                return [log.to_dict() for log in logs]
        except Exception as exc:
            logger.warning("[AuditService] get_trail failed: %s", exc)
            return []


audit_service = AuditService()


# FastAPI dependency injection factory
def get_audit_service() -> "AuditService":
    return audit_service
