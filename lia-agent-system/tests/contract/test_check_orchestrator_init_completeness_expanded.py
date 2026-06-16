"""C.4 contract: F-26 sensor glob expansion to all service files.

Workstream C ticket 4 (2026-05-23).

Audit ref: AUDIT_VOICE_SCREENING_ORCHESTRATOR.md F-12 bug.

F-12 (gemini_voice_service.py) era a mesma classe de bug que F-01
(orchestrator: ghost self._XYZ reads sem __init__ assignment) mas o
arquivo NAO se chamava *orchestrator*.py — passou pelo sensor F-26.

C.4 expande o escopo do glob para cobrir *service*.py tambem. Sensor
continua respeitando o marker # ORCHESTRATOR-GHOST-EXEMPT.
"""
from __future__ import annotations

import importlib.util
import io
import contextlib
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SENSOR = REPO_ROOT / "scripts" / "check_orchestrator_init_completeness.py"


def _run_sensor_on_string(
    tmp_path: Path,
    source: str,
    filename: str = "fake_service.py",
    subdir: str = "voice/services",
) -> subprocess.CompletedProcess:
    """Place source under tmp_path/app/domains/<subdir>/<filename> and run sensor."""
    domain_dir = tmp_path / "app" / "domains" / subdir
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / filename).write_text(source, encoding="utf-8")

    spec = importlib.util.spec_from_file_location("orch_sensor_c4", SENSOR)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SCAN_ROOTS = [tmp_path / "app" / "domains"]
    mod.REPO_ROOT = tmp_path

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


class TestSensorGlobExpansion:
    """C.4: sensor must catch ghost attrs in `*_service.py` (not only orchestrator)."""

    def test_sensor_catches_ghost_in_service_file(self, tmp_path):
        """C.4: file named gemini_voice_service.py — class with ghost attr → exit 1."""
        source = textwrap.dedent('''
            class GeminiVoiceService:
                def __init__(self):
                    self._a = 1
                    # missing self._llm_service assignment

                def do_work(self):
                    return self._llm_service.foo()
        ''').lstrip()
        result = _run_sensor_on_string(
            tmp_path, source, filename="gemini_voice_service.py"
        )
        assert result.returncode == 1, (
            f"C.4: sensor must scan *service*.py and report ghost. "
            f"Got {result.returncode}.\nstdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
        assert "_llm_service" in result.stdout

    def test_sensor_clean_service_file(self, tmp_path):
        """C.4: service file with no ghost attrs → exit 0."""
        source = textwrap.dedent('''
            class CleanService:
                def __init__(self):
                    self._a = 1
                    self._b = 2

                def do_work(self):
                    return self._a + self._b
        ''').lstrip()
        result = _run_sensor_on_string(
            tmp_path, source, filename="clean_service.py"
        )
        assert result.returncode == 0, (
            f"C.4: clean service file must pass. Got {result.returncode}.\n"
            f"stdout: {result.stdout}"
        )

    def test_sensor_honors_exempt_marker_in_service_file(self, tmp_path):
        """C.4: # ORCHESTRATOR-GHOST-EXEMPT marker works in service files too."""
        source = textwrap.dedent('''
            class FactoryInjectedService:
                def __init__(self):
                    self._a = 1

                def do_work(self):
                    # ORCHESTRATOR-GHOST-EXEMPT: injected by factory
                    return self._dep.foo()
        ''').lstrip()
        result = _run_sensor_on_string(
            tmp_path, source, filename="factory_service.py"
        )
        assert result.returncode == 0, (
            f"C.4: EXEMPT marker must suppress in service file. "
            f"Got {result.returncode}.\nstdout: {result.stdout}"
        )

    def test_sensor_still_catches_orchestrator_files(self, tmp_path):
        """C.4: orchestrator files keep being scanned (no regression of F-26)."""
        source = textwrap.dedent('''
            class FakeOrchestrator:
                def __init__(self):
                    self._a = 1

                def do_work(self):
                    return self._missing.foo()
        ''').lstrip()
        result = _run_sensor_on_string(
            tmp_path, source, filename="fake_orchestrator.py"
        )
        assert result.returncode == 1, (
            f"C.4: orchestrator-file path must still detect ghost. "
            f"Got {result.returncode}.\nstdout: {result.stdout}"
        )
        assert "_missing" in result.stdout


class TestRealCodebaseClean:
    def test_real_codebase_passes_c4_expanded_scope(self):
        """C.4: after expansion, real codebase must remain clean — if a real
        ghost surfaces, fix it OR add # ORCHESTRATOR-GHOST-EXEMPT marker."""
        result = subprocess.run(
            [sys.executable, str(SENSOR)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"C.4: real codebase has ghost attrs after expanded scope!\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
