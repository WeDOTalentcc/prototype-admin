"""Celery task: JD file upload processing (Audit B-02).

Wizard JD uploads were extracted **inside** the FastAPI request handler,
which let a single complex PDF or zip-bomb DOCX block the worker process
for arbitrarily long. This module moves the heavy parsing into a Celery
task with strict resource limits and pushes the result back to the
caller's WebSocket session via the existing ``background_task_update``
channel.

Architecture:
* ``jd_upload.process_file`` — the Celery task. Applies ``RLIMIT_AS`` and
  ``RLIMIT_CPU`` per worker child (POSIX only) before parsing so an
  expanding zip cannot OOM the pod. Soft timeout 25s, hard 30s.
* The endpoint stages the raw bytes in Redis under a TTL key so the task
  can read them without bloating the queue payload. The bytes never hit
  disk in plaintext.
* On completion / failure the task publishes a ``background_task_update``
  WS event to the session that initiated the upload (if known).

Resource limits are intentionally generous (512 MiB / 30s CPU) so legit
JDs always succeed; they exist to protect the pod from pathological
inputs, not to throttle normal users.
"""
from __future__ import annotations

import asyncio
import hashlib
import io
import json
import logging
import os
import resource
import sys
import time
import uuid as _uuid
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import celery_app

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Resource limits — applied lazily inside the worker so importing this module
# from a request handler (e.g. for `process_file.delay`) does not affect the
# FastAPI process limits.
# --------------------------------------------------------------------------- #

_DEFAULT_MEM_LIMIT_BYTES = 512 * 1024 * 1024  # 512 MiB virtual memory ceiling
_DEFAULT_CPU_LIMIT_SECONDS = 30


def _apply_extraction_rlimits() -> None:
    """Cap the worker child's memory and CPU before parsing.

    Limits are best-effort: on platforms without POSIX ``resource`` (e.g. macOS
    sandboxing, Windows) the call simply logs and returns. The values can be
    overridden via env vars for ops tuning.
    """
    if sys.platform.startswith("win"):
        return
    try:
        mem = int(os.getenv("JD_UPLOAD_MEM_LIMIT_BYTES", str(_DEFAULT_MEM_LIMIT_BYTES)))
        cpu = int(os.getenv("JD_UPLOAD_CPU_LIMIT_SECONDS", str(_DEFAULT_CPU_LIMIT_SECONDS)))
    except (TypeError, ValueError):
        mem = _DEFAULT_MEM_LIMIT_BYTES
        cpu = _DEFAULT_CPU_LIMIT_SECONDS
    try:
        # Some kernels (e.g. Cloud Run gvisor) refuse RLIMIT_AS — swallow.
        resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    except (ValueError, OSError) as exc:  # pragma: no cover — env-specific
        logger.debug("[jd_upload] RLIMIT_AS skipped: %s", exc)
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 5))
    except (ValueError, OSError) as exc:  # pragma: no cover
        logger.debug("[jd_upload] RLIMIT_CPU skipped: %s", exc)


# --------------------------------------------------------------------------- #
# Redis staging — keep payload off the queue and out of disk.
# --------------------------------------------------------------------------- #

_STAGE_PREFIX = "jd_upload:stage:"
_STAGE_TTL_SECONDS = 600  # 10 min — wide enough for backlog, narrow enough to drop on crash


async def _stage_key(task_id: str) -> str:
    return f"{_STAGE_PREFIX}{task_id}"


async def stage_payload(task_id: str, content: bytes) -> bool:
    """Persist the raw bytes under a TTL key so the worker can fetch them.

    Returns True on success. Falls back to local in-process dict when Redis is
    unavailable (single-process dev mode) so tests still work.
    """
    try:
        from app.core.redis_client import get_redis

        redis = await get_redis()
        await redis.set(await _stage_key(task_id), content, ex=_STAGE_TTL_SECONDS)
        return True
    except Exception as exc:
        logger.warning("[jd_upload] Redis staging failed (%s) — using in-mem fallback", exc)
        _sweep_local_stage()
        _LOCAL_STAGE[task_id] = (content, _now() + _STAGE_TTL_SECONDS)
        return True


async def fetch_payload(task_id: str) -> bytes | None:
    try:
        from app.core.redis_client import get_redis

        redis = await get_redis()
        key = await _stage_key(task_id)
        data = await redis.get(key)
        if data is not None:
            await redis.delete(key)
            if isinstance(data, str):
                data = data.encode("utf-8", errors="replace")
            return data
    except Exception as exc:
        logger.warning("[jd_upload] Redis fetch failed: %s", exc)
    # in-mem fallback — drop expired entries before serving so a crashed
    # worker cannot leave staged bytes pinned in memory forever.
    _sweep_local_stage()
    entry = _LOCAL_STAGE.pop(task_id, None)
    if entry is None:
        return None
    content, expires_at = entry
    if expires_at <= _now():
        return None
    return content


