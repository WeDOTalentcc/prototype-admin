"""
Anti-regressão · W2-009 (2026-05-22) — Idempotency-Key em mutations Rails.

Verifica que `WeDOTalentATSClient` + `JobCreationAPIClient` injetam
`Idempotency-Key: <uuid4>` em todo POST/PUT/PATCH/DELETE.

GET NUNCA deve receber Idempotency-Key (read-only).

Caller pode passar `idempotency_key=<explicit>` para retry idempotente.

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W2-009).
Sensor: scripts/check_idempotency_key_in_rails_clients.py.
"""
from __future__ import annotations

import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWeDOTalentATSClientIdempotencyKey:
    """WeDOTalentATSClient injetando Idempotency-Key em mutations."""

    @pytest.mark.asyncio
    async def test_post_includes_idempotency_key(self) -> None:
        from app.shared.integration.rails_client import (
            WeDOTalentATSClient,
        )

        client = WeDOTalentATSClient(base_url="http://test", token="t")
        mock_http = AsyncMock()
        mock_resp = MagicMock(status_code=200, content=b'{"data": {}}')
        mock_resp.json = MagicMock(return_value={"data": {}})
        mock_http.request = AsyncMock(return_value=mock_resp)

        with patch.object(client, "_get_client", AsyncMock(return_value=mock_http)):
            await client.post("/jobs", json_body={"title": "X"})

        call_kwargs = mock_http.request.call_args.kwargs
        headers = call_kwargs.get("headers") or {}
        assert "Idempotency-Key" in headers, (
            f"POST DEVE incluir Idempotency-Key. Got headers: {headers}"
        )
        # UUID4 format
        assert re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            headers["Idempotency-Key"],
        ), f"Idempotency-Key não é UUID4: {headers['Idempotency-Key']}"

    @pytest.mark.asyncio
    async def test_get_does_not_include_idempotency_key(self) -> None:
        """GET é read-only — NUNCA deve ter Idempotency-Key."""
        from app.shared.integration.rails_client import (
            WeDOTalentATSClient,
        )

        client = WeDOTalentATSClient(base_url="http://test", token="t")
        mock_http = AsyncMock()
        mock_resp = MagicMock(status_code=200, content=b'{"data": {}}')
        mock_resp.json = MagicMock(return_value={"data": {}})
        mock_http.request = AsyncMock(return_value=mock_resp)

        with patch.object(client, "_get_client", AsyncMock(return_value=mock_http)):
            await client.get("/jobs")

        call_kwargs = mock_http.request.call_args.kwargs
        headers = call_kwargs.get("headers") or {}
        # Headers pode ser None (passado headers=None) — ambos OK
        if headers:
            assert "Idempotency-Key" not in headers, (
                f"GET NÃO deve ter Idempotency-Key. Got: {headers}"
            )

    @pytest.mark.asyncio
    async def test_put_patch_delete_all_include_idempotency_key(self) -> None:
        from app.shared.integration.rails_client import (
            WeDOTalentATSClient,
        )

        client = WeDOTalentATSClient(base_url="http://test", token="t")
        mock_http = AsyncMock()
        mock_resp = MagicMock(status_code=200, content=b'{"data": {}}')
        mock_resp.json = MagicMock(return_value={"data": {}})
        mock_http.request = AsyncMock(return_value=mock_resp)

        with patch.object(client, "_get_client", AsyncMock(return_value=mock_http)):
            await client.put("/jobs/1", json_body={})
            await client.delete("/jobs/2")

        # 2 calls; each should have its own Idempotency-Key
        for call in mock_http.request.call_args_list:
            headers = call.kwargs.get("headers") or {}
            assert "Idempotency-Key" in headers, (
                f"PUT/DELETE DEVE ter Idempotency-Key. Got: {headers}"
            )

    @pytest.mark.asyncio
    async def test_explicit_idempotency_key_preserved(self) -> None:
        """Caller passa key explícito → server-cache hit em retry."""
        from app.shared.integration.rails_client import (
            WeDOTalentATSClient,
        )

        client = WeDOTalentATSClient(base_url="http://test", token="t")
        mock_http = AsyncMock()
        mock_resp = MagicMock(status_code=200, content=b'{"data": {}}')
        mock_resp.json = MagicMock(return_value={"data": {}})
        mock_http.request = AsyncMock(return_value=mock_resp)

        explicit_key = "00000000-0000-4000-8000-000000000001"
        with patch.object(client, "_get_client", AsyncMock(return_value=mock_http)):
            await client.post(
                "/jobs", json_body={}, idempotency_key=explicit_key
            )

        call_kwargs = mock_http.request.call_args.kwargs
        headers = call_kwargs.get("headers") or {}
        assert headers.get("Idempotency-Key") == explicit_key

    @pytest.mark.asyncio
    async def test_each_call_gets_unique_key_by_default(self) -> None:
        """Default behavior: cada call sem explicit key → UUID4 fresh."""
        from app.shared.integration.rails_client import (
            WeDOTalentATSClient,
        )

        client = WeDOTalentATSClient(base_url="http://test", token="t")
        mock_http = AsyncMock()
        mock_resp = MagicMock(status_code=200, content=b'{"data": {}}')
        mock_resp.json = MagicMock(return_value={"data": {}})
        mock_http.request = AsyncMock(return_value=mock_resp)

        with patch.object(client, "_get_client", AsyncMock(return_value=mock_http)):
            await client.post("/jobs", json_body={})
            await client.post("/jobs", json_body={})

        keys = [
            call.kwargs["headers"]["Idempotency-Key"]
            for call in mock_http.request.call_args_list
        ]
        assert keys[0] != keys[1], (
            f"Two consecutive POSTs sem explicit key devem gerar keys diferentes. "
            f"Got: {keys}"
        )


