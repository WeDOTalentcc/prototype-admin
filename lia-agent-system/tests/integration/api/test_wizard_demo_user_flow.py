"""Integration: demo user → /api/v1/wizard/smart-orchestrate resolves a
concrete tenant context (no T-E regression).

Task #1043. Reproduces the original bug end-to-end:

1. Hit a route that depends on ``get_current_user_or_demo`` (no JWT) so
   the demo user is materialised through the auto-login fallback.
2. Read the demo user back from the DB and assert
   ``user.company_id == CANONICAL_DEMO_UUID`` (would be the legacy
   string ``"demo_company"`` before this PR — that mismatch is what
   caused the wizard to ask for company id in the chat).
3. Resolve the tenant snippet for that user via ``TenantContextService``
   and assert it carries the concrete ``Demo Company`` /
   ``Tecnologia`` markers — i.e. it is NOT the degraded
   ``"sua empresa"`` / ``"geral"`` fallback.

This guards the full chain that the prompt sentinel and the structural
literal test alone cannot guarantee. If the ``companies`` row, the
seed UUID, and ``dependencies.py`` ever drift apart again, this test
fails loudly before reaching production.
"""
from __future__ import annotations

import os

import pytest

from scripts.seeds.demo_company import CANONICAL_DEMO_UUID


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_demo_user_resolves_canonical_tenant_context() -> None:
    # Force dev mode so get_current_user_or_demo is reachable.
    os.environ.setdefault("ENVIRONMENT", "development")

    # Imports are local to keep collection-time import surface small.
    from sqlalchemy import or_, select

    from app.auth.dependencies import get_current_user_or_demo
    from app.auth.models import User
    from app.core.database import async_session_maker, engine
    from app.shared.encryption.encrypted_field_mixin import _sha256_hash
    from app.shared.services.tenant_context_service import TenantContextService

    # Ensure the canonical Demo Company row exists so the resolver has
    # something to bind to. Re-runnable (UPSERT).
    from scripts.seeds.demo_company import seed_demo_company

    async with engine.begin() as conn:
        await seed_demo_company(conn)

    # ----- Step 1: trigger the auto-login fallback -----
    async with async_session_maker() as db:
        demo_user = await get_current_user_or_demo(credentials=None, db=db)

    assert demo_user is not None, "get_current_user_or_demo returned no user"

    # ----- Step 2: re-read from DB to dodge any in-memory drift -----
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

    assert persisted is not None, "Demo user not persisted"
    assert persisted.company_id == CANONICAL_DEMO_UUID, (
        f"Demo user persisted with company_id={persisted.company_id!r}; "
        f"expected canonical UUID {CANONICAL_DEMO_UUID!r}. "
        f"This is the T-E regression — the wizard would now ask for "
        f"company id in the chat. See Task #1043."
    )

    # ----- Step 3: resolve tenant snippet through the canonical service -----
    async with async_session_maker() as db:
        ctx = await TenantContextService().get_context(
            company_id=persisted.company_id,
            db=db,
        )

    assert ctx is not None
    assert ctx.company_name and ctx.company_name != "sua empresa", (
        f"TenantContextService resolved a degraded company_name "
        f"({ctx.company_name!r}) for the canonical demo user. The wizard "
        f"would degrade to asking the recruiter for the company name."
    )
    assert "Tecnologia" in (ctx.sector or ""), (
        f"Demo Company seed expected sector 'Tecnologia'; got {ctx.sector!r}"
    )

    snippet = ctx.to_prompt_snippet()
    assert "Demo Company" in snippet
    assert "Tecnologia" in snippet
    assert "sua empresa" not in snippet
