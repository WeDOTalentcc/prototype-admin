"""
Sensor: LiaFieldConfigService cache eliminates repeated DB hits for same tenant.
P1-1 regression prevention.
"""
import pytest
import time


def test_lia_field_config_cache_exists():
    """Cache dict must exist at module level."""
    import importlib
    try:
        m = importlib.import_module(
            "app.domains.cv_screening.services.lia_field_config_service"
        )
        assert hasattr(m, "_lia_field_config_cache"), (
            "_lia_field_config_cache NOT found in lia_field_config_service module. "
            "Fix: add _lia_field_config_cache: dict = {} at module level for TTL caching."
        )
        assert hasattr(m, "_LIA_FIELD_CONFIG_TTL"), (
            "_LIA_FIELD_CONFIG_TTL NOT found. Add TTL constant (e.g. 60.0 seconds)."
        )
        assert isinstance(m._LIA_FIELD_CONFIG_TTL, float), (
            "_LIA_FIELD_CONFIG_TTL must be a float (seconds)."
        )
        assert m._LIA_FIELD_CONFIG_TTL > 0, (
            "_LIA_FIELD_CONFIG_TTL must be positive."
        )
    except ImportError as e:
        pytest.skip(f"Module not importable in test env: {e}")


def test_invalidate_function_exists():
    """Invalidation helper must exist for post-write cache busting."""
    try:
        from app.domains.cv_screening.services.lia_field_config_service import (
            invalidate_lia_field_config_cache,
        )
        assert callable(invalidate_lia_field_config_cache), "Must be callable"
    except ImportError as e:
        pytest.skip(f"Module not importable: {e}")


def test_invalidate_removes_only_matching_tenant():
    """Invalidation must only remove entries for the given company_id."""
    try:
        import importlib
        m = importlib.import_module(
            "app.domains.cv_screening.services.lia_field_config_service"
        )
        from app.domains.cv_screening.services.lia_field_config_service import (
            invalidate_lia_field_config_cache,
        )
    except ImportError as e:
        pytest.skip(f"Module not importable: {e}")

    cache = m._lia_field_config_cache
    cache.clear()

    sentinel_a = object()
    sentinel_b = object()
    cache[("company-aaa", None)] = (sentinel_a, time.time())
    cache[("company-bbb", None)] = (sentinel_b, time.time())

    invalidate_lia_field_config_cache("company-aaa")

    assert ("company-aaa", None) not in cache, (
        "company-aaa entry should have been removed by invalidation"
    )
    assert ("company-bbb", None) in cache, (
        "company-bbb entry must NOT be removed when invalidating company-aaa"
    )

    cache.clear()


def test_cache_ttl_constant_is_at_least_30s():
    """TTL must be meaningful — at least 30 seconds to reduce DB load."""
    try:
        import importlib
        m = importlib.import_module(
            "app.domains.cv_screening.services.lia_field_config_service"
        )
    except ImportError as e:
        pytest.skip(f"Module not importable: {e}")
    assert m._LIA_FIELD_CONFIG_TTL >= 30.0, (
        f"_LIA_FIELD_CONFIG_TTL={m._LIA_FIELD_CONFIG_TTL} is too low. "
        "Minimum 30 seconds for meaningful DB load reduction."
    )
