"""GAP-03: Cursor-based pagination utility for large dataset endpoints.

Usage (in a new paginated endpoint):
    from app.shared.services.cursor_pagination import CursorPagination, PaginatedResult

    paginator = CursorPagination(limit=limit)
    result = await paginator.paginate(db, select(MyModel).where(...).order_by(...), cursor)
    return result.to_dict(serializer=lambda item: item.to_dict())

Multi-tenancy: callers MUST include company_id in the WHERE clause before passing the
query. This utility does not inject any tenant filter — that is the caller's responsibility.
"""
from __future__ import annotations

import json
import logging
from base64 import b64decode, b64encode
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

T = TypeVar("T")

_MAX_LIMIT = 200


@dataclass
class PaginatedResult(Generic[T]):
    items: list[T]
    next_cursor: Optional[str]
    has_more: bool
    total: Optional[int] = None  # available when count_total=True

    def to_dict(
        self,
        *,
        serializer: Callable[[T], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "items": [serializer(item) if serializer else item for item in self.items],
            "next_cursor": self.next_cursor,
            "has_more": self.has_more,
            **({"total": self.total} if self.total is not None else {}),
        }


class CursorPagination:
    """Offset-encoded cursor pagination.

    The cursor is a base64-encoded JSON with the next offset, so it is opaque
    to the client but easy to decode for debugging. Not suitable for real-time
    datasets where rows are inserted between pages — use keyset pagination for
    those cases (future ADR).
    """

    def __init__(self, limit: int = 20, max_limit: int = _MAX_LIMIT) -> None:
        self.limit = min(max(1, limit), max_limit)

    # ──────────────────────────────────────────────────────────── cursor codec ──

    @staticmethod
    def encode_cursor(offset: int) -> str:
        payload = json.dumps({"offset": offset})
        return b64encode(payload.encode()).decode()

    @staticmethod
    def decode_cursor(cursor: str) -> int:
        """Decode cursor → offset. Returns 0 on any error (fail-open)."""
        try:
            payload = json.loads(b64decode(cursor.encode()).decode())
            offset = int(payload.get("offset", 0))
            return max(0, offset)
        except Exception:
            logger.debug("[cursor_pagination] Invalid cursor — defaulting to offset=0")
            return 0

    # ───────────────────────────────────────────────────────────── paginate ──

    async def paginate(
        self,
        db: AsyncSession,
        query: Any,
        cursor: Optional[str] = None,
        *,
        count_total: bool = False,
    ) -> PaginatedResult:
        """Execute *query* with cursor pagination.

        Args:
            db: SQLAlchemy async session.
            query: A SQLAlchemy SELECT statement (already scoped to tenant).
            cursor: Opaque cursor from a previous response's ``next_cursor``.
            count_total: If True, run a COUNT(*) sub-query to populate result.total.
        """
        offset = self.decode_cursor(cursor) if cursor else 0

        # Fetch limit+1 to detect hasMore without a separate COUNT query.
        rows = (await db.execute(query.offset(offset).limit(self.limit + 1))).scalars().all()

        has_more = len(rows) > self.limit
        items = list(rows[: self.limit])

        next_cursor = self.encode_cursor(offset + self.limit) if has_more else None

        total: Optional[int] = None
        if count_total:
            # Wrap query in COUNT(*) — strip existing ORDER BY to avoid errors.
            count_q = select(func.count()).select_from(query.order_by(None).subquery())
            total = (await db.execute(count_q)).scalar_one()

        return PaginatedResult(items=items, next_cursor=next_cursor, has_more=has_more, total=total)
