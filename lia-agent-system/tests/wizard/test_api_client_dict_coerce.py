"""Sprint L sensor — pin bulletproof dict-coerce in api_client._create_job_local.

Pattern: construct create_job() input with dict-leaked scalars (titulo_padronizado
as {"text": "..."}, location as {"city": "SP"}, etc.) and assert:
1. No exception bubbles up
2. APIResponse.success == True (dev-local INSERT path succeeds)
3. job_vacancies row created with title coerced to str

Anchored to dev-local fallback (LIA_DEV_LOCAL_PUBLISH=1, RAILS_API_URL="").
Production with Rails URL set hits httpx path and is unaffected.

Sensor type: COMPUTATIONAL (test) - catches regression in dict coerce.
"""
import os
import uuid

import psycopg2
import pytest

from app.domains.job_creation.api_client import JobCreationAPIClient


@pytest.fixture
def dev_local_env(monkeypatch):
    """Force dev-local path: empty RAILS_API_URL + flag set."""
    monkeypatch.setenv("LIA_DEV_LOCAL_PUBLISH", "1")
    monkeypatch.setenv("RAILS_API_URL", "")
    monkeypatch.setenv("RAILS_BACKEND_URL", "")
    yield


@pytest.fixture
def db_cleanup():
    """Track created row ids and clean up after."""
    created_ids = []
    yield created_ids
    if created_ids:
        url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
        with psycopg2.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM job_vacancies WHERE id::text = ANY(%s)",
                    ([str(uid) for uid in created_ids],),
                )
            conn.commit()


def test_create_job_dict_in_title_field(dev_local_env, db_cleanup):
    """Regression: jd.titulo_padronizado leaked as dict should NOT crash."""
    client = JobCreationAPIClient(context=None)
    job_data = {
        # Scalar fields with DICT LEAKS upstream from LLM:
        "title": {"text": "Engenheiro Backend Pleno", "padronizado": True},
        "description": {"about_role": "Trabalhar com Python e PostgreSQL"},
        "department": {"name": "Engenharia"},
        "location": {"city": "São Paulo", "state": "SP"},
        "work_model": "Remoto",
        "seniority": "Pleno",
        # Lists:
        "technical_requirements": [
            {"skill": "Python", "level": "advanced"},
            "PostgreSQL",
            {"technology": "Docker"},
        ],
        "behavioral_competencies": [
            {"competencia": "Comunicação", "score": 8},
        ],
        "responsibilities": [
            {"text": "Manutenção de pipelines"},
            "Code review",
        ],
    }
    resp = client.create_job(job_data)
    assert resp.success, f"dev-local create_job failed: {resp.error}"
    assert resp.data, "no data in response"
    row_id = resp.data["data"]["id"]
    db_cleanup.append(uuid.UUID(row_id))
    # Verify row exists and title was coerced to str
    url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    with psycopg2.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT title, department, location, status FROM job_vacancies WHERE id = %s",
                (row_id,),
            )
            row = cur.fetchone()
    assert row is not None, "row not created"
    title, dept, loc, status = row
    assert isinstance(title, str), f"title not str: {type(title).__name__}"
    assert "Engenheiro" in title or title == "(sem titulo)", f"title content lost: {title!r}"
    assert isinstance(dept, (str, type(None))), f"dept not str|None: {type(dept).__name__}"
    assert isinstance(loc, (str, type(None))), f"loc not str|None: {type(loc).__name__}"
    assert status == "Rascunho"


def test_create_job_all_strs_baseline(dev_local_env, db_cleanup):
    """Baseline: clean string input should still work (no regression)."""
    client = JobCreationAPIClient(context=None)
    job_data = {
        "title": "Tech Lead",
        "description": "Liderar squad de 5 devs",
        "department": "Engenharia",
        "location": "Remoto",
        "work_model": "Remoto",
        "seniority": "Senior",
        "technical_requirements": ["Python", "AWS", "Kubernetes"],
        "behavioral_competencies": ["Liderança", "Mentoring"],
        "responsibilities": ["Tech vision", "1:1s"],
    }
    resp = client.create_job(job_data)
    assert resp.success, f"baseline failed: {resp.error}"
    row_id = resp.data["data"]["id"]
    db_cleanup.append(uuid.UUID(row_id))


def test_create_job_all_dicts_extreme(dev_local_env, db_cleanup):
    """Extreme: every field is a nested dict. Should still coerce + insert."""
    client = JobCreationAPIClient(context=None)
    job_data = {
        "title": {"deeply": {"nested": {"value": "Coord. Recursos Humanos"}}},
        "description": {"summary": "x" * 100},
        "department": {"raw": ["RH", "People"]},
        "location": {"address": {"street": "x"}},
        "work_model": {"type": "hybrid"},
        "seniority": {"level": "senior"},
        "technical_requirements": [{"weird": {"nested": "Excel"}}],
        "behavioral_competencies": [{"random": "dict"}],
        "responsibilities": [{"text": "Recrutamento"}],
    }
    resp = client.create_job(job_data)
    assert resp.success, f"extreme dict test failed: {resp.error}"
    db_cleanup.append(uuid.UUID(resp.data["data"]["id"]))
