"""Celery tasks: compliance (Fase 7)."""
import asyncio
import re
from datetime import UTC

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(base=TenantAwareTask, name="audit.apply_lifecycle_policy", bind=True, max_retries=3)
def apply_audit_lifecycle_policy(self) -> dict:
    """
    Aplica política de retenção S3 no bucket de auditoria.
    Executada 1x por mês via Celery Beat.
    Idempotente.
    """
    import asyncio

    from lia_audit.audit_storage import get_audit_storage

    span = _celery_span("celery.task_start", "audit.apply_lifecycle_policy")

    try:
        storage = get_audit_storage()
        result = asyncio.run(storage.apply_lifecycle_policy())
        _finish_celery_success(span, "audit.apply_lifecycle_policy")
        logger.info(f"[audit.lifecycle] Applied: {result}")
        from app.shared.resilience.cron_health import record_cron_run
        record_cron_run("audit.apply_lifecycle_policy")
        return {"applied": result}
    except Exception as exc:
        _finish_celery_failure(span, "audit.apply_lifecycle_policy", exc)
        logger.error(f"[audit.lifecycle] Error: {exc}")
        _emit_celery_retry("audit.apply_lifecycle_policy", exc, self.request.retries, self.max_retries, 3600)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("audit.apply_lifecycle_policy", exc)
        raise self.retry(exc=exc, countdown=3600)

