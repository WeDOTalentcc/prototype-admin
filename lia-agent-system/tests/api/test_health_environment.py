"""
Task #1250 — GET /api/v1/health/environment.

Endpoint de diagnóstico que confirma (sem expor credenciais) que cada
ambiente publicado usa banco e Redis próprios. Reporta APP_ENV e um
identificador NÃO-sensível (backend, host mascarado, porta, nome e um
fingerprint não-reversível) de Postgres e Redis.

Cobre:
  T1. Payload tem app_env + database + redis com campos esperados.
  T2. NUNCA vaza usuário/senha/connection string completa.
  T3. Mesmo banco entre dois ambientes → mesmo fingerprint (isolação quebrada);
      bancos diferentes → fingerprints diferentes.
  T4. URLs ausentes caem no default das settings (configured=True/False).
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_client() -> TestClient:
    from app.api.v1 import system_health

    app = FastAPI()
    app.include_router(system_health.router, prefix="/api/v1")
    return TestClient(app)


_SECRET_USER = "lia_secret_user"
_SECRET_PASS = "sup3r-s3cret-pw"


def test_environment_payload_shape(monkeypatch):
    """T1: estrutura básica do payload."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        f"postgresql+asyncpg://{_SECRET_USER}:{_SECRET_PASS}@ep-cool-frog-123.neon.tech:5432/neondb",
    )
    monkeypatch.setenv("REDIS_URL", f"redis://default:{_SECRET_PASS}@redis-host.internal:6379/2")

    resp = _make_client().get("/api/v1/health/environment")
    assert resp.status_code == 200
    body = resp.json()

    assert body["app_env"] == "production"
    db = body["database"]
    assert db["configured"] is True
    assert db["backend"] == "postgresql+asyncpg"
    assert db["port"] == 5432
    assert db["name"] == "neondb"
    assert db["fingerprint"]
    # host masked, not full host
    assert db["host_masked"] != "ep-cool-frog-123.neon.tech"
    assert "***" in db["host_masked"]

    redis = body["redis"]
    assert redis["configured"] is True
    assert redis["backend"] == "redis"
    assert redis["port"] == 6379
    assert redis["name"] == "2"


def test_environment_never_leaks_credentials(monkeypatch):
    """T2: nenhuma credencial vaza no payload (usuário/senha/string completa)."""
    monkeypatch.setenv(
        "DATABASE_URL",
        f"postgresql+asyncpg://{_SECRET_USER}:{_SECRET_PASS}@ep-cool-frog-123.neon.tech:5432/neondb",
    )
    monkeypatch.setenv("REDIS_URL", f"redis://default:{_SECRET_PASS}@redis-host.internal:6379/0")

    raw = _make_client().get("/api/v1/health/environment").text
    assert _SECRET_PASS not in raw
    assert _SECRET_USER not in raw
    assert "neon.tech:5432/neondb" not in raw  # full target not echoed verbatim


def test_environment_same_db_same_fingerprint(monkeypatch):
    """T3a: mesmo host:port/name → mesmo fingerprint mesmo com creds diferentes."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://dev_user:dev_pw@shared-db.internal:5432/appdb",
    )
    fp_dev = _make_client().get("/api/v1/health/environment").json()["database"]["fingerprint"]

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://prod_user:prod_pw@shared-db.internal:5432/appdb",
    )
    fp_main = _make_client().get("/api/v1/health/environment").json()["database"]["fingerprint"]

    assert fp_dev == fp_main  # same physical DB → isolation broken signal


def test_environment_different_db_different_fingerprint(monkeypatch):
    """T3b: bancos distintos → fingerprints distintos (isolação OK)."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://u:p@dev-db.internal:5432/devdb",
    )
    fp_dev = _make_client().get("/api/v1/health/environment").json()["database"]["fingerprint"]

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://u:p@prod-db.internal:5432/proddb",
    )
    fp_main = _make_client().get("/api/v1/health/environment").json()["database"]["fingerprint"]

    assert fp_dev != fp_main


def test_environment_unset_redis_uses_default(monkeypatch):
    """T4: sem REDIS_URL no env, cai no default das settings (configured=True)."""
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://u:p@dev-db.internal:5432/devdb",
    )
    body = _make_client().get("/api/v1/health/environment").json()
    # default settings provides a redis url, so it should be described
    assert body["redis"]["configured"] is True
    assert body["redis"]["backend"] == "redis"
