"""GAP-03: Canonical cursor pagination public API.

Re-exports the cursor pagination primitives from
app.shared.services.cursor_pagination under the canonical
app.shared.pagination path so callers have a stable, short import.

Usage::

    from app.shared.pagination import CursorPagination, PaginatedResult
    from app.shared.pagination import encode_cursor, decode_cursor, build_cursor_response

Multi-tenancy note: callers MUST scope the SQLAlchemy query to the current
company BEFORE passing it to CursorPagination.paginate.  This module
does NOT inject any tenant filter.
"""
from __future__ import annotations

from app.shared.services.cursor_pagination import (  # noqa: F401 — re-export
    CursorPagination,
    PaginatedResult,
)

# ── convenience free functions ──────────────────────────────────────────────


def encode_cursor(offset: int) -> str:
    """Encode integer offset to opaque base-64 cursor string."""
    return CursorPagination.encode_cursor(offset)


def decode_cursor(cursor: str | None) -> int:
    """Decode cursor string → offset integer. Returns 0 when *cursor* is
    None, empty, or unparseable (fail-open contract)."""
    if not cursor:
        return 0
    return CursorPagination.decode_cursor(cursor)


def build_cursor_response(
    items: list,
    offset: int,
    limit: int,
    total: int | None = None,
) -> dict:
    """Build a ready-to-return cursor-pagination dict.

    Args:
        items:  The page of serialised items (already trimmed to *limit*).
        offset: The offset used to fetch this page.
        limit:  The page size requested.
        total:  Optional total row count (expensive; omit when not pre-computed).

    Returns::

        {
            "items": [...],
            "next_cursor": "<opaque str>" | None,
            "has_more": True | False,
            "total_count": <int> | None,
        }
    """
    has_more = len(items) == limit
    next_offset = offset + limit if has_more else None
    return {
        "items": items,
        "next_cursor": encode_cursor(next_offset) if next_offset is not None else None,
        "has_more": has_more,
        "total_count": total,
    }
