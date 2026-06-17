import asyncio
import sys

async def clean():
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                DELETE FROM routing_cache_vectors
                WHERE domain_id = 'job_management'
                AND (
                    message_text ILIKE '%criar%vaga%'
                    OR message_text ILIKE '%nova%vaga%'
                    OR message_text ILIKE '%abrir%vaga%'
                    OR message_text ILIKE '%quero criar%'
                    OR message_text ILIKE '%vamos criar%'
                    OR message_text ILIKE '%preciso contratar%'
                    OR message_text ILIKE '%publicar%vaga%'
                    OR message_text ILIKE '%wizard%'
                    OR message_text ILIKE '%requisi_ao%vaga%'
                )
            """))
            await db.commit()
            print(f"Deleted {result.rowcount} stale routing_cache_vectors entries")
    except Exception as e:
        print(f"DB cleanup failed: {e}")
        sys.exit(1)

asyncio.run(clean())
