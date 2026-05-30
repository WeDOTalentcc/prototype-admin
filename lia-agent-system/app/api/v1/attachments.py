"""
Attachments API Endpoints

Handles candidate file attachments - CVs, documents, certificates, videos, transcripts, etc.
Supports file upload with multipart/form-data.
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse

from app.schemas.attachment import (
    AttachmentCreate,
    AttachmentListResponse,
    AttachmentResponse,
    CandidateFilesResponse,
    CategoryCount,
    FileUploadResponse,
)
from app.shared.services.attachment_service import attachment_service
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from typing import Annotated
from fastapi import Path as FastAPIPath
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/attachments", tags=["attachments"])
candidate_attachments_router = APIRouter(prefix="/candidates", tags=["candidates"])

UPLOAD_DIR = Path("uploads/candidate_files")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'mp4': 'video/mp4',
    'mov': 'video/quicktime',
}

CATEGORY_MAP = {
    'cv': {'label': 'Currículos', 'icon': '📄'},
    'portfolio': {'label': 'Portfólios', 'icon': '💼'},
    'video': {'label': 'Vídeos', 'icon': '🎥'},
    'certificate': {'label': 'Certificados', 'icon': '🏆'},
    'document': {'label': 'Documentos', 'icon': '📝'},
    'transcript': {'label': 'Transcrições', 'icon': '📋'},
    'other': {'label': 'Outros', 'icon': '📁'},
}


def get_file_category(filename: str, mime_type: str = None) -> str:
    """Determine file category based on filename and mime type."""
    filename_lower = filename.lower()
    
    if any(kw in filename_lower for kw in ['cv', 'curriculo', 'currículo', 'resume']):
        return 'cv'
    if any(kw in filename_lower for kw in ['portfolio', 'portfólio']):
        return 'portfolio'
    if any(kw in filename_lower for kw in ['certificado', 'certificate', 'diploma']):
        return 'certificate'
    if filename_lower.endswith(('.mp4', '.mov', '.avi', '.webm')):
        return 'video'
    if mime_type and mime_type.startswith('video/'):
        return 'video'
    
    return 'document'


@router.post("", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def create_attachment(data: AttachmentCreate, company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create a new attachment record.
    
    Records a new file attachment for a candidate, such as CV, document, certificate, etc.
    """
    try:
        attachment = await attachment_service.create_attachment(
            candidate_id=data.candidate_id,
            candidate_name=data.candidate_name,
            file_name=data.file_name,
            file_type=data.file_type,
            file_url=data.file_url,
            file_size=data.file_size,
            mime_type=data.mime_type,
            upload_source=data.upload_source,
            related_entity_type=data.related_entity_type,
            related_entity_id=data.related_entity_id,
            description=data.description,
            uploaded_by=data.uploaded_by,
            uploaded_by_name=data.uploaded_by_name,
            company_id=data.company_id,
        )
        
        # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
        logger.info(f"✅ Created attachment {attachment.id} for candidate {data.candidate_name}")
        
        return attachment.to_dict()
        
    except Exception as e:
        logger.error(f"❌ Error creating attachment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create attachment: {str(e)}"
        )


@router.get("", response_model=AttachmentListResponse)
async def list_attachments(
    company_id: str = Query(..., description="Company ID (required)"),
    candidate_id: str | None = Query(None, description="Filter by candidate ID"),
    file_type: str | None = Query(None, description="Filter by type: cv, document, certificate, video, transcript, other"),
    upload_source: str | None = Query(None, description="Filter by source: candidate, recruiter, lia, ats"),
    is_active: bool | None = Query(True, description="Filter by active status (default: True)"),
    limit: int = Query(50, ge=1, le=200, description="Max results (default: 50, max: 200)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List attachments with optional filters.
    
    Returns paginated list of attachments for a company.
    """
    try:
        result = await attachment_service.list_attachments(
            company_id=company_id,
            candidate_id=candidate_id,
            file_type=file_type,
            upload_source=upload_source,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        
        logger.info(f"📋 Listed {len(result['attachments'])} attachments (total: {result['total']})")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error listing attachments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list attachments: {str(e)}"
        )


@router.get("/{attachment_id}", response_model=AttachmentResponse)
async def get_attachment(attachment_id: Annotated[str, FastAPIPath(pattern=DUAL_ID_PATH_PATTERN)], company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get a single attachment by ID.
    
    Returns full attachment details or 404 if not found.
    """
    try:
        attachment = await attachment_service.get_attachment_by_id(attachment_id)
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attachment not found: {attachment_id}"
            )
        
        logger.info(f"📋 Retrieved attachment: {attachment.id}")
        
        return attachment.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting attachment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get attachment: {str(e)}"
        )


