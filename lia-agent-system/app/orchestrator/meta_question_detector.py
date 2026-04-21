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
    # Optional informal lead-in: greeting ("oi", "olá", "bom dia", "ei",
    # "opa"), discourse marker ("olha", "escuta", "então"), or a hedged
    # opener ("será que", "queria saber se"). All optional, all followed
    # by a comma or whitespace. Keeps the "starts at the opener" semantics
    # but tolerates the way recruiters actually type in PT-BR chat.
    r"^\s*"
    r"(?:(?:oi|ol[áa]|ei|opa|bom\s+dia|boa\s+tarde|boa\s+noite|"
    r"olha|escuta|ent[ãa]o|hmm|hum)[,\s]+)?"
    r"(?:lia[,\s]+)?"
    r"(?:(?:ser[áa]\s+que|queria\s+saber\s+se|gostaria\s+de\s+saber\s+se|"
    r"me\s+diz(?:\s+a[ií])?\s+se|sabe\s+me\s+dizer\s+se)[,\s]+)?"
    r"(?:lia[,\s]+)?"
    r"(?:"
    # Pronoun + capability verb. "voce" without accent and slang "vc"/"ce"
    # are first-class citizens in chat — they were the most common false
    # negatives reported after Task #726 shipped.
    r"(?:voc[eê]|vc|c[eê])\s+(?:consegue|sabe|pode|conseguiria|saberia|poderia)|"
    r"consegue|sabe|"
    r"tem\s+como|"
    # "da pra" / "da para" without accent shows up constantly on mobile.
    r"d[áa]\s+(?:pra|para)|"
    r"[ée]\s+poss[íi]vel|"
    r"rola\s+(?:de|pra)|"  # informal: "rola de exportar?"
    r"como\s+(?:eu\s+)?fa[çc]o\s+(?:pra|para)|"
    r"como\s+(?:que\s+)?(?:eu\s+)?(?:fa[çc]o|pe[çc]o)|"
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
    r"(?:"
    # Locations
    r"\bem\s+s[ãa]o\s+paulo\b|\bem\s+sp\b|\bem\s+rj\b|\bem\s+belo\b|\bem\s+curitiba\b|"
    r"\bno\s+rio\b|\bno\s+brasil\b|\bremoto\b|\bpresencial\b|\bh[íi]brido\b|"
    # Tech / skills
    r"\breact\b|\bangular\b|\bvue\b|\bpython\b|\bjava\b|\bjavascript\b|\btypescript\b|\bnode\b|"
    r"\bkotlin\b|\bswift\b|\bgolang\b|\bgo\b|c\+\+|c#|\bruby\b|\bphp\b|"
    r"\baws\b|\bgcp\b|\bazure\b|\bkubernetes\b|\bdocker\b|\bterraform\b|"
    r"\bsql\b|\bpostgres\b|\bmongo\b|\bredis\b|\bkafka\b|\bspark\b|"
    r"\bdevops\b|\bsre\b|\bqa\b|\bbackend\b|\bfrontend\b|\bfullstack\b|\bmobile\b|\bdata\s+science\b|"
    # Status / stage qualifiers (review fix #2): "vagas ativas",
    # "candidatos pendentes", "entrevistas agendadas" etc. carry enough
    # operational specificity to be real commands even with polite phrasing.
    r"\bativ[ao]s?\b|\bpendentes?\b|\babert[ao]s?\b|\bfechad[ao]s?\b|"
    r"\bpausad[ao]s?\b|\barquivad[ao]s?\b|\baprovad[ao]s?\b|\breprovad[ao]s?\b|"
    r"\baprovados?\b|\beliminad[ao]s?\b|\brejeitad[ao]s?\b|"
    r"\bagendad[ao]s?\b|\bcancelad[ao]s?\b|\bconclu[íi]d[ao]s?\b|\bvencid[ao]s?\b|"
    # Pipeline stages
    r"\btriagem\b|\bentrevista\s+(?:t[ée]cnica|final|inicial|com\s+gestor)|"
    r"\bproposta\b|\bonboarding\b|\bshortlist\b|\bbanco\s+de\s+talentos\b|"
    # Senioridade
    r"\bj[úu]nior\b|\bpleno\b|\bs[êe]nior\b|\bespecialista\b|\bestagi[áa]rio\b|\btrainee\b|\blead\b|\bstaff\b|\bprincipal\b|"
    # Time / quantifiers
    r"\b(?:hoje|amanh[ãa]|ontem|semana|m[êe]s|trimestre|ano)\b|"
    r"\bdesta\s+semana\b|\bdo\s+m[êe]s\b|\bda\s+sprint\b|"
    r"\b\d+\s*(?:candidatos?|vagas?|dias?|semanas?|meses?|anos?|h(?:oras?)?)\b|"
    # IDs (vagas, candidatos)
    r"\bv0\d{3,}\b|\bc0\d{3,}\b|\bID\s*\d+\b|"
    # Job titles / functions (jobs/screening domain)
    r"\bdesenvolvedor[ae]s?\b|\bdev(?:eloper)?s?\b|\bengenheir[ao]s?\b|"
    r"\brecrutador[ae]s?\b|\bdesigner\b|\bproduct\s+manager\b|\bscrum\s+master\b|"
    # Proper noun openers: "do João", "da Marina", "para Marco". The
    # uppercase character class must remain case-sensitive even though the
    # rest of the regex runs IGNORECASE — otherwise lowercase fragments
    # like "da pra" get treated as a proper-noun reference and suppress
    # legitimate meta-questions ("dá pra exportar candidatos?").
    r"\bd[oa]\s+(?-i:[A-Z])\w+|\bpara\s+(?-i:[A-Z])\w+"
    r")",
    re.IGNORECASE | re.UNICODE,
)

