"""
API endpoints for affirmative action management.
"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.shared.services.affirmative_service import (
    AffirmativeService,
    AffirmativeConsentRequiredError,
)
from lia_models.candidate import Candidate
from lia_models.job_vacancy import JobVacancy
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/affirmative", tags=["affirmative"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CriteriaResponse(BaseModel):
    criteria: list[dict[str, Any]]


class EligibilityResponse(BaseModel):
    status: str
    message: str
    eligible: bool | None = None
    requires_document: bool | None = None
    document_types: list[str] | None = None


class PendingDocumentsResponse(BaseModel):
    documents: list[dict[str, Any]]
    count: int


class DocumentRequestResponse(BaseModel):
    document_id: str
    deadline: str


class DocumentVerifyLiaResponse(BaseModel):
    status: str
    verified: bool


class DocumentVerifyRecruiterResponse(BaseModel):
    status: str
    approved: bool


class ExpiredDocumentsResponse(BaseModel):
    expired_count: int


class EligibilityCheckRequest(WeDoBaseModel):
    candidate_id: str
    vacancy_id: str


class DocumentUploadRequest(WeDoBaseModel):
    document_id: str
    document_url: str
    original_filename: str
    document_type: str


class DocumentVerificationRequest(WeDoBaseModel):
    document_id: str
    approved: bool
    notes: str | None = None


@router.get("/criteria", response_model=CriteriaResponse)
async def get_affirmative_criteria(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all available affirmative action criteria."""
    # SMOKE-#6 fix (audit 2026-05-20): AFFIRMATIVE_CRITERIA é dict[str, dict] (gender, race, ...),
    # mas CriteriaResponse declara list[dict[str, Any]]. Pydantic 2 rejeita o tipo errado.
    # Compliance LGPD/Lei 12.711 ADP — catálogo precisa funcionar pra transparência (Art. 9º).
    from app.shared.services.affirmative_service import AFFIRMATIVE_CRITERIA
    criteria_list = [{"key": k, **v} for k, v in AFFIRMATIVE_CRITERIA.items()]
    return {"criteria": criteria_list}


@router.post("/check-eligibility", response_model=EligibilityResponse)
async def check_eligibility(
    request: EligibilityCheckRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Check if candidate is eligible for affirmative vacancy."""
    service = AffirmativeService(db)
    candidate = (await db.execute(
        select(Candidate).where(Candidate.id == UUID(request.candidate_id), Candidate.company_id == company_id)
    )).scalar_one_or_none()
    vacancy = (await db.execute(
        select(JobVacancy).where(JobVacancy.id == UUID(request.vacancy_id), JobVacancy.company_id == company_id)
    )).scalar_one_or_none()
    if candidate is None or vacancy is None:
        raise HTTPException(404, "Candidato ou vaga nao encontrados para esta empresa")
    result = service.check_candidate_eligibility(candidate, vacancy)
    return {
        "status": "eligible" if result.get("eligible") else "not_eligible",
        "message": result.get("reason", "Elegibilidade avaliada"),
        "eligible": result.get("eligible"),
        "requires_document": result.get("requires_document"),
        "document_types": result.get("document_types"),
    }


@router.get("/pending-documents/{company_id}", response_model=PendingDocumentsResponse)
async def get_pending_documents(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    vacancy_id: str | None = None,
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get all pending document uploads for a company."""
    service = AffirmativeService(db)
    vacancy_uuid = UUID(vacancy_id) if vacancy_id else None
    documents = await service.get_pending_documents(company_id, vacancy_uuid)
    return {"documents": documents, "count": len(documents)}


@router.post("/documents/request", response_model=DocumentRequestResponse)
async def request_document(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    criteria_type: str,
    db: AsyncSession = Depends(get_tenant_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Create a document upload request with 24h deadline."""
    service = AffirmativeService(db)
    document = await service.create_document_request(
        candidate_id=UUID(candidate_id),
        vacancy_id=UUID(vacancy_id),
        company_id=company_id,
        criteria_type=criteria_type
    )
    return {"document_id": str(document.id), "deadline": document.upload_deadline.isoformat()}


@router.post("/documents/verify-lia", response_model=DocumentVerifyLiaResponse)
async def verify_document_lia(
    document_id: str,
    verification_result: dict,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """LIA automated verification of document."""
    service = AffirmativeService(db)
    document = await service.verify_document_lia(UUID(document_id), verification_result)
    return {"status": document.status, "verified": document.verified_by_lia}


@router.post("/documents/verify-recruiter", response_model=DocumentVerifyRecruiterResponse)
async def verify_document_recruiter(
    request: DocumentVerificationRequest,
    recruiter_email: str,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Recruiter manual verification of document."""
    service = AffirmativeService(db)
    document = await service.verify_document_recruiter(
        document_id=UUID(request.document_id),
        recruiter_email=recruiter_email,
        approved=request.approved,
        notes=request.notes
    )
    return {"status": document.status, "approved": request.approved}


@router.post("/check-expired/{company_id}", response_model=ExpiredDocumentsResponse)
async def check_expired_documents(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Check and mark expired documents."""
    service = AffirmativeService(db)
    count = await service.check_expired_documents(company_id)
    return {"expired_count": count}

@router.post("/documents/{document_id}/upload", response_model=DocumentVerifyLiaResponse)
async def upload_affirmative_document(
    document_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Upload multipart do documento afirmativo. Grava em disco e chama o service
    (que valida consent LGPD + prazo). Path-traversal mitigado: document_id e UUID-gated
    e o filename e sanitizado."""
    from pathlib import Path as _P
    safe_name = (file.filename or "documento").replace("/", "_").replace("\\", "_").replace("..", "_")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "Arquivo excede 10MB")
    upload_dir = _P("uploads/affirmative") / str(document_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    with open(upload_dir / safe_name, "wb") as fh:
        fh.write(content)
    url = f"/api/v1/affirmative/documents/download/{document_id}/{safe_name}"
    service = AffirmativeService(db)
    try:
        document = await service.upload_document(UUID(document_id), url, file.filename or safe_name, document_type)
    except AffirmativeConsentRequiredError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"status": document.status, "verified": document.verified_by_lia}


@router.get("/documents/download/{document_id}/{filename}")
async def download_affirmative_document(
    document_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    filename: str,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
):
    """Download do documento sensível — RBAC: so o tenant dono pode baixar."""
    from pathlib import Path as _P
    from lia_models.affirmative_audit import CandidateAffirmativeDocument
    doc = (await db.execute(
        select(CandidateAffirmativeDocument).where(CandidateAffirmativeDocument.id == UUID(document_id))
    )).scalar_one_or_none()
    if doc is None or doc.company_id != company_id:
        raise HTTPException(404, "Documento nao encontrado")
    safe_name = filename.replace("/", "_").replace("..", "_")
    path = _P("uploads/affirmative") / str(document_id) / safe_name
    if not path.exists():
        raise HTTPException(404, "Arquivo nao encontrado")
    return FileResponse(str(path))


reorder_collection_before_item(router)
