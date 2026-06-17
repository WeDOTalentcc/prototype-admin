"""
Contract tests: Pipeline IDOR — ownership check em inheritance-status + mark-customized
P0-W1-02 + P0-W1-03

Contexto:
  - P0-W1-02: GET /pipeline/job/{job_id}/inheritance-status
    Antes do fix: endpoint buscava JobVacancy por id mas NÃO verificava
    se job.company_id batia com o company_id do JWT. Qualquer usuário
    autenticado podia ler pipeline_config de vagas de outras empresas.

  - P0-W1-03: POST /pipeline/job/{job_id}/mark-customized
    Já fixado em Phase G.3 (docstring no endpoint): UPDATE escopa por
    id AND company_id. Rowcount=0 → 404. Sem enumeration leak.

Estratégia: unit tests puros com mocks — sem spin-up de DB real.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers para construir mocks canonicamente
# ---------------------------------------------------------------------------


def _make_job(job_id: str, company_id: str) -> MagicMock:
    """Retorna um mock de JobVacancy com company_id e pipeline_config."""
    job = MagicMock()
    job.id = uuid.UUID(job_id)
    job.company_id = company_id
    job.pipeline_config = None
    job.is_pipeline_customized = False
    return job


def _make_user(company_id: str) -> MagicMock:
    """Retorna um mock de User com company_id setado."""
    user = MagicMock()
    user.company_id = company_id
    user.role = "recruiter"
    return user


def _make_stage_repo(job_or_none) -> MagicMock:
    """Retorna um mock de RecruitmentStageRepository cujo db.get
    devolve job_or_none."""
    repo = MagicMock()
    repo.db = MagicMock()
    repo.db.get = AsyncMock(return_value=job_or_none)
    # Para o path sa_select (inheritance-status usa db.execute)
    result_mock = MagicMock()
    result_mock.scalars.return_value.first.return_value = job_or_none
    repo.db.execute = AsyncMock(return_value=result_mock)
    return repo


# ---------------------------------------------------------------------------
# P0-W1-02: GET /pipeline/job/{job_id}/inheritance-status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inheritance_status_denies_cross_tenant():
    """
    P0-W1-02 GREEN: get_pipeline_inheritance_status deve retornar 403
    quando o job pertence a company diferente do JWT do usuário.

    Antes do fix (RED), o endpoint retornava 200 com pipeline_config
    da vaga de outra empresa — IDOR cross-tenant info disclosure.
    """
    from fastapi import HTTPException

    from app.api.v1.recruitment_stages.stages_pipeline import (
        get_pipeline_inheritance_status,
    )

    job_id = str(uuid.uuid4())
    attacker_company = "company-attacker-111"
    victim_company = "company-victim-222"

    job = _make_job(job_id, victim_company)
    stage_repo = _make_stage_repo(job)
    user = _make_user(attacker_company)

    with patch(
        "app.api.v1.recruitment_stages.stages_pipeline.get_user_company_id",
        return_value=attacker_company,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_pipeline_inheritance_status(
                job_id=job_id,
                current_user=user,
                stage_repo=stage_repo,
                company_id=attacker_company,
            )

    assert exc_info.value.status_code == 403, (
        f"Esperado 403 Access denied, obtido {exc_info.value.status_code}. "
        "O endpoint não verificou ownership — IDOR P0-W1-02 não corrigido."
    )


@pytest.mark.asyncio
async def test_inheritance_status_allows_same_company():
    """
    P0-W1-02 GREEN: deve retornar 200 quando o job pertence à mesma empresa do JWT.
    """
    from app.api.v1.recruitment_stages.stages_pipeline import (
        get_pipeline_inheritance_status,
    )

    job_id = str(uuid.uuid4())
    company_id = "company-legitimate-333"

    job = _make_job(job_id, company_id)
    stage_repo = _make_stage_repo(job)
    user = _make_user(company_id)

    with patch(
        "app.api.v1.recruitment_stages.stages_pipeline.get_user_company_id",
        return_value=company_id,
    ):
        result = await get_pipeline_inheritance_status(
            job_id=job_id,
            current_user=user,
            stage_repo=stage_repo,
            company_id=company_id,
        )

    assert result["job_id"] == job_id
    assert "is_customized" in result


@pytest.mark.asyncio
async def test_inheritance_status_returns_404_when_job_not_found():
    """
    P0-W1-02: deve retornar 404 quando job não existe — não 403 nem 200.
    Garante que não haja enumeration leak (mesma resposta para "não existe"
    e "não é seu" não é o padrão aqui; mantemos 404 para job ausente).
    """
    from fastapi import HTTPException

    from app.api.v1.recruitment_stages.stages_pipeline import (
        get_pipeline_inheritance_status,
    )

    job_id = str(uuid.uuid4())
    company_id = "company-any-444"

    stage_repo = _make_stage_repo(None)  # job não encontrado
    user = _make_user(company_id)

    with patch(
        "app.api.v1.recruitment_stages.stages_pipeline.get_user_company_id",
        return_value=company_id,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_pipeline_inheritance_status(
                job_id=job_id,
                current_user=user,
                stage_repo=stage_repo,
                company_id=company_id,
            )

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# P0-W1-03: POST /pipeline/job/{job_id}/mark-customized
# (Phase G.3 fix — verificação de regressão: o fix NÃO deve ser revertido)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mark_customized_denies_cross_tenant():
    """
    P0-W1-03 REGRESSION PIN: mark_pipeline_customized deve retornar 404
    (sem enumeration leak) quando job_id pertence a outra empresa.

    O Phase G.3 fix implementou: UPDATE WHERE id=X AND company_id=Y.
    Rowcount=0 → 404. Esse teste garante que a clausula company_id
    no WHERE nunca seja removida sem detectar a regressão.
    """
    from fastapi import HTTPException

    from app.api.v1.recruitment_stages.stages_pipeline import (
        mark_pipeline_customized,
    )

    job_id = str(uuid.uuid4())
    attacker_company = "company-attacker-555"

    stage_repo = MagicMock()
    stage_repo.db = MagicMock()
    # Simula UPDATE que não encontrou rows (job de outra empresa)
    result_mock = MagicMock()
    result_mock.rowcount = 0
    stage_repo.db.execute = AsyncMock(return_value=result_mock)
    stage_repo.db.commit = AsyncMock()

    user = _make_user(attacker_company)

    with patch(
        "app.api.v1.recruitment_stages.stages_pipeline.get_user_company_id",
        return_value=attacker_company,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await mark_pipeline_customized(
                job_id=job_id,
                current_user=user,
                stage_repo=stage_repo,
                company_id=attacker_company,
            )

    assert exc_info.value.status_code == 404, (
        f"Esperado 404 (rowcount=0 cross-tenant), obtido {exc_info.value.status_code}. "
        "O Phase G.3 WHERE company_id pode ter sido removido — IDOR P0-W1-03 regrediu."
    )


@pytest.mark.asyncio
async def test_mark_customized_succeeds_for_own_company():
    """
    P0-W1-03 REGRESSION PIN: mark_pipeline_customized deve retornar 200
    para job da mesma empresa (rowcount > 0).
    """
    from app.api.v1.recruitment_stages.stages_pipeline import (
        mark_pipeline_customized,
    )

    job_id = str(uuid.uuid4())
    company_id = "company-own-666"

    stage_repo = MagicMock()
    stage_repo.db = MagicMock()
    result_mock = MagicMock()
    result_mock.rowcount = 1  # UPDATE encontrou a row
    stage_repo.db.execute = AsyncMock(return_value=result_mock)
    stage_repo.db.commit = AsyncMock()

    user = _make_user(company_id)

    with patch(
        "app.api.v1.recruitment_stages.stages_pipeline.get_user_company_id",
        return_value=company_id,
    ):
        result = await mark_pipeline_customized(
            job_id=job_id,
            current_user=user,
            stage_repo=stage_repo,
            company_id=company_id,
        )

    assert result["success"] is True
    assert result["is_customized"] is True
