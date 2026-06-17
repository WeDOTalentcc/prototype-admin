"""Task #857 + #872 — legacy wizard entrypoints return HTTP 410 Gone.

Covers:

* **N-01** ``GraphRunnerService.stream_job_wizard``
* **N-02** ``WizardOrchestratorService.get_wizard_step``
* **N-03** (Revisão 4 reabertura) the 5 REST endpoints in
  ``app.api.v1.lia_assistant.wizard``:
  - ``POST /api/v1/lia/job-wizard/interpret``
  - ``POST /api/v1/lia/job-wizard/orchestrate``
  - ``POST /api/v1/lia/job-wizard/salary-benchmark``
  - ``POST /api/v1/lia/job-wizard/evaluate``
  - ``POST /api/v1/lia/job-wizard/step``

All five must respond with HTTP 410, the canonical migration payload, and
emit a structured INFO log carrying ``tenant.company_id``, ``caller`` and
``path``.
"""
from __future__ import annotations

import asyncio
import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.v1.lia_assistant.wizard import router as legacy_wizard_router
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


@pytest.fixture
def legacy_wizard_client() -> TestClient:
    """A minimal FastAPI app mounting only the legacy wizard router.

    Mirrors the production prefix ``/api/v1/lia`` so the asserted URLs
    match the public contract tracked in the audit doc.
    """
    app = FastAPI()
    app.include_router(legacy_wizard_router, prefix="/api/v1/lia")
    return TestClient(app, raise_server_exceptions=False)


LEGACY_WIZARD_PATHS = [
    ("/api/v1/lia/job-wizard/interpret", "interpret_user_message"),
    ("/api/v1/lia/job-wizard/orchestrate", "orchestrate_wizard_message"),
    ("/api/v1/lia/job-wizard/salary-benchmark", "get_salary_benchmark"),
    ("/api/v1/lia/job-wizard/evaluate", "evaluate_wizard_input"),
    ("/api/v1/lia/job-wizard/step", "process_wizard_step"),
]


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


class TestLegacyWizardRestEndpoints410:
    """Task #872 — N-03 reabertura.

    The 5 REST endpoints in ``lia_assistant.wizard`` previously processed
    job creation requests bypassing PolicyGate / FairnessGuard / per-turn
    audit log. They must now answer 410 with the canonical migration
    payload. No request body validation, no DB access, no LLM call.
    """

    @pytest.mark.parametrize("path,endpoint_name", LEGACY_WIZARD_PATHS)
    def test_returns_410_with_canonical_detail(
        self,
        legacy_wizard_client: TestClient,
        path: str,
        endpoint_name: str,
    ) -> None:
        response = legacy_wizard_client.post(path, json={"any": "payload"})
        assert response.status_code == 410, (
            f"{path} expected 410 Gone, got {response.status_code}: "
            f"{response.text}"
        )
        assert response.json() == {"detail": CANONICAL_DETAIL}

    @pytest.mark.parametrize("path,endpoint_name", LEGACY_WIZARD_PATHS)
    def test_returns_410_even_with_empty_body(
        self,
        legacy_wizard_client: TestClient,
        path: str,
        endpoint_name: str,
    ) -> None:
        # No body, no headers, no auth — the deprecated path must still
        # respond 410 (NOT 401/422) so external callers never confuse a
        # validation error with a real outage.
        response = legacy_wizard_client.post(path)
        assert response.status_code == 410

    @pytest.mark.parametrize("path,endpoint_name", LEGACY_WIZARD_PATHS)
    def test_emits_structured_deprecation_log_with_company_id(
        self,
        legacy_wizard_client: TestClient,
        caplog: pytest.LogCaptureFixture,
        path: str,
        endpoint_name: str,
    ) -> None:
        caplog.set_level(
            logging.INFO,
            logger="app.api.v1.lia_assistant.wizard",
        )
        response = legacy_wizard_client.post(
            path,
            json={"hello": "world"},
            headers={
                "X-Company-ID": "company-uuid-42",
                "X-Session-ID": "session-uuid-99",
            },
        )
        assert response.status_code == 410

        records = [
            r for r in caplog.records
            if r.message == "wizard.legacy.deprecated_call"
        ]
        assert records, f"expected deprecation log for {path}"
        rec = records[-1]
        assert getattr(rec, "tenant.company_id") == "company-uuid-42"
        assert rec.caller == f"lia_assistant.wizard.{endpoint_name}"
        assert rec.path == path
        assert rec.session_id == "session-uuid-99"

    def test_get_method_returns_405_not_410(
        self, legacy_wizard_client: TestClient
    ) -> None:
        # Routes are mounted only for POST. Sanity check that we did
        # not accidentally widen the surface area while deprecating.
        response = legacy_wizard_client.get(
            "/api/v1/lia/job-wizard/interpret"
        )
        assert response.status_code == 405

    def test_company_id_header_absent_logs_none(
        self,
        legacy_wizard_client: TestClient,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(
            logging.INFO,
            logger="app.api.v1.lia_assistant.wizard",
        )
        response = legacy_wizard_client.post(
            "/api/v1/lia/job-wizard/step", json={}
        )
        assert response.status_code == 410

        records = [
            r for r in caplog.records
            if r.message == "wizard.legacy.deprecated_call"
        ]
        assert records
        assert getattr(records[-1], "tenant.company_id") is None
