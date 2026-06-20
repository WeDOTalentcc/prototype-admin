#!/usr/bin/env python3
"""
Sensor C4 P0 — surfaces de geracao sobre candidato sem GuardedCandidateContentService.

Detecta funcoes `generate_*` em app/domains/*/services/ que:
  - Operam sobre candidatos (by naming convention e content)
  - NAO importam ou usam GuardedCandidateContentService

Comportamento:
  - Lista surfaces NOT_MIGRATED como baseline aceitavel
  - FALHA (exit 1) se total NOT_MIGRATED > BASELINE (regressao)
  - Output otimizado para LLM: instrucao de fix embutida

Baseline 2026-06-20 (C4 P0 #1):
  - report_generator.py -> MIGRADO
  - Surfaces restantes: 4 (feedback_generator_service + strategic_opinion + rubric + cv_scoring)

Uso:
  python scripts/check_c4_guarded_generation.py           # warn-only
  python scripts/check_c4_guarded_generation.py --strict  # exit 1 se > baseline

"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

# Baseline de surfaces ainda nao-migradas (ratchet que encolhe com o tempo)
# Cada card P0 subsequente deve reduzir esse numero.
BASELINE_NOT_MIGRATED = 4  # C4 P0 #1 migrou: report_generator (generate_report + generate_feedback)

# Funcoes-alvo: nomes que sugerem geracao de conteudo sobre candidato
CANDIDATE_CONTENT_FUNCTIONS = {
    "generate_report",
    "generate_feedback",
    "generate_strategic_opinion",
    "generate_rubric_evaluation",
    "generate_fit_rationale",
    "generate_cv_scoring",
    "generate_parecer",
    "generate_cultural_fit",
    "generate_candidate_report",
    "generate_candidate_feedback",
    "generate_rejection_feedback",
    "generate_personalized_feedback",
}

GUARD_IMPORT = "guarded_content_service"
GUARD_CLASS = "GuardedCandidateContentService"
GUARD_FACTORY = "get_guarded_content_service"

def scan_file(path: Path) -> list:
    """Retorna lista de funcoes generate_* no arquivo que NAO usam GuardedContentService."""
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return []

    # Verificar se o arquivo importa GuardedCandidateContentService
    uses_guard = (
        GUARD_IMPORT in source
        or GUARD_CLASS in source
        or GUARD_FACTORY in source
    )

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    violations = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in CANDIDATE_CONTENT_FUNCTIONS:
                if not uses_guard:
                    violations.append(node.name)

    return violations


def main(strict: bool = False) -> int:
    root = Path("app/domains")
    if not root.exists():
        # Try relative to script location
        root = Path(__file__).parent.parent / "app" / "domains"

    not_migrated = []

    for py_file in sorted(root.rglob("*.py")):
        if "/tests/" in str(py_file) or "__pycache__" in str(py_file):
            continue
        if "/services/" not in str(py_file):
            continue

        violations = scan_file(py_file)
        for func_name in violations:
            rel_path = str(py_file).replace(str(root.parent.parent) + "/", "")
            not_migrated.append((rel_path, func_name))

    total = len(not_migrated)

    print(f"\n=== Sensor C4 — GuardedCandidateContentService ratchet ===")
    print(f"Baseline: {BASELINE_NOT_MIGRATED} | Encontrado: {total}")
    print()

    if not_migrated:
        print("Surfaces NAO migradas para GuardedCandidateContentService:")
        for path, func in not_migrated:
            print(f"  NOT_MIGRATED  {path}::{func}")
        print()
        print("-> Fix: adicione ao arquivo:")
        print("    from app.shared.compliance.guarded_content_service import get_guarded_content_service")
        print("    # Antes do return, chame:")
        print("    guard_result = get_guarded_content_service().guard_generated_content(")
        print("        content=llm_generated_text,")
        print("        company_id=company_id,  # obrigatorio, fail-closed")
        print("        content_type=\"<surface_name>\",")
        print("    )")
    else:
        print("Todas as surfaces de geracao sobre candidato estao migradas!")

    if total > BASELINE_NOT_MIGRATED:
        print()
        print(f"REGRESSAO: {total} > baseline {BASELINE_NOT_MIGRATED}")
        print(f"   Novas surfaces nao-migradas detectadas. Migre antes de fazer merge.")
        return 1
    elif total < BASELINE_NOT_MIGRATED:
        print()
        print(f"PROGRESSO: {total} < baseline {BASELINE_NOT_MIGRATED}")
        print(f"   Atualize BASELINE_NOT_MIGRATED = {total} neste script apos confirmar.")
    else:
        print()
        print(f"Baseline mantido: {total} == {BASELINE_NOT_MIGRATED}")

    return 0


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    sys.exit(main(strict=strict))
