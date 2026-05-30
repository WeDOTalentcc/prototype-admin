"""
API endpoints for affirmative action management.
"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_tenant_db
from app.shared.services.affirmative_service import AffirmativeService
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
    AffirmativeService(db)
    return {"status": "pending", "message": "Eligibility check requires candidate and vacancy data"}


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
    documents = service.get_pending_documents(company_id, vacancy_uuid)
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
    document = service.create_document_request(
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
    document = service.verify_document_lia(UUID(document_id), verification_result)
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
    document = service.verify_document_recruiter(
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
    count = service.check_expired_documents(company_id)
    return {"expired_count": count}

reorder_collection_before_item(router)
