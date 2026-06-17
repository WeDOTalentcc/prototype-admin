"""
WSI Question Builder
====================

Conversões puras (sem I/O, sem `self`) que transformam snapshots persistidos
de banco/JSON em modelos `WSIQuestion` consumíveis pelo orquestrador de voz e
pelos endpoints de chat.

Histórico:
- Audit task #496 (PR2): consolidação de duas implementações divergentes
  de `_convert_snapshot_to_wsi_questions` que coexistiam em
  `wsi_voice_orchestrator.py` (cobria categoria "company") e em
  `wsi_endpoints.py` (cobria categoria "eligibility"). Anti-pattern #2 do
  canonical-fix (cópia divergente). Esta versão é a fonte única e cobre
  TODAS as 4 categorias usadas no sistema:
    - eligibility → CBI / contextual
    - technical   → Bloom / autodeclaration
    - behavioral  → BigFive / situational
    - company     → CBI / contextual
  Default seguro (Bloom / contextual) para categorias desconhecidas.
"""

from __future__ import annotations

from .models import WSIQuestion

_FRAMEWORK_MAP: dict[str, str] = {
    "eligibility": "CBI",
    "technical": "Bloom",
    "behavioral": "BigFive",
    "company": "CBI",
}

_TYPE_MAP: dict[str, str] = {
    "eligibility": "contextual",
    "technical": "autodeclaration",
    "behavioral": "situational",
    "company": "contextual",
}

_DEFAULT_FRAMEWORK = "Bloom"
_DEFAULT_TYPE = "contextual"


def convert_snapshot_to_wsi_questions(snapshot: list) -> list[WSIQuestion]:
    """
    Converte um snapshot de question_set (lista de dicts persistida) em uma
    lista de `WSIQuestion`.

    Aceita as variações de chave históricas para o texto da pergunta
    (`text`, `question`, `question_text`) e da competência alvo
    (`skill_targeted`, `competency_validated`). Perguntas sem texto são
    silenciosamente ignoradas (não há informação para entrevistar).

    Args:
        snapshot: Lista de dicts conforme persistida em
            `screening_question_sets.questions_snapshot`.

    Returns:
        Lista de `WSIQuestion` válidas (Pydantic já valida os campos
        obrigatórios na construção).
    """
    converted: list[WSIQuestion] = []
    for idx, q in enumerate(snapshot):
        text = q.get("text", q.get("question", q.get("question_text", "")))
        if not text:
            continue
        category = q.get("category", "technical")
        question = WSIQuestion(
            id=q.get("id", f"qs_{idx}"),
            competency=q.get(
                "skill_targeted",
                q.get("competency_validated", category),
            ),
            framework=_FRAMEWORK_MAP.get(category, _DEFAULT_FRAMEWORK),
            question_type=_TYPE_MAP.get(category, _DEFAULT_TYPE),
            question_text=text,
            weight=float(q.get("weight", 0.75)),
            expected_signals=q.get("expected_signals", []),
            scoring_criteria=q.get("scoring_criteria", {}),
        )
        converted.append(question)
    return converted
