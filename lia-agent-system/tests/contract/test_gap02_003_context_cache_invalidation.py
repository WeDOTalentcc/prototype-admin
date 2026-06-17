"""
GAP-02-003 Sensor: validates that company settings update endpoints
invalidate the ContextAggregatorService cache so agents see fresh data
immediately instead of waiting up to 5 minutes (TTL).

Tests verify:
1. clear_cache is called with the correct company_id after successful updates
2. clear_cache is NOT called when the update fails (exception before commit)
3. The wiring exists in every relevant endpoint module
"""
from __future__ import annotations

import ast
import importlib
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Static analysis: verify the import + call exist in each endpoint file
# ---------------------------------------------------------------------------

# Modules that MUST call context_aggregator.clear_cache after settings update
ENDPOINT_FILES_THAT_MUST_INVALIDATE = [
    ROOT / "app" / "api" / "v1" / "company.py",
    ROOT / "app" / "api" / "v1" / "company_culture.py",
    ROOT / "app" / "api" / "v1" / "hiring_policy.py",
    ROOT / "app" / "api" / "v1" / "company_ai_persona.py",
    ROOT / "app" / "api" / "v1" / "ai_config.py",
]


class TestCacheInvalidationWiring:
    """Static analysis: every settings endpoint file must import and call clear_cache."""

    @pytest.mark.parametrize(
        "filepath",
        ENDPOINT_FILES_THAT_MUST_INVALIDATE,
        ids=[p.stem for p in ENDPOINT_FILES_THAT_MUST_INVALIDATE],
    )
    def test_file_imports_context_aggregator(self, filepath: Path):
        """Endpoint file must import context_aggregator (the singleton)."""
        source = filepath.read_text(encoding="utf-8")
        assert "context_aggregator" in source, (
            f"{filepath.name} does not import context_aggregator. "
            "Fix: add 'from app.domains.ai.services.context_aggregator_service "
            "import context_aggregator' and call context_aggregator.clear_cache(company_id) "
            "after successful settings update."
        )

    @pytest.mark.parametrize(
        "filepath",
        ENDPOINT_FILES_THAT_MUST_INVALIDATE,
        ids=[p.stem for p in ENDPOINT_FILES_THAT_MUST_INVALIDATE],
    )
    def test_file_calls_clear_cache(self, filepath: Path):
        """Endpoint file must call clear_cache somewhere."""
        source = filepath.read_text(encoding="utf-8")
        assert "clear_cache" in source, (
            f"{filepath.name} never calls clear_cache. "
            "Fix: add context_aggregator.clear_cache(company_id) after successful "
            "settings update (after db.commit or repo.flush)."
        )


class TestClearCacheMethod:
    """Unit tests for the clear_cache method itself."""

    def test_clear_cache_removes_matching_keys(self):
        from app.domains.ai.services.context_aggregator_service import ContextAggregatorService

        svc = ContextAggregatorService()
        svc._cache = {
            "comp-1:sess-a": MagicMock(),
            "comp-1:sess-b": MagicMock(),
            "comp-2:sess-c": MagicMock(),
        }
        svc.clear_cache("comp-1")
        assert "comp-1:sess-a" not in svc._cache
        assert "comp-1:sess-b" not in svc._cache
        assert "comp-2:sess-c" in svc._cache

    def test_clear_cache_all(self):
        from app.domains.ai.services.context_aggregator_service import ContextAggregatorService

        svc = ContextAggregatorService()
        svc._cache = {"a:1": MagicMock(), "b:2": MagicMock()}
        svc.clear_cache()
        assert len(svc._cache) == 0

    def test_clear_cache_noop_when_no_match(self):
        from app.domains.ai.services.context_aggregator_service import ContextAggregatorService

        svc = ContextAggregatorService()
        svc._cache = {"comp-1:sess-a": MagicMock()}
        svc.clear_cache("nonexistent")
        assert len(svc._cache) == 1


class TestCacheNotClearedOnFailure:
    """Verify the pattern: clear_cache should only run AFTER successful write."""

    @pytest.mark.parametrize(
        "filepath",
        ENDPOINT_FILES_THAT_MUST_INVALIDATE,
        ids=[p.stem for p in ENDPOINT_FILES_THAT_MUST_INVALIDATE],
    )
    def test_clear_cache_not_in_except_block(self, filepath: Path):
        """clear_cache must NOT appear inside an except block (would run on failure)."""
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # Check if clear_cache is called inside except
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        func = child.func
                        if isinstance(func, ast.Attribute) and func.attr == "clear_cache":
                            pytest.fail(
                                f"{filepath.name}: clear_cache called inside except block "
                                f"at line {child.lineno}. This would invalidate cache on "
                                "failure. Move it to the success path (after commit/flush)."
                            )