@celery_app.task(base=TenantAwareTask, name="lgpd.run_cleanup_daily", bind=True, max_retries=3)
def run_lgpd_cleanup_task(self, dry_run: bool = False) -> dict:
    """
    Executa limpeza de dados LGPD para todas as empresas.

    Aplica políticas de retenção (LGPD Art. 16):
      - 90 dias: candidatos rejeitados / retirados (dados operacionais)
      - 90 dias: mensagens de chat/conversa (minimização LGPD Art. 18)
      - 180 dias: dados de avaliação e triagem
      - 365 dias: logs de auditoria e compliance

    Agendado diariamente às 02h Brasília via Celery Beat (beat_schedule: lgpd-cleanup-daily).

    Args:
        dry_run: Se True, simula sem deletar (padrão: False em produção).

    Returns:
        Dict com { dry_run, ran_at, candidates_deleted,
                   vacancy_candidates_deleted, ai_consumption_deleted,
                   chat_messages_deleted, interview_notes_deleted,
                   screening_logs_deleted, ai_decision_logs_deleted, errors }
    """
    span = _celery_span("celery.task_start", "lgpd.run_cleanup_daily")
    span.set_attribute("dry_run", str(dry_run))

    async def _run() -> dict:
        from app.shared.services.lgpd_cleanup_service import run_cleanup
        return await run_cleanup(dry_run=dry_run)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "lgpd.run_cleanup_daily")
        logger.info("lgpd.run_cleanup_daily concluído: %s", result)
        from app.shared.resilience.cron_health import record_cron_run
        record_cron_run("lgpd.run_cleanup_daily")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "lgpd.run_cleanup_daily", exc)
        logger.error("lgpd.run_cleanup_daily falhou: %s", exc)
        _emit_celery_retry("lgpd.run_cleanup_daily", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("lgpd.run_cleanup_daily", exc)
        raise self.retry(exc=exc, countdown=300)

@celery_app.task(base=TenantAwareTask, name="conversation.ttl_cleanup", bind=True, max_retries=3)
def conversation_ttl_cleanup_task(self, dry_run: bool = False) -> dict:
    """
    Job Celery Beat dedicado para TTL de dados de conversa.

    Aplica TTL por tipo de dado (LGPD Art. 18 — minimização e retenção):
      - chat_messages / conversation_messages: 90 dias
      - interview_notes: 180 dias
      - screening_tasks: 365 dias
      - fairness_audit_log: 365 dias (EU AI Act)

    Agendado diariamente às 03h Brasília via Celery Beat
    (beat_schedule: conversation-ttl-cleanup-daily).

    Args:
        dry_run: Se True, simula sem deletar (padrão: False em produção).

    Returns:
        Dict com { dry_run, ran_at, tables, total_deleted, errors }
    """
    span = _celery_span("celery.task_start", "conversation.ttl_cleanup")
    span.set_attribute("dry_run", str(dry_run))

    async def _run() -> dict:
        from app.shared.services.lgpd_cleanup_service import run_conversation_ttl_cleanup
        return await run_conversation_ttl_cleanup(dry_run=dry_run)

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "conversation.ttl_cleanup")
        logger.info("conversation.ttl_cleanup concluído: %s", result)
        return result
    except Exception as exc:
        _finish_celery_failure(span, "conversation.ttl_cleanup", exc)
        logger.error("conversation.ttl_cleanup falhou: %s", exc)
        _emit_celery_retry("conversation.ttl_cleanup", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("conversation.ttl_cleanup", exc)
        raise self.retry(exc=exc, countdown=300)  # retry em 5 min

@celery_app.task(base=TenantAwareTask, name="pii.backfill_encrypt_existing", bind=True, max_retries=2)
def pii_backfill_encrypt_existing_task(
    self,
    batch_size: int = 500,
    dry_run: bool = False,
) -> dict:
    """
    Phase-2 backfill: encrypt existing plaintext PII bytes for rows added before migration 060.

    For each row where email_encrypted IS NULL but email IS NOT NULL:
      1. Fernet-encrypt the plaintext email → write to email_encrypted
      2. SHA-256 hash the email → write to email_hash (pgcrypto already covers this
         for most rows; this catches any missed rows)
      3. Repeat for cpf → cpf_encrypted on the candidates table

    Runs in batches (batch_size) to avoid long-running transactions.
    Requires FIELD_ENCRYPTION_KEY to be set.

    Safe to re-run: idempotent (WHERE email_encrypted IS NULL ensures skipping done rows).

    Args:
        batch_size: rows per batch (default 500)
        dry_run: log counts without committing (default False)

    Returns:
        Dict with per-table encrypted counts and any errors.
    """
    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.shared.encryption.encrypted_field_mixin import _encrypt, _sha256_hash
        from sqlalchemy import text

        summary: dict = {
            "dry_run": dry_run,
            "batch_size": batch_size,
            "tables": {},
            "errors": [],
        }

        _PII_TABLES_ALLOWED = frozenset(["candidates", "client_users", "users"])
        _SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")

        tables_config = [
            ("candidates", "email", "email_encrypted", "email_hash"),
            ("client_users", "email", "email_encrypted", "email_hash"),
            ("users", "email", "email_encrypted", "email_hash"),
        ]

        async with AsyncSessionLocal() as db:
            for table, email_col, enc_col, hash_col in tables_config:
                if table not in _PII_TABLES_ALLOWED:
                    raise ValueError(f"Table '{table}' not in PII backfill allow-list")
                if not _SAFE_ID_RE.match(table):
                    raise ValueError(f"Table '{table}' contains invalid characters")
                for col in (email_col, enc_col, hash_col):
                    if not _SAFE_ID_RE.match(col):
                        raise ValueError(f"Column '{col}' contains invalid characters")

                encrypted_count = 0
                try:
                    while True:
                        rows = (await db.execute(
                            text(
                                f"SELECT id, {email_col} FROM {table} "
                                f"WHERE {enc_col} IS NULL AND {email_col} IS NOT NULL "
                                f"LIMIT :limit"
                            ),
                            {"limit": batch_size},
                        )).all()

                        if not rows:
                            break

                        for row in rows:
                            enc_val = _encrypt(row[1])
                            hash_val = _sha256_hash(row[1])
                            if not dry_run:
                                await db.execute(
                                    text(
                                        f"UPDATE {table} SET {enc_col} = :enc, {hash_col} = :hsh "
                                        f"WHERE id = :id"
                                    ),
                                    {"enc": enc_val, "hsh": hash_val, "id": row[0]},
                                )
                        if not dry_run:
                            await db.commit()

                        encrypted_count += len(rows)
                        logger.info(
                            "pii.backfill_encrypt_existing%s: %s — encrypted %d rows (batch)",
                            " (dry-run)" if dry_run else "",
                            table,
                            len(rows),
                        )

                        if len(rows) < batch_size:
                            break

                    summary["tables"][table] = {"encrypted": encrypted_count}

                except Exception as exc:
                    logger.error("pii.backfill_encrypt_existing: error on %s: %s", table, exc)
                    summary["errors"].append(f"{table}: {exc}")
                    try:
                        await db.rollback()
                    except Exception:
                        pass

            # Also backfill cpf_encrypted on candidates
            cpf_encrypted_count = 0
            try:
                while True:
                    rows = (await db.execute(
                        text(
                            "SELECT id, cpf FROM candidates "
                            "WHERE cpf_encrypted IS NULL AND cpf IS NOT NULL "
                            "LIMIT :limit"
                        ),
                        {"limit": batch_size},
                    )).all()

                    if not rows:
                        break

                    for row in rows:
                        enc_val = _encrypt(row[1])
                        if not dry_run:
                            await db.execute(
                                text(
                                    "UPDATE candidates SET cpf_encrypted = :enc WHERE id = :id"
                                ),
                                {"enc": enc_val, "id": row[0]},
                            )
                    if not dry_run:
                        await db.commit()

                    cpf_encrypted_count += len(rows)

                    if len(rows) < batch_size:
                        break

                summary["tables"]["candidates_cpf"] = {"encrypted": cpf_encrypted_count}

            except Exception as exc:
                logger.error("pii.backfill_encrypt_existing: error on candidates PII field: %s", exc)
                summary["errors"].append(f"candidates_cpf: {exc}")

        return summary

    span = _celery_span("celery.task_start", "pii.backfill_encrypt_existing")
    span.set_attribute("batch_size", str(batch_size))
    span.set_attribute("dry_run", str(dry_run))

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "pii.backfill_encrypt_existing")
        logger.info("pii.backfill_encrypt_existing concluído: %s", result)
        return result
    except Exception as exc:
        _finish_celery_failure(span, "pii.backfill_encrypt_existing", exc)
        logger.error("pii.backfill_encrypt_existing falhou: %s", exc)
        _emit_celery_retry("pii.backfill_encrypt_existing", exc, self.request.retries, self.max_retries, 600)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("pii.backfill_encrypt_existing", exc)
        raise self.retry(exc=exc, countdown=600)  # retry em 10 min

