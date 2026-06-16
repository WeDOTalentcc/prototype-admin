"""F-26 P1 contract: AST sensor detects ghost __init__ attrs in orchestrators.

Audit ref: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-26

Sensor: scripts/check_orchestrator_init_completeness.py
Purpose: prevent regression of F-01/F-12 class of bugs (self._XYZ read
without self._XYZ assignment in __init__).
"""
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SENSOR = REPO_ROOT / "scripts" / "check_orchestrator_init_completeness.py"


def _run_sensor_on_string(tmp_path: Path, source: str, filename: str = "fake_orchestrator.py") -> subprocess.CompletedProcess:
    """Place source in tmp_path/app/domains/voice/services/<filename> and run sensor."""
    domain_dir = tmp_path / "app" / "domains" / "voice" / "services"
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / filename).write_text(source, encoding="utf-8")

    # Patch the scan root via subprocess env: easier approach is direct import + monkeypatch.
    # Direct import of sensor module to allow rewriting SCAN_ROOTS.
    import importlib.util
    spec = importlib.util.spec_from_file_location("orch_sensor", SENSOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SCAN_ROOTS = [tmp_path / "app" / "domains"]
    mod.REPO_ROOT = tmp_path

    # Capture stdout/stderr and exit code.
    import io
    import contextlib

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
        exit_code = mod.main()

    return subprocess.CompletedProcess(
        args=[],
        returncode=exit_code,
        stdout=stdout_buf.getvalue(),
        stderr=stderr_buf.getvalue(),
    )


def test_sensor_detects_ghost_attribute(tmp_path):
    """F-26: ghost self._XYZ read without __init__ assignment is detected."""
    source = textwrap.dedent('''
        class FakeOrchestrator:
            def __init__(self):
                self._a = 1
                # missing self._llm_service assignment

            def do_work(self):
                return self._llm_service.foo()
    ''').lstrip()
    result = _run_sensor_on_string(tmp_path, source)
    assert result.returncode == 1, (
        f"F-26: sensor must return 1 on ghost attr. Got {result.returncode}. "
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "_llm_service" in result.stdout, (
        f"F-26: sensor output must mention the ghost attribute. "
        f"stdout: {result.stdout}"
    )


def test_sensor_passes_clean_class(tmp_path):
    """F-26: class with all reads covered by __init__ assignments -> exit 0."""
    source = textwrap.dedent('''
        class CleanOrchestrator:
            def __init__(self):
                self._a = 1
                self._b = 2

            def do_work(self):
                return self._a + self._b
    ''').lstrip()
    result = _run_sensor_on_string(tmp_path, source)
    assert result.returncode == 0, (
        f"F-26: clean class must return 0. Got {result.returncode}. "
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_sensor_honors_exempt_marker(tmp_path):
    """F-26: lines with # ORCHESTRATOR-GHOST-EXEMPT marker are suppressed."""
    source = textwrap.dedent('''
        class FactoryInjectedOrchestrator:
            def __init__(self):
                self._a = 1

            def do_work(self):
                # ORCHESTRATOR-GHOST-EXEMPT: injected by factory via setattr in DI container
                return self._dependency.foo()
    ''').lstrip()
    result = _run_sensor_on_string(tmp_path, source)
    assert result.returncode == 0, (
        f"F-26: EXEMPT marker must suppress violation. Got {result.returncode}. "
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_sensor_passes_on_real_voice_orchestrator_post_f01():
    """F-26 baseline check: post-F-01/F-12 fixes, real codebase must be clean."""
    result = subprocess.run(
        [sys.executable, str(SENSOR)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"F-26: real codebase has ghost attrs after F-01/F-12 fixes -- regression!\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
