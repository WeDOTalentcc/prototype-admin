"""
Meta-question detector — Task #726.

Recognises capability/meta questions ("consegue buscar candidatos?",
"você sabe agendar entrevista?") and short-circuits them with an informational
response instead of letting the action_executor or LLM cascade execute the
underlying action with garbage params.

Invariants
----------
- A meta-question MUST start with a capability opener pronoun pattern
  ("consegue", "você sabe", "tem como", "dá pra/para", "é possível",
  "como faço pra/para", "você pode", "pode me", "dá").
- The action verb that follows MUST be one of the known platform verbs
  (busca, lista, mostra, cria, agenda, move, exporta, gera, envia, etc.).
- The message MUST NOT contain a concrete operational filter (proper noun,
  known tech keyword, location prefix, numeric quantifier). If a filter is
  present we treat the message as a real command (even if phrased as a
  question), to avoid false positives that swallow valid searches like
  "consegue buscar candidatos React em SP?".

Fallbacks are explicit: if no opener matches, return ``None`` and the
caller proceeds with the regular pipeline. There is no silent default.
"""
from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass

logger = logging.getLogger(__name__)


_CAPABILITY_OPENERS = re.compile(
    r"^\s*(?:lia[,\s]+)?(?:"
    r"voc[eê]\s+(?:consegue|sabe|pode|consegueria)|"
    r"consegue|sabe|"
    r"tem\s+como|"
    r"d[áa]\s+(?:pra|para)|"
    r"[ée]\s+poss[íi]vel|"
    r"como\s+(?:eu\s+)?fa[çc]o\s+(?:pra|para)|"
    r"como\s+(?:eu\s+)?pe[çc]o|"
    r"pode\s+me|"
    r"poderia"
    r")\b",
    re.IGNORECASE | re.UNICODE,
)

# Verbs that signal an "action ask" — the user is asking whether the platform
# can perform one of these. If the opener matches but no action verb follows,
# we don't treat it as a meta-question (e.g. "consegue dormir?" — out of scope,
# let the LLM cascade handle it as small talk).
_ACTION_VERBS = re.compile(
    r"\b(?:"
    r"busca[rn]?|pesquisa[rn]?|encontra[rn]?|procura[rn]?|"
    r"lista[rn]?|listar|mostra[rn]?|exibe[rn]?|ver|"
    r"cria[rn]?|criar|adiciona[rn]?|cadastra[rn]?|registra[rn]?|"
    r"agenda[rn]?|agendar|reagenda[rn]?|"
    r"mover|move[rn]?|mova|avan[çc]a[rn]?|aprovar?|reprovar?|rejeitar?|"
    r"exporta[rn]?|baixa[rn]?|"
    r"envia[rn]?|enviar|manda[rn]?|comunica[rn]?|"
    r"gera[rn]?|gerar|"
    r"analisa[rn]?|avalia[rn]?|comparar?|"
    r"triage[mn]?|triar|"
    r"sincroniza[rn]?|importa[rn]?|"
    r"abrir|abre[rn]?|fecha[rn]?|pausa[rn]?|reabri[rn]?"
    r")\b",
    re.IGNORECASE | re.UNICODE,
)

# Concrete operational filter signals. If ANY of these appear, the message is
# specific enough to be a real command, so we don't intercept.
_SPECIFIC_FILTERS = re.compile(
    r"\b(?:"
    # Locations
    r"em\s+s[ãa]o\s+paulo|em\s+sp\b|em\s+rj\b|em\s+belo|em\s+curitiba|"
    r"no\s+rio\b|no\s+brasil|remoto|presencial|h[íi]brido|"
    # Tech / skills
    r"react|angular|vue|python|java\b|javascript|typescript|node\b|"
    r"kotlin|swift|golang|\bgo\b|c\+\+|\bc#\b|ruby|php|"
    r"aws|gcp|azure|kubernetes|docker|terraform|"
    r"sql\b|postgres|mongo|redis|kafka|spark|"
    r"devops|sre\b|qa\b|backend|frontend|fullstack|mobile|data\s+science|"
    # Quantifiers / IDs
    r"\d+\s*(?:candidatos?|vagas?|dias?|semanas?|meses?)|"
    r"v0\d{3,}|"
    # Proper noun openers: "do João", "da Marina"
    r"d[oa]\s+[A-Z]"
    r")\b",
    re.IGNORECASE | re.UNICODE,
)

