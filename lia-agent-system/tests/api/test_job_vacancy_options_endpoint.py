"""
Onda 1 / O1.1 — GET /job-vacancies/options serves the dropdown vocabularies
(status, prioridade, urgência, modelo de trabalho, tipo de contrato, senioridade)
from FastAPI as the single canonical source. Rails is out of the flow.

Root cause (audit 2026-06-06): the "Informações Gerais" dropdowns were empty
because their backend-proxy routes 404'd (silent `[] ` via shouldRetryOnError:false).
Going FastAPI-canonical, this one endpoint backs 6 of the dropdowns.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.routing import APIRoute

from app.api.v1.job_vacancies import router as job_vacancies_router
from app.api.v1.job_vacancies._shared import VALID_JOB_STATUSES


def _options_app():
    from app.auth.dependencies import get_current_active_user

    app = FastAPI()
    app.include_router(job_vacancies_router)

    user = type("U", (), {"id": "u1", "email": "r@c.com", "company_id": "c1", "role": "recruiter"})()
    app.dependency_overrides[get_current_active_user] = lambda: user
    return app


class TestOptionsRouteRegistered:
    def test_options_route_exists_and_is_static_before_item_handler(self):
        routes = [r for r in job_vacancies_router.routes if isinstance(r, APIRoute)]
        paths = [r.path for r in routes]
        assert "/job-vacancies/options" in paths, (
            "GET /job-vacancies/options must be registered as a static collection route"
        )
        # Must come before the BARE item catch-all /job-vacancies/{job_vacancy_id}
        # to avoid being shadowed (suffixed item routes like .../{id}/metrics are fine).
        opt_idx = next(i for i, r in enumerate(routes) if r.path == "/job-vacancies/options")
        catchall_idxs = [
            i for i, r in enumerate(routes)
            if r.path in ("/job-vacancies/{job_vacancy_id}", "/job-vacancies/{job_id}")
        ]
        if catchall_idxs:
            assert opt_idx < min(catchall_idxs), (
                "/options must be registered before the bare item catch-all"
            )


class TestOptionsPayload:
    def test_returns_200_with_six_vocabularies(self):
        client = TestClient(_options_app(), raise_server_exceptions=False)
        resp = client.get("/job-vacancies/options")
        assert resp.status_code == 200
        body = resp.json()
        for key in (
            "statuses", "priorities", "urgency_levels",
            "work_models", "employment_types", "seniority_levels",
        ):
            assert key in body, f"missing vocabulary: {key}"
            assert isinstance(body[key], list) and len(body[key]) > 0
            assert {"id", "name"} <= set(body[key][0].keys())

    def test_statuses_match_canonical_constant(self):
        client = TestClient(_options_app(), raise_server_exceptions=False)
        body = client.get("/job-vacancies/options").json()
        names = [o["name"] for o in body["statuses"]]
        assert names == VALID_JOB_STATUSES

    def test_work_models_are_canonical_pt(self):
        client = TestClient(_options_app(), raise_server_exceptions=False)
        body = client.get("/job-vacancies/options").json()
        names = [o["name"] for o in body["work_models"]]
        assert set(names) == {"remoto", "híbrido", "presencial"}

    def test_urgency_levels_are_1_to_5(self):
        client = TestClient(_options_app(), raise_server_exceptions=False)
        body = client.get("/job-vacancies/options").json()
        ids = [o["id"] for o in body["urgency_levels"]]
        assert ids == [1, 2, 3, 4, 5]
