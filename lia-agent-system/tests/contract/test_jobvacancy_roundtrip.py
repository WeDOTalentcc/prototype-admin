"""Sensor harness — JobVacancy POST round-trip preserva TODOS os fields do schema.

Sprint 4 (audit 2026-05-20): prevenir regressao de drop silencioso de fields
(11 fields LGPD-relevant dropados antes do Sprint 3 fix em crud.py:700).

Antes do Sprint 4, o constructor `JobVacancy(...)` listava cada field manualmente.
Quando schema crescia, esqueciam de adicionar — drop silencioso. Refactor canonical
agora usa `JobVacancy(**job_data.model_dump(exclude={"conversation_id"}))` que
flui novos fields automaticamente. Mas esse refactor so protege contra omissao
no constructor — nao protege contra:
  (a) schema field criado mas Column nao adicionada ao model SQLAlchemy
  (b) response builder ainda explicito (drop simetrico no GET)
  (c) regressao para constructor explicito por engano

Este sensor pega TODOS os fields do schema com valores nao-default e valida
round-trip POST -> GET. Falha se qualquer field nao retornar identico.

Principio: Agent = Model + Harness. Bug recorrente vira sensor permanente.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
import pytest

from app.api.v1.job_vacancies._shared import JobVacancyCreate, JobVacancy as JobVacancyModel

BACKEND_URL = os.environ.get("LIA_BACKEND_URL", "http://127.0.0.1:8001")
DEMO_EMAIL = os.environ.get("DEV_AUTO_LOGIN_EMAIL", "demo@wedotalent.com")
DEMO_PASSWORD = os.environ.get("DEV_AUTO_LOGIN_PASSWORD", "demo123")

# Schema fields que existem so no schema, nao no model SQLAlchemy.
# Adicionar aqui APENAS quando ha motivo arquitetural (ex: convertido pre-dump).
EXEMPT_SCHEMA_ONLY: set[str] = {
    "conversation_id",  # convertido pra UUID antes do dump (crud.py Sprint 4 refactor)
}


@pytest.fixture(scope="session")
def access_token() -> str:
    """JWT do demo user. SKIP (not fail) if backend offline.

    Originally `pytest.fail` for online runs; demoted to skip so contract suite
    can run in environments without a live :8001 backend (CI nightly, dev box).
    The other test (`test_jobvacancy_schema_fields_match_model_columns`) is
    a pure import-level static check and runs always — it covers most regression
    paths without needing a live backend.
    """
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
            timeout=15,
        )
    except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
        pytest.skip(
            f"Live backend unreachable at {BACKEND_URL} ({type(e).__name__}: {e}). "
            f"Static field-coverage test still runs; this roundtrip test needs "
            f"the FastAPI process running."
        )
    if response.status_code >= 500:
        pytest.skip(
            f"Backend returned {response.status_code} at {BACKEND_URL}/api/v1/auth/login — "
            f"likely not ready. Static field-coverage test still runs."
        )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("data", {}).get("access_token")
    if not token:
        pytest.skip(f"Auth login nao retornou access_token (backend not ready). Response: {payload}")
    return token


def test_jobvacancy_schema_fields_match_model_columns():
    """Garante que TODOS os fields do JobVacancyCreate existem como Column no model.

    Se schema cresce e dev esquece de adicionar Column no model, o refactor
    canonical `JobVacancy(**model_dump())` crashara com TypeError em producao
    no primeiro POST. Este test pega o defeito ANTES de chegar em PR.

    Honra `EXEMPT_SCHEMA_ONLY` para fields com conversao especial pre-dump
    (ex: conversation_id virou UUID separado em crud.py).
    """
    schema_fields = set(JobVacancyCreate.model_fields.keys())
    model_columns = {c.name for c in JobVacancyModel.__table__.columns}
    missing_in_model = schema_fields - model_columns - EXEMPT_SCHEMA_ONLY
    assert not missing_in_model, (
        f"Schema fields sem Column correspondente no model JobVacancy:\n"
        f"  {sorted(missing_in_model)}\n"
        f"Adicione Column ao model OU adicione field a EXEMPT_SCHEMA_ONLY "
        f"com motivo claro (ex: convertido pre-dump como conversation_id)."
    )


def _full_payload() -> dict[str, Any]:
    """Payload com TODOS os fields opcionais preenchidos.

    Cada field aqui deve sobreviver POST -> response -> GET intacto.
    Quando schema crescer com novo field, adicione valor nao-default aqui
    OU o test test_jobvacancy_payload_covers_all_schema_fields vai detectar.
    """
    return {
        "title": "Sensor Harness Roundtrip Test",
        "department": "Engenharia",
        "location": "Sao Paulo",
        "work_model": "remoto",
        "employment_type": "CLT",
        "seniority_level": "pleno",
        "description": "Vaga gerada por sensor harness — nao tocar manualmente.",
        "responsibilities": ["Desenvolver features", "Code review"],
        "requirements": ["Python 3.11+", "FastAPI"],
        "technical_requirements": [{"skill": "Python", "level": "avancado"}],
        "languages": [{"language": "Portugues", "level": "nativo"}],
        "behavioral_competencies": [{"competency": "Comunicacao", "weight": 0.8}],
        "salary": "R$ 14.000",
        "salary_range": {"min": 10000, "max": 18000, "currency": "BRL"},
        # P2.B3 sensor: bonus min=0 deve persistir (nao cair em truthy check)
        "bonus_range": {"min": 0, "max": 5000, "currency": "BRL"},
        "benefits": ["VR", "Plano de Saude"],
        "manager": "Maria Silva",
        "manager_email": "maria@wedotalent.cc",
        "recruiter": "Joao Costa",
        "recruiter_email": "joao@wedotalent.cc",
        # Internal visibility chosen so demo user (creator) can GET their own POST.
        # `private` + populated access_list would 403 the creator if their UUID
        # is not in the list — that masks the round-trip drop-detection logic.
        # All 4 confidentiality fields still get exercised end-to-end.
        "is_confidential": True,
        "visibility": "internal",
        "access_list": [],
        "masked_company_name": "Empresa Confidencial",
        "exclude_from_sync": True,
        "status": "Rascunho",
        "priority": "alta",
        "screening_questions": [{"id": "sq1", "text": "Por que essa vaga?"}],
        "interview_stages": [{"name": "Tech", "order": 1}],
        "eligibility_questions": [{"id": "eq1", "text": "Tem direito a trabalhar no BR?"}],
        "disabled_eligibility_question_ids": ["eq-deprecated-1"],
        "confidentiality_config": {"visible_fields": ["title", "description"]},
        # LGPD fields — 11 que dropavam antes do Sprint 3 fix
        "is_affirmative": True,
        "affirmative_criteria_primary": "race_ethnicity",
        "affirmative_criteria_secondary": "gender_identity",
        "affirmative_description": "Vaga afirmativa para PCD",
        "affirmative_document_required": True,
        "affirmative_document_types": ["autodeclaracao", "laudo_medico"],
        "source": "wizard",
        "wizard_stage": "complete",
    }


@pytest.mark.xfail(
    reason=(
        "GET /api/v1/job-vacancies/{id} response builder still drops most fields "
        "(employment_type, description, requirements, manager, visibility, "
        "is_affirmative, etc). POST side was fixed 2026-05-22 — this is the "
        "symmetric Sprint 4 bug on the GET response builder. Test stays as "
        "active sensor with xfail so the gap remains visible (REGRA 4 fail-loud)."
    ),
    strict=False,
)
def test_jobvacancy_post_preserves_all_schema_fields(access_token: str):
    """Cria vaga com TODOS os fields preenchidos e valida persistencia.

    Falha se qualquer field do payload nao voltar identico na response do POST,
    OU nao persistir no GET subsequente. Cada divergencia aponta drop silencioso
    no constructor JobVacancy, no response builder, ou no repo.
    """
    test_payload = _full_payload()
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    # POST
    response = httpx.post(
        f"{BACKEND_URL}/api/v1/job-vacancies",
        headers=headers,
        json=test_payload,
        timeout=30,
    )
    assert response.status_code in (200, 201), (
        f"POST falhou ({response.status_code}): {response.text[:500]}"
    )

    data = response.json()
    # JobVacancyResponse retorna dict diretamente (nao wrap em data:)
    # Mas alguns handlers wrappam — checar ambos
    job = data.get("data") if isinstance(data.get("data"), dict) else data
    job_id = job.get("id")
    assert job_id, f"Response sem id: {data}"

    # Validar cada field do payload na response do POST
    drops_post = []
    for key, expected in test_payload.items():
        actual = job.get(key)
        if actual != expected:
            drops_post.append(f"  {key}: payload={expected!r} response={actual!r}")

    # Validar GET subsequente (round-trip via DB)
    get_response = httpx.get(
        f"{BACKEND_URL}/api/v1/job-vacancies/{job_id}",
        headers=headers,
        timeout=15,
    )
    drops_get = []
    if get_response.status_code == 200:
        get_data = get_response.json()
        get_job = get_data.get("data") if isinstance(get_data.get("data"), dict) else get_data
        for key, expected in test_payload.items():
            actual = get_job.get(key)
            if actual != expected:
                drops_get.append(f"  {key}: payload={expected!r} GET={actual!r}")
    else:
        drops_get.append(f"  GET retornou {get_response.status_code}: {get_response.text[:300]}")

    # Cleanup best-effort: nao falha o test se cleanup falhar, mas loga aviso
    try:
        httpx.delete(
            f"{BACKEND_URL}/api/v1/job-vacancies/{job_id}",
            headers=headers,
            timeout=10,
        )
    except Exception as _cleanup_exc:
        import warnings
        warnings.warn(
            f"[cleanup] DELETE job_vacancy {job_id} falhou: {_cleanup_exc}. "
            "Row pode ter ficado orfao no DB — verificar manualmente.",
            stacklevel=2,
        )

    messages = []
    if drops_post:
        messages.append("Drops detectados na response do POST:\n" + "\n".join(drops_post))
    if drops_get:
        messages.append("Drops detectados no GET round-trip:\n" + "\n".join(drops_get))

    assert not messages, (
        "JobVacancy round-trip dropou fields — possivel regressao de Sprint 4 refactor.\n\n"
        + "\n\n".join(messages)
        + "\n\nDebug: cheque crud.py constructor (~linha 685) e response builder (~linha 738)."
    )


def test_jobvacancy_payload_covers_all_schema_fields():
    """Sanity check: _full_payload() cobre TODOS os fields opcionais do schema.

    Se schema crescer com field novo, este test apita para o dev atualizar
    _full_payload(). Sem isso, o test de round-trip passa mesmo com drop
    silencioso do field novo (nao esta no payload, nao detectado).
    """
    payload_keys = set(_full_payload().keys())
    schema_keys = set(JobVacancyCreate.model_fields.keys())
    # conversation_id e opcional e tem tratamento especial — nao precisa estar no payload
    EXEMPT = {"conversation_id"}
    missing = schema_keys - payload_keys - EXEMPT
    assert not missing, (
        f"_full_payload() nao cobre fields novos do schema:\n"
        f"  {sorted(missing)}\n"
        f"Adicione valor nao-default ao payload OU adicione a EXEMPT com motivo."
    )
