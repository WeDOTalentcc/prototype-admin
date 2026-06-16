#!/usr/bin/env python3
"""
check_subapp_monolith_imports.py — Sensor de débito técnico Sprint G6.

Detecta importações do monolito (`from app.*`) nos sub-apps
(apps/api-onboarding, apps/api-funil, apps/api-vagas).

Categorias:
  infra    — app.core.*, app.config.*, app.middleware.*, app.shared.pii_masking
             Candidatos à migração para libs/ (infra portátil)
  routes   — app.api.v1.*
             Núcleo do strangler fig — diferir, são as rotas de domínio
  domains  — app.domains.*
             Lógica de domínio — diferir para após extração de bounded contexts

Modo: informativo (não blocking) — sensor de rastreamento de dívida técnica.
Exit 0 sempre. Use --summary para output compacto.

Usage:
    python3 scripts/check_subapp_monolith_imports.py
    python3 scripts/check_subapp_monolith_imports.py --summary
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

APPS_ROOT = Path(__file__).parent.parent / "apps"

SUBAPPS = ["api-onboarding", "api-funil", "api-vagas"]

# Prefixos que definem a categoria
INFRA_PREFIXES = (
    "app.core.",
    "app.config.",
    "app.middleware.",
    "app.shared.pii_masking",
)

ROUTES_PREFIXES = (
    "app.api.",
)

DOMAINS_PREFIXES = (
    "app.domains.",
)

# ---------------------------------------------------------------------------
# Heurística: tem equivalente em libs/?
# ---------------------------------------------------------------------------

LIBS_EQUIV = {
    # Tem equivalente confirmado em libs/
    "app.core.config": True,           # libs/config/lia_config/config.py exporta `settings`
    "app.core.database": True,         # libs/config/lia_config/database.py exporta init_db
    # Sem equivalente confirmado em libs/
    "app.core.sentry": False,
    "app.core.logging_config": False,
    "app.core.logging_middleware": False,
    "app.shared.pii_masking": False,
    "app.config.langsmith": False,
    "app.middleware.rate_limiter": False,
    "app.middleware.request_id": False,
}


def _has_lib_equivalent(module: str) -> bool:
    """True se sabemos que há equivalente em libs/."""
    return LIBS_EQUIV.get(module, False)


# ---------------------------------------------------------------------------
# Parser de importações
# ---------------------------------------------------------------------------

def extract_from_app_imports(filepath: Path) -> list:
    """Retorna lista de módulos importados via `from app.X import Y`."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, OSError) as e:
        print("  [WARN] Nao foi possivel parsear {}: {}".format(filepath, e), file=sys.stderr)
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("app."):
                imports.append(module)
    return imports


def categorize(module: str) -> str:
    """Classifica o módulo em infra / routes / domains / other."""
    if module.startswith(INFRA_PREFIXES):
        return "infra"
    if module.startswith(ROUTES_PREFIXES):
        return "routes"
    if module.startswith(DOMAINS_PREFIXES):
        return "domains"
    return "other"


# ---------------------------------------------------------------------------
# Scan principal
# ---------------------------------------------------------------------------

def scan_subapp(subapp_name: str) -> dict:
    """Varre todos os .py de um sub-app. Retorna breakdown por categoria."""
    subapp_dir = APPS_ROOT / subapp_name
    if not subapp_dir.exists():
        return {"error": "Diretorio nao encontrado: {}".format(subapp_dir)}

    py_files = sorted(subapp_dir.rglob("*.py"))
    py_files = [f for f in py_files if "__pycache__" not in str(f)]

    breakdown = defaultdict(list)  # category -> [(file, module)]

    for filepath in py_files:
        imports = extract_from_app_imports(filepath)
        for module in imports:
            category = categorize(module)
            rel_path = filepath.relative_to(APPS_ROOT.parent)
            breakdown[category].append((str(rel_path), module))

    return dict(breakdown)


def main():
    summary_mode = "--summary" in sys.argv

    print("=" * 70)
    print("SENSOR: check_subapp_monolith_imports -- Sprint G6")
    print("Rastreia importacoes do monolito (from app.*) nos sub-apps")
    print("=" * 70)
    print()

    grand_total = 0
    grand_by_category = defaultdict(int)

    for subapp in SUBAPPS:
        breakdown = scan_subapp(subapp)

        if "error" in breakdown:
            print("[ERRO] {}: {}".format(subapp, breakdown["error"]))
            continue

        total = sum(len(v) for v in breakdown.values())
        grand_total += total

        print("  {} ({} imports do monolito)".format(subapp, total))
        print("-" * 50)

        for category in ["infra", "routes", "domains", "other"]:
            entries = breakdown.get(category, [])
            count = len(entries)
            grand_by_category[category] += count

            if count == 0:
                continue

            label_map = {
                "infra":   "infra   (candidatos libs/)",
                "routes":  "routes  (strangler fig -- diferir)",
                "domains": "domains (bounded ctx -- diferir)",
                "other":   "other   (revisar manualmente)",
            }
            label = label_map.get(category, category)
            print("  {}: {}".format(label, count))

            if not summary_mode:
                # Agrupa por arquivo para leitura mais limpa
                by_file = defaultdict(list)
                for filepath, module in entries:
                    by_file[filepath].append(module)

                for filepath, modules in sorted(by_file.items()):
                    print("    {}".format(filepath))
                    for m in modules:
                        has_lib_equiv = _has_lib_equivalent(m)
                        marker = "" if has_lib_equiv else "  # MONOLITH-IMPORT: needs lib extraction"
                        print("      from {} import ...{}".format(m, marker))

        print()

    # ---------------------------------------------------------------------------
    # Resumo global
    # ---------------------------------------------------------------------------
    print("=" * 70)
    print("TOTAIS GLOBAIS: {} imports do monolito em {} sub-apps".format(grand_total, len(SUBAPPS)))
    print("-" * 50)
    for category in ["infra", "routes", "domains", "other"]:
        count = grand_by_category.get(category, 0)
        if count > 0:
            print("  {:8s}: {:3d}".format(category, count))
    print("=" * 70)
    print()
    print("GUIA de acao:")
    print("  infra   -> verificar equivalente em libs/; marcar MONOLITH-IMPORT se ausente")
    print("  routes  -> strangler fig gradual (nao forcar agora)")
    print("  domains -> bounded context extraction (sprint futuro)")
    print()
    print("Exit: 0 (sensor informativo -- nao blocking)")
    # Sempre exit 0 -- eh sensor de rastreamento, nao blocking
    sys.exit(0)


if __name__ == "__main__":
    main()
