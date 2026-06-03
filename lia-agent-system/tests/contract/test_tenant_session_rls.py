"""Sensor canonical RLS (2026-06-03) — tenant_session seta o GUC app.company_id.

Root cause do "chat nao ve dados": tools do agentic loop abrem AsyncSessionLocal
sem o middleware RLS -> app.company_id NULL -> RLS (FORCED em ~241 tabelas)
bloqueia tudo. tenant_session(company_id) seta o GUC na transacao, igual ao
get_tenant_db dos endpoints HTTP. Este teste pina que o GUC fica setado.
"""
import pytest
from sqlalchemy import text

_CID = "00000000-0000-4000-a000-000000000001"


@pytest.mark.asyncio
async def test_tenant_session_sets_guc():
    from app.core.database import tenant_session
    async with tenant_session(_CID) as db:
        r = await db.execute(text("SELECT current_setting('app.company_id', true)"))
        assert r.scalar() == _CID


@pytest.mark.asyncio
async def test_tenant_session_empty_company_skips_set(monkeypatch):
    # company_id vazio -> NAO chama set_tenant_context (fail-closed; nunca vaza).
    # Teste de COMPORTAMENTO (nao de estado do DB, que sofre poluicao de pool).
    import app.core.database as dbmod
    calls = []
    async def _spy(db, cid):
        calls.append(cid)
    monkeypatch.setattr(dbmod, "set_tenant_context", _spy)
    async with dbmod.tenant_session("") as db:
        assert db is not None
    assert calls == []  # vazio -> nao setou contexto
