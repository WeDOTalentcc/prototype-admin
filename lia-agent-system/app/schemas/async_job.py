"""
AsyncJobResponse — schema padrão para operações de longa duração.

Endpoints que disparam tarefas Celery retornam este schema.
O cliente usa job_id para acompanhar progresso via WebSocket ou polling REST.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AsyncJobResponse(BaseModel):
    """Resposta imediata ao disparar uma operação assíncrona."""

    job_id: str = Field(..., description="ID único da tarefa Celery")
    status: Literal["queued", "processing", "completed", "failed"] = Field(
        default="queued",
        description="Status atual da tarefa",
    )
    estimated_duration_seconds: int = Field(
        default=30,
        description="Estimativa de duração em segundos (best-effort)",
    )
    websocket_url: str = Field(
        ...,
        description="URL WebSocket para acompanhar progresso em tempo real",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de criação da tarefa (UTC)",
    )
    domain: str | None = Field(
        default=None,
        description="Domínio que originou a tarefa (ex: sourcing, cv_screening)",
    )
    company_id: str | None = Field(
        default=None,
        description="ID da empresa dona da tarefa",
    )


class AsyncJobStatusResponse(BaseModel):
    """Status detalhado de uma tarefa — endpoint de polling fallback."""

    job_id: str
    status: Literal["queued", "processing", "completed", "failed"]
    progress_percent: int = Field(default=0, ge=0, le=100)
    message: str | None = None
    result: dict | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
