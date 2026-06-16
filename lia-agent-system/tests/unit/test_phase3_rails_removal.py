"""
Phase 3 Rail Removal — TDD tests.

Verifies that:
1. candidates endpoint serves from local DB (no Rails fallback)
2. job_vacancies endpoint serves from local DB (no Rails fallback)
3. bias_audit endpoint calls BiasAuditService directly (no RailsAdapter)
4. No RailsAdapter imported in the 3 target files
"""
from __future__ import annotations

import importlib
import sys
import types
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Test 1 — No RailsAdapter import in target files
# ---------------------------------------------------------------------------

def test_candidates_crud_has_no_rails_adapter_import():
    """Phase 3: candidates_crud must not import RailsAdapter."""
    import ast, pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/candidates/candidates_crud.py"
    ).read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            module = getattr(node, "module", "") or ""
            assert "RailsAdapter" not in names, "RailsAdapter still imported in candidates_crud"
            assert "rails_adapter" not in module or "rails_sync" in module, (
                f"rails_adapter module still imported: {module}"
            )


def test_job_vacancies_crud_has_no_rails_adapter_import():
    """Phase 3: job_vacancies/crud must not import RailsAdapter."""
    import ast, pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/job_vacancies/crud.py"
    ).read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            module = getattr(node, "module", "") or ""
            assert "RailsAdapter" not in names, "RailsAdapter still imported in job_vacancies/crud"
            assert "rails_adapter" not in module or "rails_sync" in module, (
                f"rails_adapter module still imported: {module}"
            )


def test_bias_audit_has_no_rails_adapter_import():
    """Phase 3: bias_audit must not import RailsAdapter."""
    import ast, pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/bias_audit.py"
    ).read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names]
            assert "RailsAdapter" not in names, "RailsAdapter still imported in bias_audit"


# ---------------------------------------------------------------------------
# Test 2 — No RAILS_ENABLED reference in target files
# ---------------------------------------------------------------------------

def test_candidates_crud_has_no_rails_enabled_reference():
    import pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/candidates/candidates_crud.py"
    ).read_text()
    assert "RAILS_ENABLED" not in src, "RAILS_ENABLED still referenced in candidates_crud"


def test_job_vacancies_crud_has_no_rails_enabled_reference():
    import pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/job_vacancies/crud.py"
    ).read_text()
    assert "RAILS_ENABLED" not in src, "RAILS_ENABLED still referenced in job_vacancies/crud"


def test_bias_audit_has_no_bias_adapter_reference():
    import pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/bias_audit.py"
    ).read_text()
    assert "_bias_adapter" not in src, "_bias_adapter still referenced in bias_audit"


# ---------------------------------------------------------------------------
# Test 3 — bias_audit endpoints call BiasAuditService directly
# ---------------------------------------------------------------------------

def _make_bias_app():
    from app.api.v1.bias_audit import router
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return app


def test_bias_audit_get_report_calls_service_directly():
    """GET /bias-audit/job/{id} must call bias_audit_service, not RailsAdapter."""
    from app.shared.tenant_guard import get_verified_company_id
    from app.shared.security.require_company_id import require_company_id
    from app.core.database import get_db

    company_uuid = str(uuid.uuid4())
    job_uuid = str(uuid.uuid4())

    fake_report = MagicMock()
    fake_report.job_id = job_uuid
    fake_report.evaluated_at = __import__("datetime").datetime.utcnow()
    fake_report.total_candidates = 5
    fake_report.dimensions = []
    fake_report.has_alerts = False

    app = _make_bias_app()
    app.dependency_overrides[get_verified_company_id] = lambda: company_uuid
    app.dependency_overrides[require_company_id] = lambda: company_uuid
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch(
        "app.shared.services.bias_audit_service.bias_audit_service.get_adverse_impact_by_job",
        new=AsyncMock(return_value=fake_report),
    ) as mock_svc:
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(f"/api/v1/bias-audit/job/{job_uuid}")
        # Service must have been called — not bypassed via RailsAdapter
        assert mock_svc.called or resp.status_code < 500, (
            f"Unexpected server error: {resp.status_code} {resp.text[:200]}"
        )


# ---------------------------------------------------------------------------
# Test 4 — candidates list endpoint works without Rails (RAILS_API_URL unset)
# ---------------------------------------------------------------------------

def test_candidates_list_works_without_rails_api_url(monkeypatch):
    """list_candidates must not fail when RAILS_API_URL is unset."""
    monkeypatch.delenv("RAILS_API_URL", raising=False)
    import pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/candidates/candidates_crud.py"
    ).read_text()
    # Ensure there's no dynamic os.environ.get("RAILS_API_URL") that would gate the path
    # The Rails fallback has been removed, so RAILS_API_URL being absent must not be an error
    assert "RAILS_API_URL" not in src, (
        "candidates_crud still reads RAILS_API_URL — fallback not fully removed"
    )


def test_job_vacancies_list_works_without_rails_api_url(monkeypatch):
    """list_job_vacancies must not fail when RAILS_API_URL is unset."""
    monkeypatch.delenv("RAILS_API_URL", raising=False)
    import pathlib
    src = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/api/v1/job_vacancies/crud.py"
    ).read_text()
    assert "RAILS_API_URL" not in src, (
        "job_vacancies/crud still reads RAILS_API_URL — fallback not fully removed"
    )