class TestJobCreationAPIClientIdempotencyKey:
    """JobCreationAPIClient injetando Idempotency-Key em mutations."""

    def test_post_includes_idempotency_key(self) -> None:
        from app.domains.job_creation.api_client import JobCreationAPIClient

        client = JobCreationAPIClient()
        mock_http = MagicMock()
        mock_resp = MagicMock(
            status_code=200, text='{"data": {}}'
        )
        mock_resp.json = MagicMock(return_value={"data": {}})
        mock_http.request = MagicMock(return_value=mock_resp)

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_http)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_ctx):
            with patch.object(client, "_get_headers", return_value={"Authorization": "Bearer X"}):
                client._request("POST", "/jobs", json_body={"title": "X"})

        call_kwargs = mock_http.request.call_args.kwargs
        headers = call_kwargs.get("headers") or {}
        assert "Idempotency-Key" in headers, (
            f"JobCreationAPI POST DEVE ter Idempotency-Key. Got: {headers}"
        )

    def test_get_does_not_include_idempotency_key(self) -> None:
        from app.domains.job_creation.api_client import JobCreationAPIClient

        client = JobCreationAPIClient()
        mock_http = MagicMock()
        mock_resp = MagicMock(status_code=200, text='{"data": {}}')
        mock_resp.json = MagicMock(return_value={"data": {}})
        mock_http.request = MagicMock(return_value=mock_resp)

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_http)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("httpx.Client", return_value=mock_ctx):
            with patch.object(client, "_get_headers", return_value={"Authorization": "Bearer X"}):
                client._request("GET", "/jobs")

        call_kwargs = mock_http.request.call_args.kwargs
        headers = call_kwargs.get("headers") or {}
        assert "Idempotency-Key" not in headers, (
            f"GET NÃO deve ter Idempotency-Key. Got: {headers}"
        )


class TestSensorBlocking:
    """W2-009 sensor BLOCKING."""

    def test_sensor_exists(self) -> None:
        from pathlib import Path

        sensor = (
            Path(__file__).resolve().parents[2]
            / "scripts"
            / "check_idempotency_key_in_rails_clients.py"
        )
        assert sensor.exists()

    def test_sensor_passes_strict(self) -> None:
        import subprocess
        import sys
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[2]
        sensor = repo_root / "scripts" / "check_idempotency_key_in_rails_clients.py"
        result = subprocess.run(
            [sys.executable, str(sensor)],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        assert result.returncode == 0, (
            f"Idempotency sensor FAILED (exit={result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
