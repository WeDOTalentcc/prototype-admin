"""
Candidate Portal Public API

Public endpoints for candidates to access and fill data requests.
NO JWT authentication required - uses unique token + OTP verification.

Security:
- Unique token validation per request
- OTP verification (6 digits, 10 min expiry, max 3 attempts)
- Rate limiting for OTP requests
- Input sanitization
"""
import logging
import os
import re
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.candidate import Candidate
from app.models.data_request import (
    DataFieldType,
    DataRequest,
    DataRequestConfig,
    DataRequestStatus,
)
from app.models.data_request import (
    DataRequestResponse as DataRequestResponseModel,
)
from app.models.job_vacancy import JobVacancy
from app.shared.types import WeDoBaseModel
from lia_models.observability import ConsentRecord

# RAILS-DEPRECATED: This endpoint manages Rails-owned entities (candidates/jobs/applies/users).
# Direct DB calls will be replaced by RailsAdapter after ats-api-rails handoff.
# See: app/domains/integrations_hub/services/rails_adapter.py

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portal/data-request", tags=["Candidate Portal"])

UPLOAD_DIR = "uploads/candidate_files"
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "application/pdf": [".pdf"],
}

OTP_RATE_LIMIT_SECONDS = 60


class PortalDataRequestResponse(BaseModel):
    """Response for portal data request info."""
    id: str
    status: str
    expires_at: datetime
    is_expired: bool
    otp_verified: bool
    otp_required: bool
    fields: list[dict[str, Any]]
    fields_completed: list[dict[str, Any]]
    completion_percentage: float
    branding: dict[str, Any]
    candidate_info: dict[str, Any]
    vacancy_info: dict[str, Any] | None = None


class CandidatePortalOTPRequest(WeDoBaseModel):
    """Request to send a new OTP."""
    channel: str = Field(default="email", pattern="^(email|whatsapp)$")


class RequestOTPResponse(BaseModel):
    """Response for OTP request."""
    success: bool
    message: str
    channel: str
    expires_in_minutes: int = 10


class CandidatePortalOTPVerify(WeDoBaseModel):
    """Request to verify OTP code."""
    code: str = Field(..., min_length=6, max_length=6, pattern="^[0-9]{6}$")


class VerifyOTPResponse(BaseModel):
    """Response for OTP verification."""
    verified: bool
    message: str
    attempts_remaining: int | None = None


class FieldSubmission(BaseModel):
    """A single field submission."""
    name: str
    value: str | None = None
    
    @validator('name')
    def sanitize_name(cls, v):
        return re.sub(r'[^\w\-]', '', v)


class SubmitDataRequest(WeDoBaseModel):
    """Request to submit data."""
    fields: list[FieldSubmission]
    is_final: bool = False
    # Phase 3a: consent_id required when template has sensitive fields (LGPD Art. 11)
    consent_id: str | None = None


class SubmitDataResponse(BaseModel):
    """Response for data submission."""
    success: bool
    status: str
    fields_saved: int
    fields_with_errors: list[dict[str, Any]]
    completion_percentage: float
    message: str


class FileUploadResponse(BaseModel):
    """Response for file upload."""
    success: bool
    field_name: str
    file_name: str
    file_url: str
    file_size_bytes: int
    message: str


async def get_data_request_by_token(
    token: str,
    db: AsyncSession,
    require_otp: bool = True,
) -> DataRequest:
    """
    Validate token and return data request.
    
    Args:
        token: Unique access token
        db: Database session
        require_otp: Whether to require OTP verification
        
    Returns:
        DataRequest if valid
        
    Raises:
        HTTPException if token invalid, expired, or OTP not verified
    """
    result = await db.execute(
        select(DataRequest).where(DataRequest.token == token)
    )
    data_request = result.scalar_one_or_none()
    
    if not data_request:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    if data_request.status == DataRequestStatus.CANCELLED:
        raise HTTPException(status_code=410, detail="Solicitação cancelada")
    
    if data_request.is_expired():
        data_request.status = DataRequestStatus.EXPIRED
        raise HTTPException(status_code=410, detail="Solicitação expirada")
    
    if require_otp and not data_request.otp_verified:
        config = await get_company_config(db, data_request.company_id)
        if config and config.require_otp:
            raise HTTPException(
                status_code=403, 
                detail="Verificação OTP necessária"
            )
    
    return data_request


