"""Integration: demo user → POST /api/v1/wizard/smart-orchestrate
resolves a concrete tenant context (no T-E regression).

Task #1043. Reproduces the original bug end-to-end:

1. Hit ``POST /api/v1/wizard/smart-orchestrate`` *without* an Authorization
   header so ``get_current_user_or_demo`` materialises the demo user
   through the auto-login fallback.
2. Read the demo user back from the DB and assert
   ``user.company_id == CANONICAL_DEMO_UUID`` (would be the legacy
   string ``"demo_company"`` before this PR — that mismatch is what
   caused the wizard to ask for company id in the chat).
3. Resolve the tenant snippet for that user via
   ``TenantContextService`` and assert it carries the concrete
   ``Demo Company`` / ``Tecnologia`` markers — i.e. it is NOT the
   degraded ``"sua empresa"`` fallback.
4. Inspect the wizard response: it must NOT ask for company identity
   nor for recruiter cadastro (T-E anti-pattern).

If the ``companies`` row, the seed UUID, ``dependencies.py`` and the
prompt guards ever drift apart again, this test fails loudly before
reaching production.
"""
from __future__ import annotations

import os
import re

import pytest

from scripts.seeds.demo_company import CANONICAL_DEMO_UUID


pytestmark = pytest.mark.integration


# Anti-pattern markers — recurrence of the T-E regression.
_ANTI_TENANT_QUESTION = re.compile(
    r"qual\s+(é\s+)?(o\s+)?(nome|setor|porte|tamanho|plano|headcount)\s+da?\s+empresa"
    r"|informe\s+(o\s+)?company[_\s]?id"
    r"|qual\s+(é\s+)?(o\s+)?id\s+da\s+empresa"
    r"|em\s+qual\s+empresa\s+voc[êe]\s+trabalha",
    re.IGNORECASE,
)
_ANTI_RECRUITER_CADASTRO = re.compile(
    r"qual\s+(é\s+)?(o\s+)?seu\s+nome"
    r"|qual\s+(o\s+)?seu\s+cargo"
    r"|qual\s+(é\s+)?(o\s+)?seu\s+(e-?mail|telefone)"
    r"|preciso\s+(saber|do)\s+seus?\s+dados"
    r"|cadastrar\s+(você|voc[êe]|o\s+recrutador)",
    re.IGNORECASE,
)
_ANTI_DEFAULT_FALLBACK = re.compile(r"\bsua empresa\b|\bgeral\b", re.IGNORECASE)


@pytest.mark.asyncio
async def test_wizard_smart_orchestrate_does_not_ask_for_tenant_or_recruiter() -> None:
    # Force dev mode so get_current_user_or_demo reaches the auto-login fallback.
    os.environ.setdefault("ENVIRONMENT", "development")

    # Local imports to keep collection-time surface minimal.
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy import or_, select

    from app.auth.models import User
    from app.core.database import async_session_maker, engine
    from app.main import app
    from app.shared.encryption.encrypted_field_mixin import _sha256_hash
    from app.shared.services.tenant_context_service import TenantContextService
    from scripts.seeds.demo_company import seed_demo_company

    # Ensure the canonical Demo Company row exists.
    async with engine.begin() as conn:
        await seed_demo_company(conn)

    # ----- Step 1: hit the actual wizard endpoint without auth header -----
    payload = {
        "message": "Quero criar uma vaga de Engenheiro de Software Pleno (backend, Python).",
        "current_stage": "intake",
        "collected_data": {},
        "conversation_history": [],
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/wizard/smart-orchestrate",
            json=payload,
            timeout=30.0,
        )

    assert response.status_code == 200, (
        f"Wizard endpoint returned {response.status_code}: "
        f"{response.text[:500]}"
    )
    body = response.json()
    lia_message = (body.get("message") or body.get("response_text") or "").strip()
    assert lia_message, f"Wizard returned empty message; body={body!r}"

    # ----- Step 2: re-read demo user from DB and assert canonical UUID -----
    async with async_session_maker() as db:
        result = await db.execute(
            select(User).where(
                or_(
                    User.email_hash == _sha256_hash("demo@wedotalent.com"),
                    User._email_raw == "demo@wedotalent.com",
                )
            )
        )
        persisted = result.scalar_one_or_none()

    assert persisted is not None, "Demo user not persisted by auto-login"
    assert persisted.company_id == CANONICAL_DEMO_UUID, (
        f"Demo user persisted with company_id={persisted.company_id!r}; "
        f"expected canonical UUID {CANONICAL_DEMO_UUID!r}. "
        f"This is the T-E regression — Task #1043."
    )

    # ----- Step 3: resolve tenant snippet end-to-end -----
    async with async_session_maker() as db:
        ctx = await TenantContextService().get_context(
            company_id=persisted.company_id,
            db=db,
        )
    assert ctx is not None
    assert ctx.company_name and ctx.company_name != "sua empresa", (
        f"TenantContextService resolved a degraded company_name "
        f"({ctx.company_name!r}) for the canonical demo user."
    )
    snippet = ctx.to_prompt_snippet()
    assert "Demo Company" in snippet
    assert "Tecnologia" in snippet
    assert "sua empresa" not in snippet

    # ----- Step 4: assert the wizard response itself is T-E-clean -----
    assert not _ANTI_TENANT_QUESTION.search(lia_message), (
        f"Wizard regressed T-E (asked for tenant identity): {lia_message!r}"
    )
    assert not _ANTI_RECRUITER_CADASTRO.search(lia_message), (
        f"Wizard regressed T-E (asked for recruiter cadastro): {lia_message!r}"
    )
    assert not _ANTI_DEFAULT_FALLBACK.search(lia_message), (
        f"Wizard used the degraded fallback ('sua empresa'/'geral'): {lia_message!r}"
    )
