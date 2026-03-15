"""
Communications API Endpoints

Handles communication history for candidates - emails, WhatsApp, screening invites, etc.
Also provides direct email and WhatsApp sending via SendGrid and Twilio integrations.
"""

from fastapi import APIRouter, HTTPException, Query, status, Header, Depends
from typing import Optional, Dict, Any, List
import logging

from app.services.communication_history_service import communication_history_service


from app.schemas.communication import (
    CommunicationCreate,
    CommunicationResponse,
    CommunicationListResponse,
    CommunicationStatusUpdate,
)
from app.services.email_service import (
    sendgrid_email_service,
    SendEmailRequest,
    SendTemplateEmailRequest,
    SendBulkEmailRequest,
    BulkEmailRecipient,
    EmailSendResult,
    BulkEmailResult,
)
from app.services.whatsapp_service import (
    whatsapp_service,
    SendWhatsAppRequest,
    SendWhatsAppTemplateRequest,
    SendInteractiveRequest,
    InteractiveButton,
    WhatsAppSendResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/communications", tags=["communications"])
candidate_communications_router = APIRouter(prefix="/candidates", tags=["candidates"])


def require_company_id(x_company_id: Optional[str] = Header(None, alias="X-Company-ID")) -> str:
    """Dependency to require and validate X-Company-ID header for multi-tenant security."""
    if not x_company_id:
        raise HTTPException(
            status_code=403,
            detail="Company ID required. Please provide X-Company-ID header."
        )
    return x_company_id


@router.post("", response_model=CommunicationResponse, status_code=status.HTTP_201_CREATED)
async def create_communication(data: CommunicationCreate):
    """
    Log a new communication.
    
    Creates a new communication history record for tracking emails,
    WhatsApp messages, screening invites, and other candidate communications.
    """
    try:
        communication = await communication_history_service.log_communication(
            candidate_id=data.candidate_id,
            candidate_name=data.candidate_name,
            candidate_email=data.candidate_email,
            candidate_phone=data.candidate_phone,
            vacancy_id=data.vacancy_id,
            vacancy_title=data.vacancy_title,
            communication_type=data.communication_type,
            channel=data.channel,
            direction=data.direction,
            subject=data.subject,
            message_content=data.message_content,
            template_id=data.template_id,
            template_name=data.template_name,
            attachments=data.attachments,
            sent_by=data.sent_by,
            sent_by_name=data.sent_by_name,
            company_id=data.company_id,
            extra_data=data.extra_data,
        )
        
        logger.info(f"✅ Created communication {communication.id} for candidate {data.candidate_name}")
        
        return communication.to_dict()
        
    except Exception as e:
        logger.error(f"❌ Error creating communication: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create communication: {str(e)}"
        )


@router.get("", response_model=CommunicationListResponse)
async def list_communications(
    company_id: str = Query(..., description="Company ID (required)"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    communication_type: Optional[str] = Query(None, description="Filter by type: email, whatsapp, triagem_invite, etc."),
    channel: Optional[str] = Query(None, description="Filter by channel: email, whatsapp"),
    status: Optional[str] = Query(None, description="Filter by status: pending, sent, delivered, read, failed"),
    limit: int = Query(50, ge=1, le=200, description="Max results (default: 50, max: 200)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List communications with optional filters.
    
    Returns paginated list of communications for a company.
    """
    try:
        result = await communication_history_service.list_communications(
            company_id=company_id,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            communication_type=communication_type,
            channel=channel,
            status=status,
            limit=limit,
            offset=offset,
        )
        
        logger.info(f"📋 Listed {len(result['communications'])} communications (total: {result['total']})")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error listing communications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list communications: {str(e)}"
        )


@router.get("/history", response_model=CommunicationListResponse)
async def get_communication_history(
    company_id: str = Query(..., description="Company ID (required)"),
    candidate_id: Optional[str] = Query(None, description="Filter by candidate ID"),
    vacancy_id: Optional[str] = Query(None, description="Filter by vacancy ID"),
    channel: Optional[str] = Query(None, description="Filter by channel: email, whatsapp"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: pending, sent, delivered, read, failed"),
    limit: int = Query(50, ge=1, le=200, description="Max results (default: 50, max: 200)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Get communication history with optional filters.
    
    Returns paginated list of communications for a company.
    This is an alias for the list_communications endpoint with a cleaner URL.
    """
    try:
        result = await communication_history_service.list_communications(
            company_id=company_id,
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            channel=channel,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
        
        logger.info(f"📋 History: {len(result['communications'])} communications (total: {result['total']})")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting communication history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get communication history: {str(e)}"
        )


@router.get("/{communication_id}", response_model=CommunicationResponse)
async def get_communication(communication_id: str):
    """
    Get a single communication by ID.
    
    Returns full communication details or 404 if not found.
    """
    try:
        communication = await communication_history_service.get_communication_by_id(communication_id)
        
        if not communication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Communication not found: {communication_id}"
            )
        
        logger.info(f"📋 Retrieved communication: {communication.id}")
        
        return communication.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting communication: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get communication: {str(e)}"
        )


@router.put("/{communication_id}/status", response_model=CommunicationResponse)
async def update_communication_status(
    communication_id: str,
    data: CommunicationStatusUpdate
):
    """
    Update communication status.
    
    Updates the status and sets appropriate timestamp.
    Valid statuses: sent, delivered, read, failed
    """
    try:
        valid_statuses = ["pending", "sent", "delivered", "read", "failed"]
        if data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        communication = await communication_history_service.update_communication_status(
            communication_id=communication_id,
            new_status=data.status,
            error_message=data.error_message,
        )
        
        if not communication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Communication not found: {communication_id}"
            )
        
        logger.info(f"✅ Updated communication {communication_id} status to: {data.status}")
        
        return communication.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating communication status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update communication status: {str(e)}"
        )


