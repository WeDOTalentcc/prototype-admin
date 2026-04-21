"""
Correction detector — FIX 16.

Recognises user CORRECTIONS of a previous LIA turn ("não, quis dizer X",
"estamos falando de X e nao Y", "na verdade...") and short-circuits them
with a clarification response, BEFORE the cascade router or action
executor can interpret the correction as a literal query.

Bug observed in chat audit 2026-04-21 (screenshot 3):
    Turn 5: user says "estamos falando de buscar candidatos e nao perfil cultura"
    → keyword matcher saw "candidatos" + "buscar", dispatched to search_candidates
    → full phrase went as raw_query → "Nenhum candidato encontrado para
       'e nao perfil cultura'"
    User's correction was interpreted as a search. Frustrating UX.

Invariants
----------
- A correction message matches ONE of the correction openers:
    * "não, ...", "nao, ...", "não é isso", "nao é isso"
    * "quis dizer ...", "quiz dizer ..." (typo common)
    * "na verdade ...", "ao contrário ..."
    * "estamos falando de X ... e nao Y" / "estamos falando de X, nao Y"
    * "não foi isso", "nao foi isso"
    * "não é sobre X", "nao é sobre X"
- Short affirmations ("não" / "nao" standalone) are NOT corrections —
  they are negative affirmations handled elsewhere. A correction requires
  additional clarifying content.
- Capability questions ("consegue?", "você sabe?") are NOT corrections —
  those are handled by meta_question_detector (Task #726).

Fail-open: on empty input or regex miss, returns None and the caller
proceeds with the regular pipeline. No silent defaults.

Canonical structure mirrors meta_question_detector.py.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# Padrões que iniciam uma correção explícita
_CORRECTION_OPENERS = re.compile(
    r"(?:"
    # "não/nao, <algo>" — negação seguida de clarificação
    r"^\s*(?:lia[,\s]+)?n[ãa]o\s*,\s*(?=\S)"
    # "não é isso" / "nao é isso" / "não foi isso"
    r"|n[ãa]o\s+(?:[ée]|foi)\s+isso"
    # "quis dizer X" / "quiz dizer" (typo comum)
    r"|qui[sz]\s+dizer"
    # "na verdade"
    r"|na\s+verdade"
    # "ao contrário" / "ao contrario"
    r"|ao\s+contr[áa]rio"
    # "estamos falando de X (e nao/mas) Y"
    r"|estamos\s+falando\s+d[eo]"
    # "não é sobre X" / "nao e sobre X"
    r"|n[ãa]o\s+[ée]?\s*sobre\s+"
    # "não era isso"
    r"|n[ãa]o\s+era\s+isso"
    r")",
    re.IGNORECASE | re.UNICODE,
)

# Padrões de meta-questão (para EXCLUIR falso positivo: "você sabe que X não é Y")
_META_QUESTION_GUARD = re.compile(
    r"^\s*(?:voc[eê]\s+(?:sabe|consegue|pode)|consegue|sabe|tem\s+como|d[áa]\s+(?:pra|para)|"
    r"[ée]\s+poss[íi]vel|como\s+fa[çc]o)\b",
    re.IGNORECASE | re.UNICODE,
)

# Minimum additional content beyond the correction opener. Standalone "não"
# is a negative affirmation, not a correction.
_MIN_LENGTH = 6


@dataclass(frozen=True)
class CorrectionDetection:
    """Result of correction detection."""
    is_correction: bool
    reply: str
    matched_pattern: str


# Generic clarification reply in PT-BR. Deliberately neutral — agent flow
# will ask the user to reformulate without guessing the intent.
_CLARIFICATION_REPLY = (
    "Desculpe, acho que entendi errado no turno anterior. "
    "Pode me dizer com outras palavras o que você precisa? "
    "Se estiver retomando algo que já pedimos antes, me diz qual ação ou "
    "candidato/vaga específica para eu continuar no mesmo contexto."
)


def detect_user_correction(message: str | None) -> CorrectionDetection | None:
    """Detect if message is a correction of the previous LIA turn.

    Returns CorrectionDetection with a neutral clarification reply if the
    message matches correction patterns, None otherwise.

    Fail-open: returns None for empty input or regex miss.
    """
    if not message or not isinstance(message, str):
        return None
    stripped = message.strip()
    if len(stripped) < _MIN_LENGTH:
        return None

    # Exclude meta-capability questions — those have their own detector
    if _META_QUESTION_GUARD.match(stripped):
        return None

    match = _CORRECTION_OPENERS.search(stripped)
    if match is None:
        return None

    logger.info(
        "[correction_detector] user correction detected: pattern=%r input=%r",
        match.group(0), stripped[:100],
    )

    return CorrectionDetection(
        is_correction=True,
        reply=_CLARIFICATION_REPLY,
        matched_pattern=match.group(0),
    )
