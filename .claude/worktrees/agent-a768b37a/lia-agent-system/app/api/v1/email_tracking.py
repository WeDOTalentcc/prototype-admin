"""
Email Tracking endpoints — COMP-7.

GET  /api/v1/email-tracking/pixel/{token}.gif  — pixel 1x1 (open tracking)
GET  /api/v1/email-tracking/click/{token}      — redirect com click tracking
GET  /api/v1/email-tracking/stats/{notification_id} — stats agregadas

LGPD disclosure obrigatória nos emails:
"Este email contém pixels de rastreamento para medir abertura. Veja nossa Política de Privacidade."
"""
import logging
from fastapi import APIRouter, Request, Depends, Path, Query
from fastapi.responses import Response, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db as get_async_db

router = APIRouter(prefix="/email-tracking", tags=["Email Tracking"])

logger = logging.getLogger(__name__)

# 1x1 GIF transparente (binary, base64-decoded)
_TRANSPARENT_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0x21,
    0xf9, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2c, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3b
])


@router.get("/pixel/{token}.gif", include_in_schema=False)
async def tracking_pixel(
    request: Request,
    token: str = Path(...),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Pixel de rastreamento 1x1 GIF.

    Registra abertura do email. Retorna GIF transparente.
    IP é armazenado apenas como SHA256 hash (LGPD-safe).
    """
    from app.services.email_tracking_service import email_tracking_service

    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")

    try:
        await email_tracking_service.record_open(
            db=db,
            token=token,
            ip=ip,
            user_agent=user_agent,
        )
    except Exception as e:
        logger.debug("[EmailTracking] pixel error (non-blocking): %s", e)

    return Response(
        content=_TRANSPARENT_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/click/{token}")
async def tracking_click(
    request: Request,
    token: str = Path(...),
    url: str = Query(..., description="URL de destino (encoded)"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Link redirect com tracking de clique.

    Registra clique e redireciona para URL de destino.
    """
    from app.services.email_tracking_service import email_tracking_service

    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")

    # Validação básica de URL (evitar open redirect para domínios externos maliciosos)
    # Aceita apenas http/https
    if not url.startswith(("http://", "https://")):
        url = "https://app.wedotalent.com"  # fallback seguro

    try:
        redirect_url = await email_tracking_service.record_click(
            db=db,
            token=token,
            link_url=url,
            ip=ip,
            user_agent=user_agent,
        )
        return RedirectResponse(url=redirect_url or url, status_code=302)
    except Exception as e:
        logger.debug("[EmailTracking] click error (non-blocking): %s", e)
        return RedirectResponse(url=url, status_code=302)


@router.get("/stats/{notification_id}")
async def get_tracking_stats(
    notification_id: str = Path(...),
    company_id: str = Query(..., description="ID da empresa (multi-tenant)"),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Estatísticas de tracking para uma notificação.

    Retorna opens, clicks, unique_opens.
    Dados agregados — sem PII individual (LGPD-safe).
    """
    from app.services.email_tracking_service import email_tracking_service

    stats = await email_tracking_service.get_stats(
        db=db,
        notification_id=notification_id,
        company_id=company_id,
    )
    return stats
