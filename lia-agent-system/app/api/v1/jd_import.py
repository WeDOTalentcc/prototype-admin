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
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo, get_user_company_id
from app.auth.models import User
from app.core.database import get_db
from app.domains.job_management.services.jd_import_service import JDImportService, get_jd_import_service


# Local factory — uses module-local JDImportService (supports test mocking)
def get_jd_import_service():  # type: ignore[override]  # noqa: F811
    """DI factory for JDImportService — creates new instance using module-local class."""
    return JDImportService()

from app.domains.job_management.services.wizard_data_priority_service import JobContext, WizardDataPriorityService, get_wizard_data_priority_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

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


class BatchImportRequest(WeDoBaseModel):
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


# DUPLICATE_OF_INTENT: app/api/v1/wizard_suggestions.py — wizard suggestion wire-format reused for JD import (Sprint Q.1 triagem I bucket)
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
company_id: str = Depends(require_company_id)):
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
company_id: str = Depends(require_company_id)):
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
company_id: str = Depends(require_company_id)):
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
company_id: str = Depends(require_company_id)):
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
company_id: str = Depends(require_company_id)):
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
company_id: str = Depends(require_company_id)):
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


@router.post("/import/upload-file", response_model=dict[str, Any])
async def upload_jd_file(
    file: UploadFile = File(..., description="Arquivo JD (.txt, .pdf, .docx, .md)"),
    title: str = Query("", description="Título da vaga (opcional, extraído do arquivo se vazio)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    service: JDImportService = Depends(get_jd_import_service),
company_id: str = Depends(require_company_id)) -> dict[str, Any]:
    """
    Importa uma Job Description a partir de upload de arquivo (P3-2).

    Suporta: .txt, .md, .pdf (extrai texto via pypdf se disponível), .docx (extrai via python-docx).
    O texto extraído é passado para JDImportService.import_jd() para parse estruturado.

    Returns:
        JD importada e parseada com campos extraídos (título, skills, requisitos, benefícios).
    """
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
                "[jd-import/upload] FairnessGuard soft_warnings company=%s file=%s: %s",
                get_user_company_id(current_user), filename, _result.soft_warnings,
            )
    except HTTPException:
        raise
    except Exception:
        pass  # fail-safe

    # Importar via JDImportService
    company_id = parse_company_id(get_user_company_id(current_user))

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

    # Audit log estruturado (LGPD/SOX rastreabilidade)
    logger.info(
        "[jd-import/upload] imported company=%s file=%s size_bytes=%d title=%s fairness_warnings=%d",
        company_id,
        filename,
        len(content),
        jd_data["title"],
        len(fairness_warnings),
    )

    result = {**imported.to_dict(), "source_filename": filename}
    if fairness_warnings:
        result["fairness_warnings"] = fairness_warnings
    return result


@router.get("/data-coverage", response_model=DataCoverageResponse)
async def get_data_coverage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    service: WizardDataPriorityService = Depends(get_wizard_data_priority_service),
company_id: str = Depends(require_company_id)):
    """
    Get data coverage statistics.
    
    Shows which data sources have data and provides
    recommendations for improving suggestions.
    """
    company_id = parse_company_id(get_user_company_id(current_user))
    
    coverage = await service.get_data_coverage(db, company_id)
    
    return DataCoverageResponse(**coverage)
