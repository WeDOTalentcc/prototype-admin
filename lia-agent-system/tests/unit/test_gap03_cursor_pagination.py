"""Unit tests for GAP-03-001 + GAP-03-002 + GAP-03-003 — cursor pagination.

GAP-03-001: encode/decode round-trip
GAP-03-002: decode handles None / invalid gracefully (fail-open → offset 0)
GAP-03-003: build_cursor_response produces correct has_more / next_cursor
"""
from __future__ import annotations

import json
from base64 import b64encode

import pytest

from app.shared.pagination import (
    CursorPagination,
    build_cursor_response,
    decode_cursor,
    encode_cursor,
)


# ─────────────────────────────────────────── GAP-03-001: encode/decode ──────


class TestEncodeDecode:
    def test_encode_decode_roundtrip(self):
        for offset in [0, 1, 20, 100, 999, 10_000]:
            cursor = encode_cursor(offset)
            assert decode_cursor(cursor) == offset, f"roundtrip failed for offset={offset}"

    def test_cursor_is_opaque_string(self):
        cursor = encode_cursor(42)
        assert isinstance(cursor, str)
        # Should not contain raw digits visibly (it's base64 encoded)
        assert "42" not in cursor


# ─────────────────────────────────────────── GAP-03-002: fail-open decode ───


class TestDecodeFailOpen:
    def test_decode_none_returns_zero(self):
        assert decode_cursor(None) == 0

    def test_decode_empty_string_returns_zero(self):
        assert decode_cursor("") == 0

    def test_decode_invalid_base64_returns_zero(self):
        assert decode_cursor("!!!not-base64!!!") == 0

    def test_decode_valid_base64_but_missing_offset_key_returns_zero(self):
        cursor = b64encode(json.dumps({"wrong_key": 5}).encode()).decode()
        # CursorPagination.decode_cursor returns 0 when offset key missing
        assert decode_cursor(cursor) == 0

    def test_decode_negative_offset_clamped(self):
        cursor = b64encode(json.dumps({"offset": -10}).encode()).decode()
        assert decode_cursor(cursor) == 0


# ─────────────────────────────────────────── GAP-03-003: build_cursor_response


class TestBuildCursorResponse:
    def test_has_more_true_when_items_equals_limit(self):
        items = list(range(20))
        result = build_cursor_response(items, offset=0, limit=20)
        assert result["has_more"] is True
        assert result["next_cursor"] is not None

    def test_has_more_false_when_fewer_than_limit(self):
        items = list(range(5))
        result = build_cursor_response(items, offset=0, limit=20)
        assert result["has_more"] is False
        assert result["next_cursor"] is None

    def test_next_cursor_decodes_to_correct_offset(self):
        items = list(range(20))
        result = build_cursor_response(items, offset=0, limit=20)
        assert decode_cursor(result["next_cursor"]) == 20

    def test_next_cursor_advances_on_second_page(self):
        items = list(range(20))
        result = build_cursor_response(items, offset=40, limit=20)
        assert decode_cursor(result["next_cursor"]) == 60

    def test_total_count_included_when_provided(self):
        items = list(range(5))
        result = build_cursor_response(items, offset=0, limit=20, total=100)
        assert result["total_count"] == 100

    def test_total_count_none_when_not_provided(self):
        items = list(range(5))
        result = build_cursor_response(items, offset=0, limit=20)
        assert result["total_count"] is None

    def test_items_preserved_in_response(self):
        items = [{"id": 1}, {"id": 2}]
        result = build_cursor_response(items, offset=0, limit=20)
        assert result["items"] == items


# ─────────────────────────────────── integration: list_candidates wiring ────


class TestListCandidatesWiring:
    """Verify list_candidates endpoint accepts cursor param and returns pagination fields."""

    def test_cursor_param_registered_in_endpoint(self):
        """Endpoint must declare cursor as an optional Query param."""
        from app.api.v1.candidates.candidates_crud import list_candidates
        import inspect
        sig = inspect.signature(list_candidates)
        assert "cursor" in sig.parameters, "cursor param missing from list_candidates"

    def test_cursor_param_default_is_none(self):
        from app.api.v1.candidates.candidates_crud import list_candidates
        import inspect
        sig = inspect.signature(list_candidates)
        param = sig.parameters["cursor"]
        # FastAPI Query wraps the default; the annotation should allow None
        ann = param.annotation
        assert ann is not inspect.Parameter.empty
        # annotation should include str | None
        ann_str = str(ann)
        assert "None" in ann_str or "Optional" in ann_str, f"cursor should be optional, got {ann_str}"

    def test_pagination_imports_present_in_module(self):
        """decode_cursor and encode_cursor must be importable from the module."""
        import app.api.v1.candidates.candidates_crud as mod
        # They are imported at module level; accessing via module dict
        assert hasattr(mod, "decode_cursor"), "decode_cursor not imported in candidates_crud"
        assert hasattr(mod, "encode_cursor"), "encode_cursor not imported in candidates_crud"
