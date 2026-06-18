"""Optimistic locking support for job vacancy updates."""

from datetime import datetime
from fastapi import HTTPException


def check_optimistic_lock(
    db_updated_at: datetime | None,
    expected_updated_at: datetime | None,
) -> None:
    """Check optimistic lock: raise HTTPException(409) if stale."""
    if expected_updated_at is None:
        return
    
    if db_updated_at is None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "optimistic_lock_conflict",
                "message": "Recurso foi modificado. Recarregue e tente novamente.",
                "expected_updated_at": expected_updated_at.isoformat(),
                "current_updated_at": None,
            }
        )
    
    if db_updated_at != expected_updated_at:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "optimistic_lock_conflict",
                "message": "Recurso foi modificado. Recarregue e tente novamente.",
                "expected_updated_at": expected_updated_at.isoformat(),
                "current_updated_at": db_updated_at.isoformat(),
            }
        )
