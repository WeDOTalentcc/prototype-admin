from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
import base64
import logging
import uuid
from datetime import datetime


def _get_consent_event_model():
    from app.domains.analytics.models.observability import ConsentEvent
    return ConsentEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/communication', tags=['communication-optout'])

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


def decode_unsubscribe_token(token: str):
    try:
        decoded = base64.urlsafe_b64decode(token).decode('utf-8')
        parts = decoded.split(':', 1)
        if len(parts) != 2:
            return None, None
        email, company_id = parts
        if not email or not company_id:
            return None, None
        return email, company_id
    except Exception:
        return None, None


@router.get("/unsubscribe/{token}", response_class=HTMLResponse)
async def unsubscribe_page(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    ConsentEvent = _get_consent_event_model()
    email, company_id = decode_unsubscribe_token(token)
    if not email or not company_id:
        logger.warning(f"Invalid unsubscribe token attempted")
        return HTMLResponse(content=ERROR_HTML, status_code=400)

    try:
        company_uuid = uuid.UUID(company_id)
    except ValueError:
        logger.warning(f"Invalid company_id in unsubscribe token")
        return HTMLResponse(content=ERROR_HTML, status_code=400)

    existing_query = select(ConsentEvent).where(
        and_(
            ConsentEvent.company_id == company_uuid,
            ConsentEvent.subject_email == email,
            ConsentEvent.event_type == 'revoked',
            ConsentEvent.channel == 'communication_email'
        )
    ).limit(1)
    result = await db.execute(existing_query)
    existing = result.scalar_one_or_none()

    if existing:
        return HTMLResponse(content=ALREADY_OPTED_OUT_HTML.format(email=email))

    return HTMLResponse(content=UNSUBSCRIBE_PAGE_HTML.format(email=email))


@router.post("/unsubscribe/{token}", response_class=HTMLResponse)
async def process_unsubscribe(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    ConsentEvent = _get_consent_event_model()
    email, company_id = decode_unsubscribe_token(token)
    if not email or not company_id:
        logger.warning(f"Invalid unsubscribe token on POST")
        return HTMLResponse(content=ERROR_HTML, status_code=400)

    try:
        company_uuid = uuid.UUID(company_id)
    except ValueError:
        logger.warning(f"Invalid company_id in unsubscribe token on POST")
        return HTMLResponse(content=ERROR_HTML, status_code=400)

    existing_query = select(ConsentEvent).where(
        and_(
            ConsentEvent.company_id == company_uuid,
            ConsentEvent.subject_email == email,
            ConsentEvent.event_type == 'revoked',
            ConsentEvent.channel == 'communication_email'
        )
    ).limit(1)
    result = await db.execute(existing_query)
    existing = result.scalar_one_or_none()

    if existing:
        return HTMLResponse(content=ALREADY_OPTED_OUT_HTML.format(email=email))

    try:
        import hashlib
        now = datetime.utcnow()
        proof_data = f"{email}|{company_id}|revoked|communication_email|{now.isoformat()}"
        proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()

        nil_version_id = uuid.UUID('00000000-0000-0000-0000-000000000000')

        consent_event = ConsentEvent(
            id=uuid.uuid4(),
            company_id=company_uuid,
            consent_version_id=nil_version_id,
            subject_email=email,
            subject_identifier=email,
            event_type='revoked',
            consent_given=False,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent', '')[:500],
            device_info={},
            channel='communication_email',
            proof_hash=proof_hash,
            expires_at=None
        )

        db.add(consent_event)
        await db.commit()

        logger.info(f"LGPD opt-out processed for email={email}, company_id={company_id}")
        return HTMLResponse(content=CONFIRM_HTML.format(email=email))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error processing unsubscribe for {email}: {e}", exc_info=True)
        return HTMLResponse(content=ERROR_HTML, status_code=500)
