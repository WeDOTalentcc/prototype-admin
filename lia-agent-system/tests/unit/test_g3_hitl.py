"""Onda 3.2 G3 — HITL checkpoint tests."""
from __future__ import annotations


def test_build_checkpoint_canonical_shape() -> None:
    """G3: build_hitl_checkpoint returns canonical dict with all required fields."""
    from app.orchestrator.hitl import build_hitl_checkpoint

    cp = build_hitl_checkpoint(
        tool_name="close_job",
        tool_params={"job_id": "v0040", "reason": "budget"},
        governance_tags=["destructive", "external_comms"],
    )
    assert cp is not None
    assert cp["tool_name"] == "close_job"
    assert "job_id" in cp["tool_params_summary"]
    assert cp["governance_tags"] == ["destructive", "external_comms"]
    assert "checkpoint_id" in cp
    assert "requested_at" in cp
    assert cp["approval_endpoint"] == "/api/v1/approvals"


def test_build_checkpoint_default_reason_destructive() -> None:
    """G3: destructive tag triggers destructive-warning reason."""
    from app.orchestrator.hitl import build_hitl_checkpoint

    cp = build_hitl_checkpoint(
        tool_name="close_job",
        governance_tags=["destructive"],
    )
    assert cp is not None
    assert "destrutiva" in cp["reason"].lower() or "reversível" in cp["reason"].lower()


def test_build_checkpoint_default_reason_pii() -> None:
    """G3: pii tag triggers LGPD-oriented reason."""
    from app.orchestrator.hitl import build_hitl_checkpoint

    cp = build_hitl_checkpoint(
        tool_name="export_candidates",
        governance_tags=["pii"],
    )
    assert cp is not None
    assert "lgpd" in cp["reason"].lower() or "pessoal" in cp["reason"].lower()


def test_build_checkpoint_summarizes_long_params() -> None:
    """G3: string params truncated to 100 chars; collections summarized."""
    from app.orchestrator.hitl import build_hitl_checkpoint

    cp = build_hitl_checkpoint(
        tool_name="send_bulk_email",
        tool_params={
            "body": "x" * 500,
            "recipients": list(range(50)),
            "template": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7},
        },
    )
    assert cp is not None
    assert len(cp["tool_params_summary"]["body"]) <= 100
    assert "list(50" in cp["tool_params_summary"]["recipients"]
    assert "dict" in cp["tool_params_summary"]["template"]


def test_build_checkpoint_none_tool_returns_none() -> None:
    """G3: empty/None tool_name → None (no checkpoint)."""
    from app.orchestrator.hitl import build_hitl_checkpoint

    assert build_hitl_checkpoint(tool_name="") is None


def test_feature_flag_off_returns_none() -> None:
    """G3: LIA_HITL_CHECKPOINT_ENABLED=false disables builder."""
    import app.orchestrator.hitl as mod

    original = mod._HITL_CHECKPOINT_ENABLED
    try:
        mod._HITL_CHECKPOINT_ENABLED = False
        assert mod.build_hitl_checkpoint(tool_name="close_job", governance_tags=["destructive"]) is None
    finally:
        mod._HITL_CHECKPOINT_ENABLED = original


def test_chat_response_has_hitl_checkpoint_field() -> None:
    """G3: ChatResponse exposes hitl_checkpoint: dict | None field."""
    from app.orchestrator.main_orchestrator import ChatResponse

    resp = ChatResponse(success=True, content="test")
    assert resp.hitl_checkpoint is None  # default

    cp = {"checkpoint_id": "abc", "tool_name": "close_job"}
    resp2 = ChatResponse(success=True, content="test", hitl_checkpoint=cp)
    assert resp2.hitl_checkpoint == cp


def test_marker_catalog_has_lia_hitl() -> None:
    """G3: LIA-HITL in catalog + G2 drift guard passes."""
    from pathlib import Path

    import yaml

    here = Path(__file__).resolve()
    for parent in here.parents:
        cand = parent / "app/shared/observability/marker_catalog.yaml"
        if cand.exists():
            break
    data = yaml.safe_load(cand.read_text(encoding="utf-8"))
    assert "LIA-HITL" in data["markers"]
    assert data["markers"]["LIA-HITL"]["category"] == "governance"


def test_g3_marker_in_hitl_module() -> None:
    """G3 audit marker."""
    from pathlib import Path

    import app.orchestrator.hitl as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "G3" in source
    assert "build_hitl_checkpoint" in source
