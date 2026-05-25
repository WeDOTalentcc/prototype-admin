import asyncio, os, sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    url = os.getenv("DATABASE_URL","").replace("postgresql://","postgresql+asyncpg://")
    if not url:
        print("NO_DATABASE_URL"); return
    eng = create_async_engine(url)
    async with eng.connect() as c:
        print("\n=== Metadata 8 vagas ===")
        r = await c.execute(text("""
            SELECT id::text, title, status, company_id, source, created_at::text
            FROM job_vacancies
            WHERE title ILIKE '%sensor%harness%roundtrip%'
            ORDER BY created_at DESC
        """))
        for row in r:
            print(" | ".join(str(x) for x in row))
        
        print("\n=== Companies envolvidas ===")
        r = await c.execute(text("""
            SELECT company_id, count(*) FROM job_vacancies
            WHERE title ILIKE '%sensor%harness%roundtrip%'
            GROUP BY company_id
        """))
        for row in r:
            print(f"  {row[0]} -> {row[1]} leak(s)")
        
        print("\n=== Candidatos vinculados ===")
        r = await c.execute(text("""
            SELECT jv.id::text, jv.title, count(va.id) as n_cands
            FROM job_vacancies jv
            LEFT JOIN vacancy_applies va ON va.vacancy_id = jv.id
            WHERE jv.title ILIKE '%sensor%harness%roundtrip%'
            GROUP BY jv.id, jv.title
        """))
        for row in r:
            print(f"  job={row[0][:8]} title={row[1]} candidatos={row[2]}")
        
        print("\n=== Tasks vinculadas ===")
        r = await c.execute(text("""
            SELECT count(*) FROM tasks
            WHERE related_job_id::text IN (
              SELECT id::text FROM job_vacancies WHERE title ILIKE '%sensor%harness%roundtrip%'
            )
        """))
        print(f"  tasks_relacionadas: {r.scalar()}")
        
        print("\n=== Activity feed vinculadas ===")
        r = await c.execute(text("""
            SELECT count(*) FROM activity_feed
            WHERE target_id IN (
              SELECT id::text FROM job_vacancies WHERE title ILIKE '%sensor%harness%roundtrip%'
            )
        """))
        print(f"  activity_feed_relacionadas: {r.scalar()}")
        
    await eng.dispose()

asyncio.run(main())
