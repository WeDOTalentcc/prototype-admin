#!/usr/bin/env python3
"""
SENSOR canonical (harness-engineering): detect re-introduction of hardcoded
alert rules constants no frontend.

Audit 2026-05-20 Sprint 3 F6 — catalogo agora e per-tenant via DB
(alert_rule_templates) + endpoints canonical + hook useAlertRuleTemplates.

O legacy DEFAULT_ALERTS em
`CommunicationHub.constants.ts` esta marcado como @deprecated e PRESERVADO
como fallback transitorio (hook tem loading state; usuario nao deve ver
catalogo vazio durante loading). Decisao F6 2026-05-21: NAO deletar agora —
runtime warning em useCommunicationHub.ts informa o status deprecated.

Qualquer reintroducao de `DEFAULT_ALERTS` ou `ALERT_RULES_BANK` em outro
arquivo (FORA do allowlist canonical) deve ser flagada.

IMPORTANTE: existe SEGUNDO DEFAULT_ALERTS em `goalsPlanningConstants.ts`
com schema DIFERENTE (goals/planning module, fora do escopo Sprint 3 alert
rules). Sensor IGNORA `goalsPlanningConstants.ts` e `useGoalsPlanningHub.ts`.

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
    "DEFAULT_ALERTS",
    "ALERT_RULES_BANK",
    "ALERT_RULE_TEMPLATES_BANK",
)

# Files allowed to contain references:
# - CommunicationHub.constants.ts: canonical legacy fallback (deprecated, preserved)
# - useCommunicationHub.ts: legacy seed consumer + runtime deprecation warning
# - use-alert-rule-templates.ts: canonical hook (may reference legacy filename in comments)
# - goalsPlanningConstants.ts / useGoalsPlanningHub.ts: SEGUNDO DEFAULT_ALERTS com
#   schema diferente (goals/planning module). Fora do escopo Sprint 3 alert rules.
ALLOWLIST = {
    "components/settings/communication-hub/CommunicationHub.constants.ts",
    "components/settings/communication-hub/useCommunicationHub.ts",
    "components/settings/goalsPlanningConstants.ts",
    "components/settings/useGoalsPlanningHub.ts",
    "hooks/communication/use-alert-rule-templates.ts",
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
            # Match if line contains any FORBIDDEN_NAME (covers both
            # `import { DEFAULT_ALERTS } from ...` AND `const x = DEFAULT_ALERTS`).
            for forbidden_name in FORBIDDEN_NAMES:
                if forbidden_name in line:
                    # heuristic: skip type-only references in inline comments
                    if "//" in line.split(forbidden_name)[0]:
                        continue
                    hits.append((path, line_no, line.strip()))
                    break
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect reintroduction of hardcoded alert rules bank."
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
        print(f"✅ No hardcoded alert rules bank detected "
              f"under {root}.")
        return 0

    print(
        f"⚠️  {len(hits)} reintroduction(s) of hardcoded "
        f"DEFAULT_ALERTS/ALERT_RULES_BANK detected.\n\n"
        f"Audit 2026-05-20 Sprint 3 F6: catalogo alert rules deve vir do hook\n"
        f"useAlertRuleTemplates (canonical per-tenant via DB), nao de file\n"
        f"hardcoded. Se voce realmente precisa de uma lista master estatica,\n"
        f"adicione o arquivo ao ALLOWLIST do sensor com justificativa.\n"
        f"\n"
        f"Para criar templates per-tenant, use a tool wizard:\n"
        f"  create_custom_alert_rule_template via communication agent\n"
        f"  ou POST /api/backend-proxy/alert-rule-templates direto.\n"
    )
    for path, line_no, snippet in hits:
        print(f"── {path.relative_to(root.parent)}:{line_no}")
        print(f"   {snippet[:120]}")
        print()

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
