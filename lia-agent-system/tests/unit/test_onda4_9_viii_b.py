"""Onda 4.9 VIII.B — persona validator CI integration tests."""
from __future__ import annotations

from pathlib import Path

import yaml


def _find_workflow() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        # Lookup at repo root level: .github/workflows/lia-eval.yml
        cand = parent.parent / ".github/workflows/lia-eval.yml"
        if cand.exists():
            return cand
        cand2 = parent / ".github/workflows/lia-eval.yml"
        if cand2.exists():
            return cand2
    raise RuntimeError("lia-eval.yml not found")


def test_viiib_marker_in_workflow() -> None:
    """VIII.B: workflow contains VIII.B step marker."""
    text = _find_workflow().read_text(encoding="utf-8")
    assert "VIII.B" in text
    assert "persona consistency check" in text.lower() or "persona_validator" in text


def test_workflow_references_validate_response_and_recordings() -> None:
    """VIII.B: step imports validate_response + reads persona_recordings.yaml."""
    text = _find_workflow().read_text(encoding="utf-8")
    assert "validate_response" in text
    assert "persona_recordings.yaml" in text


def test_workflow_fails_safe_without_recordings() -> None:
    """VIII.B: step exits 0 when recordings file missing (CI doesn't break)."""
    text = _find_workflow().read_text(encoding="utf-8")
    # Structural: the heredoc must include the early-return path
    assert "no recordings" in text.lower() or "SystemExit(0)" in text
    assert "skipping" in text.lower()


def test_workflow_fails_on_persona_regression() -> None:
    """VIII.B: step exits 1 when any scenario fails validation."""
    text = _find_workflow().read_text(encoding="utf-8")
    assert "SystemExit(1)" in text
    assert "failed" in text.lower()


def test_workflow_yaml_parses_after_patch() -> None:
    """VIII.B regression: workflow YAML still parses after edit."""
    data = yaml.safe_load(_find_workflow().read_text(encoding="utf-8"))
    # YAML 1.1 parses top-level 'on' as bool True in some versions
    on_key = data.get("on") or data.get(True)
    assert on_key is not None
    assert "jobs" in data and "eval" in data["jobs"]


def test_workflow_step_order_before_artifact_upload() -> None:
    """VIII.B: validator step runs BEFORE upload-artifact (so failures don't skip upload)."""
    text = _find_workflow().read_text(encoding="utf-8")
    viib_idx = text.find("VIII.B")
    upload_idx = text.find("Upload eval artifacts")
    assert viib_idx > 0 and upload_idx > 0
    assert viib_idx < upload_idx, "VIII.B step must come BEFORE upload-artifact"
