"""
Anti-regressão · W2-010 Phase A (2026-05-22) — Canonical Rails client.

Verifica:
1. Canonical home `app/shared/integration/rails_client.py` existe + expõe
   classe RailsClient + 3 helpers async.
2. Métodos têm OTel `@trace_span` decorator wired (PRIMEIRA observability
   em path Rails).
3. `app/shared/rails_client.py` virou shim re-exportando do canonical
   com DeprecationWarning.
4. 3 helpers preservam API original (return dict, swallow exceptions).
5. Idempotency key (W2-009) passa transparentemente via delegate.

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W2-010).
Sensor: scripts/check_rails_client_canonical_home.py.
"""
from __future__ import annotations

import warnings
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCanonicalHomeExists:
    """`app/shared/integration/rails_client.py` é o canonical home."""

    def test_canonical_module_importable(self) -> None:
        from app.shared.integration import rails_client  # noqa: F401

    def test_canonical_exports_class_and_helpers(self) -> None:
        from app.shared.integration.rails_client import (  # noqa: F401
            RailsClient,
            rails_get,
            rails_patch,
            rails_post,
        )

    def test_class_has_all_5_http_methods(self) -> None:
        from app.shared.integration.rails_client import RailsClient

        for method_name in ("get", "post", "put", "patch", "delete"):
            assert hasattr(RailsClient, method_name), (
                f"RailsClient missing canonical method: {method_name}"
            )


class TestOTelObservabilityWired:
    """OTel `@trace_span` decorator presente em todos os 5 métodos HTTP."""

    def test_all_methods_have_trace_span_wrap(self) -> None:
        import inspect

        from app.shared.integration.rails_client import RailsClient

        src = inspect.getsource(RailsClient)
        # Cada método deve ter @trace_span imediatamente acima
        for method in ("get", "post", "put", "patch", "delete"):
            assert f"@trace_span(\"rails.{method}\"" in src, (
                f"Method {method} NÃO tem @trace_span decorator wired.\n"
                f"Esperado: @trace_span(\"rails.{method}\", ...)"
            )


class TestShimBehavior:
    """`app/shared/rails_client.py` agora é deprecation shim."""

    def test_shim_emits_deprecation_warning(self) -> None:
        import importlib

        # Force reimport para capturar warning
        import app.shared.rails_client

        importlib.reload(app.shared.rails_client)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            importlib.reload(app.shared.rails_client)
            deprecations = [
                warn for warn in w if issubclass(warn.category, DeprecationWarning)
            ]
            assert len(deprecations) >= 1, (
                "Shim deve emitir DeprecationWarning indicando canonical W2-010"
            )

    def test_shim_reexports_helpers(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            from app.shared.rails_client import rails_get, rails_patch, rails_post

        from app.shared.integration.rails_client import (
            rails_get as canonical_get,
            rails_patch as canonical_patch,
            rails_post as canonical_post,
        )
        # Mesma função (re-export, não duplicado)
        assert rails_get is canonical_get
        assert rails_patch is canonical_patch
        assert rails_post is canonical_post


class TestHelpersBackCompat:
    """3 helpers preservam API original (return dict, swallow exceptions)."""

    @pytest.mark.asyncio
    async def test_rails_get_returns_dict(self) -> None:
        from app.shared.integration.rails_client import rails_get
        from app.shared.integration import rails_client as canonical_mod

        mock_singleton = MagicMock()
        mock_resp = MagicMock(data={"foo": "bar"})
        mock_singleton.get = AsyncMock(return_value=mock_resp)

        with patch.object(canonical_mod, "_get_singleton", return_value=mock_singleton):
            result = await rails_get("/v1/jobs")

        assert result == {"foo": "bar"}

    @pytest.mark.asyncio
    async def test_rails_post_swallows_exception_returns_empty(self) -> None:
        from app.shared.integration.rails_client import rails_post
        from app.shared.integration import rails_client as canonical_mod

        mock_singleton = MagicMock()
        mock_singleton.post = AsyncMock(side_effect=RuntimeError("boom"))

        with patch.object(canonical_mod, "_get_singleton", return_value=mock_singleton):
            result = await rails_post("/v1/jobs", data={"x": 1})

        assert result == {}  # Swallows exception, returns empty dict


class TestIdempotencyKeyPassthrough:
    """W2-009 idempotency passa transparentemente pelo canonical (delegate)."""

    @pytest.mark.asyncio
    async def test_post_forwards_idempotency_key_to_delegate(self) -> None:
        from app.shared.integration.rails_client import RailsClient

        client = RailsClient()
        mock_delegate = MagicMock()
        mock_delegate.post = AsyncMock(return_value=MagicMock())
        client._delegate = mock_delegate

        explicit_key = "00000000-0000-4000-8000-000000000001"
        await client.post("/jobs", json_body={}, idempotency_key=explicit_key)

        call_kwargs = mock_delegate.post.call_args.kwargs
        assert call_kwargs.get("idempotency_key") == explicit_key, (
            f"W2-009 idempotency_key DEVE ser forwarded pro delegate. "
            f"Got: {call_kwargs}"
        )


class TestSensorBlocking:
    """W2-010 sensor BLOCKING."""

    def test_sensor_exists(self) -> None:
        from pathlib import Path

        sensor = (
            Path(__file__).resolve().parents[2]
            / "scripts"
            / "check_rails_client_canonical_home.py"
        )
        assert sensor.exists(), f"Sensor missing: {sensor}"

    def test_sensor_passes_strict(self) -> None:
        import subprocess
        import sys
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[2]
        sensor = repo_root / "scripts" / "check_rails_client_canonical_home.py"
        result = subprocess.run(
            [sys.executable, str(sensor)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        assert result.returncode == 0, (
            f"Canonical home sensor FAILED (exit={result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
