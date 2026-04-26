"""
JD Import API endpoints.

Phase 1B Learning Loop: Import job descriptions from ATS/HRIS.

Endpoints:
- POST /import/batch - Import multiple JDs
- POST /import/single - Import single JD
- GET /import/stats - Get import statistics
- GET /import/batches - List import batches
- GET /suggestions/{field} - Get suggestions for a wizard field
- GET /similar-jobs - Find similar jobs for Fast Track
"""
import hashlib
import logging
import uuid as _uuid_mod
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_user_or_demo,
    get_current_user_strict,
    get_user_company_id,
)
from app.auth.models import User
from app.core.database import AsyncSessionLocal, get_db
from app.domains.job_management.services.jd_import_service import JDImportService, get_jd_import_service


# Local factory — uses module-local JDImportService (supports test mocking)
def get_jd_import_service():  # type: ignore[override]  # noqa: F811
    """DI factory for JDImportService — creates new instance using module-local class."""
    return JDImportService()

from app.domains.job_management.services.wizard_data_priority_service import JobContext, WizardDataPriorityService, get_wizard_data_priority_service

router = APIRouter(tags=["Learning Loop"])
logger = logging.getLogger(__name__)

def parse_company_id(company_id: str) -> UUID:
    """Convert company_id string to UUID."""
    if not company_id:
        raise ValueError("company_id is required")
    try:
        return UUID(company_id)
    except ValueError:
        raise ValueError(f"Invalid company_id: '{company_id}'. A valid UUID is required.")


class JDImportItem(BaseModel):
    """Single JD to import."""
    title: str = Field(..., description="Job title")
    external_id: str | None = None
    department: str | None = None
    area: str | None = None
    seniority: str | None = None
    employment_type: str | None = None
    work_model: str | None = None
    location: str | None = None
    description: str | None = None
    responsibilities_text: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "BRL"
    benefits: list[str] = []
    hiring_manager: str | None = None
    recruiter: str | None = None
    headcount: int = 1
    status: str | None = None
    was_filled: bool | None = None
    candidates_count: int | None = None
    time_to_fill_days: int | None = None
    created_date: datetime | None = None
    closed_date: datetime | None = None
    metadata: dict[str, Any] = {}


class BatchImportRequest(BaseModel):
    """Request to import multiple JDs."""
    source: str = Field(default="manual_upload", description="Import source (ats_gupy, manual_upload, etc.)")
    jds: list[JDImportItem] = Field(..., description="List of JDs to import")


class BatchImportResponse(BaseModel):
    """Response from batch import."""
    batch_id: str
    status: str
    total: int
    successful: int
    failed: int
    skipped: int
    errors: list[dict[str, Any]] = []


class SuggestionResponse(BaseModel):
    """Response with suggestion data."""
    value: Any
    source: str
    confidence: float
    explanation: str
    metadata: dict[str, Any] = {}


class DataCoverageResponse(BaseModel):
    """Response with data coverage statistics."""
    imported_jds: int
    skills_catalog: int
    job_patterns: int
    coverage_score: int
    recommendations: list[str] = []


@router.post("/import/batch", response_model=BatchImportResponse)
async def import_batch_jds(
    request: BatchImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    service: JDImportService = Depends(get_jd_import_service),
):
    """
    Import multiple job descriptions in a batch.
    
    This endpoint parses and normalizes JDs from external sources,
    building the company's skill catalog and learning patterns.
    """
    company_id = parse_company_id(get_user_company_id(current_user))
    user_id = str(current_user.id) if current_user.id else None

    # FAR-2: FairnessGuard — verificar JDs antes de importar
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        for _jd in request.jds:
            _text = f"{_jd.title} {_jd.description or ''}"
            _fg_result = _fg.check(_text)
            if _fg_result.is_blocked:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "fairness_blocked",
                        "category": _fg_result.category,
                        "message": _fg_result.educational_message,
                        "job_title": _jd.title,
                    },
                )
    except Exception as _fg_exc:
        if getattr(_fg_exc, "status_code", None) == 422:
            raise
        pass  # fail-open

    jds_data = [jd.model_dump() for jd in request.jds]

    batch = await service.import_batch_jds(
        db=db,
        company_id=company_id,
        jds_data=jds_data,
        source=request.source,
        created_by=user_id
    )
    
    return BatchImportResponse(
        batch_id=str(batch.id),
        status=batch.status,
        total=batch.total_records,
        successful=batch.successful_records,
        failed=batch.failed_records,
        skipped=batch.skipped_records,
        errors=batch.errors or []
    )


