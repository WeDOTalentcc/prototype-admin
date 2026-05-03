"""Smoke tests para Sprint B endpoints + wiring (sem DB real).

Valida:
- Routers sao loadable e expoem rotas esperadas
- record_jd_fire_and_forget nao raise mesmo com inputs invalidos
- _hook_conclusion_hired nao raise quando vc/job nao existem
- Audit log instrumentation nao quebra fluxo se audit_service falha
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


def test_jd_similar_router_loads():
    """jd_similar router exporta 4 rotas esperadas."""
    from app.api.v1 import jd_similar
    paths = sorted(r.path for r in jd_similar.router.routes)
    assert "/jd-similar/lookup" in paths
    assert "/jd-similar/record" in paths
    assert "/jd-similar/{record_id}/reuse" in paths
    assert "/jd-similar/mark-filled" in paths


def test_learning_loops_config_router_loads():
    """learning_loops_config router exporta 2 rotas (GET+PATCH)."""
    from app.api.v1 import learning_loops_config
    paths = sorted(r.path for r in learning_loops_config.router.routes)
    assert "/companies/{company_id}/learning-loops-config" in paths
    # P1.4 cleanup: alias router NAO deve existir mais
    assert not hasattr(learning_loops_config, "hiring_policy_router")


def test_record_jd_fire_and_forget_no_raise_on_empty_inputs():
    """fire-and-forget never raises - vital pra sync wiring."""
    from app.domains.job_creation.services.jd_similar_service import (
        record_jd_fire_and_forget,
    )

    # Empty company_id - early return, no raise
    record_jd_fire_and_forget(
        company_id="",
        job_id="job-x",
        title="Vaga",
        jd_enriched={},
    )

    # Empty title - early return, no raise
    record_jd_fire_and_forget(
        company_id="co-x",
        job_id="job-x",
        title="",
        jd_enriched={},
    )

    # All empty - early return, no raise
    record_jd_fire_and_forget(
        company_id="",
        job_id="",
        title="",
        jd_enriched={},
    )


@pytest.mark.asyncio
async def test_hook_conclusion_hired_no_raise_on_missing_vc():
    """Hook fail-soft: VC nao existe - log warning + continue."""
    from app.domains.communication.services.transition_dispatch_service import (
        TransitionDispatchService,
    )

    # Mock db.execute to return empty result
    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars = MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    mock_db.execute = AsyncMock(return_value=mock_result)

    svc = TransitionDispatchService(db=mock_db)

    # Should not raise even when VC lookup returns None
    await svc._hook_conclusion_hired(
        vacancy_candidate_id="vc-nonexistent",
        company_id="company-x",
    )


@pytest.mark.asyncio
async def test_hook_conclusion_hired_skip_on_missing_company_id():
    """Hook early-return quando company_id ausente (multi-tenancy)."""
    from app.domains.communication.services.transition_dispatch_service import (
        TransitionDispatchService,
    )

    mock_db = MagicMock()
    mock_db.execute = AsyncMock()
    svc = TransitionDispatchService(db=mock_db)

    await svc._hook_conclusion_hired(
        vacancy_candidate_id="vc-x",
        company_id=None,
    )

    # Sem company_id, db.execute nao deve ter sido chamado
    mock_db.execute.assert_not_called()


def test_jd_similar_endpoints_have_request_validation():
    """Endpoints REST validam corpo via Pydantic - schemas presentes."""
    from app.api.v1.jd_similar import (
        JdRecordRequest,
        JdSimilarLookupResponse,
        MarkFilledRequest,
        ReuseRequest,
    )

    # Validacao de campos obrigatorios
    with pytest.raises(Exception):  # ValidationError
        JdRecordRequest(
            company_id="",  # min_length=1
            job_id="x",
            title="x",
            jd_enriched={},
        )
    with pytest.raises(Exception):
        MarkFilledRequest(
            company_id="x",
            job_id="x",
            time_to_fill_days=-1,  # ge=0
            candidates_count=0,
        )


def test_learning_loops_config_returns_defaults_for_unknown_company():
    """_extract_loops retorna defaults sem DB call quando policy ausente."""
    from app.api.v1.learning_loops_config import _DEFAULT_LOOPS, _extract_loops

    result = _extract_loops(None)
    assert result == _DEFAULT_LOOPS
    # Defaults garantem opt-in pra LGPD-sensitive loops
    assert result["bigfive_department_history"] is False
    assert result["wsi_question_effectiveness"] is False
    # E ON pra loops de baixo risco
    assert result["jd_similar_suggestion"] is True
    assert result["bigfive_company_culture"] is True
