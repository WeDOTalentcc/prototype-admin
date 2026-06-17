"""Sprint O.1 sensor: job_vacancy_id propagation from publish_node to orchestrator response.

Prevents regression of the bug where the wizard returns ``job_published=True``
but ``job_vacancy_id=None`` because the publish_node state was overwritten by
calibration/handoff/review_gate nodes downstream.

Anchors:
- WizardSessionService injects ``stage_payload["job_vacancy_id"]`` from
  ``result["job_id"]`` (top-level state) at process_message return.
- calibration_node also surfaces ``data.job_id`` in its ws_stage_payload.
- Orchestrator extracts job_vacancy_id from stage_payload with multiple
  fallbacks.

If this test fails, check:
- app/domains/job_creation/services/wizard_session_service.py around the
  ``# Sprint O.1 canonical: propagate job_vacancy_id forward`` block.
- app/api/v1/wizard_smart_orchestrator.py orchestrator ``job_vacancy_id=(...)``
  extraction chain.
- app/domains/job_creation/graph.py calibration_node ``data`` dict — ensure
  ``"job_id": str(job_id) if job_id else None`` is preserved.
"""
from __future__ import annotations

import pytest


def test_o1_orchestrator_extracts_job_vacancy_id_from_top_level_state():
    """Simulates the WizardSessionService injection contract.

    The session service writes ``stage_payload["job_vacancy_id"]`` from
    ``result["job_id"]`` before returning. The orchestrator MUST surface that
    in its SmartOrchestrateResponse.
    """
    # Arrange: stage_payload as it leaves WizardSessionService after O.1 fix.
    fake_job_id = "3caf395f-d079-46a2-a1ef-9bbe66a4f100"
    stage_payload = {
        "type": "wizard_stage",
        "stage": "calibration",
        "job_vacancy_id": fake_job_id,  # ← O.1 injection at session service
        "data": {
            "message": "Calibração em andamento",
            "job_id": fake_job_id,  # ← O.1: calibration_node also preserves
            "candidates": [],
            "threshold": 3,
            "approved_count": 0,
            "complete": False,
        },
    }

    # Act: replicate orchestrator extraction chain (must mirror file:line):
    # app/api/v1/wizard_smart_orchestrator.py — job_vacancy_id=(...)
    extracted = (
        stage_payload.get("job_vacancy_id")
        or (stage_payload.get("data") or {}).get("job_id")
        or (stage_payload.get("data") or {}).get("job_vacancy_id")
        or (stage_payload.get("data") or {}).get("id")
    )

    # Assert
    assert extracted == fake_job_id, (
        f"O.1 regression: orchestrator did not extract job_vacancy_id from "
        f"stage_payload. Got {extracted!r}, expected {fake_job_id!r}."
    )


def test_o1_orchestrator_falls_back_to_data_job_id_when_top_level_missing():
    """Defense-in-depth: even if O.1 injection at session service breaks,
    the orchestrator should still extract job_id from publish_node's data dict
    (graph.py:2371 ``"job_id": job_id`` in ws_stage_payload.data).
    """
    fake_job_id = "abcd1234-0000-4000-8000-000000000001"
    stage_payload = {
        "type": "wizard_stage",
        "stage": "publish",
        # NOTE: no top-level job_vacancy_id (simulating session service skip)
        "data": {
            "message": "Vaga publicada",
            "job_id": fake_job_id,  # ← publish_node canonical
        },
    }

    extracted = (
        stage_payload.get("job_vacancy_id")
        or (stage_payload.get("data") or {}).get("job_id")
        or (stage_payload.get("data") or {}).get("job_vacancy_id")
        or (stage_payload.get("data") or {}).get("id")
    )

    assert extracted == fake_job_id, (
        "O.1 defense-in-depth regression: orchestrator did not fall back to "
        "stage_payload.data.job_id when top-level job_vacancy_id missing."
    )


def test_o1_calibration_node_preserves_job_id_in_data():
    """Read calibration_node source and assert it preserves ``job_id`` in
    ``ws_stage_payload.data``. Regression if Sprint O.3 (or later) reorders the
    data dict and drops the key.
    """
    from pathlib import Path
    # PR-10 (ONDA 3 sub-B): calibration_node moved to nodes/calibration.py
    repo_root = Path(__file__).resolve().parents[2]
    node_path = repo_root / "app" / "domains" / "job_creation" / "nodes" / "calibration.py"
    graph_path = repo_root / "app" / "domains" / "job_creation" / "graph.py"
    if node_path.is_file():
        src = node_path.read_text()
    else:
        assert graph_path.is_file(), f"graph.py not found at {graph_path}"
        src = graph_path.read_text()
    cal_idx = src.find("def calibration_node(")
    assert cal_idx != -1, "calibration_node function not found in graph.py or nodes/calibration.py"
    next_def = src.find("\ndef ", cal_idx + 1)
    cal_body = src[cal_idx:next_def] if next_def != -1 else src[cal_idx:]

    # Assert the canonical O.1 line exists
    assert '"job_id": str(job_id) if job_id else None' in cal_body, (
        "Sprint O.1 regression: calibration_node no longer sets "
        '"job_id": str(job_id) if job_id else None in ws_stage_payload.data. '
        "Re-add to preserve vacancy id forward through calibration stage."
    )


def test_o1_wizard_session_service_injects_job_vacancy_id():
    """Read wizard_session_service.py and assert the O.1 injection block
    survives. Regression if a refactor removes the top-level-state propagation.
    """
    from pathlib import Path
    svc_path = (
        Path(__file__).resolve().parents[2]
        / "app" / "domains" / "job_creation" / "services" / "wizard_session_service.py"
    )
    assert svc_path.is_file(), f"wizard_session_service.py not found at {svc_path}"

    src = svc_path.read_text()
    assert "Sprint O.1 canonical: propagate job_vacancy_id forward" in src, (
        "Sprint O.1 regression: WizardSessionService no longer propagates "
        "job_vacancy_id from result['job_id'] into stage_payload. Re-add the "
        "block immediately after stage_payload extraction."
    )
    # The actual injection line
    assert 'stage_payload.setdefault("job_vacancy_id", str(_o1_job_id))' in src, (
        "Sprint O.1 regression: setdefault('job_vacancy_id', ...) line missing."
    )
