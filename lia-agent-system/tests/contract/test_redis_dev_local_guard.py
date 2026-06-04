"""Sensor (harness, computacional) — guard de quota de Redis remoto em dev.

Pina o comportamento do produtor canonical `settings.REDIS_URL`
(libs/config/lia_config/config.py): em desenvolvimento, REDIS_URL remoto
(ex.: Upstash) é redirecionado para o redis-server local para NAO consumir
a quota mensal do Redis gerenciado. Producao nunca e afetada.

Contexto: o free tier do Upstash da 500k comandos/mes; dev compartilhando a
mesma instancia de producao estourava a quota. O workflow `lia-backend` ja
sobe um redis-server local (porta 6379); este guard garante que dev o use.
"""
import pytest

from libs.config.lia_config.config import Settings

_UPSTASH = "rediss://default:tok123@prepared-drake-39645.upstash.io:6379"
_LOCAL = "redis://localhost:6379/0"


def test_dev_redirects_remote_redis_to_local(monkeypatch):
    monkeypatch.delenv("LIA_DEV_ALLOW_REMOTE_REDIS", raising=False)
    s = Settings(APP_ENV="development", REDIS_URL=_UPSTASH)
    assert s.REDIS_URL == _LOCAL


def test_dev_keeps_local_redis_untouched(monkeypatch):
    monkeypatch.delenv("LIA_DEV_ALLOW_REMOTE_REDIS", raising=False)
    s = Settings(APP_ENV="development", REDIS_URL=_LOCAL)
    assert s.REDIS_URL == _LOCAL


def test_dev_keeps_127_0_0_1_untouched(monkeypatch):
    monkeypatch.delenv("LIA_DEV_ALLOW_REMOTE_REDIS", raising=False)
    s = Settings(APP_ENV="development", REDIS_URL="redis://127.0.0.1:6379/1")
    assert s.REDIS_URL == "redis://127.0.0.1:6379/1"


def test_production_keeps_remote_redis(monkeypatch):
    monkeypatch.delenv("LIA_DEV_ALLOW_REMOTE_REDIS", raising=False)
    s = Settings(APP_ENV="production", REDIS_URL=_UPSTASH, SECRET_KEY="x" * 24)
    assert s.REDIS_URL == _UPSTASH


def test_escape_hatch_allows_remote_in_dev(monkeypatch):
    monkeypatch.setenv("LIA_DEV_ALLOW_REMOTE_REDIS", "true")
    s = Settings(APP_ENV="development", REDIS_URL=_UPSTASH)
    assert s.REDIS_URL == _UPSTASH