@celery_app.task(base=TenantAwareTask, 
    name="data.retention.run",
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def run_retention_cleanup(self) -> dict:
    """
    Job mensal de anonimização de candidatos não contratados (LGPD Art. 18).
    Roda apenas para empresas com auto_anonymize=True (opt-in).
    Candidatos contratados (is_hired=True) NUNCA são anonimizados.

    Celery Beat schedule (adicionar em celery_config.py):
        "data-retention-monthly": {
            "task": "data.retention.run",
            "schedule": crontab(day_of_month=1, hour=2, minute=0),
        }
    """
    import asyncio
    span = _celery_span("celery.task_start", "data.retention.run")
    try:
        result = asyncio.run(_run_retention_cleanup_async())
        _finish_celery_success(span, "data.retention.run")
        from app.shared.resilience.cron_health import record_cron_run
        record_cron_run("data.retention.run")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "data.retention.run", exc)
        _emit_celery_retry("data.retention.run", exc, self.request.retries, self.max_retries, 60)
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("data.retention.run", exc)
        raise self.retry(exc=exc)

async def _run_retention_cleanup_async() -> dict:
    from datetime import datetime, timedelta
    from uuid import uuid4

    from sqlalchemy import select, update

    try:
        from lia_config.database import AsyncSessionLocal
    except ImportError:
        from app.core.database import AsyncSessionLocal

    from lia_models.retention_policy import CompanyRetentionPolicy

    # Candidate model — try multiple import paths
    try:
        from lia_models.candidate import Candidate
    except ImportError:
        from app.models.candidate import Candidate

    total_anonymized = 0
    companies_processed = 0
    errors = []

    async with AsyncSessionLocal() as session:
        from sqlalchemy import text as _text  # noqa: F401
        policies_result = await session.execute(
            select(CompanyRetentionPolicy).where(
                CompanyRetentionPolicy.auto_anonymize == True  # noqa: E712
            )
        )
        policies = policies_result.scalars().all()

        for policy in policies:
            try:
                cutoff_date = datetime.now(UTC) - timedelta(
                    days=policy.retention_months * 30
                )
                # ADR-001-EXEMPT: Rails-owned Candidate table — LGPD Art. 16 data retention policy (anonymization)
                result = await session.execute(
                    update(Candidate)
                    .where(
                        Candidate.company_id == policy.company_id,
                        Candidate.is_hired == False,  # noqa: E712
                        Candidate.created_at < cutoff_date,
                        Candidate.anonymized_at == None,  # noqa: E711
                    )
                    .values(
                        name=f"ANONIMIZADO-{uuid4().hex[:8]}",
                        email=None,
                        phone=None,
                        cpf=None,
                        linkedin_url=None,
                        github_url=None,
                        portfolio_url=None,
                        photo_url=None,
                        address=None,
                        anonymized_at=datetime.now(UTC),
                        anonymized_by="data.retention.run",
                    )
                )
                count = result.rowcount
                total_anonymized += count
                companies_processed += 1
                await session.execute(
                    update(CompanyRetentionPolicy)
                    .where(CompanyRetentionPolicy.company_id == policy.company_id)
                    .values(
                        last_cleanup_at=datetime.now(UTC),
                        last_cleanup_count=count,
                    )
                )
                logger.info(
                    "Retention cleanup: company=%s anonymized=%d cutoff=%s",
                    policy.company_id, count, cutoff_date.date()
                )
            except Exception as e:
                errors.append({"company_id": policy.company_id, "error": str(e)})
                logger.error("Retention cleanup failed for company=%s: %s", policy.company_id, e)

        await session.commit()

    result_dict = {
        "companies_processed": companies_processed,
        "total_anonymized": total_anonymized,
        "errors": errors,
        "ran_at": datetime.now(UTC).isoformat(),
    }
    logger.info("Retention cleanup complete: %s", result_dict)
    return result_dict



