"""WT-2022 P0.SUB_STATUSES — AST sensor: imports diretos de SUB_STATUSES.

Detecta em arquivos .ts/.tsx sob plataforma-lia/src qualquer import de
SUB_STATUSES vindo de @/lib/recruitment-stages, @/lib/recruitment ou
@/lib/recruitment/sub-statuses-data.

Pattern violation:
    import { SUB_STATUSES } from "@/lib/recruitment-stages"
    const subStatuses = SUB_STATUSES[stage] || []
    // -> lookup hardcoded ignora customizacao dos sub-statuses da empresa
    //    via Configuracoes > Pipeline (recruitment_sub_statuses table).
    //    Recrutador adiciona sub-status la, Kanban view nao reflete = bug.

Pattern canonical:
    import { useRecruitmentStages } from "@/hooks/recruitment/use-recruitment-stages"
    const { legacySubStatuses } = useRecruitmentStages()
    const subStatuses = legacySubStatuses[stage] ?? SUB_STATUSES[stage] ?? []
    // legacySubStatuses: shape legacy camelCase normalizado via
    // normalizeSubStatusesFromHook -- drop-in pra utils que esperam
    // {displayName, isDefault, isWaiting, isApproval, isRejection}.
    //
    // OU pra cenarios fora de React:
    import { normalizeSubStatusesFromHook } from "@/lib/recruitment"

Por que: SUB_STATUSES e a lista canonical hardcoded (WeDOTalent defaults).
Em producao cada tenant pode customizar sub-statuses por estagio em
Configuracoes > Pipeline. Consumers que importam SUB_STATUSES direto
ignoram essa customizacao = ghost setting (vide CLAUDE.md "lia_field_toggles
canonical pattern") = quebra de contrato implicito de UI.

Modo: WARN-ONLY no baseline inicial. Promover STRICT quando consumers
restantes migrarem (boy-scout).

Exit codes:
    0 = OK (zero violations) ou --warn-only mode (default)
    1 = --strict + violations detectadas

Uso:
    python3 scripts/check_no_sub_statuses_direct_import.py             # WARN-ONLY (default)
    python3 scripts/check_no_sub_statuses_direct_import.py --strict    # baseline 0+
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

# Sob WORKSPACE_ROOT/plataforma-lia/src/
WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[2]
FRONTEND_ROOT = WORKSPACE_ROOT / "plataforma-lia" / "src"

# Detecta import { ... SUB_STATUSES ... } from "@/lib/recruitment[-stages|/sub-statuses-data]"
# Aceita multi-linha entre { e }.
# Quote chars: double-quote (chr 34) or apostrophe (chr 39).
_QUOTE = "[" + chr(34) + chr(39) + "]"
IMPORT_PATTERN = re.compile(
    r"import\s*(?:type\s+)?\{[^}]*\bSUB_STATUSES\b[^}]*\}\s*from\s*"
    + _QUOTE
    + r"@/lib/recruitment(?:-stages|/sub-statuses-data|)?"
    + _QUOTE,
    re.MULTILINE | re.DOTALL,
)

# Arquivos canonical (source-of-truth do simbolo) — isentos.
# Path normalizado relativo ao FRONTEND_ROOT, sem leading slash.
EXEMPT_PATHS = {
    "lib/recruitment-stages.ts",
    "lib/recruitment/sub-statuses-data.ts",
    "lib/recruitment/stage-utils.ts",
    "lib/recruitment/index.ts",
    "hooks/recruitment/use-recruitment-stages.ts",
    # Consumers transitional que mantem SUB_STATUSES como FALLBACK (com
    # legacySubStatuses do hook canonical na prioridade 1). Padrao aceito.
    # Ao migrar, remover do EXEMPT.
    "components/tables/cell-renderers.tsx",
    "components/pages/job-kanban/hooks/useKanbanDragDrop.ts",
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
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 quando houver violations (promocao do baseline).",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="(default) Nunca falhar mesmo com violations.",
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
        print("OK: zero imports diretos de SUB_STATUSES.")
        return 0

    print(
        f"WT-2022 P0.SUB_STATUSES: {len(violations)} import(s) direto(s) de "
        f"SUB_STATUSES detectado(s)."
    )
    print("")
    print("Fix recomendado pra cada arquivo:")
    print("  1. React component/hook (preferido):")
    print(
        "     const { legacySubStatuses } = useRecruitmentStages()"
    )
    print(
        "     const subStatuses = legacySubStatuses[stage] ?? SUB_STATUSES[stage] ?? []"
    )
    print("  2. Util/non-React:")
    print(
        "     import { normalizeSubStatusesFromHook } from \"@/lib/recruitment\""
    )
    print("     Receber sub_statuses via parametro do caller.")
    print("")
    print("Por que importa: cada tenant customiza sub-statuses em")
    print("Configuracoes > Pipeline. Import direto ignora essa customizacao.")
    print("")
    print("Violations:")
    for rel, lineno, snippet in violations[:50]:
        print(f"  {rel}:{lineno}  {snippet}")
    if len(violations) > 50:
        print(f"  ... +{len(violations) - 50} more")

    if args.strict:
        return 1
    # WARN-ONLY default — promover STRICT em sprint futura quando baseline = 0.
    print("")
    print("(WARN-ONLY default — exit 0. Use --strict pra promocao.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