@router.post("/import/single", response_model=dict[str, Any])
async def import_single_jd(
    jd: JDImportItem,
    source: str = Query("manual_upload", description="Import source"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    service: JDImportService = Depends(get_jd_import_service),
):
    """
    Import a single job description.
    
    Returns the parsed and normalized JD data.
    """
    company_id = parse_company_id(get_user_company_id(current_user))

    # FAR-2: FairnessGuard — verificar JD antes de importar
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        _text = f"{jd.title} {jd.description or ''}"
        _fg_result = _fg.check(_text)
        if _fg_result.is_blocked:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "fairness_blocked",
                    "category": _fg_result.category,
                    "message": _fg_result.educational_message,
                },
            )
    except Exception as _fg_exc:
        if getattr(_fg_exc, "status_code", None) == 422:
            raise
        pass  # fail-open

    imported = await service.import_jd(
        db=db,
        company_id=company_id,
        jd_data=jd.model_dump(),
        source=source,
        parse_immediately=True
    )
    
    return imported.to_dict()


@router.get("/import/stats", response_model=dict[str, Any])
async def get_import_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    service: JDImportService = Depends(get_jd_import_service),
):
    """
    Get import statistics for a company.
    
    Shows total JDs imported, skills in catalog, and recent imports.
    """
    company_id = parse_company_id(get_user_company_id(current_user))
    
    return await service.get_import_stats(db, company_id)


@router.get("/suggestions/{field}", response_model=Optional[SuggestionResponse])
async def get_field_suggestion(
    field: str,
    job_title: str | None = Query(None),
    department: str | None = Query(None),
    seniority: str | None = Query(None),
    location: str | None = Query(None),
    work_model: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    service: WizardDataPriorityService = Depends(get_wizard_data_priority_service),
):
    """
    Get the best suggestion for a wizard field.
    
    Queries all data sources in priority order and returns
    the best match with confidence score and explanation.
    
    Fields: job_title, department, seniority, salary_range,
            technical_skills, behavioral_competencies,
            responsibilities, benefits
    """
    company_id = parse_company_id(get_user_company_id(current_user))
    
    context = JobContext(
        company_id=company_id,
        job_title=job_title,
        department=department,
        seniority=seniority,
        location=location,
        work_model=work_model
    )
    
    suggestion = await service.get_suggestion(db, field, context)
    
    if suggestion:
        return SuggestionResponse(
            value=suggestion.value,
            source=suggestion.source.value,
            confidence=suggestion.confidence,
            explanation=suggestion.explanation,
            metadata=suggestion.metadata
        )
    
    return None


@router.get("/suggestions/all", response_model=dict[str, SuggestionResponse])
async def get_all_field_suggestions(
    job_title: str | None = Query(None),
    department: str | None = Query(None),
    seniority: str | None = Query(None),
    location: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    service: WizardDataPriorityService = Depends(get_wizard_data_priority_service),
):
    """
    Get suggestions for all wizard fields at once.
    
    More efficient than calling individual endpoints.
    """
    company_id = parse_company_id(get_user_company_id(current_user))
    
    context = JobContext(
        company_id=company_id,
        job_title=job_title,
        department=department,
        seniority=seniority,
        location=location
    )
    
    suggestions = await service.get_field_suggestions(db, context)
    
    return {
        field: SuggestionResponse(
            value=s.value,
            source=s.source.value,
            confidence=s.confidence,
            explanation=s.explanation,
            metadata=s.metadata
        )
        for field, s in suggestions.items()
    }


@router.get("/similar-jobs", response_model=list[dict[str, Any]])
async def get_similar_jobs(
    job_title: str | None = Query(None),
    department: str | None = Query(None),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    service: WizardDataPriorityService = Depends(get_wizard_data_priority_service),
):
    """
    Find similar jobs for Fast Track mode.
    
    Returns jobs from imported JDs and LIA history
    that can be used as templates.
    """
    company_id = parse_company_id(get_user_company_id(current_user))
    
    context = JobContext(
        company_id=company_id,
        job_title=job_title,
        department=department
    )
    
    return await service.get_similar_jobs(db, context, limit)


# ---------------------------------------------------------------------------
# Task #838 — JD upload privacy & audit hardening
# ---------------------------------------------------------------------------
# Records consent + each upload event in `audit_logs` (immutable) instead of
# the previous best-effort `logger.info`. Filename is hashed (SHA-256) before
# persistence so plaintext PII never reaches the audit trail (mitigates M-13).
# ---------------------------------------------------------------------------

JD_UPLOAD_CONSENT_AGENT = "jd_upload_consent"
JD_UPLOAD_AUDIT_AGENT = "jd_upload"


def _hash_filename(filename: str) -> str:
    """Return a stable SHA-256 hex digest of the filename (avoids logging PII)."""
    return hashlib.sha256((filename or "").encode("utf-8", errors="replace")).hexdigest()


