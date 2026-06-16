import asyncio, sys, json
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
from lia_config.database import AsyncSessionLocal
from sqlalchemy import text

SEED_TAG = "seed_diretor_juridico"

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("""
            SELECT c.name, c.work_history, c.education_snapshot, c.languages, c.certifications
            FROM candidates c
            WHERE c.source = :tag
            LIMIT 2
        """), {"tag": SEED_TAG})
        
        for row in res.fetchall():
            name = row[0]
            wh = row[1] or []
            edu = row[2] or []
            langs = row[3] or []
            certs = row[4] or []
            
            print(f"\n{'='*50}")
            print(f"Name: {name}")
            print(f"work_history [{len(wh)} entries]:")
            for e in wh[:2]:
                print(f"  - {e.get('title')} at {e.get('company_name')} ({e.get('start_date')} - {e.get('end_date') or 'atual'})")
            print(f"education_snapshot [{len(edu)} entries]:")
            for e in edu[:2]:
                print(f"  - {e.get('degree')} in {e.get('field_of_study')} at {e.get('institution')}")
            print(f"languages [{len(langs)} entries]:")
            for l in langs[:3]:
                print(f"  - {l}")
            print(f"certifications [{len(certs)} entries]: {certs[:3]}")

asyncio.run(main())
