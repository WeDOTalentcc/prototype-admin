#!/usr/bin/env python3
"""
Sensor anti-regressão · W1-007 (2026-05-22)

Verifica que `app/shared/compliance/c3b_layer.py:pre_compliance` continua
chamando `HateSpeechGuard.check()` ANTES de PII strip.

Pattern de violação:
- Remover bloco HateSpeechGuard de c3b_layer (merge accident, refactor errado)
- Mover HateSpeechGuard para DEPOIS de PII strip (slur normalizado em pseudo-PII)
- Deletar app/shared/compliance/hate_speech_guard.py

Sem hate check pre-PII, slur com U+200B / leetspeak / lookalike passa direto
pro LLM sem normalização adversarial.

Mensagem em PT-BR + fix sugerido em sintaxe exata (harness pattern CLAUDE.md).

Mode: BLOCKING (após W1-007 ser shipped é canonical).
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
C3B_FILE = REPO_ROOT / "app" / "shared" / "compliance" / "c3b_layer.py"
GUARD_FILE = REPO_ROOT / "app" / "shared" / "compliance" / "hate_speech_guard.py"


def check_hate_speech_guard_present() -> list[str]:
    """Verifica que hate_speech_guard.py existe + tem class canonical."""
    errors: list[str] = []

    if not GUARD_FILE.exists():
        errors.append(
            "❌ `app/shared/compliance/hate_speech_guard.py` não existe\n"
            "   FIX: criar HateSpeechGuard com 5 layers adversarial pt-BR\n"
            "   Referência: tests/security/test_red_team_hate_speech_pt_br.py"
        )
        return errors

    src = GUARD_FILE.read_text()
    if "class HateSpeechGuard" not in src:
        errors.append(
            "❌ `HateSpeechGuard` class não encontrada em hate_speech_guard.py\n"
            "   FIX: implementar class HateSpeechGuard com método check()"
        )
    if "class HateCategory" not in src:
        errors.append(
            "❌ `HateCategory` enum não encontrado\n"
            "   FIX: enum com 6 categorias (RACIAL_SLUR, SEXUAL_ORIENTATION_SLUR, "
            "GENDER_SLUR, ABLEIST_SLUR, PROFANITY_ATTACK, DEHUMANIZATION)"
        )
    # Verifica 5 layers (NFKD + leetspeak + lookalike + zero-width + spaced)
    required_normalizers = (
        "_LEETSPEAK_TABLE",
        "_LOOKALIKE_TABLE",
        "_ZERO_WIDTH",
        "_SPACED_LETTERS",
        "unicodedata.normalize",
    )
    missing = [name for name in required_normalizers if name not in src]
    if missing:
        errors.append(
            f"❌ HateSpeechGuard incompleto · faltando: {missing}\n"
            "   FIX: implementar 5 layers adversarial:\n"
            "   L1 NFKD (unicodedata.normalize)\n"
            "   L2 leetspeak (_LEETSPEAK_TABLE)\n"
            "   L3 lookalike (_LOOKALIKE_TABLE)\n"
            "   L4 zero-width (_ZERO_WIDTH)\n"
            "   L5 spaced-letters (_SPACED_LETTERS)"
        )
    return errors


def check_c3b_calls_hate_speech_guard() -> list[str]:
    """Verifica que c3b_layer.pre_compliance chama HateSpeechGuard ANTES de PII."""
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
            "❌ função `pre_compliance` não encontrada em c3b_layer.py\n"
            "   FIX: c3b_layer.pre_compliance(message, company_id, domain) é entry-point compliance"
        )
        return errors

    body_src = ast.unparse(pre_compliance_fn)
    has_hs_guard = "HateSpeechGuard" in body_src
    has_check_call = ".check(" in body_src

    if not has_hs_guard:
        errors.append(
            "❌ `pre_compliance` NÃO chama HateSpeechGuard\n"
            f"   File: {C3B_FILE.relative_to(REPO_ROOT)}\n"
            "   Risco: hate speech com bypass adversarial passa pro LLM (compliance gap)\n"
            "   FIX: adicionar ANTES de PII strip:\n"
            "       from app.shared.compliance.hate_speech_guard import HateSpeechGuard\n"
            "       hs_guard = HateSpeechGuard()\n"
            "       hs_result = hs_guard.check(message)\n"
            "       if hs_result.is_blocked:\n"
            "           return PreComplianceResult(hate_speech_blocked=True, ...)\n"
            "   Referência: tests/security/test_red_team_hate_speech_pt_br.py"
        )

    if not has_check_call:
        errors.append(
            "❌ `pre_compliance` referencia HateSpeechGuard mas não chama .check(...)\n"
            "   FIX: usar `hs_guard.check(message)` que retorna HateSpeechCheckResult"
        )

    if "hate_speech_blocked" not in src:
        errors.append(
            "❌ `PreComplianceResult` não tem campo `hate_speech_blocked`\n"
            f"   File: {C3B_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: adicionar no dataclass:\n"
            "       hate_speech_blocked: bool = False"
        )

    # CRITICAL: HateSpeechGuard deve aparecer ANTES de strip_pii (ordem importa)
    if has_hs_guard:
        idx_hs = body_src.find("HateSpeechGuard")
        idx_pii = body_src.find("strip_pii_for_llm_prompt")
        if idx_pii != -1 and idx_hs > idx_pii:
            errors.append(
                "❌ HateSpeechGuard chamado DEPOIS de strip_pii_for_llm_prompt\n"
                "   Risco: PII strip pode alterar slur, ocultando hate speech\n"
                "   FIX: mover HateSpeechGuard ANTES do bloco de PII strip"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    errors.extend(check_hate_speech_guard_present())
    errors.extend(check_c3b_calls_hate_speech_guard())

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
            print(file=sys.stderr)
        if args.warn_only:
            print("⚠️  WARN-ONLY mode: 0 exit despite failures", file=sys.stderr)
            return 0
        return 1

    print("✅ HateSpeechGuard wired em c3b_layer.pre_compliance (W1-007)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
