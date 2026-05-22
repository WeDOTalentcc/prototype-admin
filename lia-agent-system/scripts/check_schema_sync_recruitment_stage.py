"""WT-2022: AST sensor de schema-sync RecruitmentStage TS<->Python.

Detecta drift entre os 2 shapes TS de RecruitmentStage que coexistem
(legacy camelCase vs canonical snake_case). O adapter
`normalizeStageFromHook` em `use-recruitment-stages.ts` depende dessa
consistencia: se um lado adicionar field sem espelhar no outro, kanban
ou settings podem renderizar undefined.

Surfaces monitoradas:
- Frontend legacy: plataforma-lia/src/lib/recruitment/stages-data.ts
  (interface RecruitmentStage, camelCase: displayName/stageOrder/stageType)
- Frontend canonical: plataforma-lia/src/components/settings/recruitment-journey.types.ts
  (interface RecruitmentStage, snake_case: display_name/order/type)

Conforme CLAUDE.md secao "Schema-sync TS<->Python": adicionar field em
um exige espelho no outro. Sensor warn-only inicial (shapes podem evoluir
em sprints separadas), ratchet pra blocking quando baseline = 0.

Pattern: extracao por regex (nao TS parser completo) - suficiente pra
shape contract enforcement em interface simples.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
FE_LEGACY = ROOT / "plataforma-lia/src/lib/recruitment/stages-data.ts"
FE_CANONICAL = ROOT / "plataforma-lia/src/components/settings/recruitment-journey.types.ts"

# Fields REQUIRED em cada lado (lista cuidadosamente curada do adapter
# `normalizeStageFromHook` - se aparecer aqui = adapter le esse field).
LEGACY_REQUIRED_FIELDS = {
    "name",
    "displayName",
    "stageOrder",
    "stageType",
    "isInitial",
    "isFinal",
    "stageCategory",
}
CANONICAL_REQUIRED_FIELDS = {
    "name",
    "display_name",
    "order",
    "type",
    "isActive",
}

# Pareamento adapter (legacy <- canonical). Se canonical perder o field
# do RHS, adapter quebra. Validamos que ambos os lados existem.
ADAPTER_PAIRINGS = {
    "displayName": "display_name",
    "stageOrder": "order",
    "stageType": "type",
}


def extract_ts_interface_fields(ts_file: pathlib.Path, interface_name: str) -> set[str]:
    """Extrai field names de `interface <Name> { ... }`.

    Regex-based (nao TS parser). Suficiente pra interface single-level.
    Retorna set vazio se arquivo nao existe ou interface nao encontrada
    (sinaliza problema visivel no relatorio).
    """
    if not ts_file.exists():
        return set()
    content = ts_file.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"(?:export\s+)?interface\s+{interface_name}\s*\{{([^}}]+)\}}",
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        return set()
    body = match.group(1)
    # Captura `name:` ou `name?:` (com optional). Ignora linhas comentario.
    field_pattern = re.compile(r"^\s*(\w+)\s*\??\s*:", re.MULTILINE)
    fields: set[str] = set()
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("*"):
            continue
        m = field_pattern.match(line)
        if m:
            fields.add(m.group(1))
    return fields


def main() -> int:
    if not FE_LEGACY.exists():
        print(
            f"WT-2022 SCHEMA-SYNC: FE_LEGACY nao encontrado em {FE_LEGACY}",
            file=sys.stderr,
        )
        return 0  # warn-only
    if not FE_CANONICAL.exists():
        print(
            f"WT-2022 SCHEMA-SYNC: FE_CANONICAL nao encontrado em {FE_CANONICAL}",
            file=sys.stderr,
        )
        return 0

    legacy_fields = extract_ts_interface_fields(FE_LEGACY, "RecruitmentStage")
    canonical_fields = extract_ts_interface_fields(FE_CANONICAL, "RecruitmentStage")

    issues: list[str] = []

    legacy_missing = LEGACY_REQUIRED_FIELDS - legacy_fields
    if legacy_missing:
        issues.append(
            f"FE_LEGACY ({FE_LEGACY.name}) RecruitmentStage missing required fields: "
            f"{sorted(legacy_missing)}"
        )

    canonical_missing = CANONICAL_REQUIRED_FIELDS - canonical_fields
    if canonical_missing:
        issues.append(
            f"FE_CANONICAL ({FE_CANONICAL.name}) RecruitmentStage missing required fields: "
            f"{sorted(canonical_missing)}"
        )

    # Adapter pairing: cada legacy field tem canonical correspondente?
    for legacy_field, canonical_field in ADAPTER_PAIRINGS.items():
        if legacy_field in legacy_fields and canonical_field not in canonical_fields:
            issues.append(
                f"ADAPTER DRIFT: legacy.{legacy_field} existe mas "
                f"canonical.{canonical_field} ausente. normalizeStageFromHook "
                f"vai produzir undefined em canonical->legacy mapping."
            )
        if canonical_field in canonical_fields and legacy_field not in legacy_fields:
            issues.append(
                f"ADAPTER DRIFT: canonical.{canonical_field} existe mas "
                f"legacy.{legacy_field} ausente. Adapter nao tem destino "
                f"pra renderizar field canonical."
            )

    if issues:
        print(f"WT-2022 SCHEMA-SYNC: {len(issues)} issue(s) (modo=WARN-ONLY):")
        for issue in issues:
            print(f"  - {issue}")
        print(
            "\nFix: adicionar field espelhando em ambos arquivos OU atualizar "
            "ADAPTER_PAIRINGS/REQUIRED_FIELDS deste sensor se foi mudanca intencional."
        )
        return 0  # warn-only ate ratchet

    print("OK: RecruitmentStage schema-sync TS<->TS consistente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
