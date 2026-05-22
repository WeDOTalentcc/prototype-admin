"""
HateSpeechGuard pt-BR · W1-007 (2026-05-22)

Detecta hate speech em pt-BR com 5 layers adversarial:
  L1 — NFKD normalize (acentos / case)
  L2 — leetspeak (1337, @, !, $, etc.)
  L3 — lookalike Cyrillic (а=a, е=e, о=o, р=p)
  L4 — zero-width chars (U+200B, U+200C, U+202E, U+FEFF, U+2060)
  L5 — spaced-letters ('v i a d o' → 'viado')

Adaptado de v5 hate_speech_guard.py (284 LOC, padrão @classmethod).
Adaptações para lia canonical:
  - HateSpeechCheckResult.is_blocked (vs allowed) — alinha FairnessCheckResult
  - educational_message (vs message) — alinha FairnessCheckResult
  - Instance method (vs @classmethod) — padrão lia
  - Sem Prometheus v5-specific (canary_metrics adicionado em W1-006 part 2)

Wiring canonical:
  - app/shared/compliance/c3b_layer.py:pre_compliance (ANTES de PII strip)
  - Defesa em profundidade: post_compliance também valida outputs

Pre-audit: /Users/paulomoraes/Documents/Python/replit_lia_audit/sprint_logs/sprint_1.1/W1-007_AUDIT.md
Tests: tests/security/test_red_team_hate_speech_pt_br.py
Sensor: scripts/check_hate_speech_guard_wired.py
"""
from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

logger = logging.getLogger(__name__)


class HateCategory(str, Enum):
    RACIAL_SLUR = "racial_slur"
    SEXUAL_ORIENTATION_SLUR = "sexual_orientation_slur"
    GENDER_SLUR = "gender_slur"
    ABLEIST_SLUR = "ableist_slur"
    PROFANITY_ATTACK = "profanity_attack"
    DEHUMANIZATION = "dehumanization"


@dataclass
class HateSpeechCheckResult:
    """Result canonical alinhado com FairnessCheckResult lia."""
    is_blocked: bool = False
    matched_term: Optional[str] = None
    category: Optional[HateCategory] = None
    educational_message: Optional[str] = None
    detected_patterns: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    adversarial_normalization: bool = False


_BLOCK_MESSAGE = (
    "Não posso processar mensagens com termos ofensivos, injuriosos "
    "ou discriminatórios. Reformule sua solicitação respeitando os "
    "direitos e a dignidade das pessoas."
)


# ─── Pattern registry · 6 categorias ────────────────────────────────────────

_RACIAL_DEHUMANIZATION_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(?:preto|negro|neguinh[oa]|pardo)\s+(?:macaco|primata|bicho|chimpanz[eé]|gorila|orangotang[oa])\b", re.I),
    re.compile(r"\bmacaco\s+(?:preto|negro|pardo|africano)\b", re.I),
    re.compile(r"\b(?:volta|vai)\s+(?:pra|para)\s+(?:[áa]frica|senzala|tronco)\b", re.I),
    re.compile(r"\b(?:cabelo\s+ruim|cabelo\s+de\s+bombril|cabelo\s+pixaim)\b", re.I),
    re.compile(r"\b(?:pretinh[oa]\s+do\s+cabelo|crioul[oa]\s+(?:safad[oa]|fedid[oa]|nojent[oa]))\b", re.I),
    re.compile(r"\bnegrad[ao]\s+(?:imunda|fedid[ao]|nojent[ao]|safad[ao])\b", re.I),
]

_RACIAL_DIRECT_SLURS: List[re.Pattern] = [
    re.compile(r"\b(?:nigger|nigga|negr[aã]o\s+(?:bait[oa]la|merda|imund[oa]))\b", re.I),
    re.compile(r"\bcrioul[oa]\s+(?:imund[oa]|fedid[oa]|nojent[oa]|burr[oa]|safad[oa])\b", re.I),
    re.compile(r"\bnegro\s+(?:safad[oa]|nojent[oa]|imund[oa]|burr[oa]|fedid[oa]|fdp|filho\s+da\s+puta)\b", re.I),
]

