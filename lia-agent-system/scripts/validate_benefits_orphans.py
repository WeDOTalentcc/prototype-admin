#!/usr/bin/env python3
"""
validate_benefits_orphans.py — Fase 3, Passo 3.1 (non-destructive).

Para cada job_vacancy.benefits (string ou dict):
  Se string: tenta casar com company_benefits.name (mesma empresa).
  Se dict com id: registra como estruturado.

Com --apply: cria company_benefits orphaos + salva CSVs em /tmp/.

Uso:
  python3 validate_benefits_orphans.py         # dry-run
  python3 validate_benefits_orphans.py --apply
"""
import asyncio, sys, csv
from collections import defaultdict

DB_URL = __import__("os").environ.get("DATABASE_URL", "")
if not DB_URL:
    sys.exit("ERROR: DATABASE_URL not set")

APPLY = "--apply" in sys.argv


async def main():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text

    engine = create_async_engine(DB_URL, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        jobs = (await session.execute(
            text("SELECT id, company_id, title, benefits FROM job_vacancies WHERE benefits IS NOT NULL AND benefits != '[]'::jsonb")
        )).fetchall()

        cb_rows = (await session.execute(text("SELECT id, company_id, name FROM company_benefits"))).fetchall()
        cb_by_company: dict[str, dict[str, str]] = defaultdict(dict)
        for r in cb_rows:
            cb_by_company[r.company_id][r.name.lower()] = str(r.id)

        matches, orphans, structured = [], [], []

        for job in jobs:
            jid, cid, benefits = str(job.id), str(job.company_id), (job.benefits or [])
            for b in benefits:
                if isinstance(b, dict) and b.get("id"):
                    structured.append({"job_id": jid, "company_id": cid, "benefit": b})
                elif isinstance(b, str) and b.strip():
                    uuid = cb_by_company.get(cid, {}).get(b.strip().lower())
                    (matches if uuid else orphans).append({"job_id": jid, "company_id": cid, "benefit_name": b, "benefit_uuid": uuid or ""})

        print(f"\n=== Orphan Report ===")
        print(f"Jobs scanned:        {len(jobs)}")
        print(f"Already structured:  {len(structured)}")
        print(f"Matched (name->id):  {len(matches)}")
        print(f"Orphans (no match):  {len(orphans)}")

        if orphans:
            print("\nOrphan samples (first 20):")
            for o in orphans[:20]:
                print(f"  co={o['company_id'][:8]}... job={o['job_id'][:8]}... benefit=\"{o['benefit_name']}\"")

        if APPLY:
            import uuid as _uuid
            from datetime import datetime
            created = 0
            for o in orphans:
                await session.execute(text("""
                    INSERT INTO company_benefits (id, company_id, name, category, value_type, is_active, is_highlighted, imported_from_legacy, created_at, updated_at)
                    VALUES (:id, :cid, :name, 'other', 'informative', true, false, true, :now, :now)
                    ON CONFLICT DO NOTHING
                """), {"id": str(_uuid.uuid4()), "cid": o["company_id"], "name": o["benefit_name"], "now": datetime.utcnow()})
                created += 1
            await session.commit()
            print(f"\nCREATED {created} company_benefits (imported_from_legacy=true)")
            for fname, rows, fields in [
                ("/tmp/relatorio_matches.csv", matches, ["job_id","company_id","benefit_name","benefit_uuid"]),
                ("/tmp/relatorio_orfaos.csv", orphans, ["job_id","company_id","benefit_name"]),
            ]:
                with open(fname, "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
            print("CSVs: /tmp/relatorio_matches.csv + /tmp/relatorio_orfaos.csv")

    await engine.dispose()

asyncio.run(main())