@candidate_communications_router.get("/{candidate_id}/communications", response_model=CommunicationListResponse)
async def get_candidate_communications(
    candidate_id: str,
    company_id: str = Query(..., description="Company ID (required)"),
    limit: int = Query(100, ge=1, le=500, description="Max results (default: 100, max: 500)"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Get all communications for a specific candidate.
    
    Returns paginated list of all communications for the candidate.
    """
    try:
        result = await communication_history_service.get_candidate_communications(
            candidate_id=candidate_id,
            company_id=company_id,
            limit=limit,
            offset=offset,
        )
        
        logger.info(f"📋 Retrieved {len(result['communications'])} communications for candidate {candidate_id}")
        
        return {
            "communications": result["communications"],
            "total": result["total"],
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting candidate communications: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get candidate communications: {str(e)}"
        )


@router.post("/email/send", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def send_email(
    request: SendEmailRequest,
    company_id: str = Depends(require_company_id)
):
    """
    Send an email via SendGrid.
    
    Requires X-Company-ID header for multi-tenant security.
    
    In development mode, logs the email without sending.
    In production mode, sends via SendGrid API.
    
    Request body:
    - to_email: Recipient email address (required)
    - to_name: Recipient name (optional)
    - subject: Email subject (required)
    - body: Plain text body (required)
    - body_html: HTML body (optional)
    - cc: List of CC emails (optional)
    - bcc: List of BCC emails (optional)
    - reply_to: Reply-to address (optional)
    - categories: SendGrid categories for tracking (optional)
    - metadata: Custom metadata (optional)
    
    Returns:
    - success: Whether the email was sent successfully
    - message_id: SendGrid message ID (if successful)
    - status: Email status (sent, failed)
    - provider: Email provider used
    - error: Error message (if failed)
    """
    try:
        metadata = request.metadata or {}
        metadata["company_id"] = company_id
        
        result = await sendgrid_email_service.send_email(
            to_email=request.to_email,
            to_name=request.to_name,
            subject=request.subject,
            body=request.body,
            body_html=request.body_html,
            cc=request.cc,
            bcc=request.bcc,
            reply_to=request.reply_to,
            categories=request.categories,
            metadata=metadata,
        )
        
        if result.success:
            logger.info(f"✅ Email sent to {request.to_email} for company {company_id}, ID: {result.message_id}")
        else:
            logger.warning(f"⚠️ Email to {request.to_email} failed: {result.error}")
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"❌ Error sending email: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/email/send-template", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def send_template_email(
    request: SendTemplateEmailRequest,
    company_id: str = Depends(require_company_id)
):
    """
    Send an email using a predefined template.
    
    Requires X-Company-ID header for multi-tenant security.
    
    Uses templates from EmailTemplates (communication_templates.py).
    
    Request body:
    - to_email: Recipient email (required)
    - to_name: Recipient name (optional)
    - template_name: Template name (required)
    - template_data: Template variables dictionary (required)
    - cc: CC recipients (optional)
    - reply_to: Reply-to address (optional)
    - categories: SendGrid categories (optional)
    - metadata: Custom metadata (optional)
    """
    try:
        metadata = request.metadata or {}
        metadata["company_id"] = company_id
        
        result = await sendgrid_email_service.send_template_email(
            to_email=request.to_email,
            to_name=request.to_name,
            template_name=request.template_name,
            template_data=request.template_data,
            cc=request.cc,
            reply_to=request.reply_to,
            categories=request.categories,
            metadata=metadata,
        )
        
        if result.success:
            logger.info(f"✅ Template email '{request.template_name}' sent to {request.to_email} for company {company_id}")
        else:
            logger.warning(f"⚠️ Template email failed: {result.error}")
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"❌ Error sending template email: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send template email: {str(e)}"
        )


@router.post("/email/send-bulk", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def send_bulk_email(
    request: SendBulkEmailRequest,
    company_id: str = Depends(require_company_id)
):
    """
    Send bulk emails to multiple recipients.
    
    Requires X-Company-ID header for multi-tenant security.
    
    Supports per-recipient personalization using {{variable}} placeholders.
    
    Request body:
    - recipients: List of recipients with email, name, and personalization data
    - subject: Email subject (required)
    - body: Plain text body (required)
    - body_html: HTML body (optional)
    - categories: SendGrid categories (optional)
    - metadata: Custom metadata (optional)
    """
    try:
        metadata = request.metadata or {}
        metadata["company_id"] = company_id
        
        result = await sendgrid_email_service.send_bulk_email(
            recipients=request.recipients,
            subject=request.subject,
            body=request.body,
            body_html=request.body_html,
            categories=request.categories,
            metadata=metadata,
        )
        
        logger.info(f"📧 Bulk email for company {company_id}: {result.successful}/{result.total} sent successfully")
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"❌ Error sending bulk email: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send bulk email: {str(e)}"
        )


@router.post("/whatsapp/send", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def send_whatsapp(
    request: SendWhatsAppRequest,
    company_id: str = Depends(require_company_id)
):
    """
    Send a WhatsApp message via Twilio.
    
    Requires X-Company-ID header for multi-tenant security.
    
    In development mode, logs the message without sending.
    In production mode, sends via Twilio WhatsApp API.
    
    Request body:
    - to_phone: Recipient phone number with country code (required)
    - message: Message text (required)
    - media_url: URL of media to attach (optional)
    - metadata: Custom metadata (optional)
    - candidate_id: Candidate ID for tracking (optional)
    
    Returns:
    - success: Whether the message was sent
    - message_id: Twilio message SID (if successful)
    - status: Message status (sent, delivered, read, failed)
    - provider: Provider used (twilio or development)
    - error: Error message (if failed)
    """
    try:
        metadata = request.metadata or {}
        metadata["company_id"] = company_id
        
        result = await whatsapp_service.send_message(
            to_phone=request.to_phone,
            message=request.message,
            media_url=request.media_url,
            metadata=metadata,
        )
        
        if result.success:
            logger.info(f"✅ WhatsApp sent to {request.to_phone} for company {company_id}, ID: {result.message_id}")
        else:
            logger.warning(f"⚠️ WhatsApp to {request.to_phone} failed: {result.error}")
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send WhatsApp message: {str(e)}"
        )


@router.post("/whatsapp/send-template", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def send_whatsapp_template(
    request: SendWhatsAppTemplateRequest,
    company_id: str = Depends(require_company_id)
):
    """
    Send a WhatsApp message using a predefined template.
    
    Requires X-Company-ID header for multi-tenant security.
    
    Uses templates from WhatsAppTemplates (communication_templates.py).
    
    Request body:
    - to_phone: Recipient phone (required)
    - template_name: Template name (required)
    - template_data: Template variables dictionary (required)
    - media_url: Media URL to attach (optional)
    - metadata: Custom metadata (optional)
    - candidate_id: Candidate ID (optional)
    """
    try:
        metadata = request.metadata or {}
        metadata["company_id"] = company_id
        
        result = await whatsapp_service.send_template(
            to_phone=request.to_phone,
            template_name=request.template_name,
            template_data=request.template_data,
            media_url=request.media_url,
            metadata=metadata,
        )
        
        if result.success:
            logger.info(f"✅ WhatsApp template '{request.template_name}' sent to {request.to_phone} for company {company_id}")
        else:
            logger.warning(f"⚠️ WhatsApp template failed: {result.error}")
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"❌ Error sending WhatsApp template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send WhatsApp template: {str(e)}"
        )


@router.post("/whatsapp/send-interactive", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def send_whatsapp_interactive(
    request: SendInteractiveRequest,
    company_id: str = Depends(require_company_id)
):
    """
    Send an interactive WhatsApp message with buttons.
    
    Requires X-Company-ID header for multi-tenant security.
    
    Interactive messages allow recipients to respond by clicking buttons.
    Maximum 3 buttons allowed.
    
    Request body:
    - to_phone: Recipient phone (required)
    - body: Main message body (required)
    - buttons: List of buttons with id and title (required, max 3)
    - header: Message header (optional)
    - footer: Message footer (optional)
    - metadata: Custom metadata (optional)
    - candidate_id: Candidate ID (optional)
    """
    try:
        metadata = request.metadata or {}
        metadata["company_id"] = company_id
        
        result = await whatsapp_service.send_interactive(
            to_phone=request.to_phone,
            body=request.body,
            buttons=request.buttons,
            header=request.header,
            footer=request.footer,
            metadata=metadata,
        )
        
        if result.success:
            logger.info(f"✅ Interactive WhatsApp sent to {request.to_phone} for company {company_id}")
        else:
            logger.warning(f"⚠️ Interactive WhatsApp failed: {result.error}")
        
        return result.model_dump()
        
    except Exception as e:
        logger.error(f"❌ Error sending interactive WhatsApp: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send interactive WhatsApp: {str(e)}"
        )


from pydantic import BaseModel

class TransferCommunicationsRequest(BaseModel):
    """Request model for transferring communications between recruiters."""
    job_ids: List[str]
    from_recruiter_ids: List[str]
    to_recruiter_id: str


@router.post("/transfer")
async def transfer_communications(
    request: TransferCommunicationsRequest,
    company_id: str = Depends(require_company_id)
):
    """
    Transfer pending communications from previous recruiters to a new recruiter.
    
    This is used when reassigning jobs to update ownership of:
    - Pending email drafts
    - Scheduled messages
    - Communication threads
    """
    try:
        transferred_count = 0
        
        for job_id in request.job_ids:
            result = await communication_history_service.transfer_communications_ownership(
                job_id=job_id,
                from_user_ids=request.from_recruiter_ids,
                to_user_id=request.to_recruiter_id,
                company_id=company_id
            )
            transferred_count += result.get("transferred", 0)
        
        logger.info(f"Transferred {transferred_count} communications for {len(request.job_ids)} jobs")
        
        return {
            "success": True,
            "transferred_count": transferred_count,
            "message": f"{transferred_count} comunicação(ões) transferida(s)"
        }
    except Exception as e:
        logger.error(f"Error transferring communications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao transferir comunicações: {str(e)}"
        )
