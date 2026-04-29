"""Single source of truth for JD upload size limits.

Both the FastAPI backend and the Next.js proxy must agree on the same
ceiling so the user does not get a confusing 413 from one tier while the
other tier accepted the bytes (Audit M-12).

The value can be overridden via the ``UPLOAD_JD_MAX_BYTES`` env var so
operations can tune it without redeploying. Default is 10 MiB.

Frontend usage: ``plataforma-lia/src/app/api/backend-proxy/jd-import/upload/route.ts``
reads the same env var (``UPLOAD_JD_MAX_BYTES``) — keep both sides in lock-step.
"""
from __future__ import annotations

import os

DEFAULT_JD_UPLOAD_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MiB


def _resolve_jd_upload_max_bytes() -> int:
    """Return the effective JD upload ceiling in bytes.

    Reads ``UPLOAD_JD_MAX_BYTES`` from the environment. Invalid values fall
    back to the default to avoid an exception at import time.
    """
    raw = os.getenv("UPLOAD_JD_MAX_BYTES")
    if not raw:
        return DEFAULT_JD_UPLOAD_MAX_BYTES
    try:
        value = int(raw)
        if value <= 0:
            return DEFAULT_JD_UPLOAD_MAX_BYTES
        return value
    except (TypeError, ValueError):
        return DEFAULT_JD_UPLOAD_MAX_BYTES


JD_UPLOAD_MAX_BYTES: int = _resolve_jd_upload_max_bytes()


def jd_upload_max_mb() -> int:
    """Human-readable ceiling in MiB used in error messages."""
    return max(1, JD_UPLOAD_MAX_BYTES // (1024 * 1024))
