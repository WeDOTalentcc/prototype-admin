#!/usr/bin/env python3
"""
SENSOR canonical (harness-engineering): detect re-introducao de catalogo
hardcoded de webhook events no frontend.

Audit 2026-05-20 Sprint 5 F6 — catalogo agora e per-tenant via DB
(webhook_event_types) + endpoint canonical (/api/v1/webhook-event-types)
+ hook useWebhookEventTypes. A constante array `WEBHOOK_EVENTS` em
`plataforma-lia/.../webhook-types.ts` foi REMOVIDA; o arquivo agora
contem apenas o interface `Webhook` (shape do recurso studio_webhooks).

Qualquer reintroducao de:
  - constante `WEBHOOK_EVENTS` em src/ (export const WEBHOOK_EVENTS = [...])
  - constante `WebhookEvent` (type union de string literals com .* events)
  - import direto de `from .../webhook-types` em arquivos NAO na allowlist
    (alem do `Webhook` interface canonical permitido)

deve ser flagada.

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
import re
import sys
from pathlib import Path

# Forbidden constant names (case-sensitive)
FORBIDDEN_CONSTANTS = (
    "WEBHOOK_EVENTS",
)

# Forbidden import patterns — apenas allowlist pode importar de webhook-types.ts
FORBIDDEN_IMPORT_PATTERNS = (
    re.compile(r"""from\s+['"][^'"]*webhook-types['"]"""),
)

# Files allowed to import or reference webhook-types.
# Canonical hook + the file itself + WebhooksManager (consumer canonical da
# Webhook interface) + use-webhooks (mantém o type import canonical).
ALLOWLIST = {
    "components/pages-agent-studio/custom-agents/webhook-types.ts",
    "components/settings/WebhooksManager.tsx",
    "hooks/agents/use-webhooks.ts",
    "hooks/webhooks/use-webhook-event-types.ts",
}

# Constants allowed to appear in the file itself (the deprecation note may
# reference them). Other files NOT in ALLOWLIST should never mention WEBHOOK_EVENTS.
SKIP_DIR_FRAGMENTS = (
    "/node_modules/", "/.next/", "/dist/", "/__tests__/",
    ".test.", ".spec.", "/.bak/",
)


def find_hits(root: Path) -> list[tuple[Path, int, str, str]]:
    """Return (path, line_no, snippet, kind)."""
    hits: list[tuple[Path, int, str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in (".ts", ".tsx", ".js", ".jsx"):
            continue
        if any(skip in str(path) for skip in SKIP_DIR_FRAGMENTS):
            continue
        rel = str(path.relative_to(root))
        is_allowlisted = rel in ALLOWLIST
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for line_no, line in enumerate(source.splitlines(), start=1):
            stripped = line.strip()
            # Skip pure comment lines
            if stripped.startswith(("//", "*", "/*")):
                continue

            # Forbidden import patterns
            if not is_allowlisted:
                for pat in FORBIDDEN_IMPORT_PATTERNS:
                    if pat.search(line):
                        hits.append((path, line_no, line.strip(), "import"))
                        break

            # Forbidden constants — anywhere outside the canonical file itself
            if rel != "components/pages-agent-studio/custom-agents/webhook-types.ts":
                for name in FORBIDDEN_CONSTANTS:
                    # only flag declarations / array usages, not type-only
                    if name in line and (
                        "const " in line
                        or "let " in line
                        or "var " in line
                        or "export " in line
                        or "[" in line
                    ):
                        hits.append((path, line_no, line.strip(), "constant"))
                        break

    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect reintroduction of hardcoded webhook events catalog."
    )
    parser.add_argument(
        "--root",
        default="../plataforma-lia/src",
        help="Root dir to scan (default: ../plataforma-lia/src).",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 even if violations found.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        # fallback canonical path
        alt = Path("/home/runner/workspace/plataforma-lia/src").resolve()
        if alt.exists():
            root = alt
        else:
            print(f"Error: --root {root} does not exist", file=sys.stderr)
            return 2

    hits = find_hits(root)
    if not hits:
        print(
            f"✅ No hardcoded webhook events catalog detected under {root}."
        )
        return 0

    print(
        f"⚠️  {len(hits)} reintroduction(s) of hardcoded WEBHOOK_EVENTS / "
        f"webhook-types imports detected.\n\n"
        f"Audit 2026-05-20 Sprint 5 F6: catalogo webhook events deve vir do hook\n"
        f"useWebhookEventTypes() (canonical per-tenant via DB), nao de file\n"
        f"hardcoded. Se voce realmente precisa importar de webhook-types.ts,\n"
        f"adicione o arquivo ao ALLOWLIST do sensor com justificativa.\n"
        f"Para criar novos events: use tool wizard `create_custom_webhook_event_type`\n"
        f"OU migration alembic (vide 157_webhook_event_types.py).\n"
    )
    for path, line_no, snippet, kind in hits:
        try:
            rel = path.relative_to(root.parent)
        except ValueError:
            rel = path
        print(f"── [{kind}] {rel}:{line_no}")
        print(f"   {snippet[:140]}")
        print()

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
