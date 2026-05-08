"""Tests for check_no_pii_in_logs.py sensor — validates f-string PII detection.

R-010.1 — Validates that the PII-in-logs CI guard correctly detects f-string
interpolation of PII variables in logger calls.
"""
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SENSOR_PATH = (
    Path(__file__).parent.parent.parent / "scripts" / "check_no_pii_in_logs.py"
)


def run_sensor_on_content(content: str, tmp_path: Path) -> tuple[int, str]:
    """Write content to a temp file and run sensor against it."""
    test_file = tmp_path / "test_module.py"
    test_file.write_text(content, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SENSOR_PATH), str(test_file)],
        capture_output=True,
        text=True,
        # Run from the scripts' parent so Path("app").rglob still works
        cwd=str(SENSOR_PATH.parent.parent),
    )
    combined = result.stdout + result.stderr
    return result.returncode, combined


class TestFStringPiiDetection:
    """Sensor correctly flags f-string logger calls that embed PII variable names."""

    def test_detects_email_in_fstring(self, tmp_path):
        """Sensor catches logger.info with f-string containing {email}."""
        code = textwrap.dedent(
            """
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Sending to {email}")
            """
        )
        returncode, output = run_sensor_on_content(code, tmp_path)
        assert (
            "email" in output.lower()
            or "violation" in output.lower()
            or "pii" in output.lower()
            or "f-string" in output.lower()
        ), f"Expected PII violation in output, got: {output!r}"

    def test_detects_phone_in_fstring(self, tmp_path):
        """Sensor catches logger.warning with f-string containing {phone_number}."""
        code = textwrap.dedent(
            """
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Calling {phone_number}")
            """
        )
        returncode, output = run_sensor_on_content(code, tmp_path)
        assert (
            "phone" in output.lower()
            or "violation" in output.lower()
            or "f-string" in output.lower()
        ), f"Expected PII violation for phone, got: {output!r}"

    def test_detects_manager_email_fstring(self, tmp_path):
        """Sensor catches manager_email interpolated in f-string."""
        code = textwrap.dedent(
            """
            import logging
            logger = logging.getLogger(__name__)
            manager_email = "mgr@example.com"
            logger.info(f"Manager: {manager_email}")
            """
        )
        returncode, output = run_sensor_on_content(code, tmp_path)
        assert (
            "email" in output.lower()
            or "violation" in output.lower()
            or "f-string" in output.lower()
        ), f"Expected PII violation for manager_email, got: {output!r}"

    def test_detects_recruiter_name_fstring(self, tmp_path):
        """Sensor catches recruiter_name interpolated in f-string."""
        code = textwrap.dedent(
            """
            import logging
            logger = logging.getLogger(__name__)
            recruiter_name = "Ana Silva"
            logger.info(f"Recruiter: {recruiter_name}")
            """
        )
        returncode, output = run_sensor_on_content(code, tmp_path)
        assert (
            "name" in output.lower()
            or "violation" in output.lower()
            or "f-string" in output.lower()
        ), f"Expected PII violation for recruiter_name, got: {output!r}"

    def test_detects_cpf_fstring(self, tmp_path):
        """Sensor catches CPF interpolated in f-string."""
        code = textwrap.dedent(
            """
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Invalid CPF: {cpf}")
            """
        )
        returncode, output = run_sensor_on_content(code, tmp_path)
        assert (
            "cpf" in output.lower()
            or "violation" in output.lower()
            or "f-string" in output.lower()
        ), f"Expected PII violation for cpf, got: {output!r}"


class TestSafePatternsPass:
    """Sensor does not flag safe, non-PII structured logging patterns."""

    def test_allows_percent_style_with_job_id(self, tmp_path):
        """Safe: %s-style format with non-PII context variable."""
        code = textwrap.dedent(
            """
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Processing job %s", job_id)
            logger.info("Completed", extra={"job_id": job_id, "count": n})
            """
        )
        # The sensor should not flag these — they have no f-string PII
        # returncode may still be 0 (no violations in this file portion)
        # We just verify no crash
        returncode, output = run_sensor_on_content(code, tmp_path)
        # job_id is not a PII variable name the sensor targets
        assert "job_id" not in output.lower() or "violation" not in output.lower(), (
            f"False positive: safe log flagged. Output: {output!r}"
        )

    def test_allows_fstring_without_pii_vars(self, tmp_path):
        """Safe: f-string in logger with non-PII variable names."""
        code = textwrap.dedent(
            """
            import logging
            logger = logging.getLogger(__name__)
            count = 5
            logger.info(f"Processed {count} jobs successfully")
            """
        )
        returncode, output = run_sensor_on_content(code, tmp_path)
        # count is not a PII variable — should not be flagged
        assert "f-string" not in output.lower() or "violation" not in output.lower(), (
            f"False positive: count variable incorrectly flagged. Output: {output!r}"
        )


class TestSensorSelfConsistency:
    """Sensor produces consistent output for the fixed job_vacancy_service.py."""

    def test_fixed_service_file_passes(self):
        """After R-010.1 fixes, job_vacancy_service.py should have 0 f-string PII violations."""
        service_path = (
            SENSOR_PATH.parent.parent
            / "app/domains/job_management/services/job_vacancy_service.py"
        )
        assert service_path.exists(), f"Service file not found at {service_path}"

        # Import check_fstring_pii directly from the sensor module
        import importlib.util
        spec = importlib.util.spec_from_file_location("sensor", str(SENSOR_PATH))
        sensor_mod = importlib.util.load_from_spec(spec)  # type: ignore[attr-defined]
        spec.loader.exec_module(sensor_mod)  # type: ignore[union-attr]

        lines = service_path.read_text(encoding="utf-8").splitlines()
        violations = sensor_mod.check_fstring_pii(service_path, lines)
        assert violations == [], (
            f"job_vacancy_service.py still has f-string PII violations after fix:\n"
            + "\n".join(violations)
        )