async def _company_has_jd_upload_consent(company_id: UUID) -> bool:
    """Return True if the company has previously granted JD upload consent."""
    from lia_models.audit_log import AuditLog

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(AuditLog.id)
                .where(
                    and_(
                        AuditLog.company_id == str(company_id),
                        AuditLog.agent_name == JD_UPLOAD_CONSENT_AGENT,
                        AuditLog.decision == "granted",
                    )
                )
                .limit(1)
            )
            return result.scalar_one_or_none() is not None
    except Exception as exc:  # pragma: no cover — fail-closed when DB unreachable
        logger.warning("[jd-import/upload] consent lookup failed: %s", exc)
        return False


async def _record_jd_upload_consent(company_id: UUID, user_id: str | None) -> None:
    """Persist a one-shot JD-upload consent record per company (LGPD Art. 7/8)."""
    from lia_models.audit_log import AuditLog

    try:
        async with AsyncSessionLocal() as session:
            log = AuditLog(
                id=str(_uuid_mod.uuid4()),
                company_id=str(company_id),
                agent_name=JD_UPLOAD_CONSENT_AGENT,
                # decision_type is a free-form String(100) on AuditLog; using a
                # dedicated value keeps governance dashboards able to filter
                # consent grants without colliding with feedback audits.
                decision_type="consent_granted",
                action="jd_upload_consent",
                decision="granted",
                reasoning=[
                    "purpose=jd_processing",
                    "legal_basis=LGPD Art. 7º, II",
                    "scope=company",
                ],
                criteria_used=["consent_purpose:jd_processing"],
                criteria_ignored=[],
                actor_user_id=user_id,
                retention_until=datetime.utcnow() + timedelta(days=1825),
            )
            session.add(log)
            await session.commit()
    except Exception as exc:
        logger.warning("[jd-import/upload] consent persistence failed: %s", exc)


async def _record_jd_upload_audit(
    *,
    company_id: UUID,
    user_id: str | None,
    upload_uuid: str,
    filename_hash: str,
    size_bytes: int,
    extension: str,
    fairness_warnings_count: int,
) -> None:
    """Persist an immutable upload record (M-10): user, company, hash, size, uuid, ts."""
    from lia_models.audit_log import AuditLog

    try:
        async with AsyncSessionLocal() as session:
            log = AuditLog(
                id=upload_uuid,
                company_id=str(company_id),
                agent_name=JD_UPLOAD_AUDIT_AGENT,
                decision_type="job_creation",
                action="jd_file_upload",
                decision="imported",
                reasoning=[
                    f"filename_hash={filename_hash}",
                    f"size_bytes={size_bytes}",
                    f"extension={extension}",
                    f"fairness_warnings={fairness_warnings_count}",
                ],
                criteria_used=["filename_hash", "size_bytes", "extension"],
                criteria_ignored=[],
                actor_user_id=user_id,
                retention_until=datetime.utcnow() + timedelta(days=1825),
            )
            session.add(log)
            await session.commit()
    except Exception as exc:
        # Audit failure should not silently lose the upload trail. Re-raise so
        # the request fails closed and the operator is alerted.
        logger.error("[jd-import/upload] audit persistence failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Falha ao registrar auditoria do upload. Tente novamente.",
        )


@router.get("/import/jd-upload/consent-status", response_model=dict[str, bool])
async def get_jd_upload_consent_status(
    current_user: User = Depends(get_current_user_strict),
) -> dict[str, bool]:
    """
    Preflight para o gate LGPD de upload de JD (Task #838 / M-01).

    Devolve `{has_consent: bool}` para a empresa do usuário autenticado.
    O frontend usa essa resposta para suprimir o diálogo de consentimento
    quando a empresa já consentiu em sessão anterior — concretizando o
    requisito "bypass para domínios já consentidos".

    Não tem efeito colateral: read-only sobre `audit_logs`.
    """
    company_id = parse_company_id(get_user_company_id(current_user))
    has_consent = await _company_has_jd_upload_consent(company_id)
    return {"has_consent": bool(has_consent)}