# In-process fallback when Redis is unavailable. Each entry is a
# ``(payload, monotonic_expires_at)`` tuple so abandoned uploads (e.g. a
# Celery worker that crashed between ``stage_payload`` and ``fetch_payload``)
# are evicted on the next access instead of leaking until the process
# restarts. The TTL mirrors the Redis path's ``_STAGE_TTL_SECONDS``.
_LOCAL_STAGE: dict[str, tuple[bytes, float]] = {}


def _now() -> float:
    """Indirection over ``time.monotonic`` so tests can fast-forward."""
    return time.monotonic()


def _sweep_local_stage() -> None:
    """Drop expired entries from the in-process fallback store."""
    now = _now()
    expired = [key for key, (_, exp) in _LOCAL_STAGE.items() if exp <= now]
    for key in expired:
        _LOCAL_STAGE.pop(key, None)


# --------------------------------------------------------------------------- #
# WebSocket broadcast — direct Redis publish so we do not depend on the
# in-process WSManager (worker runs in a separate process).
# --------------------------------------------------------------------------- #

_WS_CHANNEL_PREFIX = "ws:session:"


async def _broadcast_ws(session_id: str | None, payload: dict[str, Any]) -> None:
    if not session_id:
        return
    try:
        from app.core.redis_client import get_redis

        redis = await get_redis()
        await redis.publish(
            f"{_WS_CHANNEL_PREFIX}{session_id}",
            json.dumps(payload, default=str),
        )
    except Exception as exc:
        logger.debug("[jd_upload] WS broadcast failed: %s", exc)


