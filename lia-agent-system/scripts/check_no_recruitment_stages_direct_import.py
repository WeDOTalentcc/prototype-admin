"""WT-2022 P0.STAGES — AST sensor: imports diretos de RECRUITMENT_STAGES.

Detecta em arquivos .ts/.tsx sob plataforma-lia/src qualquer import de
RECRUITMENT_STAGES vindo de @/lib/recruitment-stages ou @/lib/recruitment.

Pattern violation:
    import { RECRUITMENT_STAGES } from "@/lib/recruitment-stages"
    const stages = RECRUITMENT_STAGES
    // -> lookup hardcoded ignora customizacao do pipeline da empresa
    //    via /api/backend-proxy/company-pipeline

Pattern canonical:
    import { useRecruitmentStages } from "@/hooks/recruitment/use-recruitment-stages"
    const { legacyStages } = useRecruitmentStages()
    // legacyStages: shape legacy camelCase normalizado via
    // normalizeStagesFromHook -- drop-in pra utils que esperam
    // {displayName, stageOrder, stageType, isInitial, ...}
    //
    // OU pra cenarios fora de React:
    import { normalizeStagesFromHook } from "@/lib/recruitment/stages-data"

Por que: RECRUITMENT_STAGES e a lista canonical hardcoded (WeDOTalent
defaults). Em produção cada tenant pode customizar pipeline via
Configuracoes > Jornada de Recrutamento. Consumers que importam direto
ignoram essa customizacao = bug silencioso.

Modo: STRICT por default (promovido 2026-05-21 — baseline 0 sustentado).
Use --warn-only pra exit-0 mesmo com violations (rollback emergencial).

Exit codes:
    0 = OK (zero violations) ou --warn-only mode
    1 = STRICT default + violations detectadas

Uso:
    python3 scripts/check_no_recruitment_stages_direct_import.py           # STRICT (default)
    python3 scripts/check_no_recruitment_stages_direct_import.py --warn-only  # legacy
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

# Sob WORKSPACE_ROOT/plataforma-lia/src/
WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[2]
FRONTEND_ROOT = WORKSPACE_ROOT / "plataforma-lia" / "src"

# Detecta import { ... RECRUITMENT_STAGES ... } from "@/lib/recruitment[-stages]"
# Aceita multi-linha entre { e }.
# Quote chars: double-quote (chr 34) or apostrophe (chr 39).
_QUOTE = "[" + chr(34) + chr(39) + "]"
IMPORT_PATTERN = re.compile(
    r"import\s*(?:type\s+)?\{[^}]*\bRECRUITMENT_STAGES\b[^}]*\}\s*from\s*"
    + _QUOTE
    + r"@/lib/recruitment(?:-stages)?"
    + _QUOTE,
    re.MULTILINE | re.DOTALL,
)

# Arquivos canonical (source-of-truth do simbolo) — isentos.
# Path normalizado relativo ao FRONTEND_ROOT, sem leading slash.
EXEMPT_PATHS = {
    "lib/recruitment-stages.ts",
    "lib/recruitment/stages-data.ts",
    "lib/recruitment/stage-utils.ts",
    "lib/recruitment/index.ts",
    "hooks/recruitment/use-recruitment-stages.ts",
}


def is_exempt(rel_path: str) -> bool:
    return rel_path in EXEMPT_PATHS


def find_violations(root: pathlib.Path):
    """Yield (rel_path, lineno, snippet) tuples."""
    for ts_file in root.rglob("*.ts"):
        yield from _scan_file(ts_file, root)
    for tsx_file in root.rglob("*.tsx"):
        yield from _scan_file(tsx_file, root)


def _scan_file(path: pathlib.Path, root: pathlib.Path):
    rel = str(path.relative_to(root)).replace("\\\\", "/")
    if is_exempt(rel):
        return
    # Skip tests (consumers reais sao components/hooks, nao tests)
    if "/__tests__/" in rel or rel.endswith(".test.ts") or rel.endswith(".test.tsx"):
        return
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    for match in IMPORT_PATTERN.finditer(content):
        lineno = content[: match.start()].count("\n") + 1
        snippet = match.group(0).replace("\n", " ").strip()
        if len(snippet) > 160:
            snippet = snippet[:160] + "..."
        yield (rel, lineno, snippet)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    # WT-2022 P0.STAGES — promovido warn-only → STRICT em 2026-05-21
    # (baseline 0 sustentado, 10 consumers migrados). Mantemos --warn-only
    # flag pra rollback emergencial caso violation legitima de boy-scout
    # precise ser merged enquanto fix nao landa.
    parser.add_argument(
        "--strict",
        action="store_true",
        help="(deprecated, agora default) Exit 1 quando houver violations.",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Legacy: nunca falhar mesmo com violations (rollback emergencial).",
    )
    args = parser.parse_args()

    if not FRONTEND_ROOT.exists():
        print(
            f"WARN: frontend root nao existe: {FRONTEND_ROOT}",
            file=sys.stderr,
        )
        return 0

    violations = list(find_violations(FRONTEND_ROOT))

    if not violations:
        print("OK: zero imports diretos de RECRUITMENT_STAGES.")
        return 0

    print(
        f"WT-2022 P0.STAGES: {len(violations)} import(s) direto(s) de "
        f"RECRUITMENT_STAGES detectado(s)."
    )
    print("")
    print("Fix recomendado pra cada arquivo:")
    print("  1. React component/hook:")
    print(
        "     const { legacyStages } = useRecruitmentStages()"
        "  // pipeline da empresa"
    )
    print("  2. Util/non-React:")
    print(
        "     import { normalizeStagesFromHook } from \"@/lib/recruitment/stages-data\""
    )
    print("     Receber stages via parametro do caller (ja segue pattern).")
    print("")
    print("Violations:")
    for rel, lineno, snippet in violations[:50]:
        print(f"  {rel}:{lineno}  {snippet}")
    if len(violations) > 50:
        print(f"  ... +{len(violations) - 50} more")

    if args.warn_only:
        print("")
        print("(--warn-only flag — exit 0; promover para strict ASAP)")
        return 0
    # STRICT default desde 2026-05-21 (WT-2022 ratchet promotion).
    return 1


if __name__ == "__main__":
    sys.exit(main())
