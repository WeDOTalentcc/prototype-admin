"""Behavior tests for the 4 culture endpoints relocated in T2/#994.

The sentinel in ``test_company_culture_relocation_t2_994.py`` only proves
the routes are mounted on ``app.api.v1.company_culture``; it does NOT
exercise their behavior. This module covers the happy paths (with the
external services — Apify, LLM, httpx — mocked) and the LLM JSON-parse
fallback paths in ``analyze-culture`` and ``generate-evp``.

Endpoints under test (mounted on ``legacy_router`` with prefix ``/company``):
- POST /api/v1/company/enrich
- POST /api/v1/company/auto-enrich/{profile_id}
- POST /api/v1/company/profile/{profile_id}/generate-evp
- POST /api/v1/company/analyze-culture
"""
from __future__ import annotations

import uuid
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
from app.domains.company.dependencies import (
    get_company_profile_repo,
    get_culture_profile_repo,
)
from app.main import app


PROFILE_ID = uuid.uuid4()
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


def _make_profile():
    p = MagicMock()
    p.id = PROFILE_ID
    p.name = "Acme Corp"
    p.industry = "Technology"
    p.description = "We build platforms."
    p.company_size = "51-200"
    p.linkedin_url = "https://linkedin.com/company/acme"
    p.headquarters_city = None
    p.founded_year = None
    p.employee_count = None
    p.additional_data = {}
    return p


def _profile_repo_dep():
    repo = MagicMock()
    repo.get_by_id = AsyncMock(return_value=_make_profile())
    repo.update = AsyncMock(return_value=None)
    return repo


def _culture_repo_dep():
    repo = MagicMock()
    cp = MagicMock()
    cp.id = uuid.uuid4()
    cp.culture_description = None
    cp.core_competencies = []
    cp.mission = "Empower talent"
    cp.vision = "Better hiring for everyone"
    cp.values = ["trust", "ownership"]
    repo.get_for_company = AsyncMock(return_value=cp)
    repo.update = AsyncMock(return_value=None)
    return repo


@pytest.fixture(scope="module")
def client():
    app.dependency_overrides[get_db] = _db_dep
    app.dependency_overrides[get_current_user] = _user_dep
    app.dependency_overrides[get_current_active_user] = _user_dep
    app.dependency_overrides[get_current_user_or_demo] = _user_dep
    app.dependency_overrides[get_current_user_strict] = _user_dep
    app.dependency_overrides[get_company_profile_repo] = _profile_repo_dep
    app.dependency_overrides[get_culture_profile_repo] = _culture_repo_dep
    # AuthEnforcementMiddleware runs before dependency_overrides take effect,
    # so we need a real signed JWT in the Authorization header. The middleware
    # only cares that the token decodes; the user behind the request is
    # supplied by the dependency overrides above.
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


# ───────────────────────────── /enrich ─────────────────────────────

