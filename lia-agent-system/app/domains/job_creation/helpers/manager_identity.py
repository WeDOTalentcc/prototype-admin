"""Captura deterministica da identidade do gestor (nome + email) a partir do
texto CRU do recrutador -- server-side, ANTES do masking LGPD.

Motivacao (audit 2026-06-05): no caminho ATIVO do wizard (orchestrator), todo
inbound e mascarado antes do LLM (Presidio NER apaga PERSON, regex apaga email).
O LLM fica cego ao nome do gestor e o INVENTA a cada turno (Carlos Mendes,
Ricardo Almeida...). A captura tem que ser deterministica no servidor, igual ja
era feito com o email. Aqui ficam as duas fontes determinISTICAS:

1. derive_name_from_email("paulo.moraes@x") -> "Paulo Moraes"  (sinal forte)
2. extract_manager_name_from_text("o gestor e Paulo Moraes")    (texto cru)

Nunca inventa: retorna None quando nao ha sinal plausivel -- a LIA entao
PERGUNTA em vez de chutar. A proveniencia e declarada pelo chamador (sugestao a
confirmar). Espelha a decisao Paulo 2026-05-31 (email determinISTICo, nunca pelo
LLM), agora estendida ao nome (audit 2026-06-05).

Canonical: este modulo e a UNICA fonte da derivacao nome<-email. O no do grafo
``intake.py`` importa daqui (DRY -- antes tinha copia local _derive_name_from_email).
"""
from __future__ import annotations

import re
import unicodedata

# Mailboxes genericas: nao geram nome de pessoa (rh@, vagas@, contato@...).
_GENERIC_MAILBOX_PREFIXES = {
    "rh", "rh2", "recrutamento", "vagas", "jobs", "talent", "talentos",
    "recruiting", "hr", "careers", "carreiras", "admin", "info",
    "atendimento", "suporte", "comercial", "contato", "contato2",
    "no-reply", "noreply", "naoresponda", "sac", "financeiro", "ti",
}

# Tokens que NUNCA sao nome de pessoa (papel, senioridade, contrato, modelo,
# respostas HITL, departamentos comuns). Usados para rejeitar falso-positivo na
# extracao por texto cru.
_NON_NAME_TOKENS = {
    "gestor", "gestora", "responsavel", "manager", "chefe", "lider",
    "diretor", "diretora", "gerente", "coordenador", "coordenadora",
    "senior", "senior", "junior", "pleno", "especialista", "head", "lead",
    "estagiario", "trainee", "analista", "assistente", "auxiliar",
    "clt", "pj", "estagio", "temporario", "freelancer", "freela",
    "remoto", "hibrido", "presencial", "onsite",
    "sim", "nao", "ok", "okay", "aprovado", "aprovada", "certo", "isso",
    "tecnologia", "marketing", "vendas", "financas", "financeiro", "rh",
    "produto", "engenharia", "comercial", "operacoes", "juridico",
    "vaga", "cargo", "empresa", "email", "nome", "gente", "pessoal",
}

# Sinaliza que a frase fala de gestor/responsavel (gate de contexto).
_MANAGER_CONTEXT_RE = re.compile(
    r"\b(gestor|gestora|respons[aá]vel|reporta|manager|chefe|l[ií]der)\b",
    re.IGNORECASE,
)

# Captura "<conector> <Nome [Sobrenome...]>" (1 a 4 tokens alfabeticos).
# Conectores: se chama/chamado/chamada/eh/é/e (com ou sem acento)/:/=.
# "e" sem acento e comum (gente digita sem acento) -- gateado por contexto de
# gestor + rejeicao de tokens nao-nome, entao nao captura a conjuncao "e".
_NAME_AFTER_RE = re.compile(
    r"(?:\bse\s+chama\b|\bchamad[oa]\b|\bchama\b|\beh\b|\bé\b|\be\b|:|=)\s*"
    r"([A-Za-zÀ-ÿ]{2,}(?:\s+(?:d[aeiou]s?\s+)?[A-Za-zÀ-ÿ]{2,}){0,3})",
    re.IGNORECASE,
)

# Captura "reporta (a|ao|para|pro) <Nome>" e "gestor[a] <Nome>" direto.
_NAME_REPORTS_RE = re.compile(
    r"\breporta\s+(?:a|ao|para|pro)\s+"
    r"([A-Za-zÀ-ÿ]{2,}(?:\s+(?:d[aeiou]s?\s+)?[A-Za-zÀ-ÿ]{2,}){0,3})",
    re.IGNORECASE,
)

