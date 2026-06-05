"""Integração (DB real) — roundtrip do parecer via OpinionsRepository.create_parecer_opinion.

Complementa os sensores mock-based (test_parecer_persistence.py) exercitando o
caminho real contra Postgres:
  * persiste 2 versões de parecer (opinion_type='general', vaga NULL)
  * versionamento atômico: version 1 → 2, is_current flip
  * score_breakdown.qualification_matrix faz roundtrip JSON intacto
  * multi-tenancy: leituras escopadas por company_id (RLS app.company_id)

Skip se DATABASE_URL ausente. Limpa as próprias linhas (prefixo de company_id).
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
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(new_qs), parts.fragment)
    )


_COMPANY = "parecer-rt-test-co"


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
        await session.execute(
            text("DELETE FROM lia_opinions WHERE company_id = :c"), {"c": _COMPANY}
        )
        await session.execute(
            text("DELETE FROM candidates WHERE company_id = :c"), {"c": _COMPANY}
        )

    async with sm() as session:
        # RLS: setar o tenant da sessão (no-op se a role bypassa RLS)
        await session.execute(
            text("SELECT set_config('app.company_id', :c, false)"), {"c": _COMPANY}
        )
        await _cleanup(session)
        await session.execute(
            text(
                "INSERT INTO candidates (id, company_id, source) "
                "VALUES (CAST(:id AS uuid), :c, 'test')"
            ),
            {"id": cand_id, "c": _COMPANY},
        )
        await session.commit()
        try:
            yield session, _COMPANY, cand_id
        finally:
            await session.rollback()  # se o teste abortou a tx, limpa antes do cleanup
            await session.execute(
                text("SELECT set_config('app.company_id', :c, false)"), {"c": _COMPANY}
            )
            await _cleanup(session)
            await session.commit()
    await engine.dispose()


_MATRIX = {
    "mode": "grouped",
    "criteria": [
        {"id": "tech:python", "label": "Python", "group": "must_have", "status": "met",
         "provenance": "resume", "is_inference": False, "confidence": 1.0},
    ],
    "met_count": 1,
    "total_count": 1,
    "must_have_met": 1,
    "must_have_total": 1,
    "overall_label": "Atende 1/1 qualificações",
}


async def _make(repo, company_id, cand_id, summary):
    return await repo.create_parecer_opinion(
        candidate_id=cand_id,
        job_vacancy_id=None,
        company_id=company_id,
        score=8.5,
        recommendation="RECOMMENDED",
        summary=summary,
        score_breakdown={"qualification_matrix": _MATRIX},
        strengths=["forte"],
        concerns=[],
        gaps=[],
        matched_skills=["Python"],
        missing_skills=["Go"],
        next_steps=["entrevista"],
    )


@pytest.mark.asyncio
async def test_parecer_roundtrip_versioning_and_matrix(pg_ctx):
    from uuid import UUID

    from app.domains.opinions.repositories.opinions_repository import OpinionsRepository

    session, company_id, cand_id = pg_ctx
    repo = OpinionsRepository(session)

    id1 = await _make(repo, company_id, cand_id, "parecer v1")
    await session.commit()
    id2 = await _make(repo, company_id, cand_id, "parecer v2")
    await session.commit()
    session.expire_all()

    op1 = await repo.get_by_id(UUID(id1), company_id)
    op2 = await repo.get_by_id(UUID(id2), company_id)

    # versionamento atômico + is_current flip
    assert op1 is not None and op2 is not None
    assert op1.version == 1 and op2.version == 2
    assert op1.is_current is False
    assert op2.is_current is True
    assert op2.opinion_type == "general"

    # score_breakdown.qualification_matrix roundtrip intacto
    sb = op2.score_breakdown or {}
    qm = sb.get("qualification_matrix") or {}
    assert qm.get("met_count") == 1
    assert qm.get("criteria")[0]["id"] == "tech:python"
    assert op2.summary == "parecer v2"
    assert op2.matched_skills == ["Python"]

    # apenas 1 corrente
    current = await repo.get_current_by_candidate(UUID(cand_id), company_id)
    current_general = [o for o in current if o.opinion_type == "general"]
    assert len(current_general) == 1
    assert str(current_general[0].id) == id2


@pytest.mark.asyncio
async def test_parecer_tenant_read_isolation(pg_ctx):
    from uuid import UUID

    from app.domains.opinions.repositories.opinions_repository import OpinionsRepository

    session, company_id, cand_id = pg_ctx
    repo = OpinionsRepository(session)

    oid = await _make(repo, company_id, cand_id, "parecer tenant")
    await session.commit()
    session.expire_all()

    # company correta encontra
    assert await repo.get_by_id(UUID(oid), company_id) is not None
    # company diferente NÃO encontra (escopo por company_id no WHERE)
    assert await repo.get_by_id(UUID(oid), "outra-company-xyz") is None
