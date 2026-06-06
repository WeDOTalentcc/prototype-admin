"""Pré-resolução determinística de entidades nomeadas (bloqueador-2).

O LLM (mesmo Sonnet) alucina o match de entidade — pediu "Diretor Jurídico",
narrou "Engenheiro de Software" com as 103 vagas na mão. Em vez de confiar no
raciocínio do LLM, resolvemos a vaga/candidato NOMEADO via DB (company-scoped,
fuzzy) e injetamos um hint FORTE no prompt. Computacional > inferencial (harness).

Multi-tenancy: company_id sempre do contexto (nunca payload). Falha → hint vazio
(fail-open: nunca derruba o turno).
"""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any
from contextvars import ContextVar

# Vaga ativa do turno (resolvida por nome OU referente cross-turn). Tools
# inerentemente vacancy-scoped (rank/list_candidates) usam como FALLBACK
# computacional quando o LLM não passa vacancy_id -- "computacional > inferencial"
# (CLAUDE.md). Reset a cada turno (set pelo SSE com a resolução atual): query
# global ('liste todos') -> '' -> sem filtro; 'dessa vaga' -> id -> filtra.
_active_vacancy_id: ContextVar[str] = ContextVar("lia_active_vacancy_id", default="")


def set_active_vacancy(vacancy_id: str | None) -> None:
    """Marca a vaga ativa do turno (ou limpa com '' / None)."""
    _active_vacancy_id.set(str(vacancy_id) if vacancy_id else "")


def get_active_vacancy() -> str:
    """Vaga ativa do turno ('' se nenhuma). Fallback p/ tools vacancy-scoped."""
    return _active_vacancy_id.get("") or ""


_STOPWORDS = {
    "de", "da", "do", "das", "dos", "a", "o", "e", "para", "por", "com", "em",
    "na", "no", "vaga", "vagas", "candidato", "candidata", "candidatos", "perfil",
    "rankeie", "rankear", "ranqueie", "pipeline", "funil", "mostre", "mostra",
    "ver", "veja", "liste", "lista", "ativa", "ativas", "aberta", "abertas",
    "que", "esta", "está", "tem", "qual", "quais", "me", "sobre",
}


