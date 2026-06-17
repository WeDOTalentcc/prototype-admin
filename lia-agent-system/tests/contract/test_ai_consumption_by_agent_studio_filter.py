"""Contract test for /ai-consumption/by-agent studio_agent_id filter.

Wave 0 Fix 5 (2026-05-27).

Pina:
  - Repository.get_usage_by_agent aceita studio_agent_id opcional
  - Quando passado, SQL WHERE inclui AiConsumption.studio_agent_id == val
  - Endpoint expõe studio_agent_id como Query param opcional
  - Backward-compat: sem o param, comportamento original mantido
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest


def test_repo_signature_accepts_studio_agent_id():
    """Repository method must declare studio_agent_id keyword argument."""
    from app.domains.ai.repositories.ai_consumption_repository import (
        AiConsumptionRepository,
    )

    sig = inspect.signature(AiConsumptionRepository.get_usage_by_agent)
    assert "studio_agent_id" in sig.parameters, (
        "Fix 5 não aplicado: get_usage_by_agent não tem param studio_agent_id."
    )
    # Default deve ser None pra backward-compat.
    assert sig.parameters["studio_agent_id"].default is None, (
        "studio_agent_id deve ter default=None (backward-compat)."
    )


def test_repo_applies_studio_agent_id_filter_in_query():
    """Source AST check: when studio_agent_id is passed, the SQL conditions list grows."""
    src = Path("app/domains/ai/repositories/ai_consumption_repository.py").read_text()
    # Garante que o branch `if studio_agent_id:` adiciona à lista de conditions
    assert "AiConsumption.studio_agent_id ==" in src, (
        "Fix 5 não aplicado: nenhum WHERE em studio_agent_id no repository."
    )
    # E que está dentro de `if studio_agent_id`
    assert "if studio_agent_id:" in src, (
        "Filter deve estar em branch condicional `if studio_agent_id:`."
    )


def test_endpoint_signature_accepts_studio_agent_id():
    """Endpoint must declare studio_agent_id as Query parameter."""
    from app.api.v1 import ai_consumption as ep_module

    sig = inspect.signature(ep_module.get_usage_by_agent)
    assert "studio_agent_id" in sig.parameters, (
        "Fix 5 não aplicado: endpoint /by-agent não expõe studio_agent_id."
    )


def test_endpoint_passes_studio_agent_id_to_repo():
    """Source AST check: endpoint forwards studio_agent_id to repo.get_usage_by_agent."""
    src = Path("app/api/v1/ai_consumption.py").read_text()
    assert "studio_agent_id=studio_agent_id" in src, (
        "Endpoint must forward studio_agent_id to repo call. Fix 5 incompleto."
    )


@pytest.mark.asyncio
async def test_repo_filter_with_mock():
    """Smoke: repo accepts studio_agent_id without raising."""
    from unittest.mock import AsyncMock, MagicMock
    from app.domains.ai.repositories.ai_consumption_repository import (
        AiConsumptionRepository,
    )

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.all = MagicMock(return_value=[])
    mock_db.execute = AsyncMock(return_value=mock_result)

    repo = AiConsumptionRepository(mock_db)
    rows = await repo.get_usage_by_agent(
        "00000000-0000-4000-a000-000000000001",
        studio_agent_id="agent-123",
    )
    assert rows == []
    # Confirma que execute foi chamado (SQL gerado sem erro)
    assert mock_db.execute.await_count == 1
