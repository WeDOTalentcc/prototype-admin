"""
Job-creation disambiguator — canonical detector for "is this a job-creation
request?" used to enforce the inviolable rule (Task #1211 / #1212):

    Job creation is ALWAYS the canonical multi-turn wizard, and ONLY the wizard.
    Plan & Execute (LIA-P&E) must NEVER create a job.

This is a *pure* module (no DB, no LLM, no app singletons) so it can be reused
identically by:
  • the wizard bootstrap in ``MainOrchestrator._try_wizard_canonical`` (Phase 1.4),
    catching composite phrasings like "criar a vaga e publicar" that the
    substring-only ``_WIZARD_START_PATTERNS`` misses and would otherwise leak
    into Phase 1.3 (Plan & Execute);
  • capturing the optional post-wizard *continuation* (the "...e publicar" part)
    so LIA can proactively offer to run it once the wizard finishes.

Design contract:
  • ``is_creation`` — the message asks to create/open a new vacancy.
  • ``continuation_kind`` — canonical id of the second task in a composite
    request, ONLY when it maps to an already-connected continuation
    (``publish_job`` / ``sync_job``). ``None`` when there is no second task OR
    when the second task is not yet connected.
  • ``continuation_text`` — human-readable raw description of the second task
    (preserved even when not connected, so the offer can be explicit instead of
    silently dropping it — never fake success).
  • ``continuation_connected`` — whether ``continuation_kind`` can be executed
    today. ``False`` for unknown/not-yet-wired continuations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["JobCreationDetection", "detect_job_creation", "CONNECTED_CONTINUATIONS"]


# Verb + (optional qualifier) + vaga/posição/requisição. Mirrors the canonical
# wizard-creation veto in ``app/orchestrator/context/navigation_intent.py``
# (``_WIZARD_CREATION_KEYWORDS``) — same source of truth for "this is wizard
# creation, not navigation / not a plan".
_CREATION_RE = re.compile(
    r"\b("
    r"(criar|crie|abrir|abra|abre|publicar)"
    r"\s+(uma\s+|um\s+|a\s+|o\s+)?"
    r"(nova\s+|novo\s+)?"
    r"(vaga|vagas|posi[cç][aã]o|posi[cç][oõ]es|requisi[cç][aã]o|requisi[cç][oõ]es)"
    r")",
    re.IGNORECASE,
)

# "preciso de uma vaga", "quero criar...", "vamos criar..." — looser intent
# phrasings that still mean "start the creation wizard".
_CREATION_INTENT_RE = re.compile(
    r"\b("
    r"(quero|preciso|vamos|gostaria)\s+(de\s+)?(criar|abrir|uma\s+vaga|nova\s+vaga)|"
    r"contratar\b"
    r")",
    re.IGNORECASE,
)

# A plain "publicar a vaga" (no create verb) is publish-only, NOT creation.
_PUBLISH_ONLY_RE = re.compile(
    r"^\s*(publicar|sincronizar|sincroniza|publica)\b",
    re.IGNORECASE,
)

# Canonical continuation kinds that are already wired end-to-end and may be
# executed after the wizard finishes. Anything not here is captured as text but
# flagged ``continuation_connected=False`` (offer signals it explicitly).
CONNECTED_CONTINUATIONS: dict[str, re.Pattern[str]] = {
    "publish_job": re.compile(r"public", re.IGNORECASE),
    "sync_job": re.compile(r"sincroniz|sync|integra", re.IGNORECASE),
}

# Splits the composite request into [creation, continuation] on the first
# top-level " e " (with optional surrounding context like "e depois").
_COMPOSITE_SPLIT_RE = re.compile(r"\s+e\s+(?:depois\s+|tamb[ée]m\s+|j[áa]\s+)?", re.IGNORECASE)


@dataclass(frozen=True)
class JobCreationDetection:
    is_creation: bool
    continuation_kind: str | None = None
    continuation_text: str | None = None
    continuation_connected: bool = False


def _classify_continuation(text: str) -> tuple[str | None, bool]:
    """Map a raw continuation phrase to a connected continuation kind.

    Returns ``(kind, connected)``. ``kind`` is ``None`` when not connected.
    """
    for kind, pattern in CONNECTED_CONTINUATIONS.items():
        if pattern.search(text):
            return kind, True
    return None, False


def detect_job_creation(message: str | None) -> JobCreationDetection | None:
    """Return a :class:`JobCreationDetection` when ``message`` is a job-creation
    request, else ``None``.

    Pure / side-effect free. Safe to call on every turn.
    """
    if not message or not message.strip():
        return None

    text = message.strip()

    if _PUBLISH_ONLY_RE.search(text):
        return None

    is_creation = bool(_CREATION_RE.search(text) or _CREATION_INTENT_RE.search(text))
    if not is_creation:
        return None

    # Composite? Split on the first top-level " e ". The first segment must hold
    # the creation verb; the rest is the continuation.
    continuation_kind: str | None = None
    continuation_text: str | None = None
    continuation_connected = False

    parts = _COMPOSITE_SPLIT_RE.split(text, maxsplit=1)
    if len(parts) == 2:
        head, tail = parts[0], parts[1].strip()
        head_is_creation = bool(
            _CREATION_RE.search(head) or _CREATION_INTENT_RE.search(head)
        )
        if head_is_creation and tail:
            continuation_text = tail
            continuation_kind, continuation_connected = _classify_continuation(tail)

    return JobCreationDetection(
        is_creation=True,
        continuation_kind=continuation_kind,
        continuation_text=continuation_text,
        continuation_connected=continuation_connected,
    )
