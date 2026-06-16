"""
Fix demo session branding - T017

Updates any triagem sessions that have 'WeDOTalent' or 'WeDo Talent'
as company_name to use the actual client company name from the
company profile instead. Demo sessions should show the client's
company name, not the platform brand.

Usage:
    python scripts/fix_demo_session_branding.py
"""
import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BRAND_NAMES = ["WeDOTalent", "WeDo Talent", "Wedo Talent", "wedo talent", "WedoTalent"]

SQL_UPDATE = """
UPDATE triagem_sessions ts
SET company_name = COALESCE(
    (SELECT cp.name FROM company_profiles cp WHERE cp.id::text = ts.company_id LIMIT 1),
    ts.company_name
)
WHERE ts.company_name IN ({placeholders})
  AND EXISTS (
    SELECT 1 FROM company_profiles cp WHERE cp.id::text = ts.company_id AND cp.name IS NOT NULL
  );
"""

SQL_FALLBACK_UPDATE = """
UPDATE triagem_sessions
SET company_name = 'Empresa Cliente'
WHERE company_name IN ({placeholders})
  AND NOT EXISTS (
    SELECT 1 FROM company_profiles cp WHERE cp.id::text = triagem_sessions.company_id AND cp.name IS NOT NULL
  );
"""


async def fix_branding():
    from app.core.database import get_db, async_engine
    from sqlalchemy import text

    placeholders = ", ".join(f"'{name}'" for name in BRAND_NAMES)

    async with async_engine.begin() as conn:
        result = await conn.execute(
            text(f"SELECT COUNT(*) FROM triagem_sessions WHERE company_name IN ({placeholders})")
        )
        count = result.scalar()
        logger.info(f"Found {count} triagem sessions with platform brand as company_name")

        if count == 0:
            logger.info("No sessions to update. Done.")
            return

        await conn.execute(
            text(SQL_UPDATE.format(placeholders=placeholders))
        )
        logger.info("Updated sessions with matching company profiles")

        await conn.execute(
            text(SQL_FALLBACK_UPDATE.format(placeholders=placeholders))
        )
        logger.info("Updated remaining sessions with fallback company name")

    logger.info("Branding fix complete.")


if __name__ == "__main__":
    asyncio.run(fix_branding())
