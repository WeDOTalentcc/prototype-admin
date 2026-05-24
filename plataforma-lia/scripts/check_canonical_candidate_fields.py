#!/usr/bin/env python3
"""
Sensor canonical (F11, 2026-05-24): detecta acessos camelCase em objetos
`candidate` que deveriam usar canonical snake_case do backend.

Canonical fields (do schema Postgres + Pydantic backend):
- current_title (não currentTitle)
- current_company (não currentCompany)
- years_of_experience (não yearsOfExperience)
- technical_skills (não technicalSkills)
- soft_skills (não softSkills)
- self_introduction (não selfIntroduction)
- work_history (não workHistory)
- location_city (não locationCity)
- is_blacklisted (não isBlacklisted)
- is_hired (não isHired)
- hired_job_title (não hiredJobTitle)
- linkedin_url (não linkedinUrl)
- github_url (não githubUrl)
- portfolio_url (não portfolioUrl)
- avatar_url (não avatarUrl)
- date_of_birth (não dateOfBirth)
- communication_consent (não communicationConsent)

Esses campos são canonical do backend (Pydantic schema + DB column names).
Acessos camelCase (legacy) frequentemente são undefined em runtime e quebram
features silenciosamente.

Por que é warn-only e não blocking imediato:
- 100+ sites legacy ainda existem
- Migração precisa ser progressiva para não quebrar fallback chains
- Sensor mede progresso, mas não força big-bang fix

Honra acessos com fallback: `candidate.current_title || candidate.currentTitle`
é OK (já tem canonical first). Apenas acessos puramente camelCase contam.
"""
import argparse
import re
import sys
from pathlib import Path
from collections import defaultdict


ROOT = Path("/home/runner/workspace/plataforma-lia/src")

CANONICAL_PAIRS = {
    "currentTitle": "current_title",
    "currentCompany": "current_company",
    "currentRole": "current_title",
    "yearsOfExperience": "years_of_experience",
    "technicalSkills": "technical_skills",
    "softSkills": "soft_skills",
    "selfIntroduction": "self_introduction",
    "workHistory": "work_history",
    "locationCity": "location_city",
    "isBlacklisted": "is_blacklisted",
    "isHired": "is_hired",
    "hiredJobTitle": "hired_job_title",
    "linkedinUrl": "linkedin_url",
    "githubUrl": "github_url",
    "portfolioUrl": "portfolio_url",
    "avatarUrl": "avatar_url",
    "dateOfBirth": "date_of_birth",
    "communicationConsent": "communication_consent",
    "willingToRelocate": "willing_to_relocate",
}


def scan(root: Path) -> list[tuple[str, int, str, str, str]]:
    """Returns [(file, lineno, camel_field, canonical, line)]"""
    violations = []
    for f in root.rglob("*.tsx"):
        if "__tests__" in f.parts or "node_modules" in f.parts:
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(lines):
            for camel, canonical in CANONICAL_PAIRS.items():
                # Match candidate.camelField or c.camelField (not as part of bigger word)
                pattern = re.compile(rf"\b(candidate|c|_candidate)\.{camel}\b")
                if not pattern.search(line):
                    continue
                # Skip if same line has fallback to canonical (e.g. c.current_title || c.currentTitle)
                if re.search(rf"\b(candidate|c|_candidate)\.{canonical}\b", line):
                    continue
                violations.append((str(f), i + 1, camel, canonical, line.strip()))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args()

    root = Path(args.root)
    violations = scan(root)

    print("check_canonical_candidate_fields.py\n")
    if not violations:
        print("✅ 0 violations — todos candidate.* fields usam canonical snake_case.")
        return 0

    by_file = defaultdict(list)
    for fp, ln, camel, canon, line in violations:
        by_file[fp].append((ln, camel, canon, line))

    for fp in sorted(by_file):
        rel = fp.replace("/home/runner/workspace/plataforma-lia/", "")
        print(f"\n📄 {rel}")
        for ln, camel, canon, line in by_file[fp]:
            print(f"   L{ln}: candidate.{camel} → candidate.{canon}")
            print(f"          {line[:100]}")

    print(f"\nTotal: {len(violations)} violation(s).")
    print(f"→ Fix: trocar candidate.{{camelField}} → candidate.{{canonical_snake}}.")
    print(f"       OU adicionar canonical primeiro como fallback:")
    print(f"       candidate.canonical_snake || candidate.camelField")
    return 1 if args.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