async def get_company_config(
    db: AsyncSession,
    company_id: UUID,
) -> DataRequestConfig | None:
    """Get company configuration for data requests."""
    result = await db.execute(
        select(DataRequestConfig).where(DataRequestConfig.company_id == company_id)
    )
    return result.scalar_one_or_none()


def validate_field_value(
    field_type: str,
    value: str,
    validation_rules: dict[str, Any] | None = None,
) -> tuple[bool, str | None]:
    """
    Validate a field value based on its type.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        return True, None
    
    try:
        if field_type == DataFieldType.CPF.value:
            cpf = re.sub(r'\D', '', value)
            if len(cpf) != 11:
                return False, "CPF deve ter 11 dígitos"
            if cpf == cpf[0] * 11:
                return False, "CPF inválido"
            
        elif field_type == DataFieldType.CNPJ.value:
            cnpj = re.sub(r'\D', '', value)
            if len(cnpj) != 14:
                return False, "CNPJ deve ter 14 dígitos"
            
        elif field_type == DataFieldType.EMAIL.value:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                return False, "E-mail inválido"
            
        elif field_type == DataFieldType.PHONE.value:
            phone = re.sub(r'\D', '', value)
            if len(phone) < 10 or len(phone) > 11:
                return False, "Telefone deve ter 10 ou 11 dígitos"
            
        elif field_type == DataFieldType.DATE.value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return False, "Data inválida (formato: YYYY-MM-DD)"
            
        elif field_type == DataFieldType.NUMBER.value:
            try:
                float(value)
            except ValueError:
                return False, "Valor numérico inválido"
            
        elif field_type == DataFieldType.CURRENCY.value:
            currency_pattern = r'^[\d.,]+$'
            clean_value = re.sub(r'[R$\s]', '', value)
            if not re.match(currency_pattern, clean_value):
                return False, "Valor monetário inválido"
        
        if validation_rules:
            if 'pattern' in validation_rules:
                if not re.match(validation_rules['pattern'], value):
                    return False, validation_rules.get('pattern_error', 'Formato inválido')
            
            if 'min_length' in validation_rules:
                if len(value) < validation_rules['min_length']:
                    return False, f"Mínimo de {validation_rules['min_length']} caracteres"
            
            if 'max_length' in validation_rules:
                if len(value) > validation_rules['max_length']:
                    return False, f"Máximo de {validation_rules['max_length']} caracteres"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False, "Erro na validação"


def sanitize_input(value: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks."""
    if not value:
        return value
    
    value = re.sub(r'<[^>]*>', '', value)
    value = value.replace('\x00', '')
    
    return value.strip()


