"""Onda 3.3 Init VII — Error recovery policies tests."""
from __future__ import annotations


def test_yaml_parses_with_5_v1_policies() -> None:
    """VII: error_policies.yaml must have at least 5 v1 policies."""
    from pathlib import Path
    import yaml

    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "app/orchestrator/error_policies.yaml"
        if cand.exists():
            break
    data = yaml.safe_load(cand.read_text(encoding="utf-8"))
    assert "policies" in data and isinstance(data["policies"], list)
    assert len(data["policies"]) >= 5

    expected_ids = {"tool_timeout", "empty_result", "enum_error", "permission_denied", "tenant_mismatch"}
    present_ids = {p["id"] for p in data["policies"]}
    missing = expected_ids - present_ids
    assert not missing, f"VII: missing v1 policies: {missing}"


def test_list_policy_ids() -> None:
    """VII: list_policy_ids returns catalog entries."""
    from app.orchestrator.error_policies import list_policy_ids

    ids = list_policy_ids()
    assert "tool_timeout" in ids
    assert "empty_result" in ids


def test_resolve_policy_by_string_signal() -> None:
    """VII: resolve_policy matches trigger substrings."""
    from app.orchestrator.error_policies import resolve_policy

    policy = resolve_policy("timeout")
    assert policy is not None
    assert policy.id == "tool_timeout"


def test_resolve_policy_by_exception_class() -> None:
    """VII: resolve_policy inspects exception class name."""
    from app.orchestrator.error_policies import resolve_policy

    class TimeoutError(Exception):
        pass

    policy = resolve_policy(TimeoutError("conn dropped"))
    assert policy is not None
    assert policy.id == "tool_timeout"


def test_resolve_policy_unknown_returns_none() -> None:
    """VII: unknown signal → None (caller uses fallback)."""
    from app.orchestrator.error_policies import resolve_policy

    assert resolve_policy("totally_unexpected_error_xyz") is None


def test_apply_policy_renders_template() -> None:
    """VII: apply_policy returns shaped dict + renders template."""
    from app.orchestrator.error_policies import apply_policy

    out = apply_policy("enum_mismatch", context={"valid_values": "a, b, c"})
    assert out["policy_id"] == "enum_error"
    assert "a, b, c" in out["response"]
    assert out["severity"] == "warning"


def test_apply_policy_fallback_on_unknown() -> None:
    """VII: apply_policy never raises — always returns dict."""
    from app.orchestrator.error_policies import apply_policy

    out = apply_policy("xyz_unknown")
    assert out["policy_id"] is None
    assert "erro" in out["response"].lower()
    assert out["severity"] == "error"


def test_policy_anti_patterns_documented() -> None:
    """VII: each policy must document anti-patterns (what NOT to do)."""
    from pathlib import Path
    import yaml

    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "app/orchestrator/error_policies.yaml"
        if cand.exists():
            break
    data = yaml.safe_load(cand.read_text(encoding="utf-8"))
    offenders = [p["id"] for p in data["policies"] if not p.get("anti_patterns")]
    assert not offenders, f"VII: policies missing anti_patterns: {offenders}"


def test_feature_flag_off_disables_resolution() -> None:
    """VII: LIA_ERROR_POLICIES_ENABLED=false → resolve returns None."""
    import app.orchestrator.error_policies as mod

    original = mod._ERROR_POLICIES_ENABLED
    try:
        mod._ERROR_POLICIES_ENABLED = False
        assert mod.resolve_policy("timeout") is None
    finally:
        mod._ERROR_POLICIES_ENABLED = original


def test_marker_catalog_has_lia_errpol() -> None:
    """VII: LIA-ERRPOL in G2 catalog."""
    from pathlib import Path
    import yaml

    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "app/shared/observability/marker_catalog.yaml"
        if cand.exists():
            break
    data = yaml.safe_load(cand.read_text(encoding="utf-8"))
    assert "LIA-ERRPOL" in data["markers"]


def test_initVII_marker_in_module() -> None:
    """VII: error_policies.py module has Init VII marker."""
    from pathlib import Path
    import app.orchestrator.error_policies as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "Init VII" in source
    assert "resolve_policy" in source and "apply_policy" in source
