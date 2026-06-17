import sys
P = "app/domains/sourcing/tools/query_tools.py"
src = open(P, encoding="utf-8").read()

def rep(old, new, label):
    global src
    if src.count(old) != 1:
        print(f"ABORT [{label}]: count={src.count(old)}"); sys.exit(1)
    src = src.replace(old, new); print(f"OK [{label}]")

# 1) location -> location_city (coluna real do model Candidate; era AttributeError)
rep(
    'conditions.append(Candidate.location.ilike(f"%{location}%"))',
    'conditions.append(Candidate.location_city.ilike(f"%{location}%"))',
    "location -> location_city")

# 2) skills post-filter -> technical_skills (coluna real; era sempre vazio)
rep(
    "for skill in (getattr(c, 'skills', []) or [])",
    "for skill in (getattr(c, 'technical_skills', []) or [])",
    "skills -> technical_skills")

open(P, "w", encoding="utf-8").write(src)
print("OK: colunas corrigidas")
