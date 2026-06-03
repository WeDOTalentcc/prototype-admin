"""Sensor canonical: barra regressão do wiring de ai_persona em callers de SystemPromptBuilder.

Lista canonical de callers principais que DEVEM usar build_system_prompt_with_persona.
Cada arquivo nessa lista é verificado:
1. Não pode chamar SystemPromptBuilder.build() diretamente sem ai_persona= no kwarg.
2. Se chamar build_system_prompt_with_persona — OK.

Exemptions documentadas inline:
- Agent Studio (custom_agent_runtime.py): já passa ai_persona em 3 sites — pattern próprio canonical.
- Voice (voice_system_prompt.py): pattern próprio canonical.

Background: ghost setting fix 2026-05-24 — wire de ai_persona em 7 callers canonical
(chat SSE, conversational, insights x3, _shared, interview_notes x2,
lia_profile_analysis, candidate_search). Antes desse fix, cliente customizava
name/tone na UI \"Personalidade da IA\" e a mudança NÃO chegava ao prompt em
nenhum desses surfaces.

Harness disciplina (Hashimoto): GUIDE (CLAUDE.md) + SENSOR (este) +
DÉBITO TÉCNICO (não há — todos os 7 callers wired).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Callers canonical wired pelo ghost setting fix 2026-05-24.
# Adicionar arquivo novo aqui = força que ele use o helper canonical.
CANONICAL_CALLERS = [
    "app/api/v1/chat.py",
    "app/api/v1/lia_assistant/conversational.py",
    "app/api/v1/lia_assistant/insights.py",
    "app/api/v1/lia_assistant/_shared.py",
    "app/api/v1/interview_notes.py",
    "app/api/v1/lia_profile_analysis.py",
    "app/api/v1/candidate_search/misc_search.py",
    # 2026-06-02: orquestradores (caminho DEFAULT do chat). Fix anterior
    # (8b3ef6f44, 2026-05-24) cobriu 7 callers REST mas omitiu os 3 orquestradores
    # que montam o system prompt da conversa principal.
    "app/orchestrator/execution/main_orchestrator.py",
    "app/orchestrator/services/fallback_react_service.py",
    "app/orchestrator/legacy/orchestrator.py",
]

# Exemptions — pattern próprio canonical já wired.
# Documentar SEMPRE a razão; revisar trimestralmente se ainda se justifica.
EXEMPT_CALLERS = {
    # Agent Studio: custom_agent_runtime.py já passa ai_persona em 3 sites
    # via load próprio (pattern canonical pre-helper).
    "app/domains/agents/services/custom_agent_runtime.py",
    # Voice: voice_system_prompt.py tem pattern próprio de injection de persona
    # (mesma feature E2.3, wiring diferente por contexto streaming TTS).
    "app/shared/prompts/voice_system_prompt.py",
}


def check_file(path: Path) -> list[str]:
    """Retorna lista de violations no arquivo. Vazia = OK."""
    violations: list[str] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        return [f"{path}: SyntaxError ao parsear: {exc}"]

    rel = str(path.relative_to(ROOT))
    if rel in EXEMPT_CALLERS:
        return []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Detecta SystemPromptBuilder.build(...)
        func = node.func
        is_build_call = (
            isinstance(func, ast.Attribute)
            and func.attr == "build"
            and isinstance(func.value, ast.Name)
            and func.value.id == "SystemPromptBuilder"
        )
        if not is_build_call:
            continue

        # Verifica se ai_persona= está nos kwargs
        has_ai_persona_kwarg = any(
            kw.arg == "ai_persona" for kw in node.keywords
        )
        if not has_ai_persona_kwarg:
            violations.append(
                f"{rel}:{node.lineno}: SystemPromptBuilder.build() sem ai_persona= "
                f"→ usar build_system_prompt_with_persona() canonical em vez disso "
                f"(ghost setting: customização de nome/tom da IA não chega ao prompt). "
                f"Ver app/shared/prompts/persona_aware_prompt.py."
            )

    return violations


def main() -> int:
    all_violations: list[str] = []
    missing_files: list[str] = []
    for caller in CANONICAL_CALLERS:
        path = ROOT / caller
        if not path.exists():
            missing_files.append(caller)
            continue
        all_violations.extend(check_file(path))

    if missing_files:
        print("WARNING: callers canonical listados mas arquivos não existem:")
        for f in missing_files:
            print(f"  - {f}")
        print("(Atualizar CANONICAL_CALLERS no sensor se o caller foi renomeado/removido.)")

    if all_violations:
        print("\n❌ Persona-aware prompt sensor: violations encontradas")
        for v in all_violations:
            print(f"  - {v}")
        print(
            "\n→ Fix: substituir SystemPromptBuilder.build(...) por "
            "await build_system_prompt_with_persona(company_id=..., db=..., ...) "
            "(import: from app.shared.prompts.persona_aware_prompt import "
            "build_system_prompt_with_persona)."
        )
        return 1

    print(
        f"✅ Persona-aware prompt sensor: 0 violations em "
        f"{len(CANONICAL_CALLERS)} callers canonical (exempt: {len(EXEMPT_CALLERS)})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
