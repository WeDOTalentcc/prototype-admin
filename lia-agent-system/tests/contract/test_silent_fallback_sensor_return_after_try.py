"""Sensor tests for return-after-try silent-fallback detection (Pattern D).

Followup of P0.D (commit 7d9dd1372 — wsi report_generator). The P0.D
commit message documented a known limitation:

    Sensor anti-recidiva — known limitation:
      scripts/check_no_silent_llm_fallback.py detecta apenas pattern
      return {success: True} DENTRO do except handler. O pattern atual
      do report_generator era except → data = _fallback (assignment) +
      return Object(...) FORA do try/except — falso negativo do sensor.

This test module pins the EXTENDED detection: the sensor's Pattern D
heuristic catches `except: var = fallback` followed by `return Obj(var=var)`
sibling to the try/except, even when the return is OUTSIDE the handler.

Test strategy mirrors tests/unit/test_pii_in_logs_sensor.py: write a
synthetic Python module to tmp_path, run the sensor against it via
subprocess, and assert hit/no-hit on stdout. This isolates the sensor's
AST logic from the live codebase and lets us pin both detection and
exemption pathways deterministically.

REGRA 4 (CLAUDE.md): handlers tocando LLM MUST fail-loud. Patterns
that look like the report_generator pre-fix bug MUST surface.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

SENSOR_PATH = (
    Path(__file__).parent.parent.parent / "scripts" / "check_no_silent_llm_fallback.py"
)


@pytest.fixture
def llm_scope_dir():
    """Create a tmp dir outside pytest's `test_` namespace.

    The sensor's SKIP_PATH_HINTS contains `/test_` to ignore tests/ dirs in
    the real codebase. Pytest's default tmp_path lives under
    ``/tmp/pytest-of-<user>/test_<funcname><N>/`` which trips that skip hint
    and makes synthetic files invisible to the sensor.

    We bypass this by using ``tempfile.mkdtemp`` with a `llm-` prefix
    (matches LLM_PATH_HINTS, does not contain `/test_`). Cleaned up after
    the test.
    """
    base = Path(tempfile.mkdtemp(prefix="llm-sensor-"))
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _run_sensor(content: str, scope_dir: Path, filename: str = "llm_handler.py") -> tuple[int, str]:
    """Write `content` to scope_dir/<llm-scoped-name> and run sensor.

    Sensor is run with --root=<scope_dir> so only the synthetic file is
    scanned. `scope_dir` must come from the `llm_scope_dir` fixture so
    the path stays out of pytest's `test_` namespace.
    """
    test_file = scope_dir / filename
    test_file.write_text(content, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SENSOR_PATH), "--root", str(scope_dir)],
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr
    return result.returncode, combined


class TestPatternDDetection:
    """Pattern D: except-assigns-var → return-after-try-uses-var.

    The exact anti-pattern the P0.D wsi report_generator bug exhibited,
    invisible to Patterns A/B/C (return inside the except handler).
    """

    def test_detects_p0d_pattern_data_assigned_in_except_then_return_uses_data(self, llm_scope_dir):
        """Canonical P0.D shape: data = fallback in except, return Obj(data=data) after."""
        code = textwrap.dedent(
            """
            class Report:
                def __init__(self, *, data):
                    self.data = data

            async def generate_llm_report():
                fallback = {"summary": "placeholder"}
                try:
                    data = await call_llm()
                except Exception as e:
                    import logging
                    logging.error("llm failed: %s", e)
                    data = fallback
                return Report(data=data)
            """
        )
        rc, output = _run_sensor(code, llm_scope_dir)
        assert "return-after-try-uses-except-assigned-var" in output, (
            f"Expected Pattern D detection for P0.D shape, got:\n{output}"
        )
        assert "data" in output, f"Expected tainted name 'data' in output:\n{output}"

    def test_detects_when_return_is_nested_under_if(self, llm_scope_dir):
        """Pattern D walks into nested if/else for the return scan."""
        code = textwrap.dedent(
            """
            def build_llm_payload(want_full):
                try:
                    payload = invoke_claude()
                except Exception:
                    payload = {"stub": True}
                if want_full:
                    return {"data": payload, "meta": "full"}
                return {"data": payload}
            """
        )
        rc, output = _run_sensor(code, llm_scope_dir)
        assert "return-after-try-uses-except-assigned-var" in output, (
            f"Expected Pattern D under nested if, got:\n{output}"
        )

    def test_does_not_flag_when_fallback_used_kwarg_declared(self, llm_scope_dir):
        """Canonical opt-out: return Obj(..., fallback_used=True) is NOT flagged."""
        code = textwrap.dedent(
            """
            class Report:
                def __init__(self, *, data, fallback_used):
                    self.data = data
                    self.fallback_used = fallback_used

            async def generate_llm_report():
                fallback = {"summary": "placeholder"}
                try:
                    data = await call_llm()
                    used_fallback = False
                except Exception:
                    data = fallback
                    used_fallback = True
                return Report(data=data, fallback_used=used_fallback)
            """
        )
        rc, output = _run_sensor(code, llm_scope_dir)
        assert "✅" in output or "No silent LLM-fallback" in output, (
            f"Expected no detection when fallback_used kwarg present, got:\n{output}"
        )

    def test_does_not_flag_when_return_uses_different_variable(self, llm_scope_dir):
        """If the return doesn't read the except-assigned var, no Pattern D."""
        code = textwrap.dedent(
            """
            def fetch_llm_summary():
                try:
                    raw = invoke_gpt()
                except Exception:
                    raw = None
                # Return a constant, not `raw` — no taint flow.
                return {"status": "ok", "result": "static"}
            """
        )
        rc, output = _run_sensor(code, llm_scope_dir)
        assert "✅" in output or "No silent LLM-fallback" in output, (
            f"Expected no detection when return ignores tainted var, got:\n{output}"
        )

    def test_does_not_flag_when_handler_does_not_catch_exception(self, llm_scope_dir):
        """Narrow except (e.g. ValueError-only) is NOT considered bare-ish."""
        code = textwrap.dedent(
            """
            def parse_llm_json():
                try:
                    data = invoke_anthropic()
                except ValueError:
                    # Narrow exception — handler is intentional, not silent catch-all.
                    data = {"empty": True}
                return {"payload": data}
            """
        )
        rc, output = _run_sensor(code, llm_scope_dir)
        # Narrow except is NOT bare-ish, so no Pattern D fire.
        assert "✅" in output or "No silent LLM-fallback" in output, (
            f"Expected no detection for narrow except (ValueError), got:\n{output}"
        )

    def test_honors_regra4_exempt_marker_on_except_handler(self, llm_scope_dir):
        """A `# REGRA-4-EXEMPT: <reason>` near the except suppresses detection."""
        code = textwrap.dedent(
            """
            def load_llm_config():
                try:
                    config = read_yaml()
                except Exception:
                    # REGRA-4-EXEMPT: config bootstrap, not LLM I/O — caller
                    # handles None via downstream defaults.
                    config = {"inline": "default"}
                return {"cfg": config}
            """
        )
        rc, output = _run_sensor(code, llm_scope_dir)
        assert "✅" in output or "No silent LLM-fallback" in output, (
            f"Expected exemption marker to suppress Pattern D, got:\n{output}"
        )

    def test_honors_regra4_exempt_marker_above_try_multiline(self, llm_scope_dir):
        """Canonical placement: multi-line comment-block ABOVE the try.

        This is the placement the WT-2022 cleanup uses for the LangGraph
        wrappers (job_wizard_graph._invoke_langgraph, interview_graph._invoke_langgraph).
        The marker can be several lines above the try header — up to 5 by
        default to fit the canonical 3-line justification comment-block.
        """
        code = textwrap.dedent(
            """
            class Result:
                def __init__(self, data, error=None):
                    self.data = data
                    self.error = error

            async def invoke_with_canonical_envelope(state):
                # REGRA-4-EXEMPT: LangGraph wrapper — except handler sets
                # result["error"] = str(exc) as canonical inline error envelope.
                # Downstream code checks result.get("error") before treating as ok.
                try:
                    result = await ainvoke_llm(state)
                except Exception as exc:
                    result = {"data": None, "error": str(exc)}
                return Result(data=result.get("data"), error=result.get("error"))
            """
        )
        rc, output = _run_sensor(code, llm_scope_dir)
        assert "✅" in output or "No silent LLM-fallback" in output, (
            f"Expected exemption marker above try (5-line window) to suppress, got:\n{output}"
        )


