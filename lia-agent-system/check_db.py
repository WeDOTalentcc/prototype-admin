import asyncio
import sys
sys.path.insert(0, ".")

async def check():
    from app.db.session import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as s:
        r = await s.execute(text("SELECT version_num FROM alembic_version"))
        print("DB version:", r.fetchall())

        for tbl in ["company_retention_policies", "agent_templates"]:
            r2 = await s.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '" + tbl + "')"
            ))
            print(f"  {tbl} exists:", r2.scalar())

        r3 = await s.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'audit_logs' AND column_name = 'output_text'"
        ))
        print("  audit_logs.output_text column:", r3.fetchone())

        # Check HNSW indexes
        r4 = await s.execute(text(
            "SELECT indexname FROM pg_indexes WHERE indexname LIKE '%hnsw%'"
        ))
        print("  HNSW indexes:", r4.fetchall())

asyncio.run(check())
