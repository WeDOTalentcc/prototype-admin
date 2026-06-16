"""TDD: FairnessGuard fail-fast on empty protected_attributes registry.

ADR-031 v2 Sprint 4B.1 — addresses the LGPD compliance gap that lived
in production from Mar 2026 (loader path bug → empty registry → fail-OPEN).

Tests:
  1. With registry loaded (default), FairnessGuard.__init__ succeeds
  2. With registry empty + strict=True, raises RuntimeError
  3. With registry empty + strict=False (default in tests),
     logs warning + degrades gracefully
  4. Default strict mode honors LIA_ENV (production → strict)

Skill: tdd-workflow + harness-engineering (sensor at startup).
"""
from __future__ import annotations

import logging
import os
from unittest.mock import patch

import pytest


def test_fairness_guard_succeeds_when_registry_loaded():
    """Default path: YAML loaded → FairnessGuard initializes normally."""
    from app.shared.compliance.fairness_guard import FairnessGuard

    # No exception, simple smoke
    guard = FairnessGuard()
    assert guard is not None


def test_fairness_guard_raises_when_registry_empty_and_strict():
    """ADR-031 v2 fail-fast: strict=True + empty registry → RuntimeError."""
    from app.shared.compliance.fairness_guard import FairnessGuard

    with patch(
        "app.shared.compliance.protected_attributes.is_registry_loaded",
        return_value=False,
    ):
        with pytest.raises(RuntimeError, match="protected_attributes registry"):
            FairnessGuard(strict=True)


def test_fairness_guard_warns_when_registry_empty_and_not_strict(caplog):
    """Test mode: strict=False + empty registry → logged warning, no raise."""
    from app.shared.compliance.fairness_guard import FairnessGuard

    with patch(
        "app.shared.compliance.protected_attributes.is_registry_loaded",
        return_value=False,
    ):
        with caplog.at_level(logging.WARNING):
            guard = FairnessGuard(strict=False)
        assert guard is not None
        assert any(
            "DEGRADED MODE" in rec.message or "fail-OPEN" in rec.message
            for rec in caplog.records
        ), "FairnessGuard should warn when degraded"


def test_fairness_guard_strict_default_honors_production_env(monkeypatch):
    """Default strict mode = True when LIA_ENV in (production, staging)."""
    from app.shared.compliance.fairness_guard import FairnessGuard

    monkeypatch.setenv("LIA_ENV", "production")
    with patch(
        "app.shared.compliance.protected_attributes.is_registry_loaded",
        return_value=False,
    ):
        with pytest.raises(RuntimeError):
            FairnessGuard()  # no explicit strict — env-driven


def test_fairness_guard_strict_default_lenient_in_dev(monkeypatch, caplog):
    """Default strict mode = False when LIA_ENV not in (production, staging)."""
    from app.shared.compliance.fairness_guard import FairnessGuard

    monkeypatch.setenv("LIA_ENV", "development")
    with patch(
        "app.shared.compliance.protected_attributes.is_registry_loaded",
        return_value=False,
    ):
        with caplog.at_level(logging.WARNING):
            guard = FairnessGuard()  # no explicit strict
        assert guard is not None


def test_fairness_guard_handles_is_registry_loaded_exception(caplog):
    """Defensive: if is_registry_loaded() itself raises, treat as not-loaded.

    Avoids ImportError / AttributeError crashing FairnessGuard creation.
    """
    from app.shared.compliance.fairness_guard import FairnessGuard

    with patch(
        "app.shared.compliance.protected_attributes.is_registry_loaded",
        side_effect=ImportError("simulated"),
    ):
        with caplog.at_level(logging.ERROR):
            guard = FairnessGuard(strict=False)
        assert guard is not None
        assert any("is_registry_loaded() raised" in rec.message for rec in caplog.records)


def test_fairness_guard_strict_default_honors_app_env_when_lia_env_unset(monkeypatch):
    """ADR-031 v2: APP_ENV=production + LIA_ENV unset -> strict=True (fail-fast).

    Fecha o env-var split-brain: todo o resto do stack (main.py lifespan,
    ADR-AUTH-001, REDIS_ENCRYPTION_KEY guard, LLM key guard) usa APP_ENV.
    O FairnessGuard lia SOMENTE LIA_ENV. Um deployment canonico seguindo
    .env.production.example seta APP_ENV=production SEM LIA_ENV -> strict
    caia para False silenciosamente e o matching de atributos protegidos
    LGPD (raca/etnia/religiao) passava em modo fail-OPEN. Este teste pina
    que APP_ENV agora e honrado como fallback.
    """
    from app.shared.compliance.fairness_guard import FairnessGuard

    monkeypatch.delenv("LIA_ENV", raising=False)
    monkeypatch.setenv("APP_ENV", "production")
    with patch(
        "app.shared.compliance.protected_attributes.is_registry_loaded",
        return_value=False,
    ):
        with pytest.raises(RuntimeError, match="protected_attributes registry"):
            FairnessGuard()  # env-driven; fallback APP_ENV deve ativar strict


def test_fairness_guard_lia_env_takes_precedence_over_app_env(monkeypatch):
    """LIA_ENV explicito vence APP_ENV (sem regressao para deployments que ja setam LIA_ENV)."""
    from app.shared.compliance.fairness_guard import FairnessGuard

    monkeypatch.setenv("LIA_ENV", "development")
    monkeypatch.setenv("APP_ENV", "production")
    with patch(
        "app.shared.compliance.protected_attributes.is_registry_loaded",
        return_value=False,
    ):
        # LIA_ENV=development => strict=False => warns, nao raise
        guard = FairnessGuard()
        assert guard is not None
