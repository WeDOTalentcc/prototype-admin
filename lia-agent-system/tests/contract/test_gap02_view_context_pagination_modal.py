"""Tests for GAP-02-001: view_context pagination + modal awareness.

Verifies that format_view_context handles:
- pagination_state dict (current_page, total_pages, page_size, total_items)
- active_modal string (which modal is open)

Both fields are optional — backward-compatible. When absent, output is unchanged.
"""
import pytest


def test_pagination_state_surfaced():
    """Recruiter on page 3 of 10 — agent must know this."""
    from app.orchestrator.context.view_context import format_view_context
    out = format_view_context({
        "page_type": "funil",
        "counts": {"total": 200},
        "pagination_state": {
            "current_page": 3,
            "total_pages": 10,
            "page_size": 20,
            "total_items": 200,
        },
    })
    assert "3" in out and "10" in out, (
        "GAP-02-001 NOT FIXED: pagination_state not rendered. "
        "format_view_context must output current_page and total_pages when pagination_state is present."
    )
    # Should signal this is paginated content
    assert "página" in out.lower() or "pag" in out.lower(), (
        "GAP-02-001 NOT FIXED: pagination output missing 'página' label."
    )


def test_active_modal_surfaced():
    """Recruiter has offer modal open — agent must know context."""
    from app.orchestrator.context.view_context import format_view_context
    out = format_view_context({
        "page_type": "kanban",
        "active_modal": "offer_review",
    })
    assert "offer_review" in out or "modal" in out.lower(), (
        "GAP-02-001 NOT FIXED: active_modal not rendered. "
        "format_view_context must output active_modal when present."
    )


def test_active_modal_null_does_not_crash():
    """None active_modal is silently ignored — no mention of modal in output."""
    from app.orchestrator.context.view_context import format_view_context
    out = format_view_context({
        "page_type": "vagas",
        "active_modal": None,
    })
    # Should not crash, should not emit modal line
    assert "modal" not in out.lower()


def test_pagination_state_missing_does_not_break_existing():
    """Backward-compat: no pagination_state → same output as before."""
    from app.orchestrator.context.view_context import format_view_context
    out = format_view_context({
        "page_type": "vagas",
        "counts": {"total": 50},
    })
    assert "Vagas" in out
    assert "50" in out
    assert "página" not in out.lower()


def test_only_first_page_not_noisy():
    """Page 1 of 1 should still be mentioned so agent knows table is not truncated."""
    from app.orchestrator.context.view_context import format_view_context
    out = format_view_context({
        "page_type": "funil",
        "pagination_state": {
            "current_page": 1,
            "total_pages": 1,
            "page_size": 50,
            "total_items": 12,
        },
    })
    # Even page 1/1 informs agent that all items are visible
    assert "1" in out


def test_view_context_from_context_passes_pagination_through():
    """view_context_from_context must not strip pagination_state from explicit vc."""
    from app.orchestrator.context.view_context import view_context_from_context
    ctx = {
        "view_context": {
            "page_type": "funil",
            "pagination_state": {"current_page": 2, "total_pages": 5},
            "active_modal": "candidate_detail",
        }
    }
    vc = view_context_from_context(ctx)
    assert vc is not None
    assert vc.get("pagination_state", {}).get("current_page") == 2
    assert vc.get("active_modal") == "candidate_detail"
