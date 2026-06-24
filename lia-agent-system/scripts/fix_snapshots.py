"""
Fix: populate candidates.work_history and education_snapshot for seeded Diretor Juridico candidates.
The FastAPI serializer reads from JSON snapshot columns, not from relational tables.
Also fix: languages format {level} → {proficiency} to match UI expectations.
"""
import asyncio
import json
import sys
sys.path.insert(0, "/home/runner/workspace/lia-agent-system")
from lia_config.database import AsyncSessionLocal
from sqlalchemy import text

SEED_TAG = "seed_diretor_juridico"

async def main():
    async with AsyncSessionLocal() as db:
        # Get all seeded candidate IDs
        res = await db.execute(text(
            "SELECT id, name, languages FROM candidates WHERE source = :tag"
        ), {"tag": SEED_TAG})
        candidates = res.fetchall()
        print(f"Found {len(candidates)} seeded candidates")

        for c_row in candidates:
            cid = str(c_row[0])
            name = c_row[1]
            curr_langs = c_row[2]

            # ── 1. Build work_history from candidate_experiences ──────────
            exp_res = await db.execute(text("""
                SELECT company_name, title, start_date, end_date, is_current,
                       description, location, industries, sequence_order
                FROM candidate_experiences
                WHERE candidate_id = CAST(:cid AS uuid)
                ORDER BY sequence_order ASC
            """), {"cid": cid})
            exps = exp_res.fetchall()

            work_history = []
            for e in exps:
                work_history.append({
                    "company_name": e[0],
                    "title": e[1],
                    "start_date": e[2],
                    "end_date": e[3],
                    "is_current": e[4] or False,
                    "description": e[5] or "",
                    "location": e[6] or "",
                    "industries": list(e[7]) if e[7] else [],
                    "sequence_order": e[8] or 0,
                })

            # ── 2. Build education_snapshot from candidate_education ───────
            edu_res = await db.execute(text("""
                SELECT institution, degree, field_of_study, start_date, end_date,
                       is_completed, institution_city, institution_state, institution_country,
                       sequence_order
                FROM candidate_education
                WHERE candidate_id = CAST(:cid AS uuid)
                ORDER BY sequence_order ASC
            """), {"cid": cid})
            edus = edu_res.fetchall()

            education_snapshot = []
            for e in edus:
                education_snapshot.append({
                    "institution": e[0],
                    "degree": e[1] or "",
                    "field_of_study": e[2] or "",
                    "start_date": e[3],
                    "end_date": e[4],
                    "is_completed": e[5] or True,
                    "institution_city": e[6] or "",
                    "institution_state": e[7] or "",
                    "institution_country": e[8] or "Brasil",
                    "sequence_order": e[9] or 0,
                })

            # ── 3. Fix languages format: {level} → {proficiency} ──────────
            fixed_langs = curr_langs
            if isinstance(curr_langs, list):
                fixed_langs = []
                for lang in curr_langs:
                    if isinstance(lang, dict):
                        fixed_lang = {
                            "language": lang.get("language", ""),
                            "proficiency": lang.get("proficiency") or lang.get("level", ""),
                        }
                        fixed_langs.append(fixed_lang)

            # ── 4. Update the candidates table ────────────────────────────
            # education_snapshot was added by migration 258 (was missing from DB)
            await db.execute(text("""
                UPDATE candidates
                SET work_history = CAST(:wh AS json),
                    education_snapshot = CAST(:edu AS json),
                    languages = CAST(:langs AS json),
                    updated_at = NOW()
                WHERE id = CAST(:cid AS uuid)
            """), {
                "wh": json.dumps(work_history),
                "edu": json.dumps(education_snapshot),
                "langs": json.dumps(fixed_langs),
                "cid": cid,
            })

            print(f"  ✅ {name}: {len(work_history)} exps, {len(education_snapshot)} edus, {len(fixed_langs)} langs")

        await db.commit()
        print("\n✅ Snapshots atualizados com sucesso!")

asyncio.run(main())
