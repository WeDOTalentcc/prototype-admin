"""Celery tasks: compliance (Fase 7)."""
import asyncio
import re
from datetime import UTC

from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(name="audit.apply_lifecycle_policy", bind=True, max_retries=3)
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
        return {"applied": result}
    except Exception as exc:
        _finish_celery_failure(span, "audit.apply_lifecycle_policy", exc)
        logger.error(f"[audit.lifecycle] Error: {exc}")
        _emit_celery_retry("audit.apply_lifecycle_policy", exc, self.request.retries, self.max_retries, 3600)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("audit.apply_lifecycle_policy", exc)
        raise self.retry(exc=exc, countdown=3600)

@celery_app.task(name="lgpd.run_cleanup_daily", bind=True, max_retries=3)
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
        return result
    except Exception as exc:
        _finish_celery_failure(span, "lgpd.run_cleanup_daily", exc)
        logger.error("lgpd.run_cleanup_daily falhou: %s", exc)
        _emit_celery_retry("lgpd.run_cleanup_daily", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("lgpd.run_cleanup_daily", exc)
        raise self.retry(exc=exc, countdown=300)

@celery_app.task(name="conversation.ttl_cleanup", bind=True, max_retries=3)
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

@celery_app.task(name="pii.backfill_encrypt_existing", bind=True, max_retries=2)
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

@celery_app.task(
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

    from libs.models.lia_models.retention_policy import CompanyRetentionPolicy

    # Candidate model — try multiple import paths
    try:
        from libs.models.lia_models.candidate import Candidate
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

