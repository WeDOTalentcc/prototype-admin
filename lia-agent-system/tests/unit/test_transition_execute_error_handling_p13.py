"""P1.3 — transition/execute deve propagar exceções em vez de retornar HTTP 200 com success=False.

Testa:
1. Exceção inesperada (RuntimeError) → levanta HTTPException(500), NÃO retorna TransitionExecuteResponse.
2. HTTPException(404) → propaga sem ser convertida para 200.
3. ValueError → HTTPException(422).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


def _make_request(**kwargs):
    """Cria um TransitionExecuteRequest mínimo para os testes."""
    from app.api.v1.recruitment_stages._shared import TransitionExecuteRequest
    defaults = dict(
        vacancy_candidate_id="abc-123",
        to_stage="hired",
        action="manual",
    )
    defaults.update(kwargs)
    return TransitionExecuteRequest(**defaults)


def _make_user():
    user = MagicMock()
    user.id = "user-001"
    return user


def _make_stage_repo():
    repo = MagicMock()
    db = AsyncMock()
    execute_result = MagicMock()
    execute_result.rowcount = 1
    db.execute = AsyncMock(return_value=execute_result)
    db.commit = AsyncMock()
    repo.db = db
    return repo


@pytest.mark.asyncio
async def test_unexpected_exception_raises_http500():
    """RuntimeError dentro do handler deve virar HTTPException(500), não HTTP 200 com success=False."""
    from app.api.v1.recruitment_stages.stages_transition import execute_transition

    stage_repo = _make_stage_repo()
    # Forçar crash APÓS a query de update (rowcount=1 passa) — no bloco de automação
    stage_repo.db.execute.side_effect = RuntimeError("Simulated DB crash")

    with pytest.raises(HTTPException) as exc_info:
        await execute_transition(
            request=_make_request(),
            current_user=_make_user(),
            stage_repo=stage_repo,
            company_id="company-001",
        )

    assert exc_info.value.status_code == 500, (
        f"Esperado 500, obtido {exc_info.value.status_code}. "
        "O endpoint estava swallowing a exceção como HTTP 200 success=False."
    )


@pytest.mark.asyncio
async def test_http_exception_propagates():
    """HTTPException(404) deve propagar intacta, não ser convertida para HTTP 200."""
    from app.api.v1.recruitment_stages.stages_transition import execute_transition

    stage_repo = _make_stage_repo()
    stage_repo.db.execute.side_effect = HTTPException(status_code=404, detail="Not found upstream")

    with pytest.raises(HTTPException) as exc_info:
        await execute_transition(
            request=_make_request(),
            current_user=_make_user(),
            stage_repo=stage_repo,
            company_id="company-001",
        )

    assert exc_info.value.status_code == 404, (
        f"Esperado 404 propagado, obtido {exc_info.value.status_code}."
    )


@pytest.mark.asyncio
async def test_value_error_raises_http422():
    """ValueError de validação de negócio deve virar HTTPException(422), não 200."""
    from app.api.v1.recruitment_stages.stages_transition import execute_transition

    stage_repo = _make_stage_repo()
    stage_repo.db.execute.side_effect = ValueError("Invalid stage transition: hired → triagem")

    with pytest.raises(HTTPException) as exc_info:
        await execute_transition(
            request=_make_request(),
            current_user=_make_user(),
            stage_repo=stage_repo,
            company_id="company-001",
        )

    assert exc_info.value.status_code == 422, (
        f"Esperado 422 para ValueError, obtido {exc_info.value.status_code}."
    )
    assert "Invalid stage transition" in str(exc_info.value.detail)