def test_enrich_happy_path_combines_linkedin_and_glassdoor(client):
    """Both Apify scrapers return data; response merges into enriched_culture."""
    linkedin_payload = {
        "description": "An innovative tech company.",
        "tagline": "Build the future.",
        "specialties": ["AI", "Recruiting"],
    }
    glassdoor_payload = {
        "mission": "Hire better.",
        "overview": "Vision text.",
        "employee_pros": ["good benefits"],
        "culture_rating": "4.5",
        "overall_rating": "4.3",
        "work_life_balance": "4.0",
    }
    with (
        patch(
            "app.api.v1.company_culture.apify_service.scrape_linkedin_company",
            new=AsyncMock(return_value=linkedin_payload),
        ),
        patch(
            "app.api.v1.company_culture.apify_service.scrape_glassdoor_company",
            new=AsyncMock(return_value=glassdoor_payload),
        ),
    ):
        resp = client.post(
            "/api/v1/company/enrich",
            json={
                "linkedin_url": "https://linkedin.com/company/acme",
                "glassdoor_company_name": "Acme",
            },
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["linkedin_data"] == linkedin_payload
    assert body["glassdoor_data"] == glassdoor_payload
    enriched = body["enriched_culture"]
    assert enriched["company_description"] == linkedin_payload["description"]
    assert enriched["tagline"] == linkedin_payload["tagline"]
    assert enriched["specialties"] == linkedin_payload["specialties"]
    assert enriched["mission"] == glassdoor_payload["mission"]
    assert enriched["vision"] == glassdoor_payload["overview"]
    assert enriched["culture_highlights"] == glassdoor_payload["employee_pros"]
    assert enriched["culture_rating"] == "4.5"
    assert body["errors"] == []


# ───────────────────── /auto-enrich/{profile_id} ─────────────────────

def test_auto_enrich_happy_path_persists_inferred_fields(client):
    """LinkedIn + Glassdoor + LLM inference all succeed; profile.update is called."""
    profile = _make_profile()
    profile_repo = MagicMock()
    profile_repo.get_by_id = AsyncMock(return_value=profile)
    profile_repo.update = AsyncMock(return_value=None)

    cp = MagicMock()
    cp.culture_description = None
    cp.core_competencies = []
    cp.mission = "Empower talent"
    cp.vision = "Better hiring for everyone"
    cp.values = ["trust"]
    cp_repo = MagicMock()
    cp_repo.get_for_company = AsyncMock(return_value=cp)
    cp_repo.update = AsyncMock(return_value=None)

    app.dependency_overrides[get_company_profile_repo] = lambda: profile_repo
    app.dependency_overrides[get_culture_profile_repo] = lambda: cp_repo

    linkedin_payload = {
        "headquarters": {"city": "São Paulo", "state": "SP", "country": "Brasil"},
        "founded": "2015",
        "company_size": "51-200",
        "description": "An innovative tech company.",
    }
    inferred_json = (
        "```json\n"
        "{"
        '"work_model": "híbrido",'
        '"growth_opportunities": "Trilha clara",'
        '"team_dynamics": "Colaborativo",'
        '"leadership_style": "Servidor",'
        '"core_competencies": ["aprendizado", "ownership", "comunicação"],'
        '"diversity_initiatives": "Programa DEI",'
        '"sustainability": "Não especificado",'
        '"social_impact": "Bolsas",'
        '"engineering_culture": "TDD"'
        "}\n```"
    )
    try:
        with (
            patch(
                "app.api.v1.company_culture.apify_service.scrape_linkedin_company",
                new=AsyncMock(return_value=linkedin_payload),
            ),
            patch(
                "app.api.v1.company_culture.apify_service.scrape_glassdoor_company",
                new=AsyncMock(return_value={"employee_pros": ["bom clima"]}),
            ),
            patch(
                "app.api.v1.company_culture.llm_service.generate",
                new=AsyncMock(return_value=inferred_json),
            ),
        ):
            resp = client.post(f"/api/v1/company/auto-enrich/{profile.id}")
    finally:
        app.dependency_overrides[get_company_profile_repo] = _profile_repo_dep
        app.dependency_overrides[get_culture_profile_repo] = _culture_repo_dep

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert "headquarters" in body["fields_updated"]
    assert "founded_year" in body["fields_updated"]
    assert "employee_count" in body["fields_updated"]
    assert "work_model" in body["fields_updated"]
    assert "core_competencies" in body["fields_updated"]
    assert body["inferred_data"]["work_model"] == "híbrido"
    assert body["apify_data"]["linkedin"] == linkedin_payload
    profile_repo.update.assert_awaited()


def test_auto_enrich_returns_404_when_profile_missing(client):
    profile_repo = MagicMock()
    profile_repo.get_by_id = AsyncMock(return_value=None)
    app.dependency_overrides[get_company_profile_repo] = lambda: profile_repo
    try:
        resp = client.post(f"/api/v1/company/auto-enrich/{uuid.uuid4()}")
    finally:
        app.dependency_overrides[get_company_profile_repo] = _profile_repo_dep
    assert resp.status_code == 404


# ───────────────── /profile/{profile_id}/generate-evp ─────────────────

def test_generate_evp_happy_path_persists_analysis(client):
    """Strips ```json fences, parses, and writes evp_analysis to additional_data."""
    profile = _make_profile()
    profile.additional_data = {
        "tagline": "Build the future.",
        "mission": "Hire better.",
        "specialties": ["AI"],
        "culture_highlights": ["good benefits"],
    }
    profile_repo = MagicMock()
    profile_repo.get_by_id = AsyncMock(return_value=profile)
    profile_repo.update = AsyncMock(return_value=None)
    app.dependency_overrides[get_company_profile_repo] = lambda: profile_repo

    evp_json = (
        "```json\n"
        "{"
        '"statement": "Empower talent.",'
        '"pillars": [{"name": "Crescimento", "description": "Trilha", "evidence": "Mentoria"}],'
        '"tone_guidance": ["claro", "humano", "direto", "empático", "ágil"],'
        '"candidate_promise": "Você vai crescer aqui."'
        "}\n```"
    )
    try:
        with patch(
            "app.api.v1.company_culture.llm_service.generate",
            new=AsyncMock(return_value=evp_json),
        ):
            resp = client.post(f"/api/v1/company/profile/{profile.id}/generate-evp")
    finally:
        app.dependency_overrides[get_company_profile_repo] = _profile_repo_dep

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    evp = body["evp_analysis"]
    assert evp["statement"] == "Empower talent."
    assert evp["pillars"][0]["name"] == "Crescimento"
    assert evp["candidate_promise"] == "Você vai crescer aqui."
    profile_repo.update.assert_awaited()
    update_kwargs = profile_repo.update.await_args
    saved_additional = update_kwargs.args[1]["additional_data"]
    assert "evp_analysis" in saved_additional


def test_generate_evp_returns_failure_envelope_on_invalid_json(client):
    """LLM JSON-parse fallback path: malformed JSON returns success=False with error."""
    profile = _make_profile()
    profile_repo = MagicMock()
    profile_repo.get_by_id = AsyncMock(return_value=profile)
    profile_repo.update = AsyncMock(return_value=None)
    app.dependency_overrides[get_company_profile_repo] = lambda: profile_repo
    try:
        with patch(
            "app.api.v1.company_culture.llm_service.generate",
            new=AsyncMock(return_value="this is not json at all"),
        ):
            resp = client.post(f"/api/v1/company/profile/{profile.id}/generate-evp")
    finally:
        app.dependency_overrides[get_company_profile_repo] = _profile_repo_dep

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is False
    assert body["evp_analysis"] is None
    assert body["error"] and "Falha ao processar" in body["error"]
    profile_repo.update.assert_not_awaited()


def test_generate_evp_returns_404_when_profile_missing(client):
    profile_repo = MagicMock()
    profile_repo.get_by_id = AsyncMock(return_value=None)
    app.dependency_overrides[get_company_profile_repo] = lambda: profile_repo
    try:
        resp = client.post(f"/api/v1/company/profile/{uuid.uuid4()}/generate-evp")
    finally:
        app.dependency_overrides[get_company_profile_repo] = _profile_repo_dep
    assert resp.status_code == 404


# ─────────────────────── /analyze-culture ───────────────────────

def _make_audited_model(response_text: str):
    """Builds a fake audited LLM model whose ``ainvoke`` returns ``response_text``."""
    model = MagicMock()
    response = MagicMock()
    response.content = response_text
    model.ainvoke = AsyncMock(return_value=response)
    return model


def test_analyze_culture_happy_path_with_fenced_json(client):
    """LLM returns JSON inside ```json fences; values normalized into response."""
    payload = (
        "```json\n"
        "{"
        '"vision": "Visão clara",'
        '"mission": "Missão clara",'
        '"values": ["inovação", {"name": "colaboração"}, ""],'
        '"tone": "professional",'
        '"evp": "Crescimento contínuo",'
        '"culture_summary": "Cultura forte.",'
        '"suggested_values": ['
        '{"name": "ownership", "description": "dono do processo", "category": "value"},'
        '"transparência"'
        "],"
        '"confidence": 0.85'
        "}\n```"
    )
    fake_model = _make_audited_model(payload)
    with patch(
        "app.api.v1.company_culture.llm_service.get_audited_model",
        return_value=fake_model,
    ):
        # website_url=None → skips httpx fetch entirely
        resp = client.post(
            "/api/v1/company/analyze-culture",
            json={"additional_context": "Empresa de tecnologia."},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["analysis"]["vision"] == "Visão clara"
    assert body["analysis"]["mission"] == "Missão clara"
    # dict values normalized to strings; empty entries dropped
    assert body["analysis"]["values"] == ["inovação", "colaboração"]
    assert body["confidence"] == 0.85
    # No website_url given → no source analyzed
    assert body["sources_analyzed"] == []
    # suggested_values: dict + bare string both supported
    names = [sv["name"] for sv in body["suggested_values"]]
    assert "ownership" in names
    assert "transparência" in names


def test_analyze_culture_uses_regex_fallback_when_fenced_block_invalid(client):
    """LLM JSON-parse fallback: first parse fails, regex {...} extraction succeeds."""
    payload = (
        "Aqui vai a análise: garbage prefix "
        '{"vision": "v", "mission": "m", "values": ["x"], "tone": "informal", '
        '"evp": "e", "culture_summary": "s", "suggested_values": [], '
        '"confidence": 0.4} trailing words'
    )
    fake_model = _make_audited_model(payload)
    with patch(
        "app.api.v1.company_culture.llm_service.get_audited_model",
        return_value=fake_model,
    ):
        resp = client.post(
            "/api/v1/company/analyze-culture",
            json={"additional_context": "ctx"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["analysis"]["vision"] == "v"
    assert body["analysis"]["tone"] == "informal"
    assert body["confidence"] == 0.4


def test_analyze_culture_uses_default_envelope_when_all_parses_fail(client):
    """LLM JSON-parse fallback: both parse paths fail → safe default analysis envelope."""
    fake_model = _make_audited_model("totalmente sem json aqui, só prosa solta")
    with patch(
        "app.api.v1.company_culture.llm_service.get_audited_model",
        return_value=fake_model,
    ):
        resp = client.post(
            "/api/v1/company/analyze-culture",
            json={"additional_context": "ctx"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["analysis"]["vision"] == ""
    assert body["analysis"]["mission"] == ""
    assert body["analysis"]["values"] == []
    assert body["analysis"]["tone"] == "professional"
    assert "Não foi possível analisar" in body["analysis"]["culture_summary"]
    assert body["confidence"] == 0.2
