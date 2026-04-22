"""Onda 4.5 V.B — Citations populate em ChatResponse (agentic) tests."""
from __future__ import annotations

from pathlib import Path


def test_vb_marker_in_main_orchestrator() -> None:
    """V.B: main_orchestrator contains V.B marker + citation_processor import."""
    import app.orchestrator.main_orchestrator as mo

    source = Path(mo.__file__).read_text(encoding="utf-8")
    assert "V.B" in source
    assert "build_citations_from_tool_calls" in source
    assert "citations=_citations" in source or "citations=_citations," in source


def test_citation_processor_reachable_from_orchestrator() -> None:
    """V.B: integration path — processor importable."""
    from app.orchestrator.citation_processor import build_citations_from_tool_calls

    # Should work with orchestrator's tool_calls_made shape
    tool_calls = [
        {"name": "search_jobs", "parameters": {"status": "Ativa"}, "result": {"message": "30 vagas"}},
    ]
    citations = build_citations_from_tool_calls(tool_calls, response_text="Encontrei 30 vagas")
    assert len(citations) == 1
    assert citations[0]["tool_name"] == "search_jobs"


def test_chat_response_citations_default_empty() -> None:
    """V.B regression: ChatResponse default citations=[] preserves backward compat."""
    from app.orchestrator.main_orchestrator import ChatResponse

    resp = ChatResponse(success=True, content="test")
    assert resp.citations == []
    assert resp.has_citations is False


def test_chat_response_citations_populated() -> None:
    """V.B: ChatResponse accepts citations list + has_citations flag."""
    from app.orchestrator.main_orchestrator import ChatResponse

    cites = [{"tool_name": "search_jobs", "result_summary": "30 vagas"}]
    resp = ChatResponse(
        success=True,
        content="Encontrei 30 vagas",
        citations=cites,
        has_citations=True,
    )
    assert len(resp.citations) == 1
    assert resp.has_citations is True


def test_vb_agentic_path_wires_citations_end_to_end() -> None:
    """V.B end-to-end: agentic path builds citations from _tool_calls.

    We can't easily run main_orchestrator.process() in isolation, so this
    test confirms the source path contains the wiring (structural) and
    that the types flow correctly.
    """
    import app.orchestrator.main_orchestrator as mo
    source = Path(mo.__file__).read_text(encoding="utf-8")

    # Assert the wiring block exists together (not just separate references)
    assert (
        "build_citations_from_tool_calls(\n                                _tool_calls"
        in source
        or "build_citations_from_tool_calls(_tool_calls"
        in source.replace("                                ", "")
    ), "V.B: wire must call build_citations_from_tool_calls with _tool_calls"
    assert "has_citations=bool(_citations)" in source


def test_vb_fail_safe_on_citation_exception() -> None:
    """V.B: citation build failure does NOT crash the response path.

    Structural check: the code wraps the citation build in try/except.
    """
    import app.orchestrator.main_orchestrator as mo
    source = Path(mo.__file__).read_text(encoding="utf-8")

    # Find V.B block — ensure it's wrapped in try/except
    vb_idx = source.find("Onda 4.5 V.B")
    assert vb_idx > 0
    block = source[vb_idx : vb_idx + 1500]
    assert "try:" in block
    assert "except Exception" in block
    assert "citation build skipped" in block.lower()
