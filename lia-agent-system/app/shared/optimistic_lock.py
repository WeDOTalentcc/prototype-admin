"""GAP-05-004: Optimistic locking helper for concurrent edit protection.

Uses `updated_at` as the lock token. When a client sends the timestamp
it last saw (expected_updated_at) and the DB value has moved, the helper
raises HTTP 409 Conflict with the current DB timestamp in the response
so the client can merge/retry.

Backward-compatible: passing expected=None skips the check entirely.
"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException


def check_optimistic_lock(
    db_updated_at: Optional[datetime],
    expected_updated_at: Optional[datetime],
) -> None:
    """Compare DB timestamp against client expectation.

    Args:
        db_updated_at: Current `updated_at` value from the database row.
        expected_updated_at: Timestamp the client believes is current.
            None means "skip check" (backward compat).

    Raises:
        HTTPException(409): When timestamps do not match, meaning another
            user modified the record after the client read it. The detail
            dict includes `current_updated_at` so the FE can offer a
            reload-and-retry flow.
    """
    if expected_updated_at is None:
        return  # Client opted out of locking -- backward compat

    if db_updated_at != expected_updated_at:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "optimistic_lock_conflict",
                "message": (
                    "This vacancy was modified by another user since you "
                    "loaded it. Please reload and try again."
                ),
                "current_updated_at": (
                    db_updated_at.isoformat() if db_updated_at else None
                ),
                "expected_updated_at": expected_updated_at.isoformat(),
            },
        )