@router.get("/{token}", response_model=PortalDataRequestResponse)
async def get_data_request_info(
    token: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get data request information including fields to fill and company branding.
    
    This endpoint does NOT require OTP verification - it's used to display
    the initial portal page before OTP is verified.
    """
    data_request = await get_data_request_by_token(token, db, require_otp=False)
    
    now = datetime.utcnow()
    if not data_request.first_accessed_at:
        data_request.first_accessed_at = now
    data_request.last_accessed_at = now
    
    config = await get_company_config(db, data_request.company_id)
    
    candidate = await db.get(Candidate, data_request.candidate_id)
    candidate_info = {
        "name": candidate.name if candidate else "Candidato",
        "email": candidate.email if candidate else None,
        "email_masked": mask_email(candidate.email) if candidate and candidate.email else None,
    }
    
    vacancy_info = None
    if data_request.vacancy_id:
        vacancy = await db.get(JobVacancy, data_request.vacancy_id)
        if vacancy:
            vacancy_info = {
                "title": vacancy.title,
                "department": vacancy.department,
            }
    
    branding = {
        "logo_url": config.portal_logo_url if config else None,
        "primary_color": config.portal_primary_color if config else "#000000",
        "welcome_message": config.portal_welcome_message if config else None,
        "thank_you_message": config.portal_thank_you_message if config else None,
        "privacy_policy_url": config.privacy_policy_url if config else None,
        "terms_url": config.terms_url if config else None,
    }
    
    otp_required = config.require_otp if config else True
    
    return PortalDataRequestResponse(
        id=str(data_request.id),
        status=data_request.status.value,
        expires_at=data_request.expires_at,
        is_expired=data_request.is_expired(),
        otp_verified=data_request.otp_verified,
        otp_required=otp_required,
        fields=data_request.fields_requested or [],
        fields_completed=data_request.fields_completed or [],
        completion_percentage=data_request.get_completion_percentage(),
        branding=branding,
        candidate_info=candidate_info,
        vacancy_info=vacancy_info,
    )


@router.post("/{token}/request-otp", response_model=RequestOTPResponse)
async def request_otp(
    token: str,
    request_data: CandidatePortalOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a new OTP code sent via email or WhatsApp.
    
    Rate limited to 1 request per minute.
    OTP expires in 10 minutes.
    """
    data_request = await get_data_request_by_token(token, db, require_otp=False)
    
    if data_request.otp_verified:
        return RequestOTPResponse(
            success=True,
            message="OTP já verificado anteriormente",
            channel=request_data.channel,
            expires_in_minutes=0,
        )
    
    now = datetime.utcnow()
    if data_request.otp_expires_at:
        time_since_last = (now - data_request.otp_expires_at).total_seconds() + 600
        if time_since_last < OTP_RATE_LIMIT_SECONDS:
            wait_time = int(OTP_RATE_LIMIT_SECONDS - time_since_last)
            raise HTTPException(
                status_code=429,
                detail=f"Aguarde {wait_time} segundos para solicitar novo código"
            )
    
    config = await get_company_config(db, data_request.company_id)
    otp_expiration_minutes = config.otp_expiration_minutes if config else 10
    
    otp_code = DataRequest.generate_otp()
    data_request.otp_code = otp_code
    data_request.otp_expires_at = now + timedelta(minutes=otp_expiration_minutes)
    data_request.otp_attempts = 0
    
    
    candidate = await db.get(Candidate, data_request.candidate_id)
    
    if request_data.channel == "email" and candidate and candidate.email:
        try:
            logger.info(f"Sending OTP to candidate_id={candidate.id} via email for data request {data_request.id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to send OTP email: {e}")
            raise HTTPException(status_code=500, detail="Erro ao enviar código por e-mail")
    
    elif request_data.channel == "whatsapp" and candidate and candidate.phone:
        try:
            logger.info(f"Sending OTP to candidate_id={candidate.id} via WhatsApp for data request {data_request.id}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to send OTP WhatsApp: {e}")
            raise HTTPException(status_code=500, detail="Erro ao enviar código por WhatsApp")
    
    return RequestOTPResponse(
        success=True,
        message=f"Código enviado via {request_data.channel}",
        channel=request_data.channel,
        expires_in_minutes=otp_expiration_minutes,
    )


@router.post("/{token}/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(
    token: str,
    request_data: CandidatePortalOTPVerify,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify OTP code.
    
    Maximum 3 attempts. After 3 failed attempts, request a new code.
    """
    data_request = await get_data_request_by_token(token, db, require_otp=False)
    
    if data_request.otp_verified:
        return VerifyOTPResponse(
            verified=True,
            message="OTP já verificado anteriormente",
        )
    
    config = await get_company_config(db, data_request.company_id)
    max_attempts = config.max_otp_attempts if config else 3
    
    if data_request.otp_attempts >= max_attempts:
        raise HTTPException(
            status_code=429,
            detail="Número máximo de tentativas excedido. Solicite um novo código."
        )
    
    now = datetime.utcnow()
    if not data_request.otp_code or not data_request.otp_expires_at:
        raise HTTPException(
            status_code=400,
            detail="Nenhum código OTP foi solicitado. Solicite um novo código."
        )
    
    if now > data_request.otp_expires_at:
        raise HTTPException(
            status_code=400,
            detail="Código OTP expirado. Solicite um novo código."
        )
    
    data_request.otp_attempts = (data_request.otp_attempts or 0) + 1
    
    if not secrets.compare_digest(request_data.code, data_request.otp_code):
        attempts_remaining = max_attempts - data_request.otp_attempts
        
        if attempts_remaining <= 0:
            return VerifyOTPResponse(
                verified=False,
                message="Código incorreto. Número máximo de tentativas excedido.",
                attempts_remaining=0,
            )
        
        return VerifyOTPResponse(
            verified=False,
            message="Código incorreto. Tente novamente.",
            attempts_remaining=attempts_remaining,
        )
    
    data_request.otp_verified = True
    data_request.otp_code = None
    
    logger.info(f"OTP verified for data request {data_request.id}")
    
    return VerifyOTPResponse(
        verified=True,
        message="Código verificado com sucesso!",
    )


@router.post("/{token}/submit", response_model=SubmitDataResponse)
async def submit_data(
    token: str,
    request_data: SubmitDataRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit data for the request.
    
    Can be partial (save progress) or final (complete).
    Validates fields based on their type.
    """
    data_request = await get_data_request_by_token(token, db, require_otp=True)
    
    if data_request.status == DataRequestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Solicitação já foi concluída")

    # --- Phase 3a: sensitive-field consent gate (LGPD Art. 11) ---
    _fields_req_preview = {f.get("name") for f in (data_request.fields_requested or [])}
    _sensitive_in_template = any(n in SENSITIVE_DATA_REQUEST_FIELDS for n in _fields_req_preview)
    if request_data.is_final and _sensitive_in_template:
        if not request_data.consent_id:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "consent_required",
                    "message": "Campos sensiveis requerem consentimento explicito (Art. 11 LGPD)",
                },
            )
        import uuid as _uuid_gate
        try:
            _cid = _uuid_gate.UUID(request_data.consent_id)
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=422,
                detail={"error": "consent_invalid", "message": "consent_id invalido"},
            )
        # Use db.get (PK lookup) — simpler than a query, testable without SA column expressions
        _cr = await db.get(ConsentRecord, _cid)
        if (
            _cr is None
            or not _cr.is_active
            or str(_cr.candidate_id) != str(data_request.candidate_id)
        ):
            raise HTTPException(
                status_code=422,
                detail={"error": "consent_invalid", "message": "consent_id nao encontrado ou nao pertence ao candidato"},
            )
    # --- end consent gate ---

    fields_requested = {f.get('name'): f for f in (data_request.fields_requested or [])}
    fields_completed = {f.get('name'): f for f in (data_request.fields_completed or [])}
    
    fields_saved = 0
    fields_with_errors = []
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:500]
    
    for field_submission in request_data.fields:
        field_name = sanitize_input(field_submission.name)
        field_value = sanitize_input(field_submission.value) if field_submission.value else None
        
        if field_name not in fields_requested:
            fields_with_errors.append({
                "name": field_name,
                "error": "Campo não solicitado",
            })
            continue
        
        field_config = fields_requested[field_name]
        field_type = field_config.get('field_type', 'text')
        validation_rules = field_config.get('validation_rules')
        
        if field_type in [DataFieldType.FILE.value, DataFieldType.PHOTO.value]:
            continue
        
        is_valid, error_message = validate_field_value(field_type, field_value, validation_rules)
        
        if not is_valid:
            fields_with_errors.append({
                "name": field_name,
                "error": error_message,
            })
            continue
        
        existing_response = await db.execute(
            select(DataRequestResponseModel).where(
                DataRequestResponseModel.data_request_id == data_request.id,
                DataRequestResponseModel.field_name == field_name,
            )
        )
        response = existing_response.scalar_one_or_none()
        
        if response:
            response.value = field_value
            response.is_valid = True
            response.validation_errors = []
            response.updated_at = datetime.utcnow()
            response.ip_address = client_ip
            response.user_agent = user_agent
        else:
            response = DataRequestResponseModel(
                data_request_id=data_request.id,
                field_name=field_name,
                field_type=field_type,
                value=field_value,
                is_valid=True,
                validation_errors=[],
                ip_address=client_ip,
                user_agent=user_agent,
            )
            db.add(response)
        
        fields_completed[field_name] = {
            "name": field_name,
            "value": field_value,
            "submitted_at": datetime.utcnow().isoformat(),
        }
        fields_saved += 1
    
    data_request.fields_completed = list(fields_completed.values())
    
    completion_percentage = data_request.get_completion_percentage()
    
    if request_data.is_final and completion_percentage >= 100:
        data_request.status = DataRequestStatus.COMPLETED
        data_request.completed_at = datetime.utcnow()
        message = "Dados enviados com sucesso! Obrigado por preencher."
        
        logger.info(f"Data request {data_request.id} completed")
    elif completion_percentage > 0:
        data_request.status = DataRequestStatus.PARTIALLY_FILLED
        message = "Progresso salvo com sucesso."
    else:
        message = "Nenhum campo foi salvo."
    
    
    return SubmitDataResponse(
        success=len(fields_with_errors) == 0,
        status=data_request.status.value,
        fields_saved=fields_saved,
        fields_with_errors=fields_with_errors,
        completion_percentage=completion_percentage,
        message=message,
    )


