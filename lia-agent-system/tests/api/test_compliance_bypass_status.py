"""
R-007 — Testes do endpoint /api/v1/health/compliance/bypass-status.

Espelha o alerta CRITICAL emitido no startup (app/main.py lifespan) com
um endpoint de runtime que canary monitoring consulta pra detectar
flags de bypass de compliance deixadas ON em produção.

Cenários cobertos:
  T1. Nenhuma flag ativa → warning_count=0, active_bypasses=[].
  T2. LIA_DISABLE_C3B=1 sozinha → warning_count=1, flag listada.
  T3. Múltiplas flags (LIA_ALLOW_NON_COMPLIANT_AGENTS + LIA_DISABLE_C3B) →
      warning_count=2, ambas listadas.
  T4. Flag inválida (=0 explícito) é ignorada.
  T5. environment field reflete APP_ENV.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_app() -> FastAPI:
    """Build minimal FastAPI app with system_health router only."""
    from app.api.v1 import system_health

    app = FastAPI()
    app.include_router(system_health.router, prefix="/api/v1")
    return app


def _clear_bypass_envs(monkeypatch) -> None:
    """Remove all R-007 bypass flags do ambiente."""
    for flag in (
        "LIA_ALLOW_NON_COMPLIANT_DOMAINS",
        "LIA_ALLOW_NON_COMPLIANT_AGENTS",
        "LIA_DISABLE_C3B",
        "LIA_ALLOW_REGISTRY_DRIFT",
    ):
        monkeypatch.delenv(flag, raising=False)


def test_bypass_status_no_active_flags(monkeypatch):
    """T1 — sem flags ativas, payload vazio + warning_count=0."""
    _clear_bypass_envs(monkeypatch)
    monkeypatch.setenv("APP_ENV", "development")

    client = TestClient(_make_app())
    r = client.get("/api/v1/health/compliance/bypass-status")
    assert r.status_code == 200
    data = r.json()
    assert data["warning_count"] == 0
    assert data["active_bypasses"] == []
    assert data["environment"] == "development"
    assert "timestamp" in data


def test_bypass_status_one_active_flag(monkeypatch):
    """T2 — LIA_DISABLE_C3B=1 sozinha → 1 flag listada."""
    _clear_bypass_envs(monkeypatch)
    monkeypatch.setenv("LIA_DISABLE_C3B", "1")

    client = TestClient(_make_app())
    r = client.get("/api/v1/health/compliance/bypass-status")
    assert r.status_code == 200
    data = r.json()
    assert data["warning_count"] == 1
    flags = [b["flag"] for b in data["active_bypasses"]]
    assert "LIA_DISABLE_C3B" in flags
    # description não-vazia
    assert all(b["description"] for b in data["active_bypasses"])


def test_bypass_status_multiple_active_flags(monkeypatch):
    """T3 — 2 flags simultâneas → ambas listadas."""
    _clear_bypass_envs(monkeypatch)
    monkeypatch.setenv("LIA_ALLOW_NON_COMPLIANT_AGENTS", "1")
    monkeypatch.setenv("LIA_DISABLE_C3B", "1")

    client = TestClient(_make_app())
    r = client.get("/api/v1/health/compliance/bypass-status")
    assert r.status_code == 200
    data = r.json()
    assert data["warning_count"] == 2
    flags = {b["flag"] for b in data["active_bypasses"]}
    assert "LIA_ALLOW_NON_COMPLIANT_AGENTS" in flags
    assert "LIA_DISABLE_C3B" in flags


def test_bypass_status_explicit_zero_is_inactive(monkeypatch):
    """T4 — flag explicitamente "0" não conta como ativa."""
    _clear_bypass_envs(monkeypatch)
    monkeypatch.setenv("LIA_ALLOW_NON_COMPLIANT_DOMAINS", "0")
    monkeypatch.setenv("LIA_DISABLE_C3B", "0")

    client = TestClient(_make_app())
    r = client.get("/api/v1/health/compliance/bypass-status")
    assert r.status_code == 200
    data = r.json()
    assert data["warning_count"] == 0


def test_bypass_status_all_four_flags_active(monkeypatch):
    """T5 — todas as 4 flags ativas → warning_count=4."""
    _clear_bypass_envs(monkeypatch)
    monkeypatch.setenv("LIA_ALLOW_NON_COMPLIANT_DOMAINS", "1")
    monkeypatch.setenv("LIA_ALLOW_NON_COMPLIANT_AGENTS", "1")
    monkeypatch.setenv("LIA_DISABLE_C3B", "1")
    monkeypatch.setenv("LIA_ALLOW_REGISTRY_DRIFT", "1")

    client = TestClient(_make_app())
    r = client.get("/api/v1/health/compliance/bypass-status")
    assert r.status_code == 200
    data = r.json()
    assert data["warning_count"] == 4
    flags = {b["flag"] for b in data["active_bypasses"]}
    assert flags == {
        "LIA_ALLOW_NON_COMPLIANT_DOMAINS",
        "LIA_ALLOW_NON_COMPLIANT_AGENTS",
        "LIA_DISABLE_C3B",
        "LIA_ALLOW_REGISTRY_DRIFT",
    }


def test_bypass_status_environment_field_reflects_app_env(monkeypatch):
    """T6 — environment field espelha APP_ENV."""
    _clear_bypass_envs(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")

    client = TestClient(_make_app())
    r = client.get("/api/v1/health/compliance/bypass-status")
    assert r.status_code == 200
    assert r.json()["environment"] == "production"