@celery_app.task(base=TenantAwareTask, name="agent_working_memory.cleanup", bind=True, max_retries=3)
def cleanup_expired_working_memory(self) -> dict:
    """
    Delete AgentWorkingMemory rows where expires_at < now().

    UC-P2-02: TTL enforcement for agent working memory.
    Without this job the table grows unbounded; Celery Beat schedules it
    daily at 03h UTC (beat_schedule key: agent-working-memory-cleanup-daily).

    Returns:
        Dict with { deleted, ran_at }.
    """
    import asyncio
    from datetime import datetime, timezone

    span = _celery_span("celery.task_start", "agent_working_memory.cleanup")

    async def _run() -> dict:
        from lia_config.database import AsyncSessionLocal
        from lia_agents_core.working_memory import AgentWorkingMemory
        from sqlalchemy import delete, and_

        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(AgentWorkingMemory).where(
                    and_(
                        AgentWorkingMemory.expires_at.isnot(None),
                        AgentWorkingMemory.expires_at < now,
                    )
                )
            )
            deleted = result.rowcount
            await db.commit()
        logger.info("[agent_working_memory.cleanup] Deleted %d expired rows", deleted)
        return {"deleted": deleted, "ran_at": now.isoformat()}

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "agent_working_memory.cleanup")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "agent_working_memory.cleanup", exc)
        logger.error("agent_working_memory.cleanup falhou: %s", exc)
        _emit_celery_retry(
            "agent_working_memory.cleanup", exc,
            self.request.retries, self.max_retries, 3600
        )
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("agent_working_memory.cleanup", exc)
        raise self.retry(exc=exc, countdown=3600)

@celery_app.task(base=TenantAwareTask, name="rls.health_check", bind=True, max_retries=2)
def rls_health_check(self) -> dict:
    """
    R-002 — Sensor diário de RLS Postgres em tabelas críticas (cron 04h UTC).

    Verifica via pg_class.relrowsecurity / relforcerowsecurity que tabelas
    críticas (audit_logs, lgpd_consents, tenant_llm_configs, etc) ainda
    estão com RLS FORCED. Detecta drift causado por:
      - ALTER TABLE ... DISABLE ROW LEVEL SECURITY manual via psql
      - Tabela nova introduzida sem migration RLS canonical

    Equivalente runtime de pgrep ao endpoint GET /api/v1/health/rls.
    Migration 068 + 118-126 cobrem ~119 tabelas; este job pulsa diário no
    subset crítico e dispara CRITICAL log + Sentry breadcrumb se drift.

    Conformidade: LGPD Art. 12, Art. 19 (segurança lógica multi-tenancy).

    Returns:
        Dict com {status: ok|drift_detected, missing: [...], checked: N}.
    """
    import asyncio
    from sqlalchemy import text as _text
    from app.core.database import AsyncSessionLocal

    _RLS_CRITICAL_TABLES = (
        "audit_logs",
        "users",
        "lgpd_consents",
        "tenant_llm_configs",
        "vacancy_candidates",
        "triagem_sessions",
        "bias_audits",
        "compliance_reports",
        "fairness_reports",
    )

    async def _check() -> list[str]:
        async with AsyncSessionLocal() as session:
            sql = _text(
                """
                SELECT relname, relrowsecurity, relforcerowsecurity
                FROM pg_class WHERE relname = ANY(:tables)
                """
            )
            result = await session.execute(sql, {"tables": list(_RLS_CRITICAL_TABLES)})
            rows = result.fetchall()
            found = {r[0]: (r[1], r[2]) for r in rows}
            missing: list[str] = []
            for tbl in _RLS_CRITICAL_TABLES:
                if tbl not in found:
                    missing.append(f"{tbl}: not found in pg_class")
                    continue
                rowsec, forcesec = found[tbl]
                if not (rowsec and forcesec):
                    missing.append(
                        f"{tbl}: rowsec={rowsec}, forcesec={forcesec}"
                    )
            return missing

    span = _celery_span("celery.task_start", "rls.health_check")
    try:
        missing = asyncio.run(_check())
        _finish_celery_success(span, "rls.health_check")
    except Exception as exc:
        _finish_celery_failure(span, "rls.health_check", exc)
        logger.error("rls.health_check failed: %s", exc)
        _emit_celery_retry(
            "rls.health_check", exc,
            self.request.retries, self.max_retries, 600,
        )
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("rls.health_check", exc)
        raise self.retry(exc=exc, countdown=600)

    if missing:
        logger.critical(
            "[RLS Health] DRIFT DETECTED in critical tables: %s",
            missing,
        )
        try:
            import sentry_sdk  # type: ignore[import-not-found]
            sentry_sdk.capture_message(
                f"RLS drift detected in critical tables: {missing}",
                level="error",
            )
        except Exception:
            # Sentry optional — never let alerting failure mask the result
            pass
        return {
            "status": "drift_detected",
            "missing": missing,
            "checked": len(_RLS_CRITICAL_TABLES),
        }

    logger.info(
        "[RLS Health] All %d critical tables RLS-protected",
        len(_RLS_CRITICAL_TABLES),
    )
    return {"status": "ok", "checked": len(_RLS_CRITICAL_TABLES)}