_EMAIL_LIKE_RE = re.compile(r"\S+@\S+")


def derive_name_from_email(email: str | None) -> str | None:
    """Deriva um nome-candidato do prefixo do email (paulo.moraes@x -> Paulo
    Moraes). Heuristica conservadora: usa so o local-part antes do @, separa por
    . _ -, descarta tokens numericos e mailboxes genericas (rh@, contato@...).
    Retorna None quando nao da um nome plausivel -- a LIA entao PERGUNTA.
    """
    if not email or "@" not in email:
        return None
    local = email.split("@", 1)[0].strip().lower()
    parts = [t for t in re.split(r"[._\-]+", local) if t and not t.isdigit()]
    if (
        not parts
        or local in _GENERIC_MAILBOX_PREFIXES
        or parts[0] in _GENERIC_MAILBOX_PREFIXES
    ):
        return None
    words = [t.capitalize() for t in parts if len(t) >= 2]
    if not words:
        return None
    return " ".join(words)


def _norm(value: str) -> str:
    return (
        unicodedata.normalize("NFKD", value or "")
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .strip()
    )


def _title(phrase: str) -> str:
    # Title-case preservando conectivos minusculos (Maria da Silva).
    lower_connectives = {"da", "de", "di", "do", "du", "das", "dos", "e"}
    out = []
    for i, tok in enumerate(phrase.split()):
        n = _norm(tok)
        if i > 0 and n in lower_connectives:
            out.append(n)
        else:
            out.append(tok[:1].upper() + tok[1:].lower())
    return " ".join(out)


def _looks_like_name(phrase: str) -> bool:
    """Frase parece nome de pessoa: 1-4 tokens, todos alfabeticos, nenhum token
    'forte' (nao-conectivo) e papel/senioridade/resposta-HITL.
    """
    if not phrase:
        return False
    toks = phrase.split()
    if not (1 <= len(toks) <= 4):
        return False
    connectives = {"da", "de", "di", "do", "du", "das", "dos", "e"}
    strong = [t for t in toks if _norm(t) not in connectives]
    if not strong:
        return False
    for t in strong:
        n = _norm(t)
        if len(n) < 2 or not n.isalpha() or n in _NON_NAME_TOKENS:
            return False
    return True


def _clean(cand: str) -> str:
    # Remove pontuacao de borda e colapsa espacos.
    cand = re.sub(r"[^A-Za-zÀ-ÿ\s]", " ", cand or "")
    return re.sub(r"\s+", " ", cand).strip()


def extract_manager_name_from_text(
    raw_text: str | None,
    *,
    manager_context_hint: bool = False,
) -> str | None:
    """Extrai o nome do gestor do texto CRU do recrutador. Deterministico.

    - ``manager_context_hint``: True quando a ultima fala da LIA pediu o nome do
      gestor (ex.: "qual o nome do gestor?"). Habilita capturar uma resposta
      "crua" (so o nome, sem conector) e relaxa o gate de contexto.
    - Em mensagens de CORRECAO ("nao e Carlos e Paulo Moraes"), pega o ULTIMO
      candidato plausivel -- a correcao vence.
    - Nunca retorna email-prefix nem papel/senioridade. None se sem sinal.
    """
    if not raw_text:
        return None
    text = raw_text.strip()
    has_ctx = manager_context_hint or bool(_MANAGER_CONTEXT_RE.search(text))
    if not has_ctx:
        return None

    # Remove emails para nao capturar prefixo de email como nome.
    text_wo_email = _EMAIL_LIKE_RE.sub(" ", text)

    candidates: list[str] = []
    candidates.extend(_NAME_AFTER_RE.findall(text_wo_email))
    candidates.extend(_NAME_REPORTS_RE.findall(text_wo_email))

    # ULTIMO candidato plausivel vence (correcao "nao e X e Y" -> Y).
    for cand in reversed(candidates):
        name = _clean(cand)
        if name and _looks_like_name(name):
            return _title(name)

    # Resposta crua a um pedido explicito de nome ("qual o nome do gestor?"
    # -> usuario responde "Paulo Moraes"). So quando a LIA pediu (hint).
    if manager_context_hint:
        bare = _clean(text_wo_email)
        if bare and _looks_like_name(bare):
            return _title(bare)

    return None
