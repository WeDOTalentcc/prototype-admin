"""Simulate what the FastAPI serializer returns for a seeded candidate."""
import asyncio, sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
from lia_config.database import AsyncSessionLocal
from sqlalchemy import text
from sqlalchemy.orm import Session
from libs.models.lia_models.candidate import Candidate

SEED_TAG = "seed_diretor_juridico"

async def main():
    async with AsyncSessionLocal() as db:
        # Load via ORM (same as the real API endpoint does)
        from sqlalchemy import select
        result = await db.execute(
            select(Candidate).where(Candidate.source == SEED_TAG).limit(1)
        )
        c = result.scalar_one_or_none()
        
        if not c:
            print("ERROR: No seeded candidate found")
            return
        
        print(f"Candidate: {c.name}")
        print(f"\nwork_history (len={len(c.work_history or [])}):")
        for exp in (c.work_history or [])[:2]:
            print(f"  - {exp.get('title')} at {exp.get('company_name')}")
        
        edu = getattr(c, "education_snapshot", None) or []
        print(f"\neducation (len={len(edu)}) [from getattr 'education_snapshot']:")
        for e in edu[:2]:
            print(f"  - {e.get('degree')} at {e.get('institution')}")
        
        langs = c.languages or {}
        print(f"\nlanguages: {langs}")
        
        certs = c.certifications or []
        print(f"\ncertifications: {certs[:3]}")

asyncio.run(main())
