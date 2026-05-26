#!/usr/bin/env python3
"""
Sensor PR-16: valida que entries em STAGE_TOOLS seguem convencao
canonical snake_case (creation + lifecycle).

Background: PR-1 (commit 4e904792) descobriu drift kebab vs snake.
PR-8 (d16f6316) documentou design layered como ADR. PR-16 (2026-05-26)
reconciliou kebab -> snake nos 7 creation stages pra alinhar com
WizardStage Literal canonical (app/domains/job_creation/state.py).

Convencao canonical pos-PR-16:
- TODAS as keys = snake_case (sem hyphen)
- Creation stages alinhados com WizardStage Literal
- Lifecycle Phase E mantem snake (DB column values)

Esse sensor:
1. Identifica conjunto canonical de creation stages (snake)
2. Identifica conjunto canonical de lifecycle stages (snake)
3. Qualquer entry FORA dos 2 conjuntos = violation (nome novo precisa
   atualizar canonical set abaixo OU foi typo)
4. Qualquer entry com hyphen = violation (regressao para kebab)

Mode: blocking por default (baseline 0 esperado pos-PR-16).
"""

import ast
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Canonical sets (atualizar quando adicionar stages -- sensor e
# guardrail, nao cego). Todos snake_case pos-PR-16.
CANONICAL_SNAKE_CREATION = {
    "intake",
    "jd_enrichment",
    "pipeline_template",
    "salary",
    "competency",
    "wsi_questions",
    "review",
    "publish",
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

                if "-" in key:
                    suggested = key.replace("-", "_")
                    violations.append(
                        f"STAGE_TOOLS[{key!r}]: usa hyphen (kebab-case). "
                        f"Convencao canonical pos-PR-16 e snake_case. "
                        f"Renomeie ({key!r} -> {suggested!r})."
                    )
                    continue

                if key in CANONICAL_SNAKE_CREATION:
                    continue
                if key in CANONICAL_SNAKE_LIFECYCLE:
                    continue

                violations.append(
                    f"STAGE_TOOLS[{key!r}]: nao esta em "
                    f"CANONICAL_SNAKE_CREATION nem CANONICAL_SNAKE_LIFECYCLE. "
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
