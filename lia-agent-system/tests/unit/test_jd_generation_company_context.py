"""Unit test: generate_jd injects build_company_agent_context into job_data.

Red before the wiring (no MARKER_EMPRESA in company_culture), green after.
Calls the endpoint coroutine directly with mocked dependencies so no HTTP
client / Postgres is required.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

import app.api.v1.jd_generation as jd_mod
from app.api.v1.jd_generation import GenerateJDRequest, generate_jd


@pytest.mark.asyncio
async def test_generate_jd_injects_company_context_into_job_data():
    request = GenerateJDRequest(job_title="Engenheiro de Dados", department="Tech")

    captured = {}

    async def _fake_generate_full_description(*, job_data, company_id):
        captured["job_data"] = job_data
        captured["company_id"] = company_id
        return {"description": "ok"}

    with patch(
        "app.shared.services.lia_agent_context_builder.build_company_agent_context",
        new=AsyncMock(return_value="MARKER_EMPRESA: missao filtrada"),
    ), patch.object(
        jd_mod.jd_generator_service,
        "generate_full_description",
        new=AsyncMock(side_effect=_fake_generate_full_description),
    ), patch.object(
        jd_mod, "_fg_check_input", return_value=None
    ), patch(
        "app.api.v1.jd_generation.AsyncSessionLocal"
    ) as mock_session_local:
        # async context manager returning a dummy session
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=object())
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)

        audit_svc = AsyncMock()
        await generate_jd(
            request=request,
            current_user=object(),
            audit_svc=audit_svc,
            company_id="co-123",
        )

    job_data = captured.get("job_data")
    assert job_data is not None, "service was not called"
    culture = job_data.get("company_culture") or ""
    assert "MARKER_EMPRESA" in culture, (
        f"company context not injected; company_culture={culture!r}"
    )
