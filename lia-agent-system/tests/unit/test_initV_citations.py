"""Onda 2.4 Init V — Citations backend tests."""
from __future__ import annotations


def test_citation_processor_empty_returns_empty() -> None:
    """Init V: None/empty tool_calls → empty citations."""
    from app.orchestrator.citation_processor import build_citations_from_tool_calls

    assert build_citations_from_tool_calls(None) == []
    assert build_citations_from_tool_calls([]) == []


def test_citation_processor_single_tool_call() -> None:
    """Init V: single tool_call → 1 citation entry with canonical fields."""
    from app.orchestrator.citation_processor import build_citations_from_tool_calls

    tool_calls = [{
        "tool_name": "search_jobs",
        "tool_params": {"status": "Ativa"},
        "result": {"success": True, "message": "Encontradas 30 vagas"},
    }]
    citations = build_citations_from_tool_calls(tool_calls)
    assert len(citations) == 1
    c = citations[0]
    assert c["tool_name"] == "search_jobs"
    assert c["tool_params"] == {"status": "Ativa"}
    assert "30 vagas" in c["result_summary"]
    assert 0 <= c["confidence"] <= 1


def test_citation_processor_varied_shapes() -> None:
    """Init V: handles 'name'/'parameters'/'arguments' aliases."""
    from app.orchestrator.citation_processor import build_citations_from_tool_calls

    tool_calls = [
        {"name": "search_candidates", "arguments": {"skill": "python"}, "output": "ok"},
        {"tool": "close_job", "parameters": {"job_id": "v1"}},
    ]
    citations = build_citations_from_tool_calls(tool_calls)
    assert len(citations) == 2
    assert citations[0]["tool_name"] == "search_candidates"
    assert citations[0]["tool_params"] == {"skill": "python"}
    assert citations[1]["tool_name"] == "close_job"


def test_citation_processor_feature_flag_off() -> None:
    """Init V: env LIA_CITATIONS_ENABLED=false → empty."""
    import app.orchestrator.citation_processor as mod

    original = mod._CITATIONS_ENABLED
    try:
        mod._CITATIONS_ENABLED = False
        tool_calls = [{"tool_name": "search_jobs", "tool_params": {}}]
        assert mod.build_citations_from_tool_calls(tool_calls) == []
    finally:
        mod._CITATIONS_ENABLED = original


def test_citation_processor_robust_to_malformed() -> None:
    """Init V: malformed entries don't crash — skipped gracefully."""
    from app.orchestrator.citation_processor import build_citations_from_tool_calls

    tool_calls = [
        "not a dict",
        None,
        {"tool_name": "valid_tool"},
        42,
    ]
    citations = build_citations_from_tool_calls(tool_calls)
    # Only the dict entry counts
    assert len(citations) == 1
    assert citations[0]["tool_name"] == "valid_tool"


def test_citation_summary_truncates_long_result() -> None:
    """Init V: result_summary bounded to prevent citation bloat."""
    from app.orchestrator.citation_processor import build_citations_from_tool_calls

    long_text = "x" * 1000
    tool_calls = [{"tool_name": "t", "result": long_text}]
    citations = build_citations_from_tool_calls(tool_calls)
    assert len(citations[0]["result_summary"]) <= 200


def test_chat_response_schema_has_citations_fields() -> None:
    """Init V: ChatResponse Pydantic model must expose citations + has_citations."""
    from app.orchestrator.main_orchestrator import ChatResponse

    resp = ChatResponse(success=True, content="test")
    # Default values
    assert resp.citations == []
    assert resp.has_citations is False

    # Populated
    resp2 = ChatResponse(
        success=True,
        content="test",
        citations=[{"tool_name": "search_jobs"}],
        has_citations=True,
    )
    assert len(resp2.citations) == 1
    assert resp2.has_citations is True


def test_initV_marker_present() -> None:
    """Init V audit marker for traceability."""
    from pathlib import Path

    import app.orchestrator.citation_processor as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "Init V" in source, "Init V: citation_processor must contain marker"
    assert "build_citations_from_tool_calls" in source
