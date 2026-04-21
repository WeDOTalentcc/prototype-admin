"""
CandidateSearchService — fonte canônica de busca textual de candidatos.

Criado em Task #727 para resolver:
1. Bug do LEFT JOIN em sourcing_actions._search_candidates que virava INNER JOIN
   (predicado `vc.company_id = :co` no WHERE descartava linhas com NULL do JOIN).
2. Cinco implementações paralelas de "search_candidates" — agora consolidadas
   neste service único; consumidores ficam finos.

Escopo (parâmetro `scope`):
  - "local"  : só candidatos vinculados a `vacancy_candidates` da empresa.
  - "global" : pool de candidatos sem filtro de empresa (banco compartilhado).
  - "both"   : tenta local; se vazio, cai para global e marca `fellback_to_global=True`.

Default é "both" para evitar a UX ruim de "0 resultados" em tenants novos sem
vacancy_candidates ainda. O fallback é sempre explícito na resposta.
"""
from __future__ import annotations

import logging
from typing import Any, Literal

from sqlalchemy import text

from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

Scope = Literal["local", "global", "both"]

_VALID_SCOPES: set[str] = {"local", "global", "both"}


# SELECT base — colunas que TODOS os consumidores hoje precisam.
# Mantém compatibilidade com sourcing_actions (id, name, current_title,
# current_company, location_city, seniority_level) e talent_tool_registry
# (location_state, technical_skills, years_of_experience, lia_score,
# skills_match_percentage, status).
_SELECT_FIELDS = """
    c.id,
    c.name,
    c.current_title,
    c.current_company,
    c.location_city,
    c.location_state,
    c.seniority_level,
    c.technical_skills,
    c.years_of_experience,
    c.lia_score,
    c.skills_match_percentage,
    c.status
"""


def _build_text_predicate() -> str:
    """Predicado de match textual reutilizado por local e global."""
    return """(
        :query = ''
        OR c.name ILIKE :qlike
        OR c.current_title ILIKE :qlike
        OR c.current_company ILIKE :qlike
        OR c.location_city ILIKE :qlike
        OR :query = ANY(c.technical_skills)
    )"""


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "name": row.name,
        "current_title": row.current_title,
        "current_company": row.current_company,
        "location_city": row.location_city,
        "location_state": row.location_state,
        "seniority_level": row.seniority_level,
        "technical_skills": list(row.technical_skills or []),
        "years_of_experience": row.years_of_experience,
        "lia_score": row.lia_score,
        "skills_match_percentage": row.skills_match_percentage,
        "status": row.status,
    }


async def search_candidates(
    query: str,
    company_id: str | None,
    *,
    scope: Scope = "both",
    limit: int = 10,
    location: str | None = None,
    min_experience: int | None = None,
) -> dict[str, Any]:
    """Busca canônica de candidatos por texto livre.

    Default scope rationale (Task #727):
        Default `scope="both"` é intencional. UX esperada: ao buscar,
        priorizamos candidatos da empresa (local) e — se não houver —
        caímos automaticamente para o pool global, sinalizando o
        fallback via `fellback_to_global=True`. Isto evita que o
        recrutador veja "0 resultados" quando a empresa ainda não
        possui candidatos vinculados (cenário comum em onboarding).
        Consumidores que NÃO querem fallback devem passar `scope="local"`
        ou `scope="global"` explicitamente.

    Args:
        query: termo de busca livre (nome, cargo, skill, cidade, empresa).
        company_id: tenant; obrigatório quando `scope` é "local" ou "both".
        scope: "local" | "global" | "both".
        limit: 1..50.
        location: filtro opcional por cidade/estado.
        min_experience: filtro opcional por anos mínimos de experiência.

    Returns:
        dict com:
          - status: "ok" | "error"
          - candidates: list[dict]
          - total: int
          - scope_used: scope efetivamente aplicado ("local" ou "global")
          - fellback_to_global: bool — True quando local não retornou nada e
            caímos para global automaticamente.
          - error: str opcional quando status="error".
    """
    if scope not in _VALID_SCOPES:
        return {
            "status": "error",
            "candidates": [],
            "total": 0,
            "scope_used": scope,
            "fellback_to_global": False,
            "error": f"scope inválido: {scope!r}. Use 'local', 'global' ou 'both'.",
        }

    if not query or not query.strip():
        return {
            "status": "error",
            "candidates": [],
            "total": 0,
            "scope_used": scope,
            "fellback_to_global": False,
            "error": "query vazia.",
        }

    if scope in ("local", "both") and not company_id:
        return {
            "status": "error",
            "candidates": [],
            "total": 0,
            "scope_used": scope,
            "fellback_to_global": False,
            "error": "company_id obrigatório para scope 'local' ou 'both'.",
        }

    safe_limit = max(1, min(int(limit), 50))
    q = query.strip()
    bind: dict[str, Any] = {
        "query": q,
        "qlike": f"%{q}%",
        "lim": safe_limit,
        "loc": f"%{location}%" if location else "",
        "use_loc": 1 if location else 0,
        "min_exp": int(min_experience) if min_experience is not None else 0,
        "use_exp": 1 if min_experience is not None else 0,
    }

    text_pred = _build_text_predicate()
    extra_filters = """
        AND (:use_loc = 0 OR c.location_city ILIKE :loc OR c.location_state ILIKE :loc)
        AND (:use_exp = 0 OR (c.years_of_experience IS NOT NULL AND c.years_of_experience >= :min_exp))
    """

    rows: list[Any] = []
    scope_used: str = scope
    fellback = False

    try:
        async with AsyncSessionLocal() as db:
            if scope in ("local", "both"):
                # Filtro company_id via EXISTS — não usa JOIN para evitar
                # duplicação de linhas quando candidato está em N vagas, e
                # mantém claro que o predicado de tenant nunca é opcional.
                local_sql = f"""
                    SELECT {_SELECT_FIELDS}
                    FROM candidates c
                    WHERE c.is_active = TRUE
                      AND EXISTS (
                          SELECT 1 FROM vacancy_candidates vc
                          WHERE vc.candidate_id = c.id
                            AND vc.company_id = :co
                      )
                      AND {text_pred}
                      {extra_filters}
                    ORDER BY c.lia_score DESC NULLS LAST, c.name
                    LIMIT :lim
                """
                local_bind = dict(bind, co=str(company_id))
                result = await db.execute(text(local_sql), local_bind)
                rows = list(result.fetchall())
                scope_used = "local"

            if scope == "global" or (scope == "both" and not rows):
                # Pool global — sem filtro de tenant. Útil para tenants que
                # ainda não têm vacancy_candidates ou para sourcing inicial.
                global_sql = f"""
                    SELECT {_SELECT_FIELDS}
                    FROM candidates c
                    WHERE c.is_active = TRUE
                      AND {text_pred}
                      {extra_filters}
                    ORDER BY c.lia_score DESC NULLS LAST, c.name
                    LIMIT :lim
                """
                result = await db.execute(text(global_sql), bind)
                rows = list(result.fetchall())
                fellback = scope == "both"
                scope_used = "global"
    except Exception as exc:
        logger.exception("[candidate_search] query falhou: %s", exc)
        return {
            "status": "error",
            "candidates": [],
            "total": 0,
            "scope_used": scope_used,
            "fellback_to_global": fellback,
            "error": str(exc),
        }

    candidates = [_row_to_dict(r) for r in rows]
    return {
        "status": "ok",
        "candidates": candidates,
        "total": len(candidates),
        "scope_used": scope_used,
        "fellback_to_global": fellback,
    }
