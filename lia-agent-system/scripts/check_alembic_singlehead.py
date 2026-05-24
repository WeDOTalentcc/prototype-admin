#!/usr/bin/env python3
"""
Bug 2 sensor canonical: valida que alembic_version table tem EXATAMENTE
1 row consistente. Multi-head state (>1 row) é corrompido — causa de
'Requested revision X overlaps with other requested revisions Y' em
alembic upgrade.

Causa raiz Bug 2 (2026-05-24): migration 191 rodou parcialmente, tabela
company_benefit_history foi criada mas as 6 colunas de company_benefits
faltaram. alembic_version ficou com 2 rows (189 + 190) = state corrompido.

Run:
    python3 lia-agent-system/scripts/check_alembic_singlehead.py
    python3 lia-agent-system/scripts/check_alembic_singlehead.py --blocking
"""
import argparse
import asyncio
import os
import sys
import urllib.parse


async def check() -> tuple[int, list[str]]:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
    except ImportError:
        return -1, ["WARN: sqlalchemy not available in this env, skipping"]

    url = os.getenv("DATABASE_URL", "")
    if not url:
        return -1, ["WARN: DATABASE_URL not set, skipping"]
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    params.pop("sslmode", None)
    new_q = urllib.parse.urlencode(params, doseq=True)
    url = urllib.parse.urlunparse(parsed._replace(query=new_q))

    engine = create_async_engine(url, connect_args={"ssl": False})
    rows: list[str] = []
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
            rows = [r[0] for r in result.all()]
    finally:
        await engine.dispose()
    return len(rows), rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocking", action="store_true")
    args = parser.parse_args()

    count, rows = asyncio.run(check())
    if count < 0:
        print(rows[0] if rows else "WARN: skipped")
        return 0

    if count == 1:
        print(f"✅ check_alembic_singlehead: 1 row consistent ({rows[0]})")
        return 0

    print(f"⚠️  check_alembic_singlehead: {count} row(s) in alembic_version (expected 1)")
    for r in rows:
        print(f"  - {r}")
    print(
        "  → Fix: Em transação única, DELETE FROM alembic_version; "
        "INSERT INTO alembic_version (version_num) VALUES ('<head>'). "
        "Verifique antes que as DDLs de cada revision foram aplicadas "
        "(SELECT column_name FROM information_schema.columns WHERE table_name = ...). "
        "Reference: Bug 2 fix 2026-05-24."
    )
    if args.blocking:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