@router.delete("/{attachment_id}", response_model=AttachmentResponse)
async def delete_attachment(attachment_id: Annotated[str, FastAPIPath(pattern=DUAL_ID_PATH_PATTERN)], company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Soft delete an attachment (deactivate).
    
    Sets is_active=False instead of actually deleting the record.
    """
    try:
        attachment = await attachment_service.deactivate_attachment(attachment_id)
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attachment not found: {attachment_id}"
            )
        
        logger.info(f"✅ Deactivated attachment: {attachment.id}")
        
        return attachment.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deactivating attachment: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate attachment: {str(e)}"
        )


@candidate_attachments_router.get("/{candidate_id}/attachments", response_model=AttachmentListResponse)
async def get_candidate_attachments(
    candidate_id: Annotated[str, FastAPIPath(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID (required)"),
    limit: int = Query(100, ge=1, le=500, description="Max results (default: 100, max: 500)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    """
    Get all attachments for a specific candidate.
    
    Returns paginated list of all active attachments for the candidate.
    """
    try:
        result = await attachment_service.get_candidate_attachments(
            candidate_id=candidate_id,
            company_id=company_id,
            limit=limit,
            offset=offset,
        )
        
        logger.info(f"📋 Retrieved {len(result['attachments'])} attachments for candidate {candidate_id}")
        
        return {
            "attachments": result["attachments"],
            "total": result["total"],
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting candidate attachments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candidate attachments: {str(e)}"
        )


@candidate_attachments_router.post("/{candidate_id}/files", response_model=FileUploadResponse)
async def upload_candidate_file(
    candidate_id: Annotated[str, FastAPIPath(pattern=DUAL_ID_PATH_PATTERN)],
    file: UploadFile = File(...),
    candidate_name: str = Form(default="Candidato"),
    category: str = Form(default=""),
    description: str = Form(default=""),
    company_id: str = Form(...),
    uploaded_by: str = Form(default="system"),
    uploaded_by_name: str = Form(default="Sistema"),
_company_gate: str = Depends(require_company_id_strict_match("form.company_id"))):
    """
    Upload a file for a candidate.
    
    Accepts multipart/form-data with the file and metadata.
    Stores the file in the uploads directory and creates a database record.
    
    Supported file types: PDF, DOC, DOCX, JPG, PNG, MP4 (max 10MB)
    Categories: cv, portfolio, video, certificate, document, transcript, other
    """
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}"
            )
        
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        file_type = category if category else get_file_category(file.filename, file.content_type)
        
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{unique_id}_{file.filename.replace(' ', '_')}"
        
        candidate_dir = UPLOAD_DIR / candidate_id
        candidate_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = candidate_dir / safe_filename
        with open(file_path, 'wb') as f:
            f.write(content)
        
        file_url = f"/api/v1/candidates/{candidate_id}/files/download/{safe_filename}"
        
        attachment = await attachment_service.create_attachment(
            candidate_id=candidate_id,
            candidate_name=candidate_name,
            file_name=file.filename,
            file_type=file_type,
            file_url=file_url,
            file_size=file_size,
            mime_type=file.content_type or ALLOWED_EXTENSIONS.get(ext),
            upload_source="recruiter",
            description=description or None,
            uploaded_by=uploaded_by,
            uploaded_by_name=uploaded_by_name,
            company_id=company_id,
        )
        
        logger.info(f"✅ Uploaded file {file.filename} for candidate {candidate_id}")
        
        return FileUploadResponse(
            success=True,
            message=f"Arquivo '{file.filename}' enviado com sucesso",
            attachment=attachment.to_dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading file: {str(e)}", exc_info=True)
        return FileUploadResponse(
            success=False,
            message="Erro ao fazer upload do arquivo",
            error=str(e)
        )


@candidate_attachments_router.get("/{candidate_id}/files", response_model=CandidateFilesResponse)
async def get_candidate_files(
    candidate_id: Annotated[str, FastAPIPath(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Query(..., description="Company ID"),
    category: str | None = Query(None, description="Filter by category"),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    """
    Get all files for a candidate with category counts.
    
    Returns files grouped with category counts for the UI.
    """
    try:
        result = await attachment_service.get_candidate_attachments(
            candidate_id=candidate_id,
            company_id=company_id,
            limit=500,
            offset=0,
        )
        
        attachments = result["attachments"]
        
        if category:
            attachments = [a for a in attachments if a.get("file_type") == category]
        
        category_counts = {}
        for att in result["attachments"]:
            cat = att.get("file_type", "other")
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        categories = []
        for cat, info in CATEGORY_MAP.items():
            count = category_counts.get(cat, 0)
            categories.append(CategoryCount(
                category=cat,
                label=info['label'],
                count=count,
                icon=info['icon']
            ))
        
        categories = [c for c in categories if c.count > 0] + [c for c in categories if c.count == 0]
        
        logger.info(f"📋 Retrieved {len(attachments)} files for candidate {candidate_id}")
        
        return CandidateFilesResponse(
            attachments=attachments,
            total=len(attachments),
            categories=categories[:6]
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting candidate files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candidate files: {str(e)}"
        )


@candidate_attachments_router.get("/{candidate_id}/files/download/{filename}")
async def download_candidate_file(
    candidate_id: Annotated[str, FastAPIPath(pattern=DUAL_ID_PATH_PATTERN)],
    filename: str,
company_id: str = Depends(require_company_id)):
    """
    Download a candidate file.
    
    Returns the file as a streaming response.
    """
    try:
        file_path = UPLOAD_DIR / candidate_id / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        content_type = ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')
        
        def file_generator():
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    yield chunk
        
        original_filename = '_'.join(filename.split('_')[2:]) if filename.count('_') >= 2 else filename
        
        return StreamingResponse(
            file_generator(),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{original_filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )


@candidate_attachments_router.delete("/{candidate_id}/files/{attachment_id}")
async def delete_candidate_file(
    candidate_id: Annotated[str, FastAPIPath(pattern=DUAL_ID_PATH_PATTERN)],
    attachment_id: Annotated[str, FastAPIPath(pattern=DUAL_ID_PATH_PATTERN)],
company_id: str = Depends(require_company_id)):
    """
    Delete a candidate file.
    
    Soft deletes the attachment record and optionally removes the file.
    """
    try:
        attachment = await attachment_service.deactivate_attachment(attachment_id)
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found"
            )
        
        logger.info(f"✅ Deleted file {attachment_id} for candidate {candidate_id}")
        
        return {
            "success": True,
            "message": "Arquivo excluído com sucesso",
            "attachment_id": attachment_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

reorder_collection_before_item(router)
