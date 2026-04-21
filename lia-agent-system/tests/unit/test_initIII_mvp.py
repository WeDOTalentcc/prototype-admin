"""Onda 3.5 Init III MVP — Episodic memory tests."""
from __future__ import annotations

import pytest


def test_list_allowed_keys() -> None:
    """III MVP: schema introspection returns allowed keys list."""
    from app.shared.memory.recruiter_preferences import list_allowed_keys

    keys = list_allowed_keys()
    assert "preferred_top_n" in keys
    assert "last_filters" in keys
    assert "communication_channel" in keys


def test_set_preference_valid_key() -> None:
    """III MVP: set_preference stores valid key."""
    from app.shared.memory.recruiter_preferences import set_preference

    updated = set_preference({}, "preferred_top_n", 5)
    assert updated["preferred_top_n"] == 5


def test_set_preference_preserves_existing() -> None:
    """III MVP: set_preference is immutable-style (new dict)."""
    from app.shared.memory.recruiter_preferences import set_preference

    original = {"preferred_top_n": 5, "communication_channel": "email"}
    updated = set_preference(original, "briefing_style", "short")
    assert "preferred_top_n" in updated
    assert "communication_channel" in updated
    assert updated["briefing_style"] == "short"
    # Original dict NOT mutated (immutable-style)
    assert "briefing_style" not in original


def test_set_preference_rejects_schema_violation() -> None:
    """III MVP: unknown key rejected (schema guard)."""
    from app.shared.memory.recruiter_preferences import set_preference

    with pytest.raises(ValueError, match="not in allowed schema"):
        set_preference({}, "candidate_cpf", "123.456.789-00")


def test_set_preference_rejects_pii_cpf() -> None:
    """III MVP LGPD: CPF in value rejected."""
    from app.shared.memory.recruiter_preferences import set_preference

    # Technically last_filters IS in schema, but CPF in value blocked
    with pytest.raises(ValueError, match="PII pattern"):
        set_preference({}, "last_filters", {"candidate_cpf": "123.456.789-00"})


def test_set_preference_rejects_pii_email() -> None:
    """III MVP LGPD: email in value rejected."""
    from app.shared.memory.recruiter_preferences import set_preference

    with pytest.raises(ValueError, match="PII pattern"):
        set_preference({}, "last_filters", "contato@empresa.com.br")


def test_get_preference_missing_returns_default() -> None:
    """III MVP: get_preference missing key returns default."""
    from app.shared.memory.recruiter_preferences import get_preference

    assert get_preference(None, "preferred_top_n", default=10) == 10
    assert get_preference({}, "missing", default="fallback") == "fallback"


def test_get_preference_hit() -> None:
    """III MVP: get_preference existing key returns value."""
    from app.shared.memory.recruiter_preferences import get_preference

    prefs = {"preferred_top_n": 3}
    assert get_preference(prefs, "preferred_top_n") == 3


def test_feature_flag_off_set_passthrough() -> None:
    """III MVP: LIA_EPISODIC_MEMORY_ENABLED=false → no-op set."""
    import app.shared.memory.recruiter_preferences as mod

    original = mod._EPISODIC_MEMORY_ENABLED
    try:
        mod._EPISODIC_MEMORY_ENABLED = False
        out = mod.set_preference({"existing": 1}, "preferred_top_n", 5)
        assert out == {"existing": 1}, "Flag off should return unchanged dict"
    finally:
        mod._EPISODIC_MEMORY_ENABLED = original


def test_feature_flag_off_get_returns_default() -> None:
    """III MVP: flag off → get returns default."""
    import app.shared.memory.recruiter_preferences as mod

    original = mod._EPISODIC_MEMORY_ENABLED
    try:
        mod._EPISODIC_MEMORY_ENABLED = False
        assert mod.get_preference({"preferred_top_n": 5}, "preferred_top_n", default="X") == "X"
    finally:
        mod._EPISODIC_MEMORY_ENABLED = original


def test_marker_catalog_has_lia_memset() -> None:
    """III MVP: LIA-MEMSET in G2 catalog."""
    from pathlib import Path
    import yaml

    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "app/shared/observability/marker_catalog.yaml"
        if cand.exists():
            break
    data = yaml.safe_load(cand.read_text(encoding="utf-8"))
    assert "LIA-MEMSET" in data["markers"]
    assert data["markers"]["LIA-MEMSET"]["category"] == "memory"


def test_initIII_marker_in_module() -> None:
    """III MVP module marker for traceability."""
    from pathlib import Path
    import app.shared.memory.recruiter_preferences as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "Init III MVP" in source
    assert "set_preference" in source and "get_preference" in source
