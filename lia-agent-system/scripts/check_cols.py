import asyncio, sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
from lia_config.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'candidates'
            ORDER BY ordinal_position
        """))
        print("=== candidates columns ===")
        for r in res.fetchall():
            print(f"  {r[0]}: {r[1]}")

asyncio.run(main())