_HOMOPHOBIC_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(?:viado|veado|bicha\s+(?:louca|nojenta|imunda)|bait[oa]la)\b", re.I),
    re.compile(r"\b(?:faggot|fag\s+ass|sapat[aã]o\s+(?:nojent|imund|safad))\b", re.I),
    re.compile(r"\b(?:traveco|tranny|she.?male)\b", re.I),
]

_GENDER_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(?:vagabunda|puta\s+(?:que\s+pariu|de\s+merda|nojenta)|piranha\s+(?:nojenta|safada|imunda))\b", re.I),
    re.compile(r"\b(?:vai\s+lavar\s+lou[çc]a|lugar\s+de\s+mulher\s+[eé]\s+na\s+cozinha)\b", re.I),
]

_ABLEIST_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(?:retardad[oa]\s+(?:mental|nojent[oa])|mongoloid[ae]|aleijad[oa]\s+(?:imund[oa]|nojent[oa]))\b", re.I),
    re.compile(r"\bdebil[oó]ide\s+(?:mental|do\s+caralho)\b", re.I),
]

_PROFANITY_ATTACK_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(?:cu\s+raspado|cu\s+(?:fedido|imundo|peludo|sujo)|toma\s+no\s+cu)\b", re.I),
    re.compile(r"\b(?:vai\s+(?:tomar|se\s+foder|se\s+lascar)|filh[oa]\s+da\s+puta|fdp\s+(?:de\s+merda|nojent[oa]))\b", re.I),
    re.compile(r"\b(?:corno\s+manso|corno\s+do\s+caralho|otario\s+(?:nojento|fdp))\b", re.I),
]


_PATTERN_REGISTRY = [
    (HateCategory.DEHUMANIZATION, _RACIAL_DEHUMANIZATION_PATTERNS),
    (HateCategory.RACIAL_SLUR, _RACIAL_DIRECT_SLURS),
    (HateCategory.SEXUAL_ORIENTATION_SLUR, _HOMOPHOBIC_PATTERNS),
    (HateCategory.GENDER_SLUR, _GENDER_PATTERNS),
    (HateCategory.ABLEIST_SLUR, _ABLEIST_PATTERNS),
    (HateCategory.PROFANITY_ATTACK, _PROFANITY_ATTACK_PATTERNS),
]


# ─── 5 Layers de normalização ────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """L1 · NFKD normalize + lowercase."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return no_accents.lower().strip()


_LEETSPEAK_TABLE = str.maketrans({
    "@": "a", "4": "a",
    "0": "o",
    "1": "i", "!": "i", "|": "i",
    "3": "e", "€": "e",
    "5": "s", "$": "s",
    "7": "t", "+": "t",
    "9": "g",
})

_LOOKALIKE_TABLE = str.maketrans({
    "а": "a", "А": "a",  # Cyrillic
    "е": "e", "Е": "e",
    "о": "o", "О": "o",
    "р": "p", "Р": "p",
    "с": "c", "С": "c",
    "у": "y", "У": "y",
    "х": "x", "Х": "x",
    "ı": "i",  # Turkish
    "α": "a", "ο": "o", "ν": "v", "ϲ": "c",  # Greek
})

_ZERO_WIDTH = re.compile(r"[​‌‍﻿⁠‮]")

_EMOJI_LIKE = re.compile(
    r"["
    r"\U0001F300-\U0001F9FF"
    r"\U0001FA00-\U0001FAFF"
    r"\U00002600-\U000027BF"
    r"]"
)

_INTRA_WORD_PUNCT = re.compile(
    r"[\.\,\-\_\*\~\^\`\'\"\(\)\[\]\{\}\?\!\;\:\/\\\|]"
)

_MULTI_SPACE = re.compile(r"\s+")


