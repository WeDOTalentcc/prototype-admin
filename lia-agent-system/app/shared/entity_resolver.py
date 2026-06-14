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


_active_candidate_id: ContextVar[str] = ContextVar("lia_active_candidate_id", default="")


def set_active_candidate(candidate_id: str | None) -> None:
    """Candidato ativo do turno (resolvido por nome, UNAMBIGUO). Tools de
    candidato (view_candidate_profile) usam como fallback quando o LLM nao passa
    candidate_id -- evita crash asyncpg (UUID '') + 'instabilidade tecnica'."""
    _active_candidate_id.set(str(candidate_id) if candidate_id else "")


def get_active_candidate() -> str:
    """Candidato ativo do turno ('' se nenhum/ambiguo)."""
    return _active_candidate_id.get("") or ""


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


# ── Escopo de vaga STICKY por conversa (fix 2026-06-07, live audit #1) ──
# O entity resolver so resolve vaga do historico quando a msg diz "essa vaga".
# Num follow-up sobre candidatos ("detalhes dos 3") nao ha referente -> a vaga
# zerava e list_candidates/rank perdiam o escopo (traziam candidatos de OUTRAS
# vagas). Aqui guardamos a ultima vaga resolvida POR CONVERSA e reaproveitamos
# como fallback. Modulo-level (per-process; conversa termina no restart).
_ACTIVE_VACANCY_BY_CONV: dict[str, str] = {}


def sticky_vacancy(conversation_id: str, resolved_vacancy: str) -> str:
    """Retorna a vaga a usar no turno: a resolvida (e persiste), ou a ultima
    desta conversa quando o turno nao resolveu nenhuma (em vez de zerar)."""
    cid = str(conversation_id or "")
    if resolved_vacancy:
        if len(_ACTIVE_VACANCY_BY_CONV) > 2000:
            _ACTIVE_VACANCY_BY_CONV.clear()  # cap simples anti-leak
        if cid:
            _ACTIVE_VACANCY_BY_CONV[cid] = resolved_vacancy
        return resolved_vacancy
    return _ACTIVE_VACANCY_BY_CONV.get(cid, "") if cid else ""


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
    """items: [(id, title)]. Retorna os titulos que compartilham >=2 tokens
    significativos com a mensagem (ou titulo de 1 token batido exato). Ordena por
    score desc. Funcao PURA.

    P0-B fix (2026-06-14): adiciona fuzzy fallback via SequenceMatcher para tokens
    de vaga. Sem isso, typo de 1 char ("juridoc" vs "juridico") zeraba o overlap
    e o sticky_vacancy fallback retornava a vaga errada.
    Estrategia:
      - Fase 1: overlap exato de tokens (comportamento original)
      - Fase 2: se overlap exato < 2, tenta match fuzzy (ratio >= 0.82) entre
        tokens da mensagem e tokens do titulo
    Score = overlap_exato + 0.5 * overlap_fuzzy (incentiva exato, tolera typo)
    """
    mtok = _tokens(message)
    if not mtok:
        return []
    scored: list[tuple[float, str, str]] = []
    for _id, title in items:
        ttok = _tokens(title)
        if not ttok:
            continue
        # Fase 1: token intersection exata
        exact_overlap = ttok & mtok
        exact_score = len(exact_overlap)

        # Fase 2: fuzzy fallback para tokens sem match exato
        fuzzy_score = 0.0
        if exact_score < 2:
            unmatched_msg = mtok - exact_overlap
            unmatched_ttok = ttok - exact_overlap
            for mt in unmatched_msg:
                for tt in unmatched_ttok:
                    if SequenceMatcher(None, mt, tt).ratio() >= 0.80:
                        fuzzy_score += 1.0  # conta equivalente a token exato (threshold >= 0.80)
                        break  # cada msg-token conta so uma vez

        total = exact_score + fuzzy_score
        # Threshold: >=2 tokens equivalentes (exatos ou fuzzy combinados)
        if total >= 2 or (len(ttok) == 1 and exact_score >= 1):
            scored.append((total, _id, title))
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


def _extract_identifiers(message: str) -> tuple[list[str], list[str], list[str]]:
    """Extrai CPF/email/telefone de uma mensagem (DRY: reusa os patterns do
    pii_masking). Usado para resolver candidato POR identificador sem vazar o valor
    cru ao LLM (resolve-then-strip, ADR-LGPD-002)."""
    if not message:
        return [], [], []
    from app.shared.pii_masking import CPF_PATTERN, EMAIL_PATTERN, PHONE_BR_PATTERN

    cpfs = [m for m in CPF_PATTERN.findall(message) if m]
    emails = [m for m in EMAIL_PATTERN.findall(message) if m]
    phones = [m for m in PHONE_BR_PATTERN.findall(message) if m]
    return cpfs, emails, phones


