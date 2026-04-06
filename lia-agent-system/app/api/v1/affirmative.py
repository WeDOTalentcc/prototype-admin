"""
API endpoints for affirmative action management.
"""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.database import get_db
from app.services.affirmative_service import AffirmativeService

router = APIRouter(prefix="/affirmative", tags=["affirmative"])


class EligibilityCheckRequest(BaseModel):
    candidate_id: str
    vacancy_id: str


class DocumentUploadRequest(BaseModel):
    document_id: str
    document_url: str
    original_filename: str
    document_type: str


class DocumentVerificationRequest(BaseModel):
    document_id: str
    approved: bool
    notes: str | None = None


@router.get("/criteria", response_model=None)
async def get_affirmative_criteria():
    """Get all available affirmative action criteria."""
    from app.services.affirmative_service import AFFIRMATIVE_CRITERIA
    return {"criteria": AFFIRMATIVE_CRITERIA}


@router.post("/check-eligibility", response_model=None)
async def check_eligibility(
    request: EligibilityCheckRequest,
    db: Session = Depends(get_db)
):
    """Check if candidate is eligible for affirmative vacancy."""
    AffirmativeService(db)
    return {"status": "pending", "message": "Eligibility check requires candidate and vacancy data"}


@router.get("/pending-documents/{company_id}", response_model=None)
async def get_pending_documents(
    company_id: str,
    vacancy_id: str | None = None,
    db: Session = Depends(get_db)
):
    """Get all pending document uploads for a company."""
    service = AffirmativeService(db)
    vacancy_uuid = UUID(vacancy_id) if vacancy_id else None
    documents = service.get_pending_documents(company_id, vacancy_uuid)
    return {"documents": documents, "count": len(documents)}


@router.post("/documents/request", response_model=None)
async def request_document(
    candidate_id: str,
    vacancy_id: str,
    company_id: str,
    criteria_type: str,
    db: Session = Depends(get_db)
):
    """Create a document upload request with 24h deadline."""
    service = AffirmativeService(db)
    document = service.create_document_request(
        candidate_id=UUID(candidate_id),
        vacancy_id=UUID(vacancy_id),
        company_id=company_id,
        criteria_type=criteria_type
    )
    return {"document_id": str(document.id), "deadline": document.upload_deadline.isoformat()}


@router.post("/documents/verify-lia", response_model=None)
async def verify_document_lia(
    document_id: str,
    verification_result: dict,
    db: Session = Depends(get_db)
):
    """LIA automated verification of document."""
    service = AffirmativeService(db)
    document = service.verify_document_lia(UUID(document_id), verification_result)
    return {"status": document.status, "verified": document.verified_by_lia}


@router.post("/documents/verify-recruiter", response_model=None)
async def verify_document_recruiter(
    request: DocumentVerificationRequest,
    recruiter_email: str,
    db: Session = Depends(get_db)
):
    """Recruiter manual verification of document."""
    service = AffirmativeService(db)
    document = service.verify_document_recruiter(
        document_id=UUID(request.document_id),
        recruiter_email=recruiter_email,
        approved=request.approved,
        notes=request.notes
    )
    return {"status": document.status, "approved": request.approved}


@router.post("/check-expired/{company_id}", response_model=None)
async def check_expired_documents(
    company_id: str,
    db: Session = Depends(get_db)
):
    """Check and mark expired documents."""
    service = AffirmativeService(db)
    count = service.check_expired_documents(company_id)
    return {"expired_count": count}
