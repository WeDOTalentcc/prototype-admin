"""Pré-resolução determinística de entidades nomeadas (bloqueador-2).

O LLM (mesmo Sonnet) alucina o match de entidade — pediu "Diretor Jurídico",
narrou "Engenheiro de Software" com as 103 vagas na mão. Em vez de confiar no
raciocínio do LLM, resolvemos a vaga/candidato NOMEADO via DB (company-scoped,
fuzzy por tokens) e injetamos um hint FORTE no prompt. Computacional >
inferencial (harness — quando o LLM erra de forma sistemática, escora com guide
computacional).

Multi-tenancy: company_id sempre do contexto (nunca payload). Falha → hint vazio
(fail-open: nunca derruba o turno).
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

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


def match_titles_in_message(message: str, items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """items: [(id, title)]. Retorna os cujo TÍTULO tem >=60% dos tokens (>=1)
    presentes na mensagem. Ordena por nº de tokens casados (desc). Função PURA."""
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
        # em titulos bilingues/parenteticos — ex "Diretor(a) Juridico(a) (Chief Legal
        # Officer)" (5 tokens) vs "diretor juridico" (2) = 40% < 60% -> nao casava a
        # vaga que existe. Agora basta interseccao de 2 tokens significativos (ou
        # titulo de 1 token batido exato).
        if len(overlap) >= 2 or (len(ttok) == 1 and len(overlap) >= 1):
            scored.append((len(overlap), _id, title))
    scored.sort(key=lambda x: -x[0])
    return [(i, t) for _, i, t in scored]


async def resolve_named_entities(message: str, company_id: str, db: Any) -> dict:
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
        result["jobs"] = matched
        if matched:
            hints.append(
                "VAGA(S) que o recrutador referiu (use EXATAMENTE este id; NAO "
                "invente outro titulo): "
                + "; ".join(f"'{t}' (id={i})" for i, t in matched)
            )
    except Exception:
        pass

    # ── Candidatos: extrai sequencia Capitalizada (nome) e busca por nome ──
    try:
        m = re.search(
            r"(?:perfil|candidat[oa]|fit)\s+(?:d[eo]\s+|completo\s+d[eo]\s+)?"
            r"([A-ZÀ-Ý][\wÀ-ÿ]+(?:\s+[A-ZÀ-Ý][\wÀ-ÿ]+){0,3})",
            message,
        )
        name = m.group(1).strip() if m else ""
        if name and len(_tokens(name)) >= 1:
            like = "%" + "%".join(name.split()) + "%"
            r = await db.execute(
                _t(
                    "SELECT id, name FROM candidates "
                    "WHERE company_id = CAST(:co AS varchar) AND name ILIKE :lk "
                    "LIMIT 5"
                ),
                {"co": str(company_id), "lk": like},
            )
            cands = [(str(x["id"]), x["name"]) for x in r.mappings()]
            result["candidates"] = cands
            if cands:
                hints.append(
                    "CANDIDATO(S) referido(s): "
                    + "; ".join(f"'{n}' (id={i})" for i, n in cands)
                )
            elif name:
                hints.append(
                    f"NAO existe candidato com nome ~'{name}' na base (diga isso; "
                    "NAO liste todos nem invente)."
                )
    except Exception:
        pass

    result["hint"] = "\n".join(hints)
    return result