@celery_app.task(base=TenantAwareTask, name="dsr.check_overdue_daily", bind=True, max_retries=3)
def check_dsr_overdue_daily(self) -> dict:
    """
    WT-2022 P5.3: Verificar DSRs com SLA expirado e criar Alerts.

    LGPD Art. 20 estabelece prazo de 15 dias úteis para resposta a DSR.
    Este job roda diariamente e:
    - Query DataSubjectRequest WHERE sla_deadline < now() AND status IN ('pending', 'processing', 'in_review')
    - Para cada DSR overdue sem Alert ativo, cria Alert(type=DEADLINE_APPROACHING, severity=HIGH)
    - Evita duplicação: skip se já existe Alert ativo para essa DSR.

    Agendado diariamente às 09h Brasília via Celery Beat (beat_schedule: dsr-check-overdue-daily).

    Returns:
        Dict com {ran_at, checked, overdue_found, alerts_created, errors}
    """
    span = _celery_span("celery.task_start", "dsr.check_overdue_daily")

    async def _run() -> dict:
        from datetime import datetime
        from sqlalchemy import and_, select
        from app.core.database import async_session_maker
        from app.models.observability import DataSubjectRequest
        from lia_models.alert import Alert, AlertSeverity, AlertStatus, AlertType

        now = datetime.utcnow()
        summary = {
            "ran_at": now.isoformat(),
            "checked": 0,
            "overdue_found": 0,
            "alerts_created": 0,
            "alerts_skipped_duplicate": 0,
            "errors": [],
        }

        async with async_session_maker() as db:
            # Query DSRs overdue
            stmt = select(DataSubjectRequest).where(
                and_(
                    DataSubjectRequest.sla_deadline < now,
                    DataSubjectRequest.status.in_(["pending", "processing", "in_review"]),
                )
            )
            result = await db.execute(stmt)
            overdue_dsrs = list(result.scalars().all())
            summary["overdue_found"] = len(overdue_dsrs)
            summary["checked"] = len(overdue_dsrs)

            for dsr in overdue_dsrs:
                try:
                    # Check existing active alert for this DSR
                    existing_q = select(Alert).where(
                        and_(
                            Alert.alert_type == AlertType.DEADLINE_APPROACHING,
                            Alert.status == AlertStatus.ACTIVE,
                            Alert.context["dsr_id"].astext == str(dsr.id),
                        )
                    )
                    existing = (await db.execute(existing_q)).scalar_one_or_none()
                    if existing is not None:
                        summary["alerts_skipped_duplicate"] += 1
                        continue

                    # Create alert
                    days_over = (now - dsr.sla_deadline).days
                    alert = Alert(
                        alert_type=AlertType.DEADLINE_APPROACHING,
                        severity=AlertSeverity.HIGH,
                        status=AlertStatus.ACTIVE,
                        title=f"DSR LGPD prazo vencido ({days_over}d)",
                        message=(
                            f"DSR {dsr.id} tipo '{dsr.request_type}' status '{dsr.status}' "
                            f"vencido em {days_over} dias (LGPD Art. 20 — 15 dias úteis). "
                            "Requer ação imediata para evitar não-conformidade ANPD."
                        ),
                        context={
                            "dsr_id": str(dsr.id),
                            "request_type": dsr.request_type,
                            "status": dsr.status,
                            "sla_deadline": dsr.sla_deadline.isoformat(),
                            "days_overdue": days_over,
                            "company_id": str(dsr.company_id),
                            "source": "WT-2022 P5.3 cron",
                        },
                    )
                    db.add(alert)
                    summary["alerts_created"] += 1

                    # Hardening C.4 -- canary signal SLA worker LGPD.
                    # Incrementado por alerta criado (NAO por DSR overdue,
                    # pra alinhar com nome do counter). Zero por 24h+ pode
                    # indicar worker travado OU ausencia real de DSRs vencidas.
                    try:
                        from app.shared.observability.canary_metrics import (
                            dsr_overdue_created_total,
                        )
                        if dsr_overdue_created_total is not None:
                            dsr_overdue_created_total.inc()
                    except Exception as _metric_exc:  # pragma: no cover -- fail-open
                        logger.debug(
                            "[dsr.check_overdue] canary metric inc failed (fail-open): %s",
                            _metric_exc,
                        )

                except Exception as exc:
                    summary["errors"].append({
                        "dsr_id": str(dsr.id),
                        "error": str(exc)[:200],
                    })
                    logger.error(
                        "[dsr.check_overdue] Failed to create alert for DSR %s: %s",
                        dsr.id, exc, exc_info=True,
                    )

            await db.commit()

        return summary

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "dsr.check_overdue_daily")
        logger.info("[dsr.check_overdue_daily] %s", result)
        from app.shared.resilience.cron_health import record_cron_run
        record_cron_run("dsr.check_overdue_daily")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "dsr.check_overdue_daily", exc)
        logger.error("dsr.check_overdue_daily falhou: %s", exc)
        _emit_celery_retry("dsr.check_overdue_daily", exc, self.request.retries, self.max_retries, 600)

        if self.request.retries >= self.max_retries:
            _emit_dlq_push("dsr.check_overdue_daily", exc)
        raise self.retry(exc=exc, countdown=600)


