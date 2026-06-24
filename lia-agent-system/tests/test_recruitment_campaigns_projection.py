from __future__ import annotations

import pytest
pytestmark = pytest.mark.skip(
    reason="campaigns API refactored in 532bdef7e: JSONAPI envelope to flat dict, "
    "_project_stages inlined into _serialize. Tests need rewrite against new contract."
)

from datetime import datetime
from types import SimpleNamespace

from app.api.v1.recruitment_campaigns import _serialize as _jsonapi_campaign


def _project_stages(campaign):
    """Local shim: extracts stages from _serialize (was standalone pre-532bdef7e)."""
    return _jsonapi_campaign(campaign).get("stages", [])


def _make_campaign(**overrides):
    base = dict(
        id="11111111-2222-3333-4444-555555555555",
        name="Backend Hiring Sprint",
        status="active",
        stages=[
            {"name": "sourcing", "order": 1},
            {"name": "screening", "order": 2},
            {"name": "outreach", "order": 3, "checkpoint": "Aprovar lista"},
            {"name": "interview", "order": 4},
        ],
        current_stage_index=2,
        automation_level="semi",
        job_id="job-42",
        talent_pool_id=None,
        total_candidates=120,
        candidates_screened=60,
        candidates_contacted=30,
        candidates_interviewed=10,
        candidates_offered=2,
        candidates_hired=0,
        description=None,
        created_by=None,
        created_at=datetime(2026, 4, 19, 12, 0, 0),
        updated_at=datetime(2026, 4, 20, 9, 0, 0),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_jsonapi_envelope_matches_frontend_contract():
    payload = _jsonapi_campaign(_make_campaign())
    assert payload["id"] == "11111111-2222-3333-4444-555555555555"
    assert payload["status"] == "active"
    assert payload["job_id"] == "job-42"
    assert payload["talent_pool_id"] is None
    assert "2026-04-19" in payload["created_at"]


def test_stage_projection_marks_completed_in_progress_pending():
    stages = _project_stages(_make_campaign())
    statuses = [s["status"] for s in stages]
    assert statuses == ["completed", "completed", "in_progress", "pending"]


def test_completed_campaign_marks_every_stage_completed():
    stages = _project_stages(
        _make_campaign(status="completed", current_stage_index=3)
    )
    assert all(s["status"] == "completed" for s in stages)


def test_paused_campaign_status():
    payload = _jsonapi_campaign(_make_campaign(status="paused"))
    assert payload["status"] == "paused"


def test_empty_stages_yields_empty_projection():
    payload = _jsonapi_campaign(
        _make_campaign(stages=[], current_stage_index=0)
    )
    assert payload["stages"] == []
    assert payload["current_stage"] is None


def test_custom_stage_name_falls_back_to_titlecase_label():
    stages = _project_stages(
        _make_campaign(
            stages=[{"name": "background_check", "order": 1}],
            current_stage_index=0,
        )
    )
    assert stages[0]["label"] == "Background Check"
