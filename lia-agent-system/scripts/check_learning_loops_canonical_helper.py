#!/usr/bin/env python3
"""Sensor canonical: barra regressão na consumidência de learning_loops toggles.

Todo consumer de toggles `learning_loops` em app/domains/ DEVE usar
`load_learning_loops_toggles` (helper canonical em
app/shared/services/learning_loops_toggles.py). Detecta padrões anti-canonical:

1. `select(CompanyHiringPolicy)` direto em services para ler
   `automation_rules.learning_loops` sem usar o helper.
2. `.get("<learning_loops_key>", <literal_default>)` que sobrescreve o canonical
   default. Helper canonical já garante presença de TODAS as 5 chaves com
   tipo bool — usar default literal é DRY violation e fonte de drift
   (caso F2.1 audit 2026-05-24: 4 fontes paralelas, defaults divergentes).

CONSUMERS_PATHS lista os arquivos canonical que sabidamente consomem o
helper. EXEMPT_FILES documenta exceções inline (e.g., o próprio helper
e o model que define os defaults).

Background: F2 audit 2026-05-24. Sprint B P3 D2 helper criado 2026-05-21
para eliminar drift entre múltiplas fontes de verdade. F2.1 + F2.2 fix
2026-05-24 estendeu o pattern para jd_similar_service + alinhou default
bigfive_department_history=False (ADR-LGPD-001 conservative).

Exit codes:
- 0: zero violations (canonical preserved)
- 1: pelo menos uma violation detectada (output otimizado pra LLM consumer)
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Arquivos consumers conhecidos que LÊEM learning_loops toggles via helper.
# Sensor verifica esses arquivos. Adicionar novo consumer aqui quando criar.
CONSUMERS_PATHS = [
    "app/domains/job_creation/services/bigfive_service.py",
    "app/domains/job_creation/services/jd_similar_service.py",
    "app/domains/communication/services/transition_dispatch_service.py",
]

# Chaves canonical do dict learning_loops (mesmo set definido em
# AUTOMATION_RULES_DEFAULTS["learning_loops"]). Sensor detecta default
# literal nas calls toggles.get(<canonical_key>, <literal>).
LEARNING_LOOPS_KEYS = {
    "enabled",
    "bigfive_company_culture",
    "bigfive_department_history",
    "wsi_question_effectiveness",
    "jd_similar_suggestion",
}

# Arquivos isentos: definição canonical (constants) ou o próprio helper.
EXEMPT_FILES = {
    # Helper canonical - é onde o default literal canonical vive (defaults
    # = AUTOMATION_RULES_DEFAULTS["learning_loops"]).
    "app/shared/services/learning_loops_toggles.py",
    # Source-of-truth dos defaults (AUTOMATION_RULES_DEFAULTS).
    "libs/models/lia_models/company_hiring_policy.py",
    # Endpoint REST aceita exemption documentada (recebe payload do cliente).
    "app/api/v1/learning_loops_config.py",
}


def check_file(path: Path) -> list[str]:
    """Retorna lista de violations (strings legíveis para LLM consumer)."""
    rel = str(path.relative_to(ROOT))
    if rel in EXEMPT_FILES:
        return []
    if not path.exists():
        return []

    src = path.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [f"{rel}: SyntaxError ({exc})"]

    violations: list[str] = []
    uses_helper = "load_learning_loops_toggles" in src

    # Pattern 1: toggles.get("<canonical_key>", <bool literal>) com default
    # literal — viola production-quality DRY (helper já garante presença).
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_get_call = isinstance(func, ast.Attribute) and func.attr == "get"
        if not is_get_call:
            continue
        if len(node.args) != 2:
            continue
        first_arg, second_arg = node.args[0], node.args[1]
        if not (isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str)):
            continue
        if first_arg.value not in LEARNING_LOOPS_KEYS:
            continue
        if isinstance(second_arg, ast.Constant) and isinstance(second_arg.value, bool):
            violations.append(
                f"{rel}:{node.lineno}: `.get(\"{first_arg.value}\", {second_arg.value})` "
                f"com default literal — confie no helper canonical, use "
                f"`toggles.get(\"{first_arg.value}\")` (helper garante presença das 5 "
                f"chaves canonical com tipo bool)."
            )

    # Pattern 2: query inline de CompanyHiringPolicy + leitura de
    # automation_rules sem usar o helper canonical. Heurística string-based;
    # falso positivo aceitável se confirmar via inspeção manual.
    if (
        "select(CompanyHiringPolicy)" in src
        and "automation_rules" in src
        and not uses_helper
    ):
        violations.append(
            f"{rel}: faz query inline de CompanyHiringPolicy para ler "
            f"automation_rules sem usar load_learning_loops_toggles(). "
            f"Migrar para o helper canonical em "
            f"app/shared/services/learning_loops_toggles.py."
        )

    return violations


def main() -> int:
    all_violations: list[str] = []
    for caller in CONSUMERS_PATHS:
        path = ROOT / caller
        all_violations.extend(check_file(path))

    if all_violations:
        print("FAIL: Learning Loops canonical helper sensor")
        for v in all_violations:
            print(f"  - {v}")
        print(
            "\nHelper canonical: app/shared/services/learning_loops_toggles.py "
            "(single source of truth desde 2026-05-21). Adicionar consumer "
            "novo? Atualize CONSUMERS_PATHS neste sensor."
        )
        return 1

    print(
        f"PASS: Learning Loops canonical sensor — 0 violations em "
        f"{len(CONSUMERS_PATHS)} consumers."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
