"""Tests for GAP-11-003: 5xx HTTPException must not expose detail=str(e).

OWASP A09 — Security Misconfiguration: raw exception strings in 5xx responses
leak internal details (config keys, class names, paths).

4xx errors are intentional user-facing messages and are NOT tested here.
"""
import re
from pathlib import Path

# From tests/contract/, go up to lia-agent-system/
_REPO_ROOT = Path(__file__).parent.parent.parent
APP_DIR = _REPO_ROOT / "app"
SCRIPTS_DIR = _REPO_ROOT / "scripts"


def _find_5xx_str_e_lines():
    violations = []
    for py_file in APP_DIR.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(content.splitlines(), 1):
            if "HTTPException" in line and ("str(e)" in line or "str(exc)" in line):
                if re.search(r"status_code\s*=\s*5\d\d", line):
                    violations.append((str(py_file.relative_to(_REPO_ROOT)), i, line.strip()))
    return violations


class TestOWASPA09No5xxDetailStrE:
    def test_no_5xx_detail_str_e(self):
        """No HTTPException with 5xx status_code should expose raw detail=str(e)."""
        violations = _find_5xx_str_e_lines()
        msg = "\n".join(
            f"  {path}:{line}: {text}\n  → Fix: replace detail=str(e) with opaque message + logger.error(exc_info=True)"
            for path, line, text in violations
        )
        assert not violations, f"OWASP A09 — {len(violations)} violation(s):\n{msg}"

    def test_opinions_py_502_no_str_e(self):
        """opinions.py 502 should not expose raw exception string."""
        target = APP_DIR / "api" / "v1" / "opinions.py"
        assert target.exists(), f"opinions.py not found at {target}"
        violations = [
            line for line in target.read_text().splitlines()
            if "502" in line and "str(e)" in line
        ]
        assert not violations, f"opinions.py still has 502 detail=str(e): {violations}"

    def test_analysis_py_503_no_str_e(self):
        """analysis.py 503 should not expose raw exception string."""
        target = APP_DIR / "api" / "v1" / "analysis.py"
        assert target.exists(), f"analysis.py not found at {target}"
        violations = [
            line for line in target.read_text().splitlines()
            if "503" in line and "str(e)" in line
        ]
        assert not violations, f"analysis.py still has 503 detail=str(e): {violations}"

    def test_kanban_assistant_py_503_no_str_e(self):
        """kanban_assistant.py 503 should not expose raw exception string."""
        target = APP_DIR / "api" / "v1" / "kanban_assistant.py"
        assert target.exists(), f"kanban_assistant.py not found at {target}"
        violations = [
            line for line in target.read_text().splitlines()
            if "503" in line and "str(e)" in line
        ]
        assert not violations, f"kanban_assistant.py still has 503 detail=str(e): {violations}"

    def test_sensor_script_exists(self):
        """Regression sensor script must exist."""
        sensor = SCRIPTS_DIR / "check_no_5xx_detail_str_e.py"
        assert sensor.exists(), f"OWASP A09 sensor missing: {sensor}"