# Keep the templated reply short, deterministic, and aligned with the LIA
# voice (no emojis, no flattery). The reply tells the user (a) yes the
# platform can do this, (b) how to phrase a real command. We intentionally
# avoid claiming specifics ("o banco tem N candidatos") because the
# inventory check belongs to a real action call.
_INFORMATIONAL_REPLY = (
    "Sim, posso fazer isso. Para eu executar a busca de verdade, me passe "
    "pelo menos um critério concreto — por exemplo:\n"
    "- \"busque candidatos React em São Paulo\"\n"
    "- \"liste candidatos com experiência em Python sênior\"\n"
    "- \"procure candidatos para a vaga V0042\"\n\n"
    "Quanto mais específico (skill, senioridade, localização ou vaga), "
    "melhor o resultado."
)


@dataclass(frozen=True)
class MetaQuestionResult:
    matched_opener: str
    matched_verb: str
    reply: str


# ── Telemetry — aggregated counters only (no PII) ────────────────────────────
_LOCK = threading.Lock()
_COUNT_TOTAL: int = 0
_COUNT_BY_VERB: dict[str, int] = {}


def get_meta_question_stats() -> dict[str, object]:
    """Snapshot of meta-question interception counters.

    Exposed via ``GET /api/v1/orchestrator/health`` (same surface used by
    ``domain_mappings.get_fallback_stats``) so operators can monitor
    prevalence in production. Aggregated counts only — request identifiers
    stay in the structured info log.
    """
    with _LOCK:
        return {
            "total": _COUNT_TOTAL,
            "by_verb": dict(
                sorted(_COUNT_BY_VERB.items(), key=lambda kv: -kv[1])
            ),
        }


def reset_meta_question_stats() -> None:
    """Clear meta-question counters (testing helper)."""
    global _COUNT_TOTAL
    with _LOCK:
        _COUNT_TOTAL = 0
        _COUNT_BY_VERB.clear()


def _record(verb: str) -> None:
    global _COUNT_TOTAL
    with _LOCK:
        _COUNT_TOTAL += 1
        _COUNT_BY_VERB[verb] = _COUNT_BY_VERB.get(verb, 0) + 1


def detect_meta_capability_question(message: str) -> MetaQuestionResult | None:
    """Return a ``MetaQuestionResult`` if ``message`` is a capability question.

    Returns ``None`` when the message is a real command, small talk, or
    anything outside the meta-question shape. Caller should fall through to
    the normal pipeline in that case.
    """
    if not message:
        return None
    text = message.strip()
    if not text:
        return None
    # Sanity cap — capability questions are short by nature; long messages
    # are almost always real commands or descriptions.
    if len(text) > 220:
        return None

    opener_match = _CAPABILITY_OPENERS.search(text)
    if not opener_match:
        return None

    # Verb MUST appear close to the opener — otherwise we risk false positives
    # on sentences like "Como faço para contratar um dev que busca desafios?".
    # We accept the verb if it sits within ~40 chars (~6 short words) after
    # the opener ends.
    tail = text[opener_match.end() : opener_match.end() + 40]
    verb_match = _ACTION_VERBS.search(tail)
    if not verb_match:
        return None

    if _SPECIFIC_FILTERS.search(text):
        # Looks specific enough to be a real command — let the action
        # executor handle it.
        return None

    verb = verb_match.group(0).lower()
    _record(verb)
    logger.info(
        "[meta_question] intercepted capability question",
        extra={
            "matched_opener": opener_match.group(0).strip().lower(),
            "matched_verb": verb,
            "message_len": len(text),
        },
    )
    return MetaQuestionResult(
        matched_opener=opener_match.group(0).strip().lower(),
        matched_verb=verb,
        reply=_INFORMATIONAL_REPLY,
    )
