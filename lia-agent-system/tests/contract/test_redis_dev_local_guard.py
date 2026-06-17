"""Sensor (harness, computacional) — guard de quota de Redis remoto em dev.

Pina o comportamento do produtor canonical `settings.REDIS_URL`
(libs/config/lia_config/config.py): em desenvolvimento, REDIS_URL remoto
(ex.: Upstash) e redirecionado para o redis-server local para NAO consumir
a quota mensal do Redis gerenciado. Producao real (Cloud Run) nunca e afetada.

Contexto: o free tier do Upstash da 500k comandos/mes; dev compartilhando a
mesma instancia de producao estourava a quota (Usage 500000/500000 observado).
O workflow `lia-backend` ja sobe um redis-server local (porta 6379); este
guard garante que dev o use.

NOTA 1: APP_ENV nao e sinal confiavel de producao neste setup — o workspace
Replit de DEV tem APP_ENV=production setado como Secret global. O sinal robusto
e "workspace Replit de dev" = REPLIT_DEV_DOMAIN presente + REPLIT_DEPLOYMENT
ausente. Como estes testes rodam DENTRO do Replit, cada caso controla esses
env vars explicitamente via monkeypatch.

NOTA 2: ~18 consumidores leem os.getenv("REDIS_URL") direto (bypass de
settings.REDIS_URL). Por isso o guard tambem reescreve os.environ["REDIS_URL"]
no redirect — coberto por test_redirect_also_rewrites_os_environ.
"""
import os

import pytest

from libs.config.lia_config.config import Settings

_UPSTASH = "rediss://default:tok123@prepared-drake-39645.upstash.io:6379"
_LOCAL = "redis://localhost:6379/0"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Baseline limpo + restaura REDIS_URL (o validator pode muta-lo direto)."""
    monkeypatch.delenv("LIA_DEV_ALLOW_REMOTE_REDIS", raising=False)
    monkeypatch.delenv("REPLIT_DEV_DOMAIN", raising=False)
    monkeypatch.delenv("REPLIT_DEPLOYMENT", raising=False)
    _saved = os.environ.get("REDIS_URL")
    monkeypatch.delenv("REDIS_URL", raising=False)
    yield
    if _saved is None:
        os.environ.pop("REDIS_URL", None)
    else:
        os.environ["REDIS_URL"] = _saved


def test_replit_workspace_redirects_remote_even_with_appenv_production(monkeypatch):
    """Caso REAL do bug: workspace Replit dev com APP_ENV=production poluido."""
    monkeypatch.setenv("REPLIT_DEV_DOMAIN", "abc.replit.dev")
    s = Settings(APP_ENV="production", REDIS_URL=_UPSTASH, SECRET_KEY="x" * 24)
    assert s.REDIS_URL == _LOCAL


def test_dev_appenv_redirects_remote(monkeypatch):
    """Dev fora do Replit (APP_ENV=development) tambem redireciona."""
    s = Settings(APP_ENV="development", REDIS_URL=_UPSTASH)
    assert s.REDIS_URL == _LOCAL


def test_redirect_also_rewrites_os_environ(monkeypatch):
    """Bypass guard: os.environ["REDIS_URL"] deve virar local no redirect."""
    monkeypatch.setenv("REPLIT_DEV_DOMAIN", "abc.replit.dev")
    monkeypatch.setenv("REDIS_URL", _UPSTASH)
    Settings(APP_ENV="production", REDIS_URL=_UPSTASH, SECRET_KEY="x" * 24)
    assert os.environ["REDIS_URL"] == _LOCAL


def test_local_redis_untouched(monkeypatch):
    s = Settings(APP_ENV="development", REDIS_URL=_LOCAL)
    assert s.REDIS_URL == _LOCAL


def test_127_0_0_1_untouched(monkeypatch):
    s = Settings(APP_ENV="development", REDIS_URL="redis://127.0.0.1:6379/1")
    assert s.REDIS_URL == "redis://127.0.0.1:6379/1"


def test_real_production_keeps_remote(monkeypatch):
    """Producao real (Cloud Run): sem env REPLIT_*, APP_ENV=production."""
    monkeypatch.setenv("REDIS_URL", _UPSTASH)
    s = Settings(APP_ENV="production", REDIS_URL=_UPSTASH, SECRET_KEY="x" * 24)
    assert s.REDIS_URL == _UPSTASH
    assert os.environ["REDIS_URL"] == _UPSTASH  # env nao mutado em prod


def test_replit_deployment_keeps_remote(monkeypatch):
    """Replit Deployment (producao via Replit): REPLIT_DEPLOYMENT set -> remoto."""
    monkeypatch.setenv("REPLIT_DEV_DOMAIN", "abc.replit.dev")
    monkeypatch.setenv("REPLIT_DEPLOYMENT", "1")
    s = Settings(APP_ENV="production", REDIS_URL=_UPSTASH, SECRET_KEY="x" * 24)
    assert s.REDIS_URL == _UPSTASH


def test_escape_hatch_allows_remote_in_dev(monkeypatch):
    monkeypatch.setenv("REPLIT_DEV_DOMAIN", "abc.replit.dev")
    monkeypatch.setenv("LIA_DEV_ALLOW_REMOTE_REDIS", "true")
    s = Settings(APP_ENV="development", REDIS_URL=_UPSTASH)
    assert s.REDIS_URL == _UPSTASH
