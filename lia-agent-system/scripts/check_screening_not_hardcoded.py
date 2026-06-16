#!/usr/bin/env python3
"""
SENSOR canonical (harness-engineering): detect re-introduction of hardcoded
eligibility/screening questions bank no frontend.

Audit 2026-05-20 Sprint 1 F6 — catalogo agora e per-tenant via DB
(eligibility_question_templates) + endpoints canonical + hook
useEligibilityTemplates. O arquivo legacy `eligibility-questions-bank.ts`
foi DELETADO; qualquer reintroducao de constantes ELIGIBILITY_QUESTIONS_BANK
ou SCREENING_QUESTIONS_BANK em src/ deve ser flagada.

Run modes:
  blocking (default): exit 1 if hits found
  --warn-only: exit 0, lists hits

Exit codes:
  0 = no hits, OR warn-only mode
  1 = hits exist + blocking mode
  2 = usage error
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

FORBIDDEN_NAMES = (
    "ELIGIBILITY_QUESTIONS_BANK",
    "SCREENING_QUESTIONS_BANK",
)

FORBIDDEN_IMPORTS = (
    "from \"@/components/settings/eligibility-questions-bank\"",
    "from '@/components/settings/eligibility-questions-bank'",
    "from \"./eligibility-questions-bank\"",
    "from './eligibility-questions-bank'",
)

# Files allowed to contain references (e.g. the canonical hook itself
# may reference the legacy filename in comments).
ALLOWLIST = {
    "hooks/screening/use-eligibility-templates.ts",
    "components/screening-config/CompanyBankQuestions.tsx",
    "components/settings/useRecruitmentScreening.ts",
    "components/settings/RecruitmentScreeningTab.tsx",
    "components/settings/EligibilityTemplatesManager.tsx",
}


def find_hits(root: Path) -> list[tuple[Path, int, str]]:
    hits: list[tuple[Path, int, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in (".ts", ".tsx", ".js", ".jsx"):
            continue
        if any(skip in str(path) for skip in (
            "/node_modules/", "/.next/", "/dist/", "/__tests__/",
            ".test.", ".spec.", "/.bak/",
        )):
            continue
        rel = str(path.relative_to(root))
        if rel in ALLOWLIST:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_no, line in enumerate(source.splitlines(), start=1):
            for forbidden_imp in FORBIDDEN_IMPORTS:
                if forbidden_imp in line:
                    hits.append((path, line_no, line.strip()))
                    break
            else:
                # Check forbidden constants only if not in allowlist
                for forbidden_name in FORBIDDEN_NAMES:
                    if forbidden_name in line and "from" not in line:
                        # heuristic: skip type-only references
                        if "//" in line.split(forbidden_name)[0]:
                            continue
                        hits.append((path, line_no, line.strip()))
                        break
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect reintroduction of hardcoded eligibility questions bank."
    )
    parser.add_argument(
        "--root",
        default="../plataforma-lia/src",
        help="Root dir to scan (default: ../plataforma-lia/src relative to lia-agent-system).",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 even if violations found.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        # Try alternative paths
        alt = Path("/home/runner/workspace/plataforma-lia/src").resolve()
        if alt.exists():
            root = alt
        else:
            print(f"Error: --root {root} does not exist", file=sys.stderr)
            return 2

    hits = find_hits(root)
    if not hits:
        print(f"✅ No hardcoded eligibility/screening questions bank detected "
              f"under {root}.")
        return 0

    print(
        f"⚠️  {len(hits)} reintroduction(s) of hardcoded "
        f"ELIGIBILITY_QUESTIONS_BANK/SCREENING_QUESTIONS_BANK detected.\n\n"
        f"Audit 2026-05-20 Sprint 1 F6: catalogo eligibility deve vir do hook\n"
        f"useEligibilityTemplates (canonical per-tenant via DB), nao de file\n"
        f"hardcoded. Se voce realmente precisa de uma lista master estatica,\n"
        f"adicione o arquivo ao ALLOWLIST do sensor com justificativa.\n"
    )
    for path, line_no, snippet in hits:
        print(f"── {path.relative_to(root.parent)}:{line_no}")
        print(f"   {snippet[:120]}")
        print()

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
