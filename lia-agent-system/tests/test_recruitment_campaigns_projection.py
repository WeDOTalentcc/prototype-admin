"""Task #609 — Workflow rail / JobCampaignBadge projection.

The endpoint at ``GET /api/v1/recruitment_campaigns`` powers two surfaces:

1. ``useWorkflowRail`` (``plataforma-lia/src/components/workflow-rail``) —
   reads ``data[*].attributes.{name,current_stage,stages,pending_action,
   job_id,talent_pool_id,created_at}``.
2. ``JobCampaignBadge`` (``plataforma-lia/src/components/jobs``) — reads
   ``data[*].attributes.status`` and decides between active/paused/none.

These tests pin the JSONAPI shape and the per-stage projection so we don't
silently regress those consumers.
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from app.api.v1.recruitment_campaigns import (
    _jsonapi_campaign,
    _project_stages,
)


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
        created_at=datetime(2026, 4, 19, 12, 0, 0),
        updated_at=datetime(2026, 4, 20, 9, 0, 0),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_jsonapi_envelope_matches_frontend_contract():
    payload = _jsonapi_campaign(_make_campaign())

    assert payload["id"] == "11111111-2222-3333-4444-555555555555"
    assert payload["type"] == "recruitment_campaign"
    attrs = payload["attributes"]
    assert attrs["name"] == "Backend Hiring Sprint"
    assert attrs["status"] == "active"
    assert attrs["current_stage"] == "outreach"
    assert attrs["job_id"] == "job-42"
    assert attrs["talent_pool_id"] is None
    assert attrs["created_at"].startswith("2026-04-19T12:00:00")
    # Pending action surfaces the in-progress stage's checkpoint so the rail
    # can render the action banner.
    assert attrs["pending_action"] == {
        "message": "Aprovar lista",
        "candidatesCount": 30,
    }


def test_stage_projection_marks_completed_in_progress_pending():
    stages = _project_stages(_make_campaign())

    statuses = [s["status"] for s in stages]
    assert statuses == ["completed", "completed", "in_progress", "pending"]

    # Labels are humanised for the canonical stage names so the rail does not
    # have to translate them on the client.
    labels = [s["label"] for s in stages]
    assert labels == ["Sourcing", "Triagem", "Contato", "Entrevista"]

    counts = [s["candidatesCount"] for s in stages]
    assert counts == [120, 60, 30, 10]


def test_completed_campaign_marks_every_stage_completed():
    stages = _project_stages(
        _make_campaign(status="completed", current_stage_index=3)
    )
    assert all(s["status"] == "completed" for s in stages)


def test_paused_campaign_keeps_current_stage_in_progress():
    """The badge distinguishes ``paused`` vs ``active`` purely from the
    top-level ``status`` field — make sure we don't accidentally collapse
    stage statuses when a campaign is paused."""
    payload = _jsonapi_campaign(_make_campaign(status="paused"))
    assert payload["attributes"]["status"] == "paused"
    statuses = [s["status"] for s in payload["attributes"]["stages"]]
    assert statuses == ["completed", "completed", "in_progress", "pending"]


def test_empty_stages_yields_empty_projection_and_no_pending_action():
    payload = _jsonapi_campaign(
        _make_campaign(stages=[], current_stage_index=0)
    )
    assert payload["attributes"]["stages"] == []
    assert payload["attributes"]["current_stage"] is None
    assert payload["attributes"]["pending_action"] is None


def test_custom_stage_name_falls_back_to_titlecase_label():
    stages = _project_stages(
        _make_campaign(
            stages=[{"name": "background_check", "order": 1}],
            current_stage_index=0,
        )
    )
    assert stages[0]["label"] == "Background Check"
    # Custom stages without a counter field surface a 0 instead of None so
    # the rail can always render the badge.
    assert stages[0]["candidatesCount"] == 0
