#!/usr/bin/env python3
"""
Sensor anti-regressão · W1-005 (2026-05-22)

Verifica que `app/shared/compliance/c3b_layer.py:pre_compliance` continua
chamando `PromptInjectionGuard.check()` entre PII strip e FairnessGuard.

Pattern de violação: alguém remove o bloco de injection guard wiring (intentionally
or via merge accident). Sem injection check, c3b passa input direto pro LLM
sem validação adversarial — gap OWASP LLM01.

Mensagem otimizada pra consumo de LLM (PT-BR + fix sugerido em sintaxe exata).

Mode: BLOCKING (após W1-005 ser shipped, é canonical canônico).

Run:
    python scripts/check_c3b_wires_injection_guard.py
    python scripts/check_c3b_wires_injection_guard.py --warn-only  # ratchet mode
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
C3B_FILE = REPO_ROOT / "app" / "shared" / "compliance" / "c3b_layer.py"


def check_pre_compliance_calls_injection_guard() -> list[str]:
    """Verifica que pre_compliance() chama PromptInjectionGuard.check.

    Returns list of error messages (empty = passing).
    """
    errors: list[str] = []

    if not C3B_FILE.exists():
        errors.append(f"❌ {C3B_FILE.relative_to(REPO_ROOT)} não existe")
        return errors

    src = C3B_FILE.read_text()
    tree = ast.parse(src)

    pre_compliance_fn = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            if node.name == "pre_compliance":
                pre_compliance_fn = node
                break

    if pre_compliance_fn is None:
        errors.append(
            "❌ função `pre_compliance` não encontrada em "
            f"{C3B_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: c3b_layer.pre_compliance(message, company_id, domain) é entry-point "
            "canonical para compliance pre-LLM"
        )
        return errors

    # Walk body looking for "PromptInjectionGuard" reference
    body_src = ast.unparse(pre_compliance_fn)
    has_injection_guard = "PromptInjectionGuard" in body_src
    has_check_call = ".check(" in body_src

    if not has_injection_guard:
        errors.append(
            "❌ `pre_compliance` NÃO chama PromptInjectionGuard\n"
            f"   File: {C3B_FILE.relative_to(REPO_ROOT)}\n"
            "   Risco: input adversarial passa direto pro LLM sem validação (OWASP LLM01)\n"
            "   FIX: adicionar entre PII strip e FairnessGuard:\n"
            "       from app.shared.compliance.prompt_injection_guard import PromptInjectionGuard\n"
            "       guard = PromptInjectionGuard()\n"
            "       ig_result = guard.check(clean)\n"
            "       if ig_result.is_blocked:\n"
            "           return PreComplianceResult(injection_blocked=True, ...)\n"
            "   Referência: tests/security/test_red_team_c3b_injection_wiring.py"
        )

    if not has_check_call:
        errors.append(
            "❌ `pre_compliance` referencia PromptInjectionGuard mas não chama .check(...)\n"
            f"   File: {C3B_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: usar `guard.check(clean)` que retorna InjectionCheckResult"
        )

    # Verify PreComplianceResult has injection_blocked field
    if "injection_blocked" not in src:
        errors.append(
            "❌ `PreComplianceResult` não tem campo `injection_blocked`\n"
            f"   File: {C3B_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: adicionar no dataclass:\n"
            "       injection_blocked: bool = False"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Exit 0 even on failures (ratchet mode during W1-005 rollout)",
    )
    args = parser.parse_args()

    errors = check_pre_compliance_calls_injection_guard()

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
            print(file=sys.stderr)
        if args.warn_only:
            print("⚠️  WARN-ONLY mode: 0 exit despite failures", file=sys.stderr)
            return 0
        return 1

    print("✅ c3b_layer.pre_compliance wired com PromptInjectionGuard (W1-005)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