def _serialize_progress(
    task_id: str,
    status: str,
    *,
    progress: int | None = None,
    message: str = "",
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mirror of `serialize_background_task_update` — kept inline to avoid
    pulling FastAPI imports into the worker."""
    return {
        "type": "background_task_update",
        "task_id": task_id,
        "task_type": "wizard",
        "label": "Importação de Job Description",
        "status": status,
        "progress": progress,
        "message": message or None,
        "result": result,
    }


# --------------------------------------------------------------------------- #
# Pure extraction — kept testable / sync. Imports are lazy so the worker
# only loads pypdf / python-docx when actually needed.
# --------------------------------------------------------------------------- #


def _extract_text(content: bytes, ext: str) -> str:
    if ext in {".txt", ".md"}:
        return content.decode("utf-8", errors="replace")
    if ext == ".pdf":
        import pypdf  # type: ignore[import]

        reader = pypdf.PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == ".docx":
        import docx  # type: ignore[import]

        document = docx.Document(io.BytesIO(content))
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())
    raise ValueError(f"Unsupported extension for extraction: {ext}")


def _hash_filename(filename: str) -> str:
    return hashlib.sha256((filename or "").encode("utf-8", errors="replace")).hexdigest()


# --------------------------------------------------------------------------- #
# Async core — runs inside the Celery task event loop.
# --------------------------------------------------------------------------- #


async def _process_file_async(
    *,
    task_id: str,
    company_id_str: str,
    user_id: str | None,
    filename: str,
    extension: str,
    title: str,
    consent_acknowledged: bool,
    session_id: str | None,
) -> dict[str, Any]:
    from app.api.v1.jd_import import (  # local import — avoid heavy import at worker boot
        JD_UPLOAD_AUDIT_AGENT,
        _company_has_jd_upload_consent,
        _record_jd_upload_audit,
        _record_jd_upload_consent,
    )
    from app.domains.job_management.services.jd_import_service import JDImportService
    from app.core.database import AsyncSessionLocal

    company_uuid = UUID(company_id_str)

    content = await fetch_payload(task_id)
    if content is None:
        await _broadcast_ws(
            session_id,
            _serialize_progress(
                task_id,
                "failed",
                message="Payload do upload expirou antes do processamento.",
            ),
        )
        return {"success": False, "error": "payload_expired"}

    await _broadcast_ws(
        session_id,
        _serialize_progress(task_id, "running", progress=20, message="Extraindo texto..."),
    )

    try:
        raw_text = _extract_text(content, extension)
    except MemoryError:
        # rlimits triggered — return clean error instead of crashing the worker.
        msg = "Arquivo excedeu o limite de memória durante a extração (possível zip bomb)."
        await _broadcast_ws(session_id, _serialize_progress(task_id, "failed", message=msg))
        return {"success": False, "error": "resource_exceeded", "detail": msg}
    except Exception as exc:
        msg = f"Falha ao ler {extension.upper()}: {exc}"
        await _broadcast_ws(session_id, _serialize_progress(task_id, "failed", message=msg))
        return {"success": False, "error": "extraction_failed", "detail": str(exc)}

    if not raw_text.strip():
        msg = "Arquivo vazio ou sem texto extraível."
        await _broadcast_ws(session_id, _serialize_progress(task_id, "failed", message=msg))
        return {"success": False, "error": "empty_text", "detail": msg}

    # PII minimization (LGPD) — fail-safe.
    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt

        raw_text = strip_pii_for_llm_prompt(raw_text)
    except Exception:
        pass

    # FairnessGuard — same gating as the synchronous endpoint had.
    fairness_warnings: list[str] = []
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard

        fg_result = FairnessGuard().check(raw_text[:2000])
        if getattr(fg_result, "is_blocked", False):
            msg = (
                f"JD contém linguagem discriminatória e não pode ser importada. "
                f"{getattr(fg_result, 'educational_message', '') or 'Revise o conteúdo.'}"
            )
            await _broadcast_ws(session_id, _serialize_progress(task_id, "failed", message=msg))
            return {"success": False, "error": "fairness_blocked", "detail": msg}
        if getattr(fg_result, "soft_warnings", None):
            fairness_warnings = list(fg_result.soft_warnings)
    except Exception:
        pass  # fail-safe

    await _broadcast_ws(
        session_id,
        _serialize_progress(task_id, "running", progress=70, message="Importando vaga..."),
    )

    jd_data = {
        "title": title or filename.rsplit(".", 1)[0],
        "description": raw_text,
        "source_file": filename,
    }

    service = JDImportService()
    async with AsyncSessionLocal() as db:
        imported = await service.import_jd(
            db=db,
            company_id=company_uuid,
            jd_data=jd_data,
            source="file_upload",
            parse_immediately=True,
        )
        imported_dict = imported.to_dict()

    filename_hash = _hash_filename(filename)
    upload_uuid = task_id  # task_id doubles as audit uuid for traceability

    await _record_jd_upload_audit(
        company_id=company_uuid,
        user_id=user_id,
        upload_uuid=upload_uuid,
        filename_hash=filename_hash,
        size_bytes=len(content),
        extension=extension,
        fairness_warnings_count=len(fairness_warnings),
    )

    if consent_acknowledged:
        try:
            already = await _company_has_jd_upload_consent(company_uuid)
            if not already:
                await _record_jd_upload_consent(company_uuid, user_id)
        except Exception:
            pass

    result = {
        "success": True,
        **imported_dict,
        "source_filename": filename,
        "audit": {
            "uuid": upload_uuid,
            "filename_hash": filename_hash,
            "size_bytes": len(content),
        },
    }
    if fairness_warnings:
        result["fairness_warnings"] = fairness_warnings

    await _broadcast_ws(
        session_id,
        _serialize_progress(
            task_id,
            "completed",
            progress=100,
            message="Vaga importada com sucesso.",
            result={"imported_jd_id": imported_dict.get("id")},
        ),
    )
    return result


# --------------------------------------------------------------------------- #
# Celery entry point
# --------------------------------------------------------------------------- #


@celery_app.task(base=TenantAwareTask, 
    name="vagas.jd_upload.process_file",
    bind=True,
    soft_time_limit=25,
    time_limit=30,
    max_retries=0,
    queue="vagas_normal",
)
def jd_upload_process_file_task(
    self,
    task_id: str,
    company_id: str,
    user_id: str | None,
    filename: str,
    extension: str,
    title: str = "",
    consent_acknowledged: bool = False,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Process a staged JD upload payload asynchronously."""
    _apply_extraction_rlimits()

    async def _run() -> dict[str, Any]:
        return await _process_file_async(
            task_id=task_id,
            company_id_str=company_id,
            user_id=user_id,
            filename=filename,
            extension=extension,
            title=title,
            consent_acknowledged=consent_acknowledged,
            session_id=session_id,
        )

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("[jd_upload] task failed: %s", exc)
        try:
            asyncio.run(
                _broadcast_ws(
                    session_id,
                    _serialize_progress(
                        task_id,
                        "failed",
                        message=f"Falha inesperada: {exc}",
                    ),
                )
            )
        except Exception:
            pass
        return {"success": False, "error": "unexpected", "detail": str(exc)}


def new_task_id() -> str:
    return str(_uuid.uuid4())


__all__ = [
    "jd_upload_process_file_task",
    "stage_payload",
    "fetch_payload",
    "new_task_id",
]
