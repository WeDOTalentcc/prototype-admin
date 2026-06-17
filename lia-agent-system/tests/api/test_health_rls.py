"""
R-002 — Sensor de runtime para Postgres RLS em tabelas críticas.

Testes unitários para o endpoint GET /api/v1/health/rls.

Estes testes NÃO requerem Postgres — usam dependency_overrides para
fornecer um AsyncSession mock que retorna linhas controladas de
pg_class. Cobrem 3 cenários:

  T1. Todas as tabelas críticas com RLS forçado → 200 + payload OK.
  T2. audit_logs sem RLS (drift simulado: relrowsecurity=False) → 503
      + missing inclui audit_logs.
  T3. Tabela crítica não existe em pg_class (não criada ainda) → 503 +
      missing reporta 'table not found'.

Migration 068 + 118-126 cobrem ~119 tabelas. Este endpoint detecta drift
(ALTER TABLE DISABLE ROW LEVEL SECURITY manual ou tabela nova sem RLS).
"""
from __future__ import annotations

from typing import Iterable
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


_CRITICAL = (
    "audit_logs",
    "users",
    "lgpd_consents",
    "tenant_llm_configs",
    "vacancy_candidates",
    "triagem_sessions",
    "bias_audits",
    "compliance_reports",
    "fairness_reports",
)


def _make_app(rows: Iterable[tuple[str, bool, bool]]):
    """Build FastAPI app with system_health router + mocked DB returning rows."""
    from app.api.v1 import system_health
    from app.core.database import get_db

    app = FastAPI()
    app.include_router(system_health.router, prefix="/api/v1")

    fake_result = MagicMock()
    fake_result.fetchall.return_value = list(rows)

    fake_db = MagicMock()

    async def _execute(*args, **kwargs):
        return fake_result

    fake_db.execute = _execute

    async def mock_db():
        yield fake_db

    app.dependency_overrides[get_db] = mock_db
    return app


def test_health_rls_all_protected_returns_200():
    """T1: todas as tabelas críticas RLS-forçado → 200."""
    rows = [(t, True, True) for t in _CRITICAL]
    app = _make_app(rows)
    client = TestClient(app)
    resp = client.get("/api/v1/health/rls")
    assert resp.status_code == 200
    body = resp.json()
    assert body["missing"] == []
    assert set(body["rls_protected"]) == set(_CRITICAL)
    assert body["checked_count"] == len(_CRITICAL)


def test_health_rls_drift_audit_logs_returns_503():
    """T2: audit_logs com relrowsecurity=False → 503 + missing reporta drift."""
    rows = []
    for t in _CRITICAL:
        if t == "audit_logs":
            rows.append((t, False, False))  # drift simulado
        else:
            rows.append((t, True, True))
    app = _make_app(rows)
    client = TestClient(app)
    resp = client.get("/api/v1/health/rls")
    assert resp.status_code == 503
    body = resp.json()
    missing_tables = [m["table"] for m in body["missing"]]
    assert "audit_logs" in missing_tables
    assert "audit_logs" not in body["rls_protected"]
    # Other tables remain protected
    assert "users" in body["rls_protected"]
    assert body["checked_count"] == len(_CRITICAL)


def test_health_rls_missing_table_returns_503():
    """T3: tabela crítica não encontrada em pg_class → 503 + missing reporta."""
    # Omit lgpd_consents — simula tabela ainda não criada
    rows = [(t, True, True) for t in _CRITICAL if t != "lgpd_consents"]
    app = _make_app(rows)
    client = TestClient(app)
    resp = client.get("/api/v1/health/rls")
    assert resp.status_code == 503
    body = resp.json()
    missing_tables = [m["table"] for m in body["missing"]]
    assert "lgpd_consents" in missing_tables
    # Reason should clearly indicate "not found"
    missing_entry = next(m for m in body["missing"] if m["table"] == "lgpd_consents")
    assert "not found" in missing_entry["reason"].lower()
