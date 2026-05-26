#!/usr/bin/env python3
"""
Sensor PR-8 / F-3.2: valida que entries em STAGE_TOOLS seguem convencao
canonical layered (kebab=creation, snake=lifecycle).

Background: STAGE_TOOLS dict em
app/domains/job_management/agents/wizard_tool_registry.py mistura 2
convencoes por design (nao bug -- ADR documentada inline + CLAUDE.md).
Mas misturar dentro da MESMA camada (ex: adicionar "pipeline_template"
snake quando convencao e kebab "pipeline-template") gera drift.

Esse sensor:
1. Identifica conjunto canonical de stages KEBAB (wizard creation)
2. Identifica conjunto canonical de stages SNAKE (lifecycle Phase E)
3. Qualquer entry FORA dos 2 conjuntos = violation (nome novo precisa
   decidir camada explicitamente + atualizar canonical set abaixo)
4. Qualquer entry que tenha "_" E "-" (mistura) = violation

Mode: warn-only por default. --blocking para CI gate.
"""

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Canonical sets (atualizar quando adicionar stages -- sensor e
# guardrail, nao cego)
CANONICAL_KEBAB_CREATION = {
    "input-evaluation",
    "jd-enrichment",
    "pipeline-template",
    "salary",
    "competencies",
    "wsi-questions",
    "review-publish",
}

CANONICAL_SNAKE_LIFECYCLE = {
    "enriquecida",
    "wsi_config",
    "aguardando_aprovacao",
    "publicada",
    "ao_vivo",
}

REGISTRY_FILE = (
    PROJECT_ROOT
    / "app/domains/job_management/agents/wizard_tool_registry.py"
)


def main() -> int:
    source = REGISTRY_FILE.read_text()
    tree = ast.parse(source)

    violations: list[str] = []
    found_keys: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.AnnAssign):
            if not isinstance(node, ast.Assign):
                continue
            targets = node.targets
        else:
            targets = [node.target]

        for target in targets:
            if not (isinstance(target, ast.Name) and target.id == "STAGE_TOOLS"):
                continue
            value = node.value
            if not isinstance(value, ast.Dict):
                continue
            for key_node in value.keys:
                if not (
                    isinstance(key_node, ast.Constant)
                    and isinstance(key_node.value, str)
                ):
                    continue
                key = key_node.value
                found_keys.add(key)

                has_underscore = "_" in key
                has_dash = "-" in key

                if has_underscore and has_dash:
                    violations.append(
                        f"STAGE_TOOLS[{key!r}]: mistura kebab+snake na MESMA "
                        f"entry. Decidir convencao: kebab (creation) OU snake "
                        f"(lifecycle). Renomeie."
                    )
                    continue

                if key in CANONICAL_KEBAB_CREATION:
                    continue
                if key in CANONICAL_SNAKE_LIFECYCLE:
                    continue

                violations.append(
                    f"STAGE_TOOLS[{key!r}]: nao esta em "
                    f"CANONICAL_KEBAB_CREATION nem CANONICAL_SNAKE_LIFECYCLE. "
                    f"Se for stage nova, atualize sensor "
                    f"(scripts/check_stage_tools_naming.py) + ADR inline em "
                    f"wizard_tool_registry.py."
                )

    for v in violations:
        print(f"WARN {v}")
    print(
        f"\nTotal: {len(violations)} violations (baseline esperado: 0). "
        f"Encontradas {len(found_keys)} entries."
    )

    if "--blocking" in sys.argv and violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
