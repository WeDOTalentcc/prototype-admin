"""W4-041 · TDD tests · Tier 6 canary feature flag gate.

Verifica:
1. Flag `tier6_canary_enabled` existe em DEFAULT_FLAGS (default False).
2. Canary metric `tier6_invocations_total` existe + labels canonical.
3. Cascaded router gate code: env var + flag AMBOS necessários.
4. Off-by-default fail-safe (default=False).
5. Per-tenant via env override pattern existente.

Sensor anti-regressão: scripts/check_tier6_canary_wired.py
"""
from __future__ import annotations

from pathlib import Path
import pytest


def test_flag_in_default_flags():
    """W4-041 · tier6_canary_enabled deve estar em DEFAULT_FLAGS."""
    from app.shared.governance.feature_flag_service import FeatureFlagService

    assert "tier6_canary_enabled" in FeatureFlagService.DEFAULT_FLAGS
    flag = FeatureFlagService.DEFAULT_FLAGS["tier6_canary_enabled"]
    assert flag["default"] is False, "Tier 6 canary MUST be off by default (fail-safe)"
    assert flag["category"] == "routing"
    # Description deve mencionar W4-041 e canary
    assert "W4-041" in flag["description"]


def test_flag_is_enabled_default_off(monkeypatch):
    """W4-041 · is_enabled('tier6_canary_enabled') default = False sem env."""
    from app.core.feature_flags import is_enabled

    # Limpa env overrides
    monkeypatch.delenv("FEATURE_FLAG_TIER6_CANARY_ENABLED", raising=False)
    assert is_enabled("tier6_canary_enabled") is False


def test_flag_global_env_override(monkeypatch):
    """W4-041 · FEATURE_FLAG_TIER6_CANARY_ENABLED=true ativa global."""
    from app.core.feature_flags import is_enabled

    monkeypatch.setenv("FEATURE_FLAG_TIER6_CANARY_ENABLED", "true")
    assert is_enabled("tier6_canary_enabled") is True


def test_flag_per_tenant_env_override(monkeypatch):
    """W4-041 · per-tenant env override pattern (FEATURE_FLAG_<KEY>__<company_id>)."""
    from app.core.feature_flags import is_enabled

    monkeypatch.delenv("FEATURE_FLAG_TIER6_CANARY_ENABLED", raising=False)
    monkeypatch.setenv("FEATURE_FLAG_TIER6_CANARY_ENABLED__test-company-abc", "true")
    assert is_enabled("tier6_canary_enabled", company_id="test-company-abc") is True
    assert is_enabled("tier6_canary_enabled", company_id="other-company") is False


def test_canary_metric_exists():
    """W4-041 · tier6_invocations_total counter deve existir."""
    from app.shared.observability.canary_metrics import tier6_invocations_total

    # None se prometheus_client indisponível (fail-open) — aceitável
    if tier6_invocations_total is None:
        pytest.skip("prometheus_client unavailable in this env")
    # Labels canonical: company_id_hash + flag_state
    assert hasattr(tier6_invocations_total, "labels")


def test_router_gate_code_canonical():
    """W4-041 · cascaded_router.py deve ter gate: env AND flag."""
    src = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "orchestrator"
        / "cascaded_router.py"
    ).read_text()
    assert "tier6_canary_enabled" in src, "Router must reference flag name"
    assert "_tier6_env_enabled" in src, "Router must split env check var"
    assert "_tier6_flag_enabled" in src, "Router must check feature flag"
    assert "AUTONOMOUS_REACT_ENABLED" in src, "Legacy env var still present"
    # Gate combina ambos
    assert "if _tier6_env_enabled and _tier6_flag_enabled:" in src


def test_router_emits_canary_metric():
    """W4-041 · cascaded_router.py deve emitir tier6_invocations_total."""
    src = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "orchestrator"
        / "cascaded_router.py"
    ).read_text()
    assert "tier6_invocations_total" in src
    assert 'flag_state="on" if _tier6_flag_enabled else "off"' in src


def test_canary_metric_has_w4041_doc():
    """W4-041 · counter doc string menciona ticket pra ratchet."""
    src = (
        Path(__file__).resolve().parents[2]
        / "app"
        / "shared"
        / "observability"
        / "canary_metrics.py"
    ).read_text()
    assert "W4-041" in src
    assert "tier6_invocations_total" in src
    assert "company_id_hash" in src and "flag_state" in src
