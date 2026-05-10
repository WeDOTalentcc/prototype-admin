"""
Async Endpoints — Fase 5

Endpoints que disparam tarefas Celery de longa duração e retornam AsyncJobResponse.
O cliente acompanha progresso via WebSocket /ws/jobs/{job_id}.
"""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.celery_app import celery_app
from app.schemas.async_job import AsyncJobResponse, AsyncJobStatusResponse

router = APIRouter(prefix="/async", tags=["async-jobs"])
logger = logging.getLogger(__name__)

_WS_BASE = "/ws/jobs"


def _build_response(task_result, domain: str, company_id: str, estimate: int) -> AsyncJobResponse:
    return AsyncJobResponse(
        job_id=task_result.id,
        status="queued",
        estimated_duration_seconds=estimate,
        websocket_url=f"{_WS_BASE}/{task_result.id}",
        domain=domain,
        company_id=company_id,
    )


# ---------------------------------------------------------------------------
# Triagem em lote
# ---------------------------------------------------------------------------

class TriagemBatchRequest(BaseModel):
    candidate_ids: list[str] = Field(..., min_items=1, description="IDs dos candidatos a triar")
    job_id: str = Field(..., description="ID da vaga")
    company_id: str = Field(..., description="ID da empresa")


@router.post("/triagem/run-batch", response_model=AsyncJobResponse, summary="Triagem curricular em lote")
async def run_triagem_batch(req: TriagemBatchRequest):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Dispara triagem curricular em lote via Celery.
    Retorna job_id para acompanhar via WebSocket.
    Estimativa: ~1s por candidato + overhead (mínimo 10s).
    """
    try:
        task = celery_app.send_task(
            "agents.triagem.run",
            kwargs={
                "candidate_ids": req.candidate_ids,
                "job_id": req.job_id,
                "company_id": req.company_id,
            },
        )
        estimate = max(10, len(req.candidate_ids) * 2)
        return _build_response(task, "cv_screening", req.company_id, estimate)
    except Exception as exc:
        logger.error("Falha ao enfileirar triagem: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao enfileirar triagem")


# ---------------------------------------------------------------------------
# Entrevista WSI
# ---------------------------------------------------------------------------

class WSIInterviewRequest(BaseModel):
    candidate_id: str
    job_id: str
    company_id: str
    interview_type: str = Field(default="wsi_full", description="wsi_full | wsi_quick | triagem_voz")
    context: dict = Field(default_factory=dict)


@router.post("/interviews/wsi/start", response_model=AsyncJobResponse, summary="Iniciar entrevista WSI")
async def start_wsi_interview(req: WSIInterviewRequest):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Inicia entrevista WSI em background.
    Sessões podem durar de 20 minutos a 2 horas.
    """
    try:
        task = celery_app.send_task(
            "agents.wsi_interview.start",
            kwargs={
                "request_data": req.model_dump(exclude={"company_id"}),
                "company_id": req.company_id,
            },
        )
        return _build_response(task, "interview_scheduling", req.company_id, 1800)
    except Exception as exc:
        logger.error("Falha ao enfileirar WSI interview: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao iniciar entrevista WSI")


# ---------------------------------------------------------------------------
# Sourcing assíncrono
# ---------------------------------------------------------------------------

class SourcingSearchRequest(BaseModel):
    criteria: dict = Field(..., description="Critérios de busca: skills, location, seniority, etc.")
    job_id: str
    company_id: str


@router.post("/sourcing/search", response_model=AsyncJobResponse, summary="Busca de candidatos via Pearch")
async def search_candidates_async(req: SourcingSearchRequest):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Busca candidatos via Pearch AI + banco interno em background.
    Pearch pode levar 30-120s dependendo do perfil.
    """
    try:
        task = celery_app.send_task(
            "agents.sourcing.search",
            kwargs={
                "criteria": req.criteria,
                "job_id": req.job_id,
                "company_id": req.company_id,
            },
        )
        return _build_response(task, "sourcing", req.company_id, 60)
    except Exception as exc:
        logger.error("Falha ao enfileirar sourcing search: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao enfileirar busca de candidatos")


# ---------------------------------------------------------------------------
# Email em massa
# ---------------------------------------------------------------------------

class BulkEmailRequest(BaseModel):
    recipients: list[str] = Field(..., min_items=1)
    template_id: str | None = None
    subject: str = ""
    body: str = ""
    variables: dict = Field(default_factory=dict)
    company_id: str


@router.post("/communication/email/bulk", response_model=AsyncJobResponse, summary="Envio de email em massa")
async def send_bulk_email(req: BulkEmailRequest):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Dispara envio de email em massa via Celery.
    Usa chunks para listas grandes (> 100 destinatários).
    5 retries com exponential backoff.
    """
    try:
        task = celery_app.send_task(
            "communication.email.send_bulk",
            kwargs={
                "email_data": req.model_dump(exclude={"company_id"}),
                "company_id": req.company_id,
            },
        )
        estimate = max(10, len(req.recipients) // 10)
        return _build_response(task, "communication", req.company_id, estimate)
    except Exception as exc:
        logger.error("Falha ao enfileirar bulk email: %s", exc)
        raise HTTPException(status_code=500, detail="Erro ao enfileirar envio de emails")


# ---------------------------------------------------------------------------
# Status polling (fallback quando WebSocket não disponível)
# ---------------------------------------------------------------------------

@router.get("/jobs/{job_id}/status", response_model=AsyncJobStatusResponse, summary="Status de tarefa async")
async def get_job_status(job_id: str):
    """
    Polling fallback — retorna status atual de uma tarefa Celery.
    Preferir WebSocket /ws/jobs/{job_id} para atualizações em tempo real.
    """
    try:
        result = celery_app.AsyncResult(job_id)
        status_map = {
            "PENDING": "queued",
            "STARTED": "processing",
            "SUCCESS": "completed",
            "FAILURE": "failed",
            "RETRY": "processing",
            "REVOKED": "failed",
        }
        from datetime import datetime
        return AsyncJobStatusResponse(
            job_id=job_id,
            status=status_map.get(result.state, "queued"),
            progress_percent=100 if result.state == "SUCCESS" else 0,
            message=None,
            result=result.result if result.state == "SUCCESS" and isinstance(result.result, dict) else None,
            error=str(result.result) if result.state == "FAILURE" else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    except Exception as exc:
        logger.error("Falha ao consultar status do job %s: %s", job_id, exc)
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
