"""R-006 — DEV_MODE gateado por ENVIRONMENT.

Sprint 1 Quick Wins — REMEDIATION_BRIEF Wave 0.
Cobre criterio de aceite F-309 / R-006.

LIA_DEV_MODE=true em production/staging foi a fonte de varios incidentes de
config drift. R-006 garante que mesmo se a env estiver setada, o codigo
ignora se ENVIRONMENT nao for "test"|"development"|"local"|"dev".
"""

from __future__ import annotations

import importlib
import sys


def _reload_module():
    """Reimporta auth_enforcement com novas env vars."""
    if "app.middleware.auth_enforcement" in sys.modules:
        del sys.modules["app.middleware.auth_enforcement"]
    return importlib.import_module("app.middleware.auth_enforcement")


def test_dev_mode_blocked_in_production(monkeypatch) -> None:
    """R-006: ENVIRONMENT=production + LIA_DEV_MODE=true → DEV_MODE INATIVO."""
    monkeypatch.setenv("LIA_DEV_MODE", "true")
    monkeypatch.setenv("ENVIRONMENT", "production")
    mod = _reload_module()
    assert mod._DEV_MODE is False, "R-006: LIA_DEV_MODE=true MAS ENVIRONMENT=production deveria desativar DEV_MODE."


def test_dev_mode_blocked_in_staging(monkeypatch) -> None:
    """R-006: ENVIRONMENT=staging + LIA_DEV_MODE=true → DEV_MODE INATIVO."""
    monkeypatch.setenv("LIA_DEV_MODE", "true")
    monkeypatch.setenv("ENVIRONMENT", "staging")
    mod = _reload_module()
    assert mod._DEV_MODE is False, "R-006: staging tambem precisa bloquear DEV_MODE — config drift comum."


def test_dev_mode_active_in_development(monkeypatch) -> None:
    """R-006: ENVIRONMENT=development + LIA_DEV_MODE=true → DEV_MODE ATIVO."""
    monkeypatch.setenv("LIA_DEV_MODE", "true")
    monkeypatch.setenv("ENVIRONMENT", "development")
    mod = _reload_module()
    assert mod._DEV_MODE is True


def test_dev_mode_active_in_test(monkeypatch) -> None:
    """R-006: ENVIRONMENT=test + LIA_DEV_MODE=true → DEV_MODE ATIVO."""
    monkeypatch.setenv("LIA_DEV_MODE", "true")
    monkeypatch.setenv("ENVIRONMENT", "test")
    mod = _reload_module()
    assert mod._DEV_MODE is True


def test_dev_mode_inactive_when_lia_dev_mode_unset(monkeypatch) -> None:
    """R-006: sem LIA_DEV_MODE explicito, DEV_MODE INATIVO em qualquer env."""
    monkeypatch.delenv("LIA_DEV_MODE", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    mod = _reload_module()
    assert mod._DEV_MODE is False


def test_dev_mode_inactive_with_unknown_environment(monkeypatch) -> None:
    """R-006: ENVIRONMENT=foo (desconhecido) bloqueia DEV_MODE — fail closed."""
    monkeypatch.setenv("LIA_DEV_MODE", "true")
    monkeypatch.setenv("ENVIRONMENT", "foo-unknown")
    mod = _reload_module()
    assert mod._DEV_MODE is False, "R-006: ENVIRONMENT desconhecido deve fail-closed (DEV_MODE INATIVO)."
