import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://lia_user:lia_password@localhost:5432/lia_db"

async def check():
    engine = create_async_engine(DB_URL)
    async with engine.begin() as conn:
        r = await conn.execute(text("SELECT version_num FROM alembic_version"))
        print("DB alembic version:", r.fetchall())

        for tbl in ["company_retention_policies", "agent_templates"]:
            r2 = await conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '" + tbl + "')"
            ))
            print(f"  {tbl} exists:", r2.scalar())

        r3 = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'audit_logs' AND column_name IN ('output_text','input_text')"
        ))
        print("  audit_logs new columns:", r3.fetchall())

        r4 = await conn.execute(text(
            "SELECT indexname FROM pg_indexes WHERE indexname LIKE '%hnsw%'"
        ))
        print("  HNSW indexes:", r4.fetchall())

    await engine.dispose()

asyncio.run(check())