class TestPatternABCStillFires:
    """Regression guard: extending the sensor must not break Patterns A/B/C.

    The pre-existing pattern (return success-envelope INSIDE the except
    handler) still has to be detected after the Pattern D additions.
    """

    def test_pattern_a_return_success_envelope_inside_except(self, llm_scope_dir):
        """Classic Pattern A: bare except returns dict with success=True."""
        code = textwrap.dedent(
            """
            def call_llm():
                try:
                    return invoke_claude()
                except Exception:
                    return {"success": True, "data": []}
            """
        )
        rc, output = _run_sensor(code, llm_scope_dir)
        assert "bare-except-returns-success-envelope" in output, (
            f"Expected Pattern A detection (legacy), got:\n{output}"
        )


class TestBlockingMode:
    """`--blocking` flag must exit 1 when Pattern D fires."""

    def test_blocking_mode_exit1_on_pattern_d(self, llm_scope_dir):
        code = textwrap.dedent(
            """
            class Wrap:
                def __init__(self, data):
                    self.data = data

            def llm_handler():
                try:
                    data = invoke_gemini()
                except Exception:
                    data = "fallback"
                return Wrap(data)
            """
        )
        test_file = llm_scope_dir / "llm_blocking.py"
        test_file.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SENSOR_PATH), "--root", str(llm_scope_dir), "--blocking"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"Expected blocking exit 1 on Pattern D, got rc={result.returncode}\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