# ════════════════════════════════════════════════════════════════════════════
# P0.B Phase 2 (audit 2026-05-21): backfill Fernet encryption pra rows
# pre-migration-160 das colunas PII email em interview + offer_proposal.
# Pattern canonical: mesma estrutura de pii_backfill_encrypt_existing_task
# (linha 133+) que faz Candidate / ClientUser / User.
# ════════════════════════════════════════════════════════════════════════════


@celery_app.task(
    base=TenantAwareTask,
    name="pii.backfill_encrypt_interview_offer_existing",
    bind=True,
    max_retries=2,
)
def pii_backfill_encrypt_interview_offer_existing_task(
    self,
    batch_size: int = 500,
    dry_run: bool = False,
) -> dict:
    """
    P0.B Phase 2 (audit 2026-05-21): encrypt existing plaintext PII em
    interview + interview_feedbacks + offer_proposals.

    Migration 160 adicionou colunas ``*_encrypted`` / ``*_hash`` + flipou
    raw columns NOT NULL → nullable (transition phase). Esta task encripta
    os bytes dos rows EXISTENTES (pre-migration) que tem plaintext mas
    NULL em encrypted column.

    Idempotent: WHERE encrypted IS NULL AND plaintext IS NOT NULL —
    safe to re-run.

    Tabelas + colunas tratadas:
      - interviews.candidate_email           → candidate_email_encrypted + hash
      - interviews.interviewer_email         → interviewer_email_encrypted + hash
      - interviews.graph_organizer_email     → graph_organizer_email_encrypted (no hash)
      - interview_feedbacks.interviewer_email → interviewer_email_encrypted + hash
      - offer_proposals.candidate_email      → candidate_email_encrypted + hash

    Roda apos migration 160 ser aplicada. Pode rodar 1x manual via
    Celery dispatch OR agendar Beat (separate config). Phase 3 / 4 das
    migrations futuras (NOT NULL enforcement + drop plaintext) DEPENDEM
    desta task ter rodado a 100% antes.

    Args:
        batch_size: rows per batch (default 500).
        dry_run: log counts sem commit (default False).

    Returns:
        Dict com per-(table, column) encrypted counts + errors.
    """
    import asyncio
    import re

    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.shared.encryption.encrypted_field_mixin import _encrypt, _sha256_hash
        from sqlalchemy import text

        summary: dict = {
            "dry_run": dry_run,
            "batch_size": batch_size,
            "tables": {},
            "errors": [],
        }

        # SQL identifier allow-list canonical (mesmo pattern da Phase 1 task).
        _SAFE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")
        _ALLOWED_TABLES = frozenset([
            "interviews",
            "interview_feedbacks",
            "offer_proposals",
        ])

        # (table, plaintext_col, encrypted_col, hash_col_or_None)
        # hash_col=None → graph_organizer_email (query path improvável).
        tables_config = [
            ("interviews", "candidate_email",
             "candidate_email_encrypted", "candidate_email_hash"),
            ("interviews", "interviewer_email",
             "interviewer_email_encrypted", "interviewer_email_hash"),
            ("interviews", "graph_organizer_email",
             "graph_organizer_email_encrypted", None),
            ("interview_feedbacks", "interviewer_email",
             "interviewer_email_encrypted", "interviewer_email_hash"),
            ("offer_proposals", "candidate_email",
             "candidate_email_encrypted", "candidate_email_hash"),
        ]

        async with AsyncSessionLocal() as db:
            for table, plain_col, enc_col, hash_col in tables_config:
                # Defense-in-depth: validate identifier safety even though
                # tables_config is hardcoded above (canonical anti-injection
                # pattern from Phase 1 task — mantemos pra futura modificacao).
                if table not in _ALLOWED_TABLES:
                    raise ValueError(f"Table '{table}' not in PII backfill allow-list")
                for col in (plain_col, enc_col, *( [hash_col] if hash_col else [] )):
                    if not _SAFE_ID_RE.match(col):
                        raise ValueError(f"Column '{col}' contains invalid characters")

                key = f"{table}.{plain_col}"
                encrypted_count = 0

                try:
                    while True:
                        rows = (await db.execute(
                            text(
                                f"SELECT id, {plain_col} FROM {table} "
                                f"WHERE {enc_col} IS NULL AND {plain_col} IS NOT NULL "
                                f"LIMIT :limit"
                            ),
                            {"limit": batch_size},
                        )).all()

                        if not rows:
                            break

                        for row in rows:
                            enc_val = _encrypt(row[1])
                            params: dict = {"enc": enc_val, "id": row[0]}
                            if hash_col:
                                params["hsh"] = _sha256_hash(row[1])
                                update_sql = (
                                    f"UPDATE {table} "
                                    f"SET {enc_col} = :enc, {hash_col} = :hsh "
                                    f"WHERE id = :id"
                                )
                            else:
                                update_sql = (
                                    f"UPDATE {table} "
                                    f"SET {enc_col} = :enc "
                                    f"WHERE id = :id"
                                )
                            if not dry_run:
                                await db.execute(text(update_sql), params)

                        if not dry_run:
                            await db.commit()

                        encrypted_count += len(rows)
                        logger.info(
                            "pii.backfill_encrypt_interview_offer_existing%s: "
                            "%s — encrypted %d rows (batch)",
                            " (dry-run)" if dry_run else "",
                            key,
                            len(rows),
                        )

                        if len(rows) < batch_size:
                            break

                    summary["tables"][key] = {"encrypted": encrypted_count}

                except Exception as exc:
                    logger.error(
                        "pii.backfill_encrypt_interview_offer_existing: "
                        "error on %s: %s",
                        key, exc,
                    )
                    summary["errors"].append(f"{key}: {exc}")
                    try:
                        await db.rollback()
                    except Exception:
                        pass

        return summary

    span = _celery_span(
        "celery.task_start",
        "pii.backfill_encrypt_interview_offer_existing",
    )
    try:
        result = asyncio.run(_run())
        _finish_celery_success(
            span, "pii.backfill_encrypt_interview_offer_existing",
        )
        logger.info(
            "[pii.backfill_encrypt_interview_offer_existing] %s", result,
        )
        from app.shared.resilience.cron_health import record_cron_run
        record_cron_run("pii.backfill_encrypt_interview_offer_existing")
        return result
    except Exception as exc:
        _finish_celery_failure(
            span, "pii.backfill_encrypt_interview_offer_existing", exc,
        )
        logger.error(
            "pii.backfill_encrypt_interview_offer_existing falhou: %s", exc,
        )
        _emit_celery_retry(
            "pii.backfill_encrypt_interview_offer_existing",
            exc, self.request.retries, self.max_retries, 600,
        )
        if self.request.retries >= self.max_retries:
            _emit_dlq_push(
                "pii.backfill_encrypt_interview_offer_existing", exc,
            )
        raise self.retry(exc=exc, countdown=600)

