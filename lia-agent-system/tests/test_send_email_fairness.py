"""
Sensor — send_email bloqueia texto com vies explicito (L1) antes de enviar.
O texto pode ter sido editado a mao no modal de comunicacao. Auditoria 2026-06-10.
"""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.api.v1.communication import send_email, SendEmailRequest


@pytest.mark.asyncio
async def test_send_email_blocks_discriminatory_text():
    req = SendEmailRequest(
        to_email="a@b.com",
        subject="Retorno sobre sua candidatura",
        body_html="<p>Olá, decidimos não seguir; prefiro homens para esta vaga.</p>",
        body_text="Olá, decidimos não seguir; prefiro homens para esta vaga.",
    )
    with pytest.raises(HTTPException) as exc:
        await send_email(req, MagicMock(), "co-1")
    assert exc.value.status_code == 422
    assert isinstance(exc.value.detail, dict)
    assert exc.value.detail.get("error") == "fairness_blocked"
