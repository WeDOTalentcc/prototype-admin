"""Integração (DB real) — C1: aprendizado por feedback escopado por EMPRESA + USUARIO.

Quem recruta p/ TI nao deve influenciar o ranking de quem recruta p/ Financas.
load_search_feedback filtra por company_id + user_id -> cada recrutador ve so o
efeito do proprio like/dislike. Skip se DATABASE_URL ausente.
"""
from __future__ import annotations

import os
import uuid

import pytest


def _async_url():
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
    p = urlsplit(url)
    drop = {"sslmode", "sslrootcert", "sslcert", "sslkey", "channel_binding"}
    qs = [(k, v) for k, v in parse_qsl(p.query) if k not in drop]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(qs), p.fragment))


_CO = "feedback-peruser-rt-co"
_CAND = "cand-peruser-x"


@pytest.fixture
async def seeded():
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    url = _async_url()
    if not url:
        pytest.skip("DATABASE_URL not available")
    engine = create_async_engine(url, future=True)
    sm = async_sessionmaker(engine, expire_on_commit=False)

    async def _clean(s):
        await s.execute(text("DELETE FROM search_feedbacks WHERE company_id = :c"), {"c": _CO})

    async with sm() as s:
        await s.execute(text("SELECT set_config('app.company_id', :c, false)"), {"c": _CO})
        await _clean(s)
        for uid, fb in [("user-A", "like"), ("user-B", "dislike")]:
            await s.execute(
                text(
                    "INSERT INTO search_feedbacks (id, company_id, candidate_id, user_id, feedback_type) "
                    "VALUES (:id, :c, :cand, :uid, :fb)"
                ),
                {"id": str(uuid.uuid4()), "c": _CO, "cand": _CAND, "uid": uid, "fb": fb},
            )
        await s.commit()
    try:
        yield
    finally:
        async with sm() as s:
            await s.execute(text("SELECT set_config('app.company_id', :c, false)"), {"c": _CO})
            await _clean(s)
            await s.commit()
        await engine.dispose()


@pytest.mark.asyncio
async def test_feedback_escopado_por_usuario(seeded):
    from app.domains.cv_screening.services.lia_score_service import lia_score_service

    a = await lia_score_service.load_search_feedback([_CAND], company_id=_CO, user_id="user-A")
    b = await lia_score_service.load_search_feedback([_CAND], company_id=_CO, user_id="user-B")
    assert a == {_CAND: "like"}, f"user-A deveria ver so o proprio like, veio {a}"
    assert b == {_CAND: "dislike"}, f"user-B deveria ver so o proprio dislike, veio {b}"


@pytest.mark.asyncio
async def test_feedback_isolado_entre_usuarios(seeded):
    from app.domains.cv_screening.services.lia_score_service import lia_score_service

    # usuario sem feedback nao herda o de ninguem
    c = await lia_score_service.load_search_feedback([_CAND], company_id=_CO, user_id="user-C")
    assert c == {}, f"user-C nao tem feedback proprio, deveria vir vazio, veio {c}"