async def _resolve_candidates_by_identifier(
    message: str, company_id: str, db: Any
) -> list[tuple[str, str]]:
    """Resolve candidato(s) por identificador (CPF/email/telefone) via hash indexado,
    company-scoped. Retorna [(id, name)]. NUNCA usa o identificador cru na query nem no
    hint — só o HASH (resolve-then-strip + minimização Art. 12). Decripta name p/ o hint
    (linhas pós-migração têm name plaintext = NULL)."""
    if not message or not company_id:
        return []
    cpfs, emails, phones = _extract_identifiers(message)
    if not (cpfs or emails or phones):
        return []
    from sqlalchemy import text as _t

    from app.models.candidate import Candidate
    from app.shared.encryption.encrypted_field_mixin import _decrypt

    conds: list[str] = []
    params: dict = {"co": str(company_id)}
    hi = 0
    for raw in cpfs:
        h = Candidate.cpf_hash_for(raw)
        if h:
            conds.append(f"cpf_hash = :h{hi}")
            params[f"h{hi}"] = h
            hi += 1
    for raw in emails:
        h = Candidate.email_hash_for(raw)
        if h:
            conds.append(f"email_hash = :h{hi}")
            params[f"h{hi}"] = h
            hi += 1
    for raw in phones:
        h = Candidate.phone_hash_for(raw)
        if h:
            conds.append(f"phone_hash = :h{hi}")
            params[f"h{hi}"] = h
            hi += 1
    if not conds:
        return []
    r = await db.execute(
        _t(
            "SELECT id, name, name_encrypted FROM candidates "
            "WHERE company_id = CAST(:co AS varchar) "
            f"AND ({' OR '.join(conds)}) LIMIT 10"
        ),
        params,
    )
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for m in r.mappings():
        cid = str(m["id"])
        if cid in seen:
            continue
        seen.add(cid)
        nm = m.get("name") or _decrypt(m.get("name_encrypted")) or ""
        out.append((cid, nm))
    return out


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
                # Fix 2026-06-08: exclude 'Concluída'/'Rascunho' from default
                # disambiguation pool. A user asking "candidates of android"
                # means the ACTIVE job, not a concluded one with the same title.
                # When user mentions 'concluída'/'fechada', the concluded status
                # pool is checked in a second pass (see below).
                "SELECT id, title FROM job_vacancies "
                "WHERE company_id = CAST(:co AS varchar) "
                "AND status IN ('Ativa','Aprovada','Reaberta','Paralisada') LIMIT 400"
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
        # Second pass: if no active match found and user mentions concluded/closed,
        # extend search to Concluída/Rascunho status.
        if not matched:
            _concluded_keywords = {"concluída", "concluido", "fechada", "fechado", "arquivada", "encerrada"}
            _msg_lower = (message or "").lower()
            if any(k in _msg_lower for k in _concluded_keywords):
                try:
                    r2 = await db.execute(
                        _t(
                            "SELECT id, title FROM job_vacancies "
                            "WHERE company_id = CAST(:co AS varchar) "
                            "AND status IN ('Concluída','Rascunho','Arquivada') LIMIT 200"
                        ),
                        {"co": str(company_id)},
                    )
                    concluded_jobs = [(str(m["id"]), m["title"] or "") for m in r2.mappings()]
                    matched = match_titles_in_message(message, concluded_jobs)[:3]
                except Exception:
                    pass
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

    # ── Candidatos por IDENTIFICADOR (CPF/email/telefone) — precede o match por
    #    nome (mais preciso, zero ambiguidade). resolve-then-strip: usa o HASH, nunca
    #    o identificador cru; o hint leva nome+id, nunca o CPF/email. ──
    try:
        _ident = await _resolve_candidates_by_identifier(message, company_id, db)
        if _ident:
            result["candidates"] = _ident
            hints.append(
                "CANDIDATO(S) referido(s) por identificador (use EXATAMENTE este id): "
                + "; ".join(f"'{n}' (id={i})" for i, n in _ident)
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
            _existing_ids = {x[0] for x in result["candidates"]}
            result["candidates"] = result["candidates"] + [
                c for c in cands if c[0] not in _existing_ids
            ]
            if cands:
                hints.append(
                    "CANDIDATO(S) referido(s) (use EXATAMENTE este id): "
                    + "; ".join(f"'{n}' (id={i})" for i, n in cands)
                )
            elif not result["candidates"]:
                hints.append(
                    f"NAO existe candidato com nome ~'{name_q}' na base "
                    "(diga isso claramente; NAO liste todos nem invente)."
                )
    except Exception:
        pass

    result["hint"] = "\n".join(hints)
    return result