@router.post("/{token}/upload", response_model=FileUploadResponse)
async def upload_file(
    token: str,
    field_name: str = Form(...),
    file: UploadFile = File(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a file/document for a specific field.
    
    Validates file type and size.
    """
    data_request = await get_data_request_by_token(token, db, require_otp=True)
    
    if data_request.status == DataRequestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Solicitação já foi concluída")
    
    field_name = sanitize_input(field_name)
    fields_requested = {f.get('name'): f for f in (data_request.fields_requested or [])}
    
    if field_name not in fields_requested:
        raise HTTPException(status_code=400, detail="Campo não encontrado")
    
    field_config = fields_requested[field_name]
    field_type = field_config.get('field_type')
    
    if field_type not in [DataFieldType.FILE.value, DataFieldType.PHOTO.value]:
        raise HTTPException(status_code=400, detail="Este campo não aceita upload de arquivos")
    
    max_size_mb = field_config.get('max_file_size_mb', MAX_FILE_SIZE_MB)
    allowed_types = field_config.get('allowed_file_types', list(ALLOWED_FILE_TYPES.keys()))
    
    content_type = file.content_type
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de arquivo não permitido. Tipos aceitos: {', '.join(allowed_types)}"
        )
    
    file_content = await file.read()
    file_size = len(file_content)
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Arquivo muito grande. Tamanho máximo: {max_size_mb}MB"
        )
    
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".bin"
    safe_filename = f"{data_request.id}_{field_name}_{secrets.token_hex(8)}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, 'wb') as f:
        f.write(file_content)
    
    file_url = f"/{file_path}"
    
    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent", "")[:500] if request else ""
    
    existing_response = await db.execute(
        select(DataRequestResponseModel).where(
            DataRequestResponseModel.data_request_id == data_request.id,
            DataRequestResponseModel.field_name == field_name,
        )
    )
    response = existing_response.scalar_one_or_none()
    
    if response:
        if response.file_url:
            old_file_path = response.file_url.lstrip('/')
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove old file: {e}")
        
        response.file_url = file_url
        response.file_name = file.filename
        response.file_size_bytes = file_size
        response.file_mime_type = content_type
        response.is_valid = True
        response.updated_at = datetime.utcnow()
        response.ip_address = client_ip
        response.user_agent = user_agent
    else:
        response = DataRequestResponseModel(
            data_request_id=data_request.id,
            field_name=field_name,
            field_type=field_type,
            file_url=file_url,
            file_name=file.filename,
            file_size_bytes=file_size,
            file_mime_type=content_type,
            is_valid=True,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        db.add(response)
    
    fields_completed = {f.get('name'): f for f in (data_request.fields_completed or [])}
    fields_completed[field_name] = {
        "name": field_name,
        "file_url": file_url,
        "file_name": file.filename,
        "submitted_at": datetime.utcnow().isoformat(),
    }
    data_request.fields_completed = list(fields_completed.values())
    
    if data_request.status == DataRequestStatus.PENDING:
        data_request.status = DataRequestStatus.PARTIALLY_FILLED
    
    
    # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
    logger.info(f"File uploaded for data request {data_request.id}, field {field_name}")
    
    return FileUploadResponse(
        success=True,
        field_name=field_name,
        file_name=file.filename,
        file_url=file_url,
        file_size_bytes=file_size,
        message="Arquivo enviado com sucesso!",
    )


def mask_email(email: str) -> str:
    """Mask email for privacy (e.g., j***@gmail.com)."""
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 1:
        return f"{local[0]}***@{domain}"
    return f"{local[0]}{'*' * (len(local) - 1)}@{domain}"


# ---------------------------------------------------------------------------
# Phase 3a — LGPD Art. 11 consent gate for sensitive fields
# ---------------------------------------------------------------------------

# Campos sensiveis que requerem consentimento explicito (LGPD Art. 11)
SENSITIVE_DATA_REQUEST_FIELDS: frozenset[str] = frozenset({
    "disability_info",
    "pcd_type",
    "pcd_document",
    "gender",
    "race_ethnicity",
    "racial_autodeclaration",
})

CONSENT_VERSAO_DISCLAIMER = "1.0"


class DataRequestConsentRequest(WeDoBaseModel):
    """Request to record explicit consent before submitting sensitive fields (LGPD Art. 11)."""
    canal: str = Field(default="web", pattern=r"^(web|whatsapp|chamada_online|chamada_telefonica)$")
    versao_disclaimer: str = Field(default=CONSENT_VERSAO_DISCLAIMER, max_length=10)


class DataRequestConsentResponse(BaseModel):
    """Response confirming consent was recorded."""
    ok: bool
    consent_id: str


@router.post("/{token}/consent", response_model=DataRequestConsentResponse)
async def record_data_request_consent(
    token: str,
    request_data: DataRequestConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Record explicit candidate consent (LGPD Art. 11) before submitting
    sensitive fields (disability, gender, race/ethnicity).

    Must be called BEFORE the final submit when the template contains
    any field in SENSITIVE_DATA_REQUEST_FIELDS.

    Returns consent_id to be included in the subsequent submit call.
    """
    import uuid as _uuid_mod

    data_request = await get_data_request_by_token(token, db, require_otp=True)

    if data_request.status == DataRequestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Solicitacao ja foi concluida")

    try:
        candidate_id_uuid = _uuid_mod.UUID(str(data_request.candidate_id))
        company_id_uuid = _uuid_mod.UUID(str(data_request.company_id))
    except (ValueError, AttributeError) as exc:
        logger.error(
            "[DataRequestConsent] ID conversion error for data_request %s: %s",
            data_request.id, exc, exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Erro interno ao registrar consentimento")

    vaga_id = None
    if data_request.vacancy_id:
        try:
            vaga_id = _uuid_mod.UUID(str(data_request.vacancy_id))
        except (ValueError, AttributeError):
            pass

    now = datetime.utcnow()
    client_ip = request.client.host if request.client else None
    user_agent_str = request.headers.get("user-agent", "")[:500]

    sensitive_names = ", ".join(sorted(SENSITIVE_DATA_REQUEST_FIELDS))
    consent_text = (
        "Candidato consentiu explicitamente com a coleta de dados sensiveis "
        "(Art. 11, paragrafo 2, II LGPD) via portal de coleta de dados WeDOTalent. "
        f"Campos sensiveis: {sensitive_names}. "
        f"Solicitacao de dados ID: {data_request.id}."
    )

    try:
        consent_record = ConsentRecord(
            id=_uuid_mod.uuid4(),
            company_id=company_id_uuid,
            candidate_id=candidate_id_uuid,
            consent_type="dados_coletados_solicitacao",
            version=request_data.versao_disclaimer,
            canal=request_data.canal,
            vaga_id=vaga_id,
            processo_id=None,
            granted_at=now,
            is_active=True,
            legal_basis="Art. 11, paragrafo 2, II - LGPD",
            consent_text=consent_text,
            versao_disclaimer=request_data.versao_disclaimer,
            source="data_request_portal",
            ip_address=client_ip,
            user_agent=user_agent_str,
        )
        db.add(consent_record)
        await db.flush()
        await db.commit()
    except Exception as exc:
        logger.error(
            "[DataRequestConsent] DB error creating ConsentRecord for data_request %s: %s",
            data_request.id, exc, exc_info=True,
        )
        await db.rollback()
        raise HTTPException(status_code=500, detail="Erro ao registrar consentimento") from exc

    logger.info(
        "[DataRequestConsent] ConsentRecord %s created for data_request %s (canal=%s)",
        consent_record.id, data_request.id, request_data.canal,
    )

    return DataRequestConsentResponse(ok=True, consent_id=str(consent_record.id))
