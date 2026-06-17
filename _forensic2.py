import os, psycopg2
url = os.environ["DATABASE_URL"]
conn = psycopg2.connect(url)
cur = conn.cursor()

print("=== Metadata 8 vagas ===")
cur.execute("""
    SELECT id::text, title, status, company_id, source, created_at::text
    FROM job_vacancies
    WHERE title ILIKE %s
    ORDER BY created_at DESC
""", ('%sensor%harness%roundtrip%',))
for row in cur.fetchall():
    print(" | ".join(str(x) for x in row))

print("\n=== Companies envolvidas ===")
cur.execute("""
    SELECT company_id, count(*) FROM job_vacancies
    WHERE title ILIKE %s GROUP BY company_id
""", ('%sensor%harness%roundtrip%',))
for row in cur.fetchall():
    print(f"  {row[0]} -> {row[1]} leak(s)")

print("\n=== Candidatos vinculados ===")
cur.execute("""
    SELECT jv.id::text, count(va.id) as n_cands
    FROM job_vacancies jv
    LEFT JOIN vacancy_applies va ON va.vacancy_id = jv.id
    WHERE jv.title ILIKE %s
    GROUP BY jv.id
""", ('%sensor%harness%roundtrip%',))
for row in cur.fetchall():
    print(f"  job={row[0][:8]} candidatos={row[1]}")

print("\n=== Tasks vinculadas ===")
cur.execute("""
    SELECT count(*) FROM tasks
    WHERE related_job_id::text IN (
      SELECT id::text FROM job_vacancies WHERE title ILIKE %s
    )
""", ('%sensor%harness%roundtrip%',))
print(f"  tasks_relacionadas: {cur.fetchone()[0]}")

print("\n=== Activity feed vinculadas ===")
cur.execute("""
    SELECT count(*) FROM activity_feed
    WHERE target_id IN (
      SELECT id::text FROM job_vacancies WHERE title ILIKE %s
    )
""", ('%sensor%harness%roundtrip%',))
print(f"  activity_feed_relacionadas: {cur.fetchone()[0]}")

cur.close(); conn.close()
