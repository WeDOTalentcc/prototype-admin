#!/usr/bin/env python3
"""
SENSOR canonical (harness-engineering): detect re-introduction of hardcoded
DEFAULT_STAGES catalog (15 stages do funil de recrutamento) no frontend.

Audit 2026-05-20 Sprint 2 F6 — catalogo agora e per-tenant via DB
(pipeline_stage_templates) + endpoints canonical + hook
usePipelineStageTemplates. O catalogo hardcoded `DEFAULT_STAGES` em
src/components/settings/RecruitmentJourneyConfig.tsx:51 e o legacy de
suporte; qualquer NOVA introducao em arquivos fora do ALLOWLIST deve ser
flagada.

NOTA: `DEFAULT_STAGES_FALLBACK` (PT-BR, ~5 strings) e PERMITIDO em modais
como resiliencia UX (preservado por decisao Sprint 2 F4) — diferente do
catalogo completo de 15 stages.

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

# Constants forbidden outside ALLOWLIST (catalogo completo de 15 stages)
FORBIDDEN_NAMES = (
    "DEFAULT_STAGES",
)

# Imports forbidden outside ALLOWLIST
FORBIDDEN_IMPORTS = (
    "from \"@/components/settings/RecruitmentJourneyConfig\"",
    "from '@/components/settings/RecruitmentJourneyConfig'",
)

# Files allowed to contain DEFAULT_STAGES references — legacy fonte +
# settings page that owns the locally-edited journey (distinct concern from
# job-creation pipeline catalog).
ALLOWLIST = {
    # Canonical source (legacy export — preserved como deprecation target)
    "components/settings/RecruitmentJourneyConfig.tsx",
    # Settings page that consumes DEFAULT_STAGES as initial state
    # (locally-edited recruitment journey config — distinct from pipeline
    # template catalog used in job creation)
    "components/settings/useRecruitmentPersistence.ts",
    # Hook recruitment-stages: legacy fallback for settings persistence
    "hooks/recruitment/use-recruitment-stages.ts",
    # Canonical hook itself references legacy filename in comments
    "hooks/pipeline/use-pipeline-stage-templates.ts",
    # Test for the recruitment-stages hook
    "hooks/__tests__/use-recruitment-stages.test.ts",
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
            # Skip lines using DEFAULT_STAGES_FALLBACK (canonical UX
            # resilience — preserved per Sprint 2 F4 decision)
            stripped = line.strip()
            if "DEFAULT_STAGES_FALLBACK" in stripped:
                continue
            # Check forbidden imports first — only when import line references
            # DEFAULT_STAGES specifically (type-only imports of
            # RecruitmentStage/SubStatus are NOT a hardcoded catalog usage).
            triggered = False
            for forbidden_imp in FORBIDDEN_IMPORTS:
                if forbidden_imp not in line:
                    continue
                if "DEFAULT_STAGES" in line:
                    hits.append((path, line_no, stripped))
                    triggered = True
                    break
            if triggered:
                continue
            # Check forbidden constants (DEFAULT_STAGES standalone)
            for forbidden_name in FORBIDDEN_NAMES:
                if forbidden_name not in line:
                    continue
                # Reject only when truly identifies DEFAULT_STAGES standalone,
                # not DEFAULT_STAGES_FALLBACK or DEFAULT_STAGES_FOO
                idx = line.find(forbidden_name)
                # check next char after token to ensure word-boundary
                end = idx + len(forbidden_name)
                if end < len(line) and (line[end].isalnum() or line[end] == "_"):
                    continue  # different token (e.g. DEFAULT_STAGES_FALLBACK)
                # heuristic: skip type-only / comment-only refs
                pre = line[:idx]
                if "//" in pre or "*" in pre.strip()[:2]:
                    continue
                hits.append((path, line_no, stripped))
                break
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect reintroduction of hardcoded DEFAULT_STAGES catalog."
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
        print(f"✅ No hardcoded DEFAULT_STAGES catalog detected outside ALLOWLIST "
              f"under {root}.")
        return 0

    print(
        f"⚠️  {len(hits)} reintroduction(s) of hardcoded DEFAULT_STAGES detected.\n\n"
        f"Audit 2026-05-20 Sprint 2 F6: catalogo de pipeline stages deve vir do hook\n"
        f"usePipelineStageTemplates (canonical per-tenant via DB), nao de file\n"
        f"hardcoded. Se voce realmente precisa do legacy DEFAULT_STAGES (e.g., para\n"
        f"o settings page locally-edited journey), adicione o arquivo ao ALLOWLIST\n"
        f"do sensor com justificativa.\n\n"
        f"Resilience UX: DEFAULT_STAGES_FALLBACK (~5 strings PT-BR) e permitido\n"
        f"em modais como fallback de loading/error — sensor nao flagar.\n"
    )
    for path, line_no, snippet in hits:
        print(f"── {path.relative_to(root.parent)}:{line_no}")
        print(f"   {snippet[:120]}")
        print()

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
