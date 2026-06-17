#!/usr/bin/env python3
"""
SENSOR canonical (harness-engineering): detect re-introducao de catalogo
hardcoded de integracoes no frontend.

Audit 2026-05-20 Sprint 4 F6 — catalogo agora e per-tenant via DB
(integration_catalog_entries) + endpoints canonical em
/api/v1/integration-catalog + hook useIntegrationCatalog em
src/hooks/integrations/use-integration-catalog.ts. O arquivo legacy
`integration-data.ts` esta marcado @deprecated, em fallback controlado,
mas qualquer reintroducao de constantes INTEGRATIONS_CATALOG /
INTEGRATION_PROVIDERS / novos imports diretos do arquivo legacy fora
da ALLOWLIST canonical deve ser flagada.

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

# Constantes proibidas de reaparecer no frontend (qualquer arquivo .ts/.tsx)
FORBIDDEN_NAMES = (
    "INTEGRATIONS_CATALOG",
    "INTEGRATION_PROVIDERS",
)

# Imports diretos do arquivo legacy. Permitidos APENAS para arquivos na ALLOWLIST.
FORBIDDEN_IMPORT_PATTERNS = (
    'from "@/components/settings/integrations/integration-data"',
    "from '@/components/settings/integrations/integration-data'",
    'from "./integration-data"',
    "from './integration-data'",
    'from "./integrations/integration-data"',
    "from './integrations/integration-data'",
    'from "../integrations/integration-data"',
    "from '../integrations/integration-data'",
)

# Arquivos canonical que tem permissao de tocar o file legacy enquanto a
# migracao Sprint 4 esta em curso. Adicionar novos arquivos a esta lista
# exige justificativa documentada em comentario PR.
ALLOWLIST = {
    # Hook canonical (consome catalogo dinamico, importa types do legacy
    # apenas para compat de shape Integration durante migracao)
    "hooks/integrations/use-integration-catalog.ts",
    # Consumers legados (refatorados Sprint 4 F4 com fallback canonical)
    "components/settings/IntegrationsHub.tsx",
    "components/settings/integrations/IntegrationCard.tsx",
    "components/settings/integrations/IntegrationDetailDrawer.tsx",
    # O proprio arquivo legacy
    "components/settings/integrations/integration-data.ts",
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
        in_allowlist = rel in ALLOWLIST
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_no, line in enumerate(source.splitlines(), start=1):
            # Forbidden imports — flag only outside allowlist
            matched_import = False
            if not in_allowlist:
                for forbidden_imp in FORBIDDEN_IMPORT_PATTERNS:
                    if forbidden_imp in line:
                        hits.append((path, line_no, line.strip()))
                        matched_import = True
                        break
            if matched_import:
                continue
            # Forbidden constants (INTEGRATIONS_CATALOG / INTEGRATION_PROVIDERS):
            # flagged anywhere except if defined or re-exported inside an allowlisted file
            for forbidden_name in FORBIDDEN_NAMES:
                if forbidden_name not in line:
                    continue
                # Heuristic: comment-only references skipped
                idx = line.find(forbidden_name)
                prefix = line[:idx]
                if "//" in prefix or "*" in prefix.strip()[:1] if prefix.strip() else False:
                    continue
                # If line is an import binding from the legacy file, already flagged above
                if "from" in line and "integration-data" in line and in_allowlist:
                    # allowed type import inside allowlisted file
                    continue
                hits.append((path, line_no, line.strip()))
                break
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect reintroducao de catalogo hardcoded de integracoes."
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
        alt = Path("/home/runner/workspace/plataforma-lia/src").resolve()
        if alt.exists():
            root = alt
        else:
            print(f"Error: --root {root} does not exist", file=sys.stderr)
            return 2

    hits = find_hits(root)
    if not hits:
        print(
            f"OK: nenhum catalogo hardcoded de integracoes detectado "
            f"sob {root}."
        )
        return 0

    print(
        f"AVISO: {len(hits)} reintroducao(oes) de catalogo hardcoded de "
        f"integracoes detectada(s).\n\n"
        f"Audit 2026-05-20 Sprint 4 F6: catalogo de integracoes DEVE vir do\n"
        f"hook useIntegrationCatalog (canonical per-tenant via DB), nao de\n"
        f"file hardcoded. Para consumir integracoes no frontend use:\n"
        f"  import {{ useIntegrationCatalog }}\n"
        f"  from '@/hooks/integrations/use-integration-catalog'\n\n"
        f"Se voce realmente precisa de uma referencia ao legacy\n"
        f"integration-data.ts (ex: compat de tipo durante migracao),\n"
        f"adicione o arquivo ao ALLOWLIST do sensor com justificativa.\n"
    )
    for path, line_no, snippet in hits:
        print(f"-- {path.relative_to(root.parent)}:{line_no}")
        print(f"   {snippet[:120]}")
        print()

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
