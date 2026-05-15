"""Task #1098 — integration coverage for GET /api/v1/company/culture-profile/{id}.

The wizard's culture step was failing with ResponseValidationError for tenants
whose company_culture_profiles row was written before the model's Python-side
defaults existed (or via raw SQL). The SQLAlchemy model declares the array /
Big-Five-score columns with default=[]/default=50 only — no server_default,
no NOT NULL — so legacy rows can carry NULL where Pydantic's list[str]/int
fields then refuse to validate.

These tests exercise the full FastAPI path (response_model serialization with
from_attributes=True) using a stub repo that returns either a fully-NULL ORM
row or a populated one, asserting the endpoint stays HTTP 200 and surfaces
the documented defaults ([] and 50) for the legacy rows.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import (
    get_current_active_user,
    get_current_user,
    get_current_user_or_demo,
    get_current_user_strict,
)
from app.auth.security import create_access_token
from app.core.database import get_db
from app.domains.company_culture.dependencies import get_company_culture_repo
from app.main import app


COMPANY_ID = "11111111-1111-1111-1111-111111111111"


def _user():
    u = MagicMock()
    u.id = "user-1"
    u.company_id = COMPANY_ID
    u.role = "admin"
    u.is_active = True
    u.email = "admin@company.com"
    return u


def _user_dep():
    return _user()


def _db_dep():
    yield MagicMock()


def _make_legacy_orm_row():
    """ORM-shaped object with NULLs for every nullable-but-defaulted column."""
    row = MagicMock(spec=[
        "id", "company_id", "website_url", "linkedin_url",
        "mission", "vision", "culture_description",
        "values", "evp_bullets", "core_competencies", "analyzed_pages",
        "locations", "tech_stack", "default_languages",
        "openness_score", "conscientiousness_score", "extraversion_score",
        "agreeableness_score", "stability_score",
        "industry", "employee_count", "company_size", "headquarters",
        "founded_year", "work_model", "growth_opportunities",
        "team_dynamics", "leadership_style", "dei_initiatives",
        "sustainability", "social_impact", "engineering_culture",
        "source", "confidence_score",
        "last_analysis_at", "created_at", "updated_at",
    ])
    row.id = uuid.uuid4()
    row.company_id = uuid.UUID(COMPANY_ID)
    row.website_url = "https://legacy.example.com"
    row.linkedin_url = None
    row.mission = None
    row.vision = None
    row.culture_description = None
    # The fields that previously broke validation
    row.values = None
    row.evp_bullets = None
    row.core_competencies = None
    row.analyzed_pages = None
    row.locations = None
    row.tech_stack = None
    row.default_languages = None
    row.openness_score = None
    row.conscientiousness_score = None
    row.extraversion_score = None
    row.agreeableness_score = None
    row.stability_score = None
    # Other optional fields
    row.industry = None
    row.employee_count = None
    row.company_size = None
    row.headquarters = None
    row.founded_year = None
    row.work_model = None
    row.growth_opportunities = None
    row.team_dynamics = None
    row.leadership_style = None
    row.dei_initiatives = None
    row.sustainability = None
    row.social_impact = None
    row.engineering_culture = None
    # Required server-side fields
    row.source = "auto"
    row.confidence_score = 0.5
    row.last_analysis_at = datetime(2024, 1, 1, 12, 0, 0)
    row.created_at = datetime(2024, 1, 1, 12, 0, 0)
    row.updated_at = datetime(2024, 1, 1, 12, 0, 0)
    return row


def _make_populated_orm_row():
    row = _make_legacy_orm_row()
    row.values = ["transparency", "ownership"]
    row.evp_bullets = ["Remote-first"]
    row.core_competencies = ["communication"]
    row.tech_stack = ["python", "react"]
    row.openness_score = 73
    row.conscientiousness_score = 68
    row.mission = "Empower talent"
    return row


def _legacy_repo_dep():
    repo = MagicMock()
    repo.get_profile_by_company = AsyncMock(return_value=_make_legacy_orm_row())
    return repo


def _populated_repo_dep():
    repo = MagicMock()
    repo.get_profile_by_company = AsyncMock(return_value=_make_populated_orm_row())
    return repo


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _db_dep
    app.dependency_overrides[get_current_user] = _user_dep
    app.dependency_overrides[get_current_active_user] = _user_dep
    app.dependency_overrides[get_current_user_or_demo] = _user_dep
    app.dependency_overrides[get_current_user_strict] = _user_dep
    token = create_access_token(
        subject="user-1",
        role="admin",
        company_id=COMPANY_ID,
    )
    with patch("app.main.init_db", AsyncMock()):
        with TestClient(app, raise_server_exceptions=False) as c:
            c.headers.update({"Authorization": f"Bearer {token}"})
            yield c
    app.dependency_overrides.clear()


def test_get_culture_profile_legacy_nulls_serialize_with_defaults(client):
    """Tenant with NULL array/score columns: HTTP 200 + coerced defaults."""
    app.dependency_overrides[get_company_culture_repo] = _legacy_repo_dep

    resp = client.get(f"/api/v1/company/culture-profile/{COMPANY_ID}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["website_url"] == "https://legacy.example.com"
    # Arrays coerced from NULL → []
    assert body["values"] == []
    assert body["evp_bullets"] == []
    assert body["core_competencies"] == []
    assert body["analyzed_pages"] == []
    assert body["locations"] == []
    assert body["tech_stack"] == []
    assert body["default_languages"] == []
    # Big-Five scores coerced from NULL → 50
    assert body["openness_score"] == 50
    assert body["conscientiousness_score"] == 50
    assert body["extraversion_score"] == 50
    assert body["agreeableness_score"] == 50
    assert body["stability_score"] == 50


def test_get_culture_profile_populated_row_passes_through(client):
    """Tenant with real cultural data: populated values are not clobbered."""
    app.dependency_overrides[get_company_culture_repo] = _populated_repo_dep

    resp = client.get(f"/api/v1/company/culture-profile/{COMPANY_ID}")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["values"] == ["transparency", "ownership"]
    assert body["evp_bullets"] == ["Remote-first"]
    assert body["tech_stack"] == ["python", "react"]
    assert body["openness_score"] == 73
    assert body["conscientiousness_score"] == 68
    assert body["mission"] == "Empower talent"
    # Fields still NULL on this row are still coerced
    assert body["analyzed_pages"] == []
    assert body["stability_score"] == 50