def _apply_lookalike_and_leet(text: str) -> str:
    """L2+L3+L4 · NFKD + lookalike + leetspeak + zero-width + emoji strip."""
    nfkd = unicodedata.normalize("NFKD", text)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    no_zw = _ZERO_WIDTH.sub("", no_accents)
    no_emoji = _EMOJI_LIKE.sub("", no_zw)
    lookalike = no_emoji.translate(_LOOKALIKE_TABLE)
    deleet = lookalike.translate(_LEETSPEAK_TABLE)
    return deleet.lower().strip()


def _normalize_adversarial(text: str) -> str:
    """L1-L4 com espaços preservados."""
    if not text:
        return ""
    base = _apply_lookalike_and_leet(text)
    despaced = _INTRA_WORD_PUNCT.sub(" ", base)
    return _MULTI_SPACE.sub(" ", despaced).strip()


def _normalize_compact(text: str) -> str:
    """L1-L4 sem nenhum separador (slurs de 1 palavra)."""
    if not text:
        return ""
    base = _apply_lookalike_and_leet(text)
    no_punct = _INTRA_WORD_PUNCT.sub("", base)
    return _MULTI_SPACE.sub("", no_punct)


_SPACED_LETTERS = re.compile(
    r"(?:(?<=^)|(?<=\s))"
    r"([a-z](?:[\s\.\-_]+[a-z]){3,})"
    r"(?=\s|$|[\.\,\?\!])"
)


def _normalize_unspaced_letters(text: str) -> str:
    """L5 · colapsa 'v i a d o' → 'viado'."""
    if not text:
        return ""
    base = _apply_lookalike_and_leet(text)
    base = _INTRA_WORD_PUNCT.sub(" ", base)

    def _collapse(match):
        seq = match.group(1)
        return re.sub(r"[\s\.\-_]+", "", seq)

    collapsed = _SPACED_LETTERS.sub(_collapse, base)
    return _MULTI_SPACE.sub(" ", collapsed).strip()


# ─── Guard canonical (instance method, padrão lia) ───────────────────────────

class HateSpeechGuard:
    """
    Hate speech detector pt-BR com defesa adversarial 5-layers.

    Pattern lia canonical · instance method · alinhado FairnessGuard.

    Uso:
        guard = HateSpeechGuard()
        result = guard.check("texto do usuário")
        if result.is_blocked:
            # respond com result.educational_message
    """

    def check(self, text: str) -> HateSpeechCheckResult:
        if not text or not text.strip():
            return HateSpeechCheckResult(is_blocked=False)

        raw_lower = text.lower()
        normalized = _normalize(text)
        adversarial = _normalize_adversarial(text)
        compact = _normalize_compact(text)
        unspaced = _normalize_unspaced_letters(text)

        # Tenta nas variantes em ordem:
        #   1. raw_lower         — texto cru lowercase (não adversarial)
        #   2. normalized        — NFKD + lower (L1 só, não adversarial)
        #   3. adversarial       — L1-L4 com espaços (adversarial)
        #   4. unspaced          — L5 colapsa 'r a c i s t a' (adversarial)
        #   5. compact           — L1-L4 sem separadores (adversarial)
        for category, patterns in _PATTERN_REGISTRY:
            for pat in patterns:
                match = pat.search(raw_lower) or pat.search(normalized)
                if match:
                    return self._block(match, category, pat, via_adversarial=False)

                for candidate in (adversarial, unspaced, compact):
                    if not candidate:
                        continue
                    match = pat.search(candidate)
                    if match:
                        return self._block(match, category, pat, via_adversarial=True)

        return HateSpeechCheckResult(is_blocked=False)

    @staticmethod
    def _block(
        match: re.Match,
        category: HateCategory,
        pat: re.Pattern,
        via_adversarial: bool,
    ) -> HateSpeechCheckResult:
        matched = match.group(0)
        logger.warning(
            "[HateSpeechGuard] BLOCKED · category=%s term=%r adversarial=%s",
            category.value, matched, via_adversarial,
        )
        return HateSpeechCheckResult(
            is_blocked=True,
            matched_term=matched,
            category=category,
            educational_message=_BLOCK_MESSAGE,
            detected_patterns=[pat.pattern],
            adversarial_normalization=via_adversarial,
        )
