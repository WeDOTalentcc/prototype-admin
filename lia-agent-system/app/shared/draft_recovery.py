"""Draft recovery pattern — save partial form state for later recovery.

Provides utilities for building, validating, and merging draft snapshots.
Used by the job vacancy PATCH endpoint to persist wizard state when a user
navigates away mid-wizard.

Pattern: status=rascunho vacancies store a ``draft_data`` JSONB snapshot that
the FE can retrieve via GET /api/v1/job-vacancies/{job_id}/draft and restore.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

DRAFT_TTL_DAYS = 7
_DRAFT_VERSION = 1


def build_draft_snapshot(
    form_data: dict[str, Any],
    step: str | None = None,
) -> dict[str, Any]:
    """Build a draft snapshot dict with metadata.

    Args:
        form_data: Partial form fields captured from the wizard.
        step: Current wizard step identifier (e.g. "descricao", "requisitos").

    Returns:
        Snapshot dict with ``data``, ``step``, ``saved_at``, ``version``.
    """
    return {
        "data": form_data,
        "step": step,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "version": _DRAFT_VERSION,
    }


def is_draft_expired(
    snapshot: dict[str, Any],
    ttl_days: int = DRAFT_TTL_DAYS,
) -> bool:
    """Check if a draft snapshot is older than TTL.

    Args:
        snapshot: Snapshot dict previously built by :func:`build_draft_snapshot`.
        ttl_days: Maximum age in days before the snapshot is considered expired.

    Returns:
        ``True`` if expired or malformed, ``False`` if still valid.
    """
    try:
        saved_at_raw = snapshot["saved_at"]
        saved_at = datetime.fromisoformat(saved_at_raw)
        # Normalise to UTC-aware for comparison
        if saved_at.tzinfo is None:
            saved_at = saved_at.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - saved_at).days
        return age_days > ttl_days
    except (KeyError, ValueError, TypeError):
        return True


def merge_draft_with_existing(
    existing: dict[str, Any],
    draft: dict[str, Any],
) -> dict[str, Any]:
    """Merge draft fields into existing, preferring non-None/non-empty draft values.

    Existing keys that are absent in the draft are kept as-is.
    Draft keys with ``None`` or empty-string values do NOT override existing.

    Args:
        existing: Current persisted vacancy fields.
        draft: Partial fields from the wizard draft snapshot (``snapshot["data"]``).

    Returns:
        Merged dict — safe to pass as an update payload.
    """
    merged = dict(existing)
    for key, value in draft.items():
        if value is not None and value != "":
            merged[key] = value
    return merged
