"""Canonical Demo Company seed (Task #969 / T-C).

Idempotent UPSERT that materialises the demo tenant under its canonical
UUID with rich values populating the new columns added by Alembic
migration ``127_enrich_companies_schema``.

Why the values are concrete and editorial
-----------------------------------------
Demo Company is the tenant most users see first. Its
``TenantContext.to_prompt_snippet()`` becomes the example of what the
LIA infers about a tenant. Generic defaults
(``sector="geral"``, ``plan="standard"``) hide regressions in the
TenantContextService chain. Concrete values surface them immediately.

Run standalone::

    cd lia-agent-system && python -m scripts.seeds.demo_company
"""
from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)

CANONICAL_DEMO_UUID = "00000000-0000-4000-a000-000000000001"

DEMO_COMPANY_VALUES = {
    "id": CANONICAL_DEMO_UUID,
    "name": "Demo Company",
    "display_name": "Demo Company - WeDo Talent",
    "is_active": True,
    "is_demo": True,
    "sector": "Tecnologia",
    "industry_segment": "HRTech",
    "plan": "enterprise",
    "timezone": "America/Sao_Paulo",
    "headcount_range": "50-200",
    "lia_persona_override": (
        "Voce e a LIA da WeDo Talent, parceira de recrutamento da "
        "Demo Company. Use linguagem direta, baseada em dados, e "
        "explicite trade-offs antes de recomendar uma decisao."
    ),
}


_UPSERT_SQL = text(
    """
    INSERT INTO companies (
        id, name, display_name, is_active, is_demo,
        sector, industry_segment, plan, timezone,
        headcount_range, lia_persona_override,
        created_at, updated_at
    ) VALUES (
        :id, :name, :display_name, :is_active, :is_demo,
        :sector, :industry_segment, :plan, :timezone,
        :headcount_range, :lia_persona_override,
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
    )
    ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        display_name = EXCLUDED.display_name,
        is_active = EXCLUDED.is_active,
        is_demo = EXCLUDED.is_demo,
        sector = EXCLUDED.sector,
        industry_segment = EXCLUDED.industry_segment,
        plan = EXCLUDED.plan,
        timezone = EXCLUDED.timezone,
        headcount_range = EXCLUDED.headcount_range,
        lia_persona_override = EXCLUDED.lia_persona_override,
        updated_at = CURRENT_TIMESTAMP
    """
)


async def seed_demo_company(conn) -> dict:
    """Upsert the canonical Demo Company row.

    Args:
        conn: SQLAlchemy AsyncConnection (must be inside a transaction).

    Returns:
        Snapshot of values written (for logging/auditing).
    """
    await conn.execute(_UPSERT_SQL, DEMO_COMPANY_VALUES)
    return dict(DEMO_COMPANY_VALUES)


async def _main() -> None:
    from app.core.database import engine

    async with engine.begin() as conn:
        snapshot = await seed_demo_company(conn)
    logger.info(
        "[seeds.demo_company] upserted canonical demo tenant id=%s sector=%s plan=%s",
        snapshot["id"], snapshot["sector"], snapshot["plan"],
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(_main())
