"""Tests for GAP-02-005: ViewContextSchema — Pydantic schema for view_context.

Verifies:
- Valid payload validates cleanly
- Missing optional fields use safe defaults
- Extra fields from FE are tolerated (extra="ignore")
- Malformed pagination fields are caught gracefully
- parse_view_context() never raises — always graceful degradation
- modal_open is kept consistent with active_modal
"""
import pytest


# ---------------------------------------------------------------------------
# ViewContextSchema direct validation
# ---------------------------------------------------------------------------


def test_valid_full_payload_validates():
    """A complete, well-formed payload from FE validates without error."""
    from app.orchestrator.context.view_context_schema import ViewContextSchema

    data = {
        "page_type": "funil",
        "job_vacancy_id": "abc-123",
        "candidate_id": "cand-456",
        "current_stage": "triagem",
        "pagination_state": {
            "current_page": 2,
            "total_pages": 10,
            "page_size": 20,
            "total_items": 200,
        },
        "active_modal": "candidate_detail",
        "counts": {"total": 200},
        "active_filters": ["status=entrevista"],
        "captured_at": "2026-06-16T12:00:00.000Z",
    }
    schema = ViewContextSchema.model_validate(data)
    assert schema.page_type == "funil"
    assert schema.job_vacancy_id == "abc-123"
    assert schema.candidate_id == "cand-456"
    assert schema.pagination_state is not None
    assert schema.pagination_state.current_page == 2
    assert schema.active_modal == "candidate_detail"
    assert schema.captured_at == "2026-06-16T12:00:00.000Z"


def test_missing_optional_fields_use_defaults():
    """Empty dict → all fields get safe defaults, no ValidationError."""
    from app.orchestrator.context.view_context_schema import ViewContextSchema

    schema = ViewContextSchema.model_validate({})
    assert schema.page_type is None
    assert schema.job_vacancy_id is None
    assert schema.pagination_state is None
    assert schema.active_modal is None
    assert schema.captured_at is None
    assert schema.filters_active == {}
    assert schema.active_filters == []
    assert schema.counts == {}
    assert schema.visible_ids == []


def test_extra_fields_tolerated():
    """FE may send fields we don't know yet — they are silently ignored."""
    from app.orchestrator.context.view_context_schema import ViewContextSchema

    data = {
        "page_type": "vagas",
        "some_future_field": "value",
        "another_unknown": 42,
    }
    # Must not raise
    schema = ViewContextSchema.model_validate(data)
    assert schema.page_type == "vagas"
    # Extra fields are not stored
    assert not hasattr(schema, "some_future_field")


def test_malformed_pagination_page_not_negative():
    """Pagination fields < 1 should be caught by ge=1 constraint."""
    from pydantic import ValidationError
    from app.orchestrator.context.view_context_schema import PaginationStateSchema

    with pytest.raises(ValidationError):
        PaginationStateSchema.model_validate({"current_page": 0})


def test_pagination_total_items_optional():
    """total_items is optional in PaginationStateSchema."""
    from app.orchestrator.context.view_context_schema import PaginationStateSchema

    schema = PaginationStateSchema.model_validate({"current_page": 1, "total_pages": 5})
    assert schema.total_items is None


def test_modal_awareness_sync_modal_open():
    """modal_open is set to True when active_modal is present."""
    from app.orchestrator.context.view_context_schema import ModalAwarenessSchema

    schema = ModalAwarenessSchema.model_validate({"active_modal": "offer_review"})
    assert schema.modal_open is True


def test_modal_awareness_no_active_modal_stays_closed():
    """No active_modal → modal_open stays False."""
    from app.orchestrator.context.view_context_schema import ModalAwarenessSchema

    schema = ModalAwarenessSchema.model_validate({})
    assert schema.modal_open is False
    assert schema.active_modal is None


def test_entity_focus_validates():
    """EntityFocusSchema validates correctly."""
    from app.orchestrator.context.view_context_schema import ViewContextSchema

    data = {
        "entity_focus": {
            "type": "candidate",
            "id": "cand-789",
            "label": "Maria Santos",
        }
    }
    schema = ViewContextSchema.model_validate(data)
    assert schema.entity_focus is not None
    assert schema.entity_focus.id == "cand-789"
    assert schema.entity_focus.label == "Maria Santos"


# ---------------------------------------------------------------------------
# parse_view_context() — graceful wrapper
# ---------------------------------------------------------------------------


def test_parse_view_context_valid_payload():
    """Valid dict → returns ViewContextSchema."""
    from app.orchestrator.context.view_context_schema import parse_view_context

    result = parse_view_context({"page_type": "vagas", "captured_at": "2026-06-16T10:00:00Z"})
    assert result is not None
    assert result.page_type == "vagas"
    assert result.captured_at == "2026-06-16T10:00:00Z"


def test_parse_view_context_none_returns_none():
    """None input → None output (no context available)."""
    from app.orchestrator.context.view_context_schema import parse_view_context

    assert parse_view_context(None) is None


def test_parse_view_context_empty_dict_returns_none():
    """Empty dict → None (no useful context)."""
    from app.orchestrator.context.view_context_schema import parse_view_context

    # Empty dict is falsy check in parse_view_context → None
    assert parse_view_context({}) is None


def test_parse_view_context_extra_fields_tolerated():
    """Extra fields in raw dict are silently ignored."""
    from app.orchestrator.context.view_context_schema import parse_view_context

    result = parse_view_context({"page_type": "kanban", "future_field": "x"})
    assert result is not None
    assert result.page_type == "kanban"


def test_parse_view_context_never_raises_on_bad_pagination(monkeypatch):
    """Even if pydantic raises internally, parse_view_context never propagates."""
    from app.orchestrator.context import view_context_schema as mod

    # Force model_validate to raise unexpectedly
    original = mod.ViewContextSchema.model_validate

    def _raise(data, **kwargs):
        raise RuntimeError("Simulated unexpected error")

    monkeypatch.setattr(mod.ViewContextSchema, "model_validate", classmethod(lambda cls, d, **kw: _raise(d)))
    # Should not propagate — returns None gracefully
    result = mod.parse_view_context({"page_type": "vagas"})
    assert result is None
