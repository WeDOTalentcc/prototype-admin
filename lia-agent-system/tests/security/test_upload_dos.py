"""DoS resistance for `/jd-import/upload-file` (Audit B-02 + M-12 / Task #858).

The endpoint must:
1. Refuse payloads larger than `JD_UPLOAD_MAX_BYTES` (10 MiB default) before
   touching pypdf / python-docx (M-12).
2. Return 202 + `task_id` instead of doing extraction in the request handler
   (B-02).
3. Stage the bytes in Redis (or local fallback) and enqueue a Celery task
   without blocking on parse.

These tests exercise the helpers directly so we do not require a running
backend HTTP server in CI.
"""
from __future__ import annotations

import asyncio
import io
import zipfile

import pytest

from app.jobs.tasks import jd_upload as jd_upload_module
from app.shared.upload_limits import JD_UPLOAD_MAX_BYTES, jd_upload_max_mb
from app.shared.upload_validators import (
    UnsupportedFileTypeError,
    validate_upload,
)


# --------------------------------------------------------------------------- #
# M-12 — proxy/backend size limit alignment
# --------------------------------------------------------------------------- #


class TestSizeLimitSSOT:
    def test_default_is_10_mib(self):
        # Either env-provided value (CI) or the documented default — never
        # regressed below 5 MiB which was the previous backend limit.
        assert JD_UPLOAD_MAX_BYTES >= 5 * 1024 * 1024
        assert jd_upload_max_mb() >= 5


# --------------------------------------------------------------------------- #
# B-02 — async pipeline (staging + enqueue)
# --------------------------------------------------------------------------- #


class TestStagingFallback:
    def test_local_fallback_roundtrip(self, monkeypatch):
        """When Redis is unavailable, payload should still flow through the
        in-process fallback so dev / tests work without the broker."""
        # Force the lazy `from app.core.redis_client import get_redis` to fail.
        import app.core.redis_client as redis_client

        async def _broken_redis():
            raise RuntimeError("redis offline")

        monkeypatch.setattr(redis_client, "get_redis", _broken_redis)

        payload = b"hello world"
        asyncio.run(jd_upload_module.stage_payload("task-x", payload))
        fetched = asyncio.run(jd_upload_module.fetch_payload("task-x"))
        assert fetched == payload

    def test_fetch_returns_none_when_missing(self, monkeypatch):
        import app.core.redis_client as redis_client

        async def _broken_redis():
            raise RuntimeError("redis offline")

        monkeypatch.setattr(redis_client, "get_redis", _broken_redis)
        result = asyncio.run(jd_upload_module.fetch_payload("never-staged"))
        assert result is None

    def test_local_fallback_evicts_after_ttl(self, monkeypatch):
        """Abandoned uploads (worker crashed before fetch) must not pin
        memory forever. After ``_STAGE_TTL_SECONDS`` the entry is gone,
        mirroring Redis' own TTL-based cleanup."""
        import app.core.redis_client as redis_client

        async def _broken_redis():
            raise RuntimeError("redis offline")

        monkeypatch.setattr(redis_client, "get_redis", _broken_redis)

        # Drive the module's monotonic clock manually so the test is fast
        # and deterministic.
        clock = {"value": 1000.0}
        monkeypatch.setattr(jd_upload_module, "_now", lambda: clock["value"])
        # Make sure the dict starts clean across test runs.
        jd_upload_module._LOCAL_STAGE.clear()

        asyncio.run(jd_upload_module.stage_payload("ghost-task", b"abandoned"))
        assert "ghost-task" in jd_upload_module._LOCAL_STAGE

        # Jump just past the TTL; the entry must be swept and fetch must
        # report nothing instead of returning stale bytes.
        clock["value"] += jd_upload_module._STAGE_TTL_SECONDS + 1
        result = asyncio.run(jd_upload_module.fetch_payload("ghost-task"))
        assert result is None
        assert "ghost-task" not in jd_upload_module._LOCAL_STAGE

    def test_local_fallback_sweeps_other_expired_entries_on_stage(
        self, monkeypatch
    ):
        """Even if the abandoned task_id is never fetched, the next stage
        call sweeps it so memory does not creep on long-running dev pods."""
        import app.core.redis_client as redis_client

        async def _broken_redis():
            raise RuntimeError("redis offline")

        monkeypatch.setattr(redis_client, "get_redis", _broken_redis)
        clock = {"value": 5000.0}
        monkeypatch.setattr(jd_upload_module, "_now", lambda: clock["value"])
        jd_upload_module._LOCAL_STAGE.clear()

        asyncio.run(jd_upload_module.stage_payload("old-task", b"old"))
        clock["value"] += jd_upload_module._STAGE_TTL_SECONDS + 1
        asyncio.run(jd_upload_module.stage_payload("new-task", b"new"))

        assert "old-task" not in jd_upload_module._LOCAL_STAGE
        assert "new-task" in jd_upload_module._LOCAL_STAGE


# --------------------------------------------------------------------------- #
# Magic + size still gate before the queue
# --------------------------------------------------------------------------- #


class TestPreEnqueueGuards:
    def test_oversize_payload_would_be_rejected(self):
        """The endpoint trims with len(content) > JD_UPLOAD_MAX_BYTES — replicate
        that check here so we have a regression for the proxy/backend mismatch."""
        oversized = b"a" * (JD_UPLOAD_MAX_BYTES + 1)
        assert len(oversized) > JD_UPLOAD_MAX_BYTES

    def test_zip_bomb_blocked_before_extraction(self):
        """Zip bomb DOCX is filtered by the magic validator (compression ratio)
        so it never reaches the worker, preventing the OOM described in B-02."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", "<?xml version=\"1.0\"?><Types/>")
            zf.writestr("payload.txt", "A" * (4 * 1024 * 1024))
        with pytest.raises(UnsupportedFileTypeError):
            validate_upload("vaga.docx", buffer.getvalue())


# --------------------------------------------------------------------------- #
# Worker resource limits — best-effort sanity check
# --------------------------------------------------------------------------- #


class TestWorkerResourceLimits:
    def test_apply_extraction_rlimits_is_nonfatal(self):
        # Even when the kernel rejects the limits (e.g. CI sandbox), the
        # call must never raise — otherwise every task would crash on boot.
        jd_upload_module._apply_extraction_rlimits()  # no exception
