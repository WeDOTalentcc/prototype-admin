"""Unit tests for CursorPagination — pure, no DB required.

GAP-03-001: cursor encode/decode round-trip
GAP-03-002: limit boundary (respects max_limit)
GAP-03-003: has_more / next_cursor logic
GAP-03-004: decode fails gracefully (fail-open → offset 0)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.shared.services.cursor_pagination import CursorPagination, PaginatedResult


# ─────────────────────────────────────────────── cursor codec ──

class TestCursorCodec:
    def test_encode_decode_round_trip(self):
        for offset in [0, 20, 100, 999]:
            cursor = CursorPagination.encode_cursor(offset)
            assert CursorPagination.decode_cursor(cursor) == offset

    def test_decode_invalid_cursor_returns_zero(self):
        assert CursorPagination.decode_cursor("!!!invalid!!!") == 0
        assert CursorPagination.decode_cursor("") == 0
        assert CursorPagination.decode_cursor("eyJub3RvZmZzZXQiOiAifQ==") == 0  # no 'offset' key

    def test_decode_negative_offset_clamped_to_zero(self):
        import json
        from base64 import b64encode
        cursor = b64encode(json.dumps({"offset": -5}).encode()).decode()
        assert CursorPagination.decode_cursor(cursor) == 0


# ─────────────────────────────────────────────── limit cap ──

class TestLimitCap:
    def test_limit_capped_at_max(self):
        p = CursorPagination(limit=9999, max_limit=100)
        assert p.limit == 100

    def test_limit_below_max_unchanged(self):
        p = CursorPagination(limit=25, max_limit=200)
        assert p.limit == 25

    def test_limit_minimum_is_one(self):
        p = CursorPagination(limit=0)
        assert p.limit == 1


# ─────────────────────────────────────────────── paginate (mocked session) ──

def _make_db_mock(rows: list) -> AsyncMock:
    """Build an AsyncSession mock returning *rows* from execute(...).scalars().all()."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    db = AsyncMock()
    db.execute = AsyncMock(return_value=execute_result)
    return db


class TestPaginate:
    @pytest.mark.asyncio
    async def test_has_more_when_extra_row_returned(self):
        items = list(range(21))  # limit=20, fetches 21 → has_more=True
        db = _make_db_mock(items)
        p = CursorPagination(limit=20)
        result = await p.paginate(db, MagicMock(), cursor=None)
        assert result.has_more is True
        assert result.next_cursor is not None
        assert len(result.items) == 20

    @pytest.mark.asyncio
    async def test_no_more_when_exact_limit_returned(self):
        items = list(range(20))  # fetches 21, gets 20 → has_more=False
        db = _make_db_mock(items)
        p = CursorPagination(limit=20)
        result = await p.paginate(db, MagicMock(), cursor=None)
        assert result.has_more is False
        assert result.next_cursor is None
        assert len(result.items) == 20

    @pytest.mark.asyncio
    async def test_no_more_when_fewer_than_limit(self):
        items = list(range(5))
        db = _make_db_mock(items)
        p = CursorPagination(limit=20)
        result = await p.paginate(db, MagicMock(), cursor=None)
        assert result.has_more is False
        assert result.next_cursor is None

    @pytest.mark.asyncio
    async def test_cursor_advances_offset(self):
        items_page1 = list(range(21))
        db = _make_db_mock(items_page1)
        p = CursorPagination(limit=20)
        result1 = await p.paginate(db, MagicMock(), cursor=None)
        cursor2 = result1.next_cursor

        # Decode the cursor and verify it points to offset 20
        assert CursorPagination.decode_cursor(cursor2) == 20

    @pytest.mark.asyncio
    async def test_to_dict_with_serializer(self):
        db = _make_db_mock([{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}])
        p = CursorPagination(limit=20)
        result = await p.paginate(db, MagicMock())
        d = result.to_dict(serializer=lambda x: x)
        assert d["items"] == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        assert "has_more" in d
        assert "next_cursor" in d

    @pytest.mark.asyncio
    async def test_invalid_cursor_treated_as_first_page(self):
        db = _make_db_mock([1, 2, 3])
        p = CursorPagination(limit=20)
        result = await p.paginate(db, MagicMock(), cursor="INVALID")
        assert len(result.items) == 3
        assert result.has_more is False
