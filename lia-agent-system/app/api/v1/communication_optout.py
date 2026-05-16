import base64
import hashlib
import hmac
import html
import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.communication.repositories.optout_repository import OptoutRepository
from app.shared.security.require_company_id import require_company_id


# TODO(phase2): extract to repository — communication opt-out
def _get_consent_event_model():
    from app.domains.analytics.models.observability import ConsentEvent
    return ConsentEvent


_HMAC_SECRET = os.environ.get("UNSUBSCRIBE_HMAC_SECRET", "")
if not _HMAC_SECRET:
    import secrets as _secrets
    _HMAC_SECRET = _secrets.token_hex(32)
    logging.getLogger(__name__).warning(
        "UNSUBSCRIBE_HMAC_SECRET not set — generated ephemeral key. "
        "Set this env var for persistent unsubscribe tokens across restarts."
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/communication', tags=['communication-optout'])


def generate_signed_token(email: str, company_id: str) -> str:
    payload = f"{email}:{company_id}"
    sig = hmac.new(_HMAC_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    raw = f"{payload}:{sig}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify_signed_token(token: str):
    try:
        decoded = base64.urlsafe_b64decode(token).decode("utf-8")
        parts = decoded.rsplit(":", 1)
        if len(parts) != 2:
            return None, None
        payload, sig = parts
        expected = hmac.new(_HMAC_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected):
            return None, None
        email_company = payload.split(":", 1)
        if len(email_company) != 2 or not email_company[0] or not email_company[1]:
            return None, None
        return email_company[0], email_company[1]
    except Exception:
        return None, None

UNSUBSCRIBE_PAGE_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cancelar Inscrição - Plataforma LIA / WeDOTalent</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
        .container {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.08); max-width: 480px; width: 90%; padding: 40px; text-align: center; }}
        .logo {{ font-size: 1.5rem; font-weight: 700; color: #6C2BD9; margin-bottom: 24px; }}
        h1 {{ font-size: 1.25rem; color: #1a1a2e; margin-bottom: 12px; }}
        p {{ color: #555; line-height: 1.6; margin-bottom: 24px; }}
        .email {{ font-weight: 600; color: #333; }}
        form button {{ background: #6C2BD9; color: #fff; border: none; border-radius: 8px; padding: 12px 32px; font-size: 1rem; cursor: pointer; transition: background 0.2s; }}
        form button:hover {{ background: #5a23b5; }}
        .footer {{ margin-top: 32px; font-size: 0.8rem; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">Plataforma LIA / WeDOTalent</div>
        <h1>Cancelar Recebimento de Comunicações</h1>
        <p>Você está solicitando o cancelamento do recebimento de e-mails de comunicação para o endereço:</p>
        <p class="email">{email}</p>
        <p>Ao confirmar, você deixará de receber comunicações por e-mail relacionadas a processos seletivos desta empresa.</p>
        <form method="POST">
            <button type="submit">Confirmar Cancelamento</button>
        </form>
        <div class="footer">Plataforma LIA / WeDOTalent &mdash; Em conformidade com a LGPD</div>
    </div>
</body>
</html>"""

ALREADY_OPTED_OUT_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Já Cancelado - Plataforma LIA / WeDOTalent</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
        .container {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.08); max-width: 480px; width: 90%; padding: 40px; text-align: center; }}
        .logo {{ font-size: 1.5rem; font-weight: 700; color: #6C2BD9; margin-bottom: 24px; }}
        h1 {{ font-size: 1.25rem; color: #1a1a2e; margin-bottom: 12px; }}
        p {{ color: #555; line-height: 1.6; }}
        .check {{ font-size: 3rem; margin-bottom: 16px; }}
        .footer {{ margin-top: 32px; font-size: 0.8rem; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">Plataforma LIA / WeDOTalent</div>
        <div class="check">&#10003;</div>
        <h1>Comunicações Já Canceladas</h1>
        <p>O endereço <strong>{email}</strong> já teve o recebimento de comunicações cancelado anteriormente.</p>
        <p>Nenhuma ação adicional é necessária.</p>
        <div class="footer">Plataforma LIA / WeDOTalent &mdash; Em conformidade com a LGPD</div>
    </div>
</body>
</html>"""

CONFIRM_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cancelamento Confirmado - Plataforma LIA / WeDOTalent</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
        .container {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.08); max-width: 480px; width: 90%; padding: 40px; text-align: center; }}
        .logo {{ font-size: 1.5rem; font-weight: 700; color: #6C2BD9; margin-bottom: 24px; }}
        h1 {{ font-size: 1.25rem; color: #1a1a2e; margin-bottom: 12px; }}
        p {{ color: #555; line-height: 1.6; }}
        .check {{ font-size: 3rem; color: #22c55e; margin-bottom: 16px; }}
        .footer {{ margin-top: 32px; font-size: 0.8rem; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">Plataforma LIA / WeDOTalent</div>
        <div class="check">&#10003;</div>
        <h1>Cancelamento Confirmado</h1>
        <p>O endereço <strong>{email}</strong> foi removido da lista de comunicações com sucesso.</p>
        <p>Você não receberá mais e-mails de comunicação desta empresa.</p>
        <div class="footer">Plataforma LIA / WeDOTalent &mdash; Em conformidade com a LGPD</div>
    </div>
</body>
</html>"""

ERROR_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erro - Plataforma LIA / WeDOTalent</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }}
        .container {{ background: #fff; border-radius: 12px; box-shadow: 0 2px 16px rgba(0,0,0,0.08); max-width: 480px; width: 90%; padding: 40px; text-align: center; }}
        .logo {{ font-size: 1.5rem; font-weight: 700; color: #6C2BD9; margin-bottom: 24px; }}
        h1 {{ font-size: 1.25rem; color: #e74c3c; margin-bottom: 12px; }}
        p {{ color: #555; line-height: 1.6; }}
        .footer {{ margin-top: 32px; font-size: 0.8rem; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">Plataforma LIA / WeDOTalent</div>
        <h1>Link Inválido</h1>
        <p>O link de cancelamento é inválido ou expirou. Por favor, entre em contato com o suporte.</p>
        <div class="footer">Plataforma LIA / WeDOTalent &mdash; Em conformidade com a LGPD</div>
    </div>
</body>
</html>"""


@router.get("/unsubscribe/{token}", response_class=HTMLResponse, response_model=None)
async def unsubscribe_page(token: str, request: Request, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    ConsentEvent = _get_consent_event_model()
    email, company_id = verify_signed_token(token)
    if not email or not company_id:
        logger.warning("Invalid or forged unsubscribe token attempted")
        return HTMLResponse(content=ERROR_HTML, status_code=400)

    safe_email = html.escape(email)

    try:
        company_uuid = uuid.UUID(company_id)
    except ValueError:
        logger.warning("Invalid company_id in unsubscribe token")
        return HTMLResponse(content=ERROR_HTML, status_code=400)

    repo = OptoutRepository(db)
    existing = await repo.get_existing_optout(company_uuid, email)

    if existing:
        return HTMLResponse(content=ALREADY_OPTED_OUT_HTML.format(email=safe_email))

    return HTMLResponse(content=UNSUBSCRIBE_PAGE_HTML.format(email=safe_email))


@router.post("/unsubscribe/{token}", response_class=HTMLResponse, response_model=None)
async def process_unsubscribe(token: str, request: Request, db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    ConsentEvent = _get_consent_event_model()
    email, company_id = verify_signed_token(token)
    if not email or not company_id:
        logger.warning("Invalid or forged unsubscribe token on POST")
        return HTMLResponse(content=ERROR_HTML, status_code=400)

    safe_email = html.escape(email)

    try:
        company_uuid = uuid.UUID(company_id)
    except ValueError:
        logger.warning("Invalid company_id in unsubscribe token on POST")
        return HTMLResponse(content=ERROR_HTML, status_code=400)

    repo = OptoutRepository(db)
    existing = await repo.get_existing_optout(company_uuid, email)

    if existing:
        return HTMLResponse(content=ALREADY_OPTED_OUT_HTML.format(email=safe_email))

    try:
        consent_version_id = await repo.get_active_consent_version_id(company_uuid)
        if not consent_version_id:
            logger.warning(f"No active consent version for company {company_id}, type communication_email")
            return HTMLResponse(content=ERROR_HTML, status_code=400)

        await repo.create_optout_event(
            company_id=company_uuid,
            consent_version_id=consent_version_id,
            email=email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent', ''),
        )

        logger.info(f"LGPD opt-out processed for company_id={company_id}")
        return HTMLResponse(content=CONFIRM_HTML.format(email=safe_email))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing unsubscribe: {e}", exc_info=True)
        return HTMLResponse(content=ERROR_HTML, status_code=500)
