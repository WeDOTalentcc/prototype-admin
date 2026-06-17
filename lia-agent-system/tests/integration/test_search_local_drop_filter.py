"""Integração (DB real) — search_local_candidates: drop-filter-if-zero (P0-1).

Pina o defeito que zerava a busca local: filtros estruturados derivados do LLM
(industries, funding_stages, countries, tiers, timezones) eram aplicados como
gate ELIMINATORIO (AND via Candidate.id.in_(subq)). Quando o LLM extraia algo
sem match (ex: industry='B2B'), o AND apagava TODOS os candidatos, inclusive os
que casavam pela query de texto -> "Sem resultados" mesmo havendo PMs reais.

Fix: tratar os filtros estruturados como degradacao graciosa — se o conjunto
estrito zerar, refazer a busca SEM os filtros estruturados (mantendo texto +
require_email/phone + exclude, que sao escolhas reais do usuario) + warning.

Skip se DATABASE_URL ausente. Semeia e limpa as proprias linhas.
"""
from __future__ import annotations

import os
import uuid

import pytest


def _get_async_database_url():
    from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "+asyncpg" not in url:
        return None
    parts = urlsplit(url)
    drop = {"sslmode", "sslrootcert", "sslcert", "sslkey", "channel_binding"}
    new_qs = [(k, v) for k, v in parse_qsl(parts.query) if k not in drop]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(new_qs), parts.fragment))


_COMPANY = "search-localfilter-rt-co"
_TOKEN = "zzuniquetoken42"


@pytest.fixture
async def pg_ctx():
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    url = _get_async_database_url()
    if not url:
        pytest.skip("DATABASE_URL not available")

    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)
    cand_id = str(uuid.uuid4())

    async def _cleanup(session):
        await session.execute(text("DELETE FROM candidates WHERE company_id = :c"), {"c": _COMPANY})

    async with sm() as session:
        await session.execute(text("SELECT set_config('app.company_id', :c, false)"), {"c": _COMPANY})
        await _cleanup(session)
        await session.execute(
            text(
                "INSERT INTO candidates (id, company_id, source, name, current_title, is_active) "
                "VALUES (CAST(:id AS uuid), :c, 'test', :n, :t, true)"
            ),
            {"id": cand_id, "c": _COMPANY, "n": "ZZ Tester", "t": "Engenheiro " + _TOKEN.upper()},
        )
        await session.commit()
        try:
            yield session, _COMPANY, cand_id
        finally:
            await session.rollback()
            await session.execute(text("SELECT set_config('app.company_id', :c, false)"), {"c": _COMPANY})
            await _cleanup(session)
            await session.commit()
    await engine.dispose()


@pytest.mark.asyncio
async def test_industry_filter_sem_match_nao_zera_busca(pg_ctx):
    """Industry inexistente NAO deve apagar o candidato que casa por texto."""
    session, company_id, cand_id = pg_ctx
    from app.domains.sourcing.services.pearch_service import PearchService

    svc = PearchService()
    profiles, total = await svc.search_local_candidates(
        session,
        query=_TOKEN,
        limit=10,
        industries=["NonexistentIndustryXYZ123"],
        include_discovered=False,
    )
    # Sem o fix: filtro de industry inexistente -> 0 resultados (FALHA aqui).
    # Com o fix (drop-filter-if-zero): cai para text-only -> candidato semeado aparece.
    assert len(profiles) >= 1, (
        "esperava o candidato via fallback drop-filter; industry inexistente zerou a busca "
        f"(veio {len(profiles)} perfis)"
    )


@pytest.mark.asyncio
async def test_busca_texto_sem_filtros_retorna(pg_ctx):
    """Controle: sem filtros estruturados, o text-match retorna normalmente."""
    session, company_id, cand_id = pg_ctx
    from app.domains.sourcing.services.pearch_service import PearchService

    svc = PearchService()
    profiles, total = await svc.search_local_candidates(
        session, query=_TOKEN, limit=10, include_discovered=False
    )
    assert len(profiles) >= 1
