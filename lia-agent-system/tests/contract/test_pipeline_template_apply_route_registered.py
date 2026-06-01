"""Sensor canonical: o vacancy_apply_router DEVE estar registrado no app real.

Defeito de harness corrigido (2026-06-01): vacancy_apply_router
(POST /vacancies/{id}/apply-pipeline-template) era definido em
app/api/v1/pipeline_templates.py mas NUNCA incluido em register_all_routes
(routes.py). Resultado: apply retornava 404 em producao -- wizard e linking
manual quebrados.

O teste pre-existente test_pipeline_template_rbac.py NAO pegou isso porque
asserta sobre vacancy_apply_router.routes (router isolado), nao sobre o app
montado. Este sensor fecha o gap: registra as rotas no app REAL e verifica que
o path canonico existe -- feedback de integracao, nao de unidade isolada.
"""

from fastapi import FastAPI

from app.api.routes import register_all_routes

APPLY_PATH = "/api/v1/vacancies/{vacancy_id}/apply-pipeline-template"


def _registered_paths() -> set[str]:
    app = FastAPI()
    register_all_routes(app)
    return {getattr(r, "path", "") for r in app.routes}


def test_apply_pipeline_template_route_is_registered_in_real_app():
    paths = _registered_paths()
    vacancy_paths = sorted(p for p in paths if "vacanc" in p.lower())
    assert APPLY_PATH in paths, (
        "apply-pipeline-template NAO esta registrado no app real.\n"
        "-> Fix: em app/api/routes.py, adicionar "
        'app.include_router(pipeline_templates.vacancy_apply_router, prefix="/api/v1").\n'
        f"Paths /vacancies encontrados: {vacancy_paths}"
    )