def _norm(s: str) -> str:
    """lowercase + remove acentos + remove pontuação (mantém espaços)."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _tokens(s: str) -> set[str]:
    return {t for t in _norm(s).split() if len(t) > 2 and t not in _STOPWORDS}


# ── Resolução de candidato por NOME (fuzzy, sem pg_trgm) ──
# Fix P1 2026-06-06: o extractor antigo exigia gatilho + Capitalizado + de/do,
# falhando em "tem felipe almeida na base" (sem gatilho/lowercase) e "perfil da
# yasmim reis" (typo + "da"). Agora: extração case-insensitive + match fuzzy
# (difflib) que tolera typo de 1 letra, sem depender de pg_trgm.
_NAME_TRIGGER = re.compile(
    r"(?:perfil|candidat[oa]s?|fit|abrir|ver|veja|mostr\w+|quem|sobre|tem)\b(.*)",
    re.IGNORECASE | re.DOTALL,
)
_NAME_NA_BASE = re.compile(r"(.+?)\s+na\s+base\b", re.IGNORECASE)
_NAME_NOISE = {"base", "completo", "favor", "agora"}


def _extract_name_query(message: str) -> str:
    """Extrai a sequência de nome de candidato referida (sem exigir gatilho+
    maiúscula+de/do como antes). Filtra stopwords/ruído. '' se nada parecer nome.
    Função PURA."""
    if not message:
        return ""
    region = ""
    m = _NAME_NA_BASE.search(message)
    if m:
        region = m.group(1)
    else:
        m = _NAME_TRIGGER.search(message)
        if m:
            region = m.group(1)
    toks = [
        t for t in region.split()
        if _norm(t) not in _STOPWORDS
        and _norm(t) not in _NAME_NOISE
        and len(_norm(t)) >= 2
    ]
    return " ".join(toks[:4])


def _best_fuzzy_match(
    query: str, names: list[tuple[str, str]], threshold: float = 0.72
) -> list[tuple[str, str]]:
    """names: [(id, name)]. Casa por (a) containment de TODAS as palavras da query
    no nome (score 1.0 — pega 1º nome e nome exato) ou (b) similaridade difflib
    >= threshold (tolera typo de 1 letra). Ordena por score desc. Função PURA."""
    q = _norm(query)
    qwords = [w for w in q.split() if w]
    if not qwords:
        return []
    scored: list[tuple[float, str, str]] = []
    for _id, name in names:
        n = _norm(name)
        if not n:
            continue
        contained = all(w in n for w in qwords)
        score = 1.0 if contained else SequenceMatcher(None, q, n).ratio()
        if score >= threshold:
            scored.append((score, _id, name))
    scored.sort(key=lambda x: -x[0])
    return [(i, nm) for _, i, nm in scored]


def match_titles_in_message(message: str, items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """items: [(id, title)]. Retorna os títulos que compartilham >=2 tokens
    significativos com a mensagem (ou título de 1 token batido exato). Ordena por
    nº de tokens casados (desc). Função PURA."""
    mtok = _tokens(message)
    if not mtok:
        return []
    scored: list[tuple[int, str, str]] = []
    for _id, title in items:
        ttok = _tokens(title)
        if not ttok:
            continue
        overlap = ttok & mtok
        # Fix P0 2026-06-06: antes exigia 60% dos tokens do TITULO, o que falhava
        # em titulos bilingues/parenteticos. Agora basta interseccao de 2 tokens
        # significativos (ou titulo de 1 token batido exato).
        if len(overlap) >= 2 or (len(ttok) == 1 and len(overlap) >= 1):
            scored.append((len(overlap), _id, title))
    scored.sort(key=lambda x: -x[0])
    return [(i, t) for _, i, t in scored]


# Referente a vaga SEM nome ("dessa/essa vaga", "a vaga", "dela") -- fix
# cross-turn 2026-06-06: permite resolver a vaga da HISTÓRIA quando o usuário não
# repete o nome ("temos a vaga X?" -> "liste os candidatos dessa vaga"). Sem
# isto o LLM perdia o id e chamava rank/list_candidates com vacancy="" (funil
# global / vazio) -- os 24 candidatos da vaga não eram vistos (transcript Paulo).
_VACANCY_REFERENT_RE = re.compile(
    r"\b(?:d?ess[ae]s?|d?est[ae]s?|ness[ae]s?|naquel[ae]s?|aquel[ae]s?|a|da|na|"
    r"para\s+a|pra)\s+(?:vagas?|posi[çc][ãa]o|requisi[çc][ãa]o)\b"
    r"|\bdela\b|\bnela\b",
    re.IGNORECASE,
)


def _has_vacancy_referent(message: str) -> bool:
    """True se a msg refere uma vaga por artigo/pronome SEM nome ('dessa vaga',
    'a vaga', 'dela'). Usado p/ resolver a vaga da história recente."""
    return bool(_VACANCY_REFERENT_RE.search(message or ""))


async def resolve_named_entities(
    message: str, company_id: str, db: Any, history_text: str = ""
) -> dict:
    """Resolve vaga(s)/candidato(s) nomeados na mensagem. Retorna {jobs, candidates, hint}."""
    from sqlalchemy import text as _t

    result: dict = {"jobs": [], "candidates": [], "hint": ""}
    if not message or not company_id:
        return result
    hints: list[str] = []

    # ── Vagas: carrega titulos nao-arquivados (company-scoped) e casa por tokens ──
    try:
        r = await db.execute(
            _t(
                "SELECT id, title FROM job_vacancies "
                "WHERE company_id = CAST(:co AS varchar) "
                "AND status IN ('Ativa','Aprovada','Rascunho','Concluída') LIMIT 400"
            ),
            {"co": str(company_id)},
        )
        jobs = [(str(m["id"]), m["title"] or "") for m in r.mappings()]
        matched = match_titles_in_message(message, jobs)[:3]
        _from_history = False
        # Cross-turn: "liste os candidatos DESSA vaga" não tem nome -> resolve a
        # vaga mais relevante da HISTÓRIA recente quando há referente sem nome.
        if not matched and history_text and _has_vacancy_referent(message):
            matched = match_titles_in_message(history_text, jobs)[:1]
            _from_history = bool(matched)
        result["jobs"] = matched
        if matched:
            _ctx = (
                " (vaga em contexto -- o usuário disse 'essa/dessa vaga')"
                if _from_history else ""
            )
            hints.append(
                "VAGA(S) que o recrutador referiu" + _ctx + " (use EXATAMENTE "
                "este id; NAO invente outro titulo): "
                + "; ".join(f"'{t}' (id={i})" for i, t in matched)
            )
    except Exception:
        pass

    # ── Candidatos: extrai nome (case-insensitive) e casa fuzzy (difflib) ──
    try:
        name_q = _extract_name_query(message)
        words = [w for w in _norm(name_q).split() if len(w) >= 2]
        if name_q and words:
            like = " OR ".join(f"name ILIKE :w{i}" for i in range(len(words)))
            params: dict = {"co": str(company_id)}
            for i, w in enumerate(words):
                params[f"w{i}"] = f"%{w}%"
            r = await db.execute(
                _t(
                    "SELECT id, name FROM candidates "
                    "WHERE company_id = CAST(:co AS varchar) "
                    f"AND ({like}) LIMIT 40"
                ),
                params,
            )
            pool = [(str(x["id"]), x["name"]) for x in r.mappings()]
            cands = _best_fuzzy_match(name_q, pool)[:5]
            result["candidates"] = cands
            if cands:
                hints.append(
                    "CANDIDATO(S) referido(s) (use EXATAMENTE este id): "
                    + "; ".join(f"'{n}' (id={i})" for i, n in cands)
                )
            else:
                hints.append(
                    f"NAO existe candidato com nome ~'{name_q}' na base "
                    "(diga isso claramente; NAO liste todos nem invente)."
                )
    except Exception:
        pass

    result["hint"] = "\n".join(hints)
    return result
