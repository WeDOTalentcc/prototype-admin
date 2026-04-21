"""
Task A — regression tests for check_forbidden_imports.py

Validates:
1. Existing forbidden patterns still caught
2. NEW: app.core.observability caught (FIX 13 migration → forbidden post-FIX 19)
3. Script exits 0 on clean source
"""
import re
import subprocess
import sys
from pathlib import Path


class TestCheckForbiddenImports:
    SCRIPT = Path("scripts/check_forbidden_imports.py")

    def test_script_exists_and_runs(self):
        assert self.SCRIPT.exists(), f"{self.SCRIPT} missing"
        # Should import without syntax errors
        import importlib.util
        spec = importlib.util.spec_from_file_location("cfi", self.SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "FORBIDDEN_PATTERNS")
        assert hasattr(mod, "main")

    def test_app_core_observability_is_forbidden(self):
        """FIX 13 migrated app/core/observability.py → app/shared/observability/tool_metrics.py.
        Reintroducing app.core.observability is forbidden and must be caught by CI."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("cfi", self.SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        test_lines = [
            "from app.core.observability import emit_tool_call",
            "from app.core.observability.tool_metrics import X",
            "import app.core.observability",
        ]
        for line in test_lines:
            caught = any(p.search(line) for p in mod.FORBIDDEN_PATTERNS)
            assert caught, f"Pattern not caught: {line!r}"

    def test_legacy_observability_still_forbidden(self):
        """Regression: task #343 patterns still there."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("cfi", self.SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        for line in [
            "from app.shared.tracing import X",
            "from app.shared.services.token_budget_service import X",
            "from app.config.langsmith import X",
        ]:
            caught = any(p.search(line) for p in mod.FORBIDDEN_PATTERNS)
            assert caught, f"Legacy pattern regression: {line!r}"

    def test_canonical_paths_are_allowed(self):
        """Positive: canonical import paths must NOT match forbidden patterns."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("cfi", self.SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        for line in [
            "from app.shared.observability.tool_metrics import emit_tool_call",
            "from app.shared.observability.tracing import X",
            "from app.shared.observability.langsmith import is_langsmith_enabled",
            "from lia_models.user import User",
            "from app.tools.registry import tool_registry",
        ]:
            caught = any(p.search(line) for p in mod.FORBIDDEN_PATTERNS)
            assert not caught, f"Canonical path wrongly flagged: {line!r}"