@router.post("/import/upload-file", status_code=202)
async def upload_jd_file(
    file: UploadFile = File(..., description="Arquivo JD (.txt, .pdf, .docx, .md)"),
    title: str = Query("", description="Título da vaga (opcional, extraído do arquivo se vazio)"),
    consent_acknowledged: bool = Query(
        False,
        description=(
            "LGPD Art. 7: o usuário confirma o consentimento granular para "
            "processamento da JD nesta sessão. Empresas que já consentiram "
            "previamente são liberadas automaticamente."
        ),
    ),
    session_id: str = Query(
        "",
        description=(
            "ID da sessão WebSocket que receberá `background_task_update` "
            "com o progresso. Opcional — se omitido, o cliente precisa "
            "consultar status por outro canal."
        ),
    ),
    current_user: User = Depends(get_current_user_strict),
) -> dict[str, Any]:
    """
    Aceita o upload de uma Job Description e enfileira o parse para um worker
    Celery (Audit B-02). O endpoint só faz validações leves (auth, consent,
    magic number, tamanho) — a extração PDF/DOCX e o `JDImportService.import_jd`
    rodam fora do request loop.

    Privacidade & auditoria (Task #838 / #858):
    - Autenticação estrita: o modo demo está desabilitado (M-09).
    - Consentimento granular explícito uma vez por empresa, com bypass em
      sessões subsequentes a partir do registro imutável (M-01).
    - Validação por **magic number** antes de qualquer parse (A-02).
    - Limite de tamanho compartilhado com o proxy Next.js (M-12) via
      `UPLOAD_JD_MAX_BYTES`.
    - Cada upload grava `user_id`, `company_id`, `filename_hash`, `size_bytes`,
      `uuid` e `timestamp` em `audit_logs` (M-10) — feito pelo worker.

    Returns:
        ``202 {task_id, status: "queued", ...}``. O frontend acompanha o
        progresso via WS `background_task_update` (canal já existente).
    """
    from app.jobs.tasks.jd_upload import (
        jd_upload_process_file_task,
        new_task_id,
        stage_payload,
    )
    from app.shared.upload_limits import JD_UPLOAD_MAX_BYTES, jd_upload_max_mb
    from app.shared.upload_validators import UnsupportedFileTypeError, validate_upload

    # Identidade do solicitante — necessária para consent + enfileiramento
    company_id = parse_company_id(get_user_company_id(current_user))
    user_id = str(current_user.id) if getattr(current_user, "id", None) else None

    # M-01: Consentimento granular explícito (com bypass para empresas já consentidas)
    if not consent_acknowledged:
        already_consented = await _company_has_jd_upload_consent(company_id)
        if not already_consented:
            raise HTTPException(
                status_code=428,
                detail={
                    "error": "consent_required",
                    "message": (
                        "Para enviar a Job Description, confirme o consentimento "
                        "granular LGPD para processamento desta JD."
                    ),
                    "purpose": "jd_processing",
                    "consent_param": "consent_acknowledged",
                    "legal_basis": "LGPD Art. 7º, II / EU AI Act Art. 13",
                },
            )

    # M-12: Limite de tamanho idêntico ao proxy Next.js (env UPLOAD_JD_MAX_BYTES,
    # default 10 MiB). Lê os bytes uma vez e bloqueia antes de qualquer parse.
    content = await file.read()
    if len(content) > JD_UPLOAD_MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande. Máximo: {jd_upload_max_mb()}MB",
        )

    filename = file.filename or ""

    # A-02: Validação por magic number antes de aceitar a fila.
    try:
        validated = validate_upload(filename, content)
    except UnsupportedFileTypeError as exc:
        # Distingue extensão whitelist (400) de bytes que não batem (415).
        from app.shared.upload_validators import _ALLOWED_EXTENSIONS  # type: ignore

        status_code = 400 if (exc.declared_ext or "") not in _ALLOWED_EXTENSIONS else 415
        raise HTTPException(status_code=status_code, detail=str(exc))

    # Stage do payload em Redis (TTL 10 min) — mantém o body fora da fila.
    task_id = new_task_id()
    await stage_payload(task_id, content)

    # Enfileiramento — soft/hard timeout e rlimits são aplicados dentro do worker.
    try:
        jd_upload_process_file_task.apply_async(
            kwargs={
                "task_id": task_id,
                "company_id": str(company_id),
                "user_id": user_id,
                "filename": filename,
                "extension": validated.extension,
                "title": title,
                "consent_acknowledged": consent_acknowledged,
                "session_id": session_id or None,
            },
            task_id=task_id,
        )
    except Exception as exc:
        logger.error("[jd-import/upload] enqueue failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Fila de processamento indisponível. Tente novamente em instantes.",
        )

    return {
        "success": True,
        "task_id": task_id,
        "status": "queued",
        "message": "Upload aceito. Acompanhe o progresso via WebSocket.",
        "audit": {
            "uuid": task_id,
            "filename_hash": _hash_filename(filename),
            "size_bytes": len(content),
        },
    }


@router.get("/data-coverage", response_model=DataCoverageResponse)
async def get_data_coverage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    service: WizardDataPriorityService = Depends(get_wizard_data_priority_service),
):
    """
    Get data coverage statistics.
    
    Shows which data sources have data and provides
    recommendations for improving suggestions.
    """
    company_id = parse_company_id(get_user_company_id(current_user))
    
    coverage = await service.get_data_coverage(db, company_id)
    
    return DataCoverageResponse(**coverage)
