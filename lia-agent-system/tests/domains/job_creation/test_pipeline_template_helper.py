"""Regression test PR-4 site C-1 fix.

Site `_apply_pipeline_template_to_state._run()` em graph.py:1396 usava
`_asyncio.run()` em sync function chamada de dentro de event loop ativo
(Python 3.12+ raise RuntimeError → mascarado por except Exception →
template silenciosamente NÃO aplicado).

Fix PR-4 (2026-05-26): substitui por `run_coro_in_threadpool()` que delega
para ThreadPoolExecutor em thread separada.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_apply_template_in_running_loop_no_runtime_error():
    """Regression sentinel para PR-4 site C-1.

    Antes do fix: _asyncio.run() levantava RuntimeError ('asyncio.run cannot
    be called from a running event loop') em Python 3.12+ — mascarado por
    `except Exception: return None`. Template silenciosamente ignorado.

    Depois do fix: run_coro_in_threadpool() delega para ThreadPoolExecutor +
    asyncio.run em thread separada — funciona com loop ativo.
    """
    # Setup: mock do AsyncSessionLocal + repo retornando template fake.
    fake_template = MagicMock()
    fake_template.stages = [{"name": "Triagem", "interview_type": "screening"}]
    fake_template.name = "Template Default"

    fake_session = AsyncMock()
    fake_session.__aenter__.return_value = fake_session
    fake_session.__aexit__.return_value = None

    fake_repo = MagicMock()
    fake_repo.get_by_id = AsyncMock(return_value=fake_template)
    fake_repo.increment_usage = AsyncMock(return_value=None)

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=fake_session,
    ), patch(
        "app.domains.pipeline.repositories.pipeline_template_repository."
        "PipelineTemplateRepository",
        return_value=fake_repo,
    ), patch(
        "app.domains.pipeline.services.pipeline_template_service."
        "translate_template_stages_to_interview_stages",
        return_value=[{"name": "Triagem", "interview_type": "screening"}],
    ):
        from app.domains.job_creation.graph import _apply_pipeline_template_to_state

        # IMPORTANTE: o decorator @pytest.mark.asyncio garante que estamos
        # num running event loop. Antes do PR-4, _asyncio.run aqui raise
        # RuntimeError → except Exception mascara → return None silently.
        state = {
            "workspace_id": "11111111-1111-1111-1111-111111111111",
            "company_id": "11111111-1111-1111-1111-111111111111",
        }
        result = _apply_pipeline_template_to_state(
            state, template_id="22222222-2222-2222-2222-222222222222",
        )

    # Após o fix: helper canonical funciona com loop ativo → template aplicado.
    assert result is not None, (
        "PR-4 regression: _apply_pipeline_template_to_state retornou None — "
        "indicação que asyncio.run em loop ativo voltou (Python 3.12+ raise)."
    )
    assert "interview_stages" in result
    assert result["template_name"] == "Template Default"


@pytest.mark.asyncio
async def test_apply_template_returns_none_when_no_company_id():
    """Sanity check: company_id ausente continua retornando None (fail-open)."""
    from app.domains.job_creation.graph import _apply_pipeline_template_to_state

    state = {}  # sem workspace_id nem company_id
    result = _apply_pipeline_template_to_state(state, template_id="anything")
    assert result is None


@pytest.mark.asyncio
async def test_apply_template_returns_none_when_template_not_found():
    """Repo retorna None → função retorna None (fail-open)."""
    fake_session = AsyncMock()
    fake_session.__aenter__.return_value = fake_session
    fake_session.__aexit__.return_value = None

    fake_repo = MagicMock()
    fake_repo.get_by_id = AsyncMock(return_value=None)

    with patch(
        "app.core.database.AsyncSessionLocal",
        return_value=fake_session,
    ), patch(
        "app.domains.pipeline.repositories.pipeline_template_repository."
        "PipelineTemplateRepository",
        return_value=fake_repo,
    ):
        from app.domains.job_creation.graph import _apply_pipeline_template_to_state

        state = {"workspace_id": "11111111-1111-1111-1111-111111111111"}
        result = _apply_pipeline_template_to_state(
            state, template_id="22222222-2222-2222-2222-222222222222",
        )

    assert result is None
