#!/usr/bin/env python3
"""Sensor: CanonicalPipelineStage Python ↔ TypeScript interface estão em sync.

Verifica que:
1. Os campos core de CanonicalPipelineStage (Python TypedDict em app/shared/types.py)
   existem na interface PipelineStage do TypeScript (src/hooks/pipeline/use-pipeline-templates.ts)
2. Nenhum campo core novo no Python ficou sem espelho no TS (drift prevention)

Sensor computacional (AST-free, regex) — barato e direto.
Exit 0 = sync OK. Exit 1 = drift detectado + fix instructions.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent  # lia-agent-system/

# ─── Source of truth: campos core do CanonicalPipelineStage ────────────────
CORE_FIELDS = {"name", "order", "type", "sla_days", "instructions"}

# ─── TypeScript file com a interface PipelineStage ─────────────────────────
TS_FILES = [
    "../plataforma-lia/src/hooks/pipeline/use-pipeline-templates.ts",
    "../plataforma-lia/src/types/pipeline-stage.types.ts",
]

def main() -> int:
    violations = []

    # 1. Confirmar que CORE_FIELDS existem em app/shared/types.py
    types_py = ROOT / "app/shared/types.py"
    if not types_py.exists():
        violations.append(f"[{types_py}] não encontrado")
    else:
        content = types_py.read_text(encoding="utf-8")
        if "CanonicalPipelineStage" not in content:
            violations.append(f"[{types_py}] CanonicalPipelineStage não encontrado")
        for field in CORE_FIELDS:
            # Verifica "field: type" dentro do bloco CanonicalPipelineStage
            if not re.search(rf'\b{field}\s*:', content):
                violations.append(
                    f"[{types_py}] campo core '{field}' ausente em CanonicalPipelineStage\n"
                    f"  → Fix: adicionar '{field}: <tipo>' ao TypedDict CanonicalPipelineStage"
                )

    # 2. Verificar que campos core existem na interface TS
    ts_found = None
    for ts_rel in TS_FILES:
        ts_file = ROOT / ts_rel
        if ts_file.exists():
            ts_found = ts_file
            break

    if ts_found is None:
        violations.append(
            f"Nenhum arquivo TS encontrado em {TS_FILES}\n"
            f"  → Fix: criar plataforma-lia/src/types/pipeline-stage.types.ts com "
            f"interface PipelineStage com campos {sorted(CORE_FIELDS)}"
        )
    else:
        ts_content = ts_found.read_text(encoding="utf-8")
        # TS usa sla_days ou slaDays (camelCase)
        ts_field_map = {
            "name": "name",
            "order": "order",
            "type": "type",
            "sla_days": ["sla_days", "slaDays"],
            "instructions": "instructions",
        }
        for py_field, ts_variants in ts_field_map.items():
            variants = [ts_variants] if isinstance(ts_variants, str) else ts_variants
            if not any(re.search(rf'\b{v}\s*[?:]', ts_content) for v in variants):
                violations.append(
                    f"[{ts_found}] campo '{py_field}' (ou variante camelCase) ausente\n"
                    f"  → Fix: adicionar '{py_field}?: ...' à interface PipelineStage"
                )

    if violations:
        print(f"❌ Pipeline stage schema DRIFT detectado — {len(violations)} violation(s):\n")
        for v in violations:
            print(f"  {v}\n")
        return 1

    print(f"✅ CanonicalPipelineStage Python ↔ TypeScript: sync OK ({len(CORE_FIELDS)} campos core)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
