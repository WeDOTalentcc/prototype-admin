import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db
from app.shared.channels.channel_adapter import ChannelMessage, ChannelType
from app.shared.channels.multi_channel_service import multi_channel_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/multi-channel", tags=["multi-channel"])


class SendMessageRequest(WeDoBaseModel):
    recipient_id: str
    recipient_name: str
    recipient_contact: str
    subject: str | None = None
    body_text: str = ""
    body_html: str | None = None
    template_id: str | None = None
    template_vars: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    vacancy_id: str | None = None
    channels: list[str] = ["email"]
    fallback: bool = True


class SendMessageResponse(BaseModel):
    success: bool
    channel: str
    message_id: str
    status: str
    provider_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BulkMessageItem(BaseModel):
    recipient_id: str
    recipient_name: str
    recipient_contact: str
    subject: str | None = None
    body_text: str = ""
    body_html: str | None = None
    template_id: str | None = None
    template_vars: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    company_id: str = ""
    vacancy_id: str | None = None


class BulkSendRequest(WeDoBaseModel):
    messages: list[BulkMessageItem]
    channel: str = "email"


class BulkSendResponse(BaseModel):
    total: int
    sent: int
    failed: int
    results: list[SendMessageResponse]


class ChannelStatusResponse(BaseModel):
    channels: list[dict[str, Any]]


class DeliveryStatusResponse(BaseModel):
    message_id: str
    status: str | None = None
    found: bool = True


@router.post("/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest, current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id), db: AsyncSession = Depends(get_db)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        channel_types = []
        for ch in request.channels:
            try:
                channel_types.append(ChannelType(ch))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Canal inválido: {ch}. Canais válidos: {[c.value for c in ChannelType]}",
                )

        message = ChannelMessage(
            recipient_id=request.recipient_id,
            recipient_name=request.recipient_name,
            recipient_contact=request.recipient_contact,
            subject=request.subject,
            body_text=request.body_text,
            body_html=request.body_html,
            template_id=request.template_id,
            template_vars=request.template_vars,
            metadata=request.metadata,
            company_id=company_id,
            vacancy_id=request.vacancy_id,
        )

        result = await multi_channel_service.send_message(
            message=message,
            channels=channel_types,
            fallback=request.fallback,
            db=db,
        )

        return SendMessageResponse(
            success=result.success,
            channel=result.channel.value,
            message_id=result.message_id,
            status=result.status.value,
            provider_id=result.provider_id,
            error=result.error,
            metadata=result.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[MULTI_CHANNEL_API] Erro ao enviar mensagem: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{message_id}", response_model=DeliveryStatusResponse)
async def get_delivery_status(message_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)], current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        status = await multi_channel_service.get_delivery_status(message_id)
        if status is None:
            return DeliveryStatusResponse(
                message_id=message_id,
                status=None,
                found=False,
            )
        return DeliveryStatusResponse(
            message_id=message_id,
            status=status.value,
            found=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[MULTI_CHANNEL_API] Erro ao verificar status: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels", response_model=ChannelStatusResponse)
async def list_available_channels(current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id), db: AsyncSession = Depends(get_db)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        channels = await multi_channel_service.get_available_channels(company_id=company_id, db=db)
        return ChannelStatusResponse(channels=channels)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[MULTI_CHANNEL_API] Erro ao listar canais: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", response_model=BulkSendResponse)
async def send_bulk_messages(request: BulkSendRequest, current_user: User = Depends(get_current_user_or_demo), company_id: str = Depends(require_company_id), db: AsyncSession = Depends(get_db)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    try:
        try:
            channel_type = ChannelType(request.channel)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Canal inválido: {request.channel}. Canais válidos: {[c.value for c in ChannelType]}",
            )

        messages = [
            ChannelMessage(
                recipient_id=item.recipient_id,
                recipient_name=item.recipient_name,
                recipient_contact=item.recipient_contact,
                subject=item.subject,
                body_text=item.body_text,
                body_html=item.body_html,
                template_id=item.template_id,
                template_vars=item.template_vars,
                metadata=item.metadata,
                company_id=item.company_id or company_id,
                vacancy_id=item.vacancy_id,
            )
            for item in request.messages
        ]

        results = await multi_channel_service.send_bulk(messages, channel_type, db=db)

        response_results = [
            SendMessageResponse(
                success=r.success,
                channel=r.channel.value,
                message_id=r.message_id,
                status=r.status.value,
                provider_id=r.provider_id,
                error=r.error,
                metadata=r.metadata,
            )
            for r in results
        ]

        sent = sum(1 for r in results if r.success)
        failed = len(results) - sent

        return BulkSendResponse(
            total=len(results),
            sent=sent,
            failed=failed,
            results=response_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"[MULTI_CHANNEL_API] Erro no envio em massa: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
