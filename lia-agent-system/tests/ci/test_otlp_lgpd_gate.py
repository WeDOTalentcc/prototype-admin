"""
Test wrapper que invoca o OTLP LGPD checker como gate de CI.

Este teste:
1. Roda no CI normal (pytest)
2. Falha se houver violations LGPD em span attributes
3. Pode ser usado como pre-commit hook

Sprint III follow-up: P0 LGPD enforcement automatizado.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path("/home/runner/workspace/lia-agent-system")
TOOL_PATH = REPO_ROOT / "tools/migration/otlp_lgpd_check.py"


class TestOtlpLgpdGate:
    """Gate de CI: zero violations LGPD em span attributes."""

    def test_otlp_lgpd_check_passes(self):
        """O checker deve passar (exit 0) — produção sem violations LGPD."""
        result = subprocess.run(
            [sys.executable, str(TOOL_PATH)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            # Mostrar violations para debug
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        assert result.returncode == 0, (
            "OTLP LGPD violations detected — check span attributes for "
            "race/religion/gender/etc. Use audit_service.log_decision() instead. "
            "See app/orchestrator/_observability.py for canonical list."
        )

    def test_tool_exists_and_executable(self):
        """Sanity check: tool existe e é Python script."""
        assert TOOL_PATH.exists()
        assert TOOL_PATH.read_text().startswith('"""')

    def test_tool_imports_canonical_constants(self):
        """Tool importa FORBIDDEN_SPAN_ATTR_PATTERNS de _observability.py."""
        source = TOOL_PATH.read_text()
        assert "FORBIDDEN_SPAN_ATTR_PATTERNS" in source
        assert "from app.orchestrator.observability._observability import" in source
