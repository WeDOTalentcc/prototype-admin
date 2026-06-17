"""
Canonical backend PT-BR confirmation classifier (Task #1211).

Single source of truth for "did the recruiter say yes / no / something
ambiguous?" when LIA proactively proposes a next step in the chat (e.g. the
post-wizard continuity offer: "quer que eu publique a vaga no ATS agora?").

Mirrors the *philosophy* of the frontend ``classifyNavConfirmation``
(``plataforma-lia/src/components/.../classify-nav-confirmation``):

  • natural PT-BR variations of agreement and refusal;
  • NEGATIVES take precedence over positive tokens — "pode esperar" / "agora
    não" must classify as ``no`` even though they contain "pode";
  • anything not clearly yes/no is ``ambiguous`` (the proposal stays pending and
    LIA re-asks, never auto-executing on a guess).

Pure / side-effect free — safe to call on every turn.
"""
from __future__ import annotations

import re
import unicodedata

__all__ = ["classify_confirmation"]


def _strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", _strip_accents(text or "").lower()).strip()


# NEGATIVES evaluated first (precedence). Accent-insensitive (normalized).
_NEGATIVE_PATTERNS: tuple[str, ...] = (
    r"\bnao\b",
    r"\bn\b",
    r"\bnops?\b",
    r"\bnegativo\b",
    r"agora nao",
    r"\bdepois\b",
    r"mais tarde",
    r"outra hora",
    r"deixa pra la",
    r"deixa pra depois",
    r"deixa quieto",
    r"esquec",
    r"esquef",  # esqueça normalized variants
    r"\bcancel",
    r"\bpara\b",
    r"\bpare\b",
    r"\bpode esperar\b",
    r"pode deixar pra",
    r"melhor nao",
    r"prefiro nao",
    r"sem publicar",
    r"nao precisa",
    r"nao quero",
    r"por enquanto nao",
)

# POSITIVES — natural PT-BR agreement.
_POSITIVE_PATTERNS: tuple[str, ...] = (
    r"\bsim\b",
    r"\bs\b",
    r"\bclaro\b",
    r"\bisso\b",
    r"\bok\b",
    r"\bokay\b",
    r"\bblz\b",
    r"\bbeleza\b",
    r"\bvamos\b",
    r"\bbora\b",
    r"\bvai\b",
    r"\bmanda\b",
    r"manda ver",
    r"manda bala",
    r"\bfechou\b",
    r"\bfechado\b",
    r"\bpode\b",
    r"pode ser",
    r"pode ir",
    r"pode publicar",
    r"pode sincronizar",
    r"pode criar",
    r"pode mandar",
    r"\bperfeito\b",
    r"\bquero\b",
    r"\bcom certeza\b",
    r"\bpor favor\b",
    r"\bfaz\b",
    r"\bfa[cz]a\b",
    r"\bsigam?\b",
    r"\bsegue\b",
    r"\bpositivo\b",
    r"\baprovo\b",
    r"\baprovado\b",
    r"\bconfirmo\b",
    r"\bconfirmado\b",
    r"\bavan[cf]ar?\b",
)


def classify_confirmation(message: str | None) -> str:
    """Classify a free-text PT-BR reply to a yes/no proposal.

    Returns one of ``"yes"`` | ``"no"`` | ``"ambiguous"``.

    Negatives take precedence: a message containing both a positive and a
    negative token (e.g. "pode esperar") resolves to ``no``.
    """
    norm = _normalize(message)
    if not norm:
        return "ambiguous"

    for pat in _NEGATIVE_PATTERNS:
        if re.search(pat, norm):
            return "no"

    for pat in _POSITIVE_PATTERNS:
        if re.search(pat, norm):
            return "yes"

    return "ambiguous"
