"""Producer fix (2026-06-04): engine auto-injeta app.company_id do contextvar.

Root cause: ~226 tools do agentic loop abrem AsyncSessionLocal cru (fora do
middleware HTTP get_db) -> app.company_id NULL -> RLS FORCED (~241 tabelas)
bloqueia tudo -> tool retorna 0. Fix no PRODUTOR (canonical-fix #3): um listener
no engine "begin" (lia_config.database) replica a logica ja provada do get_db
(le _current_company_id, seta o GUC), corrigindo TODAS as tools de uma vez +
futuras. No-op quando contextvar vazio (jobs cross-tenant legitimos = status
quo, fail-closed). set_config(is_local=true) e TX-scoped: reverte no fim da
transacao (sem vazamento entre tenants no pool -- comprovado por sonda manual).

Testes deterministicos (sem DB-state): assercoes de ESTADO do DB sofrem
poluicao de pool entre testes async (cada teste em event loop proprio ->
conexao asyncpg presa ao loop morto corrompe a proxima). Por isso a logica do
listener e validada por invocacao direta + introspeccao do registro no engine.
Prova end-to-end: sonda manual (no-leak + auto-inject) + preview live.
"""
from sqlalchemy import event

from lia_config.database import engine
import lia_config.database as dbmod

_CID = "00000000-0000-4000-a000-000000000001"


class _FakeConn:
    """Captura chamadas conn.execute do listener (unit, sem DB/pool/loop)."""

    def __init__(self):
        self.executed = []

    def execute(self, stmt, params=None):
        self.executed.append((str(stmt), params))


def test_listener_is_registered_on_engine_begin():
    """O listener DEVE estar wired no evento `begin` do engine (anti-remocao).

    Sem isso, sessoes cruas no agentic loop voltam a abrir sem o GUC -> RLS
    bloqueia tudo -> chat cego. Pina o produtor.
    """
    assert event.contains(engine.sync_engine, "begin", dbmod._inject_tenant_guc_on_begin)


def test_listener_skips_when_contextvar_empty(monkeypatch):
    """Contextvar vazio -> guard `if not cid: return` -> nenhum set_config."""
    monkeypatch.setattr(dbmod, "_get_current_company_id", lambda: "")
    conn = _FakeConn()
    dbmod._inject_tenant_guc_on_begin(conn)
    assert conn.executed == []


def test_listener_sets_guc_when_contextvar_present(monkeypatch):
    """Contextvar setado -> listener emite set_config(app.company_id, cid, true)."""
    monkeypatch.setattr(dbmod, "_get_current_company_id", lambda: _CID)
    conn = _FakeConn()
    dbmod._inject_tenant_guc_on_begin(conn)
    assert len(conn.executed) == 1
    sql, params = conn.executed[0]
    assert "set_config" in sql and "app.company_id" in sql
    assert params == {"cid": _CID}
