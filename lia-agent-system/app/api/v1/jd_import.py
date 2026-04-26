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


@router.post("/import/upload-file", response_model=dict[str, Any])
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_strict),
    service: JDImportService = Depends(get_jd_import_service),
) -> dict[str, Any]:
    """
    Importa uma Job Description a partir de upload de arquivo (P3-2).

    Suporta: .txt, .md, .pdf (extrai texto via pypdf se disponível), .docx (extrai via python-docx).
    O texto extraído é passado para JDImportService.import_jd() para parse estruturado.

    Privacidade & auditoria (Task #838):
    - Autenticação estrita: o modo demo está desabilitado (M-09).
    - Consentimento granular explícito uma vez por empresa, com bypass em
      sessões subsequentes a partir do registro imutável (M-01).
    - Cada upload grava `user_id`, `company_id`, `filename_hash`, `size_bytes`,
      `uuid` e `timestamp` em `audit_logs` (M-10).

    Returns:
        JD importada e parseada com campos extraídos (título, skills, requisitos, benefícios).
    """
    # Identidade do solicitante — necessária para consent + audit antes do parse
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

    # Validar tipo de arquivo
    allowed_extensions = {".txt", ".md", ".pdf", ".docx"}
    filename = file.filename or ""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não suportado: '{ext}'. Use: {', '.join(sorted(allowed_extensions))}",
        )

    # Validar tamanho (máx 5MB)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Máximo: 5MB")

    # Extrair texto conforme tipo
    raw_text: str = ""
    if ext in {".txt", ".md"}:
        raw_text = content.decode("utf-8", errors="replace")
    elif ext == ".pdf":
        try:
            import io

            import pypdf  # type: ignore[import]
            reader = pypdf.PdfReader(io.BytesIO(content))
            raw_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            # pypdf não instalado — retorna texto vazio com aviso
            raise HTTPException(
                status_code=422,
                detail="Parse de PDF não disponível neste ambiente. Use .txt ou .docx.",
            )
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Erro ao ler PDF: {exc}")
    elif ext == ".docx":
        try:
            import io

            import docx  # type: ignore[import]
            doc = docx.Document(io.BytesIO(content))
            raw_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except ImportError:
            raise HTTPException(
                status_code=422,
                detail="Parse de DOCX não disponível neste ambiente. Use .txt.",
            )
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Erro ao ler DOCX: {exc}")

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Arquivo vazio ou sem texto extraível.")

    # LGPD: minimizar PII antes de processar (CPF, email, telefone, endereço)
    try:
        from app.shared.pii_masking import strip_pii_for_llm_prompt
        raw_text = strip_pii_for_llm_prompt(raw_text)
    except Exception:
        pass  # fail-safe: prosseguir sem stripping se módulo indisponível

    # FairnessGuard: detectar linguagem discriminatória no JD antes de importar
    fairness_warnings: list[str] = []
    try:
        from app.shared.compliance.fairness_guard import FairnessGuard
        _fg = FairnessGuard()
        _result = _fg.check(raw_text[:2000])  # checar amostra inicial
        if _result.is_blocked:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Job description contém linguagem discriminatória e não pode ser importada. "
                    f"{_result.educational_message or 'Revise o conteúdo e remova critérios protegidos.'}"
                ),
            )
        if _result.soft_warnings:
            fairness_warnings = _result.soft_warnings
            logger.warning(
                "[jd-import/upload] FairnessGuard soft_warnings company=%s filename_hash=%s: %s",
                company_id, _hash_filename(filename), _result.soft_warnings,
            )
    except HTTPException:
        raise
    except Exception:
        pass  # fail-safe

    # Importar via JDImportService
    jd_data = {
        "title": title or filename.rsplit(".", 1)[0],
        "description": raw_text,
        "source_file": filename,
    }

    imported = await service.import_jd(
        db=db,
        company_id=company_id,
        jd_data=jd_data,
        source="file_upload",
        parse_immediately=True,
    )

    # M-10: Auditoria imutável em `audit_logs` (substitui logger.info anterior)
    upload_uuid = str(_uuid_mod.uuid4())
    filename_hash = _hash_filename(filename)
    await _record_jd_upload_audit(
        company_id=company_id,
        user_id=user_id,
        upload_uuid=upload_uuid,
        filename_hash=filename_hash,
        size_bytes=len(content),
        extension=ext,
        fairness_warnings_count=len(fairness_warnings),
    )

    # M-01: registrar consentimento granular em primeira concessão (idempotente
    # para a empresa). Posteriores uploads detectam o registro e não pedem de novo.
    if consent_acknowledged:
        try:
            already = await _company_has_jd_upload_consent(company_id)
            if not already:
                await _record_jd_upload_consent(company_id, user_id)
        except Exception as exc:
            logger.warning("[jd-import/upload] failed to persist consent: %s", exc)

    result = {
        **imported.to_dict(),
        "source_filename": filename,
        "audit": {
            "uuid": upload_uuid,
            "filename_hash": filename_hash,
            "size_bytes": len(content),
        },
    }
    if fairness_warnings:
        result["fairness_warnings"] = fairness_warnings
    return result


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