# Keep the templated reply short, deterministic, and aligned with the LIA
# voice (no emojis, no flattery). The reply tells the user (a) yes the
# platform can do this, (b) how to phrase a real command. We intentionally
# avoid claiming specifics ("o banco tem N candidatos") because the
# inventory check belongs to a real action call.
# Intent-aware reply templates keyed by verb family. Avoids the misleading
# "busca de candidatos" guidance when the user actually asked about a
# different capability (export, scheduling, etc.).
_REPLY_TEMPLATES: dict[str, str] = {
    "search": (
        "Sim, posso buscar candidatos. Para eu executar a busca de verdade, "
        "me passe pelo menos um critério concreto — por exemplo:\n"
        "- \"busque candidatos React em São Paulo\"\n"
        "- \"liste candidatos com experiência em Python sênior\"\n"
        "- \"procure candidatos para a vaga V0042\""
    ),
    "list": (
        "Sim, posso listar. Me diga o que você quer ver (ex.: \"liste vagas "
        "ativas\", \"mostre candidatos da vaga V0042\", \"liste entrevistas "
        "desta semana\")."
    ),
    "create": (
        "Sim, posso criar/cadastrar. Me passe os dados básicos — por exemplo: "
        "\"crie uma vaga de Tech Lead remoto\" ou \"cadastre um candidato "
        "novo com nome, email e skills\"."
    ),
    "schedule": (
        "Sim, posso agendar. Me diga com quem, quando e o tipo — por exemplo: "
        "\"agende entrevista com Marco amanhã às 14h\" ou \"reagende a "
        "entrevista do candidato X para sexta\"."
    ),
    "move": (
        "Sim, posso mover/aprovar/reprovar candidatos. Me diga quais e para "
        "qual etapa — por exemplo: \"mova João para Entrevista Final\" ou "
        "\"aprove os 3 candidatos selecionados para próxima fase\"."
    ),
    "export": (
        "Sim, posso exportar. Me diga o que e em qual formato — por exemplo: "
        "\"exporte candidatos da vaga V0042 em CSV\" ou \"baixe relatório de "
        "pipeline de outubro\"."
    ),
    "send": (
        "Sim, posso enviar mensagens. Me diga para quem e o conteúdo (ou "
        "peça uma mensagem personalizada) — por exemplo: \"envie convite de "
        "entrevista para Marco\"."
    ),
    "generate": (
        "Sim, posso gerar conteúdo. Me diga o tipo — por exemplo: \"gere "
        "uma mensagem de outreach para o candidato X\" ou \"gere relatório "
        "de pipeline da vaga V0042\"."
    ),
    "analyze": (
        "Sim, posso analisar/avaliar/comparar. Me diga o alvo — por exemplo: "
        "\"analise o perfil do candidato X para a vaga V0042\" ou \"compare "
        "os top 3 candidatos da shortlist\"."
    ),
}

_VERB_GROUPS: dict[str, str] = {
    "busca": "search", "buscar": "search", "buscan": "search",
    "pesquisa": "search", "pesquisar": "search", "pesquisan": "search",
    "encontra": "search", "encontrar": "search", "encontran": "search",
    "procura": "search", "procurar": "search", "procuran": "search",
    "lista": "list", "listar": "list", "listan": "list",
    "mostra": "list", "mostrar": "list", "mostran": "list",
    "exibe": "list", "exibi": "list", "exibir": "list", "exiben": "list", "exibin": "list",
    "ver": "list",
    "cria": "create", "criar": "create", "crian": "create",
    "adiciona": "create", "adicionar": "create", "adicionan": "create",
    "cadastra": "create", "cadastrar": "create", "cadastran": "create",
    "registra": "create", "registrar": "create", "registran": "create",
    "agenda": "schedule", "agendar": "schedule", "agendan": "schedule",
    "reagenda": "schedule", "reagendar": "schedule", "reagendan": "schedule",
    "mover": "move", "move": "move", "moven": "move", "mova": "move",
    "avança": "move", "avancar": "move", "avançar": "move",
    "aprova": "move", "aprovar": "move", "aprovan": "move",
    "reprova": "move", "reprovar": "move", "reprovan": "move",
    "rejeita": "move", "rejeitar": "move", "rejeitan": "move",
    "exporta": "export", "exportar": "export", "exportan": "export",
    "baixa": "export", "baixar": "export", "baixan": "export",
    "envia": "send", "enviar": "send", "envian": "send",
    "manda": "send", "mandar": "send", "mandan": "send",
    "comunica": "send", "comunicar": "send", "comunican": "send",
    "gera": "generate", "gerar": "generate", "geran": "generate",
    "analisa": "analyze", "analisar": "analyze", "analisan": "analyze",
    "avalia": "analyze", "avaliar": "analyze", "avalian": "analyze",
    "compara": "analyze", "comparar": "analyze", "comparan": "analyze",
}


def _reply_for_verb(verb: str) -> str:
    """Return the intent-aware reply template for the matched verb.

    Falls back to the search template (the most common case in this product)
    when the verb is recognised but ungrouped, since it preserves the
    operator-friendly guidance pattern.
    """
    group = _VERB_GROUPS.get(verb.lower())
    if group and group in _REPLY_TEMPLATES:
        return _REPLY_TEMPLATES[group]
    return _REPLY_TEMPLATES["search"]


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
        reply=_reply_for_verb(verb),
    )
