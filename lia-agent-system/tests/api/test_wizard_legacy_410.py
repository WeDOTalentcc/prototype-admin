"""Task #857 — legacy wizard entrypoints return HTTP 410 Gone.

Covers ``GraphRunnerService.stream_job_wizard`` (N-01) and
``WizardOrchestratorService.get_wizard_step`` (N-02): both must raise
``HTTPException(410)`` with the canonical migration payload and emit a
structured INFO log carrying ``tenant.company_id``, ``caller`` and
``path``.
"""
from __future__ import annotations

import asyncio
import logging

import pytest
from fastapi import HTTPException

from app.domains.ai.services.graph_runner import GraphRunnerService
from app.domains.job_management.services.wizard_orchestrator_service import (
    get_wizard_step,
)


CANONICAL_DETAIL = {
    "error": (
        "Endpoint deprecated. Use WS /ws/agent-chat with "
        "domain=job_creation."
    ),
}


class TestStreamJobWizard410:
    def test_returns_410_with_canonical_detail(self) -> None:
        service = GraphRunnerService()
        assert service.graph is None

        agen = service.stream_job_wizard(
            session_id="session-abc",
            user_message="hello",
            company_id="company-uuid-1",
            user_id="user-uuid-1",
        )
        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(agen.__anext__())

        assert excinfo.value.status_code == 410
        assert excinfo.value.detail == CANONICAL_DETAIL

    def test_does_not_raise_notimplementederror(self) -> None:
        service = GraphRunnerService()
        agen = service.stream_job_wizard(
            session_id="s",
            user_message="m",
            company_id="c",
            user_id="u",
        )
        with pytest.raises(HTTPException):
            asyncio.run(agen.__anext__())

    def test_emits_structured_deprecation_log_with_company_id(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        service = GraphRunnerService()
        service.logger.propagate = True
        service.logger.setLevel(logging.INFO)
        caplog.set_level(logging.INFO)

        agen = service.stream_job_wizard(
            session_id="session-abc",
            user_message="hello",
            company_id="company-uuid-7",
            user_id="user-uuid-1",
        )
        with pytest.raises(HTTPException):
            asyncio.run(agen.__anext__())

        records = [
            r for r in caplog.records
            if r.message == "wizard.legacy.deprecated_call"
        ]
        assert records, "expected structured deprecation log"
        rec = records[-1]
        assert getattr(rec, "tenant.company_id") == "company-uuid-7"
        assert rec.caller == "GraphRunnerService.stream_job_wizard"
        assert "graph_runner" in rec.path


class TestGetWizardStep410:
    def test_returns_410_with_canonical_detail(self) -> None:
        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(get_wizard_step(session_id="s"))

        assert excinfo.value.status_code == 410
        assert excinfo.value.detail == CANONICAL_DETAIL

    def test_does_not_raise_notimplementederror(self) -> None:
        with pytest.raises(HTTPException):
            asyncio.run(get_wizard_step(session_id="s"))

    def test_emits_structured_deprecation_log_with_company_id(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO)

        with pytest.raises(HTTPException):
            asyncio.run(
                get_wizard_step(session_id="s", _company_id="company-uuid-9")
            )

        records = [
            r for r in caplog.records
            if r.message == "wizard.legacy.deprecated_call"
        ]
        assert records, "expected structured deprecation log"
        rec = records[-1]
        assert getattr(rec, "tenant.company_id") == "company-uuid-9"
        assert rec.caller == "WizardOrchestratorService.get_wizard_step"
        assert "wizard_orchestrator_service" in rec.path