# Sprint 11.0 (2026-05-24) — canonical async function extracted from
# `check_dsr_overdue_daily` Celery task body, callable by MonitoringLoop.
#
# Why: Celery NOT deployed on Replit; this task was orphan. LGPD Art. 20
# requires 15-day SLA response — without this, alerts not raised, team
# misses non-conformance windows. Sprint 11.0 wires this into the
# MonitoringLoop singleton via `_check_daily_dsr_overdue()` (see
# `app/domains/recruiter_assistant/services/monitoring_loop.py`).
#
# Canonical pattern (re-used Sprint 11.3 batches):
#   1. async def <task_canonical>(db) -> dict — does the actual work
#   2. Celery decorator task wraps with asyncio.run() + observability
#   3. MonitoringLoop calls async function directly with shared db
async def check_dsr_overdue_canonical(db) -> dict:
    """Check DataSubjectRequest overdue per LGPD Art. 20 + create Alerts.

    Canonical async function — same body as the Celery task's inner `_run`,
    extracted so MonitoringLoop can call directly without asyncio.run.

    Multi-tenancy: query crosses tenants (DSR overdue is a system-wide
    signal). RLS enforced per row via app_current_company_id() helper.

    Args:
        db: AsyncSession (caller provides — usually MonitoringLoop's
            shared session per iteration).

    Returns:
        dict with {ran_at, checked, overdue_found, alerts_created,
        alerts_skipped_duplicate, errors}
    """
    from datetime import datetime
    from sqlalchemy import and_, select
    from app.models.observability import DataSubjectRequest
    from lia_models.alert import Alert, AlertSeverity, AlertStatus, AlertType

    now = datetime.utcnow()
    summary = {
        "ran_at": now.isoformat(),
        "checked": 0,
        "overdue_found": 0,
        "alerts_created": 0,
        "alerts_skipped_duplicate": 0,
        "errors": [],
    }

    # Query DSRs overdue
    stmt = select(DataSubjectRequest).where(
        and_(
            DataSubjectRequest.sla_deadline < now,
            DataSubjectRequest.status.in_(["pending", "processing", "in_review"]),
        )
    )
    result = await db.execute(stmt)
    overdue_dsrs = list(result.scalars().all())
    summary["overdue_found"] = len(overdue_dsrs)
    summary["checked"] = len(overdue_dsrs)

    for dsr in overdue_dsrs:
        try:
            # Check existing active alert for this DSR
            existing_q = select(Alert).where(
                and_(
                    Alert.alert_type == AlertType.DEADLINE_APPROACHING,
                    Alert.status == AlertStatus.ACTIVE,
                    Alert.context["dsr_id"].astext == str(dsr.id),
                )
            )
            existing = (await db.execute(existing_q)).scalar_one_or_none()
            if existing is not None:
                summary["alerts_skipped_duplicate"] += 1
                continue

            # Create alert
            days_over = (now - dsr.sla_deadline).days
            alert = Alert(
                alert_type=AlertType.DEADLINE_APPROACHING,
                severity=AlertSeverity.HIGH,
                status=AlertStatus.ACTIVE,
                title=f"DSR LGPD prazo vencido ({days_over}d)",
                message=(
                    f"DSR {dsr.id} tipo \'{dsr.request_type}\' status \'{dsr.status}\' "
                    f"vencido em {days_over} dias (LGPD Art. 20 — 15 dias úteis). "
                    "Requer ação imediata para evitar não-conformidade ANPD."
                ),
                context={
                    "dsr_id": str(dsr.id),
                    "request_type": dsr.request_type,
                    "status": dsr.status,
                    "sla_deadline": dsr.sla_deadline.isoformat(),
                    "days_overdue": days_over,
                    "company_id": str(dsr.company_id),
                    "source": "Sprint 11.0 MonitoringLoop migration (was WT-2022 P5.3 cron)",
                },
            )
            db.add(alert)
            summary["alerts_created"] += 1

            # Hardening C.4 -- canary signal SLA worker LGPD.
            try:
                from app.shared.observability.canary_metrics import (
                    dsr_overdue_created_total,
                )
                if dsr_overdue_created_total is not None:
                    dsr_overdue_created_total.inc()
            except Exception as _metric_exc:  # pragma: no cover -- fail-open
                logger.debug(
                    "[dsr.check_overdue] canary metric inc failed (fail-open): %s",
                    _metric_exc,
                )

        except Exception as exc:
            summary["errors"].append({
                "dsr_id": str(dsr.id),
                "error": str(exc)[:200],
            })
            logger.error(
                "[dsr.check_overdue] Failed to create alert for DSR %s: %s",
                dsr.id, exc, exc_info=True,
            )

    await db.commit()

    return summary

