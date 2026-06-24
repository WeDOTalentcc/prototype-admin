"""
TDD — Wizard publish FastAPI-native path.

Verifica que _publish_job_fastapi cria JobVacancy + ScreeningQuestionSet
sem usar publish_node / RAILS_API_URL.
"""
import sys
import types
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

COMPANY_ID = str(uuid.uuid4())
JOB_ID = str(uuid.uuid4())

_BASE_STATE = {
    "jd_enriched": {
        "titulo_padronizado": "Engenheiro de Software Pleno",
        "about_role": "Responsável pelo desenvolvimento de APIs REST.",
        "responsabilidades": ["Desenvolver APIs", "Code review"],
        "skills_obrigatorias": [{"technology": "Python", "level": "Avançado"}],
    },
    "parsed_department": "Engenharia",
    "parsed_location": "São Paulo, SP",
    "parsed_seniority": "pleno",
    "salary_min": 8000,
    "salary_max": 12000,
    "salary_currency": "BRL",
    "wsi_questions": [
        {"id": "q1", "question": "Descreva uma situação.", "block": 1, "type": "behavioral"},
    ],
    "questions_approved": True,
    "screening_mode": "compact",
}


def _make_vacancy_class(job_id=JOB_ID):
    """Retorna uma classe fake de JobVacancy com id fixo."""
    class FakeVacancy:
        def __init__(self, **kwargs):
            self.id = uuid.UUID(job_id)
            for k, v in kwargs.items():
                setattr(self, k, v)
    return FakeVacancy


def _patch_lazy_imports(mock_vacancy_class, mock_repo, mock_qs_repo, mock_db):
    """Injeta sys.modules fakes para os lazy imports dentro de _publish_job_fastapi."""
    fake_db_mod = types.ModuleType("app.core.database")
    fake_db_mod.AsyncSessionLocal = lambda: mock_db

    fake_repo_mod = types.ModuleType(
        "app.domains.job_management.repositories.job_vacancy_crud_repository"
    )
    fake_repo_mod.JobVacancyCRUDRepository = lambda db: mock_repo

    fake_jv_mod = types.ModuleType("libs.models.lia_models.job_vacancy")
    fake_jv_mod.JobVacancy = mock_vacancy_class

    fake_qs_mod = types.ModuleType(
        "app.domains.cv_screening.repositories.screening_question_set_repository"
    )
    fake_qs_mod.ScreeningQuestionSetRepository = lambda db: mock_qs_repo

    keys = [
        "app.core.database",
        "app.domains.job_management.repositories.job_vacancy_crud_repository",
        "libs.models.lia_models.job_vacancy",
        "app.domains.cv_screening.repositories.screening_question_set_repository",
    ]
    originals = {k: sys.modules.get(k) for k in keys}
    sys.modules["app.core.database"] = fake_db_mod
    sys.modules["app.domains.job_management.repositories.job_vacancy_crud_repository"] = fake_repo_mod
    sys.modules["libs.models.lia_models.job_vacancy"] = fake_jv_mod
    sys.modules["app.domains.cv_screening.repositories.screening_question_set_repository"] = fake_qs_mod
    return originals, keys


def _restore(originals, keys):
    for k in keys:
        v = originals.get(k)
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


@pytest.mark.asyncio
async def test_publish_fastapi_creates_vacancy_with_ativa_status():
    """_publish_job_fastapi cria JobVacancy com status=Ativa e retorna job_id."""
    from app.domains.job_creation.orchestrator.wizard_service_tools import (
        _publish_job_fastapi,
    )

    mock_repo = MagicMock()
    mock_qs_repo = MagicMock()
    mock_qs_repo.insert_set = AsyncMock()
    mock_db = AsyncMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)
    mock_db.commit = AsyncMock()

    created_kwargs: dict = {}

    def _fake_vacancy_class(**kwargs):
        created_kwargs.update(kwargs)
        v = MagicMock()
        v.id = uuid.UUID(JOB_ID)
        return v

    mock_repo.create_vacancy = AsyncMock(side_effect=lambda v: v)

    originals, keys = _patch_lazy_imports(_fake_vacancy_class, mock_repo, mock_qs_repo, mock_db)
    try:
        with (
            patch(
                "app.domains.job_creation.helpers.vacancy_vocab.to_canonical_seniority",
                return_value="Pleno",
            ),
            patch(
                "app.domains.job_creation.helpers.vacancy_vocab.to_canonical_work_model",
                return_value=None,
            ),
        ):
            result = await _publish_job_fastapi(dict(_BASE_STATE), COMPANY_ID)
    finally:
        _restore(originals, keys)

    assert result["job_id"] == JOB_ID
    assert result["share_link"] == f"/pt/jobs/{JOB_ID}"
    mock_repo.create_vacancy.assert_called_once()
    # question_set criado porque questions_approved=True
    mock_qs_repo.insert_set.assert_called_once()
    assert created_kwargs["status"] == "Ativa"
    assert created_kwargs["company_id"] == COMPANY_ID


@pytest.mark.asyncio
async def test_publish_fastapi_skips_question_set_when_not_approved():
    """Sem questions_approved=True, ScreeningQuestionSet NÃO é persistido."""
    from app.domains.job_creation.orchestrator.wizard_service_tools import (
        _publish_job_fastapi,
    )

    state = {**_BASE_STATE, "questions_approved": False}

    mock_repo = MagicMock()
    mock_qs_repo = MagicMock()
    mock_qs_repo.insert_set = AsyncMock()
    mock_db = AsyncMock()
    mock_db.__aenter__ = AsyncMock(return_value=mock_db)
    mock_db.__aexit__ = AsyncMock(return_value=None)
    mock_db.commit = AsyncMock()

    def _fake_vacancy_class(**kwargs):
        v = MagicMock()
        v.id = uuid.UUID(JOB_ID)
        return v

    mock_repo.create_vacancy = AsyncMock(side_effect=lambda v: v)

    originals, keys = _patch_lazy_imports(_fake_vacancy_class, mock_repo, mock_qs_repo, mock_db)
    try:
        with (
            patch("app.domains.job_creation.helpers.vacancy_vocab.to_canonical_seniority", return_value="Pleno"),
            patch("app.domains.job_creation.helpers.vacancy_vocab.to_canonical_work_model", return_value=None),
        ):
            result = await _publish_job_fastapi(state, COMPANY_ID)
    finally:
        _restore(originals, keys)

    assert result["job_id"] == JOB_ID
    mock_qs_repo.insert_set.assert_not_called()


def test_handle_publish_job_calls_fastapi_not_rails():
    """_handle_publish_job não referencia publish_node — usa _publish_job_fastapi."""
    import inspect
    from app.domains.job_creation.orchestrator import wizard_service_tools as wst

    src = inspect.getsource(wst._handle_publish_job)
    assert "publish_node" not in src, (
        "publish_node ainda está sendo chamado — deve ser substituído por _publish_job_fastapi"
    )
    assert "_publish_job_fastapi" in src
    assert "run_coro_in_threadpool" in src
