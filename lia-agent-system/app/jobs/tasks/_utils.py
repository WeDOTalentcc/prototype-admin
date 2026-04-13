"""Shared Celery task helpers and tracing spans (Fase 7)."""

import asyncio
import re
from datetime import UTC

from app.core.celery_app import celery_app
from app.shared.pii_masking import get_masked_logger
from app.shared.tracing import finish_span, get_tracer

logger = get_masked_logger(__name__)

def _celery_span(name: str, task_name: str):
    """Helper: cria span sync para Celery task com OTel timing."""
    tracer = get_tracer()
    return tracer.create_span(name, attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}",
        "celery.task_name": task_name,
    }, _start_otel=True)

def _finish_celery_success(start_span, task_name: str):
    """Finaliza start span e emite celery.task_success."""
    finish_span(start_span, status="success")
    tracer = get_tracer()
    success_span = tracer.create_span("celery.task_success", attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}",
        "celery.task_name": task_name,
    }, _start_otel=True)
    finish_span(success_span, status="ok")

def _finish_celery_failure(start_span, task_name: str, exc: Exception):
    """Finaliza start span e emite celery.task_failure."""
    finish_span(start_span, status="failure", error=exc)
    tracer = get_tracer()
    fail_span = tracer.create_span("celery.task_failure", attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}",
        "celery.task_name": task_name, "error.type": type(exc).__name__,
    }, _start_otel=True)
    finish_span(fail_span, status="error", error=exc)

def _emit_celery_retry(task_name: str, exc: Exception, attempt: int, max_retries: int, countdown: int):
    """Emite span celery.task_retry com metadados de tentativa."""
    tracer = get_tracer()
    retry_span = tracer.create_span("celery.task_retry", attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}",
        "celery.task_name": task_name, "error.type": type(exc).__name__,
        "retry.attempt": str(attempt), "retry.max_retries": str(max_retries),
        "retry.countdown_seconds": str(countdown),
    }, _start_otel=True)
    finish_span(retry_span, status="retry", error=exc)

def _emit_dlq_push(task_name: str, exc: Exception):
    """Emite span celery.dlq_push quando retries são esgotados."""
    tracer = get_tracer()
    dlq_span = tracer.create_span("celery.dlq_push", attributes={
        "service": "celery_tasks", "tier_name": f"celery_{task_name}_dlq",
        "celery.task_name": task_name, "error.type": type(exc).__name__,
        "dlq.reason": "max_retries_exceeded",
    }, _start_otel=True)
    finish_span(dlq_span, status="error", error=exc)

